# CISC7204 Assignment02 Module04 Lab04

Student: MC642380 GUO QIZHEN

## Contents and completed work

Tasks 1-6: Flight Delay Time Statistics; year input (default 2010, allowed 2010-2020); five monthly average delay charts by airline. Outputs are carrier-plot, weather-plot, nas-plot, security-plot and late-plot, arranged as 2/2/1 graphs.

Practice tasks (external complete instructions): flight_details.py is the saved practice version. It changes the H1 heading to Flight Details Statistics Dashboard and its font size to 35, while retaining all five graphs and computations. Run this file to see the final practice heading.

Run only one script at a time. Stop with Ctrl+C before running the other script.

## Run

The tested environment is Python 3.12 with the dependencies in requirements.txt. The existing um-dash environment is ready to use:

```bash
conda activate um-dash
python flight_delay.py
```

Alternatively, use `/opt/anaconda3/envs/um-dash/bin/python` as the PyCharm interpreter.

Open http://127.0.0.1:8050 in the browser after the console reports the server is running. All scripts use port 8050, so run one at a time. To stop a running terminal server, press **Ctrl+C**; in PyCharm use **Stop**.

For a fresh Python environment, install the dependencies first:

```bash
python -m pip install -r requirements.txt
```

## Data

The complete professor-provided airline_data.csv is included: 9,827,502 bytes, 27,000 rows and 110 columns. Scripts resolve this file relative to their own location, so moving or extracting the entire project folder retains the data path. If the file is absent, the script falls back to the original public URL:

https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/airline_data.csv

Do not modify the CSV while an application is starting. No API key is needed.
