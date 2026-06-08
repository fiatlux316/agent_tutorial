from pydantic import BaseModel, Field


##### 출력 구조화 
print("\n=== 출력 구조화 예시 ===\n")

# 1) 스키마 정의
class SearchQuery(BaseModel):
    search_query: str = Field(..., description="웹 검색에 최적화된 질의문")
    justification: str = Field(..., description="해당 질의가 왜 적절한지의 근거")

# 2) 구조화된 출력으로 LLM 래핑
from llm import get_llm
llm = get_llm()
structured_llm = llm.with_structured_output(SearchQuery)

# 3) 프롬프트 실행
prompt = "랭그래프가 왜 필요한가?"
result = structured_llm.invoke(prompt)

# 4) 사용
print("검색어:", result.search_query)
print("근거:", result.justification)

