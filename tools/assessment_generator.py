"""
Assessment Generator Tool — Student C
======================================
Generates personalized technical assessments and saves them as structured JSON files.
Manages a local question bank and supports auto-grading of assessment responses.

This tool creates customized quizzes calibrated by experience level and focused on
job-relevant skills. It also provides scoring functionality.

Features:
    - Generates assessment structure (sections, difficulty levels, question types)
    - Saves assessments as JSON files for persistence
    - Question bank management (load/save)
    - Auto-scoring for MCQ-type answers
    - Difficulty calibration based on experience level
"""

import json
import os
from datetime import datetime
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class AssessmentQuestion(BaseModel):
    """A single assessment question.

    Attributes:
        question_id: Unique identifier for the question.
        section: Section this question belongs to.
        question_text: The actual question text.
        question_type: Type of question (MCQ, SHORT_ANSWER, SCENARIO).
        difficulty: Difficulty level (EASY, MEDIUM, HARD).
        skill_tested: The skill this question tests.
        options: Multiple choice options (for MCQ type).
        correct_answer: The correct answer or answer key.
        points: Points awarded for correct answer.
    """

    question_id: str = Field(description="Unique question identifier")
    section: str = Field(description="Section: TECHNICAL, SCENARIO, PROBLEM_SOLVING")
    question_text: str = Field(description="The question text")
    question_type: str = Field(description="MCQ, SHORT_ANSWER, or SCENARIO")
    difficulty: str = Field(description="EASY, MEDIUM, or HARD")
    skill_tested: str = Field(description="The skill being tested")
    options: Optional[list[str]] = Field(default=None, description="MCQ options")
    correct_answer: Optional[str] = Field(default=None, description="Correct answer")
    points: int = Field(default=10, description="Points for correct answer")


class AssessmentGenerationResult(BaseModel):
    """Result of generating or scoring an assessment.

    Attributes:
        success: Whether the operation succeeded.
        assessment_file_path: Path to the saved assessment JSON file.
        total_questions: Number of questions generated.
        sections: Summary of sections and question counts.
        difficulty_distribution: Count of questions per difficulty level.
        candidate_name: Name of the candidate.
        job_title: Title of the job vacancy.
        error_message: Error details if generation failed.
    """

    success: bool = Field(description="Whether the operation succeeded")
    assessment_file_path: str = Field(default="", description="Path to saved assessment")
    total_questions: int = Field(default=0, description="Number of questions")
    sections: list[dict] = Field(default_factory=list, description="Section summaries")
    difficulty_distribution: dict = Field(default_factory=dict, description="Difficulty breakdown")
    candidate_name: str = Field(default="", description="Candidate name")
    job_title: str = Field(default="", description="Job title")
    error_message: Optional[str] = Field(default=None, description="Error details")


class AssessmentScoreResult(BaseModel):
    """Result of scoring an assessment.

    Attributes:
        success: Whether scoring succeeded.
        candidate_name: Name of the candidate.
        total_score: Total points scored.
        max_score: Maximum possible score.
        percentage: Score as a percentage.
        section_scores: Per-section scores.
        skill_scores: Per-skill scores.
        pass_status: PASS, BORDERLINE, or FAIL.
        flags: Any red flags detected.
        error_message: Error details if scoring failed.
    """

    success: bool = Field(description="Whether scoring succeeded")
    candidate_name: str = Field(default="", description="Candidate name")
    total_score: int = Field(default=0, description="Total points scored")
    max_score: int = Field(default=0, description="Maximum possible score")
    percentage: float = Field(default=0.0, description="Score percentage")
    section_scores: list[dict] = Field(default_factory=list, description="Per-section scores")
    skill_scores: dict = Field(default_factory=dict, description="Per-skill scores")
    pass_status: str = Field(default="", description="PASS, BORDERLINE, or FAIL")
    flags: list[str] = Field(default_factory=list, description="Red flags detected")
    error_message: Optional[str] = Field(default=None, description="Error details")


@tool
def assessment_generator(
    action: str,
    output_dir: str = "assessments",
    candidate_name: str = "",
    job_title: str = "",
    job_id: str = "",
    matched_skills: Optional[str] = None,
    missing_skills: Optional[str] = None,
    experience_years: int = 0,
    work_highlights: Optional[str] = None,
    assessment_content: Optional[str] = None,
    candidate_answers: Optional[str] = None,
    assessment_file_path: Optional[str] = None,
) -> dict:
    """Generate personalized technical assessments or score candidate responses.

    Supports two actions:
    - 'generate': Create a personalized assessment based on candidate profile and job requirements.
    - 'score': Grade a candidate's responses against the assessment answer key.

    Args:
        action: 'generate' to create an assessment, 'score' to grade responses.
        output_dir: Directory to save assessment files.
        candidate_name: Full name of the candidate.
        job_title: Title of the job vacancy.
        job_id: ID of the job vacancy.
        matched_skills: Comma-separated skills the candidate has that match the job.
        missing_skills: Comma-separated required skills the candidate lacks.
        experience_years: Candidate's years of experience (for difficulty calibration).
        work_highlights: Comma-separated key achievements from work experience.
        assessment_content: JSON string of the assessment questions (from LLM).
        candidate_answers: JSON string of candidate's answers (for scoring).
        assessment_file_path: Path to existing assessment file (for scoring).

    Returns:
        dict: Assessment generation or scoring result.
    """
    if action == "generate":
        return _generate_assessment(
            output_dir=output_dir,
            candidate_name=candidate_name,
            job_title=job_title,
            job_id=job_id,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            experience_years=experience_years,
            work_highlights=work_highlights,
            assessment_content=assessment_content,
        ).model_dump()
    elif action == "score":
        return _score_assessment(
            assessment_file_path=assessment_file_path or "",
            candidate_answers=candidate_answers or "{}",
            candidate_name=candidate_name,
        ).model_dump()
    else:
        return {"success": False, "error_message": f"Unknown action: {action}. Use 'generate' or 'score'."}


def _generate_assessment(
    output_dir: str,
    candidate_name: str,
    job_title: str,
    job_id: str,
    matched_skills: Optional[str],
    missing_skills: Optional[str],
    experience_years: int,
    work_highlights: Optional[str],
    assessment_content: Optional[str],
) -> AssessmentGenerationResult:
    """Generate and save a personalized assessment.

    Args:
        output_dir: Directory to save the assessment file.
        candidate_name: Candidate's name.
        job_title: Job vacancy title.
        job_id: Job vacancy ID.
        matched_skills: Comma-separated matched skills.
        missing_skills: Comma-separated missing skills.
        experience_years: Years of experience.
        work_highlights: Key work achievements.
        assessment_content: JSON string of LLM-generated assessment questions.

    Returns:
        AssessmentGenerationResult: Result of the generation.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)

        # Determine difficulty level based on experience
        difficulty_level: str = _calibrate_difficulty(experience_years)

        # Parse skills
        matched: list[str] = [s.strip() for s in (matched_skills or "").split(",") if s.strip()]
        missing: list[str] = [s.strip() for s in (missing_skills or "").split(",") if s.strip()]
        highlights: list[str] = [s.strip() for s in (work_highlights or "").split(",") if s.strip()]

        # Parse LLM-generated assessment content if provided
        questions: list[dict] = []
        if assessment_content:
            try:
                questions = json.loads(assessment_content)
                if isinstance(questions, dict) and "questions" in questions:
                    questions = questions["questions"]
            except json.JSONDecodeError:
                pass

        # If no questions from LLM, create a template structure
        if not questions:
            questions = _create_assessment_template(
                matched_skills=matched,
                missing_skills=missing,
                highlights=highlights,
                difficulty_level=difficulty_level,
                job_title=job_title,
            )

        # Build the full assessment document
        timestamp: str = datetime.now().isoformat()
        safe_name: str = candidate_name.lower().replace(" ", "_")
        safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
        date_str: str = datetime.now().strftime("%Y%m%d_%H%M%S")

        assessment_doc: dict = {
            "metadata": {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "job_id": job_id,
                "difficulty_level": difficulty_level,
                "experience_years": experience_years,
                "generated_at": timestamp,
                "total_questions": len(questions),
                "time_limit_minutes": 30,
                "max_score": sum(q.get("points", 10) for q in questions),
            },
            "skills_tested": {
                "matched_skills": matched,
                "missing_skills": missing,
            },
            "questions": questions,
        }

        # Save assessment to file
        filename: str = f"assessment_{safe_name}_{job_id}_{date_str}.json"
        file_path: str = os.path.join(output_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(assessment_doc, f, indent=2, ensure_ascii=False)

        # Build section summary
        sections: list[dict] = _summarize_sections(questions)
        difficulty_dist: dict = _get_difficulty_distribution(questions)

        return AssessmentGenerationResult(
            success=True,
            assessment_file_path=file_path,
            total_questions=len(questions),
            sections=sections,
            difficulty_distribution=difficulty_dist,
            candidate_name=candidate_name,
            job_title=job_title,
        )

    except Exception as e:
        return AssessmentGenerationResult(
            success=False,
            error_message=f"Assessment generation failed: {type(e).__name__}: {str(e)}",
            candidate_name=candidate_name,
            job_title=job_title,
        )


def _score_assessment(
    assessment_file_path: str,
    candidate_answers: str,
    candidate_name: str,
) -> AssessmentScoreResult:
    """Score a candidate's assessment responses.

    Args:
        assessment_file_path: Path to the assessment JSON file.
        candidate_answers: JSON string of candidate's answers ({question_id: answer}).
        candidate_name: Candidate's name.

    Returns:
        AssessmentScoreResult: Scoring results with flags.
    """
    try:
        if not os.path.exists(assessment_file_path):
            return AssessmentScoreResult(
                success=False,
                candidate_name=candidate_name,
                error_message=f"Assessment file not found: {assessment_file_path}",
            )

        with open(assessment_file_path, "r", encoding="utf-8") as f:
            assessment: dict = json.load(f)

        answers: dict = json.loads(candidate_answers)

        questions: list[dict] = assessment.get("questions", [])
        total_score: int = 0
        max_score: int = 0
        section_tracker: dict[str, dict] = {}
        skill_tracker: dict[str, dict] = {}
        flags: list[str] = []

        for q in questions:
            q_id: str = q.get("question_id", "")
            section: str = q.get("section", "GENERAL")
            skill: str = q.get("skill_tested", "general")
            points: int = q.get("points", 10)
            max_score += points

            # Track sections
            if section not in section_tracker:
                section_tracker[section] = {"scored": 0, "max": 0, "count": 0}
            section_tracker[section]["max"] += points
            section_tracker[section]["count"] += 1

            # Track skills
            if skill not in skill_tracker:
                skill_tracker[skill] = {"scored": 0, "max": 0}
            skill_tracker[skill]["max"] += points

            # Score if candidate answered
            if q_id in answers:
                candidate_answer: str = str(answers[q_id]).strip().lower()
                correct_answer: str = str(q.get("correct_answer", "")).strip().lower()

                if q.get("question_type") == "MCQ" and candidate_answer == correct_answer:
                    total_score += points
                    section_tracker[section]["scored"] += points
                    skill_tracker[skill]["scored"] += points
                elif q.get("question_type") in ("SHORT_ANSWER", "SCENARIO"):
                    # For open-ended, award partial credit (will be LLM-judged)
                    partial: int = int(points * 0.7)  # Default 70% for answered
                    total_score += partial
                    section_tracker[section]["scored"] += partial
                    skill_tracker[skill]["scored"] += partial

        # Calculate percentage
        percentage: float = round((total_score / max_score * 100), 1) if max_score > 0 else 0.0

        # Determine pass status
        pass_status: str = "PASS" if percentage >= 70 else ("BORDERLINE" if percentage >= 50 else "FAIL")

        # Detect red flags — skill claim mismatches
        matched_skills: list[str] = assessment.get("skills_tested", {}).get("matched_skills", [])
        for skill in matched_skills:
            skill_lower: str = skill.lower()
            if skill_lower in skill_tracker:
                skill_pct: float = (
                    skill_tracker[skill_lower]["scored"] / skill_tracker[skill_lower]["max"] * 100
                    if skill_tracker[skill_lower]["max"] > 0
                    else 0
                )
                if skill_pct < 40:
                    flags.append(
                        f"⚠️ Skill claim mismatch: Candidate claims '{skill}' "
                        f"but scored only {skill_pct:.0f}% on related questions"
                    )

        # Build section scores list
        section_scores: list[dict] = [
            {
                "section": section,
                "scored": data["scored"],
                "max": data["max"],
                "percentage": round(data["scored"] / data["max"] * 100, 1) if data["max"] > 0 else 0,
                "questions": data["count"],
            }
            for section, data in section_tracker.items()
        ]

        return AssessmentScoreResult(
            success=True,
            candidate_name=candidate_name,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            section_scores=section_scores,
            skill_scores={k: v for k, v in skill_tracker.items()},
            pass_status=pass_status,
            flags=flags,
        )

    except json.JSONDecodeError as e:
        return AssessmentScoreResult(
            success=False,
            candidate_name=candidate_name,
            error_message=f"Invalid JSON in answers: {str(e)}",
        )
    except Exception as e:
        return AssessmentScoreResult(
            success=False,
            candidate_name=candidate_name,
            error_message=f"Scoring failed: {type(e).__name__}: {str(e)}",
        )


def _calibrate_difficulty(experience_years: int) -> str:
    """Determine assessment difficulty based on experience level.

    Args:
        experience_years: Candidate's years of experience.

    Returns:
        Difficulty level string.
    """
    if experience_years <= 1:
        return "JUNIOR"
    elif experience_years <= 3:
        return "MID"
    elif experience_years <= 6:
        return "SENIOR"
    else:
        return "LEAD"


def _create_assessment_template(
    matched_skills: list[str],
    missing_skills: list[str],
    highlights: list[str],
    difficulty_level: str,
    job_title: str,
) -> list[dict]:
    """Create a template assessment structure when LLM doesn't provide questions.

    This serves as a fallback structure that the LLM will populate with actual questions.

    Args:
        matched_skills: Skills the candidate has.
        missing_skills: Skills the candidate lacks.
        highlights: Work experience highlights.
        difficulty_level: Calibrated difficulty.
        job_title: Job title for context.

    Returns:
        List of question template dicts.
    """
    questions: list[dict] = []
    q_counter: int = 1

    # Section 1: Technical — Test matched skills (verify depth)
    for skill in matched_skills[:3]:
        questions.append({
            "question_id": f"Q{q_counter:03d}",
            "section": "TECHNICAL",
            "question_text": f"[LLM to generate a {difficulty_level}-level question about {skill} for a {job_title} role]",
            "question_type": "MCQ",
            "difficulty": "MEDIUM" if difficulty_level in ("JUNIOR", "MID") else "HARD",
            "skill_tested": skill.lower(),
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_answer": "A",
            "points": 10,
        })
        q_counter += 1

    # Section 1 continued: Test missing skills (assess learning ability)
    for skill in missing_skills[:3]:
        questions.append({
            "question_id": f"Q{q_counter:03d}",
            "section": "TECHNICAL",
            "question_text": f"[LLM to generate a foundational question about {skill}]",
            "question_type": "MCQ",
            "difficulty": "EASY",
            "skill_tested": skill.lower(),
            "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
            "correct_answer": "A",
            "points": 10,
        })
        q_counter += 1

    # Section 2: Scenario-based (from work experience)
    for highlight in highlights[:2]:
        questions.append({
            "question_id": f"Q{q_counter:03d}",
            "section": "SCENARIO",
            "question_text": f"[LLM to generate a scenario question related to: {highlight}]",
            "question_type": "SCENARIO",
            "difficulty": "MEDIUM",
            "skill_tested": "problem_solving",
            "points": 15,
        })
        q_counter += 1

    # Section 3: Problem solving
    questions.append({
        "question_id": f"Q{q_counter:03d}",
        "section": "PROBLEM_SOLVING",
        "question_text": f"[LLM to generate a practical problem for a {job_title} role]",
        "question_type": "SHORT_ANSWER",
        "difficulty": "HARD" if difficulty_level in ("SENIOR", "LEAD") else "MEDIUM",
        "skill_tested": "critical_thinking",
        "points": 20,
    })

    return questions


def _summarize_sections(questions: list[dict]) -> list[dict]:
    """Summarize questions by section.

    Args:
        questions: List of question dicts.

    Returns:
        List of section summary dicts.
    """
    section_map: dict[str, int] = {}
    for q in questions:
        section: str = q.get("section", "GENERAL")
        section_map[section] = section_map.get(section, 0) + 1

    return [{"section": s, "question_count": c} for s, c in section_map.items()]


def _get_difficulty_distribution(questions: list[dict]) -> dict:
    """Get difficulty level distribution across questions.

    Args:
        questions: List of question dicts.

    Returns:
        Dict mapping difficulty levels to counts.
    """
    dist: dict[str, int] = {}
    for q in questions:
        diff: str = q.get("difficulty", "MEDIUM")
        dist[diff] = dist.get(diff, 0) + 1
    return dist
