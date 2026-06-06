import sys
from pathlib import Path

# ensure project package is importable when running from repo root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'project'))

from services import dataset_loader


def main():
    for name in ['online_retail', 'online_retail_ii']:
        df, meta = dataset_loader.load_builtin(name)
        print(name, 'status->', meta.get('status'), 'rows->', meta.get('rows'), 'cols->', meta.get('columns'))


if __name__ == '__main__':
    main()
