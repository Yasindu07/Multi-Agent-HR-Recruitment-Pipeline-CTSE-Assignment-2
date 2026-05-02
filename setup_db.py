"""
Database Setup Script
=====================
Creates the local SQLite database with sample job vacancies.
Run this once before starting the pipeline.

Usage:
    python setup_db.py
"""

import json
import os
import sqlite3


def setup_database(db_path: str = "data/hr_jobs.db") -> None:
    """Create the SQLite database and populate it with sample job postings.

    Args:
        db_path: Path to the SQLite database file. Parent directory is
                 created automatically if it doesn't exist.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn: sqlite3.Connection = sqlite3.connect(db_path)
    cursor: sqlite3.Cursor = conn.cursor()

    # Create jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            required_skills TEXT NOT NULL,
            preferred_skills TEXT NOT NULL,
            min_experience_years INTEGER NOT NULL,
            required_education TEXT NOT NULL,
            description TEXT NOT NULL,
            salary_range TEXT,
            status TEXT DEFAULT 'OPEN',
            source_file TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Create candidates table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            years_of_experience INTEGER DEFAULT 0,
            skills TEXT DEFAULT '[]',
            education TEXT DEFAULT '[]',
            work_experience TEXT DEFAULT '[]',
            github_url TEXT,
            certifications TEXT DEFAULT '[]',
            source_file TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Create pipeline_runs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            candidate_ids TEXT DEFAULT '[]',
            model TEXT DEFAULT 'llama3.2',
            status TEXT DEFAULT 'RUNNING',
            results TEXT DEFAULT '{}',
            created_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    """)

    # Create match_results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS match_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            candidate_id INTEGER,
            job_id TEXT,
            match_score INTEGER DEFAULT 0,
            recommendation TEXT,
            skill_match TEXT DEFAULT '{}',
            assessment_score REAL DEFAULT 0,
            assessment_status TEXT,
            interview_guide_path TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (job_id) REFERENCES jobs(job_id)
        )
    """)

    # Sample job postings
    sample_jobs: list[dict] = [
        {
            "job_id": "JOB-001",
            "title": "Senior Full-Stack Developer",
            "department": "Engineering",
            "required_skills": json.dumps([
                "python", "reactjs", "postgresql", "docker", "git", "rest-api"
            ]),
            "preferred_skills": json.dumps([
                "kubernetes", "typescript", "graphql", "cicd", "aws"
            ]),
            "min_experience_years": 4,
            "required_education": "Bachelor's in Computer Science or related field",
            "description": (
                "We are looking for a Senior Full-Stack Developer to design, build, and "
                "maintain scalable web applications. The ideal candidate has strong experience "
                "with Python backends and React frontends, and is comfortable with containerized "
                "deployments. You will lead feature development, mentor junior developers, and "
                "contribute to architectural decisions."
            ),
            "salary_range": "LKR 800,000 - 1,200,000 per annum",
            "status": "OPEN",
        },
        {
            "job_id": "JOB-002",
            "title": "Data Scientist",
            "department": "Analytics",
            "required_skills": json.dumps([
                "python", "pandas", "scikit-learn", "sql", "statistics", "data-visualization"
            ]),
            "preferred_skills": json.dumps([
                "tensorflow", "spark", "tableau", "r", "deep-learning"
            ]),
            "min_experience_years": 3,
            "required_education": "Bachelor's in Computer Science, Statistics, or Mathematics",
            "description": (
                "Join our Analytics team as a Data Scientist to analyze large datasets, "
                "build predictive models, and deliver actionable insights. You will work "
                "closely with stakeholders to understand business problems and translate "
                "them into data-driven solutions."
            ),
            "salary_range": "LKR 700,000 - 1,000,000 per annum",
            "status": "OPEN",
        },
        {
            "job_id": "JOB-003",
            "title": "DevOps Engineer",
            "department": "Infrastructure",
            "required_skills": json.dumps([
                "docker", "kubernetes", "terraform", "linux", "cicd", "bash"
            ]),
            "preferred_skills": json.dumps([
                "aws", "ansible", "prometheus", "grafana", "python"
            ]),
            "min_experience_years": 3,
            "required_education": "Bachelor's in Computer Science or related field",
            "description": (
                "We need a DevOps Engineer to manage our cloud infrastructure, "
                "automate deployment pipelines, and ensure system reliability. "
                "You will implement CI/CD workflows, manage container orchestration, "
                "and monitor production systems."
            ),
            "salary_range": "LKR 750,000 - 1,100,000 per annum",
            "status": "OPEN",
        },
        {
            "job_id": "JOB-004",
            "title": "Junior Mobile Developer",
            "department": "Mobile",
            "required_skills": json.dumps([
                "flutter", "dart", "firebase", "git", "rest-api"
            ]),
            "preferred_skills": json.dumps([
                "kotlin", "swift", "figma", "sqlite", "agile"
            ]),
            "min_experience_years": 1,
            "required_education": "Bachelor's in Computer Science or related field",
            "description": (
                "We're looking for a Junior Mobile Developer to help build "
                "cross-platform mobile applications using Flutter. You will work "
                "with our design team to implement pixel-perfect UIs and integrate "
                "with backend APIs."
            ),
            "salary_range": "LKR 400,000 - 600,000 per annum",
            "status": "OPEN",
        },
        {
            "job_id": "JOB-005",
            "title": "Machine Learning Engineer",
            "department": "AI Research",
            "required_skills": json.dumps([
                "python", "tensorflow", "pytorch", "machine-learning", "deep-learning",
                "mathematics"
            ]),
            "preferred_skills": json.dumps([
                "mlops", "docker", "kubernetes", "spark", "nlp"
            ]),
            "min_experience_years": 3,
            "required_education": "Bachelor's or Master's in Computer Science, AI, or related field",
            "description": (
                "Join our AI Research team to develop and deploy machine learning models. "
                "You will work on NLP, computer vision, and recommendation systems, "
                "collaborating with researchers and engineers to bring models to production."
            ),
            "salary_range": "LKR 900,000 - 1,400,000 per annum",
            "status": "OPEN",
        },
    ]

    for job in sample_jobs:
        cursor.execute(
            """
            INSERT OR REPLACE INTO jobs 
            (job_id, title, department, required_skills, preferred_skills, 
             min_experience_years, required_education, description, salary_range, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job["job_id"],
                job["title"],
                job["department"],
                job["required_skills"],
                job["preferred_skills"],
                job["min_experience_years"],
                job["required_education"],
                job["description"],
                job["salary_range"],
                job["status"],
            ),
        )

    conn.commit()
    conn.close()
    print(f"✅ Database created with {len(sample_jobs)} job postings at {db_path}")
    print("\nJob Listings:")
    for job in sample_jobs:
        skills: list = json.loads(job["required_skills"])
        print(f"  [{job['job_id']}] {job['title']} — {job['department']} "
              f"({len(skills)} required skills, {job['min_experience_years']}+ years)")


if __name__ == "__main__":
    setup_database()
