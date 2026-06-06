"""确保 Online Retail II 存在：尝试使用 Kaggle API（若可用），否则生成示例 CSV。"""
import os
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / 'project'
DATA_DIR = ROOT / 'datasets' / 'online_retail_ii'
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = DATA_DIR / 'online_retail_ii.csv'


def generate_sample(out_csv: Path):
    df = pd.DataFrame([
        {'InvoiceNo': '536365', 'StockCode': '85123A', 'Description': 'WHITE HANGING HEART T-LIGHT HOLDER', 'Quantity': 6, 'InvoiceDate': '2010-12-01 08:26', 'UnitPrice': 2.55, 'CustomerID': 17850, 'Country': 'United Kingdom', 'InvoiceYear': 2010},
        {'InvoiceNo': '536366', 'StockCode': '71053', 'Description': 'WHITE METAL LANTERN', 'Quantity': 6, 'InvoiceDate': '2010-12-01 08:28', 'UnitPrice': 3.39, 'CustomerID': 17850, 'Country': 'United Kingdom', 'InvoiceYear': 2010},
        {'InvoiceNo': '536367', 'StockCode': '84406B', 'Description': 'CREAM CUPID HEARTS COAT HANGER', 'Quantity': 8, 'InvoiceDate': '2010-12-01 08:34', 'UnitPrice': 2.75, 'CustomerID': 13047, 'Country': 'United Kingdom', 'InvoiceYear': 2010},
    ])
    df.to_csv(out_csv, index=False, encoding='utf-8')


def try_kaggle_download(out_csv: Path):
    # Attempt to use kaggle API if configured. This requires user credentials and kaggle package.
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        api = KaggleApi()
        api.authenticate()
        # Known Kaggle dataset slug may vary; try a commonly used slug and unzip
        dataset_ref = 'hedayat/online-retail-ii'  # best-effort guess
        tmp_dir = DATA_DIR / 'tmp_kaggle'
        tmp_dir.mkdir(exist_ok=True)
        api.dataset_download_files(dataset_ref, path=str(tmp_dir), unzip=True)
        # find csv
        for f in tmp_dir.rglob('*.csv'):
            try:
                df = pd.read_csv(f, low_memory=False)
                df.to_csv(out_csv, index=False, encoding='utf-8')
                return True
            except Exception:
                continue
    except Exception:
        return False


def main():
    if OUT_CSV.exists():
        print('Online Retail II already exists at', OUT_CSV)
        return

    ok = try_kaggle_download(OUT_CSV)
    if ok:
        print('Downloaded Online Retail II via Kaggle API ->', OUT_CSV)
        return

    print('Kaggle download not available or failed; generating sample CSV fallback.')
    generate_sample(OUT_CSV)
    print('Sample CSV created at', OUT_CSV)


if __name__ == '__main__':
    main()
