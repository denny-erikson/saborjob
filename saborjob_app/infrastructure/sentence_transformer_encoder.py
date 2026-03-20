from __future__ import annotations

import streamlit as st


@st.cache_resource(show_spinner=False)
def _load_model(model_name: str):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError(
            "Dependencia ausente para ranking local. Instale sentence-transformers."
        ) from exc

    return SentenceTransformer(model_name, device="cpu")


@st.cache_data(show_spinner=False)
def _encode_texts(model_name: str, texts: tuple[str, ...]) -> list[list[float]]:
    model = _load_model(model_name)
    embeddings = model.encode(list(texts), normalize_embeddings=True, device="cpu")
    return embeddings.tolist()


class SentenceTransformerEncoder:
    def __init__(self, model_name: str) -> None:
        self._model_name = model_name

    def encode(self, texts: list[str]) -> list[list[float]]:
        return _encode_texts(self._model_name, tuple(texts))
