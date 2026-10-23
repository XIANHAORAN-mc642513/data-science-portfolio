from pathlib import Path
from textwrap import wrap

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px


# Read the unmodified dataset included beside this script.
DATA_FILE = Path(__file__).resolve().with_name('automobile-sales.csv')
data = pd.read_csv(DATA_FILE)
MONTH_ORDER = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
year_list = list(range(1980, 2024))

app = dash.Dash(__name__)
app.title = 'Automobile Sales Statistics Dashboard'

dropdown_options = [
    {'label': 'Yearly Statistics', 'value': 'Yearly Statistics'},
    {'label': 'Recession Period Statistics', 'value': 'Recession Period Statistics'},
]

app.layout = html.Div([
    # TASK 2.1: Exact dashboard title and required styling.
    html.H1(
        'Automobile Sales Statistics Dashboard',
        style={'textAlign': 'center', 'color': '#503D36', 'font-size': 24},
    ),
    # TASK 2.2: Each dropdown is in a separate division.
    html.Div([
        html.Label('Select Statistics:', htmlFor='dropdown-statistics'),
        dcc.Dropdown(
            id='dropdown-statistics', options=dropdown_options,
            value='Select Statistics', placeholder='Select a report type',
            style={'width': '80%', 'fontSize': 20},
            clearable=False,
        ),
    ]),
    html.Div([
        html.Label('Select Year:', htmlFor='select-year'),
        dcc.Dropdown(
            id='select-year',
            options=[{'label': year, 'value': year} for year in year_list],
            value='Select-year', placeholder='Select-year', disabled=True,
            style={'width': '80%', 'fontSize': 20},
            clearable=False,
        ),
    ], style={'marginTop': '12px'}),
    # TASK 2.3: Both report types render four graphs in two rows.
    html.Div([
        html.Div(
            id='output-container', className='chart-grid',
            style={'display': 'flex', 'flexDirection': 'column'},
        ),
    ]),
])


def chart_grid(figures, prefix):
    """Return the two flex rows used by both four-chart reports."""
    graphs = []
    for number, figure in enumerate(figures, start=1):
        title = '<br>'.join(wrap(figure.layout.title.text, width=54))
        figure.update_layout(
            height=420, margin={'l': 60, 'r': 25, 't': 80, 'b': 70},
            title={'text': title, 'font': {'size': 15}},
        )
        graphs.append(html.Div(
            dcc.Graph(
                id=f'{prefix}-chart-{number}', figure=figure,
                config={'displayModeBar': False},
            ),
            style={'width': '50%', 'minWidth': 0},
        ))
    return [
        html.Div(graphs[:2], className='chart-item', style={'display': 'flex'}),
        html.Div(graphs[2:], className='chart-item', style={'display': 'flex'}),
    ]


# TASK 2.4: False enables year selection; True disables it.
@app.callback(
    Output(component_id='select-year', component_property='disabled'),
    Input(component_id='dropdown-statistics', component_property='value'),
)
def update_input_container(selected_statistics):
    if selected_statistics == 'Yearly Statistics':
        return False
    return True


@app.callback(
    Output(component_id='output-container', component_property='children'),
    [Input(component_id='dropdown-statistics', component_property='value'),
     Input(component_id='select-year', component_property='value')],
)
def update_output_container(selected_statistics, input_year):
    # TASK 2.5: Recession statistics use all rows flagged Recession == 1.
    if selected_statistics == 'Recession Period Statistics':
        recession_data = data[data['Recession'] == 1]

        yearly_rec = recession_data.groupby('Year', as_index=False)['Automobile_Sales'].mean()
        R_chart1 = px.line(
            yearly_rec, x='Year', y='Automobile_Sales',
            title='Average Automobile Sales Fluctuation over Recession Period',
            labels={'Automobile_Sales': 'Average Automobile Sales'},
        )

        average_sales = recession_data.groupby(
            'Vehicle_Type', as_index=False
        )['Automobile_Sales'].mean()
        R_chart2 = px.bar(
            average_sales, x='Vehicle_Type', y='Automobile_Sales',
            title='Average Vehicles Sold by Vehicle Type during Recessions',
            labels={'Vehicle_Type': 'Vehicle Type',
                    'Automobile_Sales': 'Average Automobile Sales'},
        )

        exp_rec = recession_data.groupby(
            'Vehicle_Type', as_index=False
        )['Advertising_Expenditure'].sum()
        R_chart3 = px.pie(
            exp_rec, values='Advertising_Expenditure', names='Vehicle_Type',
            title='Total Advertising Expenditure Share during Recessions',
        )

        unemp_data = recession_data.groupby(
            ['unemployment_rate', 'Vehicle_Type'], as_index=False
        )['Automobile_Sales'].mean()
        R_chart4 = px.bar(
            unemp_data, x='unemployment_rate', y='Automobile_Sales',
            color='Vehicle_Type', barmode='group',
            labels={'unemployment_rate': 'Unemployment Rate (%)',
                    'Automobile_Sales': 'Average Automobile Sales',
                    'Vehicle_Type': 'Vehicle Type'},
            title='Effect of Unemployment Rate on Vehicle Type and Sales',
        )
        return chart_grid([R_chart1, R_chart2, R_chart3, R_chart4], 'recession')

    # TASK 2.6: Wait for a valid year before rendering the yearly report.
    if selected_statistics == 'Yearly Statistics' and input_year in year_list:
        yearly_data = data[data['Year'] == input_year]

        # Plot 1 deliberately covers the whole period, as required.
        yas = data.groupby('Year', as_index=False)['Automobile_Sales'].mean()
        Y_chart1 = px.line(
            yas, x='Year', y='Automobile_Sales',
            title='Yearly Average Automobile Sales for the Whole Period',
            labels={'Automobile_Sales': 'Average Automobile Sales'},
        )

        # Plot 2 totals only the selected year's monthly sales.
        mas = yearly_data.groupby('Month')['Automobile_Sales'].sum().reindex(MONTH_ORDER).reset_index()
        Y_chart2 = px.line(
            mas, x='Month', y='Automobile_Sales',
            title=f'Total Monthly Automobile Sales in {input_year}',
            labels={'Automobile_Sales': 'Total Automobile Sales'},
            category_orders={'Month': MONTH_ORDER},
        )

        avr_vdata = yearly_data.groupby(
            'Vehicle_Type', as_index=False
        )['Automobile_Sales'].mean()
        Y_chart3 = px.bar(
            avr_vdata, x='Vehicle_Type', y='Automobile_Sales',
            title=f'Average Vehicles Sold by Vehicle Type in {input_year}',
            labels={'Vehicle_Type': 'Vehicle Type',
                    'Automobile_Sales': 'Average Automobile Sales'},
        )

        exp_data = yearly_data.groupby(
            'Vehicle_Type', as_index=False
        )['Advertising_Expenditure'].sum()
        Y_chart4 = px.pie(
            exp_data, values='Advertising_Expenditure', names='Vehicle_Type',
            title=f'Total Advertising Expenditure for Each Vehicle in {input_year}',
        )
        return chart_grid([Y_chart1, Y_chart2, Y_chart3, Y_chart4], 'yearly')

    return None


if __name__ == '__main__':
    app.run(debug=False)
