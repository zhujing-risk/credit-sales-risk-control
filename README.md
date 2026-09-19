# 赊销风控 AI Agent（credit-sales-risk-control）

面向 B2B 赊销场景的 AI 风控 Agent 应用，演示「规则引擎兜底 + LLM 增强」架构。

## 核心能力
- **三模块 Agent**：客户画像 / 跑路预警 / 自动催收
- **Function Calling 工作流**：评分卡、预警规则封装为工具，由 LLM 按工作流编排调用
- **Prompt 设计与调优**：结构化 Prompt（角色 + 风控约束 + 输出格式）
- **效果评测**：合规性 / 信息覆盖 / 完整性三维评测

## 目录
- `demo/` — 完整代码，快速开始见 [demo/README.md](demo/README.md)
- `赊销风控模块_进销存SaaS合作方案.md` — 面向进销存 SaaS 的商业合作方案

## 技术栈
Python · Streamlit · OpenAI 兼容接口（DeepSeek / 豆包 / 通义）
