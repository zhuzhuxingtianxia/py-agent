# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: third_party.py
@Time: 2026/10/12
@Author: hil
@Desc: 接入 LangChain 社区现成的第三方工具（以 Tavily 搜索为例）
~~~~~~~~~~~~~~~~~~~~~~~~
"""
# src/tools/third_party.py
import os
from langchain_community.tools.tavily_search import TavilyAnswer

# 确保环境变量中配置了 TAVILY_API_KEY
# os.environ["TAVILY_API_KEY"] = "your-tavily-api-key"

# 直接实例化 LangChain 社区现成的第三方联网搜索工具
web_search_tool = TavilyAnswer(max_results=3, name="enterprise_web_search")

"""
自定义包装任意外部第三方 API, 例如如下：调用外部第三方天气预报 API 获取指定城市的实时天气
如果第三方工具没有现成的 LangChain 适配器，你可以用 @tool 手动封装一个 HTTP 请求：
import requests
from langchain_core.tools import tool

@tool
def fetch_external_weather_api(city: str) -> str:
    try:
        # 假设对接某公开气象 API 或内部天气服务
        # response = requests.get(f"https://api.weatherapi.com/v1/current.json?key=XXX&q={city}")
        # data = response.json()
        return f"【第三方天气】{city} 实时气温: 22°C，晴，空气质量优。"
    except Exception as e:
        return f"调用外部天气服务失败: {str(e)}"
~~~~~~~~~~~~~~~~~~~~~~~~
"""