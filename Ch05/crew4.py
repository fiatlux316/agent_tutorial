# Knowledge Base 기반 Crew  (커스텀 임베딩 함수 적용)
# 추론 모드 적용

from crewai import Crew, Process
from agents import knowledge_agent
from tasks import knowledge_task
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.rag.embeddings.providers.custom.custom_provider import CustomProvider
from embedding_custom_adapter import E5Embeddings

pdf_source = PDFKnowledgeSource(
    file_paths=["KB주택시장리뷰_2026년 1월호.pdf", 
                "KB주택시장리뷰_2025년 12월호.pdf"]
)
knowledge_crew = Crew(
    agents=[knowledge_agent],
    tasks=[knowledge_task],
    knowledge_sources=[pdf_source],
    embedder=CustomProvider(embedding_callable=E5Embeddings),
    process=Process.sequential,
    verbose=True
)
result = knowledge_crew.kickoff(
    inputs={"question": "2026년 1월호와 2025년 12월호에서 공통으로 강조하는 시장 리스크는 무엇인가?"}
)

print("=== Crew Result ===")
# 크루 단위 통합 결과(원문)
print(result.raw)   