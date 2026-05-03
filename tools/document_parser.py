"""
Document Parser Tool — Student A
=================================
Parses PDF and DOCX files (resumes and job flyers) and extracts raw text content.
Uses pdfplumber for PDFs and python-docx for DOCX files.

This tool is the system's "eyes" — it reads uploaded documents and provides
raw text for the Document Intelligence Extractor agent to process.

Features:
    - PDF parsing with pdfplumber (handles complex layouts, tables)
    - DOCX parsing with python-docx (preserves paragraph structure)
    - File validation (type, size, existence)
    - Structured error handling (never raises, always returns a result)
    - Metadata extraction (page count, file size)
"""

import os
from typing import Optional

import pdfplumber
from docx import Document as DocxDocument
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class DocumentParseResult(BaseModel):
    """Structured result from document parsing.

    Attributes:
        success: Whether the document was successfully parsed.
        raw_text: Extracted raw text from the document.
        page_count: Number of pages/sections in the document.
        file_name: Original filename of the parsed document.
        file_type: File extension (.pdf or .docx).
        file_size_kb: File size in kilobytes.
        error_message: Error message if parsing failed, None otherwise.
    """

    success: bool = Field(description="Whether the document was successfully parsed")
    raw_text: str = Field(description="Extracted raw text from the document")
    page_count: int = Field(description="Number of pages in the document")
    file_name: str = Field(description="Original filename of the parsed document")
    file_type: str = Field(description="File extension (.pdf or .docx)")
    file_size_kb: float = Field(description="File size in kilobytes")
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if parsing failed",
    )


@tool
def document_parser(file_path: str) -> dict:
    """Parse a PDF or DOCX document and extract its raw text content.

    This tool reads a local document file (PDF or DOCX), extracts text from
    all pages/sections, and returns a structured result with the raw text
    and file metadata. Used for both resume and job flyer extraction.

    Args:
        file_path: Absolute path to the document file on the local filesystem.
                   Must be a valid .pdf or .docx file that exists and is readable.

    Returns:
        dict: A dictionary containing:
            - success (bool): Whether parsing succeeded
            - raw_text (str): The full extracted text content
            - page_count (int): Number of pages processed
            - file_name (str): The basename of the file
            - file_type (str): File extension
            - file_size_kb (float): Size of the file in KB
            - error_message (str|None): Error details if parsing failed
    """
    result: DocumentParseResult = _parse_document(file_path)
    return result.model_dump()


def _parse_document(file_path: str) -> DocumentParseResult:
    """Internal document parsing logic.

    Args:
        file_path: Absolute path to the document file.

    Returns:
        DocumentParseResult: Structured parsing result.
    """
    try:
        # --- Validation ---
        if not os.path.exists(file_path):
            return DocumentParseResult(
                success=False,
                raw_text="",
                page_count=0,
                file_name=os.path.basename(file_path),
                file_type="",
                file_size_kb=0.0,
                error_message=f"File not found: {file_path}",
            )

        file_ext: str = os.path.splitext(file_path)[1].lower()
        if file_ext not in (".pdf", ".docx"):
            return DocumentParseResult(
                success=False,
                raw_text="",
                page_count=0,
                file_name=os.path.basename(file_path),
                file_type=file_ext,
                file_size_kb=0.0,
                error_message=f"Unsupported file type: {file_ext}. Expected .pdf or .docx",
            )

        file_size_kb: float = round(os.path.getsize(file_path) / 1024, 2)

        # 10 MB limit
        if file_size_kb > 10240:
            return DocumentParseResult(
                success=False,
                raw_text="",
                page_count=0,
                file_name=os.path.basename(file_path),
                file_type=file_ext,
                file_size_kb=file_size_kb,
                error_message=f"File too large: {file_size_kb:.1f}KB (max 10MB)",
            )

        # --- Parsing ---
        if file_ext == ".pdf":
            return _parse_pdf(file_path, file_size_kb)
        else:
            return _parse_docx(file_path, file_size_kb)

    except Exception as e:
        return DocumentParseResult(
            success=False,
            raw_text="",
            page_count=0,
            file_name=os.path.basename(file_path),
            file_type=os.path.splitext(file_path)[1].lower(),
            file_size_kb=0.0,
            error_message=f"Unexpected error: {type(e).__name__}: {str(e)}",
        )


def _parse_pdf(file_path: str, file_size_kb: float) -> DocumentParseResult:
    """Parse a PDF file using pdfplumber.

    Args:
        file_path: Path to the PDF file.
        file_size_kb: Pre-calculated file size in KB.

    Returns:
        DocumentParseResult: Parsed document data.
    """
    extracted_pages: list[str] = []

    with pdfplumber.open(file_path) as pdf:
        page_count: int = len(pdf.pages)

        for page in pdf.pages:
            page_text: Optional[str] = page.extract_text()
            if page_text:
                extracted_pages.append(page_text.strip())

    raw_text: str = "\n\n".join(extracted_pages)

    if not raw_text.strip():
        return DocumentParseResult(
            success=False,
            raw_text="",
            page_count=page_count,
            file_name=os.path.basename(file_path),
            file_type=".pdf",
            file_size_kb=file_size_kb,
            error_message="PDF contains no extractable text (may be image-based/scanned)",
        )

    return DocumentParseResult(
        success=True,
        raw_text=raw_text,
        page_count=page_count,
        file_name=os.path.basename(file_path),
        file_type=".pdf",
        file_size_kb=file_size_kb,
    )


def _parse_docx(file_path: str, file_size_kb: float) -> DocumentParseResult:
    """Parse a DOCX file using python-docx.

    Args:
        file_path: Path to the DOCX file.
        file_size_kb: Pre-calculated file size in KB.

    Returns:
        DocumentParseResult: Parsed document data.
    """
    doc: DocxDocument = DocxDocument(file_path)
    paragraphs: list[str] = []

    for para in doc.paragraphs:
        text: str = para.text.strip()
        if text:
            paragraphs.append(text)

    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            row_text: list[str] = []
            for cell in row.cells:
                cell_text: str = cell.text.strip()
                if cell_text:
                    row_text.append(cell_text)
            if row_text:
                paragraphs.append(" | ".join(row_text))

    raw_text: str = "\n".join(paragraphs)

    if not raw_text.strip():
        return DocumentParseResult(
            success=False,
            raw_text="",
            page_count=1,
            file_name=os.path.basename(file_path),
            file_type=".docx",
            file_size_kb=file_size_kb,
            error_message="DOCX contains no extractable text",
        )

    return DocumentParseResult(
        success=True,
        raw_text=raw_text,
        page_count=len(doc.sections),
        file_name=os.path.basename(file_path),
        file_type=".docx",
        file_size_kb=file_size_kb,
    )
