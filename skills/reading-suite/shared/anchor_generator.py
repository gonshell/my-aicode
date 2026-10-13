#!/usr/bin/env python3
"""
锚点生成器：查找对话内容对应 note.md 的行号范围
"""

from pathlib import Path
from typing import Optional, Tuple


class AnchorGenerator:
    """锚点生成器"""
    
    def __init__(self, note_file: Path):
        self.note_file = note_file
        self._lines = None
    
    @property
    def lines(self) -> list:
        if self._lines is None and self.note_file.exists():
            with open(self.note_file, "r", encoding="utf-8") as f:
                self._lines = f.readlines()
        return self._lines or []
    
    def find_relevant_lines(self, content: str) -> Optional[Tuple[int, int]]:
        """
        查找内容对应的 note.md 行号范围
        
        简化实现：通过关键词匹配找到最相关的章节
        实际可以用语义相似度搜索
        """
        if not self.lines:
            return None
        
        # 提取关键词
        keywords = [w for w in content.split() if len(w) > 2]
        if not keywords:
            return None
        
        # 简单的行匹配：找包含最多关键词的连续区域
        best_start = 0
        best_count = 0
        
        for i, line in enumerate(self.lines):
            count = sum(1 for kw in keywords if kw in line)
            if count > best_count:
                best_count = count
                best_start = i
        
        if best_count == 0:
            return None
        
        # 返回一个范围，前后各3行
        start = max(0, best_start - 3) + 1  # 转成1-based
        end = min(len(self.lines), best_start + 3) + 1
        
        return (start, end)
