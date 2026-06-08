"""Advanced chart helpers with shared dashboard theming."""

from config.theme import CHART_COLORS, PRIMARY, SECONDARY_BACKGROUND, apply_plotly_theme


CUSTOMER_HEATMAP_SCALE = [[0, SECONDARY_BACKGROUND], [1, PRIMARY]]


def apply_theme(chart, height=None):
    """Apply the global theme to a Plotly figure-like object."""
    if hasattr(chart, "update_layout"):
        return apply_plotly_theme(chart, height=height)
    return chart


def style_customer_segment_chart(fig):
    """Style customer segmentation bar or pie charts with the global color sequence."""
    if fig is None:
        return fig
    for index, trace in enumerate(getattr(fig, "data", [])):
        if getattr(trace, "type", "") == "pie":
            trace.update(marker=dict(colors=CHART_COLORS))
        else:
            trace.update(marker_color=CHART_COLORS[index % len(CHART_COLORS)])
    return apply_plotly_theme(fig)


def style_customer_value_chart(fig):
    """Style customer value distribution charts with the global color sequence."""
    return style_customer_segment_chart(fig)


def style_customer_behavior_heatmap(fig):
    """Style customer behavior heatmaps with the required light-gray to primary scale."""
    if fig is None:
        return fig
    for trace in getattr(fig, "data", []):
        trace.update(colorscale=CUSTOMER_HEATMAP_SCALE)
    return apply_plotly_theme(fig)


def build_advanced_chart(config):
    """Return the advanced chart payload with theme applied when possible."""
    if isinstance(config, dict):
        chart_type = config.get("type")
        for key in ("figure", "fig", "chart"):
            if key in config:
                if chart_type in {"customer_segment", "customer_segmentation"}:
                    config[key] = style_customer_segment_chart(config[key])
                elif chart_type in {"customer_value", "customer_value_distribution"}:
                    config[key] = style_customer_value_chart(config[key])
                elif chart_type in {"customer_behavior_heatmap", "heatmap"}:
                    config[key] = style_customer_behavior_heatmap(config[key])
                else:
                    config[key] = apply_theme(config[key])
    return {"chart": "advanced", "config": config}
