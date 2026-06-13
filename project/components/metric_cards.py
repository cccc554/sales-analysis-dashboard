"""Metric card data helpers."""
# 代码来源：AI生成
# 模块说明：组件模块，负责可复用界面组件渲染。

from config.theme import PRIMARY


# 函数说明：构建 build_cards 所需的数据结构或界面内容。
# 代码来源：AI生成
def build_cards(metrics, translator):
    """Return metric card data with themed value color."""
    return [
        {
            "label": translator.translate(name),
            "value": value,
            "value_color": PRIMARY,
        }
        for name, value in metrics.items()
    ]
