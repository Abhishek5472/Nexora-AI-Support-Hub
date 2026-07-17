import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Any
import fitz  # PyMuPDF

from backend.core.config import settings

logger = logging.getLogger(__name__)

class DocumentService:
    """
    Service to handle discovery, validation, and text extraction from knowledge-base PDFs.
    """
    def __init__(self):
        self.base_path = Path(settings.KNOWLEDGE_BASE_PATH).resolve()

    def discover_documents(self) -> List[Path]:
        """
        Scan the knowledge-base directory and return a deterministically sorted list
        of supported PDF files. Ignores hidden files, .gitkeep, and temporary formats.
        """
        if not self.base_path.exists() or not self.base_path.is_dir():
            logger.warning(f"Knowledge base directory does not exist: {self.base_path}")
            return []

        pdf_files = []
        for file in self.base_path.glob("**/*"):
            # Skip directories
            if not file.is_file():
                continue

            # Skip hidden/temporary files and gitkeeps
            name = file.name
            if name.startswith(".") or name.startswith("~$") or name == ".gitkeep":
                continue

            # Validate file extension
            if file.suffix.lower() != ".pdf":
                logger.debug(f"Ignoring non-PDF file: {file}")
                continue

            pdf_files.append(file)

        # Sort deterministically
        pdf_files.sort(key=lambda p: str(p))
        return pdf_files

    def validate_file(self, file_path: Path) -> None:
        """
        Performs strict security and readability validations on a PDF file.
        Raises ValueError or PermissionError if checks fail.
        """
        resolved_file = file_path.resolve()

        # 1. Prevent path traversal: check common path
        try:
            os.path.commonpath([self.base_path, resolved_file])
            if not str(resolved_file).startswith(str(self.base_path)):
                raise ValueError("Path traversal detected!")
        except Exception:
            raise ValueError("Path traversal validation failed.")

        # 2. Basic file integrity checks
        if not resolved_file.exists():
            raise FileNotFoundError(f"File not found: {resolved_file}")

        if resolved_file.suffix.lower() != ".pdf":
            raise ValueError("Only PDF file format is supported.")

        if not os.access(resolved_file, os.R_OK):
            raise PermissionError(f"File is not readable: {resolved_file}")

        # 3. File size check
        size_bytes = resolved_file.stat().st_size
        if size_bytes == 0:
            raise ValueError("File is empty.")

        max_bytes = settings.MAX_KNOWLEDGE_FILE_SIZE_MB * 1024 * 1024
        if size_bytes > max_bytes:
            raise ValueError(
                f"File size {size_bytes / (1024*1024):.2f}MB exceeds the maximum "
                f"limit of {settings.MAX_KNOWLEDGE_FILE_SIZE_MB}MB."
            )

    def extract_pages(self, file_path: Path) -> List[Dict[str, Any]]:
        """
        Extracts clean text page-by-page from the PDF, preserving source metadata.
        Raises ValueError if no usable text is extracted from the entire document.
        """
        # Validate path and metadata beforehand
        self.validate_file(file_path)

        resolved_file = file_path.resolve()
        relative_path = resolved_file.relative_to(self.base_path)
        
        pages = []
        doc = None
        try:
            # Open PDF in read-only text mode, no JS execution
            doc = fitz.open(resolved_file)
            total_pages = doc.page_count

            if total_pages == 0:
                raise ValueError(f"PDF contains 0 pages: {file_path.name}")

            # Extract title from metadata or fallback to filename
            title = doc.metadata.get("title") or ""
            title = title.strip()
            if not title:
                title = resolved_file.stem

            for page_idx in range(total_pages):
                page = doc.load_page(page_idx)
                # Text extraction blocks
                raw_text = page.get_text("text")

                # Normalize text: strip whitespace, remove extra spaces
                clean_text = self._normalize_text(raw_text)

                pages.append({
                    "text": clean_text,
                    "page_number": page_idx + 1,  # human-readable 1-indexed
                    "total_pages": total_pages,
                    "source_filename": resolved_file.name,
                    "source_relative_path": str(relative_path).replace("\\", "/"),
                    "document_title": title,
                    "extraction_timestamp": int(time.time())
                })
        finally:
            if doc:
                doc.close()

        # Verify that we extracted some usable text from the PDF
        total_text_len = sum(len(p["text"]) for p in pages)
        if total_text_len == 0:
            raise ValueError(
                f"PDF contains no usable extractable text: {file_path.name} "
                f"(image-only/scanned PDF without OCR is not supported)."
            )

        return pages

    def _normalize_text(self, text: str) -> str:
        """
        Cleans up spacing issues, removes repeated spaces, but preserves useful
        paragraph boundaries (\n\n) and line breaks.
        """
        if not text:
            return ""

        # Normalize line ends and strip
        lines = [line.strip() for line in text.split("\n")]
        
        # Reconstruct with space, but preserve paragraphs (empty lines)
        normalized_paragraphs = []
        current_paragraph = []

        for line in lines:
            if not line:
                if current_paragraph:
                    normalized_paragraphs.append(" ".join(current_paragraph))
                    current_paragraph = []
            else:
                # Merge multiple internal spaces in line
                clean_line = " ".join(line.split())
                current_paragraph.append(clean_line)

        if current_paragraph:
            normalized_paragraphs.append(" ".join(current_paragraph))

        # Join paragraphs with double newlines
        return "\n\n".join(normalized_paragraphs).strip()

document_service = DocumentService()
