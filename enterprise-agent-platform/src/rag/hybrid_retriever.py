# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: hybrid_retriever.py
@Time: 2026/10/10
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
from typing import List
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from langchain_core.documents import Document


class HybridRAGEngine:
    def __init__(self, qdrant_url: str = "http://localhost:6333", collection_name: str = "enterprise_docs"):
        self.collection_name = collection_name
        # 1. 初始化向量库客户端
        self.qdrant = QdrantClient(url=qdrant_url)

        # 2. 加载 Embeddings 与 Cross-Encoder Reranker 模型
        # 生产环境推荐加载本地 Hugging Face / Ollama 的 Embedding 模型
        self.embedder = SentenceTransformer("BAAI/bge-small-zh-v1.5")
        self.reranker = CrossEncoder("BAAI/bge-reranker-base")

        # 本地内存 BM25 索引维护 (实际生产可挂载 Elasticsearch)
        self.raw_documents: List[Document] = []
        self.bm25: BM25Okapi = None

    def initialize_collection(self):
        """初始化 Qdrant Vector Collection"""
        self.qdrant.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    def ingest_documents(self, docs: List[Document]):
        """海量文档入库：同时构建 Dense 向量索引与 BM25 词频索引"""
        self.raw_documents = docs
        self.initialize_collection()

        # A. 构建 Dense 向量索引并存入 Qdrant
        points = []
        corpus_texts = []
        for idx, doc in enumerate(docs):
            vector = self.embedder.encode(doc.page_content).tolist()
            points.append(PointStruct(id=idx, vector=vector, payload={"text": doc.page_content, "meta": doc.metadata}))
            # BM25 分词预处理
            corpus_texts.append(list(doc.page_content))

        self.qdrant.upsert(collection_name=self.collection_name, points=points)

        # B. 构建 Sparse BM25 索引
        self.bm25 = BM25Okapi(corpus_texts)
        print(f"✅ 成功入库 {len(docs)} 条文档，混合索引建库完成！")

    def search(self, query: str, top_k: int = 3) -> List[Document]:
        """执行：Dense + Sparse 双路召回 -> Cross-Encoder 重排序"""

        # ---- 1. Dense 向量检索 (召回 Top-10) ----
        query_vector = self.embedder.encode(query).tolist()
        dense_results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=10
        )
        dense_texts = [hit.payload["text"] for hit in dense_results]

        # ---- 2. Sparse BM25 检索 (召回 Top-10) ----
        tokenized_query = list(query)
        bm25_top_texts = self.bm25.get_top_n(tokenized_query, [d.page_content for d in self.raw_documents], n=10)

        # ---- 3. 候选集去重合并 ----
        candidate_texts = list(set(dense_texts + bm25_top_texts))

        # ---- 4. Cross-Encoder Rerank 精细打分 ----
        pairs = [[query, doc_text] for doc_text in candidate_texts]
        rerank_scores = self.reranker.predict(pairs)

        # 按 Rerank 得分倒序排序
        scored_docs = sorted(zip(candidate_texts, rerank_scores), key=lambda x: x[1], reverse=True)

        # ---- 5. 截取 Top-K 最终高质量结果 ----
        final_docs = [Document(page_content=doc_text) for doc_text, score in scored_docs[:top_k]]
        return final_docs


# ================= 测试运行 =================
if __name__ == "__main__":
    engine = HybridRAGEngine()
    test_docs = [
        Document(page_content="公司差旅报销规定：乘坐高铁二等座可全额报销，发票抬头需为企业全称。"),
        Document(page_content="IT 运维指南：打印机连接失败时，请尝试重启服务或联系工号 88392。"),
        Document(page_content="项目代码规范：Python 代码严格遵守 PEP8 规范，函数须带有 Type Hint。")
    ]

    engine.ingest_documents(test_docs)

    # 包含了精确数字的 Query，考验 BM25 与 Rerank 能力
    results = engine.search("打印机连不上找哪个工号？", top_k=1)
    print(f"\n🔍 检索最终输出结果:\n{results[0].page_content}")