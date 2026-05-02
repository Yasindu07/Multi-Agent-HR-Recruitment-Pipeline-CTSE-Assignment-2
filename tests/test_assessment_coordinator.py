"""
Tests for Agent 3: Assessment Coordinator — Student C
=====================================================
Tests the assessment generator tool and evaluation logic.

Test Categories:
    - Tool tests: Assessment generation, saving, scoring
    - Agent tests: Difficulty calibration, question structure
    - Validation tests: Red flag detection, skill-claim mismatch
"""

import json
import os

import pytest

from tools.assessment_generator import (
    _generate_assessment,
    _score_assessment,
    _calibrate_difficulty,
    _create_assessment_template,
    AssessmentGenerationResult,
    AssessmentScoreResult,
)


class TestAssessmentGeneratorTool:
    """Tests for the assessment_generator tool (Student C's custom tool)."""

    def test_generate_assessment_success(self, tmp_dir: str) -> None:
        """Property: Valid inputs → successful assessment generation."""
        result: AssessmentGenerationResult = _generate_assessment(
            output_dir=tmp_dir,
            candidate_name="Test User",
            job_title="Python Developer",
            job_id="JOB-001",
            matched_skills="python,git",
            missing_skills="docker,kubernetes",
            experience_years=3,
            work_highlights="Built REST APIs,Managed deployments",
            assessment_content=None,
        )
        assert result.success is True
        assert result.total_questions > 0
        assert os.path.exists(result.assessment_file_path)

    def test_assessment_file_is_valid_json(self, tmp_dir: str) -> None:
        """Property: Saved assessment file is valid JSON."""
        result = _generate_assessment(
            output_dir=tmp_dir,
            candidate_name="Test User",
            job_title="Developer",
            job_id="JOB-001",
            matched_skills="python",
            missing_skills="docker",
            experience_years=2,
            work_highlights="",
            assessment_content=None,
        )
        assert result.success is True

        with open(result.assessment_file_path, "r") as f:
            data: dict = json.load(f)

        assert "metadata" in data
        assert "questions" in data
        assert data["metadata"]["candidate_name"] == "Test User"

    def test_assessment_has_metadata(self, tmp_dir: str) -> None:
        """Property: Assessment includes metadata (candidate, job, difficulty)."""
        result = _generate_assessment(
            output_dir=tmp_dir,
            candidate_name="Jane",
            job_title="Data Scientist",
            job_id="JOB-002",
            matched_skills="python,pandas",
            missing_skills="spark",
            experience_years=5,
            work_highlights="",
            assessment_content=None,
        )
        with open(result.assessment_file_path, "r") as f:
            data = json.load(f)

        assert data["metadata"]["job_title"] == "Data Scientist"
        assert data["metadata"]["difficulty_level"] == "SENIOR"

    def test_scoring_pass(self, tmp_dir: str) -> None:
        """Property: Good answers → PASS status."""
        # Generate an assessment first
        gen_result = _generate_assessment(
            output_dir=tmp_dir,
            candidate_name="Smart Candidate",
            job_title="Developer",
            job_id="JOB-001",
            matched_skills="python",
            missing_skills="docker",
            experience_years=3,
            work_highlights="",
            assessment_content=None,
        )
        assert gen_result.success is True

        # Read the assessment to get question IDs and correct answers
        with open(gen_result.assessment_file_path, "r") as f:
            assessment = json.load(f)

        # Answer all questions correctly
        answers: dict = {}
        for q in assessment["questions"]:
            if q.get("correct_answer"):
                answers[q["question_id"]] = q["correct_answer"]
            else:
                answers[q["question_id"]] = "Detailed answer showing knowledge"

        score_result: AssessmentScoreResult = _score_assessment(
            assessment_file_path=gen_result.assessment_file_path,
            candidate_answers=json.dumps(answers),
            candidate_name="Smart Candidate",
        )

        assert score_result.success is True
        assert score_result.percentage >= 50
        assert score_result.pass_status in ("PASS", "BORDERLINE")

    def test_scoring_with_no_answers(self, tmp_dir: str) -> None:
        """Property: No answers → 0% score and FAIL."""
        gen_result = _generate_assessment(
            output_dir=tmp_dir,
            candidate_name="No Answer",
            job_title="Developer",
            job_id="JOB-001",
            matched_skills="python",
            missing_skills="docker",
            experience_years=1,
            work_highlights="",
            assessment_content=None,
        )

        score_result = _score_assessment(
            assessment_file_path=gen_result.assessment_file_path,
            candidate_answers=json.dumps({}),
            candidate_name="No Answer",
        )

        assert score_result.success is True
        assert score_result.percentage == 0
        assert score_result.pass_status == "FAIL"

    def test_nonexistent_assessment_file(self) -> None:
        """Property: Missing assessment file → success=False."""
        result = _score_assessment(
            assessment_file_path="/nonexistent/assessment.json",
            candidate_answers="{}",
            candidate_name="Test",
        )
        assert result.success is False
        assert "not found" in result.error_message.lower()


class TestDifficultyCalibration:
    """Tests for difficulty level calibration."""

    def test_junior_calibration(self) -> None:
        """Property: 0-1 years → JUNIOR."""
        assert _calibrate_difficulty(0) == "JUNIOR"
        assert _calibrate_difficulty(1) == "JUNIOR"

    def test_mid_calibration(self) -> None:
        """Property: 2-3 years → MID."""
        assert _calibrate_difficulty(2) == "MID"
        assert _calibrate_difficulty(3) == "MID"

    def test_senior_calibration(self) -> None:
        """Property: 4-6 years → SENIOR."""
        assert _calibrate_difficulty(4) == "SENIOR"
        assert _calibrate_difficulty(6) == "SENIOR"

    def test_lead_calibration(self) -> None:
        """Property: 7+ years → LEAD."""
        assert _calibrate_difficulty(7) == "LEAD"
        assert _calibrate_difficulty(15) == "LEAD"


class TestAssessmentTemplate:
    """Tests for the assessment template generation."""

    def test_template_has_questions(self) -> None:
        """Property: Template generates questions for given skills."""
        questions: list[dict] = _create_assessment_template(
            matched_skills=["python", "docker"],
            missing_skills=["kubernetes"],
            highlights=["Built APIs"],
            difficulty_level="MID",
            job_title="DevOps Engineer",
        )
        assert len(questions) > 0

    def test_template_has_sections(self) -> None:
        """Property: Questions cover TECHNICAL, SCENARIO, PROBLEM_SOLVING."""
        questions = _create_assessment_template(
            matched_skills=["python", "reactjs", "docker"],
            missing_skills=["kubernetes", "terraform"],
            highlights=["Led team", "Built pipelines"],
            difficulty_level="SENIOR",
            job_title="Senior Engineer",
        )
        sections: set = {q["section"] for q in questions}
        assert "TECHNICAL" in sections
        assert "SCENARIO" in sections or "PROBLEM_SOLVING" in sections

    def test_template_question_ids_unique(self) -> None:
        """Property: All question IDs are unique."""
        questions = _create_assessment_template(
            matched_skills=["python"],
            missing_skills=["docker"],
            highlights=["Worked on APIs"],
            difficulty_level="MID",
            job_title="Developer",
        )
        ids: list[str] = [q["question_id"] for q in questions]
        assert len(ids) == len(set(ids))
