"""
Shared Test Fixtures
====================
Common fixtures and utilities used across all agent test modules.
Provides sample data, temporary directories, and mock objects.
"""

import json
import os
import sqlite3
import tempfile

import pytest


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_resume_text() -> str:
    """Sample resume raw text for testing extraction."""
    return """John Doe
john.doe@email.com | +94 77 123 4567 | https://github.com/johndoe

PROFESSIONAL SUMMARY
Experienced Full-Stack Developer with 5 years of experience building scalable web 
applications. Proficient in Python, React.js, and cloud technologies.

TECHNICAL SKILLS
Python, React.js, Node.js, PostgreSQL, Docker, Git, REST APIs, TypeScript

WORK EXPERIENCE
Senior Software Engineer — TechCorp Lanka (2022 - Present)
• Led development of microservices architecture serving 100K+ users
• Implemented CI/CD pipeline reducing deployment time by 60%

Software Engineer — Digital Solutions Pvt Ltd (2020 - 2022)
• Built React.js dashboard for real-time data analytics
• Developed Python REST APIs using FastAPI framework

EDUCATION
BSc in Computer Science — University of Colombo (2020)

CERTIFICATIONS
• AWS Certified Developer
• Docker Certified Associate
"""


@pytest.fixture
def sample_job_flyer_text() -> str:
    """Sample job flyer raw text for testing extraction."""
    return """We're Hiring: Senior Full-Stack Developer
Department: Engineering

About the Role:
We need a Senior Full-Stack Developer to design and build scalable web applications.

Required Skills:
• Python
• React.js
• PostgreSQL
• Docker
• Git
• REST APIs

Preferred Skills:
• Kubernetes
• TypeScript

Requirements:
• 4+ years experience
• Bachelor's in Computer Science or related field

Salary: LKR 800,000 - 1,200,000 per annum
Application Deadline: May 30, 2026
"""


@pytest.fixture
def sample_candidate_profile() -> dict:
    """Sample extracted candidate profile."""
    return {
        "document_type": "RESUME",
        "candidate_name": "John Doe",
        "email": "john.doe@email.com",
        "phone": "+94 77 123 4567",
        "years_of_experience": 5,
        "education": [
            {"degree": "BSc in Computer Science", "institution": "University of Colombo", "year": 2020}
        ],
        "skills": ["python", "reactjs", "nodejs", "postgresql", "docker", "git", "rest-api", "typescript"],
        "work_experience": [
            {
                "company": "TechCorp Lanka",
                "role": "Senior Software Engineer",
                "duration": "2022 - Present",
                "highlights": ["Led microservices architecture", "Implemented CI/CD pipeline"],
            },
            {
                "company": "Digital Solutions Pvt Ltd",
                "role": "Software Engineer",
                "duration": "2020 - 2022",
                "highlights": ["Built React.js dashboard", "Developed Python REST APIs"],
            },
        ],
        "github_url": "https://github.com/johndoe",
        "portfolio_url": "NOT_FOUND",
        "certifications": ["AWS Certified Developer", "Docker Certified Associate"],
    }


@pytest.fixture
def sample_job_description() -> dict:
    """Sample job description from database."""
    return {
        "job_id": "JOB-001",
        "title": "Senior Full-Stack Developer",
        "department": "Engineering",
        "required_skills": ["python", "reactjs", "postgresql", "docker", "git", "rest-api"],
        "preferred_skills": ["kubernetes", "typescript", "graphql", "cicd"],
        "min_experience_years": 4,
        "required_education": "Bachelor's in Computer Science or related field",
        "description": "Build and maintain scalable web applications.",
        "salary_range": "LKR 800,000 - 1,200,000",
        "status": "OPEN",
    }


@pytest.fixture
def sample_match_report() -> dict:
    """Sample match report from Agent 2."""
    return {
        "job_id": "JOB-001",
        "job_title": "Senior Full-Stack Developer",
        "candidate_name": "John Doe",
        "overall_match_score": 85,
        "skill_match": {
            "matched_skills": ["python", "reactjs", "postgresql", "docker", "git", "rest-api"],
            "missing_skills": [],
            "bonus_skills": ["typescript", "nodejs"],
            "skill_match_percentage": 100,
        },
        "experience_match": {
            "required_years": 4,
            "candidate_years": 5,
            "meets_requirement": True,
            "experience_score": 100,
        },
        "education_match": {
            "required_degree": "Bachelor's in Computer Science",
            "candidate_degree": "BSc in Computer Science",
            "meets_requirement": True,
            "education_score": 100,
        },
        "recommendation": "STRONG_MATCH",
        "reasoning": "Candidate matches all required skills and exceeds experience requirements.",
    }


@pytest.fixture
def sample_assessment_result() -> dict:
    """Sample assessment result from Agent 3."""
    return {
        "candidate_name": "John Doe",
        "job_id": "JOB-001",
        "job_title": "Senior Full-Stack Developer",
        "total_score": 78,
        "max_score": 100,
        "percentage": 78.0,
        "section_scores": [
            {"section": "TECHNICAL", "scored": 50, "max": 60, "percentage": 83.3, "questions": 6},
            {"section": "SCENARIO", "scored": 18, "max": 30, "percentage": 60.0, "questions": 2},
            {"section": "PROBLEM_SOLVING", "scored": 10, "max": 10, "percentage": 100.0, "questions": 2},
        ],
        "pass_status": "PASS",
        "flags": [],
    }


@pytest.fixture
def sample_db(tmp_dir) -> str:
    """Create a temporary SQLite database with sample jobs."""
    db_path: str = os.path.join(tmp_dir, "test_jobs.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            required_skills TEXT NOT NULL,
            preferred_skills TEXT NOT NULL,
            min_experience_years INTEGER NOT NULL,
            required_education TEXT NOT NULL,
            description TEXT NOT NULL,
            salary_range TEXT,
            status TEXT DEFAULT 'OPEN'
        )
    """)

    cursor.execute(
        """INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            "JOB-TEST-001",
            "Test Developer",
            "Engineering",
            json.dumps(["python", "javascript", "sql"]),
            json.dumps(["docker", "kubernetes"]),
            2,
            "Bachelor's degree",
            "A test job posting",
            "LKR 500,000",
            "OPEN",
        ),
    )

    conn.commit()
    conn.close()
    return db_path


@pytest.fixture
def sample_pdf_resume(tmp_dir) -> str:
    """Create a simple test PDF resume."""
    try:
        from fpdf import FPDF
    except ImportError:
        pytest.skip("fpdf2 not installed")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Test Candidate", ln=True, align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "test@email.com | +94 77 000 0000", ln=True, align="C")
    pdf.ln(5)
    pdf.cell(0, 8, "SKILLS: Python, JavaScript, SQL, Docker", ln=True)
    pdf.cell(0, 8, "EXPERIENCE: 3 years as Software Engineer at TestCo", ln=True)
    pdf.cell(0, 8, "EDUCATION: BSc Computer Science - University of Colombo (2021)", ln=True)

    path: str = os.path.join(tmp_dir, "test_resume.pdf")
    pdf.output(path)
    return path
