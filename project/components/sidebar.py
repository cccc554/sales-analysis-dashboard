"""侧边栏组件。
负责渲染页面侧边导航、主题说明和上传入口位置。"""


def render(translator):
    """返回侧边栏布局结构。"""
    return {
        "sections": [translator.translate("模块导航"), translator.translate("上传数据")],
    }
