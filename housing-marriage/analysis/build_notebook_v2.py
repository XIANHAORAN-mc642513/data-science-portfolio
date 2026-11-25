"""Build a self-contained, six-step notebook and execute it with a local kernel."""
from pathlib import Path
import sys, os, json, ast
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.analysis_deps'))
os.environ['PYTHONPATH']=str(ROOT/'.analysis_deps')
os.environ['MPLCONFIGDIR']=str(ROOT/'.cache/matplotlib')
os.environ['IPYTHONDIR']=str(ROOT/'.cache/ipython')
os.environ['JUPYTER_RUNTIME_DIR']=str(ROOT/'.cache/jupyter_runtime')
os.environ['PYDEVD_DISABLE_FILE_VALIDATION']='1'
import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

source=(ROOT/'analysis/run_analysis_v2.py').read_text()
tree=ast.parse(source)
# Carry the exact computation definitions into the notebook, rather than hiding analysis in an external import.
main_node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='main')
definitions='\n'.join(source.splitlines()[:main_node.lineno-1])
definitions=definitions.replace('ROOT = Path(__file__).resolve().parents[1]',
    "ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'data/raw/115-01011.json').exists())")

cells=[nbf.v4.new_markdown_cell('''# 香港房价变化与初婚模式分析

1997—2025年官方年度数据。六步主线：描述、趋势、结构、同期关联、一年滞后、稳健性。

**范围**：描述统计29年；同期与滞后比较统一1997—2025年29个配对。1995—1996年仅作变化及滞后计算基期。

**主结果**：男女初婚年龄的年度变化。四个年龄组占比变化属于探索性结果。

**推断**：OLS系数，Bartlett HAC(1)标准误，小样本n/(n−k)修正，t(n−k)置信区间。四个主要系数p值用Holm调整，八个探索性系数用BH调整。相关检验的iid p值只作参考，不据此下结论。所有结果均为关联。初婚年龄差分按0.1岁精度恢复并列值，再计算Spearman。1998—2025年作为敏感性窗口，而不代替完整研究期。

在解压后的项目目录中运行此Notebook，依赖见requirements.txt。定义单元包含全部计算代码，原数据保存在data/raw。'''),
nbf.v4.new_code_cell(definitions,metadata={'jupyter':{'source_hidden':True}}),
nbf.v4.new_code_cell("from IPython.display import display, Image, Markdown\nimport runpy\nrunpy.run_path(str(ROOT / 'research/prepare_data_v2.py'))\nd = load_data()\nd.to_csv(OUT / 'annual_analysis_data.csv', encoding='utf-8-sig', float_format='%.10g')\nprint('Data checks passed: 29 years; common comparison: 29 years.')\ndisplay(d.head())"),
nbf.v4.new_markdown_cell('## 1 描述性统计\n标准差采用样本标准差。占比的分母是同年同性别全部初婚人数。'),
nbf.v4.new_code_cell("desc = descriptive(d)\ndisplay(desc.round(3))"),
nbf.v4.new_markdown_cell('## 2 房价与初婚年龄趋势分析\n水平图保留真实单位，年度变化图用于区分长期趋势与短期变化。'),
nbf.v4.new_code_cell("trend_figures(d)\nfor name in ['01_long_term_trends', '02_annual_changes']:\n    display(Image(filename=str(FIG / (name + '.png'))))"),
nbf.v4.new_markdown_cell('## 3 初婚年龄结构与性别差异\n25—29和30—34岁占比之和不要求为100%。男女中位数差不代表夫妻年龄差。'),
nbf.v4.new_code_cell("structure(d)\nfor name in ['03_age_group_shares', '04_gender_age_gap']:\n    display(Image(filename=str(FIG / (name + '.png'))))\ndisplay(pd.read_csv(TAB / '03_age_share_crossings.csv'))"),
nbf.v4.new_markdown_cell('## 4 房价变化与初婚变化的同期关联\n每个回归为一个解释变量加常数项，横轴单位是房价增长的百分点。主分析不加入未取得的收入、失业等控制变量。'),
nbf.v4.new_code_cell("results, models = association(d)\ndisplay(results[results.timing.eq('same_year')].round(4))\ndisplay(Image(filename=str(FIG / '05_same_year_scatter.png')))"),
nbf.v4.new_markdown_cell('## 5 一年滞后关联\n用g_(t−1)解释初婚变化ΔA_t，与同期采用相同结果年份。此处分别估计同期和滞后简单回归，不声称识别独立因果效应。'),
nbf.v4.new_code_cell("display(results[results.timing.eq('lag1')].round(4))\nfor name in ['06_lagged_scatter', '07_regression_effect_sizes']:\n    display(Image(filename=str(FIG / (name + '.png'))))\ndisplay(pd.read_csv(TAB / '03_gender_slope_difference_exploratory.csv').round(4))"),
nbf.v4.new_markdown_cell('## 6 稳健性与模型诊断\n先在连续日历年计算变化和滞后，再筛选年份。HAC按照真实年份间隔计算，不把2019和2023当作相邻年。逐年剔除仅用于敏感性诊断。ADF最多1阶滞后并由AIC选择，KPSS固定1阶；水平序列含趋势，变化序列含常数。检验在小样本下可能没有明确结论。'),
nbf.v4.new_code_cell("stationarity, diag = diagnostics(d, models)\nsens, loo = sensitivity(d, results)\nboot = supplements(d, results, sens)\ndisplay(sens[sens.outcome.isin(PRIMARY)][['outcome','timing','scenario','n','pearson_r','spearman_rho','change_per_10pp_price','hac_p']].round(4))\ndisplay(loo[loo.outcome.isin(PRIMARY)].round(4))\ndisplay(Image(filename=str(FIG / '09_window_comparison.png')))\ndisplay(stationarity.round(4))\ndisplay(diag[diag.outcome.isin(PRIMARY)].round(4))"),
nbf.v4.new_markdown_cell('## 阅读结果\n中文解释、限制、图表说明及完整数值表见同目录的分析结果报告_v2.html。显著性不代表因果，非显著性也不证明不存在关系。初婚年龄按0.1岁报告，差分会受舍入影响。')]
nb=nbf.v4.new_notebook(cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':'3.12'}})
dest=ROOT/'outputs_v2/housing_marriage_analysis_v2.ipynb'
nbf.write(nb,dest)
kernel_dir=ROOT/'.cache/kernels/analysis-python'
kernel_dir.mkdir(parents=True,exist_ok=True)
(kernel_dir/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
    'display_name':'Analysis Python','language':'python','env':{k:os.environ[k] for k in ['PYTHONPATH','MPLCONFIGDIR','IPYTHONDIR','JUPYTER_RUNTIME_DIR','PYDEVD_DISABLE_FILE_VALIDATION']}}))
ksm=KernelSpecManager(kernel_dirs=[str(ROOT/'.cache/kernels')])
km=KernelManager(kernel_name='analysis-python',kernel_spec_manager=ksm)
client=NotebookClient(nb,timeout=180,kernel_manager=km,resources={'metadata':{'path':str(ROOT)}})
client.execute()
nb.metadata.kernelspec={'name':'python3','display_name':'Python 3','language':'python'}
nbf.validate(nb)
assert not any(o.output_type=='error' for c in nb.cells if c.cell_type=='code' for o in c.outputs)
nbf.write(nb,dest)
print('Executed and validated notebook:',dest)
