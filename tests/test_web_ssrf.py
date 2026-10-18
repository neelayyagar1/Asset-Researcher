"""SSRF controls on user-supplied URLs.

This is the only place an untrusted string becomes an outbound request, and
the service will be publicly hosted. These tests encode the attacks that
matter rather than the happy path.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from asset_researcher.sources.base import Tier
from asset_researcher.sources.web import (
    UrlRejected,
    fetch_user_source,
    validate_url,
)


def _resolves_to(address: str):
    """Patch DNS so a public-looking hostname resolves where we choose."""
    return patch(
        "asset_researcher.sources.web.socket.getaddrinfo",
        return_value=[(2, 1, 6, "", (address, 443))],
    )


# --- scheme allowlist ---------------------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com/x",
        "gopher://example.com:70/_GET",
        "data:text/html,<script>alert(1)</script>",
        "javascript:alert(1)",
    ],
)
def test_non_http_schemes_are_refused(url):
    with pytest.raises(UrlRejected, match="not allowed"):
        validate_url(url)


# --- address ranges -----------------------------------------------------


@pytest.mark.parametrize(
    "url,expected",
    [
        ("http://127.0.0.1:8501/", "loopback"),
        ("http://localhost:8501/", "loopback"),
        ("http://10.0.0.5/admin", "private"),
        ("http://192.168.1.1/", "private"),
        ("http://172.16.0.1/", "private"),
        ("http://[::1]/", "loopback"),
        ("http://0.0.0.0/", "unspecified"),
    ],
)
def test_private_and_loopback_addresses_are_refused(url, expected):
    with pytest.raises(UrlRejected, match=expected):
        validate_url(url)


def test_cloud_metadata_endpoint_is_refused():
    """169.254.169.254 returns instance credentials on AWS, GCP and Azure.
    the single most exploited SSRF target."""
    with pytest.raises(UrlRejected, match="link-local"):
        validate_url("http://169.254.169.254/latest/meta-data/")


def test_a_public_hostname_resolving_to_metadata_is_refused():
    """Checking the literal string is not enough: an attacker controls their
    own DNS and can point a public name at a private address."""
    with _resolves_to("169.254.169.254"):
        with pytest.raises(UrlRejected, match="link-local"):
            validate_url("https://evil.example.com/")


def test_every_resolved_address_is_checked_not_just_the_first():
    """A host with one public and one private record would otherwise pass
    validation and then connect to the private one."""
    infos = [
        (2, 1, 6, "", ("93.184.216.34", 443)),
        (2, 1, 6, "", ("10.0.0.5", 443)),
    ]
    with patch(
        "asset_researcher.sources.web.socket.getaddrinfo", return_value=infos
    ):
        with pytest.raises(UrlRejected, match="private"):
            validate_url("https://mixed.example.com/")


def test_a_genuinely_public_url_passes():
    with _resolves_to("93.184.216.34"):
        assert validate_url("https://example.com/article") == (
            "https://example.com/article"
        )


def test_unresolvable_host_is_refused_clearly():
    import socket as _socket

    with patch(
        "asset_researcher.sources.web.socket.getaddrinfo",
        side_effect=_socket.gaierror("nodename nor servname provided"),
    ):
        with pytest.raises(UrlRejected, match="Could not resolve"):
            validate_url("https://nonexistent.invalid/")


def test_empty_and_malformed_urls_are_refused():
    with pytest.raises(UrlRejected):
        validate_url("")
    with pytest.raises(UrlRejected):
        validate_url("https://")


# --- redirects ----------------------------------------------------------


class _Response:
    def __init__(self, status=200, headers=None, body=b"", url=""):
        self.status_code = status
        self.headers = headers or {}
        self._body = body
        self.url = url
        self.encoding = "utf-8"
        self.closed = False

    @property
    def is_redirect(self):
        return self.status_code in (301, 302, 303, 307, 308)

    is_permanent_redirect = is_redirect

    def iter_content(self, n):
        yield self._body

    def raise_for_status(self):
        if self.status_code >= 400:
            raise __import__("requests").HTTPError(f"status {self.status_code}")

    def close(self):
        self.closed = True


def test_a_redirect_into_the_metadata_endpoint_is_caught():
    """Validating only the URL the user typed is insufficient, a public page
    can 302 anywhere."""
    redirect = _Response(302, {"Location": "http://169.254.169.254/latest/"})

    with _resolves_to("93.184.216.34"), patch(
        "asset_researcher.sources.web.requests.Session.get", return_value=redirect
    ):
        with pytest.raises(UrlRejected, match="link-local"):
            fetch_user_source("https://innocent.example.com/")


def test_a_redirect_loop_terminates():
    loop = _Response(302, {"Location": "https://example.com/again"})
    with _resolves_to("93.184.216.34"), patch(
        "asset_researcher.sources.web.requests.Session.get", return_value=loop
    ):
        with pytest.raises(UrlRejected, match="redirects"):
            fetch_user_source("https://example.com/start")


# --- body handling ------------------------------------------------------


def test_non_text_content_is_refused_rather_than_mangled():
    pdf = _Response(200, {"Content-Type": "application/pdf"}, b"%PDF-1.7")
    with _resolves_to("93.184.216.34"), patch(
        "asset_researcher.sources.web.requests.Session.get", return_value=pdf
    ):
        with pytest.raises(UrlRejected, match="not readable as text"):
            fetch_user_source("https://example.com/paper.pdf")


def test_a_fetched_page_is_always_tier_c():
    """Content may be excellent, but its provenance is unverified, the
    prompt requires Tier C material to be attributed as opinion."""
    html = b"<html><body><p>Analyst thinks margins will compress.</p></body></html>"
    page = _Response(200, {"Content-Type": "text/html"}, html)

    with _resolves_to("93.184.216.34"), patch(
        "asset_researcher.sources.web.requests.Session.get", return_value=page
    ):
        doc = fetch_user_source("https://example.com/note")

    assert doc.tier is Tier.C_SECONDARY
    assert "margins will compress" in doc.text
    assert doc.source_url == "https://example.com/note"


def test_an_empty_page_is_refused_rather_than_added_as_a_blank_source():
    page = _Response(200, {"Content-Type": "text/html"}, b"<html><body></body></html>")
    with _resolves_to("93.184.216.34"), patch(
        "asset_researcher.sources.web.requests.Session.get", return_value=page
    ):
        with pytest.raises(UrlRejected, match="no readable text"):
            fetch_user_source("https://example.com/blank")


# --- ambiguous numeric encodings ---------------------------------------


@pytest.mark.parametrize(
    "url",
    [
        "http://0177.0.0.1/",        # octal
        "http://017700000001/",      # octal, long form
        "http://2130706433/",        # 32-bit integer
        "http://0x7f.0.0.1/",        # hexadecimal label
        "http://0x7f000001/",        # hexadecimal, whole address
        "http://127.1/",             # short form
    ],
)
def test_alternate_ip_encodings_are_refused(url):
    """Found by running real bypass strings against this validator: all of
    these are rejected by ipaddress.ip_address and so fall through to DNS,
    where resolvers happily interpret them. On macOS 2130706433, 0x7f.0.0.1,
    127.1 and 017700000001 all resolve to 127.0.0.1, while 0177.0.0.1
    resolves to a public 177.0.0.1 here and to loopback under glibc.

    That split is the real hazard: this validator resolves once and the HTTP
    client resolves again, so a string the two read differently passes the
    check and connects elsewhere."""
    with pytest.raises(UrlRejected):
        validate_url(url)


def test_ordinary_hostnames_containing_digits_still_work():
    """The numeric-shape rule must not catch real sites."""
    for host in ("3m.com", "s3.amazonaws.com", "news24.example.org"):
        with _resolves_to("93.184.216.34"):
            assert validate_url(f"https://{host}/page")


def test_a_plain_dotted_quad_public_address_is_still_accepted():
    assert validate_url("https://93.184.216.34/article")
