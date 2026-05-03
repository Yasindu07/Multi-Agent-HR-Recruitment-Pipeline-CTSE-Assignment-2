"""
Agent 1: Document Intelligence Extractor — Student A
=====================================================
Parses incoming documents (CVs and Job Flyers) and extracts structured data.
This is the system's "eyes" — it reads uploaded documents and produces
standardized JSON profiles for downstream agents.

Responsibilities:
    - Parse PDF/DOCX resumes → CandidateProfile JSON
    - Parse PDF job flyers → JobVacancy JSON
    - Normalize skills to lowercase tags
    - Handle edge cases (corrupt files, empty text, missing fields)

Uses:
    - Tool: document_parser (PDF/DOCX extraction)
    - LLM: Ollama (structured data extraction from raw text)
"""

import json
import os
import time
from datetime import datetime
from typing import Any

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage

from state.pipeline_state import PipelineState
from tools.document_parser import document_parser, _parse_document
from tools.llm_utils import invoke_llm_with_retry
from observability.tracer import AgentTracer

# ═══════════════════════════════════════════════════════════════════════════════
# SYSTEM PROMPT — Document Intelligence Extractor
# ═══════════════════════════════════════════════════════════════════════════════

DOCUMENT_EXTRACTOR_PROMPT: str = """You are ResumeExtractorAI, a meticulous Senior HR Data Analyst with 10 years 
of experience in structured resume and job document parsing. Your ONLY job is to extract 
structured information from raw document text. You must NEVER fabricate information.
If a field is not found in the document, you MUST return "NOT_FOUND" for that field.

You will be told whether the document is a RESUME or a JOB_FLYER.

═══ FOR RESUMES — Return this exact JSON structure ═══
{
    "document_type": "RESUME",
    "candidate_name": "string",
    "email": "string or NOT_FOUND",
    "phone": "string or NOT_FOUND",
    "years_of_experience": integer or 0,
    "education": [
        {"degree": "string", "institution": "string", "year": "integer or NOT_FOUND"}
    ],
    "skills": ["string"],
    "work_experience": [
        {"company": "string", "role": "string", "duration": "string", "highlights": ["string"]}
    ],
    "github_url": "string or NOT_FOUND",
    "portfolio_url": "string or NOT_FOUND",
    "certifications": ["string"]
}

═══ FOR JOB FLYERS — Return this exact JSON structure ═══
{
    "document_type": "JOB_FLYER",
    "title": "string",
    "department": "string or NOT_FOUND",
    "required_skills": ["string"],
    "preferred_skills": ["string"],
    "min_experience_years": integer or 0,
    "required_education": "string or NOT_FOUND",
    "description": "string",
    "salary_range": "string or NOT_FOUND",
    "application_deadline": "string or NOT_FOUND"
}

═══ CONSTRAINTS ═══
1. Output ONLY valid JSON. No explanations, no markdown code fences, no commentary.
2. Skills must be normalized to lowercase (e.g., "React.js" → "reactjs", "Python" → "python", "Node.js" → "nodejs").
3. If the document is clearly not a valid resume or job flyer (e.g., a random document), return:
   {"error": "INVALID_DOCUMENT", "reason": "brief explanation"}
4. You must extract ALL skills mentioned, including those embedded in job descriptions or work experience.
5. Years of experience should be calculated from work history if not explicitly stated.
6. Do NOT add any skills, qualifications, or information that is not explicitly mentioned in the document."""


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT NODE FUNCTION
# ═══════════════════════════════════════════════════════════════════════════════

def document_extractor_node(
    state: PipelineState,
    llm: ChatOllama = None,
    tracer: AgentTracer = None,
) -> dict[str, Any]:
    """LangGraph node function for the Document Intelligence Extractor agent.

    Processes all uploaded documents (resumes and job flyers), extracts structured
    data using the document_parser tool and the LLM, and updates the pipeline state.

    Args:
        state: Current pipeline state containing resume_paths and job_flyer_paths.
        llm: The ChatOllama LLM instance. If None, creates a default one.
        tracer: The AgentTracer for observability logging.

    Returns:
        dict: Updated state fields (candidate_profiles, job_vacancies, parse_errors, etc.)
    """
    agent_name: str = "DocumentExtractor"
    start_time: float = time.time()

    if tracer:
        tracer.log_agent_start(agent_name, {
            "resume_paths": state.get("resume_paths", []),
            "job_flyer_paths": state.get("job_flyer_paths", []),
        })

    # Initialize LLM if not provided
    if llm is None:
        llm = ChatOllama(model="llama3.2", temperature=0, format="json")

    candidate_profiles: list[dict] = []
    job_vacancies: list[dict] = []
    parse_errors: list[dict] = []
    log_entries: list[str] = list(state.get("processing_log", []))
    seen_files: set[str] = set()  # Deduplication tracker

    # ─── Process Resumes ──────────────────────────────────────────────────────
    resume_paths: list[str] = state.get("resume_paths", [])
    for resume_path in resume_paths:
        # Deduplication — skip files already processed
        base_name: str = os.path.basename(resume_path)
        if base_name in seen_files:
            log_entries.append(f"[{agent_name}] ⏭ Skipping duplicate: {base_name}")
            continue
        seen_files.add(base_name)
        log_entries.append(f"[{agent_name}] Processing resume: {resume_path}")

        # Step 1: Use tool to parse the document
        tool_start: float = time.time()
        parse_result = _parse_document(resume_path)
        tool_duration: float = time.time() - tool_start

        if tracer:
            tracer.log_tool_call(
                agent_name, "document_parser",
                {"file_path": resume_path, "doc_type": "RESUME"},
                parse_result, tool_duration,
            )

        if not parse_result.success:
            parse_errors.append({
                "file_path": resume_path,
                "document_type": "RESUME",
                "error": parse_result.error_message,
                "timestamp": datetime.now().isoformat(),
            })
            log_entries.append(f"[{agent_name}] ❌ Failed to parse resume: {parse_result.error_message}")
            continue

        # Step 2: Send raw text to LLM for structured extraction (with retry)
        try:
            messages = [
                SystemMessage(content=DOCUMENT_EXTRACTOR_PROMPT),
                HumanMessage(content=f"Document type: RESUME\n\nRaw text:\n{parse_result.raw_text}"),
            ]
            extracted: dict = invoke_llm_with_retry(
                llm, messages, max_retries=2,
                agent_name=agent_name, tracer=tracer,
            )

            if "error" in extracted:
                parse_errors.append({
                    "file_path": resume_path,
                    "document_type": "RESUME",
                    "error": extracted.get("reason", "Invalid document"),
                    "timestamp": datetime.now().isoformat(),
                })
                log_entries.append(f"[{agent_name}] ⚠️ Invalid resume: {extracted.get('reason')}")
            else:
                extracted["source_file"] = resume_path
                candidate_profiles.append(extracted)
                log_entries.append(
                    f"[{agent_name}] ✅ Extracted profile: {extracted.get('candidate_name', 'Unknown')} "
                    f"— {len(extracted.get('skills', []))} skills found"
                )

        except ValueError as e:
            parse_errors.append({
                "file_path": resume_path,
                "document_type": "RESUME",
                "error": f"LLM JSON extraction failed after retries: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            })
            log_entries.append(f"[{agent_name}] ❌ LLM JSON failed after retries for resume")
        except Exception as e:
            parse_errors.append({
                "file_path": resume_path,
                "document_type": "RESUME",
                "error": f"LLM error: {type(e).__name__}: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            })
            log_entries.append(f"[{agent_name}] ❌ LLM error: {str(e)}")

    # ─── Process Job Flyers ───────────────────────────────────────────────────
    flyer_paths: list[str] = state.get("job_flyer_paths", [])
    for flyer_path in flyer_paths:
        # Deduplication
        base_name = os.path.basename(flyer_path)
        if base_name in seen_files:
            log_entries.append(f"[{agent_name}] ⏭ Skipping duplicate flyer: {base_name}")
            continue
        seen_files.add(base_name)
        log_entries.append(f"[{agent_name}] Processing job flyer: {flyer_path}")

        # Step 1: Parse the flyer document
        tool_start = time.time()
        parse_result = _parse_document(flyer_path)
        tool_duration = time.time() - tool_start

        if tracer:
            tracer.log_tool_call(
                agent_name, "document_parser",
                {"file_path": flyer_path, "doc_type": "JOB_FLYER"},
                parse_result, tool_duration,
            )

        if not parse_result.success:
            parse_errors.append({
                "file_path": flyer_path,
                "document_type": "JOB_FLYER",
                "error": parse_result.error_message,
                "timestamp": datetime.now().isoformat(),
            })
            log_entries.append(f"[{agent_name}] ❌ Failed to parse flyer: {parse_result.error_message}")
            continue

        # Step 2: LLM extraction (with retry)
        try:
            messages = [
                SystemMessage(content=DOCUMENT_EXTRACTOR_PROMPT),
                HumanMessage(content=f"Document type: JOB_FLYER\n\nRaw text:\n{parse_result.raw_text}"),
            ]
            extracted = invoke_llm_with_retry(
                llm, messages, max_retries=2,
                agent_name=agent_name, tracer=tracer,
            )

            if "error" in extracted:
                parse_errors.append({
                    "file_path": flyer_path,
                    "document_type": "JOB_FLYER",
                    "error": extracted.get("reason", "Invalid document"),
                    "timestamp": datetime.now().isoformat(),
                })
            else:
                # Generate a job_id if not present
                if "job_id" not in extracted:
                    job_count: int = len(job_vacancies) + 1
                    extracted["job_id"] = f"JOB-AUTO-{job_count:03d}"
                extracted["status"] = "OPEN"
                extracted["source_file"] = flyer_path
                job_vacancies.append(extracted)
                log_entries.append(
                    f"[{agent_name}] ✅ Extracted vacancy: {extracted.get('title', 'Unknown')} "
                    f"— {len(extracted.get('required_skills', []))} required skills"
                )

        except ValueError:
            parse_errors.append({
                "file_path": flyer_path,
                "document_type": "JOB_FLYER",
                "error": "LLM JSON extraction failed after retries for flyer",
                "timestamp": datetime.now().isoformat(),
            })
        except Exception as e:
            parse_errors.append({
                "file_path": flyer_path,
                "document_type": "JOB_FLYER",
                "error": f"LLM error: {type(e).__name__}: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            })

    # ─── Finalize ─────────────────────────────────────────────────────────────
    duration: float = time.time() - start_time
    summary: str = (
        f"Extracted {len(candidate_profiles)} candidate profiles and "
        f"{len(job_vacancies)} job vacancies. {len(parse_errors)} errors."
    )
    log_entries.append(f"[{agent_name}] {summary}")

    if tracer:
        tracer.log_agent_end(agent_name, "SUCCESS", summary, duration)

    return {
        "candidate_profiles": candidate_profiles,
        "job_vacancies": job_vacancies,
        "parse_errors": parse_errors,
        "current_agent": "document_extractor",
        "processing_log": log_entries,
    }
