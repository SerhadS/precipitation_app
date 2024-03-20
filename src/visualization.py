import pandas as pd
import numpy as np
import os
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pickle
from utils import get_db_engine

# Filter the DataFrame to include data from 1994 to 2014
start_year = 1994
end_year = 2014
year = 1994

sql = """
SELECT a.*, b.closest_country, b.closest_city FROM extreme_rainfall_events a
LEFT JOIN
(
SELECT * FROM map_coord_to_loc
) b
ON a.lat=b.lat AND a.lon=b.lon    
WHERE a.datetime BETWEEN '{}-01-01' AND '{}-01-01'
ORDER BY a.pr_mm
"""

sql_year_country = """
SELECT a.*, b.closest_country, b.closest_city FROM extreme_rainfall_events a
LEFT JOIN
(
SELECT * FROM map_coord_to_loc
) b
ON a.lat=b.lat AND a.lon=b.lon    
WHERE a.datetime BETWEEN '{}-01-01' AND '{}-01-01'
AND b.closest_country='{}'
"""

sql_countries = """
SELECT DISTINCT closest_country AS country 
FROM map_coord_to_loc
"""


data_folder = '../data'

# Create a SQLAlchemy engine
engine = get_db_engine()

countries_list = [x for x in sorted(pd.read_sql(sql_countries, engine).country.unique()) if x!='']

# load data to plot return values
with open(os.path.join(data_folder, 'country_pr_return_periods.pickle'), 'rb') as f:
    pr_return_data = pickle.load(f)


# df = df[df.pr_mm>=df.pr_mm.quantile(0.99)]
# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='world-map'),
        ], lg=9),  # Map column takes 6 out of 12 columns (medium-sized)

        dbc.Col([
            html.H6('Top 10 Countries with Most Events'),
            html.Div(id='top-countries-table')
        ], lg=3)  # Table column takes 6 out of 12 columns (medium-sized)
    ], className="justify-content-center", align="center"),
    dbc.Row([
        html.Br(),
        dcc.Slider(
                id='year-slider',
                min=start_year,
                max=end_year,
                value=start_year,
                marks={str(year): str(year) for year in range(start_year, end_year + 1)},
                step=None
            ),
        html.Br(),
    ]),
    dbc.Row([
        html.Hr(),
        html.Br(),
        dcc.Dropdown(
                id='country-dropdown',
                options=[{'label': country, 'value': country} for country in countries_list],
                value=countries_list[0],  # Default selected country
                clearable=False,
                style={'width': '200px'}
            )
        
    ], className="justify-content-center", align="center"),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='precipitation-histogram')
        ], lg=6),# Center the dropdown and graph
        dbc.Col([
            dcc.Graph(id='precipitation-return')
        ], lg=6),# Center the dropdown and graph
    ], className="justify-content-center", align="center"),

])

selected_year = 1994



@app.callback(
    [Output('world-map', 'figure'),
     Output('top-countries-table', 'children')],
    [Input('year-slider', 'value')]
)
def update_map_and_table(selected_year):
    global df
    df = update_df(selected_year)
    filtered_df = df[df.pr_mm>=df.pr_mm.quantile(0.99)]
    
    fig = px.scatter_mapbox(filtered_df, lat='lat', lon='lon', color='pr_mm',
                         title=f'99th % of Extreme Rainfall Events in {selected_year}',
                         hover_name='datetime', hover_data=['closest_country', 'pr_mm'], color_continuous_scale=px.colors.sequential.Rainbow,
                         range_color=[50, 350], height=600, zoom=0.5, size_max = 50)

    fig.update_layout(mapbox_style="open-street-map")

    # Create top 10 table data
    top_10_data = filtered_df.groupby(['closest_country'])['datetime'].nunique()\
    .reset_index(name='Approx. # Distinct Events')\
    .rename(columns = {'closest_country':'Country'}).sort_values(by='Approx. # Distinct Events', ascending=False).head(10)
    # .drop(columns=['datetime'])\
    
    table = html.Table([
        html.Thead(html.Tr([html.Th(col) for col in top_10_data.columns])),
        html.Tbody([
            html.Tr([html.Td(top_10_data.iloc[i][col], style={'textAlign': 'center'}) for col in top_10_data.columns])
            for i in range(len(top_10_data))
        ])
    ])
    
    return fig, table

def update_df(selected_year):
    global df
    try:
        if pd.to_datetime(f'{selected_year}-01-01')>df.datetime.max() or pd.to_datetime(f'{selected_year}-12-31')<df.datetime.min():
            df = pd.read_sql(sql.format(selected_year, selected_year+1), engine)
        return df
    except:
        df = pd.read_sql(sql.format(selected_year, selected_year+1), engine)
        return df
    

@app.callback(
    Output('precipitation-histogram', 'figure'),
    [Input('country-dropdown', 'value'), Input('year-slider', 'value')]
)
def update_histogram(selected_country, selected_year):
    global df
    df = update_df(selected_year)
    country_data = df[df.closest_country==selected_country]

    bins1 = np.arange(0,360,10)
    counts, bins2 = np.histogram(country_data.pr_mm, bins=bins1)
    bins2 = 0.5 * (bins1[:-1] + bins2[1:])
    
    # specify sensible widths
    widths = []
    for i, b1 in enumerate(bins1[1:]):
        widths.append(b1-bins2[i])
    
    # plotly figure
    fig = go.Figure(go.Bar(
        x=bins2,
        y=counts,
        width=[10]*len(widths)
    ),layout_yaxis_range=[0,3.5], 
    layout={'title':f'Precipitation above Avg.Max Precipitation for {selected_country}',
           'yaxis_title':'Number of Events', 'xaxis_title':'Precipitation (mm)'})
    fig.update_yaxes(type="log")
    
    return fig

@app.callback(
    Output('precipitation-return', 'figure'),
    [Input('country-dropdown', 'value')]
)
def update_return_value(selected_country):
    
    TR_val, XI_val = pr_return_data[selected_country]['TR_val'], pr_return_data[selected_country]['XI_val']
    
    # plotly figure
    fig = go.Figure(
        data=go.Scatter(
            x=TR_val, 
            y=XI_val, 
            mode='lines+markers',
            line = dict(color='black', width=4)),
        layout={
            'title':f'Return value for precipitation in {selected_country}',
            'yaxis_title':'PR (mm)', 'xaxis_title':'Years'})
    
    
    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, port=4255)


