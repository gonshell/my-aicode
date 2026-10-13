#!/usr/bin/env python3
"""
阅读模式主入口

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
from reading.shared.file_utils import ensure_root_dir, resolve_article_path
from reading.shared.state_manager import SessionManager
from reading.shared.dialogue_writer import DialogueWriter
from reading.shared.role_validator import RoleValidator
from reading.shared.anchor_generator import AnchorGenerator

logger = get_logger()

# 输入长度限制：10万字
MAX_INPUT_LENGTH = 100000


def handle_new_article(user_input: str, context: Optional[Dict] = None, intent=None) -> str:
    """处理新文章阅读"""
    root_dir = ensure_root_dir()
    
    # 输入长度检查
    if len(user_input) > MAX_INPUT_LENGTH:
        return (
            f"⚠️  文章太长了（当前 {len(user_input)} 字）。\n\n"
            f"为了保证阅读质量，建议单次不要超过 {MAX_INPUT_LENGTH} 字。\n"
            "你可以分几次发给我。"
        )
    
    # 简单的文章标题提取（实际应该用LLM）
    article_title = user_input[:50] if len(user_input) > 50 else user_input
    article_title = article_title.replace("\n", " ").strip()
    
    # 生成文章slug
    article_slug = "article-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    article_dir = resolve_article_path(root_dir, article_slug)
    
    # 初始化会话
    session_mgr = SessionManager(article_dir)
    session_mgr.init_new_session(
        article_title=article_title,
        article_content=user_input,
        active_role="thinking_partner"
    )
    
    # 初始化note.md
    note_content = f"""---
title: {article_title}
author: 未知
source: 用户输入
read_date: {datetime.now().isoformat()}
status: reading
---

# {article_title}

## 📋 文章结构
（待填充）

## 🎯 核心论点
（待填充）

## 💡 我的洞察
（待填充）
"""
    with open(article_dir / "note.md", "w", encoding="utf-8") as f:
        f.write(note_content)
    
    # 初始化对话记录
    dialogue_writer = DialogueWriter(article_dir)
    dialogue_writer.init_dialogue(
        article_title=article_title,
        start_time=datetime.now().isoformat()
    )
    
    # 记录系统开场白
    dialogue_writer.add_turn(
        speaker="系统",
        content=f"开始阅读：{article_title}",
        section="开头",
        tags=["系统消息"]
    )
    
    logger.info("创建新文章会话：%s", article_slug)
    
    return (
        f"✅ 开始阅读：**{article_title}**\n\n"
        "我已经帮你创建了结构化笔记。我们可以开始讨论了——\n\n"
        "💡 你可以随时说：\n"
        "- \"挑挑毛病\" → 切换到魔鬼代言人模式\n"
        "- \"引导我想想\" → 切换到苏格拉底提问模式\n"
        "- \"用学术标准审一下\" → 切换到同行评审模式\n"
        "- \"先到这，明天继续\" → 保存状态，下次回来继续\n"
        "- \"整理一下\" → 把我们的讨论回流到笔记里"
    )


def handle_continue_session(user_input: str, context: Optional[Dict] = None, intent=None) -> str:
    """继续未完成的会话"""
    root_dir = ensure_root_dir()
    articles_dir = root_dir / "articles"
    
    if not articles_dir.exists():
        return "还没有任何阅读历史，先给我一篇文章开始吧！"
    
    # 查找所有有活跃会话的文章
    active_sessions = []
    for article_dir in articles_dir.iterdir():
        session_file = article_dir / ".session.yaml"
        if session_file.exists():
            session_mgr = SessionManager(article_dir)
            session = session_mgr.load()
            active_sessions.append({
                "dir": article_dir,
                "title": session.get("article_title", "未知文章"),
                "turns": session.get("turn_count", 0),
                "updated": session.get("last_updated", "")
            })
    
    if not active_sessions:
        return "没有找到未完成的阅读会话，给我一篇文章开始吧！"
    
    # 按最后更新时间排序，取最近的
    active_sessions.sort(key=lambda x: x["updated"], reverse=True)
    
    if len(active_sessions) == 1:
        # 只有一个，直接继续
        s = active_sessions[0]
        return (
            f"✅ 继续上次的阅读：**{s['title']}**\n\n"
            f"我们已经讨论了 {s['turns']} 轮，上次更新是 {s['updated'][:16]}。\n\n"
            "我们接着聊吧！"
        )
    else:
        # 有多个，让用户选
        result = "找到多个未完成的阅读会话：\n\n"
        for i, s in enumerate(active_sessions[:5], 1):
            result += f"{i}. **{s['title']}** — 已讨论 {s['turns']} 轮\n"
        result += "\n你想继续哪个？"
        return result


def handle_discussion(user_input: str, context: Optional[Dict] = None, intent=None) -> str:
    """处理正常讨论对话"""
    # 简化实现：返回一个标准响应，实际会调用LLM
    return (
        f"你说的很有道理。我们继续深入讨论？\n\n"
        "（实际实现会根据当前角色生成对应风格的回应，并写入对话记录）"
    )


def handle_role_switch(user_input: str, new_role: str, context: Optional[Dict] = None, intent=None) -> str:
    """处理角色切换"""
    role_names = {
        "thinking_partner": "🧑‍🤝‍🧑 思考伙伴",
        "devil_advocate": "😈 魔鬼代言人",
        "socratic_tutor": "👨‍🏫 苏格拉底辅导员",
        "peer_reviewer": "🔬 同行评审",
    }
    
    return (
        f"✅ 已切换到「{role_names.get(new_role, new_role)}」模式。\n\n"
        "我们继续讨论吧！"
    )


def main(user_input: str, context: Optional[Dict] = None, intent=None) -> str:
    """阅读模式主入口"""
    logger.info("进入阅读模式，用户输入：%s", user_input[:100])
    
    # 意图识别已经在外层做过了，这里处理具体的子意图
    user_lower = user_input.lower()
    
    if any(w in user_lower for w in ["继续", "接着", "刚才"]):
        return handle_continue_session(user_input, context, intent)
    
    if any(w in user_lower for w in ["角色", "模式", "挑毛病", "反调", "引导", "学术标准"]):
        # 提取角色
        if any(w in user_lower for w in ["挑毛病", "反调", "找茬"]):
            return handle_role_switch(user_input, "devil_advocate", context, intent)
        elif any(w in user_lower for w in ["引导", "苏格拉底", "启发"]):
            return handle_role_switch(user_input, "socratic_tutor", context, intent)
        elif any(w in user_lower for w in ["学术标准", "严格审", "同行评审"]):
            return handle_role_switch(user_input, "peer_reviewer", context, intent)
    
    # 如果是新文章（没有上下文，输入比较长）
    if len(user_input) > 200 or any(w in user_lower for w in ["读一下", "看看这篇", "解析", "文章"]):
        return handle_new_article(user_input, context, intent)
    
    # 默认是正常讨论
    return handle_discussion(user_input, context, intent)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(main(" ".join(sys.argv[1:])))
    else:
        print("请输入用户内容")
