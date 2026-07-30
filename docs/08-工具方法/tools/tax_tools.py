"""税务工具方法（MTH-09-001 纳税审核方法 / MTH-09-002 税务风险评估工具）

提供一线高频、可参数化计算的税务工具：
- 税负率测算与预警（增值税、企业所得税）
- 分税种纳税调整（业务招待费、广告费、福利费、工会经费、职工教育经费、利息支出）
- 发票风险基础扫描
- 税务健康度综合评分

所有函数统一返回 :class:`base.ToolResult`。
注意：行业税负率 ``INDUSTRY_VAT_BENCHMARK`` 仅为**示例性预警参考值**，实际应用应以主管税务机关
公布的行业预警值为准，并支持通过参数覆盖。

涉及的税法比例（企业所得税税前扣除限额）：
- 业务招待费：按发生额 60% 扣除，最高不超过当年销售(营业)收入 5‰。
- 广告费和业务宣传费：一般企业不超过销售(营业)收入 15%（化妆品/医药/饮料制造 30%）。
- 职工福利费：不超过工资薪金总额 14%。
- 工会经费：不超过工资薪金总额 2%。
- 职工教育经费：不超过工资薪金总额 8%（超额可结转）。
"""

from __future__ import annotations

from .base import ToolResult, ToolValidationError, require_number, require_positive, require_non_negative

# 增值税税负率行业预警参考值（示例，非官方发布，可参数覆盖）
INDUSTRY_VAT_BENCHMARK = {
    "制造业": 0.035,
    "商贸零售": 0.015,
    "建筑安装": 0.030,
    "现代服务业": 0.030,
    "交通运输": 0.035,
    "房地产": 0.040,
    "软件开发": 0.045,
    "餐饮住宿": 0.020,
}


def calc_tax_burden_rate(tax_paid, revenue) -> ToolResult:
    """税负率测算：税额 ÷ 销售收入。

    用途：衡量单位销售收入承担的税额，是税负率预警的基础指标。

    Args:
        tax_paid: 已缴税额（非负）。
        revenue: 销售收入（须 > 0）。

    Returns:
        ToolResult: ``value``=税负率（小数，如 0.035 表示 3.5%）。
    """
    tax = require_non_negative("tax_paid", tax_paid)
    rev = require_positive("revenue", revenue)
    rate = tax / rev
    return ToolResult(
        method_id="MTH-09-001",
        method_name="税负率测算",
        value=round(rate, 6),
        inputs=dict(tax_paid=tax_paid, revenue=revenue),
        details=dict(tax_paid=tax, revenue=rev),
        notes="税负率 = 税额 / 销售收入。",
    )


def assess_vat_burden(vat_paid, revenue, benchmark=None, industry=None) -> ToolResult:
    """增值税税负率预警。

    用途：将企业增值税税负率与行业预警值比较，显著偏低提示虚开发票/隐匿收入风险。

    Args:
        vat_paid: 实缴增值税额（非负）。
        revenue: 应税销售收入（> 0）。
        benchmark: 行业预警税负率（小数）；不传则按 ``industry`` 取示例基准。
        industry: 行业名称，用于匹配示例基准（与 ``benchmark`` 二选一/互补）。

    Returns:
        ToolResult: ``value``=风险标记（"正常"/"关注"/"高风险"）；
            ``details``=实际税负率、基准、偏离度。
    """
    rate_res = calc_tax_burden_rate(vat_paid, revenue)
    rate = rate_res.value
    if benchmark is None and industry is not None:
        benchmark = INDUSTRY_VAT_BENCHMARK.get(industry)
    if benchmark is None:
        return ToolResult(
            method_id="MTH-09-002",
            method_name="增值税税负率预警",
            value="无法判定",
            inputs=dict(vat_paid=vat_paid, revenue=revenue, industry=industry),
            details=dict(actual_rate=rate),
            warnings=["未提供 benchmark 且 industry 不在示例表中，无法比较。"],
            notes="请补充行业预警值 benchmark 或有效的 industry。",
        )
    bench = require_positive("benchmark", benchmark)
    deviation = (rate - bench) / bench if bench else 0.0
    warnings: list[str] = []
    if rate < bench * 0.7:
        level = "高风险"
        warnings.append(f"实际税负率 {rate:.4f} 低于预警值 {bench:.4f} 的 70%，存在隐匿收入或进项异常风险。")
    elif rate < bench * 0.9:
        level = "关注"
        warnings.append(f"实际税负率 {rate:.4f} 低于预警值 {bench:.4f} 的 90%，建议复核。")
    else:
        level = "正常"
    return ToolResult(
        method_id="MTH-09-002",
        method_name="增值税税负率预警",
        value=level,
        inputs=dict(vat_paid=vat_paid, revenue=revenue, benchmark=bench, industry=industry),
        details=dict(actual_rate=rate, benchmark=bench, deviation=round(deviation, 4)),
        warnings=warnings,
        notes="低于预警值 70% 判为高风险；70%~90% 为关注；否则正常。行业基准为示例值。",
    )


def assess_income_tax_burden(income_tax_paid, pre_tax_profit, benchmark=None) -> ToolResult:
    """企业所得税税负率预警。

    用途：以所得税税负率（应纳所得税额 ÷ 利润总额）评估盈利企业的所得税负担合理性。

    Args:
        income_tax_paid: 应纳企业所得税额（非负）。
        pre_tax_profit: 利润总额（税前）。
        benchmark: 所得税税负率预警基准（默认 0.25，即法定税率附近）。

    Returns:
        ToolResult: ``value``=风险标记；``details``=实际税负率。
    """
    tax = require_non_negative("income_tax_paid", income_tax_paid)
    profit = require_number("pre_tax_profit", pre_tax_profit)
    bench = require_positive("benchmark", benchmark if benchmark is not None else 0.25)
    if profit <= 0:
        return ToolResult(
            method_id="MTH-09-002",
            method_name="企业所得税税负率预警",
            value="不适用",
            inputs=dict(income_tax_paid=income_tax_paid, pre_tax_profit=pre_tax_profit),
            warnings=["利润总额 ≤ 0，所得税税负率不适用（亏损或零利润）。"],
            notes="盈利企业方可计算所得税税负率。",
        )
    rate = tax / profit
    deviation = (rate - bench) / bench
    warnings: list[str] = []
    if rate < bench * 0.6:
        level = "高风险"
        warnings.append(f"所得税税负率 {rate:.4f} 显著低于基准 {bench:.4f}，关注纳税调整是否充分。")
    else:
        level = "正常"
    return ToolResult(
        method_id="MTH-09-002",
        method_name="企业所得税税负率预警",
        value=level,
        inputs=dict(income_tax_paid=income_tax_paid, pre_tax_profit=pre_tax_profit, benchmark=bench),
        details=dict(actual_rate=round(rate, 6), benchmark=bench, deviation=round(deviation, 4)),
        warnings=warnings,
        notes="显著低于基准 60% 判为高风险。基准默认 0.25（可覆盖）。",
    )


def calc_tax_adjustment(
    revenue,
    wages,
    entertainment,
    advertising,
    welfare,
    union_fund,
    education_fund,
    nonfin_interest_expense=None,
    fin_interest_rate=None,
    nonfin_loan_principal=None,
    advertising_ratio: float = 0.15,
) -> ToolResult:
    """分税种纳税调整测算（企业所得税税前扣除限额调增）。

    用途：按税法限额计算各项费用超标部分，汇总纳税调增额，用于纳税申报前复核。

    Args:
        revenue: 销售(营业)收入（> 0）。
        wages: 工资薪金总额（非负）。
        entertainment: 业务招待费实际发生额（非负）。
        advertising: 广告费和业务宣传费实际发生额（非负）。
        welfare: 职工福利费实际发生额（非负）。
        union_fund: 工会经费实际发生额（非负）。
        education_fund: 职工教育经费实际发生额（非负）。
        nonfin_interest_expense: 向非金融机构借款利息支出（可选）。
        fin_interest_rate: 同期同类金融企业贷款利率（可选，与上式配套）。
        nonfin_loan_principal: 非金融机构借款本金（可选）。
        advertising_ratio: 广告费扣除比例（默认 0.15，特殊行业可传 0.30）。

    Returns:
        ToolResult: ``value``=纳税调增合计；
            ``details``=各项限额/超标/调增明细。
    """
    rev = require_positive("revenue", revenue)
    wg = require_non_negative("wages", wages)

    # 业务招待费
    ent_limit = min(entertainment * 0.6, rev * 0.005)
    ent_adj = max(0.0, require_non_negative("entertainment", entertainment) - ent_limit)

    # 广告费和业务宣传费
    adv_limit = rev * advertising_ratio
    adv_adj = max(0.0, require_non_negative("advertising", advertising) - adv_limit)

    # 职工福利费
    wel_limit = wg * 0.14
    wel_adj = max(0.0, require_non_negative("welfare", welfare) - wel_limit)

    # 工会经费
    un_limit = wg * 0.02
    un_adj = max(0.0, require_non_negative("union_fund", union_fund) - un_limit)

    # 职工教育经费
    ed_limit = wg * 0.08
    ed_adj = max(0.0, require_non_negative("education_fund", education_fund) - ed_limit)

    # 非金融借款利息
    int_adj = 0.0
    if nonfin_interest_expense is not None:
        if fin_interest_rate is None or nonfin_loan_principal is None:
            raise ToolValidationError("非金融借款利息调整需同时提供 fin_interest_rate 与 nonfin_loan_principal")
        cap = require_non_negative("nonfin_loan_principal", nonfin_loan_principal) * require_non_negative(
            "fin_interest_rate", fin_interest_rate
        )
        int_adj = max(0.0, require_non_negative("nonfin_interest_expense", nonfin_interest_expense) - cap)

    items = {
        "业务招待费": dict(actual=entertainment, limit=round(ent_limit, 4), adjust=round(ent_adj, 4)),
        "广告费和业务宣传费": dict(actual=advertising, limit=round(adv_limit, 4), adjust=round(adv_adj, 4)),
        "职工福利费": dict(actual=welfare, limit=round(wel_limit, 4), adjust=round(wel_adj, 4)),
        "工会经费": dict(actual=union_fund, limit=round(un_limit, 4), adjust=round(un_adj, 4)),
        "职工教育经费": dict(actual=education_fund, limit=round(ed_limit, 4), adjust=round(ed_adj, 4)),
        "非金融借款利息": dict(actual=nonfin_interest_expense or 0, limit=round(cap, 4) if nonfin_interest_expense is not None else None, adjust=round(int_adj, 4)),
    }
    total = round(ent_adj + adv_adj + wel_adj + un_adj + ed_adj + int_adj, 4)
    return ToolResult(
        method_id="MTH-09-001",
        method_name="纳税调整测算",
        value=total,
        inputs=dict(
            revenue=revenue, wages=wages, entertainment=entertainment, advertising=advertising,
            welfare=welfare, union_fund=union_fund, education_fund=education_fund,
            advertising_ratio=advertising_ratio,
        ),
        details=dict(items=items),
        notes="返回各项税法限额内可扣金额及超标调增额，合计为应纳税所得额调增数。",
    )


def scan_invoice_risk(
    invoice_total,
    revenue,
    top_amount_ratio: float = None,
    threshold_ratio: float = 0.8,
) -> ToolResult:
    """发票风险基础扫描（比率法）。

    用途：以"开票金额/销售收入"比值做初步异常筛查；占比过高或过低均提示风险。

    Args:
        invoice_total: 开票总金额（非负）。
        revenue: 销售收入（> 0）。
        top_amount_ratio: 顶额（接近单张限额）发票金额占比（可选，0~1）。
        threshold_ratio: 判定阈值（默认 0.8）。

    Returns:
        ToolResult: ``value``=风险标记；``details``=开票收入比、顶额占比。
    """
    inv = require_non_negative("invoice_total", invoice_total)
    rev = require_positive("revenue", revenue)
    ratio = inv / rev
    warnings: list[str] = []
    if ratio > 1.2:
        level = "关注"
        warnings.append(f"开票金额/收入比 {ratio:.2f} 偏高，关注是否存在虚增收入或提前开票。")
    elif ratio < 0.3:
        level = "关注"
        warnings.append(f"开票金额/收入比 {ratio:.2f} 偏低，关注是否隐匿销售收入。")
    else:
        level = "正常"
    if top_amount_ratio is not None:
        tar = require_number("top_amount_ratio", top_amount_ratio)
        if tar > threshold_ratio:
            level = "高风险" if level != "高风险" else level
            warnings.append(f"顶额发票金额占比 {tar:.2f} 超过阈值 {threshold_ratio}，存在集中开票风险。")
    return ToolResult(
        method_id="MTH-09-002",
        method_name="发票风险扫描",
        value=level,
        inputs=dict(invoice_total=invoice_total, revenue=revenue, top_amount_ratio=top_amount_ratio),
        details=dict(invoice_revenue_ratio=round(ratio, 4), top_amount_ratio=top_amount_ratio),
        warnings=warnings,
        notes="为基础比率筛查，非完整风险模型；结合资金流、货物流进一步核实。",
    )


def tax_health_score(
    vat_burden_level: str = None,
    income_tax_level: str = None,
    invoice_level: str = None,
    adjustment_ratio: float = 0.0,
) -> ToolResult:
    """税务健康度综合评分（0~100）。

    用途：将多项税务风险信号汇总为单一健康度分数与等级，便于排序与跟踪。

    Args:
        vat_burden_level: 增值税税负预警结果（"正常"/"关注"/"高风险"）。
        income_tax_level: 所得税税负预警结果（同上）。
        invoice_level: 发票风险扫描结果（同上）。
        adjustment_ratio: 纳税调增额/利润总额（或收入）的比值（0~1，越大越差）。

    Returns:
        ToolResult: ``value``=健康度分数(0~100)；``details``=各项扣分与等级。
    """
    score = 100.0
    deductions = {}
    for name, level in (
        ("增值税税负", vat_burden_level),
        ("所得税税负", income_tax_level),
        ("发票风险", invoice_level),
    ):
        if level == "高风险":
            deductions[name] = 25
            score -= 25
        elif level == "关注":
            deductions[name] = 10
            score -= 10
        elif level == "不适用":
            deductions[name] = 0
        else:
            deductions[name] = 0
    adj = require_number("adjustment_ratio", adjustment_ratio)
    adj_deduction = min(20.0, max(0.0, adj * 100))
    score -= adj_deduction
    deductions["纳税调整"] = round(adj_deduction, 2)
    score = max(0.0, round(score, 1))
    grade = "优" if score >= 85 else "良" if score >= 70 else "中" if score >= 55 else "差"
    return ToolResult(
        method_id="MTH-09-002",
        method_name="税务健康度评分",
        value=score,
        inputs=dict(
            vat_burden_level=vat_burden_level, income_tax_level=income_tax_level,
            invoice_level=invoice_level, adjustment_ratio=adjustment_ratio,
        ),
        details=dict(deductions=deductions, grade=grade),
        notes="分数越高越健康；高风险项各扣 25，关注项各扣 10，纳税调整按比例最高扣 20。",
    )


if __name__ == "__main__":
    print(assess_vat_burden(180, 12000, industry="制造业").value)
    print(calc_tax_adjustment(
        revenue=10000, wages=2000, entertainment=120, advertising=1800,
        welfare=320, union_fund=40, education_fund=180,
    ).value)
