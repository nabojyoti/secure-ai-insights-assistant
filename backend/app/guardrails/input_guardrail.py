import re
from dataclasses import dataclass

from app.core.exceptions import AppError
from app.guardrails.guardrails_ai_adapter import GuardrailsAIAdapter


class GuardrailViolation(AppError):
    status_code = 400
    code = "guardrail_violation"


class OutOfScopeQuestion(AppError):
    status_code = 422
    code = "out_of_scope"


@dataclass(frozen=True)
class InputGuardrailResult:
    sanitized_query: str
    flags: list[str]


class InputGuardrail:
    blocked_patterns = {
        "prompt_injection": re.compile(
            r"\b(ignore|bypass|override|disable)\b.{0,40}\b(instruction|guardrail|policy|system)\b",
            re.I,
        ),
        "secret_exfiltration": re.compile(r"\b(api[_ -]?key|password|secret|token|private key|\.env)\b", re.I),
        "unsafe_sql": re.compile(
            r"\b(drop|delete|update|insert|alter|create|truncate|grant|revoke)\b|--|/\*|\bunion\s+select\b",
            re.I,
        ),
        "filesystem_probe": re.compile(r"(\.\./|[a-zA-Z]:\\|/etc/|/var/|/home/|\\windows\\)", re.I),
    }

    external_domain_pattern = re.compile(
        r"\b(weather|temperature|forecast|rain|stock price|crypto|bitcoin|election|president|sports score|news|"
        r"capital of|recipe|medical|doctor|flight|train|traffic)\b",
        re.I,
    )

    allowed_domain_pattern = re.compile(
        r"\b(movie|movies|title|titles|genre|comedy|sci-fi|drama|sports|stellar run|dark orbit|last kingdom|"
        r"viewer|viewers|audience|segment|watch|views|completion|revenue|rating|review|sentiment|city|regional|"
        r"engagement|marketing|campaign|spend|roi|performance|performed|trend|trending|recommendation|"
        r"leadership|quarter|report|pdf|csv|sql|data|analytics|insight)\b",
        re.I,
    )

    def __init__(self) -> None:
        self.guardrails_ai = GuardrailsAIAdapter()

    def validate(self, query: str) -> InputGuardrailResult:
        sanitized = re.sub(r"\s+", " ", query).strip()
        if len(sanitized) < 3:
            raise GuardrailViolation("Question is too short")
        if len(sanitized) > 1000:
            raise GuardrailViolation("Question exceeds the allowed length")

        flags = [name for name, pattern in self.blocked_patterns.items() if pattern.search(sanitized)]
        if flags:
            raise GuardrailViolation(
                "Question was blocked by input guardrails because it requested unsafe or unauthorized access"
            )

        if self.external_domain_pattern.search(sanitized) or not self.allowed_domain_pattern.search(sanitized):
            raise OutOfScopeQuestion(
                "This assistant only answers internal entertainment analytics questions using approved SQL, CSV, and PDF sources"
            )

        return InputGuardrailResult(sanitized_query=sanitized, flags=flags)
