"""
HR Recruitment Pipeline — Main Entry Point
==========================================
Runs the complete Multi-Agent HR Recruitment Pipeline locally using
Ollama LLMs and LangGraph orchestration.

Usage:
    # Process sample data with default settings
    python main.py

    # Process specific resumes against a specific job
    python main.py --resumes data/sample_resumes/john_doe_fullstack.pdf --job-id JOB-001

    # Use a different Ollama model
    python main.py --model llama3:8b

    # Process job flyers too
    python main.py --flyers data/sample_flyers/flyer_senior_fullstack.pdf
"""

import argparse
import glob
import os
import sys
import uuid

from observability.tracer import AgentTracer
from pipeline.graph import build_pipeline


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="HR Recruitment Pipeline — Multi-Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with all sample data
  python main.py

  # Process specific resumes
  python main.py --resumes resume1.pdf resume2.pdf

  # Process against a specific job
  python main.py --job-id JOB-001

  # Use a different model
  python main.py --model phi3
        """,
    )

    parser.add_argument(
        "--resumes",
        nargs="*",
        help="Paths to resume PDF/DOCX files. If not specified, uses all files in data/sample_resumes/",
    )

    parser.add_argument(
        "--flyers",
        nargs="*",
        help="Paths to job flyer PDF files. If not specified, uses all files in data/sample_flyers/",
    )

    parser.add_argument(
        "--job-id",
        type=str,
        default=None,
        help="Target job ID from the database (e.g., JOB-001). If not specified, matches against all open jobs.",
    )

    parser.add_argument(
        "--model",
        type=str,
        default="llama3.2",
        help="Ollama model to use (default: llama3.2). Must be pulled locally first.",
    )

    parser.add_argument(
        "--temperature",
        type=float,
        default=0,
        help="LLM temperature (default: 0 for deterministic output).",
    )

    parser.add_argument(
        "--db-path",
        type=str,
        default="data/hr_jobs.db",
        help="Path to the SQLite job database (default: data/hr_jobs.db).",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the HR Recruitment Pipeline."""

    args: argparse.Namespace = parse_args()

    # ─── Banner ───────────────────────────────────────────────────────────────
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     🏢  HR RECRUITMENT PIPELINE — Multi-Agent System         ║
║         Powered by Ollama + LangGraph                        ║
║         100% Local • Zero Cloud • Privacy-First              ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # ─── Validate database ────────────────────────────────────────────────────
    if not os.path.exists(args.db_path):
        print("⚠️  Database not found. Running setup_db.py...")
        from setup_db import setup_database
        setup_database(args.db_path)

    # ─── Gather resume paths ─────────────────────────────────────────────────
    if args.resumes:
        resume_paths: list[str] = [os.path.abspath(r) for r in args.resumes]
    else:
        resume_dir: str = "data/sample_resumes"
        if os.path.exists(resume_dir):
            resume_paths = sorted(glob.glob(os.path.join(resume_dir, "*.pdf")))
            resume_paths += sorted(glob.glob(os.path.join(resume_dir, "*.docx")))
        else:
            print("⚠️  No sample resumes found. Run: python create_sample_data.py")
            resume_paths = []

    # ─── Gather flyer paths ──────────────────────────────────────────────────
    if args.flyers:
        flyer_paths: list[str] = [os.path.abspath(f) for f in args.flyers]
    else:
        flyer_dir: str = "data/sample_flyers"
        if os.path.exists(flyer_dir):
            flyer_paths = sorted(glob.glob(os.path.join(flyer_dir, "*.pdf")))
        else:
            flyer_paths = []

    # ─── Print configuration ─────────────────────────────────────────────────
    print(f"📋 Configuration:")
    print(f"   Model:       {args.model}")
    print(f"   Temperature: {args.temperature}")
    print(f"   Database:    {args.db_path}")
    print(f"   Resumes:     {len(resume_paths)} file(s)")
    for r in resume_paths:
        print(f"     • {os.path.basename(r)}")
    print(f"   Flyers:      {len(flyer_paths)} file(s)")
    for f in flyer_paths:
        print(f"     • {os.path.basename(f)}")
    if args.job_id:
        print(f"   Target Job:  {args.job_id}")
    print()

    if not resume_paths and not flyer_paths:
        print("❌ No input files provided. Please specify --resumes or --flyers, or run create_sample_data.py first.")
        sys.exit(1)

    # ─── Initialize tracer ────────────────────────────────────────────────────
    run_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    tracer: AgentTracer = AgentTracer(log_dir="logs", run_id=run_id)

    print(f"📊 Trace log: logs/pipeline_trace_{run_id}.jsonl\n")
    print("🚀 Starting pipeline...\n")

    # ─── Build and run pipeline ──────────────────────────────────────────────
    pipeline = build_pipeline(
        model_name=args.model,
        temperature=args.temperature,
        tracer=tracer,
    )

    # Create initial state
    initial_state: dict = {
        "resume_paths": resume_paths,
        "job_flyer_paths": flyer_paths,
        "target_job_id": args.job_id,
        "db_path": os.path.abspath(args.db_path),
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

    # Run the pipeline with a thread config for checkpointing
    config: dict = {
        "configurable": {"thread_id": f"hr-pipeline-{run_id}"}
    }

    try:
        final_state = pipeline.invoke(initial_state, config=config)

        # Log pipeline completion
        tracer.log_pipeline_end(
            status="COMPLETED",
            total_candidates=len(final_state.get("candidate_profiles", [])),
        )

        # Print output file locations
        print("\n📁 Generated Files:")
        for guide in final_state.get("interview_guides", []):
            print(f"   📄 {guide.get('file_path', 'unknown')}")
        if final_state.get("comparison_report"):
            print(f"   📊 {final_state['comparison_report']}")
        for assessment in final_state.get("assessments", []):
            print(f"   📝 {assessment.get('assessment_file_path', 'unknown')}")

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        tracer.log_pipeline_end(status="INTERRUPTED")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {type(e).__name__}: {str(e)}")
        tracer.log_pipeline_end(status="FAILED")
        raise


# Required import for the run_id timestamp
from datetime import datetime


if __name__ == "__main__":
    main()
