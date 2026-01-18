"""Summarization service for items."""

from __future__ import annotations


class Summarizer:
    def summarize(self, url: str) -> str:
        raise NotImplementedError


class SimpleSummarizer(Summarizer):
    def summarize(self, url: str) -> str:
        return f"Summary for {url}"
