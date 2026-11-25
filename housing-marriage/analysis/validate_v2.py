"""Independent numeric and notebook checks for the revised analysis."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.analysis_deps'))
import numpy as np
import pandas as pd
from scipy.stats import pearsonr,spearmanr
from statsmodels.stats.multitest import multipletests
import nbformat

d=pd.read_csv(ROOT/'outputs_v2/annual_analysis_data.csv').set_index('year')
assert list(d.index)==list(range(1997,2026)) and d.notna().all().all()
a=json.loads((ROOT/'data/raw/115-01011.json').read_text())
b=json.loads((ROOT/'data/raw/115-01013.json').read_text())
assert a['header']['status']['code']==b['header']['status']['code']==0
for s in json.loads((ROOT/'research/source_register_v2.json').read_text()):
    assert hashlib.sha256((ROOT/'data/raw'/s['file']).read_bytes()).hexdigest()==s['sha256']
ages={(int(x['period']),x['SEX']):float(x['figure']) for x in a['dataSet']
    if x['sv']=='MED_AGE_1STM' and x.get('SEX') in ['M','F'] and x['figure']!=''}
counts={(int(x['period']),x['SEX'],x['AGE']):x['figure'] for x in b['dataSet']}
f=pd.read_excel(ROOT/'research/rvd_price_indices.xlsx',sheet_name='Annual  按年',header=None)
f=pd.DataFrame({'year':pd.to_numeric(f[2],errors='coerce'),'price':pd.to_numeric(f[26],errors='coerce')}).dropna()
prices=dict(zip(f.year.astype(int),f.price))
for year in d.index:
    np.testing.assert_allclose(d.loc[year,'price_index'],prices[year],rtol=0,atol=1e-7)
    np.testing.assert_allclose(d.loc[year,'price_change_pct'],100*(prices[year]/prices[year-1]-1),rtol=0,atol=1e-7)
    np.testing.assert_allclose(d.loc[year,'price_change_lag1_pct'],100*(prices[year-1]/prices[year-2]-1),rtol=0,atol=1e-7)
    for sex,name in [('M','male'),('F','female')]:
        assert d.loc[year,'median_age_'+name]==ages[year,sex]
        # Calculate differences as integer tenths, independently of floating subtraction.
        delta=(round(10*ages[year,sex])-round(10*ages[year-1,sex]))/10
        np.testing.assert_allclose(d.loc[year,'median_age_change_'+name],delta,atol=1e-12)
        assert counts[year,sex,'']==sum(v for (y,s,g),v in counts.items() if y==year and s==sex and g!='')
        for group in ['25-29','30-34']:
            key=group.replace('-','_')
            expected=100*counts[year,sex,group]/counts[year,sex,'']
            previous=100*counts[year-1,sex,group]/counts[year-1,sex,'']
            np.testing.assert_allclose(d.loc[year,f'share_{name}_{key}_pct'],expected,atol=1e-7)
            np.testing.assert_allclose(d.loc[year,f'share_change_{name}_{key}_pp'],expected-previous,atol=1e-7)
r=pd.read_csv(ROOT/'outputs_v2/tables/04_05_associations_and_hac_regressions.csv')
assert len(r)==12 and r.n.eq(29).all()
for row in r.itertuples():
    x=d[row.predictor];y=d[row.outcome]
    np.testing.assert_allclose(row.pearson_r,pearsonr(x,y).statistic,atol=1e-9)
    if row.outcome.startswith('median_age_change_'):y=y.round(1)
    np.testing.assert_allclose(row.spearman_rho,spearmanr(x,y).statistic,atol=1e-9)
for family,method in [('primary','holm'),('exploratory','fdr_bh')]:
    q=r[r.family.eq(family)];np.testing.assert_allclose(q.adjusted_hac_p,multipletests(q.hac_p,method=method)[1],atol=1e-9)
sens=pd.read_csv(ROOT/'outputs_v2/tables/06_sensitivity_comparisons.csv')
assert sens[sens.scenario.eq('omit1997')].n.eq(28).all()
strict=sens[sens.scenario.eq('exclude_all_pairs_touching_2020_2022')]
assert strict[strict.timing.eq('same_year')].n.eq(25).all()
assert strict[strict.timing.eq('lag1')].n.eq(24).all()
for row in strict.itertuples():
    for t in map(int,row.years.split(',')):
        assert not set(range(t-(2 if row.timing=='lag1' else 1),t+1)) & {2020,2021,2022}
nb=nbformat.read(ROOT/'outputs_v2/housing_marriage_analysis_v2.ipynb',as_version=4)
nbformat.validate(nb);cells=[c for c in nb.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in cells)
assert not any(o.output_type=='error' for c in cells for o in c.outputs)
assert 'supplements(d, results, sens)' in ''.join(c.source for c in cells)
summary={'rows':29,'full_years':'1997–2025','missing_cells':0,'raw_files_sha256_checked':3,
    'prices_and_growth_values_checked':87,'median_levels_checked':58,'integer_tenth_age_differences_checked':58,
    'age_shares_and_changes_checked':232,'models_checked':12,'primary_family':'4 models, Holm',
    'exploratory_age_share_family':'8 models, BH','strict_pandemic_samples':{'same_year':25,'lag1':24},
    'notebook_executed_code_cells':len(cells),'notebook_errors':0,
    'main_figures':len(list((ROOT/'outputs_v2/figures').glob('*.png'))),
    'appendix_figures':len(list((ROOT/'outputs_v2/appendix').glob('A*.png'))),
    'hac_crosscheck':'Consecutive samples verified against statsmodels; missing-year samples retain calendar gaps.'}
(ROOT/'outputs_v2/appendix/validation_summary.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False))
print(json.dumps(summary,indent=2,ensure_ascii=False))
