import sql
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import json
from urllib.request import urlopen
import pycountry
import numpy as np

"""
Connect to SQLite3 database
"""
# db = sql.connect_sqlite3("cites")

# Rebuild Database
# sql.build_database("cites_2")

"""
Get Data
"""

# print("Getting taxa Data")
# query = "SELECT * from distinct_table_amount"
# taxa_data = sql.getData(query, db)
# print("Getting Temporal Data")
# query = "SELECT * from temporal"
# temporal_data = sql.getData(query, db)

def get_country_code(alpha_2):
    for co in list(pycountry.countries):
        if alpha_2 in co.alpha_2:
            return co.alpha_3
        else:
            for co in list(pycountry.historic_countries):
                if alpha_2 in co.alpha_2:
                    return co.alpha_3
    return alpha_2 + "(Not Found)"

"""
Init DASH
"""

# visit http://127.0.0.1:8050/ in your web browser.

app = Dash(__name__)

"""
Layout Components
"""
control_panel = dbc.Card(
    [
        html.Div(
            [
                html.H1("Control Panel", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [
                html.P("Nothing to see here. Interactivity not implemented yet.")
            ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

data_map = dbc.Card(
    [
        html.Div(
            [
                html.H1("Map", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [
                html.H4('Plotting imports/exports on map'),
                html.P("Select type:"),
                dcc.RadioItems(
                    id='spatial_type',
                    options=["Imports", "Exports"],
                    value="Imports",
                    inline=True
                ),
                dcc.Graph(id="graph"),
            ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

histogram_0 = dbc.Card(
    [
        html.Div(
            [
                html.H1("Histogram", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [
            ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

histogram_1 = dbc.Card(
    [
        html.Div(
            [
                html.H1("Histogram", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [

            ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

histogram_2 = dbc.Card(
    [
        html.Div(
            [
                html.H1("Histogram (Top X)", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [

            ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

histogram_3 = dbc.Card(
    [
        html.Div(
            [
                html.H1("???", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [

            ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

histogram_4 = dbc.Card(
    [
        html.Div(
            [
                html.H1("???", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [

            ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

"""
DASH Layout
"""

app.layout = dbc.Container(
    [
        # Control Panel
        dbc.Row(
            [
                dbc.Col(control_panel, md=12)
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(histogram_0, md=6),
                dbc.Col(data_map, md=6)
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(histogram_1, md=6),
                dbc.Col(histogram_2, md=6)
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(histogram_3, md=6),
                dbc.Col(histogram_4, md=6)
            ],
            align="center",
        ),
    ],
    fluid=True
)


@app.callback(
    Output("graph", "figure"),
    Input("spatial_type", "value"))
def display_choropleth(spatial_type):
    # Get Data from Database
    db = sql.connect_sqlite3("cites")
    print("Getting Spatial Data")
    query_1 = "SELECT * from imports"
    query_2 = "SELECT * from exports"
    data_1 = sql.getData(query_1, db)
    data_2 = sql.getData(query_2, db)
    spatial_data = data_1.merge(data_2, how="outer", on="Country", sort=True)
    spatial_data.fillna(0, inplace=True)
    spatial_data.drop(spatial_data.tail(1).index, inplace=True)
    # Convert to Alpha-3, because that's how the geojson works)
    spatial_data["Country"] = spatial_data["Country"].apply(lambda x: get_country_code(x))
    # Remove countries with no trade
    spatial_data = spatial_data[spatial_data.Imports != 0.0]
    spatial_data = spatial_data[spatial_data.Exports != 0.0]
    # Log() Numbers for better accuracy
    spatial_data["Imports"] = np.log(spatial_data["Imports"])
    spatial_data["Exports"] = np.log(spatial_data["Exports"])
    #print(spatial_data.to_string())
    print("Done.")

    # Setup Map
    with urlopen(
            'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/countries.geojson') as response:
        geojson = json.load(response)

    fig = px.choropleth(
        spatial_data,
        locations="Country",
        locationmode="geojson-id",
        geojson=geojson,
        color=spatial_type,
        featureidkey="id",
        center={"lat": 45.5517, "lon": -73.7073},
        range_color=[0, 20])
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
