"""导航栏组件。
提供 MD3 风格导航项、全局语言切换入口和页面切换布局。"""
# 代码来源：AI生成
# 模块说明：组件模块，负责可复用界面组件渲染。


# 函数说明：渲染当前页面或组件。
# 代码来源：AI生成
def render(translator, current_page):
    """返回导航栏配置。"""
    return {
        "menu": [translator.translate(label) for label in ["首页", "数据中心", "销售分析", "客户分析"]],
        "active": current_page,
    }
