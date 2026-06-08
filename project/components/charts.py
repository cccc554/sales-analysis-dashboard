"""Shared chart component helpers."""

from config.theme import apply_plotly_theme


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


def plot_placeholder(translator):
    """Return a placeholder chart message."""
    return {"message": translator.translate("chart_placeholder")}
