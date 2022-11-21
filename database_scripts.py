import csv
import datetime
import os
import sqlite3
import time
import pandas as pd
import numpy as np
import pycountry

"""
Connect to database
"""


def connect_sqlite3(database):
    connection = None
    try:
        connection = sqlite3.connect(database + ".db", check_same_thread=False)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during 'connection to database' in connect_sqlite3")
    return connection


"""
Drop Table if already exists
"""


def drop_table_if_exist(conn, table):
    # Drop table if it already exists
    try:
        sql = "drop table if exists {table}".format(
            table=table)
        conn.execute(sql)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during 'drop table' in drop_table_if_exist")


"""
Create Table
"""


def create_table_from_df(conn, table, df):
    cols = df.columns.to_numpy().tolist()
    try:
        sql = "create table {table} ({cols})".format(
            table=table,
            cols=", ".join("'{0}' {1}".format(value, "TEXT") for index, value in enumerate(cols)))
        conn.execute(sql)
        print("Table successfully created")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating table")


"""
Run query on database and return as pandas df
"""


def run_query(sql, conn):
    try:
        result = pd.read_sql_query(sql, conn)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during run_query")
    return result


"""
Populate Dropdown Menu (Species)
"""


def build_dropdown_species():
    try:
        conn = connect_sqlite3("cites")
        df = run_query("SELECT Taxon from distinct_table_amount", conn)
        taxon_list = df["Taxon"].values.tolist()
        conn.close()
        return taxon_list
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred during build_dropdown_species")


"""
Create a temporary table in the sqlite database with Species Data
"""


def build_main_df(input_taxon, conn, ctxtriggered_id):
    if ctxtriggered_id == "input_taxon":
        try:
            sql = "DELETE FROM temp.taxon"
            conn.execute(sql)
            sql = "INSERT INTO temp.taxon SELECT * FROM shipments WHERE Taxon=\"{}\"".format(input_taxon)
            conn.execute(sql)
        except sqlite3.Error as err:
            print(f"The error '{err}' occurred while 'copying data into temp table' in build_main_df")
    else:
        try:
            sql = "CREATE TEMPORARY TABLE temp.taxon AS SELECT * FROM shipments WHERE Taxon=\"{}\"".format(input_taxon)
            conn.execute(sql)
            print("Temporary taxon table created.")
        except sqlite3.Error as err:
            print(f"The error '{err}' occurred while 'creating temporary taxon table' in build_main_df")

"""
Get all uniques in temporary table attribute
"""


def get_unique_values(attribute, conn):
    sql = "SELECT DISTINCT {} FROM temp.taxon".format(attribute)
    df = run_query(sql, conn)
    df = df.fillna(value="Unknown")
    return df[attribute].values.tolist()


"""
Convert Python List to SQL List
"""


def list_to_sql(Plist):
    citations = lambda x: "'" + str(x) + "'"
    Plist = map(citations, Plist)
    SQLlist = "(" + ", ".join(map(str, Plist)) + ")"
    return SQLlist


"""
Retrieve and transform data needed for shipments in map graph
"""


def get_data_map_graph(temporal_input, filter_terms, filter_purpose, filter_source, conn):
    try:
        sql_start = "SELECT Year, Importer, Exporter FROM temp.taxon WHERE Year<={0} AND Term IN {1} AND".format(
            temporal_input, list_to_sql(filter_terms))
        sql_purpose = "Purpose IN {0}".format(list_to_sql(filter_purpose))
        sql_purpose_null = "OR Purpose IS NULL"
        sql_source = "Source IN {0}".format(list_to_sql(filter_source))
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
        df = run_query(sql, conn)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while 'getting data from temp table' in get_data_map_graph")

    return df


"""
Retrieve data from CITES+ database, related to the current species.
"""


def retrieve_cites_plus(species):
    pass

    # Write data to temp table


"""
Test integrity of temporary tables.
"""


def integrity_test():
    pass


"""
Build database from CITES csv files.
Only use to build a new database!
The auxiliary tables are used to speed up certain functions.
"""


def ready_aux_databases(cites_plus_csv, cites_checklist_csv):
    print("Merging CITES+, CITES Checklist and CITES Trade Database.")
    print("Importing and Preparing Data")
    # CITES+
    # Get columns for database
    with open(cites_plus_csv, 'r') as f:
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
    conn = connect_sqlite3(database)
    # Create table with cols
    table = "shipments"
    # Drop table if it already exists
    sql = "drop table if exists {table}".format(
        table=table)
    conn.execute(sql)
    # Create table
    try:
        sql = "create table {table} ({cols})".format(
            table=table,
            cols=", ".join("'{0}' {1}".format(value, datatypes[index]) for index, value in enumerate(cols)))
        conn.execute(sql)
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
            df.to_sql(table, conn, if_exists='append', index=False)
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
                db_rows = conn.execute("SELECT Count(*) FROM shipments")
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
        sql = "CREATE TABLE distinct_table_amount AS SELECT DISTINCT Taxon, Class, \"Order\", Family, Genus, COUNT(Importer) as 'amount' FROM shipments GROUP BY Taxon, Class, \"Order\", Family, Genus,"
        conn.execute(sql)
        print("Distinct Auxiliary Table successfully created. Only two more to go...")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating Distinct Auxiliary Table")
    # Create tables for specific data
    try:
        sql = "CREATE TABLE imports AS SELECT Importer as 'Country', COUNT(Importer) as 'Imports' from shipments GROUP BY Importer,"
        conn.execute(sql)
        print("Imports table successfully created. Almost there...")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating imports table")
    try:
        sql = "CREATE TABLE exports AS SELECT Exporter as 'Country', COUNT(Exporter) as 'Exports' from shipments GROUP BY Exporter,"
        conn.execute(sql)
        print("Exports table successfully created.")
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while creating exports table")
    print("Main Database creation complete")
    print("Create species+ database")
    build_species_plus_table("cites")


def build_species_plus_table(database):
    speciesplus_csv = "CITES/species_plus_params_cites_listing.csv"
    # Optimize Pandas Import
    # Get columns for database
    with open(speciesplus_csv, 'r') as f:
        csv_reader = csv.DictReader(f)
        cols = csv_reader.fieldnames
    dtypes_dict = {cols[i]: "str" for i in range(len(cols))}
    df = pd.read_csv(speciesplus_csv, dtype=dtypes_dict)
    # Drop Cols
    drop_cols = ["Id", "Kingdom", "Family", "Phylum", "Class", "Order", "Genus", "Species", "Subspecies",
                 "Author", "Rank", "# Full note", "All_DistributionFullNames", "All_DistributionISOCodes",]
    df.drop(labels=drop_cols, axis="columns", inplace=True)
    df.rename(columns={"NativeDistributionFullNames": "Native_Distribution"}, inplace=True)
    conn = connect_sqlite3(database)
    table = "species_plus"
    drop_table_if_exist(conn, table)
    create_table_from_df(conn, table, df)
    # Sort Cols for nicety
    df = df.reindex(sorted(df.columns), axis=1)
    first_column = df.pop("Scientific Name")
    second_column = df.pop("Listed under")
    third_column = df.pop("Listing")
    fourth_column = df.pop("Party")
    df.insert(0, "Scientific Name", first_column)
    df.insert(1, "Listed under", second_column)
    df.insert(2, "Listing", third_column)
    df.insert(3, "Party", fourth_column)
    # Insert Data to table database
    try:
        df.to_sql(table, conn, if_exists='replace', index=False)
    except sqlite3.Error as err:
        print(f"The error '{err}' occurred while importing species + database")
    print("Species+ Database creation complete")
