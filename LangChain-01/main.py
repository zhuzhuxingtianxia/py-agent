# -*- coding: utf-8 -*-
import getpass
import os
from typing import Optional, List

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    # 加载环境变量
    load_dotenv()
except ImportError:
    # 如果 python-dotenv 未安装，则定义一个空函数作为回退
    def load_dotenv():
        print("load_dotenv not found")
        pass

def check_smith():
    os.environ["LANGSMITH_TRACING"] = "true"
    if "LANGSMITH_API_KEY" not in os.environ:
        os.environ["LANGSMITH_API_KEY"] = getpass.getpass(
            prompt="Enter your LangSmith API key (optional): "
        )
    if "LANGSMITH_PROJECT" not in os.environ:
        os.environ["LANGSMITH_PROJECT"] = getpass.getpass(
            prompt='Enter your LangSmith Project Name (default = "default"): '
        )
        if not os.environ.get("LANGSMITH_PROJECT"):
            os.environ["LANGSMITH_PROJECT"] = "default"
    print("check smith OK")


def check_openai_key():
    if not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = getpass.getpass("Enter API key for OpenAI: ")
    print("check openai key OK")

class Person(BaseModel):
    """Information about a person."""
    # 实体Person的文档字符串。此文档字符串作为schema Person的描述发送到LLM，它可以帮助改进提取结果。
    # 1. Each field is an `optional` -- 这允许模型拒绝提取它，Optional不强迫LLM编造信息，不知道输出None
    # 2. Each field has a `description` -- LLM使用此描述。.
    # 有一个好的描述可以帮助提高提取结果。

    # 人的名字
    name: Optional[str] = Field(default=None, description="The name of the person")
    # 人的头发颜色（如果知道的话）
    hair_color: Optional[str] = Field(default=None, description="The color of the person's hair if known")
    # 身高
    height_in_meters: Optional[str] = Field(default=None, description="Height measured in meters")

class Data(BaseModel):
    """Extracted data about people."""
    # 创建一个模型，以便我们可以提取多个实体。
    people: List[Person]

def info_retrieval():
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")
    # 结构化模型
    structured_llm = llm.with_structured_output(Data)
    # 提示词模版
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert extraction algorithm. "
                "Only extract relevant information from the text. "
                "If you do not know the value of an attribute asked to extract, "
                "return null for the attribute's value.",
            ),
            # 请参阅如何通过参考示例提高性能。
            # MessagesPlaceholder('examples'),
            ("human", "{text}"),
        ]
    )
    # 输入文本
    # text = "Alan Smith is 6 feet tall and has blond hair."
    text = "My name is Jeff, my hair is black and i am 6 feet tall. Anna has the same color hair as me."
    prompt = prompt_template.invoke({"text": text})
    # 根据提示器返回响应
    response = structured_llm.invoke(prompt)
    # 将模型转字典结构
    res = response.model_dump()
    print(res)

# 使用@tool装饰器创建工具
@tool
def multiply(a: int, b: int) -> int:
    """Multiply a and b.
    Args:
        a: first int
        b: second int
    """
    return a * b

def tool_call_func(user_input = None):
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")
    # Tool列表
    tools_list = [multiply]
    # 工具绑定
    llm_with_tools = llm.bind_tools(tools_list)
    # 用户输入
    if user_input is None:
        # user_input = "Hello world!"
        user_input = "What is 2 multiplied by 3?"
    # 工具回调
    result = llm_with_tools.invoke(user_input)
    print(result)
    print(result.tool_calls)
    if hasattr(result, "tool_calls") and result.tool_calls:
        for tool_call in result.tool_calls:
            tool_name = tool_call["name"]
            args = tool_call["args"]
            tool_call_id = tool_call["id"]
            if tool_name == "multiply":
                tool_response = multiply.invoke(args)
                print(f"{tool_name}结果: {tool_response}")
                # 可选：将工具执行结果反馈给模型，让它生成自然语言回答
                final_messages = [
                    HumanMessage(content=user_input),
                    result,
                    ToolMessage(
                        tool_call_id=tool_call_id,
                        content=str(tool_response)  # 工具执行结果
                    )
                ]
                final_answer = llm.invoke(final_messages)
                print(final_answer.content)



# 程序入口
if __name__ == '__main__':
    check_smith()
    check_openai_key()
    tool_call_func("我想知道三乘以五是多少？")