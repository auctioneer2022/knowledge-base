"""合并报表分析工具（MTH-02-005 合并报表分析方法）

提供合并范围判断，以及常见抵销分录的结构化构建：
- 长期股权投资与所有者权益抵销
- 内部债权债务抵销
- 内部交易（收入/成本/存货未实现损益）抵销
- 未实现内部销售损益抵销

返回的抵销分录以 :class:`OffsetEntry` 结构描述，便于直接生成工作底稿。
所有对外函数统一返回 :class:`base.ToolResult`。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .base import ToolResult, ToolValidationError, require_number, require_non_negative, require_positive


@dataclass
class OffsetEntry:
    """一条抵销分录的结构化描述。

    Attributes:
        summary: 业务摘要（如"长期股权投资与所有者权益抵销"）。
        debits: 借方列表，元素为 ``(科目, 金额)``。
        credits: 贷方列表，元素为 ``(科目, 金额)``。
    """

    summary: str
    debits: List[tuple] = field(default_factory=list)
    credits: List[tuple] = field(default_factory=list)


def assess_consolidation_scope(
    direct_pct: float,
    indirect_pct: float = 0.0,
    voting_pct: float | None = None,
    substantive_control: bool = False,
) -> ToolResult:
    """合并范围判断（控制三要素：权力、可变回报、运用权力影响回报）。

    用途：依据持股比例与实质控制因素，判定子公司是否纳入合并范围。

    Args:
        direct_pct: 直接持股比例（0~100，百分数，如 60 表示 60%）。
        indirect_pct: 通过其他子公司间接持股比例（默认 0）。
        voting_pct: 实际表决权比例（可选，区别于直接持股）。
        substantive_control: 是否构成实质控制（如协议控制、半数以下但主导经营）。

    Returns:
        ToolResult: ``value``=是否纳入合并（bool）；
            ``details``=有效持股比例与判定依据。
    """
    dp = require_number("direct_pct", direct_pct)
    ip = require_non_negative("indirect_pct", indirect_pct)
    effective = dp + ip
    vp = require_number("voting_pct", voting_pct) if voting_pct is not None else None
    consolidated = (effective > 50) or (vp is not None and vp > 50) or substantive_control
    basis = []
    if effective > 50:
        basis.append(f"有效持股 {effective:.2f}% > 50%")
    if vp is not None and vp > 50:
        basis.append(f"表决权 {vp:.2f}% > 50%")
    if substantive_control:
        basis.append("存在实质控制安排")
    if not basis:
        basis.append(f"有效持股 {effective:.2f}% ≤ 50% 且无实质控制")
    return ToolResult(
        method_id="MTH-02-005",
        method_name="合并范围判断",
        value=consolidated,
        inputs=dict(direct_pct=direct_pct, indirect_pct=indirect_pct, voting_pct=voting_pct, substantive_control=substantive_control),
        details=dict(effective_pct=round(effective, 4), voting_pct=vp, basis=basis),
        notes="控制 = 权力 + 可变回报 + 能运用权力影响回报；任一满足即纳入合并。",
    )


def build_equity_offset(
    parent_investment: float,
    subsidiary_equity: float,
    nci_ratio: float,
) -> ToolResult:
    """长期股权投资与所有者权益抵销分录构建。

    用途：抵销母公司长期股权投资与子公司所有者权益，确认商誉与少数股东权益。

    Args:
        parent_investment: 母公司对子公司长期股权投资账面价值（非负）。
        subsidiary_equity: 子公司所有者权益账面价值（非负）。
        nci_ratio: 少数股东持股比例（0~1，小数）。

    Returns:
        ToolResult: ``value``=List[OffsetEntry]；``details``=商誉/少数股东权益金额。
    """
    inv = require_non_negative("parent_investment", parent_investment)
    eq = require_non_negative("subsidiary_equity", subsidiary_equity)
    nci = require_number("nci_ratio", nci_ratio)
    if not (0 <= nci <= 1):
        raise ToolValidationError(f"nci_ratio 应在 [0,1]，收到：{nci}")
    parent_ratio = 1 - nci
    nci_equity = eq * nci
    goodwill = inv - eq * parent_ratio
    entries: List[OffsetEntry] = []
    if goodwill > 0:
        entries.append(OffsetEntry(
            summary="长期股权投资与所有者权益抵销（含商誉）",
            debits=[("子公司所有者权益", round(eq, 2)), ("商誉", round(goodwill, 2))],
            credits=[("长期股权投资", round(inv, 2)), ("少数股东权益", round(nci_equity, 2))],
        ))
    else:
        entries.append(OffsetEntry(
            summary="长期股权投资与所有者权益抵销",
            debits=[("子公司所有者权益", round(eq, 2))],
            credits=[("长期股权投资", round(inv, 2)), ("少数股东权益", round(nci_equity, 2))],
        ))
        if goodwill < 0:
            entries[0].debits.append(("营业外收入/负商誉", round(-goodwill, 2)))
    return ToolResult(
        method_id="MTH-02-005",
        method_name="权益抵销分录",
        value=entries,
        inputs=dict(parent_investment=parent_investment, subsidiary_equity=subsidiary_equity, nci_ratio=nci_ratio),
        details=dict(goodwill=round(goodwill, 4), nci_equity=round(nci_equity, 4)),
        notes="当长期股权投资 > 应享权益份额时确认商誉；后者大于前者为廉价购买（负商誉）。",
    )


def build_intercompany_payable_receivable(receivable: float, payable: float) -> ToolResult:
    """内部债权债务抵销（应收账款与应付账款等）。

    用途：抵销集团内部因交易形成的应收应付，避免重复计量。

    Args:
        receivable: 内部应收账款余额（非负）。
        payable: 内部应付账款余额（非负）。

    Returns:
        ToolResult: ``value``=List[OffsetEntry]（按较小额全额抵销，不等提示预警）。
    """
    rec = require_non_negative("receivable", receivable)
    pay = require_non_negative("payable", payable)
    offset = min(rec, pay)
    warnings: list[str] = []
    if rec != pay:
        warnings.append(f"往来余额不一致（应收 {rec} / 应付 {pay}），按较小额 {offset} 抵销，差额需核查。")
    entries = [OffsetEntry(
        summary="内部债权债务抵销",
        debits=[("应付账款", round(offset, 2))],
        credits=[("应收账款", round(offset, 2))],
    )]
    return ToolResult(
        method_id="MTH-02-005",
        method_name="内部往来抵销",
        value=entries,
        inputs=dict(receivable=receivable, payable=payable),
        details=dict(offset=round(offset, 4)),
        warnings=warnings,
        notes="内部往来应全额抵销；余额不等提示未达账项或入账差异。",
    )


def build_intercompany_revenue_cost(revenue: float, cost: float, unsold_profit: float = 0.0) -> ToolResult:
    """内部交易收入成本及存货未实现损益抵销。

    用途：抵销内部销售收入与成本，并将未实现内部销售损益从存货中剔除。

    Args:
        revenue: 内部销售收入（非负）。
        cost: 内部销售成本（非负）。
        unsold_profit: 期末未实现内部损益中归属于集团的部分（默认 0，非负）。

    Returns:
        ToolResult: ``value``=List[OffsetEntry]。
    """
    rev = require_non_negative("revenue", revenue)
    cst = require_non_negative("cost", cost)
    up = require_non_negative("unsold_profit", unsold_profit)
    gross_margin = round(rev - cst, 4)
    warnings: list[str] = []
    if gross_margin < 0:
        warnings.append(f"内部交易毛利为负（收入 {rev} < 成本 {cst}），请核查内部定价或入账数据。")
    entries = [OffsetEntry(
        summary="内部交易收入成本抵销",
        debits=[("营业收入", round(rev, 2))],
        credits=[("营业成本", round(cst, 2))],
    )]
    if up > 0:
        entries.append(OffsetEntry(
            summary="存货中未实现内部损益抵销",
            debits=[("营业成本", round(up, 2))],
            credits=[("存货", round(up, 2))],
        ))
    return ToolResult(
        method_id="MTH-02-005",
        method_name="内部交易抵销",
        value=entries,
        inputs=dict(revenue=revenue, cost=cost, unsold_profit=unsold_profit),
        details=dict(gross_margin=gross_margin, unsold_profit=round(up, 4)),
        warnings=warnings,
        notes="未实现损益 = 内部毛利 × 期末未售比例；需结合 NCI 分摊。",
    )


def build_unrealized_profit(transfer_price: float, cost: float, unsold_ratio: float, nci_ratio: float = 0.0) -> ToolResult:
    """未实现内部销售损益计算与分摊。

    用途：计算集团内部货物买卖产生的未实现损益及其在母子公司间的分摊。

    Args:
        transfer_price: 内部转移价格（卖方收入，非负）。
        cost: 卖方成本（非负）。
        unsold_ratio: 买方期末未售出比例（0~1）。
        nci_ratio: 子公司少数股东持股比例（0~1，默认 0）。

    Returns:
        ToolResult: ``value``=归属于母公司的未实现损益（已扣 NCI 部分）；
            ``details``=总未实现损益、NCI 分摊。
    """
    tp = require_non_negative("transfer_price", transfer_price)
    cst = require_non_negative("cost", cost)
    ur = require_number("unsold_ratio", unsold_ratio)
    nr = require_number("nci_ratio", nci_ratio)
    if not (0 <= ur <= 1):
        raise ToolValidationError(f"unsold_ratio 应在 [0,1]，收到：{ur}")
    if not (0 <= nr <= 1):
        raise ToolValidationError(f"nci_ratio 应在 [0,1]，收到：{nr}")
    total_profit = max(0.0, tp - cst)
    unrealized = total_profit * ur
    nci_share = unrealized * nr
    parent_share = unrealized * (1 - nr)
    return ToolResult(
        method_id="MTH-02-005",
        method_name="未实现内部损益分摊",
        value=round(parent_share, 4),
        inputs=dict(transfer_price=transfer_price, cost=cost, unsold_ratio=unsold_ratio, nci_ratio=nci_ratio),
        details=dict(total_unrealized=round(unrealized, 4), nci_share=round(nci_share, 4), parent_share=round(parent_share, 4)),
        notes="抵销时按母公司享有份额调减存货/营业成本；少数股东部分在少数股东权益中反映。",
    )


if __name__ == "__main__":
    res = build_equity_offset(parent_investment=800, subsidiary_equity=1000, nci_ratio=0.2)
    for e in res.value:
        print(e.summary, e.debits, e.credits)
