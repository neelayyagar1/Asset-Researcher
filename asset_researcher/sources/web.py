"""User-supplied URLs -> Tier C source text.

This is the feature the product thesis rests on: a fund's research process is
idiosyncratic, and supporting *their* sources is what separates this from a
tool that only reads filings.

It is also the only place where an untrusted string becomes an outbound
network request, which makes it the main security surface in the project.

# Server-Side Request Forgery

On a hosted deployment, anyone can type a URL. Without controls, that turns
this service into a proxy for reaching things it can reach and the user
cannot:

- **Cloud metadata endpoints.** `http://169.254.169.254/` returns instance
  credentials on AWS, GCP, and Azure. This is the single most exploited SSRF
  target and it is one HTTP GET away from a total compromise.
- **Loopback and private ranges.** `http://127.0.0.1:8501/`, `http://10.x`,
  `http://192.168.x` reach services bound to the host or the private network
  that are not otherwise exposed.
- **Non-HTTP schemes.** `file:///etc/passwd`, `gopher://`, `ftp://` read local
  files or speak to arbitrary TCP services.
- **Redirects.** A public URL may 302 to any of the above, so validating only
  the URL the user typed is not enough, every hop must be checked.

The controls below are deny-by-default: a scheme allowlist, DNS resolution
with every resolved address checked against private ranges, per-hop
revalidation with redirects followed manually, and hard caps on size and time.

**Known residual risk. DNS rebinding.** Validation resolves the hostname and
then issues the request, so a hostile resolver could return a public address
to the check and a private one to the connection. Closing that properly means
pinning the validated IP through the TLS layer, which `requests` does not
support cleanly. Given the deployment (a demo with a spend cap, no internal
network worth reaching), the residual risk is accepted and recorded rather
than papered over. If this ever runs inside a fund's network, this is the
first thing to fix.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

import requests

from asset_researcher.documents.extract import html_to_text
from asset_researcher.sources.base import SourceDocument, Tier

ALLOWED_SCHEMES = frozenset({"http", "https"})

MAX_REDIRECTS = 3
MAX_BYTES = 2_000_000  # a research article; anything larger is not prose
TIMEOUT_SECONDS = 15

# Content types worth extracting. A PDF or image would need a different
# reader, and refusing is clearer than returning mojibake.
ALLOWED_CONTENT_TYPES = ("text/html", "application/xhtml+xml", "text/plain")

_USER_AGENT = "Asset-Researcher/0.1 (research tool; contact via app operator)"


class UrlRejected(ValueError):
    """The URL was refused before any request was made, or mid-redirect.

    Carries a reason written for the person who typed it, a blocked URL
    should explain itself rather than fail opaquely.
    """


@dataclass(frozen=True)
class FetchedPage:
    url: str  # final URL after redirects
    title: str
    text: str
    truncated: bool


def _is_disallowed_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> str | None:
    """Reason this address is off-limits, or None if it is fine.

    `is_global` would cover most of this in one call, but enumerating the
    categories produces an error message that says *why*, which matters when
    a user is trying to work out whether their link is wrong or the tool is.
    """
    # Order matters, and only for the message, every branch blocks. Python's
    # ipaddress reports link-local and unspecified addresses as `is_private`
    # too, so testing `is_private` first would describe 169.254.169.254 as a
    # "private network address" and bury the fact that it is the cloud
    # metadata endpoint. Most specific category first.
    if ip.is_loopback:
        return "loopback address"
    if ip.is_link_local:
        return "link-local address (cloud metadata range)"
    if ip.is_unspecified:
        return "unspecified address"
    if ip.is_multicast:
        return "multicast address"
    if ip.is_private:
        return "private network address"
    if ip.is_reserved:
        return "reserved address"
    if not ip.is_global:
        return "non-public address"
    return None


_HEX_LABEL_PREFIXES = ("0x", "0X")


def _reject_ambiguous_numeric_host(hostname: str) -> None:
    """Refuse host strings that look like an address but do not parse as one.

    Found by testing real bypass strings against this validator: `0177.0.0.1`
    (octal), `0x7f.0.0.1` (hex), `2130706433` (32-bit integer) and `127.1`
    (short form) are all rejected by `ipaddress.ip_address`, so they fall
    through to DNS, where the resolver happily interprets them. Measured on
    macOS, every one of the last three resolves to 127.0.0.1, and `0177.0.0.1`
    resolves to a *public* 177.0.0.1 here while glibc reads the octal and
    returns loopback.

    That platform split is the actual danger: this validator resolves once and
    the HTTP client resolves again independently, so any string the two read
    differently defeats the check entirely, it would pass here and connect
    somewhere else in production.

    A legitimate website hostname is never all digits and dots, so refusing
    that shape closes the whole class rather than chasing each encoding.
    """
    labels = hostname.split(".")

    if any(label.lower().startswith(_HEX_LABEL_PREFIXES) for label in labels):
        raise UrlRejected(
            f"'{hostname}' uses hexadecimal address notation, which different "
            f"resolvers read differently. Use a normal hostname or a plain "
            f"dotted-quad address."
        )

    if all(character in "0123456789." for character in hostname):
        # Only reachable when ip_address() already rejected it, a well-formed
        # address is handled by the caller before this point.
        raise UrlRejected(
            f"'{hostname}' looks like a numeric address but is not a valid "
            f"one. Octal, hexadecimal and short-form addresses are refused "
            f"because different resolvers interpret them differently."
        )


def _resolve_and_validate(hostname: str) -> None:
    """Every address a hostname resolves to must be public.

    All records are checked, not just the first: a host with one public and
    one private A record would otherwise pass validation and then connect to
    the private one.
    """
    try:
        infos = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UrlRejected(f"Could not resolve host '{hostname}': {exc}") from exc

    if not infos:
        raise UrlRejected(f"Host '{hostname}' resolved to no addresses.")

    for info in infos:
        address = info[4][0]
        try:
            ip = ipaddress.ip_address(address)
        except ValueError:
            raise UrlRejected(f"Host '{hostname}' resolved to an unusable address.")
        reason = _is_disallowed_ip(ip)
        if reason:
            raise UrlRejected(
                f"'{hostname}' resolves to {address}, a {reason}. Only public "
                f"internet addresses can be fetched."
            )


def validate_url(url: str) -> str:
    """Check a URL and return it normalized. Raises UrlRejected otherwise."""
    url = (url or "").strip()
    if not url:
        raise UrlRejected("No URL supplied.")

    parsed = urlparse(url)

    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UrlRejected(
            f"Scheme '{parsed.scheme or '(none)'}' is not allowed. Use http or "
            f"https, file, ftp, gopher and similar schemes are refused."
        )

    if not parsed.hostname:
        raise UrlRejected("URL has no hostname.")

    # A bare IP is checked directly; a name is resolved first.
    try:
        ip = ipaddress.ip_address(parsed.hostname)
    except ValueError:
        # Refuse address-shaped strings that do not parse cleanly before
        # handing anything to the resolver.
        _reject_ambiguous_numeric_host(parsed.hostname)
        _resolve_and_validate(parsed.hostname)
    else:
        reason = _is_disallowed_ip(ip)
        if reason:
            raise UrlRejected(
                f"{parsed.hostname} is a {reason}. Only public internet "
                f"addresses can be fetched."
            )

    return url


def fetch_url(url: str, timeout: int = TIMEOUT_SECONDS) -> FetchedPage:
    """Fetch and extract a user-supplied page, validating every redirect hop."""
    current = validate_url(url)

    # A context manager, because every path out of this loop that is not the
    # happy one is a raise: a rejected redirect target, a redirect with no
    # Location, running out of hops. Each left a connection pool open, and
    # the interface accepts one URL per line.
    with requests.Session() as session:
        session.max_redirects = 0  # followed manually so each hop is revalidated

        for _ in range(MAX_REDIRECTS + 1):
            response = session.get(
                current,
                timeout=timeout,
                allow_redirects=False,
                stream=True,  # headers first, so a huge body is never buffered
                headers={
                    "User-Agent": _USER_AGENT,
                    "Accept": "text/html,text/plain",
                },
            )

            if response.is_redirect or response.is_permanent_redirect:
                location = response.headers.get("Location")
                response.close()
                if not location:
                    raise UrlRejected("Redirect with no destination.")
                current = requests.compat.urljoin(current, location)
                # The point of manual redirects: revalidate the new target.
                current = validate_url(current)
                continue

            return _read_body(response, current)

    raise UrlRejected(f"More than {MAX_REDIRECTS} redirects; giving up.")


def _read_body(response: requests.Response, url: str) -> FetchedPage:
    try:
        response.raise_for_status()

        # Fails closed. `if content_type and ...` let a response with no
        # Content-Type header skip the allowlist altogether, so arbitrary
        # bytes reached the extractor on the one input a stranger controls.
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        if not content_type:
            raise UrlRejected(
                "The response declared no content type, so it cannot be "
                "confirmed as readable text."
            )
        if not any(
            content_type.startswith(allowed) for allowed in ALLOWED_CONTENT_TYPES
        ):
            raise UrlRejected(
                f"Content type '{content_type}' is not readable as text. "
                f"HTML and plain text pages are supported."
            )

        chunks: list[bytes] = []
        total = 0
        truncated = False
        for chunk in response.iter_content(8192):
            chunks.append(chunk)
            total += len(chunk)
            if total >= MAX_BYTES:
                truncated = True
                break

        raw = b"".join(chunks).decode(
            response.encoding or "utf-8", errors="replace"
        )
    except requests.RequestException as exc:
        raise UrlRejected(f"Could not fetch the page: {exc}") from exc
    finally:
        response.close()

    text = html_to_text(raw) if "<" in raw[:2000] else raw
    return FetchedPage(
        url=url, title=_title_for(url, text), text=text.strip(), truncated=truncated
    )


def _title_for(url: str, text: str) -> str:
    host = urlparse(url).hostname or "user source"
    first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    if first_line and len(first_line) <= 120:
        return f"{first_line} ({host})"
    return host


def fetch_user_source(url: str) -> SourceDocument:
    """A user URL as a Tier C SourceDocument.

    Always Tier C. The content may well be excellent, but its provenance is
    unverified, so the prompt requires it to be attributed as opinion and
    never presented as established fact (ARCHITECTURE.md §4).
    """
    page = fetch_url(url)
    if not page.text:
        raise UrlRejected("The page contained no readable text.")

    # `truncated` was computed and discarded, so a page cut at the byte cap
    # entered the bundle looking complete. The project's first rule is that
    # nothing is silently missing, so the label carries it: the label is what
    # the citation and the sources table both show.
    label = f"User source: {page.title}"
    if page.truncated:
        label += " (truncated at the size limit)"

    return SourceDocument(
        text=page.text,
        tier=Tier.C_SECONDARY,
        label=label,
        source_url=page.url,
        as_of="",  # publication date is not reliably discoverable
    )
