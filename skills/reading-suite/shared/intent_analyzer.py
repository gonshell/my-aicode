#!/usr/bin/env python3
"""
意图识别核心：自动判断用户想要做什么（阅读 / 拆卡片 / 复盘）
"""

import re
from typing import Dict, Tuple, Optional
from dataclasses import dataclass

from .logger import get_logger

logger = get_logger()


@dataclass
class Intent:
    """识别出的意图"""
    mode: str  # "read" / "cards" / "review"
    confidence: float  # 0.0 - 1.0
    parameters: Dict[str, str]
    raw_input: str


class IntentAnalyzer:
    """意图分析器"""
    
    # 各模式的触发关键词，按权重排序
    KEYWORDS = {
        "read": [
            (1.0, ["读一下", "帮我读", "看看这篇", "解析一下", "分析一下"]),
            (0.8, ["继续读", "接着看", "往下读", "刚才那篇"]),
            (0.7, ["笔记", "记录", "整理一下"]),
            (0.5, ["文章", "内容", "这段话", "这段"]),
        ],
        "cards": [
            (1.0, ["拆成卡片", "提取卡片", "做成卡片", "卡片化"]),
            (0.9, ["拆卡片", "做卡片", "生成卡片", "原子化"]),
            (0.7, ["整理成卡", "转成卡片"]),
        ],
        "review": [
            (1.0, ["复盘一下", "全局复盘", "知识库复盘", "检查一下"]),
            (0.9, ["有没有重复", "有没有冲突", "找问题", "优化笔记"]),
            (0.8, ["最近一周", "最近一月", "全部复盘"]),
            (0.7, ["review", "Review", "REVIEW"]),
        ]
    }
    
    # 角色切换关键词
    ROLE_KEYWORDS = {
        "devil_advocate": ["挑毛病", "唱反调", "找茬", "反面", "质疑"],
        "socratic_tutor": ["引导我", "苏格拉底", "启发式", "给我提问"],
        "peer_reviewer": ["学术标准", "严格审", "同行评审", "专业角度"],
    }
    
    # 复盘范围关键词
    SCOPE_KEYWORDS = {
        "last_7_days": ["一周", "7天", "最近一周"],
        "last_30_days": ["一月", "30天", "最近一月", "这个月"],
        "all": ["全部", "所有", "整个", "全局"],
    }
    
    def analyze(self, user_input: str) -> Intent:
        """
        分析用户输入的意图
        
        返回：
            Intent 对象，包含 mode、confidence、parameters
        """
        user_lower = user_input.lower().strip()
        
        scores = {
            "read": 0.0,
            "cards": 0.0,
            "review": 0.0
        }
        
        parameters = {}
        
        # 1. 匹配各模式关键词
        for mode, keyword_groups in self.KEYWORDS.items():
            for weight, keywords in keyword_groups:
                for kw in keywords:
                    if kw in user_input:
                        scores[mode] += weight
                        break  # 每组只匹配一次
        
        # 2. 识别角色切换参数
        for role, keywords in self.ROLE_KEYWORDS.items():
            for kw in keywords:
                if kw in user_input:
                    parameters["switch_to_role"] = role
                    # 角色切换肯定是在阅读模式下
                    scores["read"] += 0.5
                    break
        
        # 3. 识别复盘范围
        for scope, keywords in self.SCOPE_KEYWORDS.items():
            for kw in keywords:
                if kw in user_input:
                    parameters["review_scope"] = scope
                    break
        
        # 4. 识别"继续"类指令
        continue_words = ["继续", "接着", "刚才", "之前"]
        if any(w in user_lower for w in continue_words):
            # 这个时候应该自动检测哪个模式有未完成的会话
            parameters["continue_last"] = True
            # 默认偏向阅读模式
            scores["read"] += 0.3
        
        # 5. 找出最高分
        max_score = max(scores.values())
        total_score = sum(scores.values())
        
        # 如果所有分数都是0，默认是阅读模式
        if total_score < 0.1:
            logger.info("没有匹配到明确关键词，默认阅读模式")
            return Intent(
                mode="read",
                confidence=0.5,
                parameters=parameters,
                raw_input=user_input
            )
        
        # 计算置信度
        best_mode = max(scores, key=scores.get)
        confidence = scores[best_mode] / total_score if total_score > 0 else 0.5
        
        # 6. 边界情况处理
        # 如果两个模式分数很接近（差小于0.2），默认阅读模式
        second_best = sorted(scores.values())[-2]
        if max_score - second_best < 0.2:
            logger.warn("意图识别不明确，分数接近：%s", scores)
            # 模糊的时候默认阅读模式
            best_mode = "read"
            confidence = 0.5
        
        intent = Intent(
            mode=best_mode,
            confidence=confidence,
            parameters=parameters,
            raw_input=user_input
        )
        
        logger.info("意图识别结果：mode=%s, confidence=%.2f, params=%s",
                   best_mode, confidence, parameters)
        
        return intent
    
    def is_confident_enough(self, intent: Intent, threshold: float = 0.6) -> bool:
        """判断置信度是否足够高"""
        return intent.confidence >= threshold


# 便捷函数
def analyze_intent(user_input: str) -> Intent:
    analyzer = IntentAnalyzer()
    return analyzer.analyze(user_input)
