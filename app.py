import database_scripts as db
from cfg import null_graph
import plot_builder as pltbld
from dash import Dash, html, dcc, ctx, dash_table
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
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
header_search = html.Div(
    [
        dcc.Dropdown(db.buildDropdownTaxon(), "Corallus hortulanus", id="input_taxon"),
        html.Div(id="search_hidden_div", style={"display": "none"})

    ]
)

header_info = dbc.Row([
    dbc.Col([
        html.P("English Common Names: XXXXXX, YYYYYYY, ZZZZZZZ"),
        html.P("Kingdom: XXXXXXX. Family: XXXXXXX"),
    ], md=5),
    dbc.Col([
        html.P("Downloads"),
        html.P("CITES Identification Guide"),
        html.P("XXXXXX, ZZZZZZ"),
    ], md=5),
], align="center",
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
        dbc.Row(html.H5("Term type per trade", style={"text-align": "center"}), ),
        dbc.Row([
            dcc.Graph(id="plot_1_graph"),
        ])
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

spatial_map = html.Div(
    [
        dcc.Graph(id="spatial_map"),
    ]
    , style={"margin": "auto auto"})

temporal_control = dbc.Card(
    dbc.InputGroup(
        [
            dbc.Button("1979", outline=True, color="secondary", className="me-1", id="temporal_start"),
            dbc.Input(id="temporal_input", placeholder="Input Year...", type="number", maxlength=4, minlength=4,
                      min=1979, max=2022, style={"width": "150px", "margin-left": "-5px"}),
            dbc.Button("2022", outline=True, color="secondary", className="me-1", id="temporal_end"),
            dbc.Button(">", outline=True, color="secondary", className="me-1", id="temporal_animate",
                       style={"margin-left": "-5px"}),
        ])
    , body=True,
)

spatial_filters = dbc.Card(
    [
        dbc.Row([
            dbc.Col("Terms", md=3),
            dbc.Col(dcc.Dropdown(
                multi=True,
                id="filter_terms",
                searchable=False,
            ), md=9)
        ]),
        dbc.Row([
            dbc.Col("Purpose", md=3),
            dbc.Col(dcc.Dropdown(
                multi=True,
                id="filter_purpose",
                searchable=False,
            ), md=9)
        ]),
        dbc.Row([
            dbc.Col("Source", md=3),
            dbc.Col(dcc.Dropdown(
                multi=True,
                id="filter_source",
                searchable=False,
            ), md=9)
        ]),

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
                        dbc.Row([dbc.Col(Plot_1, md=7), dbc.Col(Accum_data, md=5)]),
                        dbc.Row([dbc.Col(Plot_3, md=6), dbc.Col(Plot_4, md=6)]),
                    ]
                    , md=6)
                ,
                dbc.Col(
                    [
                        dbc.Row(spatial_map),
                        dbc.Row(
                            [dbc.Col(temporal_control, md=5), dbc.Col(spatial_filters, md=7)])
                    ]
                    , md=6)
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
    db.buildMainDataframe(input_taxon, conn, ctx.triggered_id)
    return "search_active"


"""
Temporal Callbacks
"""


@app.callback(
    Output("temporal_input", "value"),
    Input("temporal_start", "n_clicks"),
    Input("temporal_end", "n_clicks"))
def temporal_buttons(temporal_start, temporal_end):
    if ctx.triggered_id == "temporal_start":
        return 1979
    elif ctx.triggered_id == "temporal_end":
        return 2022
    else:
        return 1979


"""
Filter Callbacks
"""


@app.callback(
    Output("filter_terms", "options"),
    Output("filter_terms", "value"),
    Output("filter_purpose", "options"),
    Output("filter_purpose", "value"),
    Output("filter_source", "options"),
    Output("filter_source", "value"),
    Input("search_hidden_div", "children"), prevent_initial_call=True)
def populateFilters(activation):
    Term_List = db.getUniquevalues("Term", conn)
    Purpose_List = db.getUniquevalues("Purpose", conn)
    Purpose_List.sort()
    Purpose_Dict = pltbld.createDictFilters(Purpose_List, "Purpose")
    Source_List = db.getUniquevalues("Source", conn)
    Source_List.sort()
    Source_Dict = pltbld.createDictFilters(Source_List, "Source")
    return Term_List, Term_List, Purpose_Dict, Purpose_List, Source_Dict, Source_List


"""
Plot_1 Callback
"""


@app.callback(
    Output("plot_1_graph", "figure"),
    Input("search_hidden_div", "children"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"), prevent_initial_call=True
)
def buildPlot_1(activation, temporal_input, filter_terms, filter_purpose, filter_source):
    return pltbld.buildLineDiagram("Term", temporal_input, filter_terms, filter_purpose, filter_source, conn)


"""
Spatial Callback
"""


@app.callback(
    Output("spatial_map", "figure"),
    Input("search_hidden_div", "children"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"), prevent_initial_call=True)
def buildMap(activation, temporal_input, filter_terms, filter_purpose, filter_source):
    map_fig = pltbld.buildMapGraph()
    map_fig = pltbld.updateMapGraph(temporal_input, filter_terms, filter_purpose, filter_source, conn, map_fig)
    return map_fig


if __name__ == "__main__":
    app.run_server(debug=True)
