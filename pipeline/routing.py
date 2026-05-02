"""
Routing Functions
=================
Conditional routing logic for the LangGraph pipeline.
These functions determine the next agent to execute based on
the current pipeline state.

The routing creates a Coordinator-Worker-Delegator pattern:
    - After extraction: Did we get valid data? → Continue or fail
    - After matching: Any shortlisted candidates? → Assess or summarize
    - After assessment: Any passed candidates? → Interview or summarize
"""

from state.pipeline_state import PipelineState


def route_after_extraction(state: PipelineState) -> str:
    """Route after the Document Extractor agent completes.

    Decision logic:
        - If we have at least one candidate profile → proceed to matching
        - If extraction failed for all documents → go to summary (end)

    Args:
        state: Current pipeline state after document extraction.

    Returns:
        Next node name: "candidate_matcher" or "generate_summary"
    """
    candidate_profiles: list = state.get("candidate_profiles", [])
    job_vacancies: list = state.get("job_vacancies", [])

    if candidate_profiles:
        # We have candidates to match — proceed
        return "candidate_matcher"

    # No candidates extracted — check if we at least have job vacancies
    # (edge case: recruiter only uploaded flyers)
    if job_vacancies and not candidate_profiles:
        return "generate_summary"

    # Nothing extracted — fail gracefully
    return "generate_summary"


def route_after_matching(state: PipelineState) -> str:
    """Route after the Candidate Matcher agent completes.

    Decision logic:
        - If any candidates scored ≥ 60% (shortlisted) → proceed to assessment
        - If all candidates rejected → go to summary (end early)

    Args:
        state: Current pipeline state after candidate matching.

    Returns:
        Next node name: "assessment_coordinator" or "generate_summary"
    """
    shortlisted: list = state.get("shortlisted_candidates", [])

    if shortlisted:
        return "assessment_coordinator"

    # All candidates rejected — no point in assessment
    return "generate_summary"


def route_after_assessment(state: PipelineState) -> str:
    """Route after the Assessment Coordinator agent completes.

    Decision logic:
        - If any candidates passed or borderline → proceed to interview guide
        - If all candidates failed assessment → go to summary (end)

    Args:
        state: Current pipeline state after assessments.

    Returns:
        Next node name: "interview_strategist" or "generate_summary"
    """
    assessment_results: list = state.get("assessment_results", [])
    shortlisted: list = state.get("shortlisted_candidates", [])

    # If we have assessment results with PASS or BORDERLINE → continue
    for result in assessment_results:
        if result.get("pass_status") in ("PASS", "BORDERLINE"):
            return "interview_strategist"

    # If assessment results exist but all failed
    if assessment_results:
        return "generate_summary"

    # If no assessment results but we have shortlisted candidates
    # (assessment might have been skipped), still generate interview guides
    if shortlisted:
        return "interview_strategist"

    return "generate_summary"
