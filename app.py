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


# ------------------------------------------------------------------ controls

# No sidebar. The controls that matter sit at the top of the page where
# they are visible, and the section index is a sticky bar the reader can
# reach at any scroll depth. Burying the index under four input widgets in
# a collapsible drawer made the one thing a reader needs constantly the
# hardest thing on the page to reach, and collapsing that drawer used to
# hide the entire input surface.
presets = load_presets()
report = st.session_state.get("report")

controls = st.columns([1.1, 2.4, 1.2, 1.1, 0.9] if report else [1.1, 2.4, 1.2])
ticker = controls[0].text_input("Ticker", value="AAPL", max_chars=8).strip().upper()
choice = controls[1].selectbox(
    "Mandate", ["Describe my own"] + [p.name for p in presets], index=1
)
controls[2].markdown('<div style="height:1.62rem"></div>', unsafe_allow_html=True)
run = controls[2].button("Generate report", type="primary", use_container_width=True)

prefill = (
    ""
    if choice == "Describe my own"
    else next(p.description for p in presets if p.name == choice)
)

with st.expander("Mandate detail and additional sources"):
    mandate_text = st.text_area("Mandate description", value=prefill, height=110)
    st.caption(
        "Sets emphasis and ordering only. It does not change the reported "
        "figures, the citations, or which divergences are disclosed."
    )
    urls_text = st.text_area("Additional sources", height=70, placeholder="https://")
    st.caption(
        "Public URLs. Classified as secondary and attributed as opinion. "
        f"Demo budget remaining today: ${spend.remaining_today():,.2f}"
    )

if report is not None:
    controls[3].markdown('<div style="height:1.62rem"></div>', unsafe_allow_html=True)
    controls[3].download_button(
        "HTML",
        data=report_to_html(report),
        file_name=f"{report.ticker}-research-note.html",
        mime="text/html",
        use_container_width=True,
    )
    controls[4].markdown('<div style="height:1.62rem"></div>', unsafe_allow_html=True)
    controls[4].download_button(
        "Markdown",
        data=report_to_markdown(report),
        file_name=f"{report.ticker}-research-note.md",
        mime="text/markdown",
        use_container_width=True,
    )


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


if run:
    if not ticker:
        write(ui.status("error", "Input", "Enter a ticker."))
    else:
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


# ------------------------------------------------------------- open state

report = st.session_state.get("report")
if report is None:
    write(
        ui.open_state(
            "Read the filings, then read what management said about them.",
            "A ticker in, a sourced research note out: the filed financial "
            "record, the narrative management wrapped around it, and the "
            "places where the two do not agree. Every figure comes from the "
            "company's own submissions to the SEC, every claim carries a "
            "citation back to the source text, and every report states the "
            "strongest case against its own thesis.",
            "Enter a ticker above. About a minute.",
        )
    )
    st.stop()


bundle = report.bundle
rec = report.reconciliation
price = bundle.quote.price if bundle.quote else None
cases = bundle.valuation_cases
implied = bundle.implied
context = bundle.cash_context

# ----------------------------------------------------------------- masthead

write(
    ui.masthead(
        bundle.company_name,
        bundle.ticker,
        bundle.as_of,
        [bundle.display_industry, f"Prepared for {report.mandate.summary()}"],
    )
)
write(ui.stat_strip(headline_stats(report)))

level, message = report.verification_banner
write(
    ui.block(
        ui.status(
            level,
            {
                "success": "Citations located",
                "warning": "Citations partial",
                "error": "Citations absent",
            }[level],
            message,
        ),
        ui.status("warning", "Model divergence", implied.caveat)
        if implied is not None and implied.caveat
        else "",
        ui.status("info", "Source currency", bundle.staleness_note)
        if bundle.staleness_note
        else "",
    )
)


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

