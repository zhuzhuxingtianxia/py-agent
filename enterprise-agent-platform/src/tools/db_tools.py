# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: db_tools.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
# src/tools/db_tools.py
from langchain_core.tools import tool

@tool
def query_employee_status(employee_id: str) -> str:
    """根据员工工号查询内部员工的基本档案与在职状态。"""
    # 模拟企业内部数据库查询
    mock_db = {
        "88392": {"name": "张三", "department": "研发部", "status": "在职"},
        "10042": {"name": "李四", "department": "市场部", "status": "出差中"}
    }
    emp = mock_db.get(employee_id)
    if emp:
        return f"员工信息: 姓名-{emp['name']}, 部门-{emp['department']}, 状态-{emp['status']}"
    return "未找到该工号对应的员工信息。"