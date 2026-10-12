# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: main.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import json
import asyncio
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage

# 导入 Day 3 编译好的 LangGraph 工作流对象
# from src.agent.langgraph_workflow import app as agent_app

app = FastAPI(title="Enterprise Agent Platform API", version="1.0")

# 配置跨域 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    query: str
    thread_id: str = "default_session"


async def generate_agent_stream(query: str) -> AsyncGenerator[str, None]:
    """异步生成器：透传 LangGraph 生成过程中的 Token 和状态更新"""
    try:
        # 模拟调用 LangGraph 节点的流式输出 (app.astream_events)
        # 实际生产中使用：async for event in agent_app.astream_events({"messages": [HumanMessage(content=query)]}, version="v1"):

        # 1. 模拟发送状态变更事件
        yield json.dumps({"type": "status", "data": "🔍 Supervisor 正在调度意图路由..."})
        await asyncio.sleep(0.5)

        yield json.dumps({"type": "status", "data": "📚 路由至 RAG 节点，正在检索向量与关键词数据库..."})
        await asyncio.sleep(0.5)

        # 2. 模拟流式吐出回答 Token
        mock_answer = f"根据企业规章制度，关于‘{query}’的解答如下：请于出差结束后 5 个工作日内提交发票并在系统内填写报销单。"
        for char in mock_answer:
            yield json.dumps({"type": "token", "data": char})
            await asyncio.sleep(0.05)

        yield json.dumps({"type": "done", "data": "[FINISH]"})
    except Exception as e:
        yield json.dumps({"type": "error", "data": str(e)})


@app.post("/api/v1/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """SSE 流式 Chat 接口"""
    return EventSourceResponse(generate_agent_stream(request.query))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)