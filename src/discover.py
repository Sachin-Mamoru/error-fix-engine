"""Automatic error-topic discovery.

Calls Gemini once per pipeline run to generate a batch of NEW error topics
that don't already exist in the combined config.  Topics are appended to
config/discovered_errors.yaml so the next article-generation step can pick
them up immediately.

With the free tier (1 500 RPD) spread across 12 daily runs, each run can
safely generate ~100 articles.  Adding 30 fresh topics per run means the
topic backlog always stays well ahead of the article queue.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Optional

import yaml
from google import genai
from slugify import slugify  # type: ignore[import-untyped]

from src.logger import get_logger
from src.models import ErrorEntry

log = get_logger(__name__)

DISCOVERED_YAML = Path(__file__).parent.parent / "config" / "discovered_errors.yaml"

# How many new topics to request per pipeline run.
# Paid tier 1 with unlimited RPD: 100 topics/run × 12 runs/day = 1200 new
# topics/day, keeping the backlog well ahead of the 500 articles/run queue.
TOPICS_PER_RUN = 100

# Broad technology categories rotated per run to keep topics diverse.
CATEGORY_WHEEL = [
    "Python, Django, Flask, FastAPI",
    "JavaScript, Node.js, npm, yarn, Bun",
    "TypeScript, ESLint, Vite, Webpack",
    "React, Next.js, Vue.js, Nuxt",
    "Docker, Docker Compose, containerd",
    "Kubernetes, Helm, kubectl",
    "AWS Lambda, S3, EC2, EKS, RDS, IAM",
    "Google Cloud, GCP, Cloud Run, BigQuery",
    "Azure, AKS, Azure Functions, CosmosDB",
    "PostgreSQL, MySQL, SQLite, MariaDB",
    "MongoDB, Redis, Elasticsearch, Cassandra",
    "Nginx, Apache, Traefik, Caddy",
    "GitHub Actions, GitLab CI, CircleCI, Jenkins",
    "Terraform, Pulumi, Ansible, CloudFormation",
    "Rust, Go, Java, Spring Boot, Maven, Gradle",
    "Ruby, Rails, Bundler",
    "PHP, Laravel, Composer",
    "SSL/TLS, Let's Encrypt, OpenSSL, Certbot",
    "Kafka, RabbitMQ, Celery, Redis Queues",
    "GraphQL, REST APIs, gRPC, WebSockets",
    "Git, GitHub, GitLab",
    "Linux, Bash, systemd, cron",
    "Stripe, Twilio, SendGrid, Slack API",
    "Vercel, Netlify, Heroku, Railway",
    "OpenAI API, Gemini API, Anthropic, Hugging Face",
]


def _build_discovery_prompt(
    existing_names: set[str],
    category_hint: str,
    count: int,
) -> str:
    # Pass up to 120 existing error names to avoid duplicates (keep prompt short)
    sample = sorted(existing_names)[:120]
    existing_block = "\n".join(f"- {n}" for n in sample)

    return f"""You are a senior software engineer and technical SEO expert.

Your task: generate a JSON array of {count} REAL, commonly-searched software
error messages that developers encounter.

Focus on tools/technologies in this category this round:
{category_hint}

Strict requirements:
1. Each error must be a REAL error message or error code from a real tool.
2. Do NOT repeat any of the errors already covered (list below).
3. Vary severity and context: runtime errors, build errors, CLI errors,
   HTTP errors, API errors, database errors, permission errors, etc.
4. Return ONLY a raw JSON array — no markdown fences, no extra text.

JSON schema for each item:
{{
  "tool":        "exact name of the tool/platform/language",
  "error_code":  "error code string if one exists, else null",
  "error_name":  "the exact error message developers copy-paste into Google",
  "description": "one sentence: what does this error mean?",
  "context":     "where it occurs, e.g. runtime, build, CLI, database, API",
  "tags":        ["tag1", "tag2", "tag3"],
  "related":     []
}}

Already covered (do not duplicate):
{existing_block}

Return the JSON array now:"""


def _parse_topics(raw: str) -> list[dict]:
    """Extract a JSON array from Gemini's response, tolerating markdown fences."""
    # Strip ```json ... ``` or ``` ... ``` wrappers if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip())

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        # Try to extract the first [...] block
        m = re.search(r"\[.*\]", cleaned, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
    log.warning("Could not parse discovery response", raw_preview=raw[:200])
    return []


def _load_discovered() -> tuple[list[dict], set[str]]:
    """Return (raw_list, existing_slugs) from discovered_errors.yaml."""
    if not DISCOVERED_YAML.exists():
        return [], set()
    raw = yaml.safe_load(DISCOVERED_YAML.read_text(encoding="utf-8")) or {}
    items: list[dict] = raw.get("errors", [])
    slugs = {
        slugify(f"{i.get('tool','')} {i.get('error_code') or i.get('error_name','')}")
        for i in items
    }
    return items, slugs


def _append_to_discovered(new_items: list[dict]) -> None:
    """Append validated new items to discovered_errors.yaml."""
    existing, _ = _load_discovered()
    combined = existing + new_items
    DISCOVERED_YAML.parent.mkdir(parents=True, exist_ok=True)
    DISCOVERED_YAML.write_text(
        yaml.dump({"errors": combined}, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
    log.info(
        "Discovered topics saved",
        added=len(new_items),
        total=len(combined),
        path=str(DISCOVERED_YAML),
    )


def discover_new_topics(
    client: genai.Client,
    model: str,
    all_known_entries: list[ErrorEntry],
    count: int = TOPICS_PER_RUN,
) -> list[ErrorEntry]:
    """Ask Gemini for `count` new error topics and append them to discovered_errors.yaml.

    Returns the newly added ErrorEntry objects so the pipeline can include
    them in the current run's generation queue immediately.
    """
    # Build the set of names already known (seed + previously discovered)
    known_names: set[str] = {e.error_name for e in all_known_entries}
    known_slugs: set[str] = {e.slug for e in all_known_entries}

    # Pick a rotating category based on current discovered count
    _, discovered_slugs = _load_discovered()
    category_index = len(discovered_slugs) % len(CATEGORY_WHEEL)
    category_hint = CATEGORY_WHEEL[category_index]

    log.info(
        "Discovering new topics",
        count=count,
        category=category_hint,
        already_known=len(known_names),
    )

    prompt = _build_discovery_prompt(known_names, category_hint, count)

    try:
        response = client.models.generate_content(model=model, contents=prompt)
        raw = response.text
    except Exception as exc:  # noqa: BLE001
        log.error("Discovery API call failed", error=str(exc))
        return []

    topics = _parse_topics(raw)
    if not topics:
        log.warning("No topics parsed from discovery response")
        return []

    # Validate and de-duplicate
    valid_new: list[dict] = []
    new_entries: list[ErrorEntry] = []

    for item in topics:
        if not isinstance(item, dict):
            continue
        tool = (item.get("tool") or "").strip()
        error_name = (item.get("error_name") or "").strip()
        if not tool or not error_name:
            continue

        entry = ErrorEntry(
            tool=tool,
            error_name=error_name,
            description=item.get("description", ""),
            context=item.get("context", ""),
            tags=item.get("tags", []),
            related=item.get("related", []),
            error_code=item.get("error_code") or None,
        )

        if entry.slug in known_slugs:
            log.debug("Skipping duplicate slug", slug=entry.slug)
            continue

        known_slugs.add(entry.slug)
        valid_new.append({
            "tool": tool,
            "error_code": item.get("error_code") or None,
            "error_name": error_name,
            "description": entry.description,
            "context": entry.context,
            "tags": entry.tags,
            "related": [],
        })
        new_entries.append(entry)

    log.info(
        "Discovery complete",
        proposed=len(topics),
        valid_new=len(valid_new),
    )

    if valid_new:
        _append_to_discovered(valid_new)

    # Brief pause so the probe + discovery calls don't eat into the RPM window
    time.sleep(5)

    return new_entries
