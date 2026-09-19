# -*- coding: utf-8 -*-
"""
客户端层 — LLM 调用（OpenAI 兼容接口，支持 Function Calling）
================================================================
统一封装大模型调用，供 agent.py 使用。换模型只需改 .env，不改代码。
"""

import config
from openai import OpenAI


def get_client() -> OpenAI:
    """构造 OpenAI 兼容客户端（DeepSeek/豆包/通义均兼容）。"""
    if not config.is_configured():
        raise RuntimeError("未配置 LLM_API_KEY：请复制 .env.example 为 .env 并填入 Key")
    return OpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)


def chat(messages, tools=None, tool_choice=None, temperature=None):
    """
    调用 LLM。
      messages   : 对话消息列表
      tools      : 工具 schema 列表（传入即启用 Function Calling）
      tool_choice: "auto" 让模型决定是否调工具；"none" 禁用
    返回 OpenAI ChatCompletion 响应对象（调用方自行取 message / tool_calls）。
    """
    client = get_client()
    kwargs = dict(
        model=config.LLM_MODEL,
        messages=messages,
        temperature=config.LLM_TEMPERATURE if temperature is None else temperature,
    )
    if tools:
        kwargs["tools"] = tools
    if tool_choice:
        kwargs["tool_choice"] = tool_choice
    return client.chat.completions.create(**kwargs)
