import os
from math import ceil

import streamlit as st

from saborjob_app.application.services.job_catalog import JobCatalogService
from saborjob_app.application.services.resume_matching import ResumeMatchingService
from saborjob_app.config import BRAND_NAME, DATA_FILE, EMBEDDING_MODEL_NAME, PAGE_SIZE_OPTIONS
from saborjob_app.infrastructure.json_job_repository import JsonJobRepository
from saborjob_app.infrastructure.local_resume_extractor import PyMuPDFResumeExtractor
from saborjob_app.infrastructure.sentence_transformer_encoder import SentenceTransformerEncoder
from saborjob_app.presentation.components import (
    render_empty_state,
    render_hero,
    render_job_cards,
    render_metrics,
    render_pagination,
    render_profile_summary,
    render_results_bar,
    render_sidebar_feedback,
    render_sidebar_filters,
)
from saborjob_app.presentation.state import clear_resume_analysis, get_resume_digest
from saborjob_app.presentation.styles import inject_styles


os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")


def sync_page_state(filter_signature: tuple, total_pages: int) -> int:
    previous_signature = st.session_state.get("filter_signature")
    if previous_signature != filter_signature:
        st.session_state.filter_signature = filter_signature
        st.session_state.page_number = 1

    current_page = int(st.session_state.get("page_number", 1))
    current_page = max(1, min(current_page, total_pages))
    st.session_state.page_number = current_page
    return current_page


def handle_resume_analysis(
    jobs,
    resume_bytes: bytes | None,
    current_resume_digest: str | None,
    extractor: PyMuPDFResumeExtractor,
    matching_service: ResumeMatchingService,
) -> None:
    if resume_bytes is None:
        return

    progress_placeholder = st.empty()
    status_placeholder = st.empty()

    try:
        progress_bar = progress_placeholder.progress(0, text="Preparando a analise local")
        status_box = status_placeholder.status("Processando curriculo", expanded=True)

        def update_progress(step: int, message: str) -> None:
            progress_bar.progress(step, text=message)
            status_box.write(message)

        update_progress(5, "Extraindo texto do PDF")
        resume_text = extractor.extract_text(resume_bytes)
        if not resume_text:
            raise RuntimeError("Nao foi possivel extrair texto do PDF enviado.")

        profile, match_results = matching_service.analyze_resume_match(
            jobs,
            resume_text,
            progress_callback=update_progress,
        )

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


def main() -> None:
    st.set_page_config(page_title=BRAND_NAME, page_icon=":briefcase:", layout="wide")

    inject_styles()

    repository = JsonJobRepository(DATA_FILE)
    extractor = PyMuPDFResumeExtractor()
    encoder = SentenceTransformerEncoder(EMBEDDING_MODEL_NAME)
    catalog_service = JobCatalogService()
    matching_service = ResumeMatchingService(encoder)

    jobs = repository.load_jobs()
    if not jobs:
        st.error(f"Arquivo nao encontrado: {DATA_FILE}")
        return

    profile = st.session_state.get("resume_profile")
    match_results = st.session_state.get("resume_match_results")
    sidebar_inputs = render_sidebar_filters(jobs, profile_active=bool(match_results), page_size_options=PAGE_SIZE_OPTIONS)

    current_resume_bytes = (
        sidebar_inputs.uploaded_resume.getvalue() if sidebar_inputs.uploaded_resume is not None else None
    )
    current_resume_digest = get_resume_digest(current_resume_bytes)
    analyzed_resume_digest = st.session_state.get("resume_analyzed_digest")

    if sidebar_inputs.clear_clicked:
        clear_resume_analysis()
        st.session_state["resume_uploader"] = None
        st.rerun()

    render_sidebar_feedback(
        sidebar_inputs.uploaded_resume,
        current_resume_digest,
        analyzed_resume_digest,
        bool(match_results),
    )

    render_hero(len(jobs))
    render_metrics(catalog_service.build_metrics(jobs, match_results), has_match_results=bool(match_results))

    if profile:
        render_profile_summary(profile)

    filtered_jobs = catalog_service.apply_filters(
        jobs,
        sidebar_inputs.search_value,
        sidebar_inputs.selected_locations,
        sidebar_inputs.selected_companies,
        sidebar_inputs.selected_tags,
    )
    filtered_jobs = catalog_service.sort_jobs(filtered_jobs, sidebar_inputs.sort_option, match_results)

    render_results_bar(len(filtered_jobs), sidebar_inputs.sort_option)

    if sidebar_inputs.analyze_clicked:
        handle_resume_analysis(
            jobs,
            current_resume_bytes,
            current_resume_digest,
            extractor,
            matching_service,
        )

    if not filtered_jobs:
        render_empty_state()
        return

    filter_signature = (
        sidebar_inputs.search_value.strip().lower(),
        tuple(sidebar_inputs.selected_locations),
        tuple(sidebar_inputs.selected_companies),
        tuple(sidebar_inputs.selected_tags),
        sidebar_inputs.sort_option,
        sidebar_inputs.page_size,
    )
    total_pages = max(1, ceil(len(filtered_jobs) / sidebar_inputs.page_size))
    page_number = sync_page_state(filter_signature, total_pages)
    page_jobs, total_pages = catalog_service.paginate(filtered_jobs, page_number, sidebar_inputs.page_size)

    render_job_cards(page_jobs, match_results)
    render_pagination(page_number, total_pages)
    st.caption(f"Fonte local: {DATA_FILE}")


if __name__ == "__main__":
    main()
