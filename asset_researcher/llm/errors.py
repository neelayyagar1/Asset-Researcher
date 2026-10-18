class LLMError(RuntimeError):
    """Base class for provider-level failures."""


class StructuredOutputError(LLMError):
    """The model's response didn't validate against the requested schema, or
    the response carried a refusal/incomplete stop reason. Callers should
    treat this as a failed call, not silently accept partial output, a
    concept mapping or reconciliation result that failed validation is worse
    than no result at all."""
