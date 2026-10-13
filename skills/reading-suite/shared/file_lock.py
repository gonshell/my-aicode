#!/usr/bin/env python3
"""
简单的文件锁：防止并发写入同一个状态文件

优化：添加死锁自动清理，如果锁文件超过一定时间自动删除
"""

import os
import time
from pathlib import Path
from typing import Optional

from .logger import get_logger

logger = get_logger()


class FileLock:
    """上下文管理器形式的文件锁"""
    
    def __init__(self, file_path: Path, timeout: int = 5, lock_ttl: int = 60):
        """
        Args:
            file_path: 要锁定的文件路径
            timeout: 获取锁超时时间（秒）
            lock_ttl: 锁的最大存活时间（秒），超过自动清理死锁
        """
        self.lock_file = file_path.with_suffix(file_path.suffix + ".lock")
        self.timeout = timeout
        self.lock_ttl = lock_ttl
        self._locked = False
    
    def _cleanup_stale_lock(self):
        """清理超时的死锁文件"""
        if self.lock_file.exists():
            try:
                mtime = self.lock_file.stat().st_mtime
                age = time.time() - mtime
                
                if age > self.lock_ttl:
                    self.lock_file.unlink()
                    logger.warn("清理超时死锁文件：%s (已存在%d秒)", 
                               self.lock_file, age)
                    return True
            except Exception as e:
                logger.exception(e, "清理死锁文件失败")
        
        return False
    
    def __enter__(self):
        start = time.time()
        
        # 首先尝试清理可能存在的死锁
        self._cleanup_stale_lock()
        
        while time.time() - start < self.timeout:
            try:
                # 原子性创建锁文件
                fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.close(fd)
                self._locked = True
                logger.info("获取文件锁成功：%s", self.lock_file)
                return self
            except FileExistsError:
                # 锁已存在，再检查一次是不是死锁
                self._cleanup_stale_lock()
                time.sleep(0.1)
        
        raise TimeoutError(f"获取文件锁超时（{self.timeout}秒）：{self.lock_file}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._locked and self.lock_file.exists():
            try:
                self.lock_file.unlink()
                self._locked = False
                logger.info("释放文件锁：%s", self.lock_file)
            except Exception as e:
                logger.exception(e, "删除锁文件失败")
        return False  # 不抑制异常
