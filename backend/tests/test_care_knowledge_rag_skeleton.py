from __future__ import annotations

import unittest
from pathlib import Path

from application.interfaces import (
    CareKnowledgeIngestionInterface,
    CareKnowledgeRetrieverInterface,
    EmbeddingProviderInterface,
)
from domain.models import CareKnowledgeChunk, CareKnowledgeHit, CareKnowledgeSource
from infrastructure.knowledge import (
    CareKnowledgeRepository,
    CareKnowledgeRetriever,
    OpenAIEmbeddingProvider,
    UrlCareKnowledgeIngestor,
)


class TestCareKnowledgeRagSkeleton(unittest.TestCase):
    def test_domain_models_capture_external_knowledge_metadata(self) -> None:
        source = CareKnowledgeSource(
            id="source-1",
            url="https://example.org/care/feeding",
            title="Feeding guide",
            allowed_domain="example.org",
        )
        chunk = CareKnowledgeChunk(
            id="chunk-1",
            source_id=source.id,
            title=source.title,
            text="Feed transitions should be gradual.",
            source_url=source.url,
            content_hash="hash-1",
        )
        hit = CareKnowledgeHit(chunk=chunk, score=0.91)

        self.assertTrue(source.enabled)
        self.assertEqual(hit.chunk.source_url, source.url)
        self.assertEqual(hit.score, 0.91)

    def test_interfaces_are_exported_with_expected_methods(self) -> None:
        self.assertTrue(hasattr(CareKnowledgeRetrieverInterface, "search"))
        self.assertTrue(hasattr(CareKnowledgeIngestionInterface, "ingest"))
        self.assertTrue(hasattr(EmbeddingProviderInterface, "embed"))

    def test_infrastructure_skeletons_do_not_implement_runtime_behavior(self) -> None:
        source = CareKnowledgeSource(
            id="source-1",
            url="https://example.org/care/feeding",
            title="Feeding guide",
            allowed_domain="example.org",
        )
        repository = CareKnowledgeRepository()
        embedding_provider = OpenAIEmbeddingProvider(api_key="test-key", model="test-embedding-model")
        retriever = CareKnowledgeRetriever(repository=repository, embedding_provider=embedding_provider)
        ingestor = UrlCareKnowledgeIngestor(allowed_domains=("example.org",))

        with self.assertRaises(NotImplementedError):
            repository.save_source(source)
        with self.assertRaises(NotImplementedError):
            embedding_provider.embed("feeding")
        with self.assertRaises(NotImplementedError):
            retriever.search("밥을 잘 안 먹어요", limit=3)
        with self.assertRaises(NotImplementedError):
            ingestor.ingest(source)

    def test_design_doc_and_sprint_card_exist(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        design_doc = repo_root / "docs/superpowers/designs/pet-log-pipeline/13-care-answer-rag.md"
        sprint_card = (
            repo_root
            / "docs/superpowers/plans/pet-log-agent-sprints/cards/sprint-06/6-18-care-knowledge-rag-skeleton.md"
        )

        self.assertIn("CareAnswerProvider", design_doc.read_text())
        self.assertIn("OpenAI embeddings", design_doc.read_text())
        self.assertIn("내부 구현 없음", sprint_card.read_text())


if __name__ == "__main__":
    unittest.main()
