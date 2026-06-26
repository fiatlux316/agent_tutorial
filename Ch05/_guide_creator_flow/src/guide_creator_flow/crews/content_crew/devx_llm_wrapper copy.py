import os
import requests
from typing import Any, Dict, List, Optional, Union
from dotenv import load_dotenv
from pydantic import Field
from crewai.llms.base_llm import BaseLLM
from crewai.utilities.types import LLMMessage

# .env 파일 로드
load_dotenv()

class CompanyLLMWrapper(BaseLLM) :
    """
    회사 내부 생성형 AI 게이트웨이 호출을 위한 Custom CrewAI LLM Wrapper
    """    
    api_url: str = Field(default="https://devx-llm-gw-api.shinsegae-inc.com/v1/chat/completions")
    api_key: str = Field(default="sk-YFerB-BGuzWkCcBrFzorjA")
    
    # BaseLLM의 필드 오버라이드
    llm_type: str = "company-llm-gateway"
    model: str = Field(default="bedrock/global.anthropic.claude-sonnet-4-6")

    def call(
        self,
        messages: Union[str, List[LLMMessage]],
        tools: Optional[List[Dict[str, Any]]] = None,
        callbacks: Optional[List[Any]] = None,
        available_functions: Optional[Dict[str, Any]] = None,
        from_task: Optional[Any] = None,
        from_agent: Optional[Any] = None,
        response_model: Optional[Any] = None,
    ) -> str:
        # 메시지 포맷 변환
        formatted_messages = []
        if isinstance(messages, str):
            formatted_messages = [{"role": "user", "content": messages}]
        else:
            for msg in messages:
                content = msg.get("content", "")
                if not isinstance(content, str):
                    content = str(content)
                formatted_messages.append({
                    "role": msg.get("role", "user"),
                    "content": content
                })

        # HTTP 헤더 설정
        headers = {
            "Content-Type": "application/json",
            "x-litellm-api-key": self.api_key
        }

        # 요청 페이로드 설정
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": self.temperature or 0.0,
        }

        try:
            # API 호출
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            response_json = response.json()
            
            # 응답 본문에서 텍스트 추출
            return response_json["choices"][0]["message"]["content"]
            
        except Exception as e:
            raise RuntimeError(f"사내 생성형 AI API 호출 오류: {e}")

# 래퍼 생성 (.env 환경변수값 기반으로 명시적 초기화)
llm = CompanyLLMWrapper(
    model=os.getenv("DEVX_MODEL"),
    api_url=os.getenv("DEVX_API_URL"),
    llm_type=os.getenv("LLM_TYPE"),
    api_key=os.getenv("DEVX_API_KEY"),
    temperature=float(os.getenv("DEVX_TEMPERATURE"))
)