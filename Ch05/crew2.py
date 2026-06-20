from crewai import Crew, Process
from agents import llm, analyst, writer
from tasks import analyze_task, write_task


ai_trend_crew = Crew(
    agents=[analyst, writer],
    tasks=[analyze_task, write_task],
    process=Process.sequential,
    planning=True,
    planning_llm=llm,
    verbose=True
)
result = ai_trend_crew.kickoff(
    inputs={"topic": "2026년 AI 트렌드"}
)

print("=== Crew Result ===")
print(result.raw) # 크루 단위 통합 결과(원문)

# print("\n=== Blog Generation Output (Pydantic) ===")
# print(write_blog_task.output.pydantic.model_dump())   # 블로그 원문(검증된 스키마)

# print("\n=== Summary Output (Markdown) ===")
# print(save_task.output.raw)                  # 요약본 마크다운 결과
