# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: math_tools.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
# src/tools/math_tools.py
from langchain_core.tools import tool

@tool
def calculate_compound_interest(principal: float, rate: float, years: int) -> str:
    """计算复利终值。参数: principal(本金), rate(年化利率，如0.05), years(投资年限)。"""
    amount = principal * ((1 + rate) ** years)
    return f"经过 {years} 年后，本息总额为: {amount:.2f} 元"