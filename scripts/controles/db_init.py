import psycopg2


def db_connect():
    try:
        conn = psycopg2.connect("dbname='ban_anomaly_20190103' user='ban'")
        return conn
    except Exception as e:
        print("Connection a la base impossible")
        print(e)

def init():
    conn=db_connect()

    try:
        cur = conn.cursor()
        cur.execute("CREATE SCHEMA IF NOT EXISTS controles;")
        cur.execute("DROP TABLE IF EXISTS controles.resource;")
        cur.execute("DROP TABLE IF EXISTS controles.item;")
        cur.execute("DROP TABLE IF EXISTS controles.metadata;")
        cur.execute("CREATE TABLE controles.metadata (id serial PRIMARY KEY, date timestamp without time zone, kind character varying, level character varying, item_nb integer, extent character varying);")
        cur.execute("CREATE TABLE controles.item(id serial PRIMARY KEY, id_meta integer REFERENCES controles.metadata (id),comment text);")
        cur.execute("CREATE TABLE controles.resource(id serial PRIMARY KEY, id_res integer, version integer, name character varying, id_item integer REFERENCES controles.item (id));")
        cur.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;")
        cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        conn.commit()
    except Exception as e:
        print("Echec de creation des tables")
        print(e)
