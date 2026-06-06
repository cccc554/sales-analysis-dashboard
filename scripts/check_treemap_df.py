import sys
import pandas as pd
sys.path.insert(0, 'project')
from pages import customer_analysis as ca
from services.translator import t

print('python version:', sys.version)

csv_path = 'project/datasets/online_retail/online_retail.csv'
print('loading', csv_path)
try:
    df = pd.read_csv(csv_path, encoding='unicode_escape')
except Exception as e:
    print('failed to read csv:', e)
    raise
print('loaded df shape:', df.shape)

# detect columns using page util
customer_col = ca._find_column(df, ["customerid", "customer id", "customer", "custid"])
order_col = ca._find_column(df, ["invoiceno", "invoice", "orderid", "order_id", "order no", "order"])
qty_col = ca._find_column(df, ["quantity", "qty", "amount", "units"])
price_col = ca._find_column(df, ["unitprice", "unit price", "price", "unit_price"])
date_col = ca._find_column(df, ["invoicedate", "invoice date", "date", "orderdate", "order_date", "timestamp"])
revenue_col = ca._find_column(df, ["revenue", "total", "sales", "amount", "line_total", "amountpaid"]) 

print('detected columns:')
print(' customer_col ->', customer_col)
print(' order_col ->', order_col)
print(' qty_col ->', qty_col)
print(' price_col ->', price_col)
print(' date_col ->', date_col)
print(' revenue_col ->', revenue_col)

# compute revenue if needed
rev_col = None
if revenue_col:
    rev_col = revenue_col
elif price_col and qty_col:
    try:
        df = df.copy()
        df['_revenue_calc'] = pd.to_numeric(df[price_col], errors='coerce').fillna(0) * pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
        rev_col = '_revenue_calc'
    except Exception as e:
        print('error computing _revenue_calc', e)
        rev_col = None

print('rev_col ->', rev_col)

if not (customer_col and date_col and rev_col):
    print('not enough fields to compute RFM; exiting')
    sys.exit(0)

# compute rfm
try:
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    grouped = df.groupby(customer_col)
    last_purchase = grouped[date_col].max()
    max_date = df[date_col].max()
    recency = (max_date - last_purchase).dt.days
    if order_col:
        frequency = grouped[order_col].nunique()
    else:
        frequency = grouped.size()
    monetary = grouped[rev_col].apply(lambda s: pd.to_numeric(s, errors='coerce').sum())

    rfm = pd.DataFrame({"recency": recency, "frequency": frequency, "monetary": monetary}).dropna()
    if "orders" not in rfm.columns:
        rfm["orders"] = rfm["frequency"]

    print('rfm.shape ->', rfm.shape)
    print('rfm.columns ->', list(rfm.columns))
    print('rfm.head ->')
    print(rfm.head(10))

    # segmentation logic
    r75 = rfm['recency'].quantile(0.75)
    f75 = rfm['frequency'].quantile(0.75)
    m75 = rfm['monetary'].quantile(0.75)

    def seg(row):
        try:
            if row['monetary'] >= m75 and row['frequency'] >= f75:
                return 'high_value'
            if row['frequency'] >= f75:
                return 'loyal'
            if row['recency'] >= r75:
                return 'at_risk'
            return 'normal'
        except Exception:
            return 'normal'

    rfm['segment'] = rfm.apply(seg, axis=1)
    print('after segmentation, columns ->', list(rfm.columns))
    print('final rfm.shape ->', rfm.shape)
    print('segment value_counts ->')
    print(rfm['segment'].value_counts())

    # treemap dataframe
    treemap_df = rfm.reset_index()
    id_col = treemap_df.columns[0]
    print('index column name detected ->', id_col)
    treemap_df = treemap_df.rename(columns={id_col: 'CustomerID'})
    print('treemap_df.shape ->', treemap_df.shape)
    print('treemap_df.columns ->', list(treemap_df.columns))
    print('treemap_df.head ->')
    print(treemap_df.head(10))

    # check required path & values columns
    path_ok = all(c in treemap_df.columns for c in ['segment', 'CustomerID']) or 'segment_label' in treemap_df.columns
    values_ok = 'monetary' in treemap_df.columns
    print('path_ok ->', path_ok)
    print('values_ok ->', values_ok)

    # build plotly fig to inspect internal fields (labels/parents/values)
    try:
        import plotly.express as px
        # create localized segment_label used in page
        seg_map = {"high_value": t("segment_high_value"), "loyal": t("segment_loyal"), "normal": t("segment_normal"), "at_risk": t("segment_at_risk")}
        treemap_df['segment_label'] = treemap_df['segment'].map(seg_map).fillna(t('segment_normal'))
        labels = {"CustomerID": t("column_customer_id"), "segment_label": t("label_segment"), "monetary": t("label_monetary"), "orders": t("column_orders")}
        fig = px.treemap(
            treemap_df,
            path=["segment_label", "CustomerID"],
            values="monetary",
            color="segment_label",
            custom_data=["orders"],
            labels=labels,
            title='debug treemap',
        )
        print('fig traces ->', len(fig.data))
        tr = fig.data[0]
        print('trace type ->', getattr(tr, 'type', None))
        try:
            labels_arr = list(tr.labels)
            parents_arr = list(tr.parents)
            values_arr = list(tr.values)
            print('labels count ->', len(labels_arr))
            print('parents count ->', len(parents_arr))
            print('values count ->', len(values_arr))
            print('values sample ->', values_arr[:10])
        except Exception as e:
            print('could not inspect trace arrays:', e)
    except Exception as e:
        print('plotly not available or fig build failed:', e)

except Exception as e:
    print('error computing rfm/treemap', e)
    raise
