"""Pydantic model -> structured-output-compatible JSON Schema.

The Messages API's structured outputs feature supports a real but limited
subset of JSON Schema: no minLength/maxLength, no numeric constraints
(minimum, maximum, multipleOf), and every object must set
additionalProperties to false.
pydantic's default `model_json_schema()` includes constraints the API
doesn't support and omits additionalProperties, so this strips one and adds
the other recursively before the schema goes anywhere near a request.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

_UNSUPPORTED_KEYS = {"minLength", "maxLength", "minimum", "maximum", "multipleOf"}


def _clean(node: Any) -> Any:
    if isinstance(node, dict):
        cleaned = {k: _clean(v) for k, v in node.items() if k not in _UNSUPPORTED_KEYS}
        if cleaned.get("type") == "object" and "properties" in cleaned:
            cleaned.setdefault("additionalProperties", False)
            # Every property is required. pydantic omits any field carrying a
            # default, and a property absent from `required` is one the model
            # may silently skip: adding a section to the report schema then
            # produced an empty section rather than an error, because the
            # default filled in behind it.
            #
            # A field the model genuinely cannot answer should come back as an
            # empty string or list it chose to send, which is visible, rather
            # than as a default that looks like the model was never asked.
            cleaned["required"] = list(cleaned["properties"].keys())
        elif cleaned.get("type") == "object":
            cleaned.setdefault("additionalProperties", False)
        return cleaned
    if isinstance(node, list):
        return [_clean(v) for v in node]
    return node


def to_structured_schema(model: type[BaseModel]) -> dict:
    raw = model.model_json_schema()
    return _clean(raw)
