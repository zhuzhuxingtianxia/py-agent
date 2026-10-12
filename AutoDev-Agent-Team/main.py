# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: main.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import config
from pipeline import AutoDevPipeline


def main():
    # 检查 API Key
    if config.OPENAI_API_KEY == "your-api-key-here":
        print("⚠️ 警告: 请先在 config.py 或 .env 文件中设置 OPENAI_API_KEY！")
        return

    # 创建并运行流水线
    pipeline = AutoDevPipeline()

    # 输入需求示例
    user_requirement = "帮我写一个带有计时和计分功能的 Python 贪吃蛇游戏，使用 tkinter 实现 GUI 界面。"

    success, delivery_pkg = pipeline.run(user_requirement)

    if success:
        print(f"\n✅ 自动化任务完成！请检查产出文件目录: {delivery_pkg}")
    else:
        print("\n❌ 任务执行失败，请检查调试日志。")


if __name__ == "__main__":
    main()