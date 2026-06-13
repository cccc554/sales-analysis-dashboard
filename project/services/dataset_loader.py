"""数据集加载服务。
负责内置数据集映射和用户上传数据读取与元信息提取。"""
# 代码来源：AI生成 + 学生修改
# 模块说明：服务模块，负责数据、模型或通用业务能力封装。

import io
import os
from typing import Optional, Tuple
import pandas as pd
import streamlit as st

BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets")
DATA_LOAD_CACHE_TTL_SECONDS = 3600
UPLOAD_PARSE_CACHE_TTL_SECONDS = 1800
SUPPORTED_UPLOAD_EXTENSIONS = (".csv", ".xls", ".xlsx")


UPLOAD_ERROR_DETAIL = {
    "en": {
        "invalid_format": "Unsupported file extension. Only .csv, .xls, and .xlsx files can be parsed.",
        "empty_file": "The uploaded file is empty and contains no readable bytes.",
        "empty_dataset": "The uploaded file was parsed, but no valid rows or columns were found.",
        "encoding_failed": "CSV decoding failed with utf-8, utf-8-sig, and GBK. Please save the file as utf-8 or GBK and upload again.",
        "parse_failed": "The file parser raised an exception. Please check whether the file content matches its extension and has a valid header row.",
        "read_failed": "The uploaded file stream could not be read.",
    },
    "zh": {
        "invalid_format": "文件扩展名不支持，当前仅能解析 .csv、.xls、.xlsx 文件。",
        "empty_file": "上传文件为空，没有可读取的字节内容。",
        "empty_dataset": "文件已完成解析，但未发现有效的数据行或数据列。",
        "encoding_failed": "CSV 使用 utf-8、utf-8-sig、GBK 均解码失败，建议另存为 utf-8 或 GBK 后重新上传。",
        "parse_failed": "文件解析器抛出异常，请检查文件内容是否与扩展名一致，并确认存在有效表头。",
        "read_failed": "无法读取上传文件流。",
    },
}


# 函数说明：处理 get_builtin_catalog 相关逻辑。
# 代码来源：AI生成 + 学生修改
def get_builtin_catalog():
    """返回内置数据集目录信息（id -> folder path）。"""
    # Only keep e-commerce relevant built-in datasets
    return {
        "online_retail": os.path.join(BASE, "online_retail"),
        "online_retail_ii": os.path.join(BASE, "online_retail_ii"),
    }


# 函数说明：处理 list_builtin_datasets 相关逻辑。
# 代码来源：AI生成 + 学生修改
def list_builtin_datasets():
    return list(get_builtin_catalog().keys())


# 函数说明：处理 _lang 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _lang() -> str:
    language = str(st.session_state.get("language", "en")).lower()
    return "zh" if language.startswith("zh") else "en"


# 函数说明：处理 _detail 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _detail(key: str, lang: Optional[str] = None) -> str:
    # Keep low-level error details localized for upstream pages.
    bundle = UPLOAD_ERROR_DETAIL.get(lang or _lang(), UPLOAD_ERROR_DETAIL["en"])
    return bundle.get(key, key)


# 函数说明：查找 _find_first_csv 相关字段或资源。
# 代码来源：AI生成 + 学生修改
def _find_first_csv(folder: str) -> Optional[str]:
    if not os.path.isdir(folder):
        return None
    for fname in os.listdir(folder):
        if fname.lower().endswith(".csv"):
            return os.path.join(folder, fname)
    return None


# 函数说明：处理 _read_builtin_csv 相关逻辑。
# 代码来源：AI生成 + 学生修改
@st.cache_data(ttl=DATA_LOAD_CACHE_TTL_SECONDS, show_spinner=False)
def _read_builtin_csv(csv_path: str, modified_time: float) -> pd.DataFrame:
    return pd.read_csv(csv_path, low_memory=False)


# 函数说明：加载 load_builtin 对应的配置或数据。
# 代码来源：AI生成 + 学生修改
def load_builtin(name: str) -> Tuple[Optional[pd.DataFrame], dict]:
    """尝试加载内置数据集的第一个 CSV 文件，返回 (DataFrame, meta)。

    如果不存在 CSV，返回 (None, meta)。
    """
    catalog = get_builtin_catalog()
    folder = catalog.get(name)
    meta = {"name": name}
    if not folder:
        meta.update({"status": "not_found"})
        return None, meta

    csv_path = _find_first_csv(folder)
    if not csv_path:
        # 尝试对特定数据集触发下载脚本（例如 online_retail）
        if name == 'online_retail':
            try:
                import scripts.download_online_retail as dl

                dl.main()
                csv_path = _find_first_csv(folder)
            except Exception:
                pass
        if name == 'online_retail_ii':
            try:
                import scripts.download_online_retail_ii as dl2

                dl2.main()
                csv_path = _find_first_csv(folder)
            except Exception:
                pass

        if not csv_path:
            meta.update({"status": "no_csv"})
            return None, meta

    try:
        df = _read_builtin_csv(csv_path, os.path.getmtime(csv_path))
        meta.update({"status": "loaded", "path": csv_path, "rows": len(df), "columns": len(df.columns)})
        return df, meta
    except Exception as e:
        meta.update({"status": "error", "error": str(e)})
        return None, meta


# 函数说明：构建 _build_loaded_meta 所需的数据结构或界面内容。
# 代码来源：AI生成 + 学生修改
def _build_loaded_meta(df: pd.DataFrame) -> dict:
    rows = len(df)
    cols = len(df.columns)
    missing_count = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum()) if rows > 0 else 0
    duplicate_rate = duplicate_rows / rows if rows > 0 else 0
    all_empty_cols = [c for c in df.columns if df[c].isnull().all()]
    duplicate_colnames = df.columns[df.columns.duplicated()].tolist()

    return {
        "status": "loaded",
        "rows": rows,
        "columns": cols,
        "missing_count": missing_count,
        "duplicate_rows": duplicate_rows,
        "duplicate_rate": duplicate_rate,
        "all_empty_columns": all_empty_cols,
        "duplicate_column_names": duplicate_colnames,
    }


# 函数说明：处理 _parse_uploaded_content 相关逻辑。
# 代码来源：AI生成 + 学生修改
@st.cache_data(ttl=UPLOAD_PARSE_CACHE_TTL_SECONDS, show_spinner=False)
def _parse_uploaded_content(filename: str, content: bytes, lang: str) -> Tuple[Optional[pd.DataFrame], dict]:
    lower = filename.lower()
    if not lower.endswith(SUPPORTED_UPLOAD_EXTENSIONS):
        return None, {
            "status": "invalid_format",
            "error_key": "invalid_file_format",
            "detail": _detail("invalid_format", lang),
        }

    try:
        if lower.endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = None
            last_error = None
            for encoding in ("utf-8", "utf-8-sig", "gbk"):
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                    break
                except Exception as e:
                    last_error = e
            if df is None:
                return None, {
                    "status": "encoding_failed",
                    "error_key": "upload_encoding_failed",
                    "error": str(last_error),
                    "detail": _detail("encoding_failed", lang),
                }
    except Exception as e:
        return None, {
            "status": "parse_failed",
            "error_key": "upload_parse_failed",
            "error": str(e),
            "detail": _detail("parse_failed", lang),
        }

    if df is None or df.empty or len(df.columns) == 0:
        return None, {
            "status": "empty_dataset",
            "error_key": "empty_dataset",
            "detail": _detail("empty_dataset", lang),
        }

    return df, _build_loaded_meta(df)


# 函数说明：加载 load_uploaded_file 对应的配置或数据。
# 代码来源：AI生成 + 学生修改
def load_uploaded_file(uploaded_file) -> Tuple[Optional[pd.DataFrame], dict]:
    """从 `st.file_uploader` 返回的 file-like 对象读取成 DataFrame，并返回元信息。"""
    meta = {"filename": getattr(uploaded_file, "name", "uploaded")}

    try:
        content = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    except Exception as e:
        meta.update({
            "status": "read_failed",
            "error_key": "upload_error",
            "error": str(e),
            "detail": _detail("read_failed"),
        })
        return None, meta

    size = len(content)
    meta["size_bytes"] = size
    if size == 0:
        meta.update({
            "status": "empty_file",
            "error_key": "empty_file",
            "error": "empty file",
            "detail": _detail("empty_file"),
        })
        return None, meta

    df, parsed_meta = _parse_uploaded_content(meta["filename"], content, _lang())
    meta.update(parsed_meta)
    return df, meta
