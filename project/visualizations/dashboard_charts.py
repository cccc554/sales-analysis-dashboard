"""Dashboard chart collection helpers with shared theming."""

from config.theme import ACCENT, PRIMARY, apply_plotly_theme


def style_comparison_chart(fig):
    """Use primary as the default color for comparison charts."""
    if fig is None:
        return fig
    for trace in getattr(fig, "data", []):
        if hasattr(trace, "marker"):
            trace.update(marker_color=PRIMARY)
        if hasattr(trace, "line"):
            trace.update(line=dict(color=PRIMARY, width=3))
    return apply_plotly_theme(fig)


def style_dual_axis_chart(fig):
    """Use primary for the first series and accent for the second series."""
    if fig is None:
        return fig
    colors = [PRIMARY, ACCENT]
    for index, trace in enumerate(getattr(fig, "data", [])):
        color = colors[index] if index < len(colors) else PRIMARY
        if hasattr(trace, "marker"):
            trace.update(marker_color=color)
        if hasattr(trace, "line"):
            trace.update(line=dict(color=color, width=3))
    return apply_plotly_theme(fig)


def _theme_item(item):
    if hasattr(item, "update_layout"):
        return apply_plotly_theme(item)
    if isinstance(item, dict):
        chart_type = item.get("type")
        themed = dict(item)
        for key, value in themed.items():
            if key in {"figure", "fig", "chart"} and hasattr(value, "update_layout"):
                if chart_type == "dual_axis":
                    themed[key] = style_dual_axis_chart(value)
                elif chart_type in {"comparison", "compare"}:
                    themed[key] = style_comparison_chart(value)
                else:
                    themed[key] = apply_plotly_theme(value)
            else:
                themed[key] = _theme_item(value)
        return themed
    if isinstance(item, list):
        return [_theme_item(value) for value in item]
    return item


def build_dashboard(charts):
    """Return a dashboard payload with theme applied to Plotly figures."""
    return {"dashboard": _theme_item(charts)}
