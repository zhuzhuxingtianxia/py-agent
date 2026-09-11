# -*- coding: utf-8 -*-
# 聊天模型和提示
import getpass
import os
import sys
from langchain.chat_models import init_chat_model
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 这是一个简单的函数
def my_print(name):
    # 可以使用断点debug代码
    print('Python %s on %s' % (sys.version, sys.platform))
    print(f'Hi, {name}')

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
    if not os.getenv("DEEPSEEK_API_KEY"):
        os.environ["DEEPSEEK_API_KEY"] = getpass.getpass("Enter your DeepSeek API key: ")

# 检查模型是否可用
def openai_gpt_3(model="gpt-3.5-turbo"):
    try:
        # 初始化模型
        model = ChatOpenAI(model=model, temperature=0.7)
        # 发送测试请求
        response = model.invoke("模型是否可用？")

        if response.content:
            print(f"✅ {model} 可用，响应内容:", response.content[:50] + "...")
        else:
            print("❌ 收到空响应")

    except Exception as e:
        if "quota" in str(e).lower():
            print("⚠️ 超出配额：模型可用但配额不足")
        elif "does not exist" in str(e).lower():
            print(f"❌ 模型不存在：{model} 可能已停用")
        else:
            print(f"❌ 错误信息: {e}")

def openai_chat(txt="hi"):
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    # model = init_chat_model(model="gpt-3.5-turbo", model_provider="openai")
    messages = [
        SystemMessage("转换下面的内容从English到中文"),
        HumanMessage(txt),
    ]
    for token in model.stream(messages):
        print(token.content, end="|")
    # res = model.invoke(messages)
    # print(res)

def prompt_temp(text="Good morning!", language="Chinese"):
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    # system_template = "转换下面的内容从中文到{language}"
    system_template = "Translate the following from English into {language}"
    prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_template), ("user", "{text}")]
    )
    prompt = prompt_template.invoke({"language": language, "text": text})
    # 格式化消息
    prompt.to_messages()
    # 调用 chat 模型
    response = model.invoke(prompt)
    print(response.content)

def deepseek_chat():
    model = init_chat_model("deepseek-reasoner", model_provider="deepseek")
    query = "介绍 系统自己!"
    response = model.invoke([{"role": "user", "content": query}])
    print(response.text())


# 程序入口
if __name__ == '__main__':
    my_print('PyCharm')
    # check_smith()
    check_openai_key()
    # openai_gpt_3()
    # openai_chat()
    deepseek_chat()
    # prompt_temp()