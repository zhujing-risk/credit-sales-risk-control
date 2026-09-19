# 赊销风控 Demo（AI Agent 版）

给进销存 SaaS 老板看的演示 Demo，同时是求职用的 AI 应用工程作品。

**核心架构：「规则引擎兜底 + LLM 增强」**
- 工具层（`tools.py`）：评分卡 / 跑路预警 / 催收策略，用确定性代码产出结构化数据，保证可解释、可兜底；
- 编排层（`agent.py`）：LLM 通过 Function Calling 自主调用工具，把数据转成老板看得懂的人话。

## 运行

```bash
pip install streamlit openai
cd demo
cp .env.example .env        # 填入你的 LLM API Key
streamlit run app.py
```

浏览器自动打开 `http://localhost:8501`（用 Chrome，老 Safari 会白屏）。

## 配置 LLM（.env）

支持任意 OpenAI 兼容接口的国内模型：

| 模型 | LLM_BASE_URL | LLM_MODEL |
|------|--------------|-----------|
| DeepSeek（默认） | `https://api.deepseek.com` | `deepseek-chat` |
| 豆包（火山方舟） | `https://ark.cn-beijing.volces.com/api/v3` | 你的 endpoint id |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |

**不填 key 也能跑**：规则展示（信用分/预警信号/催收模板）不依赖 LLM，只有「AI 生成」按钮需要 key。

## 演示脚本（30 秒）

1. **「② 跑路预警」** → 看 `XX服饰` 红色高危（规则信号）；
2. 点 **「🤖 AI 生成预警推送」** → LLM 生成通俗预警话术；
3. **「③ 自动催收」** → 逾期天数拉到 15，点 **「🤖 AI 生成催收话术」** → LLM 生成合规话术。

## 文件结构

| 文件 | 作用 |
|------|------|
| `app.py` | Streamlit 界面（三个 Tab + AI 生成按钮） |
| `agent.py` | **编排层**：Function Calling 工作流（LLM 调工具 → 生成人话） |
| `tools.py` | **工具层**：评分卡/预警/催收封装成 Function Calling 工具 |
| `prompts.py` | **Prompt 层**：结构化 Prompt（角色+约束+输出格式） |
| `llm_client.py` | **客户端层**：OpenAI 兼容调用 |
| `config.py` | 配置读取（.env / 环境变量） |
| `evaluate.py` | **评测层**：合规性/信息覆盖/完整性评测 |
| `risk_engine.py` | 风控核心逻辑（评分卡/预警规则/催收模板） |
| `mock_data.py` | mock 下游客户数据 |

## 效果评测

```bash
python evaluate.py   # 需先配置 .env
```

跑 3 个用例，评测维度：合规性（无违规词）、信息覆盖（含客户名/风险等级/额度）、完整性。
