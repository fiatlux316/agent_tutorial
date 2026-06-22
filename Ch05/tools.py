from crewai_tools import RagTool, SerperDevTool
#from embedding_adapter_chroma import E5ChromaEmbeddings
from embedding_adapter_custom import E5ChromaEmbeddings

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from crewai.tools import tool

# 로컬 E5 임베딩 어댑터 인스턴스 생성
custom_embeddings = E5ChromaEmbeddings()

# config 
config = {
    "vectordb": {
        "provider": "chromadb",
        "config": {
            "collection_name": "kb-collection",
            "embedding_function": custom_embeddings
        }
    },
    "chunker": {
        "chunk_size": 300,
        "chunk_overlap": 50,
        "length_function": "len",
        "min_chunk_size": 0 
    }
}

# 1) 웹 검색 전용 도구 : SerperDevTool
serper_tool = SerperDevTool(
    n_results=5,  # 상위 5개 결과만 사용
)

# 2) RAG 도구 생성 : RagTool
rag_tool = RagTool(
    name="MyDocsRAG",
    description="내 문서를 기반으로 질문에 답하는 RAG 툴",
    summarize=True,          # 검색 결과를 한 번 요약해서 응답에 사용
    verbose=True,             # 내부 동작 로깅
    config=config,
)

# KB 주택시장 리뷰 PDF 추가
rag_tool.add(
    data_type="file",
    path="./knowledge/KB주택시장리뷰_2026년 1월호.pdf",
)

# KB 연구보고서 리스트 페이지 추가
rag_tool.add(
    data_type="website",
    url="https://www.kbfg.com/kbresearch/report/reportList.do",
)


# 3) Custom Tool
# 3-1) 입력 스키마 정의 (Pydantic 기반)
class CurrencyInput(BaseModel):
    amount: float = Field(..., description="변환할 금액(숫자)")
    rate: float = Field(..., description="적용할 환율(예: 1325.5)")

# 3-2) BaseTool 상속하여 사용자 정의 도구 만들기
class CurrencyConverterTool(BaseTool):
    name: str = "환율 변환 도구"
    description: str = "주어진 금액을 환율에 따라 변환하여 반환합니다."
    args_schema: Type[BaseModel] = CurrencyInput

    def _run(self, amount: float, rate: float) -> str:
        """실행 로직"""
        result = amount * rate
        return f"{result:,.2f} 원"
    
currency_converter_tool = CurrencyConverterTool()
#print(currency_converter_tool.run(amount=100, rate=1325.5))


# 3-3) tool 데코레이터를 사용해 간단하게 사용자 정의 도구 만들기
@tool("환율 변환 도구")
def currency_converter(amount: float, rate: float) -> str:
    """주어진 금액(amount)에 환율(rate)을 적용하여 원화(KRW) 금액을 계산합니다."""
    result = amount * rate
    return f"{result:,.2f} 원"

# 실행 테스트
#print(currency_converter.run(amount=100, rate=1325.5))

