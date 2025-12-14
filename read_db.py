import sqlite3

def read_from_db(db_path, query):
    """
    Connects to the SQLite database at db_path, executes the provided SQL query,
    and returns the results as a list of tuples.

    :param db_path: Path to the SQLite database file.
    :param query: SQL query to be executed.
    :return: List of tuples containing the query results.
    """
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Execute the provided SQL query
        cursor.execute(query)

        # Fetch all results from the executed query
        results = cursor.fetchall()

        return results

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()