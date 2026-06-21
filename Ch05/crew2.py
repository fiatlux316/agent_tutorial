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
# 크루 단위 통합 결과(원문)
print(result.raw)
