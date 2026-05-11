"""OpenAI API integration for structured agent reasoning."""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

try:
    from openai import APIError, AsyncOpenAI
except ImportError:  # pragma: no cover - dependency is installed in runtime env
    APIError = Exception  # type: ignore[assignment]
    AsyncOpenAI = None  # type: ignore[assignment]

from app.core.config.settings import Settings
from app.utils.exceptions import AIServiceException

logger = logging.getLogger(__name__)


class OpenAIService:
    """Thin wrapper around OpenAI structured JSON responses."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = self._build_client(settings)

    async def generate_json(
        self,
        *,
        instructions: str,
        payload: dict[str, Any],
        schema_name: str,
        schema: dict[str, Any],
        model: str | None = None,
    ) -> dict[str, Any]:
        """Generate and parse a JSON object using the OpenAI API."""
        if self._client is None:
            raise AIServiceException("The openai package is not installed.")
        if not self._settings.openai_api_key:
            raise AIServiceException(
                "OPENAI_API_KEY is not configured.",
                status_code=503,
            )

        input_text = json.dumps(payload, indent=2, ensure_ascii=False)
        selected_model = model or self._settings.openai_model

        try:
            response = await self._client.responses.create(
                model=selected_model,
                instructions=instructions,
                input=input_text,
                max_output_tokens=self._settings.openai_max_output_tokens,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": schema,
                        "strict": True,
                    }
                },
            )
            raw_text = self._extract_response_text(response)
        except TypeError:
            raw_text = await self._generate_json_with_chat_fallback(
                instructions=instructions,
                input_text=input_text,
                schema_name=schema_name,
                schema=schema,
                model=selected_model,
            )
        except APIError as exc:
            logger.exception("OpenAI API error")
            raise AIServiceException("OpenAI API request failed.") from exc

        return self._parse_json(raw_text)

    async def stream_chat_text(
        self,
        *,
        system: str,
        user: str,
        model: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream assistant text deltas from the Chat Completions API."""
        if self._client is None:
            raise AIServiceException("The openai package is not installed.")
        if not self._settings.openai_api_key:
            raise AIServiceException(
                "OPENAI_API_KEY is not configured.",
                status_code=503,
            )

        selected_model = model or self._settings.openai_model

        try:
            stream = await self._client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                stream=True,
            )
        except APIError as exc:
            logger.exception("OpenAI streaming API error")
            raise AIServiceException("OpenAI API request failed.") from exc

        async for chunk in stream:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                continue
            delta = getattr(choices[0], "delta", None)
            if delta is None:
                continue
            piece = getattr(delta, "content", None)
            if piece:
                yield str(piece)

    def _build_client(self, settings: Settings):  # type: ignore[no-untyped-def]
        if AsyncOpenAI is None:
            return None
        return AsyncOpenAI(
            api_key=settings.openai_api_key or None,
            timeout=settings.request_timeout_seconds,
        )

    async def _generate_json_with_chat_fallback(
        self,
        *,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
        model: str,
    ) -> str:
        """Fallback for older SDKs where Responses structured output differs."""
        assert self._client is not None
        response = await self._client.chat.completions.create(
            model=model,
            messages=[
                {"role": "developer", "content": instructions},
                {
                    "role": "user",
                    "content": (
                        "Return JSON matching this schema named "
                        f"{schema_name}: {json.dumps(schema)}\n\n{input_text}"
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        return response.choices[0].message.content or "{}"

    def _extract_response_text(self, response: Any) -> str:
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text)

        output = getattr(response, "output", None) or []
        parts: list[str] = []
        for item in output:
            content_items = getattr(item, "content", []) or []
            for content in content_items:
                text = getattr(content, "text", None)
                if text:
                    parts.append(str(text))
        return "\n".join(parts)

    def _parse_json(self, raw_text: str) -> dict[str, Any]:
        text = raw_text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise AIServiceException("OpenAI returned invalid JSON.") from exc
        if not isinstance(payload, dict):
            raise AIServiceException("OpenAI returned a non-object JSON payload.")
        return payload
