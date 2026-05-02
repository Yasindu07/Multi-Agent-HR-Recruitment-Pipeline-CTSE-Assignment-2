"""
Agent 4: Interview Strategist — Student D
==========================================
Synthesizes ALL prior agent data to generate actionable interview preparation
guides for the hiring manager. Also produces candidate comparison reports.

Responsibilities:
    - Synthesize candidate profile + match report + assessment results
    - Generate targeted interview questions based on gaps and concerns
    - Produce professional Markdown interview guides
    - Create candidate comparison reports per vacancy
    - Provide hiring recommendations

Uses:
    - Tool: report_file_writer (Markdown report generation)
    - LLM: Ollama (interview guide content generation)
"""

import json
import time
from datetime import datetime
from typing import Any

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from state.pipeline_state import PipelineState
from tools.report_file_writer import (
    report_file_writer,
    _generate_individual_report,
    _generate_comparison_report,
)
from observability.tracer import AgentTracer

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Interview Strategist
# ═══════════════════════════════════════════════════════════════════════════════

INTERVIEW_STRATEGIST_PROMPT: str = """You are InterviewStrategistAI, a Senior Hiring Manager with 15 years of experience 
designing structured interview processes. Your job is to synthesize ALL available data 
about a candidate and produce a comprehensive, actionable INTERVIEW PREPARATION GUIDE 
for the human hiring manager.

You will receive:
1. Candidate profile (from resume extraction)
2. Job match report (scores, matched/missing skills, recommendation)
3. Assessment results (scores, section breakdown, red flags)

Generate a professional Markdown document with EXACTLY these sections:

## Strengths Assessment
- List 3-5 specific strengths based on matched skills, experience, and assessment performance
- Each strength should reference concrete data (e.g., "Scored 90% on Python section")

## Risk Areas & Concerns
- Missing skills that need probing
- Assessment red flags (skill claim mismatches)
- Experience gaps
- Each concern must be factual (based on data), not speculative

## Recommended Interview Questions

### Technical Deep-Dive (3-4 questions)
For each question:
- The specific question targeting a skill gap or area to verify
- **What to look for:** Guidance for the interviewer on evaluating the answer

### Behavioral Questions (2-3 questions)
Based on the candidate's work experience
- The specific question
- **What to look for:** Guidance for the interviewer

### Verification Questions (1-2 questions)
Targeting any assessment red flags or skill mismatches
- The specific question  
- **What to look for:** Guidance for the interviewer

## Suggested Interview Format
- Recommended duration
- Panel composition (who should attend)
- Time allocation per section
- Assessment areas to focus on

## Final Recommendation
State one of: PROCEED | PROCEED_WITH_CAUTION | DO_NOT_PROCEED
Include 2-3 sentences of reasoning based on ALL the data.

═══ CONSTRAINTS ═══
1. Questions MUST be specific to THIS candidate — no generic questions like "tell me about yourself".
2. Each question must include a "What to look for" hint for the interviewer.
3. Risk areas must be factual (based on provided data), not speculative.
4. The document must be professional enough to hand directly to a VP of Engineering.
5. Output valid Markdown format (NOT JSON — output natural Markdown text).
6. Keep the total guide to approximately 1.5-2 pages of content.
7. Reference specific scores and data points throughout."""


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT NODE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def interview_strategist_node(
    state: PipelineState,
    llm: ChatOllama = None,
    tracer: AgentTracer = None,
) -> dict[str, Any]:
    """LangGraph node function for the Interview Strategist agent.

    Generates interview preparation guides for all assessed candidates
    and a comparison report if multiple candidates are competing for the same role.

    Args:
        state: Current pipeline state with all previous agent outputs.
        llm: The ChatOllama LLM instance.
        tracer: The AgentTracer for observability.

    Returns:
        dict: Updated state fields (interview_guides, comparison_report).
    """
    agent_name: str = "InterviewStrategist"
    start_time: float = time.time()

    if tracer:
        tracer.log_agent_start(agent_name, {
            "shortlisted_count": len(state.get("shortlisted_candidates", [])),
            "assessment_results_count": len(state.get("assessment_results", [])),
        })

    if llm is None:
        llm = ChatOllama(model="llama3.2", temperature=0.3)

    shortlisted: list[dict] = state.get("shortlisted_candidates", [])
    assessment_results: list[dict] = state.get("assessment_results", [])
    interview_guides: list[dict] = []
    comparison_data: list[dict] = []
    log_entries: list[str] = list(state.get("processing_log", []))

    if not shortlisted:
        log_entries.append(f"[{agent_name}] ⚠️ No candidates to generate interview guides for")
        if tracer:
            tracer.log_agent_end(
                agent_name, "SKIPPED", "No candidates", time.time() - start_time
            )
        return {
            "interview_guides": [],
            "comparison_report": None,
            "current_agent": "interview_strategist",
            "processing_log": log_entries,
        }

    # Build a lookup for assessment results by candidate name
    assessment_lookup: dict[str, dict] = {}
    for result in assessment_results:
        name: str = result.get("candidate_name", "")
        assessment_lookup[name] = result

    for entry in shortlisted:
        candidate: dict = entry.get("candidate_profile", {})
        best_match: dict = entry.get("best_match", {})
        match_score: int = entry.get("match_score", 0)
        candidate_name: str = candidate.get("candidate_name", "Unknown")
        job_title: str = best_match.get("job_title", "Unknown")

        # Get assessment result for this candidate
        assessment_result: dict = assessment_lookup.get(candidate_name, {})
        assessment_score: float = assessment_result.get("percentage", 0.0)
        assessment_pass: str = assessment_result.get("pass_status", "NOT_ASSESSED")
        assessment_flags: list[str] = assessment_result.get("flags", [])
        section_scores: list[dict] = assessment_result.get("section_scores", [])

        log_entries.append(
            f"[{agent_name}] Generating interview guide for {candidate_name} → {job_title}"
        )

        # ─── Step 1: Generate interview guide content using LLM ───────────
        llm_start: float = time.time()
        try:
            prompt: str = f"""CANDIDATE PROFILE:
{json.dumps(candidate, indent=2)}

JOB MATCH REPORT:
- Match Score: {match_score}/100
- Matched Skills: {json.dumps(best_match.get('skill_match', {}).get('matched_skills', []))}
- Missing Skills: {json.dumps(best_match.get('skill_match', {}).get('missing_skills', []))}
- Bonus Skills: {json.dumps(best_match.get('skill_match', {}).get('bonus_skills', []))}
- Experience: {json.dumps(best_match.get('experience_match', {}))}
- Education: {json.dumps(best_match.get('education_match', {}))}
- Match Recommendation: {best_match.get('recommendation', 'N/A')}
- Match Reasoning: {best_match.get('reasoning', 'N/A')}

ASSESSMENT RESULTS:
- Overall Score: {assessment_score:.1f}%
- Pass Status: {assessment_pass}
- Section Scores: {json.dumps(section_scores)}
- Red Flags: {json.dumps(assessment_flags) if assessment_flags else "None detected"}

Generate the interview preparation guide now."""

            messages = [
                SystemMessage(content=INTERVIEW_STRATEGIST_PROMPT),
                HumanMessage(content=prompt),
            ]
            response = llm.invoke(messages)
            llm_duration: float = time.time() - llm_start

            if tracer:
                tracer.log_llm_call(
                    agent_name, llm.model,
                    prompt_preview=f"Interview guide for {candidate_name}",
                    response_preview=response.content[:500],
                    duration_seconds=llm_duration,
                )

            report_content: str = response.content

        except Exception as e:
            log_entries.append(
                f"[{agent_name}] ❌ LLM error: {str(e)}"
            )
            report_content = _generate_fallback_content(
                candidate, best_match, assessment_result
            )

        # ─── Step 2: Determine recommendation ────────────────────────────
        recommendation: str = _determine_recommendation(
            match_score, assessment_score, assessment_pass, assessment_flags
        )

        # ─── Step 3: Save report using tool ───────────────────────────────
        tool_start: float = time.time()
        report_result = _generate_individual_report(
            output_dir="reports",
            candidate_name=candidate_name,
            job_title=job_title,
            report_content=report_content,
            match_score=match_score,
            assessment_score=assessment_score,
            assessment_pass_status=assessment_pass,
            recommendation=recommendation,
        )
        tool_duration: float = time.time() - tool_start

        if tracer:
            tracer.log_tool_call(
                agent_name, "report_file_writer",
                {
                    "report_type": "individual",
                    "candidate_name": candidate_name,
                    "job_title": job_title,
                },
                report_result, tool_duration,
            )

        if report_result.success:
            guide_entry: dict = {
                "candidate_name": candidate_name,
                "job_title": job_title,
                "file_path": report_result.file_path,
                "match_score": match_score,
                "assessment_score": assessment_score,
                "assessment_pass_status": assessment_pass,
                "recommendation": recommendation,
                "generated_at": report_result.timestamp,
            }
            interview_guides.append(guide_entry)

            log_entries.append(
                f"[{agent_name}] ✅ Interview guide saved: {report_result.file_path}"
            )

            # Add to comparison data
            comparison_data.append({
                "candidate_name": candidate_name,
                "match_score": match_score,
                "assessment_score": assessment_score,
                "assessment_pass_status": assessment_pass,
                "recommendation": recommendation,
                "strengths": ", ".join(best_match.get("skill_match", {}).get("matched_skills", [])[:3]),
                "concerns": ", ".join(best_match.get("skill_match", {}).get("missing_skills", [])[:3]),
            })
        else:
            log_entries.append(
                f"[{agent_name}] ❌ Report generation failed: {report_result.error_message}"
            )

    # ─── Step 4: Generate comparison report if multiple candidates ────────
    comparison_report_path: str = None
    if len(comparison_data) > 1:
        log_entries.append(
            f"[{agent_name}] Generating comparison report for {len(comparison_data)} candidates"
        )

        job_title_for_comparison: str = comparison_data[0].get("job_title", "Unknown") if comparison_data else "Unknown"
        # Use job_title from the first candidate's best_match
        if shortlisted:
            job_title_for_comparison = shortlisted[0].get("best_match", {}).get("job_title", "Unknown")

        comp_result = _generate_comparison_report(
            output_dir="reports",
            job_title=job_title_for_comparison,
            comparison_data=json.dumps(comparison_data),
        )

        if comp_result.success:
            comparison_report_path = comp_result.file_path
            log_entries.append(
                f"[{agent_name}] ✅ Comparison report saved: {comp_result.file_path}"
            )

    # ─── Finalize ─────────────────────────────────────────────────────────────
    duration: float = time.time() - start_time
    summary: str = (
        f"Generated {len(interview_guides)} interview guides"
        + (f" + 1 comparison report" if comparison_report_path else "")
    )
    log_entries.append(f"[{agent_name}] {summary}")

    if tracer:
        tracer.log_agent_end(agent_name, "SUCCESS", summary, duration)

    return {
        "interview_guides": interview_guides,
        "comparison_report": comparison_report_path,
        "current_agent": "interview_strategist",
        "pipeline_status": "COMPLETED",
        "processing_log": log_entries,
    }


def _determine_recommendation(
    match_score: int,
    assessment_score: float,
    assessment_pass: str,
    flags: list[str],
) -> str:
    """Determine the final hiring recommendation based on all scores.

    Args:
        match_score: Match score from Agent 2 (0-100).
        assessment_score: Assessment percentage from Agent 3.
        assessment_pass: Assessment pass status.
        flags: Red flags from assessment.

    Returns:
        Recommendation string.
    """
    if assessment_pass == "FAIL":
        return "DO_NOT_PROCEED"

    if match_score >= 80 and assessment_score >= 70 and not flags:
        return "PROCEED"

    if match_score >= 60 and assessment_score >= 50:
        return "PROCEED_WITH_CAUTION"

    if flags:
        return "PROCEED_WITH_CAUTION"

    return "DO_NOT_PROCEED"


def _generate_fallback_content(
    candidate: dict,
    best_match: dict,
    assessment_result: dict,
) -> str:
    """Generate a basic interview guide when LLM fails.

    Args:
        candidate: Candidate profile.
        best_match: Best match report.
        assessment_result: Assessment results.

    Returns:
        Markdown content string.
    """
    candidate_name: str = candidate.get("candidate_name", "Unknown")
    matched_skills: list[str] = best_match.get("skill_match", {}).get("matched_skills", [])
    missing_skills: list[str] = best_match.get("skill_match", {}).get("missing_skills", [])

    return f"""## Strengths Assessment
- Matched skills: {', '.join(matched_skills) if matched_skills else 'None identified'}
- Experience: {candidate.get('years_of_experience', 'N/A')} years

## Risk Areas & Concerns
- Missing skills: {', '.join(missing_skills) if missing_skills else 'None'}
- Assessment score: {assessment_result.get('percentage', 'N/A')}%

## Recommended Interview Questions

### Technical Deep-Dive
1. Please describe your experience with the skills listed on your resume.
   - **What to look for:** Depth of knowledge, practical examples

### Behavioral Questions
1. Tell me about a challenging project and how you handled it.
   - **What to look for:** Problem-solving approach, teamwork

## Suggested Interview Format
- Duration: 45 minutes
- Panel: 1 Technical Lead + 1 HR Representative

## Final Recommendation
*Auto-generated fallback — LLM was unavailable for detailed analysis.*
"""
