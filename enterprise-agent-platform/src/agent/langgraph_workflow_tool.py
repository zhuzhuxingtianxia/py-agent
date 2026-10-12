# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: langgraph_workflow_tool.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
# src/agent/langgraph_workflow_tool.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from src.tools import ALL_TOOLS  # 引入本地工具集
from src.tools.third_party import web_search_tool, fetch_external_weather_api  # 引入第三方工具

# 1. 聚合所有可用工具
master_tools_list = ALL_TOOLS + [web_search_tool, fetch_external_weather_api]

# 2. 初始化大模型并绑定工具
llm = ChatOpenAI(
    base_url="http://localhost:8001/v1",
    api_key="EMPTY",
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
    temperature=0.0
).bind_tools(master_tools_list)


def smart_agent_node(state):
    """能够自主选择本地工具或第三方工具的智能 Agent 节点"""
    messages = [SystemMessage(
        content="你是一个企业超级智能助手。请根据用户需求，自主选择最合适的工具（内部数据库、数学计算、联网搜索或天气查询）来解决问题。")] + list(
        state["messages"])

    response = llm.invoke(messages)
    return {"messages": [response]}