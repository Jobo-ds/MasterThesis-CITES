import sql
import plot_builder as pltbld
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import json
from urllib.request import urlopen

import numpy as np

"""
Connect to SQLite3 database
"""
# db = sql.connect_sqlite3("cites")


"""
Get Data
"""

# print("Getting taxa Data")
# query = "SELECT * from distinct_table_amount"
# taxa_data = sql.getData(query, db)
# print("Getting Temporal Data")
# query = "SELECT * from temporal"
# temporal_data = sql.getData(query, db)


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

spatial_map = dbc.Card(
    [
        html.Div(
            [
                html.H1(id="title_spatialMap", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [
                html.H4('Plotting all imports/exports on map'),
                dbc.RadioItems(
                    id="spatial_type",
                    value="Imports",
                    options=[
                        {"label": "Imports", "value": "Imports"},
                        {"label": "Exports", "value": "Exports"},
                    ]),
                dcc.Graph(id="spatial_graph_map"),
            ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

spatial_hist = dbc.Card(
    [
        html.Div(
            [
                html.H1(id="title_spatialHist", style={"text-align": "center"}),
            ]
        ),
        html.Div(
            [
                dcc.Graph(id="spatial_graph_hist"),
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
                dbc.Col(html.P("Placeholder."), md=6),
                dbc.Col(html.P("Placeholder."), md=6)
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(html.P("Placeholder."), md=6),
                dbc.Col(html.P("Placeholder."), md=6)
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(spatial_hist, md=6),
                dbc.Col(spatial_map, md=6)
            ],
            align="center",
        ),
    ],
    fluid=True
)


# Update Map title
@app.callback(
    Output("title_spatialMap", "children"),
    Output("title_spatialHist", "children"),
    Input("spatial_type", "value"))
def update_title_spatialMap(spatial_type):
    return f"Map of total {spatial_type}", f"Top {spatial_type}"


# Spatial
@app.callback(
    Output("spatial_graph_map", "figure"),
    Output("spatial_graph_hist", "figure"),
    Input("spatial_type", "value"))
def display_choropleth(spatial_type):
    spatial_data = sql.getSpatialTotal()

    # Setup Map
    with urlopen(
            'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/countries.geojson') as response:
        geojson = json.load(response)

    # https://plotly.github.io/plotly.py-docs/generated/plotly.express.choropleth.html
    fig_map = px.choropleth(
        spatial_data,
        locations="Country",
        # locationmode="geojson-id",
        locationmode="ISO-3",
        geojson=geojson,
        color=spatial_type,
        featureidkey="id",
        range_color=[0, 20],
        fitbounds="locations",
        color_continuous_scale="Blues")
    # fig_map.update_layout(
    #     # margin={"r": 0, "t": 0, "l": 0, "b": 0})
    # )
    spatial_data_hist = spatial_data.nlargest(n=10, columns=spatial_type)
    fig_hist = px.histogram(
        spatial_data_hist,
        x=spatial_type,
        y="Country",
    )
    return fig_map, fig_hist


if __name__ == "__main__":
    app.run_server(debug=True)
