"""
Job Database Manager Tool — Student B
======================================
Manages the local SQLite database for job vacancies and candidate operations.
Supports CRUD operations: inserting new vacancies (from flyer extraction),
querying open positions, and fetching job requirements for matching.

This tool is the bridge between the agents and the persistent job data store.

Features:
    - SQLite connection with row_factory for dict-like access
    - Insert new job vacancies (from Agent 1's flyer extraction)
    - Query jobs by ID, department, skills, or status
    - Skill-based filtering with normalization
    - Structured error handling (never raises)
"""

import json
import os
import sqlite3
from typing import Optional

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Structured job description from the local database.

    Attributes:
        job_id: Unique identifier for the job posting.
        title: Job title.
        department: Department or team.
        required_skills: List of required technical skills.
        preferred_skills: List of nice-to-have skills.
        min_experience_years: Minimum years of experience required.
        required_education: Minimum education qualification.
        description: Full job description text.
        salary_range: Salary range if available.
        status: Job posting status (OPEN, CLOSED, ON_HOLD).
    """

    job_id: str = Field(description="Unique identifier for the job posting")
    title: str = Field(description="Job title")
    department: str = Field(description="Department or team")
    required_skills: list[str] = Field(description="List of required technical skills")
    preferred_skills: list[str] = Field(description="List of nice-to-have skills")
    min_experience_years: int = Field(description="Minimum years of experience required")
    required_education: str = Field(description="Minimum education qualification")
    description: str = Field(description="Full job description text")
    salary_range: Optional[str] = Field(default=None, description="Salary range if available")
    status: str = Field(description="Job posting status: OPEN, CLOSED, ON_HOLD")


class JobQueryResult(BaseModel):
    """Result of querying the local job database.

    Attributes:
        success: Whether the query executed successfully.
        jobs: List of matching job descriptions.
        total_count: Total number of matching jobs.
        error_message: Error message if query failed.
    """

    success: bool = Field(description="Whether the query executed successfully")
    jobs: list[dict] = Field(default_factory=list, description="Matching job descriptions")
    total_count: int = Field(description="Total number of matching jobs")
    error_message: Optional[str] = Field(default=None, description="Error message if query failed")


class JobInsertResult(BaseModel):
    """Result of inserting a new job vacancy.

    Attributes:
        success: Whether the insert succeeded.
        job_id: ID of the inserted job.
        error_message: Error message if insert failed.
    """

    success: bool = Field(description="Whether the insert succeeded")
    job_id: str = Field(description="ID of the inserted job")
    error_message: Optional[str] = Field(default=None, description="Error message if insert failed")


@tool
def job_database_manager(
    db_path: str,
    action: str,
    job_id: Optional[str] = None,
    department: Optional[str] = None,
    skill_filter: Optional[str] = None,
    status_filter: str = "OPEN",
    job_data: Optional[str] = None,
) -> dict:
    """Manage the local SQLite job database — query and insert job vacancies.

    Supports two actions:
    - 'query': Fetch job descriptions matching given filters.
    - 'insert': Insert a new job vacancy from extracted flyer data.

    Args:
        db_path: Absolute path to the SQLite database file.
        action: The operation to perform — 'query' or 'insert'.
        job_id: Optional specific job ID to retrieve (for query action).
        department: Optional department name filter (for query action).
        skill_filter: Optional comma-separated skills to match (for query action).
        status_filter: Job status filter, defaults to 'OPEN'. Use 'ALL' for all statuses.
        job_data: JSON string of job vacancy data (for insert action).

    Returns:
        dict: Result containing success status, data, and any error messages.
    """
    if action == "query":
        skills: Optional[list[str]] = None
        if skill_filter:
            skills = [s.strip().lower() for s in skill_filter.split(",")]

        result: JobQueryResult = _query_jobs(
            db_path=db_path,
            job_id=job_id,
            department=department,
            skill_filter=skills,
            status_filter=status_filter,
        )
        return result.model_dump()

    elif action == "insert":
        if not job_data:
            return JobInsertResult(
                success=False,
                job_id="",
                error_message="job_data is required for insert action",
            ).model_dump()

        try:
            parsed_job: dict = json.loads(job_data)
        except json.JSONDecodeError as e:
            return JobInsertResult(
                success=False,
                job_id="",
                error_message=f"Invalid JSON in job_data: {str(e)}",
            ).model_dump()

        result_insert: JobInsertResult = _insert_job(db_path, parsed_job)
        return result_insert.model_dump()

    else:
        return {"success": False, "error_message": f"Unknown action: {action}. Use 'query' or 'insert'."}


def _query_jobs(
    db_path: str,
    job_id: Optional[str] = None,
    department: Optional[str] = None,
    skill_filter: Optional[list[str]] = None,
    status_filter: str = "OPEN",
) -> JobQueryResult:
    """Query the local SQLite database for job descriptions.

    Args:
        db_path: Path to the SQLite database.
        job_id: Optional specific job ID to retrieve.
        department: Optional department name filter (case-insensitive partial match).
        skill_filter: Optional list of skills to match against required_skills.
        status_filter: Job posting status filter.

    Returns:
        JobQueryResult: Structured query results.
    """
    try:
        if not os.path.exists(db_path):
            return JobQueryResult(
                success=False,
                jobs=[],
                total_count=0,
                error_message=f"Database file not found: {db_path}",
            )

        conn: sqlite3.Connection = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor: sqlite3.Cursor = conn.cursor()

        if job_id:
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        else:
            query: str = "SELECT * FROM jobs WHERE 1=1"
            params: list = []

            if status_filter and status_filter != "ALL":
                query += " AND status = ?"
                params.append(status_filter)

            if department:
                query += " AND LOWER(department) LIKE ?"
                params.append(f"%{department.lower()}%")

            cursor.execute(query, params)

        rows = cursor.fetchall()
        jobs: list[dict] = []

        for row in rows:
            required_skills: list[str] = json.loads(row["required_skills"])
            preferred_skills: list[str] = json.loads(row["preferred_skills"])

            # Apply skill filter if provided
            if skill_filter:
                normalized_required: list[str] = [s.lower() for s in required_skills]
                if not any(skill in normalized_required for skill in skill_filter):
                    continue

            job_dict: dict = {
                "job_id": row["job_id"],
                "title": row["title"],
                "department": row["department"],
                "required_skills": required_skills,
                "preferred_skills": preferred_skills,
                "min_experience_years": row["min_experience_years"],
                "required_education": row["required_education"],
                "description": row["description"],
                "salary_range": row["salary_range"] if row["salary_range"] else None,
                "status": row["status"],
            }
            jobs.append(job_dict)

        conn.close()

        return JobQueryResult(
            success=True,
            jobs=jobs,
            total_count=len(jobs),
        )

    except sqlite3.Error as e:
        return JobQueryResult(
            success=False,
            jobs=[],
            total_count=0,
            error_message=f"Database error: {type(e).__name__}: {str(e)}",
        )
    except Exception as e:
        return JobQueryResult(
            success=False,
            jobs=[],
            total_count=0,
            error_message=f"Unexpected error: {type(e).__name__}: {str(e)}",
        )


def _insert_job(db_path: str, job_data: dict) -> JobInsertResult:
    """Insert a new job vacancy into the database.

    Args:
        db_path: Path to the SQLite database.
        job_data: Dictionary containing job vacancy fields.

    Returns:
        JobInsertResult: Result of the insertion.
    """
    try:
        if not os.path.exists(db_path):
            return JobInsertResult(
                success=False,
                job_id="",
                error_message=f"Database file not found: {db_path}",
            )

        # Validate required fields
        required_fields: list[str] = ["job_id", "title", "department", "required_skills"]
        for field in required_fields:
            if field not in job_data:
                return JobInsertResult(
                    success=False,
                    job_id=job_data.get("job_id", ""),
                    error_message=f"Missing required field: {field}",
                )

        conn: sqlite3.Connection = sqlite3.connect(db_path)
        cursor: sqlite3.Cursor = conn.cursor()

        # Normalize skills to JSON arrays if they're lists
        required_skills: str = (
            json.dumps(job_data["required_skills"])
            if isinstance(job_data["required_skills"], list)
            else job_data["required_skills"]
        )
        preferred_skills: str = (
            json.dumps(job_data.get("preferred_skills", []))
            if isinstance(job_data.get("preferred_skills", []), list)
            else job_data.get("preferred_skills", "[]")
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO jobs 
            (job_id, title, department, required_skills, preferred_skills, 
             min_experience_years, required_education, description, salary_range, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                job_data["job_id"],
                job_data["title"],
                job_data["department"],
                required_skills,
                preferred_skills,
                job_data.get("min_experience_years", 0),
                job_data.get("required_education", "Not specified"),
                job_data.get("description", ""),
                job_data.get("salary_range", None),
                job_data.get("status", "OPEN"),
            ),
        )

        conn.commit()
        conn.close()

        return JobInsertResult(
            success=True,
            job_id=job_data["job_id"],
        )

    except sqlite3.Error as e:
        return JobInsertResult(
            success=False,
            job_id=job_data.get("job_id", ""),
            error_message=f"Database error: {type(e).__name__}: {str(e)}",
        )
    except Exception as e:
        return JobInsertResult(
            success=False,
            job_id=job_data.get("job_id", ""),
            error_message=f"Unexpected error: {type(e).__name__}: {str(e)}",
        )
