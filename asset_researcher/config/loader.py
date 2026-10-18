"""Loads settings.yaml plus secrets from the environment into one typed object.

Secrets never live in this module's return value in a form that gets printed or
logged accidentally: Settings.__repr__ is overridden below to redact them, and
callers should read the specific field they need rather than logging the whole
object.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, SecretStr

_CONFIG_DIR = Path(__file__).parent
_REPO_ROOT = _CONFIG_DIR.parent.parent


class LLMConfig(BaseModel):
    model: str
    effort: dict[str, str]


class EdgarConfig(BaseModel):
    base_url: str
    rate_limit_per_sec: float
    cache_dir: str


class FinnhubConfig(BaseModel):
    base_url: str
    rate_limit_per_sec: float
    cache_dir: str


class QuantConfig(BaseModel):
    resolution_cache_dir: str


class BundleConfig(BaseModel):
    # Character budget per source component. Exceeding one is recorded as a
    # gap on the bundle rather than truncated silently.
    token_budget: dict[str, int]


class SectorConfig(BaseModel):
    ranges: dict[str, list[list[int]]]
    default: str


class HostingConfig(BaseModel):
    spend_cap_daily_usd: float
    spend_cap_session_usd: float


class ReportConfig(BaseModel):
    disclaimer: str


class Settings(BaseModel):
    """Full application settings: settings.yaml merged with required secrets.

    Secret fields use SecretStr so a stray print(settings) or log call doesn't
    leak a key, str(settings) shows '**********' for those fields.
    """

    llm: LLMConfig
    edgar: EdgarConfig
    finnhub: FinnhubConfig
    quant: QuantConfig
    bundle: BundleConfig
    sectors: SectorConfig
    hosting: HostingConfig
    report: ReportConfig

    # Secrets are read into SecretStr but NOT required to be non-empty here.
    # Each client validates its own dependency at construction time (see
    # require_secret below). EDGAR code should be testable without an
    # Anthropic or Finnhub key present, and vice versa. Only edgar_user_agent
    # is required eagerly: EDGAR calls are cheap to test and the whole app
    # touches EDGAR, so there's no meaningful "path that doesn't need it".
    anthropic_api_key: SecretStr
    finnhub_api_key: SecretStr
    edgar_user_agent: str

    repo_root: Path

    def resolved_cache_dir(self, relative: str) -> Path:
        path = self.repo_root / relative
        path.mkdir(parents=True, exist_ok=True)
        return path


def _require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and fill it in."
        )
    return value


_CONTACT = re.compile(r"[^@\s]+@[^@\s]+\.[A-Za-z]{2,}")
_PLACEHOLDER_DOMAINS = ("example.com", "example.org", "example.net")


def _require_edgar_user_agent(value: str) -> str:
    """EDGAR fair access requires a real contact, and only checks it is there.

    Validating non-emptiness was not enough, because `.env.example` ships
    `contact@example.com` and copying it verbatim is the obvious thing to do.
    That sends a fake contact to the SEC on every request, which is a fair
    access violation and earns an IP block part-way through a report rather
    than at startup where it can be understood.
    """
    contact = _CONTACT.search(value)
    if not contact:
        raise RuntimeError(
            "EDGAR_USER_AGENT must contain a real contact email address. "
            "The SEC requires every request to identify who is making it, "
            "and rejects requests that do not."
        )
    if any(contact.group(0).lower().endswith(d) for d in _PLACEHOLDER_DOMAINS):
        raise RuntimeError(
            "EDGAR_USER_AGENT still carries the placeholder address from "
            ".env.example. Put your own address there: the SEC blocks "
            "clients that do not identify a reachable contact."
        )
    return value


def require_secret(value: SecretStr, name: str) -> str:
    """Call this in a client's __init__, not at import time, fail at the point
    of actual use, with a message naming exactly which key is missing."""
    revealed = value.get_secret_value()
    if not revealed:
        raise RuntimeError(
            f"{name} is not set. Add it to .env (see .env.example) before "
            f"using this client."
        )
    return revealed


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load once per process. Cached, env and settings.yaml are read at startup."""
    load_dotenv(_REPO_ROOT / ".env")

    with open(_CONFIG_DIR / "settings.yaml") as f:
        raw = yaml.safe_load(f)

    return Settings(
        **raw,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        finnhub_api_key=os.environ.get("FINNHUB_API_KEY", ""),
        edgar_user_agent=_require_edgar_user_agent(
            _require_env("EDGAR_USER_AGENT")
        ),
        repo_root=_REPO_ROOT,
    )
