from crewai import Crew, Process
from agents import blog_agent
from tasks import write_blog_task, save_task

# 기본 crew
blog_crew = Crew(
    agents=[blog_agent],
    tasks=[write_blog_task, save_task],
    process=Process.sequential,
    verbose=True
)
result = blog_crew.kickoff(inputs={"topic": "에이전트"})


print("=== Crew Result ===")
# 크루 단위 통합 결과(원문)
print(result.raw) 

print("\n=== Blog Generation Output (Pydantic) ===")
# 블로그 원문(검증된 스키마)
print(write_blog_task.output.pydantic.model_dump())   

print("\n=== Summary Output (Markdown) ===")
# 요약본 마크다운 결과
print(save_task.output.raw)          
