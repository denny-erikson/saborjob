from __future__ import annotations

import streamlit as st


@st.cache_data(show_spinner=False)
def _extract_text_from_pdf(pdf_bytes: bytes) -> str:
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


class PyMuPDFResumeExtractor:
    def extract_text(self, pdf_bytes: bytes) -> str:
        return _extract_text_from_pdf(pdf_bytes)
