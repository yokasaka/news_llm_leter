"""RSS discovery service to find feed URLs from site HTML."""

from __future__ import annotations

from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin


@dataclass
class FeedCandidate:
    url: str
    type: str
    title: str | None = None


class _LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        attr_map = {key.lower(): value for key, value in attrs if value is not None}
        rel = attr_map.get("rel", "").lower()
        if "alternate" in rel:
            self.links.append(attr_map)


class RssDiscoveryService:
    def discover(self, base_url: str, html: str) -> list[FeedCandidate]:
        parser = _LinkCollector()
        parser.feed(html)
        candidates: list[FeedCandidate] = []
        for link in parser.links:
            link_type = link.get("type", "")
            if "rss" not in link_type and "atom" not in link_type:
                continue
            href = link.get("href")
            if not href:
                continue
            candidates.append(
                FeedCandidate(
                    url=urljoin(base_url, href),
                    type=link_type,
                    title=link.get("title"),
                )
            )
        return candidates
