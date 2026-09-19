# -*- coding: utf-8 -*-
"""
赊销风控 Demo — 核心风控引擎
================================================================
三大模块（对应给 SaaS 老板看的三个功能）：

  1. build_profile      下游赊销客户画像（信用分 + 画像标签 + 建议额度）
  2. detect_runaway     跑路预警（异常信号检测 + 风险分级）
  3. build_collection   自动催收（分阶段话术生成）

说明：
  - 骨架阶段用「规则 + 模板」实现，保证离线可跑；
  - 预留 LLM_ENABLED 开关 + _llm_* 接口，接入 Claude API 后，
    话术 / 画像摘要 / 预警话术会从「模板」升级为「LLM 生成的自然语言」。
"""

import statistics

# ---------------------------------------------------------------------------
# LLM 开关：设为 True 并填入 API Key 后，启用 LLM 增强（骨架阶段保持 False）
# ---------------------------------------------------------------------------
LLM_ENABLED = False
LLM_API_KEY = None  # TODO: 接入 Claude API 时填入


def _llm_generate(prompt: str) -> str:
    """LLM 接口占位：接入 Claude API 后替换为真实调用。"""
    # TODO: 真实实现示例（接入 Claude）：
    #   import anthropic
    #   client = anthropic.Anthropic(api_key=LLM_API_KEY)
    #   return client.messages.create(model="claude-fable-5-1", ...).content[0].text
    raise NotImplementedError("LLM 未启用，请使用模板模式（LLM_ENABLED=False）")


# ===========================================================================
# 模块 1：下游赊销客户画像
# ===========================================================================

def _subscore_repayment(c):
    """回款表现 40 分：按拖欠次数扣分，每次扣 8 分。"""
    return max(0, 40 - c["overdue_count"] * 8)


def _subscore_stability(c):
    """经营稳定性 30 分：按进货量波动（变异系数）扣分。"""
    amounts = c["monthly_purchase"]
    mean = statistics.mean(amounts)
    if mean == 0:
        return 0
    cv = statistics.pstdev(amounts) / mean  # 变异系数：标准差/均值
    # cv<=0.05 满分，之后每 0.05 扣 5 分
    return max(0, round(30 - (cv - 0.05) / 0.05 * 5))


def _subscore_quality(c):
    """交易质量 20 分：按退货率扣分。"""
    return max(0, round(20 - c["return_rate"] * 200))


def _subscore_anomaly(c):
    """异常信号 10 分：外部风险直接扣满，近期骤降/激增各扣 5 分。"""
    score = 10
    if c["ext_risk"]:
        score -= 10
    amounts = c["monthly_purchase"]
    base = statistics.mean(amounts[:-1]) if len(amounts) > 1 else amounts[0]
    latest = amounts[-1]
    if base > 0 and latest < base * 0.5:      # 进货量骤降
        score -= 5
    if base > 0 and latest > base * 1.8:      # 清仓式激增
        score -= 5
    return max(0, score)


def build_profile(c):
    """
    生成客户画像：
      - credit_score  信用分（0~100）
      - risk_label    风险标签（优质/稳定/警惕/危险）
      - suggest_credit 建议赊销额度（元）
      - summary       人话画像摘要（模板版，LLM 版待接入）
    """
    parts = {
        "回款表现": _subscore_repayment(c),
        "经营稳定性": _subscore_stability(c),
        "交易质量": _subscore_quality(c),
        "异常信号": _subscore_anomaly(c),
    }
    credit_score = round(sum(parts.values()))

    # 风险标签
    if credit_score >= 85:
        risk_label = "优质"
    elif credit_score >= 70:
        risk_label = "稳定"
    elif credit_score >= 55:
        risk_label = "警惕"
    else:
        risk_label = "危险"

    # 建议赊销额度：以当前赊销余额为锚，按分数线性缩放
    suggest_credit = int(c["total_credit"] * credit_score / 100)

    # 人话摘要（模板版）
    if LLM_ENABLED:
        summary = _llm_generate(f"用一句话给服装批发商描述下游客户 {c['name']} 的信用情况")
    else:
        status = "从不拖欠" if c["overdue_count"] == 0 else f"近3个月拖欠{c['overdue_count']}次"
        summary = (
            f"{c['name']}：{c['years']}年老客户，主营{c['category']}，"
            f"{status}，建议赊销上限 {suggest_credit/10000:.1f} 万"
        )

    return {
        "credit_score": credit_score,
        "risk_label": risk_label,
        "suggest_credit": suggest_credit,
        "summary": summary,
        "parts": parts,
    }


# ===========================================================================
# 模块 2：跑路预警
# ===========================================================================

def detect_runaway(c):
    """
    检测跑路风险信号，返回信号列表。
    每条信号: {level, signal, desc}
      level: 高危/中危/低危
    """
    signals = []
    amounts = c["monthly_purchase"]
    base = statistics.mean(amounts[:-1]) if len(amounts) > 1 else amounts[0]
    latest = amounts[-1]

    # 信号1：进货量骤降（↓50%以上）→ 下游生意崩了/要关门
    if base > 0 and latest < base * 0.5:
        drop_pct = round((1 - latest / base) * 100)
        signals.append({
            "level": "高危",
            "signal": "进货量骤降",
            "desc": f"近1月进货 {latest/10000:.1f}万，较前几月均值下降 {drop_pct}%",
        })

    # 信号2：清仓式拿货（激增80%以上）+ 有拖欠 → 跑路前套现
    if base > 0 and latest > base * 1.8 and c["overdue_count"] > 0:
        signals.append({
            "level": "高危",
            "signal": "清仓式套现",
            "desc": "最后1月进货激增且有拖欠，疑似跑路前大量套货",
        })

    # 信号3：拖欠次数多 → 资金链紧张
    if c["overdue_count"] >= 2:
        signals.append({
            "level": "中危",
            "signal": "账期恶化",
            "desc": f"近3个月拖欠 {c['overdue_count']} 次，回款持续恶化",
        })

    # 信号4：外部风险（工商异常/司法被执行等）
    if c["ext_risk"]:
        signals.append({
            "level": "中危",
            "signal": "外部风险",
            "desc": f"命中外部风险：{c['ext_risk']}",
        })

    # 信号5：退货率异常
    if c["return_rate"] > 0.15:
        signals.append({
            "level": "低危",
            "signal": "退货率偏高",
            "desc": f"退货率 {c['return_rate']*100:.0f}%，异常偏高",
        })

    # 综合风险等级：取最高危信号
    level_order = {"高危": 3, "中危": 2, "低危": 1}
    risk_level = "无风险"
    for s in signals:
        if level_order.get(s["level"], 0) > level_order.get(risk_level, 0):
            risk_level = s["level"]

    return {"risk_level": risk_level, "signals": signals}


# ===========================================================================
# 模块 3：自动催收
# ===========================================================================

# 分阶段催收策略：逾期天数 → (阶段, 话术模板)
# 模板变量：{name} 客户名, {amount} 金额, {days} 逾期天数
_COLLECTION_STAGES = [
    (0,   "到期提醒", "张哥，{name}这批货款 {amount} 今天到期了，方便的话安排一下哈"),
    (3,   "温和催收", "张哥，{name}那笔款超了 {days} 天，是不是周转有困难？咱们商量下"),
    (7,   "升级催收", "{name}，货款已逾期 {days} 天，麻烦本周内结清，不然我这边也难周转"),
    (15,  "严肃催收", "{name}，已多次提醒，请尽快处理 {amount} 货款，否则我这边要走正式流程了"),
]


def build_collection(c, overdue_days):
    """
    根据逾期天数生成催收话术。
    overdue_days: 逾期天数（0=当天到期）
    返回: {stage, tone, message}
    """
    _, stage, template = _COLLECTION_STAGES[0]
    for s, stg, t in _COLLECTION_STAGES:
        if overdue_days >= s:
            stage, template = stg, t

    # 根据客户关系调整语气（老客户用熟人口吻）
    if LLM_ENABLED:
        message = _llm_generate(
            f"给欠款客户{c['name']}写一句逾期{overdue_days}天的催收话术，金额{c['total_credit']}元，语气得体但有力度"
        )
    else:
        message = template.format(
            name=c["name"],
            amount=f"{c['total_credit']/10000:.1f}万",
            days=overdue_days,
        )

    # 语气标签（老熟人 vs 一般）
    tone = "熟人口吻" if c["years"] >= 3 else "正式口吻"
    return {"stage": stage, "tone": tone, "message": message}


if __name__ == "__main__":
    # 快速自测：打印每个客户的画像 + 预警 + 一句催收
    from mock_data import get_customers
    for c in get_customers():
        p = build_profile(c)
        r = detect_runaway(c)
        col = build_collection(c, overdue_days=7)
        print(f"\n【{c['name']}】 信用分={p['credit_score']} 标签={p['risk_label']} 额度={p['suggest_credit']}")
        print(f"  风险等级={r['risk_level']} 信号数={len(r['signals'])}")
        print(f"  催收({col['stage']}/{col['tone']}): {col['message']}")
