import pycountry
import plotly.express as px
import pandas as pd
import database_scripts as db
import sqlite3

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


def buildLineDiagram(input_attribute, conn):
    # Get Data from temp table
    try:
        sql = "SELECT {}, Year FROM temp.taxon".format(input_attribute)
        df = db.runQuery(sql, conn)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while 'getting data from temp table' in buildLineDiagram")
    print(df.head(5))
    print("...........")
    df["Term"] = df["Term"].astype("category")
    df = df.groupby("Term", "Year")["Year"].count()
    print(df.head(5))
    fig = px.line(
        df,
        y="Term",
        x="Year",
        color=input_attribute,
        markers=True
    )
    return fig
