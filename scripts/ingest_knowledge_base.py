import os
import sys
import argparse
import hashlib
import time
import logging
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Adjust sys.path to resolve backend imports from repository root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import settings
from backend.services.document_service import document_service
from backend.services.rag_service import rag_service

# Set up logging for CLI execution
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ingest_cli")

def calculate_checksum(filepath: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    """
    sha255 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha255.update(chunk)
    return sha255.hexdigest()

def check_should_skip(discovered_docs: List[Path], manifest_path: Path) -> bool:
    """
    Checks if the complete document set and their checksums are unchanged
    compared to the active manifest.json.
    """
    if not manifest_path.exists():
        logger.info("Manifest file does not exist. Full rebuild required.")
        return False

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        manifest_docs = manifest.get("documents", {})
        
        # Check matching counts
        if len(discovered_docs) != len(manifest_docs):
            logger.info(
                f"Document count mismatch. Discovered: {len(discovered_docs)}, "
                f"Manifest has: {len(manifest_docs)}. Rebuild required."
            )
            return False

        # Compare path keys and file checksums
        base_path = Path(settings.KNOWLEDGE_BASE_PATH).resolve()
        for doc_path in discovered_docs:
            rel_path = str(doc_path.resolve().relative_to(base_path)).replace("\\", "/")
            if rel_path not in manifest_docs:
                logger.info(f"New document discovered: '{rel_path}'. Rebuild required.")
                return False

            current_hash = calculate_checksum(doc_path)
            manifest_hash = manifest_docs[rel_path].get("checksum")
            if current_hash != manifest_hash:
                logger.info(f"Document modified: '{rel_path}'. Rebuild required.")
                return False

        return True
    except Exception as e:
        logger.warning(f"Error reading manifest file, forcing rebuild: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Nexora AI Support Hub Knowledge Base Ingestion CLI")
    parser.add_argument(
        "--rebuild", 
        action="store_true", 
        help="Force a complete rebuilding of the local FAISS vector store index."
    )
    args = parser.parse_args()

    start_time = time.time()
    logger.info("Starting knowledge base ingestion check...")

    # 1. Discover PDFs
    discovered_pdfs = document_service.discover_documents()
    if not discovered_pdfs:
        logger.error("No supported PDF documents discovered in knowledge base directory.")
        sys.exit(1)

    logger.info(f"Discovered {len(discovered_pdfs)} PDF document(s) in knowledge base.")

    # 2. Check for changes (Idempotency)
    manifest_path = Path(settings.VECTOR_STORE_PATH).resolve() / "manifest.json"
    
    if check_should_skip(discovered_pdfs, manifest_path) and not args.rebuild:
        logger.info("All documents and checksums are unchanged. Skipping index rebuild.")
        logger.info("Ingestion completed successfully (no changes detected).")
        sys.exit(0)

    logger.info("Rebuilding vector store index...")

    # 3. Process documents page by page
    all_chunks = []
    processed_manifest = {}
    failed_docs = []
    total_pages = 0

    base_path = Path(settings.KNOWLEDGE_BASE_PATH).resolve()

    for pdf_path in discovered_pdfs:
        rel_path = str(pdf_path.resolve().relative_to(base_path)).replace("\\", "/")
        logger.info(f"Processing document: '{rel_path}'...")
        try:
            doc_checksum = calculate_checksum(pdf_path)
            
            # Extract page blocks
            pages = document_service.extract_pages(pdf_path)
            pages_count = len(pages)
            total_pages += pages_count

            # Create semantic chunks
            doc_chunks = rag_service.chunk_document(pages, doc_checksum)
            all_chunks.extend(doc_chunks)

            # Record document details in manifest
            processed_manifest[rel_path] = {
                "filename": pdf_path.name,
                "checksum": doc_checksum,
                "pages": pages_count,
                "chunks": len(doc_chunks),
                "title": pages[0]["document_title"] if pages_count > 0 else pdf_path.stem
            }
            logger.info(f"Successfully processed '{rel_path}' ({pages_count} pages, {len(doc_chunks)} chunks).")

        except Exception as e:
            logger.error(f"Failed to process document '{rel_path}': {e}")
            failed_docs.append((rel_path, str(e)))

    # If any document failed, fail the build to protect store integrity
    if failed_docs:
        logger.error("Ingestion aborted. The following documents failed processing:")
        for doc_name, err in failed_docs:
            logger.error(f"  - {doc_name}: {err}")
        sys.exit(1)

    if not all_chunks:
        logger.error("No chunks generated across all documents. Aborting rebuild.")
        sys.exit(1)

    # 4. Generate embeddings
    logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
    chunk_texts = [chunk["text"] for chunk in all_chunks]
    
    try:
        embeddings = rag_service.generate_embeddings(chunk_texts)
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        sys.exit(1)

    # 5. Persist RAG Store atomically
    manifest_payload = {
        "documents": processed_manifest,
        "total_documents": len(processed_manifest),
        "total_pages": total_pages,
        "total_chunks": len(all_chunks)
    }

    try:
        rag_service.save_vector_store(
            embeddings=embeddings,
            metadata=all_chunks,
            manifest=manifest_payload
        )
    except Exception as e:
        logger.error(f"Failed to persist vector store artifacts: {e}")
        sys.exit(1)

    elapsed = time.time() - start_time
    
    # 6. Concise final summary print
    print("\n" + "="*50)
    print("KNOWLEDGE INGESTION COMPLETE")
    print("="*50)
    print(f"Documents Discovered : {len(discovered_pdfs)}")
    print(f"Processed Successfully: {len(processed_manifest)}")
    print(f"Failed Documents     : {len(failed_docs)}")
    print(f"Total Pages Extracted: {total_pages}")
    print(f"Total Chunks Created : {len(all_chunks)}")
    print(f"Embedding Model      : {settings.EMBEDDING_MODEL_NAME}")
    print(f"Embedding Dimension  : {embeddings.shape[1]}")
    print(f"Vector Store Path    : {settings.VECTOR_STORE_PATH}")
    print(f"Time Elapsed (sec)   : {elapsed:.2f}")
    print("="*50 + "\n")

    sys.exit(0)

if __name__ == "__main__":
    main()
