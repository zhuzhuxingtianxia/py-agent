# local_rag_app
在企业私有化部署场景中，数据安全和准确性是第一位的。
本项目将完全脱离 OpenAI 等云端 API，在物理断网/离线环境下，基于 LangChain + Ollama/Qwen + Chroma 向量数据库 + Streamlit 前端 搭建企业级 RAG（检索增强生成）系统 。

## 项目整体架构与设计思路
    [本地文档 PDF/MD/TXT] 
           │
           ▼ (1. 文本解析 & 递归切分)
    [Text Chunks (文本块)]
           │
           ▼ (2. 离线 Embedding 模型向量化: bge-small-zh-v1.5)
    [Chroma 向量数据库 (磁盘持久化保存)]
           │
           │ (3. 用户提问 -> 相似度检索向量库 Top-K)
           ▼
    [精准召回上下文 (Context)]
           │
           ▼ (4. 注入防幻觉 Strict Prompt)
    [LLM 本地大模型: Ollama (Qwen2.5-7B)]
           │
           ▼ (5. Streamlit 打字机流式输出 + 附带文档引用页码)
    [前端交互界面]

## 环境搭建与依赖准备
使用 Ollama 在本地一键运行大语言模型 。在终端中执行：

```
# 下载并启动 Qwen2.5 7B 指令微调模型（或轻量级 1.5B/3B 模型）
ollama run qwen2.5:7b
```
注：模型下载完成后，切断网络连接该模型依然能在本地本地 GPU/CPU 上正常推理 。

Python 依赖包安装:
```
pip install langchain langchain-community langchain-core chromadb sentence-transformers pypdf streamlit
```

## 项目完整源码实现

    local_rag_app/
    ├── app.py              # Streamlit 前端界面与会话管理
    ├── rag_engine.py       # RAG 核心逻辑：文档加载、向量化、检索链与防幻觉Prompt
    └── chroma_db/          # 本地向量数据库持久化目录（自动生成）

## 核心工程细节与“精准防幻觉”深度讲解

#### 为什么能做到 100% 物理断网运行？
* 模型本地运行：通过 `Ollama` 运行开源模型 `Qwen2.5`，推理过程全部在本地 GPU/CPU 计算。
* 离线嵌入与向量库：选用 HuggingFace 本地加载的 `bge-small-zh-v1.5` Embedding 模型，结合本地持久化的轻量级向量数据库 `ChromaDB`，不需要网络请求第三方 API。

#### 解决“长文中信息被切断”的 Chunking 策略

代码中使用 `RecursiveCharacterTextSplitter` 搭配 `chunk_size=500` 与 `chunk_overlap=50`。
重叠区（Overlap）保证了当关键语句位于切分边界时，上下文不会断裂，提高了检索的连贯性。

#### 杜绝大模型“凭空捏造”的 Prompt 锁死机制
在 `STRICT_RAG_PROMPT` 中采用了极严格的围栏策略：

1. 显式限界：使用 `<context>` 标签严格框定参考资料。
2. 拒绝机制：明确要求在 Context 查无此信息时，必须返回“根据当前本地知识库资料，无法回答该问题”，强制切断大模型利用自带预训练权重进行猜测的通道。
3. 低 Temperature：设置 `temperature=0.01`，确保大模型的生成策略高度确定化。

#### 增强可信度的可追溯性设计（Citations）
前端界面不仅输出回答，还会同步通过 `retriever.get_relevant_documents` 展开显示召回的原文片段和具体页码，方便用户进行人工比对。

## 启动应用
在项目目录下运行：

```
streamlit run app.py
```

#### 实测防幻觉效果
* 正面测试：上传一份公司内部制度 PDF（如《差旅报销制度.pdf》），提问“出差补贴每天多少钱？” $\rightarrow$ 模型准确从文档提取并回答。
* 反向防幻觉测试：提问文档中完全没有提到的问题（如“公司的CEO是谁？”），模型将触发约束机制，准确回复“根据当前本地知识库资料，无法回答该问题。”，绝不胡乱编造。