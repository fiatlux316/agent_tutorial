import requests
from typing import Any, Dict, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

class CompanyLLMWrapper(BaseChatModel):
    """
    회사 내부 생성형 AI 게이트웨이 호출을 위한 Custom LangChain LLM Wrapper
    """
    # api_url: str = "https://devx-llm-gw-api.shinsegae-inc.com/v1/chat/completions"
    # api_key: str = "sk-YFerB-BGuzWkCcBrFzorjA"
    # model_name: str = "bedrock/global.anthropic.claude-sonnet-4-6"
    # temperature: float = 0.0

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # LangChain 메시지 형식을 OpenAI/LiteLLM 호환 형식으로 변환
        formatted_messages = []
        for message in messages:
            if isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                role = "user"
            
            # content가 string인지 확인 (가끔 list 형태의 멀티모달 포맷일 수 있으므로 단순 변환 처리)
            content = message.content
            if not isinstance(content, str):
                content = str(content)
                
            formatted_messages.append({
                "role": role,
                "content": content
            })

        # HTTP 헤더 설정
        headers = {
            "Content-Type": "application/json",
            "x-litellm-api-key": self.api_key
        }

        # 요청 페이로드 설정
        payload = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": self.temperature,
            **kwargs
        }

        # Stop 시퀀스 처리
        if stop is not None:
            payload["stop"] = stop

        try:
            # API 호출
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
            
            # 응답 본문에서 텍스트 추출
            text = response_json["choices"][0]["message"]["content"]
            
            # LangChain ChatResult 객체 반환
            ai_message = AIMessage(content=text)
            generation = ChatGeneration(message=ai_message)
            return ChatResult(generations=[generation])
            
        except Exception as e:
            raise RuntimeError(f"사내 생성형 AI API 호출 오류: {e}")

    @property
    def _llm_type(self) -> str:
        return "company-llm-gateway"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        return {
            "api_url": self.api_url,
            "model_name": self.model_name,
            "temperature": self.temperature,
        }

# 직접 실행 테스트용 코드
if __name__ == "__main__":
    print("Custom LLM Wrapper 테스트 실행 중...")
    
    # 래퍼 생성
    llm = CompanyLLMWrapper(
        api_url="https://devx-llm-gw-api.shinsegae-inc.com/v1/chat/completions",
        api_key="sk-YFerB-BGuzWkCcBrFzorjA",
        model_name="bedrock/global.anthropic.claude-sonnet-4-6",
        temperature=0.0
    )
    
    # 테스트 메시지 전송
    test_messages = [
        SystemMessage(content="너는 유능한 AI 어시스턴트이다."),
        HumanMessage(content="자바가 뭐야? 한 문장으로 대답해줘.")
    ]
    
    try:
        result = llm.invoke(test_messages)
        print("성공! 응답 결과:")
        print(result.content)
    except Exception as e:
        print(f"테스트 실패: {e}")