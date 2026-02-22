"""Content generator – uses Google Gemini API to create SEO articles.

Safe design:
  - API key is read from the GEMINI_API_KEY environment variable only.
  - Secrets are never logged.
  - All API calls are retried with exponential back-off.
  - Each error entry is isolated; a failure on one does NOT abort the batch.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from google import genai

from src.logger import get_logger
from src.models import ErrorEntry, GeneratedArticle

log = get_logger(__name__)

# ── Gemini model name (free tier as of 2026) ─────────────────────────────────
GEMINI_MODEL = "gemini-2.0-flash"

# ── Rate-limit constants (free tier: 15 RPM, 1500 RPD) ───────────────────────
# 15 RPM = one request every 4 s minimum.
# We use 15 s between articles so retries still fit inside the minute window.
INTER_ARTICLE_DELAY_S = 15       # seconds between successful generations
BATCH_SIZE = 10                  # pause after every N articles
BATCH_PAUSE_S = 70               # seconds to pause between batches (> 1 min)
RETRY_429_WAIT_S = 65            # wait after a 429 before retrying

# ── Article generation parameters ────────────────────────────────────────────
TARGET_MIN_WORDS = 900
TARGET_MAX_WORDS = 1200


def _is_rate_limit(exc: BaseException) -> bool:
    """Return True when the exception is a 429 / RESOURCE_EXHAUSTED."""
    return "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)


def _build_prompt(entry: ErrorEntry, related_slugs: list[str]) -> str:
    """Build the Gemini prompt for a single error entry."""
    related_links_md = "\n".join(
        f"- [{slug}](/errors/{slug}.html)" for slug in related_slugs[:4]
    )

    return f"""You are a senior software engineer writing a practical, SEO-optimised
troubleshooting guide. Write a complete Markdown article for the error below.

**Error:** {entry.error_name}
**Tool / Platform:** {entry.tool}
**Context:** {entry.context}
**Short description:** {entry.description}

### Article requirements
1. Open with an H1 that is exactly: `# {entry.error_name}`
2. Right after H1, add a short one-sentence meta-description as a blockquote
   (starts with `> `) — used for SEO preview.
3. Include ALL of the following H2 sections in this order:
   - `## What This Error Means`
   - `## Why It Happens`
   - `## Common Causes`
   - `## Step-by-Step Fix`  (numbered steps, include shell/code blocks where relevant)
   - `## Code Examples`     (concise, copy-paste ready)
   - `## Environment-Specific Notes`  (cloud, Docker, local dev differences)
   - `## Frequently Asked Questions`  (3–5 Q&A pairs in bold-question style)
4. End with a `## Related Errors` section that includes these Markdown links:
{related_links_md if related_links_md else "   *(none)*"}
5. Length: {TARGET_MIN_WORDS}–{TARGET_MAX_WORDS} words.
6. Tone: calm, direct, engineer-to-engineer. No hype, no filler sentences.
7. Include at least two code blocks with syntax highlighting hints (e.g. ```bash or ```python).
8. Do NOT include any YAML front-matter.
9. Do NOT include any HTML tags.

Write only the Markdown article — no preamble, no commentary outside the article.
"""


def _configure_client() -> genai.Client:
    """Configure Gemini client from env; raise clearly if key is missing."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY environment variable is not set. "
            "Add it as a GitHub Actions secret named GEMINI_API_KEY."
        )
    # Never log the key value
    client = genai.Client(api_key=api_key)
    log.info("Gemini client configured", model=GEMINI_MODEL)
    return client


def _call_gemini(client: genai.Client, prompt: str) -> str:
    """Call Gemini with 429-aware retry logic.

    Strategy:
      - On 429 (quota exceeded): wait RETRY_429_WAIT_S seconds then retry.
        The free-tier window resets every minute, so waiting > 60 s guarantees
        the next attempt lands in a fresh window.
      - On other transient errors: standard exponential back-off.
      - Give up after 5 attempts total.
    """
    last_exc: Optional[Exception] = None
    for attempt in range(1, 6):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            return response.text
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if _is_rate_limit(exc):
                log.warning(
                    "Rate limit hit – waiting before retry",
                    attempt=attempt,
                    wait_s=RETRY_429_WAIT_S,
                )
                time.sleep(RETRY_429_WAIT_S)
            else:
                wait = min(4 * (2 ** (attempt - 1)), 60)
                log.warning(
                    "Transient error – retrying",
                    attempt=attempt,
                    wait_s=wait,
                    error=str(exc),
                )
                time.sleep(wait)
    raise last_exc  # type: ignore[misc]


class ArticleGenerator:
    """Orchestrates article generation for all error entries."""

    def __init__(self) -> None:
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = _configure_client()
        return self._client

    def generate_one(
        self,
        entry: ErrorEntry,
        all_slugs: list[str],
    ) -> Optional[GeneratedArticle]:
        """Generate a single article; returns None on failure."""
        # Build related slugs from entry.related list (match against known slugs)
        related_slugs = [s for s in entry.related if s in all_slugs]

        prompt = _build_prompt(entry, related_slugs)
        log.info("Generating article", slug=entry.slug, tool=entry.tool)

        try:
            markdown_text = _call_gemini(self.client, prompt)
        except Exception as exc:  # noqa: BLE001
            log.error(
                "All retries exhausted for article",
                slug=entry.slug,
                error=str(exc),
            )
            return None

        article = GeneratedArticle(error=entry, markdown_content=markdown_text)
        log.info(
            "Article generated",
            slug=entry.slug,
            words=article.word_count,
        )
        # Respect free-tier RPM (15 RPM → ≥4 s/request).
        # 15 s gives headroom for occasional retries within the same minute.
        log.debug("Rate-limit delay", wait_s=INTER_ARTICLE_DELAY_S)
        time.sleep(INTER_ARTICLE_DELAY_S)
        return article

    def generate_batch(
        self,
        entries: list[ErrorEntry],
        already_done: set[str],
        content_dir: Path,
    ) -> list[GeneratedArticle]:
        """Generate articles for entries not yet in already_done.

        Saves each Markdown file immediately so progress survives partial runs.
        """
        all_slugs = {e.slug for e in entries}
        results: list[GeneratedArticle] = []

        pending = [e for e in entries if e.slug not in already_done]
        log.info(
            "Batch generation starting",
            total=len(entries),
            pending=len(pending),
            already_done=len(already_done),
        )

        for i, entry in enumerate(pending):
            article = self.generate_one(entry, list(all_slugs))
            if article is None:
                log.warning("Skipping failed entry", slug=entry.slug)
            else:
                # Persist Markdown immediately so progress survives partial runs
                md_path = content_dir / "errors" / f"{entry.slug}.md"
                md_path.parent.mkdir(parents=True, exist_ok=True)
                md_path.write_text(article.markdown_content, encoding="utf-8")
                log.info("Markdown saved", path=str(md_path))
                results.append(article)

            # Every BATCH_SIZE articles, pause longer to let the RPM window reset.
            # This prevents accumulated quota debt across a large run.
            if (i + 1) % BATCH_SIZE == 0 and (i + 1) < len(pending):
                log.info(
                    "Batch pause – letting quota window reset",
                    completed=i + 1,
                    remaining=len(pending) - (i + 1),
                    wait_s=BATCH_PAUSE_S,
                )
                time.sleep(BATCH_PAUSE_S)

        log.info("Batch generation complete", generated=len(results))
        return results
