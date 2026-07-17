import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Schema / Index version constraint
SCHEMA_VERSION = "1.0"

class RAGService:
    """
    Service managing document chunking, lazy embedding generation, FAISS index construction,
    atomic persistence, and semantic similarity searching.
    """
    def __init__(self):
        self.vector_store_path = Path(settings.VECTOR_STORE_PATH).resolve()
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._metadata: Optional[List[Dict[str, Any]]] = None
        self._manifest: Optional[Dict[str, Any]] = None

    def get_embedding_model(self) -> SentenceTransformer:
        """
        Lazily loads the multilingual SentenceTransformer model.
        Prevents memory footprint during health/auth startup.
        """
        if self._model is None:
            logger.info(f"Initializing embedding model: {settings.EMBEDDING_MODEL_NAME}...")
            # Load sentence transformer model locally (cached after first download)
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return self._model

    def chunk_document(
        self, 
        pages: List[Dict[str, Any]], 
        doc_checksum: str, 
        chunk_size: int = None, 
        chunk_overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        Partitions page text blocks into semantically bounded overlapping chunks.
        Appends deterministic source-aware chunk IDs and metadata.
        """
        c_size = chunk_size or settings.CHUNK_SIZE
        c_overlap = chunk_overlap or settings.CHUNK_OVERLAP

        if c_size <= 0:
            raise ValueError("Chunk size must be positive.")
        if c_overlap < 0:
            raise ValueError("Chunk overlap must be non-negative.")
        if c_overlap >= c_size:
            raise ValueError("Chunk overlap must be smaller than chunk size.")

        chunks = []
        chunk_idx = 0

        # Extract pages content details
        for page in pages:
            text = page["text"]
            page_num = page["page_number"]
            source_rel_path = page["source_relative_path"]
            doc_title = page["document_title"]
            filename = page["source_filename"]

            if not text:
                continue

            # Sub-split text by semantic dividers (paragraphs or sentences)
            splits = text.split("\n\n")
            
            buffer = ""
            for split in splits:
                split = split.strip()
                if not split:
                    continue
                
                # If adding this split exceeds chunk_size, flush buffer first
                if len(buffer) + len(split) > c_size:
                    if buffer:
                        chunks.append(self._create_chunk_record(
                            text=buffer,
                            page_start=page_num,
                            page_end=page_num,
                            chunk_index=chunk_idx,
                            source_filename=filename,
                            source_relative_path=source_rel_path,
                            document_title=doc_title,
                            doc_checksum=doc_checksum
                        ))
                        chunk_idx += 1
                        
                        # Retain overlap character buffer
                        buffer = buffer[-c_overlap:] + " " + split
                    else:
                        # Split is larger than chunk size itself, force split it
                        words = split.split(" ")
                        temp_buffer = ""
                        for word in words:
                            if len(temp_buffer) + len(word) > c_size:
                                chunks.append(self._create_chunk_record(
                                    text=temp_buffer.strip(),
                                    page_start=page_num,
                                    page_end=page_num,
                                    chunk_index=chunk_idx,
                                    source_filename=filename,
                                    source_relative_path=source_rel_path,
                                    document_title=doc_title,
                                    doc_checksum=doc_checksum
                                ))
                                chunk_idx += 1
                                temp_buffer = temp_buffer[-c_overlap:] + " " + word
                            else:
                                temp_buffer += " " + word
                        buffer = temp_buffer.strip()
                else:
                    if buffer:
                        buffer += "\n\n" + split
                    else:
                        buffer = split

            # Flush remaining buffer for this page
            if buffer.strip():
                chunks.append(self._create_chunk_record(
                    text=buffer.strip(),
                    page_start=page_num,
                    page_end=page_num,
                    chunk_index=chunk_idx,
                    source_filename=filename,
                    source_relative_path=source_rel_path,
                    document_title=doc_title,
                    doc_checksum=doc_checksum
                ))
                chunk_idx += 1

        return chunks

    def _create_chunk_record(
        self,
        text: str,
        page_start: int,
        page_end: int,
        chunk_index: int,
        source_filename: str,
        source_relative_path: str,
        document_title: str,
        doc_checksum: str
    ) -> Dict[str, Any]:
        """
        Creates a structured chunk metadata dictionary with deterministic source-aware ID.
        """
        normalized_text = " ".join(text.lower().split())
        
        # Deterministic source-aware ID format: prevents collisions of identical texts
        raw_id_seed = f"{doc_checksum}_{source_relative_path}_p{page_start}-{page_end}_i{chunk_index}_{normalized_text}"
        chunk_id = hashlib.sha256(raw_id_seed.encode("utf-8")).hexdigest()

        return {
            "chunk_id": chunk_id,
            "source_filename": source_filename,
            "source_relative_path": source_relative_path,
            "document_title": document_title,
            "page_start": page_start,
            "page_end": page_end,
            "chunk_index": chunk_index,
            "text": text,
            "character_count": len(text),
            "document_checksum": doc_checksum,
            "ingestion_timestamp": int(time.time()),
            "schema_version": SCHEMA_VERSION
        }

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generates normalized sentence embeddings in batches.
        Detects and rejects empty inputs, NaNs, or inf values.
        """
        if not texts:
            return np.empty((0, 0), dtype=np.float32)

        # Validate inputs
        for idx, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Empty or whitespace-only text found at index {idx}.")

        model = self.get_embedding_model()
        
        # Batch embedding generation, normalize vectors for cosine similarity (dot product)
        embeddings = model.encode(
            texts, 
            batch_size=settings.EMBEDDING_BATCH_SIZE, 
            normalize_embeddings=True,
            show_progress_bar=False
        )
        
        # Convert to float32 numpy array
        embeddings_arr = np.array(embeddings, dtype=np.float32)

        # Rejection of invalid floats
        if np.isnan(embeddings_arr).any() or np.isinf(embeddings_arr).any():
            raise ValueError("Generated embedding contains NaN or infinite values.")

        return embeddings_arr

    def save_vector_store(
        self, 
        embeddings: np.ndarray, 
        metadata: List[Dict[str, Any]], 
        manifest: Dict[str, Any]
    ) -> None:
        """
        Atomically persists FAISS index, metadata, and manifest.
        Validates artifact counts, embedding dimensions, model tag, and schemas before activation.
        Updates manifest.json last to guarantee index consistency.
        """
        if len(embeddings) != len(metadata):
            raise ValueError(
                f"Embedding vector count ({len(embeddings)}) must match metadata "
                f"record count ({len(metadata)})."
            )

        dimension = embeddings.shape[1] if len(embeddings) > 0 else 384
        
        # Build FAISS Flat Inner Product index (ideal for normalized cosine similarity vectors)
        index = faiss.IndexFlatIP(dimension)
        if len(embeddings) > 0:
            index.add(embeddings)

        # Build absolute paths for vector store targets
        os.makedirs(self.vector_store_path, exist_ok=True)
        index_path = self.vector_store_path / "index.faiss"
        meta_path = self.vector_store_path / "metadata.json"
        manifest_path = self.vector_store_path / "manifest.json"

        # Tmp paths for atomic writes
        index_tmp = self.vector_store_path / "index.faiss.tmp"
        meta_tmp = self.vector_store_path / "metadata.json.tmp"
        manifest_tmp = self.vector_store_path / "manifest.json.tmp"

        try:
            # 1. Write FAISS Index
            faiss.write_index(index, str(index_tmp))

            # 2. Write metadata.json
            with open(meta_tmp, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 3. Write manifest.json
            complete_manifest = {
                "schema_version": SCHEMA_VERSION,
                "embedding_model": settings.EMBEDDING_MODEL_NAME,
                "embedding_dimension": dimension,
                "vector_count": len(metadata),
                "timestamp": int(time.time()),
                **manifest
            }
            with open(manifest_tmp, "w", encoding="utf-8") as f:
                json.dump(complete_manifest, f, ensure_ascii=False, indent=2)

            # 4. Atomic verification: reload tmp files to check integrity
            loaded_index = faiss.read_index(str(index_tmp))
            if loaded_index.ntotal != len(metadata):
                raise ValueError("FAISS temporary index vector count mismatch on validation.")
            if loaded_index.d != dimension:
                raise ValueError("FAISS temporary index dimension mismatch on validation.")

            # 5. Rename temporary files to active files (activate manifest last)
            if os.path.exists(index_tmp):
                if os.path.exists(index_path):
                    os.remove(index_path)
                os.rename(index_tmp, index_path)

            if os.path.exists(meta_tmp):
                if os.path.exists(meta_path):
                    os.remove(meta_path)
                os.rename(meta_tmp, meta_path)

            if os.path.exists(manifest_tmp):
                if os.path.exists(manifest_path):
                    os.remove(manifest_path)
                os.rename(manifest_tmp, manifest_path)

            logger.info("Successfully persisted vector store atomically.")

            # Refresh local variables in memory
            self._index = index
            self._metadata = metadata
            self._manifest = complete_manifest

        except Exception as e:
            logger.error(f"Atomic persistence failed: {e}")
            # Clean up temporary files on failures
            for path in [index_tmp, meta_tmp, manifest_tmp]:
                if os.path.exists(path):
                    try:
                        os.remove(path)
                    except Exception:
                        pass
            raise

    def load_vector_store(self) -> None:
        """
        Lazily loads FAISS index, metadata, and manifest into memory.
        Validates index/metadata compatibility, schemas, dimensions, and model configurations.
        """
        # Return if already loaded
        if self._index is not None and self._metadata is not None:
            return

        index_path = self.vector_store_path / "index.faiss"
        meta_path = self.vector_store_path / "metadata.json"
        manifest_path = self.vector_store_path / "manifest.json"

        if not index_path.exists() or not meta_path.exists() or not manifest_path.exists():
            raise FileNotFoundError("Vector store files are missing. Please build the index first.")

        try:
            # 1. Load and parse manifest
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

            # Validate schema and model configurations
            if manifest.get("schema_version") != SCHEMA_VERSION:
                raise ValueError("Unsupported vector store schema version.")
            if manifest.get("embedding_model") != settings.EMBEDDING_MODEL_NAME:
                raise ValueError(
                    f"Model mismatch. Configured: {settings.EMBEDDING_MODEL_NAME}, "
                    f"Index built with: {manifest.get('embedding_model')}"
                )

            # 2. Load FAISS index
            index = faiss.read_index(str(index_path))

            # Validate index dimension and count specs
            expected_dim = manifest.get("embedding_dimension")
            if index.d != expected_dim:
                raise ValueError(f"FAISS index dimension {index.d} mismatches manifest {expected_dim}.")
            
            expected_count = manifest.get("vector_count")
            if index.ntotal != expected_count:
                raise ValueError(f"FAISS index count {index.ntotal} mismatches manifest {expected_count}.")

            # 3. Load Metadata JSON
            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Validate index/metadata count consistency
            if len(metadata) != index.ntotal:
                raise ValueError(
                    f"Index vector count ({index.ntotal}) is incompatible with "
                    f"metadata records ({len(metadata)})."
                )

            self._index = index
            self._metadata = metadata
            self._manifest = manifest
            logger.info("Successfully loaded vector store and validated configuration bounds.")

        except Exception as e:
            logger.error(f"Failed to load or validate vector store: {e}")
            # Reset states on failures
            self._index = None
            self._metadata = None
            self._manifest = None
            raise ValueError(f"Vector store is corrupted or incompatible: {e}")

    def query_similarity(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Executes local semantic similarity searches against the loaded FAISS store.
        """
        k = top_k or settings.RETRIEVAL_TOP_K
        if k <= 0:
            raise ValueError("top_k must be a positive integer.")

        if not query or not query.strip():
            return []

        # Ensure index is loaded and validated
        self.load_vector_store()
        
        # Generate query vector
        query_vector = self.generate_embeddings([query])
        
        # Search FAISS
        # FlatIP index returns inner product, which is identical to cosine similarity on L2-normalized vectors.
        scores, indices = self._index.search(query_vector, k)

        results = []
        raw_scores = scores[0]
        raw_indices = indices[0]

        for score, idx in zip(raw_scores, raw_indices):
            # FAISS returns -1 for unmapped index hits
            if idx < 0 or idx >= len(self._metadata):
                continue

            # Skip results falling below the configured threshold
            # Cosine similarity score ranges from -1 to 1. 0.0 is default.
            if score < settings.RETRIEVAL_SCORE_THRESHOLD:
                continue

            chunk_meta = self._metadata[idx]
            results.append({
                "chunk_id": chunk_meta["chunk_id"],
                "text": chunk_meta["text"],
                "source_filename": chunk_meta["source_filename"],
                "document_title": chunk_meta["document_title"],
                "page_start": chunk_meta["page_start"],
                "page_end": chunk_meta["page_end"],
                "similarity_score": float(score),
                "chunk_metadata": {
                    "source_relative_path": chunk_meta["source_relative_path"],
                    "character_count": chunk_meta["character_count"],
                    "chunk_index": chunk_meta["chunk_index"],
                    "ingestion_timestamp": chunk_meta["ingestion_timestamp"]
                }
            })

        return results

rag_service = RAGService()
