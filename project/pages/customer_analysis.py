"""Customer Analysis 页面 — 客户仪表盘。

布局：
1) 客户核心指标（总客户数、活跃客户数、人均消费、人均订单数）
2) 客户排行榜（Top20）
3) RFM 分析与客户分层柱状图
4) 客户价值与订单分布图

优先使用当前已加载数据集，缺少字段时优雅降级。所有可见文本通过 `t(...)` 国际化。
"""

import streamlit as st
import pandas as pd
from typing import Optional
try:
    import plotly.express as px
except Exception:
    px = None

from services.translator import t
from services import data_manager
from services.ai_insights import render_ai_insights
from config.theme import ACCENT, CARD, CHART_COLORS, PRIMARY, SECONDARY_BACKGROUND, SUCCESS, TEXT, WARNING, apply_plotly_theme


def _find_column(df: pd.DataFrame, candidates) -> Optional[str]:
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        cand_low = cand.lower()
        if cand_low in lower_map:
            return lower_map[cand_low]
    for col in cols:
        for cand in candidates:
            if cand.lower() in col.lower():
                return col
    return None


def render():
    st.title(t("customer_analysis"))
    st.write(t("customer_analysis_summary"))

    cur = data_manager.get_current_dataset()
    if not cur:
        st.info(t("no_dataset_loaded"))
        return

    df = cur.get("df")
    if df is None or df.empty:
        st.info(t("no_dataset_loaded"))
        return

    # detect columns
    customer_col = _find_column(df, ["customerid", "customer id", "customer", "custid"])
    order_col = _find_column(df, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"])
    qty_col = _find_column(df, ["quantity", "qty", "amount", "units"])
    price_col = _find_column(df, ["unitprice", "unit price", "price", "unit_price"])
    date_col = _find_column(df, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"])
    revenue_col = _find_column(df, ["revenue", "total", "sales", "amount", "line_total", "amountpaid"]) 

    # compute revenue if needed
    rev_col = None
    if revenue_col:
        rev_col = revenue_col
    elif price_col and qty_col:
        try:
            df = df.copy()
            df["_revenue_calc"] = pd.to_numeric(df[price_col], errors="coerce").fillna(0) * pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
            rev_col = "_revenue_calc"
        except Exception:
            rev_col = None

    # KPIs
    total_customers = None
    if customer_col:
        try:
            total_customers = int(df[customer_col].nunique())
        except Exception:
            total_customers = None

    active_customers = None
    if customer_col and date_col:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            max_date = df[date_col].max()
            thresh = max_date - pd.Timedelta(days=365)
            recent = df[df[date_col] >= thresh]
            active_customers = int(recent[customer_col].nunique())
        except Exception:
            active_customers = None

    avg_spend = None
    if customer_col and rev_col:
        try:
            cust_rev = df.groupby(customer_col)[rev_col].sum()
            avg_spend = float(cust_rev.mean())
        except Exception:
            avg_spend = None

    avg_orders = None
    if customer_col:
        try:
            if order_col:
                cust_orders = df.groupby(customer_col)[order_col].nunique()
            else:
                cust_orders = df.groupby(customer_col).size()
            avg_orders = float(cust_orders.mean())
        except Exception:
            avg_orders = None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(t("kpi_total_customers"), f"{total_customers:,}" if total_customers is not None else t("not_available"))
    c2.metric(t("kpi_active_customers"), f"{active_customers:,}" if active_customers is not None else t("not_available"))
    c3.metric(t("kpi_avg_spend_per_customer"), f"{avg_spend:,.2f}" if avg_spend is not None else t("not_available"))
    c4.metric(t("kpi_avg_orders_per_customer"), f"{avg_orders:,.2f}" if avg_orders is not None else t("not_available"))

    st.markdown("---")

    # Top customers
    st.subheader(t("top_customers"))
    if customer_col and rev_col:
        try:
            grouped = df.groupby(customer_col)
            revenue_series = grouped[rev_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
            if order_col:
                orders_series = grouped[order_col].nunique()
            else:
                orders_series = grouped.size()

            top = pd.DataFrame({
                "customer": revenue_series.index.astype(str),
                "revenue": revenue_series.values,
                "orders": orders_series.reindex(revenue_series.index).values,
            })
            top = top.sort_values("revenue", ascending=False).head(20)
            display = top.rename(columns={
                "customer": t("column_customer_id"),
                "orders": t("column_orders"),
                "revenue": t("column_revenue"),
            })[[t("column_customer_id"), t("column_orders"), t("column_revenue")]]
            st.table(display)
        except Exception:
            st.warning(t("no_customers_data"))
    else:
        st.info(t("no_customers_data"))

    st.markdown("---")

    # RFM 分析
    # RFM -> Customer Segmentation (horizontal bar chart)
    lang = st.session_state.get("language", None)
    if lang and str(lang).lower().startswith("zh"):
        seg_title = "客户分层分布"
    else:
        seg_title = "Customer Segmentation"
    st.subheader(seg_title)
    if customer_col and date_col and rev_col:
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

            grouped = df.groupby(customer_col)
            last_purchase = grouped[date_col].max()
            max_date = df[date_col].max()

            recency = (max_date - last_purchase).dt.days

            if order_col:
                frequency = grouped[order_col].nunique()
            else:
                frequency = grouped.size()

            monetary = grouped[rev_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum())

            # build rfm without dropping rows; normalize/fill missing values to avoid empty DataFrame
            rfm = pd.DataFrame({"recency": recency, "frequency": frequency, "monetary": monetary})

            # recency: fill NaN with max existing recency or a large sentinel
            if rfm["recency"].notna().any():
                try:
                    r_max = int(rfm["recency"].max())
                except Exception:
                    r_max = 9999
                rfm["recency"] = rfm["recency"].fillna(r_max)
            else:
                rfm["recency"] = rfm["recency"].fillna(9999)

            # frequency/monetary: coerce numeric and fill zeros
            rfm["frequency"] = pd.to_numeric(rfm["frequency"], errors="coerce").fillna(0)
            rfm["monetary"] = pd.to_numeric(rfm["monetary"], errors="coerce").fillna(0)

            # ensure orders column exists (orders == frequency)
            if "orders" not in rfm.columns:
                rfm["orders"] = rfm["frequency"]

            if rfm.empty:
                st.info(t("no_rfm_data"))
            else:
                # segmentation logic (same as before)
                r75 = rfm["recency"].quantile(0.75)
                f75 = rfm["frequency"].quantile(0.75)
                m75 = rfm["monetary"].quantile(0.75)

                def seg(row):
                    try:
                        if row["monetary"] >= m75 and row["frequency"] >= f75:
                            return "high_value"
                        if row["frequency"] >= f75:
                            return "loyal"
                        if row["recency"] >= r75:
                            return "at_risk"
                        return "normal"
                    except Exception:
                        return "normal"

                rfm["segment"] = rfm.apply(seg, axis=1)

                # counts by segment with localized labels
                counts = rfm["segment"].value_counts().reset_index()
                counts.columns = ["segment_key", "count"]
                seg_label_map = {"high_value": t("segment_high_value"), "loyal": t("segment_loyal"), "normal": t("segment_normal"), "at_risk": t("segment_at_risk")}
                counts["label"] = counts["segment_key"].map(seg_label_map).fillna(t("segment_normal"))
                counts = counts.sort_values("count", ascending=False)

                if px:
                    fig = px.bar(counts, x="count", y="label", orientation="h", labels={"count": t("label_count"), "label": t("rfm_segments")}, title=seg_title, color_discrete_sequence=[PRIMARY])
                    fig = apply_plotly_theme(fig)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.bar_chart(counts.set_index("label")["count"])
        except Exception:
            st.warning(t("unable_compute_rfm"))
    else:
        st.info(t("not_enough_rfm_fields"))

    st.markdown("---")

    # Top10 高价值客户（保留并放到 KPI 下面）
    st.subheader(t("top10_high_value_customers"))
    if customer_col and rev_col:
        try:
            grouped = df.groupby(customer_col)
            revenue_series = grouped[rev_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum())
            if order_col:
                orders_series = grouped[order_col].nunique()
            else:
                orders_series = grouped.size()

            top = pd.DataFrame({
                "customer": revenue_series.index.astype(str),
                "revenue": revenue_series.values,
                "orders": orders_series.reindex(revenue_series.index).values,
            })
            top = top.sort_values("revenue", ascending=False).head(10)

            # build mapping from rfm index (string) to raw segment key, then map to localized label
            seg_label_map = {"high_value": t("segment_high_value"), "loyal": t("segment_loyal"), "normal": t("segment_normal"), "at_risk": t("segment_at_risk")}
            rfm_map = {}
            if "rfm" in locals() and not rfm.empty:
                rfm_map = {str(idx): seg for idx, seg in rfm["segment"].items()}

            top["segment"] = top["customer"].map(lambda cid: seg_label_map.get(rfm_map.get(str(cid), "normal"), t("segment_normal")))

            display = top.rename(columns={
                "customer": t("column_customer_id"),
                "orders": t("column_orders"),
                "revenue": t("column_revenue"),
                "segment": t("label_segment"),
            })[[t("column_customer_id"), t("column_orders"), t("column_revenue"), t("label_segment")]]
            st.table(display)
        except Exception:
            st.warning(t("no_customers_data"))
    else:
        st.info(t("no_customers_data"))

    st.markdown("---")

    # Top客户贡献率分析（Pareto）
    st.subheader(t("revenue_share"))
    try:
        grouped = df.groupby(customer_col)
        revenue_series = grouped[rev_col].apply(lambda s: pd.to_numeric(s, errors="coerce").sum()).sort_values(ascending=False)
        if revenue_series.empty:
            st.info(t("no_customers_data"))
        else:
            total = revenue_series.sum()
            cum_pct = revenue_series.cumsum() / total
            pareto_df = pd.DataFrame({
                "rank": range(1, len(cum_pct) + 1),
                "revenue": revenue_series.values,
                "cum_pct": cum_pct.values,
            })
            if px:
                fig_pareto = px.line(pareto_df, x="rank", y="cum_pct", labels={"rank": t("kpi_total_customers"), "cum_pct": t("label_revenue")}, title=t("revenue_share"), color_discrete_sequence=[PRIMARY])
                # mark 80% contribution position
                idx80 = pareto_df[pareto_df["cum_pct"] >= 0.8].index
                if len(idx80) > 0:
                    pos = int(pareto_df.loc[idx80[0], "rank"])
                    val = float(pareto_df.loc[idx80[0], "cum_pct"])
                    fig_pareto.add_vline(x=pos, line_dash="dash", line_color=WARNING)
                    fig_pareto.add_annotation(x=pos, y=val, text=f"80% -> {pos}", showarrow=True, arrowhead=2)
                fig_pareto.update_yaxes(tickformat=".0%")
                fig_pareto = apply_plotly_theme(fig_pareto)
                st.plotly_chart(fig_pareto, use_container_width=True)
            else:
                st.write(pareto_df)

            # TopN contribution metrics
            top10_pct = revenue_series.head(10).sum() / total if len(revenue_series) >= 1 else 0
            top50_pct = revenue_series.head(50).sum() / total if len(revenue_series) >= 1 else 0
            top100_pct = revenue_series.head(100).sum() / total if len(revenue_series) >= 1 else 0
            m1, m2, m3 = st.columns(3)
            m1.metric(t("top10_high_value_customers"), f"{top10_pct:.1%}")
            m2.metric("Top50", f"{top50_pct:.1%}")
            m3.metric("Top100", f"{top100_pct:.1%}")
    except Exception:
        st.warning(t("unable_compute_rfm"))

    st.markdown("---")

    # 客户价值等级分布（甜甜圈）
    st.subheader(t("customer_segment_distribution"))
    if "rfm" in locals() and not rfm.empty:
        try:
            seg_map = {"high_value": t("segment_high_value"), "loyal": t("segment_loyal"), "normal": t("segment_normal"), "at_risk": t("segment_at_risk")}
            seg_counts = rfm["segment"].map(seg_map).value_counts().reset_index()
            seg_counts.columns = [t("rfm_segments"), t("label_count")]
            if px and not seg_counts.empty:
                fig_donut = px.pie(seg_counts, names=t("rfm_segments"), values=t("label_count"), hole=0.4, color_discrete_sequence=CHART_COLORS)
                fig_donut.update_traces(textinfo='percent+label', hovertemplate='%{label}: %{percent} (%{value})')
                fig_donut = apply_plotly_theme(fig_donut)
                st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.table(seg_counts)
        except Exception:
            st.warning(t("unable_compute_rfm"))
    else:
        st.info(t("no_rfm_data"))

    st.markdown("---")

    # 客户价值矩阵（散点图）
    # Customer Value Quadrant Chart
    # show localized title: Chinese -> 客户价值四象限分析, English -> Customer Value Matrix
    lang = st.session_state.get("language", None)
    if lang and str(lang).lower().startswith("zh"):
        matrix_title = "客户价值四象限分析"
        quad_labels = {
            "lt": "大额客户",
            "rt": "核心客户",
            "lb": "普通客户",
            "rb": "活跃客户",
        }
    else:
        matrix_title = "Customer Value Matrix"
        quad_labels = {
            "lt": "High-Spend Customers",
            "rt": "Core Customers",
            "lb": "Regular Customers",
            "rb": "Active Customers",
        }

    st.subheader(matrix_title)
    # 客户价值矩阵：改为 Treemap（树状图）
    if "rfm" in locals() and not rfm.empty and all(c in rfm.columns for c in ["frequency", "monetary", "segment"]):
        try:
            # 聚合到按 segment 展示：统计客户数与销售额
            tmp = rfm.reset_index()
            id_col = tmp.columns[0]
            tmp = tmp.rename(columns={id_col: "CustomerID"})
            tmp["monetary"] = pd.to_numeric(tmp["monetary"], errors="coerce").fillna(0)

            treemap_df = (
                tmp.groupby("segment")
                .agg(
                    customer_count=("CustomerID", "count"),
                    sales=("monetary", "sum"),
                )
                .reset_index()
            )

            # segment_label is the fixed English color key; segment_display is the Chinese label shown in the treemap.
            seg_color_key_map = {"high_value": "High Value", "loyal": "Loyal", "normal": "Normal", "at_risk": "At-risk"}
            seg_display_map = {"high_value": "高价值客户", "loyal": "忠诚客户", "normal": "普通客户", "at_risk": "流失风险客户"}
            treemap_df["segment_label"] = treemap_df["segment"].map(seg_color_key_map).fillna("Normal")
            treemap_df["segment_display"] = treemap_df["segment"].map(seg_display_map).fillna("普通客户")

            # sales percent
            total_sales = treemap_df["sales"].sum() if not treemap_df.empty else 0
            treemap_df["sales_pct"] = treemap_df["sales"].apply(lambda x: x / total_sales if total_sales else 0)

            # customer percent
            total_customers = treemap_df["customer_count"].sum() if not treemap_df.empty else 0
            treemap_df["customer_pct"] = treemap_df["customer_count"].apply(lambda x: x / total_customers if total_customers else 0)

            labels = {"segment_display": t("label_segment"), "segment_label": t("label_segment"), "sales": t("label_monetary"), "customer_count": t("label_count")}

            # localized percent label for customers if needed
            if lang and str(lang).lower().startswith("zh"):
                pct_label_customer = "客户占比"
            else:
                pct_label_customer = "Customer %"

            if px:
                # 使用 customer_count 作为面积，sales 作为颜色
                fig = px.treemap(
                    treemap_df,
                    path=["segment_display"],
                    values="sales",
                    color="segment_label",
                    color_discrete_map={
                        "High Value": PRIMARY,
                        "Loyal": SUCCESS,
                        "Normal": ACCENT,
                        "At-risk": WARNING,
                    },
                    custom_data=["customer_count", "customer_pct", "sales", "sales_pct"],
                    labels=labels,
                    title=matrix_title,
                )
                hovertemplate = (
                    f"{t('label_segment')}: %{{label}}<br>"
                    f"{t('label_count')}: %{{customdata[0]:.0f}}<br>"
                    f"{pct_label_customer}: %{{customdata[1]:.1%}}<br>"
                    f"{t('label_monetary')}: %{{customdata[2]:,.0f}}<br>"
                    f"{t('revenue_share')}: %{{customdata[3]:.1%}}<extra></extra>"
                )

                # 文本显示：等级、客户数、客户占比、销售额、销售占比（格式化）
                texttemplate = (
                    f"<b>%{{label}}</b><br>"
                    f"{t('label_count')}: %{{customdata[0]:.0f}}<br>"
                    f"{pct_label_customer}: %{{customdata[1]:.1%}}<br>"
                    f"{t('label_monetary')}: %{{customdata[2]:,.0f}}<br>"
                    f"{t('revenue_share')}: %{{customdata[3]:.1%}}"
                )

                fig.update_traces(
                    hovertemplate=hovertemplate,
                    texttemplate=texttemplate,
                    textinfo="label+text",
                    textfont_size=20,
                    textfont_family='Arial',
                    textfont_color='white',
                    marker=dict(line=dict(width=2, color=CARD)),
                )

                fig = apply_plotly_theme(fig, height=600)
                fig.update_layout(
                    margin=dict(t=50, l=25, r=25, b=25),
                    font=dict(size=20, color=TEXT),
                    uniformtext=dict(minsize=18, mode='show'),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                display = treemap_df[["segment_label", "customer_count", "sales"]].rename(columns={"segment_label": t("label_segment"), "customer_count": t("label_count"), "sales": t("label_monetary")})
                st.table(display)
        except Exception:
            st.warning(t("unable_compute_rfm"))
    else:
        st.info(t("no_rfm_data"))

    st.markdown("---")

    # 客户行为相关性（热力图）
    st.subheader(t("customer_behavior_heatmap"))
    if "rfm" in locals() and not rfm.empty:
        try:
            # create bins
            freq_bins = pd.qcut(rfm["frequency"].fillna(0), q=5, duplicates='drop')
            mon_bins = pd.qcut(rfm["monetary"].fillna(0), q=5, duplicates='drop')
            heat = pd.crosstab(freq_bins, mon_bins)
            if px:
                fig_heat = px.imshow(heat.values, x=[str(x) for x in heat.columns], y=[str(y) for y in heat.index], labels={"x": t("label_monetary_bins"), "y": t("label_frequency_bins"), "color": t("label_count")}, title=t("customer_behavior_heatmap"), color_continuous_scale=[[0, SECONDARY_BACKGROUND], [1, PRIMARY]])
                fig_heat = apply_plotly_theme(fig_heat)
                st.plotly_chart(fig_heat, use_container_width=True)
            else:
                st.table(heat)
        except Exception:
            st.warning(t("no_rfm_data"))
    else:
        st.info(t("no_rfm_data"))

    insight_items = [
        f"{t('kpi_total_customers')}: {total_customers:,}" if total_customers is not None else f"{t('kpi_total_customers')}: {t('not_available')}",
        f"{t('kpi_active_customers')}: {active_customers:,}" if active_customers is not None else f"{t('kpi_active_customers')}: {t('not_available')}",
        f"{t('kpi_avg_spend_per_customer')}: {avg_spend:,.2f}" if avg_spend is not None else f"{t('kpi_avg_spend_per_customer')}: {t('not_available')}",
        f"{t('kpi_avg_orders_per_customer')}: {avg_orders:,.2f}" if avg_orders is not None else f"{t('kpi_avg_orders_per_customer')}: {t('not_available')}",
    ]
    if "rfm" in locals() and not rfm.empty and "segment" in rfm.columns:
        try:
            seg_label_map = {"high_value": t("segment_high_value"), "loyal": t("segment_loyal"), "normal": t("segment_normal"), "at_risk": t("segment_at_risk")}
            top_segment_key = rfm["segment"].value_counts().idxmax()
            top_segment_count = int(rfm["segment"].value_counts().max())
            insight_items.append(f"{t('rfm_segments')}: {seg_label_map.get(top_segment_key, top_segment_key)} ({top_segment_count:,})")
        except Exception:
            pass
    render_ai_insights("customer_analysis", t("customer_analysis"), insight_items)
