"""tools 包回归测试（F-08：纳入版本库的测试套件）

覆盖：
- 各模块 happy path
- 参数校验异常路径
- 审计发现的边界缺陷修复（F-01 零负债 inf、F-02 未知 level、F-03 DCF terminal_year）

运行：``python -m tools.test_tools``（无需 pytest）；亦可被 pytest 发现（函数名 test_*）。
"""

from __future__ import annotations

import math

from . import financial_warning as fw, tax_tools as tt, valuation as va, consolidation as co
from .base import ToolValidationError, require_in_range


def test_financial_warning_happy():
    r = fw.calc_altman_z(
        working_capital=1200, retained_earnings=800, ebit=600,
        market_value_equity=5000, total_liabilities=3000,
        sales=9000, total_assets=10000,
    )
    assert r.value is not None and r.value > 0
    assert fw.assess_warning("original", r.value).value in ("安全", "灰色", "危机")


def test_f01_zero_liability_not_inf():
    # 零负债：X4 无穷，calc_* 必须返回 value=None（而非 inf），且 assess_warning 优雅处理 inf
    cases = [
        dict(working_capital=1200, retained_earnings=800, ebit=600,
             market_value_equity=5000, total_liabilities=0, sales=9000, total_assets=10000),
        dict(working_capital=1200, retained_earnings=800, ebit=600,
             book_value_equity=5000, total_liabilities=0, sales=9000, total_assets=10000),
        dict(working_capital=1200, retained_earnings=800, ebit=600,
             book_value_equity=5000, total_liabilities=0, total_assets=10000),
    ]
    for kwargs in cases:
        res = fw.calc_altman_z(**kwargs) if "market_value_equity" in kwargs else (
            fw.calc_altman_z_nonmanufacturing(**kwargs) if "sales" not in kwargs
            else fw.calc_altman_z_private(**kwargs)
        )
        assert res.value is None, f"{kwargs} 应返回 None（无负债主体），实际 {res.value}"
        assert any("无穷" in w or "失真" in w for w in res.warnings)
    # 直接传 inf 给 assess_warning 不应抛异常
    ar = fw.assess_warning("original", float("inf"))
    assert ar.value == "安全"


def test_f_score_and_assess():
    r = fw.calc_f_score(
        working_capital=1200, retained_earnings=800, ebit=600,
        equity_market_value=5000, total_liabilities=3000,
        sales=9000, total_assets=10000,
    )
    assert r.value is not None
    assert fw.assess_f_score(r.value).value in ("安全", "风险", "不确定")


def test_tax_burden_and_adjustment():
    assert tt.calc_tax_burden_rate(350, 10000).value == 0.035
    res = tt.assess_vat_burden(180, 12000, industry="制造业")
    assert res.value in ("正常", "关注", "高风险", "无法判定")
    adj = tt.calc_tax_adjustment(
        revenue=10000, wages=2000, entertainment=120, advertising=1800,
        welfare=320, union_fund=40, education_fund=180,
    )
    assert adj.value >= 0
    assert "业务招待费" in adj.details["items"]


def test_f02_health_score_whitelist():
    # 合法值
    ok = tt.tax_health_score(vat_burden_level="正常", income_tax_level="高风险", invoice_level="关注")
    assert 0 <= ok.value <= 100
    # 非法值（误传"高危"）必须抛异常，不得静默忽略
    for bad in ("高危", "Error", 1, "safe"):
        try:
            tt.tax_health_score(vat_burden_level=bad)
            raise AssertionError(f"非法 level={bad!r} 应抛 ToolValidationError")
        except ToolValidationError:
            pass


def test_tax_validation():
    try:
        tt.calc_tax_burden_rate(10, 0)
        raise AssertionError("revenue=0 应抛 ToolValidationError")
    except ToolValidationError:
        pass


def test_f03_dcf_terminal_year_no_double_count():
    fcf = [100, 100, 100]
    # terminal_year=None（默认末期为 3）
    base = va.calc_dcf(fcf, discount_rate=0.1, terminal_value=500)
    # terminal_year=2（< 预测期）应被 clamp 到 3，结果与默认一致，且给出 warning
    clamped = va.calc_dcf(fcf, discount_rate=0.1, terminal_value=500, terminal_year=2)
    assert clamped.value == base.value, f"重复计数：{clamped.value} != {base.value}"
    assert any("重复计数" in w for w in clamped.warnings)
    # 正常 case
    r = va.calc_dcf([100, 120, 140, 160, 180], discount_rate=0.10, terminal_growth=0.02)
    assert r.value > 0


def test_valuation_basic():
    assert va.calc_capm(0.03, 1.2, 0.05).value == 0.09
    assert va.calc_wacc(0.7, 0.09, 0.3, 0.05, 0.25).value == 0.07425
    assert va.calc_income_approach(100, 0.1).value == 1000
    assert va.calc_market_approach(200, 5).value == 1000
    assert va.calc_physical_depreciation(1000, 4, 10).value == 400
    assert va.calc_cost_approach(1000, 200, 50, 30).value == 720


def test_consolidation():
    res = co.assess_consolidation_scope(direct_pct=60)
    assert res.value is True
    eq = co.build_equity_offset(parent_investment=800, subsidiary_equity=1000, nci_ratio=0.2)
    assert len(eq.value) >= 1
    un = co.build_unrealized_profit(transfer_price=100, cost=70, unsold_ratio=0.5, nci_ratio=0.2)
    assert un.value == 12.0  # (100-70)*0.5*(1-0.2)


def test_consolidation_validation():
    try:
        co.build_equity_offset(100, 100, nci_ratio=1.5)
        raise AssertionError("nci_ratio=1.5 应抛 ToolValidationError")
    except ToolValidationError:
        pass


# ---------- P2 低优先级项回归（F-09 / F-11 / PKG-05 / F-12 / VAL-02 / CON-01） ----------

def test_p2_f09_band_parameter():
    # band 参数可覆盖，不确定区宽度随阈值/模型变化
    r_default = fw.assess_f_score(0.05, threshold=0.0274)
    r_wide = fw.assess_f_score(0.05, threshold=0.0274, band=0.5)
    assert r_default.value in ("安全", "风险", "不确定")
    assert r_default.details["band"] == (round(0.0274 - 0.0775, 4), round(0.0274 + 0.0775, 4))
    assert r_wide.details["band"] == (round(0.0274 - 0.5, 4), round(0.0274 + 0.5, 4))
    # 取落入默认"风险"但宽 band"不确定"区的值，分类应不同
    f_gap = -0.2
    assert fw.assess_f_score(f_gap, threshold=0.0274).value == "风险"
    assert fw.assess_f_score(f_gap, threshold=0.0274, band=0.5).value == "不确定"


def test_p2_f11_altman_convergence():
    # 三个 Altman 变体经私有 _weighted_altman 收敛后，正常场景均返回有限 Z 值
    z = fw.calc_altman_z(working_capital=1200, retained_earnings=800, ebit=600,
                         market_value_equity=5000, total_liabilities=3000,
                         sales=9000, total_assets=10000)
    zp = fw.calc_altman_z_private(working_capital=1200, retained_earnings=800, ebit=600,
                                 book_value_equity=5000, total_liabilities=3000,
                                 sales=9000, total_assets=10000)
    zn = fw.calc_altman_z_nonmanufacturing(working_capital=1200, retained_earnings=800, ebit=600,
                                           book_value_equity=5000, total_liabilities=3000,
                                           total_assets=10000)
    for r in (z, zp, zn):
        assert r.value is not None and math.isfinite(r.value), f"{r.method_name} 应返回有限 Z"
    # 比率 details 已 round 至 6 位
    assert all(abs(r.details[k]) < 1e3 for r in (z, zp) for k in ("X1", "X2", "X3", "X4", "X5"))


def test_p2_pkg05_require_in_range_guard():
    # low > high 应抛异常（调用方配置错误）
    try:
        require_in_range("x", 5, low=10, high=1)
        raise AssertionError("low>high 应抛 ToolValidationError")
    except ToolValidationError:
        pass
    # 正常区间仍可用
    assert require_in_range("x", 5, low=1, high=10) == 5


def test_p2_f12_dcf_terminal_year_validation():
    # terminal_year < 1 应抛异常
    try:
        va.calc_dcf([100, 100, 100], discount_rate=0.1, terminal_year=0)
        raise AssertionError("terminal_year=0 应抛 ToolValidationError")
    except ToolValidationError:
        pass
    # 浮点整数应被接受并转 int
    r = va.calc_dcf([100, 100, 100], discount_rate=0.1, terminal_value=500, terminal_year=3.0)
    assert r.value > 0


def test_p2_val02_wacc_overweight_raises():
    # 权益+债务权重 > 1 应抛异常（资本来源超额配置）
    try:
        va.calc_wacc(weight_equity=0.7, cost_equity=0.09, weight_debt=0.7,
                     cost_debt=0.05, tax_rate=0.25)
        raise AssertionError("we+wd>1 应抛 ToolValidationError")
    except ToolValidationError:
        pass
    # 轻微不足 1 仅 warning
    w = va.calc_wacc(weight_equity=0.6, cost_equity=0.09, weight_debt=0.3,
                     cost_debt=0.05, tax_rate=0.25)
    assert any("≠ 1" in s for s in w.warnings)


def test_p2_con01_negative_gross_margin():
    # 收入 < 成本（负毛利）应预警
    r = co.build_intercompany_revenue_cost(revenue=100, cost=150, unsold_profit=10)
    assert any("毛利为负" in s for s in r.warnings)
    assert r.details["gross_margin"] < 0
    # 正常情形无此预警
    r2 = co.build_intercompany_revenue_cost(revenue=150, cost=100, unsold_profit=10)
    assert not any("毛利为负" in s for s in r2.warnings)


def _run_all():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = []
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failures.append((t.__name__, repr(e)))
            print(f"FAIL  {t.__name__}: {e}")
    print("-" * 40)
    print(f"共 {len(tests)} 项，通过 {len(tests) - len(failures)}，失败 {len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    _run_all()
