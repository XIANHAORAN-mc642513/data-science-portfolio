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

# Task 2: HTML title, numeric input and output graph.
app = dash.Dash(__name__)
app.layout = html.Div(children=[
    html.H1('Airline Performance Dashboard',
            style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40}),
    html.Div(['Input Year: ', dcc.Input(
        id='input-year', value=2010, type='number', min=2010, max=2020, step=1,
        style={'height': '50px', 'font-size': 35})], style={'font-size': 40}),
    html.Br(), html.Br(),
    html.Div(dcc.Graph(id='line-plot')),
])

# Task 3: Input year -> monthly average arrival delay -> line chart.
@app.callback(Output('line-plot', 'figure'), Input('input-year', 'value'))
def get_graph(entered_year):
    if entered_year is None or not 2010 <= entered_year <= 2020 or int(entered_year) != entered_year:
        raise PreventUpdate
    df = airline_data[airline_data['Year'] == int(entered_year)]
    line_data = df.groupby('Month')['ArrDelay'].mean().reset_index()
    fig = go.Figure(data=go.Scatter(
        x=line_data['Month'], y=line_data['ArrDelay'], mode='lines',
        line=dict(color='green')))
    fig.update_layout(title='Month vs Average Flight Delay Time',
                      xaxis_title='Month', yaxis_title='ArrDelay')
    return fig

# Press Ctrl+C in the terminal to stop the app.
if __name__ == '__main__':
    app.run()
