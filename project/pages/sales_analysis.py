"""Sales analysis page with enterprise BI dashboard styling."""

from html import escape
from typing import Optional

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
except Exception:
    px = None

from services import data_manager
from services.ai_insights import render_ai_insights
from services.translator import t


PRIMARY = "#2563EB"
SECONDARY = "#3B82F6"
SUCCESS = "#10B981"
WARNING = "#F59E0B"
DANGER = "#EF4444"
BORDER = "#E5E7EB"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"


SALES_CSS = """
<style>
.sales-hero {
    background: linear-gradient(135deg, #2563EB, #3B82F6);
    border-radius: 16px;
    padding: 28px 32px;
    color: #FFFFFF;
    box-shadow: 0 18px 45px rgba(37, 99, 235, 0.22);
    margin-bottom: 24px;
}
.sales-eyebrow {
    margin: 0 0 8px 0;
    font-size: 13px;
    letter-spacing: 0;
    text-transform: uppercase;
    font-weight: 700;
    opacity: 0.86;
}
.sales-hero h1 {
    margin: 0;
    font-size: 32px;
    line-height: 1.15;
    font-weight: 700;
}
.sales-hero p {
    margin: 10px 0 0 0;
    color: rgba(255, 255, 255, 0.86);
    font-size: 15px;
}
.sales-kpi-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
    transition: transform 160ms ease, box-shadow 160ms ease, border-color 160ms ease;
    min-height: 118px;
}
.sales-kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 18px 42px rgba(37, 99, 235, 0.16);
    border-color: rgba(37, 99, 235, 0.34);
}
.sales-kpi-label {
    color: #64748B;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 12px;
}
.sales-kpi-value {
    color: #0F172A;
    font-size: 28px;
    font-weight: 700;
    line-height: 1.1;
}
.sales-kpi-accent {
    width: 42px;
    height: 4px;
    border-radius: 999px;
    margin-top: 16px;
}
.chart-panel {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 18px 18px 8px 18px;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
    margin-top: 16px;
}
</style>
"""


def _find_column(df: pd.DataFrame, candidates) -> Optional[str]:
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        cand_low = cand.lower()
        if cand_low in lower_map:
            return lower_map[cand_low]
    for col in cols:
        col_low = col.lower()
        for cand in candidates:
            if cand.lower() in col_low:
                return col
    return None


def _format_metric(value, decimals: int = 2) -> str:
    if value is None:
        return t("not_available")
    try:
        number = float(value)
    except Exception:
        return t("not_available")
    if decimals == 0:
        return f"{number:,.0f}"
    return f"{number:,.{decimals}f}"


def _render_kpi(label: str, value: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="sales-kpi-card">
            <div class="sales-kpi-label">{escape(label)}</div>
            <div class="sales-kpi-value">{escape(value)}</div>
            <div class="sales-kpi-accent" style="background:{accent};"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _style_figure(fig, height: int = 380, hovermode: str = "closest"):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(t=48, l=24, r=20, b=30),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color=TEXT_DARK, family="Arial", size=12),
        title=dict(font=dict(size=16, color=TEXT_DARK), x=0),
        hovermode=hovermode,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=TEXT_MUTED),
        ),
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(226, 232, 240, 0.9)",
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(226, 232, 240, 0.9)",
        zeroline=False,
        linecolor=BORDER,
        tickfont=dict(color=TEXT_MUTED),
        title_font=dict(color=TEXT_MUTED),
    )
    return fig


def _build_revenue_column(df: pd.DataFrame, revenue_col, price_col, qty_col):
    if revenue_col:
        return df, revenue_col
    if price_col and qty_col:
        try:
            work = df.copy()
            quantity = pd.to_numeric(work[qty_col], errors="coerce").fillna(0)
            price = pd.to_numeric(work[price_col], errors="coerce").fillna(0)
            work["_revenue_calc"] = quantity * price
            return work, "_revenue_calc"
        except Exception:
            return df, None
    return df, None


def render():
    st.markdown(SALES_CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <section class="sales-hero">
            <div class="sales-eyebrow">Sales Performance</div>
            <h1>{escape(t("sales_analysis"))}</h1>
            <p>{escape(t("sales_analysis_summary"))}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    cur = data_manager.get_current_dataset()
    if not cur:
        st.info(t("no_dataset_loaded"))
        return

    df = cur.get("df")
    if df is None or df.empty:
        st.info(t("no_dataset_loaded"))
        return

    price_col = _find_column(df, ["unitprice", "unit price", "price", "unit_price"])
    qty_col = _find_column(df, ["quantity", "qty", "amount", "units"])
    revenue_col = _find_column(df, ["revenue", "total", "sales", "amount", "line_total", "amountpaid", "sales_amount"])
    order_col = _find_column(df, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"])
    customer_col = _find_column(df, ["customerid", "customer id", "customer", "custid"])
    date_col = _find_column(df, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"])
    product_col = _find_column(df, ["description", "product", "productname", "stockcode", "item"])
    country_col = _find_column(df, ["country", "country_name", "region"])

    df, rev_col = _build_revenue_column(df, revenue_col, price_col, qty_col)

    def safe_sum(col):
        try:
            return float(pd.to_numeric(df[col], errors="coerce").sum())
        except Exception:
            return None

    revenue_total = safe_sum(rev_col) if rev_col else None
    orders_count = None
    if order_col:
        try:
            orders_count = int(df[order_col].nunique())
        except Exception:
            orders_count = None
    customers_count = None
    if customer_col:
        try:
            customers_count = int(df[customer_col].nunique())
        except Exception:
            customers_count = None
    aov = revenue_total / orders_count if revenue_total is not None and orders_count else None

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        _render_kpi(t("kpi_revenue"), _format_metric(revenue_total), PRIMARY)
    with k2:
        _render_kpi(t("kpi_orders"), _format_metric(orders_count, 0), SECONDARY)
    with k3:
        _render_kpi(t("kpi_customers"), _format_metric(customers_count, 0), SUCCESS)
    with k4:
        _render_kpi(t("kpi_aov"), _format_metric(aov), WARNING)

    left, right = st.columns(2)
    with left:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        if date_col and rev_col:
            try:
                work = df.copy()
                work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
                df_month = work.dropna(subset=[date_col]).copy()
                if df_month.empty:
                    st.info(t("no_valid_dates_to_show_trend"))
                else:
                    df_month["ym"] = df_month[date_col].dt.to_period("M").dt.to_timestamp()
                    monthly = df_month.groupby("ym", as_index=False)[rev_col].sum()
                    if monthly.empty:
                        st.info(t("no_sales_data_for_trend"))
                    elif px:
                        fig = px.line(
                            monthly,
                            x="ym",
                            y=rev_col,
                            title=t("monthly_sales_trend"),
                            labels={"ym": t("label_month"), rev_col: t("label_revenue")},
                            markers=True,
                            color_discrete_sequence=[PRIMARY],
                        )
                        fig.update_traces(line=dict(width=3), marker=dict(size=7), hovertemplate="%{x|%Y-%m}<br>%{y:,.2f}<extra></extra>")
                        st.plotly_chart(_style_figure(fig, hovermode="x unified"), use_container_width=True)
                    else:
                        st.line_chart(monthly.set_index("ym")[rev_col])
            except Exception:
                st.warning(t("unable_compute_monthly_trend"))
        else:
            st.info(t("monthly_trend_requires_fields"))
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        if country_col and rev_col:
            try:
                country_df = (
                    df.groupby(country_col, as_index=False)[rev_col]
                    .sum()
                    .sort_values(by=rev_col, ascending=False)
                    .head(20)
                )
                if country_df.empty:
                    st.info(t("no_country_sales_data"))
                elif px:
                    fig2 = px.bar(
                        country_df,
                        x=country_col,
                        y=rev_col,
                        title=t("sales_by_country"),
                        labels={country_col: t("label_country"), rev_col: t("label_revenue")},
                        color_discrete_sequence=[SECONDARY],
                    )
                    fig2.update_traces(hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>")
                    st.plotly_chart(_style_figure(fig2), use_container_width=True)
                else:
                    st.bar_chart(country_df.set_index(country_col)[rev_col])
            except Exception:
                st.warning(t("unable_compute_sales_by_country"))
        else:
            st.info(t("country_revenue_field_missing"))
        st.markdown("</div>", unsafe_allow_html=True)

    main_col, side_col = st.columns([1.35, 1])
    with main_col:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        if product_col and rev_col:
            try:
                prod_df = (
                    df.groupby(product_col, as_index=False)[rev_col]
                    .sum()
                    .sort_values(by=rev_col, ascending=False)
                    .head(10)
                )
                if prod_df.empty:
                    st.info(t("no_product_sales_data"))
                elif px:
                    prod_df = prod_df.sort_values(by=rev_col, ascending=True)
                    fig_top = px.bar(
                        prod_df,
                        x=rev_col,
                        y=product_col,
                        orientation="h",
                        title=t("top_10_products"),
                        labels={product_col: t("label_product"), rev_col: t("label_revenue")},
                        color_discrete_sequence=[PRIMARY],
                    )
                    fig_top.update_traces(hovertemplate="%{y}<br>%{x:,.2f}<extra></extra>")
                    st.plotly_chart(_style_figure(fig_top, height=430), use_container_width=True)
                else:
                    st.table(prod_df)
            except Exception:
                st.warning(t("unable_compute_top_products"))
        else:
            st.info(t("product_revenue_field_missing"))
        st.markdown("</div>", unsafe_allow_html=True)

    with side_col:
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        try:
            pie_df = None
            names_col = None
            name_label = None
            if product_col and rev_col:
                pie_df = (
                    df.groupby(product_col, as_index=False)[rev_col]
                    .sum()
                    .sort_values(by=rev_col, ascending=False)
                    .head(10)
                )
                names_col = product_col
                name_label = t("label_product")
            elif country_col and rev_col:
                pie_df = (
                    df.groupby(country_col, as_index=False)[rev_col]
                    .sum()
                    .sort_values(by=rev_col, ascending=False)
                    .head(10)
                )
                names_col = country_col
                name_label = t("label_country")

            if pie_df is None:
                st.info(t("not_enough_fields_revenue_share"))
            elif pie_df.empty:
                st.info(t("no_data_for_revenue_share"))
            elif px:
                fig3 = px.pie(
                    pie_df,
                    names=names_col,
                    values=rev_col,
                    title=t("revenue_share"),
                    hole=0.48,
                    labels={names_col: name_label, rev_col: t("label_revenue")},
                    color_discrete_sequence=[PRIMARY, SECONDARY, SUCCESS, WARNING, DANGER, "#6366F1", "#14B8A6", "#84CC16", "#F97316", "#64748B"],
                )
                fig3.update_traces(textinfo="percent+label", hovertemplate="%{label}<br>%{value:,.2f}<br>%{percent}<extra></extra>")
                st.plotly_chart(_style_figure(fig3, height=430), use_container_width=True)
            else:
                st.write(pie_df)
        except Exception:
            st.warning(t("unable_render_revenue_share_chart"))
        st.markdown("</div>", unsafe_allow_html=True)

    insight_items = [
        f"{t('kpi_revenue')}: {_format_metric(revenue_total)}",
        f"{t('kpi_orders')}: {_format_metric(orders_count, 0)}",
        f"{t('kpi_customers')}: {_format_metric(customers_count, 0)}",
        f"{t('kpi_aov')}: {_format_metric(aov)}",
    ]
    try:
        if product_col and rev_col:
            top_product = (
                df.groupby(product_col)[rev_col]
                .sum()
                .sort_values(ascending=False)
                .head(1)
            )
            if not top_product.empty:
                insight_items.append(f"{t('top_10_products')}: {top_product.index[0]} ({_format_metric(top_product.iloc[0])})")
        if country_col and rev_col:
            top_country = (
                df.groupby(country_col)[rev_col]
                .sum()
                .sort_values(ascending=False)
                .head(1)
            )
            if not top_country.empty:
                insight_items.append(f"{t('sales_by_country')}: {top_country.index[0]} ({_format_metric(top_country.iloc[0])})")
    except Exception:
        pass
    render_ai_insights("sales_analysis", t("sales_analysis"), insight_items)
