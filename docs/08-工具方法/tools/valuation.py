"""评估方法 · 快速估值与贬值速算（MTH-03-001 企业价值评估 / MTH-03-002 资产评估方法）

抽取评估方法中最常用、可参数化计算的片段，提供：
- CAPM 股权资本成本
- WACC 加权平均资本成本
- DCF 企业自由现金流折现
- 收益法（资本化法）
- 市场法（乘数法）
- 成本法及实体性/功能性/经济性贬值速算

所有对外函数统一返回 :class:`base.ToolResult`。利率/折现率均以小数传入（0.10 表示 10%）。
"""

from __future__ import annotations

from .base import ToolResult, ToolValidationError, require_number, require_positive, require_non_negative


def calc_capm(risk_free_rate, beta, market_risk_premium) -> ToolResult:
    """CAPM 股权资本成本：Ke = Rf + β·(Rm−Rf)。

    用途：测算股权投资者要求的必要报酬率，作为 DCF/WACC 的权益成本。

    Args:
        risk_free_rate: 无风险利率（小数）。
        beta: 系统性风险系数（非负数）。
        market_risk_premium: 市场风险溢价（小数）。

    Returns:
        ToolResult: ``value``=股权资本成本 Ke。
    """
    rf = require_number("risk_free_rate", risk_free_rate)
    b = require_non_negative("beta", beta)
    mrp = require_number("market_risk_premium", market_risk_premium)
    ke = rf + b * mrp
    return ToolResult(
        method_id="MTH-03-001",
        method_name="CAPM 股权资本成本",
        value=round(ke, 6),
        inputs=dict(risk_free_rate=risk_free_rate, beta=beta, market_risk_premium=market_risk_premium),
        notes="Ke = 无风险利率 + β × 市场风险溢价。",
    )


def calc_wacc(weight_equity, cost_equity, weight_debt, cost_debt, tax_rate) -> ToolResult:
    """WACC 加权平均资本成本：WACC = We·Ke + Wd·Kd·(1−T)。

    用途：作为企业整体（含债权）的折现率。

    Args:
        weight_equity: 权益权重（0~1）。
        cost_equity: 股权资本成本 Ke。
        weight_debt: 债务权重（0~1）。
        cost_debt: 税后债务成本 Kd（已含税盾前的利息率）。
        tax_rate: 所得税税率（0~1）。

    Returns:
        ToolResult: ``value``=WACC；``details``=权重合计校验。
    """
    we = require_number("weight_equity", weight_equity)
    ce = require_number("cost_equity", cost_equity)
    wd = require_number("weight_debt", weight_debt)
    cd = require_number("cost_debt", cost_debt)
    tr = require_number("tax_rate", tax_rate)
    if not (0 <= we <= 1 and 0 <= wd <= 1):
        raise ToolValidationError("权重应在 [0,1]")
    if not (0 <= tr <= 1):
        raise ToolValidationError("tax_rate 应在 [0,1]")
    wacc = we * ce + wd * cd * (1 - tr)
    warnings = []
    if abs(we + wd - 1.0) > 1e-6:
        warnings.append(f"权益权重+债务权重={we + wd:.4f} ≠ 1，已按给定权重直接计算（未归一化）。")
    return ToolResult(
        method_id="MTH-03-001",
        method_name="WACC 加权平均资本成本",
        value=round(wacc, 6),
        inputs=dict(weight_equity=weight_equity, cost_equity=cost_equity, weight_debt=weight_debt, cost_debt=cost_debt, tax_rate=tax_rate),
        details=dict(weight_sum=round(we + wd, 4)),
        warnings=warnings,
        notes="WACC = We·Ke + Wd·Kd·(1−T)。",
    )


def calc_dcf(free_cash_flows, discount_rate, terminal_value: float = 0.0, terminal_growth: float = None, terminal_year: int = None) -> ToolResult:
    """DCF 企业自由现金流折现。

    用途：将预测期各年企业自由现金流及终值折现，得到企业整体价值。

    Args:
        free_cash_flows: 预测期各年企业自由现金流列表（第 1 年对应 t=1）。
        discount_rate: 折现率（小数，通常取 WACC）。
        terminal_value: 直接给定终值（与 ``terminal_growth`` 二选一）。
        terminal_growth: 永续增长率（Gordon 模型：TV = FCF_n·(1+g)/(r−g)）。
        terminal_year: 终值对应年份（默认最后一期）。

    Returns:
        ToolResult: ``value``=企业价值（现值合计）；
            ``details``=各期现值、终值现值。
    """
    if not free_cash_flows:
        raise ToolValidationError("free_cash_flows 不能为空")
    r = require_number("discount_rate", discount_rate)
    if r <= 0:
        raise ToolValidationError("discount_rate 必须为正数")
    if terminal_growth is not None:
        g = require_number("terminal_growth", terminal_growth)
        if g >= r:
            raise ToolValidationError("永续增长率 g 必须小于折现率 r，否则模型不收敛。")
    fcf = [require_non_negative("free_cash_flows[i]", v) for v in free_cash_flows]
    pv_list = []
    for t, cf in enumerate(fcf, start=1):
        pv = cf / ((1 + r) ** t)
        pv_list.append(round(pv, 4))
    last_t = terminal_year if terminal_year is not None else len(fcf)
    if terminal_growth is not None:
        tv = fcf[-1] * (1 + terminal_growth) / (r - terminal_growth)
    else:
        tv = terminal_value
    pv_terminal = tv / ((1 + r) ** last_t)
    total = sum(pv_list) + pv_terminal
    return ToolResult(
        method_id="MTH-03-001",
        method_name="DCF 企业价值",
        value=round(total, 4),
        inputs=dict(free_cash_flows=free_cash_flows, discount_rate=discount_rate, terminal_value=terminal_value, terminal_growth=terminal_growth, terminal_year=terminal_year),
        details=dict(pv_periods=pv_list, terminal_value=round(tv, 4), pv_terminal=round(pv_terminal, 4)),
        notes="TV 可由 Gordon 模型或外部给定；r 须 > g。",
    )


def calc_income_approach(net_operating_income, capitalization_rate) -> ToolResult:
    """收益法（资本化法）：V = NOI / r。

    用途：以稳定收益除以资本化率快速估算价值（适用于收益稳定的资产/企业）。

    Args:
        net_operating_income: 年净收益（NOI，非负）。
        capitalization_rate: 资本化率（小数，>0）。

    Returns:
        ToolResult: ``value``=评估价值。
    """
    noi = require_non_negative("net_operating_income", net_operating_income)
    r = require_positive("capitalization_rate", capitalization_rate)
    v = noi / r
    return ToolResult(
        method_id="MTH-03-001",
        method_name="收益法(资本化)",
        value=round(v, 4),
        inputs=dict(net_operating_income=net_operating_income, capitalization_rate=capitalization_rate),
        notes="V = 年净收益 / 资本化率。",
    )


def calc_market_approach(target_metric, multiplier) -> ToolResult:
    """市场法（乘数法）：V = 指标 × 乘数。

    用途：以可比交易/上市公司的财务乘数（P/E、P/B、EV/EBITDA 等）快速估算价值。

    Args:
        target_metric: 被评估对象的对应财务指标（如净利润、净资产、EBITDA）。
        multiplier: 选用的市场乘数。

    Returns:
        ToolResult: ``value``=评估价值。
    """
    m = require_number("target_metric", target_metric)
    mult = require_number("multiplier", multiplier)
    v = m * mult
    return ToolResult(
        method_id="MTH-03-001",
        method_name="市场法(乘数)",
        value=round(v, 4),
        inputs=dict(target_metric=target_metric, multiplier=multiplier),
        notes="V = 财务指标 × 市场乘数；乘数须取自可比交易/上市公司。",
    )


def calc_physical_depreciation(replacement_cost, age, total_life) -> ToolResult:
    """实体性贬值速算（年限法）：贬值 = RC × 已使用年限 / 总使用年限。

    Args:
        replacement_cost: 重置成本（非负）。
        age: 已使用年限（非负）。
        total_life: 总使用年限（>0）。

    Returns:
        ToolResult: ``value``=实体性贬值额。
    """
    rc = require_non_negative("replacement_cost", replacement_cost)
    a = require_non_negative("age", age)
    tl = require_positive("total_life", total_life)
    dep = rc * a / tl
    return ToolResult(
        method_id="MTH-03-002",
        method_name="实体性贬值(年限法)",
        value=round(dep, 4),
        inputs=dict(replacement_cost=replacement_cost, age=age, total_life=total_life),
        details=dict(rate=round(a / tl, 4)),
        notes="贬值率 = 已使用年限 / 总使用年限。",
    )


def calc_functional_obsolescence(excess_annual_cost, discount_rate, remaining_life) -> ToolResult:
    """功能性贬值速算：超额运营成本现值 = 年超额成本 × 年金现值系数。

    Args:
        excess_annual_cost: 年超额运营成本（税后，非负）。
        discount_rate: 折现率（小数，>0）。
        remaining_life: 剩余使用年限（>0）。

    Returns:
        ToolResult: ``value``=功能性贬值额。
    """
    eac = require_non_negative("excess_annual_cost", excess_annual_cost)
    r = require_positive("discount_rate", discount_rate)
    n = require_positive("remaining_life", remaining_life)
    annuity = (1 - (1 + r) ** (-n)) / r
    dep = eac * annuity
    return ToolResult(
        method_id="MTH-03-002",
        method_name="功能性贬值(超额成本现值)",
        value=round(dep, 4),
        inputs=dict(excess_annual_cost=excess_annual_cost, discount_rate=discount_rate, remaining_life=remaining_life),
        details=dict(annuity_factor=round(annuity, 4)),
        notes="贬值 = 年超额运营成本 × 年金现值系数。",
    )


def calc_economic_obsolescence(replacement_cost, utilization_before, utilization_after) -> ToolResult:
    """经济性贬值速算：贬值 = RC × (1 − 利用率后 / 利用率前)。

    Args:
        replacement_cost: 重置成本（非负）。
        utilization_before: 资产满负荷利用率（0~1）。
        utilization_after: 现状利用率（0~1）。

    Returns:
        ToolResult: ``value``=经济性贬值额。
    """
    rc = require_non_negative("replacement_cost", replacement_cost)
    ub = require_number("utilization_before", utilization_before)
    ua = require_number("utilization_after", utilization_after)
    if not (0 < ub <= 1 and 0 <= ua <= 1):
        raise ToolValidationError("利用率应在 (0,1] 与 [0,1] 区间")
    dep = rc * (1 - ua / ub)
    return ToolResult(
        method_id="MTH-03-002",
        method_name="经济性贬值(利用率法)",
        value=round(dep, 4),
        inputs=dict(replacement_cost=replacement_cost, utilization_before=utilization_before, utilization_after=utilization_after),
        details=dict(utilization_ratio=round(ua / ub, 4)),
        notes="贬值 = 重置成本 × (1 − 现状利用率/满负荷利用率)。",
    )


def calc_cost_approach(replacement_cost, physical_depr, functional_depr, economic_depr) -> ToolResult:
    """成本法：评估值 = 重置成本 − 实体性 − 功能性 − 经济性贬值。

    Args:
        replacement_cost: 重置成本（非负）。
        physical_depr: 实体性贬值额（非负）。
        functional_depr: 功能性贬值额（非负）。
        economic_depr: 经济性贬值额（非负）。

    Returns:
        ToolResult: ``value``=评估值；``details``=各项贬值与贬值率。
    """
    rc = require_non_negative("replacement_cost", replacement_cost)
    pd = require_non_negative("physical_depr", physical_depr)
    fd = require_non_negative("functional_depr", functional_depr)
    ed = require_non_negative("economic_depr", economic_depr)
    total_depr = pd + fd + ed
    value = max(0.0, rc - total_depr)
    return ToolResult(
        method_id="MTH-03-002",
        method_name="成本法",
        value=round(value, 4),
        inputs=dict(replacement_cost=replacement_cost, physical_depr=physical_depr, functional_depr=functional_depr, economic_depr=economic_depr),
        details=dict(total_depreciation=round(total_depr, 4), depreciation_rate=round(total_depr / rc, 4) if rc else 0),
        notes="评估值 = 重置成本 − 三类贬值合计；不得低于 0。",
    )


if __name__ == "__main__":
    print(calc_dcf([100, 120, 140, 160, 180], discount_rate=0.10, terminal_growth=0.02).value)
    print(calc_cost_approach(1000, 200, 50, 30).value)
