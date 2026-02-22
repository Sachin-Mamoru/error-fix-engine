#!/usr/bin/env python3
"""Main pipeline – orchestrates content generation and site build.

Usage:
    python -m scripts.run_pipeline              # generate + build all
    python -m scripts.run_pipeline --build-only # skip generation, rebuild site
    python -m scripts.run_pipeline --dry-run    # log what would happen, no API calls

Environment variables:
    GEMINI_API_KEY   Required for content generation (set as GitHub Actions secret)
    BASE_URL         Optional: override the public site URL in generated HTML
    LOG_LEVEL        Optional: DEBUG | INFO | WARNING (default: INFO)
"""
from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path

# ── Make sure the project root is on sys.path ────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.logger import configure_logging, get_logger
from src.config_loader import load_errors, load_generated_index, save_generated_index
from src.generator import ArticleGenerator
from src.site_builder import SiteBuilder

# ── Path constants ────────────────────────────────────────────────────────────
CONFIG_PATH    = PROJECT_ROOT / "config" / "errors.yaml"
CONTENT_DIR    = PROJECT_ROOT / "content"
SITE_DIR       = PROJECT_ROOT / "site"
TEMPLATES_DIR  = PROJECT_ROOT / "templates"
GENERATED_IDX  = CONTENT_DIR / "generated.yaml"

DEFAULT_BASE_URL = (
    "https://YOUR_GITHUB_USERNAME.github.io/error-fix-engine"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="error-fix-engine pipeline")
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Skip content generation; only rebuild the static site from existing Markdown.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be generated without making API calls.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    log_level = os.environ.get("LOG_LEVEL", "INFO")
    configure_logging(log_level)
    log = get_logger("pipeline")

    base_url = os.environ.get("BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    log.info(
        "Pipeline starting",
        build_only=args.build_only,
        dry_run=args.dry_run,
        base_url=base_url,
    )

    # ── 1. Load error definitions ─────────────────────────────────────────────
    try:
        all_entries = load_errors(CONFIG_PATH)
    except FileNotFoundError as exc:
        log.error("Config file not found", error=str(exc))
        return 1

    if not all_entries:
        log.error("No error entries loaded — check config/errors.yaml")
        return 1

    log.info("Error entries loaded", count=len(all_entries))

    # ── 2. Content generation ─────────────────────────────────────────────────
    if not args.build_only:
        already_done = load_generated_index(GENERATED_IDX)
        pending = [e for e in all_entries if e.slug not in already_done]

        if args.dry_run:
            log.info(
                "DRY RUN – articles that would be generated",
                count=len(pending),
                slugs=[e.slug for e in pending],
            )
        else:
            if not pending:
                log.info("All articles already generated — skipping API calls")
            else:
                generator = ArticleGenerator()
                new_articles = generator.generate_batch(
                    entries=all_entries,
                    already_done=already_done,
                    content_dir=CONTENT_DIR,
                )

                new_slugs = {a.error.slug for a in new_articles}
                updated_done = already_done | new_slugs
                save_generated_index(GENERATED_IDX, updated_done)

                log.info(
                    "Generation phase complete",
                    new=len(new_slugs),
                    total_done=len(updated_done),
                )

    # ── 3. Site build ─────────────────────────────────────────────────────────
    if not args.dry_run:
        builder = SiteBuilder(
            content_dir=CONTENT_DIR,
            site_dir=SITE_DIR,
            templates_dir=TEMPLATES_DIR,
            base_url=base_url,
        )
        builder.build(all_entries)

    log.info("Pipeline finished successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
