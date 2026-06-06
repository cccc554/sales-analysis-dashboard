"""应用配置模块。
包含全局参数加载和默认设置。"""


def load_settings():
    """返回应用默认设置。"""
    return {
        "default_language": "en",
        "theme": "enterprise",
        "available_pages": [
            "home",
            "dataset_center",
            "sales_analysis",
            "customer_analysis",
            "product_analysis",
            "market_basket_analysis",
            "forecast_analysis",
            "ai_assistant",
            "about",
        ],
    }
