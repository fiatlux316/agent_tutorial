import subprocess
import sys

from typing import Annotated, Literal
from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain.agents import create_agent 
from langgraph.graph import MessagesState
from langgraph.types import Command
from IPython.display import Image, display

from llm import get_llm
llm = get_llm()

# 1) 검색 도구 (Tavily API 필요)
tavily_tool = TavilySearch(max_results=5)

# 2) 로컬 파이썬 실행 도구 (subprocess 사용, PythonREPL 대체)
def execute_python_code(code: str) -> str:
    """파이썬 코드를 안전하게 실행하고 결과를 반환합니다."""
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return f"실행 실패:\n{result.stderr}"
        return result.stdout if result.stdout else "(출력 없음)"
    except subprocess.TimeoutExpired:
        return "실행 시간 초과 (10초)"
    except Exception as e:
        return f"실행 중 오류: {repr(e)}"

@tool
def python_repl_tool(
    code: Annotated[str, "차트를 생성하기 위한 파이썬 코드"]
):
    """파이썬 코드를 실행합니다. 출력은 print(...)로 표시해야 합니다."""
    result = execute_python_code(code)
    return f"성공적으로 실행했습니다:\n```python\n{code}\n```\nStdout: {result}\n\nFINAL ANSWER"


# 3) 시스템 프롬프트 템플릿
def make_system_prompt(suffix: str):
    return (
        "당신은 다른 어시스턴트와 협업하는 유능한 AI입니다. "
        "주어진 도구만 사용해 작업을 완수하세요. "
        "최종 답변을 얻으면 반드시 'FINAL ANSWER'를 붙여 종료하세요."
        f"\n{suffix}"
    )

def get_next_node(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        return END
    return goto


# 4) 리서처 노드 (검색 전용)
research_agent = create_agent(
    model=llm,
    tools=[tavily_tool],
    system_prompt=make_system_prompt("당신은 리서치만 할 수 있습니다. 동료 차트 생성자와 협업하세요.")
)

def research_node(state: MessagesState) -> Command[Literal["chart_generator", "__end__"]]:
    result = research_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "chart_generator")
    # 일부 모델/프로바이더 제약 회피: 마지막 메시지를 Human 역할로 래핑
    result["messages"][-1] = HumanMessage(content=result["messages"][-1].content, name="researcher")
    return Command(update={"messages": result["messages"]}, goto=goto)

# 5) 차트 생성 노드 (파이썬 실행 전용)
chart_agent = create_agent(
    model=llm,
    tools=[python_repl_tool],
    system_prompt=make_system_prompt("당신은 차트 생성만 할 수 있습니다. 동료 리서처와 협업하세요.")
)

def chart_node(state: MessagesState) -> Command[Literal["researcher", "__end__"]]:
    result = chart_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "researcher")
    result["messages"][-1] = HumanMessage(content=result["messages"][-1].content, name="chart_generator")
    return Command(update={"messages": result["messages"]}, goto=goto)



# 6) 그래프 구성
workflow = StateGraph(MessagesState)
workflow.add_node("researcher", research_node)
workflow.add_node("chart_generator", chart_node)
workflow.add_edge(START, "researcher")  # 리서처부터 시작
graph = workflow.compile()

# 다이어그램 표시
try:
    display(Image(graph.get_graph().draw_mermaid_png()))
except Exception:
    pass


# 7) 실행
events = graph.stream(
    {
        "messages": [(
            "user",
            "지난 1년간 달러 환율 데이터를 조사하고, 그 데이터를 기반으로 라인 차트를 만드세요."
            "차트를 생성했으면 작업을 종료하세요."
        )]
    },
    {"recursion_limit": 150}  # 안전장치: 최대 스텝 제한
)

for step in events:
    print(step)   # 각 단계의 중간 결과/메시지 스트림 확인
    print("----")
