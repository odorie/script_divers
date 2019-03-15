import sys
import os
import sql
import controle
import const
sys.path.append(os.path.dirname(sys.path[0]))


def check_group_kind():
    conn = sql.util.db_connect()
    cur = conn.cursor()

    way_file_path = os.path.join(const.ROOT_DIR, 'config\way.txt')
    area_file_path = os.path.join(const.ROOT_DIR, 'config\\area.txt')
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

    way_schem = '(' + ways + ') %'
    area_schem = '(' + areas + ') %'
    cur.execute(
        "SELECT g.id, g.version, '', m.insee FROM \"group\" g, municipality m where g.municipality_id=m.pk and ((g.name SIMILAR TO %s AND g.name NOT SIMILAR TO %s AND kind != 'way') OR (g.name SIMILAR TO %s AND g.name NOT SIMILAR TO %s AND kind != 'area'))",(way_schem, area_schem, area_schem, way_schem)
    )

    resources = cur.fetchall()
    controle.controle.insert_simple_item("group_kind", resources)


def check_group_same_name():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute(
        "select g1.id, g1.version, g2.id, g2.version, '', m.insee "
        "FROM \"group\" as g1, \"group\" as g2, municipality m " 
        "where g1.municipality_id = g2.municipality_id "
        "and g1.municipality_id=m.pk "
        "and g1.pk > g2.pk "
        "and dmetaphone_alt(g1.name)=dmetaphone_alt(g2.name) " 
        "and levenshtein(g1.name, g2.name)::float/LEAST(length(g1.name), length(g2.name)) + (1-similarity(g1.name, g2.name)::float ) < 0.44 "
    )
    resources = cur.fetchall()
    controle.controle.insert_double_item("group_same_name", resources)


def check_group_name_format():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    pattern = """[!"$%&()*+,/:;<=>?[\]^_|~#]+"""
    cur.execute(
        "select g.id, g.version, '',  m.insee from \"group\" g, municipality m where g.municipality_id=m.pk and g.name ~* '{}';".format(pattern)
    )
    resources = cur.fetchall()

    controle.controle.insert_simple_item("group_name_format", resources)