from pathlib import Path

import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px


# Load the original dataset stored beside this script.
data_file = Path(__file__).resolve().with_name("Historical_Wildfires.csv")
df = pd.read_csv(data_file)

# Extract month names and years.
dates = pd.to_datetime(df["Date"])
df["Month"] = dates.dt.month_name()
df["Year"] = dates.dt.year

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True

app.layout = html.Div(children=[
    # TASK 2.1: Add the dashboard title.
    html.H1(
        "Australia Wildfire Dashboard",
        style={"textAlign": "center", "color": "#503D36", "font-size": 26},
    ),
    html.Div([
        # First inner division: input controls.
        html.Div([
            # TASK 2.2: Add the region radio items and year dropdown.
            html.Div([
                html.H2("Select Region:", style={"margin-right": "2em"}),
                dcc.RadioItems(
                    options=[
                        {"label": "New South Wales", "value": "NSW"},
                        {"label": "Northern Territory", "value": "NT"},
                        {"label": "Queensland", "value": "QL"},
                        {"label": "South Australia", "value": "SA"},
                        {"label": "Tasmania", "value": "TA"},
                        {"label": "Victoria", "value": "VI"},
                        {"label": "Western Australia", "value": "WA"},
                    ],
                    value="NSW",
                    id="region",
                    inline=True,
                ),
            ]),
            html.Div([
                html.H2("Select Year:", style={"margin-right": "2em"}),
                dcc.Dropdown(
                    options=sorted(df["Year"].unique().tolist()),
                    value=2005,
                    id="year",
                    clearable=False,
                ),
            ]),
        ]),
        # Second inner division: two initially empty chart containers.
        # TASK 2.3: Add both output divisions side by side.
        html.Div([
            html.Div([], id="plot1", style={"width": "50%"}),
            html.Div([], id="plot2", style={"width": "50%"}),
        ], style={"display": "flex"}),
    ]),
])


# TASK 2.4: Connect both input values to both output children.
@app.callback(
    [
        Output(component_id="plot1", component_property="children"),
        Output(component_id="plot2", component_property="children"),
    ],
    [
        Input(component_id="region", component_property="value"),
        Input(component_id="year", component_property="value"),
    ],
)
# TASK 2.5: Filter by region and year, then calculate monthly means.
def reg_year_display(input_region, input_year):
    region_data = df[df["Region"] == input_region]
    y_r_data = region_data[region_data["Year"] == input_year]

    est_data = (
        y_r_data.groupby("Month")["Estimated_fire_area"]
        .mean()
        .reset_index()
    )
    fig1 = px.pie(
        est_data,
        values="Estimated_fire_area",
        names="Month",
        title="{} : Monthly Average Estimated Fire Area in year {}".format(
            input_region, input_year
        ),
    )

    veg_data = (
        y_r_data.groupby("Month")["Count"]
        .mean()
        .reset_index()
    )
    fig2 = px.bar(
        veg_data,
        x="Month",
        y="Count",
        title=(
            "{} : Average Count of Pixels for Presumed Vegetation Fires "
            "in year {}"
        ).format(input_region, input_year),
    )

    return [dcc.Graph(figure=fig1), dcc.Graph(figure=fig2)]


if __name__ == "__main__":
    app.run()
