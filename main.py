from read_db import get_movie_by_actor, get_movie_by_title, get_movie_by_director, get_movie_by_year



def main():
    result = get_movie_by_actor("travolta")
    print(result)


if __name__ == "__main__":
    main()
