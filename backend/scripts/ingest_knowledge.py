import argparse
import hashlib
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


def calculate_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a PDF document into the RAG vector DB.")
    parser.add_argument("pdf_path", type=str, help="Path to the PDF file")
    args = parser.parse_args()

    pdf_path = Path(args.pdf_path).resolve()
    if not pdf_path.exists():
        print(f"Error: File not found at {pdf_path}")
        return

    backend_root = Path(__file__).resolve().parents[1]
    load_dotenv(backend_root / ".env", override=False)

    print(f"Loading {pdf_path.name}...")
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()

    print(f"Loaded {len(docs)} pages. Splitting text...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} text chunks.")

    # Prepare metadata to match CareKnowledgeChunk requirements
    for i, chunk in enumerate(chunks):
        page_num = chunk.metadata.get("page", 0)
        chunk.metadata = {
            "source_id": f"doc_{pdf_path.stem}",
            "title": f"{pdf_path.stem} (Page {page_num})",
            "source_url": f"file://{pdf_path.name}",
            "content_hash": calculate_hash(chunk.page_content),
        }

    persist_directory = str(backend_root / ".chroma_db")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    print(f"Embedding and storing chunks into Chroma DB at {persist_directory}...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
        collection_name="care_knowledge",
    )
    
    print("Ingestion complete! ✨")


if __name__ == "__main__":
    main()
