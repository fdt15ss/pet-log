# CareAnswerProvider RAG

`CareAnswerProvider` will answer guardian care questions with two context sources:

- `CareContext`: pet profile, recent records, and due reminders.
- care knowledge retrieval: administrator-approved external care guide URLs.

This document defines the RAG boundary only. It does not implement URL fetching, HTML parsing, chunking, embedding calls, vector search, or prompt injection into answers.

## Source Policy

- v1 uses an administrator allowlist for external URLs or domains.
- Arbitrary guardian-submitted URLs are not fetched.
- Each source keeps its original URL and title so answers can cite where care guidance came from.
- Medical wording remains constrained: retrieved text can inform general guidance, but answers must not diagnose, prescribe, or claim certainty.

## Data Shape

- `CareKnowledgeSource`: approved external URL metadata.
- `CareKnowledgeChunk`: normalized text chunk with source URL and content hash.
- `CareKnowledgeHit`: retrieved chunk plus similarity score.

The MVP storage target is SQLite. Embedding vectors may be stored as JSON or BLOB columns in a future implementation. That storage choice is an implementation detail behind repository and retriever interfaces so it can later move to pgvector or an external vector database.

## Flow

1. Admin approves a source URL/domain.
2. Ingestion fetches the URL, extracts readable text, chunks it, and stores chunks.
3. Embedding provider creates an OpenAI embedding for each chunk.
4. Retriever embeds the guardian question and returns the most relevant chunks.
5. `CareAnswerProvider` includes selected snippets in the answer prompt.

## Skeleton Boundaries

- `CareKnowledgeIngestionInterface` owns source-to-chunk ingestion.
- `EmbeddingProviderInterface` owns OpenAI embeddings.
- `CareKnowledgeRetrieverInterface` owns question-to-hit retrieval.
- `CareAnswerProvider` may accept an optional retriever dependency, but answer behavior stays unchanged until retrieval is implemented.

## Defaults

- Embedding model default: `text-embedding-3-small`.
- Environment override: `OPENAI_CARE_KNOWLEDGE_EMBEDDING_MODEL`.
- Existing answer model remains controlled by `OPENAI_CARE_ANSWER_MODEL`.

## Deferred Work

- URL fetching and SSRF protections.
- HTML readability extraction.
- Chunking strategy.
- Embedding persistence.
- Similarity scoring and top-k search.
- Prompt formatting with citations.
- RAG quality tests and safety evals.
