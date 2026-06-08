"""Metric card data helpers."""

from config.theme import PRIMARY


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
