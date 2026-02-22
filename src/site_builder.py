"""Static site builder.

Reads Markdown files from content/errors/
Renders HTML pages using Jinja2 templates
Generates:
  - site/index.html          (homepage with full error listing)
  - site/errors/<slug>.html  (individual error pages)
  - site/sitemap.xml
  - site/robots.txt
  - site/assets/style.css    (copy from templates/assets/)
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import markdown as md_lib
from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.logger import get_logger
from src.models import ErrorEntry

log = get_logger(__name__)

# Markdown extensions for richer HTML output
MD_EXTENSIONS = [
    "extra",        # tables, fenced code, footnotes, …
    "codehilite",   # syntax highlighting
    "toc",          # [TOC] + auto anchor generation
    "nl2br",        # newlines → <br> (friendlier for LLM output)
    "sane_lists",
]

MD_EXTENSION_CONFIGS = {
    "codehilite": {"guess_lang": False, "css_class": "highlight"},
    "toc": {"permalink": True},
}


def _render_markdown(text: str) -> str:
    """Convert Markdown text to an HTML fragment (no <html>/<body> wrapper)."""
    return md_lib.markdown(
        text,
        extensions=MD_EXTENSIONS,
        extension_configs=MD_EXTENSION_CONFIGS,
    )


class SiteBuilder:
    """Builds the complete static site from content/ → site/."""

    def __init__(
        self,
        content_dir: Path,
        site_dir: Path,
        templates_dir: Path,
        base_url: str = "https://errorfix.dev",
    ) -> None:
        self.content_dir = content_dir
        self.site_dir = site_dir
        self.templates_dir = templates_dir
        self.base_url = base_url.rstrip("/")

        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        # Expose a helper inside templates
        self.env.globals["base_url"] = self.base_url
        self.env.globals["build_date"] = datetime.now(tz=timezone.utc).strftime(
            "%B %d, %Y"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def build(self, all_entries: list[ErrorEntry]) -> None:
        """Full build: individual pages → homepage → sitemap → robots."""
        self.site_dir.mkdir(parents=True, exist_ok=True)
        (self.site_dir / "errors").mkdir(parents=True, exist_ok=True)

        self._copy_assets()

        # Build pages for entries that have generated Markdown
        built_entries: list[ErrorEntry] = []
        for entry in all_entries:
            md_path = self.content_dir / "errors" / f"{entry.slug}.md"
            if not md_path.exists():
                log.debug("No markdown yet, skipping HTML build", slug=entry.slug)
                continue
            self._build_error_page(entry, md_path, all_entries)
            built_entries.append(entry)

        self._build_homepage(built_entries)
        self._build_sitemap(built_entries)
        self._build_robots()

        log.info(
            "Site build complete",
            pages=len(built_entries),
            output_dir=str(self.site_dir),
        )

    # ── Private helpers ───────────────────────────────────────────────────────

    def _copy_assets(self) -> None:
        src = self.templates_dir / "assets"
        dst = self.site_dir / "assets"
        if src.exists():
            shutil.copytree(src, dst, dirs_exist_ok=True)
            log.debug("Assets copied", src=str(src), dst=str(dst))

    def _build_error_page(
        self,
        entry: ErrorEntry,
        md_path: Path,
        all_entries: list[ErrorEntry],
    ) -> None:
        raw_md = md_path.read_text(encoding="utf-8")
        html_body = _render_markdown(raw_md)

        # Resolve related entries for sidebar links
        slug_map = {e.slug: e for e in all_entries}
        related_entries = [slug_map[s] for s in entry.related if s in slug_map]

        template = self.env.get_template("error_page.html")
        html = template.render(
            entry=entry,
            html_body=html_body,
            related_entries=related_entries,
            page_title=f"{entry.error_name} – How to Fix | error-fix-engine",
            meta_description=(
                f"How to fix {entry.error_name} in {entry.tool}. "
                f"{entry.description}. Step-by-step guide with code examples."
            ),
            canonical_url=f"{self.base_url}/errors/{entry.slug}.html",
        )

        out_path = self.site_dir / "errors" / f"{entry.slug}.html"
        out_path.write_text(html, encoding="utf-8")
        log.debug("Error page built", slug=entry.slug, path=str(out_path))

    def _build_homepage(self, built_entries: list[ErrorEntry]) -> None:
        # Group by tool for a cleaner homepage layout
        tools: dict[str, list[ErrorEntry]] = {}
        for entry in built_entries:
            tools.setdefault(entry.tool, []).append(entry)

        template = self.env.get_template("index.html")
        html = template.render(
            tools=tools,
            total_articles=len(built_entries),
            page_title="Error Fix Engine – How to Fix Software & Cloud Errors",
            meta_description=(
                "Step-by-step guides to fix OpenAI, Docker, Kubernetes, AWS, "
                "Python and Linux errors. Engineer-written, no fluff."
            ),
            canonical_url=self.base_url + "/",
        )

        (self.site_dir / "index.html").write_text(html, encoding="utf-8")
        log.info("Homepage built", articles=len(built_entries))

    def _build_sitemap(self, built_entries: list[ErrorEntry]) -> None:
        today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        template = self.env.get_template("sitemap.xml")
        xml = template.render(
            entries=built_entries,
            base_url=self.base_url,
            today=today,
        )
        (self.site_dir / "sitemap.xml").write_text(xml, encoding="utf-8")
        log.info("sitemap.xml built", urls=len(built_entries) + 1)

    def _build_robots(self) -> None:
        content = (
            "User-agent: *\n"
            "Allow: /\n"
            f"Sitemap: {self.base_url}/sitemap.xml\n"
        )
        (self.site_dir / "robots.txt").write_text(content, encoding="utf-8")
        log.info("robots.txt written")
