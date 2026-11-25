"""Build the six-step report and a concise presentation companion from V2 outputs."""
from pathlib import Path
import base64,html,json,zipfile,sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs_v2'
d=pd.read_csv(OUT/'annual_analysis_data.csv').set_index('year')
r=pd.read_csv(OUT/'tables/04_05_associations_and_hac_regressions.csv')
s=pd.read_csv(OUT/'tables/06_sensitivity_comparisons.csv')
diag=pd.read_csv(OUT/'appendix/A04_regression_diagnostics.csv')
boot=pd.read_csv(OUT/'appendix/A07_circular_block_bootstrap.csv')
gender=pd.read_csv(OUT/'tables/03_gender_slope_difference_exploratory.csv')
labels={'median_age_change_male':'男性','median_age_change_female':'女性'}
timings={'same_year':'同期','lag1':'滞后一年'}

def mainrow(o,t):return r[r.outcome.eq(o)&r.timing.eq(t)].iloc[0]

def mdtable(df):
    return '\n'.join(['| '+' | '.join(df.columns)+' |','| '+' | '.join(['---']*len(df.columns))+' |']+
        ['| '+' | '.join(map(str,x))+' |' for x in df.itertuples(index=False,name=None)])

css='''body{margin:0;background:#f1f4f6;color:#243447;font:16px/1.85 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}main{max-width:1100px;margin:auto;padding:45px 38px 70px;background:white}h1{font-size:31px;line-height:1.4;color:#163c5e}h2{font-size:23px;margin:46px 0 18px;color:#163c5e}h3{font-size:18px;margin:25px 0 12px}p{max-width:980px}.meta{color:#627487}.table{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px;line-height:1.7;margin:22px 0}th,td{padding:9px 11px;border:1px solid #d9e0e7;text-align:right}th:first-child,td:first-child{text-align:left}th{background:#e8eff5}tr:nth-child(even){background:#f7f9fb}figure{margin:28px 0}img{width:100%;height:auto}figcaption{font-size:13px;color:#627487}a{color:#2463a0}nav a{display:inline-block;margin:5px 18px 5px 0}li{margin:8px 0}@media(max-width:700px){main{padding:22px 17px}h1{font-size:25px}table{min-width:650px}}@media print{body{background:white}main{padding:0}h2{break-after:avoid}figure{break-inside:avoid}}'''
sources=[('RVD住宅价格指数','https://www.rvd.gov.hk/doc/en/statistics/his_data_4.xls'),
    ('C&SD初婚年龄表115-01011','https://www.censtatd.gov.hk/en/web_table.html?id=115-01011'),
    ('C&SD初婚人数表115-01013','https://www.censtatd.gov.hk/en/web_table.html?id=115-01013'),
    ('HAC协方差说明','https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.RegressionResults.get_robustcov_results.html'),
    ('并列排名说明','https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.rankdata.html'),
    ('环形区块Bootstrap说明','https://bashtage.github.io/arch/bootstrap/generated/arch.bootstrap.CircularBlockBootstrap.html')]

def render(title,sections,filename):
    doc=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>'+html.escape(title)+'</title><style>'+css+'</style><main><h1>'+html.escape(title)+'</h1>',
        '<p class="meta">香港年度数据 1997—2025 · V2 · 官方数据下载版本 2026年11月6日</p>',
        '<nav>'+''.join(f'<a href="#s{i}">{html.escape(x["title"])}</a>' for i,x in enumerate(sections))+'</nav>']
    md=['# '+title,'官方数据下载版本：2026年11月6日。V2，29年完整比较期。']
    for i,x in enumerate(sections):
        doc+=['<section id="s'+str(i)+'"><h2>'+html.escape(x['title'])+'</h2>'];md+=['','## '+x['title'],'']
        for p in x.get('paragraphs',[]):doc+=['<p>'+html.escape(p)+'</p>'];md += [p,'']
        for df in x.get('tables',[]):doc+=['<div class="table">'+df.to_html(index=False,border=0)+'</div>'];md += [mdtable(df),'']
        for f,caption in x.get('figures',[]):
            encoded=base64.b64encode((OUT/f).read_bytes()).decode()
            doc+=['<figure><img src="data:image/png;base64,'+encoded+'" alt="'+html.escape(caption)+'"><figcaption>'+html.escape(caption)+'</figcaption></figure>']
            md += [f'![{caption}]({f})','']
        doc+=['</section>']
    doc+=['<h2>数据与方法来源</h2><ul>']+[f'<li><a href="{url}">{html.escape(label)}</a></li>' for label,url in sources]+['</ul></main></html>']
    md+=['## 数据与方法来源','']+[f'- [{label}]({url})' for label,url in sources]
    (OUT/(filename+'.html')).write_text('\n'.join(doc));(OUT/(filename+'.md')).write_text('\n\n'.join(md))

desctable=[]
variables=[('price_index','房价指数（1999=100）'),('median_age_male','男性初婚年龄（岁）'),
    ('median_age_female','女性初婚年龄（岁）'),('age_gap_male_minus_female','男女中位数之差（岁）')]
for sex,sexlabel in [('male','男性'),('female','女性')]:
    for age in ['25_29','30_34']:variables.append((f'share_{sex}_{age}_pct',sexlabel+age.replace('_','—')+'岁初婚占比（%）'))
for c,label in variables:
    y=d[c];desctable.append({'指标':label,'1997':f'{y.loc[1997]:.2f}','2025':f'{y.loc[2025]:.2f}',
        '均值':f'{y.mean():.2f}','标准差':f'{y.std(ddof=1):.2f}'})
stats=pd.DataFrame(desctable)
modeltable=[]
for o in labels:
    for t in timings:
        q=mainrow(o,t)
        modeltable.append({'性别':labels[o],'设定':timings[t],'Pearson r':f'{q.pearson_r:.3f}',
            'Spearman ρ':f'{q.spearman_rho:.3f}','每10个百分点房价涨幅对应变化（岁）':f'{q.change_per_10pp_price:.3f}',
            '95% HAC区间':f'[{q.ci95_low_per_10pp:.3f}, {q.ci95_high_per_10pp:.3f}]',
            'HAC p':f'{q.hac_p:.3f}','Holm调整p':f'{q.adjusted_hac_p:.3f}'})
modeltable=pd.DataFrame(modeltable)
windowtable=[]
for o in labels:
    for t in timings:
        row={'性别':labels[o],'设定':timings[t]}
        for key,label in [('full','完整29年'),('omit1997','剔除1997'),('post2003','2004—2025'),('pre2020','1997—2019'),('exclude_all_pairs_touching_2020_2022','严格剔除疫情配对')]:
            q=s[s.outcome.eq(o)&s.timing.eq(t)&s.scenario.eq(key)].iloc[0]
            row[label]=f'{q.pearson_r:.3f} (n={q.n})'
        windowtable.append(row)
windowtable=pd.DataFrame(windowtable)

step1={'title':'1 描述性统计','paragraphs':[
    '分析以全港日历年为单位，合并RVD全港私人住宅All Classes年均价格指数、C&SD男女初婚年龄中位数及分年龄组初婚人数。主研究期统一为1997—2025年，同期和一年滞后均有29个完整配对。1995—1996年仅用于计算前置变化与滞后，不计入主研究期。',
    '房价涨跌幅=100×(P_t/P_(t−1)−1)，单位%；初婚年龄变化=A_t−A_(t−1)，单位岁；年龄组占比=100×该组初婚人数/同年同性别全部初婚人数；占比年度变化单位为百分点。人数不是夫妇对数，占比也不是年龄别初婚率。',
    '保留官方原始文件，不填补或插值。年度无重复，所选29年指标无缺失，各年龄组人数加总与官方总数一致。初婚年龄变化按原始0.1岁精度处理，恢复Spearman排名的并列值；年龄组占比采用未按展示精度舍入的计算值。'], 'tables':[stats]}
step2={'title':'2 房价与初婚年龄趋势分析','paragraphs':[
    '男性初婚年龄中位数由29.6岁升至32.9岁，增加3.3岁；女性由26.8岁升至31.3岁，增加4.5岁。研究期内女性中位数增加更多。男性中位数减去女性中位数的差值由2.8岁缩小至1.6岁，这不是夫妻年龄差。',
    '房价年均指数最低为2003年的61.6，最高为2021年的392.7。2021—2025年房价指数下降26.1%，但男女初婚年龄中位数均再提高0.7岁。这个阶段说明两条长期路径并非简单同步，不能仅凭房价高和初婚年龄高就确认联系。',
    '房价水平与男女初婚年龄水平的Pearson相关分别为0.699、0.855，但改用同期年度变化后变为−0.504、−0.218。两类相关回答不同问题，方向反转说明定义和时间趋势会明显影响结果。水平相关只作描述，不作为主推断证据。',
    'ADF与KPSS作为附录诊断：房价和初婚年龄水平序列不支持直接作平稳水平回归；房价涨跌和男女初婚年龄变化的检查较支持采用变化量。ADF最多1阶滞后、AIC选择，水平序列含趋势，变化序列含常数；KPSS固定1阶。29年的检验能力有限，不能把不拒绝当成证明。'],
    'figures':[('figures/01_long_term_trends.png','图1 房价和初婚年龄采用真实单位、对齐年份。'),('figures/02_annual_changes.png','图2 年度变化用于关联分析；灰色区域只标记2020—2022年。')]}
step3={'title':'3 初婚年龄结构与性别差异分析','paragraphs':[
    '男性25—29岁初婚占比由37.54%降至22.56%，下降14.98个百分点；30—34岁由29.40%升至37.38%，提高7.98个百分点。女性相应变化为42.97%降至30.84%，以及17.52%升至37.84%。女性30—34岁组提高20.32个百分点。',
    '男性30—34岁占比首次超过25—29岁是在2005年，但2009年短暂回落到其下方，2010年起持续高于后者。女性则从2022年起持续高于后者。这提供了比“整体晚婚”更具体的初婚者年龄组成证据；不等于追踪同一批人延迟了多少年。',
    '性别比较以描述性差异为主。补充以男女初婚年龄变化之差直接回归房价变化：同期未调整p约0.028，但两个探索性性别对比作Holm调整后约0.056；滞后未调整p约0.574。因此不将性别斜率差写成已确认结论，更不以“一边显著、另一边不显著”判定差异。'],
    'figures':[('figures/03_age_group_shares.png','图3 两个目标年龄组不覆盖全部年龄，占比不必加总为100%。'),('figures/04_gender_age_gap.png','图4 比较年度男女初婚者中位数，不能解释为夫妻年龄差。')]}
step4={'title':'4 房价变化与初婚变化的相关分析','paragraphs':[
    '同期主模型为ΔA_t=α+βg_t+ε_t，男女分别估计。男性Pearson r=−0.504，女性r=−0.218；正确处理并列值后的Spearman分别为−0.404和−0.088。女性同期关联较弱，且对极端年份及相关方法更敏感。',
    '单变量HAC回归显示，房价涨幅增加10个百分点，对应男性初婚年龄年度增幅约减少0.054岁，女性约减少0.017岁。这里是年度增幅较小，不是初婚年龄必然下降，也不是个人婚期提前。',
    '回归采用Bartlett核HAC(1)、n/(n−k)小样本修正和t(27)区间。四个主模型的未调整p及Holm调整p一并报告。男性同期和女性滞后单项p低于0.05，但四个主要比较调整后均不低于0.05。95%区间是逐模型区间，未经同时推断调整。',
    '男性同期Breusch–Pagan异方差F检验p约0.011，提示普通同方差标准误不适合直接用于主推断。HAC能调整协方差估计，却不能解决遗漏变量、反向关系或个别年份影响。'],
    'tables':[modeltable], 'figures':[('figures/05_same_year_scatter.png','图5 每个点是一个年份；1997年是关键影响点。'),('figures/07_regression_effect_sizes.png','图6 回归系数与逐模型95% HAC区间，保留跨零和不跨零的全部结果。')]}
step5={'title':'5 一年滞后关联分析','paragraphs':[
    '滞后模型以g_(t−1)解释ΔA_t，仍使用1997—2025这29个婚姻观察年。例如1997年初婚变化对应1996年房价变化，后者需要1995年指数作为基期。',
    '男性滞后Pearson r=−0.379，女性r=−0.393；Spearman分别为−0.498和−0.461。女性在两种相关方法下都呈现比同期更明显的样本关联；男性Pearson的同期绝对值较大、Spearman的滞后绝对值较大。不能概括为“滞后一定比同期强”。未正式检验相关系数差值。',
    '房价上一年涨幅增加10个百分点，对应男性本年初婚年龄年度增幅约减少0.041岁，女性约减少0.031岁。男性HAC p=0.062、女性p=0.027；Holm调整后分别约0.123、0.085。此处同期与滞后是分别拟合的简单模型，不是相互控制后的独立效应。',
    '四个年龄组占比变化的8项探索性分析，Pearson约在−0.227至0.274之间，BH调整后均不显著。女性25—29岁占比变化的ADF和KPSS结论存在冲突，更应限制为探索性描述。'],
    'figures':[('figures/06_lagged_scatter.png','图7 男女滞后方向均为负，不能据此解释因果。')]}
step6={'title':'6 稳健性检验','paragraphs':[
    '完整29年为主样本，另报告剔除1997年的28年、2004—2025、1997—2019、剔除疫情结果年和剔除全部疫情相关原始年份配对。窗口选择用于检查影响，不能将显著的子样本替代主结果。2004年分界是阶段敏感性分析，不是已识别的结构断点。',
    '男性同期相关从完整样本−0.504变为剔除1997年的−0.336，在2004—2025窗口进一步变为−0.191；其负向方向保持，但大小依赖早期年份。2004—2025男女滞后相关分别为−0.574和−0.539；这是窗口内的探索性结果，不能用更小p值升级主结论。',
    '逐年剔除后，四个初婚年龄关联仍均为负；方向一致不意味着大小和显著性完全稳定。Spearman检查保留真实并列值；HAC带宽0、1、2均完整披露，不按结果选择带宽。',
    '严格疫情剔除会同时检查年龄差及房价差所需的每个原始年份：同期剩25年，滞后剩24年。先在连续年度计算再筛选；HAC按真实日历间隔计算，不把2019和2023视为相邻年。',
    '参考组员的方法，补充2、3、4年环形区块成对Bootstrap，每个设定10000次，种子20261106。3年区块下男性同期、男性滞后、女性同期、女性滞后r的95%区间约为[−0.76,−0.08]、[−0.73,−0.09]、[−0.48,0.13]、[−0.64,−0.19]。这些是未经多重比较调整的探索性相关区间，不是HAC回归系数区间；两种方法不能混用为同一检验。',
    '残差低阶自相关检查未发现明显证据，但样本有限；男性同期异方差与1997年影响点需要保留在解释中。附录提供所有残差、影响点、平稳性、逐年剔除和Bootstrap结果。'],
    'tables':[windowtable], 'figures':[('figures/09_window_comparison.png','图8 所有窗口采用相同色标，显示关联对研究期的敏感性。')]}
conclusion={'title':'研究回答与价值','paragraphs':[
    '本研究的主要发现是：香港初婚者年龄结构在1997—2025年明显向较高年龄组移动，同时男女初婚年龄中位数差缩小；房价的年度波动与初婚变化之间存在负向样本关联，但关联强弱依赖性别、同期或滞后定义及研究窗口。',
    '研究价值首先在于把“初婚年龄上升”细化为男女和两个年龄组的可比较变化。其次，明确区分长期水平与年度变化，展示同一数据可能产生方向不同的相关，避免把共同趋势误读为机制。最后，用完整样本、影响点和多种敏感性设定检验一个常见直觉，给出了可复核的证据边界。',
    '现有结果不支持将香港长期初婚变化简单归因于私人住宅价格，也不能反过来证明住房因素不重要。房价指数不是个人住房负担，且未控制收入、就业、教育、迁移、公共房屋和利率等因素。数据只能识别年度汇总关联，不能识别个体婚姻决策或因果机制。',
    '没有明确显著结果并不等于没有研究价值。这里真正能够汇报的是明确的长期人口变化、不同口径下关联的差别，以及结论对早期年份和研究窗口的敏感性。']}
repro={'title':'复现与版本说明','paragraphs':[
    'V2保留原始下载版本，扩展前置房价到1995年，将同期和滞后比较统一为29年，并修复初婚年龄变化Spearman的浮点并列值问题。原V1文件保留，未覆盖；不能将V1的28年系数与V2的29年系数拼到同一张结果表中。',
    '输出包括9张主图、6张附图、CSV结果、已执行Notebook和汇报提纲。Notebook中的运行环境版本随包保留。来源SHA256见research/source_register_v2.json，数据字典见research/variable_dictionary_v2.csv。表中年龄中位数的原始精度为0.1岁，模型的小数位不代表更高的测量精度。']}
render('香港房价与初婚变化 六步分析报告',[step1,step2,step3,step4,step5,step6,conclusion,repro],'分析结果报告_v2')

slides=[
 {'title':'1 描述性统计','paragraphs':['汇报重点：三个官方来源，29年完整年度数据。用同年同性别全部初婚人数作占比分母。','建议讲法：我们按年份合并官方房价和初婚数据，利用1995—1996年前置数据保留1997—2025年全部29个同期及滞后配对。研究对象是年度汇总变化，不是个人结婚决定。'],
  'tables':[pd.DataFrame([{'数据':'房价','指标':'全港私人住宅年均指数','单位':'1999=100'}, {'数据':'初婚时间','指标':'男女初婚年龄中位数','单位':'岁'}, {'数据':'年龄结构','指标':'25—29、30—34岁初婚占比','单位':'%'}])]},
 {'title':'2 房价与初婚年龄趋势分析','paragraphs':['一句话发现：房价经历升降，初婚年龄总体上升，二者不是简单同步。','建议讲法：男性初婚年龄提高3.3岁，女性提高4.5岁。尤其2021—2025年，房价指数下降26.1%，但男女初婚年龄都再提高0.7岁。因此，我们不能只看长期水平一起高，就认定房价推迟了结婚。'], 'figures':[('figures/01_long_term_trends.png','展示图：长期趋势')]},
 {'title':'3 初婚年龄结构与性别差异分析','paragraphs':['一句话发现：初婚者年龄结构向较高年龄组移动，男女转变时点不同。','建议讲法：女性30—34岁占比从17.5%升至37.8%，提高约20.3个百分点。男性从2010年起、女性从2022年起，这一年龄组持续超过25—29岁组。这里描述初婚者的构成，不是说同龄人有多少比例结婚。'], 'figures':[('figures/03_age_group_shares.png','展示图：男女年龄组占比')]},
 {'title':'4 房价变化与初婚变化的相关分析','paragraphs':['一句话发现：完整样本男性同期负向关联较明显，女性同期较弱。','建议讲法：房价年度涨跌与初婚年龄年度变化的Pearson相关，男性约−0.50、女性约−0.22。负号表示房价涨幅较高时，年龄增幅倾向较小，不表示年龄一定下降。我们补充了HAC回归，但多重比较调整后不能把关系称为已确认。'], 'figures':[('figures/05_same_year_scatter.png','展示图：同期散点')]},
 {'title':'5 一年滞后关联分析','paragraphs':['一句话发现：女性滞后关联比同期更明显，男性没有统一的同期与滞后强弱排序。','建议讲法：上一年房价变化与今年初婚变化配对后，男女Pearson相关分别约−0.38和−0.39。男性的Spearman滞后相关更强，但Pearson同期更强。因此，我们不会简单总结为一年后影响更大，更不会把时间先后当成因果证据。'], 'figures':[('figures/06_lagged_scatter.png','展示图：滞后散点')]},
 {'title':'6 稳健性检验','paragraphs':['一句话发现：负向方向较一致，强弱取决于样本窗口，1997年尤其重要。','建议讲法：去掉1997年，男性同期相关从−0.50变为−0.34；看2004—2025年则约−0.19。逐年剔除后方向仍为负，但大小会改变。研究的贡献是把初婚模式的长期变化和房价短期关联区分开，并说明现有证据能支持到哪里。'], 'figures':[('figures/09_window_comparison.png','展示图：研究窗口比较')]}]
render('六步汇报版 每步一个重点',slides,'汇报版_六步主线')

qa='''# 汇报问答与表述边界

## 建议开场

我们的研究考察香港1997—2025年房价变化与初婚模式的关联。我们先确认男女初婚年龄和年龄结构的长期变化，再检验房价年度波动与初婚变化是否同步或滞后，最后检查结论是否由某些年份决定。

## 建议收尾

香港初婚者的年龄结构明显向较高年龄移动，但房价周期无法单独概括这一长期变化。短期负向关联在部分设定下较明显，同时对年份和方法敏感。我们提供的是可复核的汇总证据与解释边界，为未来加入收入、就业及住房可负担性指标提供基础。

## 为什么这个研究有价值

它回答了三个可检验问题：初婚模式具体怎样变化；房价与初婚在长期水平和短期变化上是否一致；关联是否受关键年份影响。价值不取决于房价系数一定显著，也不取决于证明一个预设方向。

## 相关是负的，是否说明房价高促进结婚

不能。主分析横轴是房价涨跌，纵轴是初婚年龄的年度增幅。负相关表示涨幅较高时年龄增幅倾向较小，不等于年龄水平下降，更不是个体因果效应。收入、就业、迁移和人口组成等遗漏因素仍可能影响结果。

## 是否存在显著关系

完整29年HAC(1)简单回归中，男性同期和女性滞后的未调整p值低于0.05，但四项主比较Holm调整后均未达到0.05。报告保留两种p值和逐模型区间。不能仅挑选未调整p值，也不能把不显著解释为绝对没有关系。

## 为什么Bootstrap有些区间不跨零，但回归调整后仍不显著

Bootstrap估计的是相关系数的不确定性，HAC表估计的是回归斜率的不确定性，且表中还披露多重比较调整。它们不是同一个推断程序。区块Bootstrap区间未经多重比较调整，且仍依赖序列足够稳定，因此用作探索性补充。

## 为什么有29个滞后配对

使用研究期之外的1995—1996年作计算前置值。1997年初婚变化用1996年年龄；对应1996年房价涨跌，又需要1995年房价。1995—1996不算作新增观察年。

## 为什么不删除1997年

1997年属于既定研究期，是合法观察，不因影响大就删除。我们保留它作为主结果，同时披露删除后的结果，以展示敏感性。

## 能否确认男女不同

可以描述初婚年龄、占比和样本相关的差异，不能直接将这些描述称为统计上确认的斜率差异。两个探索性男女差值回归Holm调整后都未达到0.05。

## 为什么年龄组占比不能称为初婚率

分母是当年所有首次结婚者，不是该年龄组全部人口或未婚人口。本数据没有相容的人口风险分母。

## 为什么没有建立复杂模型

只有29年数据，多参数动态模型容易不稳定。本项目以简洁的同期、滞后模型和诊断支撑解释。HAC调整不解决因果识别问题。

## 图表如何取舍

按六步展示：第一步用一张数据口径表，第二至第六步各用一张图，共五张核心图。回归置信区间、年度变化、男女年龄差及诊断放补充页。所有数值统一使用V2，不能混用旧28年版本。
'''
(OUT/'汇报问答与表述边界.md').write_text(qa)
(ROOT/'README_v2.md').write_text('''# 香港房价与初婚分析 V2

主报告：outputs_v2/分析结果报告_v2.html。汇报阅读版：outputs_v2/汇报版_六步主线.html。
HTML内嵌所有图表，可单独分享。六步讲法、图和数据口径已对应。问答见outputs_v2/汇报问答与表述边界.md。

## 复现

Python 3.12，安装requirements.txt。项目根目录运行：

```bash
python -m pip install -r requirements.txt
python research/prepare_data_v2.py
python analysis/run_analysis_v2.py
python analysis/build_report_v2.py
```

或打开outputs_v2/housing_marriage_analysis_v2.ipynb，从头运行。Notebook包含所有计算定义和结果。

V2保留1995—1996作前置值，主比较1997—2025年29组；1998—2025年等窗口用于稳健性。
Spearman初婚年龄差分按原始0.1岁精度恢复并列值。四主模型Holm调整，八探索性年龄组模型BH调整，两个探索性性别斜率对比单独Holm调整。所有敏感性设定完整披露。

data/raw保留官方原文件；research/rvd_price_indices.xlsx是官方XLS的读取副本。如重新下载XLS，需要先用LibreOffice转换到此路径。来源URL、原始下载日期及SHA256见research/source_register_v2.json。

outputs_v2/figures有9张PNG主图和相应SVG，appendix有6张附图以及诊断CSV。主报告只选取其中8张用于叙述，其余可供补充页使用。统计结果保留具体年份、样本量和多种口径。不要把不同样本或不同类型区间混合解释。
''')
print('Built V2 full report, six-step presentation companion and Q&A.')
if '--package' in sys.argv:
    target=ROOT/'香港房价与初婚_六步分析_V2.zip'
    files=[ROOT/'requirements.txt',ROOT/'README_v2.md']
    files += [ROOT/'analysis'/f for f in ['run_analysis_v2.py','build_notebook_v2.py','build_report_v2.py','validate_v2.py']]
    files += [ROOT/'research'/f for f in ['prepare_data_v2.py','source_register_v2.json','variable_dictionary_v2.csv','rvd_price_indices.xlsx']]
    files += list((ROOT/'data/raw').glob('*'))+[ROOT/'data/processed/annual_1997_2025_v2.csv']
    files += [f for f in OUT.rglob('*') if f.is_file() and f.suffix not in ['.jpg']]
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for f in files:z.write(f,'housing_marriage_v2/'+str(f.relative_to(ROOT)))
    print('Packaged:',target)
