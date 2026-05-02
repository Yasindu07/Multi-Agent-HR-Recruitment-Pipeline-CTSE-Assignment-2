"""
Pipeline State Definition
=========================
Defines the global state (TypedDict) that flows through the entire agent pipeline.
Each agent reads from and writes to specific fields, ensuring no context is lost
between agent transitions.

State Flow:
    Input → Agent 1 (extraction) → Agent 2 (matching) → Agent 3 (assessment) → Agent 4 (interview)
"""

from typing import TypedDict, Optional, Annotated
from langgraph.graph import add_messages


class CandidateProfile(TypedDict):
    """Extracted candidate data from a resume."""
    candidate_name: str
    email: str
    phone: str
    years_of_experience: int
    education: list[dict]
    skills: list[str]
    work_experience: list[dict]
    github_url: str
    portfolio_url: str
    certifications: list[str]


class JobVacancy(TypedDict):
    """Extracted job vacancy data from a flyer or manual input."""
    job_id: str
    title: str
    department: str
    required_skills: list[str]
    preferred_skills: list[str]
    min_experience_years: int
    required_education: str
    description: str
    salary_range: str
    status: str


class MatchReport(TypedDict):
    """Job matching result for a single candidate-vacancy pair."""
    job_id: str
    job_title: str
    candidate_name: str
    overall_match_score: int
    skill_match: dict
    experience_match: dict
    education_match: dict
    recommendation: str
    reasoning: str


class AssessmentResult(TypedDict):
    """Assessment/quiz result for a candidate."""
    candidate_name: str
    job_id: str
    job_title: str
    assessment_content: str
    total_questions: int
    sections: list[dict]
    difficulty_level: str
    assessment_file_path: str


class InterviewGuide(TypedDict):
    """Interview preparation guide for a candidate."""
    candidate_name: str
    job_title: str
    report_content: str
    file_path: str
    recommendation: str


class PipelineState(TypedDict):
    """Global state that flows through the entire HR recruitment agent pipeline.

    This is the single source of truth. Each agent reads from and writes to
    specific fields, ensuring no context is lost between agent transitions.

    Write Boundaries:
        - Agent 1 writes: candidate_profiles, job_vacancies, parse_errors
        - Agent 2 writes: match_reports, shortlisted_candidates, rejected_candidates
        - Agent 3 writes: assessments, assessment_results
        - Agent 4 writes: interview_guides, comparison_report
    """

    # ─── Inputs ───
    resume_paths: list[str]
    job_flyer_paths: list[str]
    target_job_id: Optional[str]
    db_path: str

    # ─── Agent 1 Outputs (Document Intelligence Extractor) ───
    candidate_profiles: list[dict]
    job_vacancies: list[dict]
    parse_errors: list[dict]

    # ─── Agent 2 Outputs (Smart Candidate Matcher) ───
    match_reports: list[dict]
    shortlisted_candidates: list[dict]
    rejected_candidates: list[dict]

    # ─── Agent 3 Outputs (Assessment Coordinator) ───
    assessments: list[dict]
    assessment_results: list[dict]

    # ─── Agent 4 Outputs (Interview Strategist) ───
    interview_guides: list[dict]
    comparison_report: Optional[str]

    # ─── Pipeline Metadata ───
    current_agent: str
    pipeline_status: str  # RUNNING, COMPLETED, FAILED
    processing_log: list[str]  # Append-only observability log
    error_log: list[str]

    # ─── LangGraph Messages ───
    messages: Annotated[list, add_messages]
