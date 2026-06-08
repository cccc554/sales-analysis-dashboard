"""About page for the e-commerce retail analytics platform."""

import streamlit as st

from services.translator import t


ABOUT_CSS = """
<style>
.about-hero {
    border-radius: 16px;
    padding: 30px 32px;
    background: linear-gradient(135deg, #2E86AB, #2E86AB);
    color: #FFFFFF;
    box-shadow: 0 18px 46px rgba(37, 99, 235, 0.22);
    margin-bottom: 22px;
}
.about-hero h1 {
    margin: 0 0 10px 0;
    color: #FFFFFF;
    font-weight: 700;
}
.about-hero p {
    margin: 0;
    color: #E2E8F0;
}
.about-card {
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 16px;
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
}
.about-card h3 {
    margin: 0 0 12px 0;
    color: #1E293B;
    font-weight: 700;
}
.about-card p {
    color: #64748B;
    line-height: 1.62;
}
.about-pill {
    display: inline-block;
    border: 1px solid #E2E8F0;
    border-radius: 999px;
    padding: 8px 13px;
    margin: 5px 7px 5px 0;
    background: #F5F7FA;
    color: #2E86AB;
    font-size: 0.9rem;
}
.arch-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
}
.arch-node {
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    background: #F5F7FA;
    padding: 16px;
    min-height: 104px;
}
.arch-node .step {
    color: #2E86AB;
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 8px;
}
.arch-node .name {
    color: #1E293B;
    font-weight: 700;
}
.arch-node .desc {
    color: #64748B;
    font-size: 0.88rem;
    margin-top: 6px;
}
</style>
"""


def _card(title: str, body: str):
    st.markdown(
        f"""
        <div class="about-card">
            <h3>{title}</h3>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _pill_list(items):
    return "".join(f'<span class="about-pill">{item}</span>' for item in items)


def render():
    st.markdown(ABOUT_CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <section class="about-hero">
            <h1>{t("about_page_title")}</h1>
            <p>{t("about_page_caption")}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    _card(
        t("about_system_intro_title"),
        t("about_system_intro_body"),
    )

    left, right = st.columns([1.1, 1])
    with left:
        _card(
            t("about_tech_stack_title"),
            _pill_list([
                t("about_tech_python"),
                t("about_tech_streamlit"),
                t("about_tech_pandas"),
                t("about_tech_plotly"),
                t("about_tech_sklearn"),
            ]),
        )
        _card(
            t("about_features_title"),
            _pill_list([
                t("about_feature_sales"),
                t("about_feature_rfm"),
                t("about_feature_product"),
                t("about_feature_basket"),
                t("about_feature_forecast"),
                t("about_feature_ai"),
            ]),
        )

    with right:
        _card(
            t("about_dataset_title"),
            t("about_dataset_body"),
        )
        _card(
            t("about_author_title"),
            t("about_author_body"),
        )

    st.markdown(
        f"""
        <div class="about-card">
            <h3>{t("about_architecture_title")}</h3>
            <div class="arch-grid">
                <div class="arch-node">
                    <div class="step">01</div>
                    <div class="name">{t("about_arch_data_title")}</div>
                    <div class="desc">{t("about_arch_data_desc")}</div>
                </div>
                <div class="arch-node">
                    <div class="step">02</div>
                    <div class="name">{t("about_arch_engine_title")}</div>
                    <div class="desc">{t("about_arch_engine_desc")}</div>
                </div>
                <div class="arch-node">
                    <div class="step">03</div>
                    <div class="name">{t("about_arch_visual_title")}</div>
                    <div class="desc">{t("about_arch_visual_desc")}</div>
                </div>
                <div class="arch-node">
                    <div class="step">04</div>
                    <div class="name">{t("about_arch_decision_title")}</div>
                    <div class="desc">{t("about_arch_decision_desc")}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
