# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: config.py
@Time: 2026/10/9
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Enterprise Smart Agent Platform"

    # 底层 vLLM 推理服务地址
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:8001/v1")
    LLM_MODEL_NAME: str = os.getenv("LLM_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct-AWQ")

    # Qdrant 向量库配置
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    COLLECTION_NAME: str = "enterprise_knowledge"

    # Redis 状态记忆配置
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")


settings = Settings()

if __name__ == "__main__":
    print(f"🚀 初始化 {settings.PROJECT_NAME} 配置成功！")
    print(f"🔗 vLLM API Endpoint: {settings.LLM_BASE_URL}")
    print(f"📦 Qdrant Engine: {settings.QDRANT_URL}")