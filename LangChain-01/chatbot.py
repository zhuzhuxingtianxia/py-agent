# -*- coding: utf-8 -*-
import getpass
import os
import threading
from typing import TypedDict, Annotated, Sequence

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, trim_messages, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph, MessagesState, add_messages

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

# 简单的直接使用ChatModel模型
def simple_chat():
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    response = model.invoke([HumanMessage(content="Hi! I'm Bob")])
    print(response.content)
    response = model.invoke([HumanMessage(content="What's my name?")])
    print(response.content)

def simple_chat_history():
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    response = model.invoke(
        [
            HumanMessage(content="Hi! I'm Bob"),
            AIMessage(content="Hello Bob! How can I assist you today?"),
            HumanMessage(content="What's my name?"),
        ]
    )
    print(response.content)

# 调用模型
def call_model(state: MessagesState):
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    response = model.invoke(state["messages"])
    return {"messages": response}

class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str
# 调用模型
def call_model_trim(state: State):
    model = init_chat_model("gpt-4o-mini", model_provider="openai")
    trimmer = trim_messages(
        max_tokens=65,
        strategy="last",
        token_counter=model,
        include_system=True,
        allow_partial=False,
        start_on="human",
    )
    trimmed_messages = trimmer.invoke(state["messages"])
    # 自定义系统消息提示模版，并利用MessagesPlaceholder以传入所有消息
    prompt_template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                # You are a helpful assistant. Answer all questions to the best of your ability in {language}.
                "你是个乐于助人的助手。尽你所能用{language}回答所有问题。",
            ),
            MessagesPlaceholder(variable_name="messages"),
        ]
    )
    prompt = prompt_template.invoke(
        {"messages": trimmed_messages, "language": state["language"]}
    )
    response = model.invoke(prompt)
    return {"messages": [response]}

def chat_with_graph():
    workflow = StateGraph(state_schema=State)
    # 添加单个节点到Graph
    workflow.add_edge(START, "model")
    workflow.add_node("model", call_model_trim)
    # 将Graph添加到内存中
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)
    # 传递到runnable中，此配置包含的信息不直接属于input，但很重要。它使单个应用程序支持多个对话线程(不同thread_id不同对话)
    config = RunnableConfig(configurable={"thread_id": "abc123"})

    language = "zh"
    query = "Hi I'm Todd, please tell me a joke."
    input_messages = [HumanMessage(query)]
    for chunk, metadata in app.stream(
            {"messages": input_messages, "language": language},
            config,
            stream_mode="messages",
    ):
        if isinstance(chunk, AIMessage):
            print(chunk.content, end="|")


# 程序入口
if __name__ == '__main__':
    check_smith()
    check_openai_key()
    chat_with_graph()
