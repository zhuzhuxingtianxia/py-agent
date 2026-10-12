# enterprise-agent-platform

从零开始架构并落地一个企业级全私有化 Agent 平台——“企业智囊平台 (Enterprise Smart Agent Platform)”。


系统的全景架构设计、技术选型闭环与环境基础设施搭建。

## 企业级私有化 Agent 平台整体架构设计
1. 确定终极项目业务蓝图：明确“企业智囊平台”的三大核心功能模块（私有知识问答、自动化代码/数据分析、多 Agent 流程编排）。
2. 绘制全栈系统分层架构：理清前端、网关、Agent 编排层（LangGraph）、向量检索层（RAG）与底层本地推理/微调层（vLLM/QLoRA）的数据拓扑。
3. 搭建工程基础骨架：完成项目目录结构规划与 Docker Compose 私有化服务栈配置。

#### 企业级全私有化 Agent 平台全景架构
一个生产级、数据不出域的企业 Agent 平台必须具备高并发、高可用、可拓展、安全审计四大特性。系统的整体分层架构设计如下：

    ┌────────────────────────────────────────────────────────────────────────┐
    │                   前端交互层 (UI Layer)                                │
    │        Web Portal (Next.js / Streamlit) / API RESTful Gateway          │
    └───────────────────────────────────┬────────────────────────────────────┘
                                        │ HTTP / WebSocket
    ┌───────────────────────────────────▼────────────────────────────────────┐
    │              Agent 编排与控制层 (Orchestration Layer)                  │
    │  ┌──────────────────────────────────────────────────────────────────┐  │
    │  │ LangGraph 状态图引擎 (StateGraph & Dynamic Routing)             │  │
    │  │  ├── Supervisor 路由分配节点                                     │  │
    │  │  ├── RAG 检索生成节点 (Hybrid Search + Rerank)                   │  │
    │  │  └── Code Executor 代码运行/分析节点                            │  │
    │  └──────────────────────────────────────────────────────────────────┘  │
    │  ┌──────────────────────────────────────────────────────────────────┐  │
    │  │ 持久化与状态记忆 (Memory & Checkpointer)                         │  │
    │  │  └── PostgreSQL / Redis (保存 Conversation State 与 Checkpoint)  │  │
    │  └──────────────────────────────────────────────────────────────────┘  │
    └───────────────────────────────────┬────────────────────────────────────┘
                                        │ Internal gRPC / HTTP
    ┌───────────────────────────────────▼────────────────────────────────────┐
    │             企业知识与工具检索层 (RAG & Tools Layer)                    │
    │  ├── Qdrant / Milvus (向量数据库 - 密集检索)                           │
    │  ├── Elasticsearch (文本数据库 - 稀疏 BM25 检索)                        │
    │  └── Local Sandbox / DB Drivers (本地工具扩展)                         │
    └───────────────────────────────────┬────────────────────────────────────┘
                                        │ OpenAI Compatible API (v1/chat)
    ┌───────────────────────────────────▼────────────────────────────────────┐
    │            底层私有化大模型推理与微调层 (Inference & LLM Layer)        │
    │  ├── vLLM API Cluster (Qwen2.5-7B/14B-Instruct-AWQ 高并发推理)         │
    │  └── Local QLoRA Adapters (特定领域/格式化输出微调权重)                │
    └────────────────────────────────────────────────────────────────────────┘


#### 关键选型与设计原则：
1. 解耦与标准化：Agent 编排层与底层 LLM 推理层之间通过 OpenAI API 兼容协议（vLLM 暴露的 `/v1/chat/completions`）隔离，未来支持无缝平滑切换不同基座模型。
2. 确定性状态管理：采用 LangGraph 替代自由度过高的纯 ReAct 循环，使用 PostgreSQL/Redis 作为 `Checkpointer` 保存对话状态，支持人机协作中断与中断后恢复（Human-in-the-Loop）。
3. 混合检索 RAG：知识库采用 Dense Vector (Qdrant) + Sparse Text (BM25) 双路召回，并挂载 Reranker 模型，确保专业文档检索的极高准确率。

#### Docker Compose 基础服务栈
通过 `docker-compose.yml` 快速一键拉起向量数据库（Qdrant）、缓存与状态持久化（Redis）以及本地推理环境。

在 Docker 容器内部调用宿主机上由 vLLM 或 Ollama 启动的大模型推理 API 时，使用 `host.docker.internal` 可以安全地跨越容器网络连通宿主机上的 GPU 服务端口（如 `8001` 或 `11434`）。

#### 项目目录规划 (`enterprise-agent-platform/`)
    enterprise-agent-platform/
      ├── docker-compose.yml           # 基础设施容器编排
      ├── config/                      # 全局配置文件
      ├── src/
      │   ├── agent/                   # LangGraph Agent 核心编排逻辑
      │   ├── rag/                     # 混合检索 RAG 引擎
      │   ├── tools/                   # 自定义本地工具库
      │   └── api/                     # FastAPI 服务对外接口
      ├── data/                        # 向量库与持久化卷存储
      └── requirements.txt             # Python 项目依赖

#### 最终工程代码树 (`enterprise-agent-platform/`)
      enterprise-agent-platform/
      ├── docker-compose.yml             # 基础设施 (Qdrant, Redis, FastAPI, Streamlit)
      ├── requirements.txt               # 全栈 Python 依赖包
      ├── README.md                      # 项目部署与交付文档
      ├── config/
      │   └── settings.py                # 全局配置参数 (vLLM URL, VectorDB URL)
      ├── src/
      │   ├── rag/
      │   │   └── hybrid_retriever.py    # Day 2: Dense+BM25+Rerank 混合 RAG 引擎
      │   ├── agent/
      │   │   └── langgraph_workflow.py  # Day 3: LangGraph 状态图与 Python 代码沙箱
      │   ├── api/
      │   │   └── main.py                # Day 4: FastAPI SSE 异步流式网关
      │   └── ui/
      │       └── app.py                 # Day 4: Streamlit 响应式交互前端
      └── scripts/
          └── run_all.sh                 # 一键启动全栈服务脚本

状态解耦设计：
Agent 的当前状态（State）与执行 Checkpoint 独立存储在 Redis 中，而知识库数据保存在 Qdrant 中。这种“计算、记忆与检索”三者分离的云原生设计，极大地方便了后期的横向扩展（Scale-out）。

#### 思考

1. 多租户与权限隔离：在企业级私有化平台中，不同部门（如 HR 与 研发）对知识库的访问权限不同。在设计 Qdrant 向量数据库与 Agent RAG 检索层时，应该如何配置 `payload_filter`（有效载荷过滤）来实现基于角色的权限控制（RBAC）？
2. 服务健康检查：在将 `agent-backend` 启动连接 vLLM 时，如果 vLLM 模型正在装载显存中未就绪，后端 API 应该采用怎样的 Retry（重试）与 Health-Check（健康检查）策略来避免容器启动报错挂掉？

## 高精度双路召回 + Rerank 混合重排 RAG 引擎
`src/rag/hybrid_retriever.py`

1. 为什么必须用双路召回（Hybrid Search）？
    * Dense 向量检索：擅长理解“语义相似”但词汇不同的句子（如“怎么报销差旅费”与“出差费用申请流程”），但在遇到型号（如 `RTX-4090`）、人名、错误码或精确数字时容易失效。
    * Sparse 关键词检索（BM25）：基于词频统计，对精确词汇完全对齐，恰好填补了向量检索的短板。
   
2. Cross-Encoder Reranking 重排序原理
   * Bi-Encoder（向量生成）：Query 和 Document 分别独立编码成 Vector，计算余弦相似度。速度极快，但缺乏 Query 与 Doc 词语之间的细粒度交互。
   * Cross-Encoder（重排打分）：将 `Query` 和 `Document` 拼接为 `[CLS] Query [SEP] Document [SEP]` 一起输入 Transformer 神经网络，通过全量 Self-Attention自注意力 极其精准地计算相关性得分。
   
#### 工程细节解析
1. 粗召回与精重排的 Top-K 比例：
    
    在真实生产中，通常采用 双路召回 (Top-20 ~ Top-50) $\rightarrow$ Reranker 排序 $\rightarrow$ 输出最终 Top-3 ~ Top-5 的链路。既保证了 Recall（召回率不漏掉信息），又通过 Reranker 保障了 Precision（精确度，防止无关冗余上下文污染 LLM）。
2. 包装为 Agent 可调用的 Tool：
    
    我们可以使用 `@tool` 装饰器将 `engine.search()` 方法无缝包装为 LangGraph Agent 的工具，使 Agent 能够根据用户问题自主决定是否发起混合 RAG 检索。

#### 思考
1. Reranker 性能延时：Cross-Encoder 的计算开销比单纯的向量余弦计算高一个数量级。如果在并发极高的场景下 Rerank 导致响应延迟（Latency）增加，有哪些手段（如使用更小参数的 Reranker 模型、限制输入 Reranker 的候选文档数量）可以调优？
2. 切片策略（Chunking）优化：对于长达 100 页的 PDF 手册，直接按固定字符长度（如 500 字符）切片容易切断语义。应该使用哪种基于 Markdown 标题结构（`MarkdownHeaderTextSplitter`）或语义句子边界的切片策略？


## LangGraph 构建多 Agent 控制流与代码沙箱
`src/agent/langgraph_workflow.py`

在复杂的企业业务中，单一 Agent 往往难以同时处理 RAG 知识检索、复杂 SQL 编写以及数据可视化等多种任务。通过 LangGraph 的 StateGraph，我们可以构建模块化的多 Agent 架构.

1. 设计：定义包含全局 State、条件分支路由（Conditional Edges）与 Checkpoint 记忆恢复图。
2. 实现能够安全运行 Python 代码进行数据分析/图表绘制的本地工具。
3. Supervisor 路由节点与 Task Planning 循环

#### 设计原则
1. 全局共享状态 (`AgentState`)：所有的 Agent 节点共同维护一个包含 `messages`（历史消息）和 `next_step`（下一步路由目标）的 TypedDict。
2. 确定性路由逻辑 (Conditional Routing)：Supervisor 节点负责解析当前任务，并通过 LLM 的 Structured Output 指令返回下一步应该跳转至 `rag_agent`、`code_agent` 还是 `END`。
3. 安全代码沙箱：对于代码执行节点，采用 Python 内置受限执行或隔离进程（Docker/Subprocess），防止恶意代码破坏系统安全。

#### 控制流解析
1. `add_messages` 状态更新机制：
    
    在 LangGraph 的 `AgentState` 中，通过 `Annotated[Sequence[BaseMessage], add_messages]` 定义 `messages` 列表。 
   这样节点在返回 `{"messages": [new_msg]}` 时，图引擎会自动将其智能追加（Append）到全局对话数组末尾，而不是覆盖原有的聊天历史。
2. 人机协作中断与恢复（Human-in-the-Loop）扩展：
   在需要涉及关键操作（如“自动执行删除数据库操作”或“提交高额报销审批”）时，
   可以通过在 LangGraph 编译时配置 `checkpointer` 和 `interrupt_before=["code_agent"]` 机制，强制在执行前暂停图工作流，等待人工在 Web 界面点击“同意”后再恢复执行。

#### 思考
1. 死循环防范机制：
   
   在复杂的多 Agent 循环图中（如 `Agent A` 反复指派 `Agent B` 修正代码），
   如果 Agent 陷入无限思考重试，应该如何在 LangGraph 的 `invoke(config={"recursion_limit": 10})` 中设置最大递归深度，避免死循环消耗算力？
2. 代码沙箱安全增强：
   
   内置的 `exec()` 尽管方便，但在生产环境下仍存在读取主机敏感文件或进行网络攻击的隐患。
在企业级私有化落地的生产环境，应该如何配置基于 Docker 容器隔离（如 `docker run` 超时销毁机制）或 Pyodide（WebAssembly 隔离沙箱）的安全执行环境？


## FastAPI 后端网关与 Streamlit 前端交互
`src/api/main.py`

在传统的 HTTP 请求中，客户端发送请求后必须等待服务器端完全生成全部文本（甚至完成多轮 Tool Call）才能收到 HTTP 200 响应。对于复杂 Agent 任务，
这可能导致前端出现长达 5~15 秒的“白屏/卡顿”。

#### SSE (Server-Sent Events) 协议
**警告**移动端不支持SSE协议，需WebSockt协议
1. 客户端建立一次 HTTP 管道并保持连接 (`Content-Type: text/event-stream`)。
2. 只要 LangGraph 节点吐出新的 Token 或节点状态变更（如 `Supervisor 正在思考 -> 路由至 RAG 节点 -> 吐出回答`），服务端即刻以事件流形式向前端推送文本。

#### 运行测试
1. 启动后端：`python src/api/main.py` （运行在 `http://localhost:8000`）
2. 启动前端：`streamlit run src/ui/app.py` （访问 `http://localhost:8501`）

#### 核心工程细节解析
1. 状态指示器（Status Placeholder）的用户体验增强：
   
   在 Streamlit 前端中使用 `st.status()`，能在 Agent 进行思考、路由、RAG 数据库检索或代码沙箱执行时，动态展示当前正在进行的后台操作步骤。
一旦输出最终文本，状态框自动折叠或隐去，极大地提升了企业用户的交互体验。

2. 前后端解耦部署：
   
   通过 FastAPI API 网关将前端 Streamlit 与后端 LangGraph Agent 执行逻辑完全解耦。
未来如果将 Streamlit 替换为 Vue / React 或钉钉/飞书企微机器人，只需对接同一个 `/api/v1/chat/stream` 接口即可无缝迁移。

#### 思考

1. 多轮对话 Session 管理：在 FastAPI 接口中，如果用户需要继续追问（多轮对话），应该如何在 `ChatRequest` 中传入 `thread_id`，并使用 LangGraph 的 `MemorySaver` / `Redis` 保存并恢复历史 `AgentState`？
2. 并发与吞吐调优：当有 50 个企业员工同时在 Streamlit 前端进行流式提问时，FastAPI 后端的 `async` 异步协程池与 vLLM 底层的 Continuous Batching（连续批处理）是如何共同协作保障高并发吞吐的？

## 企业级 Agent 平台生产验收评估指标体系

|评估维度|核心指标 (Metrics)|生产合格标准| 优化调优手段  |
|---|---|---|---------|
|RAG 知识检索能力|Hits@K (召回率) / MRR (平均倒数排名)|Top-3 召回率 $> 85\%$|引入 Dense + Sparse (BM25) 双路召回与 Cross-Encoder Reranker。|
|Agent 路由与控制|Router Accuracy (意图路由准确率)|路由准确率 $> 95\%$|使用 Few-Shot Prompting，或将意图分类微调（QLoRA）进基座模型。|
|推理吞吐与延迟|TTFT (首字延迟) & TPS (每秒 Token 输出)|TTFT $< 1.5\text{s}$，TPS $> 25\text{ tokens/s}$|采用 vLLM 引擎（PagedAttention & Continuous Batching）配合 AWQ/GGUF 量化。|
|系统安全性与稳定性|Code Sandbox 逃逸率 / SSE 断连重连率|沙箱逃逸率 $= 0\%$，接口可用性 $> 99.9\%$|使用 Docker 隔离沙箱，FastAPI SSE 增加 心跳包（Heartbeat）与自动重连机制。|

#### 项目部署
一键启动脚本 `scripts/run_all.sh`
