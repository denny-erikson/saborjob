from __future__ import annotations

from typing import Protocol

from saborjob_app.domain.models import Job


class JobRepository(Protocol):
    def load_jobs(self) -> list[Job]:
        """Return available jobs."""


class ResumeTextExtractor(Protocol):
    def extract_text(self, pdf_bytes: bytes) -> str:
        """Extract raw text from a resume PDF."""


class TextEncoder(Protocol):
    def encode(self, texts: list[str]) -> list[list[float]]:
        """Encode texts into normalized vectors."""
