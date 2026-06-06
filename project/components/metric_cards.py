"""指标卡片组件。
定义关键指标展示卡片的接口和描述。"""


def build_cards(metrics, translator):
    """返回卡片数据结构。"""
    return [{"label": translator.translate(name), "value": value} for name, value in metrics.items()]
