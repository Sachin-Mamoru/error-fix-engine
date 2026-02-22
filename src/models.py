"""Data models for error-fix-engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ErrorEntry:
    """Represents one error definition from config/errors.yaml."""

    tool: str
    error_name: str
    description: str
    context: str
    tags: list[str] = field(default_factory=list)
    related: list[str] = field(default_factory=list)
    error_code: Optional[str] = None

    # Derived at load time
    slug: str = ""

    def __post_init__(self) -> None:
        if not self.slug:
            from slugify import slugify  # type: ignore[import-untyped]

            base = f"{self.tool}-{self.error_code or self.error_name}"
            self.slug = slugify(base)


@dataclass
class GeneratedArticle:
    """Represents a fully generated article ready to publish."""

    error: ErrorEntry
    markdown_content: str
    word_count: int = 0

    def __post_init__(self) -> None:
        if self.markdown_content is None:
            self.markdown_content = ""
        if not self.word_count:
            self.word_count = len(self.markdown_content.split())
