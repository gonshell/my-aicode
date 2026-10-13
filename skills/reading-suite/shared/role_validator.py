#!/usr/bin/env python3
"""
四角色硬约束检查器
所有角色的回应必须通过检查，不通过就重写
"""

from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any


class BaseRoleValidator(ABC):
    @abstractmethod
    def validate(self, response: str, user_input: str, session: Dict) -> Tuple[bool, str]:
        """返回 (是否通过, 错误信息)"""
        pass


class ThinkingPartnerValidator(BaseRoleValidator):
    """思考伙伴的约束"""
    
    def validate(self, response: str, user_input: str, session: Dict) -> Tuple[bool, str]:
        # 约束：不能替用户下结论
        if "你应该" in response or "你应当" in response:
            return False, "思考伙伴不能说'你应该'，不能替用户下结论"
        
        return True, ""


class DevilAdvocateValidator(BaseRoleValidator):
    """魔鬼代言人的约束"""
    
    def validate(self, response: str, user_input: str, session: Dict) -> Tuple[bool, str]:
        # 约束：每一个质疑必须锚定到具体内容，不能空泛
        if len(response.strip()) < 20:
            return False, "魔鬼代言人的质疑必须锚定到具体内容，不能空泛"
        
        # 约束：不能人身攻击
        attack_keywords = ["你错了", "你不对", "愚蠢", "荒谬"]
        for kw in attack_keywords:
            if kw in response:
                return False, f"魔鬼代言人不能人身攻击，不能说'{kw}'"
        
        return True, ""


class SocraticTutorValidator(BaseRoleValidator):
    """苏格拉底辅导员的约束"""
    
    def validate(self, response: str, user_input: str, session: Dict) -> Tuple[bool, str]:
        # 约束1：必须以问号结尾
        stripped = response.strip()
        if not stripped.endswith("？") and not stripped.endswith("?"):
            return False, "苏格拉底模式必须以问题结尾，不能直接给答案"
        
        # 约束2：不能包含"你应该"
        if "你应该" in response or "你应当" in response:
            return False, "苏格拉底模式不能给建议，不能说'你应该'"
        
        return True, ""


class PeerReviewerValidator(BaseRoleValidator):
    """同行评审的约束"""
    
    def validate(self, response: str, user_input: str, session: Dict) -> Tuple[bool, str]:
        # 约束：每一个评价必须给证据强度分或明确说明依据
        has_score = any(f"{i}分" in response for i in range(1, 6))
        has_evidence = any(kw in response for kw in ["证据", "数据", "来源", "引用", "依据"])
        
        if not has_score and not has_evidence:
            return False, "同行评审模式必须给出评价依据或证据强度分"
        
        # 约束：不能模糊处理
        if "可能" in response and "大概" in response and "也许" in response:
            return False, "同行评审不能太模糊，要给出明确的判断和依据"
        
        return True, ""


class RoleValidator:
    """工厂类，根据角色返回对应的校验器"""
    
    VALIDATORS = {
        "thinking_partner": ThinkingPartnerValidator,
        "devil_advocate": DevilAdvocateValidator,
        "socratic_tutor": SocraticTutorValidator,
        "peer_reviewer": PeerReviewerValidator
    }
    
    ROLE_NAMES = {
        "thinking_partner": "思考伙伴",
        "devil_advocate": "魔鬼代言人",
        "socratic_tutor": "苏格拉底辅导员",
        "peer_reviewer": "同行评审"
    }
    
    def __init__(self, role: str):
        self.role = role
        self.validator = self.VALIDATORS[role]()
    
    def validate(self, response: str, user_input: str, session: Dict) -> Tuple[bool, str]:
        return self.validator.validate(response, user_input, session)
