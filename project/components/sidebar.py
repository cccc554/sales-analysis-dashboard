"""侧边栏组件。
负责渲染页面侧边导航、主题说明和上传入口位置。"""
# 代码来源：AI生成
# 模块说明：组件模块，负责可复用界面组件渲染。


# 函数说明：渲染当前页面或组件。
# 代码来源：AI生成
def render(translator):
    """返回侧边栏布局结构。"""
    return {
        "sections": [translator.translate("模块导航"), translator.translate("上传数据")],
    }
