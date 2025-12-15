from read_db import get_movies_by_actor, get_movies_by_title, get_movies_by_director, get_movies_by_year, get_movies_by_genre


def main():
    result = get_movies_by_actor("travolta")
    print(result)


if __name__ == "__main__":
    main()
