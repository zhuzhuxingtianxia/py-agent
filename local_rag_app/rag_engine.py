# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: rag_engine.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# 1. 初始化离线 Embedding 模型与 LLM
DB_DIR = "./chroma_db"
EMBED_MODEL_NAME = "BAAI/bge-small-zh-v1.5"  # 本地缓存或预下载的中文向量模型


def get_embeddings():
    """获取本地嵌入模型 (无需联网)"""
    return HuggingFaceEmbeddings(
        model_name=EMBED_MODEL_NAME,
        model_kwargs={'device': 'cpu'},  # 如果有GPU可改为 'cuda'
        encode_kwargs={'normalize_embeddings': True}
    )


def get_llm():
    """获取本地离线运行的 Ollama 大模型"""
    return ChatOllama(
        model="qwen2.5:7b",
        temperature=0.01  # 降至极低温度，进一步抑制随机生成与幻觉
    )


# 2. 文档解析与入库
def process_and_store_document(file_path: str) -> Chroma:
    """加载文档、切分并存入本地 Chroma 向量数据库"""
    ext = os.path.splitext(file_path)[-1].lower()

    # 动态选择加载器
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".md":
        loader = UnstructuredMarkdownLoader(file_path)
    else:
        loader = TextLoader(file_path, encoding="utf-8")

    documents = loader.load()

    # 递归字符分块：保持语义连贯性
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # 每个 chunk 限制 500 字左右
        chunk_overlap=50,  # 重叠 50 字，防止上下文截断
        separators=["\n\n", "\n", "。", "！", "？", " ", ""]
    )
    chunks = text_splitter.split_documents(documents)

    # 持久化写入 Chroma 向量库
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        persist_directory=DB_DIR
    )
    return vectorstore


# 3. 防幻觉 Prompt 设计与检索生成链构建
STRICT_RAG_PROMPT = """你是一个严谨的企业私有知识库问答助手。
请严格仅基于下方提供的 <context> 标签内的资料回答用户的问题。

【硬性约束规则】：
1. 如果 <context> 中的资料没有包含回答问题所需的信息，请直接回复：“根据当前本地知识库资料，无法回答该问题。”
2. 绝对不允许基于你自身的预训练知识进行推理、补充或凭空编造！
3. 回答必须客观、精准，直接提取上下文关键信息。

<context>
{context}
</context>

用户问题：{question}
回答："""


def format_docs(docs):
    """将召回的多个文档块拼接为格式化的 Context"""
    formatted = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "未知来源")
        page = doc.metadata.get("page", 0)
        formatted.append(f"[片段 {i} | 来源: {os.path.basename(source)} (第 {page + 1} 页)]:\n{doc.page_content}")
    return "\n\n".join(formatted)


def build_rag_chain(vectorstore: Chroma):
    """使用 LCEL 快速构建检索增强生成链"""
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 4}  # 召回相似度最高的 Top-4 块
    )

    prompt = ChatPromptTemplate.from_template(STRICT_RAG_PROMPT)
    llm = get_llm()

    # 构建 LCEL 链：平行获取 Context 与 Question -> 格式化 Prompt -> LLM 推理 -> 文本解析
    chain = (
            {
                "context": retriever | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
    )
    return chain, retriever