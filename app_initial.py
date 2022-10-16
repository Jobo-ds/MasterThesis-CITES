import database_scripts as db
from cfg import null_graph
import plot_builder as pltbld
from dash import Dash, html, dcc, ctx
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

print("Populating dropdown menus")
# Create Taxon List for Dropdown menus
df = db.runQuery("SELECT Taxon from distinct_table_amount", conn)
taxon_list = df["Taxon"].values.tolist()

# Create Column List for Dropdown menus
df = db.runQuery("PRAGMA table_info(shipments);", conn)
blacklist = ["Id", "Taxon", "Quantity", "Import.permit", "Export.permit", "Origin.permit"]
col_list = df["name"].values.tolist()
col_list = [word for word in col_list if word not in blacklist]

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
                html.H3("Control Panel", style={"text-align": "center"}),
            ]
        ),
        html.Div([
        ], style={"margin": "auto auto"}
        ),
        html.Div(
            [

            ]
        ),
    ],
    body=True,
)

taxon_1 = dbc.Card(
    [
        html.Div(
            [
                dbc.Row(
                    [
                        html.H3("Plot Attribute of Taxon", style={"text-align": "center"}),
                        html.H5(id="taxon1_title", style={"text-align": "center"}),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            html.P("Plot", style={"text-align": "center", "margin-top": "4px", "margin-left": "0px"})
                            , md=1),
                        dbc.Col(
                            dcc.Dropdown(taxon_list, "Corallus hortulanus", id="input_taxon")
                            , md=5),
                        # dcc.Store stores the current data
                        dcc.Store(id='taxon_data'),
                        dbc.Col(
                            html.P("On", style={"text-align": "center", "margin-top": "4px"})
                            , md=1),
                        dbc.Col(
                            dcc.Dropdown(col_list, "Term", id="input_attribute")
                            , md=5),
                    ]
                ),
                dbc.Row(
                    [
                        dbc.Col(" ", md=9),
                        dbc.Col([
                            daq.BooleanSwitch(
                                on=False,
                                label="Line Chart",
                                labelPosition="Right",
                                id="taxon1_linechart_switch"
                            )
                        ]
                            , md=3),
                    ],
                ),
                dbc.Row(
                    [
                        dcc.Graph(id="taxon_1_graph"),
                    ]
                ),
            ], style={"margin": "15px"}
        )
    ]
)

spatial_map = dbc.Card(
    [
        html.Div(
            [
                html.H3(id="title_spatialMap", style={"text-align": "center"}),
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
                html.H3(id="title_spatialHist", style={"text-align": "center"}),
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
        # Populate Dropdowns

        # Control Panel
        dbc.Row(
            [
                dbc.Col(control_panel, md=12)
            ],
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(taxon_1, md=6),
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


# Taxon
# Fetch data on selected Taxon
@app.callback(Output("taxon_data", 'data'), Input('input_taxon', 'value'))
def getTaxonData(input_taxon):
    sql = "SELECT * FROM shipments WHERE Taxon=\"{}\"".format(input_taxon)
    df = db.runQuery(sql, conn)

    return df.to_json(date_format='iso', orient='split')


# Graph
@app.callback(
    Output("taxon_1_graph", "figure"),
    Output("taxon1_title", "children"),
    [Input("taxon_data", "data"),
     Input("input_attribute", "value"),
     Input("input_taxon", "value"),
     Input("taxon1_linechart_switch", "on")])
def display_taxon(taxon_data, input_attribute, input_taxon, taxon1_linechart_switch):
    df = pd.read_json(taxon_data, orient='split')

    # Generate Figure
    if taxon1_linechart_switch:
        # Make a nice even line
        # df = df.sort_values(by="Year")
        #df = df.groupby(['Year'])['Term'].agg(['count']).reset_index()
        #print(df)
        fig = px.line(
            df,
            x="Year",
            color=input_attribute,
            markers=True
        )
        return fig, \
               f"Line Chart of total {input_attribute} on {input_taxon}"
    else:
        fig = px.histogram(
            df,
            y=input_attribute,
        )
        fig.update_layout(
            xaxis_title="Total Count",
        )
        fig.update_yaxes(
            categoryorder="total descending"
        )
        return fig, \
               f"Histogram of total {input_attribute} on {input_taxon}"


# Spatial
@app.callback(
    Output("spatial_graph_map", "figure"),
    Output("spatial_graph_hist", "figure"),
    Output("title_spatialMap", "children"),
    Output("title_spatialHist", "children"),
    Input("spatial_type", "value"))
def display_choropleth(spatial_type):
    spatial_data = db.getSpatialTotal(conn)
    spatial_data_map = spatial_data.copy(deep=True)
    # Convert to Alpha-3, because that's how the geojson works)
    spatial_data_map["Country"] = spatial_data_map["Country"].apply(lambda x: pltbld.alpha2_to_alpha_3(x))
    # Log() Numbers for better accuracy
    spatial_data_map["Imports"] = np.log(spatial_data_map["Imports"])
    spatial_data_map["Exports"] = np.log(spatial_data_map["Exports"])

    # Setup Map
    with urlopen(
            'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/countries.geojson') as response:
        geojson = json.load(response)

    # https://plotly.github.io/plotly.py-docs/generated/plotly.express.choropleth.html
    fig_map = px.choropleth(
        spatial_data_map,
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
    # Convert to name for usability
    spatial_data_hist["Country"] = spatial_data_hist["Country"].apply(lambda x: pltbld.alpha3_to_Name(x))

    fig_hist = px.histogram(
        spatial_data_hist,
        x=spatial_type,
        y="Country",
    )
    return fig_map, fig_hist, f"Map of total {spatial_type}", f"Top {spatial_type}"


if __name__ == "__main__":
    app.run_server(debug=True)
