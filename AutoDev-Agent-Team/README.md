# `AutoDev-Agent-Team` (全自动软件工程 Agent 团队)
基于 Multi-Agent 标准化操作流程（SOP）与本地代码沙箱测试，实现“输入一句话需求 $\rightarrow$ 自动产出 PRD、架构设计、源代码及自动测试修正 $\rightarrow$ 交付 Zip 工程包”的全流程自动化软件开发系统。

## 项目目录结构
    AutoDev-Agent-Team/
    ├── agent_workspace/           # 自动生成的工程产物与沙箱运行目录（运行后自动建）
    ├── requirements.txt           # 项目依赖包清单
    ├── config.py                  # 系统配置文件（模型参数、API Key 与沙箱配置）
    ├── schemas.py                 # Pydantic 结构化数据契约 (SOP 规范定义)
    ├── agents.py                  # 各角色 Agent（PM, Architect, Engineer, QA, Packager）实现
    ├── pipeline.py                # SOP 全自动化流水线与 Debug 自纠错引擎
    ├── main.py                    # 系统运行主入口文件
    └── README.md                  # 项目部署与使用文档

## 环境准备与依赖安装

* 确保 Python 版本：需 Python 3.10+。
* 创建虚拟环境:
```
python -m venv venv
# Linux/macOS 激活:
source venv/bin/activate
# Windows 激活:
.\venv\Scripts\activate
```
* 安装依赖
```
pip install -r requirements.txt
```

#### 配置环境变量与 API
在项目根目录新建 `.env` 文件，或者直接在 `config.py` 中填写相应的配置：
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# 如果使用本地部署的大模型推理服务（如 vLLM / Ollama），填入 Base URL：
# OPENAI_BASE_URL=http://localhost:8000/v1
# MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
```

#### 运行系统
执行主程序开始跑通 Agent SOP 流水线：
```
python main.py
```

### 查看交付物
运行完成后，系统会自动建立并输出至 `./agent_workspace/` 文件夹：
* `PRD.md`：产品经理生成的结构化需求文档。
* `ARCHITECTURE.md`：架构师设计的架构规范。
* `<代码文件>.py`：经过 QA 沙箱运行测试验证的代码。
* `<项目名>_delivery.zip`：打包归档的最终项目交付包。