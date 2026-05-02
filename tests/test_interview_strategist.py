"""
Tests for Agent 4: Interview Strategist — Student D
====================================================
Tests the report file writer tool and interview guide generation.

Test Categories:
    - Tool tests: Report generation, file saving, comparison reports
    - Agent tests: Recommendation logic, content structure
    - Quality tests: Candidate-specific content, no generic questions
"""

import json
import os

import pytest

from tools.report_file_writer import (
    _generate_individual_report,
    _generate_comparison_report,
    ReportGenerationResult,
)
from agents.interview_strategist import _determine_recommendation


class TestReportFileWriterTool:
    """Tests for the report_file_writer tool (Student D's custom tool)."""

    def test_individual_report_success(self, tmp_dir: str) -> None:
        """Property: Valid inputs → successful report generation."""
        result: ReportGenerationResult = _generate_individual_report(
            output_dir=tmp_dir,
            candidate_name="John Doe",
            job_title="Senior Developer",
            report_content="## Strengths\n- Strong Python skills\n\n## Concerns\n- None",
            match_score=85,
            assessment_score=78.5,
            assessment_pass_status="PASS",
            recommendation="PROCEED",
        )
        assert result.success is True
        assert os.path.exists(result.file_path)
        assert result.file_path.endswith(".md")
        assert result.file_size_kb > 0

    def test_report_contains_yaml_frontmatter(self, tmp_dir: str) -> None:
        """Property: Report starts with YAML front matter."""
        result = _generate_individual_report(
            output_dir=tmp_dir,
            candidate_name="Jane Smith",
            job_title="Data Scientist",
            report_content="## Content",
            match_score=70,
            assessment_score=65.0,
            assessment_pass_status="BORDERLINE",
            recommendation="PROCEED_WITH_CAUTION",
        )
        with open(result.file_path, "r") as f:
            content: str = f.read()

        assert content.startswith("---")
        assert "candidate: Jane Smith" in content
        assert "position: Data Scientist" in content

    def test_report_contains_candidate_snapshot(self, tmp_dir: str) -> None:
        """Property: Report includes a candidate snapshot table."""
        result = _generate_individual_report(
            output_dir=tmp_dir,
            candidate_name="Alex Kumar",
            job_title="DevOps Engineer",
            report_content="## Content here",
            match_score=90,
            assessment_score=82.0,
            assessment_pass_status="PASS",
            recommendation="PROCEED",
        )
        with open(result.file_path, "r") as f:
            content = f.read()

        assert "Candidate Snapshot" in content
        assert "Alex Kumar" in content
        assert "90/100" in content

    def test_report_contains_audit_footer(self, tmp_dir: str) -> None:
        """Property: Report includes audit information footer."""
        result = _generate_individual_report(
            output_dir=tmp_dir,
            candidate_name="Test User",
            job_title="Developer",
            report_content="## Content",
            match_score=75,
            assessment_score=70.0,
            assessment_pass_status="PASS",
            recommendation="PROCEED",
        )
        with open(result.file_path, "r") as f:
            content = f.read()

        assert "Audit Information" in content
        assert "No data was sent to" in content
        assert "external cloud service" in content

    def test_report_filename_has_timestamp(self, tmp_dir: str) -> None:
        """Property: Report filename includes candidate name and timestamp."""
        result = _generate_individual_report(
            output_dir=tmp_dir,
            candidate_name="John Doe",
            job_title="Developer",
            report_content="",
            match_score=50,
            assessment_score=50.0,
            assessment_pass_status="BORDERLINE",
            recommendation="PROCEED_WITH_CAUTION",
        )
        filename: str = os.path.basename(result.file_path)
        assert "john_doe" in filename.lower()
        assert filename.startswith("interview_guide_")

    def test_output_dir_created_automatically(self, tmp_dir: str) -> None:
        """Property: Non-existent output directory is created."""
        nested_dir: str = os.path.join(tmp_dir, "reports", "2026", "april")
        result = _generate_individual_report(
            output_dir=nested_dir,
            candidate_name="Test",
            job_title="Dev",
            report_content="Test",
            match_score=0,
            assessment_score=0.0,
            assessment_pass_status="FAIL",
            recommendation="DO_NOT_PROCEED",
        )
        assert result.success is True
        assert os.path.exists(nested_dir)


class TestComparisonReport:
    """Tests for the comparison report generation."""

    def test_comparison_report_success(self, tmp_dir: str) -> None:
        """Property: Multiple candidate data → successful comparison report."""
        comparison_data: list[dict] = [
            {
                "candidate_name": "Alice",
                "match_score": 85,
                "assessment_score": 78,
                "assessment_pass_status": "PASS",
                "recommendation": "PROCEED",
                "strengths": "Python, Docker",
                "concerns": "No Kubernetes",
            },
            {
                "candidate_name": "Bob",
                "match_score": 72,
                "assessment_score": 65,
                "assessment_pass_status": "BORDERLINE",
                "recommendation": "PROCEED_WITH_CAUTION",
                "strengths": "React, TypeScript",
                "concerns": "Limited backend",
            },
        ]
        result = _generate_comparison_report(
            output_dir=tmp_dir,
            job_title="Senior Developer",
            comparison_data=json.dumps(comparison_data),
        )
        assert result.success is True
        assert result.report_type == "COMPARISON"

        with open(result.file_path, "r") as f:
            content: str = f.read()
        assert "Alice" in content
        assert "Bob" in content
        assert "Ranking Summary" in content

    def test_comparison_with_invalid_json(self, tmp_dir: str) -> None:
        """Property: Invalid JSON → success=False."""
        result = _generate_comparison_report(
            output_dir=tmp_dir,
            job_title="Test",
            comparison_data="not valid json",
        )
        assert result.success is False
        assert "json" in result.error_message.lower()


class TestRecommendationLogic:
    """Tests for the recommendation determination logic."""

    def test_proceed_for_strong_candidate(self) -> None:
        """Property: High scores + no flags → PROCEED."""
        result: str = _determine_recommendation(
            match_score=85,
            assessment_score=75.0,
            assessment_pass="PASS",
            flags=[],
        )
        assert result == "PROCEED"

    def test_do_not_proceed_for_failed_assessment(self) -> None:
        """Property: Failed assessment → DO_NOT_PROCEED regardless of match."""
        result = _determine_recommendation(
            match_score=90,
            assessment_score=30.0,
            assessment_pass="FAIL",
            flags=[],
        )
        assert result == "DO_NOT_PROCEED"

    def test_caution_for_flags(self) -> None:
        """Property: Red flags → PROCEED_WITH_CAUTION."""
        result = _determine_recommendation(
            match_score=80,
            assessment_score=70.0,
            assessment_pass="PASS",
            flags=["Skill claim mismatch: Python"],
        )
        assert result == "PROCEED_WITH_CAUTION"

    def test_caution_for_borderline(self) -> None:
        """Property: Borderline scores → PROCEED_WITH_CAUTION."""
        result = _determine_recommendation(
            match_score=65,
            assessment_score=55.0,
            assessment_pass="BORDERLINE",
            flags=[],
        )
        assert result == "PROCEED_WITH_CAUTION"

    def test_do_not_proceed_for_low_scores(self) -> None:
        """Property: Low match + low assessment → DO_NOT_PROCEED."""
        result = _determine_recommendation(
            match_score=40,
            assessment_score=35.0,
            assessment_pass="FAIL",
            flags=[],
        )
        assert result == "DO_NOT_PROCEED"
