"""
FastAPI Backend for HR Recruitment Pipeline
============================================
Full CRUD for candidates, jobs, pipeline runs + SSE streaming.
"""

import os
import sys
import json
import glob
import time
import asyncio
import sqlite3
from datetime import datetime
from typing import Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from observability.tracer import AgentTracer
from agents.document_extractor import document_extractor_node
from agents.candidate_matcher import candidate_matcher_node
from agents.assessment_coordinator import assessment_coordinator_node
from agents.interview_strategist import interview_strategist_node
from pipeline.routing import (
    route_after_extraction,
    route_after_matching,
    route_after_assessment,
)

# ═══════════════════════════════════════════════════════════════════════════════
# APP SETUP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="HR Recruitment Pipeline API", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.join("data", "_uploads")
DB_PATH = os.path.abspath("data/hr_jobs.db")


# ═══════════════════════════════════════════════════════════════════════════════
# DATABASE HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def get_db():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_db():
    """Ensure database exists."""
    if not os.path.exists(DB_PATH):
        from setup_db import setup_database
        setup_database()


def row_to_dict(row):
    """Convert sqlite3.Row to dict with JSON field parsing."""
    d = dict(row)
    for field in ["required_skills", "preferred_skills", "skills", "education",
                   "work_experience", "certifications", "candidate_ids"]:
        if field in d and isinstance(d[field], str):
            try:
                d[field] = json.loads(d[field])
            except (json.JSONDecodeError, TypeError):
                pass
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# PYDANTIC MODELS
# ═══════════════════════════════════════════════════════════════════════════════

class JobCreate(BaseModel):
    job_id: str
    title: str
    department: str = ""
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    min_experience_years: int = 0
    required_education: str = ""
    description: str = ""
    salary_range: str = ""
    status: str = "OPEN"


class JobUpdate(BaseModel):
    title: Optional[str] = None
    department: Optional[str] = None
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    min_experience_years: Optional[int] = None
    required_education: Optional[str] = None
    description: Optional[str] = None
    salary_range: Optional[str] = None
    status: Optional[str] = None


class CandidateCreate(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    years_of_experience: int = 0
    skills: list[str] = []
    education: list[dict] = []
    work_experience: list[dict] = []
    github_url: str = ""
    certifications: list[str] = []
    source_file: str = ""


class CandidateUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    years_of_experience: Optional[int] = None
    skills: Optional[list[str]] = None
    education: Optional[list[dict]] = None
    work_experience: Optional[list[dict]] = None
    github_url: Optional[str] = None
    certifications: Optional[list[str]] = None


# ═══════════════════════════════════════════════════════════════════════════════
# HEALTH
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/health")
async def health():
    ensure_db()
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD STATS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/dashboard")
async def dashboard():
    ensure_db()
    db = get_db()
    stats = {
        "total_jobs": db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
        "open_jobs": db.execute("SELECT COUNT(*) FROM jobs WHERE status='OPEN'").fetchone()[0],
        "total_candidates": db.execute("SELECT COUNT(*) FROM candidates").fetchone()[0],
        "total_runs": db.execute("SELECT COUNT(*) FROM pipeline_runs").fetchone()[0],
        "completed_runs": db.execute("SELECT COUNT(*) FROM pipeline_runs WHERE status='COMPLETED'").fetchone()[0],
        "total_matches": db.execute("SELECT COUNT(*) FROM match_results").fetchone()[0],
        "shortlisted": db.execute("SELECT COUNT(*) FROM match_results WHERE recommendation IN ('STRONG_MATCH','MODERATE_MATCH')").fetchone()[0],
    }
    # Recent activity
    recent_runs = db.execute("SELECT * FROM pipeline_runs ORDER BY created_at DESC LIMIT 5").fetchall()
    stats["recent_runs"] = [row_to_dict(r) for r in recent_runs]
    db.close()
    return stats


# ═══════════════════════════════════════════════════════════════════════════════
# JOBS CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/jobs")
async def list_jobs():
    ensure_db()
    db = get_db()
    rows = db.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
    db.close()
    return {"jobs": [row_to_dict(r) for r in rows]}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    db = get_db()
    row = db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "Job not found")
    return row_to_dict(row)


@app.post("/api/jobs")
async def create_job(job: JobCreate):
    db = get_db()
    now = datetime.now().isoformat()
    db.execute(
        """INSERT OR REPLACE INTO jobs 
           (job_id, title, department, required_skills, preferred_skills,
            min_experience_years, required_education, description, salary_range, status, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (job.job_id, job.title, job.department, json.dumps(job.required_skills),
         json.dumps(job.preferred_skills), job.min_experience_years, job.required_education,
         job.description, job.salary_range, job.status, now, now),
    )
    db.commit()
    db.close()
    return {"status": "created", "job_id": job.job_id}


@app.put("/api/jobs/{job_id}")
async def update_job(job_id: str, update: JobUpdate):
    db = get_db()
    row = db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(404, "Job not found")

    fields = []
    values = []
    for k, v in update.model_dump(exclude_none=True).items():
        if k in ("required_skills", "preferred_skills"):
            v = json.dumps(v)
        fields.append(f"{k} = ?")
        values.append(v)
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(job_id)

    db.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?", values)
    db.commit()
    db.close()
    return {"status": "updated", "job_id": job_id}


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    db = get_db()
    db.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
    db.commit()
    db.close()
    return {"status": "deleted", "job_id": job_id}


@app.post("/api/jobs/extract")
async def extract_job_flyer(file: UploadFile = File(...)):
    """Upload a job flyer PDF → extract with LLM → return preview (not saved)."""
    os.makedirs(os.path.join(UPLOAD_DIR, "flyers"), exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, "flyers", file.filename)
    with open(dest, "wb") as f:
        f.write(await file.read())

    # Use document extractor to parse the flyer
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="llama3.2", temperature=0, format="json")
    tracer = AgentTracer(log_dir="logs", run_id=f"extract_{datetime.now().strftime('%H%M%S')}")

    state = {
        "resume_paths": [],
        "job_flyer_paths": [os.path.abspath(dest)],
        "target_job_id": None,
        "db_path": DB_PATH,
        "candidate_profiles": [],
        "job_vacancies": [],
        "parse_errors": [],
        "match_reports": [], "shortlisted_candidates": [], "rejected_candidates": [],
        "assessments": [], "assessment_results": [], "interview_guides": [],
        "comparison_report": None, "current_agent": "", "pipeline_status": "RUNNING",
        "processing_log": [], "error_log": [], "messages": [],
    }

    result = await asyncio.to_thread(document_extractor_node, state, llm=llm, tracer=tracer)
    vacancies = result.get("job_vacancies", [])
    if vacancies:
        v = vacancies[0]
        v["source_file"] = dest
        return {"extracted": v, "source_file": dest}
    return {"extracted": None, "errors": result.get("parse_errors", []), "source_file": dest}


# ═══════════════════════════════════════════════════════════════════════════════
# CANDIDATES CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/candidates")
async def list_candidates():
    ensure_db()
    db = get_db()
    rows = db.execute("SELECT * FROM candidates ORDER BY created_at DESC").fetchall()
    db.close()
    return {"candidates": [row_to_dict(r) for r in rows]}


@app.get("/api/candidates/{cid}")
async def get_candidate(cid: int):
    db = get_db()
    row = db.execute("SELECT * FROM candidates WHERE id = ?", (cid,)).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, "Candidate not found")
    return row_to_dict(row)


@app.post("/api/candidates")
async def create_candidate(c: CandidateCreate):
    db = get_db()
    now = datetime.now().isoformat()
    cursor = db.execute(
        """INSERT INTO candidates 
           (name, email, phone, years_of_experience, skills, education,
            work_experience, github_url, certifications, source_file, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (c.name, c.email, c.phone, c.years_of_experience, json.dumps(c.skills),
         json.dumps(c.education), json.dumps(c.work_experience), c.github_url,
         json.dumps(c.certifications), c.source_file, now, now),
    )
    new_id = cursor.lastrowid
    db.commit()
    db.close()
    return {"status": "created", "id": new_id}


@app.put("/api/candidates/{cid}")
async def update_candidate(cid: int, update: CandidateUpdate):
    db = get_db()
    row = db.execute("SELECT * FROM candidates WHERE id = ?", (cid,)).fetchone()
    if not row:
        db.close()
        raise HTTPException(404, "Candidate not found")

    fields = []
    values = []
    for k, v in update.model_dump(exclude_none=True).items():
        if k in ("skills", "education", "work_experience", "certifications"):
            v = json.dumps(v)
        fields.append(f"{k} = ?")
        values.append(v)
    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(cid)

    db.execute(f"UPDATE candidates SET {', '.join(fields)} WHERE id = ?", values)
    db.commit()
    db.close()
    return {"status": "updated", "id": cid}


@app.delete("/api/candidates/{cid}")
async def delete_candidate(cid: int):
    db = get_db()
    db.execute("DELETE FROM candidates WHERE id = ?", (cid,))
    db.commit()
    db.close()
    return {"status": "deleted", "id": cid}


@app.post("/api/candidates/extract")
async def extract_cv(file: UploadFile = File(...)):
    """Upload a CV PDF → extract with LLM → return preview (not saved)."""
    os.makedirs(os.path.join(UPLOAD_DIR, "resumes"), exist_ok=True)
    dest = os.path.join(UPLOAD_DIR, "resumes", file.filename)
    with open(dest, "wb") as f:
        f.write(await file.read())

    from langchain_ollama import ChatOllama
    llm = ChatOllama(model="llama3.2", temperature=0, format="json")
    tracer = AgentTracer(log_dir="logs", run_id=f"extract_{datetime.now().strftime('%H%M%S')}")

    state = {
        "resume_paths": [os.path.abspath(dest)],
        "job_flyer_paths": [],
        "target_job_id": None,
        "db_path": DB_PATH,
        "candidate_profiles": [],
        "job_vacancies": [],
        "parse_errors": [],
        "match_reports": [], "shortlisted_candidates": [], "rejected_candidates": [],
        "assessments": [], "assessment_results": [], "interview_guides": [],
        "comparison_report": None, "current_agent": "", "pipeline_status": "RUNNING",
        "processing_log": [], "error_log": [], "messages": [],
    }

    result = await asyncio.to_thread(document_extractor_node, state, llm=llm, tracer=tracer)
    profiles = result.get("candidate_profiles", [])
    if profiles:
        p = profiles[0]
        p["source_file"] = dest
        return {"extracted": p, "source_file": dest}
    return {"extracted": None, "errors": result.get("parse_errors", []), "source_file": dest}


# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS HISTORY
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/results")
async def list_results():
    ensure_db()
    db = get_db()
    runs = db.execute("""
        SELECT pr.*, j.title as job_title 
        FROM pipeline_runs pr LEFT JOIN jobs j ON pr.job_id = j.job_id 
        ORDER BY pr.created_at DESC
    """).fetchall()
    db.close()
    return {"runs": [row_to_dict(r) for r in runs]}


@app.get("/api/results/{run_id}")
async def get_result(run_id: int):
    db = get_db()
    run = db.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,)).fetchone()
    if not run:
        db.close()
        raise HTTPException(404, "Run not found")
    matches = db.execute("""
        SELECT mr.*, c.name as candidate_name, j.title as job_title
        FROM match_results mr
        LEFT JOIN candidates c ON mr.candidate_id = c.id
        LEFT JOIN jobs j ON mr.job_id = j.job_id
        WHERE mr.run_id = ?
    """, (run_id,)).fetchall()
    db.close()
    return {
        "run": row_to_dict(run),
        "matches": [row_to_dict(m) for m in matches],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE RUN (SSE)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/run")
async def run_pipeline_sse(
    model: str = "llama3.2",
    job_id: str = "ALL",
    candidate_ids: str = "",
    use_sample: bool = False,
):
    """Run pipeline with SSE streaming. Accepts comma-separated candidate IDs."""

    async def event_generator():
        from langchain_ollama import ChatOllama

        run_id_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        tracer = AgentTracer(log_dir="logs", run_id=run_id_str)

        llm_json = ChatOllama(model=model, temperature=0, format="json")
        llm_markdown = ChatOllama(model=model, temperature=0.3)

        resume_paths = []
        flyer_paths = []
        selected_candidate_ids = [int(x) for x in candidate_ids.split(",") if x.strip()]

        # If candidate IDs provided, get their source files
        if selected_candidate_ids:
            db = get_db()
            for cid in selected_candidate_ids:
                row = db.execute("SELECT source_file FROM candidates WHERE id = ?", (cid,)).fetchone()
                if row and row["source_file"] and os.path.exists(row["source_file"]):
                    resume_paths.append(os.path.abspath(row["source_file"]))
            db.close()

        if use_sample:
            sample_resume_dir = "data/sample_resumes"
            sample_flyer_dir = "data/sample_flyers"
            if not os.path.exists(sample_resume_dir) or not os.listdir(sample_resume_dir):
                from create_sample_data import create_sample_resumes, create_sample_flyers
                create_sample_resumes()
                create_sample_flyers()
            ensure_db()
            resume_paths += sorted([os.path.abspath(p) for p in glob.glob(os.path.join(sample_resume_dir, "*.pdf"))])

        # Add any uploaded files
        up_resume = os.path.join(UPLOAD_DIR, "resumes")
        if os.path.exists(up_resume):
            resume_paths += sorted([os.path.abspath(p) for p in glob.glob(os.path.join(up_resume, "*.pdf"))])

        if not resume_paths:
            yield {"event": "error", "data": json.dumps({"message": "No resumes found. Add candidates or enable sample data."})}
            return

        # Create pipeline run record
        ensure_db()
        db = get_db()
        cursor = db.execute(
            "INSERT INTO pipeline_runs (job_id, candidate_ids, model, status, created_at) VALUES (?, ?, ?, 'RUNNING', ?)",
            (job_id if job_id != "ALL" else None, json.dumps(selected_candidate_ids), model, datetime.now().isoformat()),
        )
        db_run_id = cursor.lastrowid
        db.commit()
        db.close()

        yield {
            "event": "pipeline_start",
            "data": json.dumps({
                "run_id": db_run_id,
                "resume_count": len(resume_paths),
                "flyer_count": len(flyer_paths),
                "model": model,
                "timestamp": datetime.now().isoformat(),
            }),
        }

        state = {
            "resume_paths": resume_paths,
            "job_flyer_paths": flyer_paths,
            "target_job_id": job_id if job_id != "ALL" else None,
            "db_path": DB_PATH,
            "candidate_profiles": [], "job_vacancies": [], "parse_errors": [],
            "match_reports": [], "shortlisted_candidates": [], "rejected_candidates": [],
            "assessments": [], "assessment_results": [], "interview_guides": [],
            "comparison_report": None, "current_agent": "initializing",
            "pipeline_status": "RUNNING", "processing_log": [], "error_log": [], "messages": [],
        }

        agent_steps = [
            ("document_extractor", "Document Extractor", document_extractor_node, llm_json),
            ("candidate_matcher", "Candidate Matcher", candidate_matcher_node, llm_json),
            ("assessment_coordinator", "Assessment Coordinator", assessment_coordinator_node, llm_json),
            ("interview_strategist", "Interview Strategist", interview_strategist_node, llm_markdown),
        ]

        route_checks = {
            "document_extractor": (route_after_extraction, "candidate_matcher"),
            "candidate_matcher": (route_after_matching, "assessment_coordinator"),
            "assessment_coordinator": (route_after_assessment, "interview_strategist"),
        }

        for i, (agent_key, agent_label, agent_fn, agent_llm) in enumerate(agent_steps):
            if i > 0:
                prev_key = agent_steps[i - 1][0]
                route_fn, expected_next = route_checks.get(prev_key, (None, None))
                if route_fn:
                    decision = route_fn(state)
                    if decision != expected_next:
                        yield {"event": "agent_skipped", "data": json.dumps({"agent": agent_key, "label": agent_label})}
                        continue

            yield {"event": "agent_start", "data": json.dumps({"agent": agent_key, "label": agent_label, "timestamp": datetime.now().isoformat()})}
            await asyncio.sleep(0.1)

            try:
                start_time = time.time()
                result = await asyncio.to_thread(agent_fn, state, llm=agent_llm, tracer=tracer)
                duration = time.time() - start_time
                state.update(result)

                agent_data: dict[str, Any] = {
                    "agent": agent_key, "label": agent_label,
                    "duration_seconds": round(duration, 1),
                    "timestamp": datetime.now().isoformat(),
                }

                if agent_key == "document_extractor":
                    agent_data["profiles"] = state.get("candidate_profiles", [])
                    agent_data["vacancies"] = state.get("job_vacancies", [])
                    agent_data["errors"] = state.get("parse_errors", [])
                elif agent_key == "candidate_matcher":
                    agent_data["shortlisted"] = state.get("shortlisted_candidates", [])
                    agent_data["rejected"] = state.get("rejected_candidates", [])
                elif agent_key == "assessment_coordinator":
                    agent_data["assessments"] = state.get("assessments", [])
                    agent_data["results"] = state.get("assessment_results", [])
                elif agent_key == "interview_strategist":
                    guides_with_content = []
                    for g in state.get("interview_guides", []):
                        guide_entry = dict(g)
                        fpath = g.get("file_path", "")
                        if fpath and os.path.exists(fpath):
                            with open(fpath, "r") as f:
                                content = f.read()
                            if content.startswith("---"):
                                parts = content.split("---", 2)
                                if len(parts) >= 3:
                                    content = parts[2].strip()
                            guide_entry["content"] = content
                        guides_with_content.append(guide_entry)
                    agent_data["guides"] = guides_with_content

                yield {"event": "agent_complete", "data": json.dumps(agent_data, default=str)}

            except Exception as e:
                yield {"event": "agent_error", "data": json.dumps({"agent": agent_key, "label": agent_label, "error": f"{type(e).__name__}: {str(e)}"})}
                # Update run as failed
                db = get_db()
                db.execute("UPDATE pipeline_runs SET status='FAILED', completed_at=? WHERE id=?", (datetime.now().isoformat(), db_run_id))
                db.commit()
                db.close()
                break

        # Save results to database
        db = get_db()
        db.execute(
            "UPDATE pipeline_runs SET status='COMPLETED', results=?, completed_at=? WHERE id=?",
            (json.dumps({
                "profiles_count": len(state.get("candidate_profiles", [])),
                "shortlisted_count": len(state.get("shortlisted_candidates", [])),
                "rejected_count": len(state.get("rejected_candidates", [])),
                "assessments_count": len(state.get("assessment_results", [])),
                "guides_count": len(state.get("interview_guides", [])),
            }), datetime.now().isoformat(), db_run_id),
        )

        # Save match results
        for s in state.get("shortlisted_candidates", []):
            m = s.get("best_match", {})
            db.execute(
                """INSERT INTO match_results (run_id, job_id, match_score, recommendation, skill_match, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (db_run_id, m.get("job_id", job_id), m.get("overall_match_score", 0),
                 m.get("recommendation", ""), json.dumps(m.get("skill_match", {})),
                 datetime.now().isoformat()),
            )

        db.commit()
        db.close()

        yield {"event": "pipeline_done", "data": json.dumps({
            "status": "COMPLETED", "run_id": db_run_id,
            "timestamp": datetime.now().isoformat(),
        })}

    return EventSourceResponse(event_generator())
