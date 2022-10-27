import pycountry
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import database_scripts as db
import sqlite3
import json
from urllib.request import urlopen
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


"""
Create dictionaries for filters from database results
"""


def createDictFilters(filter_list, outputfilter):
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


def buildLineDiagram(input_attribute, temporal_input, filter_terms, filter_purpose, filter_source, conn):
    try:
        sql_start = "SELECT {0}, Year, count({0}) FROM temp.taxon WHERE Year<={1} AND".format(input_attribute,
                                                                                              temporal_input)
        sql_purpose = "Purpose IN {0}".format(db.ListToSQL(filter_purpose))
        sql_purpose_null = "OR Purpose IS NULL"
        sql_source = "Source IN {0}".format(db.ListToSQL(filter_source))
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
        df = db.runQuery(sql, conn)
        df = df.loc[df['Term'].isin(filter_terms)].reset_index(drop=True)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while 'getting data from temp table' in buildLineDiagram")
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
    return fig


"""
Build a map graph
"""


def buildMapGraph():
    # Setup Map
    with urlopen(
            'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/countries.geojson') as response:
        geojson = json.load(response)

    # Documentation Links
    # https://plotly.com/python/maps/
    # https://plotly.github.io/plotly.py-docs/generated/plotly.express.choropleth.html
    # https://plotly.com/python/reference/layout/geo/

    fig_map = px.line_geo(
        locationmode="ISO-3",
        geojson=geojson,
        featureidkey="id",
        fitbounds="locations", )
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


def getDataMapGraph(temporal_input, filter_terms, filter_purpose, filter_source, conn):
    try:
        sql_start = "SELECT Year, Importer, Exporter FROM temp.taxon WHERE Year<={0} AND Term IN {1} AND".format(
            temporal_input, db.ListToSQL(filter_terms))
        sql_purpose = "Purpose IN {0}".format(db.ListToSQL(filter_purpose))
        sql_purpose_null = "OR Purpose IS NULL"
        sql_source = "Source IN {0}".format(db.ListToSQL(filter_source))
        sql_source_null = "OR Source IS NULL"
        sql_end = "ORDER BY Year"

        if "Unknown" in filter_purpose:
            sql = sql_start + " (" + sql_purpose + " " + sql_purpose_null + ")"
        else:
            sql = sql_start + " " + sql_purpose
        if "Unknown" in filter_source:
            sql = sql + " AND (" + sql_source + " " + sql_source_null + ")" + " " + sql_end
        else:
            sql = sql + " AND " + sql_source + " " + sql_end
        df = db.runQuery(sql, conn)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while 'getting data from temp table' in buildLineDiagram")

    return df


def drawOnMapGraph(importer, exporter, map_fig):
    print("Hello")


def updateMapGraph(temporal_input, filter_terms, filter_purpose, filter_source, conn, map_fig):
    import time

    start = time.time()
    df = getDataMapGraph(temporal_input, filter_terms, filter_purpose, filter_source, conn)
    df.fillna(value="Unknown", axis="index", inplace=True)
    # print(df.isnull().values.any())
    # x = input('Press Enter:')
    print(len(df))

    # Calculate Lines for Map
    # Setup MultiIndex DF
    df2 = df.loc[:, ["Exporter", "Importer"]].drop_duplicates(inplace=False).reset_index(drop=True)
    df2["width"] = 0.0
    df2["opacity"] = 0.0
    shipment_traces = df2.set_index(['Exporter', 'Importer'])
    shipment_traces.sort_index(level=0, inplace=True)
    # shipment_traces = df2.groupby(["Exporter", "Importer"])

    print("Length before adding widths and Opacity: " + str(len(shipment_traces)))

    def opacity_decrease(x):
        if x > 0.2:
            return x - 0.05
        else:
            return 0.05

    def width_increase(df, row):
        if df.loc[(row["Exporter"], row["Importer"]), ['width']].values[0] >= 10.0:
            return
        else:
            return 0.05

    # Calculate styling
    current_year = 0
    Unknown_locations = 0
    df.to_csv("df.csv", sep='\t')
    for index, row in df.iterrows():
        if row["Importer"] != "Unknown" and row["Exporter"] != "Unknown":
            if current_year != row['Year']:
                current_year = row['Year']
                shipment_traces["opacity"] = shipment_traces["opacity"].apply(lambda x: opacity_decrease(x))
            # Add width and opacity
            # print("Year: {}".format(row['Year']))
            # idx = pd.IndexSlice
            # wid_opq = shipment_traces.loc[idx[row["Exporter"], row["Importer"]], :]
            # print("Current width/opaq for {0} and {1}: {2}".format(row["Exporter"], row["Importer"], wid_opq))

            # print("Looking for: {} and {}".format(row["Exporter"], row["Importer"]))
            # print(shipment_traces.loc[idx[row["Exporter"], row["Importer"]], :])
            print(shipment_traces.loc[(row["Exporter"], row["Importer"]), ['width']].values[0])

            shipment_traces.loc[(row["Exporter"], row["Importer"]), ['width']] += 0.1
            shipment_traces.loc[(row["Exporter"], row["Importer"]), ['opacity']] = 1.0
            # print("Updated width/opaq for {0} and {1}: {2}".format(row["Exporter"], row["Importer"], wid_opq))
        else:
            Unknown_locations += 1

    print(f"Null Locations: {Unknown_locations}")
    shipment_traces = shipment_traces.reset_index()
    # print("======================")
    # print("Length before dropping 0: " + str(len(shipment_traces)))
    # print("======================")
    # print("Records with 0.0 widths (They shouldn't be there)")
    # print(shipment_traces[shipment_traces['width'] == 0.0])
    # shipment_traces = shipment_traces[shipment_traces['width'] != 0.0]
    # print("======================")
    # print("Length After dropping 0 rows: " + str(len(shipment_traces)))
    # print("======================")
    # print(shipment_traces)

    with urlopen(
            'https://raw.githubusercontent.com/eesur/country-codes-lat-long/master/country-codes-lat-long-alpha3.json') as response:
        countries_json = json.load(response)
    countries_json = pd.DataFrame(countries_json["ref_country_codes"])

    shipment_traces = shipment_traces.merge(countries_json[['latitude', 'longitude', "alpha2"]], how='left',
                                            left_on='Importer',
                                            right_on='alpha2').drop(columns=['alpha2']).rename(
        columns={"latitude": "imp_latitude", "longitude": "imp_longitude"})

    shipment_traces = shipment_traces.merge(countries_json[['latitude', 'longitude', "alpha2"]], how='left',
                                            left_on='Exporter',
                                            right_on='alpha2').drop(columns=['alpha2']).rename(
        columns={"latitude": "exp_latitude", "longitude": "exp_longitude"})

    print("====================== After Merge with GeoJSON")
    print(shipment_traces)

    # df = df.merge(countries_json[['latitude', 'longitude', "alpha2"]], how='left', left_on='Importer',
    #               right_on='alpha2').drop(columns=['alpha2']).rename(
    #     columns={"latitude": "imp_latitude", "longitude": "imp_longitude"})
    # df = df.merge(countries_json[['latitude', 'longitude', "alpha2"]], how='left', left_on='Exporter',
    #               right_on='alpha2').drop(columns=['alpha2']).rename(
    #     columns={"latitude": "exp_latitude", "longitude": "exp_longitude"})

    # https://plotly.com/python/reference/scattergeo/
    # https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Scattergeo.html
    flight_paths = []
    for i in range(len(shipment_traces)):
        map_fig.add_trace(
            go.Scattergeo(
                locationmode="ISO-3",
                lon=[shipment_traces["exp_longitude"][i], shipment_traces["imp_longitude"][i]],
                lat=[shipment_traces["exp_latitude"][i], shipment_traces["imp_latitude"][i]],
                mode='lines',
                line=dict(
                    width=shipment_traces["width"][i],
                    # opacity=shipment_traces["width"][i],
                    color="rgba(54, 139, 51, {})".format(shipment_traces['opacity'][i])),
                # opacity=float(df['cnt'][i]) / float(df['cnt'].max()),
            )
        )
    end = time.time()
    elapsed_time = end - start
    print(f"Timer: {elapsed_time}")

    return map_fig


def TemporalControl(conn):
    print("Hello")
