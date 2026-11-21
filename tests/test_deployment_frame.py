"""The frame Streamlit paints before our stylesheet arrives, and what
the first screen is allowed to depend on.

Both checks exist because the live deployment failed on them.
"""

from __future__ import annotations

import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONFIG = ROOT / ".streamlit" / "config.toml"
APP = ROOT / "app.py"


def _config() -> dict:
    return tomllib.loads(CONFIG.read_text(encoding="utf-8"))


def _shell_token(name: str) -> str:
    from asset_researcher.ui import theme

    match = re.search(rf"--{name}:\s*(#[0-9a-fA-F]{{3,6}})\s*;", theme.stylesheet())
    assert match, f"--{name} is not declared"
    return match.group(1).lower()


def test_the_cold_load_paints_the_shell_not_the_world_it_replaced():
    """Streamlit paints this frame before the stylesheet arrives.

    It held the editorial palette - cream paper and a slate accent -
    from a design that no longer ships, so every cold load flashed the
    replaced world and then settled onto the new one. The first
    impression of the page was a colour the product does not use.
    """
    theme_cfg = _config()["theme"]
    assert theme_cfg["backgroundColor"].lower() == _shell_token("shell-bg")
    assert theme_cfg["secondaryBackgroundColor"].lower() == _shell_token(
        "shell-panel"
    )
    assert theme_cfg["textColor"].lower() == _shell_token("shell-ink")
    assert theme_cfg["primaryColor"].lower() == _shell_token("shell-focus")


def test_errors_are_redacted_in_production():
    """"none", not false: false is a legacy alias mapping to
    "stacktrace", which ships the type and the full traceback with
    absolute paths and source lines."""
    assert _config()["client"]["showErrorDetails"] == "none"


def test_the_first_screen_depends_on_nothing_decorative():
    """A developer artifact may not be able to take the product down.

    app.py emitted a design-direction contract as an HTML comment at
    import time, before `write` was even defined. When the deployed
    process held a stale copy of the components module, that one call
    raised AttributeError and the entire site served a red traceback
    instead of a gate - for a comment no reader ever sees.

    The design record belongs in DESIGN.md and NOTES.md, which cannot
    crash anything.
    """
    source = APP.read_text(encoding="utf-8")
    assert "direction_contract" not in source, (
        "the first screen still depends on a decorative artifact"
    )
