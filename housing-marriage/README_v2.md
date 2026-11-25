# 香港房价与初婚分析 V2

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
