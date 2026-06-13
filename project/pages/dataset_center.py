"""Dataset Center page."""
# 代码来源：AI生成 + 学生修改
# 模块说明：页面模块，负责对应 Streamlit 页面渲染与交互。

import streamlit as st

from services import data_manager, dataset_loader
from services.translator import t


DATASET_CSS = """
<style>
.dataset-card {
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 20px;
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
    min-height: 220px;
}
.dataset-card .source {
    color: #2E86AB;
    font-weight: 700;
    margin-bottom: 10px;
}
.dataset-card .desc {
    color: #64748B;
    line-height: 1.55;
    min-height: 74px;
}
.dataset-meta-row {
    display: flex;
    gap: 10px;
    margin: 14px 0;
}
.dataset-meta-item {
    flex: 1;
    border-radius: 12px;
    background: #F5F7FA;
    border: 1px solid #E2E8F0;
    padding: 10px;
}
.dataset-meta-item .label {
    color: #64748B;
    font-size: 0.78rem;
}
.dataset-meta-item .value {
    color: #1E293B;
    font-weight: 700;
    margin-top: 4px;
}
.upload-zone {
    border: 2px dashed #2E86AB;
    border-radius: 16px;
    padding: 28px;
    background: linear-gradient(180deg, #F5F7FA, #FFFFFF);
    text-align: center;
    margin-bottom: 12px;
}
.upload-zone .title {
    color: #1E293B;
    font-size: 1.15rem;
    font-weight: 700;
}
.upload-zone .hint {
    color: #64748B;
    margin-top: 6px;
}
.file-info-card {
    border: 1px solid #E2E8F0;
    border-radius: 16px;
    padding: 18px;
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
}
</style>
"""

UPLOAD_VALIDATION_TEXT = {
    "en": {
        "guide": "Choose a built-in dataset or upload a CSV/XLS/XLSX file, then review the preview before analysis.",
        "parsing": "Parsing uploaded dataset...",
        "saving": "Saving dataset to session...",
        "few_rows": "The uploaded dataset has only {rows} rows. Analysis results may be less stable.",
        "empty_columns": "The uploaded dataset contains all-empty columns: {columns}. They will be kept, but you may want to clean them later.",
        "missing_core_fields": "The uploaded dataset does not contain recognizable product, order, quantity, price, or date fields. Please upload an e-commerce transaction dataset.",
    },
    "zh": {
        "guide": "可选择内置数据集，或上传 CSV/XLS/XLSX 文件，保存后先检查数据预览再分析。",
        "parsing": "正在解析上传数据集...",
        "saving": "正在保存数据集到会话...",
        "few_rows": "上传数据集仅有 {rows} 行，分析结果可能不够稳定。",
        "empty_columns": "上传数据集中存在全空列：{columns}。系统会保留这些列，建议后续清洗。",
        "missing_core_fields": "上传数据集中未识别到商品、订单、数量、价格、日期任一核心业务字段，请上传电商交易类数据集。",
    },
}

MIN_RECOMMENDED_ROWS = 10


# 函数说明：格式化 _format_count 相关展示数据。
# 代码来源：AI生成 + 学生修改
def _format_count(value) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return t("not_available")


# 函数说明：格式化 _format_bytes 相关展示数据。
# 代码来源：AI生成 + 学生修改
def _format_bytes(value) -> str:
    try:
        size = float(value)
    except Exception:
        return t("not_available")
    units = ["B", "KB", "MB", "GB"]
    idx = 0
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    return f"{size:,.2f} {units[idx]}"


# 函数说明：处理 _lang 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _lang() -> str:
    language = str(st.session_state.get("language", "en")).lower()
    return "zh" if language.startswith("zh") else "en"


# 函数说明：处理 _txt 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _txt(key: str, **kwargs) -> str:
    value = UPLOAD_VALIDATION_TEXT.get(_lang(), UPLOAD_VALIDATION_TEXT["en"]).get(key, key)
    return value.format(**kwargs) if kwargs else value


# 函数说明：查找 _find_column 相关字段或资源。
# 代码来源：AI生成 + 学生修改
def _find_column(df, candidates):
    cols = list(df.columns)
    lower_map = {str(c).lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    for col in cols:
        col_low = str(col).lower()
        for cand in candidates:
            if cand.lower() in col_low:
                return col
    return None


# 函数说明：处理 _dataset_card 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _dataset_card(name: str, source: str, desc: str, rows, columns):
    st.markdown(
        f"""
        <div class="dataset-card">
            <h3>{name}</h3>
            <div class="source">{source}</div>
            <div class="desc">{desc}</div>
            <div class="dataset-meta-row">
                <div class="dataset-meta-item">
                    <div class="label">{t("rows")}</div>
                    <div class="value">{_format_count(rows) if rows is not None else t("not_available")}</div>
                </div>
                <div class="dataset-meta-item">
                    <div class="label">{t("columns")}</div>
                    <div class="value">{_format_count(columns) if columns is not None else t("not_available")}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 函数说明：处理 _file_info 相关逻辑。
# 代码来源：AI生成 + 学生修改
def _file_info(meta: dict):
    st.markdown(
        f"""
        <div class="file-info-card">
            <h3>{t("dataset_file_info")}</h3>
            <div class="dataset-meta-row">
                <div class="dataset-meta-item">
                    <div class="label">{t("dataset_name")}</div>
                    <div class="value">{meta.get("name", t("not_available"))}</div>
                </div>
                <div class="dataset-meta-item">
                    <div class="label">{t("rows")}</div>
                    <div class="value">{_format_count(meta.get("rows"))}</div>
                </div>
                <div class="dataset-meta-item">
                    <div class="label">{t("columns")}</div>
                    <div class="value">{_format_count(meta.get("columns"))}</div>
                </div>
                <div class="dataset-meta-item">
                    <div class="label">{t("dataset_data_size")}</div>
                    <div class="value">{_format_bytes(meta.get("memory_bytes"))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# 函数说明：渲染 _render_upload_error 对应的界面内容。
# 代码来源：AI生成 + 学生修改
def _render_upload_error(meta: dict):
    # Reuse loader metadata so upload errors stay specific and localized.
    status = meta.get("status")
    error_key = meta.get("error_key")
    error_text = str(meta.get("error", "")).lower()

    if status == "invalid_format" or error_key == "invalid_file_format":
        st.warning(t("invalid_file_format"))
    elif status in {"empty_file", "empty_dataset"} or error_key in {"empty_file", "empty_dataset"}:
        st.warning(t("empty_dataset"))
    elif status == "encoding_failed" or error_key == "upload_encoding_failed" or "codec" in error_text or "decode" in error_text:
        st.error(t("upload_encoding_failed"))
    elif status == "parse_failed" or error_key == "upload_parse_failed":
        st.error(t("upload_parse_failed"))
    else:
        st.error(t(error_key or "upload_error"))


# 函数说明：校验 _validate_uploaded_dataset 对应的数据条件。
# 代码来源：AI生成 + 学生修改
def _validate_uploaded_dataset(df) -> bool:
    # Run quality checks after parsing and before saving to the session.
    rows = len(df)
    if rows < MIN_RECOMMENDED_ROWS:
        st.warning(_txt("few_rows", rows=rows))

    empty_columns = [str(col) for col in df.columns if df[col].isna().all()]
    if empty_columns:
        st.warning(_txt("empty_columns", columns=", ".join(empty_columns)))

    core_columns = [
        _find_column(df, ["description", "product", "productname", "product name", "item", "stockcode", "sku"]),
        _find_column(df, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"]),
        _find_column(df, ["quantity", "qty", "units"]),
        _find_column(df, ["unitprice", "unit price", "unit_price", "price"]),
        _find_column(df, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"]),
    ]
    if all(col is None for col in core_columns):
        st.error(_txt("missing_core_fields"))
        return False

    return True


# 函数说明：渲染当前页面或组件。
# 代码来源：AI生成 + 学生修改
def render():
    st.markdown(DATASET_CSS, unsafe_allow_html=True)
    st.title(t("dataset_center"))
    st.caption(t("dataset_center_summary"))
    st.caption(_txt("guide"))

    st.subheader(t("builtins_header"))
    catalog = dataset_loader.get_builtin_catalog()
    cols = st.columns(2)
    keys = list(catalog.keys())[:2]
    for i, key in enumerate(keys):
        name_key = f"{key}_name"
        src_key = f"{key}_source"
        desc_key = f"{key}_description"

        df, meta = dataset_loader.load_builtin(key)
        rows = meta.get("rows") if meta and meta.get("status") == "loaded" else None
        cols_n = meta.get("columns") if meta and meta.get("status") == "loaded" else None

        with cols[i]:
            _dataset_card(t(name_key), t(src_key), t(desc_key), rows, cols_n)
            if st.button(
                f"{t('load_label')} {t(name_key)}",
                key=f"load_top_{key}",
                use_container_width=True,
                icon=":material/database:",
                type="primary",
            ):
                if df is not None:
                    data_manager.save_dataset(t(name_key), df, {"source": t(src_key), "origin_meta": meta})
                    st.success(f"{t('upload_success')} ({t(name_key)})")
                else:
                    st.warning(t("dataset_center_summary"))

    st.markdown("---")

    st.subheader(t("upload_section"))
    st.markdown(
        f"""
        <div class="upload-zone">
            <div class="title">{t("dataset_upload_title")}</div>
            <div class="hint">{t("upload_placeholder")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        t("upload_placeholder"),
        type=["csv", "xls", "xlsx"],
        key="uploader_full",
        label_visibility="collapsed",
    )
    if uploaded is not None:
        try:
            with st.spinner(_txt("parsing")):
                df_u, meta_u = dataset_loader.load_uploaded_file(uploaded)
        except Exception:
            df_u, meta_u = None, {"status": "parse_failed", "error_key": "upload_parse_failed"}

        if df_u is not None:
            if _validate_uploaded_dataset(df_u):
                try:
                    with st.spinner(_txt("saving")):
                        data_manager.save_dataset(meta_u.get("filename"), df_u, {"source": "uploaded"})
                    st.success(t("upload_success"))
                except Exception:
                    st.error(t("dataset_save_error"))
        else:
            _render_upload_error(meta_u)

    st.markdown("---")

    cur = data_manager.get_current_dataset()
    if cur:
        meta = cur.get("meta", {})
        st.subheader(f"{t('current_dataset_label')}: {meta.get('name')}")
        _file_info(meta)

        st.markdown("---")

        st.subheader(t("preview"))
        df = cur.get("df")
        if df is not None:
            st.dataframe(df.head(20), use_container_width=True)

            with st.expander(t("field_descriptions")):
                st.subheader(t("dtypes_table"))
                st.write(df.dtypes.to_frame("dtype"))
                st.subheader(t("field_descriptions"))
                for col in df.columns:
                    samples = df[col].dropna().unique()[:3].tolist()
                    st.write(f"**{col}** - {str(df[col].dtype)} - Example: {samples}")
    else:
        st.info(t("no_dataset_loaded"))
