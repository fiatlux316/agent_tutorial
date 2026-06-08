# 오케스트레이터-워커 
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from typing import Annotated, List
from langgraph.types import Send
import operator
from langchain_core.messages import HumanMessage, SystemMessage

from llm import get_llm
llm = get_llm()

# 보고서 섹션(Section) 정의
class Section(BaseModel):
    name: str = Field(description="이 보고서 섹션의 제목")
    description: str = Field(description="이 섹션에서 다룰 주요 주제와 개념에 대한 간략한 설명")

# 보고서 섹션 목록 구조
class Sections(BaseModel):
    sections: List[Section] = Field(description="보고서의 각 섹션 목록")

# LLM에 구조화 출력(Structured Output) 스키마를 적용
planner = llm.with_structured_output(Sections)

# 전체 워크플로 상태
class State(TypedDict):
    topic: str  # 보고서 주제
    sections: list[Section]  # 보고서 섹션 목록
    completed_sections: Annotated[list, operator.add]  # 모든 워커가 작성한 섹션 결과 모음
    final_report: str  # 최종 보고서

# 워커 상태
class WorkerState(TypedDict):
    section: Section
    completed_sections: Annotated[list, operator.add]


def orchestrator(state: State):
    """보고서 목차를 생성하는 오케스트레이터"""

    report_sections = planner.invoke([
        SystemMessage(content="보고서 목차를 생성해 주세요."),
        HumanMessage(content=f"보고서 주제: {state['topic']}"),
    ])
    return {"sections": report_sections.sections}


def llm_call(state: WorkerState):
    """각 보고서 섹션을 작성하는 워커"""

    section = llm.invoke([
        SystemMessage(content="제공된 제목과 설명에 따라 보고서 섹션을 작성하세요. 각 섹션에 머리말은 포함하지 말고, 마크다운 형식을 사용하세요."),
        HumanMessage(content=f"섹션 제목: {state['section'].name}\n설명: {state['section'].description}"),
    ])

    return {"completed_sections": [section.content]}


def synthesizer(state: State):
    """작성된 섹션들을 종합하여 최종 보고서 생성"""

    completed_sections = state["completed_sections"]
    combined_report = "\n\n---\n\n".join(completed_sections)
    return {"final_report": combined_report}


def assign_workers(state: State):
    """각 섹션에 워커 할당"""
    return [Send("llm_call", {"section": s}) for s in state["sections"]]


# 워크플로 빌더 생성
builder = StateGraph(State)

# 노드 등록
builder.add_node("orchestrator", orchestrator)
builder.add_node("llm_call", llm_call)
builder.add_node("synthesizer", synthesizer)

# 엣지 연결
builder.add_edge(START, "orchestrator")
builder.add_conditional_edges("orchestrator", assign_workers, ["llm_call"])
builder.add_edge("llm_call", "synthesizer")
builder.add_edge("synthesizer", END)

# 컴파일
orchestrator_worker = builder.compile()


# 다이어그램 출력
display(Image(orchestrator_worker.get_graph().draw_mermaid_png()))

# 실행
state = orchestrator_worker.invoke({"topic": "랭그래프 오케스트레이션-워커 법칙에 관한 보고서"})
print(state["final_report"])
