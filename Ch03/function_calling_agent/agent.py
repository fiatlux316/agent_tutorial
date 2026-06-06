# Step2. 임포트
import os

from langchain.agents import create_agent
#from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_aws import ChatBedrock

#from langchain_llm_manager import LangchainLLMManager
#from llm_manager import LLMManager

from dotenv import load_dotenv

from function import *

# 환경 변수 로드(.env 파일에서 API 키 등을 로드)
load_dotenv()


# Step1. 도구 리스트 생성
tools = [
    get_customer_profile,
    search_products,
    get_customer_orders,
    get_delivery_status,
    search_reviews,
    get_customer_cart,
    get_point_history,
    get_current_promotions,
    get_popular_products,
]


#llm = LangchainLLMManager(LLMManager(provider=os.getenv("LLM_MODEL")))
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     api_key=os.getenv("GEMINI_API_KEY"),
#     temperature=0.0
# )

# Optional: BEDROCK_TOP_K를 설정하면 후보 토큰 수 제한(top_k)을 모델에 전달합니다.
# 일부 Bedrock 모델/엔드포인트는 이 필드를 허용하지 않으므로, 값이 있으면 안전하게 model_kwargs로 전달합니다.
top_k_env = os.getenv("BEDROCK_TOP_K")
model_kwargs = {}
if top_k_env:
    try:
        model_kwargs["top_k"] = int(top_k_env)
    except ValueError:
        print("환경변수 BEDROCK_TOP_K는 정수여야 합니다. 무시합니다.")

#if model_kwargs:

llm = ChatBedrock(
    model=os.getenv("BEDROCK_MODEL"),
    region=os.getenv("BEDROCK_REGION"),
    temperature=0.0,
    top_p=0.1,
    max_tokens=8000,
    model_kwargs=model_kwargs
)

# else:
#     llm = ChatBedrock(
#         model=os.getenv("BEDROCK_MODEL"),
#         region=os.getenv("BEDROCK_REGION"),
#         temperature=0.0,
#         top_p=0.1,
#         max_tokens=8000,
#     )

# temperature = 0.0
# top_p = 0.1
# top_k = 1
# self.inference_config = {"temperature": temperature, "topP": top_p , "maxTokens": 8000 }
# self.additional_model_fields = {"top_k": top_k}

# Step3. 시스템 프롬프트
SYSTEM_PROMPT = """당신은 쇼핑몰 고객 지원 도우미입니다. 사용자의 질문에 최선을 다해 답변하세요.

1. 고객 프로필, 주문 내역, 배송 상태, 포인트, 결제 정보 등에 관한 질문은 반드시 도구를 호출하여 답변합니다.
2. 이전 대화 맥락을 참고하여 일관된 답변을 제공합니다.
3. 고객의 문의에 친절하고 전문적으로 응대합니다.
4. ID 형식을 정확히 사용하십시오.
5. 현재 로그인한 사용자의 ID는 C001로 가정합니다.
"""


# Step4. 에이전트 생성
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=SYSTEM_PROMPT
)

# Step1. 대화 관리 클래스
class ConversationManager:
    def __init__(self):
        self.agent = agent
        self.chat_history = []

    def process_message(self, message: str):
        # 사용자 메시지를 히스토리에 추가
        self.chat_history.append({"role": "user", "content": message})

        # 에이전트 실행
        response = self.agent.invoke({"messages": self.chat_history})

        # 응답에서 마지막 메시지 추출
        last_message = response["messages"][-1]
        answer = last_message.content if hasattr(last_message, 'content') else str(last_message)

        # 어시스턴트 응답을 히스토리에 추가
        self.chat_history.append({"role": "assistant", "content": answer})

        # 실행 로그 생성
        log_content = [f"[User Input] {message}"]

        # tool_calls 정보 추출
        for msg in response["messages"]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    log_content.append(f"[Function Call] {tool_call['name']}")
                    log_content.append(f"[Parameters] {tool_call['args']}")
            if hasattr(msg, 'name') and msg.name:  # ToolMessage
                log_content.append(f"[Output] {msg.content}")

        log_content.append(f"[AI Response] {answer}")
        execution_log = "\n".join(log_content)

        return answer, execution_log

    def clear_history(self):
        self.chat_history = []
        return []

# 대화 관리자 인스턴스 생성
conversation_manager = ConversationManager()