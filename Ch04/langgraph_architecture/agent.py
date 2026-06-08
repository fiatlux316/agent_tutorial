from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from typing_extensions import Literal
from langgraph.graph import MessagesState
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from llm import get_llm
llm = get_llm()


@tool
def multiply(a: int, b: int) -> int:
    """두 수를 곱합니다."""
    return a * b

@tool
def add(a: int, b: int) -> int:
    """두 수를 더합니다."""
    return a + b

@tool
def divide(a: int, b: int) -> float:
    """두 수를 나눕니다."""
    return a / b

tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)


# LLM 호출 노드
def llm_call(state: MessagesState):
    """LLM이 도구 호출 여부를 결정"""
    return {
        "messages": [
            llm_with_tools.invoke(
                [SystemMessage(content="당신은 주어진 입력값으로 산술 연산을 수행하는 유용한 어시스턴트입니다.")]
                + state["messages"]
            )
        ]
    }

# 도구 실행 노드
def tool_node(state: dict):
    """LLM이 요청한 도구를 실행"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


# 반복 여부 판단
def should_continue(state: MessagesState) -> Literal["environment", END]:
    """도구 호출이 있으면 계속, 없으면 종료"""
    if state["messages"][-1].tool_calls:
        return "Action"
    return END


# 에이전트 워크플로 구성
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("environment", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {"Action": "environment", END: END},
)
agent_builder.add_edge("environment", "llm_call")

agent = agent_builder.compile()

# 실행
messages = [HumanMessage(content="3과 4를 더하세요.")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
