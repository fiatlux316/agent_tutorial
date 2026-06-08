from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

from typing_extensions import Literal
from langchain_core.messages import HumanMessage, SystemMessage

# 구조화된 출력으로 LLM 래핑
from llm import get_llm
llm = get_llm()

##### 라우팅
print("\n=== 라우팅 예시 ===\n")

# 1) 라우팅 결정을 위한 구조화 출력 스키마
class Route(BaseModel):
    step: Literal["poem", "story", "joke"] = Field(
        None, description="라우팅의 다음 단계"
    )

# 2) 구조화 출력으로 동작하는 라우터 LLM
router = llm.with_structured_output(Route)

# 3) 상태 정의
class State(TypedDict):
    input: str
    decision: str
    output: str

# 4) 노드 정의 (각각 전용 프롬프트 사용)
def llm_call_1(state: State):
    """이야기 작성"""
    result = llm.invoke(f"다음 주제로 짧은 이야기를 작성해 주세요: {state['input']}")
    return {"output": result.content}

def llm_call_2(state: State):
    """농담 작성"""
    result = llm.invoke(f"다음 주제로 짧은 농담을 작성해 주세요: {state['input']}")
    return {"output": result.content}

def llm_call_3(state: State):
    """시 작성"""
    result = llm.invoke(f"다음 주제로 짧은 시를 작성해 주세요: {state['input']}")
    return {"output": result.content}

def llm_call_router(state: State):
    """입력을 적절한 노드로 라우팅"""
    decision = router.invoke(
        [
            SystemMessage(
                content="사용자 요청을 이야기(story), 농담(joke), 시(poem) 중 하나로 분류하고, "
                        "가장 알맞은 항목을 step에 지정하세요."
            ),
            HumanMessage(content=state["input"]),
        ]
    )
    return {"decision": decision.step}

# 5) 조건부 엣지에서 분기 로직
def route_decision(state: State):
    if state["decision"] == "story":
        return "llm_call_1"
    elif state["decision"] == "joke":
        return "llm_call_2"
    elif state["decision"] == "poem":
        return "llm_call_3"

# 6) 워크플로 구성
router_builder = StateGraph(State)
router_builder.add_node("llm_call_1", llm_call_1)
router_builder.add_node("llm_call_2", llm_call_2)
router_builder.add_node("llm_call_3", llm_call_3)
router_builder.add_node("llm_call_router", llm_call_router)

router_builder.add_edge(START, "llm_call_router")
router_builder.add_conditional_edges(
    "llm_call_router",
    route_decision,
    {
        "llm_call_1": "llm_call_1",
        "llm_call_2": "llm_call_2",
        "llm_call_3": "llm_call_3",
    },
)
router_builder.add_edge("llm_call_1", END)
router_builder.add_edge("llm_call_2", END)
router_builder.add_edge("llm_call_3", END)

router_workflow = router_builder.compile()

# 7) 다이어그램 확인
display(Image(router_workflow.get_graph().draw_mermaid_png()))

# 8) 실행
state = router_workflow.invoke({"input": "한국에 대한 농담을 써 주세요"})
print(state["output"])
