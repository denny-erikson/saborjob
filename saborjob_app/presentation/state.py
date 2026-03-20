from __future__ import annotations

import hashlib

import streamlit as st


def get_resume_digest(pdf_bytes: bytes | None) -> str | None:
    if pdf_bytes is None:
        return None
    return hashlib.sha256(pdf_bytes).hexdigest()


def clear_resume_analysis() -> None:
    st.session_state["resume_profile"] = None
    st.session_state["resume_match_results"] = None
    st.session_state["resume_analyzed_digest"] = None
    st.session_state["resume_error"] = None
