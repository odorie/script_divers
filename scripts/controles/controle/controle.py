import sys
import os
sys.path.append(os.path.dirname(sys.path[0]))
import sql
import datetime
import networkx as nx

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
    "group_same_name": "alert",
    "housenumber_missing_ordinal": "incoherence",
    "position_pile":"incoherence"
}

resource_kinds = [
    "housenumber",
    "group",
    "position",
    "postcode",
    "municipality"
]


def insert_simple_item(kind, resources):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if kind not in controle_kind:
        raise Exception("kind unknown")

    splitted_kind = kind.split('_')
    level = controle_kind[kind]
    resource_type = splitted_kind[0]
    
    if resource_type not in resource_kinds:
        raise Exception("resource unknown") 

    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;", (timestamp, kind, level, len(resources), "FR"))
    meta_id = cur.fetchone()[0]
    if len(resources) == 0:
        conn.commit()
        return
    
    for res in resources:
        cur.execute("INSERT INTO controles.item VALUES (DEFAULT, %s, %s) RETURNING id;", (meta_id, res[2]))
        item_id = cur.fetchone()[0]
        cur.execute("INSERT INTO controles.resource VALUES (DEFAULT, %s, %s, %s, %s)", (res[0], res[1], resource_type, item_id))
    conn.commit()


def insert_double_item(kind, resources):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if kind not in controle_kind:
        raise Exception("kind unknown")

    splitted_kind = kind.split('_')
    level = controle_kind[kind]
    resource_type = splitted_kind[0]
    if resource_type not in resource_kinds:
        raise Exception("resource unknown")
  
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;", (timestamp, kind, level, len(resources), 'FR'))
    meta_id = cur.fetchone()[0]
    
    for res in resources:
        cur.execute("INSERT INTO controles.item VALUES (DEFAULT, %s, %s) RETURNING id;", (meta_id, res[4]))
        item_id = cur.fetchone()[0]
        cur.execute("INSERT INTO controles.resource VALUES (DEFAULT, %s, %s, %s, %s)", (res[0], res[1], resource_type, item_id))
        cur.execute("INSERT INTO controles.resource VALUES (DEFAULT, %s, %s, %s, %s)", (res[2], res[3], resource_type, item_id))
    conn.commit()


def insert_item_from_pair(kind, resources):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if kind not in controle_kind:
        raise Exception("kind unknown")

    splitted_kind = kind.split('_')
    level = controle_kind[kind]
    resource_type = splitted_kind[0]
    if resource_type not in resource_kinds:
        raise Exception("resource unknown")

    # chargement du graphe
    g = nx.Graph()
    for res in resources:
        g.add_edge(res[0],res[1])

    # calcul des composantes connexes
    print("Calcul composante connexe ({}) \n".format(str(datetime.datetime.now())))
    cc = nx.connected_components(g)

    # insertion des anomalies dans les tables de contrôle
    print("Insertion dans la table des anomalies ({}) \n".format(str(datetime.datetime.now())))
    nb_ccx = 0
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;",
                (timestamp, kind, level, nb_ccx, 'FR'))
    meta_id = cur.fetchone()[0]
    comment = ''

    for cci in cc:
        nb_ccx += 1
        cur.execute("INSERT INTO controles.item(id,id_meta,comment) VALUES (DEFAULT, %s, %s) RETURNING id;", (meta_id,comment))
        item_id = cur.fetchone()[0]
        insee = ""
        for ccii in cci:
            list = ccii.split('_')
            cur.execute("INSERT INTO controles.resource VALUES (DEFAULT, %s, %s, %s, %s, %s)",
                        (list[0], list[1], resource_type, item_id, list[2]))

    cur.execute("UPDATE controles.metadata SET item_nb = {} WHERE id = {}".format(nb_ccx,meta_id))
    cur.execute("UPDATE controles.item c SET insee = r.insee FROM controles.resource as r WHERE c.insee is null and r.id_item = c.id")
    conn.commit()


def execute_simple(kind, sql):
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute(sql)
    resources = cur.fetchall()

    insert_simple_item(kind, resources)


def check_housenumber_5000_9000():
    execute_simple("housenumber_5000_9000", "SELECT pk, version, '' FROM housenumber WHERE (number like '5%' OR number like '9%') AND char_length(number) > 3;")
    

def check_housenumber_number_null():
    execute_simple("housenumber_number_null", "SELECT pk, version, '' FROM housenumber WHERE number is null;")


def check_housenumber_number_0():
    execute_simple("housenumber_number_0", "SELECT pk, version, '' FROM housenumber WHERE number = '0' or number='00' or number='000' or number='0000' or number='00000';")


def check_housenumber_number_format():
    execute_simple("housenumber_number_format", "SELECT pk, version, '' FROM housenumber WHERE number !~ '^([0-9]){0,5}$';")


def check_housenumber_without_postcode():
    execute_simple("housenumber_without_postcode", "SELECT pk, version, '' FROM housenumber WHERE postcode_id is null;")


def check_housenumber_same_ordinal():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute("SELECT hn1.pk, hn1.version, hn2.pk, hn2.version, '' FROM housenumber as hn1, housenumber as hn2 WHERE hn1.pk != hn2.pk AND hn1.parent_id =hn2.parent_id AND hn1.number = hn2.number AND upper(hn1.ordinal) = substring(upper(hn2.ordinal) from 1 for 1);")
    resources = cur.fetchall()

    insert_double_item("housenumber_same_ordinal", resources)

def check_housenumber_ordinal_format():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    sql = """[!"$%&()*+,./:;<=>?[\]^-_|~#]+"""
    cur.execute("select pk, version, '' from housenumber where ordinal ~* %s;", (sql,))
    resources = cur.fetchall()

    insert_simple_item("housenumber_ordinal_format", resources)

def check_group_name_format():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    sql = """[!"$%&()*+,/:;<=>?[\]^_|~#]+"""
    cur.execute("""select pk, version, '' from "group" where name ~* %s;""", (sql,))
    resources = cur.fetchall()

    insert_simple_item("group_name_format", resources)

def check_group_kind():
    conn = sql.util.db_connect()
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
    cur.execute("""SELECT pk, version, '' FROM "group" where (name SIMILAR TO %s AND name NOT SIMILAR TO %s AND kind != 'way') OR (name SIMILAR TO %s AND name NOT SIMILAR TO %s AND kind != 'area')""", (way_schem, area_schem, area_schem, way_schem))
    resources = cur.fetchall()
    
    insert_simple_item("group_kind", resources)

def check_group_same_name():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute(
        """select g1.pk, g1.version, g2.pk, g2.version, '' 
        FROM "group" as g1, "group" as g2 
        where g1.municipality_id = g2.municipality_id 
        and g1.pk > g2.pk 
        and dmetaphone_alt(g1.name)=dmetaphone_alt(g2.name) 
        and levenshtein(g1.name, g2.name)::float/LEAST(length(g1.name), length(g2.name)) + (1-similarity(g1.name, g2.name)::float ) < 0.44"""
    )
    resources = cur.fetchall()

    insert_double_item("group_same_name", resources)

def check_housenumber_missing_ordinal():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    kind = 'housenumber_missing_ordinal'
    if kind not in controle_kind:
        raise Exception("kind unknown")

    splitted_kind = kind.split('_')
    level = controle_kind[kind]
    resource_type = splitted_kind[0]
    if resource_type not in resource_kinds:
        raise Exception("resource unknown")

    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute(
        """CREATE TEMPORARY TABLE IF NOT EXISTS temp_pos (
            ordinal VARCHAR(16),
            pos INT
        );
        INSERT INTO temp_pos (ordinal, pos) VALUES('', 1);
        INSERT INTO temp_pos (ordinal, pos) VALUES('A', 2);
        INSERT INTO temp_pos (ordinal, pos) VALUES('B', 3);
        INSERT INTO temp_pos (ordinal, pos) VALUES('C', 4);
        INSERT INTO temp_pos (ordinal, pos) VALUES('D', 5);
        INSERT INTO temp_pos (ordinal, pos) VALUES('E', 6);
        INSERT INTO temp_pos (ordinal, pos) VALUES('F', 7);
        INSERT INTO temp_pos (ordinal, pos) VALUES('G', 8);
        INSERT INTO temp_pos (ordinal, pos) VALUES('H', 9);
        INSERT INTO temp_pos (ordinal, pos) VALUES('I', 10);
        INSERT INTO temp_pos (ordinal, pos) VALUES('J', 11);
        INSERT INTO temp_pos (ordinal, pos) VALUES('K', 12);
        INSERT INTO temp_pos (ordinal, pos) VALUES('L', 13);
        INSERT INTO temp_pos (ordinal, pos) VALUES('BIS', 2);
        INSERT INTO temp_pos (ordinal, pos) VALUES('TER', 3);
        INSERT INTO temp_pos (ordinal, pos) VALUES('QUATER', 4);
        INSERT INTO temp_pos (ordinal, pos) VALUES('QUINQUIES', 5);
        INSERT INTO temp_pos (ordinal, pos) VALUES('SEXTO', 6);
        SELECT number, parent_id
        FROM (
            SELECT pk, version, number, parent_id, pos, rank() OVER (PARTITION BY number, parent_id ORDER BY pos ASC) AS posit
            FROM (
                SELECT hn.pk, hn.version, hn.number, hn.parent_id, hn.ordinal, tp.pos
                FROM housenumber hn JOIN temp_pos tp ON coalesce(hn.ordinal, '') = tp.ordinal
            ) AS t1
        ) AS t2
        WHERE posit!= pos
        GROUP BY number, parent_id;
        """
    )
    resources = cur.fetchall()
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;", (timestamp, kind, level, len(resources), 'FR'))
    meta_id = cur.fetchone()[0]
    
    for res in resources:
        cur.execute("INSERT INTO controles.item VALUES (DEFAULT, %s, %s) RETURNING id;", (meta_id, ''))
        item_id = cur.fetchone()[0]
        cur.execute("SELECT hn.pk, hn.version, coalesce(hn.ordinal, '') FROM housenumber hn JOIN temp_pos tp ON coalesce(hn.ordinal, '')=tp.ordinal WHERE number=%s AND parent_id=%s ORDER BY tp.pos;", (res[0], res[1]))
        housenumbers = cur.fetchall()
        comment = ''
        for hn in housenumbers:
            comment=comment + hn[2] + '-'
            cur.execute("INSERT INTO controles.resource VALUES (DEFAULT, %s, %s, %s, %s);", (hn[0], hn[1], resource_type, item_id))
        cur.execute("UPDATE controles.item SET comment=%s WHERE id=%s;", (comment, item_id))
    conn.commit()

    
def check_housenumber_outside_municipality():
    conn = sql.util.db_connect()
    cur = conn.cursor()
   
    cur.execute(
        """SELECT hn.pk, hn.version, 'num : ' || hn.number || ' // parent : ' || hn.parent_id || ' // insee : ' || mu.insee
        FROM housenumber hn INNER JOIN postcode pc ON hn.postcode_id=pc.pk
                            INNER JOIN municipality mu ON pc.municipality_id=mu.pk
                            INNER JOIN surface_commune sc ON mu.insee=sc.code_insee_cdc
                            INNER JOIN position po ON hn.pk=po.housenumber_id
        WHERE sc.gcms_detruit=FALSE AND hn.postcode_id IS NOT NULL AND ST_Within(ST_Transform(po.center, 2154), sc.geometrie)=FALSE
        UNION
        SELECT hn.pk, hn.version, 'num : ' || hn.number || ' // parent : ' || hn.parent_id || ' // insee : ' || mu.insee
        FROM housenumber hn INNER JOIN "group" gp ON hn.postcode_id=gp.pk
                            INNER JOIN municipality mu ON gp.municipality_id=mu.pk
                            INNER JOIN surface_commune sc ON mu.insee=sc.code_insee_cdc 
                            INNER JOIN position po ON hn.pk=po.housenumber_id
        WHERE sc.gcms_detruit=FALSE AND hn.postcode_id IS NULL AND ST_Within(ST_Transform(po.center, 2154), sc.geometrie)=FALSE;
    """)
    resources = cur.fetchall()

    insert_simple_item("housenumber_outside_municipality", resources)


def check_pile():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    print("Création table position projetee ({}) \n".format(str(datetime.datetime.now())))
    cur.execute("drop table if exists position90")
    cur.execute(
        "create table position90 as select p.*, st_transform(p.center,2154) as c2154, m.insee "
        "from position p, housenumber h, \"group\" g, municipality m "
        "where p.housenumber_id=h.pk "
        "and h.parent_id=g.pk "
        "and g.municipality_id=m.pk "
        "and m.insee like '90%'"
    )
    cur.execute("CREATE INDEX position90_c2154 ON position90 USING gist (c2154)")
    print("Regroupement par paire ({}) \n".format(str(datetime.datetime.now())))
    conn.commit()

    cur.execute(
        "SELECT p1.id || '_' || p1.version || '_' || p1.insee as cle1 , "
        "p2.id || '_' || p2.version || '_' || p2.insee as cle2 "
        "FROM position90 p1, position90 p2, "
        "housenumber h1, housenumber h2 "
        "WHERE p1.housenumber_id=h1.pk AND p2.housenumber_id=h2.pk AND "
        "NOT h1.pk=h2.pk AND "
        "p1.source_kind=p2.source_kind AND " 
        "p1.c2154 && st_buffer(p2.c2154,5) AND st_distance(p1.c2154, p2.c2154)<5"
    )
    resources = cur.fetchall()
    insert_item_from_pair("position_pile", resources)




