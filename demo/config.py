# -*- coding: utf-8 -*-
"""
配置层 — 从 .env / 环境变量读取 LLM 配置
================================================================
支持任意 OpenAI 兼容接口的国内模型（DeepSeek / 豆包 / 通义千问）。

用法：
  1. 复制 .env.example 为 .env
  2. 填入你的 API Key（对应模型）
  3. 若用豆包/通义，同步修改 BASE_URL 和 MODEL
"""

import os


def _load_dotenv(path=".env"):
    """轻量 .env 加载器（避免额外依赖 python-dotenv）。环境变量优先，.env 兜底。"""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())


_load_dotenv()

# ---------------- LLM 配置（OpenAI 兼容接口） ----------------
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek-chat")

# 温度：风控场景要稳定、可解释，用较低温度
LLM_TEMPERATURE = float(os.environ.get("LLM_TEMPERATURE", "0.3"))


def is_configured():
    """是否已配置 API Key。"""
    return bool(LLM_API_KEY)
