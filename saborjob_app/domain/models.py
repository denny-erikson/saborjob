from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Job:
    title: str
    company: str | None
    location: str | None
    url: str
    posted_at: str | None
    tags: list[str] = field(default_factory=list)
    source: str = "solides"


@dataclass(frozen=True)
class ResumeProfile:
    text: str
    keywords: list[str]
    seniority: str | None
    work_mode: str | None
    profile_text: str


@dataclass(frozen=True)
class MatchResult:
    score: int
    semantic_score: int
    keyword_overlap: list[str]
    seniority_match: bool
    work_mode_match: bool
    reasons: list[str]


@dataclass(frozen=True)
class SidebarInputs:
    search_value: str
    selected_locations: list[str]
    selected_companies: list[str]
    selected_tags: list[str]
    sort_option: str
    page_size: int
    uploaded_resume: object | None
    analyze_clicked: bool
    clear_clicked: bool


@dataclass(frozen=True)
class MetricsSummary:
    total_jobs: int
    companies: int
    locations: int
    remote_jobs: int
    recent_jobs: int
    strong_matches: int
