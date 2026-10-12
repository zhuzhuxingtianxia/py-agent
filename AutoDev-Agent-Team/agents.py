# -*- coding: utf-8 -*-
"""
@Project: py-agent
@File: agents.py
@Time: 2026/10/12
@Author: hil
@Desc: 
~~~~~~~~~~~~~~~~~~~~~~~~
"""
import os
import sys
import zipfile
import subprocess
from typing import Optional
from langchain_openai import ChatOpenAI
from schemas import PRDDocument, ArchitectureDesign, CodeArtifact, ExecutionResult
import config


class SoftwareEngineeringAgents:
    def __init__(self):
        # 初始化 LLM 实例
        kwargs = {"model": config.MODEL_NAME, "temperature": 0.1, "api_key": config.OPENAI_API_KEY}
        if config.OPENAI_BASE_URL:
            kwargs["base_url"] = config.OPENAI_BASE_URL

        self.llm = ChatOpenAI(**kwargs)
        self.workspace_dir = config.WORKSPACE_DIR
        os.makedirs(self.workspace_dir, exist_ok=True)

    def pm_agent(self, user_requirement: str) -> PRDDocument:
        """PM 角色：需求分析与结构化 PRD 生成"""
        print("💡 [PM Agent] 正在分析用户需求并撰写 PRD 文档...")
        pm_llm = self.llm.with_structured_output(PRDDocument)
        prompt = f"你是一名资深产品经理。请将用户的以下原始需求转换为结构化 PRD 文档：\n需求：{user_requirement}"
        return pm_llm.invoke(prompt)

    def architect_agent(self, prd: PRDDocument) -> ArchitectureDesign:
        """Architect 角色：架构与文件设计"""
        print("📐 [Architect Agent] 正在基于 PRD 进行系统架构与文件设计...")
        arch_llm = self.llm.with_structured_output(ArchitectureDesign)
        prompt = (
            f"你是一名首席软件架构师。请根据以下 PRD 进行系统架构设计：\n"
            f"项目名称：{prd.project_name}\n"
            f"核心功能：{prd.core_features}\n"
            f"设计原则：单文件或极简多文件架构，确保可以在本地 Python 环境直接运行。"
        )
        return arch_llm.invoke(prompt)

    def engineer_agent(self, prd: PRDDocument, arch: ArchitectureDesign,
                       error_log: Optional[str] = None) -> CodeArtifact:
        """Engineer 角色：编写/修复代码"""
        if error_log:
            print("🛠️ [Engineer Agent] 捕获到运行报错，正在自动 Debug 并重构代码...")
        else:
            print("👨‍💻 [Engineer Agent] 正在根据架构图编写完整代码...")

        engineer_llm = self.llm.with_structured_output(CodeArtifact)
        debug_context = f"\n【注意：上一次代码运行报错信息如下，请针对性修复】:\n{error_log}" if error_log else ""

        prompt = (
            f"你是一名高级 Python 程序员。请实现该项目的完整源代码。\n"
            f"项目名称：{prd.project_name}\n"
            f"核心功能：{prd.core_features}\n"
            f"推荐文件架构：{arch.file_structure}\n"
            f"技术要求：代码必须包含完整逻辑，具备可运行性，严禁使用省略号(...)或占位符！"
            f"{debug_context}"
        )
        return engineer_llm.invoke(prompt)

    def qa_sandbox_agent(self, code_artifact: CodeArtifact) -> ExecutionResult:
        """QA 角色：代码本地沙箱物理执行与验证"""
        print("🧪 [QA Sandbox] 正在将代码写入沙箱环境并执行动态测试...")

        # 写入物理文件
        file_path = os.path.join(self.workspace_dir, code_artifact.filename)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code_artifact.code)

        # 在子进程沙箱中运行 Python 代码
        try:
            result = subprocess.run(
                [sys.executable, file_path],
                capture_output=True,
                text=True,
                timeout=config.SANDBOX_TIMEOUT,
                cwd=self.workspace_dir
            )

            if result.returncode == 0:
                print("✅ [QA Sandbox] 代码运行测试通过！")
                return ExecutionResult(success=True, stdout=result.stdout, stderr="")
            else:
                print("❌ [QA Sandbox] 代码执行发生异常！")
                return ExecutionResult(success=False, stdout=result.stdout, stderr=result.stderr)

        except subprocess.TimeoutExpired:
            print("⚠️ [QA Sandbox] 代码执行超时（可能包含死循环或等待阻塞）！")
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"ExecutionTimeoutError: Code execution timed out after {config.SANDBOX_TIMEOUT} seconds."
            )
        except Exception as e:
            return ExecutionResult(success=False, stdout="", stderr=str(e))

    def package_delivery(self, prd: PRDDocument, arch: ArchitectureDesign, code: CodeArtifact) -> str:
        """Packager 角色：生成 PRD、架构说明与代码 Zip 包"""
        print("📦 [Packager Agent] 正在打包完整项目交付物...")

        # 保存 PRD.md
        prd_path = os.path.join(self.workspace_dir, "PRD.md")
        with open(prd_path, "w", encoding="utf-8") as f:
            f.write(
                f"# {prd.project_name} PRD\n\n## 核心功能\n" + "\n".join([f"- {feat}" for feat in prd.core_features]))

        # 保存 ARCHITECTURE.md
        arch_path = os.path.join(self.workspace_dir, "ARCHITECTURE.md")
        with open(arch_path, "w", encoding="utf-8") as f:
            f.write(f"# 架构说明\n\n## 文件结构\n" + "\n".join([f"- {item}" for item in arch.file_structure]))

        # 打包成 ZIP
        zip_filename = f"{prd.project_name}_delivery.zip"
        zip_path = os.path.join(self.workspace_dir, zip_filename)

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(prd_path, arcname="PRD.md")
            zipf.write(arch_path, arcname="ARCHITECTURE.md")
            zipf.write(os.path.join(self.workspace_dir, code.filename), arcname=code.filename)

        print(f"🎉 项目打包成功！交付包已生成至: {zip_path}")
        return zip_path