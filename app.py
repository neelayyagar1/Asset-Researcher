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
import secrets
import logging
import os
import re
import time
from html import escape

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
from asset_researcher import reports_store
from asset_researcher.ui import components as ui
from asset_researcher.ui import note_index
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
    #
    # The wait is refused at submission, not by removing the controls.
    # This branch used to render the countdown and return before the
    # form existed: no field, no button, nothing re-rendering when the
    # delay elapsed, and the countdown frozen at whatever second the
    # last attempt landed on. The only way forward was a page reload,
    # which the screen did not mention. That is the first screen of the
    # artifact, and a reviewer who mistypes four times met a dead end on
    # its front door.
    attempts = st.session_state.get("gate_attempts", 0)
    waiting = 0
    if attempts >= _GATE_FREE_ATTEMPTS:
        delay = min(2 ** (attempts - _GATE_FREE_ATTEMPTS), _GATE_MAX_DELAY)
        waited = time.monotonic() - st.session_state.get("gate_last", 0.0)
        if waited < delay:
            waiting = max(1, int(delay - waited))

    write(ui.gate())
    if waiting:
        write(ui.status(
            "warning", "Slow down",
            f"Too many attempts. Try again in {waiting} seconds; "
            f"pressing Enter will tell you how long is left.",
        ))
    # A form, so Return submits. A password box that ignores Return is
    # the most practised gesture in the world failing silently on the
    # first interaction, which reads as broken rather than as strict.
    with st.form("gate_form", clear_on_submit=True, border=False):
        entered = st.text_input(
            "Passphrase", type="password", key="gate_input",
            label_visibility="collapsed", placeholder="Passphrase",
        )
        submitted = st.form_submit_button("Enter", type="primary")
    if submitted and waiting:
        # Refused without touching the secret. The wait is enforced here
        # so the screen stays operable while it runs, and pressing Enter
        # reports the time left rather than appearing to do nothing.
        write(ui.status(
            "warning", "Slow down",
            f"Still waiting. Try again in {waiting} seconds.",
        ))
    elif submitted:
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
# Nothing decorative runs here.
#
# A design-direction contract used to be emitted at this point, as an
# HTML comment, before `write` was even defined. When the deployed
# process held a stale copy of the components module that one call
# raised AttributeError and the whole site served a red traceback
# instead of a gate - for a comment no reader ever sees. The design
# record lives in DESIGN.md and NOTES.md, where it cannot take the
# product down.

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


_LEAD_STAT = re.compile(
    r'<div class="ar-stat lead"><div class="ar-stat-label">(.*?)</div>'
    r'<div class="ar-stat-value[^"]*">(.*?)</div>',
    re.S,
)


def _framed(note_html: str) -> str:
    """A note about to be shown inside the app's frame.

    Notes are artifacts: the six that ship were built by a pipeline run
    and carry whatever scripts the renderer emitted that day. Appending
    the frame-sizing script here rather than only at build time means a
    note built last month behaves like one built this minute, and the
    fix does not cost six API calls to deploy.

    Idempotent. A freshly built note carries the same function from
    `_JUMP_SCRIPT`; running it twice sets the same height twice.
    """
    from asset_researcher.ui.export import _JUMP_SCRIPT

    if "fitFrame" in note_html:
        return note_html
    if "</body>" in note_html:
        return note_html.replace("</body>", f"{_JUMP_SCRIPT}</body>", 1)
    return note_html + _JUMP_SCRIPT


def _headline_of(html: str) -> tuple[str, str]:
    """The note's own lead statistic, or two empty strings.

    Read out of the built note rather than recomputed, so the figure on
    the index is the figure in the document by construction. A note that
    declined to produce one returns empty and the cell stays blank: the
    index may not be the one place in this product where a number
    appears without a filing behind it.
    """
    match = _LEAD_STAT.search(html or "")
    if not match:
        return "", ""
    label, value = (re.sub(r"<[^>]+>", "", g).strip() for g in match.groups())
    return label, value


class _Doc:
    """One readable document, whatever it came from.

    The index used to list only the sealed samples, and a report a
    visitor generated appeared nowhere: it existed for the life of a
    websocket and then did not. Samples and generated reports are the
    same object to a reader - a rendered note with a title - so they
    are the same object here, and the screen that lists them does not
    have to know which is which.
    """

    __slots__ = ("slug", "title", "html")

    def __init__(self, slug: str, title: str, html: str) -> None:
        self.slug = slug
        self.title = title
        self.html = html


def _session_scope() -> str:
    """This visitor's own corner of the report store.

    The store is one directory in one container, and every visitor to
    the deployment shares that container. Unscoped, a reviewer who
    generated a report on a name they were considering put that name
    at the top of the index for every other reviewer holding the link.

    The scope rides in the query string for the same reason the unlock
    token does: a row on the index is a link, a link is a page load,
    and a page load is a new Streamlit session. Without it in the URL
    a reader would lose their own reports the first time they opened
    one. It is a random value, not derived from anything about the
    visitor, and it grants access to nothing but the reports made
    under it.
    """
    scope = st.session_state.get("scope") or st.query_params.get("sid") or ""
    if not _SCOPE_OK.match(scope or ""):
        scope = secrets.token_hex(8)
    if st.session_state.get("scope") != scope:
        st.session_state["scope"] = scope
    if st.query_params.get("sid") != scope:
        st.query_params["sid"] = scope
    return scope


def _store_stamp() -> float:
    """The report directory's modification time, as a cache key.

    Streamlit reruns the whole script on every interaction, and the
    home screen reads each saved report's full HTML - a quarter of a
    megabyte each - and regexes it for the index figures. Unscoped by
    a cache that is a few megabytes read and scanned before the page
    can draw, on every click, growing with each report generated. The
    sealed samples were already cached this way; these were not.

    Keyed on mtime rather than a timer: the directory changes exactly
    when a report is saved, which is the only moment the answer can
    differ.
    """
    try:
        return reports_store.directory(_session_scope()).stat().st_mtime
    except OSError:
        return 0.0


@st.cache_resource(show_spinner=False)
def _saved_documents(scope: str, stamp: float):
    """This visitor's saved reports, re-read only when one is added.

    Both arguments are cache keys and both have to be: scope so one
    visitor's cache cannot answer another's call, stamp so a report
    saved a second ago appears.
    """
    return reports_store.listing(scope=scope)


def _documents() -> list:
    """What there is to read: this visitor's reports, then the samples.

    Theirs first, because a report someone just generated is the thing
    they came back for, and the samples do not move.
    """
    mine = [
        _Doc(s.slug, s.title, s.html)
        for s in _saved_documents(_session_scope(), _store_stamp())
    ]
    shipped = [_Doc(s.slug, s.title, s.html) for s in _samples()]
    # A generated report's slug carries a timestamp, so it cannot
    # collide with a sample's - but the index is addressable by slug
    # and a collision would make one document unreachable rather than
    # merely duplicated, which is worth one line to rule out.
    seen = {d.slug for d in mine}
    return mine + [d for d in shipped if d.slug not in seen]


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
_SCOPE_OK = re.compile(r"\A[a-f0-9]{16}\Z")

_VIEWS = ("home", "tool", "samples", "report")


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
    # A RAW string. The JavaScript below contains `\n` escapes inside a
    # JS string literal, and in a non-raw Python literal Python consumed
    # them first: the browser was served a single-quoted JS string with
    # two real newlines inside it, which is a SyntaxError, so the whole
    # listener never parsed and browser Back silently did nothing. The
    # in-app Back buttons kept working because those are server-side
    # widgets, which is exactly why the fault looked like "only your
    # buttons work".
    components.html(
        r"""<script>
        (function () {
          // The window that owns the ADDRESS BAR, which is not always
          // the one above this frame.
          //
          // This read `window.parent`. From a component iframe that is
          // the app window, which is correct on a directly served
          // Streamlit and wrong on Streamlit Cloud, where the whole app
          // runs inside `//<app>.streamlit.app/~/+/`. There, Back fires
          // on the top window and the listener never heard it: the
          // address bar went back and the page stayed put, which is the
          // original fault, unfixed in production while every local
          // check passed. A directly served app is not framed, so
          // window.top and window.parent are the same object and the
          // broken code looks correct.
          //
          // Both frames are same-origin. Reaching across origins throws,
          // so the reach is guarded and falls back to the parent.
          var host;
          try {
            host = window.top && window.top.location ? window.top
                                                     : window.parent;
          } catch (e) {
            host = window.parent;
          }
          // The app's own window, which is where the report lives.
          // On Streamlit Cloud these are two different windows: the top
          // window holds the Cloud chrome and the address bar, the app
          // runs in an iframe inside it. Binding popstate to the top
          // window and then looking for the report in the top window's
          // document found nothing, so the confirm never fired and Back
          // silently discarded a note that cost a minute and a dollar.
          var appWindow = window.parent || host;
          if (!host || host.__arBack) return;
          host.__arBack = true;
          host.addEventListener('popstate', function () {
            // A reload is the only way to follow Back, and a reload
            // ends the Streamlit session - which takes the LIVE report
            // with it. That used to mean losing the work, and the guard
            // asked every time. It no longer does: the rendered
            // document is written to disk before this screen draws and
            // the first screen links to it, so the only case left worth
            // asking about is a save that failed.
            var hasReport = null;
            try {
              hasReport = appWindow.document.getElementById('ar-report');
            } catch (e) {
              // Unreachable document: treat as no report rather than
              // blocking navigation on a guess.
            }
            // Only when the save failed. A saved report is in the
            // list on the first screen, so leaving loses the live
            // view and not the work.
            var unsaved = hasReport
              && hasReport.getAttribute('data-saved') !== '1';
            if (unsaved && !host.confirm(
                  'This report could not be saved, so leaving this page '
                  + 'loses it. Download it first if you want to keep '
                  + 'it.\n\nLeave anyway?')) {
              // Put the entry back, so the address bar matches the page.
              host.history.forward();
              return;
            }
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
    st.caption(
        "A US-listed company symbol. The tool looks it up in the SEC's own "
        "ticker list, so anything that files with the SEC works and "
        "anything else is refused by name."
    )
    # "Strategy", not "Mandate". The word mandate is real and citable -
    # CFA Standard III(C) uses "mandate, strategy, or style" in sequence -
    # but a mandate is a document agreed between an asset owner and a
    # manager, not a line someone types into a box, and "Long-only,
    # quality compounders" is a style. The word stays where the object
    # genuinely is one: MandateProfile, and the note's "Prepared for" line.
    choice = st.selectbox(
        "Strategy",
        ["Describe my own"] + [p.name for p in presets],
        index=1,
        key=f"{key}_preset",
    )
    prefill = (
        ""
        if choice == "Describe my own"
        else next(p.description for p in presets if p.name == choice)
    )
    # Streamlit ignores `value=` once a keyed widget exists: on every
    # rerun after the first, session state wins. So changing the
    # selector recomputed the prefill and the field kept whatever was
    # in it - choosing "Describe my own" left the previous preset's
    # paragraph sitting in a box labelled as the reader's own words,
    # which is the one field here that must not put words in their
    # mouth. The seed is written into state when, and only when, the
    # selection changes, so an edited description survives a rerun but
    # a new selection replaces it.
    seen = f"{key}_preset_seen"
    if st.session_state.get(seen) != choice:
        st.session_state[seen] = choice
        st.session_state[f"{key}_mandate"] = prefill
    # Tall enough for the seeded description. At 110 the default content
    # was cut through the middle of a line of type, so the first thing a
    # reader saw of the field they most need to read was the app failing
    # to hold its own text.
    mandate_text = st.text_area(
        "How you invest", value=prefill, height=150,
        key=f"{key}_mandate",
    )
    # Plain words first, then the term of art, rather than the term alone.
    # A reviewer who does not work in finance read "Mandate" and could not
    # tell whether it was real vocabulary or invented, which is a fair
    # reaction to a one-word label with nothing around it. A mandate is
    # the standing brief a fund is run to; saying what it does here means
    # a reader needs no glossary, and a portfolio manager still sees the
    # word they would use themselves.
    st.caption(
        "Horizon, what you hold, and what would make you sell. This "
        "changes which findings the note leads with and in what order. It "
        "does not change a single reported figure, a citation, or which "
        "disagreements with management get disclosed."
    )
    urls_text = st.text_area(
        "Other documents to read (URLs, optional)", height=70,
        placeholder="https://  one per line",
        key=f"{key}_urls",
    )
    # No running budget figure here. It used to print the remaining daily
    # allowance, which told a reviewer a number that is none of their
    # business and invited them to treat the demo as a meter rather than
    # as a research tool. The cap still binds; it simply does so quietly,
    # and says so only in the one case where it has to - when a run is
    # refused, which is the only moment the figure explains anything.
    st.caption(
        "Leave this empty and the note is built from SEC filings alone. "
        "Paste a public web page - a transcript, a press release, a broker "
        "note - and it is read alongside them. Anything found this way is "
        "labelled as a secondary source and attributed as opinion, never "
        "mixed in with the filed figures."
    )
    # Back sits with the action it is an alternative to, at the foot of
    # the form, rather than above it where it read as a page control. The
    # primary keeps most of the width; leaving is the smaller gesture.
    #
    # The secondary action depends on where this form is. On the empty
    # workspace it is a page control and goes home. Inside the New report
    # dialog it is a dismissal, and labelling it "Back" while navigating
    # the page behind the modal to home meant the dismissal-shaped
    # control walked away from a report that cost a minute and about a
    # dollar - the opposite of what a reader reaches for it to do.
    in_dialog = key == "dialog"
    row = st.columns([3, 1])
    run = row[0].button(
        "Generate report", type="primary", use_container_width=True,
        key=f"{key}_run",
    )
    if row[1].button(
        "Cancel" if in_dialog else "Back",
        use_container_width=True, key=f"{key}_back",
    ):
        if in_dialog:
            st.rerun()  # closes the dialog, leaving the report on screen
        else:
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
        # A placeholder that IS the live region, re-rendered per stage.
        #
        # The previous version wrote the region as one closed markdown
        # element and then wrote the stage lines after it with st.write.
        # st.markdown is not a container: its div closes, and every
        # stage line landed as a sibling outside the region, so nothing
        # was ever announced. The comment above it said the opposite -
        # the second time in this file that a note described an
        # intention rather than the code - which is why the stage text
        # is now inside the markup the region owns, where it can be seen
        # to be there.
        stage_slot = st.empty()

        def say(sentence: str) -> None:
            """Show a stage, and announce it once."""
            # No `aria-busy`. It was set here on every render and
            # never cleared, and aria-busy="true" instructs assistive
            # technology to withhold changes until it is false - so a
            # conforming screen reader announced none of the stages of
            # a ninety-second run. There is nothing for it to mark
            # anyway: the stage text IS the status, and the bar beside
            # it is already aria-hidden.
            stage_slot.markdown(
                '<div role="status" aria-live="polite" aria-atomic="true">'
                f"<p class=\"ar-stage\">{escape(sentence)}</p>"
                '<div class="ar-progress" aria-hidden="true"><i></i></div>'
                "</div>",
                unsafe_allow_html=True,
            )

        for url in urls:
            try:
                user_sources.append(fetch_user_source(url))
                st.write(f"Source accepted: {url}")
            except UrlRejected as exc:
                st.write(f"Source rejected ({url}): {exc}")

        say("Retrieving filings, market data and the peer set")
        bundle = assemble_bundle(ticker, settings, edgar, finnhub, llm)
        st.write(
            f"{len(bundle.passages)} passages, "
            f"{bundle.total_passage_chars:,} characters"
        )

        say("Parsing mandate")
        mandate = (
            parse_mandate(mandate_text, llm)
            if mandate_text.strip()
            else default_profile()
        )

        say("Drafting descriptive sections and verifying citations")
        narrative = generate_narrative(
            bundle,
            llm,
            effort=settings.llm.effort.get("narrative", "medium"),
            user_sources=user_sources,
        )

        say("Reconciling the narrative against filed figures")
        reconciliation = generate_reconciliation(
            bundle,
            narrative,
            mandate,
            llm,
            effort=settings.llm.effort.get("reconciliation", "high"),
        )
        status.update(label=f"{ticker} complete", state="complete", expanded=False)

    return build_report(bundle, mandate, narrative, reconciliation)


def _failure_message(exc: BaseException) -> str:
    """What a reader is told when a run fails.

    Never `str(exc)`. The deployment sets `showErrorDetails` to none so
    a traceback cannot reach a visitor, and this line printed the
    exception text straight into the page anyway - which is the same
    disclosure by a different route, and can carry a URL, a provider's
    error body or a key name.

    Mapped to what the reader can act on instead. The exception is still
    raised into the server log, where the owner can read it.
    """
    name = type(exc).__name__
    text = str(exc).lower()

    if "ticker" in text or "not found" in text or name == "KeyError":
        return (
            "That ticker was not found in the SEC's own ticker list. Check "
            "the symbol and try again - the tool covers US-listed filers "
            "only."
        )
    if "budget" in text or "cap" in text or "spend" in text:
        return (
            "The spending cap for this demo has been reached, so no new "
            "report can be built. The sample notes are still available and "
            "cost nothing."
        )
    if any(word in text for word in ("timeout", "timed out", "connection",
                                     "network", "503", "502")):
        return (
            "A source did not answer in time. This is usually temporary; "
            "trying again in a minute often works."
        )
    if "403" in text or "rate" in text:
        return (
            "SEC EDGAR refused the request, which it does when it is busy. "
            "Waiting a minute and trying again usually clears it."
        )
    if "api" in text or "auth" in text or "401" in text:
        return (
            "The model provider rejected the request. This is a "
            "configuration problem rather than something you can fix from "
            "here; the owner has been given the detail in the logs."
        )
    return (
        "The report could not be generated. The failure has been recorded "
        "in the server log; nothing was charged for an incomplete run."
    )


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
        # Logged with its traceback for the owner; the reader is told
        # what they can do about it.
        logging.getLogger("asset_researcher").exception(
            "report generation failed for %s", ticker
        )
        # Held, not drawn here. `_run_pending` executes before any view
        # writes its chrome, so rendering the failure at this point put
        # the error and its Try again button above the topbar, with the
        # form restated underneath - a message floating above the page
        # it belongs to. The workspace draws it in place.
        #
        # urls_text, not urls: that slot is unpacked above as the raw
        # textarea contents and split here, so storing the parsed list
        # would hand a list to `.splitlines()` on the next run.
        st.session_state["failure"] = (
            _failure_message(exc),
            (ticker, mandate_text, urls_text),
        )
        return
    st.session_state.pop("failure", None)
    if fresh is not None:
        st.session_state["report"] = fresh
        # Cleared before the attempt. It was only ever set, never
        # reset, so after one successful save the Back guard believed
        # every later report was on disk - including one whose save
        # raised, which is the single case the guard exists for.
        st.session_state.pop("report_slug", None)
        # Written down before it is shown. The index on the first
        # screen is a table of links now, and a link is a page load:
        # without this, the first row a reader clicked would end the
        # session holding the report they had just paid for. A failure
        # to save is not a reason to lose the report that is in hand,
        # so it is logged and the screen carries on.
        try:
            saved = reports_store.save(
                fresh.ticker,
                f"{fresh.bundle.company_name} ({fresh.ticker})",
                report_to_html(fresh),
                scope=_session_scope(),
            )
            st.session_state["report_slug"] = saved.slug
        except Exception:
            logging.getLogger("asset_researcher").exception(
                "could not save the rendered report for %s", fresh.ticker
            )
        # A finished run is its own screen. Without this the report was
        # not a view at all: it rendered whenever one existed, whatever
        # the view said, which is what made Home a dead button.
        st.session_state["view"] = "report"


# ------------------------------------------------------------------- home

if st.session_state["view"] == "home":
    # The link first, its target where the CONTENT starts. The span
    # used to sit above the topbar, so activating the link moved focus
    # backwards past the very thing it offers to skip.
    _skip_link("ar-home", "Skip to start")
    write(ui.topbar("reports"))
    write(ui.home())
    write('<span id="ar-home" tabindex="-1"></span>')

    notes = _documents()
    has_samples = bool(notes)

    # One column, not two. The listing used to sit in 1.9 of a 2.9-part
    # split with Get started in a rail beside it, which left a
    # four-column table rattling around in two thirds of a wide screen
    # and the lower half of the page empty - the owner's report was
    # "so much goddamn whitespace all around the front page".
    #
    # The table now runs the full measure and carries seven columns
    # instead of four, and the instructions sit beneath it as a row of
    # four steps rather than a stacked card. That is the right order
    # besides: a reader arriving at a tool they have been sent looks
    # first at what it produced, and reads how to drive it second.
    rows = []
    for note in notes:
        label = _sample_label(note.title)
        name, _, ticker = label.rpartition("(")
        figures = note_index.summarise(note.html)
        rows.append(
            {
                "ticker": ticker.rstrip(")") or note.slug.upper(),
                "company": name.strip() or label,
                "slug": note.slug,
                **figures,
            }
        )
    write(ui.head("Reports", "Built from live filings by the same pipeline "
                  "the tool runs. Open one to read it; reports you "
                  "generate join the list."))
    write(ui.flush_card(ui.report_rows(rows, token=_unlock_token(), scope=_session_scope())))
    if st.session_state.get("samples_problem"):
        write(ui.status("warning", "Samples",
                        st.session_state["samples_problem"]))

    write(ui.head("Get started"))
    write(ui.card(ui.steps(ui.STEPS)))

    # The action, then the way back to a held report. Sized rather than
    # stretched: a primary button spanning 1120px reads as a banner.
    acts = st.columns([1.4, 1.4, 4])
    if acts[0].button(ui.START_LABEL, type="primary",
                      use_container_width=True, key="enter"):
        go("tool")
    # A held report is reachable again. Leaving one is navigation, not
    # disposal: it cost a minute and about a dollar, so the only thing
    # that throws it away is the browser's own Back, which asks first.
    if st.session_state.get("report") is not None:
        if acts[1].button("Return to report", use_container_width=True,
                          key="back_to_report"):
            go("report")
    st.stop()


# ---------------------------------------------------------------- samples

if st.session_state["view"] == "samples":
    _skip_link("ar-samples", "Skip to the samples")
    # Not `samples`: that is the module, imported above, and rebinding it
    # here would break any later call to samples.load in this block.
    notes = _documents()
    write(ui.topbar("samples"))
    write('<span id="ar-samples" tabindex="-1"></span>')

    # Before any control. This view is addressable by URL, so a bookmark,
    # a pasted link or the browser's Back reaches it whether or not the
    # button that leads here was ever rendered - and with no archive the
    # radio below was built over an empty list and raised StopIteration
    # into a red error panel, which is the most expensive single thing
    # that can happen on a page a reader is judging.
    if not notes:
        write(ui.samples_empty())
        if st.session_state.get("samples_problem"):
            write(ui.status("warning", "Samples",
                            st.session_state["samples_problem"]))
        gone = st.columns([1, 1, 3])
        if gone[0].button("Back", key="samples_back_empty"):
            go("home")
        if gone[1].button(ui.START_LABEL, key="samples_build_empty"):
            go("tool")
        st.stop()

    write(ui.samples_intro(len(notes)))

    back = st.columns([1, 1, 3])
    if back[0].button("Back", key="samples_back"):
        go("home")
    if back[1].button(ui.START_LABEL, key="samples_build"):
        go("tool")

    # A row on the index links here with the document it wants in `s`,
    # which is how a clickable row reaches a specific report. The
    # parameter is hostile input: it is matched against the documents
    # that exist rather than used to find one, so an unknown or hand-
    # edited value falls back to the first rather than raising.
    #
    # Written into the widget's state rather than passed as an index,
    # because the radio owns its selection after the first render and
    # an index argument would be ignored from then on - the same
    # Streamlit rule that left the strategy box holding a preset the
    # reader had deselected.
    asked = st.query_params.get("s") or ""
    if asked and any(d.slug == asked for d in notes):
        if st.session_state.get("sample_asked") != asked:
            st.session_state["sample_asked"] = asked
            st.session_state["sample_pick"] = asked

    chosen = st.radio(
        "Report",
        [s.slug for s in notes],
        format_func=lambda slug: _sample_label(
            next(s.title for s in notes if s.slug == slug)
        ),
        horizontal=True,
        key="sample_pick",
    )
    note = next((s for s in notes if s.slug == chosen), notes[0])
    st.download_button(
        "Download this note",
        data=note.html,
        file_name=f"{note.slug}-research-note.html",
        mime="text/html",
        key="sample_dl",
    )
    # NOTE: `components.v1.html` is deprecated and Streamlit's own warning
    # gives a removal date that has now passed, so this call is on
    # borrowed time. `st.iframe` is not a replacement for it: that takes a
    # URL or a path, and this needs to render a complete HTML document
    # held in memory. Migrating means serving each note at its own route,
    # which is the right answer for other reasons too - it would end the
    # scroll-within-a-scroll - but it is a change of shape, not a swap.
    #
    # Rendered in its own document rather than injected into this page:
    # each note is a complete HTML file carrying its own stylesheet, and
    # inlining it would let those rules reach the app around it.
    # 2,000px is the height Streamlit is told; the note then sizes its
    # own frame to its content, because the frame is same-origin and the
    # document inside it can reach `window.frameElement`. Measured: a
    # note runs 36,843px and the frame now matches it, so the page
    # scrolls once through Streamlit's own container and the note's
    # section index is no longer trapped behind a nested scrollbar.
    #
    # The comment here used to say this could not be made to fit and
    # that the honest fix was a page of its own. The second half is
    # still true - a note deserves its own route - but "cannot" was
    # wrong, and it had stopped anyone looking.
    components.html(_framed(note.html), height=2000, scrolling=True)
    st.stop()


# -------------------------------------------------------------- workspace

_run_pending()
report = st.session_state.get("report")

# Only the report view shows a report, and it needs one to show. A view
# asking for a report that is no longer held falls back to the form
# rather than rendering a blank screen.
if st.session_state["view"] == "report" and report is None:
    st.session_state["view"] = "tool"

if st.session_state["view"] != "report" or report is None:
    _skip_link("ar-form", "Skip to the form")
    # One column. This was `st.columns([1.15, 1])` with nothing ever
    # written to the right half, so the screen where a reader decides
    # whether the tool is serious was 46% empty cream and looked like a
    # layout that had broken. The form sits at its own measure instead.
    write(ui.topbar("tool"))
    write(ui.workspace_intro())
    failure = st.session_state.get("failure")
    if failure:
        message, previous = failure
        write(ui.status("error", "Failed", message))
        if st.button("Try again", key="retry_failed"):
            st.session_state["pending"] = previous
            st.session_state.pop("failure", None)
            st.rerun()
    # Below the heading and below any failure message, so "Skip to the
    # form" lands at the form rather than above the page.
    write('<span id="ar-form" tabindex="-1"></span>')
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

# The bar the rest of the shell carries. This screen is the longest in
# the product and had no persistent chrome at all, so a reader deep in a
# 33,000px note had no indication of where they were and no way out
# except the browser's Back - which ends the session holding the live
# report, though the rendered document survives in the index.
# The marker the stylesheet widens the column for. It was declared and
# never emitted, so the report screen - the one that needs the width for
# a sixteen-column comparables table - was rendering in the standard
# column the whole time.
write('<span class="ar-report-view" hidden></span>')
write(ui.topbar("report"))
# Before the action row. This was emitted after New report, Home, HTML
# and Markdown, so on the longest screen in the product the bypass was
# the fifth tab stop rather than the first.
_skip_link("ar-report", "Skip to report")

# A new report is an occasional act once one is on screen, so the form is
# behind a control rather than occupying the top of every page. Home is
# beside it, because leaving should be a control in the page rather than
# a browser gesture that costs the artifact.
actions = st.columns([4, 1.1, 1.1, 1.3, 1.1])
if actions[3].button("New report", use_container_width=True, key="new"):
    _new_report_dialog()
if actions[4].button("Home", use_container_width=True, key="to_home"):
    go("home")
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

# The marker the Back guard looks for, carrying whether this report
# was written to disk. It almost always was - `_run_pending` saves the
# rendered document before this screen draws - and when it was, leaving
# costs the live view and nothing else, because the index links to the
# file. The guard reads this rather than asking on every Back, which is
# the friction the owner has objected to three times.
write(
    '<span id="ar-report" tabindex="-1" data-saved="'
    + ("1" if st.session_state.get("report_slug") else "0")
    + '"></span>'
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

