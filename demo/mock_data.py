# -*- coding: utf-8 -*-
"""
赊销风控 Demo — mock 数据
================================================================
模拟「进销存 SaaS」里能拿到的下游客户经营数据。

关键：数据里埋了 3 类「异常客户」，用来现场演示跑路预警：
  - XX服饰      : 进货量骤降 + 拖欠 → 即将跑路（高危）
  - 李记鞋业    : 最后一个月清仓式大量拿货 → 跑路前套现（高危）
  - 王姐杂货    : 稳定但命中外部司法风险（中危）
其余为优质/普通客户，用于对照。

字段说明（全部模拟 SaaS 存量数据）：
  name             客户名称
  years            经营年限（年）
  category         主营品类
  monthly_purchase 最近6个月进货金额（元），下标0最旧 → 5最新
  overdue_count    近3个月拖欠货款次数
  total_credit     当前赊销余额（元）
  return_rate      退货率（0~1）
  ext_risk         外部风险标记（工商异常/司法被执行等，None=无）
"""

from datetime import datetime


def get_month_labels(n=6):
    """生成最近 n 个月的 'YYYY-MM' 标签，最新的在最后（纯标准库实现）。"""
    now = datetime.now()
    labels = []
    year, month = now.year, now.month
    for i in range(n - 1, -1, -1):
        total = year * 12 + (month - 1) - i  # 换算成「绝对月」再回退 i 个月
        y, m = divmod(total, 12)
        labels.append(f"{y}-{m + 1:02d}")
    return labels


def get_customers():
    """返回下游赊销客户列表（mock）。"""
    return [
        {
            "name": "张老板服饰",
            "years": 3,
            "category": "女装",
            # 稳定进货，从不拖欠 → 优质客户
            "monthly_purchase": [80000, 82000, 85000, 83000, 86000, 85000],
            "overdue_count": 0,
            "total_credit": 80000,
            "return_rate": 0.02,
            "ext_risk": None,
        },
        {
            "name": "XX服饰",
            "years": 1.5,
            "category": "男装",
            # 进货量从 5万 骤降到 8千（↓80%）+ 拖欠3笔 → 即将跑路（高危）
            "monthly_purchase": [50000, 48000, 45000, 40000, 20000, 8000],
            "overdue_count": 3,
            "total_credit": 120000,
            "return_rate": 0.08,
            "ext_risk": None,
        },
        {
            "name": "李记鞋业",
            "years": 2,
            "category": "鞋靴",
            # 最后一个月进货激增（2.5万→7万），且已有拖欠 → 清仓套现（高危）
            "monthly_purchase": [30000, 32000, 28000, 25000, 26000, 70000],
            "overdue_count": 1,
            "total_credit": 90000,
            "return_rate": 0.05,
            "ext_risk": None,
        },
        {
            "name": "王姐杂货",
            "years": 5,
            "category": "日用百货",
            # 经营稳定，但命中外部司法风险（中危）
            "monthly_purchase": [15000, 16000, 15000, 14000, 15000, 14000],
            "overdue_count": 0,
            "total_credit": 20000,
            "return_rate": 0.03,
            "ext_risk": "司法被执行",
        },
        {
            "name": "赵总童装",
            "years": 4,
            "category": "童装",
            # 经营稳定，仅拖欠1次 → 普通客户
            "monthly_purchase": [40000, 42000, 38000, 41000, 39000, 40000],
            "overdue_count": 1,
            "total_credit": 60000,
            "return_rate": 0.04,
            "ext_risk": None,
        },
    ]


if __name__ == "__main__":
    # 直接运行本文件可快速查看数据
    print("月份标签:", get_month_labels())
    for c in get_customers():
        print(f"{c['name']:8s} 进货={c['monthly_purchase']} 拖欠={c['overdue_count']} 余额={c['total_credit']}")
