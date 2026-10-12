#!/bin/bash
echo "🚀 正在启动企业智囊 Agent 全私有化平台..."

# 1. 启动容器基础设施 (Qdrant & Redis)
echo "📦 正在拉起 Qdrant 向量库与 Redis 数据库..."
docker-compose up -d qdrant redis

# 2. 检查本地 vLLM API 服务状态
echo "🔍 检查本地 vLLM 大模型推理引擎状态..."
curl -s http://localhost:8001/v1/models > /dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ 警告: 未检测到运行在 8001 端口的 vLLM 服务，请先启动 vLLM！"
fi

# 3. 后台启动 FastAPI 网关
echo "⚡ 启动 FastAPI SSE 异步流式网关 (Port: 8000)..."
nohup python src/api/main.py > logs_api.log 2>&1 &

# 4. 启动 Streamlit 前端
echo "🎨 启动 Streamlit 前端交互界面 (Port: 8501)..."
streamlit run src/ui/app.py --server.port 8501 --server.address 0.0.0.0