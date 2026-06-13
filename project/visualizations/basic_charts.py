"""Basic chart helpers with shared dashboard theming."""
# 代码来源：AI生成
# 模块说明：可视化模块，负责图表样式与构建。

from config.theme import ACCENT, PRIMARY, PRIMARY_FILL, SUCCESS, WARNING, apply_plotly_theme


RFM_COLORS = [PRIMARY, ACCENT, SUCCESS, WARNING]


# 函数说明：处理 apply_theme 相关逻辑。
# 代码来源：AI生成
def apply_theme(chart, height=None):
    """Apply the global theme to a Plotly figure-like object."""
    if hasattr(chart, "update_layout"):
        return apply_plotly_theme(chart, height=height)
    return chart


# 函数说明：处理 style_top_product_ranking 相关逻辑。
# 代码来源：AI生成
def style_top_product_ranking(fig, top_count=None):
    """Style a top product bar chart with the accent business color."""
    if fig is None:
        return fig
    fig.update_traces(marker_color=ACCENT)
    return apply_plotly_theme(fig)


# 函数说明：处理 style_rfm_scatter 相关逻辑。
# 代码来源：AI生成
def style_rfm_scatter(fig):
    """Style an RFM scatter chart using the four business palette colors."""
    if fig is None:
        return fig
    for index, trace in enumerate(getattr(fig, "data", [])):
        trace.update(marker=dict(color=RFM_COLORS[index % len(RFM_COLORS)]))
    return apply_plotly_theme(fig)


# 函数说明：处理 style_sales_trend 相关逻辑。
# 代码来源：AI生成
def style_sales_trend(fig):
    """Style a sales trend line chart with primary line and soft fill."""
    if fig is None:
        return fig
    fig.update_traces(
        line=dict(color=PRIMARY, width=3),
        marker=dict(color=PRIMARY),
        fill="tozeroy",
        fillcolor=PRIMARY_FILL,
    )
    return apply_plotly_theme(fig)


# 函数说明：构建 build_basic_chart 所需的数据结构或界面内容。
# 代码来源：AI生成
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
