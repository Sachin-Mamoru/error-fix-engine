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

from src.authors import pick_author
from src.logger import get_logger
from src.models import ErrorEntry, GeneratedArticle

log = get_logger(__name__)

# ── Gemini model preference list ─────────────────────────────────────────────
# The pipeline tries each model in order and uses the first one that responds.
# gemini-1.5-flash is available to ALL API keys including brand-new free tier.
# Newer flash models are listed first so existing users benefit automatically.
GEMINI_MODEL_CANDIDATES = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-8b",
]

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


def _is_permanent(exc: BaseException) -> bool:
    """Return True for errors that will never succeed on retry (4xx non-429)."""
    msg = str(exc)
    return any(code in msg for code in ("404", "400", "403", "NOT_FOUND", "INVALID_ARGUMENT"))


def _build_prompt(
    entry: ErrorEntry,
    related_slugs: list[str],
    author_name: str,
    author_title: str,
) -> str:
    """Build the Gemini prompt for a single error entry."""
    related_links_md = "\n".join(
        f"- [{slug}](/errors/{slug}.html)" for slug in related_slugs[:4]
    )

    return f"""You are {author_name}, a {author_title}, writing a practical,
SEO-optimised troubleshooting guide from personal experience.
Write a complete Markdown article for the error below.

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
10. Occasionally use first-person phrases like "In my experience…" or "I've seen this in production when…" — it should read like a real engineer wrote it.
11. Do NOT mention AI, do NOT say this article was generated, do NOT say "As an AI" or anything similar.
12. End the article body before any author signature — the byline is handled separately.

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
    log.info("Gemini client configured")
    return client


def _resolve_model(client: genai.Client) -> str:
    """Return the first model in GEMINI_MODEL_CANDIDATES that this API key
    can actually reach, so new users and existing users both get the best
    available model automatically."""
    probe = "Reply with one word: OK"
    for model in GEMINI_MODEL_CANDIDATES:
        try:
            client.models.generate_content(model=model, contents=probe)
            log.info("Model resolved", model=model)
            return model
        except Exception as exc:  # noqa: BLE001
            log.debug("Model probe failed", model=model, reason=str(exc)[:80])
    fallback = GEMINI_MODEL_CANDIDATES[-1]
    log.warning("All model probes failed, using last candidate", model=fallback)
    return fallback


def _call_gemini(client: genai.Client, prompt: str, model: str) -> str:
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
                model=model,
                contents=prompt,
            )
            return response.text
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if _is_permanent(exc):
                log.error(
                    "Permanent API error – not retrying",
                    error=str(exc),
                )
                raise
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
        self._model: Optional[str] = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = _configure_client()
            # Resolve the best available model for this API key once
            self._model = _resolve_model(self._client)
        return self._client

    @property
    def model(self) -> str:
        # Ensure client (and model resolution) has run
        _ = self.client
        return self._model  # type: ignore[return-value]

    def generate_one(
        self,
        entry: ErrorEntry,
        all_slugs: list[str],
    ) -> Optional[GeneratedArticle]:
        """Generate a single article; returns None on failure."""
        # Build related slugs from entry.related list (match against known slugs)
        related_slugs = [s for s in entry.related if s in all_slugs]

        author = pick_author(entry.slug)
        prompt = _build_prompt(entry, related_slugs, author["name"], author["title"])
        log.info("Generating article", slug=entry.slug, tool=entry.tool)

        try:
            markdown_text = _call_gemini(self.client, prompt, self.model)
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
        max_count: int = 0,
    ) -> list[GeneratedArticle]:
        """Generate articles for entries not yet in already_done.

        Args:
            max_count: If > 0, stop after this many successful generations
                       (used to respect free-tier RPD quota per run).

        Saves each Markdown file immediately so progress survives partial runs.
        """
        all_slugs = {e.slug for e in entries}
        results: list[GeneratedArticle] = []

        pending = [e for e in entries if e.slug not in already_done]
        if max_count > 0:
            pending = pending[:max_count]

        log.info(
            "Batch generation starting",
            total=len(entries),
            pending=len(pending),
            already_done=len(already_done),
            cap=max_count or "none",
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
