import pandas as pd
from pathlib import Path

root = Path('project')
path = root / 'datasets' / 'online_retail' / 'online_retail.csv'
print('loading:', path)

df = pd.read_csv(path)
print('\n1) customer_df columns:')
print(list(df.columns))

# helper same as page

def find_column(df, candidates):
    cols = list(df.columns)
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        cand_low = cand.lower()
        if cand_low in lower_map:
            return lower_map[cand_low]
    for col in cols:
        for cand in candidates:
            if cand.lower() in col.lower():
                return col
    return None

customer_col = find_column(df, ['customerid','customer id','customer','custid'])
order_col = find_column(df, ['invoiceno','invoice','orderid','order_id','order no','order'])
qty_col = find_column(df, ['quantity','qty','amount','units'])
price_col = find_column(df, ['unitprice','unit price','price','unit_price'])
date_col = find_column(df, ['invoicedate','invoice date','date','orderdate','order_date','timestamp'])
revenue_col = find_column(df, ['revenue','total','sales','amount','line_total','amountpaid'])

print('\n2) Detected columns:')
print('customer_col ->', customer_col)
print('order_col ->', order_col)
print('qty_col ->', qty_col)
print('price_col ->', price_col)
print('date_col ->', date_col)
print('revenue_col ->', revenue_col)

# compute revenue if needed
rev_col = None
if revenue_col:
    rev_col = revenue_col
elif price_col and qty_col:
    df = df.copy()
    df['_revenue_calc'] = pd.to_numeric(df[price_col], errors='coerce').fillna(0) * pd.to_numeric(df[qty_col], errors='coerce').fillna(0)
    rev_col = '_revenue_calc'

print('\n3) rev_col ->', rev_col)

# show sample
print('\n4) sample rows (first 5):')
cols_to_show = [c for c in [customer_col, order_col, qty_col, price_col, date_col, rev_col] if c]
print(df.head()[cols_to_show])

# Compute RFM as in page
print('\n5) Computing RFM...')
if customer_col and date_col and rev_col:
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

        rfm = pd.DataFrame({'recency': recency, 'frequency': frequency, 'monetary': monetary}).dropna()
        print('rfm shape ->', rfm.shape)
        print('rfm columns ->', list(rfm.columns))
        print('rfm dtypes ->')
        print(rfm.dtypes.to_dict())
        print('\nrfm head:')
        print(rfm.head(10))

        # check recency/frequency/monetary existence
        print('\n6) fields existence:')
        print('recency' , 'recency' in rfm.columns)
        print('frequency', 'frequency' in rfm.columns)
        print('monetary', 'monetary' in rfm.columns)

        # segmentation logic
        if not rfm.empty:
            r75 = rfm['recency'].quantile(0.75)
            f75 = rfm['frequency'].quantile(0.75)
            m75 = rfm['monetary'].quantile(0.75)
            print('\nquantiles r75,f75,m75 ->', r75, f75, m75)
            def seg(row):
                try:
                    if row['monetary'] >= m75 and row['frequency'] >= f75:
                        return 'high_value'
                    if row['frequency'] >= f75:
                        return 'loyal'
                    if row['recency'] >= r75:
                        return 'at_risk'
                    return 'normal'
                except Exception as e:
                    return 'normal'
            rfm['segment'] = rfm.apply(seg, axis=1)
            print('\nsegment value counts:')
            print(rfm['segment'].value_counts())
        else:
            print('rfm is empty')

    except Exception as e:
        print('Exception during RFM compute ->', repr(e))
else:
    print('not enough fields to compute RFM')

# also output available fields in original df
print('\n7) original df dtypes:')
print(df.dtypes.to_dict())

# list potential segment field names in df
candidates = [c for c in df.columns if 'segment' in c.lower() or 'seg' in c.lower() or 'level' in c.lower()]
print('\n8) potential existing segmentation-like columns in raw df ->', candidates)
