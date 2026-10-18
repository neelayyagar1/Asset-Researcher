"""Claude implementation of LLMProvider.

Model, effort, and cache TTL come from config/settings.yaml, never hardcoded
here (ARCHITECTURE.md §3, configuration over code). Adaptive thinking is left at
its default (on, for claude-opus-5) rather than configured explicitly; effort
is the tuning knob this project uses.
"""

from __future__ import annotations

from typing import TypeVar

import anthropic
from pydantic import BaseModel

from asset_researcher.config import Settings, require_secret
from asset_researcher.llm.errors import StructuredOutputError
from asset_researcher.llm.provider import Citation, CitedResponse, CitedSpan, Effort, LLMProvider
from asset_researcher.hosting.spend import Usage
from asset_researcher.llm.schema import to_structured_schema
from asset_researcher.sources.base import SourceDocument

T = TypeVar("T", bound=BaseModel)


class ClaudeProvider(LLMProvider):
    def __init__(self, settings: Settings) -> None:
        api_key = require_secret(settings.anthropic_api_key, "ANTHROPIC_API_KEY")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = settings.llm.model
        # Cumulative usage across this provider's lifetime, so the hosting
        # spend guard can charge measured cost rather than an estimate.
        self.usage = Usage()

    def _record_usage(self, response) -> None:
        usage = getattr(response, "usage", None)
        if usage is None:
            return
        self.usage = self.usage + Usage(
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
        )

    def complete_structured(
        self,
        *,
        system: str,
        user: str,
        output_model: type[T],
        effort: Effort,
        max_tokens: int,
    ) -> T:
        schema = to_structured_schema(output_model)
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_config={
                "format": {"type": "json_schema", "schema": schema},
                "effort": effort,
            },
        )

        self._record_usage(response)

        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None)
            raise StructuredOutputError(
                f"Model declined the request (category: {category})."
            )
        if response.stop_reason == "max_tokens":
            raise StructuredOutputError(
                f"Response truncated at max_tokens={max_tokens} before "
                f"completing, output_config.format guarantees valid JSON "
                f"only on a complete response. Raise max_tokens for this call."
            )

        text_blocks = [b for b in response.content if b.type == "text"]
        if not text_blocks:
            raise StructuredOutputError(
                f"No text content in response (stop_reason={response.stop_reason})."
            )
        try:
            return output_model.model_validate_json(text_blocks[0].text)
        except Exception as e:
            raise StructuredOutputError(
                f"Response did not validate against {output_model.__name__}: {e}"
            ) from e

    def complete_cited(
        self,
        *,
        system: str,
        documents: list[SourceDocument],
        user: str,
        effort: Effort,
        max_tokens: int,
    ) -> CitedResponse:
        content: list[dict] = [
            {
                "type": "document",
                "source": {"type": "text", "media_type": "text/plain", "data": doc.text},
                "title": doc.label,
                "citations": {"enabled": True},
            }
            for doc in documents
        ]
        content.append({"type": "text", "text": user})

        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": content}],
            output_config={"effort": effort},
        )

        self._record_usage(response)

        if response.stop_reason == "refusal":
            category = getattr(response.stop_details, "category", None)
            raise StructuredOutputError(
                f"Model declined the request (category: {category})."
            )

        spans: list[CitedSpan] = []
        for block in response.content:
            if block.type != "text":
                continue

            citations = []
            for raw in getattr(block, "citations", None) or []:
                # Location fields depend on the citation type: char_location
                # for plain-text documents (what this project sends),
                # page_location for PDFs. Reading them defensively means an
                # unexpected type degrades to "no offsets", which the
                # verifier reports as unverifiable, rather than raising.
                citations.append(
                    Citation(
                        cited_text=getattr(raw, "cited_text", "") or "",
                        document_index=getattr(raw, "document_index", -1),
                        document_title=getattr(raw, "document_title", None),
                        start_char_index=getattr(raw, "start_char_index", None),
                        end_char_index=getattr(raw, "end_char_index", None),
                    )
                )

            # Uncited spans are kept deliberately. Dropping them would make the
            # coverage check meaningless, an uncited assertion is precisely
            # what it exists to surface.
            spans.append(CitedSpan(text=block.text, citations=citations))

        return CitedResponse(spans=spans)
