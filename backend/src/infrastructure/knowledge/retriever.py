from __future__ import annotations

import uuid
from pathlib import Path

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from domain.models import CareKnowledgeChunk, CareKnowledgeHit


class CareKnowledgeRetriever:
    def __init__(self, persist_directory: str | None = None) -> None:
        if persist_directory is None:
            backend_root = Path(__file__).resolve().parents[3]
            persist_directory = str(backend_root / ".chroma_db")
            
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self._vector_store = Chroma(
            collection_name="care_knowledge",
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )

    def search(self, question: str, limit: int = 3) -> tuple[CareKnowledgeHit, ...]:
        results = self._vector_store.similarity_search_with_relevance_scores(
            query=question,
            k=limit,
        )
        
        hits = []
        for doc, score in results:
            # We enforce a minimum threshold (e.g., 0.5) to ensure relevance
            if score < 0.5:
                continue
                
            chunk = CareKnowledgeChunk(
                id=str(uuid.uuid4()),  # Temporary ID for the hit
                source_id=doc.metadata.get("source_id", "unknown"),
                title=doc.metadata.get("title", "Unknown Source"),
                text=doc.page_content,
                source_url=doc.metadata.get("source_url", ""),
                content_hash=doc.metadata.get("content_hash", ""),
            )
            hits.append(CareKnowledgeHit(chunk=chunk, score=float(score)))
            
        return tuple(hits)
