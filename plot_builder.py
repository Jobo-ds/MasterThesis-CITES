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

"""
Auxiliary functions
"""


def alpha2_to_alpha_3(value):
    for co in list(pycountry.countries):
        if value in co.alpha_2:
            return co.alpha_3
        else:
            for co in list(pycountry.historic_countries):
                if value in co.alpha_2:
                    return co.alpha_3
    return value + "(Not Found)"


def alpha3_to_Name(value):
    for co in list(pycountry.countries):
        if value in co.alpha_3:
            return co.name
        else:
            for co in list(pycountry.historic_countries):
                if value in co.alpha_3:
                    return co.name
    return value + "(Name Not Found)"


def alpha2_to_Name(value):
    for co in list(pycountry.countries):
        if value in co.alpha_2:
            return co.name
        else:
            for co in list(pycountry.historic_countries):
                if value in co.alpha_2:
                    return co.name
    return value + "(Name Not Found)"


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
        purpose_list = [{"label": "Artificially propagated plants", "value": "A"},
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
        for dicts in purpose_list:
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
        sql_end = "GROUP BY {0}, Year ORDER BY Year, {0}".format(input_attribute)

        if "Unknown" in filter_purpose:
            sql = sql_start + " (" + sql_purpose + " " + sql_purpose_null + ")"
        else:
            sql = sql_start + " " + sql_purpose
        if "Unknown" in filter_source:
            sql = sql + " AND (" + sql_source + " " + sql_source_null + ")"
        else:
            sql = sql + " AND " + sql_source
        sql = sql + " " + sql_end
        df = db.run_query(sql, conn)
        df = df.loc[df['Term'].isin(filter_terms)].reset_index(drop=True)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while 'getting data from temp table' in build_line_diagram")
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
            x=0.5
        )
    )
    top_term = df["Term"].mode().tolist()
    top_term = [term.capitalize() for term in top_term]
    top_term = ", ".join(top_term)
    return fig, df["count(Term)"].sum(), top_term


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
    fig_map.update_layout(
        height=500,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False
    )
    return fig_map


"""
Add Distributions to map_graph
"""


def add_distributions_to_map_graph(input_taxon, conn, map_fig):
    print(input_taxon)
    sql = "SELECT * FROM species_plus WHERE \"Scientific Name\"=\"{0}\"".format(input_taxon)
    df = db.run_query(sql, conn)
    if df.empty:
        sql = "SELECT * FROM species_plus WHERE \"Listed under\"=\"{0}\"".format(input_taxon)
        df = db.run_query(sql, conn)
        if df.empty:
            print("Unable to find species in Species+ database...")
            return map_fig

    def create_choropleth(country_string):
        countries = country_string.split(sep=",")
        countries_iso = []
        Unknown_countries = []
        for country in countries:
            try:
                country = pycountry.countries.get(name=country)
                countries_iso.append(country.alpha_3)
            except  AttributeError as err:
                print(f"The error '{err}' occurred while converting to alpha_2 in add_iso_cols_to_row")
                Unknown_countries.append(country)
        print(f"Result: {countries_iso}")
        print(f"Unknown: {Unknown_countries}")

        map_fig.add_trace(go.Choropleth(
            locations=countries_iso,
            z=100,
            text="Test",
            colorscale='Blues',
            autocolorscale=False,
            reversescale=True,
            marker_line_color='darkgray',
            marker_line_width=0.5,
            colorbar_tickprefix='$',
            colorbar_title='GDP<br>Billions US$'))
        return map_fig
    targets = set(df.columns.to_numpy().tolist())
    ignore_cols = {"Scientific Name", "Listed under", "Listing", "Party", "Full note"}
    for col in targets.difference(ignore_cols):
        create_choropleth(str(df[col].values[0]))
    return map_fig

"""
Update the map figure with traces
"""


def update_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn, map_fig):
    import time
    start = time.time()
    # Setup dataframe and find connections to trace.
    df = db.get_data_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn)
    df.fillna(value="Unknown", axis="index", inplace=True)
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

    shipment_traces = shipment_traces.reset_index()
    count_max = shipment_traces.loc[shipment_traces["count"].idxmax()].values[2]
    shipment_traces["width"] = round((shipment_traces["count"] / count_max) * 10, 2)
    shipment_traces["width"].clip(1, axis=0, inplace=True)
    shipment_traces = shipment_traces[shipment_traces['width'] != 0.0]
    shipment_traces["mid_latitude"], shipment_traces["mid_longitude"] = 0.0, 0.0

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
        lat3 = to_degress(math.atan2(math.sin(lat1) + math.sin(lat2),
                                     math.sqrt((math.cos(lat1) + Bx) * (math.cos(lat1) + Bx) + By * By)))
        lon3 = to_degress(lon1 + math.atan2(By, math.cos(lat1) + Bx))
        return lat3, lon3

    def row_alpha2_to_name(row, col):
        return alpha2_to_Name(row[col])

    shipment_traces["mid_latitude"] = shipment_traces.apply(lambda row: calculate_midpoint(row)[0], axis=1)
    shipment_traces["mid_longitude"] = shipment_traces.apply(lambda row: calculate_midpoint(row)[1], axis=1)
    shipment_traces["Importer_full"] = shipment_traces.apply(lambda row: row_alpha2_to_name(row, "Importer"), axis=1)
    shipment_traces["Exporter_full"] = shipment_traces.apply(lambda row: row_alpha2_to_name(row, "Exporter"), axis=1)
    shipment_traces["description"] = "<b>Exporter</b>: " + shipment_traces["Exporter_full"] + "<br>" + \
                                     "<b>Importer</b>: " + shipment_traces["Importer_full"] + "<br>" + \
                                     "——————————" + "<br>" \
                                                    "<b># Shipments</b>: " + shipment_traces["count"].astype(
        str) + "<br>" + \
                                     "<b>Last Shipments</b>: " + shipment_traces["last_shipment"].astype(str)

    # Merge connections that go both directions (keeping the highest width, and opacity)

    # print(shipment_traces.to_string())

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
            )

        )),
    map_fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            bordercolor="black",
            font_size=12,
            font_family="Verdana",
            align="left",
        )
    )
    end = time.time()
    elapsed_time = end - start
    print(f"Timer: {elapsed_time}")
    return map_fig
