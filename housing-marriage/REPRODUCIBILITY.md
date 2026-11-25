# Reproduction check — 25 November 2026

The supplied project was copied into a separate working directory and tested using Python 3.12 on macOS. The release preserves the original V2 outputs; the check did not overwrite them.

All four documented commands completed successfully:

1. `python research/prepare_data_v2.py`
2. `python analysis/run_analysis_v2.py`
3. `python analysis/build_report_v2.py`
4. `python analysis/validate_v2.py`

The validation passed for 29 annual records (1997–2025), no missing cells, three raw-file SHA256 hashes, 87 price/growth values, 58 median ages, 58 age differences, 232 age-share values/changes, and 12 models. Four primary models use Holm adjustment; eight exploratory age-share models use BH adjustment. The run generated nine main figures and six appendix figures.

The included Notebook has eight executed code cells and no stored error outputs. Its structure and recorded outputs were validated; a separate Notebook-kernel rerun was not performed. The Python analysis pipeline was rerun in full.

## Verified dependency versions

| Package | Version |
| --- | --- |
| numpy | 2.3.5 |
| pandas | 2.2.3 |
| scipy | 1.18.1 |
| statsmodels | 0.15.0 |
| matplotlib | 3.11.2 |
| nbformat | 5.11.1 |
| nbclient | 0.11.0 |
| openpyxl | 3.1.5 |
| ipykernel | 7.4.0 |

Use the supplied `requirements.txt` and Python 3.12. Source data are the supplied snapshot; this check does not validate later revisions published by the data providers.
