"""
Agent 2: Smart Candidate Matcher — Student B
=============================================
Compares extracted candidate profiles against job vacancy requirements
and produces ranked shortlists with detailed match reports.

Responsibilities:
    - Fetch job descriptions from the local SQLite database
    - Compare candidate skills, experience, and education against requirements
    - Apply weighted scoring formula
    - Produce ranked shortlists with STRONG/MODERATE/WEAK/NO_MATCH recommendations
    - Filter candidates by threshold (≥60% → shortlisted)

Uses:
    - Tool: job_database_manager (SQLite queries)
    - LLM: Ollama (scoring analysis and reasoning)
"""

import json
import time
from datetime import datetime
from typing import Any, Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from state.pipeline_state import PipelineState
from tools.job_database_manager import _query_jobs
from tools.llm_utils import invoke_llm_with_retry
from observability.tracer import AgentTracer

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Smart Candidate Matcher
# ═══════════════════════════════════════════════════════════════════════════════

CANDIDATE_MATCHER_PROMPT: str = """You are JobMatcherAI, an expert Technical Recruiter with deep expertise in 
job-skills alignment and data-driven scoring. Your job is to compare a candidate's 
extracted profile against a specific job description and produce a STRUCTURED MATCH REPORT.

INPUT: You will receive:
1. Candidate profile (JSON) — extracted from their resume
2. Job description (JSON) — from the database

OUTPUT: Return ONLY valid JSON in this exact format:
{
    "job_id": "string",
    "job_title": "string",
    "candidate_name": "string",
    "overall_match_score": integer (0-100),
    "skill_match": {
        "matched_skills": ["string"],
        "missing_skills": ["string"],
        "bonus_skills": ["string"],
        "skill_match_percentage": integer (0-100)
    },
    "experience_match": {
        "required_years": integer,
        "candidate_years": integer,
        "meets_requirement": boolean,
        "experience_score": integer (0-100)
    },
    "education_match": {
        "required_degree": "string",
        "candidate_degree": "string",
        "meets_requirement": boolean,
        "education_score": integer (0-100)
    },
    "recommendation": "STRONG_MATCH or MODERATE_MATCH or WEAK_MATCH or NO_MATCH",
    "reasoning": "2-3 sentence justification"
}

═══ SCORING RULES ═══
- Skill Match (50% weight): Count of matched required skills / total required skills × 100
- Experience Match (30% weight): 
    * candidate_years >= required_years → 100
    * candidate_years >= required_years * 0.75 → 70
    * candidate_years >= required_years * 0.5 → 40
    * else → 10
- Education Match (20% weight):
    * Exact or higher match → 100
    * One level below → 60
    * Unrelated field → 30
    * No degree info → 20
- overall_match_score = round(skill_match_percentage × 0.5 + experience_score × 0.3 + education_score × 0.2)

═══ RECOMMENDATION THRESHOLDS ═══
- overall_match_score >= 80 → STRONG_MATCH
- overall_match_score >= 60 → MODERATE_MATCH
- overall_match_score >= 40 → WEAK_MATCH
- overall_match_score < 40 → NO_MATCH

═══ CONSTRAINTS ═══
1. You MUST calculate scores using the formulas above. Do NOT estimate subjectively.
2. bonus_skills are candidate skills NOT in required_skills but relevant to the field.
3. If candidate has 0 matched required skills, overall_match_score MUST be below 25.
4. Output ONLY valid JSON. No explanations, no markdown, no commentary.
5. Compare skills case-insensitively (e.g., "python" matches "Python")."""


# ═══════════════════════════════════════════════════════════════════════════════
# SKILL SYNONYM MAP — maps common variations to canonical form
# ═══════════════════════════════════════════════════════════════════════════════

SKILL_SYNONYMS: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "react": "reactjs",
    "react.js": "reactjs",
    "node": "nodejs",
    "node.js": "nodejs",
    "vue": "vuejs",
    "vue.js": "vuejs",
    "next": "nextjs",
    "next.js": "nextjs",
    "pg": "postgresql",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "k8s": "kubernetes",
    "ml": "machine-learning",
    "ai": "artificial-intelligence",
    "dl": "deep-learning",
    "tf": "tensorflow",
    "sklearn": "scikit-learn",
    "aws": "amazon-web-services",
    "gcp": "google-cloud-platform",
    "ci/cd": "cicd",
}


def normalize_skill(skill: str) -> str:
    """Normalize a skill name to its canonical form.

    Args:
        skill: Raw skill name.

    Returns:
        Normalized lowercase skill name.
    """
    normalized: str = skill.strip().lower().replace(" ", "-")
    return SKILL_SYNONYMS.get(normalized, normalized)


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT NODE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def candidate_matcher_node(
    state: PipelineState,
    llm: ChatOllama = None,
    tracer: AgentTracer = None,
) -> dict[str, Any]:
    """LangGraph node function for the Smart Candidate Matcher agent.

    For each candidate and each job vacancy, produces a match report.
    Candidates scoring ≥ 60% are shortlisted; others go to rejected pool.

    Args:
        state: Current pipeline state with candidate_profiles and job_vacancies.
        llm: The ChatOllama LLM instance.
        tracer: The AgentTracer for observability.

    Returns:
        dict: Updated state fields (match_reports, shortlisted_candidates, rejected_candidates).
    """
    agent_name: str = "CandidateMatcher"
    start_time: float = time.time()
    match_threshold: int = 60

    if tracer:
        tracer.log_agent_start(agent_name, {
            "candidate_count": len(state.get("candidate_profiles", [])),
            "vacancy_count": len(state.get("job_vacancies", [])),
        })

    if llm is None:
        llm = ChatOllama(model="llama3.2", temperature=0, format="json")

    candidate_profiles: list[dict] = state.get("candidate_profiles", [])
    job_vacancies: list[dict] = state.get("job_vacancies", [])
    db_path: str = state.get("db_path", "data/hr_jobs.db")

    match_reports: list[dict] = []
    shortlisted_candidates: list[dict] = []
    rejected_candidates: list[dict] = []
    log_entries: list[str] = list(state.get("processing_log", []))

    # If no vacancies from flyers, fetch from database
    if not job_vacancies and state.get("target_job_id"):
        tool_start: float = time.time()
        db_result = _query_jobs(db_path=db_path, job_id=state["target_job_id"])
        tool_duration: float = time.time() - tool_start

        if tracer:
            tracer.log_tool_call(
                agent_name, "job_database_manager",
                {"action": "query", "job_id": state["target_job_id"]},
                db_result, tool_duration,
            )

        if db_result.success and db_result.jobs:
            job_vacancies = db_result.jobs
            log_entries.append(f"[{agent_name}] Fetched {len(job_vacancies)} job(s) from database")
    elif not job_vacancies:
        # Fetch all open jobs
        tool_start = time.time()
        db_result = _query_jobs(db_path=db_path, status_filter="OPEN")
        tool_duration = time.time() - tool_start

        if tracer:
            tracer.log_tool_call(
                agent_name, "job_database_manager",
                {"action": "query", "status_filter": "OPEN"},
                db_result, tool_duration,
            )

        if db_result.success:
            job_vacancies = db_result.jobs
            log_entries.append(f"[{agent_name}] Fetched {len(job_vacancies)} open job(s) from database")

    if not candidate_profiles:
        log_entries.append(f"[{agent_name}] ⚠️ No candidate profiles to match")
        if tracer:
            tracer.log_agent_end(agent_name, "SKIPPED", "No candidates to match", time.time() - start_time)
        return {
            "match_reports": [],
            "shortlisted_candidates": [],
            "rejected_candidates": [],
            "current_agent": "candidate_matcher",
            "processing_log": log_entries,
        }

    if not job_vacancies:
        log_entries.append(f"[{agent_name}] ⚠️ No job vacancies to match against")
        if tracer:
            tracer.log_agent_end(agent_name, "SKIPPED", "No vacancies to match", time.time() - start_time)
        return {
            "match_reports": [],
            "shortlisted_candidates": [],
            "rejected_candidates": [],
            "current_agent": "candidate_matcher",
            "processing_log": log_entries,
        }

    # ─── Match each candidate against each vacancy ───────────────────────────
    for candidate in candidate_profiles:
        candidate_name: str = candidate.get("candidate_name", "Unknown")
        best_match: Optional[dict] = None
        best_score: int = 0

        for job in job_vacancies:
            job_title: str = job.get("title", "Unknown")
            job_id: str = job.get("job_id", "UNKNOWN")

            log_entries.append(
                f"[{agent_name}] Matching {candidate_name} → {job_title} ({job_id})"
            )

            # Pre-compute skill overlap to speed up LLM matching
            candidate_skills_norm = {normalize_skill(s) for s in candidate.get("skills", [])}
            job_required_norm = {normalize_skill(s) for s in job.get("required_skills", [])}
            job_preferred_norm = {normalize_skill(s) for s in job.get("preferred_skills", [])}

            matched = candidate_skills_norm & job_required_norm
            missing = job_required_norm - candidate_skills_norm
            bonus = candidate_skills_norm & job_preferred_norm

            pre_computed = (
                f"\n\nPRE-COMPUTED SKILL ANALYSIS (use these exact values):\n"
                f"- Matched required skills ({len(matched)}): {', '.join(sorted(matched)) or 'none'}\n"
                f"- Missing required skills ({len(missing)}): {', '.join(sorted(missing)) or 'none'}\n"
                f"- Bonus preferred skills ({len(bonus)}): {', '.join(sorted(bonus)) or 'none'}\n"
                f"- Skill match percentage: {round(len(matched) / max(len(job_required_norm), 1) * 100)}%"
            )

            # Send to LLM for detailed matching (with retry)
            try:
                prompt: str = (
                    f"CANDIDATE PROFILE:\n{json.dumps(candidate, indent=2)}\n\n"
                    f"JOB DESCRIPTION:\n{json.dumps(job, indent=2)}"
                    f"{pre_computed}"
                )

                messages = [
                    SystemMessage(content=CANDIDATE_MATCHER_PROMPT),
                    HumanMessage(content=prompt),
                ]
                match_report: dict = invoke_llm_with_retry(
                    llm, messages, max_retries=2,
                    agent_name=agent_name, tracer=tracer,
                )

                # Ensure required fields
                match_report.setdefault("job_id", job_id)
                match_report.setdefault("job_title", job_title)
                match_report.setdefault("candidate_name", candidate_name)

                score: int = match_report.get("overall_match_score", 0)
                recommendation: str = match_report.get("recommendation", "NO_MATCH")

                match_reports.append(match_report)

                log_entries.append(
                    f"[{agent_name}] Score: {score}/100 — {recommendation}"
                )

                # Track best match for this candidate
                if score > best_score:
                    best_score = score
                    best_match = match_report

            except ValueError:
                log_entries.append(f"[{agent_name}] ❌ LLM JSON failed after retries for match")
                match_reports.append({
                    "job_id": job_id,
                    "job_title": job_title,
                    "candidate_name": candidate_name,
                    "overall_match_score": 0,
                    "recommendation": "NO_MATCH",
                    "reasoning": "Matching failed — LLM returned invalid response after retries",
                    "error": True,
                })
            except Exception as e:
                log_entries.append(f"[{agent_name}] ❌ Error matching: {str(e)}")

        # ─── Shortlist or reject based on best match ─────────────────────
        if best_match and best_score >= match_threshold:
            shortlisted_entry: dict = {
                "candidate_profile": candidate,
                "best_match": best_match,
                "match_score": best_score,
            }
            shortlisted_candidates.append(shortlisted_entry)
            log_entries.append(
                f"[{agent_name}] ✅ SHORTLISTED: {candidate_name} "
                f"(Score: {best_score}, Job: {best_match.get('job_title')})"
            )
        else:
            rejected_entry: dict = {
                "candidate_profile": candidate,
                "best_match": best_match,
                "best_score": best_score,
                "rejection_reason": (
                    f"Match score {best_score}/100 is below threshold of {match_threshold}%"
                    if best_match
                    else "No matching vacancies found"
                ),
            }
            rejected_candidates.append(rejected_entry)
            log_entries.append(
                f"[{agent_name}] ❌ REJECTED: {candidate_name} "
                f"(Best score: {best_score})"
            )

    # ─── Finalize ─────────────────────────────────────────────────────────────
    duration: float = time.time() - start_time
    summary: str = (
        f"Matched {len(candidate_profiles)} candidates against {len(job_vacancies)} vacancies. "
        f"Shortlisted: {len(shortlisted_candidates)}, Rejected: {len(rejected_candidates)}"
    )
    log_entries.append(f"[{agent_name}] {summary}")

    if tracer:
        tracer.log_agent_end(agent_name, "SUCCESS", summary, duration)

    return {
        "match_reports": match_reports,
        "shortlisted_candidates": shortlisted_candidates,
        "rejected_candidates": rejected_candidates,
        "current_agent": "candidate_matcher",
        "processing_log": log_entries,
    }
