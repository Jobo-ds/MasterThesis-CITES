import csv
import datetime
import os
import sqlite3
import time
import pandas as pd
import numpy as np
import pycountry

# Understanding distributions and their combinations.
print()


def connect_sqlite3(database):
    connection = None
    try:
        connection = sqlite3.connect(database + ".db", check_same_thread=False)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during 'connection to database' in connect_sqlite3")
    return connection


def get_df(sql, conn):
    try:
        result = pd.read_sql_query(sql, conn)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during run_query")
    return result


colnames = ["Scientific Name", "Distribution_Uncertain", "Extinct(?)_Distribution", "Extinct_Distribution",
            "Introduced(?)_Distribution", "Introduced_Distribution", "Native_Distribution", "Reintroduced_Distribution"]

col_list = ["Distribution_Uncertain", "Extinct(?)_Distribution", "Extinct_Distribution", "Introduced(?)_Distribution",
            "Introduced_Distribution", "Native_Distribution", "Reintroduced_Distribution"]

# Combinations (21)

Uncertain = {
    "Extinct(?)": 0,
    "Extinct": 0,
    "Introduced(?)": 0,
    "Introduced": 0,
    "Native": 0,
    "Reintroduced": 0,
}
Extinct_ = {
    "Extinct": 0,
    "Introduced(?)": 0,
    "Introduced": 0,
    "Native": 0,
    "Reintroduced": 0,
}
Extinct = {
    "Introduced(?)": 0,
    "Introduced": 0,
    "Native": 0,
    "Reintroduced": 0,
}
Introduced_ = {
    "Introduced": 0,
    "Native": 0,
    "Reintroduced": 0,
}
Introduced = {
    "Native": 0,
    "Reintroduced": 0,
}
Native = {
    "Reintroduced": 0,
}

conn = connect_sqlite3("cites")
sql = "SELECT * FROM species_plus"
df = get_df(sql, conn)
df.drop(labels=["Listed under", "Listing", "Party", "Full note"], axis=1, inplace=True)
print("Length of original DF: " + str(len(df)))
df.dropna(axis="rows", how="all", subset=col_list, inplace=True)
print("Length of DF with Null removed: " + str(len(df)))
df = df.apply(lambda x: x.str.split(',') if (str(x[1]) != 'None') else x, axis=1)
print(df.to_string(max_rows=20))

# Perform horribly optimized counting
for index, row in df.iterrows():
    for cols_outer, current_col in enumerate(range(2, 8, 1)):
        current_row_name = row["Scientific Name"]
        print(f"Looking into {current_row_name}.")
        if isinstance(row[cols_outer], list):
            for item in row[cols_outer]:
                cols_outer_title = row[cols_outer]
                print(f"Looking for {item} in {cols_outer_title}.")
                for cols_inner, target_col in enumerate(range(current_col+1, 8, 1)):
                    if isinstance(row[target_col], list):
                        if item in row[target_col]:
                            print(f"{item} is in {row[target_col]}")
                        else:
                            print("Found nothing.")
        else:
            print("Too bad! That wasn't a list! Didn't find a list at {cols_outer}, {current_col}")
