import json
from math import ceil
from pathlib import Path

import streamlit as st


DATA_FILE = Path("data/solides_jobs.json")


def load_jobs() -> list[dict]:
    if not DATA_FILE.exists():
        st.error(f"Arquivo não encontrado: {DATA_FILE}")
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_posted_at(value: str) -> str:
    return value.replace("Postada", "Postada").strip()


def apply_filters(jobs, search_value, selected_locations, selected_companies, selected_tags):
    if search_value:
        search_value_lower = search_value.lower()
        jobs = [
            job
            for job in jobs
            if search_value_lower in (job.get("title", "") or "").lower()
            or search_value_lower in (job.get("company", "") or "").lower()
            or search_value_lower in (job.get("location", "") or "").lower()
        ]

    if selected_locations:
        jobs = [job for job in jobs if job.get("location") in selected_locations]

    if selected_companies:
        jobs = [job for job in jobs if job.get("company") in selected_companies]

    if selected_tags:
        jobs = [job for job in jobs if any(t in selected_tags for t in job.get("tags", []))]

    return jobs


def draw_job_card(job: dict):
    title = job.get("title", "-")
    company = job.get("company", "-")
    location = job.get("location", "-")
    posted_at = normalize_posted_at(job.get("posted_at", "-"))
    tags = job.get("tags", [])
    url = job.get("url", "#")

    with st.container():
        col1, col2 = st.columns([4, 1])

        with col1:
            st.subheader(title)
            st.write(f"🏢 **Empresa:** {company}")
            st.write(f"📍 **Local:** {location}")
            st.write(f"🕒 **Publicado:** {posted_at}")

            if tags:
                tag_badges = " ".join([f"✅ {tag}" for tag in tags])
                st.write(f"🏷️ **Tags:** {tag_badges}")

        with col2:
            st.markdown(f"[🔗 Abrir vaga]({url})", unsafe_allow_html=True)

        st.divider()


def main():
    st.set_page_config(
        page_title="Job Radar Solides",
        page_icon=":briefcase:",
        layout="wide",
    )

    st.title("🚀 Job Radar Solides")
    st.markdown("**Interface limpa e moderna para explorar vagas de Full Stack.**")

    jobs = load_jobs()
    if not jobs:
        return

    all_locations = sorted({job.get("location") for job in jobs if job.get("location")})
    all_companies = sorted({job.get("company") for job in jobs if job.get("company")})
    all_tags = sorted({tag for job in jobs for tag in (job.get("tags") or [])})

    with st.sidebar:
        st.header("Filtros")
        q = st.text_input("🔍 Buscar por título, empresa ou local", value="")
        selected_locations = st.multiselect("📍 Localizações", all_locations, default=None)
        selected_companies = st.multiselect("🏢 Empresas", all_companies, default=None)
        selected_tags = st.multiselect("🏷️ Tags", all_tags, default=None)
        page_size = st.slider("Tamanho da página", min_value=3, max_value=20, value=6, step=1)


    filtered_jobs = apply_filters(jobs, q, selected_locations, selected_companies, selected_tags)

    st.markdown(
        f"✅ **Foram encontradas {len(filtered_jobs)} vagas com base nos filtros.**"
    )

    total_pages = max(1, ceil(len(filtered_jobs) / page_size))
    page_number = st.sidebar.number_input(
        "Página",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
    )

    start = (page_number - 1) * page_size
    end = start + page_size
    page_jobs = filtered_jobs[start:end]

    for job in page_jobs:
        draw_job_card(job)

    st.markdown(f"**Página {page_number} de {total_pages}**")


if __name__ == "__main__":
    main()
