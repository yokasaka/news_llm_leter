import hashlib

from rss_digest.dedup import canonical_url_hash, normalize_url


def test_normalize_url_removes_fragment_and_tracking_params():
    url = (
        "https://Example.COM/News/Story/?utm_source=feed&ref=homepage&ok=1#section"
    )
    assert normalize_url(url) == "https://example.com/News/Story?ok=1"


def test_normalize_url_trims_trailing_slash_for_non_root():
    url = "https://example.com/path/subpath/"
    assert normalize_url(url) == "https://example.com/path/subpath"


def test_normalize_url_keeps_root_slash():
    url = "https://example.com"
    assert normalize_url(url) == "https://example.com/"


def test_normalize_url_preserves_non_tracking_query_params():
    url = "https://example.com/a?b=2&utm_medium=feed&c=3"
    assert normalize_url(url) == "https://example.com/a?b=2&c=3"


def test_canonical_url_hash_is_sha256_of_normalized_url():
    url = "https://Example.com/a/#fragment"
    normalized = "https://example.com/a"
    expected_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    assert canonical_url_hash(url) == expected_hash
