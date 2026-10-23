# CISC7204 Assignment02 Module04 Lab02

Student: MC642380 GUO QIZHEN

## Contents and completed work

Tasks 1-6: read airline data; sample 500 rows with random_state=42; plot Flights by DistanceGroup; create H1, P and Graph components inside a Div; run the application.

Practice tasks: the final heading is Airline On-time Performance Dashboard, font size 50. The initial Airline Dashboard heading (size 40) was checked before the practice update. The final version was relaunched with the complete CSV. Stop the server with Ctrl+C in its terminal (or the PyCharm Stop button).

The chart uses Flights, as Lab02 requests. This differs from the Month-weighted pie chart explicitly requested by Lab01.

## Run

The tested environment is Python 3.12 with the dependencies in requirements.txt. The existing um-dash environment is ready to use:

```bash
conda activate um-dash
python dash_basics.py
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
