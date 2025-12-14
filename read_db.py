import sqlite3
import json

db_name = "movies.db"

def _read_from_db_(query):
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Execute the provided SQL query
        cursor.execute(query)

        # Fetch all results from the executed query
        rows = cursor.fetchall()

        json_array = []
        for row in rows:
            try:
                if row[0]:
                    json_obj = json.loads(row[0])
                    json_array.append(json_obj)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON: {e}")
                continue        

        return json_array

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []

    finally:
        # Ensure the connection is closed
        if conn:
            conn.close()

def get_movie_by_actor(actor_name):
    db_name = "movies.db"
    query = f"SELECT movie_json FROM movies WHERE actors LIKE '%{actor_name}%'"
    return _read_from_db_(query)

def get_movie_by_title(title):
    db_name = "movies.db"
    query = f"SELECT movie_json FROM movies WHERE name LIKE '%{title}%'"
    return _read_from_db_(query)

def get_movie_by_director(director_name):
    db_name = "movies.db"
    query = f"SELECT movie_json FROM movies WHERE director LIKE '%{director_name}%'"
    return _read_from_db_(query)    

def get_movie_by_year(year):
    db_name = "movies.db"
    query = f"SELECT movie_json FROM movies WHERE year = {year}"
    return _read_from_db_(query)    