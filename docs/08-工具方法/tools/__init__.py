"""工具方法模块 · 可复用计算工具包（mth_tools）

将 ``08-工具方法`` 下高潜力候选方法（财务预警、税务工具、合并报表、快速估值）实现为
**低耦合、统一接口**的 Python 函数，便于后续封装为独立可复用模块 / WorkBuddy Skill。

统一约定（封装接口规范）：
- 所有对外函数返回 :class:`mth_tools.base.ToolResult`，字段固定
  （``method_id`` / ``method_name`` / ``value`` / ``inputs`` / ``details`` / ``warnings`` / ``notes``）。
- 入参校验失败抛 :class:`mth_tools.base.ToolValidationError`（继承自 ``ValueError``）。
- 业务预警不抛异常，写入 ``ToolResult.warnings``，由调用方决策。
- 方法之间仅依赖 ``base`` 层，互相不引用，保持低耦合。
- 命名规范：``calc_*``（测算）/ ``assess_*``（判定预警）/ ``build_*``（构建结构化结果）。
- 纯标准库实现，不引入第三方依赖。

快速开始::

    from mth_tools import financial_warning as fw
    r = fw.calc_altman_z(working_capital=1200, retained_earnings=800, ebit=600,
                         market_value_equity=5000, total_liabilities=3000,
                         sales=9000, total_assets=10000)
    print(r.value, r.notes)
"""

from __future__ import annotations

from .base import ToolResult, ToolValidationError
from . import financial_warning, tax_tools, consolidation, valuation

__all__ = [
    "ToolResult",
    "ToolValidationError",
    "financial_warning",
    "tax_tools",
    "consolidation",
    "valuation",
]
__version__ = "0.1.0"
