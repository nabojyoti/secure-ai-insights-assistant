import re
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import AppError
from app.guardrails.guardrails_ai_adapter import GuardrailsAIAdapter


class OutputGuardrailError(AppError):
    status_code = 500
    code = "output_guardrail_error"


@dataclass(frozen=True)
class OutputGuardrailResult:
    response: dict[str, Any]
    flags: list[str]


class OutputGuardrail:
    secret_like = re.compile(
        r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
        re.I,
    )

    required_keys = {"answer", "sources", "metrics", "recommendations", "trace"}

    def __init__(self) -> None:
        self.guardrails_ai = GuardrailsAIAdapter()

    def validate(self, response: dict[str, Any]) -> OutputGuardrailResult:
        missing = self.required_keys - set(response)
        if missing:
            raise OutputGuardrailError(f"Response is missing required fields: {', '.join(sorted(missing))}")

        flags: list[str] = []
        answer = str(response.get("answer", ""))
        if self.secret_like.search(answer):
            flags.append("secret_like_content")
            response["answer"] = self.secret_like.sub("[REDACTED]", answer)

        trace = response.get("trace") or {}
        tools_used = trace.get("tools_used") or []
        if not tools_used:
            raise OutputGuardrailError("Response must include the approved tools used")

        if not isinstance(response.get("sources"), list):
            raise OutputGuardrailError("Response sources must be a list")

        response["guardrails"] = {
            "input": "passed",
            "output": "passed",
            "engine": self.guardrails_ai.engine_name,
            "flags": flags,
        }
        return OutputGuardrailResult(response=response, flags=flags)
