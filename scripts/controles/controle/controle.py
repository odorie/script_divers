import sys
import os
import sql
import datetime
import networkx as nx

import util
import const

sys.path.append(os.path.dirname(sys.path[0]))


def insert_simple_item(kind, resources, dep=None):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    util.check_kind(kind)

    level = util.get_level(kind)
    resource_type = util.get_resource(kind)

    conn = sql.util.db_connect()
    cur = conn.cursor()
    emprise = 'FR'
    if dep is not None:
        emprise = 'DEP{}'.format(dep)
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;", (timestamp, kind, level, len(resources), emprise))
    meta_id = cur.fetchone()[0]
    if len(resources) == 0:
        print("Nombre d'incos: {} \n".format(len(resources)))
        conn.commit()
        return
    
    for res in resources:
        cur.execute(
            "INSERT INTO controles.item(id,id_meta,comment,insee) VALUES (DEFAULT, %s, %s, %s) RETURNING id;",
            (meta_id, res[2], res[3])
        )
        item_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO controles.resource(id,id_res,version,name,id_item,insee) VALUES (DEFAULT, %s, %s, %s, %s, %s)",
            (res[0], res[1], resource_type, item_id, res[3])
        )
    conn.commit()

    print("Nombre d'incos: {} \n".format(len(resources)))


def insert_double_item(kind, resources):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    util.check_kind(kind)

    level = util.get_level(kind)
    resource_type = util.get_resource(kind)
  
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;", (timestamp, kind, level, len(resources), 'FR'))
    meta_id = cur.fetchone()[0]
    
    for res in resources:
        cur.execute(
            "INSERT INTO controles.item(id,id_meta,comment,insee) VALUES (DEFAULT, %s, %s, %s) RETURNING id;",
            (meta_id, res[4], res[5])
        )
        item_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO controles.resource(id,id_res,version,name,id_item,insee) VALUES (DEFAULT, %s, %s, %s, %s, %s)",
            (res[0], res[1], resource_type, item_id, res[5])
        )
        cur.execute(
            "INSERT INTO controles.resource(id,id_res,version,name,id_item,insee) VALUES (DEFAULT, %s, %s, %s, %s, %s)",
            (res[2], res[3], resource_type, item_id, res[5])
        )
    conn.commit()

    print("Nombre d'incos: {} \n".format(len(resources)))


def insert_item_from_pair(kind, resources, dep):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    util.check_kind(kind)

    level = util.get_level(kind)
    resource_type = util.get_resource(kind)

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
    if dep is not None:
        dep = "DEP{}".format(dep)
    else:
        dep = "FR"
    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;",
                (timestamp, kind, level, nb_ccx, dep))
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

    print("Nombre d'incos: {} \n".format(nb_ccx))

    cur.execute("UPDATE controles.metadata SET item_nb = {} WHERE id = {}".format(nb_ccx,meta_id))
    cur.execute("UPDATE controles.item c SET insee = r.insee FROM controles.resource as r WHERE c.insee is null and r.id_item = c.id")
    conn.commit()


def execute_simple(kind, requete):
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute(requete)
    resources = cur.fetchall()

    insert_simple_item(kind, resources)



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







