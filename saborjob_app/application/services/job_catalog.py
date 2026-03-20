from __future__ import annotations

from math import ceil

from saborjob_app.domain.models import Job, MatchResult, MetricsSummary
from saborjob_app.domain.rules import is_remote, parse_posted_days


class JobCatalogService:
    def apply_filters(
        self,
        jobs: list[Job],
        search_value: str,
        selected_locations: list[str],
        selected_companies: list[str],
        selected_tags: list[str],
    ) -> list[Job]:
        filtered_jobs = jobs

        if search_value:
            query = search_value.lower().strip()
            filtered_jobs = [
                job
                for job in filtered_jobs
                if query in job.title.lower()
                or query in (job.company or "").lower()
                or query in (job.location or "").lower()
                or any(query in str(tag).lower() for tag in job.tags)
            ]

        if selected_locations:
            filtered_jobs = [job for job in filtered_jobs if job.location in selected_locations]

        if selected_companies:
            filtered_jobs = [job for job in filtered_jobs if job.company in selected_companies]

        if selected_tags:
            filtered_jobs = [job for job in filtered_jobs if any(tag in selected_tags for tag in job.tags)]

        return filtered_jobs

    def sort_jobs(
        self,
        jobs: list[Job],
        sort_option: str,
        match_results: dict[str, MatchResult] | None = None,
    ) -> list[Job]:
        if sort_option == "Maior aderencia" and match_results:
            return sorted(
                jobs,
                key=lambda job: (-(match_results.get(job.url, MatchResult(0, 0, [], False, False, [])).score), parse_posted_days(job.posted_at)),
            )

        if sort_option == "Empresa (A-Z)":
            return sorted(jobs, key=lambda job: (job.company or "").lower())

        if sort_option == "Local (A-Z)":
            return sorted(jobs, key=lambda job: (job.location or "").lower())

        return sorted(jobs, key=lambda job: parse_posted_days(job.posted_at))

    def build_metrics(
        self,
        jobs: list[Job],
        match_results: dict[str, MatchResult] | None = None,
    ) -> MetricsSummary:
        strong_matches = 0
        if match_results:
            strong_matches = sum(1 for result in match_results.values() if result.score >= 70)

        return MetricsSummary(
            total_jobs=len(jobs),
            companies=len({job.company for job in jobs if job.company}),
            locations=len({job.location for job in jobs if job.location}),
            remote_jobs=sum(1 for job in jobs if is_remote(job)),
            recent_jobs=sum(1 for job in jobs if parse_posted_days(job.posted_at) <= 7),
            strong_matches=strong_matches,
        )

    def paginate(self, jobs: list[Job], page_number: int, page_size: int) -> tuple[list[Job], int]:
        total_pages = max(1, ceil(len(jobs) / page_size))
        current_page = max(1, min(page_number, total_pages))
        start = (current_page - 1) * page_size
        end = start + page_size
        return jobs[start:end], total_pages
