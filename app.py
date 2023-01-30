import database_scripts as db
from cfg import null_graph
import plot_builder as pltbld
from dash import Dash, html, dcc, ctx, dash_table
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import dash_daq as daq
import time

import numpy as np

# Theme: https://bootswatch.com/flatly/

"""
Connect to SQLite3 database
"""
conn = db.connect_sqlite3("cites")
dev = False
dev_year = 2022

# db.build_species_plus_table("cites")

"""
Init DASH
"""

# visit http://127.0.0.1:8050/ in your web browser.

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])

null_graph = {
    "layout": {
        "xaxis": {
            "visible": False
        },
        "yaxis": {
            "visible": False
        },
        "annotations": [
            {
                "text": " <br> <br> Please Choose Species...",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {
                    "size": 28
                }
            }
        ]
    }
}

"""
Layout Components
"""
header = html.Div(
    [
        dcc.Dropdown(db.build_dropdown_species(), id="input_taxon"),
        # Ammotragus lervia (Distributions and History Listings)
        # Good examples: Bos sauveli
        # Tridacna gigas (Has almost all distributions)
        # Tridacna derasa (Has all "Possibly" distribution)
        # Papio hamadryas
        # Agapornis roseicollis
        html.Div(id="search_hidden_div", style={"display": "none"}),
        html.Div(id="trashcan_1", style={"display": "none"}),
        html.Div(id="trashcan_2", style={"display": "none"})

    ]
)

"""
Badges in Header
"""

badges = dbc.ButtonGroup(
    [
        dbc.Button(
            [
                "Filtered Shipments ",
                dbc.Badge("...", id="total_shipments", color="light", text_color="primary", className="ms-1"),
            ],
            color="primary", class_name="custom_Button",
        ),
        dbc.Button(
            [
                "Family ",
                dbc.Badge("...", id="species_family", color="light", text_color="primary", className="ms-1"),
            ],
            color="primary", class_name="custom_Button",
        ),
        dbc.Button(
            [
                "Kingdom ",
                dbc.Badge("...", id="species_kingdom", color="light", text_color="primary", className="ms-1"),
            ],
            color="primary", class_name="custom_Button",
        ),
    ], class_name="custom_ButtonGroup")

header_info = dbc.Col([badges, ], md=7)

tab_terms_trade = dbc.Card(
    [
        dbc.CardBody([
            dbc.CardBody([
                dcc.Loading(children=dcc.Graph(id="plot_1_graph", figure=null_graph), type="default", color="black",
                            parent_className="loading_wrapper")
            ])
        ]),
    ],
    className="custom_card"
)

plot_1 = dbc.Tabs(
    [
        dbc.Tab(tab_terms_trade, label="Term type per trade"),
    ]
)

tab_source = dbc.Card(
    [
        dbc.CardBody([
            dbc.CardBody([
                dcc.Loading(children=dcc.Graph(id="plot_2a_graph", figure=null_graph), type="default", color="black",
                            parent_className="loading_wrapper")
            ])
        ]),
    ],
    className="custom_card"
)

tab_purpose = dbc.Card(
    [
        dbc.CardBody([
            dcc.Loading(children=dcc.Graph(id="plot_purpose", figure=null_graph), type="default", color="black",
                        parent_className="loading_wrapper")
        ])
    ],
    className="custom_card"
)

plot_2 = dbc.Tabs(
    [
        dbc.Tab(tab_source, label="Source"),
        dbc.Tab(tab_purpose, label="Purpose"),
    ]
)

spatial_map = html.Div(
    [
        dcc.Loading(children=dcc.Graph(id="spatial_map", figure=null_graph), type="default", color="black",
                    parent_className="loading_wrapper")
    ]
    , style={"margin": "auto auto"})

history_listing = html.Div(id="history_listing_table")

temporal_control = dbc.Card(
    [
        dbc.CardHeader("Temporal Control & Data"),
        dbc.CardBody(
            [
                dbc.Row(html.P("Year Range", className="H6P", style={"margin-top": "0.5rem"}), ),
                dbc.Row(
                    [
                        dbc.Col(
                            [

                                html.P("1979", id="temporal_start", style={"margin-top": "5px"}),
                            ], md=3,
                        ),
                        dbc.Col([
                                html.P("to", style={"margin-top": "5px"}),
                                html.Div(id="temporal_max", style={"display": "none"})
                            ], md=2,),
                        dbc.Col(
                            [
                                dbc.InputGroup(
                                    [
                                        dbc.Button("-", outline=True, color="secondary", className="me-1",
                                                   id="temporal_minus",
                                                   style={"margin-left": "-5px"}),
                                        dbc.Input(id="temporal_input", placeholder="Enter year...",
                                                  type="number",
                                                  maxlength=4,
                                                  minlength=4,
                                                  min=1975, max=2022,
                                                  style={"width": "100px", "margin-left": "-5px",
                                                         "border": "1px solid #95a5a6"
                                                         }, debounce=True),
                                        dbc.Button("+", outline=True, color="secondary", className="me-1",
                                                   id="temporal_plus"),
                                    ]),
                            ], md=7
                        )
                    ]
                ),
                html.P("History Listings", className="H6P", style={"margin-top": "0.5rem"}),
                history_listing
            ]
            , className="custom_cardBody_padding"),
    ]
)

map_filters = dbc.Card(
    [
        dbc.CardHeader("Map Filters"),
        dbc.CardBody(
            [
                html.P("Minimum Amount of Shipments to Draw"),
                html.Div(dcc.Slider(0, 10, 1, value=0, id="map_shipments_lower_tol"), style={"margin-top": "10px"}),
            ]
            , className="custom_cardBody_padding"),
    ]
)

filter_terms = dbc.Card(
    [
        dbc.CardHeader("Filter Terms"),
        dbc.CardBody(
            dcc.Dropdown(
                multi=True,
                id="filter_terms",
                searchable=False, )),
    ]
)

filter_source = dbc.Card(
    [
        dbc.CardHeader("Filter Sources"),
        dbc.CardBody(
            dcc.Dropdown(
                multi=True,
                id="filter_source",
                searchable=False, )),
    ]
)

filter_purpose = dbc.Card(
    [
        dbc.CardHeader("Filter Purposes"),
        dbc.CardBody(
            dcc.Dropdown(
                multi=True,
                id="filter_purpose",
                searchable=False, )),
    ]
)

"""
DASH Layout
"""

app.layout = dbc.Container(
    [
        # Header
        dbc.Row(
            [
                dbc.Col(html.P(""), md=1),
                dbc.Col(header, md=3),
                header_info,
                dbc.Col(html.P(""), md=1),
            ],
            align="center",
            style={"background": "#e1e1e1", "height": "80px", "border-bottom": "1px solid rgba(0, 0, 0, 0.175)",
                   "padding-bottom": "5px"},
        ),
        # Data
        dbc.Row([dbc.Col(html.Br(), md=7), dbc.Col(html.Br(), md=5)]),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Row([dbc.Col(plot_1, md=12)]),
                        dbc.Row(dbc.Col([html.Br(), plot_2], md=12)),
                    ]
                    , md=6)
                ,
                dbc.Col(
                    [
                        dbc.Row(spatial_map),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        temporal_control,
                                        html.Br(),
                                        map_filters,
                                    ], md=5),
                                dbc.Col(
                                    [
                                        filter_purpose,
                                        html.Br(),
                                        filter_source,
                                        html.Br(),
                                        filter_terms,
                                    ], md=7)],
                        ),
                    ]
                    , md=6)
            ],
            align="start", justify="center",
        ),
    ],
    fluid=True, style={'backgroundColor': "#eeeeee"}
)

"""
Search Callback
"""


@app.callback(
    Output("search_hidden_div", "children"),
    Output("temporal_start", "children"),
    Output("temporal_max", "children"),
    Output("species_kingdom", "children"),
    Output("species_family", "children"),
    Output("history_listing_table", "children"),
    Input("input_taxon", "value"), prevent_initial_call=True
)
def create_taxon_temp_table(input_taxon):
    db.build_main_df(input_taxon, conn, ctx.triggered_id)
    sql = "SELECT MIN(Year), MAX(Year), Family FROM temp.Taxon"
    basic_data = db.run_query(sql, conn)
    print(basic_data)
    temporal_min = int(basic_data['MIN(Year)'].values[0])
    temporal_max = int(basic_data['MAX(Year)'].values[0])
    print(temporal_min)
    print(temporal_max)
    family = str(basic_data['Family'].values[0])
    kingdom = "MY KINGDOM"
    history_listing_table = pltbld.history_listing_generator(input_taxon, conn)
    return "search_active", temporal_min, temporal_max, kingdom, family, history_listing_table


"""
Temporal Callbacks
"""


@app.callback(
    Output("temporal_input", "value"),
    Input("temporal_max", "children"),
    Input("temporal_input", "value"),
    Input("temporal_start", "children"),
    Input("temporal_plus", "n_clicks"),
    Input("temporal_minus", "n_clicks"), prevent_initial_call=True
)
def temporal_buttons(temporal_max, temporal_input, temporal_start, temporal_plus, temporal_minus):
    if dev:
        return dev_year
    if ctx.triggered_id == "temporal_input":
        return int(temporal_input)
    elif ctx.triggered_id == "temporal_plus":
        return int(temporal_input) + 1
    elif ctx.triggered_id == "temporal_minus":
        return int(temporal_input) - 1
    else:
        return temporal_max # temporal_start + 10


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
def populate_filters(activation):
    Term_List = db.get_unique_values("Term", conn)
    Purpose_List = db.get_unique_values("Purpose", conn)
    Purpose_List.sort()
    Purpose_Dict = pltbld.create_filters_dict(Purpose_List, "Purpose")
    Source_List = db.get_unique_values("Source", conn)
    Source_List.sort()
    Source_Dict = pltbld.create_filters_dict(Source_List, "Source")
    return Term_List, Term_List, Purpose_Dict, Purpose_List, Source_Dict, Source_List


"""
Term Type per Trade Callback
"""


@app.callback(
    Output("plot_1_graph", "figure"),
    Output("total_shipments", "children"),
    Input("search_hidden_div", "children"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"), prevent_initial_call=True
)
def build_plot1(activation, temporal_input, filter_terms, filter_purpose, filter_source):
    plot = pltbld.build_line_diagram("Term", temporal_input, filter_terms, filter_purpose, filter_source, conn)
    return plot


"""
Source Plot Callback
"""


@app.callback(
    Output("plot_2a_graph", "figure"),
    Output("trashcan_1", "children"),
    Input("search_hidden_div", "children"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"), prevent_initial_call=True
)
def build_plot2a(activation, temporal_input, filter_terms, filter_purpose, filter_source):
    plot = pltbld.build_line_diagram("Source", temporal_input, filter_terms, filter_purpose, filter_source, conn)
    return plot


"""
Purpose Plot Callback
"""


@app.callback(
    Output("plot_purpose", "figure"),
    Output("trashcan_2", "children"),
    Input("search_hidden_div", "children"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"), prevent_initial_call=True
)
def build_plot2b(activation, temporal_input, filter_terms, filter_purpose, filter_source):
    plot = pltbld.build_line_diagram("Purpose", temporal_input, filter_terms, filter_purpose, filter_source, conn)
    return plot


"""
Spatial Callback
"""


@app.callback(
    Output("spatial_map", "figure"),
    Input("search_hidden_div", "children"),
    Input("input_taxon", "value"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"),
    Input("map_shipments_lower_tol", "value"), prevent_initial_call=True)
def build_map(activation, input_taxon, temporal_input, filter_terms, filter_purpose, filter_source,
              map_shipments_lower_tol):
    print("Building map ...")
    start = time.time()

    map_fig = pltbld.build_empty_map_graph()
    map_fig = pltbld.add_distributions_to_map_graph(input_taxon, conn, map_fig)
    map_fig = pltbld.update_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn,
                                     map_shipments_lower_tol, map_fig)
    end = time.time()
    elapsed_time = round(end - start, 0)
    print(f"Finished building map! Elapsed Time: {elapsed_time} secs")
    return map_fig


if __name__ == "__main__":
    app.run_server(debug=True)
