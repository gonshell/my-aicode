#!/usr/bin/env python3
"""
会话状态管理：所有状态落盘到 .session.yaml

修复：
1. 致命Bug：文件存在性判断逻辑写反（not搞反了）
2. 添加YAML序列化兼容参数
3. 添加状态降级时的日志警告
"""

import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from .file_lock import FileLock
from .logger import get_logger

logger = get_logger()


class BaseSessionManager(ABC):
    """会话状态管理器抽象基类"""
    
    def __init__(self, session_file: Path):
        self.session_file = session_file
        self.session: Dict[str, Any] = {}
    
    @abstractmethod
    def get_default_session(self) -> Dict[str, Any]:
        """返回默认的空会话结构，用于损坏时降级"""
        pass
    
    def load(self) -> Dict[str, Any]:
        """
        加载会话状态
        
        如果文件损坏，自动降级返回默认状态，不会崩溃
        """
        # ✅ 修复致命Bug：原来的逻辑写反了，应该是文件存在才去读
        if self.session_file.exists():
            try:
                with FileLock(self.session_file):
                    with open(self.session_file, "r", encoding="utf-8") as f:
                        self.session = yaml.safe_load(f) or {}
                logger.info("成功加载会话状态：%s", self.session_file)
            except Exception as e:
                logger.exception(e, "会话文件损坏，降级使用默认状态")
                self.session = self.get_default_session()
        else:
            # 文件不存在，使用默认状态
            logger.info("会话文件不存在，使用默认状态：%s", self.session_file)
            self.session = self.get_default_session()
        
        return self.session
    
    def save(self) -> None:
        """安全保存会话状态，带文件锁"""
        try:
            self.session["last_updated"] = datetime.now().isoformat()
            
            with FileLock(self.session_file):
                with open(self.session_file, "w", encoding="utf-8") as f:
                    # ✅ 优化：强制块级样式，兼容更好
                    yaml.dump(self.session, f, allow_unicode=True, default_flow_style=False)
            
            logger.info("成功保存会话状态：%s", self.session_file)
        except Exception as e:
            logger.exception(e, "保存会话状态失败")
            raise
    
    def has_active_session(self) -> bool:
        """是否有活跃会话"""
        return self.session_file.exists()


# ... 其余部分保持不变，下面是完整的类定义
class SessionManager(BaseSessionManager):
    """阅读会话状态管理器"""
    
    def __init__(self, article_dir: Path):
        super().__init__(article_dir / ".session.yaml")
        self.article_dir = article_dir
    
    def get_default_session(self) -> Dict[str, Any]:
        return {
            "article_title": "未知文章",
            "start_time": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "turn_count": 0,
            "active_role": "thinking_partner",
            "current_section": "开头",
            "context_layers": {
                "recent": [],
                "medium": "",
                "long_term": ""
            },
            "pending_reflections": [],
            "status": "recovered_from_error"
        }
    
    def init_new_session(self, article_title: str, article_content: str, 
                        active_role: str = "thinking_partner") -> None:
        """初始化新的阅读会话"""
        self.session = {
            "article_title": article_title,
            "start_time": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "turn_count": 0,
            "active_role": active_role,
            "current_section": "开头",
            "context_layers": {
                "recent": [],
                "medium": "",
                "long_term": ""
            },
            "pending_reflections": [],
            "status": "active"
        }
        self.save()
        logger.info("初始化新阅读会话：%s", article_title)
    
    def update_role(self, new_role: str) -> None:
        """更新当前角色"""
        self.load()
        self.session["active_role"] = new_role
        self.save()
        logger.info("切换角色：%s", new_role)
    
    def increment_turn(self) -> None:
        """轮次+1"""
        self.load()
        self.session["turn_count"] += 1
        self.save()
    
    def update_context_summary(self, user_input: str, response: str) -> None:
        """更新上下文摘要（分层）"""
        self.load()
        
        # 最近N轮保留完整对话
        recent = self.session["context_layers"]["recent"]
        recent.append({
            "turn": self.session["turn_count"],
            "user": user_input,
            "assistant": response
        })
        
        # 只保留最近3轮
        if len(recent) > 3:
            # 把更早的压缩到 medium 摘要
            archived = recent.pop(0)
            self.session["context_layers"]["medium"] += (
                f"\n第{archived['turn']}轮：用户说{archived['user'][:50]}...，AI回应{archived['assistant'][:50]}..."
            )
        
        self.session["context_layers"]["recent"] = recent
        self.save()
    
    def add_pending_reflection(self, item: Dict[str, Any]) -> None:
        """添加待回流条目"""
        self.load()
        self.session["pending_reflections"].append(item)
        self.save()


class CardsSessionManager(BaseSessionManager):
    """卡片拆分会话管理器"""
    
    def __init__(self, article_dir: Path):
        super().__init__(article_dir / ".cards_session.yaml")
        self.article_dir = article_dir
    
    def get_default_session(self) -> Dict[str, Any]:
        return {
            "start_time": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "recovered_from_error",
            "draft": [],
            "current_step": "reviewing_draft"
        }
    
    def init_session(self, draft: List[Dict]) -> None:
        self.session = {
            "start_time": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "status": "drafting",
            "draft": draft,
            "current_step": "reviewing_draft"
        }
        self.save()
        logger.info("初始化新卡片拆分会话，草案共%d张卡片", len(draft))
    
    def update_draft(self, draft: List[Dict]) -> None:
        self.load()
        self.session["draft"] = draft
        self.save()
        logger.info("更新卡片草案，现在%d张", len(draft))
    
    def mark_completed(self) -> None:
        self.load()
        self.session["status"] = "completed"
        self.save()
        logger.info("卡片拆分完成")


class ReviewSessionManager(BaseSessionManager):
    """复盘会话管理器"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.review_dir = root_dir / "review"
        self.review_dir.mkdir(exist_ok=True)
        super().__init__(self.review_dir / ".current_session.yaml")
    
    def get_default_session(self) -> Dict[str, Any]:
        return {
            "start_time": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "scope": "unknown",
            "status": "recovered_from_error",
            "scan_result": {"issues": [], "stats": {}},
            "current_issue_index": 0
        }
    
    def init_session(self, scope: str, scan_result: Dict) -> None:
        self.session = {
            "start_time": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "scope": scope,
            "status": "scanning",
            "scan_result": scan_result,
            "current_issue_index": 0
        }
        self.save()
        logger.info("初始化新复盘会话，范围：%s", scope)
    
    def mark_issue_resolved(self, issue_id: int, resolution: str) -> None:
        self.load()
        for issue in self.session["scan_result"]["issues"]:
            if issue["id"] == issue_id:
                issue["status"] = "resolved"
                issue["resolution"] = resolution
                break
        self.save()
        logger.info("问题#%d已解决：%s", issue_id, resolution)
    
    def mark_issue_dismissed(self, issue_id: int, reason: str) -> None:
        self.load()
        for issue in self.session["scan_result"]["issues"]:
            if issue["id"] == issue_id:
                issue["status"] = "dismissed"
                issue["dismiss_reason"] = reason
                break
        self.save()
        logger.info("问题#%d已忽略：%s", issue_id, reason)
    
    def add_user_issue(self, issue: Dict) -> None:
        self.load()
        issue["id"] = len(self.session["scan_result"]["issues"]) + 1
        issue["type"] = "user_reported"
        issue["status"] = "pending"
        self.session["scan_result"]["issues"].append(issue)
        self.save()
        logger.info("用户补充问题：%s", issue.get("description", ""))
    
    def mark_completed(self) -> None:
        self.load()
        self.session["status"] = "completed"
        self.session["completed_time"] = datetime.now().isoformat()
        self.save()
        # 归档会话文件
        archived_name = f"session-{datetime.now().strftime('%Y%m%d-%H%M')}.yaml"
        self.session_file.rename(self.review_dir / archived_name)
        logger.info("复盘完成，会话已归档：%s", archived_name)
