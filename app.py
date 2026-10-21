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

import hmac
import os
import time

import streamlit as st
import streamlit.components.v1 as components

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
from asset_researcher.hosting import samples
from asset_researcher.hosting.spend import (
    ESTIMATED_REPORT_COST_USD,
    SpendLimitExceeded,
    SpendTracker,
)
from asset_researcher.llm.claude import ClaudeProvider
from asset_researcher.sources.edgar.client import EdgarClient
from asset_researcher.sources.finnhub import FinnhubClient
from asset_researcher.sources.web import UrlRejected, fetch_user_source
from asset_researcher.ui import document, markdown, theme
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
    for key in (
        "ANTHROPIC_API_KEY", "FINNHUB_API_KEY", "EDGAR_USER_AGENT",
        "DEMO_PASSPHRASE", "SAMPLES_KEY",
    ):
        if key in os.environ:
            continue
        try:
            value = st.secrets[key]
        except Exception:
            # No secrets file, or no such key. `continue`, not `return`:
            # returning here meant a secrets.toml that set Finnhub and the
            # EDGAR agent but not Anthropic bridged nothing at all, and the
            # deployment then failed on its first EDGAR call with a 403,
            # which is the exact failure this function exists to prevent.
            continue
        os.environ[key] = str(value)


_bridge_hosted_secrets()


# Attempts before the delay starts, and the ceiling it doubles up to.
_GATE_FREE_ATTEMPTS = 3
_GATE_MAX_DELAY = 30.0


def _passphrase() -> str:
    """The shared passphrase, or "" when none is configured.

    Absent means open, which is right for a local run and wrong for a
    deployment. Setting DEMO_PASSPHRASE in the host's secrets is what
    turns the gate on.
    """
    if os.environ.get("DEMO_PASSPHRASE"):
        return os.environ["DEMO_PASSPHRASE"]
    try:
        return str(st.secrets["DEMO_PASSPHRASE"])
    except Exception:
        return ""


def _unlock_token() -> str:
    """A value that proves the passphrase was given, without being it.

    A digest rather than the phrase, so the passphrase itself never
    appears in a URL, a browser history, a server log or a screenshot.

    It is still password-equivalent for this deployment: anyone holding
    this token is in, which is the price of surviving the reload that
    Back requires. The passphrase is already shared by email, so the
    exposure is the same kind - but a URL travels more easily than a
    sentence in a message, so treat a pasted link as granting access.
    """
    secret = _passphrase()
    if not secret:
        return ""
    return hmac.new(
        secret.encode("utf-8"), b"asset-researcher-gate-v1", "sha256"
    ).hexdigest()[:32]


def _gate() -> bool:
    """Stop here unless the visitor knows the passphrase.

    This is not authentication and does not pretend to be: one secret,
    shared by everyone who has it, with no per-person revocation. What it
    buys is the thing that actually matters for a deployed demo, which is
    that a stranger cannot reach the Generate button and spend the API
    balance behind it. The spend caps are the second line and the
    provider's own limit is the third.

    `st.stop()` rather than a wrapper around the page body, because the
    rest of this file runs top to bottom at import: stopping is what keeps
    an unauthenticated visitor from reaching any of it.
    """
    secret = _passphrase()
    if not secret:
        return True
    if st.session_state.get("unlocked"):
        return True

    # A token in the URL reopens the gate after the reload that Back
    # needs. Compared as a digest against a digest, in constant time.
    supplied = st.query_params.get("k") or ""
    if supplied and hmac.compare_digest(
        supplied.encode("utf-8"), _unlock_token().encode("utf-8")
    ):
        st.session_state["unlocked"] = True
        return True

    # Backoff. Each guess was one websocket message against a microsecond
    # comparison, with nothing in front of it on Community Cloud, so the
    # gate could be ground down by a trivial script. This does not stop a
    # distributed attacker and is not meant to; it removes the easy path
    # and makes the attempt count visible to the person making them.
    attempts = st.session_state.get("gate_attempts", 0)
    if attempts >= _GATE_FREE_ATTEMPTS:
        delay = min(2 ** (attempts - _GATE_FREE_ATTEMPTS), _GATE_MAX_DELAY)
        waited = time.monotonic() - st.session_state.get("gate_last", 0.0)
        if waited < delay:
            write(ui.gate())
            write(ui.status(
                "warning", "Slow down",
                f"Too many attempts. Try again in "
                f"{max(1, int(delay - waited))} seconds.",
            ))
            return False

    write(ui.gate())
    # A form, so Return submits. A password box that ignores Return is
    # the most practised gesture in the world failing silently on the
    # first interaction, which reads as broken rather than as strict.
    with st.form("gate_form", clear_on_submit=True, border=False):
        entered = st.text_input(
            "Passphrase", type="password", key="gate_input",
            label_visibility="collapsed", placeholder="Passphrase",
        )
        submitted = st.form_submit_button("Enter", type="primary")
    if submitted:
        # Bytes, because compare_digest raises TypeError on a str holding
        # any non-ASCII character. A visitor typing an accented letter got
        # an uncaught exception instead of a refusal, and a passphrase
        # containing one would have made the gate raise for everyone, with
        # no way to unlock the app at all.
        #
        # compare_digest rather than ==, so the content comparison runs in
        # constant time. It does not hide the secret's length and is not
        # claimed to: it returns early when the lengths differ.
        # Autocorrect in a mail client turns a hyphen into an en dash, and
        # a reviewer pastes this out of an email. Folding the dash
        # variants costs nothing and saves a support round-trip.
        attempt = (entered or "").strip()
        for dash in ("\u2010", "\u2011", "\u2012", "\u2013", "\u2014"):
            attempt = attempt.replace(dash, "-")
        if hmac.compare_digest(attempt.encode("utf-8"), secret.encode("utf-8")):
            st.session_state["unlocked"] = True
            st.session_state["gate_attempts"] = 0
            st.query_params["k"] = _unlock_token()
            st.rerun()
        else:
            st.session_state["gate_attempts"] = attempts + 1
            st.session_state["gate_last"] = time.monotonic()
            write(ui.status("error", "Refused", "That passphrase is not right."))
    return False


st.set_page_config(
    page_title="Asset Researcher",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(theme.stylesheet(), unsafe_allow_html=True)

# A bypass link. The report carries twenty section anchors ahead of its
# content, so without this a keyboard user tabs through the whole index to
# reach the note. Streamlit owns the document shell and gives our content
# no `main` element to target, so the link points at the masthead, which
# is the first thing in the report proper. The exported file, whose shell
# we do write, gets a real `main` landmark.
def _skip_link(target: str, label: str) -> None:
    """A bypass link, emitted only where its target exists.

    This was emitted unconditionally and pointed at `#ar-report`, which
    is written only on the report screen, so on home and on the workspace
    the first thing a keyboard user met was a bypass control that went
    nowhere.
    """
    st.markdown(
        f'<a class="ar-skip" href="#{target}">{label}</a>',
        unsafe_allow_html=True,
    )


def write(html: str) -> None:
    """Emit a rendered block.

    Nothing reaches this that the component producing it did not escape,
    which is why the components own escaping rather than the view.
    """
    if html:
        st.markdown(html, unsafe_allow_html=True)


# Before anything that can spend money, and after `write`, which the gate
# screen renders through. Everything below this point is reachable only by
# a visitor who knows the passphrase.
if not _gate():
    st.stop()



@st.cache_data(show_spinner=False)
def _sample_label(title: str) -> str:
    """"COSTCO WHOLESALE CORP /NEW (COST)" -> "Costco Wholesale (COST)"."""
    if "(" in title:
        name, _, ticker = title.rpartition("(")
        return f"{ui.display_name(name.strip())} ({ticker.rstrip(')')})"
    return ui.display_name(title)


def _about_text() -> str:
    """The how-it-works page, from the guide the repository carries.

    One source, so the page a reviewer reads inside the product and the
    document a reader finds in the repository cannot drift apart - but
    not the whole of it. The guide also carries a worked example and a
    link list, and neither answers "how does this work": a reader on this
    page wants the mechanism, and a finding about one particular company
    is an outcome, not an explanation. Those sections stay in the
    repository where they belong.

    Selecting by heading rather than slicing, so adding a section to the
    guide does not silently add it here.
    """
    path = get_settings().repo_root / "docs" / "FOR-REVIEWERS.md"
    try:
        body = path.read_text(encoding="utf-8")
    except OSError:
        return "# How it works\n\nThe written guide did not ship with this build."

    wanted = (
        "The problem",
        "What makes it different from a chatbot over filings",
        "How it is built",
        "What it does not do",
    )
    out: list[str] = []
    keeping = False
    for line in body.splitlines():
        if line.startswith("# ") and not line.startswith("## "):
            # The document title, which is the page title here.
            out.append(line)
            continue
        if line.startswith("## "):
            keeping = line[3:].strip() in wanted
        if keeping:
            out.append(line)

    # The closing disclaimer, wherever it sits, because it says what this
    # is and that is squarely a how-it-works matter.
    closing = [
        ln.strip()
        for ln in body.splitlines()
        if ln.strip().startswith("Research assistance")
    ]
    return "\n".join(out + ([""] + closing if closing else [])).strip()


@st.cache_resource(show_spinner=False)
def _load_samples(key: str, stamp: float):
    """Open the sealed notes. Cached on the key and the file's mtime.

    Both arguments are cache keys, and that is the whole point. This took
    none, so the first call decided the answer for the life of the
    process: an app that started before SAMPLES_KEY was set cached the
    empty list and went on returning it after the secret was added, with
    the only symptom a missing button.
    """
    if not key:
        return []
    return samples.load(key)


def _samples():
    """The packed sample notes, or an empty list.

    Returns empty for a deployment that ships none, which is a normal
    state. A key that is set but does not open the archive is not: that
    is a misconfiguration, and it is recorded so the next render can say
    so rather than quietly dropping the feature.
    """
    key = os.environ.get("SAMPLES_KEY", "")
    st.session_state["samples_problem"] = ""
    if not key:
        return []
    try:
        stamp = samples.SAMPLES_PATH.stat().st_mtime
    except OSError:
        st.session_state["samples_problem"] = (
            "SAMPLES_KEY is set but no sample archive shipped with this "
            "build."
        )
        return []
    try:
        return _load_samples(key, stamp)
    except ValueError:
        st.session_state["samples_problem"] = (
            "SAMPLES_KEY does not open the sample archive. It must be the "
            "key the notes were packed under, not the demo passphrase."
        )
        return []


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
_VIEWS = ("home", "tool", "samples", "about")


def go(view: str) -> None:
    """Move to a view, and put it in the address bar.

    The three screens used to share one history entry, so the browser's
    Back - and a two-finger swipe, which is the same gesture - left the
    site entirely rather than going back a screen. Writing the view into
    the query string gives each screen its own entry, so Back means what
    a reader expects it to mean.
    """
    st.session_state["view"] = view
    st.query_params["view"] = view
    st.rerun()


def _sync_view_from_url() -> None:
    """Adopt the view the address bar is asking for.

    Streamlit does not rerun when the browser's own Back changes the
    query string: popstate fires, the URL updates, and the script never
    runs again, so the address bar said one thing and the page showed
    another. Reloading would fix that and would also end the Streamlit
    session, which means re-locking the gate on every Back - a worse
    outcome than the bug.

    So `_back_bridge` below listens for popstate in the page and asks
    Streamlit for a rerun instead, and this runs on each rerun to take
    whatever the URL now says.
    """
    # An absent parameter means home, not "leave it alone". Going back to
    # the bare URL is going back to where the visitor started, and
    # treating absence as no-opinion left the address bar on the base URL
    # while the page still showed the screen they had just left.
    requested = st.query_params.get("view") or "home"
    if requested in _VIEWS and requested != st.session_state.get("view"):
        st.session_state["view"] = requested


_sync_view_from_url()
st.session_state.setdefault("view", "home")


def _back_bridge() -> None:
    """Make the browser's Back reload, so the page follows the URL.

    Streamlit keeps query parameters on the server: they are set when the
    browser first connects and when the app writes them, and a history
    change never reaches the server. Verified directly - a rerun
    triggered after Back still read the old value - so there is no way to
    follow Back without reloading.

    A reload ends the Streamlit session, which would normally re-lock the
    gate. `_unlock_token` is what makes that survivable: the unlock rides
    in the URL, so the reloaded page comes back already open.
    """
    components.html(
        """<script>
        (function () {
          var host = window.parent;
          if (!host || host.__arBack) return;
          host.__arBack = true;
          host.addEventListener('popstate', function () {
            // The URL has already changed by the time this fires, so a
            // reload lands on whatever Back asked for.
            host.location.reload();
          });
        })();
        </script>""",
        height=0,
    )


# Below the gate, so nothing renders for a visitor who has not got in,
# and below the definition, which is where it has to be in a module that
# executes top to bottom.
_back_bridge()
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
    # Tall enough for the seeded description. At 110 the default content
    # was cut through the middle of a line of type, so the first thing a
    # reader saw of the field they most need to read was the app failing
    # to hold its own text.
    mandate_text = st.text_area(
        "Mandate description", value=prefill, height=150, key=f"{key}_mandate"
    )
    st.caption(
        "Sets emphasis and ordering only. It does not change the reported "
        "figures, the citations, or which divergences are disclosed."
    )
    urls_text = st.text_area(
        "Additional sources", height=70, placeholder="https://",
        key=f"{key}_urls",
    )
    # No running budget figure here. It used to print the remaining daily
    # allowance, which told a reviewer a number that is none of their
    # business and invited them to treat the demo as a meter rather than
    # as a research tool. The cap still binds; it simply does so quietly,
    # and says so only in the one case where it has to - when a run is
    # refused, which is the only moment the figure explains anything.
    st.caption(
        "Public URLs. Classified as secondary and attributed as opinion."
    )
    # Back sits with the action it is an alternative to, at the foot of
    # the form, rather than above it where it read as a page control. The
    # primary keeps most of the width; leaving is the smaller gesture.
    row = st.columns([3, 1])
    run = row[0].button(
        "Generate report", type="primary", use_container_width=True,
        key=f"{key}_run",
    )
    if row[1].button(
        "Back", use_container_width=True, key=f"{key}_back"
    ):
        go("home")
    return ticker, mandate_text, urls_text, run


@st.dialog("New report", width="large")
def _new_report_dialog() -> None:
    ticker, mandate_text, urls_text, run = _controls("dialog")
    if run and ticker:
        st.session_state["pending"] = (ticker, mandate_text, urls_text)
        st.rerun()
    if run and not ticker:
        # The inline form says this; the dialog used to do nothing at all.
        write(ui.status("error", "Input", "Enter a ticker."))


def generate(ticker: str, mandate_text: str, urls: list[str]):
    # Reserved, not checked: the estimate is charged to the shared counter
    # before the run starts, so two visitors arriving together cannot both
    # pass a check neither has yet paid for.
    try:
        spend.reserve(
            st.session_state["session_spend"], ESTIMATED_REPORT_COST_USD
        )
    except SpendLimitExceeded as exc:
        write(ui.status("error", "Budget", str(exc)))
        return None
    st.session_state["session_spend"] += ESTIMATED_REPORT_COST_USD

    user_sources = []

    # Call A costs roughly a dollar and runs before Call B, which is the one
    # that can fail on a truncated structured response. Recording the cost
    # only after both succeeded meant a repeatable late failure spent real
    # money against a counter that never moved, and neither cap ever bound.
    # Scoped rather than differenced against the provider's cumulative
    # counter. The provider is shared by every browser session, so a
    # before-and-after reading of that counter charged this visitor for
    # whatever other visitors spent while this run was in flight.
    try:
        with llm.usage_scope() as run:
            return _generate(ticker, mandate_text, urls, user_sources)
    finally:
        # Settle the reservation against what it really cost. The session
        # total is corrected the same way, so the estimate's headroom is
        # returned to the visitor rather than quietly kept.
        cost = run.cost_usd
        spend.settle(ESTIMATED_REPORT_COST_USD, cost)
        st.session_state["session_spend"] += cost - ESTIMATED_REPORT_COST_USD


def _generate(ticker: str, mandate_text: str, urls: list[str], user_sources: list):
    with st.status(f"Building {ticker}", expanded=True) as status:
        # The stage lines below all land within the first few seconds and
        # the longest stage then runs silently for over a minute, which
        # reads as a hung process. The bar is a time estimate, not measured
        # progress, and stops short of full for that reason; it is honest
        # here only because this block mounts once per run and is replaced
        # when the run ends, so it cannot replay on an unrelated rerun.
        # role=progressbar with no value, which is what an indeterminate
        # bar is, plus a live region so the stage changes are announced.
        # Nothing on this page was a live region at all, so a build that
        # runs for over a minute was entirely silent to a screen reader.
        st.markdown(
            '<div class="ar-progress" role="progressbar" aria-busy="true"'
            ' aria-label="Building the report">'
            "<i></i></div>",
            unsafe_allow_html=True,
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
    # The report already on screen survives a failure. Assigning the
    # result straight into session state discarded it whenever `generate`
    # returned None, which it does on a budget refusal, so a visitor who
    # hit the cap lost the note they were reading and landed back on an
    # empty form.
    try:
        fresh = generate(ticker, mandate_text, urls)
    except Exception as exc:
        write(
            ui.status(
                "error", "Failed", f"The report could not be generated: {exc}"
            )
        )
        return
    if fresh is not None:
        st.session_state["report"] = fresh


# ------------------------------------------------------------------- home

if st.session_state["view"] == "home" and report is None:
    _skip_link("ar-home", "Skip to start")
    write('<span id="ar-home" tabindex="-1"></span>')
    write(ui.home())
    # Two ways in, because they cost different things. Building a note
    # spends a real API call and takes about a minute; reading one that
    # was already built costs nothing and is instant, which is what most
    # first-time readers actually want. Saying so on the buttons is the
    # difference between a visitor who waits and one who leaves.
    # Reading a sample is the primary action, and it is the one that was
    # outlined while the expensive one was filled. It shows the best work
    # in the product, instantly, for nothing; building a report takes a
    # minute and spends a real API call. A reviewer with four minutes
    # should land on the first.
    #
    # The columns are tight and weighted, because `[1, 1, 2]` let the
    # gutters set the spacing and the three buttons read as unrelated
    # objects 140px apart rather than as one choice.
    has_samples = bool(_samples())
    actions = st.columns([1.3, 1.2, 1.3, 3.2] if has_samples else [1.4, 1.2, 4])
    if actions[0].button("Build a report", type="primary", key="enter"):
        go("tool")
    if actions[1].button("How it works", key="to_about"):
        go("about")
    if has_samples and actions[2].button("Read a sample", key="to_samples"):
        go("samples")
    # A key that is set and does not work is the owner's problem to see,
    # not a feature that quietly disappears.
    if st.session_state.get("samples_problem"):
        write(ui.status("warning", "Samples", st.session_state["samples_problem"]))
    # What each door costs, said where the choice is made rather than on
    # a screen the reader has already dismissed.
    write(ui.door_costs(has_samples))
    write(ui.home_foot())
    st.stop()


# ------------------------------------------------------------------ about

if st.session_state["view"] == "about" and report is None:
    _skip_link("ar-about", "Skip to the text")
    write('<span id="ar-about" tabindex="-1"></span>')
    # base_level=2, so the document's own "#" is the page title rather
    # than something smaller than its subheadings.
    write(ui.about(markdown.to_html(_about_text(), base_level=2)))
    if st.button("Back", key="about_back"):
        go("home")
    st.stop()


# ---------------------------------------------------------------- samples

if st.session_state["view"] == "samples" and report is None:
    _skip_link("ar-samples", "Skip to the samples")
    write('<span id="ar-samples" tabindex="-1"></span>')
    # Not `samples`: that is the module, imported above, and rebinding it
    # here would break any later call to samples.load in this block.
    notes = _samples()
    write(ui.samples_intro(len(notes)))

    back = st.columns([1, 1, 3])
    if back[0].button("Back", key="samples_back"):
        go("home")
    if back[1].button("Build one instead", key="samples_build"):
        go("tool")

    chosen = st.radio(
        "Sample note",
        [s.slug for s in notes],
        format_func=lambda slug: _sample_label(
            next(s.title for s in notes if s.slug == slug)
        ),
        horizontal=True,
        key="sample_pick",
    )
    note = next(s for s in notes if s.slug == chosen)
    st.download_button(
        "Download this note",
        data=note.html,
        file_name=f"{note.slug}-research-note.html",
        mime="text/html",
        key="sample_dl",
    )
    # Rendered in its own document rather than injected into this page:
    # each note is a complete HTML file carrying its own stylesheet, and
    # inlining it would let those rules reach the app around it.
    # Tall enough that the note reads as a document rather than through a
    # letterbox. A note measures about 33,000px; at 900 the reviewer saw
    # one thirty-sixth of it at a time, through a scrollbar nested inside
    # the page's own, with the note's sticky index trapped in the frame.
    # This cannot be made to fit - the honest fix is a page of its own -
    # but 2,000px stops the frame from being the thing they notice.
    components.html(note.html, height=2000, scrolling=True)
    st.stop()


# -------------------------------------------------------------- workspace

_run_pending()
report = st.session_state.get("report")

if report is None:
    _skip_link("ar-form", "Skip to the form")
    # One column. This was `st.columns([1.15, 1])` with nothing ever
    # written to the right half, so the screen where a reader decides
    # whether the tool is serious was 46% empty cream and looked like a
    # layout that had broken. The form sits at its own measure instead.
    write('<span id="ar-form" tabindex="-1"></span>')
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

_skip_link("ar-report", "Skip to report")
write('<span id="ar-report" tabindex="-1"></span>')
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

