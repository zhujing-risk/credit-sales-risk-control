# -*- coding: utf-8 -*-
"""
赊销风控 Demo — Streamlit 演示界面（AI Agent 版）
================================================================
架构展示：「规则引擎兜底 + LLM 增强」
  - 结构化数据（信用分/预警信号/催收策略）= 工具层确定性代码产出；
  - 「AI 生成」按钮 = LLM 通过 Function Calling 调工具，把数据转成人话。

演示主线（30 秒）：
  ① 跑路预警页 → XX服饰 红色高危（规则信号）
  ② 点「AI 生成预警推送」→ LLM 生成通俗预警话术
  ③ 自动催收页 → 点「AI 生成催收话术」→ LLM 生成合规话术

运行：
  pip install streamlit openai
  复制 .env.example 为 .env 填 key（AI 功能需要，规则展示不需要）
  streamlit run app.py
"""

import streamlit as st

import config
from mock_data import get_customers
from risk_engine import build_profile, detect_runaway, build_collection
from agent import profile_agent, warning_agent, collection_agent

st.set_page_config(page_title="赊销风控 Demo", page_icon="🛡️", layout="wide")

st.title("🛡️ 赊销风控 · AI Agent 演示")
st.caption("「规则引擎兜底 + LLM 增强」—— 帮批发商判断谁能赊、有无跑路风险、怎么催收")

# ---------------- 侧边栏：LLM 配置状态 ----------------
with st.sidebar:
    st.subheader("⚙️ LLM 配置")
    if config.is_configured():
        st.success(f"已配置：{config.LLM_MODEL}")
    else:
        st.warning("未配置 LLM（AI 生成功能不可用，规则展示仍可用）")
        st.caption("复制 `.env.example` 为 `.env`，填入 API Key")


def ai_button(label: str, fn) -> None:
    """通用「AI 生成」按钮：点击才调用 LLM（避免每次 rerun 烧 token）。"""
    if st.button(label):
        if not config.is_configured():
            st.warning("未配置 LLM，请先在 `.env` 填入 API Key")
            return
        with st.spinner("AI 生成中…"):
            try:
                result = fn()
                st.markdown(
                    f"""<div style="background:#eef6ff;border-left:4px solid #3498db;padding:14px 16px;border-radius:6px;white-space:pre-wrap">{result}</div>""",
                    unsafe_allow_html=True,
                )
            except Exception as e:  # noqa: BLE001
                st.error(f"生成失败：{e}")


customers = get_customers()
name2cust = {c["name"]: c for c in customers}

tab_profile, tab_warning, tab_collect = st.tabs(
    ["① 下游客户画像", "② 跑路预警", "③ 自动催收"]
)

# ============================ Tab 1：客户画像 ============================
with tab_profile:
    st.subheader("下游客户画像")
    st.caption("工具层产出结构化信用数据（评分卡），LLM 转成人话摘要")

    selected = st.selectbox("选择下游客户", list(name2cust.keys()))
    c = name2cust[selected]
    p = build_profile(c)  # 工具：评分卡（确定性）

    col1, col2, col3 = st.columns(3)
    col1.metric("信用分", f"{p['credit_score']} / 100")
    col2.metric("风险标签", p["risk_label"])
    col3.metric("建议赊销上限", f"{p['suggest_credit']/10000:.1f} 万")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**评分明细（工具输出）**")
        max_scores = {"回款表现": 40, "经营稳定性": 30, "交易质量": 20, "异常信号": 10}
        for k, v in p["parts"].items():
            st.progress(v / max_scores[k], text=f"{k}: {v} / {max_scores[k]}")
    with col_b:
        st.markdown("**近 6 个月进货趋势**")
        st.line_chart({"进货金额(元)": c["monthly_purchase"]})

    st.divider()
    ai_button("🤖 AI 生成人话摘要", lambda: profile_agent(selected))

# ============================ Tab 2：跑路预警 ============================
with tab_warning:
    st.subheader("跑路预警")
    st.caption("工具层产出结构化风险信号（规则引擎），LLM 生成通俗预警推送")

    for c in customers:
        r = detect_runaway(c)  # 工具：规则引擎（确定性）
        if r["risk_level"] == "无风险":
            continue
        with st.expander(f"🚨 [{r['risk_level']}] {c['name']}", expanded=(r['risk_level'] == "高危")):
            for s in r["signals"]:
                st.markdown(f"• **{s['signal']}**（{s['level']}）：{s['desc']}")
            ai_button("🤖 AI 生成预警推送", lambda name=c["name"]: warning_agent(name))

# ============================ Tab 3：自动催收 ============================
with tab_collect:
    st.subheader("自动催收")
    st.caption("工具层产出分阶段催收策略，LLM 生成合规、得体的催收话术")

    col1, col2 = st.columns(2)
    sel_name = col1.selectbox("选择欠款客户", list(name2cust.keys()))
    overdue = col2.slider("逾期天数", 0, 30, 15)

    c = name2cust[sel_name]
    col = build_collection(c, overdue)  # 工具：分阶段策略（确定性）

    st.markdown("**催收阶段**：" + col["stage"] + "　|　**语气**：" + col["tone"])
    st.markdown(
        f"""<div style="background:#f0f2f6;border-left:4px solid #95a5a6;padding:10px 14px;border-radius:6px">
        模板兜底：{col['message']}</div>""",
        unsafe_allow_html=True,
    )
    st.divider()
    ai_button("🤖 AI 生成催收话术", lambda: collection_agent(sel_name, overdue))
