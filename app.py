import hashlib
import html
import json
import os
import re
from math import ceil
from pathlib import Path
from textwrap import dedent

import numpy as np
import streamlit as st


os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")


DATA_FILE = Path("data/solides_jobs.json")
PAGE_SIZE_OPTIONS = [4, 6, 8, 10, 12]
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BRAND_NAME = "SaborJob"
ADHERENCE_TOOLTIP = "Percentual estimado de compatibilidade entre a vaga e seu curriculo."
FLAVOR_TOOLTIP = "Leitura rapida do potencial da vaga. Quanto mais sabor, mais faz sentido olhar com atencao."
PROFILE_KEYWORDS = [
    "python",
    "django",
    "flask",
    "fastapi",
    "java",
    "spring",
    "javascript",
    "typescript",
    "node",
    "react",
    "next.js",
    "next",
    "angular",
    "vue",
    "php",
    "laravel",
    "c#",
    ".net",
    "dotnet",
    "golang",
    "go",
    "ruby",
    "rails",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "sql",
    "postgresql",
    "mysql",
    "mongodb",
    "redis",
    "graphql",
    "rest",
    "microservices",
    "api",
]
SENIORITY_PATTERNS = {
    "Junior": [r"\bjunior\b", r"\bjr\b", r"\btrainee\b", r"\bestagi[áa]rio\b"],
    "Pleno": [r"\bpleno\b", r"\bpl\b", r"\bmid\b", r"\bintermedi[áa]rio\b"],
    "Senior": [r"\bsenior\b", r"\bsr\b", r"\bespecialista\b", r"\blead\b", r"\bstaff\b"],
}


@st.cache_data(show_spinner=False)
def load_jobs() -> list[dict]:
    if not DATA_FILE.exists():
        st.error(f"Arquivo nao encontrado: {DATA_FILE}")
        return []

    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


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


def is_remote(job: dict) -> bool:
    tags = [str(tag).lower() for tag in (job.get("tags") or [])]
    location = (job.get("location") or "").lower()
    return "remoto" in tags or "home office" in location


def apply_filters(
    jobs: list[dict],
    search_value: str,
    selected_locations: list[str],
    selected_companies: list[str],
    selected_tags: list[str],
) -> list[dict]:
    filtered_jobs = jobs

    if search_value:
        query = search_value.lower().strip()
        filtered_jobs = [
            job
            for job in filtered_jobs
            if query in (job.get("title", "") or "").lower()
            or query in (job.get("company", "") or "").lower()
            or query in (job.get("location", "") or "").lower()
            or any(query in str(tag).lower() for tag in (job.get("tags") or []))
        ]

    if selected_locations:
        filtered_jobs = [job for job in filtered_jobs if job.get("location") in selected_locations]

    if selected_companies:
        filtered_jobs = [job for job in filtered_jobs if job.get("company") in selected_companies]

    if selected_tags:
        filtered_jobs = [
            job for job in filtered_jobs if any(tag in selected_tags for tag in (job.get("tags") or []))
        ]

    return filtered_jobs


@st.cache_resource(show_spinner=False)
def load_embedding_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Dependencia ausente para ranking local. Instale sentence-transformers."
        ) from exc

    return SentenceTransformer(model_name, device="cpu")


@st.cache_data(show_spinner=False)
def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("Dependencia ausente para leitura de PDF. Instale PyMuPDF.") from exc

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    chunks: list[str] = []

    for page in document:
        text = page.get_text("text")
        if text:
            chunks.append(text)

    document.close()
    return "\n".join(chunks).strip()


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


def build_resume_profile(resume_text: str) -> dict:
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

    return {
        "text": condensed_text,
        "keywords": keywords,
        "seniority": seniority,
        "work_mode": work_mode,
        "profile_text": " | ".join(part for part in profile_text_parts if part),
    }


def build_job_search_text(job: dict) -> str:
    tags = ", ".join(job.get("tags") or [])
    return " | ".join(
        [
            f"Titulo: {job.get('title') or ''}",
            f"Empresa: {job.get('company') or ''}",
            f"Local: {job.get('location') or ''}",
            f"Tags: {tags}",
            f"Publicado: {job.get('posted_at') or ''}",
        ]
    )


@st.cache_data(show_spinner=False)
def encode_job_texts(texts: tuple[str, ...], model_name: str) -> list[list[float]]:
    model = load_embedding_model(model_name)
    embeddings = model.encode(list(texts), normalize_embeddings=True, device="cpu")
    return embeddings.tolist()


def cosine_similarity_scores(job_embeddings: np.ndarray, resume_embedding: np.ndarray) -> np.ndarray:
    scores = job_embeddings @ resume_embedding
    return np.clip((scores + 1) / 2, 0, 1)


def extract_job_keywords(job: dict) -> list[str]:
    searchable = normalize_match_text(
        " ".join(
            [
                job.get("title") or "",
                job.get("company") or "",
                job.get("location") or "",
                " ".join(job.get("tags") or []),
            ]
        )
    )

    matches: list[str] = []
    for keyword in PROFILE_KEYWORDS:
        pattern = re.escape(keyword.lower()).replace(r"\ ", r"\s+")
        if re.search(rf"(?<!\w){pattern}(?!\w)", searchable):
            matches.append(keyword)
    return matches


def extract_job_seniority(job: dict) -> str | None:
    searchable = normalize_match_text(
        " ".join([job.get("title") or "", " ".join(job.get("tags") or [])])
    )

    for seniority, patterns in SENIORITY_PATTERNS.items():
        if any(re.search(pattern, searchable) for pattern in patterns):
            return seniority
    return None


def build_match_reasons(
    job: dict,
    profile: dict,
    keyword_overlap: list[str],
    seniority_match: bool,
    work_mode_match: bool,
    semantic_score: float,
) -> list[str]:
    reasons: list[str] = []

    if keyword_overlap:
        reasons.append(f"Stack no ponto: {', '.join(keyword_overlap[:3])}")
    if seniority_match and profile.get("seniority"):
        reasons.append(f"Senioridade alinhada a {profile['seniority']}")
    if work_mode_match and profile.get("work_mode") == "Remoto":
        reasons.append("Modelo remoto compatível")
    elif work_mode_match and profile.get("work_mode"):
        reasons.append(f"Modelo {profile['work_mode'].lower()} compatível")
    if semantic_score >= 0.72:
        reasons.append("Boa leitura com seu perfil")
    elif semantic_score >= 0.6:
        reasons.append("Perfil com boa proximidade")

    if not reasons:
        reasons.append("Leitura geral positiva para o seu perfil")

    return reasons[:3]


def encode_resume_text(text: str, model_name: str) -> np.ndarray:
    model = load_embedding_model(model_name)
    embedding = model.encode([text], normalize_embeddings=True, device="cpu")[0]
    return np.array(embedding, dtype=float)


def analyze_resume_match(
    jobs: list[dict],
    resume_text: str,
    progress_callback=None,
) -> tuple[dict, dict[str, dict]]:
    if progress_callback:
        progress_callback(10, "Lendo o texto do curriculo")
    profile = build_resume_profile(resume_text)

    if progress_callback:
        progress_callback(30, "Carregando o modelo local em CPU")
    resume_embedding = encode_resume_text(profile["profile_text"], EMBEDDING_MODEL_NAME)

    job_texts = tuple(build_job_search_text(job) for job in jobs)

    if progress_callback:
        progress_callback(60, "Calculando representacao semantica das vagas")
    job_embeddings = np.array(encode_job_texts(job_texts, EMBEDDING_MODEL_NAME), dtype=float)

    if progress_callback:
        progress_callback(80, "Comparando perfil e vagas")
    semantic_scores = cosine_similarity_scores(job_embeddings, resume_embedding)

    match_results: dict[str, dict] = {}

    for job, semantic_score in zip(jobs, semantic_scores):
        job_keywords = extract_job_keywords(job)
        keyword_overlap = sorted(set(profile["keywords"]).intersection(job_keywords))

        if profile["keywords"]:
            keyword_score = min(len(keyword_overlap) / min(len(profile["keywords"]), 6), 1.0)
        else:
            keyword_score = 0.0

        job_seniority = extract_job_seniority(job)
        seniority_match = bool(profile["seniority"] and job_seniority == profile["seniority"])
        work_mode_match = bool(profile["work_mode"] == "Remoto" and is_remote(job))

        final_score = round(
            min(
                100,
                (semantic_score * 65)
                + (keyword_score * 25)
                + (10 if seniority_match else 0)
                + (8 if work_mode_match else 0),
            )
        )

        match_results[job.get("url") or build_job_search_text(job)] = {
            "score": final_score,
            "semantic_score": round(float(semantic_score) * 100),
            "keyword_overlap": keyword_overlap,
            "seniority_match": seniority_match,
            "work_mode_match": work_mode_match,
            "reasons": build_match_reasons(
                job,
                profile,
                keyword_overlap,
                seniority_match,
                work_mode_match,
                float(semantic_score),
            ),
        }

    if progress_callback:
        progress_callback(100, "Analise finalizada")

    return profile, match_results


def get_resume_digest(pdf_bytes: bytes) -> str:
    return hashlib.sha256(pdf_bytes).hexdigest()


def clear_resume_analysis() -> None:
    st.session_state["resume_profile"] = None
    st.session_state["resume_match_results"] = None
    st.session_state["resume_analyzed_digest"] = None
    st.session_state["resume_error"] = None


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


def sort_jobs(jobs: list[dict], sort_option: str, match_results: dict[str, dict] | None = None) -> list[dict]:
    if sort_option == "Maior aderencia" and match_results:
        return sorted(
            jobs,
            key=lambda job: (
                -(match_results.get(job.get("url") or "", {}).get("score", 0)),
                parse_posted_days(job.get("posted_at")),
            ),
        )

    if sort_option == "Empresa (A-Z)":
        return sorted(jobs, key=lambda job: (job.get("company") or "").lower())

    if sort_option == "Local (A-Z)":
        return sorted(jobs, key=lambda job: (job.get("location") or "").lower())

    return sorted(jobs, key=lambda job: parse_posted_days(job.get("posted_at")), reverse=False)


def build_metric_card(label: str, value: str, helper: str) -> str:
    return dedent(
        f"""
        <div class="metric-card">
            <div>
                <span class="metric-label">{html.escape(label)}</span>
                <strong class="metric-value">{html.escape(value)}</strong>
            </div>
            <span class="metric-helper">{html.escape(helper)}</span>
        </div>
        """
    ).strip()


def build_tag_pills(tags: list[str]) -> str:
    if not tags:
        return '<span class="tag-pill muted">Sem tags</span>'

    return "".join(
        f'<span class="tag-pill">{html.escape(tag)}</span>'
        for tag in tags
    )


def build_job_card(job: dict, match_data: dict | None = None) -> str:
    title = html.escape(job.get("title") or "Titulo indisponivel")
    company = html.escape(job.get("company") or "Empresa nao informada")
    location = html.escape(job.get("location") or "Local nao informado")
    posted_at = html.escape(normalize_posted_at(job.get("posted_at")))
    url = html.escape(job.get("url") or "#", quote=True)
    tags = build_tag_pills(job.get("tags") or [])
    remote_badge = '<span class="status-pill">Remoto</span>' if is_remote(job) else ""
    score_badge = ""
    flavor_badge = ""
    match_reasons = ""

    if match_data:
        score_badge = (
            f'<span class="score-pill" title="{html.escape(ADHERENCE_TOOLTIP, quote=True)}">'
            f'{match_data["score"]}% aderencia'
            "</span>"
        )
        flavor_badge = (
            f'<span class="flavor-pill" title="{html.escape(FLAVOR_TOOLTIP, quote=True)}">'
            f'{html.escape(get_flavor_label(match_data["score"]))}'
            "</span>"
        )
        match_reasons = "".join(
            f'<span class="signal-pill">{html.escape(reason)}</span>'
            for reason in match_data.get("reasons", [])
        )

    return "".join(
        [
            '<div class="job-card">',
            '<div class="job-card-top">',
            "<div>",
            '<span class="eyebrow">Vaga ativa</span>',
            f"<h3>{title}</h3>",
            "</div>",
            '<div class="job-badges">',
            score_badge,
            flavor_badge,
            remote_badge,
            "</div>",
            "</div>",
            '<div class="job-meta">',
            f"<span>{company}</span>",
            f"<span>{location}</span>",
            f"<span>{posted_at}</span>",
            "</div>",
            f'<div class="signal-row">{match_reasons}</div>',
            '<div class="job-footer">',
            f'<div class="tag-row">{tags}</div>',
            f'<a class="job-link" href="{url}" target="_blank">Abrir vaga</a>',
            "</div>",
            "</div>",
        ]
    )


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --bg-start: #f4f8ff;
            --bg-end: #eef3ea;
            --surface: rgba(255, 255, 255, 0.78);
            --surface-strong: #ffffff;
            --border: rgba(15, 23, 42, 0.08);
            --border-strong: rgba(15, 23, 42, 0.14);
            --text-main: #0f172a;
            --text-soft: #475569;
            --text-muted: #64748b;
            --accent: #0f766e;
            --accent-strong: #115e59;
            --accent-soft: rgba(15, 118, 110, 0.10);
            --shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
            --radius-lg: 26px;
            --radius-md: 18px;
            --radius-sm: 999px;
        }

        html, body, [class*="css"] {
            font-family: "Manrope", "Segoe UI", sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(14, 165, 233, 0.16), transparent 28%),
                radial-gradient(circle at top right, rgba(16, 185, 129, 0.14), transparent 26%),
                linear-gradient(180deg, var(--bg-start) 0%, var(--bg-end) 100%);
            color: var(--text-main);
        }

        [data-testid="stAppViewContainer"] > .main {
            padding-top: 1.6rem;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 250, 252, 0.92));
            border-right: 1px solid rgba(15, 23, 42, 0.08);
        }

        [data-testid="stSidebar"] .block-container {
            padding-top: 1rem;
            padding-bottom: 1.25rem;
        }

        .block-container {
            max-width: 1180px;
            padding-top: 0;
            padding-bottom: 2.5rem;
        }

        .hero-panel {
            padding: 1rem 1.35rem;
            border-radius: 22px;
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.78)),
                linear-gradient(135deg, rgba(15, 118, 110, 0.15), rgba(14, 165, 233, 0.10));
            border: 1px solid rgba(255, 255, 255, 0.7);
            box-shadow: var(--shadow);
            position: relative;
            overflow: hidden;
            margin-bottom: 0.9rem;
        }

        .hero-panel::after {
            content: "";
            position: absolute;
            inset: auto -72px -78px auto;
            width: 180px;
            height: 180px;
            border-radius: 999px;
            background: radial-gradient(circle, rgba(15, 118, 110, 0.18), transparent 65%);
        }

        .hero-kicker {
            display: inline-flex;
            padding: 0.3rem 0.7rem;
            border-radius: var(--radius-sm);
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--accent-strong);
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid rgba(15, 118, 110, 0.12);
        }

        .hero-title {
            margin: 0.5rem 0 0.18rem;
            font-size: clamp(1.4rem, 1.9vw, 2rem);
            line-height: 1.02;
            letter-spacing: -0.04em;
            max-width: 30ch;
        }

        .hero-copy {
            max-width: 100ch;
            color: var(--text-soft);
            font-size: 0.9rem;
            line-height: 1.45;
            margin-bottom: 0;
        }

        .section-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--text-main);
            margin: 0.4rem 0 0.8rem;
        }

        .section-subtitle {
            color: var(--text-muted);
            margin-bottom: 1rem;
        }

        .metric-card {
            min-height: 122px;
            padding: 0.9rem 1rem;
            border-radius: var(--radius-md);
            background: var(--surface);
            border: 1px solid var(--border);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
            backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .metric-label,
        .metric-helper {
            display: block;
        }

        .metric-label {
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--text-muted);
            margin-bottom: 0.45rem;
            font-weight: 700;
        }

        .metric-value {
            display: block;
            font-size: 1.65rem;
            line-height: 1;
            letter-spacing: -0.05em;
            color: var(--text-main);
            margin-bottom: 0;
        }

        .metric-helper {
            color: var(--text-soft);
            font-size: 0.84rem;
            line-height: 1.35;
        }

        .result-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 1rem 0 0.7rem;
        }

        .result-count {
            font-size: 1rem;
            color: var(--text-soft);
        }

        .result-count strong {
            color: var(--text-main);
        }

        .page-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.45rem 0.8rem;
            border-radius: var(--radius-sm);
            background: rgba(255, 255, 255, 0.78);
            color: var(--text-soft);
            border: 1px solid var(--border);
            font-size: 0.9rem;
            font-weight: 700;
        }

        .job-card {
            padding: 1.15rem 1.2rem;
            border-radius: 20px;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(255, 255, 255, 0.82));
            border: 1px solid rgba(255, 255, 255, 0.92);
            box-shadow: var(--shadow);
            margin-bottom: 0.85rem;
        }

        .job-card-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 0.6rem;
        }

        .job-badges {
            display: flex;
            align-items: center;
            justify-content: flex-end;
            gap: 0.45rem;
            flex-wrap: wrap;
        }

        .job-card h3 {
            margin: 0.25rem 0 0;
            font-size: 1.12rem;
            line-height: 1.25;
            letter-spacing: -0.03em;
            color: var(--text-main);
        }

        .eyebrow {
            color: var(--accent-strong);
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 800;
        }

        .status-pill,
        .tag-pill,
        .score-pill,
        .flavor-pill,
        .signal-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--radius-sm);
            font-size: 0.82rem;
            font-weight: 700;
            line-height: 1;
        }

        .status-pill {
            white-space: nowrap;
            height: fit-content;
            padding: 0.55rem 0.85rem;
            background: var(--accent-soft);
            color: var(--accent-strong);
            border: 1px solid rgba(15, 118, 110, 0.16);
        }

        .score-pill {
            white-space: nowrap;
            height: fit-content;
            padding: 0.55rem 0.85rem;
            background: rgba(15, 23, 42, 0.06);
            color: var(--text-main);
            border: 1px solid rgba(15, 23, 42, 0.08);
        }

        .flavor-pill {
            white-space: nowrap;
            height: fit-content;
            padding: 0.55rem 0.85rem;
            background: rgba(15, 118, 110, 0.10);
            color: var(--accent-strong);
            border: 1px solid rgba(15, 118, 110, 0.16);
        }

        .job-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            color: var(--text-soft);
            margin-bottom: 0.85rem;
        }

        .job-meta span {
            padding: 0.48rem 0.75rem;
            border-radius: var(--radius-sm);
            background: rgba(248, 250, 252, 0.9);
            border: 1px solid var(--border);
        }

        .job-footer {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: center;
            flex-wrap: wrap;
        }

        .signal-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-bottom: 0.8rem;
            min-height: 1px;
        }

        .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
        }

        .tag-pill {
            padding: 0.5rem 0.72rem;
            background: rgba(15, 23, 42, 0.05);
            color: var(--text-soft);
            border: 1px solid rgba(15, 23, 42, 0.05);
        }

        .signal-pill {
            padding: 0.42rem 0.68rem;
            background: rgba(15, 118, 110, 0.08);
            color: var(--accent-strong);
            border: 1px solid rgba(15, 118, 110, 0.14);
            justify-content: flex-start;
        }

        .tag-pill.muted {
            color: var(--text-muted);
        }

        .job-link {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 134px;
            min-height: 44px;
            border-radius: var(--radius-sm);
            background: linear-gradient(135deg, var(--accent) 0%, #0f766e 100%);
            color: #ffffff !important;
            text-decoration: none !important;
            font-weight: 800;
            box-shadow: 0 12px 24px rgba(15, 118, 110, 0.18);
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div,
        div[data-baseweb="tag"] {
            border-radius: 16px !important;
        }

        div[data-testid="stTextInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div {
            border: 1px solid var(--border-strong) !important;
            background: rgba(255, 255, 255, 0.9) !important;
        }

        div.stButton > button {
            width: 100%;
            min-height: 46px;
            border-radius: var(--radius-sm);
            border: 1px solid transparent;
            background: #0f172a;
            color: white;
            font-weight: 700;
        }

        div.stButton > button[kind="secondary"] {
            background: rgba(255, 255, 255, 0.9);
            color: var(--text-main);
            border-color: var(--border);
        }

        .sidebar-title {
            font-size: 1rem;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 0.2rem;
        }

        .sidebar-copy {
            color: var(--text-muted);
            font-size: 0.9rem;
            line-height: 1.45;
            margin-bottom: 0.8rem;
        }

        .profile-summary {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
            margin: 0.2rem 0 0.9rem;
        }

        .profile-summary strong,
        .profile-summary span {
            display: block;
        }

        .profile-summary strong {
            color: var(--text-main);
            font-size: 0.96rem;
            margin-bottom: 0.2rem;
        }

        .profile-summary span {
            color: var(--text-soft);
            font-size: 0.88rem;
            line-height: 1.45;
        }

        .empty-state {
            padding: 2rem;
            text-align: center;
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, 0.74);
            border: 1px dashed rgba(15, 23, 42, 0.16);
            color: var(--text-soft);
        }

        @media (max-width: 768px) {
            .hero-panel {
                padding: 0.95rem 1rem;
            }

            .job-card {
                padding: 1.1rem;
            }

            .result-bar {
                flex-direction: column;
                align-items: flex-start;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(total_jobs: int) -> None:
    st.markdown(
        f"""
        <section class="hero-panel">
            <span class="hero-kicker">{BRAND_NAME}</span>
            <h1 class="hero-title">Não é só sobre buscar vaga.<br>É sentir quando vale a pena.</h1>
            <p class="hero-copy">
                O {BRAND_NAME} traz triagem objetiva com uma camada de leitura intuitiva. A aderência mede o fit, e o sabor traduz o valor real da oportunidade — rápido, direto e sem ruído.Hoje o painel mostra <strong>{total_jobs}</strong> vagas disponiveis.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Aderencia: {ADHERENCE_TOOLTIP} Sabor: {FLAVOR_TOOLTIP}")


def render_profile_summary(profile: dict) -> None:
    st.markdown(
        f"""
        <div class="profile-summary">
            <strong>Perfil identificado</strong>
            <span>Senioridade: {html.escape(profile.get("seniority") or "Nao identificada")}</span>
            <span>Modelo de trabalho: {html.escape(profile.get("work_mode") or "Nao identificado")}</span>
            <span>Tecnologias-chave: {html.escape(', '.join(profile.get("keywords", [])[:8]) or "Nao identificadas")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(jobs: list[dict], match_results: dict[str, dict] | None = None) -> None:
    companies = len({job.get("company") for job in jobs if job.get("company")})
    locations = len({job.get("location") for job in jobs if job.get("location")})
    remote_jobs = sum(1 for job in jobs if is_remote(job))
    recent_jobs = sum(1 for job in jobs if parse_posted_days(job.get("posted_at")) <= 7)
    strong_matches = 0

    if match_results:
        strong_matches = sum(1 for result in match_results.values() if result.get("score", 0) >= 70)

    metric_columns = st.columns(4)
    metrics = [
        ("Vagas", str(len(jobs)), "Volume total carregado no dashboard"),
        ("Empresas", str(companies), "Marcas unicas nas listagens"),
        ("Locais", str(locations), "Cidades ou regioes representadas"),
        (
            "Aderentes" if match_results else "Recentes",
            str(strong_matches if match_results else recent_jobs),
            (
                "Vagas com score igual ou acima de 70%"
                if match_results
                else f"{remote_jobs} com indicativo de trabalho remoto"
            ),
        ),
    ]

    for column, metric in zip(metric_columns, metrics):
        with column:
            st.markdown(build_metric_card(*metric), unsafe_allow_html=True)


def render_sidebar_filters(
    jobs: list[dict],
    profile_active: bool,
) -> tuple[str, list[str], list[str], list[str], str, int, object | None, bool, bool]:
    all_locations = sorted({job.get("location") for job in jobs if job.get("location")})
    all_companies = sorted({job.get("company") for job in jobs if job.get("company")})
    all_tags = sorted({tag for job in jobs for tag in (job.get("tags") or [])})

    with st.sidebar:
        st.markdown('<div class="sidebar-title">Filtros</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-copy">Busca, refinamento e ordenacao permanecem fixos na lateral para a navegacao ficar fluida e destacar o que tem mais sabor para o seu perfil.</div>',
            unsafe_allow_html=True,
        )
        search_value = st.text_input(
            "Buscar",
            value="",
            placeholder="Titulo, empresa, local ou tag",
        )
        sort_options = ["Mais recentes", "Empresa (A-Z)", "Local (A-Z)"]
        if profile_active:
            sort_options.insert(0, "Maior aderencia")
        sort_option = st.selectbox(
            "Ordenar por",
            sort_options,
            index=0,
            help="Ordene por aderencia para ver primeiro as vagas com mais sabor para o seu perfil.",
        )
        page_size = st.selectbox("Vagas por pagina", PAGE_SIZE_OPTIONS, index=1)
        st.markdown("### Perfil")
        uploaded_resume = st.file_uploader("Curriculo em PDF", type=["pdf"], key="resume_uploader")
        analyze_clicked = st.button(
            "Analisar curriculo",
            use_container_width=True,
            disabled=uploaded_resume is None,
        )
        clear_clicked = st.button(
            "Limpar analise",
            use_container_width=True,
            disabled=not profile_active and uploaded_resume is None,
        )
        selected_locations = st.multiselect("Localizacoes", all_locations)
        selected_companies = st.multiselect("Empresas", all_companies)
        selected_tags = st.multiselect("Tags", all_tags)

    return (
        search_value,
        selected_locations,
        selected_companies,
        selected_tags,
        sort_option,
        page_size,
        uploaded_resume,
        analyze_clicked,
        clear_clicked,
    )


def sync_page_state(filter_signature: tuple, total_pages: int) -> int:
    previous_signature = st.session_state.get("filter_signature")
    if previous_signature != filter_signature:
        st.session_state.filter_signature = filter_signature
        st.session_state.page_number = 1

    current_page = int(st.session_state.get("page_number", 1))
    current_page = max(1, min(current_page, total_pages))
    st.session_state.page_number = current_page
    return current_page


def render_pagination(page_number: int, total_pages: int) -> int:
    st.markdown(
        f"""
        <div class="result-bar">
            <div class="result-count"><strong>Pagina atual:</strong> {page_number} de {total_pages}</div>
            <span class="page-chip">Navegacao da lista</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prev_col, input_col, next_col = st.columns([1, 1.2, 1], vertical_alignment="bottom")

    with prev_col:
        if st.button("Pagina anterior", disabled=page_number <= 1, use_container_width=True):
            st.session_state.page_number = page_number - 1
            st.rerun()

    with input_col:
        selected_page = st.number_input(
            "Ir para página",
            min_value=1,
            max_value=total_pages,
            value=page_number,
            step=1,
            label_visibility="collapsed",
        )
        if selected_page != page_number:
            st.session_state.page_number = int(selected_page)
            st.rerun()

    with next_col:
        if st.button("Proxima pagina", disabled=page_number >= total_pages, use_container_width=True):
            st.session_state.page_number = page_number + 1
            st.rerun()

    return int(st.session_state.get("page_number", page_number))


def main() -> None:
    st.set_page_config(
        page_title=BRAND_NAME,
        page_icon=":briefcase:",
        layout="wide",
    )

    inject_styles()

    jobs = load_jobs()
    if not jobs:
        return

    profile = st.session_state.get("resume_profile")
    match_results = st.session_state.get("resume_match_results")
    profile_active = bool(match_results)
    sidebar_values = render_sidebar_filters(jobs, profile_active=profile_active)
    (
        search_value,
        selected_locations,
        selected_companies,
        selected_tags,
        sort_option,
        page_size,
        uploaded_resume,
        analyze_clicked,
        clear_clicked,
    ) = sidebar_values

    current_resume_bytes = uploaded_resume.getvalue() if uploaded_resume is not None else None
    current_resume_digest = get_resume_digest(current_resume_bytes) if current_resume_bytes else None
    analyzed_resume_digest = st.session_state.get("resume_analyzed_digest")

    if clear_clicked:
        clear_resume_analysis()
        st.session_state["resume_uploader"] = None
        st.rerun()

    with st.sidebar:
        if st.session_state.get("resume_error"):
            st.error(st.session_state["resume_error"])
        if uploaded_resume is None:
            st.caption("Envie um PDF para calcular aderencia e descobrir quais vagas tem mais sabor para o seu perfil.")
        elif current_resume_digest == analyzed_resume_digest and match_results:
            st.success("Curriculo analisado. A ordenacao por aderencia e a leitura de sabor estao disponiveis.")
        else:
            st.info("Curriculo carregado. Clique em analisar para atualizar aderencia e sabor.")

    render_hero(len(jobs))
    render_metrics(jobs, match_results)

    if profile:
        render_profile_summary(profile)

    filtered_jobs = apply_filters(
        jobs,
        search_value,
        selected_locations,
        selected_companies,
        selected_tags,
    )
    filtered_jobs = sort_jobs(filtered_jobs, sort_option, match_results)

    st.markdown(
        f"""
        <div class="result-bar">
            <div class="result-count">
                <strong>{len(filtered_jobs)}</strong> vagas correspondem aos filtros aplicados.
            </div>
            <span class="page-chip">{sort_option}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if analyze_clicked and current_resume_bytes is not None:
        progress_placeholder = st.empty()
        status_placeholder = st.empty()

        try:
            progress_bar = progress_placeholder.progress(0, text="Preparando a analise local")
            status_box = status_placeholder.status("Processando curriculo", expanded=True)

            def update_progress(step: int, message: str) -> None:
                progress_bar.progress(step, text=message)
                status_box.write(message)

            update_progress(5, "Extraindo texto do PDF")
            resume_text = extract_text_from_pdf_bytes(current_resume_bytes)
            if not resume_text:
                raise RuntimeError("Nao foi possivel extrair texto do PDF enviado.")

            profile, match_results = analyze_resume_match(jobs, resume_text, progress_callback=update_progress)
            st.session_state["resume_profile"] = profile
            st.session_state["resume_match_results"] = match_results
            st.session_state["resume_analyzed_digest"] = current_resume_digest
            st.session_state["resume_error"] = None

            progress_bar.progress(100, text="Analise concluida")
            status_box.update(label="Curriculo processado com sucesso", state="complete", expanded=False)
            st.rerun()
        except RuntimeError as exc:
            clear_resume_analysis()
            st.session_state["resume_error"] = str(exc)
            status_placeholder.error(str(exc))
            progress_placeholder.empty()
        except Exception as exc:
            clear_resume_analysis()
            st.session_state["resume_error"] = str(exc)
            status_placeholder.error(f"Falha ao analisar o curriculo: {exc}")
            progress_placeholder.empty()

    if not filtered_jobs:
        st.markdown(
            """
            <div class="empty-state">
                Nenhuma vaga corresponde aos filtros atuais. Ajuste a busca ou remova algum recorte para ampliar o radar.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    total_pages = max(1, ceil(len(filtered_jobs) / page_size))
    filter_signature = (
        search_value.strip().lower(),
        tuple(selected_locations),
        tuple(selected_companies),
        tuple(selected_tags),
        sort_option,
        page_size,
    )
    page_number = sync_page_state(filter_signature, total_pages)

    start = (page_number - 1) * page_size
    end = start + page_size

    for job in filtered_jobs[start:end]:
        job_match = None
        if match_results:
            job_match = match_results.get(job.get("url") or "")
        st.html(build_job_card(job, job_match))

    render_pagination(page_number, total_pages)
    st.caption(f"Fonte local: {DATA_FILE}")


if __name__ == "__main__":
    main()
