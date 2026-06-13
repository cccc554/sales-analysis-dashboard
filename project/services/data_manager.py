"""数据管理层。
提供保存/读取当前数据集、计算元信息与列类型检测的工具。
"""
# 代码来源：AI生成 + 学生修改
# 模块说明：服务模块，负责数据、模型或通用业务能力封装。

import streamlit as st
import pandas as pd
from typing import Dict, Any


# 函数说明：处理 detect_columns 相关逻辑。
# 代码来源：AI生成 + 学生修改
def detect_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """检测列类型并统计数值/类别/日期列。"""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["category", "object"]).columns.tolist()
    datetime_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]

    # 对于 object 列，尝试解析为日期（采样）
    for c in df.select_dtypes(include=["object"]).columns:
        sample = df[c].dropna().head(100)
        if not sample.empty:
            parsed = pd.to_datetime(sample, errors="coerce")
            non_na = parsed.notna().sum()
            if non_na / len(sample) > 0.5:
                datetime_cols.append(c)
    # 移除 datetime cols from categorical if overlap
    categorical_cols = [c for c in categorical_cols if c not in datetime_cols]

    return {
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "datetime_columns": datetime_cols,
        "numeric_count": len(numeric_cols),
        "categorical_count": len(categorical_cols),
        "datetime_count": len(datetime_cols),
    }


# 函数说明：计算 _compute_quality_score 对应的业务指标。
# 代码来源：AI生成 + 学生修改
def _compute_quality_score(meta: Dict[str, Any]) -> int:
    """根据缺失率、重复率等生成 0-100 的质量评分，启发式。"""
    rows = meta.get("rows", 0)
    cols = meta.get("columns", 0)
    if rows == 0 or cols == 0:
        return 0

    missing_rate = meta.get("missing_rate", 0)
    duplicate_rate = meta.get("duplicate_rate", 0)
    numeric_ratio = meta.get("numeric_count", 0) / max(cols, 1)

    score = 100
    score -= missing_rate * 50
    score -= duplicate_rate * 30
    # 少量数值列可能影响分析，略微扣分
    score += (numeric_ratio - 0.5) * 10
    # clamp
    score = int(max(0, min(100, score)))
    return score


# 函数说明：处理 save_dataset 相关逻辑。
# 代码来源：AI生成 + 学生修改
def save_dataset(name: str, df: pd.DataFrame, source: Dict[str, Any]) -> None:
    """保存数据集到会话并生成 meta 信息。"""
    rows = len(df)
    cols = len(df.columns)
    missing_count = int(df.isnull().sum().sum())
    total_cells = rows * cols if rows * cols > 0 else 1
    missing_rate = missing_count / total_cells
    duplicate_rows = int(df.duplicated().sum()) if rows > 0 else 0
    duplicate_rate = duplicate_rows / rows if rows > 0 else 0
    memory_bytes = int(df.memory_usage(deep=True).sum())

    col_info = detect_columns(df)

    meta = {
        "name": name,
        "source": source,
        "rows": rows,
        "columns": cols,
        "missing_count": missing_count,
        "missing_rate": missing_rate,
        "duplicate_rows": duplicate_rows,
        "duplicate_rate": duplicate_rate,
        "numeric_count": col_info.get("numeric_count", 0),
        "categorical_count": col_info.get("categorical_count", 0),
        "datetime_count": col_info.get("datetime_count", 0),
        "memory_bytes": memory_bytes,
        "dtypes": df.dtypes.apply(lambda x: x.name).to_dict(),
        "describe": df.describe(include="all").to_dict(),
    }

    meta["quality_score"] = _compute_quality_score(meta)
    meta.update(col_info)

    st.session_state["current_dataset"] = {"name": name, "df": df, "meta": meta}


# 函数说明：处理 get_current_dataset 相关逻辑。
# 代码来源：AI生成 + 学生修改
def get_current_dataset():
    return st.session_state.get("current_dataset")


# 函数说明：处理 get_dataset_meta 相关逻辑。
# 代码来源：AI生成 + 学生修改
def get_dataset_meta():
    cur = get_current_dataset()
    return cur.get("meta") if cur else None
