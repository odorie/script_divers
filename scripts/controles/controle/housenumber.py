import sys
import os
import controle
import sql
import datetime
import util
sys.path.append(os.path.dirname(sys.path[0]))


def check_housenumber_5000_9000():
    requete = "SELECT h.id, h.version, '', m.insee "
    requete += "from housenumber h, \"group\" g, municipality m "
    requete += "where h.parent_id=g.pk and g.municipality_id=m.pk and "
    requete += "( (number like '5%' OR number like '9%') AND char_length(number) > 3 )"
    controle.controle.execute_simple("housenumber_5000_9000", requete)


def check_housenumber_missing_ordinal():
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    kind = 'housenumber_missing_ordinal'
    level = util.get_level(kind)
    resource_type = util.get_resource(kind)

    conn = sql.util.db_connect()
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS temp_pos")
    cur.execute("CREATE TABLE IF NOT EXISTS temp_pos (ordinal VARCHAR(16),pos INT)")
    cur.execute(
        "INSERT INTO temp_pos (ordinal, pos) VALUES('', 1);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('A', 2);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('B', 3);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('C', 4);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('D', 5);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('E', 6);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('F', 7);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('G', 8);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('H', 9);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('I', 10);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('J', 11);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('K', 12);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('L', 13);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('BIS', 2);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('TER', 3);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('QUATER', 4);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('QUINQUIES', 5);"
        "INSERT INTO temp_pos (ordinal, pos) VALUES('SEXTO', 6);"
    )
    cur.execute("DROP TABLE IF EXISTS check_housenumber_missing_ordinal")
    cur.execute(
        """
        CREATE TABLE check_housenumber_missing_ordinal AS SELECT number, parent_id, max(m.insee) as insee
        FROM (
            SELECT pk, version, number, parent_id, pos, rank() OVER (PARTITION BY number, parent_id ORDER BY pos ASC) AS posit
            FROM (
                SELECT hn.pk, hn.version, hn.number, hn.parent_id, hn.ordinal, tp.pos
                FROM housenumber hn JOIN temp_pos tp ON coalesce(hn.ordinal, '') = tp.ordinal
            ) AS t1
        ) AS t2, \"group\" g, municipality m 
        WHERE posit!= pos and
        t2.parent_id=g.pk and g.municipality_id=m.pk 
        GROUP BY number, parent_id;        
        """)

    cur.execute("SELECT number, parent_id, insee FROM check_housenumber_missing_ordinal")
    resources = cur.fetchall()

    cur.execute("INSERT INTO controles.metadata VALUES (DEFAULT, %s, %s, %s, %s, %s) RETURNING id;",
                (timestamp, kind, level, len(resources), 'FR'))
    meta_id = cur.fetchone()[0]

    for res in resources:
        cur.execute(
            "INSERT INTO controles.item(id,id_meta,insee) VALUES (DEFAULT, %s, %s) RETURNING id;",
            (meta_id, res[2]))
        item_id = cur.fetchone()[0]
        cur.execute(
            "SELECT hn.id, hn.version, coalesce(hn.ordinal, '') FROM housenumber hn JOIN temp_pos tp ON coalesce(hn.ordinal, '')=tp.ordinal WHERE number=%s AND parent_id=%s ORDER BY tp.pos;",
            (res[0], res[1]))
        housenumbers = cur.fetchall()
        comment = ''
        for hn in housenumbers:
            comment = comment + hn[2] + '-'
            cur.execute(
                "INSERT INTO controles.resource(id,id_res,version,name,id_item,insee) VALUES (DEFAULT, %s, %s, %s, %s, %s);",
                        (hn[0], hn[1], resource_type, item_id, res[2])
            )
        cur.execute("UPDATE controles.item SET comment=%s WHERE id=%s;", (comment, item_id))
    conn.commit()

    print("Nombre d'incos: {} \n".format(len(resources)))


def check_housenumber_number_0():
    requete  = "SELECT h.id, h.version, '', m.insee "
    requete += "from housenumber h, \"group\" g, municipality m "
    requete += "where h.parent_id=g.pk and g.municipality_id=m.pk and "
    requete += "(number = '0' or number='00' or number='000' or number='0000' or number='00000')"
    controle.controle.execute_simple("housenumber_number_0", requete)


def check_housenumber_number_format():
    requete  = "SELECT h.id, h.version, '', m.insee "
    requete += "from housenumber h, \"group\" g, municipality m "
    requete += "where h.parent_id=g.pk and g.municipality_id=m.pk and "
    requete += "number !~ '^([0-9]){0,5}$'"
    controle.controle.execute_simple("housenumber_number_format", requete)


def check_housenumber_number_null():
    requete  = "SELECT h.id, h.version, '', m.insee "
    requete += "from housenumber h, \"group\" g, municipality m "
    requete += "where h.parent_id=g.pk and g.municipality_id=m.pk and "
    requete += "number is null"
    controle.controle.execute_simple("housenumber_number_null", requete)


def check_housenumber_ordinal_format():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    pattern = """[!"$%&()*+,./:;<=>?[\]^-_|~#]+"""
    cur.execute(
        "select h.id, h.version, '', m.insee "
        "from housenumber h, \"group\" g, municipality m " 
        "where h.parent_id=g.pk and "
        "g.municipality_id=m.pk and "
        "ordinal ~* '{}' "
        .format(pattern)
    )
    resources = cur.fetchall()

    controle.controle.insert_simple_item("housenumber_ordinal_format", resources)


def check_housenumber_same_ordinal():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT hn1.id, hn1.version, hn2.id, hn2.version, '', m.insee "
        "FROM housenumber as hn1, housenumber as hn2, \"group\" g, municipality m "
        "where hn1.parent_id=g.pk and "
        "g.municipality_id=m.pk and "
        "hn1.pk != hn2.pk AND hn1.parent_id =hn2.parent_id AND hn1.number = hn2.number "
        "and upper(hn1.ordinal) = substring(upper(hn2.ordinal) from 1 for 1)"
    )
    resources = cur.fetchall()

    controle.controle.insert_double_item("housenumber_same_ordinal", resources)


def check_housenumber_without_postcode():
    conn = sql.util.db_connect()
    cur = conn.cursor()
    requete = "SELECT h.id, h.version, '', m.insee "
    requete += "from housenumber h, \"group\" g, municipality m "
    requete += "where h.parent_id=g.pk and g.municipality_id=m.pk and "
    requete += "postcode_id is null"
    controle.controle.execute_simple("housenumber_without_postcode", requete)
