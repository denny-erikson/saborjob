from __future__ import annotations

import re

from saborjob_app.config import PROFILE_KEYWORDS, SENIORITY_PATTERNS
from saborjob_app.domain.models import Job, ResumeProfile


def normalize_posted_at(value: str | None) -> str:
    if not value:
        return "Data indisponivel"
    return value.strip()


def normalize_match_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip().lower()


def parse_posted_days(value: str | None) -> int:
    if not value:
        return 9999

    value_lower = value.lower()
    if "hoje" in value_lower:
        return 0

    match = re.search(r"(\d+)\s+(dia|dias|semana|semanas|m[eê]s|m[eê]ses)", value_lower)
    if not match:
        return 9999

    amount = int(match.group(1))
    unit = match.group(2)
    if unit.startswith("semana"):
        return amount * 7
    if unit.startswith("m"):
        return amount * 30
    return amount


def is_remote(job: Job) -> bool:
    tags = [str(tag).lower() for tag in job.tags]
    location = (job.location or "").lower()
    return "remoto" in tags or "home office" in location


def extract_profile_keywords(text: str) -> list[str]:
    normalized_text = normalize_match_text(text)
    matches: list[str] = []

    for keyword in PROFILE_KEYWORDS:
        pattern = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
        if re.search(rf"(?<!\w){pattern}(?!\w)", normalized_text):
            matches.append(keyword)

    return matches


def extract_seniority(text: str) -> str | None:
    normalized_text = normalize_match_text(text)
    for seniority, patterns in SENIORITY_PATTERNS.items():
        if any(re.search(pattern, normalized_text) for pattern in patterns):
            return seniority
    return None


def extract_work_mode(text: str) -> str | None:
    normalized_text = normalize_match_text(text)
    if "remoto" in normalized_text or "home office" in normalized_text:
        return "Remoto"
    if "hibrido" in normalized_text or "híbrido" in normalized_text:
        return "Hibrido"
    if "presencial" in normalized_text:
        return "Presencial"
    return None


def build_resume_profile(resume_text: str) -> ResumeProfile:
    condensed_text = re.sub(r"\s+", " ", resume_text).strip()
    keywords = extract_profile_keywords(condensed_text)
    seniority = extract_seniority(condensed_text)
    work_mode = extract_work_mode(condensed_text)

    profile_text_parts = []
    if seniority:
        profile_text_parts.append(f"Senioridade: {seniority}")
    if work_mode:
        profile_text_parts.append(f"Preferencia: {work_mode}")
    if keywords:
        profile_text_parts.append(f"Tecnologias: {', '.join(keywords[:14])}")
    profile_text_parts.append(condensed_text[:3500])

    return ResumeProfile(
        text=condensed_text,
        keywords=keywords,
        seniority=seniority,
        work_mode=work_mode,
        profile_text=" | ".join(part for part in profile_text_parts if part),
    )


def build_job_search_text(job: Job) -> str:
    tags = ", ".join(job.tags)
    return " | ".join(
        [
            f"Titulo: {job.title}",
            f"Empresa: {job.company or ''}",
            f"Local: {job.location or ''}",
            f"Tags: {tags}",
            f"Publicado: {job.posted_at or ''}",
        ]
    )


def extract_job_keywords(job: Job) -> list[str]:
    searchable = normalize_match_text(
        " ".join([job.title, job.company or "", job.location or "", " ".join(job.tags)])
    )
    matches: list[str] = []

    for keyword in PROFILE_KEYWORDS:
        pattern = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
        if re.search(rf"(?<!\w){pattern}(?!\w)", searchable):
            matches.append(keyword)
    return matches


def extract_job_seniority(job: Job) -> str | None:
    searchable = normalize_match_text(" ".join([job.title, " ".join(job.tags)]))
    for seniority, patterns in SENIORITY_PATTERNS.items():
        if any(re.search(pattern, searchable) for pattern in patterns):
            return seniority
    return None


def build_match_reasons(
    profile: ResumeProfile,
    keyword_overlap: list[str],
    seniority_match: bool,
    work_mode_match: bool,
    semantic_score: float,
) -> list[str]:
    reasons: list[str] = []

    if keyword_overlap:
        reasons.append(f"Stack no ponto: {', '.join(keyword_overlap[:3])}")
    if seniority_match and profile.seniority:
        reasons.append(f"Senioridade alinhada a {profile.seniority}")
    if work_mode_match and profile.work_mode == "Remoto":
        reasons.append("Modelo remoto compativel")
    elif work_mode_match and profile.work_mode:
        reasons.append(f"Modelo {profile.work_mode.lower()} compativel")
    if semantic_score >= 0.72:
        reasons.append("Boa leitura com seu perfil")
    elif semantic_score >= 0.6:
        reasons.append("Perfil com boa proximidade")

    if not reasons:
        reasons.append("Leitura geral positiva para o seu perfil")

    return reasons[:3]


def get_flavor_label(score: int) -> str:
    if score <= 39:
        return "sem sabor"
    if score <= 54:
        return "pouco tempero"
    if score <= 69:
        return "bom sabor"
    if score <= 84:
        return "sabor alto"
    return "sabor absurdo"
