"""The research interface.

A view layer only. Every function it calls is importable and testable
without Streamlit, which keeps the pipeline, the tests and this page on one
set of code paths. Nothing here computes a figure; it arranges figures other
modules produced.

**The report is one document, not nine tabs.** A research note is read top
to bottom and then jumped back through, so the sections run in reading order
down a single scroll and the sidebar carries a sticky index. Tabs chopped
one note into nine screens and gave the running application a different
shape from the file it exports, which is the artefact anyone actually keeps.

Layout is done in our own markup rather than with Streamlit columns. A
Streamlit column is its own full-width block outside the page grid, so
charts placed in one escaped the content column and stopped lining up with
the tables above them.
"""

from __future__ import annotations

import os

import streamlit as st

from asset_researcher.analysis.assemble import assemble_bundle
from asset_researcher.analysis.mandate import (
    default_profile,
    load_presets,
    parse_mandate,
)
from asset_researcher.analysis.narrative import generate_narrative
from asset_researcher.analysis.reconcile import generate_reconciliation
from asset_researcher.analysis.report import build_report
from asset_researcher.config import get_settings
from asset_researcher.hosting.spend import (
    ESTIMATED_REPORT_COST_USD,
    SpendLimitExceeded,
    SpendTracker,
)
from asset_researcher.llm.claude import ClaudeProvider
from asset_researcher.sources.edgar.client import EdgarClient
from asset_researcher.sources.finnhub import FinnhubClient
from asset_researcher.sources.web import UrlRejected, fetch_user_source
from asset_researcher.ui import document, theme
from asset_researcher.ui import components as ui
from asset_researcher.ui.export import report_to_html, report_to_markdown
from asset_researcher.ui.headline import headline_stats

def _bridge_hosted_secrets() -> None:
    """Make Streamlit Cloud's secrets look like a local .env.

    The config loader reads os.environ and knows nothing about Streamlit,
    which is what keeps it importable by the tests and the CLI. Streamlit
    Community Cloud puts deployment secrets in st.secrets instead, so
    without this bridge a deployed instance starts with no credentials and
    fails on the first EDGAR call.
    """
    # st.secrets is lazy: the attribute resolves fine and the load happens
    # on first use, so wrapping only the attribute access let a missing
    # secrets.toml crash the app on every local run.
    for key in ("ANTHROPIC_API_KEY", "FINNHUB_API_KEY", "EDGAR_USER_AGENT"):
        if key in os.environ:
            continue
        try:
            value = st.secrets[key]
        except Exception:
            # No secrets file, or no such key. Local runs read .env.
            return
        os.environ[key] = str(value)


_bridge_hosted_secrets()

st.set_page_config(
    page_title="Asset Researcher",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(theme.stylesheet(), unsafe_allow_html=True)


def write(html: str) -> None:
    """Emit a rendered block.

    Nothing reaches this that the component producing it did not escape,
    which is why the components own escaping rather than the view.
    """
    if html:
        st.markdown(html, unsafe_allow_html=True)


@st.cache_resource
def services():
    settings = get_settings()
    return (
        settings,
        EdgarClient(settings),
        FinnhubClient(settings),
        ClaudeProvider(settings),
        SpendTracker(
            # Anchored to the repository like every cache path. Relative to
            # the process working directory, launching from anywhere else
            # started the daily counter at zero with no error.
            path=settings.repo_root / "data" / "spend.json",
            daily_cap_usd=settings.hosting.spend_cap_daily_usd,
            session_cap_usd=settings.hosting.spend_cap_session_usd,
        ),
    )


settings, edgar, finnhub, llm, spend = services()
st.session_state.setdefault("session_spend", 0.0)
st.session_state.setdefault("report", None)


# ------------------------------------------------------------------ views

# Three screens, not one. The tool used to open on a form, which asks a
# stranger to supply an input before anything has told them what they get
# back. Home states the proposition, the workspace runs the report, and the
# form returns as a dialog once a report is on screen, because at that
# point it is a thing you reach for occasionally rather than the first
# thing you meet.
st.session_state.setdefault("view", "home")
report = st.session_state.get("report")
presets = load_presets()


def _controls(key: str) -> tuple[str, str, str, bool]:
    """The report form. Rendered inline on the empty workspace and inside
    a dialog once there is a report to replace."""
    ticker = st.text_input(
        "Ticker", value="AAPL", max_chars=8, key=f"{key}_ticker"
    ).strip().upper()
    choice = st.selectbox(
        "Mandate",
        ["Describe my own"] + [p.name for p in presets],
        index=1,
        key=f"{key}_preset",
    )
    prefill = (
        ""
        if choice == "Describe my own"
        else next(p.description for p in presets if p.name == choice)
    )
    mandate_text = st.text_area(
        "Mandate description", value=prefill, height=110, key=f"{key}_mandate"
    )
    st.caption(
        "Sets emphasis and ordering only. It does not change the reported "
        "figures, the citations, or which divergences are disclosed."
    )
    urls_text = st.text_area(
        "Additional sources", height=70, placeholder="https://",
        key=f"{key}_urls",
    )
    st.caption(
        "Public URLs. Classified as secondary and attributed as opinion. "
        f"Demo budget remaining today: ${spend.remaining_today():,.2f}"
    )
    run = st.button(
        "Generate report", type="primary", use_container_width=True,
        key=f"{key}_run",
    )
    return ticker, mandate_text, urls_text, run


@st.dialog("New report", width="large")
def _new_report_dialog() -> None:
    ticker, mandate_text, urls_text, run = _controls("dialog")
    if run and ticker:
        st.session_state["pending"] = (ticker, mandate_text, urls_text)
        st.rerun()


def generate(ticker: str, mandate_text: str, urls: list[str]):
    try:
        spend.check_can_start(
            st.session_state["session_spend"], ESTIMATED_REPORT_COST_USD
        )
    except SpendLimitExceeded as exc:
        write(ui.status("error", "Budget", str(exc)))
        return None

    before = llm.usage.cost_usd
    user_sources = []

    # Call A costs roughly a dollar and runs before Call B, which is the one
    # that can fail on a truncated structured response. Recording the cost
    # only after both succeeded meant a repeatable late failure spent real
    # money against a counter that never moved, and neither cap ever bound.
    try:
        return _generate(ticker, mandate_text, urls, user_sources)
    finally:
        cost = llm.usage.cost_usd - before
        if cost:
            st.session_state["session_spend"] += cost
            spend.record(cost)


def _generate(ticker: str, mandate_text: str, urls: list[str], user_sources: list):
    with st.status(f"Building {ticker}", expanded=True) as status:
        # The stage lines below all land within the first few seconds and
        # the longest stage then runs silently for over a minute, which
        # reads as a hung process. The bar is a time estimate, not measured
        # progress, and stops short of full for that reason; it is honest
        # here only because this block mounts once per run and is replaced
        # when the run ends, so it cannot replay on an unrelated rerun.
        st.markdown(
            '<div class="ar-progress"><i></i></div>', unsafe_allow_html=True
        )
        for url in urls:
            try:
                user_sources.append(fetch_user_source(url))
                st.write(f"Source accepted: {url}")
            except UrlRejected as exc:
                st.write(f"Source rejected ({url}): {exc}")

        st.write("Retrieving filings, market data and the peer set")
        bundle = assemble_bundle(ticker, settings, edgar, finnhub, llm)
        st.write(
            f"{len(bundle.passages)} passages, "
            f"{bundle.total_passage_chars:,} characters"
        )

        st.write("Parsing mandate")
        mandate = (
            parse_mandate(mandate_text, llm)
            if mandate_text.strip()
            else default_profile()
        )

        st.write("Drafting descriptive sections and verifying citations")
        narrative = generate_narrative(
            bundle,
            llm,
            effort=settings.llm.effort.get("narrative", "medium"),
            user_sources=user_sources,
        )

        st.write("Reconciling the narrative against filed figures")
        reconciliation = generate_reconciliation(
            bundle,
            narrative,
            mandate,
            llm,
            effort=settings.llm.effort.get("reconciliation", "high"),
        )
        status.update(label=f"{ticker} complete", state="complete", expanded=False)

    return build_report(bundle, mandate, narrative, reconciliation)


def _run_pending() -> None:
    pending = st.session_state.pop("pending", None)
    if not pending:
        return
    ticker, mandate_text, urls_text = pending
    urls = [u.strip() for u in urls_text.splitlines() if u.strip()]
    try:
        st.session_state["report"] = generate(ticker, mandate_text, urls)
    except Exception as exc:
        st.session_state["report"] = None
        write(
            ui.status(
                "error", "Failed", f"The report could not be generated: {exc}"
            )
        )


# ------------------------------------------------------------------- home

if st.session_state["view"] == "home" and report is None:
    write(ui.home())
    if st.button("Start a report", type="primary", key="enter"):
        st.session_state["view"] = "tool"
        st.rerun()
    write(ui.home_foot())
    st.stop()


# -------------------------------------------------------------- workspace

_run_pending()
report = st.session_state.get("report")

if report is None:
    left, right = st.columns([1.15, 1])
    with left:
        write(ui.workspace_intro())
        ticker, mandate_text, urls_text, run = _controls("inline")
        if run and ticker:
            st.session_state["pending"] = (ticker, mandate_text, urls_text)
            st.rerun()
        if run and not ticker:
            write(ui.status("error", "Input", "Enter a ticker."))
    st.stop()


bundle = report.bundle
rec = report.reconciliation
price = bundle.quote.price if bundle.quote else None
cases = bundle.valuation_cases
implied = bundle.implied
context = bundle.cash_context

# ----------------------------------------------------------------- masthead

# A new report is an occasional act once one is on screen, so the form is
# behind a control rather than occupying the top of every page.
actions = st.columns([5, 1.1, 1.1, 1.3])
if actions[3].button("New report", use_container_width=True, key="new"):
    _new_report_dialog()
actions[1].download_button(
    "HTML",
    data=report_to_html(report),
    file_name=f"{report.ticker}-research-note.html",
    mime="text/html",
    use_container_width=True,
    key="dl_html",
)
actions[2].download_button(
    "Markdown",
    data=report_to_markdown(report),
    file_name=f"{report.ticker}-research-note.md",
    mime="text/markdown",
    use_container_width=True,
    key="dl_md",
)

write(
    ui.masthead(
        bundle.company_name,
        bundle.ticker,
        bundle.as_of,
        [bundle.display_industry, f"Prepared for {report.mandate.summary()}"],
    )
)
write(ui.chips(document.provenance_items(report)))
write(ui.stat_strip(headline_stats(report)))

# ------------------------------------------------------------- document

# The sections come from asset_researcher/ui/document.py, which the export
# also renders. They used to be built here and again there, which is how the
# screen came to show one set of section labels and the file another.
blocks = document.sections(report)
write(ui.nav([s.label for s in blocks]))
for block in blocks:
    write(block.html)

write(
    '<p class="ar-foot" style="margin-top:var(--s7);border-top:1px solid '
    f'var(--rule);padding-top:var(--s3)">{settings.report.disclaimer}</p>'
)

