import html
import json
import re
from math import ceil
from pathlib import Path

import streamlit as st


DATA_FILE = Path("data/solides_jobs.json")
PAGE_SIZE_OPTIONS = [4, 6, 8, 10, 12]


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


def sort_jobs(jobs: list[dict], sort_option: str) -> list[dict]:
    if sort_option == "Empresa (A-Z)":
        return sorted(jobs, key=lambda job: (job.get("company") or "").lower())

    if sort_option == "Local (A-Z)":
        return sorted(jobs, key=lambda job: (job.get("location") or "").lower())

    return sorted(jobs, key=lambda job: parse_posted_days(job.get("posted_at")), reverse=False)


def build_metric_card(label: str, value: str, helper: str) -> str:
    return f"""
    <div class="metric-card">
        <div>
            <span class="metric-label">{html.escape(label)}</span>
            <strong class="metric-value">{html.escape(value)}</strong>
        </div>
        <span class="metric-helper">{html.escape(helper)}</span>
    </div>
    """


def build_tag_pills(tags: list[str]) -> str:
    if not tags:
        return '<span class="tag-pill muted">Sem tags</span>'

    return "".join(
        f'<span class="tag-pill">{html.escape(tag)}</span>'
        for tag in tags
    )


def build_job_card(job: dict) -> str:
    title = html.escape(job.get("title") or "Titulo indisponivel")
    company = html.escape(job.get("company") or "Empresa nao informada")
    location = html.escape(job.get("location") or "Local nao informado")
    posted_at = html.escape(normalize_posted_at(job.get("posted_at")))
    url = html.escape(job.get("url") or "#", quote=True)
    tags = build_tag_pills(job.get("tags") or [])
    remote_badge = '<span class="status-pill">Remoto</span>' if is_remote(job) else ""

    return f"""
    <article class="job-card">
        <div class="job-card-top">
            <div>
                <span class="eyebrow">Vaga ativa</span>
                <h3>{title}</h3>
            </div>
            {remote_badge}
        </div>
        <div class="job-meta">
            <span>{company}</span>
            <span>{location}</span>
            <span>{posted_at}</span>
        </div>
        <div class="job-footer">
            <div class="tag-row">{tags}</div>
            <a class="job-link" href="{url}" target="_blank">Abrir vaga</a>
        </div>
    </article>
    """


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
            max-width: 15ch;
        }

        .hero-copy {
            max-width: 64ch;
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
        .tag-pill {
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
            <span class="hero-kicker">Job Radar</span>
            <h1 class="hero-title">Radar de vagas Full Stack com leitura rapida e foco no que importa.</h1>
            <p class="hero-copy">
                Explore as oportunidades coletadas da Solides com uma visualizacao mais enxuta,
                filtros sempre acessiveis na lateral e cards prontos para triagem objetiva. Hoje o radar mostra
                <strong>{total_jobs}</strong> vagas disponiveis no arquivo local.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(jobs: list[dict]) -> None:
    companies = len({job.get("company") for job in jobs if job.get("company")})
    locations = len({job.get("location") for job in jobs if job.get("location")})
    remote_jobs = sum(1 for job in jobs if is_remote(job))
    recent_jobs = sum(1 for job in jobs if parse_posted_days(job.get("posted_at")) <= 7)

    metric_columns = st.columns(4)
    metrics = [
        ("Vagas", str(len(jobs)), "Volume total carregado no dashboard"),
        ("Empresas", str(companies), "Marcas unicas nas listagens"),
        ("Locais", str(locations), "Cidades ou regioes representadas"),
        ("Recentes", str(recent_jobs), f"{remote_jobs} com indicativo de trabalho remoto"),
    ]

    for column, metric in zip(metric_columns, metrics):
        with column:
            st.markdown(build_metric_card(*metric), unsafe_allow_html=True)


def render_sidebar_filters(
    jobs: list[dict],
) -> tuple[str, list[str], list[str], list[str], str, int]:
    all_locations = sorted({job.get("location") for job in jobs if job.get("location")})
    all_companies = sorted({job.get("company") for job in jobs if job.get("company")})
    all_tags = sorted({tag for job in jobs for tag in (job.get("tags") or [])})

    with st.sidebar:
        st.markdown('<div class="sidebar-title">Filtros</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-copy">Busca, refinamento e ordenacao permanecem fixos na lateral para a navegacao ficar mais fluida.</div>',
            unsafe_allow_html=True,
        )
        search_value = st.text_input(
            "Buscar",
            value="",
            placeholder="Titulo, empresa, local ou tag",
        )
        sort_option = st.selectbox(
            "Ordenar por",
            ["Mais recentes", "Empresa (A-Z)", "Local (A-Z)"],
            index=0,
        )
        page_size = st.selectbox("Vagas por pagina", PAGE_SIZE_OPTIONS, index=1)
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
        page_title="Job Radar Solides",
        page_icon=":briefcase:",
        layout="wide",
    )

    inject_styles()

    jobs = load_jobs()
    if not jobs:
        return

    render_hero(len(jobs))
    render_metrics(jobs)

    (
        search_value,
        selected_locations,
        selected_companies,
        selected_tags,
        sort_option,
        page_size,
    ) = render_sidebar_filters(jobs)

    filtered_jobs = apply_filters(
        jobs,
        search_value,
        selected_locations,
        selected_companies,
        selected_tags,
    )
    filtered_jobs = sort_jobs(filtered_jobs, sort_option)

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
        st.markdown(build_job_card(job), unsafe_allow_html=True)

    render_pagination(page_number, total_pages)
    st.caption(f"Fonte local: {DATA_FILE}")


if __name__ == "__main__":
    main()
