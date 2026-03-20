from __future__ import annotations

import html
from textwrap import dedent

import streamlit as st

from saborjob_app.config import ADHERENCE_TOOLTIP, BRAND_NAME, FLAVOR_TOOLTIP
from saborjob_app.domain.models import Job, MatchResult, MetricsSummary, ResumeProfile, SidebarInputs
from saborjob_app.domain.rules import get_flavor_label, is_remote, normalize_posted_at


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
    return "".join(f'<span class="tag-pill">{html.escape(tag)}</span>' for tag in tags)


def build_job_card(job: Job, match_data: MatchResult | None = None) -> str:
    tags = build_tag_pills(job.tags)
    remote_badge = '<span class="status-pill">Remoto</span>' if is_remote(job) else ""
    score_badge = ""
    flavor_badge = ""
    match_reasons = ""

    if match_data:
        score_badge = (
            f'<span class="score-pill" title="{html.escape(ADHERENCE_TOOLTIP, quote=True)}">'
            f"{match_data.score}% aderencia</span>"
        )
        flavor_badge = (
            f'<span class="flavor-pill" title="{html.escape(FLAVOR_TOOLTIP, quote=True)}">'
            f"{html.escape(get_flavor_label(match_data.score))}</span>"
        )
        match_reasons = "".join(
            f'<span class="signal-pill">{html.escape(reason)}</span>' for reason in match_data.reasons
        )

    return "".join(
        [
            '<div class="job-card">',
            '<div class="job-card-top">',
            "<div>",
            '<span class="eyebrow">Vaga ativa</span>',
            f"<h3>{html.escape(job.title or 'Titulo indisponivel')}</h3>",
            "</div>",
            '<div class="job-badges">',
            score_badge,
            flavor_badge,
            remote_badge,
            "</div>",
            "</div>",
            '<div class="job-meta">',
            f"<span>{html.escape(job.company or 'Empresa nao informada')}</span>",
            f"<span>{html.escape(job.location or 'Local nao informado')}</span>",
            f"<span>{html.escape(normalize_posted_at(job.posted_at))}</span>",
            "</div>",
            f'<div class="signal-row">{match_reasons}</div>',
            '<div class="job-footer">',
            f'<div class="tag-row">{tags}</div>',
            f'<a class="job-link" href="{html.escape(job.url or "#", quote=True)}" target="_blank">Abrir vaga</a>',
            "</div>",
            "</div>",
        ]
    )


def render_hero(total_jobs: int) -> None:
    st.markdown(
        f"""
        <section class="hero-panel">
            <span class="hero-kicker">{BRAND_NAME}</span>
            <h1 class="hero-title">Nao e so sobre buscar vaga.<br>E sentir quando vale a pena.</h1>
            <p class="hero-copy">
                O {BRAND_NAME} traz triagem objetiva com uma camada de leitura intuitiva. A aderencia mede o fit,
                e o sabor traduz o valor real da oportunidade, rapido, direto e sem ruido. Hoje o painel mostra
                <strong>{total_jobs}</strong> vagas disponiveis.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Aderencia: {ADHERENCE_TOOLTIP} Sabor: {FLAVOR_TOOLTIP}")


def render_profile_summary(profile: ResumeProfile) -> None:
    st.markdown(
        f"""
        <div class="profile-summary">
            <strong>Perfil identificado</strong>
            <span>Senioridade: {html.escape(profile.seniority or "Nao identificada")}</span>
            <span>Modelo de trabalho: {html.escape(profile.work_mode or "Nao identificado")}</span>
            <span>Tecnologias-chave: {html.escape(', '.join(profile.keywords[:8]) or "Nao identificadas")}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(summary: MetricsSummary, has_match_results: bool) -> None:
    metrics = [
        ("Vagas", str(summary.total_jobs), "Volume total carregado no dashboard"),
        ("Empresas", str(summary.companies), "Marcas unicas nas listagens"),
        ("Locais", str(summary.locations), "Cidades ou regioes representadas"),
        (
            "Aderentes" if has_match_results else "Recentes",
            str(summary.strong_matches if has_match_results else summary.recent_jobs),
            (
                "Vagas com score igual ou acima de 70%"
                if has_match_results
                else f"{summary.remote_jobs} com indicativo de trabalho remoto"
            ),
        ),
    ]
    for column, metric in zip(st.columns(4), metrics):
        with column:
            st.markdown(build_metric_card(*metric), unsafe_allow_html=True)


def render_sidebar_filters(jobs: list[Job], profile_active: bool, page_size_options: list[int]) -> SidebarInputs:
    all_locations = sorted({job.location for job in jobs if job.location})
    all_companies = sorted({job.company for job in jobs if job.company})
    all_tags = sorted({tag for job in jobs for tag in job.tags})

    with st.sidebar:
        st.markdown('<div class="sidebar-title">Filtros</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sidebar-copy">Busca, refinamento e ordenacao permanecem fixos na lateral para a navegacao ficar fluida e destacar o que tem mais sabor para o seu perfil.</div>',
            unsafe_allow_html=True,
        )
        search_value = st.text_input("Buscar", value="", placeholder="Titulo, empresa, local ou tag")
        sort_options = ["Mais recentes", "Empresa (A-Z)", "Local (A-Z)"]
        if profile_active:
            sort_options.insert(0, "Maior aderencia")
        sort_option = st.selectbox(
            "Ordenar por",
            sort_options,
            index=0,
            help="Ordene por aderencia para ver primeiro as vagas com mais sabor para o seu perfil.",
        )
        page_size = st.selectbox("Vagas por pagina", page_size_options, index=1)
        st.markdown("### Perfil")
        uploaded_resume = st.file_uploader("Curriculo em PDF", type=["pdf"], key="resume_uploader")
        analyze_clicked = st.button("Analisar curriculo", use_container_width=True, disabled=uploaded_resume is None)
        clear_clicked = st.button(
            "Limpar analise",
            use_container_width=True,
            disabled=not profile_active and uploaded_resume is None,
        )
        selected_locations = st.multiselect("Localizacoes", all_locations)
        selected_companies = st.multiselect("Empresas", all_companies)
        selected_tags = st.multiselect("Tags", all_tags)

    return SidebarInputs(
        search_value=search_value,
        selected_locations=selected_locations,
        selected_companies=selected_companies,
        selected_tags=selected_tags,
        sort_option=sort_option,
        page_size=page_size,
        uploaded_resume=uploaded_resume,
        analyze_clicked=analyze_clicked,
        clear_clicked=clear_clicked,
    )


def render_sidebar_feedback(
    uploaded_resume,
    current_resume_digest: str | None,
    analyzed_resume_digest: str | None,
    has_match_results: bool,
) -> None:
    with st.sidebar:
        if st.session_state.get("resume_error"):
            st.error(st.session_state["resume_error"])
        if uploaded_resume is None:
            st.caption("Envie um PDF para calcular aderencia e descobrir quais vagas tem mais sabor para o seu perfil.")
        elif current_resume_digest == analyzed_resume_digest and has_match_results:
            st.success("Curriculo analisado. A ordenacao por aderencia e a leitura de sabor estao disponiveis.")
        else:
            st.info("Curriculo carregado. Clique em analisar para atualizar aderencia e sabor.")


def render_results_bar(result_count: int, sort_option: str) -> None:
    st.markdown(
        f"""
        <div class="result-bar">
            <div class="result-count">
                <strong>{result_count}</strong> vagas correspondem aos filtros aplicados.
            </div>
            <span class="page-chip">{html.escape(sort_option)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
            Nenhuma vaga corresponde aos filtros atuais. Ajuste a busca ou remova algum recorte para ampliar o radar.
        </div>
        """,
        unsafe_allow_html=True,
    )


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
            "Ir para pagina",
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


def render_job_cards(jobs: list[Job], match_results: dict[str, MatchResult] | None) -> None:
    for job in jobs:
        st.html(build_job_card(job, match_results.get(job.url) if match_results else None))
