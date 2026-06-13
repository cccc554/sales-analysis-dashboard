"""语言切换组件。
实现全站中英切换的界面入口和状态管理骨架。"""
# 代码来源：AI生成
# 模块说明：组件模块，负责可复用界面组件渲染。


# 函数说明：处理 get_languages 相关逻辑。
# 代码来源：AI生成
def get_languages():
    """返回支持语言列表。"""
    return ["zh", "en"]


# 函数说明：渲染当前页面或组件。
# 代码来源：AI生成
def render(current_language):
    """输出语言切换项。"""
    return {
        "current": current_language,
        "options": get_languages(),
    }
