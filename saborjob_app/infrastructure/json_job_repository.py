from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from saborjob_app.domain.models import Job


@st.cache_data(show_spinner=False)
def _load_jobs_from_path(data_file: str) -> list[Job]:
    file_path = Path(data_file)
    if not file_path.exists():
        return []

    with file_path.open("r", encoding="utf-8") as file:
        payload = json.load(file)

    return [
        Job(
            title=item.get("title") or "Titulo indisponivel",
            company=item.get("company"),
            location=item.get("location"),
            url=item.get("url") or "",
            posted_at=item.get("posted_at"),
            tags=item.get("tags") or [],
            source=item.get("source") or "solides",
        )
        for item in payload
    ]


class JsonJobRepository:
    def __init__(self, data_file: Path) -> None:
        self._data_file = data_file

    def load_jobs(self) -> list[Job]:
        return _load_jobs_from_path(str(self._data_file))
