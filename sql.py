"""
Functions for SQL-database
"""

import csv
import datetime
import os
import sqlite3
import time
import pandas as pd
import numpy as np
import plot_builder as pltbld

"""
Function to connect to database
"""


def connect_sqlite3(database):
    connection = None
    try:
        connection = sqlite3.connect(database + ".db")
        print("Connection to SqLite DB successful")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred")
    return connection


"""
Function to get data from database
"""


def getData(sql, db):
    try:
        result = pd.read_sql_query(sql, db)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during getData")
    return result


"""
Returns a list of unique properties.
Useful for list content.
"""


def getDropdownList(attribute, table, db):
    try:
        sql = "SELECT DISTINCT {} from {}".format(attribute, table)
        result = pd.read_sql(sql, db)
        result = pd.unique(result)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during getUnique")
    return result

"""
Returns all imports/exports as a dataframe
"""

def getSpatialTotal():
    # Get Data from Database
    db = connect_sqlite3("cites")
    print("Getting Spatial Data")
    query_1 = "SELECT * from imports"
    query_2 = "SELECT * from exports"
    data_1 = getData(query_1, db)
    data_2 = getData(query_2, db)
    spatial_data = data_1.merge(data_2, how="outer", on="Country", sort=True)
    spatial_data.fillna(0, inplace=True)
    spatial_data.drop(spatial_data.tail(1).index, inplace=True)
    # Convert to Alpha-3, because that's how the geojson works)
    spatial_data["Country"] = spatial_data["Country"].apply(lambda x: pltbld.get_alpha_2_code(x))
    # Remove countries with no trade
    spatial_data = spatial_data[spatial_data.Imports != 0.0]
    spatial_data = spatial_data[spatial_data.Exports != 0.0]
    # Log() Numbers for better accuracy
    spatial_data["Imports"] = np.log(spatial_data["Imports"])
    spatial_data["Exports"] = np.log(spatial_data["Exports"])
    #print(spatial_data.to_string())
    print("Complete")
    return spatial_data


def getDropdownList(attribute, table, db):
    try:
        sql = "SELECT DISTINCT {} from {}".format(attribute, table)
        result = pd.read_sql(sql, db)
        result = pd.unique(result)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during getUnique")
    return result


"""
Build database from CITES csv files.
Only use to build a new database!
The auxiliary tables are for faster plotting, would probably be smarter with foreign keys.
"""


def build_database(database):
    # Build list of CSV files
    dir = os.path.dirname(__file__) + "\CITES/"
    csv_files = os.listdir(dir)
    csv_files = [dir + x for x in csv_files]
    # Get columns for database
    with open(csv_files[0], 'r') as f:
        csv_reader = csv.DictReader(f)
        cols = csv_reader.fieldnames
    # Ready datatypes for attributes
    datatypes = ["INTEGER", "INTEGER",
                 "TEXT", "TEXT",
                 "TEXT", "TEXT",
                 "TEXT", "TEXT",
                 "TEXT", "REAL",
                 "TEXT", "TEXT",
                 "TEXT", "TEXT",
                 "TEXT", "TEXT",
                 "TEXT", "TEXT",
                 "TEXT", "TEXT",
                 "INTEGER"
                 ]
    # Connect to database
    db = connect_sqlite3(database)
    # Create table with cols
    table = "shipments"
    # Drop table if it already exists
    sql = "drop table if exists {table}".format(
        table=table)
    db.execute(sql)
    # Create table
    try:
        sql = "create table {table} ({cols})".format(
            table=table,
            cols=", ".join("'{0}' {1}".format(value, datatypes[index]) for index, value in enumerate(cols)))
        db.execute(sql)
        print("Table successfully created")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating table")
    # Import data from csv files
    pandas_dtypes = ["int", "int",
                     "str", "str",
                     "str", "str",
                     "str", "str",
                     "str", "float",
                     "str", "str",
                     "str", "str",
                     "str", "str",
                     "str", "str",
                     "str", "str",
                     "int"]
    dtypes_dict = {cols[i]: pandas_dtypes[i] for i in range(len(cols))}
    print("Starting import of csv files...")
    i = 1
    total_files = len(csv_files)
    # Debug option for database testing
    debug = False
    total_rows_proc = 0
    # Timers, for convenience.
    process_times = []
    avg_processtime = 0
    total_processtime = 0
    time_remain = 0
    for file in csv_files:
        try:
            # Using pandas df is faster than iterating over rows
            start_time = time.perf_counter()
            df = pd.read_csv(file, dtype=dtypes_dict)
            df.to_sql(table, db, if_exists='append', index=False)
            # Calculate run time
            end_time = time.perf_counter()
            run_time = end_time - start_time
            process_times.append(run_time)
            avg_processtime = sum(process_times) / len(process_times)
            time_remain = (total_files - i) * avg_processtime
            time_remain = str(datetime.timedelta(seconds=time_remain))
            print(f"{file} imported successfully ({i}/{total_files}). Time Remaining: {time_remain[0:8]}")
            if debug:
                # Database stability check (Calculate if database has the correct size)
                print("WARNING: Debug is active. Import will be a lot slower.")
                df_rows = len(df)
                total_rows_proc = total_rows_proc + df_rows
                db_rows = db.execute("SELECT Count(*) FROM shipments")
                db_rows = db_rows.fetchone()[0]
                print(f"Rows in DF: {df_rows}. Total rows processed: {total_rows_proc}. Current rows in DB: {db_rows}.")
                if total_rows_proc != db_rows:
                    raise ValueError('Mismatch in database. Stopping import...')
            i += 1
        except sqlite3.Error as err:
            print(f"The error '{err}' occurred while importing {file}")
    print("CSV files imported successfully")
    print("Creating Auxiliary tables.. This will take a minute.. or two.")
    # Create table with distinct rows
    try:
        sql = "CREATE TABLE distinct_table_amount AS SELECT DISTINCT Taxon, Class, \"Order\", Family, Genus, COUNT(Importer) as 'amount' FROM shipments GROUP BY Taxon, Class, \"Order\", Family, Genus;"
        db.execute(sql)
        print("Distinct Auxiliary Table successfully created. Only two more to go...")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating Distinct Auxiliary Table")
    # Create tables for specific data
    try:
        sql = "CREATE TABLE imports AS SELECT Importer as 'Country', COUNT(Importer) as 'Imports' from shipments GROUP BY Importer;"
        db.execute(sql)
        print("Imports table successfully created. Almost there...")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating imports table")
    try:
        sql = "CREATE TABLE exports AS SELECT Exporter as 'Country', COUNT(Exporter) as 'Exports' from shipments GROUP BY Exporter;"
        db.execute(sql)
        print("Exports table successfully created.")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating exports table")
    print("Database creation complete")
