import sys
import os
sys.path.append(os.path.dirname(sys.path[0]))
import sql

try:
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute("CREATE SCHEMA IF NOT EXISTS controles")
    cur.execute("DROP TABLE IF EXISTS controles.resource")
    cur.execute("DROP TABLE IF EXISTS controles.item")
    cur.execute("DROP TABLE IF EXISTS controles.metadata")
    cur.execute("DROP TABLE IF EXISTS controles.ban_anomaly")
    cur.execute("CREATE TABLE controles.metadata (id serial PRIMARY KEY, date timestamp without time zone, kind character varying, level character varying, item_nb integer, extent character varying)")
    cur.execute("CREATE TABLE controles.item(id serial PRIMARY KEY, id_meta integer REFERENCES controles.metadata (id),comment text, insee varchar)")
    cur.execute("CREATE TABLE controles.resource(id serial PRIMARY KEY, id_res varchar, version integer, name character varying, id_item integer REFERENCES controles.item (id),insee varchar)")
    cur.execute("create table controles.ban_anomaly (id_anomaly varchar,kind varchar,id_res varchar,version integer)");
    cur.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")
    cur.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    conn.commit()

except Exception as e:
    print("Echec de la creation des tables")
    print(e)
