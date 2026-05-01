class GuardrailsAIAdapter:
    """Tiny adapter so guardrails-ai is an optional enforcement layer, not a hard security dependency."""

    def __init__(self) -> None:
        try:
            import guardrails  # noqa: F401

            self.available = True
        except Exception:
            self.available = False

    @property
    def engine_name(self) -> str:
        return "guardrails-ai" if self.available else "deterministic-fallback"
