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

"""
Auxiliary functions
"""


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
                        {"label": "Unknown", "value": "Unknown"}
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
                       {"label": "Unknown", "value": "Unknown"}
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
        df.fillna(value="Unknown", axis="index", inplace=True)


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

    # Create dict of appendix status

    fig = px.line(
        df,
        y="count(" + input_attribute + ")",
        x="Year",
        color=input_attribute,
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
            itemclick=False,
            itemdoubleclick=False,
        )
    )
    top_result = df[input_attribute].mode().tolist()
    top_result = [input_attribute.capitalize() for input_attribute in top_result]
    top_result = ", ".join(top_result)
    return fig, df["count(" + input_attribute + ")"].sum(), top_result


"""
Build an empty map graph
"""


def build_empty_map_graph():
    fig_map = go.Figure(go.Scattergeo())
    fig_map.update_geos(
        showcoastlines=True, coastlinecolor="#dcdcce",
        showland=True, landcolor="#dfe1d2",
        showocean=True, oceancolor="#6695b4",
        showcountries=True, countrycolor="#bec2a3",
        projection_type="equirectangular",
        showframe=False,
    )
    fig_map.update_layout(  # https://plotly.com/python/reference/#layout
        height=500,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
        paper_bgcolor="#eeeeee",
        plot_bgcolor="#eeeeee"
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
    df = df.apply(lambda x: x.str.split(',').explode())

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
        if "Extinct (?)" in row[col]:
            return 0.7
        if "Extinct" in row[col]:
            return 0.6
        if "Native" in row[col]:
            return 0.1
        if "Introduced" in row[col]:
            return 0.3
        if "Introduced (?)" in row[col]:
            return 0.4
        if "Reintro" in row[col]:
            return 0.2

    def text_generation(row, col):
        if row[col] == "Native_Distribution":
            return "Native"
        if row[col] == "Reintroduced_Distribution":
            return "Reintro"
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
            new_string = row[col].replace("Reintro", "Reintrodeuced")
            return new_string

    df["alpha_3"] = df.apply(lambda row: row_name_to_alpha3(row, "Country"), axis=1)
    df["text"] = df.apply(lambda row: text_generation(row, "Distribution"), axis=1)
    df = df.groupby(["Country", "alpha_3"])["text"].apply('<br> '.join).reset_index()
    df["color_category"] = df.apply(lambda row: distribution_to_color_prioritized(row, "text"), axis=1)

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
            [0.1, "rgba(26,152,80,0.5)"],  # Native
            [0.2, "rgba(145,207,96,0.5)"],  # Reintroduced
            [0.3, "rgba(217,239,139,0.5)"],  # Introduced
            [0.4, "rgba(217,239,139,0.25)"],  # Introduced (?)
            [0.5, "rgba(254,224,139,0.5)"],  # Uncertain
            [0.6, "rgba(215,48,39,0.5)"],  # Extinct (?)
            [0.7, "rgba(215,48,39,0.5)"],  # Extinct
            [0.8, "rgba(77,77,77,0)"],  # Dummy
            [0.9, "rgba(77,77,77,0)"],  # Dummy
            [1, "rgba(77,77,77,0)"],  # Dummy
        ],
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=12,
            font_family="Verdana",
            align="left",
        ),
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
    import time
    start = time.time()
    # Setup dataframe and find connections to trace.
    df = db.get_data_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn)
    df.fillna(value="Unknown", axis="index", inplace=True)
    df.replace("XX", "Unknown", inplace=True)
    df2 = df.loc[:, ["Exporter", "Importer"]].drop_duplicates(inplace=False).reset_index(drop=True)
    df2["count"], df2["width"], df2["opacity"], df2["last_shipment"] = 0, 0.0, 0.0, 0
    shipment_traces = df2.set_index(['Exporter', 'Importer'])
    shipment_traces.sort_index(level=0, inplace=True)

    # Calculate styling of connections
    def opacity_decrease(x):
        if x > 0.3:
            return x - 0.05
        else:
            return 0.05

    current_year = 0
    Unknown_locations = 0
    for index, row in df.iterrows():
        if row["Importer"] != "Unknown" and row["Exporter"] != "Unknown":
            if current_year != row['Year']:
                current_year = row['Year']
                shipment_traces["opacity"] = shipment_traces["opacity"].apply(lambda x: opacity_decrease(x))
            shipment_traces.loc[(row["Exporter"], row["Importer"]), ['count']] += 1
            shipment_traces.loc[(row["Exporter"], row["Importer"]), ['opacity']] = 1.0
            shipment_traces.loc[(row["Exporter"], row["Importer"]), ['last_shipment']] = current_year
        else:
            Unknown_locations += 1
    shipment_traces = shipment_traces[~(shipment_traces["count"] <= map_shipments_lower_tol)]
    shipment_traces = shipment_traces.reset_index()
    count_max = shipment_traces.loc[shipment_traces["count"].idxmax()].values[2]
    shipment_traces["width"] = round((shipment_traces["count"] / count_max) * 10, 2)
    shipment_traces["width"].clip(1, axis=0, inplace=True)
    shipment_traces = shipment_traces[shipment_traces['width'] != 0.0]
    shipment_traces["mid_latitude"], shipment_traces["mid_longitude"] = 0.0, 0.0

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

    json_file = 'https://raw.githubusercontent.com/eesur/country-codes-lat-long/master/country-codes-lat-long-alpha3.json'
    with urlopen(json_file) as response:
        countries_json = json.load(response)
    countries_json = pd.DataFrame(countries_json["ref_country_codes"])

    shipment_traces = shipment_traces.merge(countries_json[['latitude', 'longitude', "alpha2"]], how='left',
                                            left_on='Importer', right_on='alpha2').drop(columns=['alpha2']).rename(
        columns={"latitude": "imp_latitude", "longitude": "imp_longitude"})

    shipment_traces = shipment_traces.merge(countries_json[['latitude', 'longitude', "alpha2"]], how='left',
                                            left_on='Exporter', right_on='alpha2').drop(columns=['alpha2']).rename(
        columns={"latitude": "exp_latitude", "longitude": "exp_longitude"})

    shipment_traces = shipment_traces.apply(lambda row: calculate_midpoint(row), axis=1)

    shipment_traces["description"] = "<b>Exporter</b>: " + shipment_traces["Exporter_full"] + "<br>" + \
                                     "<b>Importer</b>: " + shipment_traces["Importer_full"] + "<br>" + \
                                     "——————————" + "<br>" \
                                                    "<b># Shipments</b>: " + shipment_traces["count"].astype(
        str) + "<br>" + \
                                     "<b>Last Shipment</b>: " + shipment_traces["last_shipment"].astype(str)
    shipment_traces.drop(["last_shipment"], axis=1)

    # Look for duplicate midpoints and move them slightly if found.

    def move_midpoint(row):
        row["mid_latitude"] = row["mid_latitude"] + random.uniform(3.0, 4.0)
        row["mid_longitude"] = row["mid_longitude"] + random.uniform(3.0, 4.0)
        return row

    rows_series = shipment_traces[["mid_latitude", "mid_longitude"]].duplicated(keep="first")
    rows = rows_series[rows_series].index.values
    shipment_traces = shipment_traces.apply(
        lambda row: (move_midpoint(row) if row.name in rows else row), axis=1)

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
                    color="rgba(54, 139, 51, {})".format(shipment_traces['opacity'][i]))
            )),
    # Info Dot
    map_fig.add_trace(
        go.Scattergeo(
            lat=shipment_traces["mid_latitude"],
            lon=shipment_traces["mid_longitude"],
            text=shipment_traces["description"],
            mode="markers",
            hoverinfo='text',
            marker=dict(
                size=12,
                symbol="circle",
                opacity=shipment_traces["opacity"],
                cauto=False,
                color="white",
                line=dict(
                    width=2,
                    color="lightgray"
                ),
            ),
            hoverlabel=dict(
                bgcolor="white",
                bordercolor="black",
                font_size=12,
                font_family="Verdana",
                align="left",
            )

        )),
    end = time.time()
    elapsed_time = end - start
    print(f"Timer: {elapsed_time}")
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
    print(df.to_string())

    table_header = [
        html.Thead(html.Tr([html.Th("Year"), html.Th("Appx."), html.Th("Change"), html.Th("")]))
    ]
    table_rows = []

    ind: object
    for ind in df.index:
        if df['Tooltip'][ind] is None:
            table_rows.append(
                html.Tr(
                    [
                        html.Td(df['Year'][ind]),
                        html.Td(df['Appendix'][ind]),
                        html.Td(df['Change'][ind]),
                        html.Td([])
                    ]
                )
            )
        else:
            table_rows.append(
                html.Tr(
                    [
                        html.Td(df['Year'][ind]),
                        html.Td(df['Appendix'][ind]),
                        html.Td(df['Change'][ind]),
                        html.Td([
                            html.I(className="bi bi-info-circle-fill me-2",
                                   id="tooltip{}".format(df["ID2"][ind])
                                   ),
                            dbc.Tooltip(
                                df['Tooltip'][ind],
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
