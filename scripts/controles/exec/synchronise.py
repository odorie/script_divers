import sys
import os
sys.path.append(os.path.dirname(sys.path[0]))
import progressbar
import datetime
import psycopg2.extras
import argparse
import ban
import sql
import util

print("========================================\n")
print("Debut de la synchronisation avec la ban ({}) \n".format(str(datetime.datetime.now())))

parser = argparse.ArgumentParser()
parser.add_argument("--kind", help="Kind à traiter (un seul kind)",type=str)
parser.add_argument("--dept", help="Numéro du département à traiter (un seul département)",type=str)
args = parser.parse_args()

# vérification du paramètre kind
kind = args.kind
if kind is None:
    raise Exception("L'argument kind est nul")
split_kind = kind.split(",")
if len(split_kind) != 1:
    raise Exception("L'argument kind {} est multiple".format(kind))
util.check_kinds(split_kind)


# vérification du paramètre dept
dept = args.dept
if dept is None:
    raise Exception("L'argument dept est nul")
if dept != "fr":
    split_dept = dept.split(",")
    if len(split_dept) != 1:
        raise Exception("L'argument dept {} est multiple".format(dept))
    util.check_depts(split_dept)


conn = sql.util.db_connect()
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

# Récupération de toutes les anomalies BAN de ce kind et sur ce département
# Et chargement dans la table controles.ban_anomaly de la base de travail
cur.execute("TRUNCATE controles.ban_anomaly")

print("Recuperation des anomalies ban de kind {} sur le dép {} \n".format(kind, dept))
total_ano = ban.request.get_anomaly_count(dept, kind)

bar = progressbar.ProgressBar(max_value=total_ano).start()
count = 0

for i in range(0, total_ano, 100):
    collection_ano = ban.request.get_anomaly_by_bloc(dept,kind,100,i)
    # on liste chaque anomalie
    for ano_ban in collection_ano:
        count = count + 1
        resources = ano_ban['versions']
        for resource in resources:
            cur.execute("INSERT INTO controles.ban_anomaly(id_anomaly,kind,id_res,version) VALUES (%s, %s, %s, %s)",
                        (ano_ban['id'], kind, resource['data']['id'], resource['data']['version']))
        if count % 17 == 0:
            bar.update(count)
conn.commit()
bar.finish()

# Comparaison des anomalies calculées et des anomalies BAN : on le fait en PostgreSQL :
# on fait 2 tables anomalies new et anomalies old
# on calcule une clé commune sur (concaténation des id ban + version)
print("\nComparaison des anomalies ban \n")

# pour les new, on recherche le dernier lancement de ce contrôle (id_meta)
if dept != "fr":
    cur.execute(
        "select id from controles.metadata where extent = 'DEP{}' and kind = '{}' order by id DESC limit 1;"
        .format(dept, kind)
    )
else:
    cur.execute(
        "select id from controles.metadata where extent = 'FR' and kind = '{}' order by id DESC limit 1;"
        .format(kind)
    )

res = cur.fetchone()
# puis on ne récupère que les items correspondants à ce dernier lancement
if res is not None:
    id_meta = res["id"]
else:
    id_meta = -1
cur.execute("drop table if exists controles.new")
cur.execute(
    "create table controles.new as select r.id_item,"
    "md5(string_agg(r.id_res || '-' || r.version, '|' order by r.id_res)) as md5, "
    "string_agg(r.id_res || '_' || r.version, '|' order by r.id_res) as id_resources "
    "from controles.resource as r "
    "left join controles.item as i on i.id = r.id_item where i.id_meta = {} group by r.id_item"
    .format(id_meta)
)

# pour les olds, on les récupère celles qui viennent de l'api ban
cur.execute("drop table if exists controles.old")
cur.execute(
    "create table controles.old as  select id_anomaly,"
    "md5(string_agg(id_res || '-' || version, '|' order by id_res)) as md5, "
    "string_agg(id_res || '_' || version, '|' order by id_res) as id_resources "
    "from controles.ban_anomaly group by id_anomaly "
)

# comparaison old/new basée sur la clé de comparaison
cur.execute("create index idx_md5_controles_new on controles.new(md5)")
cur.execute("create index idx_md5_controles_old on controles.old(md5)")
conn.commit()

# les nouvelles anomalies (celles qui sont dans new et pas dans old)
cur.execute("drop table if exists controles.anomaly_new")
cur.execute(
    "create table controles.anomaly_new as select n.*,o.id_anomaly,i.insee from controles.new as n "
    "left join controles.old as o on (n.md5 = o.md5) "
    "left join controles.item as i on (n.id_item = i.id) "
    "where o.id_anomaly is null"
)
cur.execute("select count(*) from controles.anomaly_new")
row = cur.fetchone()
print("Création de {} anomalie(s) dans la ban \n".format(row['count']))
bar = progressbar.ProgressBar(max_value=row['count']).start()
count = 0

cur.execute("select * from controles.anomaly_new")
type_resource = kind.split("_")[0]
for row in cur:
    count = count + 1
    anomaly = {}
    anomaly["kind"] = kind
    anomaly["insee"] = row["insee"]
    versions = []
    resources = row['id_resources'].split("|")
    for resource in resources:
        json_resource = {}
        id,version = resource.split("_")
        json_resource["id"] = id
        json_resource["version"] = version
        json_resource["resource"] = type_resource
        versions.append(json_resource)
    anomaly["versions"] = versions
    ban.request.post_anomaly(anomaly)
    if count % 17 == 0:
        bar.update(count)
bar.finish()

# les anomalies à supprimer de la ban (celles qui sont dans old et pas dans new)
cur.execute("drop table if exists controles.anomaly_old")
cur.execute(
    "create table controles.anomaly_old as select o.* from controles.old as o "
    "left join controles.new as n on (n.md5 = o.md5) "
    "where n.id_item is null"
)
cur.execute("select count(*) from controles.anomaly_old")
row = cur.fetchone()
print("Suppression de {} anomalie(s) dans la ban \n".format(row['count']))
bar = progressbar.ProgressBar(max_value=row['count']).start()
count = 0

cur.execute("select * from controles.anomaly_old")
type_resource = kind.split("_")[0]
for row in cur:
    count = count + 1
    print("suppression {}".format(row['id_anomaly']))
    ban.request.delete_anomaly(row['id_anomaly'])
    if count % 17 == 0:
        bar.update(count)
bar.finish()

print("Fin de la synchronisation ({}) \n".format(str(datetime.datetime.now())))

