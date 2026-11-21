"""The retry path round-trips the pending tuple in the shape it is read."""
def test_retry_preserves_the_pending_tuple_shape():
    import pathlib, re
    src = pathlib.Path("/Users/neelayyagari/Documents/GitHub/Asset-Researcher/app.py").read_text()
    unpack = re.search(r"ticker, mandate_text, (\w+) = pending", src).group(1)
    stored = re.search(r'st\.session_state\["pending"\] = \(ticker, mandate_text, (\w+)\)\n\s+st\.rerun', src)
    assert stored, "retry no longer stores a pending tuple"
    assert stored.group(1) == unpack, (
        f"retry stores {stored.group(1)!r} but _run_pending unpacks {unpack!r}; "
        "the next run would call .splitlines() on the wrong type"
    )
