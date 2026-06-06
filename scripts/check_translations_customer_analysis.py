import re, sys
sys.path.insert(0,'project')
from services.translator import t
import streamlit as st
text = open('project/pages/customer_analysis.py','r',encoding='utf-8').read()
keys = re.findall(r't\("([^\"]+)"\)', text)
print('keys used in page:', keys)
missing = {'zh':[], 'en':[]}
for lang in ['zh','en']:
    st.session_state.language = lang
    for k in keys:
        val = t(k)
        if val == k:
            missing[lang].append(k)
print('missing translations:')
print(missing)
