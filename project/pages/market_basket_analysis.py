"""Market Basket Analysis page.

Builds basket KPIs, frequent item combinations, a rule network, contribution
charts, and a downloadable association table from the current dataset.
"""

from collections import Counter, defaultdict
from itertools import combinations
from math import cos, pi, sin
from typing import Optional

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
except Exception:
    px = None
    go = None

from services import data_manager
from services.ai_insights import render_ai_insights
from services.translator import t
from config.theme import CARD, CHART_GRADIENT, TEXT, apply_plotly_theme


MAX_RULE_ITEMS = 300
MAX_ITEMS_PER_ORDER_FOR_RULES = 50


TEXT = {
    "en": {
        "page_summary": "Discover frequently purchased product combinations and association rules.",
        "controls": "Basket Controls",
        "top_n": "Top N",
        "date_range": "Date Range",
        "category": "Product Category",
        "all_categories": "All Categories",
        "overview": "Basket Overview",
        "total_orders": "Total Orders",
        "total_products": "Total Products",
        "avg_items": "Avg Items per Order",
        "avg_order_value": "Avg Order Value",
        "frequent_combos": "Frequent Product Combinations",
        "top_combos": "Top {n} Product Combinations",
        "network": "Product Association Rule Graph",
        "contribution": "Top Association Combination Contribution",
        "details": "Basket Analysis Table",
        "search": "Search product combination",
        "download": "Download CSV",
        "combo": "Product Combination",
        "combo_short": "Combination",
        "count": "Occurrences",
        "support": "Support",
        "confidence": "Confidence",
        "lift": "Lift",
        "revenue": "Revenue",
        "share": "Share",
        "product": "Product",
        "orders": "Orders",
        "not_available": "N/A",
        "other": "Other Combinations",
        "plotly_missing": "Plotly is unavailable; charts cannot be rendered.",
        "no_dataset": "No dataset loaded.",
        "missing_required": "Market basket analysis requires product and order fields.",
        "missing_product": "Missing product field. Expected Description, Product, or ProductName.",
        "missing_order": "Missing order field. Expected InvoiceNo.",
        "empty_after_filter": "No basket records match the current filters.",
        "no_rules": "No product combinations were found. Orders need at least two distinct products.",
        "no_date": "No valid date field was found; date filtering is unavailable.",
        "revenue_unavailable": "Revenue fields were not found; contribution charts use order counts.",
    },
    "zh": {
        "page_summary": "发现高频同购商品组合和商品关联规则。",
        "controls": "篮子分析控制",
        "top_n": "Top N",
        "date_range": "日期范围",
        "category": "产品类别",
        "all_categories": "全部类别",
        "overview": "篮子分析概览",
        "total_orders": "总订单数",
        "total_products": "总商品数",
        "avg_items": "平均每单商品数",
        "avg_order_value": "平均订单金额",
        "frequent_combos": "高频商品组合",
        "top_combos": "Top {n} 商品组合",
        "network": "商品关联规则图",
        "contribution": "TOP 关联组合贡献",
        "details": "数据表与下载",
        "search": "搜索商品组合",
        "download": "下载CSV",
        "combo": "商品组合",
        "combo_short": "组合商品",
        "count": "出现次数",
        "support": "支持度",
        "confidence": "置信度",
        "lift": "提升度",
        "revenue": "销售额",
        "share": "占比",
        "product": "商品",
        "orders": "订单数",
        "not_available": "暂无",
        "other": "其他组合",
        "plotly_missing": "Plotly 不可用，无法渲染图表。",
        "no_dataset": "当前未加载任何数据集。",
        "missing_required": "篮子分析需要商品字段和订单字段。",
        "missing_product": "缺少商品字段。需要 Description、Product 或 ProductName。",
        "missing_order": "缺少订单字段。需要 InvoiceNo。",
        "empty_after_filter": "当前筛选条件下没有可用篮子记录。",
        "no_rules": "没有找到商品组合。订单中至少需要包含两个不同商品。",
        "no_date": "未识别到有效日期字段，无法使用日期筛选。",
        "revenue_unavailable": "未识别到销售额字段，贡献图将使用订单数量。",
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


def _clean_text(value) -> str:
    text = str(value).strip()
    return text if text and text.lower() != "nan" else ""


def _shorten(value: str, max_len: int = 36) -> str:
    value = str(value)
    return value if len(value) <= max_len else value[: max_len - 1] + "..."


def _combo_name(items) -> str:
    return " + ".join(str(item) for item in items)


def _combo_display(items, max_items: int = 3) -> str:
    shown = [_shorten(item) for item in list(items)[:max_items]]
    suffix = "" if len(items) <= max_items else " + ..."
    return " + ".join(shown) + suffix


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


def _prepare_work_df(df: pd.DataFrame, product_col: str, order_col: str, qty_col: Optional[str], price_col: Optional[str]):
    work = df.copy()
    work["_order_id"] = work[order_col].map(_clean_text)
    work["_product_name"] = work[product_col].map(_clean_text)
    work = work[(work["_order_id"] != "") & (work["_product_name"] != "")].copy()

    revenue_available = bool(qty_col and price_col)
    if revenue_available:
        quantity = pd.to_numeric(work[qty_col], errors="coerce").fillna(0)
        price = pd.to_numeric(work[price_col], errors="coerce").fillna(0)
        work["_line_revenue"] = quantity * price
    else:
        work["_line_revenue"] = 0.0

    return work, revenue_available


def _compute_rules(work: pd.DataFrame, revenue_available: bool):
    total_orders = int(work["_order_id"].nunique())
    if total_orders == 0:
        return pd.DataFrame(), Counter(), pd.Series(dtype=float), 0.0, 0.0

    item_counter = Counter()
    pair_counter = Counter()
    pair_revenue = defaultdict(float)
    order_item_counts = []
    order_revenue = work.groupby("_order_id")["_line_revenue"].sum()
    order_groups = []

    for _, group in work.groupby("_order_id", sort=False):
        items = sorted(set(group["_product_name"].tolist()))
        if not items:
            continue

        order_item_counts.append(len(items))
        revenue_by_item = group.groupby("_product_name")["_line_revenue"].sum().to_dict()
        order_groups.append((items, revenue_by_item))

        for item in items:
            item_counter[item] += 1

    eligible_items = {item for item, _ in item_counter.most_common(MAX_RULE_ITEMS)}

    for items, revenue_by_item in order_groups:
        filtered_items = [item for item in items if item in eligible_items]
        if len(filtered_items) > MAX_ITEMS_PER_ORDER_FOR_RULES:
            filtered_items = sorted(
                filtered_items,
                key=lambda item: (item_counter[item], revenue_by_item.get(item, 0)),
                reverse=True,
            )[:MAX_ITEMS_PER_ORDER_FOR_RULES]
            filtered_items = sorted(filtered_items)

        if len(filtered_items) < 2:
            continue

        for pair in combinations(filtered_items, 2):
            pair_counter[pair] += 1
            pair_revenue[pair] += float(revenue_by_item.get(pair[0], 0) + revenue_by_item.get(pair[1], 0))

    positive_pair_revenue_total = sum(max(value, 0) for value in pair_revenue.values())
    records = []
    for pair, count in pair_counter.items():
        item_a, item_b = pair
        support_a = item_counter[item_a] / total_orders
        support_b = item_counter[item_b] / total_orders
        support = count / total_orders
        confidence_ab = count / item_counter[item_a] if item_counter[item_a] else 0
        confidence_ba = count / item_counter[item_b] if item_counter[item_b] else 0
        confidence = max(confidence_ab, confidence_ba)
        lift = support / (support_a * support_b) if support_a and support_b else 0
        revenue = float(pair_revenue[pair])
        share = (max(revenue, 0) / positive_pair_revenue_total) if revenue_available and positive_pair_revenue_total else support

        records.append(
            {
                "item_a": item_a,
                "item_b": item_b,
                "combo": _combo_name(pair),
                "combo_short": _combo_display(pair),
                "count": int(count),
                "support": float(support),
                "confidence": float(confidence),
                "lift": float(lift),
                "revenue": revenue,
                "share": float(share),
            }
        )

    rules_df = pd.DataFrame(records)
    if not rules_df.empty:
        rules_df = rules_df.sort_values(["count", "lift", "confidence"], ascending=False).reset_index(drop=True)

    avg_items = float(pd.Series(order_item_counts).mean()) if order_item_counts else 0.0
    avg_order_value = float(order_revenue.sum() / total_orders) if revenue_available and total_orders else 0.0
    return rules_df, item_counter, order_revenue, avg_items, avg_order_value


def _render_top_combos(rules_df: pd.DataFrame, top_n: int):
    if px is None:
        st.info(_txt("plotly_missing"))
        return

    chart_df = rules_df.head(top_n).sort_values("count", ascending=True)
    fig = px.bar(
        chart_df,
        x="count",
        y="combo_short",
        orientation="h",
        color="support",
        color_continuous_scale=CHART_GRADIENT,
        labels={"count": _txt("count"), "combo_short": _txt("combo"), "support": _txt("support")},
        title=_txt("top_combos", n=top_n),
        custom_data=["combo", "count", "support"],
    )
    fig.update_traces(
        hovertemplate=(
            f"{_txt('combo')}: %{{customdata[0]}}<br>"
            f"{_txt('count')}: %{{customdata[1]:,.0f}}<br>"
            f"{_txt('share')}: %{{customdata[2]:.1%}}<extra></extra>"
        )
    )
    fig = apply_plotly_theme(fig, height=450)
    fig.update_layout(margin=dict(t=55, l=10, r=20, b=20), coloraxis_showscale=True)
    st.plotly_chart(fig, use_container_width=True)


def _render_network(rules_df: pd.DataFrame, item_counter: Counter, total_orders: int, top_n: int):
    if go is None:
        st.info(_txt("plotly_missing"))
        return

    graph_rules = rules_df.sort_values(["lift", "confidence", "count"], ascending=False).head(top_n).copy()
    if graph_rules.empty:
        st.info(_txt("no_rules"))
        return

    nodes = sorted(set(graph_rules["item_a"]).union(set(graph_rules["item_b"])))
    positions = {}
    for idx, node in enumerate(nodes):
        angle = 2 * pi * idx / max(len(nodes), 1)
        positions[node] = (cos(angle), sin(angle))

    max_lift = max(float(graph_rules["lift"].max()), 1.0)
    traces = []
    for _, row in graph_rules.iterrows():
        x0, y0 = positions[row["item_a"]]
        x1, y1 = positions[row["item_b"]]
        width = 1.5 + min(7.5, (row["lift"] / max_lift) * 7.5)
        hover_text = (
            f"{_txt('combo')}: {row['combo']}<br>"
            f"{_txt('support')}: {row['support']:.1%}<br>"
            f"{_txt('confidence')}: {row['confidence']:.1%}<br>"
            f"{_txt('lift')}: {row['lift']:.2f}"
        )
        traces.append(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(width=width, color="rgba(46, 134, 171, 0.48)"),
                hoverinfo="text",
                text=hover_text,
                showlegend=False,
            )
        )

    max_count = max(item_counter.values()) if item_counter else 1
    node_x = [positions[node][0] for node in nodes]
    node_y = [positions[node][1] for node in nodes]
    node_sizes = [18 + 42 * (item_counter[node] / max_count) for node in nodes]
    node_hover = [
        f"{_txt('product')}: {node}<br>{_txt('orders')}: {item_counter[node]:,.0f}<br>{_txt('support')}: {item_counter[node] / total_orders:.1%}"
        for node in nodes
    ]
    node_labels = [_shorten(node, 18) for node in nodes]

    traces.append(
        go.Scatter(
            x=node_x,
            y=node_y,
            mode="markers+text",
            text=node_labels,
            textposition="top center",
            hoverinfo="text",
            hovertext=node_hover,
            marker=dict(
                size=node_sizes,
                color=[item_counter[node] for node in nodes],
                colorscale=CHART_GRADIENT,
                line=dict(width=1.5, color=CARD),
                showscale=True,
                colorbar=dict(title=_txt("orders")),
            ),
            name=_txt("product"),
            showlegend=False,
        )
    )

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=_txt("network"),
        height=560,
        margin=dict(t=60, l=20, r=20, b=20),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(color=TEXT, family="Arial", size=12),
        hovermode="closest",
    )
    fig = apply_plotly_theme(fig, height=560)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    st.plotly_chart(fig, use_container_width=True)


def _render_contribution(rules_df: pd.DataFrame, top_n: int, revenue_available: bool):
    if px is None:
        st.info(_txt("plotly_missing"))
        return

    use_revenue = revenue_available and (pd.to_numeric(rules_df["revenue"], errors="coerce").fillna(0) > 0).any()
    value_col = "item_sales" if use_revenue else "count"
    metric_label = _txt("revenue") if use_revenue else _txt("count")

    chart_df = rules_df.copy()
    chart_df["item_sales"] = pd.to_numeric(chart_df["revenue"], errors="coerce").fillna(0).clip(lower=0)
    chart_df = chart_df[chart_df[value_col] > 0].sort_values(value_col, ascending=False).head(top_n).copy()
    if chart_df.empty:
        st.info(_txt("no_rules"))
        return

    total_sales = float(chart_df["item_sales"].sum()) if use_revenue else 0.0

    def _sales_share_pct(item_sales) -> float:
        if total_sales <= 0:
            return 0.0
        share_pct = float(item_sales) / total_sales * 100
        if pd.isna(share_pct):
            return 0.0
        return min(max(share_pct, 0.0), 100.0)

    chart_df["sales_share"] = chart_df["item_sales"].map(_sales_share_pct)
    chart_df["combo_treemap"] = chart_df["combo"].map(lambda value: _shorten(value, 25))
    chart_df = chart_df.reset_index(drop=True)
    chart_df["treemap_id"] = chart_df.index.map(lambda index: f"combo_{index}")
    chart_df["treemap_parent"] = ""

    st.write(chart_df[["combo", "item_sales", "sales_share"]].head(10))
    print("MARKET_BASKET_FILE =", __file__)
    print("TREEMAP sales_share describe:", chart_df["sales_share"].describe())
    print("TREEMAP sales_share nan_count =", int(chart_df["sales_share"].isna().sum()))
    print("TREEMAP sales_share gt100_count =", int((chart_df["sales_share"] > 100).sum()))

    st.markdown(
        """
        <style>
        .basket-treemap-panel {
            background: #FFFFFF;
            border-radius: 16px;
            overflow: hidden;
            padding: 8px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
        }
        </style>
        <div class="basket-treemap-panel">
        """,
        unsafe_allow_html=True,
    )

    fig = px.treemap(
        chart_df,
        names="combo_treemap",
        ids="treemap_id",
        parents="treemap_parent",
        values=value_col,
        color=value_col,
        color_continuous_scale=CHART_GRADIENT,
        title=_txt("contribution"),
        custom_data=["combo", "count", "item_sales", "lift", "sales_share"],
        labels={"combo_treemap": _txt("combo"), value_col: metric_label},
    )
    metric_template = (
        f"{_txt('revenue')}: %{{customdata[2]:,.2f}}"
        if use_revenue
        else f"{_txt('count')}: %{{customdata[1]:,.0f}}"
    )
    fig.update_traces(
        texttemplate=(
            f"<b>%{{label}}</b><br>"
            f"{metric_template}<br>"
            f"{_txt('share')}: %{{customdata[4]:.1f}}%"
        ),
        hovertemplate=(
            f"{_txt('combo')}: %{{customdata[0]}}<br>"
            f"{_txt('revenue')}: %{{customdata[2]:,.2f}}<br>"
            f"{_txt('count')}: %{{customdata[1]:,.0f}}<br>"
            f"{_txt('lift')}: %{{customdata[3]:.2f}}<br>"
            f"{_txt('share')}: %{{customdata[4]:.1f}}%<extra></extra>"
        ),
        textfont_size=15,
        textfont_color=TEXT,
        marker=dict(line=dict(width=1, color=CARD)),
        root_color=CARD,
    )
    fig = apply_plotly_theme(fig, height=700)
    fig.update_layout(
        margin=dict(t=58, l=8, r=8, b=8),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(size=15, color=TEXT, family="Arial"),
        title=dict(font=dict(size=16, color=TEXT)),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render():
    st.title(t("market_basket_analysis"))
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
    order_col = _find_column(df, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"])
    qty_col = _find_column(df, ["quantity", "qty", "units"])
    price_col = _find_column(df, ["unitprice", "unit price", "unit_price", "price"])
    date_col = _find_column(df, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"])
    category_col = _find_column(df, ["category", "product category", "product_category", "categoryname", "department", "class", "subcategory"])
    if category_col == product_col:
        category_col = None

    missing_messages = []
    if not product_col:
        missing_messages.append(_txt("missing_product"))
    if not order_col:
        missing_messages.append(_txt("missing_order"))

    if missing_messages:
        st.warning(_txt("missing_required"))
        for message in missing_messages:
            st.info(message)
        return

    if date_col:
        df["_date"] = pd.to_datetime(df[date_col], errors="coerce")

    with st.sidebar.expander(_txt("controls"), expanded=True):
        top_n = st.selectbox(_txt("top_n"), [5, 10, 12, 20], index=2, key="basket_top_n")

        if date_col and df["_date"].notna().any():
            min_date = df["_date"].min().date()
            max_date = df["_date"].max().date()
            selected_dates = st.date_input(
                _txt("date_range"),
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="basket_date_range",
            )
            if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
                start_date, end_date = selected_dates
                df = df[(df["_date"].dt.date >= start_date) & (df["_date"].dt.date <= end_date)].copy()
        elif date_col:
            st.info(_txt("no_date"))

        if category_col:
            categories = sorted([str(v) for v in df[category_col].dropna().unique().tolist()])
            selected_category = st.selectbox(_txt("category"), [_txt("all_categories")] + categories, key="basket_category")
            if selected_category != _txt("all_categories"):
                df = df[df[category_col].astype(str) == selected_category].copy()

    work, revenue_available = _prepare_work_df(df, product_col, order_col, qty_col, price_col)
    if work.empty:
        st.info(_txt("empty_after_filter"))
        return

    rules_df, item_counter, order_revenue, avg_items, avg_order_value = _compute_rules(work, revenue_available)
    total_orders = int(work["_order_id"].nunique())
    total_products = int(work["_product_name"].nunique())

    st.subheader(_txt("overview"))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(_txt("total_orders"), f"{total_orders:,}")
    k2.metric(_txt("total_products"), f"{total_products:,}")
    k3.metric(_txt("avg_items"), f"{avg_items:,.2f}")
    k4.metric(_txt("avg_order_value"), _format_money(avg_order_value) if revenue_available else _txt("not_available"))

    if not revenue_available:
        st.info(_txt("revenue_unavailable"))

    if rules_df.empty:
        st.info(_txt("no_rules"))
        return

    st.markdown("---")

    st.subheader(_txt("frequent_combos"))
    _render_top_combos(rules_df, top_n)

    st.markdown("---")

    st.subheader(_txt("network"))
    _render_network(rules_df, item_counter, total_orders, top_n)

    st.markdown("---")

    st.subheader(_txt("contribution"))
    _render_contribution(rules_df, top_n, revenue_available)

    st.markdown("---")

    st.subheader(_txt("details"))
    search_text = st.text_input(_txt("search"), key="basket_table_search")
    table_df = rules_df.copy()
    if search_text:
        table_df = table_df[table_df["combo"].str.contains(search_text, case=False, na=False)]

    display_source = table_df.copy()
    display_source["support"] = display_source["support"] * 100
    display_source["confidence"] = display_source["confidence"] * 100
    display_source["share"] = display_source["share"] * 100

    display_df = display_source.rename(
        columns={
            "combo": _txt("combo"),
            "count": _txt("count"),
            "support": _txt("support"),
            "confidence": _txt("confidence"),
            "lift": _txt("lift"),
            "revenue": _txt("revenue"),
            "share": _txt("share"),
        }
    )[
        [_txt("combo"), _txt("count"), _txt("support"), _txt("confidence"), _txt("lift"), _txt("revenue"), _txt("share")]
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        height=460,
        column_config={
            _txt("count"): st.column_config.NumberColumn(format="%d"),
            _txt("support"): st.column_config.NumberColumn(format="%.2f%%"),
            _txt("confidence"): st.column_config.NumberColumn(format="%.2f%%"),
            _txt("lift"): st.column_config.NumberColumn(format="%.2f"),
            _txt("revenue"): st.column_config.NumberColumn(format="%.2f"),
            _txt("share"): st.column_config.NumberColumn(format="%.2f%%"),
        },
    )

    csv_data = display_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        _txt("download"),
        data=csv_data,
        file_name="market_basket_analysis.csv",
        mime="text/csv",
    )

    insight_items = [
        f"{_txt('total_orders')}: {total_orders:,}",
        f"{_txt('total_products')}: {total_products:,}",
        f"{_txt('avg_items')}: {avg_items:,.2f}",
        f"{_txt('avg_order_value')}: {_format_money(avg_order_value) if revenue_available else _txt('not_available')}",
    ]
    try:
        top_rule = rules_df.sort_values(["count", "lift", "confidence"], ascending=False).head(1)
        if not top_rule.empty:
            row = top_rule.iloc[0]
            insight_items.append(f"{_txt('combo')}: {row['combo']}")
            insight_items.append(f"{_txt('count')}: {int(row['count']):,}")
            insight_items.append(f"{_txt('lift')}: {float(row['lift']):.2f}")
    except Exception:
        pass
    render_ai_insights("market_basket_analysis", t("market_basket_analysis"), insight_items)
