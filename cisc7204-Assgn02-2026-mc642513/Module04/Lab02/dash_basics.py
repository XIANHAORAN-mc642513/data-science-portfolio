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

# Task 1: Sample 500 rows reproducibly and create the distance-group pie chart.
data = airline_data.sample(n=500, random_state=42)
fig = px.pie(data, values='Flights', names='DistanceGroup',
             title='Distance group proportion by flights')

# Tasks 2-5 and Practice 1: HTML heading updated to the required final title (50px).
app = dash.Dash(__name__)
app.layout = html.Div(children=[
    html.H1('Airline On-time Performance Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 50}),
    html.P('Proportion of distance group (250 mile distance interval group) by flights.',
           style={'textAlign': 'center', 'color': '#F57241'}),
    dcc.Graph(figure=fig),
])

# Task 6: Run; press Ctrl+C in the terminal to stop the application.
if __name__ == '__main__':
    app.run()
