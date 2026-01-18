"""Relevance evaluation for feed items."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EvaluationResult:
    score: float
    decision: str
    reason: str


class RelevanceEvaluator:
    def evaluate(self, url: str) -> EvaluationResult:
        raise NotImplementedError


class KeywordRelevanceEvaluator(RelevanceEvaluator):
    def __init__(self, include_keywords: list[str] | None = None) -> None:
        self._keywords = [keyword.lower() for keyword in (include_keywords or [])]

    def evaluate(self, url: str) -> EvaluationResult:
        lowered = url.lower()
        for keyword in self._keywords:
            if keyword in lowered:
                return EvaluationResult(score=0.9, decision="include", reason="keyword")
        return EvaluationResult(score=0.1, decision="exclude", reason="no_keyword")
