from crewai import Crew, Process
from agents import knowledge_agent
from tasks import knowledge_task
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

# knowledge base 기반 crew
# 로컬 임베딩 함수를 어떻게 설정할 것인가 ?
pdf_source = PDFKnowledgeSource(
    file_paths=["./knowledge/KB주택시장리뷰_2026년 1월호.pdf", 
                "./knowledge/KB주택시장리뷰_2025년 12월호.pdf"]
)
knowledge_crew = Crew(
    agents=[knowledge_agent],
    tasks=[knowledge_task],
    knowledge_sources=[pdf_source],
    process=Process.sequential,
)
result = knowledge_crew.kickoff(
    inputs={"question": "2026년 한국 부동산 시장 전망은 어때?"}
)

print("=== Crew Result ===")
print(result.raw) # 크루 단위 통합 결과(원문)
