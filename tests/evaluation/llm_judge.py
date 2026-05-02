"""
LLM-as-a-Judge Evaluator
=========================
Uses a local Ollama LLM to evaluate agent outputs for accuracy,
completeness, and quality. This implements the "LLM-as-a-Judge"
testing methodology required by the assignment.

Usage:
    from tests.evaluation.llm_judge import LLMJudge
    
    judge = LLMJudge(model="llama3.2")
    score = judge.evaluate(
        task="resume_extraction",
        prediction=agent_output,
        ground_truth=expected_output
    )
"""

import json
from typing import Optional

from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage


class LLMJudge:
    """LLM-as-a-Judge evaluator for agent output quality.

    Uses a local Ollama model to assess whether an agent's output
    is accurate, complete, and free from hallucinations.

    Args:
        model: Ollama model name to use as the judge.
    """

    JUDGE_PROMPT: str = """You are an impartial Quality Evaluator for an HR Recruitment Pipeline system.
Your job is to evaluate whether an agent's output meets the expected criteria.

You will receive:
1. TASK: What the agent was supposed to do
2. PREDICTION: What the agent actually produced
3. GROUND_TRUTH: What the correct/expected output should be (if available)
4. CRITERIA: Specific evaluation criteria

Score the output on a scale of 0.0 to 1.0 for each criterion.
Return ONLY valid JSON:
{
    "overall_score": float (0.0 to 1.0),
    "criteria_scores": {
        "criterion_name": float
    },
    "issues": ["list of specific issues found"],
    "verdict": "PASS or FAIL"
}

A score >= 0.7 is PASS, < 0.7 is FAIL."""

    def __init__(self, model: str = "llama3.2") -> None:
        """Initialize the LLM Judge.

        Args:
            model: Name of the Ollama model to use.
        """
        self.llm: ChatOllama = ChatOllama(
            model=model,
            temperature=0,
            format="json",
        )

    def evaluate(
        self,
        task: str,
        prediction: str,
        ground_truth: Optional[str] = None,
        criteria: Optional[list[str]] = None,
    ) -> dict:
        """Evaluate an agent's output using the LLM judge.

        Args:
            task: Description of the task the agent performed.
            prediction: The agent's actual output.
            ground_truth: Expected/correct output (optional).
            criteria: List of evaluation criteria.

        Returns:
            dict: Evaluation results with scores and verdict.
        """
        if criteria is None:
            criteria = ["completeness", "accuracy", "no_hallucination", "format_correctness"]

        prompt: str = f"""TASK: {task}

PREDICTION (Agent Output):
{prediction[:2000]}

GROUND_TRUTH (Expected Output):
{ground_truth[:2000] if ground_truth else "Not provided"}

CRITERIA TO EVALUATE:
{json.dumps(criteria)}

Evaluate the prediction against the criteria and ground truth."""

        try:
            messages = [
                SystemMessage(content=self.JUDGE_PROMPT),
                HumanMessage(content=prompt),
            ]
            response = self.llm.invoke(messages)
            result: dict = json.loads(response.content)
            return result

        except (json.JSONDecodeError, Exception) as e:
            return {
                "overall_score": 0.0,
                "criteria_scores": {},
                "issues": [f"Judge evaluation failed: {str(e)}"],
                "verdict": "FAIL",
            }

    def evaluate_resume_extraction(
        self,
        extracted_profile: dict,
        original_resume_text: str,
    ) -> dict:
        """Specialized evaluation for resume extraction accuracy.

        Args:
            extracted_profile: The extracted profile JSON from Agent 1.
            original_resume_text: The raw resume text that was parsed.

        Returns:
            dict: Evaluation results.
        """
        return self.evaluate(
            task="Extract structured candidate profile from resume text. "
                 "All fields must come from the document. Missing fields should show NOT_FOUND.",
            prediction=json.dumps(extracted_profile, indent=2),
            ground_truth=original_resume_text,
            criteria=[
                "completeness - are all fields from the resume captured?",
                "accuracy - do extracted values match the resume exactly?",
                "no_hallucination - is there any fabricated information?",
                "skill_normalization - are skills lowercased consistently?",
                "not_found_usage - are missing fields marked as NOT_FOUND?",
            ],
        )

    def evaluate_match_report(
        self,
        match_report: dict,
        candidate_profile: dict,
        job_description: dict,
    ) -> dict:
        """Specialized evaluation for job matching accuracy.

        Args:
            match_report: The match result from Agent 2.
            candidate_profile: The candidate's extracted profile.
            job_description: The job requirements.

        Returns:
            dict: Evaluation results.
        """
        return self.evaluate(
            task="Compare candidate profile against job requirements and produce a scored match report. "
                 "Scoring must follow: skill(0.5) + experience(0.3) + education(0.2).",
            prediction=json.dumps(match_report, indent=2),
            ground_truth=json.dumps({
                "candidate": candidate_profile,
                "job": job_description,
            }, indent=2),
            criteria=[
                "score_accuracy - does the score follow the weighted formula?",
                "skill_matching - are matched/missing skills correctly identified?",
                "recommendation_consistency - does recommendation match the score?",
                "reasoning_quality - is the reasoning specific and data-driven?",
            ],
        )

    def evaluate_interview_guide(
        self,
        guide_content: str,
        candidate_name: str,
        missing_skills: list[str],
    ) -> dict:
        """Specialized evaluation for interview guide quality.

        Args:
            guide_content: The generated interview guide markdown.
            candidate_name: The candidate's name (for specificity check).
            missing_skills: Skills that should be probed in questions.

        Returns:
            dict: Evaluation results.
        """
        return self.evaluate(
            task="Generate a candidate-specific interview preparation guide with targeted questions. "
                 "Questions should reference the candidate's specific data, NOT be generic.",
            prediction=guide_content,
            ground_truth=json.dumps({
                "candidate_name": candidate_name,
                "missing_skills_to_probe": missing_skills,
            }),
            criteria=[
                "specificity - are questions specific to this candidate (not generic)?",
                "section_completeness - does it have all required sections?",
                "interviewer_guidance - do questions include 'What to look for' hints?",
                "professionalism - is the document professional and well-structured?",
                "recommendation_clarity - is the final recommendation clear?",
            ],
        )
