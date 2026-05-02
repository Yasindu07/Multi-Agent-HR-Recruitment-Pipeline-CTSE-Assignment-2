"""
HR Recruitment Pipeline — Streamlit Demo UI
============================================
A stunning web interface to demonstrate the Multi-Agent System pipeline.
Run with: streamlit run app.py
"""

import json
import os
import sys
import time
import glob
import sqlite3
from datetime import datetime
from typing import Optional

import streamlit as st

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="HR Recruitment Pipeline — Multi-Agent System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS for Premium Look ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    /* ═══ FORCE DARK THEME EVERYWHERE ═══ */
    html, body, .main, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"],
    section[data-testid="stMain"],
    .block-container {
        background-color: #0f172a !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif;
    }

    /* Global text color */
    h1, h2, h3, h4, h5, h6, p, span, div, label, li, td, th, a {
        color: #e2e8f0 !important;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: #0f172a !important;
    }

    /* Main container */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%) !important;
    }
    [data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stFileUploader label {
        color: #94a3b8 !important;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* ═══ FORM / INPUT DARK FIXES ═══ */
    .stSelectbox > div > div,
    .stMultiSelect > div > div,
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: rgba(148,163,184,0.2) !important;
    }

    /* Dropdowns / Popover */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    [role="listbox"] {
        background-color: #1e293b !important;
    }
    [data-baseweb="menu"] li,
    [role="option"] {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
    }
    [data-baseweb="menu"] li:hover,
    [role="option"]:hover {
        background-color: #334155 !important;
    }

    /* Checkbox */
    .stCheckbox label span {
        color: #e2e8f0 !important;
    }

    /* File uploader */
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploader"] section > div {
        background-color: #1e293b !important;
        border-color: rgba(148,163,184,0.2) !important;
    }
    [data-testid="stFileUploader"] button {
        color: #e2e8f0 !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background-color: #1e293b !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #0d9488 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #0f766e !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(13,148,136,0.3) !important;
    }
    .stButton > button[kind="secondary"] {
        background-color: #334155 !important;
    }

    /* Expander */
    .streamlit-expanderHeader,
    [data-testid="stExpander"],
    [data-testid="stExpander"] > details,
    [data-testid="stExpander"] > details > summary {
        background-color: #1e293b !important;
        color: #e2e8f0 !important;
        border-color: rgba(148,163,184,0.15) !important;
    }
    [data-testid="stExpander"] > details > div[data-testid="stExpanderDetails"] {
        background-color: #1e293b !important;
        border-color: rgba(148,163,184,0.1) !important;
    }

    /* Metrics */
    [data-testid="stMetric"],
    [data-testid="stMetricValue"],
    [data-testid="stMetricLabel"] {
        background-color: transparent !important;
        color: #e2e8f0 !important;
    }
    [data-testid="stMetricValue"] {
        color: #0d9488 !important;
        font-weight: 800 !important;
    }

    /* Info / Warning / Error boxes */
    .stAlert,
    [data-testid="stAlert"] {
        background-color: #1e293b !important;
        border-color: rgba(148,163,184,0.2) !important;
    }

    /* Status widget */
    [data-testid="stStatusWidget"],
    [data-testid="stStatusWidget"] > div {
        background-color: #1e293b !important;
    }

    /* Progress bar track */
    .stProgress > div > div {
        background-color: #334155 !important;
    }
    .stProgress > div > div > div {
        background-color: #0d9488 !important;
    }

    /* Download button */
    .stDownloadButton > button {
        background-color: #334155 !important;
        color: #e2e8f0 !important;
        border: 1px solid rgba(148,163,184,0.2) !important;
    }
    .stDownloadButton > button:hover {
        background-color: #475569 !important;
    }

    /* Code blocks */
    code {
        background-color: #334155 !important;
        color: #0d9488 !important;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
    }
    pre {
        background-color: #1e293b !important;
    }

    /* Tables */
    .stTable, table, th, td {
        background-color: #1e293b !important;
        border-color: rgba(148,163,184,0.15) !important;
    }
    th {
        background-color: #334155 !important;
        color: #94a3b8 !important;
        font-weight: 700 !important;
    }

    /* Markdown text */
    .stMarkdown, .stMarkdown p, .stMarkdown li {
        color: #e2e8f0 !important;
    }
    .stMarkdown strong {
        color: #f1f5f9 !important;
    }

    /* Caption */
    .stCaption, [data-testid="stCaption"] {
        color: #64748b !important;
    }

    /* ═══ CUSTOM COMPONENT STYLES ═══ */

    /* Header gradient */
    .main-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0d9488 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(13,148,136,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .main-header h1 {
        color: #ffffff !important;
        font-size: 2rem;
        font-weight: 800;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: #94a3b8 !important;
        font-size: 0.95rem;
        margin: 0;
        font-weight: 400;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #334155);
        border: 1px solid rgba(148,163,184,0.1);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    .metric-card .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0d9488 !important;
        line-height: 1;
    }
    .metric-card .metric-label {
        font-size: 0.75rem;
        color: #94a3b8 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.5rem;
        font-weight: 600;
    }

    /* Agent flow cards */
    .agent-card {
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        min-height: 140px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    .agent-card.pending {
        background: #1e293b;
        border-color: rgba(148,163,184,0.2);
    }
    .agent-card.running {
        background: rgba(59,130,246,0.15);
        border-color: #3b82f6;
        animation: pulse-border 2s infinite;
    }
    .agent-card.completed {
        background: rgba(13,148,136,0.15);
        border-color: #0d9488;
    }
    .agent-card.skipped {
        background: #1e293b;
        border-color: rgba(148,163,184,0.1);
        opacity: 0.6;
    }
    .agent-card.failed {
        background: rgba(239,68,68,0.1);
        border-color: #ef4444;
    }
    .agent-card .agent-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    .agent-card .agent-name {
        font-weight: 700;
        font-size: 0.85rem;
        color: #e2e8f0 !important;
    }
    .agent-card .agent-status {
        font-size: 0.7rem;
        margin-top: 0.3rem;
        color: #94a3b8 !important;
        font-weight: 500;
    }
    .flow-arrow {
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        color: #475569 !important;
    }

    @keyframes pulse-border {
        0%, 100% { box-shadow: 0 0 0 0 rgba(59,130,246,0.4); }
        50% { box-shadow: 0 0 0 8px rgba(59,130,246,0); }
    }

    /* Result card */
    .result-card {
        background: #1e293b !important;
        border: 1px solid rgba(148,163,184,0.1);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .result-card h4 {
        color: #0d9488 !important;
        margin: 0 0 0.5rem 0 !important;
    }
    .result-card p, .result-card li, .result-card ol {
        color: #94a3b8 !important;
    }
    .result-card strong {
        color: #e2e8f0 !important;
    }

    /* Score badge */
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .score-high { background: rgba(13,148,136,0.2); color: #0d9488 !important; }
    .score-mid { background: rgba(234,179,8,0.2); color: #eab308 !important; }
    .score-low { background: rgba(239,68,68,0.2); color: #ef4444 !important; }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .status-proceed { background: rgba(13,148,136,0.15); color: #0d9488 !important; border: 1px solid rgba(13,148,136,0.3); }
    .status-caution { background: rgba(234,179,8,0.15); color: #eab308 !important; border: 1px solid rgba(234,179,8,0.3); }
    .status-reject  { background: rgba(239,68,68,0.15); color: #ef4444 !important; border: 1px solid rgba(239,68,68,0.3); }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: #1e293b !important;
        border-radius: 10px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #94a3b8 !important;
        font-weight: 600;
        font-size: 0.85rem;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        background: #0f172a !important;
        color: #0d9488 !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #0f172a !important;
    }

    /* Custom divider */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148,163,184,0.2), transparent);
        margin: 1rem 0;
    }

    /* Log viewer */
    .log-entry {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 0.78rem;
        line-height: 1.6;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        margin-bottom: 2px;
        color: #cbd5e1 !important;
    }
    .log-agent  { background: rgba(59,130,246,0.08); border-left: 3px solid #3b82f6; }
    .log-tool   { background: rgba(168,85,247,0.08); border-left: 3px solid #a855f7; }
    .log-ok     { background: rgba(13,148,136,0.08); border-left: 3px solid #0d9488; }
    .log-err    { background: rgba(239,68,68,0.08); border-left: 3px solid #ef4444; }
    .log-warn   { background: rgba(234,179,8,0.08); border-left: 3px solid #eab308; }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0f172a;
    }
    ::-webkit-scrollbar-thumb {
        background: #334155;
        border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #475569;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

def init_session_state():
    """Initialize Streamlit session state variables."""
    defaults = {
        "pipeline_ran": False,
        "pipeline_running": False,
        "final_state": None,
        "agent_statuses": {
            "document_extractor": "pending",
            "candidate_matcher": "pending",
            "assessment_coordinator": "pending",
            "interview_strategist": "pending",
        },
        "uploaded_resumes": [],
        "uploaded_flyers": [],
        "run_logs": [],
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_score_class(score: int) -> str:
    if score >= 75: return "score-high"
    if score >= 50: return "score-mid"
    return "score-low"

def get_status_class(rec: str) -> str:
    if rec in ("PROCEED", "STRONG_MATCH", "PASS"): return "status-proceed"
    if rec in ("PROCEED_WITH_CAUTION", "MODERATE_MATCH", "BORDERLINE"): return "status-caution"
    return "status-reject"

def get_db_jobs(db_path: str) -> list:
    """Fetch all jobs from the database for the dropdown."""
    if not os.path.exists(db_path):
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT job_id, title, department FROM jobs WHERE status = 'OPEN'")
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jobs
    except Exception:
        return []

def save_uploaded_files(uploaded_files, dest_dir: str) -> list[str]:
    """Save uploaded files to a directory and return paths."""
    os.makedirs(dest_dir, exist_ok=True)
    paths = []
    for f in uploaded_files:
        path = os.path.join(dest_dir, f.name)
        with open(path, "wb") as out:
            out.write(f.getbuffer())
        paths.append(os.path.abspath(path))
    return paths

def render_agent_flow(statuses: dict):
    """Render the visual pipeline flow with agent cards."""
    agents = [
        ("📄", "Document\nExtractor", "document_extractor", "Agent 1"),
        ("🎯", "Candidate\nMatcher", "candidate_matcher", "Agent 2"),
        ("📝", "Assessment\nCoordinator", "assessment_coordinator", "Agent 3"),
        ("🎤", "Interview\nStrategist", "interview_strategist", "Agent 4"),
    ]
    cols = st.columns([3, 1, 3, 1, 3, 1, 3])
    for i, (icon, name, key, label) in enumerate(agents):
        status = statuses.get(key, "pending")
        status_text = {"pending": "Waiting", "running": "Processing...", "completed": "✅ Done", "failed": "❌ Failed", "skipped": "⏭ Skipped"}.get(status, "")
        with cols[i * 2]:
            st.markdown(f"""
            <div class="agent-card {status}">
                <div class="agent-icon">{icon}</div>
                <div class="agent-name">{name}</div>
                <div class="agent-status">{label} • {status_text}</div>
            </div>
            """, unsafe_allow_html=True)
        if i < 3:
            with cols[i * 2 + 1]:
                arrow_color = "#0d9488" if status == "completed" else "#475569"
                st.markdown(f'<div class="flow-arrow" style="color:{arrow_color}; margin-top: 45px;">→</div>', unsafe_allow_html=True)


def render_log_entries(logs: list[str]):
    """Render pipeline log entries with color coding."""
    for log in logs:
        if "✅" in log or "SUCCESS" in log:
            css_class = "log-ok"
        elif "❌" in log or "FAILED" in log or "Error" in log:
            css_class = "log-err"
        elif "⚠️" in log or "SKIP" in log:
            css_class = "log-warn"
        elif "🔧" in log or "Tool" in log:
            css_class = "log-tool"
        else:
            css_class = "log-agent"
        st.markdown(f'<div class="log-entry {css_class}">{log}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PIPELINE RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def create_initial_state(resume_paths, flyer_paths, job_id, db_path):
    """Create the initial pipeline state dict."""
    return {
        "resume_paths": resume_paths,
        "job_flyer_paths": flyer_paths,
        "target_job_id": job_id if job_id != "ALL" else None,
        "db_path": os.path.abspath(db_path),
        "candidate_profiles": [],
        "job_vacancies": [],
        "parse_errors": [],
        "match_reports": [],
        "shortlisted_candidates": [],
        "rejected_candidates": [],
        "assessments": [],
        "assessment_results": [],
        "interview_guides": [],
        "comparison_report": None,
        "current_agent": "initializing",
        "pipeline_status": "RUNNING",
        "processing_log": [],
        "error_log": [],
        "messages": [],
    }


def run_agent_step(agent_fn, state, llm, tracer, agent_key):
    """Run a single agent and merge results into state."""
    import time as _time
    start = _time.time()
    result = agent_fn(state, llm=llm, tracer=tracer)
    duration = _time.time() - start
    # Merge result into state
    merged = dict(state)
    merged.update(result)
    return merged, duration


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0 0.5rem 0;">
        <div style="font-size: 2.5rem; margin-bottom: 0.3rem;">🏢</div>
        <div style="font-size: 1.1rem; font-weight: 800; letter-spacing: -0.02em; color: #f1f5f9;">
            HR Recruitment
        </div>
        <div style="font-size: 0.75rem; color: #64748b; font-weight: 500;">
            Multi-Agent Pipeline
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Model Selection ──
    st.markdown("##### ⚙️ LLM Configuration")
    model_name = st.selectbox(
        "Ollama Model",
        ["llama3.2", "llama3:8b", "phi3", "qwen2:7b", "mistral"],
        index=0,
        help="Must be pulled locally first: `ollama pull <model>`"
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Resume Upload ──
    st.markdown("##### 📄 Upload Candidate CVs")
    uploaded_cvs = st.file_uploader(
        "PDF or DOCX files",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="cv_uploader",
    )
    if uploaded_cvs:
        for f in uploaded_cvs:
            st.markdown(f"<span style='font-size:0.8rem;'>✅ {f.name}</span>", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Flyer Upload ──
    st.markdown("##### 📋 Upload Job Flyers")
    uploaded_flyers = st.file_uploader(
        "PDF job flyer/poster",
        type=["pdf"],
        accept_multiple_files=True,
        key="flyer_uploader",
    )
    if uploaded_flyers:
        for f in uploaded_flyers:
            st.markdown(f"<span style='font-size:0.8rem;'>✅ {f.name}</span>", unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Job Selection ──
    st.markdown("##### 🎯 Target Vacancy")
    db_path = "data/hr_jobs.db"
    jobs = get_db_jobs(db_path)
    job_options = ["ALL — Match against all open jobs"] + [
        f"{j['job_id']} — {j['title']}" for j in jobs
    ]
    selected_job = st.selectbox("Select Job", job_options, index=0)
    target_job_id = selected_job.split(" — ")[0] if selected_job != job_options[0] else "ALL"

    # ── Use sample data checkbox ──
    use_sample = st.checkbox("Use sample data", value=True, help="Use pre-generated sample resumes and flyers")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # ── Run Button ──
    run_disabled = False
    if not uploaded_cvs and not use_sample:
        run_disabled = True

    run_clicked = st.button(
        "🚀  Run Pipeline",
        use_container_width=True,
        type="primary",
        disabled=run_disabled,
    )

    if not uploaded_cvs and not use_sample:
        st.caption("⚠️ Upload CVs or enable sample data")

    # ── Reset Button ──
    if st.session_state.pipeline_ran:
        if st.button("🔄  Reset Pipeline", use_container_width=True):
            st.session_state.pipeline_ran = False
            st.session_state.final_state = None
            st.session_state.agent_statuses = {k: "pending" for k in st.session_state.agent_statuses}
            st.session_state.run_logs = []
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

# ── Header ──
st.markdown("""
<div class="main-header">
    <h1>🏢 HR Recruitment Pipeline</h1>
    <p>Autonomous Multi-Agent System — Powered by Ollama + LangGraph — 100% Local & Privacy-First</p>
</div>
""", unsafe_allow_html=True)

# ── Pipeline Execution ──
if run_clicked and not st.session_state.pipeline_running:
    st.session_state.pipeline_running = True

    # Prepare file paths
    resume_paths = []
    flyer_paths = []

    if uploaded_cvs:
        tmp_dir = os.path.join("data", "_tmp_uploads")
        resume_paths = save_uploaded_files(uploaded_cvs, os.path.join(tmp_dir, "resumes"))
    if uploaded_flyers:
        tmp_dir = os.path.join("data", "_tmp_uploads")
        flyer_paths = save_uploaded_files(uploaded_flyers, os.path.join(tmp_dir, "flyers"))

    if use_sample:
        sample_resume_dir = "data/sample_resumes"
        sample_flyer_dir = "data/sample_flyers"

        if not os.path.exists(sample_resume_dir) or not os.listdir(sample_resume_dir):
            with st.spinner("📄 Generating sample data..."):
                from create_sample_data import create_sample_resumes, create_sample_flyers
                create_sample_resumes()
                create_sample_flyers()

        if not os.path.exists(db_path):
            from setup_db import setup_database
            setup_database()

        sample_resumes = sorted(glob.glob(os.path.join(sample_resume_dir, "*.pdf")))
        sample_flyers_list = sorted(glob.glob(os.path.join(sample_flyer_dir, "*.pdf")))
        resume_paths = [os.path.abspath(r) for r in sample_resumes] + resume_paths
        flyer_paths = [os.path.abspath(f) for f in sample_flyers_list] + flyer_paths

    if not resume_paths:
        st.error("❌ No resumes to process. Upload CVs or enable sample data.")
        st.session_state.pipeline_running = False
        st.stop()

    # ── Import agents and create LLM ──
    from observability.tracer import AgentTracer
    from agents.document_extractor import document_extractor_node
    from agents.candidate_matcher import candidate_matcher_node
    from agents.assessment_coordinator import assessment_coordinator_node
    from agents.interview_strategist import interview_strategist_node
    from pipeline.routing import route_after_extraction, route_after_matching, route_after_assessment

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    tracer = AgentTracer(log_dir="logs", run_id=run_id)

    from langchain_ollama import ChatOllama
    llm_json = ChatOllama(model=model_name, temperature=0, format="json")
    llm_markdown = ChatOllama(model=model_name, temperature=0.3)

    state = create_initial_state(resume_paths, flyer_paths, target_job_id, db_path)

    st.markdown(f"📄 Processing **{len(resume_paths)} resume(s)** and **{len(flyer_paths)} flyer(s)** with **{model_name}**")

    agent_steps = [
        ("document_extractor", "📄 Agent 1: Document Extractor", document_extractor_node, llm_json),
        ("candidate_matcher", "🎯 Agent 2: Candidate Matcher", candidate_matcher_node, llm_json),
        ("assessment_coordinator", "📝 Agent 3: Assessment Coordinator", assessment_coordinator_node, llm_json),
        ("interview_strategist", "🎤 Agent 4: Interview Strategist", interview_strategist_node, llm_markdown),
    ]

    route_checks = {
        "document_extractor": (route_after_extraction, "candidate_matcher"),
        "candidate_matcher": (route_after_matching, "assessment_coordinator"),
        "assessment_coordinator": (route_after_assessment, "interview_strategist"),
    }

    pipeline_failed = False

    for agent_key, agent_label, agent_fn, agent_llm in agent_steps:
        # Check routing — should we skip this agent?
        if agent_key != "document_extractor":
            prev_key = agent_steps[agent_steps.index((agent_key, agent_label, agent_fn, agent_llm)) - 1][0]
            route_fn, expected_next = route_checks.get(prev_key, (None, None))
            if route_fn:
                decision = route_fn(state)
                if decision != expected_next:
                    st.session_state.agent_statuses[agent_key] = "skipped"
                    continue

        st.session_state.agent_statuses[agent_key] = "running"

        with st.status(f"⏳ {agent_label} — Running...", expanded=True) as agent_status:
            try:
                st.write(f"Started at {datetime.now().strftime('%H:%M:%S')}")
                state, duration = run_agent_step(agent_fn, state, agent_llm, tracer, agent_key)
                mins, secs = divmod(int(duration), 60)

                st.session_state.agent_statuses[agent_key] = "completed"
                agent_status.update(label=f"✅ {agent_label} — Done ({mins}m {secs}s)", state="complete")

                # ── Show immediate results based on which agent just completed ──
                if agent_key == "document_extractor":
                    profiles = state.get("candidate_profiles", [])
                    vacancies = state.get("job_vacancies", [])
                    errors = state.get("parse_errors", [])
                    st.write(f"📊 **{len(profiles)}** candidate profiles, **{len(vacancies)}** job vacancies, **{len(errors)}** errors")
                    for p in profiles:
                        skills_str = ", ".join(p.get("skills", [])[:8])
                        st.write(f"  👤 **{p.get('candidate_name', '?')}** — {p.get('years_of_experience', '?')}y exp — `{skills_str}`")
                    for v in vacancies:
                        st.write(f"  💼 **{v.get('title', '?')}** ({v.get('department', '?')})")

                elif agent_key == "candidate_matcher":
                    short = state.get("shortlisted_candidates", [])
                    rej = state.get("rejected_candidates", [])
                    st.write(f"📊 **{len(short)}** shortlisted, **{len(rej)}** rejected")
                    for s in short:
                        m = s.get("best_match", {})
                        st.write(f"  ✅ **{m.get('candidate_name', '?')}** → {m.get('job_title', '?')} — Score: **{m.get('overall_match_score', 0)}/100** [{m.get('recommendation', '')}]")
                    for r in rej:
                        st.write(f"  ❌ **{r.get('candidate_profile', {}).get('candidate_name', '?')}** — Score: {r.get('best_score', 0)}/100")

                elif agent_key == "assessment_coordinator":
                    results = state.get("assessment_results", [])
                    st.write(f"📊 **{len(results)}** assessments scored")
                    for r in results:
                        st.write(f"  📝 **{r.get('candidate_name', '?')}** — {r.get('percentage', 0):.1f}% [{r.get('pass_status', '?')}]")

                elif agent_key == "interview_strategist":
                    guides = state.get("interview_guides", [])
                    st.write(f"📊 **{len(guides)}** interview guides generated")
                    for g in guides:
                        st.write(f"  🎤 **{g.get('candidate_name', '?')}** → {g.get('job_title', '?')} [{g.get('recommendation', '?')}]")

            except Exception as e:
                st.session_state.agent_statuses[agent_key] = "failed"
                agent_status.update(label=f"❌ {agent_label} — Failed", state="error")
                st.error(f"{type(e).__name__}: {str(e)}")
                pipeline_failed = True
                break

    # Save final state
    state["pipeline_status"] = "FAILED" if pipeline_failed else "COMPLETED"
    st.session_state.final_state = state
    st.session_state.pipeline_ran = True
    st.session_state.run_logs = state.get("processing_log", [])
    st.session_state.pipeline_running = False

    if not pipeline_failed:
        st.success("🎉 Pipeline completed successfully!")
    st.rerun()

# ── Agent Flow Visualization ──
st.markdown("### 🔄 Pipeline Flow")
render_agent_flow(st.session_state.agent_statuses)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Results Display ──
if st.session_state.pipeline_ran and st.session_state.final_state:
    state = st.session_state.final_state

    # ── KPI Metrics ──
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(state.get('candidate_profiles', []))}</div>
            <div class="metric-label">CVs Extracted</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(state.get('job_vacancies', []))}</div>
            <div class="metric-label">Vacancies</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(state.get('shortlisted_candidates', []))}</div>
            <div class="metric-label">Shortlisted</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(state.get('rejected_candidates', []))}</div>
            <div class="metric-label">Rejected</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(state.get('assessment_results', []))}</div>
            <div class="metric-label">Assessed</div>
        </div>""", unsafe_allow_html=True)
    with c6:
        st.markdown(f"""<div class="metric-card">
            <div class="metric-value">{len(state.get('interview_guides', []))}</div>
            <div class="metric-label">Guides</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Detail Tabs ──
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Extracted Data",
        "🎯 Match Results",
        "📝 Assessments",
        "🎤 Interview Guides",
        "📊 Pipeline Logs",
    ])

    # ── TAB 1: Extracted Data ──
    with tab1:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 👤 Candidate Profiles")
            profiles = state.get("candidate_profiles", [])
            if profiles:
                for i, profile in enumerate(profiles):
                    with st.expander(f"📄 {profile.get('candidate_name', 'Unknown')} — {len(profile.get('skills', []))} skills", expanded=(i == 0)):
                        pc1, pc2 = st.columns(2)
                        with pc1:
                            st.markdown(f"**Name:** {profile.get('candidate_name', 'N/A')}")
                            st.markdown(f"**Email:** {profile.get('email', 'N/A')}")
                            st.markdown(f"**Experience:** {profile.get('years_of_experience', 'N/A')} years")
                        with pc2:
                            st.markdown(f"**GitHub:** {profile.get('github_url', 'N/A')}")
                            st.markdown(f"**Phone:** {profile.get('phone', 'N/A')}")
                        st.markdown("**Skills:**")
                        skills = profile.get("skills", [])
                        if skills:
                            st.markdown(" ".join([f"`{s}`" for s in skills]))
                        st.markdown("**Education:**")
                        for edu in profile.get("education", []):
                            st.markdown(f"- {edu.get('degree', '')} — {edu.get('institution', '')} ({edu.get('year', '')})")
                        st.markdown("**Work Experience:**")
                        for exp in profile.get("work_experience", []):
                            st.markdown(f"- **{exp.get('role', '')}** at {exp.get('company', '')} ({exp.get('duration', '')})")
                            for h in exp.get("highlights", []):
                                st.markdown(f"  - {h}")
            else:
                st.info("No candidate profiles extracted.")

        with col_b:
            st.markdown("#### 📋 Job Vacancies")
            vacancies = state.get("job_vacancies", [])
            if vacancies:
                for i, vac in enumerate(vacancies):
                    with st.expander(f"💼 {vac.get('title', 'Unknown')} — {vac.get('department', 'N/A')}", expanded=(i == 0)):
                        st.markdown(f"**Job ID:** {vac.get('job_id', 'N/A')}")
                        st.markdown(f"**Department:** {vac.get('department', 'N/A')}")
                        st.markdown(f"**Experience:** {vac.get('min_experience_years', 'N/A')}+ years")
                        st.markdown(f"**Education:** {vac.get('required_education', 'N/A')}")
                        st.markdown(f"**Salary:** {vac.get('salary_range', 'N/A')}")
                        st.markdown("**Required Skills:**")
                        req_skills = vac.get("required_skills", [])
                        if req_skills:
                            st.markdown(" ".join([f"`{s}`" for s in req_skills]))
                        pref_skills = vac.get("preferred_skills", [])
                        if pref_skills:
                            st.markdown("**Preferred Skills:**")
                            st.markdown(" ".join([f"`{s}`" for s in pref_skills]))
            else:
                st.info("No job vacancies extracted from flyers.")

            errors = state.get("parse_errors", [])
            if errors:
                st.markdown("#### ⚠️ Parse Errors")
                for err in errors:
                    st.error(f"**{err.get('file_path', 'Unknown')}**: {err.get('error', 'Unknown error')}")

    # ── TAB 2: Match Results ──
    with tab2:
        st.markdown("#### 🎯 Candidate Matching Results")
        shortlisted = state.get("shortlisted_candidates", [])
        if shortlisted:
            st.markdown("##### ✅ Shortlisted Candidates")
            for entry in shortlisted:
                match = entry.get("best_match", {})
                score = match.get("overall_match_score", 0)
                rec = match.get("recommendation", "N/A")
                name = match.get("candidate_name", "Unknown")
                job = match.get("job_title", "Unknown")
                with st.expander(f"✅ {name} → {job} — Score: {score}/100 [{rec}]", expanded=True):
                    mc1, mc2, mc3 = st.columns(3)
                    with mc1:
                        st.metric("Match Score", f"{score}/100")
                    with mc2:
                        skill_pct = match.get("skill_match", {}).get("skill_match_percentage", 0)
                        st.metric("Skill Match", f"{skill_pct}%")
                    with mc3:
                        exp_score = match.get("experience_match", {}).get("experience_score", 0)
                        st.metric("Experience Score", f"{exp_score}/100")
                    mcol1, mcol2 = st.columns(2)
                    with mcol1:
                        matched_skills = match.get("skill_match", {}).get("matched_skills", [])
                        if matched_skills:
                            st.markdown("**✅ Matched Skills:**")
                            st.markdown(" ".join([f"`{s}`" for s in matched_skills]))
                        bonus = match.get("skill_match", {}).get("bonus_skills", [])
                        if bonus:
                            st.markdown("**🌟 Bonus Skills:**")
                            st.markdown(" ".join([f"`{s}`" for s in bonus]))
                    with mcol2:
                        missing = match.get("skill_match", {}).get("missing_skills", [])
                        if missing:
                            st.markdown("**❌ Missing Skills:**")
                            st.markdown(" ".join([f"`{s}`" for s in missing]))
                    st.markdown(f"**Reasoning:** {match.get('reasoning', 'N/A')}")

        rejected = state.get("rejected_candidates", [])
        if rejected:
            st.markdown("##### ❌ Rejected Candidates")
            for entry in rejected:
                name = entry.get("candidate_profile", {}).get("candidate_name", "Unknown")
                reason = entry.get("rejection_reason", "N/A")
                best_score = entry.get("best_score", 0)
                st.warning(f"**{name}** — Score: {best_score}/100 — {reason}")
        if not shortlisted and not rejected:
            st.info("No matching results yet. Run the pipeline first.")

    # ── TAB 3: Assessments ──
    with tab3:
        st.markdown("#### 📝 Assessment Results")
        results = state.get("assessment_results", [])
        if results:
            for res in results:
                name = res.get("candidate_name", "Unknown")
                pct = res.get("percentage", 0)
                pass_status = res.get("pass_status", "N/A")
                with st.expander(f"📝 {name} — {pct:.1f}% [{pass_status}]", expanded=True):
                    ac1, ac2, ac3 = st.columns(3)
                    with ac1:
                        st.metric("Total Score", f"{res.get('total_score', 0)}/{res.get('max_score', 0)}")
                    with ac2:
                        st.metric("Percentage", f"{pct:.1f}%")
                    with ac3:
                        st.metric("Status", pass_status)
                    section_scores = res.get("section_scores", [])
                    if section_scores:
                        st.markdown("**Section Breakdown:**")
                        for sec in section_scores:
                            sec_pct = sec.get("percentage", 0)
                            st.progress(sec_pct / 100, text=f"{sec.get('section', '?')}: {sec.get('scored', 0)}/{sec.get('max', 0)} ({sec_pct:.1f}%)")
                    flags = res.get("flags", [])
                    if flags:
                        st.markdown("**🚩 Red Flags:**")
                        for flag in flags:
                            st.error(flag)
        else:
            st.info("No assessments generated. Run the pipeline first.")

    # ── TAB 4: Interview Guides ──
    with tab4:
        st.markdown("#### 🎤 Interview Preparation Guides")
        guides = state.get("interview_guides", [])
        if guides:
            for guide in guides:
                name = guide.get("candidate_name", "Unknown")
                job = guide.get("job_title", "Unknown")
                rec = guide.get("recommendation", "N/A")
                match_score = guide.get("match_score", 0)
                assess_score = guide.get("assessment_score", 0)
                status_cls = get_status_class(rec)
                with st.expander(f"📄 {name} → {job} [{rec}]", expanded=True):
                    gc1, gc2, gc3 = st.columns(3)
                    with gc1:
                        st.metric("Match Score", f"{match_score}/100")
                    with gc2:
                        st.metric("Assessment", f"{assess_score:.1f}%")
                    with gc3:
                        st.markdown(f'<div style="padding-top:0.5rem;"><span class="status-badge {status_cls}">{rec}</span></div>', unsafe_allow_html=True)
                    file_path = guide.get("file_path", "")
                    if file_path and os.path.exists(file_path):
                        with open(file_path, "r") as f:
                            report_content = f.read()
                        if report_content.startswith("---"):
                            parts = report_content.split("---", 2)
                            if len(parts) >= 3:
                                report_content = parts[2].strip()
                        st.markdown(report_content)
                        st.download_button(
                            label="⬇️  Download Report", data=open(file_path, "r").read(),
                            file_name=os.path.basename(file_path), mime="text/markdown", key=f"download_{name}",
                        )
                    else:
                        st.warning("Report file not found on disk.")
            comp_report = state.get("comparison_report")
            if comp_report and os.path.exists(comp_report):
                st.markdown("---")
                st.markdown("#### 📊 Candidate Comparison Report")
                with open(comp_report, "r") as f:
                    comp_content = f.read()
                if comp_content.startswith("---"):
                    parts = comp_content.split("---", 2)
                    if len(parts) >= 3:
                        comp_content = parts[2].strip()
                st.markdown(comp_content)
                st.download_button(
                    label="⬇️  Download Comparison Report", data=open(comp_report, "r").read(),
                    file_name=os.path.basename(comp_report), mime="text/markdown",
                )
        else:
            st.info("No interview guides generated. Run the pipeline first.")

    # ── TAB 5: Pipeline Logs ──
    with tab5:
        st.markdown("#### 📊 Pipeline Execution Logs")
        logs = state.get("processing_log", [])
        if logs:
            st.markdown(f"**Total log entries:** {len(logs)}")
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            render_log_entries(logs)
            log_dir = "logs"
            if os.path.exists(log_dir):
                log_files = sorted(glob.glob(os.path.join(log_dir, "*.jsonl")), reverse=True)
                if log_files:
                    st.markdown("---")
                    st.markdown("#### 📄 Structured Trace Log (JSONL)")
                    latest_log = log_files[0]
                    st.caption(f"File: `{latest_log}`")
                    with open(latest_log, "r") as f:
                        log_content = f.read()
                    st.code(log_content[-3000:], language="json")
                    st.download_button("⬇️  Download Full Trace Log", data=log_content,
                        file_name=os.path.basename(latest_log), mime="application/json")
        else:
            st.info("No logs available. Run the pipeline first.")

else:
    # ── Welcome State ──
    st.markdown("")
    st.markdown("""
    <div class="result-card">
        <h4>👋 Welcome to the HR Recruitment Pipeline</h4>
        <p style="color: #94a3b8; margin: 0.5rem 0;">
            This Multi-Agent System automates the full hiring lifecycle using 4 specialized AI agents,
            all running locally on your machine with zero cloud dependencies.
        </p>
        <p style="color: #64748b; font-size: 0.85rem; margin-top: 1rem;">
            <strong>To get started:</strong>
        </p>
        <ol style="color: #94a3b8; font-size: 0.85rem;">
            <li>Upload candidate CVs (PDF/DOCX) in the sidebar — or enable <strong>sample data</strong></li>
            <li>Optionally upload a job flyer or select a target vacancy</li>
            <li>Click <strong>🚀 Run Pipeline</strong> to start the agents</li>
            <li>Watch each agent's results appear <strong>live</strong> as it completes</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🏗️ System Architecture")
    arch_col1, arch_col2 = st.columns([3, 2])
    with arch_col1:
        st.markdown("""
        | Agent | Role | Tool |
        |-------|------|------|
        | 🔵 **Document Extractor** | Parses CVs & Job Flyers → structured JSON | PDF/DOCX Parser |
        | 🟣 **Candidate Matcher** | Scores & ranks candidates against vacancies | SQLite Database |
        | 🟢 **Assessment Coordinator** | Generates personalized quizzes + auto-grades | JSON Generator |
        | 🟠 **Interview Strategist** | Creates interview guides + comparison reports | Markdown Writer |
        """)
    with arch_col2:
        st.markdown("""
        **Key Features:**
        - ✅ 100% Local — Zero cloud, all Ollama
        - 🔒 Privacy-First — PII never leaves machine
        - 🔄 Conditional Routing — Smart agent delegation
        - 📊 Full Observability — JSONL trace logging
        - 🧪 Automated Testing — Property + LLM-as-Judge
        """)

    if os.path.exists("data/sample_resumes") and os.listdir("data/sample_resumes"):
        sample_count = len(glob.glob("data/sample_resumes/*.pdf"))
        st.success(f"✅ Sample data available: {sample_count} PDF resumes ready. Enable 'Use sample data' in sidebar.")
    else:
        st.warning("⚠️ No sample data found. Click 'Use sample data' in the sidebar — it will be auto-generated on first run.")
