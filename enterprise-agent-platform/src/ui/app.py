# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: app.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import json
import requests
import streamlit as st

st.set_page_config(page_title="企业智囊 Agent 平台", page_icon="🤖", layout="wide")

st.title("🤖 企业智囊 Agent 全私有化平台")
st.caption("基于 Qwen2.5 + Hybrid RAG + LangGraph + Code Sandbox 的企业级智能体")

# 初始化 Session 中的对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

# 渲染已有聊天历史
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 处理用户新输入
if prompt := st.chat_input("请输入您的问题（如：报销流程、计算 1 到 100 累加...）"):
    # 1. 显示用户输入
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 2. 呼叫后端 FastAPI SSE 流式接口并实时渲染
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        message_placeholder = st.empty()
        full_response = ""

        # 发起 HTTP POST 请求开启流式读取
        url = "http://localhost:8000/api/v1/chat/stream"
        payload = {"query": prompt}

        try:
            with requests.post(url, json=payload, stream=True) as response:
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            data_str = decoded_line[6:]
                            data = json.loads(data_str)

                            # 处理状态更新事件
                            if data["type"] == "status":
                                status_placeholder.status(data["data"], state="running")
                            # 处理流式文本 Token
                            elif data["type"] == "token":
                                full_response += data["data"]
                                message_placeholder.markdown(full_response + "▌")
                            # 结束标记
                            elif data["type"] == "done":
                                status_placeholder.empty()
                                message_placeholder.markdown(full_response)

            st.session_state.messages.append({"role": "assistant", "content": full_response})

        except Exception as e:
            st.error(f"❌ 呼叫后端 Agent 服务失败: {str(e)}")