"""Evaluate and summarize items since a given time."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from rss_digest.db.models import GroupItem, ItemEvaluation, ItemSummary
from rss_digest.repository import (
    GroupItemsRepo,
    ItemEvaluationsRepo,
    ItemSummariesRepo,
    ItemsRepo,
)
from rss_digest.services.evaluation.relevance import RelevanceEvaluator
from rss_digest.services.evaluation.summarizer import Summarizer


@dataclass
class EvaluationSummaryResult:
    evaluations: list[ItemEvaluation]
    summaries: list[ItemSummary]


class EvaluationService:
    def __init__(
        self,
        items: ItemsRepo,
        group_items: GroupItemsRepo,
        evaluations: ItemEvaluationsRepo,
        summaries: ItemSummariesRepo,
        evaluator: RelevanceEvaluator,
        summarizer: Summarizer,
    ) -> None:
        self._items = items
        self._group_items = group_items
        self._evaluations = evaluations
        self._summaries = summaries
        self._evaluator = evaluator
        self._summarizer = summarizer

    def evaluate_since(self, group_id, since: datetime) -> EvaluationSummaryResult:
        target_items = self._group_items.list_since(group_id, since)
        evaluations: list[ItemEvaluation] = []
        summaries: list[ItemSummary] = []
        for group_item in target_items:
            if self._evaluations.find(group_id, group_item.item_id):
                continue
            item = self._items.get(group_item.item_id)
            if item is None:
                continue
            evaluation = self._evaluate_item(group_id, group_item, item.canonical_url)
            evaluations.append(evaluation)
            if evaluation.decision == "include":
                summary = self._summaries.find(group_id, group_item.item_id)
                if summary is None:
                    summary_text = self._summarizer.summarize(item.canonical_url)
                    summary = ItemSummary(
                        group_id=group_id,
                        item_id=group_item.item_id,
                        summary_md=summary_text,
                    )
                    self._summaries.add(summary)
                summaries.append(summary)
        return EvaluationSummaryResult(evaluations=evaluations, summaries=summaries)

    def _evaluate_item(
        self, group_id, group_item: GroupItem, url: str
    ) -> ItemEvaluation:
        result = self._evaluator.evaluate(url)
        evaluation = ItemEvaluation(
            group_id=group_id,
            item_id=group_item.item_id,
            relevance_score=result.score,
            decision=result.decision,
            reason=result.reason,
        )
        self._evaluations.add(evaluation)
        return evaluation
