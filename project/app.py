"""Application entrypoint for the Streamlit retail BI dashboard."""

import importlib

import streamlit as st

from config.theme import get_global_css
from config.settings import load_settings
from services.translator import Translator, t


GLOBAL_CSS = """
<style>
:root {
    --bi-primary: #2E86AB;
    --bi-primary-2: #A23B72;
    --bi-success: #2C8C5A;
    --bi-warning: #D95B5B;
    --bi-danger: #D95B5B;
    --bi-bg: #F5F7FA;
    --bi-card: #FFFFFF;
    --bi-border: #E2E8F0;
    --bi-text: #1E293B;
    --bi-muted: #64748B;
    --bi-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
}
[data-testid="stAppViewContainer"] {
    background: var(--bi-bg);
}
[data-testid="stSidebarNav"] {
    display: none;
}
[data-testid="stSidebar"] {
    background: #1E293B;
}
[data-testid="stSidebar"] * {
    color: #E2E8F0;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #E2E8F0;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1480px;
}
h1, h2, h3 {
    color: var(--bi-text);
    font-weight: 700 !important;
    letter-spacing: 0;
}
p, label, span, div {
    font-weight: 400;
}
.bi-sidebar-logo {
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 16px;
    padding: 18px 16px;
    margin: 0 0 18px 0;
    background: linear-gradient(135deg, #2E86AB, #2E86AB);
    box-shadow: 0 14px 32px rgba(37, 99, 235, 0.22);
}
.bi-sidebar-logo .mark {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.16);
    color: #FFFFFF;
    font-weight: 700;
    margin-bottom: 10px;
}
.bi-sidebar-logo .title {
    color: #FFFFFF;
    font-size: 1.02rem;
    font-weight: 700;
    line-height: 1.35;
}
.bi-sidebar-logo .subtitle {
    color: #E2E8F0;
    font-size: 0.82rem;
    margin-top: 4px;
}
.bi-nav-group {
    margin: 18px 0 8px 0;
    color: #2E86AB;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
[data-testid="stSidebar"] div.stButton > button {
    border-radius: 12px;
    border: 1px solid rgba(148, 163, 184, 0.16);
    background: rgba(15, 23, 42, 0.28);
    color: #E2E8F0;
    min-height: 42px;
    justify-content: flex-start;
    transition: all .16s ease;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    border-color: rgba(147, 197, 253, 0.7);
    background: rgba(37, 99, 235, 0.22);
}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2E86AB, #A23B72);
    color: #FFFFFF;
    border-color: rgba(255, 255, 255, 0.16);
}
div[data-testid="stMetric"] {
    background: var(--bi-card);
    border: 1px solid var(--bi-border);
    border-radius: 16px;
    padding: 18px 18px;
    box-shadow: var(--bi-shadow);
    transition: transform .16s ease, box-shadow .16s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 38px rgba(15, 23, 42, 0.12);
}
div[data-testid="stMetricLabel"] {
    color: var(--bi-muted);
}
div[data-testid="stMetricValue"] {
    color: var(--bi-text);
    font-weight: 700;
}
div.stButton > button {
    border-radius: 12px;
    border-color: var(--bi-border);
}
div.stButton > button[kind="primary"] {
    background: #2E86AB;
    border-color: #2E86AB;
    color: #FFFFFF !important;
}
div.stButton > button[kind="secondary"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    color: #1E293B;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #2E86AB;
    color: #2E86AB;
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
    border-radius: 16px;
    overflow: hidden;
}
</style>
"""


PAGE_KEYS = [
    "home",
    "dataset_center",
    "sales_analysis",
    "customer_analysis",
    "product_analysis",
    "market_basket_analysis",
    "forecast_analysis",
    "ai_assistant",
    "about",
]


TRANSLATE_KEYS = {
    "home": "home_title",
    "dataset_center": "dataset_center",
    "sales_analysis": "sales_analysis",
    "customer_analysis": "customer_analysis",
    "product_analysis": "product_analysis",
    "market_basket_analysis": "market_basket_analysis",
    "forecast_analysis": "forecast_analysis",
    "ai_assistant": "ai_assistant",
    "about": "about",
}


NAV_GROUPS = [
    ("nav_group_data", ["dataset_center"]),
    (
        "nav_group_analytics",
        [
            "sales_analysis",
            "customer_analysis",
            "product_analysis",
            "market_basket_analysis",
            "forecast_analysis",
        ],
    ),
    ("nav_group_ai", ["ai_assistant"]),
    ("nav_group_system", ["about"]),
]


NAV_ICONS = {
    "home": ":material/dashboard:",
    "dataset_center": ":material/database:",
    "sales_analysis": ":material/monitoring:",
    "customer_analysis": ":material/groups:",
    "product_analysis": ":material/category:",
    "market_basket_analysis": ":material/hub:",
    "forecast_analysis": ":material/trending_up:",
    "ai_assistant": ":material/smart_toy:",
    "about": ":material/info:",
}


def set_current_page(page_key: str) -> None:
    if page_key not in PAGE_KEYS:
        page_key = "home"
    st.session_state.current_page = page_key
    st.session_state.page_index = PAGE_KEYS.index(page_key)


def get_current_page() -> str:
    current_page = st.session_state.get("current_page")
    if current_page not in PAGE_KEYS:
        try:
            page_index = int(st.session_state.get("page_index", 0))
        except Exception:
            page_index = 0
        if page_index < 0 or page_index >= len(PAGE_KEYS):
            page_index = 0
        current_page = PAGE_KEYS[page_index]

    set_current_page(current_page)
    return current_page


def render_language_switch(translator):
    current_language = st.session_state.get("language", "en")
    cols = st.columns([6, 0.85, 0.85])
    with cols[1]:
        if st.button(
            "EN",
            key="language_en",
            type="primary" if current_language == "en" else "secondary",
            use_container_width=True,
        ):
            if current_language != "en":
                translator.set_language("en")
                st.session_state.language = "en"
                st.rerun()
    with cols[2]:
        if st.button(
            "中文",
            key="language_zh",
            type="primary" if current_language == "zh" else "secondary",
            use_container_width=True,
        ):
            if current_language != "zh":
                translator.set_language("zh")
                st.session_state.language = "zh"
                st.rerun()


def _nav_group_label(group_key: str) -> str:
    label = t(group_key)
    if label == group_key:
        normalized_key = str(group_key).lower()
        label = t(normalized_key)
    return label


def render_sidebar(current_page: str) -> str:
    st.sidebar.markdown(
        """
        <div class="bi-sidebar-logo">
            <div class="mark">BI</div>
            <div class="title">Retail Intelligence</div>
            <div class="subtitle">Enterprise Dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button(
        t("home_title"),
        key="nav_home",
        icon=NAV_ICONS["home"],
        type="primary" if current_page == "home" else "secondary",
        disabled=current_page == "home",
        use_container_width=True,
    ):
        set_current_page("home")
        st.rerun()

    for group_key, keys in NAV_GROUPS:
        st.sidebar.markdown(f'<div class="bi-nav-group">{_nav_group_label(group_key)}</div>', unsafe_allow_html=True)
        for page_key in keys:
            is_active = current_page == page_key
            if st.sidebar.button(
                t(TRANSLATE_KEYS[page_key]),
                key=f"nav_{page_key}",
                icon=NAV_ICONS[page_key],
                type="primary" if is_active else "secondary",
                disabled=is_active,
                use_container_width=True,
            ):
                set_current_page(page_key)
                st.rerun()

    return current_page


def main():
    settings = load_settings()
    if "language" not in st.session_state:
        st.session_state.language = settings.get("default_language", "en")

    translator = Translator()
    st.set_page_config(page_title=t("platform_title"), layout="wide")
    st.markdown(get_global_css(), unsafe_allow_html=True)
    render_language_switch(translator)

    current_page = get_current_page()
    current_page = render_sidebar(current_page)
    set_current_page(current_page)
    module_name = f"pages.{current_page}"

    try:
        module = importlib.import_module(module_name)
        if hasattr(module, "render"):
            module.render()
        else:
            st.error(t("page_not_implemented"))
    except Exception as e:
        st.error(f"{t('page_load_error')}: {e}")


if __name__ == "__main__":
    main()
