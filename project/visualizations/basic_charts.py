"""Basic chart helpers with shared dashboard theming."""

from config.theme import ACCENT, PRIMARY, SUCCESS, WARNING, apply_plotly_theme


RFM_COLORS = [PRIMARY, ACCENT, SUCCESS, WARNING]


def apply_theme(chart, height=None):
    """Apply the global theme to a Plotly figure-like object."""
    if hasattr(chart, "update_layout"):
        return apply_plotly_theme(chart, height=height)
    return chart


def style_top_product_ranking(fig, top_count=None):
    """Style a top product bar chart: primary bars, first rank accent."""
    if fig is None:
        return fig
    colors = [PRIMARY] * int(top_count or 1)
    if colors:
        colors[0] = ACCENT
    fig.update_traces(marker_color=colors)
    return apply_plotly_theme(fig)


def style_rfm_scatter(fig):
    """Style an RFM scatter chart using the four business palette colors."""
    if fig is None:
        return fig
    for index, trace in enumerate(getattr(fig, "data", [])):
        trace.update(marker=dict(color=RFM_COLORS[index % len(RFM_COLORS)]))
    return apply_plotly_theme(fig)


def style_sales_trend(fig):
    """Style a sales trend line chart with primary line and soft fill."""
    if fig is None:
        return fig
    fig.update_traces(
        line=dict(color=PRIMARY, width=3),
        marker=dict(color=PRIMARY),
        fill="tozeroy",
        fillcolor="rgba(46,134,171,0.2)",
    )
    return apply_plotly_theme(fig)


def build_basic_chart(config):
    """Return the basic chart payload with theme applied when possible."""
    if isinstance(config, dict):
        chart_type = config.get("type")
        for key in ("figure", "fig", "chart"):
            if key in config:
                if chart_type == "top_product_ranking":
                    config[key] = style_top_product_ranking(config[key], config.get("top_count"))
                elif chart_type == "rfm_scatter":
                    config[key] = style_rfm_scatter(config[key])
                elif chart_type == "sales_trend":
                    config[key] = style_sales_trend(config[key])
                else:
                    config[key] = apply_theme(config[key])
    return {"chart": "basic", "config": config}
