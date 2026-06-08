from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display
from typing_extensions import Literal

from llm import get_llm
llm = get_llm()

# 평가자-개선자

# 그래프 상태
class State(TypedDict):
    joke: str          # 현재 농담
    topic: str         # 주제
    feedback: str      # 평가자 피드백(개선 시 참고)
    funny_or_not: str  # 평가 등급("funny" / "not funny")

# 평가에 사용할 구조화 출력 스키마
class Feedback(BaseModel):
    grade: Literal["funny", "not funny"] = Field(
        description="농담이 재미있는지(funny) 아닌지(not funny) 판단하세요."
    )
    feedback: str = Field(
        description="재미없다면 어떻게 개선할지 구체적인 피드백을 작성하세요."
    )

# 평가자 LLM: 구조화 출력으로 등급과 피드백을 반환
evaluator = llm.with_structured_output(Feedback)


# 1) 생성자: 농담 생성(피드백이 있으면 반영하여 개선)
def llm_call_generator(state: State):
    if state.get("feedback"):
        msg = llm.invoke(
            f"주제: {state['topic']}\n"
            f"아래 피드백을 반영하여 더 재미있는 농담을 작성해 주세요.\n"
            f"[피드백]: {state['feedback']}"
        )
    else:
        msg = llm.invoke(f"주제: {state['topic']}\n짧고 재치 있는 농담을 작성해 주세요.")
    return {"joke": msg.content}

# 2) 평가자: 농담 평가(등급 + 개선 피드백을 구조화하여 반환)
def llm_call_evaluator(state: State):
    grade = evaluator.invoke(
        f"다음 농담이 재미있는지 평가하고, 필요하면 개선 피드백을 주세요.\n[농담]: {state['joke']}"
    )
    print("grade.grade:", grade.grade) 
    print("grade.feedback:", grade.feedback)
    return {"funny_or_not": grade.grade, "feedback": grade.feedback}

# 3) 분기: 평가 결과에 따라 종료/재생성 결정
def route_joke(state: State):
    print("state :", state)
    if state["funny_or_not"] == "funny":
        return "Accepted"
    elif state["funny_or_not"] == "not funny":
        return "Rejected + Feedback"


# 그래프 구성
optimizer_builder = StateGraph(State)
optimizer_builder.add_node("llm_call_generator", llm_call_generator)
optimizer_builder.add_node("llm_call_evaluator", llm_call_evaluator)

optimizer_builder.add_edge(START, "llm_call_generator")
optimizer_builder.add_edge("llm_call_generator", "llm_call_evaluator")
optimizer_builder.add_conditional_edges(
    "llm_call_evaluator",
    route_joke,
    {
        "Accepted": END,
        "Rejected + Feedback": "llm_call_generator",
    },
)

# 컴파일
optimizer_workflow = optimizer_builder.compile()

# 다이어그램 확인
display(Image(optimizer_workflow.get_graph().draw_mermaid_png()))

# 실행
state = optimizer_workflow.invoke({"topic": "한국"})
print(state["joke"])
