"""Product Analysis page.

Builds product-level KPIs, rankings, trends, contribution charts, and a
downloadable product summary table from the currently loaded dataset.
"""

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


TEXT = {
    "en": {
        "page_summary": "Analyze product performance, revenue concentration, and product-level trends.",
        "controls": "Product Controls",
        "top_n": "Top N",
        "date_range": "Date Range",
        "all_categories": "All Categories",
        "category": "Category",
        "overview": "Product Overview",
        "product_count": "Product Count",
        "total_quantity": "Total Quantity",
        "total_revenue": "Total Revenue",
        "average_revenue": "Average Revenue",
        "ranking": "Top Product Ranking",
        "top_revenue": "Top {n} Products by Revenue",
        "top_quantity": "Top {n} Products by Quantity",
        "trend": "Product Sales Trend Analysis",
        "select_product": "Select Product",
        "monthly_trend": "Monthly Sales Trend",
        "contribution": "Product Contribution Analysis",
        "treemap": "Product Revenue Contribution Treemap",
        "donut": "Product Revenue Share",
        "details": "Product Detail Table",
        "search": "Search product name",
        "download": "Download CSV",
        "product": "Product Name",
        "quantity": "Quantity",
        "revenue": "Revenue",
        "avg_price": "Average Price",
        "orders": "Orders",
        "revenue_share": "Revenue Share",
        "month": "Month",
        "other": "Other Products",
        "not_available": "N/A",
        "no_dataset": "No dataset loaded.",
        "plotly_missing": "Plotly is unavailable; charts cannot be rendered.",
        "missing_required": "Product analysis requires product, quantity, and unit price fields.",
        "missing_product": "Missing product field. Expected Description, Product, or ProductName.",
        "missing_quantity": "Missing quantity field. Expected Quantity.",
        "missing_price": "Missing unit price field. Expected UnitPrice or Price.",
        "empty_after_filter": "No product records match the current filters.",
        "no_date": "No date field was found; date filtering and monthly trend are unavailable.",
        "no_trend": "No valid monthly sales data for the selected product.",
        "no_positive_revenue": "No positive revenue data is available for contribution charts.",
    },
    "zh": {
        "page_summary": "分析产品绩效、收入集中度和单品销售趋势。",
        "controls": "产品分析控制",
        "top_n": "Top N",
        "date_range": "日期范围",
        "all_categories": "全部类别",
        "category": "产品类别",
        "overview": "产品总体概览",
        "product_count": "产品种类数",
        "total_quantity": "总销量",
        "total_revenue": "总销售额",
        "average_revenue": "平均产品销售额",
        "ranking": "Top产品排行榜",
        "top_revenue": "Top {n} 产品销售额排行榜",
        "top_quantity": "Top {n} 产品销量排行榜",
        "trend": "产品销售趋势分析",
        "select_product": "选择产品",
        "monthly_trend": "月度销售趋势",
        "contribution": "产品贡献度分析",
        "treemap": "产品销售贡献度 Treemap",
        "donut": "产品销售占比 Donut Chart",
        "details": "产品详细分析表",
        "search": "搜索产品名称",
        "download": "下载CSV",
        "product": "产品名称",
        "quantity": "销量",
        "revenue": "销售额",
        "avg_price": "平均价格",
        "orders": "订单数",
        "revenue_share": "销售占比",
        "month": "月份",
        "other": "其他产品",
        "not_available": "暂无",
        "no_dataset": "当前未加载任何数据集。",
        "plotly_missing": "Plotly 不可用，无法渲染图表。",
        "missing_required": "产品分析需要产品、销量和单价字段。",
        "missing_product": "缺少产品字段。需要 Description、Product 或 ProductName。",
        "missing_quantity": "缺少销量字段。需要 Quantity。",
        "missing_price": "缺少单价字段。需要 UnitPrice 或 Price。",
        "empty_after_filter": "当前筛选条件下没有可用产品记录。",
        "no_date": "未识别到日期字段，无法使用日期筛选和月度趋势。",
        "no_trend": "所选产品没有可用的月度销售趋势数据。",
        "no_positive_revenue": "没有可用于贡献度图表的正向销售额数据。",
    },
}


def _lang() -> str:
    lang = str(st.session_state.get("language", "en")).lower()
    return "zh" if lang.startswith("zh") else "en"


def _txt(key: str, **kwargs) -> str:
    value = TEXT.get(_lang(), TEXT["en"]).get(key, key)
    return value.format(**kwargs) if kwargs else value


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


def _format_number(value) -> str:
    try:
        return f"{float(value):,.0f}"
    except Exception:
        return _txt("not_available")


def _format_money(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return _txt("not_available")


def _clean_product_name(value) -> str:
    text = str(value).strip()
    return text if text and text.lower() != "nan" else ""


def _positive_chart_df(product_summary: pd.DataFrame, top_n: int) -> pd.DataFrame:
    chart_df = product_summary[product_summary["revenue"] > 0].copy()
    return chart_df.sort_values("revenue", ascending=False).head(top_n)


def _bar_chart(data: pd.DataFrame, x_col: str, title: str, x_label: str):
    if px is None:
        st.info(_txt("plotly_missing"))
        return

    chart_df = data.sort_values(x_col, ascending=True)
    fig = px.bar(
        chart_df,
        x=x_col,
        y="product_name",
        orientation="h",
        labels={"product_name": _txt("product"), x_col: x_label},
        title=title,
        custom_data=["product_name", "quantity", "revenue"],
    )
    fig.update_traces(
        hovertemplate=(
            f"{_txt('product')}: %{{customdata[0]}}<br>"
            f"{_txt('quantity')}: %{{customdata[1]:,.0f}}<br>"
            f"{_txt('revenue')}: %{{customdata[2]:,.2f}}<extra></extra>"
        )
    )
    fig.update_layout(height=430, margin=dict(t=55, l=10, r=20, b=20))
    st.plotly_chart(fig, use_container_width=True)


def _build_product_summary(df: pd.DataFrame, product_col: str, qty_col: str, price_col: str, order_col: Optional[str]) -> pd.DataFrame:
    work = df.copy()
    work["_product_name"] = work[product_col].map(_clean_product_name)
    work = work[work["_product_name"] != ""].copy()
    work["_quantity"] = pd.to_numeric(work[qty_col], errors="coerce").fillna(0)
    work["_unit_price"] = pd.to_numeric(work[price_col], errors="coerce").fillna(0)
    work["_revenue"] = work["_quantity"] * work["_unit_price"]

    if order_col:
        summary = (
            work.groupby("_product_name", dropna=False)
            .agg(
                quantity=("_quantity", "sum"),
                revenue=("_revenue", "sum"),
                avg_price=("_unit_price", "mean"),
                orders=(order_col, "nunique"),
            )
            .reset_index()
        )
    else:
        summary = (
            work.groupby("_product_name", dropna=False)
            .agg(
                quantity=("_quantity", "sum"),
                revenue=("_revenue", "sum"),
                avg_price=("_unit_price", "mean"),
                orders=("_product_name", "size"),
            )
            .reset_index()
        )

    summary = summary.rename(columns={"_product_name": "product_name"})
    total_revenue = float(summary["revenue"].sum()) if not summary.empty else 0
    summary["revenue_share"] = summary["revenue"] / total_revenue if total_revenue else 0
    return summary.sort_values("revenue", ascending=False)


def render():
    st.title(t("product_analysis"))
    st.write(_txt("page_summary"))

    cur = data_manager.get_current_dataset()
    if not cur:
        st.info(_txt("no_dataset"))
        return

    df = cur.get("df")
    if df is None or df.empty:
        st.info(_txt("no_dataset"))
        return

    df = df.copy()

    product_col = _find_column(df, ["description", "product", "productname", "product name", "item", "stockcode", "sku"])
    qty_col = _find_column(df, ["quantity", "qty", "units"])
    price_col = _find_column(df, ["unitprice", "unit price", "unit_price", "price"])
    order_col = _find_column(df, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"])
    date_col = _find_column(df, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"])
    category_col = _find_column(df, ["category", "product category", "product_category", "categoryname", "department", "class", "subcategory"])
    if category_col == product_col:
        category_col = None

    missing_messages = []
    if not product_col:
        missing_messages.append(_txt("missing_product"))
    if not qty_col:
        missing_messages.append(_txt("missing_quantity"))
    if not price_col:
        missing_messages.append(_txt("missing_price"))

    if missing_messages:
        st.warning(_txt("missing_required"))
        for message in missing_messages:
            st.info(message)
        return

    if date_col:
        df["_date"] = pd.to_datetime(df[date_col], errors="coerce")

    with st.sidebar.expander(_txt("controls"), expanded=True):
        top_n = st.selectbox(_txt("top_n"), [5, 10, 20], index=1, key="product_top_n")

        if date_col and df["_date"].notna().any():
            min_date = df["_date"].min().date()
            max_date = df["_date"].max().date()
            selected_dates = st.date_input(
                _txt("date_range"),
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="product_date_range",
            )
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                start_date, end_date = selected_dates
                df = df[(df["_date"].dt.date >= start_date) & (df["_date"].dt.date <= end_date)].copy()
        elif date_col:
            st.info(_txt("no_date"))

        if category_col:
            categories = sorted([str(v) for v in df[category_col].dropna().unique().tolist()])
            selected_category = st.selectbox(_txt("category"), [_txt("all_categories")] + categories, key="product_category")
            if selected_category != _txt("all_categories"):
                df = df[df[category_col].astype(str) == selected_category].copy()

    product_summary = _build_product_summary(df, product_col, qty_col, price_col, order_col)
    if product_summary.empty:
        st.info(_txt("empty_after_filter"))
        return

    total_products = int(product_summary["product_name"].nunique())
    total_quantity = float(product_summary["quantity"].sum())
    total_revenue = float(product_summary["revenue"].sum())
    avg_revenue = total_revenue / total_products if total_products else 0

    st.subheader(_txt("overview"))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(_txt("product_count"), f"{total_products:,}")
    k2.metric(_txt("total_quantity"), _format_number(total_quantity))
    k3.metric(_txt("total_revenue"), _format_money(total_revenue))
    k4.metric(_txt("average_revenue"), _format_money(avg_revenue))

    st.markdown("---")

    st.subheader(_txt("ranking"))
    left, right = st.columns(2)
    top_revenue = product_summary.sort_values("revenue", ascending=False).head(top_n)
    top_quantity = product_summary.sort_values("quantity", ascending=False).head(top_n)
    with left:
        _bar_chart(top_revenue, "revenue", _txt("top_revenue", n=top_n), _txt("revenue"))
    with right:
        _bar_chart(top_quantity, "quantity", _txt("top_quantity", n=top_n), _txt("quantity"))

    st.markdown("---")

    st.subheader(_txt("trend"))
    if date_col:
        products = product_summary["product_name"].tolist()
        selected_product = st.selectbox(_txt("select_product"), products, key="product_trend_select")
        trend_df = df.copy()
        trend_df["_product_name"] = trend_df[product_col].map(_clean_product_name)
        trend_df = trend_df[(trend_df["_product_name"] == selected_product) & trend_df["_date"].notna()].copy()

        if trend_df.empty:
            st.info(_txt("no_trend"))
        else:
            trend_df["_quantity"] = pd.to_numeric(trend_df[qty_col], errors="coerce").fillna(0)
            trend_df["_unit_price"] = pd.to_numeric(trend_df[price_col], errors="coerce").fillna(0)
            trend_df["_revenue"] = trend_df["_quantity"] * trend_df["_unit_price"]
            trend_df["month"] = trend_df["_date"].dt.to_period("M").dt.to_timestamp()
            monthly = trend_df.groupby("month", as_index=False)["_revenue"].sum()
            monthly["product_name"] = selected_product

            if px and not monthly.empty:
                fig_trend = px.line(
                    monthly,
                    x="month",
                    y="_revenue",
                    markers=True,
                    labels={"month": _txt("month"), "_revenue": _txt("revenue")},
                    title=f"{_txt('monthly_trend')}: {selected_product}",
                    custom_data=["product_name", "month", "_revenue"],
                )
                fig_trend.update_traces(
                    mode="lines+markers",
                    hovertemplate=(
                        f"{_txt('product')}: %{{customdata[0]}}<br>"
                        f"{_txt('month')}: %{{customdata[1]|%Y-%m}}<br>"
                        f"{_txt('revenue')}: %{{customdata[2]:,.2f}}<extra></extra>"
                    ),
                )
                fig_trend.update_layout(height=430, margin=dict(t=60, l=20, r=20, b=20))
                st.plotly_chart(fig_trend, use_container_width=True)
            elif not px:
                st.info(_txt("plotly_missing"))
            else:
                st.info(_txt("no_trend"))
    else:
        st.info(_txt("no_date"))

    st.markdown("---")

    st.subheader(_txt("contribution"))
    treemap_col, donut_col = st.columns(2)
    positive_df = _positive_chart_df(product_summary, top_n)
    if positive_df.empty:
        st.info(_txt("no_positive_revenue"))
    else:
        with treemap_col:
            if px:
                treemap_df = positive_df.copy()
                fig_tree = px.treemap(
                    treemap_df,
                    path=["product_name"],
                    values="revenue",
                    color="revenue",
                    color_continuous_scale="Blues",
                    title=_txt("treemap"),
                    labels={"product_name": _txt("product"), "revenue": _txt("revenue")},
                )
                fig_tree.update_traces(
                    texttemplate=(
                        f"<b>%{{label}}</b><br>"
                        f"{_txt('revenue')}: %{{value:,.2f}}<br>"
                        f"{_txt('revenue_share')}: %{{percentRoot:.1%}}"
                    ),
                    hovertemplate=(
                        f"{_txt('product')}: %{{label}}<br>"
                        f"{_txt('revenue')}: %{{value:,.2f}}<br>"
                        f"{_txt('revenue_share')}: %{{percentRoot:.1%}}<extra></extra>"
                    ),
                    textfont_size=15,
                )
                fig_tree.update_layout(height=520, margin=dict(t=55, l=10, r=10, b=10))
                st.plotly_chart(fig_tree, use_container_width=True)
            else:
                st.info(_txt("plotly_missing"))

        with donut_col:
            if px:
                top_share = positive_df.copy()
                other_revenue = float(product_summary[product_summary["revenue"] > 0]["revenue"].sum() - top_share["revenue"].sum())
                donut_df = top_share[["product_name", "revenue"]].copy()
                if other_revenue > 0:
                    donut_df = pd.concat(
                        [donut_df, pd.DataFrame([{"product_name": _txt("other"), "revenue": other_revenue}])],
                        ignore_index=True,
                    )
                donut_total = float(donut_df["revenue"].sum())
                donut_df["revenue_share"] = donut_df["revenue"] / donut_total if donut_total else 0

                fig_donut = px.pie(
                    donut_df,
                    names="product_name",
                    values="revenue",
                    hole=0.45,
                    title=_txt("donut"),
                )
                fig_donut.update_traces(
                    textinfo="percent+label",
                    hovertemplate=(
                        f"{_txt('product')}: %{{label}}<br>"
                        f"{_txt('revenue')}: %{{value:,.2f}}<br>"
                        f"{_txt('revenue_share')}: %{{percent}}<extra></extra>"
                    ),
                )
                fig_donut.update_layout(height=520, margin=dict(t=55, l=10, r=10, b=10))
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info(_txt("plotly_missing"))

    st.markdown("---")

    st.subheader(_txt("details"))
    search_text = st.text_input(_txt("search"), key="product_table_search")
    table_df = product_summary.copy()
    if search_text:
        table_df = table_df[table_df["product_name"].str.contains(search_text, case=False, na=False)]

    display_source = table_df.copy()
    display_source["revenue_share"] = display_source["revenue_share"] * 100
    display_df = display_source.rename(
        columns={
            "product_name": _txt("product"),
            "quantity": _txt("quantity"),
            "revenue": _txt("revenue"),
            "avg_price": _txt("avg_price"),
            "orders": _txt("orders"),
            "revenue_share": _txt("revenue_share"),
        }
    )[
        [_txt("product"), _txt("quantity"), _txt("revenue"), _txt("avg_price"), _txt("orders"), _txt("revenue_share")]
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        height=430,
        column_config={
            _txt("quantity"): st.column_config.NumberColumn(format="%.0f"),
            _txt("revenue"): st.column_config.NumberColumn(format="%.2f"),
            _txt("avg_price"): st.column_config.NumberColumn(format="%.2f"),
            _txt("orders"): st.column_config.NumberColumn(format="%d"),
            _txt("revenue_share"): st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        _txt("download"),
        data=csv_data,
        file_name="product_analysis.csv",
        mime="text/csv",
    )

    insight_items = [
        f"{_txt('product_count')}: {total_products:,}",
        f"{_txt('total_quantity')}: {_format_number(total_quantity)}",
        f"{_txt('total_revenue')}: {_format_money(total_revenue)}",
        f"{_txt('average_revenue')}: {_format_money(avg_revenue)}",
    ]
    try:
        top_product = product_summary.sort_values("revenue", ascending=False).head(1)
        if not top_product.empty:
            row = top_product.iloc[0]
            insight_items.append(
                f"{_txt('top_revenue', n=1)}: {row['product_name']} ({_format_money(row['revenue'])})"
            )
    except Exception:
        pass
    render_ai_insights("product_analysis", t("product_analysis"), insight_items)
