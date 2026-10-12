# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: __init__.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
# src/tools/__init__.py
from .math_tools import calculate_compound_interest
from .db_tools import query_employee_status

# 导出汇总工具列表，方便 Agent 节点一键加载
ALL_TOOLS = [
    calculate_compound_interest,
    query_employee_status,
]