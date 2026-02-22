"""Loads and validates config/errors.yaml into ErrorEntry dataclasses."""
from __future__ import annotations

from pathlib import Path

import yaml

from src.logger import get_logger
from src.models import ErrorEntry

log = get_logger(__name__)


def load_errors(config_path: Path) -> list[ErrorEntry]:
    """Parse errors.yaml and return a list of validated ErrorEntry objects."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    raw_errors: list[dict] = raw.get("errors", [])

    entries: list[ErrorEntry] = []
    for i, item in enumerate(raw_errors):
        try:
            entry = ErrorEntry(
                tool=item["tool"],
                error_name=item["error_name"],
                description=item.get("description", ""),
                context=item.get("context", ""),
                tags=item.get("tags", []),
                related=item.get("related", []),
                error_code=item.get("error_code"),
            )
            entries.append(entry)
        except (KeyError, TypeError) as exc:
            log.warning(
                "Skipping malformed error entry",
                index=i,
                item=item,
                error=str(exc),
            )

    log.info("Errors loaded from config", count=len(entries), path=str(config_path))
    return entries


def load_generated_index(index_path: Path) -> set[str]:
    """Return the set of slugs that have already been generated."""
    if not index_path.exists():
        return set()
    try:
        data = yaml.safe_load(index_path.read_text(encoding="utf-8")) or {}
        return set(data.get("generated_slugs", []))
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not read generated index", path=str(index_path), error=str(exc))
        return set()


def save_generated_index(index_path: Path, slugs: set[str]) -> None:
    """Persist the set of generated slugs to disk."""
    index_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"generated_slugs": sorted(slugs)}
    index_path.write_text(yaml.dump(data, default_flow_style=False), encoding="utf-8")
    log.debug("Generated index saved", path=str(index_path), count=len(slugs))
