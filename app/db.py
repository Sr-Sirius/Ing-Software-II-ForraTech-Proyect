import psycopg2

def get_connection():

    conn = psycopg2.connect(
        host="localhost",
        database="forratech",
        user="postgres",
        password="1234",
        port="5432",
        options="-c client_encoding=UTF8"
    )

    return conn