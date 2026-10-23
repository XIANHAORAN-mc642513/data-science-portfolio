# Module 05 Practice Project — Lab02

Student: MC642380 GUO QIZHEN

## Run

Use Python with the packages in `requirements.txt`. The configured `um-dash`
environment already has these packages. Keep `Historical_Wildfires.csv` beside
`Dash_wildfire.py`.

```bash
python Dash_wildfire.py
```

Open http://127.0.0.1:8050/ in a browser. Stop any previous Dash application on
port 8050 first. Press Ctrl+C in the terminal to stop this application.

For a new environment only:

```bash
python -m pip install -r requirements.txt
```

## Task coverage

- 2.1: Australia Wildfire Dashboard; centered, #503D36, 26px.
- 2.2: Seven region radio options, default NSW; year dropdown 2005–2020,
  default 2005. IDs are `region` and `year`.
- 2.3: Empty `plot1` and `plot2` divisions in a flex container.
- 2.4: Region and year values update both divisions' `children` properties.
- 2.5: Filter by selected region and year. Group by month and calculate the
  mean of `Estimated_fire_area` for the pie chart and `Count` for the bar chart.
  Return two `dcc.Graph` components.

The month grouping follows the professor's supplied solution. Both charts show
monthly averages, not monthly sums. Changing either input updates both charts.

## Dataset and assignment

The CSV is an unmodified copy of the dataset used in Practice Lab01.

- Assignment: https://ummoodle.um.edu.mo/mod/page/view.php?id=1241705
- Dataset: https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/Historical_Wildfires.csv

## Screenshot preparation

The assignment asks for screenshots per task; it does not prescribe a fixed
number of images. Suggested coverage:

1. Layout code covering tasks 2.1–2.3.
2. Callback code covering tasks 2.4–2.5.
3. Default dashboard with NSW / 2005 and both charts visible.
4. Changed region and year with both updated charts visible.

Code screenshots can be split if needed for readability. Save genuine screenshots
in `Screenshots/`. Local completion does not upload anything to Moodle.

AI assistance was used to draft and check the implementation. Review and
understand the code before submission.
