#!/usr/bin/env python3
"""
文件工具类：根目录确定、路径解析、文件读写等
"""

import os
import json
from pathlib import Path
from typing import Optional


def load_config(skill_root: Optional[Path] = None) -> dict:
    """加载技能配置文件"""
    if skill_root is None:
        skill_root = Path(__file__).parent.parent
    
    config_path = skill_root / "config.json"
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def ensure_root_dir(config_root: Optional[str] = None) -> Path:
    """
    按优先级确定知识库根目录并确保存在
    
    优先级：
    1. 显式传入的参数
    2. 环境变量 READING_SUITE_ROOT
    3. 配置文件中的 root_dir
    4. 默认值：~/reading-workspace/
    """
    if config_root:
        root = Path(os.path.expanduser(config_root)).expanduser()
    elif "READING_SUITE_ROOT" in os.environ:
        root = Path(os.path.expanduser(os.environ["READING_SUITE_ROOT"])).expanduser()
    else:
        root = Path("~/reading-workspace/").expanduser()
    
    root.mkdir(parents=True, exist_ok=True)
    return root


def resolve_article_path(root_dir: Path, article_slug: str) -> Path:
    """解析文章目录，确保存在"""
    article_dir = root_dir / "articles" / article_slug
    article_dir.mkdir(parents=True, exist_ok=True)
    return article_dir


def ensure_article_dirs(article_dir: Path) -> None:
    """确保文章所需的所有子目录都存在"""
    (article_dir / "cards").mkdir(exist_ok=True)
