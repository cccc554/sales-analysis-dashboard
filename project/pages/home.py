"""Home dashboard page for the e-commerce retail analytics platform."""

from typing import Optional

import pandas as pd
import streamlit as st

from services import data_manager
from services.translator import t


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


HOME_CSS = """
<style>
.home-hero {
    border-radius: 16px;
    padding: 34px 36px;
    margin-bottom: 22px;
    background: linear-gradient(135deg, #2563EB, #3B82F6);
    box-shadow: 0 18px 46px rgba(37, 99, 235, 0.22);
    color: #FFFFFF;
}
.home-hero h1 {
    margin: 0 0 10px 0;
    color: #FFFFFF;
    font-size: clamp(2rem, 4vw, 3.35rem);
    font-weight: 700;
    letter-spacing: 0;
}
.home-hero p {
    margin: 0;
    color: #DBEAFE;
    font-size: 1.08rem;
}
.home-kpi-card {
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 20px 20px;
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
    transition: transform .16s ease, box-shadow .16s ease;
    min-height: 128px;
}
.home-kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 18px 42px rgba(15, 23, 42, 0.13);
}
.home-kpi-card .label {
    color: #64748B;
    font-size: 0.9rem;
    margin-bottom: 12px;
}
.home-kpi-card .value {
    color: #0F172A;
    font-size: 1.85rem;
    line-height: 1.1;
    font-weight: 700;
}
.home-section-title {
    margin: 28px 0 14px 0;
    color: #0F172A;
    font-size: 1.35rem;
    font-weight: 700;
}
.home-module-card {
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 18px 18px;
    background: #FFFFFF;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    min-height: 154px;
}
.home-module-card:hover {
    transform: scale(1.015);
    border-color: #93C5FD;
    box-shadow: 0 18px 42px rgba(37, 99, 235, 0.14);
}
.home-module-code {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 38px;
    height: 30px;
    padding: 0 10px;
    border-radius: 999px;
    background: #EFF6FF;
    color: #2563EB;
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 12px;
}
.home-module-card h3 {
    margin: 0 0 8px 0;
    color: #0F172A;
    font-size: 1.05rem;
    font-weight: 700;
}
.home-module-card p {
    margin: 0;
    color: #64748B;
    line-height: 1.55;
    font-size: 0.94rem;
}
.home-pill {
    display: inline-block;
    border: 1px solid #DBEAFE;
    border-radius: 999px;
    padding: 8px 13px;
    margin: 5px 7px 5px 0;
    background: #EFF6FF;
    color: #1D4ED8;
    font-size: 0.9rem;
}
</style>
"""


def _find_column(df: pd.DataFrame, candidates) -> Optional[str]:
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    for col in cols:
        col_low = col.lower()
        for cand in candidates:
            if cand.lower() in col_low:
                return col
    return None


def _format_money(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return t("not_available")


def _format_count(value) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return t("not_available")


def _dataset_kpis():
    cur = data_manager.get_current_dataset()
    if not cur or cur.get("df") is None or cur.get("df").empty:
        return {
            "loaded": False,
            "revenue": None,
            "orders": None,
            "customers": None,
            "products": None,
        }

    df = cur.get("df").copy()
    order_col = _find_column(df, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"])
    customer_col = _find_column(df, ["customerid", "customer id", "customer", "custid"])
    product_col = _find_column(df, ["description", "product", "productname", "product name", "stockcode", "sku", "item"])
    qty_col = _find_column(df, ["quantity", "qty", "units"])
    price_col = _find_column(df, ["unitprice", "unit price", "unit_price", "price"])
    revenue_col = _find_column(df, ["revenue", "sales", "total", "amount", "line_total", "amountpaid", "sales_amount"])

    if revenue_col:
        revenue = pd.to_numeric(df[revenue_col], errors="coerce").fillna(0).sum()
    elif qty_col and price_col:
        quantity = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
        price = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
        revenue = (quantity * price).sum()
    else:
        revenue = None

    return {
        "loaded": True,
        "revenue": revenue,
        "orders": df[order_col].nunique() if order_col else None,
        "customers": df[customer_col].nunique() if customer_col else None,
        "products": df[product_col].nunique() if product_col else None,
    }


def _kpi_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="home-kpi-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _module_card(code: str, title: str, desc: str):
    st.markdown(
        f"""
        <div class="home-module-card">
            <div class="home-module-code">{code}</div>
            <h3>{title}</h3>
            <p>{desc}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _set_current_page(page_key: str):
    if page_key not in PAGE_KEYS:
        page_key = "home"
    st.session_state.current_page = page_key
    st.session_state.page_index = PAGE_KEYS.index(page_key)


def _nav_button(label: str, page_key: str, key: str):
    if st.button(label, key=key, use_container_width=True, icon=":material/open_in_new:"):
        _set_current_page(page_key)
        st.rerun()


def _pill_list(items):
    html = "".join(f'<span class="home-pill">{item}</span>' for item in items)
    st.markdown(html, unsafe_allow_html=True)


def render():
    st.markdown(HOME_CSS, unsafe_allow_html=True)

    st.markdown(
        f"""
        <section class="home-hero">
            <h1>{t("home_dashboard_title")}</h1>
            <p>{t("home_dashboard_subtitle")}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    kpis = _dataset_kpis()
    if not kpis["loaded"]:
        st.info(t("home_dataset_missing_hint"))

    values = [
        _format_money(kpis["revenue"]) if kpis["revenue"] is not None else t("not_available"),
        _format_count(kpis["orders"]) if kpis["orders"] is not None else t("not_available"),
        _format_count(kpis["customers"]) if kpis["customers"] is not None else t("not_available"),
        _format_count(kpis["products"]) if kpis["products"] is not None else t("not_available"),
    ]
    labels = [
        t("home_kpi_total_sales"),
        t("home_kpi_total_orders"),
        t("home_kpi_customer_count"),
        t("home_kpi_product_count"),
    ]

    for col, label, value in zip(st.columns(4), labels, values):
        with col:
            _kpi_card(label, value)

    st.markdown(f'<div class="home-section-title">{t("home_feature_nav")}</div>', unsafe_allow_html=True)

    modules = [
        ("DATA", t("home_nav_dataset_title"), t("home_nav_dataset_desc"), "dataset_center", "home_nav_dataset"),
        ("SALE", t("home_nav_sales_title"), t("home_nav_sales_desc"), "sales_analysis", "home_nav_sales"),
        ("CUST", t("home_nav_customer_title"), t("home_nav_customer_desc"), "customer_analysis", "home_nav_customer"),
        ("PROD", t("home_nav_product_title"), t("home_nav_product_desc"), "product_analysis", "home_nav_product"),
        ("MKT", t("home_nav_basket_title"), t("home_nav_basket_desc"), "market_basket_analysis", "home_nav_basket"),
        ("FCST", t("home_nav_forecast_title"), t("home_nav_forecast_desc"), "forecast_analysis", "home_nav_forecast"),
        ("AI", t("home_nav_ai_title"), t("home_nav_ai_desc"), "ai_assistant", "home_nav_ai"),
        ("INFO", t("about"), t("about_summary"), "about", "home_nav_about"),
    ]

    cols = st.columns(4)
    for idx, (code, title, desc, page_key, key) in enumerate(modules):
        with cols[idx % 4]:
            _module_card(code, title, desc)
            _nav_button(t("home_enter_module"), page_key, key)

    left, right = st.columns(2)
    with left:
        st.markdown(f'<div class="home-section-title">{t("home_project_highlights")}</div>', unsafe_allow_html=True)
        _pill_list([
            t("home_highlight_rfm"),
            t("home_highlight_basket"),
            t("home_highlight_forecast"),
            t("home_highlight_ai"),
        ])

    with right:
        st.markdown(f'<div class="home-section-title">{t("home_dataset_info")}</div>', unsafe_allow_html=True)
        _module_card("DATA", t("home_dataset_info_title"), t("home_dataset_info_desc"))
