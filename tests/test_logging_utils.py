"""Tests for shared Loguru logging configuration."""

from __future__ import annotations

import io
from pathlib import Path

from scripts import logging_utils

ROOT = Path(__file__).resolve().parents[1]
TARGET_SCRIPTS = [
    ROOT / "scripts" / "cli.py",
    ROOT / "scripts" / "fetch_hathitrust.py",
    ROOT / "scripts" / "ocr_extract.py",
    ROOT / "scripts" / "stage_hf_dataset.py",
    ROOT / "scripts" / "upload_hf_dataset.py",
    ROOT / "scripts" / "validate_catalog.py",
]


def test_configure_logging_installs_expected_sink(monkeypatch) -> None:
    calls: dict[str, object] = {}

    def fake_remove() -> None:
        calls["removed"] = True

    def fake_add(
        sink: object,
        *,
        level: str,
        log_format: str,
        colorize: bool,
        backtrace: bool,
        diagnose: bool,
    ) -> int:
        calls["sink"] = sink
        calls["level"] = level
        calls["format"] = log_format
        calls["colorize"] = colorize
        calls["backtrace"] = backtrace
        calls["diagnose"] = diagnose
        return 1

    monkeypatch.setattr(logging_utils.logger, "remove", fake_remove)
    monkeypatch.setattr(logging_utils.logger, "add", fake_add)

    sink = io.StringIO()
    logging_utils.configure_logging("DEBUG", sink=sink)

    assert calls["removed"] is True
    assert calls["sink"] is sink
    assert calls["level"] == "DEBUG"
    assert calls["format"] == logging_utils.LOG_FORMAT
    assert calls["colorize"] is False
    assert calls["backtrace"] is False
    assert calls["diagnose"] is False


def test_migrated_scripts_use_loguru_only() -> None:
    for path in TARGET_SCRIPTS:
        content = path.read_text(encoding="utf-8")
        assert "from loguru import logger" in content
        assert "import logging" not in content
        assert "logging.basicConfig" not in content
        assert "getLogger(" not in content
        assert "setLevel(" not in content
