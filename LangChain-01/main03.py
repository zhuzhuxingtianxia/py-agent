# -*- coding: utf-8 -*-
import getpass
import os
from enum import Enum
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    # 加载环境变量
    load_dotenv()
except ImportError:
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

# 文本分类
def text_category():
    #  初始化模型
    llm = init_chat_model("gpt-4o-mini", model_provider="openai")
    # 提示词模版
    tagging_prompt = ChatPromptTemplate.from_template(
    """
    从以下段落中提取所需信息. 仅提取'Schema'方法中提到的属性. Passage: {input}
    """
    )
    # 结构化模型
    structured_llm = llm.with_structured_output(Schema)
    # 输入需要分类的文本
    in_put = "我很高兴认识你！我想我们会成为非常好的朋友！"
    # in_put= "Estoy muy enojado con vos! Te voy a dar tu merecido!"
    # in_put = "Estoy increiblemente contento de haberte conocido! Creo que seremos muy buenos amigos"
    # in_put = "Weather is ok here, I can go outside without much more than a coat"
    prompt = tagging_prompt.invoke({"input": in_put})
    # 执行返回响应
    response = structured_llm.invoke(prompt)
    # 将模型转字典结构
    res = response.model_dump()
    print(res)

class SentimentEnum(str, Enum):
    happy = "happy"
    neutral = "neutral"
    sad = "sad"

class LanguageEnum(str, Enum):
    chinese="汉语"
    english="英语"
    spanish="西班牙语"
    french="法语"
    german="德语"
    italian="意大利语"

class Schema(BaseModel):
    sentiment: SentimentEnum = Field(description="The sentiment of the text")
    # 描述陈述的攻击性，数字越高，攻击性越强
    aggressiveness: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10] = Field(
        description="describes how aggressive the statement is, the higher the number the more aggressive",
    )
    language: LanguageEnum = Field(description="The language the text is written in")

# 程序入口
if __name__ == '__main__':
    check_smith()
    check_openai_key()
    text_category()