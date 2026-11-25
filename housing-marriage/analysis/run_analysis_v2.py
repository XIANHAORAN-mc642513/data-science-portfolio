"""Six-step annual time-series analysis. Run from any working directory."""
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
if (ROOT / '.analysis_deps').exists():
    sys.path.insert(0, str(ROOT / '.analysis_deps'))
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.cache/matplotlib'))
import json
import warnings
import hashlib
import importlib.metadata
import numpy as np
import pandas as pd
import scipy.stats as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller, kpss, acf
from statsmodels.stats.diagnostic import acorr_ljungbox, acorr_breusch_godfrey, het_breuschpagan
from statsmodels.stats.multitest import multipletests

OUT = ROOT / 'outputs_v2'
FIG = OUT / 'figures'
TAB = OUT / 'tables'
APP = OUT / 'appendix'
for path in [FIG, TAB, APP]:
    path.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, TEAL, GRAY = '#2463A0', '#CB6B37', '#20867D', '#657486'
COLORS = {'male': BLUE, 'female': ORANGE}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.labelcolor': '#334155',
    'axes.titleweight': 'bold', 'axes.titlesize': 13, 'figure.facecolor': 'white',
    'axes.edgecolor': '#CBD5E1', 'grid.color': '#E2E8F0', 'grid.alpha': .7,
    'legend.frameon': False, 'savefig.dpi': 200, 'svg.fonttype': 'none'})
OUTCOMES = {
    'median_age_change_male': 'Male median age',
    'median_age_change_female': 'Female median age',
    'share_change_male_25_29_pp': 'Male ages 25–29',
    'share_change_male_30_34_pp': 'Male ages 30–34',
    'share_change_female_25_29_pp': 'Female ages 25–29',
    'share_change_female_30_34_pp': 'Female ages 30–34'}
PRIMARY = list(OUTCOMES)[:2]
PREDICTORS = {'same_year': 'price_change_pct', 'lag1': 'price_change_lag1_pct'}


def save_table(frame, name, appendix=False):
    frame.to_csv((APP if appendix else TAB) / (name + '.csv'), index=False,
                 encoding='utf-8-sig', float_format='%.10g')


def save_fig(fig, name, note='', appendix=False):
    fig.text(.06, .018, 'Sources: RVD private domestic price indices; C&SD tables 115-01011 and 115-01013.\n' + note,
             fontsize=8, color=GRAY, va='bottom')
    fig.tight_layout(rect=(0, .075, 1, .94))
    dest = APP if appendix else FIG
    fig.savefig(dest / (name + '.png'))
    fig.savefig(dest / (name + '.svg'))
    plt.close(fig)


def load_data():
    d = pd.read_csv(ROOT / 'data/processed/annual_1997_2025_v2.csv').set_index('year')
    assert d.index.tolist() == list(range(1997, 2026))
    assert not d.index.duplicated().any()
    assert d.drop(columns='price_change_lag1_pct').notna().all().all()
    np.testing.assert_allclose(d.price_change_lag1_pct.iloc[1:], d.price_change_pct.iloc[:-1])
    for sex in ['male', 'female']:
        np.testing.assert_allclose(d[f'median_age_change_{sex}'].iloc[1:], d[f'median_age_{sex}'].diff().iloc[1:])
        for age in ['25_29', '30_34']:
            np.testing.assert_allclose(d[f'share_{sex}_{age}_pct'],
                100*d[f'first_marriages_{sex}_{age}']/d[f'first_marriage_total_{sex}'])
    d['age_gap_male_minus_female'] = d.median_age_male-d.median_age_female
    d['age_gap_change'] = d.median_age_change_male-d.median_age_change_female
    return d


def fit_hac(frame, outcome, predictor, bandwidth=1):
    """OLS + calendar-aware Bartlett HAC, n/(n-k) correction, t(n-k) inference.

    Unlike compressed-row HAC, missing years do not become consecutive years.
    For complete consecutive samples this equals statsmodels HAC.
    """
    sample = frame[[outcome, predictor]].dropna().sort_index()
    X = sm.add_constant(sample[predictor]).to_numpy()
    y = sample[outcome].to_numpy()
    model = sm.OLS(y, X).fit()
    score = X * model.resid[:, None]
    years = sample.index.to_numpy()
    distance = abs(years[:, None]-years[None, :])
    weights = np.maximum(0., 1.-distance/(bandwidth+1.))
    meat = score.T @ weights @ score
    bread = np.linalg.inv(X.T@X)
    n, k = X.shape
    cov = bread @ meat @ bread * n/(n-k)
    se = np.sqrt(np.diag(cov))
    if np.all(np.diff(years) == 1):
        reference = model.get_robustcov_results(cov_type='HAC', maxlags=bandwidth,
            kernel='bartlett', use_correction=True, use_t=True)
        np.testing.assert_allclose(cov, reference.cov_params(), rtol=1e-9, atol=1e-12)
    beta = model.params[1]
    critical = st.t.ppf(.975, n-k)
    p = 2*st.t.sf(abs(beta/se[1]), n-k)
    r, nominal_p = st.pearsonr(sample[predictor], sample[outcome])
    rank_y=sample[outcome].round(1) if outcome.startswith('median_age_change_') or outcome=='age_gap_change' else sample[outcome]
    rho, nominal_sp = st.spearmanr(sample[predictor], rank_y)
    row = {'outcome': outcome, 'predictor': predictor, 'n': n,
        'first_year': int(years.min()), 'last_year': int(years.max()),
        'years': ','.join(map(str, years)), 'bandwidth_calendar_years': bandwidth,
        'pearson_r': r, 'pearson_p_iid_reference_only': nominal_p,
        'spearman_rho': rho, 'spearman_p_iid_reference_only': nominal_sp,
        'intercept': model.params[0], 'beta_per_1pp_price': beta,
        'hac_se': se[1], 'hac_t': beta/se[1], 'hac_p': p,
        'ci95_low': beta-critical*se[1], 'ci95_high': beta+critical*se[1],
        'change_per_10pp_price': beta*10,
        'ci95_low_per_10pp': (beta-critical*se[1])*10,
        'ci95_high_per_10pp': (beta+critical*se[1])*10, 'r_squared': model.rsquared}
    return row, model, sample


def descriptive(d):
    columns = ['price_index','price_change_pct','median_age_male','median_age_female',
        'median_age_change_male','median_age_change_female', 'age_gap_male_minus_female'] + [
        f'share_{sex}_{age}_pct' for sex in ['male','female'] for age in ['25_29','30_34']]
    rows=[]
    for c in columns:
        s=d[c]; rows.append({'variable':c,'n':s.count(),'mean':s.mean(),'sd':s.std(ddof=1),
            'median':s.median(),'min':s.min(),'max':s.max(),'min_year':s.idxmin(),'max_year':s.idxmax(),
            'value_1997':s.loc[1997],'value_2025':s.loc[2025],'endpoint_difference':s.loc[2025]-s.loc[1997]})
    result=pd.DataFrame(rows);save_table(result,'01_descriptive_statistics')
    integrity={'annual_rows':len(d),'level_window':'1997–2025','comparison_window':'1997–2025',
        'comparison_n':len(d),'missing_cells':int(d.isna().sum().sum()),
        'missing_explanation':'No missing selected observations. 1995–1996 serve as calculation baselines.',
        'baseline_year_for_changes':1996, 'additional_price_year_for_lag':1995,'duplicate_years':int(d.index.duplicated().sum())}
    (APP/'data_checks.json').write_text(json.dumps(integrity,indent=2,ensure_ascii=False))
    return result


def trend_figures(d):
    fig,axs=plt.subplots(2,1,figsize=(10.5,7.8),sharex=True)
    axs[0].plot(d.index,d.price_index,color=TEAL,lw=2.4)
    axs[0].set(ylabel='Price index (1999 = 100)',title='Private domestic property prices')
    for sex in ['male','female']:
        c=f'median_age_{sex}';axs[1].plot(d.index,d[c],label=sex.title(),color=COLORS[sex],lw=2.4)
        axs[1].annotate(f'{d[c].iloc[-1]:.1f}',(2025,d[c].iloc[-1]),xytext=(5,0),textcoords='offset points',color=COLORS[sex])
    axs[1].set(ylabel='Median age (years)',xlabel='Year',title='Age at first marriage');axs[1].legend(ncol=2)
    for ax in axs:ax.grid(axis='y');ax.set_xlim(1996.5,2027)
    fig.suptitle('Housing prices and first-marriage timing, 1997–2025',x=.06,ha='left',fontsize=16,fontweight='bold')
    save_fig(fig,'01_long_term_trends','Annual averages for prices. Median ages describe people marrying for the first time in each year.')
    fig,axs=plt.subplots(2,1,figsize=(10.5,7.8),sharex=True)
    axs[0].bar(d.index,d.price_change_pct,color=[TEAL if v>=0 else ORANGE for v in d.price_change_pct])
    axs[0].set(ylabel='Annual price change (%)',title='Housing-price growth')
    for sex in ['male','female']:axs[1].plot(d.index,d[f'median_age_change_{sex}'],marker='o',ms=4,color=COLORS[sex],label=sex.title())
    axs[1].set(ylabel='Annual age change (years)',xlabel='Year',title='Change in median age at first marriage');axs[1].legend(ncol=2)
    for ax in axs:ax.axhline(0,color=GRAY,lw=.8);ax.axvspan(2019.5,2022.5,color=GRAY,alpha=.09);ax.grid(axis='y')
    fig.suptitle('Annual changes separate short-run movements from long-run trends',x=.06,ha='left',fontsize=15,fontweight='bold')
    save_fig(fig,'02_annual_changes','1996 provides the baseline for 1997 changes. Shading marks 2020–2022, not an estimated causal effect.')


def structure(d):
    fig,axs=plt.subplots(1,2,figsize=(11,5.8),sharex=True,sharey=True)
    crossings=[]
    for ax,sex in zip(axs,['male','female']):
        for age,color,style in [('25_29',BLUE,'-'),('30_34',ORANGE,'--')]:
            ax.plot(d.index,d[f'share_{sex}_{age}_pct'],color=color,ls=style,lw=2.4,label='Ages '+age.replace('_','–'))
        ax.set(title=sex.title(),xlabel='Year',ylim=(0,55));ax.grid(axis='y');ax.legend()
        difference=d[f'share_{sex}_30_34_pct']-d[f'share_{sex}_25_29_pct']
        first=difference[difference>0].index.min()
        last_not_higher=difference[difference <= 0].index.max()
        crossings.append({'sex':sex,'first_observed_year_30_34_exceeds_25_29':first, 'continuously_higher_from':int(last_not_higher+1)})
    axs[0].set_ylabel('Share of all first marriages of the same sex (%)')
    fig.suptitle('First-marriage age composition, 1997–2025',x=.06,ha='left',fontsize=16,fontweight='bold')
    save_fig(fig,'03_age_group_shares','Denominator: all first-marrying persons of the same sex and year. These shares are not marriage rates.')
    save_table(pd.DataFrame(crossings),'03_age_share_crossings')
    fig,ax=plt.subplots(figsize=(10.5,4.8));ax.plot(d.index,d.age_gap_male_minus_female,color=TEAL,lw=2.4)
    ax.set(title='Male minus female median age at first marriage',ylabel='Age gap (years)',xlabel='Year');ax.grid(axis='y');ax.set_ylim(0,3.3)
    save_fig(fig,'04_gender_age_gap','Difference between two annual medians, not the age gap within married couples.')


def association(d):
    common=d.loc[1997:2025].copy();rows=[];models={}
    for outcome in OUTCOMES:
        for timing,predictor in PREDICTORS.items():
            row,model,sample=fit_hac(common,outcome,predictor)
            row.update(timing=timing,family='primary' if outcome in PRIMARY else 'exploratory')
            rows.append(row);models[outcome,timing]=(model,sample)
    results=pd.DataFrame(rows)
    for family,method in [('primary','holm'),('exploratory','fdr_bh')]:
        mask=results.family.eq(family)
        results.loc[mask,'adjusted_hac_p']=multipletests(results.loc[mask,'hac_p'],method=method)[1]
        results.loc[mask,'multiplicity_method']=method
    save_table(results,'04_05_associations_and_hac_regressions')
    # Direct comparison of male and female age-change slopes; paired calendar years.
    gender=[]
    for timing,predictor in PREDICTORS.items():
        row,_,_=fit_hac(common,'age_gap_change',predictor);row['timing']=timing;gender.append(row)
    gender=pd.DataFrame(gender)
    gender['adjusted_hac_p']=multipletests(gender.hac_p,method='holm')[1]
    gender['multiplicity_method']='holm_within_two_exploratory_gender_contrasts'
    save_table(gender,'03_gender_slope_difference_exploratory')
    for timing,predictor in PREDICTORS.items():
        fig,axs=plt.subplots(1,2,figsize=(11,5.6),sharex=True,sharey=True)
        for ax,outcome,sex in zip(axs,PRIMARY,['male','female']):
            model,sample=models[outcome,timing]
            ax.scatter(sample[predictor],sample[outcome],color=COLORS[sex],s=42,alpha=.85,zorder=3)
            xx=np.linspace(sample[predictor].min()-2,sample[predictor].max()+2,150)
            ax.plot(xx,model.params[0]+model.params[1]*xx,color=COLORS[sex],lw=1.7)
            row=results[results.outcome.eq(outcome)&results.timing.eq(timing)].iloc[0]
            ax.set_title(f'{sex.title()}: r = {row.pearson_r:.2f}, n = {row.n}')
            influential=sample.index[np.argsort(model.get_influence().cooks_distance[0])[-2:]].tolist()
            for j,year in enumerate(sorted(set(influential+[2020,2025]))):
                offset_y=7 if sample.loc[year,outcome] <= 0 or j%2==0 else -13
                ax.annotate(str(year),(sample.loc[year,predictor],sample.loc[year,outcome]),xytext=(5,offset_y),textcoords='offset points',fontsize=8,color=GRAY)
            ax.axhline(0,color=GRAY,lw=.7);ax.axvline(0,color=GRAY,lw=.7);ax.grid(alpha=.4)
            ax.set_xlabel(('Same-year' if timing=='same_year' else 'Previous-year')+' housing-price change (%)')
        axs[0].set_ylabel('Annual change in median age (years)')
        fig.suptitle(('Same-year' if timing=='same_year' else 'One-year-lagged')+' association with first-marriage timing',x=.06,ha='left',fontsize=15,fontweight='bold')
        save_fig(fig,'05_same_year_scatter' if timing=='same_year' else '06_lagged_scatter','Comparison years: 1997–2025. Lines are descriptive OLS fits. Inference uses HAC errors, not iid correlation p-values.')
    primary=results[results.family.eq('primary')].reset_index(drop=True)
    fig,ax=plt.subplots(figsize=(10,5.2))
    for i,row in primary.iterrows():
        color=BLUE if 'male'==row.outcome.removeprefix('median_age_change_') else ORANGE
        ax.errorbar(row.change_per_10pp_price,i,xerr=[[row.change_per_10pp_price-row.ci95_low_per_10pp],[row.ci95_high_per_10pp-row.change_per_10pp_price]],fmt='o',color=color,capsize=4,lw=2)
    ax.set_yticks(range(4),[OUTCOMES[r.outcome]+' / '+r.timing.replace('_',' ') for r in primary.itertuples()]);ax.invert_yaxis()
    ax.axvline(0,color=GRAY,lw=1);ax.grid(axis='x');ax.set_xlabel('Annual median-age change associated with +10 pp price growth (years)')
    ax.set_title('Regression estimates with 95% HAC confidence intervals',loc='left')
    save_fig(fig,'07_regression_effect_sizes','Four primary models, n = 29 each. HAC(1), small-sample correction, t(27) pointwise intervals; not multiplicity-adjusted.')
    # Secondary outcomes use a separate scale and are explicitly exploratory.
    secondary=results[results.family.eq('exploratory')]
    matrix=secondary.pivot(index='outcome',columns='timing',values='pearson_r').reindex(list(OUTCOMES)[2:])[['same_year','lag1']]
    fig,ax=plt.subplots(figsize=(8,5));im=ax.imshow(matrix,vmin=-1,vmax=1,cmap='RdBu_r',aspect='auto')
    ax.set_xticks([0,1],['Same year','One-year lag']);ax.set_yticks(range(4),[OUTCOMES[x] for x in matrix.index])
    for i in range(4):
        for j in range(2):ax.text(j,i,f'{matrix.iloc[i,j]:.2f}',ha='center',va='center',fontsize=13)
    fig.colorbar(im,ax=ax,label='Pearson r');ax.set_title('Exploratory associations with annual age-share changes')
    save_fig(fig,'A03_age_share_associations','Annual share changes in percentage points. Eight exploratory models, n = 29 each.',appendix=True)
    return results,models


def diagnostics(d,models):
    series=['price_index','median_age_male','median_age_female','price_change_pct',*OUTCOMES]
    rows=[]
    for name in series:
        s=d[name].dropna();spec='ct' if name in ['price_index','median_age_male','median_age_female'] else 'c'
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            adf=adfuller(s,maxlag=1,autolag='AIC',regression=spec)
            kp=kpss(s,regression=spec,nlags=1)
        rows.append({'variable':name,'n':len(s),'deterministic':spec,'adf_statistic':adf[0],
            'adf_p':adf[1],'adf_selected_lags':adf[2],'adf_n_effective':adf[3],
            'kpss_statistic':kp[0],'kpss_p_table_bound_possible':kp[1],
            'kpss_lags':kp[2],'warnings':' | '.join(str(w.message) for w in caught)})
    save_table(pd.DataFrame(rows),'A01_stationarity',True)
    fig,axs=plt.subplots(1,3,figsize=(11,4.6))
    for ax,name in zip(axs,['price_change_pct',*PRIMARY]):
        a=acf(d[name],nlags=5,fft=False);ax.bar(np.arange(1,6),a[1:],color=TEAL,width=.5)
        ax.axhline(0,color=GRAY,lw=.7);ax.set(ylim=(-1,1),xticks=range(1,6),xlabel='Lag (years)',title=name.replace('median_age_change_','Age change: ').replace('price_change_pct','Price growth'))
    axs[0].set_ylabel('Autocorrelation');save_fig(fig,'A02_change_series_acf','ACF is descriptive. Short series make individual autocorrelation estimates uncertain.',True)
    diag=[];influences=[]
    for (outcome,timing),(model,sample) in models.items():
        lb=acorr_ljungbox(model.resid,lags=[1,2],model_df=0,return_df=True)
        bg=acorr_breusch_godfrey(model,nlags=1);bp=het_breuschpagan(model.resid,model.model.exog)
        influence=model.get_influence();cd=influence.cooks_distance[0]
        diag.append({'outcome':outcome,'timing':timing,'n':len(sample),
            'ljung_box_p_lag1':lb.lb_pvalue.iloc[0],'ljung_box_p_lag2':lb.lb_pvalue.iloc[1],
            'breusch_godfrey_F_p_lag1':bg[3],'breusch_pagan_F_p':bp[3],
            'max_cooks_distance':cd.max(),'most_influential_year':int(sample.index[np.argmax(cd)]),
            'cooks_screening_threshold':4/len(sample)})
        for year,cook,resid,hat in zip(sample.index,cd,model.resid,influence.hat_matrix_diag):
            influences.append({'outcome':outcome,'timing':timing,'year':year,'cooks_distance':cook,'residual':resid,'leverage':hat})
        if outcome in PRIMARY:
            fig,axs=plt.subplots(1,3,figsize=(12,4.8))
            axs[0].plot(sample.index,model.resid,marker='o',color=TEAL);axs[0].set(title='Residuals over time',xlabel='Year',ylabel='Residual (years)');axs[0].axhline(0,color=GRAY,lw=.8)
            axs[1].scatter(model.fittedvalues,model.resid,color=TEAL);axs[1].axhline(0,color=GRAY,lw=.8);axs[1].set(title='Residuals vs fitted',xlabel='Fitted age change (years)')
            axs[2].stem(sample.index,cd,basefmt=' ');axs[2].axhline(4/len(sample),color=ORANGE,ls='--');axs[2].set(title="Cook's distance",xlabel='Year')
            fig.suptitle(OUTCOMES[outcome]+' / '+timing.replace('_',' '),x=.06,ha='left',fontsize=15)
            save_fig(fig,'A04_diagnostics_'+outcome.removeprefix('median_age_change_')+'_'+timing,'Diagnostics screen for model limitations. Cook’s distance > 4/n is a review flag, not a rule for deleting years.',True)
    save_table(pd.DataFrame(diag),'A04_regression_diagnostics',True)
    save_table(pd.DataFrame(influences),'A05_observation_influence',True)
    return pd.DataFrame(rows),pd.DataFrame(diag)


def sensitivity(d,results):
    common=d.loc[1997:2025].copy();rows=[];loo=[]
    for outcome in OUTCOMES:
        for timing,predictor in PREDICTORS.items():
            # Remove affected result years AND all years entering price/age differences.
            clean=common.index.to_series().apply(lambda t: not (set(range(t-(2 if timing=='lag1' else 1),t+1)) & {2020,2021,2022}))
            scenarios={'full':common,'omit1997':common.loc[1998:],'post2003':common.loc[2004:],'exclude_outcome_years_2020_2022':common[~common.index.isin([2020,2021,2022])],
                'exclude_all_pairs_touching_2020_2022':common.loc[clean], 'pre2020':common.loc[:2019]}
            for name,sample in scenarios.items():
                row,_,_=fit_hac(sample,outcome,predictor);row.update(timing=timing,scenario=name);rows.append(row)
            for band in [0,2]:
                row,_,_=fit_hac(common,outcome,predictor,band);row.update(timing=timing,scenario=f'HAC_bandwidth_{band}');rows.append(row)
            for year in common.index:
                row,_,_=fit_hac(common.drop(index=year),outcome,predictor);row.update(timing=timing,omitted_year=year);loo.append(row)
    sensitivity=pd.DataFrame(rows);leaveout=pd.DataFrame(loo)
    save_table(sensitivity,'06_sensitivity_comparisons');save_table(leaveout,'A06_leave_one_year_out',True)
    summary=[]
    for (outcome,timing),group in leaveout.groupby(['outcome','timing'],sort=False):
        full=results[results.outcome.eq(outcome)&results.timing.eq(timing)].iloc[0]
        summary.append({'outcome':outcome,'timing':timing,'full_beta':full.beta_per_1pp_price,
            'loo_beta_min':group.beta_per_1pp_price.min(),'loo_beta_max':group.beta_per_1pp_price.max(),
            'loo_pearson_min':group.pearson_r.min(),'loo_pearson_max':group.pearson_r.max(),
            'sign_reversals':int((np.sign(group.beta_per_1pp_price)!=np.sign(full.beta_per_1pp_price)).sum()),
            'most_changing_omitted_year':int(group.loc[(group.beta_per_1pp_price-full.beta_per_1pp_price).abs().idxmax(),'omitted_year'])})
    save_table(pd.DataFrame(summary),'06_leave_one_year_out_summary')
    fig,axs=plt.subplots(1,2,figsize=(11,6.5),sharey=True)
    scenario_labels={'full':'Full sample (29 years)','omit1997':'Exclude 1997 (28 years)',
        'post2003':'2004–2025 (22 years)',
        'exclude_all_pairs_touching_2020_2022':'Exclude all pairs touching 2020–22','pre2020':'Before 2020 (23 years)'}
    for ax,outcome in zip(axs,PRIMARY):
        group=sensitivity[sensitivity.outcome.eq(outcome)&sensitivity.scenario.isin(scenario_labels)]
        for i,scenario in enumerate(scenario_labels):
            for timing,offset,color in [('same_year',-.12,BLUE),('lag1',.12,ORANGE)]:
                r=group[group.scenario.eq(scenario)&group.timing.eq(timing)].iloc[0]
                ax.errorbar(r.change_per_10pp_price,i+offset,xerr=[[r.change_per_10pp_price-r.ci95_low_per_10pp],[r.ci95_high_per_10pp-r.change_per_10pp_price]],fmt='o',color=color,capsize=3,label=timing.replace('_',' ') if i==0 else None)
        ax.axvline(0,color=GRAY,lw=1);ax.set_title(OUTCOMES[outcome]);ax.set_xlabel('Age change per +10 pp price growth (years)');ax.grid(axis='x');ax.legend(loc='upper right',ncol=2,fontsize=9)
    axs[0].set_yticks(range(len(scenario_labels)),scenario_labels.values());axs[0].invert_yaxis()
    axs[0].set_ylim(len(scenario_labels)-.3,-1.)
    fig.suptitle('Sensitivity to pandemic-period exclusions and study window',x=.06,ha='left',fontsize=15,fontweight='bold')
    save_fig(fig,'08_sensitivity_comparison','Intervals: calendar-aware HAC(1). Sample sizes and exact included years are recorded in the accompanying results table.')
    return sensitivity,pd.DataFrame(summary)


def supplements(d,results,sens):
    # Fixed-length circular paired bootstrap; identical block indices across four outcomes.
    bootstrap=[]
    for block in [2,3,4]:
        rng=np.random.default_rng(20261106)
        n=len(d);starts=rng.integers(0,n,size=(10000,int(np.ceil(n/block))))
        indices=((starts[:,:,None]+np.arange(block))%n).reshape(10000,-1)[:,:n]
        for outcome in PRIMARY:
            for timing,predictor in PREDICTORS.items():
                x=d[predictor].to_numpy()[indices];y=d[outcome].to_numpy()[indices]
                x=x-x.mean(axis=1,keepdims=True);y=y-y.mean(axis=1,keepdims=True)
                r=(x*y).sum(1)/np.sqrt((x*x).sum(1)*(y*y).sum(1))
                lo,hi=np.quantile(r,[.025,.975])
                bootstrap.append({'outcome':outcome,'timing':timing,'n':n,'block_length':block,
                    'replications':10000,'seed':20261106,'pearson_ci_low':lo,'pearson_ci_high':hi,
                    'crosses_zero':bool(lo <= 0 <= hi)})
    boot=pd.DataFrame(bootstrap);save_table(boot,'A07_circular_block_bootstrap',True)
    levels=[]
    for sex in ['male','female']:
        levels.append({'sex':sex,'pearson_levels':st.pearsonr(d.price_index,d[f'median_age_{sex}']).statistic,
            'pearson_changes':st.pearsonr(d.price_change_pct,d[f'median_age_change_{sex}']).statistic})
    save_table(pd.DataFrame(levels),'02_levels_vs_changes')
    scenario_labels={'full':'1997–2025','omit1997':'1998–2025','post2003':'2004–2025','pre2020':'1997–2019',
        'exclude_all_pairs_touching_2020_2022':'Exclude pandemic pairs'}
    order=[(o,t) for o in PRIMARY for t in PREDICTORS]
    vals=np.array([[sens[sens.outcome.eq(o)&sens.timing.eq(t)&sens.scenario.eq(s)].pearson_r.iloc[0]
        for s in scenario_labels] for o,t in order])
    fig,ax=plt.subplots(figsize=(11,5.9));im=ax.imshow(vals,vmin=-1,vmax=1,cmap='RdBu_r',aspect='auto')
    ax.set_xticks(range(5),scenario_labels.values(),rotation=15,ha='right')
    ax.set_yticks(range(4),[OUTCOMES[o]+' / '+t.replace('_',' ') for o,t in order])
    for i,(o,t) in enumerate(order):
        for j,s in enumerate(scenario_labels):
            row=sens[sens.outcome.eq(o)&sens.timing.eq(t)&sens.scenario.eq(s)].iloc[0]
            ax.text(j,i,f'{row.pearson_r:.2f}\nn={row.n}',ha='center',va='center',fontsize=11,
                color='white' if abs(row.pearson_r)>.5 else '#183347')
    fig.colorbar(im,ax=ax,label='Pearson r');ax.set_title('Association strength depends on the observation window',loc='left')
    save_fig(fig,'09_window_comparison','All windows are disclosed; no window is selected by significance. Pandemic exclusions remove every year entering either change.')
    return boot


def main():
    d=load_data();desc=descriptive(d);trend_figures(d);structure(d)
    results,models=association(d);stationarity,diag=diagnostics(d,models)
    sens,loo=sensitivity(d,results)
    supplements(d,results,sens)
    d.to_csv(OUT/'annual_analysis_data.csv',encoding='utf-8-sig',float_format='%.10g')
    versions={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','statsmodels','matplotlib','nbformat','nbclient']}
    versions['python']=sys.version
    (APP/'environment_versions.json').write_text(json.dumps(versions,indent=2))
    print(results[results.family.eq('primary')][['outcome','timing','n','pearson_r','spearman_rho','change_per_10pp_price','ci95_low_per_10pp','ci95_high_per_10pp','hac_p','adjusted_hac_p']].to_string(index=False))
    print('\nPrimary diagnostics:\n',diag[diag.outcome.isin(PRIMARY)].to_string(index=False))
    print('\nSensitivity:\n',sens[sens.outcome.isin(PRIMARY)][['outcome','timing','scenario','n','pearson_r','change_per_10pp_price','hac_p']].to_string(index=False))
    return d,desc,results,stationarity,diag,sens,loo


if __name__=='__main__':
    main()
