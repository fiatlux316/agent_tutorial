"""
Chroma DB에 E5 임베딩 모델을 적용하기 위한 커스텀 어댑터
"""
from crewai.rag.embeddings.providers.custom.embedding_callable import CustomEmbeddingFunction
from crewai.rag.core.types import Documents, Embeddings
from embedding_model import E5QEmbeddings


class E5Embeddings(CustomEmbeddingFunction):
    """CrewAI의 CustomEmbeddingFunction을 상속한 E5 임베딩 래퍼"""
    
    def __init__(self):
        self.embedder = E5QEmbeddings()

    @staticmethod
    def name() -> str:
        return "E5Embeddings"
            
    def __call__(self, input: Documents) -> Embeddings:
        """
        input: List[str] (Documents)
        output: 임베딩 벡터 리스트 (정규화는 CrewAI 내부에서 자동 처리)
        """
        embeddings = []
        for text in input:
            embedding = self.embedder.embed_query(text)
            embeddings.append(embedding.tolist())
        return embeddings