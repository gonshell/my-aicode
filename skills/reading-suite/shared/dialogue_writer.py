#!/usr/bin/env python3
"""
dialogue.md 写入工具：四层锚点系统 + 自动维护索引表

修复：
1. 索引查找算法优化，更健壮，不依赖行数间隔
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, List, Dict

from .file_lock import FileLock
from .logger import get_logger

logger = get_logger()


class DialogueWriter:
    """对话记录写入器"""
    
    def __init__(self, article_dir: Path):
        self.article_dir = article_dir
        self.dialogue_file = article_dir / "dialogue.md"
    
    def init_dialogue(self, article_title: str, start_time: str) -> None:
        """初始化 dialogue.md 文件头"""
        content = f"""---
article: {article_title}
start_time: {start_time}
last_updated: {start_time}
total_rounds: 0
sections_discussed: []
tags: []
open_questions: 0
pending_reflections: 0
---

## 🔍 对话索引

| 日期 | 讨论章节 | 主题标签 | 轮次 | 状态 |
|:-----|:---------|:---------|:-----|:-----|

--- 对话内容开始 ---

"""
        with open(self.dialogue_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info("初始化 dialogue.md：%s", article_title)
    
    def add_turn(self, speaker: str, content: str, section: str, 
                 tags: List[str], note_line_range: Optional[Tuple[int, int]] = None) -> None:
        """添加一轮对话"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 读取当前轮次
        current_round = self._get_current_round_number()
        round_num = current_round + 1
        
        # 行号锚点显示
        anchor_str = f"note.md 第{note_line_range[0]}-{note_line_range[1]}行" if note_line_range else section
        
        # 构建这一轮的内容
        turn_content = f"""
### {timestamp} · 第{round_num}轮 · 📍 锚点：{anchor_str}
**{speaker}：**
> {content}

"""
        
        # 追加到文件末尾
        with FileLock(self.dialogue_file):
            with open(self.dialogue_file, "a", encoding="utf-8") as f:
                f.write(turn_content)
        
        # 更新索引表和文件头统计信息
        self._update_header_and_index(
            round_num=round_num,
            date=timestamp,
            section=section,
            tags=tags
        )
        
        logger.info("添加第%d轮对话，角色：%s，章节：%s", round_num, speaker, section)
    
    def _get_current_round_number(self) -> int:
        """获取当前已有多少轮对话"""
        if not self.dialogue_file.exists():
            return 0
        
        with open(self.dialogue_file, "r", encoding="utf-8") as f:
            text = f.read()
            # 每出现一个 ### 就是一轮对话
            return text.count("### 20")  # 20xx年，避免匹配到其他标题
    
    def _update_header_and_index(self, round_num: int, date: str, section: str, tags: List[str]) -> None:
        """更新文件头的统计信息和对话索引表"""
        if not self.dialogue_file.exists():
            return
        
        with FileLock(self.dialogue_file):
            with open(self.dialogue_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # 第一步：更新文件头YAML
            # 找到第二个 ---，也就是YAML头的结束
            header_end = None
            dash_count = 0
            for i, line in enumerate(lines):
                if line.strip() == "---":
                    dash_count += 1
                    if dash_count == 2:
                        header_end = i
                        break
            
            if header_end is None:
                logger.error("找不到YAML头结束标记，跳过更新")
                return
            
            header_lines = lines[1:header_end]
            header = yaml.safe_load("".join(header_lines)) or {}
            
            # 更新统计
            header["last_updated"] = datetime.now().isoformat()
            header["total_rounds"] = round_num
            
            # 正确处理 sections_discussed 数组
            if section not in header.get("sections_discussed", []):
                sections = header.get("sections_discussed", [])
                sections.append(section)
                header["sections_discussed"] = sections
            
            # 更新标签去重
            existing_tags = header.get("tags", [])
            for tag in tags:
                if tag not in existing_tags:
                    existing_tags.append(tag)
            header["tags"] = existing_tags
            
            # 写回头部
            new_header_lines = yaml.dump(header, allow_unicode=True, default_flow_style=False).splitlines(keepends=True)
            lines[1:header_end] = new_header_lines
            
            # 第二步：更新对话索引表
            # ✅ 优化：用明确的标记查找，更可靠
            # 找到 "--- 对话内容开始 ---" 这一行，索引表就在它前面
            content_start_marker = "--- 对话内容开始 ---"
            
            index_end = None
            for i, line in enumerate(lines):
                if content_start_marker in line:
                    index_end = i
                    break
            
            if index_end is not None:
                # 在标记之前插入新行
                tags_str = ", ".join(tags)
                new_row = f"| {date} | {section} | {tags_str} | 第{round_num}轮 | 活跃 |\n"
                
                # 找到表格最后一行的位置（在标记之前，跳过空行）
                insert_pos = index_end - 1
                while insert_pos > 0 and lines[insert_pos].strip() == "":
                    insert_pos -= 1
                
                lines.insert(insert_pos + 1, new_row)
            
            # 写回整个文件
            with open(self.dialogue_file, "w", encoding="utf-8") as f:
                f.writelines(lines)
