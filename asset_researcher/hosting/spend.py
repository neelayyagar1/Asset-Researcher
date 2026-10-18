"""Spend caps for a publicly-linked deployment.

The demo runs on the operator's API key, so anyone with the link is spending
the operator's money. Without a ceiling, one person looping tickers, or a
crawler, drains the account and the demo is dead exactly when someone is
looking at it.

Two limits, because they stop different things:

- **Per-session**: one visitor cannot run away with the budget.
- **Daily, shared**: the account cannot be drained across many visitors, and
  the cap resets so a bad day is not permanent.

The daily counter is a file rather than a database because this is a
single-process Streamlit app; a lock keeps concurrent sessions from losing
increments. If this ever runs multi-process, this needs to move to real
shared storage, noted rather than assumed away.
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import date
from pathlib import Path

# Claude Opus 5 list pricing, USD per million tokens (config/settings.yaml
# carries the caps; these are the rates used to convert usage into dollars).
_INPUT_PER_MTOK = 5.00
_OUTPUT_PER_MTOK = 25.00
_CACHE_READ_PER_MTOK = 0.50

_LOCK = threading.Lock()


class SpendLimitExceeded(RuntimeError):
    """Raised before a run starts, never part-way through.

    Stopping mid-report would spend the money and produce nothing, which is
    the worst of both outcomes.
    """


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0

    @property
    def cost_usd(self) -> float:
        return (
            self.input_tokens / 1e6 * _INPUT_PER_MTOK
            + self.output_tokens / 1e6 * _OUTPUT_PER_MTOK
            + self.cache_read_tokens / 1e6 * _CACHE_READ_PER_MTOK
        )

    def __add__(self, other: "Usage") -> "Usage":
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_read_tokens=self.cache_read_tokens + other.cache_read_tokens,
        )


@dataclass
class SpendTracker:
    """Daily spend against a shared cap, persisted across restarts."""

    path: Path
    daily_cap_usd: float
    session_cap_usd: float

    def __post_init__(self) -> None:
        self.path = Path(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> tuple[str, float]:
        if not self.path.exists():
            return date.today().isoformat(), 0.0
        try:
            data = json.loads(self.path.read_text())
            return data.get("date", ""), float(data.get("spent_usd", 0.0))
        except (ValueError, OSError):
            # A corrupt counter must not read as "plenty of budget left".
            # Assume the cap is spent and let the operator clear it.
            return date.today().isoformat(), self.daily_cap_usd

    def spent_today(self) -> float:
        stored_date, spent = self._read()
        if stored_date != date.today().isoformat():
            return 0.0  # a new day resets the counter
        return spent

    def remaining_today(self) -> float:
        return max(0.0, self.daily_cap_usd - self.spent_today())

    def record(self, cost_usd: float) -> None:
        with _LOCK:
            stored_date, spent = self._read()
            today = date.today().isoformat()
            if stored_date != today:
                spent = 0.0
            self.path.write_text(
                json.dumps({"date": today, "spent_usd": round(spent + cost_usd, 4)})
            )

    def check_can_start(self, session_spent_usd: float, estimated_usd: float) -> None:
        """Refuse before a run rather than during one."""
        if session_spent_usd + estimated_usd > self.session_cap_usd:
            raise SpendLimitExceeded(
                f"This session has reached its spending limit "
                f"(${self.session_cap_usd:.2f}). Reload to start a new session, "
                f"or run the tool locally with your own API key, see the README."
            )

        if self.remaining_today() < estimated_usd:
            raise SpendLimitExceeded(
                f"The shared daily budget for this demo (${self.daily_cap_usd:.2f}) "
                f"is exhausted. It resets at midnight UTC. To run it now, clone "
                f"the repository and use your own API key, see the README."
            )


# A full report is two model calls over roughly 150-250k tokens of source
# material. Measured at $1.30 for Apple (200k input, 12k output); the estimate
# carries headroom for a larger filer such as JPMorgan.
#
# This must stay comfortably below the per-session cap, or the guard rejects
# every run before it starts and the demo is dead. An earlier value of $3.50
# against a $3.00 session cap did exactly that.
ESTIMATED_REPORT_COST_USD = 2.00
