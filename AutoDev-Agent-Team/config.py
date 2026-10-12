# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: config.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
from dotenv import load_dotenv

# 加载 .env 环境变量（如有）
load_dotenv()

# OpenAI / 本地推理 Endpoint 参数配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your-api-key-here")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)  # 如使用本地 vLLM 或 Ollama 可设为对应 Endpoint
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

# 沙箱与工程配置
WORKSPACE_DIR = os.path.abspath("./agent_workspace")
MAX_DEBUG_RETRIES = 3  # 代码自动 Debug 重试上限，防止死循环消耗 Token
SANDBOX_TIMEOUT = 10   # 代码沙箱单次运行超时时间（秒），防止死循环挂起进程