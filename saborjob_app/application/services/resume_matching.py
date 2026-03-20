from __future__ import annotations

import numpy as np

from saborjob_app.application.ports import TextEncoder
from saborjob_app.domain.models import Job, MatchResult, ResumeProfile
from saborjob_app.domain.rules import (
    build_job_search_text,
    build_match_reasons,
    build_resume_profile,
    extract_job_keywords,
    extract_job_seniority,
    is_remote,
)


class ResumeMatchingService:
    def __init__(self, encoder: TextEncoder) -> None:
        self._encoder = encoder

    def analyze_resume_match(
        self,
        jobs: list[Job],
        resume_text: str,
        progress_callback=None,
    ) -> tuple[ResumeProfile, dict[str, MatchResult]]:
        if progress_callback:
            progress_callback(10, "Lendo o texto do curriculo")
        profile = build_resume_profile(resume_text)

        if progress_callback:
            progress_callback(30, "Carregando o modelo local em CPU")
        resume_embedding = self._encode_single(profile.profile_text)

        if progress_callback:
            progress_callback(60, "Calculando representacao semantica das vagas")
        job_embeddings = self._encode_jobs(jobs)

        if progress_callback:
            progress_callback(80, "Comparando perfil e vagas")
        semantic_scores = self._cosine_similarity_scores(job_embeddings, resume_embedding)

        match_results: dict[str, MatchResult] = {}

        for job, semantic_score in zip(jobs, semantic_scores):
            job_keywords = extract_job_keywords(job)
            keyword_overlap = sorted(set(profile.keywords).intersection(job_keywords))

            if profile.keywords:
                keyword_score = min(len(keyword_overlap) / min(len(profile.keywords), 6), 1.0)
            else:
                keyword_score = 0.0

            job_seniority = extract_job_seniority(job)
            seniority_match = bool(profile.seniority and job_seniority == profile.seniority)
            work_mode_match = bool(profile.work_mode == "Remoto" and is_remote(job))

            final_score = round(
                min(
                    100,
                    (float(semantic_score) * 65)
                    + (keyword_score * 25)
                    + (10 if seniority_match else 0)
                    + (8 if work_mode_match else 0),
                )
            )

            match_results[job.url] = MatchResult(
                score=final_score,
                semantic_score=round(float(semantic_score) * 100),
                keyword_overlap=keyword_overlap,
                seniority_match=seniority_match,
                work_mode_match=work_mode_match,
                reasons=build_match_reasons(
                    profile,
                    keyword_overlap,
                    seniority_match,
                    work_mode_match,
                    float(semantic_score),
                ),
            )

        if progress_callback:
            progress_callback(100, "Analise finalizada")

        return profile, match_results

    def _encode_single(self, text: str) -> np.ndarray:
        return np.array(self._encoder.encode([text])[0], dtype=float)

    def _encode_jobs(self, jobs: list[Job]) -> np.ndarray:
        job_texts = [build_job_search_text(job) for job in jobs]
        return np.array(self._encoder.encode(job_texts), dtype=float)

    @staticmethod
    def _cosine_similarity_scores(job_embeddings: np.ndarray, resume_embedding: np.ndarray) -> np.ndarray:
        scores = job_embeddings @ resume_embedding
        return np.clip((scores + 1) / 2, 0, 1)
