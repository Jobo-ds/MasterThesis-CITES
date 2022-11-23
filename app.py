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
dev = True


# db.build_species_plus_table("cites")

"""
Init DASH
"""

# visit http://127.0.0.1:8050/ in your web browser.

app = Dash(__name__)

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
                "text": " <br> <br> Loading...",
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
        dcc.Dropdown(db.build_dropdown_species(), "Papio hamadryas", id="input_taxon"),
        # Good examples: Bos sauveli
        # Tridacna gigas (Has almost all distributions)
        # Tridacna derasa (Has all "Possibly" distribution)
        # Papio hamadryas
        html.Div(id="search_hidden_div", style={"display": "none"}),
        html.Div(id="trashcan_1", style={"display": "none"}),
        html.Div(id="trashcan_2", style={"display": "none"}),
        dcc.Store(id='memory')

    ]
)

header_info = dbc.Row([
    dbc.Col([
        html.P("Kingdom: Loading...", id="species_kingdom"),
        html.P("Family: Loading...", id="species_family"),
    ], md=5),
    dbc.Col([
        html.P("English Common Names: XXXXXX, YYYYYYY, ZZZZZZZ"),
    ], md=5),
], align="center",
)

tab_terms_trade = dbc.Card(
    [
        dbc.CardBody([
            dbc.CardBody([
                dcc.Loading(children=dcc.Graph(id="plot_1_graph", figure=null_graph), type="default", color="white",
                            parent_className="loading_wrapper")
            ])
        ]),
    ],
    className="custom_card"
)

tab_terms_quantity = dbc.Card(
    [
        dbc.CardBody([
            html.P("Placeholder", style={"text-align": "center"}),
        ])
    ],
    className="custom_card"
)

plot_1 = dbc.Tabs(
    [
        dbc.Tab(tab_terms_trade, label="Term type per trade"),
        dbc.Tab(tab_terms_quantity, label="Term per quantity"),
    ]
)

tab_source = dbc.Card(
    [
        dbc.CardBody([
            dbc.CardBody([
                dcc.Loading(children=dcc.Graph(id="plot_2a_graph", figure=null_graph), type="default", color="white",
                            parent_className="loading_wrapper")
            ])
        ]),
    ],
    className="custom_card"
)

tab_purpose = dbc.Card(
    [
        dbc.CardBody([
            dcc.Loading(children=dcc.Graph(id="plot_2b_graph", figure=null_graph), type="default", color="white",
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
        dcc.Loading(children=dcc.Graph(id="spatial_map", figure=null_graph), type="default", color="white",
                    parent_className="loading_wrapper")
    ]
    , style={"margin": "auto auto"})

temporal_control = dbc.Card(
    [
        dbc.CardHeader("Temporal Control & Data"),
        dbc.CardBody(
            [
                dbc.InputGroup(
                    [
                        dbc.Button("1979", outline=True, color="secondary", className="me-1", id="temporal_start"),
                        dbc.Button("-", outline=True, color="secondary", className="me-1", id="temporal_minus",
                                   style={"margin-left": "-5px"}),
                        dbc.Input(id="temporal_input", placeholder="Input Year...", type="number", maxlength=4,
                                  minlength=4,
                                  min=1975, max=2022,
                                  style={"width": "100px", "margin-left": "-5px", "border": "1px solid #95a5a6"
                                         }, debounce=True),
                        dbc.Button("+", outline=True, color="secondary", className="me-1", id="temporal_plus"),
                        dbc.Button("2022", outline=True, color="secondary", className="me-1", id="temporal_end",
                                   style={"margin-left": "-5px"}),
                        dbc.Button(">", outline=True, color="secondary", className="me-1", id="temporal_animate",
                                   style={"margin-left": "-5px"}),
                    ]),
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
Badges in Header
"""

total_badge = dbc.Button(
    [
        "Total Shipments",
        dbc.Badge("...", id="total_shipments", color="light", text_color="primary", className="ms-1"),
    ],
    color="primary", class_name="custom_Button",
)

term_badge = dbc.Button(
    [
        "Top Term",
        dbc.Badge("...", id="top_term", color="light", text_color="primary", className="ms-1"),
    ],
    color="primary", class_name="custom_Button",
)

purpose_badge = dbc.Button(
    [
        "Top Purpose",
        dbc.Badge("...", id="top_purpose", color="light", text_color="primary", className="ms-1"),
    ],
    color="primary", class_name="custom_Button",
)

source_badge = dbc.Button(
    [
        "Top Source",
        dbc.Badge("...", id="top_source", color="light", text_color="primary", className="ms-1"),
    ],
    color="primary", class_name="custom_Button",
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
                dbc.Col(header_info, md=7),
                dbc.Col(html.P(""), md=1),
            ],
            align="center",
            style={"background": "#e1e1e1", "height": "80px", "border-bottom": "1px solid rgba(0, 0, 0, 0.175)",
                   "padding-bottom": "5px"},
        ),
        dbc.Row(
            [
                dbc.ButtonGroup([
                    total_badge, term_badge, purpose_badge, source_badge
                ], class_name="custom_ButtonGroup")]),
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
    Output("memory", "data"),
    Output("temporal_start", "children"),
    Output("species_kingdom", "children"),
    Output("species_family", "children"),
    Input("input_taxon", "value"))
def create_taxon_temp_table(input_taxon):
    db.build_main_df(input_taxon, conn, ctx.triggered_id)
    sql = "SELECT MIN(Year), Family FROM temp.Taxon"
    basic_data = db.run_query(sql, conn)
    memory = {}
    memory["temporal_min"] = int(basic_data['MIN(Year)'].values[0])
    memory["family"] = str(basic_data['Family'].values[0])
    kingdom = "MY KINGDOM"
    # sql_2 = "SELECT Appendix, MIN(Year) from temp.taxon GROUP BY Appendix"
    # appendix_df = db.run_query(sql_2, conn)
    # appendix_df = pd.read_csv("CITES/History_of_CITES_Listings_2022-11-22 04 10.csv")
    # print(appendix_df.to_string(max_rows=10))

    return "search_active", memory, memory["temporal_min"], kingdom, "Family: " + memory["family"]


"""
Temporal Callbacks
"""


@app.callback(
    Output("temporal_input", "value"),
    Input("memory", "data"),
    Input("temporal_input", "value"),
    Input("temporal_start", "n_clicks"),
    Input("temporal_plus", "n_clicks"),
    Input("temporal_minus", "n_clicks"),
    Input("temporal_end", "n_clicks"))
def temporal_buttons(memory, temporal_input, temporal_start, temporal_end, temporal_plus, temporal_minus):

    dev_year = 1992
    if ctx.triggered_id == "temporal_start":
        if dev:
            return dev_year
        return memory["temporal_min"]
    elif ctx.triggered_id == "temporal_end":
        return 2022
    elif ctx.triggered_id == "temporal_plus":
        return temporal_input + 1
    elif ctx.triggered_id == "temporal_minus":
        return temporal_input - 1
    else:
        if dev:
            return dev_year
        return memory["temporal_min"]


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
    Output("top_term", "children"),
    Input("search_hidden_div", "children"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"), prevent_initial_call=True
)
def build_plot1(activation, temporal_input, filter_terms, filter_purpose, filter_source):
    return pltbld.build_line_diagram("Term", temporal_input, filter_terms, filter_purpose, filter_source, conn)


"""
Source Plot Callback
"""


@app.callback(
    Output("plot_2a_graph", "figure"),
    Output("trashcan_1", "children"),
    Output("top_source", "children"),
    Input("search_hidden_div", "children"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"), prevent_initial_call=True
)
def build_plot2a(activation, temporal_input, filter_terms, filter_purpose, filter_source):
    return pltbld.build_line_diagram("Source", temporal_input, filter_terms, filter_purpose, filter_source, conn)


"""
Purpose Plot Callback
"""


@app.callback(
    Output("plot_2b_graph", "figure"),
    Output("trashcan_2", "children"),
    Output("top_purpose", "children"),
    Input("search_hidden_div", "children"),
    Input("temporal_input", "value"),
    Input("filter_terms", "value"),
    Input("filter_purpose", "value"),
    Input("filter_source", "value"), prevent_initial_call=True
)
def build_plot2b(activation, temporal_input, filter_terms, filter_purpose, filter_source):
    return pltbld.build_line_diagram("Purpose", temporal_input, filter_terms, filter_purpose, filter_source, conn)


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
def build_map(activation, input_taxon, temporal_input, filter_terms, filter_purpose, filter_source, map_shipments_lower_tol):
    map_fig = pltbld.build_empty_map_graph()
    map_fig = pltbld.add_distributions_to_map_graph(input_taxon, conn, map_fig)
    if dev:
        return pltbld.update_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn, 8, map_fig)
    return pltbld.update_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn, map_shipments_lower_tol, map_fig)


if __name__ == "__main__":
    app.run_server(debug=True)
