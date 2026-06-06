"""Forecast Analysis page.

Aggregates monthly sales and compares Linear Regression and Moving Average
forecasts for the next six months.
"""

from typing import Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

try:
    import plotly.graph_objects as go
except Exception:
    go = None

try:
    from sklearn.linear_model import LinearRegression
except Exception:
    LinearRegression = None

from services import data_manager
from services.ai_insights import render_ai_insights


TEXT = {
    "en": {
        "title": "Forecast Analysis",
        "summary": "Monthly sales trend and six-month sales forecast comparison.",
        "overview": "Forecast KPI Overview",
        "historical_total": "Historical Total Sales",
        "monthly_average": "Average Monthly Sales",
        "forecast_total": "Recommended Forecast Total",
        "forecast_growth": "Recommended Growth Rate",
        "historical_chart": "Historical Monthly Sales Trend",
        "forecast_compare_chart": "Linear Regression vs Moving Average Forecast",
        "combined_chart": "Historical + Forecast Sales Trend",
        "forecast_table": "Forecast Result Table",
        "business_reading": "Business Interpretation",
        "model_notes": "Model Notes",
        "recommended_model": "Recommended Model",
        "linear_regression": "Linear Regression",
        "moving_average": "Moving Average",
        "linear_note": "Linear Regression: suitable for long-term trends.",
        "moving_note": "Moving Average: suitable for short-term trends.",
        "month": "Month",
        "sales": "Sales",
        "forecast_month": "Forecast Month",
        "historical_sales": "Historical Sales",
        "linear_forecast": "Linear Regression",
        "moving_forecast": "Moving Average",
        "not_available": "N/A",
        "no_dataset": "No dataset loaded.",
        "missing_date": "Missing date field. Expected InvoiceDate, Date, OrderDate, or Timestamp.",
        "missing_sales": "Missing sales fields. Expected Revenue/Sales or Quantity and UnitPrice.",
        "not_enough_data": "At least two monthly sales points are required for forecasting.",
        "plotly_missing": "Plotly is unavailable; charts cannot be rendered.",
        "recommend_linear": "Linear Regression is recommended because its recent backtest error is lower and it better captures the long-term direction.",
        "recommend_moving": "Moving Average is recommended because its recent backtest error is lower and it better follows short-term fluctuations.",
        "growth": "Future six-month sales are expected to keep growing; recommended forecast total is about {total}; expected growth rate is {growth}.",
        "decline": "Future six-month sales are expected to decline; recommended forecast total is about {total}; expected growth rate is {growth}.",
        "flat": "Future six-month sales are expected to remain relatively stable; recommended forecast total is about {total}; expected growth rate is {growth}.",
    },
    "zh": {
        "title": "预测分析（Forecast Analysis）",
        "summary": "按月份聚合销售额，并对比未来6个月的线性回归预测与移动平均预测。",
        "overview": "预测指标概览",
        "historical_total": "历史累计销售额",
        "monthly_average": "月均销售额",
        "forecast_total": "推荐模型预测未来6个月销售额",
        "forecast_growth": "推荐模型预测增长率",
        "historical_chart": "历史月度销售趋势",
        "forecast_compare_chart": "Linear Regression vs Moving Average 预测对比",
        "combined_chart": "历史+预测销售趋势",
        "forecast_table": "预测结果表格",
        "business_reading": "业务解读",
        "model_notes": "模型说明",
        "recommended_model": "推荐模型",
        "linear_regression": "Linear Regression",
        "moving_average": "Moving Average",
        "linear_note": "Linear Regression：适合长期趋势。",
        "moving_note": "Moving Average：适合短期趋势。",
        "month": "月份",
        "sales": "销售额",
        "forecast_month": "预测月份",
        "historical_sales": "历史销售额",
        "linear_forecast": "Linear Regression",
        "moving_forecast": "Moving Average",
        "not_available": "暂无",
        "no_dataset": "当前未加载任何数据集。",
        "missing_date": "缺少日期字段。需要 InvoiceDate、Date、OrderDate 或 Timestamp。",
        "missing_sales": "缺少销售额字段。需要 Revenue/Sales，或 Quantity 与 UnitPrice。",
        "not_enough_data": "至少需要两个月度销售数据点才能进行预测。",
        "plotly_missing": "Plotly 不可用，无法渲染图表。",
        "recommend_linear": "推荐 Linear Regression，因为它在最近数据回测中的误差更低，更适合捕捉长期趋势。",
        "recommend_moving": "推荐 Moving Average，因为它在最近数据回测中的误差更低，更适合跟踪短期波动。",
        "growth": "未来6个月销售额预计保持增长趋势；推荐模型预测总销售额约 {total} 元；预计增长率 {growth}。",
        "decline": "未来6个月销售额预计呈下降趋势；推荐模型预测总销售额约 {total} 元；预计增长率 {growth}。",
        "flat": "未来6个月销售额预计整体保持平稳；推荐模型预测总销售额约 {total} 元；预计增长率 {growth}。",
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


def _format_money(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return _txt("not_available")


def _format_percent(value) -> str:
    try:
        return f"{float(value):.1%}"
    except Exception:
        return _txt("not_available")


def _build_monthly_sales(df: pd.DataFrame) -> Tuple[pd.DataFrame, Optional[str]]:
    date_col = _find_column(df, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"])
    qty_col = _find_column(df, ["quantity", "qty", "units"])
    price_col = _find_column(df, ["unitprice", "unit price", "unit_price", "price"])
    revenue_col = _find_column(df, ["revenue", "sales", "total", "amount", "line_total", "amountpaid", "sales_amount"])

    if not date_col:
        return pd.DataFrame(), _txt("missing_date")

    work = df.copy()
    work["_date"] = pd.to_datetime(work[date_col], errors="coerce")
    work = work.dropna(subset=["_date"]).copy()

    if revenue_col:
        work["_sales"] = pd.to_numeric(work[revenue_col], errors="coerce").fillna(0)
    elif qty_col and price_col:
        quantity = pd.to_numeric(work[qty_col], errors="coerce").fillna(0)
        price = pd.to_numeric(work[price_col], errors="coerce").fillna(0)
        work["_sales"] = quantity * price
    else:
        return pd.DataFrame(), _txt("missing_sales")

    work["Month"] = work["_date"].dt.to_period("M").dt.to_timestamp()
    monthly = (
        work.groupby("Month", as_index=False)["_sales"]
        .sum()
        .rename(columns={"_sales": "Sales"})
        .sort_values("Month")
    )
    return monthly, None


def _future_months(monthly: pd.DataFrame, periods: int = 6) -> pd.DatetimeIndex:
    last_month = monthly["Month"].max()
    return pd.date_range(last_month + pd.offsets.MonthBegin(1), periods=periods, freq="MS")


def _forecast_linear_regression(monthly: pd.DataFrame, periods: int = 6) -> pd.DataFrame:
    y = monthly["Sales"].astype(float).values
    x = np.arange(len(monthly)).reshape(-1, 1)
    future_x = np.arange(len(monthly), len(monthly) + periods).reshape(-1, 1)

    if LinearRegression is not None:
        model = LinearRegression()
        model.fit(x, y)
        forecast_values = model.predict(future_x)
    else:
        slope, intercept = np.polyfit(np.arange(len(monthly)), y, 1)
        forecast_values = intercept + slope * future_x.ravel()

    return pd.DataFrame(
        {
            "Month": _future_months(monthly, periods),
            "Linear Regression": np.clip(forecast_values, 0, None),
        }
    )


def _forecast_moving_average(monthly: pd.DataFrame, periods: int = 6, window: int = 3) -> pd.DataFrame:
    history = monthly["Sales"].astype(float).tolist()
    values = []
    for _ in range(periods):
        current_window = history[-window:] if len(history) >= window else history
        prediction = float(np.mean(current_window)) if current_window else 0.0
        prediction = max(prediction, 0.0)
        values.append(prediction)
        history.append(prediction)

    return pd.DataFrame(
        {
            "Month": _future_months(monthly, periods),
            "Moving Average": values,
        }
    )


def _build_forecasts(monthly: pd.DataFrame) -> pd.DataFrame:
    linear = _forecast_linear_regression(monthly)
    moving = _forecast_moving_average(monthly)
    return linear.merge(moving, on="Month", how="inner")


def _moving_average_predict_from_history(history, window: int = 3) -> float:
    current_window = history[-window:] if len(history) >= window else history
    return float(np.mean(current_window)) if current_window else 0.0


def _backtest_recommendation(monthly: pd.DataFrame) -> Tuple[str, str]:
    if len(monthly) < 6:
        return "Moving Average", _txt("recommend_moving")

    holdout = min(3, max(1, len(monthly) // 4))
    train = monthly.iloc[:-holdout].copy()
    test = monthly.iloc[-holdout:].copy()

    linear_pred = _forecast_linear_regression(train, periods=holdout)["Linear Regression"].values

    history = train["Sales"].astype(float).tolist()
    moving_pred = []
    for _ in range(holdout):
        value = max(_moving_average_predict_from_history(history), 0.0)
        moving_pred.append(value)
        history.append(value)

    actual = test["Sales"].astype(float).values
    linear_mae = float(np.mean(np.abs(actual - linear_pred)))
    moving_mae = float(np.mean(np.abs(actual - np.array(moving_pred))))

    if linear_mae <= moving_mae:
        return "Linear Regression", _txt("recommend_linear")
    return "Moving Average", _txt("recommend_moving")


def _line_chart(title: str, x, y, name: str, color: str, dash: Optional[str] = None):
    if go is None:
        st.info(_txt("plotly_missing"))
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="lines+markers",
            name=name,
            line=dict(color=color, dash=dash or "solid", width=3),
            marker=dict(size=7),
            hovertemplate=f"{_txt('month')}: %{{x|%Y-%m}}<br>{_txt('sales')}: %{{y:,.2f}}<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        height=420,
        margin=dict(t=55, l=20, r=20, b=20),
        xaxis_title=_txt("month"),
        yaxis_title=_txt("sales"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _forecast_comparison_chart(forecast: pd.DataFrame):
    if go is None:
        st.info(_txt("plotly_missing"))
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=forecast["Month"],
            y=forecast["Linear Regression"],
            mode="lines+markers",
            name=_txt("linear_regression"),
            line=dict(color="#d62728", width=3, dash="dash"),
            marker=dict(size=7),
            hovertemplate=f"{_txt('forecast_month')}: %{{x|%Y-%m}}<br>{_txt('linear_regression')}: %{{y:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["Month"],
            y=forecast["Moving Average"],
            mode="lines+markers",
            name=_txt("moving_average"),
            line=dict(color="#2ca02c", width=3, dash="dot"),
            marker=dict(size=7),
            hovertemplate=f"{_txt('forecast_month')}: %{{x|%Y-%m}}<br>{_txt('moving_average')}: %{{y:,.2f}}<extra></extra>",
        )
    )
    fig.update_layout(
        title=_txt("forecast_compare_chart"),
        height=420,
        margin=dict(t=55, l=20, r=20, b=20),
        xaxis_title=_txt("month"),
        yaxis_title=_txt("sales"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _combined_chart(monthly: pd.DataFrame, forecast: pd.DataFrame):
    if go is None:
        st.info(_txt("plotly_missing"))
        return

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly["Month"],
            y=monthly["Sales"],
            mode="lines+markers",
            name=_txt("historical_sales"),
            line=dict(color="#1f77b4", width=3),
            marker=dict(size=7),
            hovertemplate=f"{_txt('month')}: %{{x|%Y-%m}}<br>{_txt('historical_sales')}: %{{y:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["Month"],
            y=forecast["Linear Regression"],
            mode="lines+markers",
            name=_txt("linear_regression"),
            line=dict(color="#d62728", width=3, dash="dash"),
            marker=dict(size=7),
            hovertemplate=f"{_txt('forecast_month')}: %{{x|%Y-%m}}<br>{_txt('linear_regression')}: %{{y:,.2f}}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["Month"],
            y=forecast["Moving Average"],
            mode="lines+markers",
            name=_txt("moving_average"),
            line=dict(color="#2ca02c", width=3, dash="dot"),
            marker=dict(size=7),
            hovertemplate=f"{_txt('forecast_month')}: %{{x|%Y-%m}}<br>{_txt('moving_average')}: %{{y:,.2f}}<extra></extra>",
        )
    )
    fig.update_layout(
        title=_txt("combined_chart"),
        height=470,
        margin=dict(t=55, l=20, r=20, b=20),
        xaxis_title=_txt("month"),
        yaxis_title=_txt("sales"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig, use_container_width=True)


def _business_interpretation(forecast: pd.DataFrame, model_name: str, forecast_total: float, growth_rate: float) -> str:
    first_value = float(forecast[model_name].iloc[0])
    last_value = float(forecast[model_name].iloc[-1])
    if last_value > first_value * 1.03:
        key = "growth"
    elif last_value < first_value * 0.97:
        key = "decline"
    else:
        key = "flat"
    return _txt(key, total=_format_money(forecast_total), growth=_format_percent(growth_rate))


def render():
    st.title(_txt("title"))
    st.write(_txt("summary"))

    cur = data_manager.get_current_dataset()
    if not cur:
        st.info(_txt("no_dataset"))
        return

    df = cur.get("df")
    if df is None or df.empty:
        st.info(_txt("no_dataset"))
        return

    monthly, error_message = _build_monthly_sales(df)
    if error_message:
        st.warning(error_message)
        return

    monthly = monthly[monthly["Sales"].notna()].copy()
    if len(monthly) < 2:
        st.info(_txt("not_enough_data"))
        return

    forecast = _build_forecasts(monthly)
    recommended_model, recommend_reason = _backtest_recommendation(monthly)

    historical_total = float(monthly["Sales"].sum())
    monthly_average = float(monthly["Sales"].mean())
    recommended_total = float(forecast[recommended_model].sum())
    baseline = float(monthly.tail(6)["Sales"].sum()) if len(monthly) >= 6 else monthly_average * 6
    growth_rate = ((recommended_total - baseline) / baseline) if baseline else 0.0

    st.subheader(_txt("overview"))
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(_txt("historical_total"), _format_money(historical_total))
    k2.metric(_txt("monthly_average"), _format_money(monthly_average))
    k3.metric(_txt("forecast_total"), _format_money(recommended_total))
    k4.metric(_txt("forecast_growth"), _format_percent(growth_rate))

    st.markdown("---")

    note_col, rec_col = st.columns(2)
    with note_col:
        st.subheader(_txt("model_notes"))
        st.info(f"{_txt('linear_note')}\n\n{_txt('moving_note')}")
    with rec_col:
        st.subheader(_txt("recommended_model"))
        st.success(f"**{recommended_model}**\n\n{recommend_reason}")

    st.markdown("---")

    left, right = st.columns(2)
    with left:
        _line_chart(
            _txt("historical_chart"),
            monthly["Month"],
            monthly["Sales"],
            _txt("historical_sales"),
            "#1f77b4",
        )
    with right:
        _forecast_comparison_chart(forecast)

    st.markdown("---")

    _combined_chart(monthly, forecast)

    st.markdown("---")

    table_df = forecast.rename(
        columns={
            "Month": _txt("forecast_month"),
            "Linear Regression": _txt("linear_regression"),
            "Moving Average": _txt("moving_average"),
        }
    )
    st.subheader(_txt("forecast_table"))
    st.dataframe(
        table_df,
        use_container_width=True,
        height=260,
        column_config={
            _txt("forecast_month"): st.column_config.DateColumn(format="YYYY-MM"),
            _txt("linear_regression"): st.column_config.NumberColumn(format="%.2f"),
            _txt("moving_average"): st.column_config.NumberColumn(format="%.2f"),
        },
    )

    st.markdown("---")

    st.subheader(_txt("business_reading"))
    st.info(_business_interpretation(forecast, recommended_model, recommended_total, growth_rate))

    insight_items = [
        f"{_txt('historical_total')}: {_format_money(historical_total)}",
        f"{_txt('monthly_average')}: {_format_money(monthly_average)}",
        f"{_txt('recommended_model')}: {recommended_model}",
        f"{_txt('forecast_total')}: {_format_money(recommended_total)}",
        f"{_txt('forecast_growth')}: {_format_percent(growth_rate)}",
        f"{_txt('business_reading')}: {recommend_reason}",
    ]
    render_ai_insights("forecast_analysis", _txt("title"), insight_items)
