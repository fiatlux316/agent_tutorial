from crewai import Crew, Process
from agents import knowledge_agent
from tasks import knowledge_task
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource
from crewai.rag.embeddings.providers.custom.custom_provider import CustomProvider
from embedding_custom_adapter import E5Embeddings

# knowledge base 기반 crew
# 로컬 E5 임베딩 모델 사용
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
)
result = knowledge_crew.kickoff(
    inputs={"question": "2026년 한국 부동산 시장 전망은 어때?"}
)

print("=== Crew Result ===")
# 크루 단위 통합 결과(원문)
print(result.raw)   