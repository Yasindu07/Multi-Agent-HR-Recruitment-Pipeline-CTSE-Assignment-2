"""
Agent 3: Assessment Coordinator — Student C
============================================
Creates personalized technical assessments/quizzes for shortlisted candidates.
Assessments are calibrated by experience level and focused on job-relevant skills.

Responsibilities:
    - Generate personalized assessments based on candidate skills + job requirements
    - Calibrate difficulty by experience level (Junior/Mid/Senior/Lead)
    - Create MCQ, scenario-based, and problem-solving questions
    - Auto-grade assessment responses
    - Detect skill-claim mismatches (red flags)

Uses:
    - Tool: assessment_generator (JSON assessment file creation + scoring)
    - LLM: Ollama (question generation + open-ended answer evaluation)
"""

import json
import time
from datetime import datetime
from typing import Any

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from state.pipeline_state import PipelineState
from tools.assessment_generator import (
    assessment_generator,
    _generate_assessment,
    _score_assessment,
    _calibrate_difficulty,
)
from observability.tracer import AgentTracer

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Assessment Coordinator
# ═══════════════════════════════════════════════════════════════════════════════

ASSESSMENT_COORDINATOR_PROMPT: str = """You are AssessmentCoordinatorAI, a Senior Technical Assessment Designer with 
expertise in competency-based evaluation. Your job is to create PERSONALIZED technical 
assessments for candidates based on their resume data and the job requirements.

You will receive:
1. Candidate profile (skills, experience, work highlights)
2. Job requirements (required skills, preferred skills, experience level)
3. Match report (matched skills, missing skills, match score)
4. Difficulty level (JUNIOR, MID, SENIOR, or LEAD)

Generate a comprehensive assessment with EXACTLY 10 questions.

Output ONLY valid JSON in this format:
{
    "questions": [
        {
            "question_id": "Q001",
            "section": "TECHNICAL or SCENARIO or PROBLEM_SOLVING",
            "question_text": "The actual question text",
            "question_type": "MCQ or SHORT_ANSWER or SCENARIO",
            "difficulty": "EASY or MEDIUM or HARD",
            "skill_tested": "specific skill being tested (lowercase)",
            "options": ["A) option1", "B) option2", "C) option3", "D) option4"],
            "correct_answer": "A",
            "points": 10
        }
    ]
}

═══ QUESTION DISTRIBUTION ═══
Section 1 — TECHNICAL (6 questions):
  - 3 MCQ questions testing MATCHED skills (to verify the candidate's depth)
  - 3 MCQ questions testing MISSING skills (to assess foundational knowledge)

Section 2 — SCENARIO (2 questions):  
  - SHORT_ANSWER format based on the candidate's WORK EXPERIENCE
  - Must reference specific technologies or situations from their resume
  - Points: 15 each

Section 3 — PROBLEM_SOLVING (2 questions):
  - SHORT_ANSWER or SCENARIO format
  - Practical challenges relevant to the job role
  - Points: 20 each

═══ DIFFICULTY CALIBRATION ═══
- JUNIOR: Focus on fundamentals, definitions, basic usage (mostly EASY/MEDIUM MCQs)
- MID: Mix of implementation and conceptual questions (MEDIUM MCQs, MEDIUM scenarios)
- SENIOR: System design, architecture, trade-offs (MEDIUM/HARD across all types)
- LEAD: Strategic decisions, team scaling, complex system problems (mostly HARD)

═══ CONSTRAINTS ═══
1. Each MCQ MUST have exactly 4 options (A, B, C, D) with ONE correct answer.
2. Questions MUST be specific to the candidate's claimed skills — NOT generic.
3. Scenario questions should reference the candidate's work experience highlights.
4. All questions must be relevant to the specific JOB ROLE, not just random tech questions.
5. correct_answer for MCQs must be one of "A", "B", "C", "D".
6. Output ONLY valid JSON. No markdown, no explanations, no code fences.
7. skill_tested must be lowercase (e.g., "python", "reactjs", "docker")."""


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT NODE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def assessment_coordinator_node(
    state: PipelineState,
    llm: ChatOllama = None,
    tracer: AgentTracer = None,
) -> dict[str, Any]:
    """LangGraph node function for the Assessment Coordinator agent.

    Generates personalized assessments for all shortlisted candidates
    and optionally scores their responses.

    Args:
        state: Current pipeline state with shortlisted_candidates and match_reports.
        llm: The ChatOllama LLM instance.
        tracer: The AgentTracer for observability.

    Returns:
        dict: Updated state fields (assessments, assessment_results).
    """
    agent_name: str = "AssessmentCoordinator"
    start_time: float = time.time()

    if tracer:
        tracer.log_agent_start(agent_name, {
            "shortlisted_count": len(state.get("shortlisted_candidates", [])),
        })

    if llm is None:
        llm = ChatOllama(model="llama3.2", temperature=0.3, format="json")

    shortlisted: list[dict] = state.get("shortlisted_candidates", [])
    assessments: list[dict] = []
    assessment_results: list[dict] = []
    log_entries: list[str] = list(state.get("processing_log", []))

    if not shortlisted:
        log_entries.append(f"[{agent_name}] ⚠️ No shortlisted candidates to assess")
        if tracer:
            tracer.log_agent_end(
                agent_name, "SKIPPED", "No shortlisted candidates", time.time() - start_time
            )
        return {
            "assessments": [],
            "assessment_results": [],
            "current_agent": "assessment_coordinator",
            "processing_log": log_entries,
        }

    for entry in shortlisted:
        candidate: dict = entry.get("candidate_profile", {})
        best_match: dict = entry.get("best_match", {})
        candidate_name: str = candidate.get("candidate_name", "Unknown")
        job_title: str = best_match.get("job_title", "Unknown")
        job_id: str = best_match.get("job_id", "UNKNOWN")

        log_entries.append(
            f"[{agent_name}] Generating assessment for {candidate_name} → {job_title}"
        )

        # Gather data for the LLM
        matched_skills: list[str] = best_match.get("skill_match", {}).get("matched_skills", [])
        missing_skills: list[str] = best_match.get("skill_match", {}).get("missing_skills", [])
        experience_years: int = candidate.get("years_of_experience", 0)
        difficulty_level: str = _calibrate_difficulty(experience_years)

        # Extract work highlights
        work_experience: list[dict] = candidate.get("work_experience", [])
        highlights: list[str] = []
        for exp in work_experience[:3]:
            role: str = exp.get("role", "")
            company: str = exp.get("company", "")
            exp_highlights: list[str] = exp.get("highlights", [])
            if exp_highlights:
                highlights.extend(exp_highlights[:2])
            elif role and company:
                highlights.append(f"Worked as {role} at {company}")

        # ─── Step 1: Generate questions using LLM ─────────────────────────
        llm_start: float = time.time()
        try:
            prompt: str = f"""CANDIDATE PROFILE:
- Name: {candidate_name}
- Skills: {json.dumps(candidate.get('skills', []))}
- Experience: {experience_years} years
- Work Experience Highlights: {json.dumps(highlights)}
- Education: {json.dumps(candidate.get('education', []))}

JOB REQUIREMENTS:
- Title: {job_title}
- Required Skills: {json.dumps(best_match.get('skill_match', {}).get('matched_skills', []) + best_match.get('skill_match', {}).get('missing_skills', []))}

MATCH ANALYSIS:
- Matched Skills: {json.dumps(matched_skills)}
- Missing Skills: {json.dumps(missing_skills)}
- Match Score: {best_match.get('overall_match_score', 0)}/100

DIFFICULTY LEVEL: {difficulty_level}

Generate a personalized assessment with 10 questions following the distribution rules."""

            messages = [
                SystemMessage(content=ASSESSMENT_COORDINATOR_PROMPT),
                HumanMessage(content=prompt),
            ]
            response = llm.invoke(messages)
            llm_duration: float = time.time() - llm_start

            if tracer:
                tracer.log_llm_call(
                    agent_name, llm.model,
                    prompt_preview=f"Assessment generation for {candidate_name}",
                    response_preview=response.content[:500],
                    duration_seconds=llm_duration,
                )

            assessment_content: str = response.content

        except Exception as e:
            log_entries.append(
                f"[{agent_name}] ❌ LLM error generating assessment: {str(e)}"
            )
            assessment_content = None

        # ─── Step 2: Save assessment using tool ───────────────────────────
        tool_start: float = time.time()
        gen_result = _generate_assessment(
            output_dir="assessments",
            candidate_name=candidate_name,
            job_title=job_title,
            job_id=job_id,
            matched_skills=",".join(matched_skills),
            missing_skills=",".join(missing_skills),
            experience_years=experience_years,
            work_highlights=",".join(highlights),
            assessment_content=assessment_content,
        )
        tool_duration: float = time.time() - tool_start

        if tracer:
            tracer.log_tool_call(
                agent_name, "assessment_generator",
                {
                    "action": "generate",
                    "candidate_name": candidate_name,
                    "job_title": job_title,
                    "difficulty": difficulty_level,
                },
                gen_result, tool_duration,
            )

        if gen_result.success:
            assessment_entry: dict = {
                "candidate_name": candidate_name,
                "job_id": job_id,
                "job_title": job_title,
                "assessment_file_path": gen_result.assessment_file_path,
                "total_questions": gen_result.total_questions,
                "difficulty_level": difficulty_level,
                "sections": gen_result.sections,
                "difficulty_distribution": gen_result.difficulty_distribution,
                "generated_at": datetime.now().isoformat(),
            }
            assessments.append(assessment_entry)

            log_entries.append(
                f"[{agent_name}] ✅ Assessment generated: {gen_result.total_questions} questions "
                f"({difficulty_level} level) → {gen_result.assessment_file_path}"
            )

            # ─── Step 3: Auto-score with simulated answers ───────────────
            # In real deployment, candidates would submit answers via a UI.
            # For demo purposes, we simulate scoring with sample answers.
            score_start: float = time.time()
            simulated_answers: dict = _generate_simulated_answers(
                gen_result.assessment_file_path
            )

            if simulated_answers:
                score_result = _score_assessment(
                    assessment_file_path=gen_result.assessment_file_path,
                    candidate_answers=json.dumps(simulated_answers),
                    candidate_name=candidate_name,
                )
                score_duration: float = time.time() - score_start

                if tracer:
                    tracer.log_tool_call(
                        agent_name, "assessment_generator",
                        {"action": "score", "candidate_name": candidate_name},
                        score_result, score_duration,
                    )

                if score_result.success:
                    questions_list = []
                    try:
                        with open(gen_result.assessment_file_path, "r", encoding="utf-8") as f:
                            saved_assessment = json.load(f)
                            questions_list = saved_assessment.get("questions", [])
                        log_entries.append(f"[{agent_name}] Loaded {len(questions_list)} questions from {gen_result.assessment_file_path}")
                    except Exception as e:
                        log_entries.append(f"[{agent_name}] ❌ Error loading questions from file: {str(e)}")


                    result_entry: dict = {
                        "candidate_name": candidate_name,
                        "job_id": job_id,
                        "job_title": job_title,
                        "total_score": score_result.total_score,
                        "max_score": score_result.max_score,
                        "percentage": score_result.percentage,
                        "section_scores": score_result.section_scores,
                        "pass_status": score_result.pass_status,
                        "flags": score_result.flags,
                        "scored_at": datetime.now().isoformat(),
                        "questions": questions_list,
                        "answers": simulated_answers,
                    }
                    assessment_results.append(result_entry)

                    log_entries.append(
                        f"[{agent_name}] 📊 Assessment scored: {score_result.percentage:.1f}% "
                        f"— {score_result.pass_status}"
                    )
                    if score_result.flags:
                        for flag in score_result.flags:
                            log_entries.append(f"[{agent_name}] 🚩 {flag}")
        else:
            log_entries.append(
                f"[{agent_name}] ❌ Assessment generation failed: {gen_result.error_message}"
            )

    # ─── Finalize ─────────────────────────────────────────────────────────────
    duration: float = time.time() - start_time
    summary: str = (
        f"Generated {len(assessments)} assessments, "
        f"scored {len(assessment_results)} candidates"
    )
    log_entries.append(f"[{agent_name}] {summary}")

    if tracer:
        tracer.log_agent_end(agent_name, "SUCCESS", summary, duration)

    return {
        "assessments": assessments,
        "assessment_results": assessment_results,
        "current_agent": "assessment_coordinator",
        "processing_log": log_entries,
    }


def _generate_simulated_answers(assessment_file_path: str) -> dict:
    """Generate simulated candidate answers for demo purposes.

    In a real system, candidates would submit answers via a web UI.
    This function reads the assessment and generates plausible answers.

    Args:
        assessment_file_path: Path to the assessment JSON file.

    Returns:
        dict: Mapping of question_id to answer.
    """
    try:
        with open(assessment_file_path, "r", encoding="utf-8") as f:
            assessment: dict = json.load(f)

        answers: dict[str, str] = {}
        questions: list[dict] = assessment.get("questions", [])

        for q in questions:
            q_id: str = q.get("question_id", "")
            q_type: str = q.get("question_type", "")

            if q_type == "MCQ":
                # Simulate: 70% chance of correct answer
                import random
                if random.random() < 0.7:
                    answers[q_id] = q.get("correct_answer", "A")
                else:
                    options = ["A", "B", "C", "D"]
                    correct = q.get("correct_answer", "A")
                    wrong_options = [o for o in options if o != correct]
                    answers[q_id] = random.choice(wrong_options)
            elif q_type in ("SHORT_ANSWER", "SCENARIO"):
                answers[q_id] = "Sample answer demonstrating knowledge of the topic."

        return answers

    except Exception:
        return {}
