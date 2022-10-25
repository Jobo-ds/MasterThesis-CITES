import pycountry
import plotly.express as px
import pandas as pd
import database_scripts as db
import sqlite3
import json
from urllib.request import urlopen

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
    if outputfilter == "purpose":
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
                        {"label": "Commercial", "value": "C"},
                        {"label": "Zoo", "value": "Z"}
                        ]
        valid_dict_list = []
        for dicts in purpose_list:
            if dicts["value"] in filter_list:
                valid_dict_list.append(dicts)
    elif outputfilter == "source":
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
                        {"label": "Assisted production", "value": "Y"}
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


def buildLineDiagram(input_attribute, temporal_input, filter_terms, filter_purpose, conn):
    try:
        sql = "SELECT {0}, Year, count({0}) FROM temp.taxon WHERE Year<={1} GROUP BY {0}, Year ORDER BY Year, {0}".format(
            input_attribute, temporal_input)
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


def buildMapGraph(conn):
    try:
        sql = "SELECT Year, Importer, Exporter FROM temp.taxon"
        df = db.runQuery(sql, conn)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while 'getting data from temp table' in buildMapGraph")
        # Setup Map
    with urlopen(
            'https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/countries.geojson') as response:
        geojson = json.load(response)

    # https://plotly.github.io/plotly.py-docs/generated/plotly.express.choropleth.html
    fig_map = px.choropleth(
        locationmode="ISO-3",
        geojson=geojson,
        featureidkey="id",
        fitbounds="locations", )
    fig_map.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig_map


def drawOnMapGraph(conn):
    print("Hello")


def updateMapGraph(conn):
    print("Hello")


def TemporalControl(conn):
    print("Hello")
