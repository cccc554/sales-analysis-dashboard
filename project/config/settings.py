"""应用配置模块。
包含全局参数加载和默认设置。"""
# 代码来源：AI生成
# 模块说明：配置模块，负责项目配置与主题样式。


# 函数说明：加载 load_settings 对应的配置或数据。
# 代码来源：AI生成
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
