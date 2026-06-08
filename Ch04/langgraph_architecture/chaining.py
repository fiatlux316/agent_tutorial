from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from IPython.display import Image, display

from llm import get_llm
llm = get_llm()

##### 프롬프트 체이닝 
print("\n=== 프롬프트 체이닝 예시 ===\n")

class State(TypedDict):
    topic: str
    joke: str
    improved_joke: str
    final_joke: str

# 1) 농담 생성
def generate_joke(state: State):
    msg = llm.invoke(f"{state['topic']}에 대한 짧은 농담을 작성해 주세요.")
    return {"joke": msg.content}

# 2) 품질 검사(펀치라인 확인)
def check_punchline(state: State):
    if "?" in state["joke"] or "!" in state["joke"]:
        return "Pass"
    return "Fail"

# 3) 농담 개선
def improve_joke(state: State):
    msg = llm.invoke(f"다음 농담에 말장난을 넣어 더 재미있게 만들어 주세요: {state['joke']}")
    return {"improved_joke": msg.content}

# 4) 농담 다듬기
def polish_joke(state: State):
    msg = llm.invoke(f"다음 농담에 예상치 못한 반전을 추가해 주세요: {state['improved_joke']}")
    return {"final_joke": msg.content}


workflow = StateGraph(State)

# 노드 등록
workflow.add_node("generate_joke", generate_joke)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)

# 순서 연결
workflow.add_edge(START, "generate_joke")
workflow.add_conditional_edges(
    "generate_joke", check_punchline, {"Fail": "improve_joke", "Pass": END}
)
workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)

# 워크플로 컴파일
chain = workflow.compile()


state = chain.invoke({"topic": "한국"})

print("Initial joke:")
print(state["joke"])
print("\n--- --- ---\n")

if "improved_joke" in state:
    print("Improved joke:")
    print(state["improved_joke"])
    print("\n--- --- ---\n")

    print("Final joke:")
    print(state["final_joke"])
else:
    print("농담이 품질 검사를 통과하여 개선이 필요하지 않습니다!")

# 다이어그램 출력
display(Image(chain.get_graph().draw_mermaid_png()))
