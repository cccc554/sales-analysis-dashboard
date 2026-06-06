"""数据集加载服务。
负责内置数据集映射和用户上传数据读取与元信息提取。"""

import os
from typing import Optional, Tuple
import pandas as pd

BASE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "datasets")


def get_builtin_catalog():
    """返回内置数据集目录信息（id -> folder path）。"""
    # Only keep e-commerce relevant built-in datasets
    return {
        "online_retail": os.path.join(BASE, "online_retail"),
        "online_retail_ii": os.path.join(BASE, "online_retail_ii"),
    }


def list_builtin_datasets():
    return list(get_builtin_catalog().keys())


def _find_first_csv(folder: str) -> Optional[str]:
    if not os.path.isdir(folder):
        return None
    for fname in os.listdir(folder):
        if fname.lower().endswith(".csv"):
            return os.path.join(folder, fname)
    return None


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
        df = pd.read_csv(csv_path, low_memory=False)
        meta.update({"status": "loaded", "path": csv_path, "rows": len(df), "columns": len(df.columns)})
        return df, meta
    except Exception as e:
        meta.update({"status": "error", "error": str(e)})
        return None, meta


def load_uploaded_file(uploaded_file) -> Tuple[Optional[pd.DataFrame], dict]:
    """从 `st.file_uploader` 返回的 file-like 对象读取成 DataFrame，并返回元信息。"""
    meta = {"filename": getattr(uploaded_file, "name", "uploaded")}
    import io

    filename = meta["filename"]
    content = uploaded_file.read()
    size = len(content)
    meta["size_bytes"] = size
    if size == 0:
        meta.update({"status": "empty_file", "error": "empty file"})
        return None, meta

    # try excel first
    try:
        lower = filename.lower()
        if lower.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(content))
        else:
            # try utf-8 then gbk
            try:
                df = pd.read_csv(io.BytesIO(content), encoding='utf-8')
            except Exception:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding='gbk')
                except Exception as e:
                    raise e

        # basic meta
        rows = len(df)
        cols = len(df.columns)
        missing_count = int(df.isnull().sum().sum())
        duplicate_rows = int(df.duplicated().sum()) if rows > 0 else 0
        duplicate_rate = duplicate_rows / rows if rows > 0 else 0
        all_empty_cols = [c for c in df.columns if df[c].isnull().all()]
        duplicate_colnames = df.columns[df.columns.duplicated()].tolist()

        meta.update({
            "status": "loaded",
            "rows": rows,
            "columns": cols,
            "missing_count": missing_count,
            "duplicate_rows": duplicate_rows,
            "duplicate_rate": duplicate_rate,
            "all_empty_columns": all_empty_cols,
            "duplicate_column_names": duplicate_colnames,
        })
        return df, meta
    except Exception as e:
        meta.update({"status": "error", "error": str(e)})
        return None, meta
