"""
Tests for Agent 2: Smart Candidate Matcher — Student B
======================================================
Tests the job database tool and the matching agent logic.

Test Categories:
    - Tool tests: Database queries, inserts, error handling
    - Agent tests: Scoring formula, recommendation thresholds, edge cases
    - Integration tests: Skill synonym normalization
"""

import json
import os

import pytest

from tools.job_database_manager import _query_jobs, _insert_job, JobQueryResult, JobInsertResult
from agents.candidate_matcher import normalize_skill


class TestJobDatabaseManagerTool:
    """Tests for the job_database_manager tool (Student B's custom tool)."""

    def test_query_existing_job_by_id(self, sample_db: str) -> None:
        """Property: Querying existing job ID → returns that job."""
        result: JobQueryResult = _query_jobs(db_path=sample_db, job_id="JOB-TEST-001")
        assert result.success is True
        assert result.total_count == 1
        assert result.jobs[0]["job_id"] == "JOB-TEST-001"

    def test_query_nonexistent_job(self, sample_db: str) -> None:
        """Property: Non-existent job ID → empty results, not error."""
        result: JobQueryResult = _query_jobs(db_path=sample_db, job_id="JOB-FAKE-999")
        assert result.success is True
        assert result.total_count == 0

    def test_query_by_status_filter(self, sample_db: str) -> None:
        """Property: Status filter returns only matching jobs."""
        result: JobQueryResult = _query_jobs(db_path=sample_db, status_filter="OPEN")
        assert result.success is True
        for job in result.jobs:
            assert job["status"] == "OPEN"

    def test_query_nonexistent_db(self) -> None:
        """Property: Missing database file → success=False with clear error."""
        result: JobQueryResult = _query_jobs(db_path="/fake/path/db.sqlite")
        assert result.success is False
        assert "not found" in result.error_message.lower()

    def test_insert_valid_job(self, sample_db: str) -> None:
        """Property: Valid job data → successful insertion."""
        job_data: dict = {
            "job_id": "JOB-NEW-001",
            "title": "New Test Role",
            "department": "Testing",
            "required_skills": ["python", "testing"],
            "preferred_skills": ["selenium"],
            "min_experience_years": 1,
            "required_education": "Bachelor's",
            "description": "A new test job",
            "status": "OPEN",
        }
        result: JobInsertResult = _insert_job(sample_db, job_data)
        assert result.success is True
        assert result.job_id == "JOB-NEW-001"

        # Verify it was inserted
        query_result = _query_jobs(db_path=sample_db, job_id="JOB-NEW-001")
        assert query_result.total_count == 1

    def test_insert_missing_required_field(self, sample_db: str) -> None:
        """Property: Missing required field → success=False with error."""
        job_data: dict = {"title": "Incomplete Job"}
        result: JobInsertResult = _insert_job(sample_db, job_data)
        assert result.success is False
        assert "missing required field" in result.error_message.lower()

    def test_skills_returned_as_list(self, sample_db: str) -> None:
        """Property: Skills are returned as parsed lists, not JSON strings."""
        result = _query_jobs(db_path=sample_db, job_id="JOB-TEST-001")
        assert result.success is True
        assert isinstance(result.jobs[0]["required_skills"], list)
        assert "python" in result.jobs[0]["required_skills"]


class TestSkillSynonymMapping:
    """Tests for the skill synonym normalization."""

    def test_javascript_synonyms(self) -> None:
        """Property: JS/js → javascript."""
        assert normalize_skill("JS") == "javascript"
        assert normalize_skill("js") == "javascript"

    def test_react_synonyms(self) -> None:
        """Property: React/React.js → reactjs."""
        assert normalize_skill("React") == "reactjs"
        assert normalize_skill("React.js") == "reactjs"

    def test_kubernetes_synonym(self) -> None:
        """Property: k8s → kubernetes."""
        assert normalize_skill("k8s") == "kubernetes"

    def test_unknown_skill_unchanged(self) -> None:
        """Property: Unknown skills are returned lowercase."""
        assert normalize_skill("FastAPI") == "fastapi"
        assert normalize_skill("PostgreSQL") == "postgresql"


class TestMatchScoring:
    """Tests for the matching agent's scoring logic."""

    def test_perfect_match_scores_high(self, sample_match_report: dict) -> None:
        """Property: Candidate matching all skills → score ≥ 80."""
        assert sample_match_report["overall_match_score"] >= 80

    def test_strong_match_recommendation(self, sample_match_report: dict) -> None:
        """Property: Score ≥ 80 → STRONG_MATCH recommendation."""
        assert sample_match_report["recommendation"] == "STRONG_MATCH"

    def test_match_report_has_required_fields(self, sample_match_report: dict) -> None:
        """Property: Match report contains all required fields."""
        required_fields: list[str] = [
            "job_id", "job_title", "candidate_name",
            "overall_match_score", "skill_match", "experience_match",
            "education_match", "recommendation", "reasoning",
        ]
        for field in required_fields:
            assert field in sample_match_report, f"Missing field: {field}"

    def test_skill_match_has_categories(self, sample_match_report: dict) -> None:
        """Property: Skill match includes matched, missing, and bonus skills."""
        skill_match: dict = sample_match_report["skill_match"]
        assert "matched_skills" in skill_match
        assert "missing_skills" in skill_match
        assert "bonus_skills" in skill_match
        assert "skill_match_percentage" in skill_match

    def test_score_within_valid_range(self, sample_match_report: dict) -> None:
        """Property: Match score is between 0 and 100."""
        assert 0 <= sample_match_report["overall_match_score"] <= 100
