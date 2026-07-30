"""工具方法模块 · 公共基础层（base）

为 ``08-工具方法`` 下各计算型工具方法提供**统一的结果封装、参数校验与异常定义**，
确保方法之间低耦合、对外的输入/输出定义一致，便于后续封装为独立可复用模块 / WorkBuddy Skill。

设计原则：
- 纯标准库实现，不引入任何第三方依赖（仅使用 ``dataclasses`` / ``typing``）。
- 所有对外函数统一返回 :class:`ToolResult`，结构固定、字段明确。
- 参数校验失败时抛出 :class:`ToolValidationError`（继承自 ``ValueError``），不静默吞错。
- 业务层预警不抛异常，而是写入 ``ToolResult.warnings``，由调用方决策。

统一返回结构 ``ToolResult`` 字段约定：
- ``method_id``   : 方法编号（对应 MTH 编码，如 ``MTH-02-004``）
- ``method_name`` : 方法中文名称
- ``value``       : 主计算结果（数值或结构化对象；无则 ``None``）
- ``inputs``      : 回显的入参（便于复核与追溯）
- ``details``     : 结构化明细（各中间量、分项结果）
- ``warnings``    : 校验或业务层面的预警信息列表
- ``notes``       : 方法说明、阈值依据或适用边界提示
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolResult:
    """所有工具方法的统一返回结构（返回值规范）。

    Attributes:
        method_id: 方法编号，对应 MTH 编码。
        method_name: 方法中文名称。
        value: 主计算结果（数值或对象），无则 ``None``。
        inputs: 回显入参，便于复核。
        details: 结构化明细，存放中间变量与分项结果。
        warnings: 预警信息列表（业务/边界提示，不抛异常）。
        notes: 方法说明、阈值依据或适用边界。
    """

    method_id: str
    method_name: str
    value: Any = None
    inputs: dict = field(default_factory=dict)
    details: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    notes: str = ""


class ToolValidationError(ValueError):
    """入参校验失败统一异常，供调用方捕获并提示用户。"""


def require_number(name: str, value: Any) -> float:
    """要求入参为有限数值，返回 ``float``。

    Args:
        name: 参数名（用于错误信息）。
        value: 待校验值。

    Returns:
        float: 转换后的数值。

    Raises:
        ToolValidationError: 非数值或为非有限值（NaN/±inf）。
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ToolValidationError(f"参数「{name}」必须为数值，收到：{value!r}")
    if v != v or v in (float("inf"), float("-inf")):
        raise ToolValidationError(f"参数「{name}」必须为有限数值，收到：{value!r}")
    return v


def require_non_negative(name: str, value: Any) -> float:
    """要求入参为非负数值。"""
    v = require_number(name, value)
    if v < 0:
        raise ToolValidationError(f"参数「{name}」不能为负数，收到：{v}")
    return v


def require_positive(name: str, value: Any) -> float:
    """要求入参为正数（>0）。"""
    v = require_number(name, value)
    if v <= 0:
        raise ToolValidationError(f"参数「{name}」必须为正数，收到：{v}")
    return v


def require_in_range(
    name: str,
    value: float,
    low: float,
    high: float,
    low_inclusive: bool = True,
    high_inclusive: bool = True,
) -> float:
    """要求入参落在 [low, high]（含边界可配）区间内。"""
    v = require_number(name, value)
    if low_inclusive and v < low:
        raise ToolValidationError(f"参数「{name}」={v} 不应低于 {low}")
    if not low_inclusive and v <= low:
        raise ToolValidationError(f"参数「{name}」={v} 应大于 {low}")
    if high_inclusive and v > high:
        raise ToolValidationError(f"参数「{name}」={v} 不应高于 {high}")
    if not high_inclusive and v >= high:
        raise ToolValidationError(f"参数「{name}」={v} 应小于 {high}")
    return v
