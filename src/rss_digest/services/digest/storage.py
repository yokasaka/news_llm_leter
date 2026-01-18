"""Markdown storage utilities."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID


@dataclass
class StorageResult:
    path: str


class StorageService:
    def __init__(self, base_dir: Path) -> None:
        self._base_dir = base_dir

    def save_digest(self, group_id: UUID, scheduled_at: datetime, markdown: str) -> StorageResult:
        filename = f"{scheduled_at:%Y%m%d%H%M}.md"
        path = self._base_dir / str(group_id) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        return StorageResult(path=str(path))
