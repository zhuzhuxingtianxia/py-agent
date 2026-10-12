# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: pipeline.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
from agents import SoftwareEngineeringAgents
import config


class AutoDevPipeline:
    def __init__(self):
        self.agents = SoftwareEngineeringAgents()

    def run(self, requirement: str):
        """驱动 SOP 流程与代码自纠错循环"""
        print(f"\n🚀 收到新项目需求: '{requirement}'\n" + "=" * 50)

        # 1. PM 阶段
        prd = self.agents.pm_agent(requirement)

        # 2. Architect 阶段
        arch = self.agents.architect_agent(prd)

        # 3. Engineer + QA 自纠错循环[cite: 1]
        retries = 0
        error_log = None
        code_artifact = None

        while retries < config.MAX_DEBUG_RETRIES:
            code_artifact = self.agents.engineer_agent(prd, arch, error_log=error_log)
            test_result = self.agents.qa_sandbox_agent(code_artifact)

            if test_result.success:
                break
            else:
                retries += 1
                error_log = test_result.stderr
                print(f"🔄 启动第 {retries}/{config.MAX_DEBUG_RETRIES} 次代码自动修复...")

        # 4. 交付打包裹
        if test_result.success:
            zip_path = self.agents.package_delivery(prd, arch, code_artifact)
            return True, zip_path
        else:
            print(f"💥 已达到最大自动重试上限 ({config.MAX_DEBUG_RETRIES})，代码纠错失败。")
            return False, None