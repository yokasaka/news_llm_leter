from rss_digest.services.rss.discovery import RssDiscoveryService


def test_rss_discovery_finds_alternate_links():
    html = """
    <html>
      <head>
        <link rel="alternate" type="application/rss+xml" href="/feed.xml" title="RSS">
        <link rel="alternate" type="application/atom+xml" href="https://example.com/atom.xml">
        <link rel="stylesheet" href="/style.css">
      </head>
    </html>
    """
    service = RssDiscoveryService()
    candidates = service.discover("https://example.com", html)

    assert [candidate.url for candidate in candidates] == [
        "https://example.com/feed.xml",
        "https://example.com/atom.xml",
    ]
