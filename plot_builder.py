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

    # Calculate Lines for Map
    # Setup MultiIndex DF
    df2 = df.loc[:, ["Importer", "Exporter"]]
    df2["width"] = 0.0
    df2["opacity"] = 0.0
    shipment_traces = df2.set_index(['Importer', 'Exporter'])

    # Calculate styling
    current_year = 0
    Null_locations = 0
    for index, row in df.iterrows():
        print("Hello0")
        if current_year != row['Year']:
            print(current_year)
            current_year = row['Year']
            print(current_year)
            year_passed = True
        # Add width and opacity
        print(row["Importer"], row["Exporter"])
        shipment_traces.at[(row["Importer"], row["Exporter"])]["width"] += 1.0
        shipment_traces.at[(row["Importer"], row["Exporter"])]["opacity"] = 1.0

    shipment_traces.to_csv('file_name.csv')
    print(f"Null Locations: {Null_locations}")


    with urlopen(
            'https://raw.githubusercontent.com/eesur/country-codes-lat-long/master/country-codes-lat-long-alpha3.json') as response:
        countries_json = json.load(response)
    countries_json = pd.DataFrame(countries_json["ref_country_codes"])

    import time

    start = time.time()

    df = df.merge(countries_json[['latitude', 'longitude', "alpha2"]], how='left', left_on='Importer',
                  right_on='alpha2').drop(columns=['alpha2']).rename(
        columns={"latitude": "imp_latitude", "longitude": "imp_longitude"})
    df = df.merge(countries_json[['latitude', 'longitude', "alpha2"]], how='left', left_on='Exporter',
                  right_on='alpha2').drop(columns=['alpha2']).rename(
        columns={"latitude": "exp_latitude", "longitude": "exp_longitude"})

    end = time.time()
    elapsed_time = end - start
    print(f"Timer: {elapsed_time}")

    # https://plotly.com/python/reference/scattergeo/
    # https://plotly.github.io/plotly.py-docs/generated/plotly.graph_objects.Scattergeo.html
    flight_paths = []
    for i in range(len(df)):
        map_fig.add_trace(
            go.Scattergeo(
                locationmode="ISO-3",
                lon=[df['exp_longitude'][i], df['imp_longitude'][i]],
                lat=[df['exp_latitude'][i], df['imp_latitude'][i]],
                mode='lines',
                line=dict(width=1, color='red'),
                # opacity=float(df['cnt'][i]) / float(df['cnt'].max()),
            )
        )
    end = time.time()
    elapsed_time = end - start
    print(f"Timer: {elapsed_time}")

    return map_fig


def TemporalControl(conn):
    print("Hello")
