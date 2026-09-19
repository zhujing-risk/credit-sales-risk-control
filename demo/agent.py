# -*- coding: utf-8 -*-
"""
编排层 — AI 风控 Agent（Function Calling 工作流编排）
================================================================
核心工作流（面试可讲）：
  LLM 收到任务 → 自主决定调用哪个风控工具 → 工具返回结构化数据
  → LLM 把数据转成老板看得懂的「人话」→ 输出最终结果

这是「规则引擎 + LLM 增强」架构的落地：
  - 工具层（tools.py）用确定性代码兜底风控逻辑，保证可解释、可兜底；
  - LLM 只负责「决策 + 自然语言生成」，不直接产出风控结论。
"""

import json

import config
from llm_client import chat
from prompts import (
    SYSTEM_PROMPT,
    build_profile_task,
    build_warning_task,
    build_collection_task,
)
from tools import TOOLS, execute_tool


def run_agent(task: str, max_tool_rounds: int = 3) -> str:
    """
    执行 Agent 工作流：LLM 按需调用工具，最终返回自然语言结果。
      task           : 用户任务（由 prompts.py 构造）
      max_tool_rounds: 工具调用最大轮数，防止死循环
    """
    if not config.is_configured():
        raise RuntimeError("LLM 未配置：请复制 .env.example 为 .env 并填入 API Key")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for _ in range(max_tool_rounds):
        resp = chat(messages, tools=TOOLS, tool_choice="auto")
        msg = resp.choices[0].message

        # 没有工具调用 → 模型已给出最终答案
        if not msg.tool_calls:
            return (msg.content or "").strip()

        # 有工具调用 → 回传 assistant 消息（含 tool_calls）
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        # 执行每个被调用的工具，把结果作为 tool 消息回传
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            result = execute_tool(tc.function.name, args)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

    return "（工具调用轮数超限，请检查）"


# ---------------- 三个场景的便捷入口 ----------------

def profile_agent(name: str) -> str:
    """场景：客户画像 → 生成人话摘要。"""
    return run_agent(build_profile_task(name))


def warning_agent(name: str) -> str:
    """场景：跑路预警 → 生成预警推送话术。"""
    return run_agent(build_warning_task(name))


def collection_agent(name: str, overdue_days: int) -> str:
    """场景：自动催收 → 生成催收话术。"""
    return run_agent(build_collection_task(name, overdue_days))


if __name__ == "__main__":
    # 自测：需先配置 .env
    print("=== 画像 Agent ===")
    print(profile_agent("XX服饰"))
    print("\n=== 预警 Agent ===")
    print(warning_agent("XX服饰"))
    print("\n=== 催收 Agent ===")
    print(collection_agent("XX服饰", overdue_days=15))
