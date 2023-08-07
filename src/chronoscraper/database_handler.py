"""
Module to handle database functionality

:author: Matt London
"""
import json
import sqlite3


def write_database_from_json(json_filename: str, db_filename: str, table_name: str) -> None:
    """
    Writes a json file into the database as a table

    :param json_filename: Path to the json file
    :param db_filename: Path to the database file
    :param table_name: Name of the table to write to
    """
    with open(json_filename, "r") as json_file:
        datalist = json.load(json_file)

    # Grab all the keys from the dictionaries
    all_keys = set().union(*(data.keys() for data in datalist))

    # Open the file
    conn = sqlite3.connect(db_filename)
    cursor = conn.cursor()

    # Create the table
    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ("

    # Grab all keys and remove spaces and slashes
    for key in all_keys:
        create_table_query += f"{key.replace(' ', '_').replace('/', '_')} TEXT, "

    # Complete the query
    create_table_query = create_table_query[:-2] + ");"
    cursor.execute(create_table_query)

    # Loop through all data and insert it to the table
    for datapoint in datalist:
        # Build the insert query
        insert_query = f"INSERT INTO {table_name} VALUES ("

        insert_query += "?, " * len(all_keys)

        insert_query = insert_query[:-2] + ");"

        # Add empty string for any missing keys
        values = [datapoint.get(key, "") for key in all_keys]

        # Run the query
        cursor.execute(insert_query, values)

    # Commit changes
    conn.commit()
    conn.close()
