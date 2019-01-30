import psycopg2
import requests
import json

conn_string = "host='sidt-ban.ign.fr' dbname='ban_anomaly_20190103' user='ban' port='5432'"
conn=psycopg2.connect(conn_string)

cur=conn.cursor()
cur.execute("SELECT kind, item.id FROM controles.metadata \
            JOIN controles.item ON item.id_meta=metadata.id;")
anomalies = cur.fetchall()
delete = []

#GET ALL ANOMALIES BAN
headers = {'Authorization': 'Bearer plop'}
response_count_ano = requests.get('http://sidt-ban.ign.fr:5959/anomaly?count=1', headers=headers)
total_ano = response_count_ano.json()["total"]
for i in range(0, total_ano, 100):
    response_ano = requests.get('http://sidt-ban.ign.fr:5959/anomaly?limit=100&offset={}'.format(i), headers=headers)
    collection_ano = response_ano.json()["collection"]
    for ano_ban in collection_ano:
        ano_ok = false
        for ano_steph in anomalies:
            if ano_steph[0]==ano_ban["kind"]:
                cur.execute("SELECT id_res, name, version FROM controles.resource where id_item={};".format(ano_steph[1]))
                resources = cur.fetchall()
                for version in ano_ban["versions"]:
                    version_ok = false
                    for resource in resources:
                        if version["model_pk"]==resource[0] and version["model_name"]==resource[1] and version["sequential"]==resource[2]:
                            version_ok = true
                            resources.pop(resource)
                            continue
                if version_ok and not resources:
                    ano_ok = true
                    anomalies.pop(ano_steph)
        if not ano_ok:                    
            delete.append(ano_ban)
json = '['
for ano in delete:
    json = json + '{"method":"DELETE", \
    "path":"/anomaly/{}"},'.format(ano['id'])
for ano in anomalies:
    json = json + '{"method":"POST", "path":"/anomaly", "body":{ "kind":"'+ano[0]+'", "insee":"", "versions":['
    cur.execute("SELECT * FROM controles.resource where id_item="+str(ano[1])+";")
    resources = cur.fetchall()
    for resource in resources:
        json = json + '{"resource":"", "id":"", "version":""},'
    json = json[:-1] + ']},'
json = json[:-1]+']'

print(json)
