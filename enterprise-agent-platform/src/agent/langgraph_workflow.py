# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: langgraph_workflow.py
@Time: 2026/10/10
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import sys
import io
from typing import Annotated, Sequence, Literal, TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages


# ================= 1. 定义全局 Agent 状态 (State) =================
class AgentState(TypedDict):
    # add_messages 用于将节点返回的新消息追加到历史消息列表中
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_node: str


# ================= 2. 定义安全 Python 代码沙箱工具 =================
@tool
def python_code_sandbox(code: str) -> str:
    """在隔离环境中执行 Python 代码，并捕获标准输出 (stdout)。适用于数据计算、统计与图表绘制。"""
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    try:
        # 在独立的全局/局部字典作用域中执行代码
        exec_globals = {}
        exec(code, exec_globals)
        output = redirected_output.getvalue()
        return output if output.strip() else "✅ 代码执行成功 (无标准输出)。"
    except Exception as e:
        return f"❌ 代码执行报错: {str(e)}"
    finally:
        sys.stdout = old_stdout


# ================= 3. 构建 Supervisor 路由决策节点 =================
# 配置连接本地 vLLM API 实例
llm = ChatOpenAI(
    base_url="http://localhost:8001/v1",
    api_key="EMPTY",
    model="Qwen/Qwen2.5-7B-Instruct-AWQ",
    temperature=0.0
)


def supervisor_node(state: AgentState) -> AgentState:
    """分析用户意图，规划任务并分发给具体子 Agent 节点"""
    system_prompt = (
        "你是一个企业智囊平台的 Supervisor 主控路由。"
        "分析用户的问题及历史上下文，选择下一步处理节点的名称：\n"
        "- 如果问题涉及公司规章制度、报销、流程等，回答 'RAG'\n"
        "- 如果问题涉及数学计算、Python 代码执行或数据分析，回答 'CODE'\n"
        "- 如果当前回答已经完备，无需进一步处理，回答 'FINISH'\n"
        "请务必严格只输出上述三个单词之一 (RAG / CODE / FINISH)。"
    )

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
    response = llm.invoke(messages)
    decision = response.content.strip().upper()

    # 简单的格式安全性防错兜底
    if "CODE" in decision:
        next_node = "code_agent"
    elif "RAG" in decision:
        next_node = "rag_agent"
    else:
        next_node = "FINISH"

    return {"next_node": next_node}


# ================= 4. 构建业务 Agent 节点 =================
def code_agent_node(state: AgentState) -> AgentState:
    """编写并调用 Python 沙箱执行代码的节点"""
    prompt = "你是一个 Python 数据分析专家。生成并直接使用 `python_code_sandbox` 工具运行代码解决问题。"
    llm_with_tools = llm.bind_tools([python_code_sandbox])

    messages = [SystemMessage(content=prompt)] + list(state["messages"])
    response = llm_with_tools.invoke(messages)

    # 如果触发了 Tool Call，执行沙箱工具
    if response.tool_calls:
        tool_call = response.tool_calls[0]
        code_to_run = tool_call["args"].get("code", "")
        tool_result = python_code_sandbox.invoke(code_to_run)

        final_answer = AIMessage(content=f"📊 代码执行结果:\n{tool_result}")
        return {"messages": [final_answer], "next_node": "FINISH"}

    return {"messages": [response], "next_node": "FINISH"}


def rag_agent_node(state: AgentState) -> AgentState:
    """模拟调用 Day 2 搭建的 Hybrid RAG 引擎的节点"""
    # 此处可直接对接 Day 2 的 HybridRAGEngine.search()
    rag_context = "【公司制度库检索结果】：差旅费用需在出差结束后 5 个工作日内提交，发票抬头必须包含企业纳税人识别号。"

    prompt = f"结合以下检索到的私有知识回答用户问题：\n{rag_context}"
    messages = [SystemMessage(content=prompt)] + list(state["messages"])
    response = llm.invoke(messages)

    return {"messages": [response], "next_node": "FINISH"}


# ================= 5. 组装 LangGraph 状态图与条件边 =================
workflow = StateGraph(AgentState)

# A. 添加所有功能节点
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("code_agent", code_agent_node)
workflow.add_node("rag_agent", rag_agent_node)

# B. 设置起始入口节点
workflow.add_edge(START, "supervisor")

# C. 配置 Supervisor 出来的动态条件边 (Conditional Edges)
workflow.add_conditional_edges(
    "supervisor",
    lambda state: state["next_node"],
    {
        "code_agent": "code_agent",
        "rag_agent": "rag_agent",
        "FINISH": END
    }
)

# D. 完成 Agent 节点后收尾结束
workflow.add_edge("code_agent", END)
workflow.add_edge("rag_agent", END)

# E. 编译生成 Graph 运行图对象
app = workflow.compile()

# ================= 测试运行 =================
if __name__ == "__main__":
    print("🚀 测试 1：触发 Python 代码沙箱分析节点")
    input_state_1 = {"messages": [HumanMessage(content="帮我计算 1 到 100 累加求和的结果是多少？")]}
    output_1 = app.invoke(input_state_1)
    print(output_1["messages"][-1].content)

    print("\n-----------------------------------\n")

    print("🚀 测试 2：触发 RAG 知识库检索节点")
    input_state_2 = {"messages": [HumanMessage(content="出差回来之后多久以内需要提交报销申请？")]}
    output_2 = app.invoke(input_state_2)
    print(output_2["messages"][-1].content)