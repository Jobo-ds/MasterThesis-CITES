import database_scripts as db
from cfg import null_graph
import plot_builder as pltbld
from dash import Dash, html, dcc, ctx, dash_table
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import json
from urllib.request import urlopen
import dash_daq as daq

import numpy as np

# Theme: https://bootswatch.com/flatly/

"""
Connect to SQLite3 database
"""
conn = db.connect_sqlite3("cites")

"""
Prepare initial data
"""

"""
Init DASH
"""

# visit http://127.0.0.1:8050/ in your web browser.

app = Dash(__name__)

"""
Layout Components
"""
header_search = dbc.Card(
    [
        html.Div(
            [
                html.H3("Search", style={"text-align": "center"}),
                dcc.Dropdown(db.buildDropdownTaxon(conn), "Corallus hortulanus", id="input_taxon"),
                html.Div(id="search_hidden_div", style={"display": "none"})

            ]
        ),
    ],
    body=True,
)

header_info = dbc.Card(
    [
        html.Div(
            [
                html.H3("Info Panel", style={"text-align": "center"}),
            ]
        ),
    ],
    body=True,
)

Accum_data = dbc.Card(
    [
        html.Div(
            [
                html.Div(html.H3("Accum. Data"
                                 , style={"text-align": "center"})),
            ]
        ),
    ],
    body=True,
)

Plot_1 = dbc.Card(
    [
        dbc.Row(html.H5("Term type per trade", style={"text-align": "center"}),),
        dbc.Row(dcc.Graph(id="plot_1_graph"))
    ],
    body=True,
)

Plot_2 = dbc.Card(
    [
        html.Div(
            [
                html.Div(html.H3("Plot_2"
                                 , style={"text-align": "center"})),
            ]
        ),
    ],
    body=True,
)

Plot_3 = dbc.Card(
    [
        html.Div(
            [
                html.Div(html.H3("Plot_3"
                                 , style={"text-align": "center"})),
            ]
        ),
    ],
    body=True,
)

Plot_4 = dbc.Card(
    [
        html.Div(
            [
                html.Div(html.H3("Plot_4"
                                 , style={"text-align": "center"})),
            ]
        ),
    ],
    body=True,
)

spatial_map = dbc.Card(
    [
        html.Div(
            [
                dcc.Graph(id="spatial_graph_map"),
            ]
            , style={"margin": "auto auto"}),
    ],
    body=True,
)

temporal_control = dbc.Card(
    [
        html.Div(
            [
                html.Div(html.H3("Temporal Control"
                                 , style={"text-align": "center"})),
            ]
        ),
    ],
    body=True,
)

spatial_filters = dbc.Card(
    [
        html.Div(
            [
                html.H3("Spatial Filters", style={"text-align": "center"}),
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
        # Header
        dbc.Row(
            [
                dbc.Col(header_search, md=3),
                dbc.Col(header_info, md=9)
            ],
            align="center",
        ),
        # Data
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row(Accum_data),
                        dbc.Row([dbc.Col(Plot_1, md=5), dbc.Col(Plot_2, md=5)]),
                        dbc.Row([dbc.Col(Plot_3, md=5), dbc.Col(Plot_4, md=5)]),
                    ]
                    , md=9)
                ,
                dbc.Col(
                    [
                        dbc.Row(spatial_map),
                        dbc.Row(
                            [dbc.Col(temporal_control, md=5), dbc.Col(spatial_filters, md=5)])
                    ]
                    , md=3)
            ],
            align="center",
        ),
    ],
    fluid=True
)

"""
Search Callback
"""
@app.callback(Output("search_hidden_div", "children"), Input("input_taxon", "value"))
def createTaxonTempTable(input_taxon):
    db.buildMainDataframe(input_taxon, conn)
    return "search_active"


"""
Plot_1 Callback
"""
@app.callback(
    Output("plot_1_graph", "figure"),
    [Input("search_hidden_div", "children")])
def buildPlot_1(activation):
    return pltbld.buildLineDiagram("Term", conn)


if __name__ == "__main__":
    app.run_server(debug=True)
