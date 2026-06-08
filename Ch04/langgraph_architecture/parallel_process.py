from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

from llm import get_llm
llm = get_llm()

##### 병렬 처리
print("\n=== 병렬 처리 예시 ===\n")

# 상태 정의
class State(TypedDict):
    topic: str
    joke: str
    story: str
    poem: str
    combined_output: str


# 1) 농담 생성
def call_llm_1(state: State):
    msg = llm.invoke(f"{state['topic']}에 대한 농담을 작성해 주세요.")
    return {"joke": msg.content}

# 2) 이야기 생성
def call_llm_2(state: State):
    msg = llm.invoke(f"{state['topic']}에 대한 이야기를 짧게 작성해 주세요.")
    return {"story": msg.content}

# 3) 시 생성
def call_llm_3(state: State):
    msg = llm.invoke(f"{state['topic']}에 대한 시를 작성해 주세요.")
    return {"poem": msg.content}

# 4) 결과 합치기
def aggregator(state: State):
    combined = f"{state['topic']}에 관한 이야기, 농담, 시입니다!\n\n"
    combined += f"이야기:\n{state['story']}\n\n"
    combined += f"농담:\n{state['joke']}\n\n"
    combined += f"시:\n{state['poem']}"
    return {"combined_output": combined}



parallel_builder = StateGraph(State)

# 노드 등록
parallel_builder.add_node("call_llm_1", call_llm_1)
parallel_builder.add_node("call_llm_2", call_llm_2)
parallel_builder.add_node("call_llm_3", call_llm_3)
parallel_builder.add_node("aggregator", aggregator)

# 병렬 연결
parallel_builder.add_edge(START, "call_llm_1")
parallel_builder.add_edge(START, "call_llm_2")
parallel_builder.add_edge(START, "call_llm_3")

# 결과 합치기
parallel_builder.add_edge("call_llm_1", "aggregator")
parallel_builder.add_edge("call_llm_2", "aggregator")
parallel_builder.add_edge("call_llm_3", "aggregator")
parallel_builder.add_edge("aggregator", END)

# 컴파일
parallel_workflow = parallel_builder.compile()


state = parallel_workflow.invoke({"topic": "한국"})
print(state["combined_output"])

# 다이어그램 출력
display(Image(parallel_workflow.get_graph().draw_mermaid_png()))

