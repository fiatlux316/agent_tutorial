# RAG Tool

from crewai_tools import RagTool, SerperDevTool
from embedding_adapter_chroma import E5ChromaEmbeddings

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

# 1) SerperDevTool 정의 (웹 검색 전용 도구)
serper_tool = SerperDevTool(
    n_results=5,  # 상위 5개 결과만 사용
)


# 1) RAG 도구 생성 (기본 설정)
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

# # 3) 질문하기
# question = "서울 및 수도권 아파트 시장"
# answer = rag_tool.run(question)

# print("Q:", question)
# print("A:", answer)




