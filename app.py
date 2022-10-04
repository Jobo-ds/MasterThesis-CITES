import sql
from dash import Dash, html, dcc
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State

"""
Connect to SQLite3 database
"""
db = sql.connect_sqlite3("cites")

# Rebuild Database
# sql.build_database("cites_2")

"""
Sorting
"""
temp_data = {
    "Taxon": "None",
    "Class": "None",
    "Order": "None",
    "Family": "None",
    "Genus": "None"
}
sort_data = pd.DataFrame(temp_data)
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
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Dropdown(
                                id="class-dropdown",
                                options=sort_list["Class"].unique(),
                                placeholder="Choose Class"
                            ), md=2),
                        dbc.Col(
                            dcc.Dropdown(
                                id="order-dropdown",
                                options=sort_list["Order"].unique(),
                                placeholder="Choose Order"
                            ), md=2),
                        dbc.Col(
                            dcc.Dropdown(
                                id="famili-dropdown",
                                options=sort_list["Family"].unique(),
                                placeholder="Choose Family"
                            ), md=2),
                        dbc.Col(
                            dcc.Dropdown(
                                id="genus-dropdown",
                                options=sort_list["Genus"].unique(),
                                placeholder="Choose Genus"
                            ), md=2),
                        dbc.Col(
                            dcc.Dropdown(
                                id="taxon-dropdown",
                                options=sort_list["Taxon"].unique(),
                                placeholder="Choose Taxon"
                            ), md=2),

                    ],
                    align="center",
                ),
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


# Main Filters
@app.callback(
    [
        Output("class-dropdown", "value")

    ],
    [
        Input(component_id="class-dropdown", component_property="value"),
        Input(component_id="order-dropdown", component_property="value"),
        Input(component_id="famili-dropdown", component_property="value"),
        Input(component_id="genus-dropdown", component_property="value"),
        Input(component_id="taxon-dropdown", component_property="value")
    ],
    prevent_initial_call=False
)
def update_filters(clas_var, order_var, family_var, genus_var, taxon_var):
    filter_dict = {
        "Class": clas_var,
        "Order": order_var,
        "Family": family_var,
        "Genus": genus_var,
        "Taxon": taxon_var
    }
    sql = "SELECT Class FROM distinct_table"
    sort_data = pd.read_sql(sql, db)
    sort_data.fillna("None", inplace=True)
    if filter_dict["Class"]:
        sql = "SELECT Class, \"Order\" FROM distinct_table WHERE Class=\"{}\"".format(filter_dict["Class"])
        sort_data = pd.read_sql(sql, db)
        sort_data.fillna("None", inplace=True)
    else:
        sort_data["Order"] = "None"
        sort_data["Family"] = "None"
        sort_data["Genus"] = "None"
        sort_data["Taxon"] = "None"
    if filter_dict["Order"]:
        sql = "SELECT Class, \"Order\", Family FROM distinct_table"
        sort_data = pd.read_sql(sql, db)
        sort_data.fillna("None", inplace=True)
    else:
        sort_data["Family"] = "None"
        sort_data["Genus"] = "None"
        sort_data["Taxon"] = "None"
    if filter_dict["Family"]:
        sql = "SELECT Class, \"Order\", Family, Genus FROM distinct_table"
        sort_data = pd.read_sql(sql, db)
        sort_data.fillna("None", inplace=True)
    else:
        sort_data["Genus"] = "None"
        sort_data["Taxon"] = "None"
    if filter_dict["Genus"]:
        sql = "SELECT Class, \"Order\", Family, Genus, Taxon FROM distinct_table"
        sort_data = pd.read_sql(sql, db)
        sort_data.fillna("None", inplace=True)
    else:
        sort_data["Taxon"] = "None"
    print(sort_data)
    return sort_data


if __name__ == "__main__":
    app.run_server(debug=True)
