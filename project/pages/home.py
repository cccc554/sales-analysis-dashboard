"""Home dashboard page for the e-commerce retail analytics platform."""

from html import escape
from typing import Optional

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except Exception:
    px = None

from config.theme import ACCENT, CHART_COLORS, PRIMARY, SUCCESS, apply_plotly_theme
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
.block-container {
    max-width: 1680px;
    padding-left: 1.5rem;
    padding-right: 1.5rem;
}
.home-hero {
    border-radius: 12px;
    padding: 34px 36px;
    margin-bottom: 22px;
    background: linear-gradient(135deg, #2E86AB, #A23B72);
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
    color: #E2E8F0;
    font-size: 1.08rem;
}
.home-kpi-card {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 22px 22px;
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
    transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    height: 132px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}
.home-kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 18px 42px rgba(15, 23, 42, 0.13);
    border-color: rgba(46, 134, 171, 0.32);
}
.home-kpi-card .label {
    color: #64748B;
    font-size: 0.9rem;
    margin-bottom: 14px;
    font-weight: 700;
}
.home-kpi-card .value {
    color: #1E293B;
    font-size: 2.35rem;
    line-height: 1.1;
    font-weight: 700;
}
.home-section-title {
    margin: 28px 0 14px 0;
    color: #1E293B;
    font-size: 1.35rem;
    font-weight: 700;
}
.home-module-card {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 18px;
    background: #FFFFFF;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
    transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
    min-height: 154px;
}
.home-module-card:hover {
    transform: scale(1.015);
    border-color: #2E86AB;
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
    background: #F5F7FA;
    color: #2E86AB;
    font-size: 0.78rem;
    font-weight: 700;
    margin-bottom: 12px;
}
.home-module-card h3 {
    margin: 0 0 8px 0;
    color: #1E293B;
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
    border: 1px solid #E2E8F0;
    border-radius: 999px;
    padding: 8px 13px;
    margin: 5px 7px 5px 0;
    background: #F5F7FA;
    color: #2E86AB;
    font-size: 0.9rem;
}
[data-testid="stPlotlyChart"] {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
    margin-bottom: 20px;
}
.home-summary-card {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 20px;
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
    min-height: 116px;
}
.home-summary-label {
    color: #64748B;
    font-size: 0.82rem;
    font-weight: 700;
    margin-bottom: 10px;
}
.home-summary-value {
    color: #1E293B;
    font-size: 1.08rem;
    line-height: 1.35;
    font-weight: 700;
}
</style>
"""


HOME_TEXT = {
    "zh": {
        "core_analytics": "核心分析图表",
        "sales_trend": "销售趋势",
        "top_products": "TOP10 产品",
        "customer_distribution": "客户分布",
        "country_sales_map": "销售国家分布",
        "no_chart_data": "暂无可用于该图表的数据。",
        "business_overview": "业务概览",
        "highest_sales_month": "销售额最高月份",
        "top_product": "TOP产品名称",
        "main_customer_country": "客户主要来源国家",
        "dataset_records": "当前数据集记录数",
        "records": "记录数",
    },
    "en": {
        "core_analytics": "Core Analytics",
        "sales_trend": "Sales Trend",
        "top_products": "Top 10 Products",
        "customer_distribution": "Customer Distribution",
        "country_sales_map": "Sales by Country",
        "no_chart_data": "No available data for this chart.",
        "business_overview": "Business Overview",
        "highest_sales_month": "Highest Sales Month",
        "top_product": "Top Product",
        "main_customer_country": "Main Customer Country",
        "dataset_records": "Dataset Records",
        "records": "Records",
    },
}


def _txt(key: str) -> str:
    language = st.session_state.get("language", "en")
    bundle = HOME_TEXT["zh"] if str(language).lower().startswith("zh") else HOME_TEXT["en"]
    return bundle.get(key, key)


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


def _build_revenue_column(df: pd.DataFrame, revenue_col, qty_col, price_col):
    if revenue_col:
        work = df.copy()
        work["_home_revenue"] = pd.to_numeric(work[revenue_col], errors="coerce").fillna(0)
        return work, "_home_revenue"
    if qty_col and price_col:
        work = df.copy()
        quantity = pd.to_numeric(work[qty_col], errors="coerce").fillna(0)
        price = pd.to_numeric(work[price_col], errors="coerce").fillna(0)
        work["_home_revenue"] = quantity * price
        return work, "_home_revenue"
    return df, None


def _strip_icon_prefix(text: str) -> str:
    cleaned = "".join(ch for ch in str(text) if ord(ch) < 0x1F300 and ord(ch) not in (0xFE0F, 0x200D))
    return cleaned.strip()


def _dataset_kpis():
    cur = data_manager.get_current_dataset()
    if not cur or cur.get("df") is None or cur.get("df").empty:
        return {
            "loaded": False,
            "df": None,
            "revenue": None,
            "orders": None,
            "customers": None,
            "products": None,
            "revenue_col": None,
            "order_col": None,
            "customer_col": None,
            "product_col": None,
            "country_col": None,
            "date_col": None,
        }

    df = cur.get("df").copy()
    order_col = _find_column(df, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"])
    customer_col = _find_column(df, ["customerid", "customer id", "customer", "custid"])
    product_col = _find_column(df, ["description", "product", "productname", "product name", "stockcode", "sku", "item"])
    country_col = _find_column(df, ["country", "country_name", "region", "market"])
    date_col = _find_column(df, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"])
    qty_col = _find_column(df, ["quantity", "qty", "units"])
    price_col = _find_column(df, ["unitprice", "unit price", "unit_price", "price"])
    revenue_col = _find_column(df, ["revenue", "sales", "total", "amount", "line_total", "amountpaid", "sales_amount"])
    df, rev_col = _build_revenue_column(df, revenue_col, qty_col, price_col)

    revenue = pd.to_numeric(df[rev_col], errors="coerce").fillna(0).sum() if rev_col else None

    return {
        "loaded": True,
        "df": df,
        "revenue": revenue,
        "orders": df[order_col].nunique() if order_col else None,
        "customers": df[customer_col].nunique() if customer_col else None,
        "products": df[product_col].nunique() if product_col else None,
        "revenue_col": rev_col,
        "order_col": order_col,
        "customer_col": customer_col,
        "product_col": product_col,
        "country_col": country_col,
        "date_col": date_col,
    }


def _kpi_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="home-kpi-card">
            <div class="label">{escape(label)}</div>
            <div class="value">{escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _module_card(code: str, title: str, desc: str):
    st.markdown(
        f"""
        <div class="home-module-card">
            <div class="home-module-code">{escape(code)}</div>
            <h3>{escape(_strip_icon_prefix(title))}</h3>
            <p>{escape(desc)}</p>
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


def _set_page_query_param(page_key: str):
    try:
        if hasattr(st, "query_params"):
            st.query_params["page"] = page_key
        elif hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params(page=page_key)
    except Exception:
        pass


def _safe_rerun():
    rerun = getattr(st, "rerun", None)
    if rerun is None:
        rerun = getattr(st, "experimental_rerun", None)
    if rerun is not None:
        rerun()


def _go_to_dataset_center():
    _set_current_page("dataset_center")
    _set_page_query_param("dataset_center")
    _safe_rerun()


def _render_missing_dataset_prompt():
    with st.container():
        prompt_col, button_col = st.columns([3, 1])
        with prompt_col:
            st.warning("⚠️ 当前首页没有数据，请先上传数据。")
        with button_col:
            if st.button("前往数据中心上传", key="home_go_dataset_center", use_container_width=True):
                _go_to_dataset_center()


def _pill_list(items):
    html = "".join(f'<span class="home-pill">{escape(item)}</span>' for item in items)
    st.markdown(html, unsafe_allow_html=True)


def _short_text(value, limit: int = 46) -> str:
    text = str(value)
    return text if len(text) <= limit else f"{text[:limit - 3]}..."


def _business_overview_items(kpis):
    df = kpis.get("df")
    if df is None or df.empty:
        unavailable = t("not_available")
        return [
            (_txt("highest_sales_month"), unavailable),
            (_txt("top_product"), unavailable),
            (_txt("main_customer_country"), unavailable),
            (_txt("dataset_records"), unavailable),
        ]

    date_col = kpis.get("date_col")
    revenue_col = kpis.get("revenue_col")
    product_col = kpis.get("product_col")
    country_col = kpis.get("country_col")
    customer_col = kpis.get("customer_col")
    unavailable = t("not_available")

    highest_month = unavailable
    if date_col and revenue_col:
        try:
            month_df = df[[date_col, revenue_col]].copy()
            month_df["_home_date"] = pd.to_datetime(month_df[date_col], errors="coerce")
            month_df = month_df.dropna(subset=["_home_date"])
            month_df["_home_month"] = month_df["_home_date"].dt.to_period("M").dt.to_timestamp()
            monthly = month_df.groupby("_home_month")[revenue_col].sum().sort_values(ascending=False)
            if not monthly.empty:
                highest_month = f"{monthly.index[0].strftime('%Y-%m')} / {_format_money(monthly.iloc[0])}"
        except Exception:
            highest_month = unavailable

    top_product = unavailable
    if product_col and revenue_col:
        try:
            products = df.groupby(product_col)[revenue_col].sum().sort_values(ascending=False)
            if not products.empty:
                top_product = _short_text(products.index[0])
        except Exception:
            top_product = unavailable

    main_country = unavailable
    if country_col:
        try:
            if customer_col:
                countries = df.groupby(country_col)[customer_col].nunique().sort_values(ascending=False)
            else:
                countries = df.groupby(country_col).size().sort_values(ascending=False)
            if not countries.empty:
                main_country = _short_text(countries.index[0], 34)
        except Exception:
            main_country = unavailable

    return [
        (_txt("highest_sales_month"), highest_month),
        (_txt("top_product"), top_product),
        (_txt("main_customer_country"), main_country),
        (_txt("dataset_records"), _format_count(len(df))),
    ]


def _summary_card(label: str, value: str):
    st.markdown(
        f"""
        <div class="home-summary-card">
            <div class="home-summary-label">{escape(label)}</div>
            <div class="home-summary-value">{escape(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_sales_trend(kpis):
    df = kpis.get("df")
    date_col = kpis.get("date_col")
    revenue_col = kpis.get("revenue_col")
    if df is None or df.empty or not date_col or not revenue_col:
        st.info(_txt("no_chart_data"))
        return

    try:
        work = df[[date_col, revenue_col]].copy()
        work["_home_date"] = pd.to_datetime(work[date_col], errors="coerce")
        work = work.dropna(subset=["_home_date"])
        if work.empty:
            st.info(_txt("no_chart_data"))
            return
        work["_home_month"] = work["_home_date"].dt.to_period("M").dt.to_timestamp()
        monthly = work.groupby("_home_month", as_index=False)[revenue_col].sum()
        if monthly.empty:
            st.info(_txt("no_chart_data"))
            return

        if px:
            fig = px.area(
                monthly,
                x="_home_month",
                y=revenue_col,
                title=f"<b>{_txt('sales_trend')}</b>",
                labels={"_home_month": t("label_month"), revenue_col: t("label_revenue")},
                color_discrete_sequence=[PRIMARY],
            )
            fig.update_traces(
                line=dict(color=PRIMARY, width=4),
                fillcolor="rgba(46,134,171,0.2)",
                hovertemplate="%{x|%Y-%m}<br>%{y:,.2f}<extra></extra>",
            )
            fig = apply_plotly_theme(fig, height=420)
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.line_chart(monthly.set_index("_home_month")[revenue_col])
    except Exception:
        st.info(_txt("no_chart_data"))


def _render_top_products(kpis):
    df = kpis.get("df")
    product_col = kpis.get("product_col")
    revenue_col = kpis.get("revenue_col")
    if df is None or df.empty or not product_col or not revenue_col:
        st.info(_txt("no_chart_data"))
        return

    try:
        products = (
            df.groupby(product_col, as_index=False)[revenue_col]
            .sum()
            .sort_values(by=revenue_col, ascending=False)
            .head(10)
        )
        if products.empty:
            st.info(_txt("no_chart_data"))
            return
        products["_home_product"] = products[product_col].astype(str).str.slice(0, 34)
        products = products.sort_values(by=revenue_col, ascending=True)

        if px:
            colors = [PRIMARY] * len(products)
            if colors:
                colors[-1] = ACCENT
            fig = px.bar(
                products,
                x=revenue_col,
                y="_home_product",
                orientation="h",
                title=f"<b>{_txt('top_products')}</b>",
                labels={"_home_product": t("label_product"), revenue_col: t("label_revenue")},
                color_discrete_sequence=[PRIMARY],
            )
            fig.update_traces(
                marker_color=colors,
                customdata=products[[product_col]].values,
                hovertemplate="%{customdata[0]}<br>%{x:,.2f}<extra></extra>",
            )
            fig = apply_plotly_theme(fig, height=420)
            fig.update_layout(bargap=0.28)
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(products.set_index("_home_product")[revenue_col])
    except Exception:
        st.info(_txt("no_chart_data"))


def _render_customer_distribution(kpis):
    df = kpis.get("df")
    customer_col = kpis.get("customer_col")
    country_col = kpis.get("country_col")
    if df is None or df.empty or not country_col:
        st.info(_txt("no_chart_data"))
        return

    try:
        if customer_col:
            grouped = df.groupby(country_col)[customer_col].nunique()
            value_label = t("home_kpi_customer_count")
        else:
            grouped = df.groupby(country_col).size()
            value_label = _txt("records")
        chart_df = (
            grouped.reset_index(name="value")
            .sort_values("value", ascending=False)
            .head(8)
        )
        if chart_df.empty:
            st.info(_txt("no_chart_data"))
            return

        if px:
            fig = px.pie(
                chart_df,
                names=country_col,
                values="value",
                title=f"<b>{_txt('customer_distribution')}</b>",
                hole=0.62,
                labels={country_col: t("label_country"), "value": value_label},
                color_discrete_sequence=CHART_COLORS,
            )
            fig.update_traces(
                textinfo="percent",
                textposition="inside",
                insidetextorientation="radial",
                hovertemplate="%{label}<br>%{value:,.0f}<br>%{percent}<extra></extra>",
            )
            fig = apply_plotly_theme(fig, height=420)
            fig.update_layout(legend=dict(orientation="v", y=0.5, x=1.02, yanchor="middle"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write(chart_df)
    except Exception:
        st.info(_txt("no_chart_data"))


def _render_country_sales_map(kpis):
    df = kpis.get("df")
    country_col = kpis.get("country_col")
    revenue_col = kpis.get("revenue_col")
    if df is None or df.empty or not country_col or not revenue_col:
        st.info(_txt("no_chart_data"))
        return

    try:
        country_df = (
            df.groupby(country_col, as_index=False)[revenue_col]
            .sum()
            .sort_values(revenue_col, ascending=False)
        )
        if country_df.empty:
            st.info(_txt("no_chart_data"))
            return

        if px:
            fig = px.choropleth(
                country_df,
                locations=country_col,
                locationmode="country names",
                color=revenue_col,
                hover_name=country_col,
                title=f"<b>{_txt('country_sales_map')}</b>",
                labels={country_col: t("label_country"), revenue_col: t("label_revenue")},
                color_continuous_scale=[PRIMARY, SUCCESS, ACCENT],
            )
            fig.update_traces(hovertemplate="%{hovertext}<br>%{z:,.2f}<extra></extra>")
            fig.update_geos(
                fitbounds="locations",
                visible=False,
                showcountries=True,
                countrycolor="#E2E8F0",
                coastlinecolor="#E2E8F0",
                projection_type="natural earth",
            )
            fig = apply_plotly_theme(fig, height=420)
            fig.update_layout(coloraxis_colorbar=dict(thickness=10, len=0.72))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.bar_chart(country_df.head(15).set_index(country_col)[revenue_col])
    except Exception:
        st.info(_txt("no_chart_data"))


def render():
    st.markdown(HOME_CSS, unsafe_allow_html=True)

    st.markdown(
        f"""
        <section class="home-hero">
            <h1>{escape(t("home_dashboard_title"))}</h1>
            <p>{escape(t("home_dashboard_subtitle"))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    kpis = _dataset_kpis()
    if not kpis["loaded"]:
        _render_missing_dataset_prompt()

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

    st.markdown(f'<div class="home-section-title">{escape(_txt("business_overview"))}</div>', unsafe_allow_html=True)
    for col, (label, value) in zip(st.columns(4), _business_overview_items(kpis)):
        with col:
            _summary_card(label, value)

    st.markdown(f'<div class="home-section-title">{escape(_txt("core_analytics"))}</div>', unsafe_allow_html=True)
    chart_left, chart_right = st.columns([0.7, 0.3])
    with chart_left:
        _render_sales_trend(kpis)
    with chart_right:
        _render_top_products(kpis)

    chart_left, chart_right = st.columns(2)
    with chart_left:
        _render_customer_distribution(kpis)
    with chart_right:
        _render_country_sales_map(kpis)

    st.markdown(f'<div class="home-section-title">{escape(t("home_feature_nav"))}</div>', unsafe_allow_html=True)

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
        st.markdown(f'<div class="home-section-title">{escape(t("home_project_highlights"))}</div>', unsafe_allow_html=True)
        _pill_list([
            t("home_highlight_rfm"),
            t("home_highlight_basket"),
            t("home_highlight_forecast"),
            t("home_highlight_ai"),
        ])

    with right:
        st.markdown(f'<div class="home-section-title">{escape(t("home_dataset_info"))}</div>', unsafe_allow_html=True)
        _module_card("DATA", t("home_dataset_info_title"), t("home_dataset_info_desc"))
