# 🏢 HR Recruitment Pipeline — Multi-Agent System

> **SE4010 – CTSE | Assignment 2 – Machine Learning**  
> Sri Lanka Institute of Information Technology  
> 100% Local • Zero Cloud • Privacy-First

## 📋 Overview

An **Autonomous Local HR Recruitment Pipeline** — a Multi-Agent System (MAS) that automates the full hiring lifecycle while keeping all candidate data private and local. Built with **LangGraph** for orchestration and **Ollama** for local LLM inference.

### The Problem
HR departments receive hundreds of resumes containing **Personally Identifiable Information (PII)** — NIC numbers, phone numbers, addresses — that cannot legally be uploaded to cloud LLMs. Manual screening of 200+ CVs per role takes 15-20 hours and produces inconsistent results.

### Our Solution
An autonomous team of 4 AI agents that:
1. **Reads** CVs and job flyers → extracts structured data
2. **Matches** candidates to vacancies → produces ranked shortlists
3. **Assesses** shortlisted candidates → generates personalized quizzes
4. **Prepares** interview guides → creates actionable documents for hiring managers

**All processing happens locally. Zero data leaves your machine.**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LangGraph Orchestrator                       │
│                                                                     │
│  📄 Input    ┌──────────────┐    ┌──────────────┐    ┌──────────┐  │
│  CVs + ──►   │  Agent 1:    │──►│  Agent 2:    │──►│ Agent 3: │  │
│  Flyers      │  Document    │   │  Candidate   │   │ Assessment│  │
│              │  Extractor   │   │  Matcher     │   │ Coord.   │  │
│              └──────────────┘   └──────────────┘   └──────────┘  │
│                     │                  │                  │        │
│                     ▼                  ▼                  ▼        │
│              ┌──────────────┐   ┌──────────────┐   ┌──────────┐  │
│              │ Tool:        │   │ Tool:        │   │ Tool:    │  │
│              │ PDF/DOCX     │   │ SQLite DB    │   │ JSON     │  │
│              │ Parser       │   │ Manager      │   │ Generator│  │
│              └──────────────┘   └──────────────┘   └──────────┘  │
│                                                         │        │
│                                                         ▼        │
│                                                   ┌──────────┐   │
│                                                   │ Agent 4: │   │
│                                                   │ Interview│   │
│                                                   │ Strategist│  │
│                                                   └──────────┘   │
│                                                         │        │
│                                                         ▼        │
│                                                   ┌──────────┐   │
│                                                   │ Tool:    │   │
│                                                   │ Report   │   │
│                                                   │ Writer   │   │
│                                                   └──────────┘   │
│                                                         │        │
│                                                         ▼        │
│                                                   📄 Interview   │
│                                                      Guides      │
└─────────────────────────────────────────────────────────────────────┘
```

### Conditional Routing (Coordinator Pattern)
- ❌ Resume parse fails → Skip candidate
- ❌ Match score < 60% → Reject with reason
- ❌ Assessment failed → Do not proceed
- ✅ Each step gates the next — no wasted processing

---

## 👥 Team & Agent Assignments

| Student | Agent | Tool | Responsibility |
|---------|-------|------|----------------|
| **A** | Document Intelligence Extractor | `document_parser` (PDF/DOCX) | Parse CVs + job flyers into structured JSON |
| **B** | Smart Candidate Matcher | `job_database_manager` (SQLite) | Score & rank candidates against vacancies |
| **C** | Assessment Coordinator | `assessment_generator` (JSON) | Generate personalized quizzes + auto-grade |
| **D** | Interview Strategist | `report_file_writer` (Markdown) | Produce interview guides + comparison reports |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai/) installed locally
- A local LLM pulled (e.g., `ollama pull llama3.2`)

### Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd ctse-assignment2

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Make sure Ollama is running
ollama serve  # In a separate terminal

# 5. Pull the model (if not already done)
ollama pull llama3.2

# 6. Set up the database with sample jobs
python setup_db.py

# 7. Create sample test data (PDF resumes + flyers)
python create_sample_data.py
```

### Running the Pipeline

```bash
# Run with all sample data
python main.py

# Process specific resumes
python main.py --resumes data/sample_resumes/john_doe_fullstack.pdf

# Match against a specific job
python main.py --job-id JOB-001

# Use a different model
python main.py --model llama3:8b

# Process job flyers
python main.py --flyers data/sample_flyers/flyer_senior_fullstack.pdf
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run individual student tests
pytest tests/test_document_extractor.py -v    # Student A
pytest tests/test_candidate_matcher.py -v     # Student B
pytest tests/test_assessment_coordinator.py -v # Student C
pytest tests/test_interview_strategist.py -v  # Student D
```

---

## 📁 Project Structure

```
ctse-assignment2/
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── setup_db.py                      # Database setup script
├── create_sample_data.py            # Sample PDF generator
│
├── agents/                          # 4 Agent implementations
│   ├── document_extractor.py        # Agent 1 (Student A)
│   ├── candidate_matcher.py         # Agent 2 (Student B)
│   ├── assessment_coordinator.py    # Agent 3 (Student C)
│   └── interview_strategist.py      # Agent 4 (Student D)
│
├── tools/                           # 4 Custom tools
│   ├── document_parser.py           # Tool 1: PDF/DOCX parser
│   ├── job_database_manager.py      # Tool 2: SQLite CRUD
│   ├── assessment_generator.py      # Tool 3: Quiz generator + scorer
│   └── report_file_writer.py        # Tool 4: Markdown report writer
│
├── state/                           # State management
│   └── pipeline_state.py            # PipelineState TypedDict
│
├── pipeline/                        # LangGraph orchestration
│   ├── graph.py                     # StateGraph definition
│   └── routing.py                   # Conditional routing functions
│
├── observability/                   # LLMOps / AgentOps
│   └── tracer.py                    # Structured JSONL logger
│
├── tests/                           # Test suite
│   ├── conftest.py                  # Shared fixtures
│   ├── test_document_extractor.py   # Student A tests
│   ├── test_candidate_matcher.py    # Student B tests
│   ├── test_assessment_coordinator.py # Student C tests
│   ├── test_interview_strategist.py # Student D tests
│   └── evaluation/
│       └── llm_judge.py             # LLM-as-a-Judge evaluator
│
├── data/                            # Data directory
│   ├── hr_jobs.db                   # SQLite database
│   ├── sample_resumes/              # Test PDF resumes
│   └── sample_flyers/               # Test PDF job flyers
│
├── reports/                         # Generated interview guides
├── assessments/                     # Generated assessments
└── logs/                            # Pipeline trace logs (JSONL)
```

---

## 🔧 Technical Stack

| Component | Technology | Why |
|-----------|-----------|-----|
| **LLM Engine** | Ollama (llama3.2 / llama3:8b) | Local, zero-cost, strong instruction following |
| **Orchestrator** | LangGraph | Graph-based state machine with conditional edges |
| **Language** | Python 3.11+ | Type hinting, async support |
| **PDF Parsing** | pdfplumber + python-docx | Handles complex layouts and DOCX |
| **Database** | SQLite3 | Zero-config local DB |
| **Validation** | Pydantic | Strict type checking for tool I/O |
| **Report Generation** | Markdown + YAML frontmatter | Professional, portable output |
| **Logging** | Custom AgentTracer (JSONL) | Structured, machine-parseable traces |
| **Testing** | pytest + LLM-as-a-Judge | Property-based + semantic evaluation |

---

## 📊 Observability

Every pipeline run produces a structured trace log at `logs/pipeline_trace_<timestamp>.jsonl`:

```json
{"event": "PIPELINE_START", "run_id": "20260418_143001", "timestamp": "..."}
{"event": "AGENT_START", "agent": "DocumentExtractor", "input_keys": ["resume_paths"]}
{"event": "TOOL_CALL", "agent": "DocumentExtractor", "tool": "document_parser", "output_success": true}
{"event": "LLM_CALL", "agent": "DocumentExtractor", "model": "llama3.2", "duration_seconds": 3.2}
{"event": "AGENT_END", "agent": "DocumentExtractor", "status": "SUCCESS", "duration_seconds": 5.1}
{"event": "ROUTING_DECISION", "from_agent": "DocumentExtractor", "to_agent": "CandidateMatcher"}
...
{"event": "PIPELINE_END", "status": "COMPLETED", "total_duration_seconds": 45.3}
```

PII (phone, email, NIC) is **automatically redacted** in all logs.

---

## 📜 License

This project was created for academic purposes as part of SE4010 – CTSE at SLIIT.
