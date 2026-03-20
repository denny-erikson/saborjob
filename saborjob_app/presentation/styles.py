import streamlit as st


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --bg-start: #f4f8ff;
            --bg-end: #eef3ea;
            --surface: rgba(255, 255, 255, 0.78);
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

        html, body, [class*="css"] { font-family: "Manrope", "Segoe UI", sans-serif; }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(14, 165, 233, 0.16), transparent 28%),
                radial-gradient(circle at top right, rgba(16, 185, 129, 0.14), transparent 26%),
                linear-gradient(180deg, var(--bg-start) 0%, var(--bg-end) 100%);
            color: var(--text-main);
        }
        [data-testid="stAppViewContainer"] > .main { padding-top: 1.6rem; }
        [data-testid="stHeader"] { background: transparent; }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 250, 252, 0.92));
            border-right: 1px solid rgba(15, 23, 42, 0.08);
        }
        [data-testid="stSidebar"] .block-container { padding-top: 1rem; padding-bottom: 1.25rem; }
        .block-container { max-width: 1180px; padding-top: 0; padding-bottom: 2.5rem; }
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
        .hero-copy { max-width: 100ch; color: var(--text-soft); font-size: 0.9rem; line-height: 1.45; margin-bottom: 0; }
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
        .metric-label, .metric-helper { display: block; }
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
        .metric-helper { color: var(--text-soft); font-size: 0.84rem; line-height: 1.35; }
        .result-bar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 1rem 0 0.7rem;
        }
        .result-count { font-size: 1rem; color: var(--text-soft); }
        .result-count strong { color: var(--text-main); }
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
        .job-badges { display: flex; align-items: center; justify-content: flex-end; gap: 0.45rem; flex-wrap: wrap; }
        .job-card h3 { margin: 0.25rem 0 0; font-size: 1.12rem; line-height: 1.25; letter-spacing: -0.03em; color: var(--text-main); }
        .eyebrow { color: var(--accent-strong); font-size: 0.75rem; letter-spacing: 0.08em; text-transform: uppercase; font-weight: 800; }
        .status-pill, .tag-pill, .score-pill, .flavor-pill, .signal-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border-radius: var(--radius-sm);
            font-size: 0.82rem;
            font-weight: 700;
            line-height: 1;
        }
        .status-pill, .score-pill, .flavor-pill { white-space: nowrap; height: fit-content; padding: 0.55rem 0.85rem; }
        .status-pill { background: var(--accent-soft); color: var(--accent-strong); border: 1px solid rgba(15, 118, 110, 0.16); }
        .score-pill { background: rgba(15, 23, 42, 0.06); color: var(--text-main); border: 1px solid rgba(15, 23, 42, 0.08); }
        .flavor-pill { background: rgba(15, 118, 110, 0.10); color: var(--accent-strong); border: 1px solid rgba(15, 118, 110, 0.16); }
        .job-meta { display: flex; flex-wrap: wrap; gap: 0.55rem; color: var(--text-soft); margin-bottom: 0.85rem; }
        .job-meta span {
            padding: 0.48rem 0.75rem;
            border-radius: var(--radius-sm);
            background: rgba(248, 250, 252, 0.9);
            border: 1px solid var(--border);
        }
        .job-footer { display: flex; justify-content: space-between; gap: 1rem; align-items: center; flex-wrap: wrap; }
        .signal-row { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-bottom: 0.8rem; min-height: 1px; }
        .tag-row { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .tag-pill { padding: 0.5rem 0.72rem; background: rgba(15, 23, 42, 0.05); color: var(--text-soft); border: 1px solid rgba(15, 23, 42, 0.05); }
        .signal-pill {
            padding: 0.42rem 0.68rem;
            background: rgba(15, 118, 110, 0.08);
            color: var(--accent-strong);
            border: 1px solid rgba(15, 118, 110, 0.14);
            justify-content: flex-start;
        }
        .tag-pill.muted { color: var(--text-muted); }
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
        div[data-baseweb="tag"] { border-radius: 16px !important; }
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
        div.stButton > button[kind="secondary"] { background: rgba(255, 255, 255, 0.9); color: var(--text-main); border-color: var(--border); }
        .sidebar-title { font-size: 1rem; font-weight: 800; color: var(--text-main); margin-bottom: 0.2rem; }
        .sidebar-copy { color: var(--text-muted); font-size: 0.9rem; line-height: 1.45; margin-bottom: 0.8rem; }
        .profile-summary {
            padding: 0.95rem 1rem;
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.75);
            border: 1px solid rgba(15, 23, 42, 0.08);
            box-shadow: 0 8px 20px rgba(15, 23, 42, 0.04);
            margin: 0.2rem 0 0.9rem;
        }
        .profile-summary strong, .profile-summary span { display: block; }
        .profile-summary strong { color: var(--text-main); font-size: 0.96rem; margin-bottom: 0.2rem; }
        .profile-summary span { color: var(--text-soft); font-size: 0.88rem; line-height: 1.45; }
        .empty-state {
            padding: 2rem;
            text-align: center;
            border-radius: var(--radius-lg);
            background: rgba(255, 255, 255, 0.74);
            border: 1px dashed rgba(15, 23, 42, 0.16);
            color: var(--text-soft);
        }
        @media (max-width: 768px) {
            .hero-panel { padding: 0.95rem 1rem; }
            .job-card { padding: 1.1rem; }
            .result-bar { flex-direction: column; align-items: flex-start; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
