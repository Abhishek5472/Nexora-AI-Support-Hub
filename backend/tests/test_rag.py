import os
import json
import time
import pytest
import numpy as np
import faiss
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.core.config import settings
from backend.services.document_service import document_service
from backend.services.rag_service import rag_service
from backend.main import app

client = TestClient(app)

@pytest.fixture
def mock_rag_paths(tmp_path):
    """
    Fixture overriding base paths to sandbox all vectorstore and PDF actions.
    """
    old_kb = settings.KNOWLEDGE_BASE_PATH
    old_vs = settings.VECTOR_STORE_PATH
    
    kb_path = tmp_path / "knowledge_base"
    vs_path = tmp_path / "vectorstore"
    
    os.makedirs(kb_path, exist_ok=True)
    os.makedirs(vs_path, exist_ok=True)
    
    settings.KNOWLEDGE_BASE_PATH = str(kb_path)
    settings.VECTOR_STORE_PATH = str(vs_path)
    
    # Reload paths inside services
    document_service.base_path = kb_path.resolve()
    rag_service.vector_store_path = vs_path.resolve()
    
    yield kb_path, vs_path
    
    settings.KNOWLEDGE_BASE_PATH = old_kb
    settings.VECTOR_STORE_PATH = old_vs
    document_service.base_path = Path(old_kb).resolve()
    rag_service.vector_store_path = Path(old_vs).resolve()

@pytest.fixture
def mock_embedding_transformer():
    """
    Fixture patching SentenceTransformer to return L2-normalized dummy unit vectors.
    """
    with patch("backend.services.rag_service.SentenceTransformer") as mock_class:
        mock_instance = MagicMock()
        
        def mock_encode(texts, **kwargs):
            n = len(texts) if isinstance(texts, list) else 1
            # Generate dummy 384 dimensional unit vectors
            vectors = np.ones((n, 384), dtype=np.float32)
            # L2 normalize
            norms = np.linalg.norm(vectors, axis=1, keepdims=True)
            return vectors / norms

        mock_instance.encode.side_effect = mock_encode
        mock_class.return_value = mock_instance
        
        # Reset rag_service internal model state to trigger reload
        rag_service._model = None
        rag_service._index = None
        rag_service._metadata = None
        rag_service._manifest = None
        
        yield mock_instance
        
        rag_service._model = None
        rag_service._index = None
        rag_service._metadata = None
        rag_service._manifest = None

# ==============================================================================
# Document Discovery & Validation Tests
# ==============================================================================

def test_discover_documents_filtering(mock_rag_paths):
    kb_path, _ = mock_rag_paths
    
    # Create mock directory structures
    (kb_path / "FAQ.pdf").touch()
    (kb_path / "UserManual.pdf").touch()
    (kb_path / "notes.txt").touch()  # Unsupported extension
    (kb_path / ".gitkeep").touch()   # Hidden file
    (kb_path / "subfolder").mkdir(exist_ok=True)
    (kb_path / "subfolder" / "Warranty.pdf").touch()  # Recursive discovery
    (kb_path / "subfolder" / ".~temp.pdf").touch()    # Temp file prefix
    
    docs = document_service.discover_documents()
    
    # Assert only valid PDFs are discovered and sorted deterministically
    assert len(docs) == 3
    filenames = [d.name for d in docs]
    assert filenames == ["FAQ.pdf", "UserManual.pdf", "Warranty.pdf"]

def test_path_traversal_prevention(mock_rag_paths):
    kb_path, _ = mock_rag_paths
    unsafe_path = kb_path / "../outside.pdf"
    
    with pytest.raises(ValueError, match="Path traversal"):
        document_service.validate_file(unsafe_path)

def test_file_size_and_type_validations(mock_rag_paths):
    kb_path, _ = mock_rag_paths
    
    empty_file = kb_path / "empty.pdf"
    empty_file.touch()
    with pytest.raises(ValueError, match="empty"):
        document_service.validate_file(empty_file)

    large_file = kb_path / "oversized.pdf"
    large_file.write_text("some oversized pdf content")
    with patch.object(Path, "stat") as mock_stat:
        mock_res = MagicMock()
        mock_res.st_size = 11 * 1024 * 1024
        mock_stat.return_value = mock_res
        with pytest.raises(ValueError, match="exceeds"):
            document_service.validate_file(large_file)

# ==============================================================================
# PDF Extraction Tests
# ==============================================================================

def test_pdf_extraction_page_preservations(mock_rag_paths):
    kb_path, _ = mock_rag_paths
    doc_file = kb_path / "sample.pdf"
    doc_file.write_text("dummy PDF contents")

    # Mock PyMuPDF Document properties
    mock_doc = MagicMock()
    mock_doc.page_count = 2
    mock_doc.metadata = {"title": "Authoritative Manual"}
    
    mock_page1 = MagicMock()
    mock_page1.get_text.return_value = "Page 1 Content Here"
    mock_page2 = MagicMock()
    mock_page2.get_text.return_value = "  Page 2 Content   Extra Spacing  "
    
    mock_doc.load_page.side_effect = [mock_page1, mock_page2]

    with patch("fitz.open", return_value=mock_doc):
        pages = document_service.extract_pages(doc_file)
        
        assert len(pages) == 2
        assert pages[0]["page_number"] == 1
        assert pages[0]["text"] == "Page 1 Content Here"
        assert pages[0]["document_title"] == "Authoritative Manual"
        assert pages[1]["page_number"] == 2
        assert pages[1]["text"] == "Page 2 Content Extra Spacing"

def test_pdf_extraction_empty_text_fails(mock_rag_paths):
    kb_path, _ = mock_rag_paths
    doc_file = kb_path / "scanned.pdf"
    doc_file.write_text("dummy scanned PDF contents")

    mock_doc = MagicMock()
    mock_doc.page_count = 1
    mock_doc.metadata = {}
    mock_page = MagicMock()
    mock_page.get_text.return_value = ""  # No text
    mock_doc.load_page.return_value = mock_page

    with patch("fitz.open", return_value=mock_doc):
        with pytest.raises(ValueError, match="no usable extractable text"):
            document_service.extract_pages(doc_file)

# ==============================================================================
# Text Chunking Tests
# ==============================================================================

def test_chunking_bounds_validation():
    # Negative chunk size
    with pytest.raises(ValueError, match="positive"):
        rag_service.chunk_document([], "checksum", chunk_size=-5)

    # Negative overlap
    with pytest.raises(ValueError, match="non-negative"):
        rag_service.chunk_document([], "checksum", chunk_size=10, chunk_overlap=-2)

    # Overlap >= size
    with pytest.raises(ValueError, match="smaller"):
        rag_service.chunk_document([], "checksum", chunk_size=10, chunk_overlap=10)

def test_chunk_ids_deterministic_and_unique():
    pages = [
        {
            "text": "Common overlapping text contents.",
            "page_number": 1,
            "source_relative_path": "RefundPolicy.pdf",
            "document_title": "Refund Policy",
            "source_filename": "RefundPolicy.pdf"
        }
    ]
    
    chunks_doc1 = rag_service.chunk_document(pages, "hash_one", chunk_size=100, chunk_overlap=10)
    chunks_doc2 = rag_service.chunk_document(pages, "hash_two", chunk_size=100, chunk_overlap=10)

    # Deterministic check
    assert chunks_doc1[0]["chunk_id"] == chunks_doc1[0]["chunk_id"]

    # Source-aware uniqueness check (same text, different checksums should yield different IDs)
    assert chunks_doc1[0]["chunk_id"] != chunks_doc2[0]["chunk_id"]

# ==============================================================================
# Embedding Validation Tests
# ==============================================================================

def test_generate_embeddings_validations(mock_embedding_transformer):
    # Reject empty lists
    assert len(rag_service.generate_embeddings([])) == 0

    # Reject whitespace or empty string
    with pytest.raises(ValueError, match="Empty or whitespace-only"):
        rag_service.generate_embeddings(["Valid text", "  "])

    # Reject NaN/inf values
    with patch.object(mock_embedding_transformer, "encode") as mock_encode:
        mock_encode.return_value = np.array([[np.nan] * 384], dtype=np.float32)
        with pytest.raises(ValueError, match="NaN or infinite"):
            rag_service.generate_embeddings(["Dummy text"])

# ==============================================================================
# FAISS Persistence Tests
# ==============================================================================

def test_atomic_persistence_and_reload(mock_rag_paths, mock_embedding_transformer):
    _, vs_path = mock_rag_paths

    dummy_embeddings = np.random.rand(2, 384).astype(np.float32)
    # L2 normalize for consistency
    dummy_embeddings /= np.linalg.norm(dummy_embeddings, axis=1, keepdims=True)

    dummy_metadata = [
        {
            "chunk_id": "id1",
            "text": "Chunk 1 Text",
            "source_filename": "FAQ.pdf",
            "source_relative_path": "FAQ.pdf",
            "document_title": "FAQ Title",
            "page_start": 1,
            "page_end": 1,
            "character_count": 12,
            "chunk_index": 0,
            "ingestion_timestamp": int(time.time()),
            "schema_version": "1.0"
        },
        {
            "chunk_id": "id2",
            "text": "Chunk 2 Text",
            "source_filename": "FAQ.pdf",
            "source_relative_path": "FAQ.pdf",
            "document_title": "FAQ Title",
            "page_start": 2,
            "page_end": 2,
            "character_count": 12,
            "chunk_index": 1,
            "ingestion_timestamp": int(time.time()),
            "schema_version": "1.0"
        }
    ]

    manifest_payload = {
        "documents": {
            "FAQ.pdf": {"checksum": "hash123", "pages": 2, "chunks": 2}
        }
    }

    # Save Store
    rag_service.save_vector_store(dummy_embeddings, dummy_metadata, manifest_payload)

    # Verify final index files exist
    assert (vs_path / "index.faiss").exists()
    assert (vs_path / "metadata.json").exists()
    assert (vs_path / "manifest.json").exists()

    # Load store and check values
    rag_service._index = None
    rag_service._metadata = None
    rag_service._manifest = None
    
    rag_service.load_vector_store()
    
    assert rag_service._manifest["embedding_dimension"] == 384
    assert len(rag_service._metadata) == 2
    assert rag_service._index.ntotal == 2

def test_load_vector_store_corrupted(mock_rag_paths):
    _, vs_path = mock_rag_paths
    (vs_path / "index.faiss").touch()
    (vs_path / "metadata.json").touch()

    # Create invalid index manifest files
    with open(vs_path / "manifest.json", "w", encoding="utf-8") as f:
        f.write("{invalid_json}")

    with pytest.raises(ValueError, match="corrupted or incompatible"):
        rag_service.load_vector_store()

# ==============================================================================
# Similarity Retrieval Tests
# ==============================================================================

def test_similarity_retrieval(mock_rag_paths, mock_embedding_transformer):
    # Setup dummy database with 2 items
    embeddings = np.array([[1.0] + [0.0]*383, [0.0]*383 + [1.0]], dtype=np.float32)
    metadata = [
        {
            "chunk_id": "id1",
            "text": "Matches first query dimension",
            "source_filename": "Pricing.pdf",
            "source_relative_path": "Pricing.pdf",
            "document_title": "Pricing Doc",
            "page_start": 1,
            "page_end": 1,
            "character_count": 29,
            "chunk_index": 0,
            "ingestion_timestamp": int(time.time()),
            "schema_version": "1.0"
        },
        {
            "chunk_id": "id2",
            "text": "Matches second query dimension",
            "source_filename": "FAQ.pdf",
            "source_relative_path": "FAQ.pdf",
            "document_title": "FAQ Doc",
            "page_start": 1,
            "page_end": 1,
            "character_count": 30,
            "chunk_index": 0,
            "ingestion_timestamp": int(time.time()),
            "schema_version": "1.0"
        }
    ]
    manifest = {"documents": {}}
    rag_service.save_vector_store(embeddings, metadata, manifest)

    # Mock query encoding to match dimension 1 exactly
    with patch.object(mock_embedding_transformer, "encode") as mock_encode:
        mock_encode.return_value = np.array([[1.0] + [0.0]*383], dtype=np.float32)
        
        # Test similarity score sorting (id1 matches perfectly, id2 has dot-product 0.0)
        hits = rag_service.query_similarity("Query text", top_k=2)
        assert len(hits) == 2
        assert hits[0]["chunk_id"] == "id1"
        assert hits[0]["similarity_score"] == 1.0
        assert hits[1]["chunk_id"] == "id2"
        assert hits[1]["similarity_score"] == 0.0

        # Test threshold cutoff
        old_threshold = settings.RETRIEVAL_SCORE_THRESHOLD
        settings.RETRIEVAL_SCORE_THRESHOLD = 0.5
        try:
            hits_filtered = rag_service.query_similarity("Query text", top_k=2)
            assert len(hits_filtered) == 1
            assert hits_filtered[0]["chunk_id"] == "id1"
        finally:
            settings.RETRIEVAL_SCORE_THRESHOLD = old_threshold

# ==============================================================================
# API Routes & Auth Security Tests
# ==============================================================================

def test_unauthenticated_api_search_rejected(mock_rag_paths):
    # API calls without Bearer tokens must return HTTP 401
    response = client.post("/api/v1/knowledge/search", json={"query": "refund policy", "top_k": 3})
    assert response.status_code == 401

def test_authenticated_api_search_missing_index(mock_rag_paths, mock_db_isolation):
    # Build authentication token bypass
    email = "test_rag@nexora.com"
    register_payload = {
        "email": email,
        "full_name": "RAG User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    }
    client.post("/api/v1/auth/register", json=register_payload)
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login_res.json()["access_token"]
    
    # Call search with missing/empty store index
    response = client.post(
        "/api/v1/knowledge/search",
        json={"query": "refund policy", "top_k": 3},
        headers={"Authorization": f"Bearer {token}"}
    )
    # Returns HTTP 503 since store index is missing
    assert response.status_code == 503
    assert "not initialized" in response.json()["error"]["message"]

def test_authenticated_api_search_success(mock_rag_paths, mock_embedding_transformer, mock_db_isolation):
    # Setup database vectors
    embeddings = np.array([[1.0] + [0.0]*383], dtype=np.float32)
    metadata = [{
        "chunk_id": "chunk123",
        "text": "The refund window is 30 days.",
        "source_filename": "RefundPolicy.pdf",
        "source_relative_path": "RefundPolicy.pdf",
        "document_title": "Refund Policy",
        "page_start": 1,
        "page_end": 1,
        "character_count": 29,
        "chunk_index": 0,
        "ingestion_timestamp": int(time.time()),
        "schema_version": "1.0"
    }]
    rag_service.save_vector_store(embeddings, metadata, {"documents": {}})

    # Setup User login
    email = "active_rag@nexora.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Active RAG User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    })
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login_res.json()["access_token"]

    # Search query
    response = client.post(
        "/api/v1/knowledge/search",
        json={"query": "What is the refund window?", "top_k": 2},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["query"] == "What is the refund window?"
    assert len(res_data["results"]) == 1
    assert res_data["results"][0]["chunk_id"] == "chunk123"
    assert res_data["results"][0]["text"] == "The refund window is 30 days."
    assert res_data["results"][0]["source_filename"] == "RefundPolicy.pdf"

def test_api_search_invalid_requests(mock_rag_paths, mock_db_isolation):
    # Setup User login
    email = "invalid_req_rag@nexora.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Validator User",
        "password": "SecurePassword123!",
        "preferred_language": "en"
    })
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": "SecurePassword123!"})
    token = login_res.json()["access_token"]

    # Empty query string
    res_empty = client.post(
        "/api/v1/knowledge/search",
        json={"query": "", "top_k": 3},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_empty.status_code == 422

    # Oversized top_k (max 20)
    res_top_k = client.post(
        "/api/v1/knowledge/search",
        json={"query": "Valid search", "top_k": 25},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_top_k.status_code == 422
