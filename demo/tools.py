# -*- coding: utf-8 -*-
"""
工具层 — 把风控能力封装成 Function Calling 工具
================================================================
将评分卡、预警规则、催收策略三个风控能力，封装为 LLM 可调用的工具。
LLM 只负责「决定调哪个工具 + 把工具结果转成人话」，风控逻辑仍由确定性代码兜底，
保证可解释、可兜底、可过监管 —— 这是「规则引擎 + LLM 增强」架构的核心。
"""

import json
from mock_data import get_customers
from risk_engine import build_profile, detect_runaway, build_collection

# ---------------- 工具 Schema（供 LLM Function Calling） ----------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_customer_profile",
            "description": "获取下游客户的信用画像：信用分、风险标签、建议赊销上限及各维度得分",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "下游客户名称"}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect_runaway_risk",
            "description": "检测下游客户的跑路风险，返回风险等级及触发的异常信号",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "下游客户名称"}
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_collection_strategy",
            "description": "获取下游客户的催收策略与阶段（根据逾期天数），用于生成催收话术",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "下游客户名称"},
                    "overdue_days": {"type": "integer", "description": "逾期天数"},
                },
                "required": ["name", "overdue_days"],
            },
        },
    },
]

# ---------------- 客户查找 ----------------
_CUSTOMERS = {c["name"]: c for c in get_customers()}


def _find(name: str):
    c = _CUSTOMERS.get(name)
    if c is None:
        raise ValueError(f"客户「{name}」不存在")
    return c


# ---------------- 工具实现（确定性风控逻辑） ----------------
def get_customer_profile(name: str) -> dict:
    """工具：客户画像（评分卡）。"""
    return build_profile(_find(name))


def detect_runaway_risk(name: str) -> dict:
    """工具：跑路预警（规则引擎）。"""
    return detect_runaway(_find(name))


def get_collection_strategy(name: str, overdue_days: int) -> dict:
    """工具：催收策略（分阶段模板）。"""
    return build_collection(_find(name), overdue_days)


# ---------------- 统一执行入口（供 agent 调用） ----------------
def execute_tool(tool_name: str, args: dict) -> dict:
    """根据 LLM 返回的工具名和参数，执行对应工具并返回结果。"""
    if tool_name == "get_customer_profile":
        return get_customer_profile(args["name"])
    if tool_name == "detect_runaway_risk":
        return detect_runaway_risk(args["name"])
    if tool_name == "get_collection_strategy":
        return get_collection_strategy(args["name"], int(args["overdue_days"]))
    raise ValueError(f"未知工具：{tool_name}")


def tool_results_as_text(tool_name: str, result: dict) -> str:
    """把工具返回的 dict 转成 JSON 文本，作为 tool 消息回传给 LLM。"""
    return json.dumps(result, ensure_ascii=False)
