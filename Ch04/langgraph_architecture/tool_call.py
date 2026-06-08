from llm import get_llm
llm = get_llm()

##### 도구 호출
print("\n=== 도구 호출 예시 ===\n")

# 1) 도구 정의
def multiply(a: int, b: int) -> int:
    """두 수의 곱을 반환"""
    return a * b

# 2) LLM에 도구 바인딩
agent = llm.bind_tools([multiply])

# 3) 사용자 질문
user_msg = "2 곱하기 3은?"

# 4) 1차 LLM 호출 -> 도구 호출 의도 파악
msg = agent.invoke(user_msg)

# 5) tool_calls 확인 및 실행
results = {}
print(msg.tool_calls)

for call in getattr(msg, "tool_calls", []):
    name = call["name"]
    args = call["args"]
    if name == "multiply":
        results[name] = multiply(**args)
print(results)
