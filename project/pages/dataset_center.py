"""Dataset Center page."""

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


def _format_count(value) -> str:
    try:
        return f"{int(value):,}"
    except Exception:
        return t("not_available")


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


def render():
    st.markdown(DATASET_CSS, unsafe_allow_html=True)
    st.title(t("dataset_center"))
    st.caption(t("dataset_center_summary"))

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
        df_u, meta_u = dataset_loader.load_uploaded_file(uploaded)
        if df_u is not None:
            data_manager.save_dataset(meta_u.get("filename"), df_u, {"source": "uploaded"})
            st.success(t("upload_success"))
        else:
            st.error(meta_u.get("error", t("upload_error")))

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
