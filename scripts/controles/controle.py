from datetime import datetime
import string
import db_init

import os
import csv

#on prefixe systematiquement avec le type de ressource
controle_kind = {
    "housenumber_5000_9000": "alert",
    "housenumber_number_0": "alert",
    "housenumber_number_null": "alert",
    "housenumber_number_format": "incoherence",
    "housenumber_without_postcode": "incoherence",
    "housenumber_ordinal_format": "incoherence",
    "group_name_format": "incoherence",
    "housenumber_same_ordinal": "incoherence",
    "group_kind": "incoherence",
    "group_same_name": "alert"
}

resource_kinds = [
    "housenumber",
    "group",
    "position",
    "postcode",
    "municipality"
]


def insert_simple_item(kind, resources):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if kind not in controle_kind:
        raise Exception("kind unknown")

    splitted_kind = kind.split('_')
    level = controle_kind[kind]
    resource_type = splitted_kind[0]
    
    if resource_type not in resource_kinds:
        raise Exception("resource unknown") 

    conn = db_init.db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;", (timestamp, kind, level, len(resources), "FR"))
    meta_id = cur.fetchone()[0]
    if len(resources) == 0:
        conn.commit()
        return
        
    cur.execute("INSERT INTO controles.item VALUES (DEFAULT, %s) RETURNING id;", (meta_id,))
    item_id = cur.fetchone()[0]
    
    for res in resources:
        cur.execute("INSERT INTO controles.resource VALUES (DEFAULT, %s, %s, %s, %s)", (res[0], res[1], resource_type, item_id))
    conn.commit()


def insert_double_item(kind, resources):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if kind not in controle_kind:
        raise Exception("kind unknown")

    splitted_kind = kind.split('_')
    level = controle_kind[kind]
    resource_type = splitted_kind[0]
    if resource_type not in resource_kinds:
        raise Exception("resource unknown")
  
    conn = db_init.db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;", (timestamp, kind, level, len(resources), 'FR'))
    meta_id = cur.fetchone()[0]
    
    for res in resources:
        cur.execute("INSERT INTO controles.item VALUES (DEFAULT, %s) RETURNING id;", (meta_id,))
        item_id = cur.fetchone()[0]
        cur.execute("INSERT INTO controles.resource VALUES (DEFAULT, %s, %s, %s, %s)", (res[0], res[1], resource_type, item_id))
        cur.execute("INSERT INTO controles.resource VALUES (DEFAULT, %s, %s, %s, %s)", (res[2], res[1], resource_type, item_id))
    conn.commit()


def execute_simple(kind, sql):
    conn = db_init.db_connect()
    cur = conn.cursor()
    cur.execute(sql)
    resources = cur.fetchall()

    insert_simple_item(kind, resources)


def check_housenumber_5000_9000():
    execute_simple("housenumber_5000_9000", "SELECT pk, version FROM housenumber WHERE (number like '5%' OR number like '9%') AND char_length(number) > 3;")
    

def check_housenumber_number_null():
    execute_simple("housenumber_number_null", "SELECT pk, version FROM housenumber WHERE number is null;")


def check_housenumber_number_0():
    execute_simple("housenumber_number_0", "SELECT pk, version FROM housenumber WHERE number = '0' or number='00' or number='000' or number='0000' or number='00000';")


def check_housenumber_number_format():
    execute_simple("housenumber_number_format", "SELECT pk, version FROM housenumber WHERE number !~ '^([0-9]){0,5}$';")


def check_housenumber_without_postcode():
    execute_simple("housenumber_without_postcode", "SELECT pk, version FROM housenumber WHERE postcode_id is null;")


def check_housenumber_same_ordinal():
    conn = db_init.db_connect()
    cur = conn.cursor()
    cur.execute("SELECT hn1.pk, hn1.version, hn2.pk, hn2.version FROM housenumber as hn1, housenumber as hn2 WHERE hn1.pk != hn2.pk AND hn1.parent_id =hn2.parent_id AND hn1.number = hn2.number AND upper(hn1.ordinal) = substring(upper(hn2.ordinal) from 1 for 1);")
    resources = cur.fetchall()

    insert_double_item("housenumber_same_ordinal", resources)

def check_housenumber_ordinal_format():
    conn = db_init.db_connect()
    cur = conn.cursor()
    sql = """[!"$%&()*+,./:;<=>?[\]^-_|~#]+"""
    cur.execute("select pk, version from housenumber where ordinal ~* %s;", (sql,))
    resources = cur.fetchall()

    insert_simple_item("housenumber_ordinal_format", resources)

def check_group_name_format():
    conn = db_init.db_connect()
    cur = conn.cursor()
    sql = """[!"$%&()*+,/:;<=>?[\]^_|~#]+"""
    cur.execute("""select pk, version from "group" where name ~* %s;""", (sql,))
    resources = cur.fetchall()

    insert_simple_item("group_name_format", resources)

def check_group_kind():
    conn = db_init.db_connect()
    cur = conn.cursor()

    script_path = os.path.dirname(__file__)
    way_file_path = os.path.join(script_path, 'way.txt')
    area_file_path = os.path.join(script_path, 'area.txt')
    way_arr = open(way_file_path, 'r').read().splitlines()
    ways = ''
    for way in way_arr:
        ways += way + '|'
    ways = ways[:-1]

    areas = ''
    area_arr = open(area_file_path, 'r').read().splitlines()
    for area in area_arr:
        areas += area + '|'
    areas = areas[:-1]

    way_schem = '('+ways+') %'
    area_schem = '('+areas+') %'
    cur.execute("""SELECT pk, version FROM "group" where (name SIMILAR TO %s AND name NOT SIMILAR TO %s AND kind != 'way') OR (name SIMILAR TO %s AND name NOT SIMILAR TO %s AND kind != 'area')""", (way_schem, area_schem, area_schem, way_schem))
    resources = cur.fetchall()
    
    insert_simple_item("group_kind", resources)

def check_group_same_name():
    conn = db_init.db_connect()
    cur = conn.cursor()
    cur.execute(
        """select g1.pk, g1.version, g2.pk, g2.version 
        FROM "group" as g1, "group" as g2 
        where g1.municipality_id = g2.municipality_id 
        and g1.pk > g2.pk 
        and dmetaphone_alt(g1.name)=dmetaphone_alt(g2.name) 
        and levenshtein(g1.name, g2.name)::float/LEAST(length(g1.name), length(g2.name)) + (1-similarity(g1.name, g2.name)::float ) < 0.44"""
    )
    resources = cur.fetchall()

    insert_double_item("group_same_name", resources)
