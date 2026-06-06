"""语言切换组件。
实现全站中英切换的界面入口和状态管理骨架。"""


def get_languages():
    """返回支持语言列表。"""
    return ["zh", "en"]


def render(current_language):
    """输出语言切换项。"""
    return {
        "current": current_language,
        "options": get_languages(),
    }
