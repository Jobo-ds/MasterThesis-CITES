import pycountry
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import database_scripts as db
import sqlite3
import json
from urllib.request import urlopen
import math
from itertools import product
import numpy as np
import random
from dash import Dash, html, dcc, ctx, dash_table
import dash_bootstrap_components as dbc
import time

# Colors
lightblue = "#a6cee3"
blue = "#1f78b4"
lightgreen ="#b2df8a"
green =" #33a02c"
lightred = "#fb9a99"
red = "#e31a1c"
lightpurple = "#cab2d6"
purple = "#6a3d9a"
orange = "#fdbf6f"

color_dict = {
    # Terms
    "Animalia Products": lightgreen,
    "Plantae Products": green,
    "Common Products": lightblue,
    "Processed Products": blue,
    "Bone": purple,
    "Skin": red,
    "Others": orange,
    # Map
    "Uncertain": orange,
    "Reintroduced": lightgreen,
    "Native": green,
    "Introduced": purple,
    "Possibly Introduced": lightpurple,
    "Extinct": red,
    "Possibly Extinct": lightred,
}

color_discrete_sequence_list = [lightblue, blue, lightgreen, green, lightred, red, lightpurple, purple, orange]

"""
Auxiliary functions
"""
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


def convert_countrycode(value, input_type, output_type):
    def result(co, output_type):
        if output_type == "name":
            return co.name
        if output_type == "alpha_2":
            return co.alpha_2
        if output_type == "alpha_3":
            return co.alpha_3

    for co in list(pycountry.countries):
        if input_type == "name":
            if value in co.name:
                return result(co, output_type)
            try:
                if value in co.official_name:
                    return result(co, output_type)
            except:
                pass
            value_alt = value.replace(" (", ", ")
            value_alt = value_alt.replace(")", "")
            if value_alt in co.name:
                return result(co, output_type)
        if input_type == "alpha_2":
            if value in co.alpha_2:
                return result(co, output_type)
        if input_type == "alpha_3":
            if value in co.alpha_3:
                return result(co, output_type)
    for co in list(pycountry.historic_countries):
        if input_type == "name":
            if value in co.name:
                return result(co, output_type)
        if input_type == "alpha_2":
            if value in co.alpha_2:
                return result(co, output_type)
        if input_type == "alpha_3":
            if value in co.alpha_3:
                return result(co, output_type)
    return value + "(Not Found)"


"""
Create dictionaries for filters from database results
"""


def create_filters_dict(filter_list, outputfilter):
    if outputfilter == "Purpose":
        purpose_list = [{"label": "Breeding", "value": "B"},
                        {"label": "Educational", "value": "E"},
                        {"label": "Botanical garden", "value": "G"},
                        {"label": "Hunting Trophy", "value": "H"},
                        {"label": "Law enforcement", "value": "L"},
                        {"label": "Medical", "value": "M"},
                        {"label": "(Re)introduction", "value": "N"},
                        {"label": "Personal", "value": "P"},
                        {"label": "Circus/Exhibition", "value": "Q"},
                        {"label": "Scientific", "value": "S"},
                        {"label": "Commercial", "value": "T"},
                        {"label": "Zoo", "value": "Z"},
                        {"label": "Missing Data", "value": "Missing Data"}
                        ]
        valid_dict_list = []
        for dicts in purpose_list:
            if dicts["value"] in filter_list:
                valid_dict_list.append(dicts)
    elif outputfilter == "Source":
        source_list = [{"label": "Artificially propagated plants", "value": "A"},
                       {"label": "Bred in captivity", "value": "C"},
                       {"label": "Bred in captivity (Appx I)", "value": "D"},
                       {"label": "Born in captivity", "value": "F"},
                       {"label": "Confiscated specimens", "value": "I"},
                       {"label": "Pre-Convention specimens", "value": "O"},
                       {"label": "Ranched specimens", "value": "R"},
                       {"label": "Source unknown", "value": "U"},
                       {"label": "Taken from wild", "value": "W"},
                       {"label": "Taken from marine env.", "value": "X"},
                       {"label": "Assisted production", "value": "Y"},
                       {"label": "Missing Data", "value": "Missing Data"}
                       ]
        valid_dict_list = []
        for dicts in source_list:
            if dicts["value"] in filter_list:
                valid_dict_list.append(dicts)
    return valid_dict_list


"""
A fallback graph that is shown when no data is available.
"""
null_graph = {
    "layout": {
        "xaxis": {
            "visible": False
        },
        "yaxis": {
            "visible": False
        },
        "height": "250",
        "annotations": [
            {
                "text": "No data for <br> selected period",
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
Build a line diagram of input data
"""


def build_line_diagram(input_attribute, temporal_input, filter_terms, filter_purpose, filter_source, conn):
    try:
        sql_start = "SELECT {0}, Year, count({0}) FROM temp.taxon WHERE Year<={1} AND".format(input_attribute,
                                                                                              temporal_input)
        sql_purpose = "Purpose IN {0}".format(db.list_to_sql(filter_purpose))
        sql_purpose_null = "OR Purpose IS NULL"
        sql_source = "Source IN {0}".format(db.list_to_sql(filter_source))
        sql_source_null = "OR Source IS NULL"
        sql_term = "Term IN {0}".format(db.list_to_sql(filter_terms))
        sql_term_null = "OR Term IS NULL"
        sql_end = "GROUP BY {0}, Year ORDER BY Year, {0}".format(input_attribute)

        if "Unknown" in filter_purpose:
            sql = sql_start + " (" + sql_purpose + " " + sql_purpose_null + ")"
        else:
            sql = sql_start + " " + sql_purpose
        if "Unknown" in filter_source:
            sql = sql + " AND (" + sql_source + " " + sql_source_null + ")"
        else:
            sql = sql + " AND " + sql_source
        if "Unknown" in filter_terms:
            sql = sql + " AND (" + sql_term + " " + sql_term_null + ")"
        else:
            sql = sql + " AND " + sql_term
        sql = sql + " " + sql_end
        df = db.run_query(sql, conn)
        df["count(" + input_attribute + ")"] = df["count(" + input_attribute + ")"].astype(int)

        if input_attribute == "Source":
            df.fillna(value="Missing Data", axis="index", inplace=True)
        if input_attribute == "Purpose":
            df.fillna(value="Missing Data", axis="index", inplace=True)
        if input_attribute == "Term":
            df.fillna(value="Missing Data", axis="index", inplace=True)
        df.rename(columns={"count(" + input_attribute + ")": "Count"}, inplace=True)


    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while 'getting data from temp table' in build_line_diagram")

    if input_attribute == "Source":
        source_dict = {"A": "Artificially propagated plants",
                       "C": "Bred in captivity",
                       "B": "Bred in captivity (Appx I)",
                       "F": "Born in captivity",
                       "I": "Confiscated specimens",
                       "O": "Pre-Convention specimens",
                       "R": "Ranched specimens",
                       "U": "Source unknown",
                       "W": "Taken from wild",
                       "X": "Taken from marine env.",
                       "Y": "Assisted production"}
        df.replace({"Source": source_dict}, inplace=True)

    if input_attribute == "Purpose":
        purpose_dict = {"B": "Breeding",
                        "E": "Educational",
                        "G": "Botanical garden",
                        "H": "Hunting Trophy",
                        "L": "Law enforcement",
                        "M": "Medical",
                        "N": "(Re)introduction",
                        "P": "Personal",
                        "Q": "Circus/Exhibition",
                        "S": "Scientific",
                        "T": "Commercial",
                        "Z": "Zoo", }
        df.replace({"Purpose": purpose_dict}, inplace=True)

    if input_attribute == "Term":
        term_dict = {
                     "specimens": "Common Products",
                     "bodies": "Animalia Products",
                     "feet": "Animalia Products",
                     "cultures": "Common Products",
                     "meat": "Animalia Products",
                     "claws": "Animalia Products",
                     "tails": "Animalia Products",
                     "hair": "Animalia Products",
                     "ears": "Animalia Products",
                     "eggs": "Animalia Products",
                     "fins": "Animalia Products",
                     "fingerlings": "Animalia Products",
                     "genitalia": "Animalia Products",
                     "calipee": "Animalia Products",
                     "gall": "Animalia Products",
                     "gall bladders": "Animalia Products",
                     "heads": "Animalia Products",
                     "musk": "Animalia Products",
                     "swim bladders": "Animalia Products",
                     "frog legs": "Animalia Products",
                     "trunk": "Animalia Products",
                     "pupae": "Animalia Products",
                     "eggshell": "Animalia Products",
                     "sawfish rostrum": "Animalia Products",
                     "gill plates": "Animalia Products",
                     "eggs (live)": "Animalia Products",
                     "timber pieces": "Plantae Products",
                     "roots": "Plantae Products",
                     "leaves": "Plantae Products",
                     "timber": "Plantae Products",
                     "flowers": "Plantae Products",
                     "fruit": "Plantae Products",
                     "wax": "Plantae Products",
                     "stems": "Plantae Products",
                     "sawn wood": "Plantae Products",
                     "chips": "Plantae Products",
                     "graft rootstocks": "Plantae Products",
                     "logs": "Plantae Products",
                     "plywood": "Plantae Products",
                     "veneer": "Plantae Products",
                     "bark": "Plantae Products",
                     "kernel": "Plantae Products",
                     "transformed wood": "Plantae Products",
                     "seeds": "Plantae Products",
                     "oil": "Common Products",
                     "live": "Common Products",
                     "dried plants": "Common Products",
                     "raw corals": "Common Products",
                     "fibres": "Common Products",
                     "extract": "Common Products",
                     "caviar": "Common Products",
                     "coral sand": "Common Products",
                     "pearls": "Common Products",
                     "pearl": "Common Products",
                     "trophies": "Processed Products",
                     "leather items": "Processed Products",
                     "shoes": "Processed Products",
                     "leather products (small)": "Processed Products",
                     "leather": "Processed Products",
                     "carvings": "Processed Products",
                     "wood products": "Processed Products",
                     "garments": "Processed Products",
                     "horn products": "Processed Products",
                     "horn carvings": "Processed Products",
                     "ivory carvings": "Processed Products",
                     "soup": "Processed Products",
                     "timber carvings": "Processed Products",
                     "cloth": "Processed Products",
                     "powder": "Processed Products",
                     "medicine": "Processed Products",
                     "leather products (large)": "Processed Products",
                     "flower pots": "Processed Products",
                     "furniture": "Processed Products",
                     "hair products": "Processed Products",
                     "sets of piano keys": "Processed Products",
                     "quills": "Processed Products",
                     "spectacle frames": "Processed Products",
                     "jewellery - ivory ": "Processed Products",
                     "jewellery": "Processed Products",
                     "wood product": "Processed Products",
                     "rug": "Processed Products",
                     "cosmetics": "Processed Products",
                     "piano keys": "Processed Products",
                     "fur products (large)": "Processed Products",
                     "fur product (small)": "Processed Products",
                     "skeletons": "Bone",
                     "skulls": "Bone",
                     "bone products": "Bone",
                     "bones": "Bone",
                     "teeth": "Bone",
                     "tusks": "Bone",
                     "bone carvings": "Bone",
                     "horns": "Bone",
                     "shells": "Bone",
                     "bone pieces": "Bone",
                     "ivory scraps": "Bone",
                     "horn pieces": "Bone",
                     "ivory pieces": "Bone",
                     "horn scraps": "Bone",
                     "baleen": "Bone",
                     "skins": "Skin",
                     "feathers": "Skin",
                     "carapaces": "Skin",
                     "scales": "Skin",
                     "skin scraps": "Skin",
                     "plates": "Skin",
                     "skin pieces": "Skin",
                     "sides": "Skin",
                     "unspecified": "Others",
                     "derivatives": "Others",
                     "venom": "Others",
                     "scraps": "Others",
                     }
        df["Category"] = df.loc[:, "Term"]
        df.replace({"Category": term_dict}, inplace=True)
        df["color_id"] = df.loc[:, "Category"]
        category_list = ["Animalia Products", "Plantae Products", "Common Products", "Processed Products", "Bone", "Skin", "Others"]
        legend_names = {}
        for category in category_list:
            unique_terms = set(df.loc[df["Category"] == category, "Term"].tolist())
            unique_string = {category : category + " (" + ", ".join(unique_terms) + ")"}
            legend_names.update(unique_string)
        df.drop(columns="Term", inplace=True)
        df.rename(columns={"Category":"Term"}, inplace=True)
        df = df.groupby(by=["Year", "Term", "color_id"], as_index=False)["Count"].sum()
    else:
        # Aggregate Misc
        df_misc = df.copy()
        df_misc = df_misc.groupby([input_attribute])["Count"].sum().sort_values(ascending=False)
        top_result = df_misc.idxmax()
        df_misc = df_misc.to_frame()
        df_misc.reset_index(inplace=True)
        df_misc = df_misc.loc[5:]
        misc_list = df_misc[input_attribute].tolist()
        misc_string = "Others (" + ", ".join(misc_list) + ")"
        df.replace(to_replace=misc_list, value=misc_string, inplace=True)

    fig = go.Figure(layout=dict(template="plotly"))
    if input_attribute == "Term":
        fig = px.line(
            df,
            y="Count",
            x="Year",
            color=input_attribute,
            color_discrete_map=color_dict,
            markers=True
        )
        fig.for_each_trace(lambda x: x.update(name=legend_names[x.name]))
    else:
        fig = px.line(
            df,
            y="Count",
            x="Year",
            color=input_attribute,
            color_discrete_sequence = color_discrete_sequence_list,
            markers=True
        )
    fig.update_layout(
        yaxis_title="Amount",
        xaxis_title="",
        legend_title="",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1,
            xanchor="center",
            x=0.5,
            itemclick="toggle",
            itemdoubleclick=False,
        ))
    fig.update_yaxes(
        zeroline=False,
        tick0=0,
    )
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        tickangle=45,
        tickfont=dict(size=14)
    )
    fig.update_traces(
        line=dict(width=3),
        connectgaps=False)

    return fig, df["Count"].sum()


"""
Build an empty map graph
"""


def build_empty_map_graph():
    fig_map = go.Figure(go.Scattergeo())
    fig_map.update_geos(
        showcoastlines=True, coastlinecolor="#dcdcce",
        showland=True, landcolor="#dfe1d2",
        showocean=True, oceancolor="#ebeced",
        showcountries=True, countrycolor="#bec2a3",
        projection_type="equirectangular",
        showframe=False,
    )
    fig_map.update_layout(  # https://plotly.com/python/reference/#layout
        height=500,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
        paper_bgcolor="#ebeced",
        plot_bgcolor="#ebeced"
    )
    return fig_map


"""
Add Distributions to map_graph
"""


def add_distributions_to_map_graph(input_taxon, conn, map_fig):
    sql = "SELECT * FROM species_plus WHERE \"Scientific Name\"=\"{0}\"".format(input_taxon)
    df = db.run_query(sql, conn)
    if len(df) == 0:
        # sql = "SELECT * FROM species_plus WHERE \"Listed under\"=\"{0}\"".format(input_taxon)
        # df = db.run_query(sql, conn)
        if len(df) == 0:
            print("Unable to find species in Species+ database...")
            return map_fig
    df.drop(labels=["Scientific Name", "Listed under", "Listing", "Party", "Full note"], axis=1, inplace=True)
    df.dropna(axis=1, inplace=True)
    df = df.transpose()
    df.reset_index(inplace=True)
    df.rename(columns={"index": "Distribution", 0: "Country"}, inplace=True)
    if len(df.Country.value_counts()) == 0:
        print("No distribution data is available...")
        return map_fig
    df.set_index(["Distribution"])
    df = df.apply(lambda x: x.str.split(",").explode())

    def row_name_to_alpha3(row, col):
        return convert_countrycode(row[col], "name", "alpha_3")

    def distribution_to_color(row, col):
        if row[col] == "Native_Distribution":
            return 0.1
        if row[col] == "Reintroduced_Distribution":
            return 0.2
        if row[col] == "Introduced_Distribution":
            return 0.3
        if row[col] == "Introduced(?)_Distribution":
            return 0.4
        if row[col] == "Distribution_Uncertain":
            return 0.5
        if row[col] == "Extinct(?)_Distribution":
            return 0.6
        if row[col] == "Extinct_Distribution":
            return 0.7

    def distribution_to_color_prioritized(row, col):
        if "Uncertain" in row[col]:
            return 0.5
        if "Reintroduced" in row[col]:
            return 0.2
        if "Possibly Extinct" in row[col]:
            return 0.6
        if "Extinct" in row[col]:
            return 0.7
        if "Native" in row[col]:
            return 0.1
        if "Introduced" in row[col]:
            return 0.3
        if "Possibly Introduced" in row[col]:
            return 0.4

    def bgcolor_converter(row, col):
        if row[col] == 0.5:  # Uncertain
            return "#fedfb7"
        if row[col] == 0.2:  # Reintroduced
            return "#d8efc4"
        if row[col] == 0.6:  # Possible Extinct
            return "#fdcccc"
        if row[col] == 0.7:  # Extinct
            return "#eb5254"
        if row[col] == 0.1:  # Native
            return "#8cde87"
        if row[col] == 0.3:  # Introduced
            return "#b495d5"
        if row[col] == 0.4:  # Possibly Introduced
            return "#e4d8ea"

    def text_generation(row, col):
        if row[col] == "Native_Distribution":
            return "Native"
        if row[col] == "Reintroduced_Distribution":
            return "Reintroduced"
        if row[col] == "Introduced_Distribution":
            return "Introduced"
        if row[col] == "Introduced(?)_Distribution":
            return "Possibly Introduced"
        if row[col] == "Distribution_Uncertain":
            return "Uncertain"
        if row[col] == "Extinct(?)_Distribution":
            return "Possibly Extinct"
        if row[col] == "Extinct_Distribution":
            return "Extinct"

    def fix_reintro(row, col):
        if "Reintro" in row[col]:
            new_string = row[col].replace("Reintro", "Reintroduced")
            return new_string

    df["alpha_3"] = df.apply(lambda row: row_name_to_alpha3(row, "Country"), axis=1)
    df["text"] = df.apply(lambda row: text_generation(row, "Distribution"), axis=1)
    df = df.groupby(["Country", "alpha_3"])["text"].apply("<br> ".join).reset_index()
    df["color_category"] = df.apply(lambda row: distribution_to_color_prioritized(row, "text"), axis=1)
    df["hoverlabel_bgcolor"] = df.apply(lambda row: bgcolor_converter(row, "color_category"), axis=1)

    map_fig.add_trace(go.Choropleth(
        z=df["color_category"],
        locations=df["alpha_3"],
        locationmode="ISO-3",
        text="<b>Country:</b> " + df["Country"] + "<br>" + "<b>Distribution Status (2022):</b><br> " + df["text"],
        hoverinfo="text",
        visible=True,
        zmin=0,
        zmax=1,
        colorscale=[
            [0, "rgba(77,77,77,0)"],  # Dummy
            [0.1, green],  # Native
            [0.2, lightgreen],  # Reintroduced
            [0.3, purple],  # Introduced
            [0.4, lightpurple],  # Introduced (?)
            [0.5, orange],  # Uncertain
            [0.6, lightred],  # Extinct (?)
            [0.7, red],  # Extinct
            [0.8, "rgba(77,77,77,0)"],  # Dummy
            [0.9, "rgba(77,77,77,0)"],  # Dummy
            [1, "rgba(77,77,77,0)"],  # Dummy
        ],
        hoverlabel=dict(
            bgcolor=df["hoverlabel_bgcolor"],
            bordercolor="black",
            font_color="black",
            font_size=12,
            font_family="Verdana",
            align="left",
        ),
        # Original Hoverlabel
        # hoverlabel=dict(
        #     bgcolor="white",
        #     bordercolor="black",
        #     font_size=12,
        #     font_family="Verdana",
        #     align="left",
        # ),
        # marker=dict(
        #     line=dict(
        #         color="red",
        #         width="10"
        #     ),
        # ),
        # colorscale="Bluered",
        showscale=False,
    ))
    return map_fig


"""
Update the map figure with traces
"""


def update_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn, map_shipments_lower_tol,
                     map_fig):
    verbose = True
    start = time.time()
    # Setup dataframe and find connections to trace.
    if verbose:
        end = time.time()
        elapsed_time = round(end - start, 0)
    df = db.get_data_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn)
    df.fillna(value="Unknown", axis="index", inplace=True)
    df.replace("XX", "Unknown", inplace=True)
    df2 = df.loc[:, ["Exporter", "Importer"]].drop_duplicates(inplace=False).reset_index(drop=True)
    df2["count"], df2["width"], df2["opacity"], df2["last_shipment"] = 0, 0.0, 0.0, 0
    shipment_traces = df2.set_index(["Exporter", "Importer"])
    shipment_traces.sort_index(level=0, inplace=True)

    # Calculate styling of connections
    def opacity_decrease(x):
        if x > 0.3:
            return x - 0.05
        else:
            return 0.05

    if verbose:
        end = time.time()
        elapsed_time = round(end - start, 0)
    current_year = 0
    Unknown_locations = 0
    for index, row in df.iterrows():
        if row["Importer"] != "Unknown" and row["Exporter"] != "Unknown":
            if current_year != row["Year"]:
                current_year = row["Year"]
                shipment_traces["opacity"] = shipment_traces["opacity"].apply(lambda x: opacity_decrease(x))
            shipment_traces.replace({"United States": "USA", "US": "USA"}, inplace=True)
            shipment_traces.loc[(row["Exporter"], row["Importer"]), ["count"]] += 1
            shipment_traces.loc[(row["Exporter"], row["Importer"]), ["opacity"]] = 1.0
            shipment_traces.loc[(row["Exporter"], row["Importer"]), ["last_shipment"]] = current_year
        else:
            Unknown_locations += 1
    if verbose:
        end = time.time()
        elapsed_time = round(end - start, 0)
    shipment_traces = shipment_traces[~(shipment_traces["count"] <= map_shipments_lower_tol)]
    shipment_traces = shipment_traces.reset_index()
    count_max = shipment_traces.loc[shipment_traces["count"].idxmax()].values[2]
    count_min = shipment_traces.loc[shipment_traces["count"].idxmin()].values[2]
    def width_percentage(n, count_max, count_min):
        return round(((n - count_min)/(count_max - count_min))*10, 2)
    shipment_traces["width"] = shipment_traces["count"].apply(lambda x: width_percentage(x, count_max, count_min))
    shipment_traces["width"].clip(lower=1, upper=10, axis=0, inplace=True)
    shipment_traces["mid_latitude"], shipment_traces["mid_longitude"] = 0.0, 0.0
    if verbose:
        end = time.time()
        elapsed_time = round(end - start, 0)

    def calculate_midpoint(row):
        # Python Implementatino of: http://www.movable-type.co.uk/scripts/latlong.html
        def to_radians(val):
            return val * math.pi / 180

        def to_degress(val):
            return val * 180 / math.pi

        lat1 = to_radians(row["exp_latitude"])
        lon1 = to_radians(row["exp_longitude"])
        lat2 = to_radians(row["imp_latitude"])
        lon2 = to_radians(row["imp_longitude"])
        Bx = math.cos(lat2) * math.cos(lon2 - lon1)
        By = math.cos(lat2) * math.sin(lon2 - lon1)
        row["mid_latitude"] = to_degress(math.atan2(math.sin(lat1) + math.sin(lat2),
                                                    math.sqrt((math.cos(lat1) + Bx) * (math.cos(lat1) + Bx) + By * By)))
        row["mid_longitude"] = to_degress(lon1 + math.atan2(By, math.cos(lat1) + Bx))
        return row

    def row_alpha2_to_name(row, col):
        return convert_countrycode(row[col], "alpha_2", "name")

    shipment_traces["Importer_full"] = shipment_traces.apply(lambda row: row_alpha2_to_name(row, "Importer"), axis=1)
    shipment_traces["Exporter_full"] = shipment_traces.apply(lambda row: row_alpha2_to_name(row, "Exporter"), axis=1)
    if verbose:
        end = time.time()
        elapsed_time = round(end - start, 0)
    historic_ISO_dict = {"AN": "BQ",
                         "CS": "RS",
                         "DD": "DE",
                         "NT": "IQ",
                         "PC": "FM",
                         "XA": "Unknown",
                         "XC": "Unknown",
                         "XE": "Unknown",
                         "XF": "Unknown",
                         "XM": "Unknown",
                         "XS": "Unknown",
                         "YU": "HR",
                         "ZC": "Unknown",
                         "ZZ": "Unknown",
                         }
    shipment_traces.replace({"Exporter": historic_ISO_dict}, inplace=True)
    shipment_traces.replace({"Importer": historic_ISO_dict}, inplace=True)

    # Adding Latitude/Longitude to Importer, Exporter & Midpoint

    json_file = "https://raw.githubusercontent.com/eesur/country-codes-lat-long/master/country-codes-lat-long-alpha3.json"
    with urlopen(json_file) as response:
        countries_json = json.load(response)
    countries_json = pd.DataFrame(countries_json["ref_country_codes"])
    if verbose:
        end = time.time()
        elapsed_time = round(end - start, 0)
    shipment_traces = shipment_traces.merge(countries_json[["latitude", "longitude", "alpha2"]], how="left",
                                            left_on="Importer", right_on="alpha2").drop(columns=["alpha2"]).rename(
        columns={"latitude": "imp_latitude", "longitude": "imp_longitude"})

    shipment_traces = shipment_traces.merge(countries_json[["latitude", "longitude", "alpha2"]], how="left",
                                            left_on="Exporter", right_on="alpha2").drop(columns=["alpha2"]).rename(
        columns={"latitude": "exp_latitude", "longitude": "exp_longitude"})

    shipment_traces = shipment_traces.apply(lambda row: calculate_midpoint(row), axis=1)

    shipment_traces["description"] = "<b>Exporter</b>: " + shipment_traces["Exporter_full"] + "<br>" + \
                                     "<b>Importer</b>: " + shipment_traces["Importer_full"] + "<br>" + \
                                     "——————————" + "<br>" \
                                                    "<b># Trades</b>: " + shipment_traces["count"].astype(
        str) + "<br>" + \
                                     "<b>Last Trade</b>: " + shipment_traces["last_shipment"].astype(str)
    shipment_traces.drop(["last_shipment"], axis=1)

    # Look for duplicate midpoints and move them slightly if found.

    def move_midpoint(row):
        row["mid_latitude"] = row["mid_latitude"] + random.uniform(3.0, 4.0)
        row["mid_longitude"] = row["mid_longitude"] + random.uniform(3.0, 4.0)
        return row

    if verbose:
        end = time.time()
        elapsed_time = round(end - start, 0)
    rows_series = shipment_traces[["mid_latitude", "mid_longitude"]].duplicated(keep="first")
    rows = rows_series[rows_series].index.values
    shipment_traces = shipment_traces.apply(
        lambda row: (move_midpoint(row) if row.name in rows else row), axis=1)
    if verbose:
        end = time.time()
        elapsed_time = round(end - start, 0)
    # Add traces to map figure
    for i in range(len(shipment_traces)):
        exp_lat, exp_lon = shipment_traces["exp_latitude"][i], shipment_traces["exp_longitude"][i]
        mid_lat, mid_lon = shipment_traces["mid_latitude"][i], shipment_traces["mid_longitude"][i]
        imp_lat, imp_lon = shipment_traces["imp_latitude"][i], shipment_traces["imp_longitude"][i]
        map_fig.add_trace(
            go.Scattergeo(
                lat=([exp_lat, mid_lat, imp_lat]),
                lon=([exp_lon, mid_lon, imp_lon]),
                mode="lines",
                hoverinfo="skip",
                line=dict(
                    width=shipment_traces["width"][i],
                    color="rgba(31, 120, 180, {})".format(shipment_traces["opacity"][i]))
            )),
    # Info Dot
    map_fig.add_trace(
        go.Scattergeo(
            lat=shipment_traces["mid_latitude"],
            lon=shipment_traces["mid_longitude"],
            text=shipment_traces["description"],
            mode="markers",
            hoverinfo="text",
            marker=dict(
                size=12,
                symbol="circle",
                opacity=shipment_traces["opacity"],
                cauto=False,
                color="#12476b",
                line=dict(
                    width=2,
                    color="#1f78b4"
                ),
            ),
            hoverlabel=dict(
                bgcolor="#6695b4",
                bordercolor="#1f78b4",
                font_color="black",
                font_size=12,
                font_family="Verdana",
                align="left",
            )

        )),
    return map_fig, shipment_traces


def map_tolerance_update(map_fig, shipment_traces, map_shipments_lower_tol):
    shipment_traces = shipment_traces[~(shipment_traces["count"] <= map_shipments_lower_tol)]
    shipment_traces = shipment_traces.reset_index()
    # Add traces to map figure
    for i in range(len(shipment_traces)):
        exp_lat, exp_lon = shipment_traces["exp_latitude"][i], shipment_traces["exp_longitude"][i]
        mid_lat, mid_lon = shipment_traces["mid_latitude"][i], shipment_traces["mid_longitude"][i]
        imp_lat, imp_lon = shipment_traces["imp_latitude"][i], shipment_traces["imp_longitude"][i]
        map_fig.add_trace(
            go.Scattergeo(
                lat=([exp_lat, mid_lat, imp_lat]),
                lon=([exp_lon, mid_lon, imp_lon]),
                mode="lines",
                hoverinfo="skip",
                line=dict(
                    width=shipment_traces["width"][i],
                    color="rgba(31, 120, 180, {})".format(shipment_traces["opacity"][i]))
            )),
    # Info Dot
    map_fig.add_trace(
        go.Scattergeo(
            lat=shipment_traces["mid_latitude"],
            lon=shipment_traces["mid_longitude"],
            text=shipment_traces["description"],
            mode="markers",
            hoverinfo="text",
            marker=dict(
                size=12,
                symbol="circle",
                opacity=shipment_traces["opacity"],
                cauto=False,
                color="#12476b",
                line=dict(
                    width=2,
                    color="#1f78b4"
                ),
            ),
            hoverlabel=dict(
                bgcolor="#6695b4",
                bordercolor="#1f78b4",
                font_color="black",
                font_size=12,
                font_family="Verdana",
                align="left",
            )

        )),
    return map_fig


def history_listing_generator(input_taxon, conn):
    sql = "SELECT * FROM history_listings WHERE FullName=\"{}\"".format(input_taxon)
    df = db.run_query(sql, conn)
    if df.empty:
        print("No data found in History Listings")
        return "No Data in History Listings."
    df.pop("FullName")
    df.pop("IsCurrent")
    df.rename(columns={"AnnotationEnglish": "Tooltip", "ChangeType": "Change"}, inplace=True)
    df["Change"].replace({"RESERVATION_WITHDRAWAL": "Reservation withdrawal"}, inplace=True)
    df["Change"] = df["Change"].str.title()
    df["Year"] = pd.to_datetime(df["EffectiveAt"]).dt.year
    df.pop("EffectiveAt")
    year_column = df.pop("Year")
    df.insert(0, "ID2", df.index)
    df.insert(1, "Year", year_column)

    table_header = [
        html.Thead(html.Tr([html.Th("Year"), html.Th("Appx."), html.Th("Change"), html.Th("")]))
    ]
    table_rows = []

    for ind in df.index:
        if df["Tooltip"][ind] is None:
            table_rows.append(
                html.Tr(
                    [
                        html.Td(df["Year"][ind]),
                        html.Td(df["Appendix"][ind]),
                        html.Td(df["Change"][ind]),
                        html.Td([])
                    ]
                )
            )
        else:
            table_rows.append(
                html.Tr(
                    [
                        html.Td(df["Year"][ind]),
                        html.Td(df["Appendix"][ind]),
                        html.Td(df["Change"][ind]),
                        html.Td([
                            html.I(className="bi bi-info-circle-fill me-2",
                                   id="tooltip{}".format(df["ID2"][ind])
                                   ),
                            dbc.Tooltip(
                                df["Tooltip"][ind],
                                target="tooltip{}".format(df["ID2"][ind]),
                                placement="top",
                            )
                        ]
                        )
                    ]
                )
            )

        table_body = [html.Tbody(table_rows)]

        table = dbc.Table(
            table_header + table_body,
            borderless=True,
            class_name="history_table_class",
            hover=False,
        )
    return table
