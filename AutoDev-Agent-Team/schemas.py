# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: schemas.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
from typing import List
from pydantic import BaseModel, Field

class PRDDocument(BaseModel):
    """产品经理产出的标准 PRD"""
    project_name: str = Field(description="项目名称")
    core_features: List[str] = Field(description="核心功能列表")
    user_stories: List[str] = Field(description="用户场景描述")

class ArchitectureDesign(BaseModel):
    """架构师产出的标准架构文档"""
    file_structure: List[str] = Field(description="系统文件目录结构列表，如 ['main.py']")
    tech_stack: List[str] = Field(description="推荐技术栈或依赖库")
    design_notes: str = Field(description="架构设计要点")

class CodeArtifact(BaseModel):
    """程序员产出的完整源码"""
    filename: str = Field(description="代码文件名，如 main.py")
    code: str = Field(description="完整的 Python 源代码")

class ExecutionResult(BaseModel):
    """沙箱测试结果"""
    success: bool
    stdout: str
    stderr: str