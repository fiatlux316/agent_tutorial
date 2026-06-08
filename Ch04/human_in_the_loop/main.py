from langgraph.types import interrupt
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


from llm import get_llm
llm = get_llm()


@tool
def human_assistance(query: str):
    """사람의 도움이 필요할 때 호출되는 도구입니다."""
    human_response = interrupt({"query": query})  # 실행 일시 중단
    return human_response


search_tool = TavilySearch(max_results=2)
tools = [search_tool, human_assistance]
llm_with_tools = llm.bind_tools(tools)


# 상태 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 챗봇 노드 정의
def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    return {"messages": [message]}


# 그래프 초기화 및 메모리 설정
graph_builder = StateGraph(State)
memory = MemorySaver()

# 노드 및 엣지 추가
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

# 그래프 컴파일
graph = graph_builder.compile(checkpointer=memory)


user_input = "AI 에이전트를 만드는 데 전문가의 조언이 필요해요. 사람의 도움을 받을 수 있을까요?"
config = {"configurable": {"thread_id": "2"}}

events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)
for event in events:
    print("\n=== New Event ===\n",event)
    if "messages" in event:
        event["messages"][-1].pretty_print()