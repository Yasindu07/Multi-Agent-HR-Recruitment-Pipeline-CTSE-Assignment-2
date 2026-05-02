"""
Agent Tracer — LLMOps / AgentOps Observability
===============================================
Structured logging and tracing for the entire agent pipeline.
Records every agent invocation with inputs, tool calls, LLM calls,
outputs, and timing — all in structured JSONL format for easy analysis.

Features:
    - Structured JSON Lines logging (machine-parseable)
    - PII auto-redaction (phone, email, NIC, address)
    - Execution timing per agent
    - Console output for real-time monitoring
    - Separate log file per pipeline run
"""

import logging
import json
import os
import re
from datetime import datetime
from typing import Any, Optional


class AgentTracer:
    """Structured logging and tracing for agent execution.

    Records every agent invocation with:
    - Agent name and timestamp
    - Input data summary (sanitized to remove PII)
    - Tool calls and their results
    - LLM prompts and responses
    - Execution time and status

    Args:
        log_dir: Directory to store log files. Created if not exists.
        run_id: Optional unique identifier for this pipeline run.
    """

    # PII patterns to redact
    PII_PATTERNS: dict[str, str] = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\+?\d[\d\s\-()]{8,}\d",
        "nic": r"\d{9}[VvXx]|\d{12}",
    }

    SENSITIVE_KEYS: set[str] = {
        "phone", "email", "address", "nic", "salary",
        "date_of_birth", "dob", "national_id", "ssn"
    }

    def __init__(self, log_dir: str = "logs", run_id: Optional[str] = None) -> None:
        """Initialize the AgentTracer.

        Args:
            log_dir: Directory to store log files.
            run_id: Optional unique run identifier. Auto-generated if not provided.
        """
        self.log_dir: str = log_dir
        self.run_id: str = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time: datetime = datetime.now()

        os.makedirs(log_dir, exist_ok=True)

        self.log_file: str = os.path.join(log_dir, f"pipeline_trace_{self.run_id}.jsonl")

        # Set up logger
        self.logger: logging.Logger = logging.getLogger(f"AgentTracer_{self.run_id}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers = []  # Clear existing handlers

        # File handler — structured JSONL
        file_handler: logging.FileHandler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(file_handler)

        # Console handler — human-readable
        console_handler: logging.StreamHandler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                "\033[90m%(asctime)s\033[0m [\033[1m%(levelname)s\033[0m] %(message)s",
                datefmt="%H:%M:%S"
            )
        )
        self.logger.addHandler(console_handler)

        # Log pipeline start
        self._log_event({
            "event": "PIPELINE_START",
            "run_id": self.run_id,
            "timestamp": self.start_time.isoformat(),
        })

    def log_agent_start(self, agent_name: str, input_data: dict[str, Any]) -> None:
        """Log the start of an agent's execution.

        Args:
            agent_name: Name of the agent being started.
            input_data: The input state data for this agent.
        """
        entry: dict[str, Any] = {
            "event": "AGENT_START",
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "input_keys": list(input_data.keys()),
            "input_summary": self._summarize(input_data),
        }
        self._log_event(entry)
        self.logger.info(f"🚀 Agent [{agent_name}] STARTED — Input keys: {list(input_data.keys())}")

    def log_tool_call(
        self,
        agent_name: str,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_output: Any,
        duration_seconds: float = 0.0,
    ) -> None:
        """Log a tool invocation by an agent.

        Args:
            agent_name: Name of the agent calling the tool.
            tool_name: Name of the tool being called.
            tool_input: The input parameters passed to the tool.
            tool_output: The output returned by the tool.
            duration_seconds: Time taken for the tool call.
        """
        entry: dict[str, Any] = {
            "event": "TOOL_CALL",
            "agent": agent_name,
            "tool": tool_name,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "input": self._sanitize(tool_input),
            "output_success": getattr(tool_output, "success", None),
            "output_summary": str(tool_output)[:500],
        }
        self._log_event(entry)
        success_icon: str = "✅" if getattr(tool_output, "success", True) else "❌"
        self.logger.info(
            f"  🔧 Tool [{tool_name}] called by [{agent_name}] "
            f"— {success_icon} ({duration_seconds:.2f}s)"
        )

    def log_llm_call(
        self,
        agent_name: str,
        model: str,
        prompt_preview: str = "",
        response_preview: str = "",
        duration_seconds: float = 0.0,
    ) -> None:
        """Log an LLM invocation.

        Args:
            agent_name: Name of the agent calling the LLM.
            model: The Ollama model name used.
            prompt_preview: First 200 chars of the prompt.
            response_preview: First 500 chars of the response.
            duration_seconds: Time taken for the LLM call.
        """
        entry: dict[str, Any] = {
            "event": "LLM_CALL",
            "agent": agent_name,
            "model": model,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "prompt_preview": self._redact_pii(prompt_preview[:200]),
            "response_preview": response_preview[:500],
        }
        self._log_event(entry)
        self.logger.info(
            f"  🤖 LLM [{model}] called by [{agent_name}] — ({duration_seconds:.2f}s)"
        )

    def log_agent_end(
        self,
        agent_name: str,
        status: str,
        output_summary: str,
        duration_seconds: float,
    ) -> None:
        """Log the completion of an agent's execution.

        Args:
            agent_name: Name of the agent that completed.
            status: Final status (SUCCESS, FAILED, SKIPPED).
            output_summary: Brief summary of what the agent produced.
            duration_seconds: Total execution time for the agent.
        """
        entry: dict[str, Any] = {
            "event": "AGENT_END",
            "agent": agent_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration_seconds, 3),
            "output_summary": output_summary[:500],
        }
        self._log_event(entry)

        status_icon: str = {"SUCCESS": "✅", "FAILED": "❌", "SKIPPED": "⏭️"}.get(status, "❓")
        self.logger.info(
            f"{status_icon} Agent [{agent_name}] {status} — "
            f"{output_summary[:100]} ({duration_seconds:.2f}s)"
        )

    def log_routing_decision(
        self, from_agent: str, to_agent: str, reason: str
    ) -> None:
        """Log a routing decision in the pipeline.

        Args:
            from_agent: The agent that just completed.
            to_agent: The next agent to execute (or END).
            reason: Why this routing decision was made.
        """
        entry: dict[str, Any] = {
            "event": "ROUTING_DECISION",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
        }
        self._log_event(entry)
        self.logger.info(f"  ➡️  Route: [{from_agent}] → [{to_agent}] — {reason}")

    def log_pipeline_end(self, status: str, total_candidates: int = 0) -> None:
        """Log the completion of the entire pipeline.

        Args:
            status: Final pipeline status (COMPLETED, FAILED).
            total_candidates: Number of candidates processed.
        """
        duration: float = (datetime.now() - self.start_time).total_seconds()
        entry: dict[str, Any] = {
            "event": "PIPELINE_END",
            "run_id": self.run_id,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "total_duration_seconds": round(duration, 2),
            "total_candidates_processed": total_candidates,
        }
        self._log_event(entry)
        self.logger.info(
            f"\n{'='*60}\n"
            f"🏁 Pipeline {status} — {total_candidates} candidates processed "
            f"in {duration:.2f}s\n"
            f"📄 Full trace log: {self.log_file}\n"
            f"{'='*60}"
        )

    def _log_event(self, entry: dict[str, Any]) -> None:
        """Write a structured JSON event to the log file."""
        try:
            self.logger.debug(json.dumps(entry, default=str))
        except (TypeError, ValueError):
            self.logger.debug(json.dumps({"event": "LOG_ERROR", "raw": str(entry)}))

    def _sanitize(self, data: dict[str, Any]) -> dict[str, Any]:
        """Remove PII from log data by redacting sensitive keys.

        Args:
            data: Dictionary that may contain PII fields.

        Returns:
            Sanitized dictionary with PII fields replaced by [REDACTED].
        """
        sanitized: dict[str, Any] = {}
        for key, value in data.items():
            if key.lower() in self.SENSITIVE_KEYS:
                sanitized[key] = "[REDACTED]"
            elif isinstance(value, str):
                sanitized[key] = self._redact_pii(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize(value)
            else:
                sanitized[key] = value
        return sanitized

    def _redact_pii(self, text: str) -> str:
        """Redact PII patterns from text.

        Args:
            text: Raw text that may contain PII.

        Returns:
            Text with PII patterns replaced by [REDACTED].
        """
        redacted: str = text
        for pii_type, pattern in self.PII_PATTERNS.items():
            redacted = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", redacted)
        return redacted

    def _summarize(self, data: dict[str, Any]) -> str:
        """Create a brief type-summary of input data.

        Args:
            data: Dictionary to summarize.

        Returns:
            JSON string showing key-type pairs.
        """
        summary: dict[str, str] = {}
        for key, value in data.items():
            if isinstance(value, list):
                summary[key] = f"list[{len(value)} items]"
            elif isinstance(value, dict):
                summary[key] = f"dict[{len(value)} keys]"
            else:
                summary[key] = type(value).__name__
        return json.dumps(summary)
