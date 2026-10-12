# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: app.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import tempfile
import streamlit as st
from rag_engine import process_and_store_document, build_rag_chain, Chroma, get_embeddings, DB_DIR

st.set_page_config(page_title="断网本地精准知识库助手", page_icon="🔒", layout="wide")

st.title("🔒 离线精准知识库问答助手 (防幻觉 RAG)")
st.caption("基于 LangChain + Ollama (Qwen2.5) + Chroma 持久化向量库 | 100% 物理断网安全运行")

# 初始化 session 状态
if "messages" not in st.session_state:
    st.session_state.messages = []

if "vectorstore" not in st.session_state:
    # 检查本地是否有持久化的 Chroma 数据库
    if os.path.exists(DB_DIR) and os.listdir(DB_DIR):
        st.session_state.vectorstore = Chroma(
            persist_directory=DB_DIR,
            embedding_function=get_embeddings()
        )
    else:
        st.session_state.vectorstore = None

# Sidebar: 文件上传区
with st.sidebar:
    st.header("📄 知识库文档管理")
    uploaded_file = st.file_uploader("上传本地文档 (PDF/MD/TXT)", type=["pdf", "md", "txt"])

    if uploaded_file is not None:
        if st.button("开始向量化入库", type="primary"):
            with st.spinner("正在解析文档并写入本地向量数据库..."):
                # 保存临时文件供 Loader 解析
                with tempfile.NamedTemporaryFile(delete=False,
                                                 suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name

                # 执行向量化与存储
                vs = process_and_store_document(tmp_path)
                st.session_state.vectorstore = vs
                os.remove(tmp_path)
                st.success("🎉 文档成功索引并存入本地向量库！")

    st.markdown("---")
    st.markdown("**系统状态**：")
    if st.session_state.vectorstore:
        st.green("🟢 本地向量库已就绪")
    else:
        st.warning("🟡 请先上传文档构建知识库")

# 主聊天区域
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "sources" in msg and msg["sources"]:
            with st.expander("🔍 查看本次回答引用的本地文档片段"):
                for src in msg["sources"]:
                    st.caption(f"📌 {src.metadata.get('source', '未知')} | 页码: {src.metadata.get('page', 0) + 1}")
                    st.text(src.page_content)

# 处理用户提问
if user_input := st.chat_input("请输入基于知识库的提问..."):
    if not st.session_state.vectorstore:
        st.error("请先在左侧侧边栏上传文档并点击入库！")
    else:
        # 1. 展现用户问题
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # 2. 调用 RAG 链处理
        rag_chain, retriever = build_rag_chain(st.session_state.vectorstore)

        # 获取检索到的文档块（用于界面引用展示）
        retrieved_docs = retriever.get_relevant_documents(user_input)

        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""

            # 流式吐字响应
            for chunk in rag_chain.stream(user_input):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")

            response_placeholder.markdown(full_response)

            # 展示参考来源
            if retrieved_docs:
                with st.expander("🔍 查看本次回答引用的本地文档片段"):
                    for doc in retrieved_docs:
                        st.caption(
                            f"📌 {os.path.basename(doc.metadata.get('source', '未知'))} | 页码: {doc.metadata.get('page', 0) + 1}")
                        st.text(doc.page_content)

        # 记录会话历史
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "sources": retrieved_docs
        })