"""Shared chart component helpers."""
# 代码来源：AI生成
# 模块说明：组件模块，负责可复用界面组件渲染。

from config.theme import apply_plotly_theme


# 函数说明：处理 apply_chart_theme 相关逻辑。
# 代码来源：AI生成
def apply_chart_theme(chart, height=None):
    """Apply the global Plotly theme when the object is a Plotly figure."""
    if hasattr(chart, "update_layout"):
        return apply_plotly_theme(chart, height=height)
    if isinstance(chart, dict):
        themed = dict(chart)
        for key, value in themed.items():
            themed[key] = apply_chart_theme(value, height=height)
        return themed
    if isinstance(chart, list):
        return [apply_chart_theme(value, height=height) for value in chart]
    return chart


# 函数说明：处理 plot_placeholder 相关逻辑。
# 代码来源：AI生成
def plot_placeholder(translator):
    """Return a placeholder chart message."""
    return {"message": translator.translate("chart_placeholder")}
