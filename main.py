import read_db

db_name = "movies.db"

def main():
    result = read_db.read_from_db(db_name, "select movie_json from movies where actors like '%travolta%'")
    print(result)


if __name__ == "__main__":
    main()
