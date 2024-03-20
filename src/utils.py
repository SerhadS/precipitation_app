from urllib.request import urlretrieve
from tenacity import retry, stop_after_attempt
from sqlalchemy import create_engine
import os



@retry(stop=stop_after_attempt(5))
def file_download(url, filepath):
    """downloads a file from a given url

    Args:
        url (str): URL of the file
        filepath (str): the path the file to be saved
    """
    urlretrieve(url, filepath)


def get_db_engine():
    """returns db engine
    """
    db_params = {
            'username': os.getenv('POSTGRES_USER'),
            'password': os.getenv('POSTGRES_PASSWORD'),
            'host': 'localhost',
            'port': os.getenv('POSTGRES_PORT'),
            'database': os.getenv('POSTGRES_DB')
        }
    # Create engine
    engine = create_engine(f'postgresql+psycopg2://{db_params["username"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}')

    return engine
    


    