#!/usr/bin/env python3
"""
统一日志机制：所有日志写入到技能自己的 logs/ 目录下
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class SkillLogger:
    """技能专用日志器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls, skill_root: Optional[Path] = None):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, skill_root: Optional[Path] = None):
        if self._initialized:
            return
        
        if skill_root is None:
            skill_root = Path(__file__).parent.parent
        
        self.log_dir = skill_root / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 按天切割日志
        today = datetime.now().strftime("%Y-%m-%d")
        self.log_file = self.log_dir / f"{today}.log"
        
        self._initialized = True
    
    def _write(self, level: str, message: str, *args):
        """写入日志行"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted = message % args if args else message
        line = f"[{timestamp}] [{level}] {formatted}\n"
        
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(line)
    
    def info(self, message: str, *args):
        self._write("INFO", message, *args)
    
    def warn(self, message: str, *args):
        self._write("WARN", message, *args)
    
    def error(self, message: str, *args):
        self._write("ERROR", message, *args)
    
    def exception(self, e: Exception, context: str = ""):
        import traceback
        tb = traceback.format_exc()
        self._write("ERROR", f"{context}: {type(e).__name__}: {e}\n{tb}")


# 便捷函数
def get_logger() -> SkillLogger:
    return SkillLogger()
