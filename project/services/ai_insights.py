"""Reusable AI insight panel for analysis pages."""

import hashlib

import streamlit as st

from services.llm_service import QwenService, get_qianwen_api_key


MODEL_OPTIONS = {"qwen-plus", "qwen-max", "qwen-turbo"}

TEXT = {
    "zh": {
        "title": "AI 智能洞察",
        "fallback_intro": "基于当前页面数据，主要结论如下：",
        "fallback_advice": "建议：优先关注异常变化、头部贡献项和可直接落地的运营动作。",
        "prompt_language": "Chinese",
        "style_defaults": {
            "专业分析": "Use a professional data analysis style with clear conclusions and supporting metrics.",
            "管理层汇报": "Use an executive reporting style. Prioritize business impact, concise conclusions, and action items.",
            "简洁模式": "Use a concise style. Keep the answer short and focused.",
            "详细模式": "Use a detailed style. Explain reasoning, evidence, and recommendations thoroughly.",
        },
        "default_style": "专业分析",
    },
    "en": {
        "title": "AI Insights",
        "fallback_intro": "Based on the current page data, the main conclusions are:",
        "fallback_advice": "Recommendation: prioritize unusual changes, leading contribution items, and practical operational actions.",
        "prompt_language": "English",
        "style_defaults": {
            "Professional Analysis": "Use a professional analysis style with clear conclusions and supporting metrics.",
            "Executive Report": "Use an executive reporting style. Prioritize business impact, concise conclusions, and action items.",
            "Concise": "Use a concise style. Keep the answer short and focused.",
            "Detailed": "Use a detailed style. Explain reasoning, evidence, and recommendations thoroughly.",
        },
        "default_style": "Professional Analysis",
    },
}


def _lang() -> str:
    language = str(st.session_state.get("language", "en")).lower()
    return "zh" if language.startswith("zh") else "en"


def _text(key: str):
    return TEXT[_lang()][key]


def _current_ai_config():
    language = _lang()
    model = st.session_state.get("ai_model_select") or st.session_state.get("ai_model_name") or "qwen-plus"
    if model not in MODEL_OPTIONS:
        model = "qwen-plus"

    try:
        temperature = float(st.session_state.get("ai_temperature", 0.2))
    except Exception:
        temperature = 0.2

    style = st.session_state.get(f"ai_response_style_{language}") or _text("default_style")
    style_instruction = _text("style_defaults").get(style, style)

    return {
        "model": model,
        "temperature": temperature,
        "style": style,
        "style_instruction": style_instruction,
    }


def _normalize_summary(summary_items) -> list[str]:
    return [str(item).strip() for item in summary_items if str(item).strip()]


def _local_insight(summary_items: list[str]) -> str:
    lines = [_text("fallback_intro"), ""]
    lines.extend(f"- {item}" for item in summary_items)
    lines.extend(["", _text("fallback_advice")])
    return "\n".join(lines)


def _build_prompt(page_title: str, summary_items: list[str], fallback: str, config: dict) -> str:
    summary_text = "\n".join(f"- {item}" for item in summary_items)
    return "\n".join(
        [
            f"Answer language: {_text('prompt_language')}",
            f"Response style: {config['style_instruction']}",
            f"Analysis page: {page_title}",
            "Use only the provided page summary. Do not invent metrics.",
            "",
            "Page data summary:",
            summary_text,
            "",
            "Local rule-based insight:",
            fallback,
            "",
            "Please generate concise BI insights with conclusions, evidence, and business recommendations.",
        ]
    )


def _cache_key(page_id: str, page_title: str, summary_items: list[str], config: dict, has_api_key: bool) -> str:
    payload = "|".join(
        [
            page_id,
            page_title,
            _lang(),
            config["model"],
            str(config["temperature"]),
            config["style"],
            str(has_api_key),
            *summary_items,
        ]
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"ai_insight_{page_id}_{digest}"


def render_ai_insights(page_id: str, page_title: str, summary_items) -> None:
    normalized_summary = _normalize_summary(summary_items)
    if not normalized_summary:
        return

    config = _current_ai_config()
    fallback = _local_insight(normalized_summary)
    api_key = get_qianwen_api_key()
    cache_key = _cache_key(page_id, page_title, normalized_summary, config, bool(api_key))

    if cache_key not in st.session_state:
        insight = fallback
        if api_key:
            try:
                service = QwenService(
                    api_key=api_key,
                    model=config["model"],
                    temperature=config["temperature"],
                )
                insight = service.generate(_build_prompt(page_title, normalized_summary, fallback, config))
            except Exception:
                insight = fallback
        st.session_state[cache_key] = insight

    st.markdown("---")
    with st.expander(_text("title"), expanded=True):
        st.info(st.session_state[cache_key])
