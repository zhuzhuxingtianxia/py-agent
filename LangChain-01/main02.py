# -*- coding: utf-8 -*-
import asyncio

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_pdf_doc():
    file_path = "./docs/nke-10k-2023.pdf"
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    # pdf有多少页
    print(len(docs))
    # 获取第一页前200字符
    print(f"{docs[0].page_content[:200]}\n")
    # 获取第一页元数据信息
    print(docs[0].metadata) #{'producer': 'EDGRpdf Service w/ EO.Pdf 22.0.40.0', 'creator': 'EDGAR Filing HTML Converter', 'creationdate': '2023-07-20T16:22:00-04:00', 'title': '0000320187-23-000039', 'author': 'EDGAR Online, a division of Donnelley Financial Solutions', 'subject': 'Form 10-K filed on 2023-07-20 for the period ending 2023-05-31', 'keywords': '0000320187-23-000039; ; 10-K', 'moddate': '2023-07-20T16:22:08-04:00', 'source': './docs/nke-10k-2023.pdf', 'total_pages': 107, 'page': 0, 'page_label': '1'}


def split_pdf_doc():
    file_path = "./docs/nke-10k-2023.pdf"
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    # add_start_index=True 保留元数据属性
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=200, add_start_index=True
    )
    all_splits = text_splitter.split_documents(docs)

    print(len(all_splits))
    # 加载嵌入模型
    # embeddings = DeterministicFakeEmbedding(size=4096)
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vector_store = InMemoryVectorStore(embeddings)
    # 为文档编制索引
    ids = vector_store.add_documents(documents=all_splits)
    print(ids)
    # 根据与字符串查询的相似性返回文档
    results = vector_store.similarity_search(
        "How many distribution centers does Nike have in the US?"
    )
    print(results[0])

    # 返回分数
    results = vector_store.similarity_search_with_score("What was Nike's revenue in 2023?")
    doc, score = results[0]
    print(f"Score: {score}\n")
    print(doc)

# 程序入口
if __name__ == '__main__':
    split_pdf_doc()