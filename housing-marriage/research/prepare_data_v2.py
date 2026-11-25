"""Prepare official annual data; run with the bundled Python runtime.

The RVD raw XLS was converted losslessly for reading using LibreOffice:
soffice --headless --convert-to xlsx --outdir research data/raw/rvd_price_indices.xls
The source workbook remains unchanged in data/raw.
"""
from pathlib import Path
import json
import hashlib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
OUT = ROOT / 'data/processed'
OUT.mkdir(parents=True, exist_ok=True)

f = pd.read_excel(ROOT / 'research/rvd_price_indices.xlsx', sheet_name='Annual  按年', header=None)
h = pd.DataFrame({'year': pd.to_numeric(f[2], errors='coerce'),
                  'price_index': pd.to_numeric(f[26], errors='coerce')}).dropna()
h.year = h.year.astype(int)
assert not h.year.duplicated().any()
h = h[h.year.between(1995, 2025)].set_index('year').sort_index()

a = pd.DataFrame(json.loads((RAW / '115-01011.json').read_text())['dataSet'])
a = a[a.sv.eq('MED_AGE_1STM') & a.SEX.isin(['M', 'F'])].copy()
a['year'] = a.period.astype(int)
a.figure = pd.to_numeric(a.figure, errors='coerce')
assert not a.duplicated(['year', 'SEX']).any()
age = a.pivot(index='year', columns='SEX', values='figure').rename(
    columns={'M': 'median_age_male', 'F': 'median_age_female'})

b = pd.DataFrame(json.loads((RAW / '115-01013.json').read_text())['dataSet'])
b['year'] = b.period.astype(int)
b.figure = pd.to_numeric(b.figure, errors='coerce')
assert not b.duplicated(['year', 'SEX', 'AGE']).any()
for (year, sex), g in b.groupby(['year', 'SEX']):
    assert g.loc[g.AGE.eq(''), 'figure'].iloc[0] == g.loc[g.AGE.ne(''), 'figure'].sum(), (year, sex)
w = b.pivot(index='year', columns=['SEX', 'AGE'], values='figure')
d = h.join(age, validate='one_to_one')
for sex, name in [('M', 'male'), ('F', 'female')]:
    d['first_marriage_total_' + name] = w[sex, '']
    for group in ['25-29', '30-34']:
        key = group.replace('-', '_')
        d[f'first_marriages_{name}_{key}'] = w[sex, group]
        d[f'share_{name}_{key}_pct'] = 100 * w[sex, group] / w[sex, '']
        d[f'share_change_{name}_{key}_pp'] = d[f'share_{name}_{key}_pct'].diff()
    d['median_age_change_' + name] = d['median_age_' + name].diff().round(1)
d['price_change_pct'] = 100 * d.price_index.pct_change(fill_method=None)
d['price_change_lag1_pct'] = d.price_change_pct.shift(1)
d = d.loc[1997:2025]
assert len(d) == 29
assert d.notna().all().all()
d.to_csv(OUT / 'annual_1997_2025_v2.csv', encoding='utf-8-sig', float_format='%.8f')

sources = [
    {'file': 'rvd_price_indices.xls', 'url': 'https://www.rvd.gov.hk/doc/en/statistics/his_data_4.xls',
     'selection': 'Annual sheet, All Classes; index base 1999=100',
     'coverage_in_download': '1980–2025 (annual sheet)',
     'notes': 'Primary sales excluded. Earlier rebased indices may differ slightly due to rounding. All New Territories districts included since Q1 1987.'},
    {'file': '115-01011.json', 'url': 'https://www.censtatd.gov.hk/api/get.php?full_series=1&id=115-01011&lang=en',
     'selection': 'sv=MED_AGE_1STM; SEX=M,F; freq=Y; unit years',
     'coverage_in_download': '1961–2025 (entire table; individual indicators may have missing early years)',
     'notes': 'No sd_value status markers for selected median-age observations in 1997–2025. Do not apply notes for other indicators to this series.'},
    {'file': '115-01013.json', 'url': 'https://www.censtatd.gov.hk/api/get.php?full_series=1&id=115-01013&lang=en',
     'selection': 'sv=PMFT; SEX=M,F; AGE empty=official total; AGE=25-29,30-34',
     'coverage_in_download': '1986–2025',
     'notes': 'Unit persons, not couples. All age groups reconcile to official totals. No sd_value status markers in selected 1997–2025 observations.'},
]
for s in sources:
    s['access_date_local'] = '2026-11-06 Asia/Shanghai'
    s['sha256'] = hashlib.sha256((RAW / s['file']).read_bytes()).hexdigest()
(ROOT / 'research/source_register_v2.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2))
dictionary = []
for c in d.columns:
    if c == 'price_index': meaning, unit = 'Official annual All Classes private domestic price index', '1999=100'
    elif c == 'price_change_pct': meaning, unit = '100*(P_t/P_(t-1)-1)', '%'
    elif c == 'price_change_lag1_pct': meaning, unit = 'Previous calendar year price_change_pct', '%'
    elif c.startswith('median_age_change'): meaning, unit = 'Current minus previous calendar year median age', 'years'
    elif c.startswith('median_age'): meaning, unit = 'Official median age at first marriage by sex', 'years'
    elif c.startswith('share_change'): meaning, unit = 'Current minus previous calendar year share', 'percentage points'
    elif c.startswith('share_'): meaning, unit = '100*selected age-group persons / all first-marrying persons of same sex and year', '%'
    else: meaning, unit = 'Official first-marrying persons for specified sex and age group or total', 'persons'
    dictionary.append({'variable': c, 'definition': meaning, 'unit': unit})
pd.DataFrame(dictionary).to_csv(ROOT / 'research/variable_dictionary_v2.csv', index=False, encoding='utf-8-sig')
print('Prepared 29 annual records with 29 complete lag1 pairs. 1995–1996 are calculation baselines; age differences preserve 0.1-year ties.')
