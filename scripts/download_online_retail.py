"""下载 Online Retail 数据集并保存为 CSV。

用法:
    python scripts/download_online_retail.py

脚本会尝试从 UCI ML 存储库页面解析并下载第一个 xlsx / xls / csv 文件，
如果下载失败，将生成一个小型示例 CSV 以保证项目可运行。
"""
import os
import sys
import requests
from urllib.parse import urljoin, urlparse
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

# target the project's datasets directory
ROOT = Path(__file__).resolve().parents[1] / 'project'
DATA_DIR = ROOT / 'datasets' / 'online_retail'
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUT_CSV = DATA_DIR / 'online_retail.csv'

UCI_PAGE = 'https://archive.ics.uci.edu/dataset/352/online%2Bretail'
UCI_BASE = 'https://archive.ics.uci.edu/'


def find_data_link(page_url: str):
    try:
        r = requests.get(page_url, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print('Failed to fetch UCI page:', e)
        return None
    soup = BeautifulSoup(r.text, 'html.parser')
    # find links to .xlsx, .xls, .csv under the page
    for a in soup.find_all('a', href=True):
        href = a['href']
        if any(href.lower().endswith(ext) for ext in ('.xlsx', '.xls', '.csv')):
            return urljoin(UCI_BASE, href) if href.startswith('/') else href
    # fallback: look for links to /ml/machine-learning-databases/... pattern
    for a in soup.find_all('a', href=True):
        href = a['href']
        if '/machine-learning-databases/' in href:
            if any(href.lower().endswith(ext) for ext in ('.xlsx', '.xls', '.csv')):
                return urljoin(UCI_BASE, href) if href.startswith('/') else href
    return None


def download_file(url: str, out_path: Path):
    print('Downloading', url)
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(out_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        return True
    except Exception as e:
        print('Download failed:', e)
        return False


def convert_to_csv(file_path: Path, out_csv: Path):
    try:
        if file_path.suffix.lower() in ('.xls', '.xlsx'):
            df = pd.read_excel(file_path, engine='openpyxl' if file_path.suffix.lower() == '.xlsx' else None)
            df.to_csv(out_csv, index=False, encoding='utf-8')
            return True
        elif file_path.suffix.lower() == '.csv':
            # just move/copy
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
            df.to_csv(out_csv, index=False, encoding='utf-8')
            return True
    except Exception as e:
        print('Conversion failed:', e)
        return False


def generate_sample(out_csv: Path):
    print('Generating sample CSV as fallback...')
    df = pd.DataFrame([
        {'InvoiceNo': '536365', 'StockCode': '85123A', 'Description': 'WHITE HANGING HEART T-LIGHT HOLDER', 'Quantity': 6, 'InvoiceDate': '2010-12-01 08:26', 'UnitPrice': 2.55, 'CustomerID': 17850, 'Country': 'United Kingdom'},
        {'InvoiceNo': '536366', 'StockCode': '71053', 'Description': 'WHITE METAL LANTERN', 'Quantity': 6, 'InvoiceDate': '2010-12-01 08:28', 'UnitPrice': 3.39, 'CustomerID': 17850, 'Country': 'United Kingdom'},
    ])
    df.to_csv(out_csv, index=False, encoding='utf-8')


def main():
    # If CSV already exists, skip
    if OUT_CSV.exists():
        print('Dataset already exists at', OUT_CSV)
        return

    print('Searching for data link on UCI page...')
    link = find_data_link(UCI_PAGE)
    if not link:
        # Try known location
        candidate = 'https://archive.ics.uci.edu/ml/machine-learning-databases/00352/Online%20Retail.xlsx'
        link = candidate
        print('No direct link found on page; trying candidate URL:', candidate)

    tmp_file = DATA_DIR / Path(urlparse(link).path).name
    ok = download_file(link, tmp_file)
    if not ok:
        print('Download failed; will generate sample CSV instead.')
        generate_sample(OUT_CSV)
        print('Sample CSV created at', OUT_CSV)
        return

    # convert to CSV
    ok = convert_to_csv(tmp_file, OUT_CSV)
    if not ok:
        print('Conversion failed; will generate sample CSV instead.')
        generate_sample(OUT_CSV)
    else:
        print('Saved CSV to', OUT_CSV)


if __name__ == '__main__':
    main()
