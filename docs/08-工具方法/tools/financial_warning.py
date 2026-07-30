"""财务预警模型计算工具（MTH-02-004 财务预警模型）

实现 Altman Z-Score（原始 / 私营 / 非制造）与周首华 F 分数模型，并提供行业阈值判定。
所有函数统一返回 :class:`base.ToolResult`。

模型与阈值依据（仅供方法参考，应用时应结合行业与企业实际）：
- Altman (1968) 原始 Z-Score，适用上市制造业：Z>2.99 安全；1.81~2.99 灰色；<1.81 危机。
- Altman 修订 Z'（私营公司，权益用账面价值）：>2.90 安全；1.23~2.90 灰色；<1.23 危机。
- Altman 修订 Z''（非制造私营）：>2.60 安全；1.10~2.60 灰色；<1.10 危机。
- 周首华等 (1996) F 分数（中国样本拓展）：F>0.3346 安全；<0.3346 高风险。

变量约定：
- X1 = 营运资金 / 总资产
- X2 = 留存收益 / 总资产
- X3 = 息税前利润(EBIT) / 总资产
- X4 = 权益市值(或账面价值) / 总负债
- X5 = 销售收入 / 总资产（Z'' 不使用）
"""

from __future__ import annotations

from typing import Literal

from .base import ToolResult, ToolValidationError, require_number, require_positive, require_non_negative


def _compute_ratios(
    working_capital,
    retained_earnings,
    ebit,
    sales,
    total_assets,
    equity_measure,
    total_liabilities,
    include_sales: bool,
):
    """计算 X1~X5 比率，统一做参数校验。

    Returns:
        dict: 含 X1~X5（X5 在 ``include_sales=False`` 时为 ``None``）及 ``warnings``。
    """
    ta = require_positive("total_assets", total_assets)
    tl = require_non_negative("total_liabilities", total_liabilities)
    wc = require_number("working_capital", working_capital)
    re_ = require_number("retained_earnings", retained_earnings)
    ebit_v = require_number("ebit", ebit)
    sales_v = require_number("sales", sales)
    eq = require_number("equity_measure", equity_measure)

    warnings: list[str] = []
    x1 = wc / ta
    x2 = re_ / ta
    x3 = ebit_v / ta
    if tl == 0:
        x4 = float("inf")
        warnings.append("总负债为 0，权益倍数(X4)视为无穷，结果偏向安全（模型对无负债主体失真）。")
    else:
        x4 = eq / tl
    x5 = (sales_v / ta) if include_sales else None
    return {"X1": x1, "X2": x2, "X3": x3, "X4": x4, "X5": x5, "warnings": warnings}


def calc_altman_z(
    working_capital,
    retained_earnings,
    ebit,
    market_value_equity,
    total_liabilities,
    sales,
    total_assets,
) -> ToolResult:
    """Altman 原始 Z-Score（1968，上市制造业）。

    用途：基于 5 个财务比率加权，预测企业短期内陷入财务危机的概率。

    Args:
        working_capital: 营运资金（流动资产-流动负债）。
        retained_earnings: 留存收益。
        ebit: 息税前利润。
        market_value_equity: 股东权益市值。
        total_liabilities: 总负债。
        sales: 销售收入。
        total_assets: 总资产（须 > 0）。

    Returns:
        ToolResult: ``value``=Z 值；``details``=X1~X5；``notes``=阈值含义。
    """
    r = _compute_ratios(
        working_capital, retained_earnings, ebit, sales, total_assets,
        market_value_equity, total_liabilities, include_sales=True,
    )
    x = {k: r[k] for k in ("X1", "X2", "X3", "X4", "X5")}
    z = 1.2 * x["X1"] + 1.4 * x["X2"] + 3.3 * x["X3"] + 0.6 * x["X4"] + 1.0 * x["X5"]
    return ToolResult(
        method_id="MTH-02-004",
        method_name="Altman Z-Score(原始)",
        value=round(z, 4),
        inputs=dict(
            working_capital=working_capital, retained_earnings=retained_earnings,
            ebit=ebit, market_value_equity=market_value_equity,
            total_liabilities=total_liabilities, sales=sales, total_assets=total_assets,
        ),
        details=x,
        warnings=r["warnings"],
        notes="Z>2.99 安全区；1.81~2.99 灰色区；<1.81 危机区。适用上市制造业。",
    )


def calc_altman_z_private(
    working_capital,
    retained_earnings,
    ebit,
    book_value_equity,
    total_liabilities,
    sales,
    total_assets,
) -> ToolResult:
    """Altman 修订 Z'（私营公司，权益用账面价值）。

    用途：对非上市（私营）企业，权益以账面价值替代市值，系数相应调整。

    Args: 同 :func:`calc_altman_z`，但 ``book_value_equity`` 为股东权益账面价值。

    Returns:
        ToolResult: ``value``=Z' 值；``details``=X1~X5。
    """
    r = _compute_ratios(
        working_capital, retained_earnings, ebit, sales, total_assets,
        book_value_equity, total_liabilities, include_sales=True,
    )
    x = {k: r[k] for k in ("X1", "X2", "X3", "X4", "X5")}
    z = 0.717 * x["X1"] + 0.847 * x["X2"] + 3.107 * x["X3"] + 0.420 * x["X4"] + 0.998 * x["X5"]
    return ToolResult(
        method_id="MTH-02-004",
        method_name="Altman Z'-Score(私营)",
        value=round(z, 4),
        inputs=dict(
            working_capital=working_capital, retained_earnings=retained_earnings,
            ebit=ebit, book_value_equity=book_value_equity,
            total_liabilities=total_liabilities, sales=sales, total_assets=total_assets,
        ),
        details=x,
        warnings=r["warnings"],
        notes="Z'>2.90 安全区；1.23~2.90 灰色区；<1.23 危机区。适用非上市企业。",
    )


def calc_altman_z_nonmanufacturing(
    working_capital,
    retained_earnings,
    ebit,
    book_value_equity,
    total_liabilities,
    total_assets,
) -> ToolResult:
    """Altman 修订 Z''（非制造业私营，剔除 X5）。

    用途：对非制造业私营主体，去掉与销售规模强相关的 X5。

    Args:
        working_capital / retained_earnings / ebit / book_value_equity /
        total_liabilities / total_assets: 含义同上，无需 ``sales``。

    Returns:
        ToolResult: ``value``=Z'' 值；``details``=X1~X4。
    """
    r = _compute_ratios(
        working_capital, retained_earnings, ebit, 0, total_assets,
        book_value_equity, total_liabilities, include_sales=False,
    )
    x = {k: r[k] for k in ("X1", "X2", "X3", "X4")}
    z = 6.56 * x["X1"] + 3.26 * x["X2"] + 6.72 * x["X3"] + 1.05 * x["X4"]
    return ToolResult(
        method_id="MTH-02-004",
        method_name="Altman Z''-Score(非制造)",
        value=round(z, 4),
        inputs=dict(
            working_capital=working_capital, retained_earnings=retained_earnings,
            ebit=ebit, book_value_equity=book_value_equity,
            total_liabilities=total_liabilities, total_assets=total_assets,
        ),
        details=x,
        warnings=r["warnings"],
        notes="Z''>2.60 安全区；1.10~2.60 灰色区；<1.10 危机区。适用非制造业。",
    )


def calc_f_score(
    working_capital,
    retained_earnings,
    ebit,
    equity_market_value,
    total_liabilities,
    sales,
    total_assets,
) -> ToolResult:
    """周首华等 (1996) F 分数模型（中国样本拓展）。

    用途：在 Altman 基础上引入现金流量因素，适配中国上市公司样本。

    公式：F = -0.1774 + 1.1091·X1 + 0.1074·X2 + 1.9271·X3 + 0.0302·X4 + 0.4961·X5。

    Args: 同 :func:`calc_altman_z`，``equity_market_value`` 为股东权益市值。

    Returns:
        ToolResult: ``value``=F 值；``details``=X1~X5。
    """
    r = _compute_ratios(
        working_capital, retained_earnings, ebit, sales, total_assets,
        equity_market_value, total_liabilities, include_sales=True,
    )
    x = {k: r[k] for k in ("X1", "X2", "X3", "X4", "X5")}
    f = (
        -0.1774
        + 1.1091 * x["X1"]
        + 0.1074 * x["X2"]
        + 1.9271 * x["X3"]
        + 0.0302 * x["X4"]
        + 0.4961 * x["X5"]
    )
    return ToolResult(
        method_id="MTH-02-004",
        method_name="F-Score(周首华)",
        value=round(f, 4),
        inputs=dict(
            working_capital=working_capital, retained_earnings=retained_earnings,
            ebit=ebit, equity_market_value=equity_market_value,
            total_liabilities=total_liabilities, sales=sales, total_assets=total_assets,
        ),
        details=x,
        warnings=r["warnings"],
        notes="原研究临界值 F>0.0274 安全（0.0274±0.0775 为不确定区）；扩展样本应用亦常取 0.3346 为临界值，详见 assess_f_score。",
    )


def assess_f_score(f_value: float, threshold: float = 0.0274) -> ToolResult:
    """将 F 分数归类为安全/风险区。

    用途：将连续的 F 值翻译为可读的风险区间。

    Args:
        f_value: F 分数（来自 :func:`calc_f_score`）。
        threshold: 临界值（默认 0.0274，即周首华等原研究；扩展样本应用可传 0.3346）。

    Returns:
        ToolResult: ``value``=风险等级（"安全"/"风险"/"不确定"）；
            ``details``=与阈值比较结果。
    """
    f = require_number("f_value", f_value)
    thr = require_number("threshold", threshold)
    if f > thr:
        level = "安全"
        cmp = f"F={f:.4f} > 临界值 {thr}"
    elif f < thr - 0.0775:
        level = "风险"
        cmp = f"F={f:.4f} < 临界值 {thr}（且低于不确定区下界 {thr - 0.0775:.4f}）"
    else:
        level = "不确定"
        cmp = f"F={f:.4f} 处于临界值 {thr} 的 ±0.0775 不确定区"
    return ToolResult(
        method_id="MTH-02-004",
        method_name="F分数风险判定",
        value=level,
        inputs=dict(f_value=f_value, threshold=threshold),
        details=dict(comparison=cmp, threshold=thr, band=(thr - 0.0775, thr + 0.0775)),
        notes=f"临界值 {thr}；±0.0775 为不确定区（仅当 threshold=0.0274 时适用该带宽）。",
    )


def assess_warning(
    model: Literal["original", "private", "nonmanufacturing"],
    z_value: float,
) -> ToolResult:
    """根据模型阈值将 Z 值归类为安全/灰色/危机区。

    用途：将连续 Z 值翻译为可读的风险区间，供一线快速判断。

    Args:
        model: 模型类型，取值 ``original`` / ``private`` / ``nonmanufacturing``。
        z_value: 对应模型的 Z（或 Z'/Z''）值。

    Returns:
        ToolResult: ``value``=风险等级（"安全"/"灰色"/"危机"/"未知"）；
            ``details``=阈值边界与比较结果。
    """
    rules = {
        "original": (1.81, 2.99, "上市制造业 Z"),
        "private": (1.23, 2.90, "私营 Z'"),
        "nonmanufacturing": (1.10, 2.60, "非制造 Z''"),
    }
    if model not in rules:
        raise ToolValidationError(
            f"model 仅支持 {list(rules)}，收到：{model!r}"
        )
    low, high, label = rules[model]
    z = require_number("z_value", z_value)
    if z == float("inf"):
        level = "安全"
        cmp = "无负债 -> 偏向安全"
    elif z > high:
        level = "安全"
        cmp = f"Z={z:.4f} > 上限 {high}"
    elif z >= low:
        level = "灰色"
        cmp = f"Z={z:.4f} 处于 [{low}, {high}]"
    else:
        level = "危机"
        cmp = f"Z={z:.4f} < 下限 {low}"
    return ToolResult(
        method_id="MTH-02-004",
        method_name="财务预警区间判定",
        value=level,
        inputs=dict(model=model, z_value=z_value),
        details=dict(lower=low, upper=high, label=label, comparison=cmp),
        notes=f"{label}模型阈值：安全>{high}；灰色[{low},{high}]；危机<{low}。",
    )


if __name__ == "__main__":
    # 演示：一家样本企业（单位：万元）
    res = calc_altman_z(
        working_capital=1200, retained_earnings=800, ebit=600,
        market_value_equity=5000, total_liabilities=3000,
        sales=9000, total_assets=10000,
    )
    print(res.method_name, "=", res.value, "|", res.notes)
    print("区间：", assess_warning("original", res.value).value)
