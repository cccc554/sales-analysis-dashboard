"""AI data analysis assistant page."""
# 代码来源：AI生成 + 学生修改
# 模块说明：页面模块，负责对应 Streamlit 页面渲染与交互。

from collections import Counter
from itertools import combinations
from typing import Optional

import pandas as pd
import streamlit as st

from services import data_manager
from services.llm_service import QwenService, get_qianwen_api_key
from services.translator import t


QUICK_QUESTION_KEYS = [
    "ai_quick_top_product",
    "ai_quick_customer_contribution",
    "ai_quick_recent_trend",
    "ai_quick_bundles",
    "ai_quick_advice",
]

MODEL_OPTIONS = ["qwen-plus", "qwen-max", "qwen-turbo"]

AI_PANEL_TEXT = {
    "zh": {
        "connected": "✅ 已连接 Qwen",
        "not_connected": "❌ 未连接",
        "guide": "可点击快捷问题，或在底部输入具体业务问题；如已配置 Qwen，将优先使用 AI 生成回答。",
        "context_loading": "正在读取当前数据集上下文...",
        "answer_loading": "正在生成回答...",
        "model_label": "模型选择",
        "temperature_help": (
            "Temperature（温度）用于控制回答的创造性和随机性。\n\n"
            "0.0~0.3：回答稳定、专业、适合数据分析。\n\n"
            "0.4~0.7：回答更加自然灵活。\n\n"
            "0.8~1.0：创造性更强，但稳定性下降。\n\n"
            "推荐：数据分析场景使用 0.2~0.3。"
        ),
        "style_label": "回答风格",
        "style_options": ["专业分析", "管理层汇报", "简洁模式", "详细模式"],
        "style_instructions": {
            "专业分析": "Use a professional data analysis style with clear conclusions and supporting metrics.",
            "管理层汇报": "Use an executive reporting style. Prioritize business impact, concise conclusions, and action items.",
            "简洁模式": "Use a concise style. Keep the answer short and focused.",
            "详细模式": "Use a detailed style. Explain reasoning, evidence, and recommendations thoroughly.",
        },
        "guidelines_title": "AI 回答规范",
        "guidelines_body": (
            "- 使用简体中文\n"
            "- 回答结构清晰\n"
            "- 优先给出分析结论\n"
            "- 提供数据依据\n"
            "- 给出业务建议"
        ),
    },
    "en": {
        "connected": "Connected",
        "not_connected": "Not Connected",
        "guide": "Click a quick question or type a business question below. Qwen is used first when configured.",
        "context_loading": "Reading the current dataset context...",
        "answer_loading": "Generating answer...",
        "model_label": "Model",
        "temperature_help": (
            "Temperature controls creativity and randomness.\n\n"
            "0.0~0.3: Stable, professional, suitable for data analysis.\n\n"
            "0.4~0.7: More natural and flexible responses.\n\n"
            "0.8~1.0: Highly creative, less stable.\n\n"
            "Recommended: Use 0.2~0.3 for data analysis."
        ),
        "style_label": "Response Style",
        "style_options": ["Professional Analysis", "Executive Report", "Concise", "Detailed"],
        "style_instructions": {
            "Professional Analysis": "Use a professional analysis style with clear conclusions and supporting metrics.",
            "Executive Report": "Use an executive reporting style. Prioritize business impact, concise conclusions, and action items.",
            "Concise": "Use a concise style. Keep the answer short and focused.",
            "Detailed": "Use a detailed style. Explain reasoning, evidence, and recommendations thoroughly.",
        },
        "guidelines_title": "AI Response Guidelines",
        "guidelines_body": (
            "- Use English\n"
            "- Clear answer structure\n"
            "- Present analysis conclusions first\n"
            "- Provide data evidence\n"
            "- Give business recommendations"
        ),
    },
}


AI_CSS = """
<style>
.ai-page-header {
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 24px 26px;
    background: linear-gradient(135deg, #F5F7FA, #FFFFFF);
    margin-bottom: 18px;
}
.ai-page-header h1 {
    margin: 0 0 8px 0;
    color: #1E293B;
    font-weight: 700;
}
.ai-page-header p {
    margin: 0;
    color: #64748B;
}
.ai-panel {
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 18px;
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
    margin-bottom: 16px;
}
.ai-panel h3 {
    margin: 0 0 12px 0;
    color: #1E293B;
    font-size: 1.08rem;
    font-weight: 700;
}
.ai-muted {
    color: #64748B;
    font-size: 0.92rem;
    line-height: 1.55;
}
.ai-status {
    border-radius: 12px;
    padding: 12px 14px;
    margin: 12px 0;
    font-weight: 700;
    border: 1px solid transparent;
}
.ai-status-connected {
    color: #2C8C5A;
    background: #F5F7FA;
    border-color: #2C8C5A;
}
.ai-status-disconnected {
    color: #D95B5B;
    background: #F5F7FA;
    border-color: #D95B5B;
}
</style>
"""


# 函数说明：处理 _panel_language 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _panel_language() -> str:
    return "zh" if str(st.session_state.get("language", "en")).startswith("zh") else "en"


# 函数说明：处理 _panel_text 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _panel_text(key: str):
    return AI_PANEL_TEXT[_panel_language()][key]


# 函数说明：查找 _find_column 相关字段或资源。
# 代码来源：AI生成 + 学生修改
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


# 函数说明：清洗 _clean_text 对应的输入文本或数据。
# 代码来源：AI生成 + 学生修改
def _clean_text(value) -> str:
    text = str(value).strip()
    return text if text and text.lower() != "nan" else ""


# 函数说明：处理 _fmt_money 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _fmt_money(value) -> str:
    try:
        return f"{float(value):,.2f}"
    except Exception:
        return t("not_available")


# 函数说明：处理 _fmt_number 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _fmt_number(value) -> str:
    try:
        return f"{float(value):,.0f}"
    except Exception:
        return t("not_available")


# 函数说明：处理 _fmt_pct 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _fmt_pct(value) -> str:
    try:
        return f"{float(value):.1%}"
    except Exception:
        return t("not_available")


# 函数说明：构建 _build_context 所需的数据结构或界面内容。
# 代码来源：AI生成 + 学生修改
def _build_context(cur):
    df = cur.get("df")
    work = df.copy()

    product_col = _find_column(work, ["description", "product", "productname", "product name", "item", "stockcode", "sku"])
    order_col = _find_column(work, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"])
    customer_col = _find_column(work, ["customerid", "customer id", "customer", "custid"])
    qty_col = _find_column(work, ["quantity", "qty", "units"])
    price_col = _find_column(work, ["unitprice", "unit price", "unit_price", "price"])
    revenue_col = _find_column(work, ["revenue", "sales", "total", "amount", "line_total", "amountpaid", "sales_amount"])
    date_col = _find_column(work, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"])

    if revenue_col:
        work["_revenue"] = pd.to_numeric(work[revenue_col], errors="coerce").fillna(0)
    elif qty_col and price_col:
        quantity = pd.to_numeric(work[qty_col], errors="coerce").fillna(0)
        price = pd.to_numeric(work[price_col], errors="coerce").fillna(0)
        work["_revenue"] = quantity * price
    else:
        work["_revenue"] = 0.0

    if qty_col:
        work["_quantity"] = pd.to_numeric(work[qty_col], errors="coerce").fillna(0)
    else:
        work["_quantity"] = 0.0

    if product_col:
        work["_product_name"] = work[product_col].map(_clean_text)
    else:
        work["_product_name"] = ""

    if date_col:
        work["_date"] = pd.to_datetime(work[date_col], errors="coerce")

    dataset_name = cur.get("name") or cur.get("meta", {}).get("name") or t("ai_current_dataset")
    order_count = int(work[order_col].nunique()) if order_col else None
    customer_count = int(work[customer_col].nunique()) if customer_col else None
    total_revenue = float(work["_revenue"].sum())

    return {
        "df": work,
        "dataset_name": dataset_name,
        "product_col": product_col,
        "order_col": order_col,
        "customer_col": customer_col,
        "qty_col": qty_col,
        "price_col": price_col,
        "date_col": date_col,
        "order_count": order_count,
        "customer_count": customer_count,
        "total_revenue": total_revenue,
    }


# 函数说明：处理 _answer_top_product 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _answer_top_product(ctx) -> str:
    df = ctx["df"]
    if not ctx["product_col"] or df["_product_name"].eq("").all():
        return t("ai_no_product_field")

    total_revenue = float(df["_revenue"].sum())
    product_df = (
        df[df["_product_name"] != ""]
        .groupby("_product_name")
        .agg(revenue=("_revenue", "sum"), quantity=("_quantity", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    if product_df.empty:
        return t("ai_no_product_records")

    top = product_df.iloc[0]
    share = float(top["revenue"] / total_revenue) if total_revenue else 0
    return t("ai_top_product_answer").format(
        product=top["_product_name"],
        revenue=_fmt_money(top["revenue"]),
        quantity=_fmt_number(top["quantity"]),
        share=_fmt_pct(share),
    )


# 函数说明：处理 _answer_customer_contribution 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _answer_customer_contribution(ctx) -> str:
    df = ctx["df"]
    customer_col = ctx["customer_col"]
    if not customer_col:
        return t("ai_no_customer_field")

    customer_df = (
        df.groupby(customer_col)
        .agg(revenue=("_revenue", "sum"))
        .reset_index()
        .sort_values("revenue", ascending=False)
    )
    if customer_df.empty:
        return t("ai_no_customer_records")

    total_revenue = float(customer_df["revenue"].sum())
    top_n = max(1, int(len(customer_df) * 0.2))
    high_value = customer_df.head(top_n)
    contribution = float(high_value["revenue"].sum())
    share = contribution / total_revenue if total_revenue else 0
    top_customer = customer_df.iloc[0]

    return t("ai_customer_contribution_answer").format(
        high_value_count=f"{len(high_value):,}",
        contribution=_fmt_money(contribution),
        share=_fmt_pct(share),
        top_customer=top_customer[customer_col],
        top_customer_revenue=_fmt_money(top_customer["revenue"]),
    )


# 函数说明：处理 _answer_recent_trend 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _answer_recent_trend(ctx) -> str:
    df = ctx["df"]
    if not ctx["date_col"]:
        return t("ai_no_date_field")

    trend_df = df.dropna(subset=["_date"]).copy()
    if trend_df.empty:
        return t("ai_invalid_date_field")

    trend_df["month"] = trend_df["_date"].dt.to_period("M").dt.to_timestamp()
    monthly = trend_df.groupby("month", as_index=False)["_revenue"].sum().sort_values("month")
    if len(monthly) < 2:
        return t("ai_not_enough_months")

    recent = monthly.tail(3)
    last_sales = float(recent["_revenue"].iloc[-1])
    prev_sales = float(recent["_revenue"].iloc[-2])
    growth = (last_sales - prev_sales) / prev_sales if prev_sales else 0
    direction = t("ai_trend_up") if growth > 0.03 else t("ai_trend_down") if growth < -0.03 else t("ai_trend_flat")

    lines = [
        t("ai_recent_trend_header"),
        "",
        t("ai_recent_trend_last_sales").format(revenue=_fmt_money(last_sales)),
        t("ai_recent_trend_growth").format(growth=_fmt_pct(growth)),
        t("ai_recent_trend_direction").format(direction=direction),
        "",
        t("ai_recent_trend_last_three"),
    ]
    for _, row in recent.iterrows():
        lines.append(t("ai_recent_trend_month_line").format(
            month=row["month"].strftime("%Y-%m"),
            revenue=_fmt_money(row["_revenue"]),
        ))
    return "\n".join(lines)


# 函数说明：处理 _answer_bundles 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _answer_bundles(ctx) -> str:
    df = ctx["df"]
    if not ctx["product_col"] or not ctx["order_col"]:
        return t("ai_no_basket_fields")

    work = df[(df["_product_name"] != "")].copy()
    item_counts = work.groupby("_product_name")[ctx["order_col"]].nunique().sort_values(ascending=False)
    eligible_items = set(item_counts.head(250).index)
    pair_counter = Counter()

    for _, group in work.groupby(ctx["order_col"], sort=False):
        items = sorted(set(group["_product_name"].tolist()).intersection(eligible_items))
        if len(items) > 30:
            items = sorted(items, key=lambda item: item_counts.get(item, 0), reverse=True)[:30]
            items = sorted(items)
        for pair in combinations(items, 2):
            pair_counter[pair] += 1

    if not pair_counter:
        return t("ai_no_bundle_records")

    lines = [t("ai_bundle_answer_header"), ""]
    for idx, (pair, count) in enumerate(pair_counter.most_common(5), start=1):
        lines.append(t("ai_bundle_answer_item").format(
            index=idx,
            item_a=pair[0],
            item_b=pair[1],
            count=f"{count:,}",
        ))
    lines.append("")
    lines.append(t("ai_bundle_answer_tip"))
    return "\n".join(lines)


# 函数说明：处理 _answer_advice 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _answer_advice(ctx) -> str:
    top_product = _answer_top_product(ctx)
    trend = _answer_recent_trend(ctx)
    customer = _answer_customer_contribution(ctx)
    bundles = _answer_bundles(ctx)

    return t("ai_advice_answer").format(
        top_product=top_product,
        trend=trend,
        customer=customer,
        bundles=bundles,
    )


# 函数说明：处理 _answer_overview 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _answer_overview(ctx) -> str:
    return t("ai_overview_answer").format(
        dataset=ctx["dataset_name"],
        orders=_fmt_number(ctx["order_count"]),
        customers=_fmt_number(ctx["customer_count"]),
        revenue=_fmt_money(ctx["total_revenue"]),
        example_question=t("ai_quick_top_product"),
    )


# 函数说明：生成 _generate_answer 对应的文本或结果。
# 代码来源：AI生成 + 学生修改
def _generate_answer(question: str, ctx) -> str:
    q = question.lower()
    if ("产品" in question and ("最高" in question or "top" in q or "销售额" in question)) or "product" in q:
        return _answer_top_product(ctx)
    if "客户" in question or "customer" in q:
        return _answer_customer_contribution(ctx)
    if "趋势" in question or "最近" in question or "trend" in q:
        return _answer_recent_trend(ctx)
    if "捆绑" in question or "组合" in question or "basket" in q or "bundle" in q:
        return _answer_bundles(ctx)
    if "建议" in question or "recommend" in q or "advice" in q:
        return _answer_advice(ctx)
    return _answer_overview(ctx)


# 函数说明：构建 _build_llm_prompt 所需的数据结构或界面内容。
# 代码来源：AI生成 + 学生修改
def _build_llm_prompt(question: str, ctx, rule_answer: str, model_config: dict) -> str:
    language = "Chinese" if str(st.session_state.get("language", "en")).startswith("zh") else "English"
    style_instruction = model_config.get("style_instruction", "")
    return "\n".join(
        [
            f"Answer language: {language}",
            f"Response style: {style_instruction}",
            "You are helping analyze an e-commerce retail dataset.",
            "Use the dataset summary and local rule-based facts below.",
            "Do not invent fields, totals, or rankings that are not provided.",
            "",
            "Dataset summary:",
            f"- Dataset name: {ctx['dataset_name']}",
            f"- Orders: {_fmt_number(ctx['order_count'])}",
            f"- Customers: {_fmt_number(ctx['customer_count'])}",
            f"- Revenue: {_fmt_money(ctx['total_revenue'])}",
            f"- Product field: {ctx['product_col'] or 'N/A'}",
            f"- Order field: {ctx['order_col'] or 'N/A'}",
            f"- Customer field: {ctx['customer_col'] or 'N/A'}",
            f"- Date field: {ctx['date_col'] or 'N/A'}",
            "",
            f"User question: {question}",
            "",
            "Local rule-based result:",
            rule_answer,
            "",
            "Please provide a concise BI-style answer with practical business interpretation.",
        ]
    )


# 函数说明：生成 _generate_llm_answer 对应的文本或结果。
# 代码来源：AI生成 + 学生修改
def _generate_llm_answer(question: str, ctx, rule_answer: str, model_config: dict) -> str:
    if model_config.get("provider") != "Qwen":
        return rule_answer

    api_key = model_config.get("api_key", "")
    if not api_key:
        return rule_answer

    try:
        service = QwenService(
            api_key=api_key,
            model=model_config.get("model") or "qwen-plus",
            temperature=model_config.get("temperature", 0.2),
        )
        return service.generate(_build_llm_prompt(question, ctx, rule_answer, model_config))
    except Exception as exc:
        return t("ai_qwen_error").format(error=str(exc), fallback=rule_answer)


# 函数说明：处理 _append_message 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _append_message(role: str, content: str):
    st.session_state.ai_assistant_messages.append({"role": role, "content": content})


# 函数说明：渲染 _render_model_config 对应的界面内容。
# 代码来源：AI生成 + 学生修改
def _render_model_config():
    st.markdown(
        f"""
        <div class="ai-panel">
            <h3>{t("ai_model_config_title")}</h3>
            <div class="ai-muted">{t("ai_model_config_desc")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    provider = st.selectbox(
        t("ai_provider_label"),
        ["OpenAI", "DeepSeek", "Qwen"],
        index=2,
        key="ai_provider",
    )
    api_key = get_qianwen_api_key()
    connected = provider == "Qwen" and bool(api_key)
    status_class = "ai-status-connected" if connected else "ai-status-disconnected"
    status_text = _panel_text("connected") if connected else _panel_text("not_connected")
    st.markdown(
        f'<div class="ai-status {status_class}">{status_text}</div>',
        unsafe_allow_html=True,
    )
    st.caption(t("ai_qwen_env_label"))

    model = st.selectbox(
        _panel_text("model_label"),
        MODEL_OPTIONS,
        index=0,
        key="ai_model_select",
    )
    temperature = st.slider(
        t("ai_temperature_label"),
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.1,
        key="ai_temperature",
    )
    st.info(_panel_text("temperature_help"))

    style_options = _panel_text("style_options")
    response_style = st.selectbox(
        _panel_text("style_label"),
        style_options,
        index=0,
        key=f"ai_response_style_{_panel_language()}",
    )

    with st.expander(_panel_text("guidelines_title")):
        st.markdown(_panel_text("guidelines_body"))

    return {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "style": response_style,
        "style_instruction": _panel_text("style_instructions").get(response_style, response_style),
    }


# 函数说明：渲染当前页面或组件。
# 代码来源：AI生成 + 学生修改
def render():
    st.markdown(AI_CSS, unsafe_allow_html=True)
    st.markdown(
        f"""
        <section class="ai-page-header">
            <h1>{t("ai_data_assistant_title")}</h1>
            <p>{t("ai_data_assistant_intro")}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.caption(_panel_text("guide"))

    cur = data_manager.get_current_dataset()
    left, right = st.columns([2.2, 1])

    with right:
        model_config = _render_model_config()

    with left:
        if not cur or cur.get("df") is None or cur.get("df").empty:
            st.info(t("ai_no_dataset_hint"))
            return

        # Build the reusable dataset context before answering questions.
        with st.spinner(_panel_text("context_loading")):
            ctx = _build_context(cur)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric(t("ai_kpi_dataset_name"), ctx["dataset_name"])
        k2.metric(t("ai_kpi_orders"), _fmt_number(ctx["order_count"]))
        k3.metric(t("ai_kpi_customers"), _fmt_number(ctx["customer_count"]))
        k4.metric(t("ai_kpi_revenue"), _fmt_money(ctx["total_revenue"]))

        st.markdown("---")

        st.subheader(t("ai_quick_questions"))
        question = None
        cols = st.columns(len(QUICK_QUESTION_KEYS))
        for idx, quick_question_key in enumerate(QUICK_QUESTION_KEYS):
            quick_question = t(quick_question_key)
            with cols[idx]:
                if st.button(quick_question, key=f"ai_quick_{idx}", use_container_width=True):
                    question = quick_question

        if "ai_assistant_messages" not in st.session_state:
            st.session_state.ai_assistant_messages = [
                {"role": "assistant", "content": _answer_overview(ctx)}
            ]

        st.subheader(t("ai_chat_history_title"))
        for message in st.session_state.ai_assistant_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input(t("ai_chat_input_placeholder"))
        if user_input:
            question = user_input

        if question:
            _append_message("user", question)
            with st.spinner(_panel_text("answer_loading")):
                rule_answer = _generate_answer(question, ctx)
                _append_message("assistant", _generate_llm_answer(question, ctx, rule_answer, model_config))
            st.rerun()
