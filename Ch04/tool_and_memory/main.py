from langchain_tavily import TavilySearch 
from langchain.chat_models import init_chat_model
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import tools_condition
from langchain_core.messages import ToolMessage

import json
import os

from dotenv import load_dotenv
load_dotenv()

tool = TavilySearch(max_results=2)
tools = [tool]

# 도구 테스트
result = tool.invoke("랭그래프에서 '노드'란 무엇인가요?")
#print(f"\n🔍 도구 응답:\n{result}")

#llm = init_chat_model("openai:gpt-4.1")
#llm = init_chat_model(f"{os.getenv('BEDROCK_MODEL')}")

llm = init_chat_model(
    model=f"google_genai:{os.getenv('GEMINI_MODEL')}",
    api_key=os.getenv('GEMINI_API_KEY'),
)

llm_with_tools = llm.bind_tools(tools)


class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)


class BasicToolNode:
    """챗봇이 요청한 도구를 실행하는 노드입니다."""

    def __init__(self, tools: list):
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        messages = inputs.get("messages", [])
        if not messages:
            raise ValueError("입력된 상태에서 메시지를 찾을 수 없습니다.")

        outputs = []
        for tool_call in messages[-1].tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"]
                )
            )
        return {"messages": outputs}

#직접 정의할 수 있으나 소스가 길어지고 복작함
#tool_node = BasicToolNode(tools=[tool])

#prebuilt의 ToolNode는 tool_calls이 있는 메시지를 자동으로 감지하여 도구를 실행하므로, 별도의 로직 없이 바로 사용할 수 있습니다.
tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)


# def route_tools(state: State):
#     """
#     마지막 챗봇 메시지에서 도구 호출(tool_calls)이 있는지 확인하여
#     있으면 'tools' 노드로, 없으면 종료(END)로 이동합니다.
#     """
#     ai_message = state["messages"][-1]

#     if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
#         return "tools"  # 도구 호출이 있으면 도구 노드로 이동
#     return END  # 도구 호출이 없으면 종료

# 직접 정의한 route_tools 를 사용할 수 있으나 소스가 길어지고 복잡함
# graph_builder.add_conditional_edges(
#     "chatbot",
#     route_tools,
#     {"tools": "tools", END: END}
# )

#prebuilt의 tools_condition은 메시지에 tool_calls이 있는지만 확인하여 간단히 조건부 경로를 설정할 수 있습니다.
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition
)

# 도구 호출 후 챗봇으로 돌아가는 경로 설정
graph_builder.add_edge("tools", "chatbot")

# 그래프의 시작점 설정
graph_builder.add_edge(START, "chatbot")

# 그래프 완성 및 컴파일
graph = graph_builder.compile()


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


while True:
    user_input = input("User: ")
    if user_input.lower() in ["quit", "exit", "q"]:
        print("Goodbye!")
        break

    stream_graph_updates(user_input)            