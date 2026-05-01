import json
from typing import Any

import httpx
from pydantic import BaseModel, Field
import time
from app.common_utils.logging_utils import logger
from app.core.config import get_settings


class SynthesizedAnswer(BaseModel):
    answer: str = Field(min_length=1, max_length=1600)
    recommendations: list[str] = Field(default_factory=list, max_length=5)
    confidence: str = Field(default="medium", pattern=r"^(low|medium|high)$")


class AnswerSynthesizer:
    def __init__(self) -> None:
        self.settings = get_settings()

    def synthesize(
        self,
        question: str,
        evidence: dict[str, Any],
        fallback_answer: str,
        fallback_recommendations: list[str],
    ) -> dict[str, Any]:
        if not self._enabled():
            logger.debug(f"🔄 Synthesizer: LLM disabled or config incomplete → using deterministic fallback")
            return self._fallback(fallback_answer, fallback_recommendations, "deterministic")

        try:
            logger.info(f"🌐 Synthesizer: Calling OpenAI API (model={self.settings.ai_model})")
            payload = self._call_openai(question, evidence)
            parsed = SynthesizedAnswer.model_validate(payload)
            logger.info(f"✅ Synthesizer: OpenAI response received | confidence={parsed.confidence}")
            return {
                "answer": parsed.answer,
                "recommendations": parsed.recommendations or fallback_recommendations,
                "confidence": parsed.confidence,
                "synthesis_engine": f"openai:{self.settings.ai_model}",
            }
        except Exception as e:
            logger.error(f"⚠️  Synthesizer: OpenAI call failed ({str(e)}) → falling back to deterministic")
            return self._fallback(fallback_answer, fallback_recommendations, "deterministic_fallback")

    def _enabled(self) -> bool:
        return (
            self.settings.enable_llm_synthesis
            and self.settings.ai_provider.lower() == "openai"
            and bool(self.settings.openai_api_key)
        )

    def _call_openai(self, question: str, evidence: dict[str, Any]) -> dict[str, Any]:
        system_prompt = (
            "You are an internal entertainment analytics assistant. "
            "Use only the supplied evidence. Do not invent facts. "
            "Return ONLY valid JSON with keys: answer, recommendations, confidence. "
            "No extra text."
        )

        user_prompt = json.dumps(
            {"question": question, "evidence": evidence}, ensure_ascii=False
        )

        for attempt in range(3):
            try:
                response = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.settings.ai_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0,
                    },
                    timeout=12,
                )

                response.raise_for_status()
                data = response.json()

                content = data["choices"][0]["message"]["content"]

                # 🛡️ Safety cleanup
                content = content.strip()

                if content.startswith("```"):
                    # remove markdown fences safely
                    content = content.strip("`")
                    if content.lower().startswith("json"):
                        content = content[4:].strip()

                return json.loads(content)

            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(1.5 * (attempt + 1))

    def _fallback(self, answer: str, recommendations: list[str], engine: str) -> dict[str, Any]:
        return {
            "answer": answer,
            "recommendations": recommendations,
            "confidence": "medium",
            "synthesis_engine": engine,
        }
