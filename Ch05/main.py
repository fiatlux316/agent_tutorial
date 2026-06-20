from crewai import Crew, Process
from dotenv import load_dotenv
load_dotenv()

from agents import blog_agent, analyst, writer, real_estate_researcher, report_writer, gemini_llm
from tasks import write_blog_task, save_task, analyze_task, write_task, search_task, analysis_task

# blog_crew = Crew(
#     agents=[blog_agent],
#     tasks=[write_blog_task, save_task],
#     process=Process.sequential,
#     verbose=True
# )
# result = blog_crew.kickoff(inputs={"topic": "에이전트"})

# ai_trend_crew = Crew(
#     agents=[analyst, writer],
#     tasks=[analyze_task, write_task],
#     process=Process.sequential,
#     planning=True,
#     planning_llm=gemini_llm,
#     verbose=True
# )
# result = ai_trend_crew.kickoff(
#     inputs={"topic": "2026년 AI 트렌드"}
# )

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
print(result.raw)                             # 크루 단위 통합 결과(원문)

# print("\n=== Blog Generation Output (Pydantic) ===")
# print(write_blog_task.output.pydantic.model_dump())   # 블로그 원문(검증된 스키마)

# print("\n=== Summary Output (Markdown) ===")
# print(save_task.output.raw)                  # 요약본 마크다운 결과
