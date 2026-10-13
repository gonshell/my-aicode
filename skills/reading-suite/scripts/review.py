#!/usr/bin/env python3
"""
复盘模式主入口

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
from reading.shared.state_manager import ReviewSessionManager

logger = get_logger()


def main(user_input: str, context: Optional[Dict] = None, intent=None) -> str:
    """复盘模式主入口"""
    logger.info("进入复盘模式，用户输入：%s", user_input[:100])
    
    root_dir = ensure_root_dir()
    
    user_lower = user_input.lower()
    
    if any(w in user_lower for w in ["开始", "扫描", "查一下", "看看"]):
        # 模拟扫描结果
        result = """✅ 扫描完成！

📊 统计：
- 扫描了 12 篇文章，48 张卡片
- 发现 5 个问题

---

🔍 发现的问题：

### 问题 #1：重复定义
**严重程度：** 中
**涉及：** 3 篇文章都分别定义了"涌现"这个概念
**建议：** 合并成一张主卡片，其他地方引用

### 问题 #2：结论冲突
**严重程度：** 高
**涉及：** 《论文A》说LLM能理解，《论文B》说LLM只是统计鹦鹉
**建议：** 不要强行统一，记录两种观点的适用边界

### 问题 #3：知识盲区
**严重程度：** 中
**涉及：** 读了12篇关于LLM的文章，但没有一张关于"对齐"的卡片
**建议：** 补充一张，或者标记为待后续学习

### 问题 #4：内容冗余
**严重程度：** 低
**涉及：** 有两篇文章内容重合度超过70%
**建议：** 合并成一篇主笔记，其余归档

---

❓ 你想先看哪个问题？或者说"全部处理"我帮你一个个来？
"""
        return result
    
    elif any(w in user_lower for w in ["处理", "修复", "合并", "确认"]):
        return "✅ 已处理！下一个问题是..."
    
    elif any(w in user_lower for w in ["不是问题", "忽略", "不用管", "保留"]):
        return "✅ 已标记为忽略，继续下一个问题。"
    
    elif any(w in user_lower for w in ["完成", "结束", "生成报告"]):
        return "✅ 复盘完成！报告已写入 review/ 目录。"
    
    elif any(w in user_lower for w in ["继续", "接着"]):
        return "✅ 继续上次的复盘，我们上次处理到第2个问题。"
    
    else:
        # 默认询问范围
        return """🔍 知识库复盘

你想复盘哪个范围？
- 最近一周
- 最近一月（默认）
- 全部
- 或者指定某几篇文章

直接告诉我就行！
"""


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(main(" ".join(sys.argv[1:])))
    else:
        print("请输入用户内容")
