"""主题配置模块。
提供简洁企业级风格的色彩占位：白色背景、浅灰卡片、蓝色主色调。
仅用于内部引用，不改变业务逻辑。
"""


def get_theme():
    """返回企业风格主题配色。"""
    return {
        "primary": "#0B63CE",        # 企业蓝
        "secondary": "#5B9BD5",
        "background": "#FFFFFF",     # 白色背景
        "surface": "#F2F4F7",        # 浅灰色卡片背景
    }
