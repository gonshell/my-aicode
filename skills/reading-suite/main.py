#!/usr/bin/env python3
"""
Reading Suite 主入口
被Hermes技能系统调用的统一入口
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any

# 把技能目录加入路径
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))

from shared.logger import get_logger
from shared.intent_analyzer import analyze_intent

logger = get_logger()


def main(user_input: str, context: Optional[Dict] = None) -> str:
    """
    技能统一入口
    
    Args:
        user_input: 用户的自然语言输入
        context: Hermes传入的上下文对象，包含历史消息等
    
    Returns:
        返回给用户的响应字符串
    """
    logger.info("=" * 60)
    logger.info("收到用户输入：%s", user_input[:100])
    
    # 第一步：意图识别
    intent = analyze_intent(user_input)
    
    logger.info("意图识别：mode=%s, confidence=%.2f", intent.mode, intent.confidence)
    
    # 第二步：路由到对应模式
    if intent.mode == "read":
        from scripts.read import main as read_main
        return read_main(user_input, context, intent)
    
    elif intent.mode == "cards":
        from scripts.cards import main as cards_main
        return cards_main(user_input, context, intent)
    
    elif intent.mode == "review":
        from scripts.review import main as review_main
        return review_main(user_input, context, intent)
    
    else:
        logger.error("未知模式：%s", intent.mode)
        return "抱歉，我没太理解你想做什么。"


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(main(" ".join(sys.argv[1:])))
    else:
        print("Reading Suite 主入口")
        print("用法：python main.py <用户输入>")
