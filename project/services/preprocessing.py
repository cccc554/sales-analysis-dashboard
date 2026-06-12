"""预处理服务。
定义数据清洗、特征工程和数据准备的接口。"""

import streamlit as st


@st.cache_data(ttl=1800, show_spinner=False)
def preprocess(data):
    """数据预处理占位函数。"""
    return {"data": data, "status": "ready_for_analysis"}
