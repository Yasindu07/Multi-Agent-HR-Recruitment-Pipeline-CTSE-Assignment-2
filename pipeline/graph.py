"""
LangGraph Pipeline Definition
==============================
Builds the HR Recruitment Pipeline as a LangGraph state machine.

Graph Structure:
    document_extractor → [conditional] → candidate_matcher → [conditional] → 
    assessment_coordinator → [conditional] → interview_strategist → generate_summary → END

Each agent is a node. Conditional edges implement the Coordinator pattern.
"""

import json
import time
from typing import Any

from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state.pipeline_state import PipelineState
from agents.document_extractor import document_extractor_node
from agents.candidate_matcher import candidate_matcher_node
from agents.assessment_coordinator import assessment_coordinator_node
from agents.interview_strategist import interview_strategist_node
from pipeline.routing import (
    route_after_extraction,
    route_after_matching,
    route_after_assessment,
)
from observability.tracer import AgentTracer


def _create_agent_wrapper(agent_fn, llm: ChatOllama, tracer: AgentTracer):
    """Create a wrapper that injects LLM and tracer into agent node functions.

    Args:
        agent_fn: The agent node function to wrap.
        llm: The shared ChatOllama instance.
        tracer: The shared AgentTracer instance.

    Returns:
        A wrapper function compatible with LangGraph node signature.
    """
    def wrapper(state: PipelineState) -> dict[str, Any]:
        return agent_fn(state, llm=llm, tracer=tracer)
    return wrapper


def generate_summary_node(state: PipelineState) -> dict[str, Any]:
    """Final summary node — aggregates pipeline results.

    This node runs at the end of the pipeline (or early if routing
    short-circuits) and produces a final summary of all processing.

    Args:
        state: Final pipeline state.

    Returns:
        dict: Updated state with pipeline_status and final log entries.
    """
    log_entries: list[str] = list(state.get("processing_log", []))
    
    candidates: int = len(state.get("candidate_profiles", []))
    vacancies: int = len(state.get("job_vacancies", []))
    shortlisted: int = len(state.get("shortlisted_candidates", []))
    rejected: int = len(state.get("rejected_candidates", []))
    assessed: int = len(state.get("assessment_results", []))
    guides: int = len(state.get("interview_guides", []))
    errors: int = len(state.get("parse_errors", []))

    summary: str = f"""
╔══════════════════════════════════════════════════════════════╗
║           HR RECRUITMENT PIPELINE — FINAL SUMMARY           ║
╠══════════════════════════════════════════════════════════════╣
║  Documents Processed                                        ║
║    • Candidate CVs extracted:    {candidates:<30}║
║    • Job vacancies extracted:    {vacancies:<30}║
║    • Parsing errors:             {errors:<30}║
╠══════════════════════════════════════════════════════════════╣
║  Matching Results                                           ║
║    • Shortlisted candidates:     {shortlisted:<30}║
║    • Rejected candidates:        {rejected:<30}║
╠══════════════════════════════════════════════════════════════╣
║  Assessment Results                                         ║
║    • Assessments completed:      {assessed:<30}║
╠══════════════════════════════════════════════════════════════╣
║  Interview Guides                                           ║
║    • Guides generated:           {guides:<30}║
╚══════════════════════════════════════════════════════════════╝"""

    log_entries.append(summary)
    print(summary)

    # Print interview guide paths
    for guide in state.get("interview_guides", []):
        path: str = guide.get("file_path", "")
        name: str = guide.get("candidate_name", "")
        rec: str = guide.get("recommendation", "")
        print(f"  📄 {name}: {path} [{rec}]")

    # Print comparison report path
    comp_report: str = state.get("comparison_report", "")
    if comp_report:
        print(f"  📊 Comparison Report: {comp_report}")

    return {
        "pipeline_status": "COMPLETED",
        "current_agent": "summary",
        "processing_log": log_entries,
    }


def build_pipeline(
    model_name: str = "llama3.2",
    temperature: float = 0,
    tracer: AgentTracer = None,
) -> Any:
    """Build the HR Recruitment Pipeline as a compiled LangGraph state machine.

    Creates a graph with 4 agent nodes + 1 summary node, connected by
    conditional edges that implement the Coordinator routing pattern.

    Args:
        model_name: The Ollama model to use (default: llama3.2).
        temperature: LLM temperature (default: 0 for deterministic output).
        tracer: AgentTracer instance for observability logging.

    Returns:
        Compiled LangGraph workflow ready for invocation.
    """
    # Create shared LLM instance
    llm: ChatOllama = ChatOllama(
        model=model_name,
        temperature=temperature,
        format="json",
    )

    # For Agent 4,  we need non-JSON format (outputs Markdown)
    llm_markdown: ChatOllama = ChatOllama(
        model=model_name,
        temperature=0.3,
    )

    # Initialize tracer if not provided
    if tracer is None:
        tracer = AgentTracer()

    # Build the state graph
    workflow: StateGraph = StateGraph(PipelineState)

    # ─── Add Agent Nodes ─────────────────────────────────────────────────────
    workflow.add_node(
        "document_extractor",
        _create_agent_wrapper(document_extractor_node, llm, tracer),
    )
    workflow.add_node(
        "candidate_matcher",
        _create_agent_wrapper(candidate_matcher_node, llm, tracer),
    )
    workflow.add_node(
        "assessment_coordinator",
        _create_agent_wrapper(assessment_coordinator_node, llm, tracer),
    )
    workflow.add_node(
        "interview_strategist",
        _create_agent_wrapper(interview_strategist_node, llm_markdown, tracer),
    )
    workflow.add_node("generate_summary", generate_summary_node)

    # ─── Set Entry Point ─────────────────────────────────────────────────────
    workflow.set_entry_point("document_extractor")

    # ─── Define Conditional Edges ─────────────────────────────────────────────
    workflow.add_conditional_edges(
        "document_extractor",
        route_after_extraction,
        {
            "candidate_matcher": "candidate_matcher",
            "generate_summary": "generate_summary",
        },
    )

    workflow.add_conditional_edges(
        "candidate_matcher",
        route_after_matching,
        {
            "assessment_coordinator": "assessment_coordinator",
            "generate_summary": "generate_summary",
        },
    )

    workflow.add_conditional_edges(
        "assessment_coordinator",
        route_after_assessment,
        {
            "interview_strategist": "interview_strategist",
            "generate_summary": "generate_summary",
        },
    )

    # ─── Define Normal Edges ──────────────────────────────────────────────────
    workflow.add_edge("interview_strategist", "generate_summary")
    workflow.add_edge("generate_summary", END)

    # ─── Compile with Checkpointing ──────────────────────────────────────────
    checkpointer: MemorySaver = MemorySaver()
    compiled = workflow.compile(checkpointer=checkpointer)

    return compiled
