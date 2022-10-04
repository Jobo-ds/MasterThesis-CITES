"""
Functions for SQL-database
"""

import csv
import datetime
import os
import sqlite3
import time
import pandas as pd

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
            df = pandas.read_csv(file, dtype=dtypes_dict)
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
    print("Creating Auxiliary tables")
    # Create table with distinct rows
    try:
        sql = "CREATE TABLE distinct_table_amount AS SELECT DISTINCT Taxon, Class, \"Order\", Family, Genus, COUNT(Importer) as 'amount' FROM shipments GROUP BY Taxon, Class, \"Order\", Family, Genus;"
        db.execute(sql)
        print("Distinct Auxiliary Table successfully created")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating Distinct Auxiliary Table")
    # Create tables for specific data
    try:
        sql = "CREATE TABLE imports AS SELECT Importer as 'Country', COUNT(Importer) as 'Imports' from shipments GROUP BY Importer;"
        db.execute(sql)
        print("Imports table successfully created")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating imports table")
    try:
        sql = "CREATE TABLE exports AS SELECT Exporter as 'Country', COUNT(Exporter) as 'Exports' from shipments GROUP BY Exporter;"
        db.execute(sql)
        print("Exports table successfully created")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating exports table")
    print("Database creation complete")
