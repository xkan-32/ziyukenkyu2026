"""Local queue storage wrapper."""

from __future__ import annotations

from app.models.local_queue import LocalQueueRecord
from app.storage.local_jsonl_store import LocalJsonlStore


class LocalQueueStore:
    def __init__(self, jsonl_store: LocalJsonlStore) -> None:
        self.jsonl_store = jsonl_store

    def enqueue(self, record: LocalQueueRecord) -> None:
        self.jsonl_store.enqueue_for_sync(record)
