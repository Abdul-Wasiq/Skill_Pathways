"""
AI Service Abstraction (spec §28).

The rest of the app should NEVER call an AI provider's SDK directly —
everything goes through AIService, so the provider/model can be swapped
via .env alone (AI_PROVIDER / AI_BASE_URL / AI_API_KEY / AI_MODEL)
without touching business logic.

Groq, OpenAI, and many other providers expose an OpenAI-compatible
`/chat/completions` endpoint, so a single small HTTP client covers all
of them.
"""
import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Raised when the AI provider call fails or returns unusable output."""


class AIService:
    def __init__(self):
        self.base_url = settings.AI_BASE_URL.rstrip("/")
        self.api_key = settings.AI_API_KEY
        self.model = settings.AI_MODEL

    def _check_configured(self) -> None:
        if not self.api_key or self.api_key == "YOUR_AI_API_KEY":
            raise AIServiceError(
                "AI provider is not configured. Set AI_API_KEY (and AI_MODEL) "
                "in backend/.env — see SETUP_REQUIRED.md."
            )

    async def complete_json(self, system_prompt: str, user_prompt: str,
                             temperature: float = 0.2, timeout: float = 30.0) -> dict:
        """
        Calls the chat completions endpoint asking for a strict JSON object
        response, and parses it. Raises AIServiceError on any failure —
        callers must handle this gracefully rather than crashing the request.
        """
        self._check_configured()
        payload = {
            "model": self.model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions", json=payload, headers=headers
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error("AI provider returned an error: %s", exc.response.text)
            raise AIServiceError("AI analysis failed. Please try again.") from exc
        except httpx.HTTPError as exc:
            logger.error("AI provider request failed: %s", exc)
            raise AIServiceError("AI analysis failed. Please try again.") from exc

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.error("Could not parse AI provider response: %s", exc)
            raise AIServiceError("AI analysis failed. Please try again.") from exc


ai_service = AIService()
