"""Tests for Hugging Face collection sync helper."""

from __future__ import annotations

from typing import Any

from scripts import sync_hf_collection as module
from scripts.sync_hf_collection import (
    DEFAULT_COLLECTION_DESCRIPTION,
    HF_COLLECTION_DESCRIPTION_LIMIT,
    parse_args,
    sync_hf_collection,
)


def test_sync_collection_dry_run_uses_child_dataset_items() -> None:
    result = sync_hf_collection(
        title="hathitrust-nz",
        namespace="edithatogo",
        description="test",
        dry_run=True,
    )
    assert result["dry_run"] is True
    assert "edithatogo/corpus-nz-hathi" in {item["item_id"] for item in result["items"]}
    assert "edithatogo/hathitrust-nz-inventory" in {item["item_id"] for item in result["items"]}
    assert len(DEFAULT_COLLECTION_DESCRIPTION) <= HF_COLLECTION_DESCRIPTION_LIMIT


def test_sync_collection_truncates_long_description_in_dry_run() -> None:
    result = sync_hf_collection(
        title="hathitrust-nz",
        namespace="edithatogo",
        description="x" * 200,
        dry_run=True,
    )
    assert len(result["description"]) <= HF_COLLECTION_DESCRIPTION_LIMIT


def test_sync_collection_execute_creates_and_adds_items(monkeypatch: Any) -> None:
    class Collection:
        slug = "edithatogo/hathitrust-nz-test"

    class MockApi:
        def __init__(self, token: str | None = None) -> None:
            self.token = token
            self.added: list[tuple[str, str, str, str | None]] = []

        def create_collection(
            self,
            title: str,
            *,
            namespace: str,
            description: str,
            private: bool,
            exists_ok: bool,
            token: str | None,
        ) -> Collection:
            assert title == "hathitrust-nz"
            assert namespace == "edithatogo"
            assert description == "test"
            assert private is False
            assert exists_ok is True
            assert token is None
            return Collection()

        def add_collection_item(
            self,
            collection_slug: str,
            item_id: str,
            item_type: str,
            *,
            note: str | None,
            exists_ok: bool,
            token: str | None,
        ) -> Collection:
            assert exists_ok is True
            assert token is None
            self.added.append((collection_slug, item_id, item_type, note))
            return Collection()

    created_api = MockApi()
    monkeypatch.setattr(module, "HfApi", lambda token=None: created_api)

    result = sync_hf_collection(
        title="hathitrust-nz",
        namespace="edithatogo",
        description="test",
    )

    assert result["resolved_slug"] == "edithatogo/hathitrust-nz-test"
    assert result["item_count"] == len(created_api.added)
    assert {item[2] for item in created_api.added} == {"dataset"}


def test_parse_args_defaults() -> None:
    args = parse_args([])
    assert args.title == "hathitrust-nz"
    assert args.namespace == "edithatogo"
    assert args.collection_slug is None
