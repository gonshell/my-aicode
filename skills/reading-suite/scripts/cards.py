#!/usr/bin/env python3
"""
卡片模式主入口

修复：统一函数签名，接受 intent 参数
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 把技能目录加入路径
skill_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(skill_root))

from reading.shared.logger import get_logger
from reading.shared.file_utils import ensure_root_dir
from reading.shared.state_manager import CardsSessionManager

logger = get_logger()


def main(user_input: str, context: Optional[Dict] = None, intent=None) -> str:
    """卡片模式主入口"""
    logger.info("进入卡片模式，用户输入：%s", user_input[:100])
    
    root_dir = ensure_root_dir()
    
    user_lower = user_input.lower()
    
    if any(w in user_lower for w in ["确认", "没问题", "就这样", "写吧"]):
        return "✅ 卡片已写入知识库！\n\n（实际实现会把草案写到 cards/ 目录，并更新索引）"
    
    elif any(w in user_lower for w in ["合并", "拆分", "修改", "调整", "不要"]):
        return "✅ 已根据你的要求更新了卡片草案。\n\n还有其他修改吗？没问题就说\"确认\"写入。"
    
    elif any(w in user_lower for w in ["继续", "接着"]):
        return "✅ 继续上次的卡片拆分。\n\n当前草案有4张卡片，还要调整吗？"
    
    else:
        # 默认生成拆分草案
        draft_response = """✅ 我建议拆成以下4张卡片：

### 📌 概念卡：卢曼卡片盒
- 定义：一种知识管理方法，强调原子化、双向链接、延迟做笔记
- 核心原则：阅读与反应分离，不要边读边画线

### 🛠️ 方法论卡：两阶段阅读法
- 第一阶段：只读，不做任何笔记
- 第二阶段：合上书写自己的理解

### 💡 观点卡：过早原子化的危害
- 过早拆卡片会把作者的框架当成你的框架
- 应该先消化，过段时间再拆

### 📌 概念卡：知识熵增
- 任何知识库只要还在增长，就会自发产生冗余、重复、冲突

---

❓ 你觉得这个拆分方案怎么样？可以：
- 说"确认" → 直接写入
- 说"把第1和第4张合并" → 调整方案
- 说"再加一张关于XX的" → 补充卡片
- 说"先放着，明天再说" → 保存进度
"""
        return draft_response


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(main(" ".join(sys.argv[1:])))
    else:
        print("请输入用户内容")
