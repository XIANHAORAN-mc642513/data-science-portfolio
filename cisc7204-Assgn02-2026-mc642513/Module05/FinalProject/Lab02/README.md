# Module 05 Final Project — Lab02

Student: MC642380 GUO QIZHEN

The implementation completes the professor's supplied
`DV0101EN-Final-Assign-Part-2-Questions.py` skeleton. It uses the original
synthetic automobile-sales dataset, included unchanged beside the script.

## Run in Theia IDE

Open this Lab02 folder in Theia. Use a terminal with the configured `um-dash`
Python environment, which already contains the dependencies.

```bash
python DV0101EN-Final-Assign-Part-2-Questions.py
```

Open http://127.0.0.1:8050/. Stop any other Dash app using this port first.
Press Ctrl+C in the terminal to stop this application. A new environment can
install the listed dependencies with `python -m pip install -r requirements.txt`.

## Required behavior

- TASK 2.1: Exact title, centered, #503D36, 24px.
- TASK 2.2: Separate report and year dropdown divisions with the required IDs,
  option labels, placeholders and initial values.
- TASK 2.3: `output-container`, class `chart-grid`, flex layout; two rows of
  two charts for each report.
- TASK 2.4: Year selection is enabled only for Yearly Statistics. The output
  callback responds to both the report type and selected year.
- TASK 2.5: Recession-only annual mean sales, vehicle-type mean sales,
  vehicle-type advertising sums, and unemployment/type mean sales.
- TASK 2.6: Whole-period annual mean sales; selected-year monthly total sales,
  vehicle-type mean sales, and vehicle-type advertising sums.

The initial page waits for a report. Choose Yearly Statistics and then a year,
or choose Recession Period Statistics to immediately display its four graphs.

## Source inconsistencies resolved

- The introductory text says 1980–2013, but TASK 2.2, the supplied skeleton and
  the actual CSV use 1980–2023. The dropdown follows the detailed task and
  skeleton: 1980–2023.
- The introductory enabled/disabled explanation reverses the booleans. TASK
  2.4 correctly describes the `disabled` property: False for Yearly Statistics,
  True otherwise.
- The monthly-chart skeleton starts with `data.groupby(...)`, but the report
  description requires monthly totals for the selected year. This implementation
  therefore groups `yearly_data` for that chart.
- Unused skeleton imports are omitted; more-itertools is not used by the app.

## Sources and screenshots

- Professor's detailed instructions: https://ummoodle.um.edu.mo/mod/page/view.php?id=1241711
- Original data: https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/d51iMGfp_t0QpO30Lym-dw/automobile-sales.csv

The detailed instructions explicitly name `RecessionReportgraphs.png` and
`YearlyReportgraphs.png`. These should show the actual running app, both dropdowns
and all four clearly readable graphs in the selected mode. Also retain code
screenshots covering tasks 2.1–2.6 as instructed. Screenshots must be actual UI
captures; chart exports or generated illustrations are not substitutes.

AI assistance was used to draft and check the implementation. Review and
understand the code before submission. No files have been submitted to Moodle.
