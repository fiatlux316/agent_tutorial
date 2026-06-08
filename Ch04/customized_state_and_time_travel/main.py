from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from langgraph.types import Command, interrupt


from llm import get_llm
llm = get_llm()


class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    release_date: str


@tool
# 상태 업데이트를 위한 ToolMessage를 생성하는 경우,
# 일반적으로 해당 도구 호출(tool call)에 대한 ID가 필요합니다.
# 이때 LangChain의 InjectedToolCallId를 사용하면,
# 해당 인자가 도구의 스키마(schema)에 모델에게 노출되지 않도록 처리할 수 있습니다.
def human_assistance(
    name: str, release_date: str, tool_call_id: Annotated[str, InjectedToolCallId]
):
    """사람의 확인이 필요한 정보를 검토받는 도구입니다."""

    # 사람에게 정보가 맞는지 물어봅니다.
    human_response = interrupt(
        {
            "question": "이 정보가 맞나요?",
            "name": name,
            "release_date": release_date,
        }
    )

    # 사람이 "Yes"로 응답한 경우 상태를 그대로 사용
    if human_response.get("correct", "").lower().startswith("y"):
        verified_name = name
        verified_date = release_date
        response = "정보가 정확하다고 확인됨."
    # 수정이 필요한 경우, 사람이 제공한 값을 사용
    else:
        verified_name = human_response.get("name", name)
        verified_date = human_response.get("release_date", release_date)
        response = f"사람이 수정한 정보: {human_response}"

    # 상태에 name, release_date 저장하고, 메시지도 함께 반환
    state_update = {
        "name": verified_name,
        "release_date": verified_date,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
    }

    # 상태 갱신을 위해 Command 객체를 반환
    return Command(update=state_update)


search_tool = TavilySearch(max_results=2)
tools = [search_tool, human_assistance]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    assert(len(message.tool_calls) <= 1)
    return {"messages": [message]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)


user_input = (
    "랭그래프가 언제 출시되었는지 찾아줄래요? "
    "결과를 찾으면 human_assistance 도구를 사용해서 사람에게 확인해줘."
)

config = {"configurable": {"thread_id": "1"}}

events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)

for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print()


## 사람의 답변 수정
print("\n=== 사람의 답변을 수정하는 시뮬레이션 ===\n")
human_command = Command(
    resume={
        "name": "랭그래프",
        "release_date": "2024년 1월 17일",
    },
)

events = graph.stream(human_command, config, stream_mode="values")

for event in events:
    if "messages" in event:
        event["messages"][-1].pretty_print() 