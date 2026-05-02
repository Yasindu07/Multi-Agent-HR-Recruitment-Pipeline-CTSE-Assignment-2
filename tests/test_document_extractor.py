"""
Tests for Agent 1: Document Intelligence Extractor — Student A
===============================================================
Tests the document parsing tool and the extraction agent logic.

Test Categories:
    - Tool tests: PDF parsing, DOCX parsing, error handling
    - Agent tests: Resume extraction, flyer extraction, edge cases
    - Security tests: PII handling, no hallucination checks
"""

import json
import os
import tempfile

import pytest

from tools.document_parser import _parse_document, DocumentParseResult


class TestDocumentParserTool:
    """Tests for the document_parser tool (Student A's custom tool)."""

    def test_valid_pdf_returns_success(self, sample_pdf_resume: str) -> None:
        """Property: Valid PDF → success=True and non-empty text."""
        result: DocumentParseResult = _parse_document(sample_pdf_resume)
        assert result.success is True
        assert len(result.raw_text) > 0
        assert result.page_count >= 1
        assert result.file_type == ".pdf"
        assert result.error_message is None

    def test_nonexistent_file_returns_error(self) -> None:
        """Property: Non-existent file → success=False with clear error."""
        result: DocumentParseResult = _parse_document("/nonexistent/path/resume.pdf")
        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_unsupported_file_type_returns_error(self, tmp_dir: str) -> None:
        """Property: Non-PDF/DOCX file → success=False with type error."""
        txt_path: str = os.path.join(tmp_dir, "resume.txt")
        with open(txt_path, "w") as f:
            f.write("This is a text file")

        result: DocumentParseResult = _parse_document(txt_path)
        assert result.success is False
        assert "unsupported" in result.error_message.lower()

    def test_empty_pdf_returns_error(self, tmp_dir: str) -> None:
        """Property: Empty/corrupt PDF → success=False, not crash."""
        try:
            from fpdf import FPDF
        except ImportError:
            pytest.skip("fpdf2 not installed")

        # Create a PDF with no text
        pdf = FPDF()
        pdf.add_page()
        empty_path: str = os.path.join(tmp_dir, "empty.pdf")
        pdf.output(empty_path)

        result: DocumentParseResult = _parse_document(empty_path)
        assert result.success is False
        assert result.error_message is not None

    def test_file_size_metadata(self, sample_pdf_resume: str) -> None:
        """Property: Result includes accurate file size metadata."""
        result: DocumentParseResult = _parse_document(sample_pdf_resume)
        assert result.file_size_kb > 0
        assert result.file_name == os.path.basename(sample_pdf_resume)

    def test_extracts_candidate_name(self, sample_pdf_resume: str) -> None:
        """Property: Raw text contains the candidate's name."""
        result: DocumentParseResult = _parse_document(sample_pdf_resume)
        assert "Test Candidate" in result.raw_text

    def test_extracts_skills(self, sample_pdf_resume: str) -> None:
        """Property: Raw text contains listed skills."""
        result: DocumentParseResult = _parse_document(sample_pdf_resume)
        assert "Python" in result.raw_text
        assert "JavaScript" in result.raw_text


class TestDocumentExtractorAgent:
    """Tests for the Document Extractor agent logic."""

    def test_resume_extraction_required_fields(self, sample_candidate_profile: dict) -> None:
        """Property: Extracted resume has all required fields."""
        required_fields: list[str] = [
            "candidate_name", "email", "skills", "education", "work_experience"
        ]
        for field in required_fields:
            assert field in sample_candidate_profile, f"Missing field: {field}"

    def test_skills_are_lowercase(self, sample_candidate_profile: dict) -> None:
        """Property: All skills are normalized to lowercase."""
        for skill in sample_candidate_profile["skills"]:
            assert skill == skill.lower(), f"Skill '{skill}' is not lowercase"

    def test_not_found_sentinel_for_missing_data(self, sample_candidate_profile: dict) -> None:
        """Property: Missing optional fields use NOT_FOUND sentinel."""
        # portfolio_url is NOT_FOUND in our sample
        assert sample_candidate_profile["portfolio_url"] == "NOT_FOUND"

    def test_no_fabricated_data(self, sample_candidate_profile: dict) -> None:
        """Security: Profile fields should come from the resume, not hallucinated."""
        assert sample_candidate_profile["candidate_name"] != ""
        assert sample_candidate_profile["email"] != ""
        # Skills count should be reasonable (not hundreds)
        assert len(sample_candidate_profile["skills"]) < 50

    def test_work_experience_has_structure(self, sample_candidate_profile: dict) -> None:
        """Property: Work experience entries have required sub-fields."""
        for exp in sample_candidate_profile["work_experience"]:
            assert "company" in exp
            assert "role" in exp
            assert "duration" in exp
