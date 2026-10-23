from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Read the professor's airline dataset; the CSV is included beside this script.
DATA_URL = "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/IBMDeveloperSkillsNetwork-DV0101EN-SkillsNetwork/Data%20Files/airline_data.csv"
DATA_FILE = Path(__file__).resolve().with_name('airline_data.csv')
airline_data = pd.read_csv(
    DATA_FILE if DATA_FILE.exists() else DATA_URL,
    encoding='ISO-8859-1',
    dtype={'Div1Airport': str, 'Div1TailNum': str,
           'Div2Airport': str, 'Div2TailNum': str},
)

from dash.exceptions import PreventUpdate

# Practice: saved as flight_details.py with the required updated heading (35px).
app = dash.Dash(__name__)
app.layout = html.Div(children=[
    html.H1('Flight Details Statistics Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 35}),
    html.Div(['Input Year: ', dcc.Input(
        id='input-year', value=2010, type='number', min=2010, max=2020, step=1,
        style={'height': '35px', 'font-size': 30})], style={'font-size': 30}),
    html.Br(), html.Br(),
    html.Div([
        html.Div(dcc.Graph(id='carrier-plot'), style={'width': '50%'}),
        html.Div(dcc.Graph(id='weather-plot'), style={'width': '50%'}),
    ], style={'display': 'flex'}),
    html.Div([
        html.Div(dcc.Graph(id='nas-plot'), style={'width': '50%'}),
        html.Div(dcc.Graph(id='security-plot'), style={'width': '50%'}),
    ], style={'display': 'flex'}),
    html.Div(dcc.Graph(id='late-plot'), style={'width': '65%'}),
])

# Task 4: Select the year and calculate monthly averages for each airline.
def compute_info(airline_data, entered_year):
    df = airline_data[airline_data['Year'] == int(entered_year)]
    avg_car = df.groupby(['Month', 'Reporting_Airline'])['CarrierDelay'].mean().reset_index()
    avg_weather = df.groupby(['Month', 'Reporting_Airline'])['WeatherDelay'].mean().reset_index()
    avg_NAS = df.groupby(['Month', 'Reporting_Airline'])['NASDelay'].mean().reset_index()
    avg_sec = df.groupby(['Month', 'Reporting_Airline'])['SecurityDelay'].mean().reset_index()
    avg_late = df.groupby(['Month', 'Reporting_Airline'])['LateAircraftDelay'].mean().reset_index()
    return avg_car, avg_weather, avg_NAS, avg_sec, avg_late

# Task 5: One year input updates all five graph figures.
@app.callback([
    Output('carrier-plot', 'figure'),
    Output('weather-plot', 'figure'),
    Output('nas-plot', 'figure'),
    Output('security-plot', 'figure'),
    Output('late-plot', 'figure'),
], Input('input-year', 'value'))
def get_graph(entered_year):
    if entered_year is None or not 2010 <= entered_year <= 2020 or int(entered_year) != entered_year:
        raise PreventUpdate
    avg_car, avg_weather, avg_NAS, avg_sec, avg_late = compute_info(airline_data, entered_year)
    carrier_fig = px.line(avg_car, x='Month', y='CarrierDelay', color='Reporting_Airline',
                          title='Average carrier delay time (minutes) by airline')
    weather_fig = px.line(avg_weather, x='Month', y='WeatherDelay', color='Reporting_Airline',
                          title='Average weather delay time (minutes) by airline')
    nas_fig = px.line(avg_NAS, x='Month', y='NASDelay', color='Reporting_Airline',
                      title='Average NAS delay time (minutes) by airline')
    sec_fig = px.line(avg_sec, x='Month', y='SecurityDelay', color='Reporting_Airline',
                      title='Average security delay time (minutes) by airline')
    late_fig = px.line(avg_late, x='Month', y='LateAircraftDelay', color='Reporting_Airline',
                       title='Average late aircraft delay time (minutes) by airline')
    return [carrier_fig, weather_fig, nas_fig, sec_fig, late_fig]

# Task 6: Run the app; press Ctrl+C in the terminal to stop.
if __name__ == '__main__':
    app.run()
