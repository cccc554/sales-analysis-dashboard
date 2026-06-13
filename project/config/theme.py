"""Central visual theme for the retail BI dashboard."""
# 代码来源：AI生成 + 学生修改
# 模块说明：配置模块，负责项目配置与主题样式。

PRIMARY = "#2E86AB"
ACCENT = "#A23B72"
SUCCESS = "#2C8C5A"
WARNING = "#D95B5B"
BACKGROUND = "#FFFFFF"
SECONDARY_BACKGROUND = "#F5F7FA"
TEXT = "#1E293B"
MUTED_TEXT = "#64748B"
BORDER = "#E2E8F0"
CARD = "#FFFFFF"
CHART_COLORS = [PRIMARY, ACCENT, SUCCESS, WARNING, MUTED_TEXT]
CHART_GRADIENT = ["#F5F7FA", "#EAF1F7", "#DCEAF3", "#9FC9DA", PRIMARY, "#557AA9", ACCENT]
BLUE_GRADIENT = ["#EEF6FF", "#D6EBFF", "#AED6FF", "#76B7F2", "#2E86AB", "#1D5F87"]
ACCENT_GRADIENT = ["#FFF1F8", "#F6D4E5", "#E9A8C8", "#D77BA9", ACCENT, "#6F2B56"]
PRIMARY_FILL = "rgba(46,134,171,0.18)"
SHADOW = "0 10px 28px rgba(30, 41, 59, 0.08)"


# 函数说明：处理 get_theme 相关逻辑。
# 代码来源：AI生成 + 学生修改
def get_theme():
    """Return the dashboard theme as a plain dictionary."""
    return {
        "primary": PRIMARY,
        "accent": ACCENT,
        "success": SUCCESS,
        "warning": WARNING,
        "background": BACKGROUND,
        "secondary_background": SECONDARY_BACKGROUND,
        "surface": CARD,
        "card": CARD,
        "text": TEXT,
        "muted_text": MUTED_TEXT,
        "border": BORDER,
        "chart_colors": CHART_COLORS,
        "chart_gradient": CHART_GRADIENT,
        "blue_gradient": BLUE_GRADIENT,
        "accent_gradient": ACCENT_GRADIENT,
        "primary_fill": PRIMARY_FILL,
        "shadow": SHADOW,
    }


# 函数说明：处理 get_global_css 相关逻辑。
# 代码来源：AI生成 + 学生修改
def get_global_css() -> str:
    """Return global Streamlit CSS for the professional business theme."""
    return f"""
<style>
:root {{
    --bi-primary: {PRIMARY};
    --bi-accent: {ACCENT};
    --bi-success: {SUCCESS};
    --bi-warning: {WARNING};
    --bi-bg: {BACKGROUND};
    --bi-bg-secondary: {SECONDARY_BACKGROUND};
    --bi-card: {CARD};
    --bi-border: {BORDER};
    --bi-text: {TEXT};
    --bi-muted: {MUTED_TEXT};
    --bi-shadow: {SHADOW};
}}
[data-testid="stAppViewContainer"] {{
    background:
        radial-gradient(circle at 18% 12%, rgba(46, 134, 171, 0.24), transparent 32%),
        radial-gradient(circle at 86% 18%, rgba(162, 59, 114, 0.16), transparent 30%),
        linear-gradient(135deg, #DDE7F0 0%, #EEF3F7 42%, #F8FAFC 100%);
}}
[data-testid="stSidebarNav"] {{
    display: none;
}}
[data-testid="stSidebar"] {{
    background: #1E293B;
}}
[data-testid="stSidebar"] * {{
    color: #FFFFFF;
}}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
    color: #CBD5E1;
}}
.block-container {{
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1480px;
}}
/* Main content background - light gray gradient */
.main .block-container {{
    background:
        radial-gradient(circle at 8% 0%, rgba(255, 255, 255, 0.86), transparent 32%),
        radial-gradient(circle at 92% 6%, rgba(46, 134, 171, 0.11), transparent 30%),
        linear-gradient(135deg, rgba(245, 247, 250, 0.96) 0%, rgba(255, 255, 255, 0.88) 58%, rgba(238, 243, 247, 0.94) 100%);
    padding: 2rem;
    border-radius: 12px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78);
}}
@keyframes biFadeInUp {{
    from {{
        opacity: 0;
        transform: translateY(10px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}
[data-testid="stPlotlyChart"],
div[data-testid="stMetric"],
.chart-panel,
.sales-kpi-card,
.home-kpi-card,
.home-summary-card,
.home-module-card,
.dataset-card,
.upload-card,
.about-card,
.ai-panel,
.ai-card {{
    animation: biFadeInUp .42s ease both;
}}
@keyframes biBarGrow {{
    from {{
        opacity: .18;
        transform: scaleY(.08);
        transform-origin: bottom;
    }}
    to {{
        opacity: 1;
        transform: scaleY(1);
        transform-origin: bottom;
    }}
}}
@keyframes biLineDraw {{
    from {{
        opacity: .35;
        transform: scaleX(.02);
    }}
    to {{
        opacity: 1;
        transform: scaleX(1);
    }}
}}
@keyframes biPieReveal {{
    from {{
        opacity: .2;
        transform: rotate(-24deg) scale(.96);
    }}
    to {{
        opacity: 1;
        transform: rotate(0deg) scale(1);
    }}
}}
@keyframes biTreemapReveal {{
    from {{
        opacity: 0;
        transform: scale(.985);
    }}
    to {{
        opacity: 1;
        transform: scale(1);
    }}
}}
[data-testid="stPlotlyChart"] .barlayer .trace path {{
    animation: biBarGrow .82s cubic-bezier(.2, .72, .2, 1) both;
}}
[data-testid="stPlotlyChart"] .scatterlayer .trace {{
    transform-box: fill-box;
    transform-origin: left center;
    animation: biLineDraw 1s ease-out both;
}}
[data-testid="stPlotlyChart"] .scatterlayer .js-line {{
    stroke-dasharray: none !important;
    stroke-dashoffset: 0 !important;
}}
[data-testid="stPlotlyChart"] .pielayer .trace {{
    transform-origin: center;
    animation: biPieReveal .82s ease-out both;
}}
[data-testid="stPlotlyChart"] .treemaplayer g {{
    transform-origin: center;
    animation: biTreemapReveal .72s ease-out both;
}}
[data-testid="stPlotlyChart"] .treemaplayer g:nth-child(2) {{
    animation-delay: .08s;
}}
[data-testid="stPlotlyChart"] .treemaplayer g:nth-child(3) {{
    animation-delay: .14s;
}}
[data-testid="stPlotlyChart"] .treemaplayer g:nth-child(4) {{
    animation-delay: .2s;
}}
h1, h2, h3 {{
    color: var(--bi-text);
    font-weight: 700 !important;
    letter-spacing: 0;
}}
p, label, span, div {{
    font-weight: 400;
}}
.bi-sidebar-logo {{
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 16px;
    padding: 18px 16px;
    margin: 0 0 18px 0;
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT});
    box-shadow: 0 14px 32px rgba(46, 134, 171, 0.22);
}}
.bi-sidebar-logo .mark {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.16);
    color: #FFFFFF;
    font-weight: 700;
    margin-bottom: 10px;
}}
.bi-sidebar-logo .title {{
    color: #FFFFFF;
    font-size: 1.02rem;
    font-weight: 700;
    line-height: 1.35;
}}
.bi-sidebar-logo .subtitle {{
    color: #E2E8F0;
    font-size: 0.82rem;
    margin-top: 4px;
}}
.bi-nav-group {{
    margin: 18px 0 8px 0;
    color: #BAE6FD;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}}
[data-testid="stSidebar"] div.stButton > button {{
    border-radius: 12px;
    border: 1px solid rgba(226, 232, 240, 0.18);
    background: rgba(30, 41, 59, 0.32);
    color: #FFFFFF;
    min-height: 42px;
    justify-content: flex-start;
    transition: all .16s ease;
}}
[data-testid="stSidebar"] div.stButton > button:hover {{
    border-color: rgba(46, 134, 171, 0.78);
    background: rgba(46, 134, 171, 0.24);
}}
[data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
    background: linear-gradient(135deg, {PRIMARY}, {ACCENT});
    color: #FFFFFF;
    border-color: rgba(255, 255, 255, 0.16);
}}
div[data-testid="stMetric"] {{
    background: var(--bi-card);
    border: 1px solid var(--bi-border);
    border-radius: 16px;
    padding: 18px 18px;
    box-shadow: var(--bi-shadow);
    transition: transform .16s ease, box-shadow .16s ease;
}}
/* Metric cards with subtle floating effect */
[data-testid="stMetric"] {{
    background-color: white;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    padding: 1rem;
}}
div[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 16px 38px rgba(30, 41, 59, 0.12);
}}
div[data-testid="stMetricLabel"] {{
    color: var(--bi-muted);
}}
div[data-testid="stMetricValue"] {{
    color: var(--bi-primary);
    font-weight: 700;
}}
div.stButton > button {{
    border-radius: 12px;
    border-color: var(--bi-border);
}}
div.stButton > button[kind="primary"] {{
    background: var(--bi-primary);
    border-color: var(--bi-primary);
    color: #FFFFFF !important;
}}
div.stButton > button[kind="secondary"] {{
    background: #FFFFFF;
    border: 1px solid var(--bi-border);
    color: var(--bi-text);
}}
div.stButton > button[kind="secondary"]:hover {{
    border-color: var(--bi-primary);
    color: var(--bi-primary);
}}
[data-testid="stDataFrame"], [data-testid="stTable"] {{
    border-radius: 16px;
    overflow: hidden;
}}
</style>
"""


# 函数说明：处理 apply_plotly_theme 相关逻辑。
# 代码来源：AI生成 + 学生修改
def apply_plotly_theme(fig, height: int | None = None):
    """Apply the shared BI theme to a Plotly figure and return it."""
    if fig is None:
        return fig

    layout_updates = {
        "template": "plotly_white",
        "paper_bgcolor": BACKGROUND,
        "plot_bgcolor": BACKGROUND,
        "font": {"color": TEXT, "family": "Arial", "size": 12},
        "colorway": CHART_COLORS,
        "hoverlabel": {
            "bgcolor": CARD,
            "bordercolor": BORDER,
            "font": {"color": TEXT, "family": "Arial", "size": 12},
        },
        "margin": {"t": 55, "l": 24, "r": 20, "b": 30},
        "legend": {
            "font": {"size": 11, "color": MUTED_TEXT},
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        },
    }
    if height is not None:
        layout_updates["height"] = height

    fig.update_layout(**layout_updates)
    fig.update_xaxes(
        showgrid=True,
        gridcolor=BORDER,
        zeroline=False,
        linecolor=BORDER,
        tickfont={"color": MUTED_TEXT},
        title_font={"color": MUTED_TEXT},
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=BORDER,
        zeroline=False,
        linecolor=BORDER,
        tickfont={"color": MUTED_TEXT},
        title_font={"color": MUTED_TEXT},
    )
    return fig
