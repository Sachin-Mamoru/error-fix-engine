"""Fake-but-realistic author pool for error articles.

Authors are assigned deterministically by slug so the same article always
shows the same author across rebuilds.
"""
from __future__ import annotations

AUTHORS: list[dict[str, str]] = [
    {"name": "Alex Mercer",      "title": "Senior Software Engineer"},
    {"name": "Jamie Okonkwo",    "title": "Platform Engineer"},
    {"name": "Priya Nair",       "title": "Site Reliability Engineer"},
    {"name": "Daniel Kovacs",    "title": "Backend Engineer"},
    {"name": "Sofia Reyes",      "title": "Cloud Infrastructure Engineer"},
    {"name": "Marcus Webb",      "title": "DevOps Engineer"},
    {"name": "Kenji Tanaka",     "title": "Full-Stack Developer"},
    {"name": "Asha Mensah",      "title": "Software Architect"},
    {"name": "Ryan Holloway",    "title": "Senior DevOps Engineer"},
    {"name": "Lena Schreiber",   "title": "Infrastructure Engineer"},
    {"name": "Chris Delacroix",  "title": "Staff Engineer"},
    {"name": "Yemi Adeyemi",     "title": "Cloud Solutions Engineer"},
    {"name": "Natasha Koval",    "title": "Senior Backend Developer"},
    {"name": "Omar Farooq",      "title": "Platform Reliability Engineer"},
    {"name": "Ingrid Holm",      "title": "Systems Engineer"},
    {"name": "Ben Whitfield",    "title": "Senior Full-Stack Engineer"},
    {"name": "Carmen Ortega",    "title": "DevOps & Cloud Specialist"},
    {"name": "Takeshi Mori",     "title": "Software Engineer"},
    {"name": "Amara Diallo",     "title": "API & Integration Engineer"},
    {"name": "Ethan Calloway",   "title": "Principal Engineer"},
    {"name": "Nina Johansson",   "title": "Site Reliability Engineer"},
    {"name": "Lucas Ferreira",   "title": "Senior Platform Engineer"},
    {"name": "Divya Krishnan",   "title": "Cloud & DevOps Engineer"},
    {"name": "Patrick Brennan",  "title": "Backend & Infrastructure Lead"},
    {"name": "Zara Osei",        "title": "Full-Stack & DevOps Engineer"},
]


def pick_author(slug: str) -> dict[str, str]:
    """Deterministically return an author for the given article slug.

    Uses a stable hash so the same slug always maps to the same author,
    even across different Python processes (hash randomisation is bypassed
    by using the sum of byte values rather than the built-in hash()).
    """
    index = sum(ord(c) for c in slug) % len(AUTHORS)
    return AUTHORS[index]
