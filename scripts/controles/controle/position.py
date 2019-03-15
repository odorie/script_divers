import datetime

import sql
import util
import controle


def check_position_outside_municipality(dep):
    conn = sql.util.db_connect()
    cur = conn.cursor()

    proj = util.get_srid_proj(dep)

    cur.execute(
        "SELECT p.id, p.version, 'num : ' || h.number || ' // parent : ' || h.parent_id "
        "|| ' // insee : ' || m.insee, m.insee "
        "from position p, housenumber h, \"group\" g, municipality m, commune sc "
        "where p.housenumber_id=h.pk "
        "and h.parent_id=g.pk "
        "and g.municipality_id=m.pk "
        "and m.insee=sc.code_insee "
        "and sc.gcms_detruit=FALSE "
        "and ST_Within(st_transform(st_setsrid(p.center,4326),{}), st_setsrid(sc.geometrie_ge,{}))=FALSE "
        "and m.insee like '{}%'".format(proj, proj, dep)
    )
    resources = cur.fetchall()

    controle.controle.insert_simple_item("position_outside_municipality", resources, dep)



def check_position_pile(dep):
    """
    Vérifie calcul des positions superposées (même source à moins de xx mètres)
    :param dep: département à contrôler
    :return:
    """
    conn = sql.util.db_connect()
    cur = conn.cursor()
    print("Création table position projetee ({}) \n".format(str(datetime.datetime.now())))
    proj = util.get_srid_proj(dep)
    cur.execute("drop table if exists position_temp")
    cur.execute(
        "create table position_temp as select p.*, st_transform(st_setsrid(p.center,4326),{}) as proj, m.insee "
        "from position p, housenumber h, \"group\" g, municipality m "
        "where p.housenumber_id=h.pk "
        "and h.parent_id=g.pk "
        "and g.municipality_id=m.pk "
        "and m.insee like '{}%'".format(proj, dep)
    )
    cur.execute("CREATE INDEX idx_position_temp_proj ON position_temp USING gist (proj)")
    print("Regroupement par paire ({}) \n".format(str(datetime.datetime.now())))
    conn.commit()

    cur.execute(
        "SELECT p1.id || '_' || p1.version || '_' || p1.insee as cle1 , "
        "p2.id || '_' || p2.version || '_' || p2.insee as cle2 "
        "FROM position_temp p1, position_temp p2, "
        "housenumber h1, housenumber h2 "
        "WHERE p1.housenumber_id=h1.pk AND p2.housenumber_id=h2.pk AND "
        "NOT h1.pk=h2.pk AND "
        "p1.source_kind=p2.source_kind AND " 
        "p1.proj && st_buffer(p2.proj,5) AND st_distance(p1.proj, p2.proj)<5"
    )
    resources = cur.fetchall()
    controle.controle.insert_item_from_pair("position_pile", resources, dep)