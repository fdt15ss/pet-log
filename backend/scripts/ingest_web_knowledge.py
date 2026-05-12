from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from infrastructure.knowledge.pipeline import WebKnowledgeIngestionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Search, evaluate, and ingest web knowledge into Chroma.")
    parser.add_argument("query", type=str, help="Search query to ingest")
    parser.add_argument("--limit", type=int, default=5, help="Maximum Tavily results to evaluate")
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[1]
    load_dotenv(backend_root / ".env", override=False)

    pipeline = WebKnowledgeIngestionPipeline()
    report = pipeline.ingest_query(args.query, limit=args.limit)

    print(f"Query: {report.query}")
    print(f"Searched: {report.searched_count}")
    print(f"Evaluated: {report.evaluated_count}")
    print(f"Accepted: {report.accepted_count}")
    print(f"Inserted chunks: {report.inserted_count}")
    print(f"Skipped rejected: {report.skipped_rejected_count}")
    print(f"Skipped duplicate: {report.skipped_duplicate_count}")
    print(f"Skipped empty: {report.skipped_empty_count}")


if __name__ == "__main__":
    main()
