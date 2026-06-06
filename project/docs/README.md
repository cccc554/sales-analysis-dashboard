# 电商数据分析平台大作业骨架

本项目为 Python Streamlit 电商数据分析平台的大作业骨架结构，包含中英双语、MD3 风格、内置数据集、用户上传、AI 助手、可视化和预测分析模块。

## 目录说明

- `app.py`: 主入口，负责页面路由与全局配置。
- `pages/`: 各个页面逻辑骨架，按功能拆分，便于独立开发。
- `components/`: 可复用界面组件，支持导航、侧边栏、语言切换和图表占位。
- `services/`: 工具服务层，负责翻译、数据加载、预处理、AI 聊天和预测接口。
- `analysis/`: 分析模块骨架，按功能拆分，单独实现计算逻辑。
- `visualizations/`: 可视化组件骨架，区分基础、进阶和仪表盘图表。
- `datasets/`: 内置数据集目录，用于存放真实数据文件。
- `config/`: 应用设置与主题配置。
- `assets/`: 资源目录，用于图标、图片和样式文件。
- `docs/`: 文档与大作业材料模板。

## 后续开发建议顺序

1. `config/` 与 `services/translator.py`：先搭建全站语言开关与主题配置。
2. `app.py` 与 `components/`：构建全局布局、导航和侧边栏。
3. `pages/`：按页面逐一实现渲染逻辑，从 `home`、`dataset_center` 开始。
4. `services/dataset_loader.py` 与 `services/preprocessing.py`：完成数据加载与预处理基础。
5. `analysis/`：实现各分析模块的计算接口。
6. `visualizations/`：补齐图表组件并与分析结果结合。
7. `services/chat_service.py`：接入 AI 聊天助手。
8. `services/forecast_service.py` 与 `pages/forecast_analysis.py`：完成预测分析功能。

## 设计原则

- 每个模块保持单一职责，便于独立开发。
- 页面与服务分离，页面负责显示，服务负责业务逻辑。
- 所有文件当前为骨架，后续可逐步补充实现。
