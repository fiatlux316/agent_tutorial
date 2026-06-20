from crewai import Crew, Process
from agents import real_estate_researcher, report_writer
from tasks import search_task, analysis_task

# 외부 tool 활용
real_estate_crew = Crew(
    agents=[real_estate_researcher, report_writer],
    tasks=[search_task, analysis_task],
    process=Process.sequential,  # 검색 → 분석 순차 실행
    verbose=True,
)
result = real_estate_crew.kickoff(
    inputs={"question": "2026년 한국 부동산 시장 전망은 어때?"}
)
print("=== Crew Result ===")
print(result.raw) # 크루 단위 통합 결과(원문)
