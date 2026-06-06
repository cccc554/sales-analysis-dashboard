import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'project'))

from services.translator import Translator


def main():
    tr = Translator()
    for lang in ['en', 'zh']:
        tr.set_language(lang)
        print('LANG:', lang)
        for key in ['dataset_center', 'builtins_header', 'upload_placeholder', 'online_retail_name', 'online_retail_description']:
            print(key, '->', tr.t(key))
        print('---')


if __name__ == '__main__':
    main()
