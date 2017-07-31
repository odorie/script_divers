#!/bin/sh
# But : exporter la ban en json 
################################################################################
# ARGUMENT :* $1 : repertoire dans lequel seront generes les json
################################################################################
#  Les donnees doivent etre dans la base ban_init en local et avoir la structure provenant
# des csv IGN
#############################################################################
# REMARQUE :
# - la base PostgreSQL, le port doivent être passés dans les variables d'environnement
#     PGDATABASE et PGUSER
#############################################################################
outPath=$1

if [ $# -ne 1 ]; then
        echo "Usage : export_ban_json.sh <outPath> "
        echo "Exemple : export_ban_json.sh /home/ban/test"
        exit 1
fi

echo "\set ON_ERROR_STOP 1" > commandeTemp.sql

requete_create_by_client_user="SELECT session.pk as id,attributes,username as user,client.name as client
                                FROM session
                                LEFT JOIN \"user\" ON (\"user\".pk = session.user_id)
                                LEFT JOIN client ON (client.pk = session.client_id)
                                WHERE session.pk = created_by_id";

requete_modified_by_client_user="SELECT session.pk as id,attributes,username as user,client.name as client
                                FROM session
                                LEFT JOIN \"user\" ON (\"user\".pk = session.user_id)
                                LEFT JOIN client ON (client.pk = session.client_id)
                                WHERE session.pk = modified_by_id";


# MUNICIPALITY
requete_municipality="
	SELECT row_to_json(t) FROM (
		SELECT 
			id,
			insee,
			name,
			siren,
			alias,
			attributes,
			version,
			created_at,
			(SELECT row_to_json(c) FROM (${requete_create_by_client_user}) AS c) AS created_by,
			modified_at,
			(SELECT row_to_json(m) FROM (${requete_modified_by_client_user}) AS m) AS modified_by 
		FROM municipality where deleted_at is null) AS t"

requete_municipality=`echo ${requete_municipality}| sed "s/\n//"`

echo "\COPY (${requete_municipality})  TO '${outPath}/municipality.ndjson'" >> commandeTemp.sql

# PostCode
requete_postcode="
        SELECT row_to_json(t) FROM (
                SELECT
                        postcode.id,
                        code,
                        name,
			complement,
			mu.id as municipality,
                        alias,
                        attributes,
                        version,
                        created_at,
                        (SELECT row_to_json(c) FROM (${requete_create_by_client_user}) AS c) AS created_by,
                        modified_at,
                        (SELECT row_to_json(m) FROM (${requete_modified_by_client_user}) AS m) AS modified_by
                FROM postcode 
		LEFT JOIN (select pk,id from municipality) as mu ON (mu.pk = municipality_id )
		where deleted_at is null
		) AS t"

requete_postcode=`echo ${requete_postcode}| sed "s/\n//"`

echo "\COPY (${requete_postcode})  TO '${outPath}/postcode.ndjson'" >> commandeTemp.sql

# Groupe
requete_group="
        SELECT row_to_json(t) FROM (
                SELECT
                        \"group\".id,
                        fantoir,
			ign,
                        laposte,
                        name,
			kind,
			addressing,
			mu.id as municipality,
                        alias,
                        attributes,
                        version,
                        created_at,
                        (SELECT row_to_json(c) FROM (${requete_create_by_client_user}) AS c) AS created_by,
                        modified_at,
                        (SELECT row_to_json(m) FROM (${requete_modified_by_client_user}) AS m) AS modified_by
                FROM \"group\"
		LEFT JOIN (select pk,id from municipality) as mu ON (mu.pk = municipality_id )
		where deleted_at is null
		) AS t"

requete_group=`echo ${requete_group}| sed "s/\n//"`

echo "\COPY (${requete_group})  TO '${outPath}/group.ndjson'" >> commandeTemp.sql

# housenumber
requete_hn="
	SELECT row_to_json(t) FROM (
                SELECT
                        hn.id,
                        cia,
                        ign,
                        laposte,
                        number,
                        ordinal,
                        g.id as parent,
                        pc.id as postcode,
			array_agg as ancestors,
                        attributes,
                        version,
                        created_at,
                        (SELECT row_to_json(c) FROM (${requete_create_by_client_user}) AS c) AS created_by,
                        modified_at,
                        (SELECT row_to_json(m) FROM (${requete_modified_by_client_user}) AS m) AS modified_by
                FROM housenumber as hn
                LEFT JOIN (select pk,id from postcode) as pc ON (pc.pk = postcode_id )
                LEFT JOIN (select pk,id from \"group\") as g ON (g.pk = parent_id )
		LEFT JOIN 
			(SELECT housenumber_id,array_agg(\"group\".id)
                        FROM housenumber_group_through LEFT JOIN \"group\" ON (group_id = \"group\".pk) GROUP BY housenumber_id)
                        AS g2 ON (g2.housenumber_id = hn.pk)
		where deleted_at is null
                ) AS t"

requete_hn=`echo ${requete_hn}| sed "s/\n//"`

echo "\COPY (${requete_hn})  TO '${outPath}/housenumber.ndjson'" >> commandeTemp.sql

# position
requete_position="
        SELECT row_to_json(t) FROM (
                SELECT
                        position.id,
                        ign,
                        laposte,
                        positioning,
                        kind,
                        name,
			st_asgeojson(center)::json as center,
                        pos2.id as parent,
                        hn.id as housenumber,
                        attributes,
                        source,
			comment,
                        version,
                        created_at,
                        (SELECT row_to_json(c) FROM (${requete_create_by_client_user}) AS c) AS created_by,
                        modified_at,
                        (SELECT row_to_json(m) FROM (${requete_modified_by_client_user}) AS m) AS modified_by
                FROM position 
                LEFT JOIN (select pk,id from housenumber) as hn ON (hn.pk = housenumber_id )
                LEFT JOIN (select pk,id from position) as pos2 ON (pos2.pk = parent_id )
		where deleted_at is null
                ) AS t"

requete_position=`echo ${requete_position}| sed "s/\n//"`

echo "\COPY (${requete_position})  TO '${outPath}/position.ndjson'" >> commandeTemp.sql


psql -f commandeTemp.sql

if [ $? -ne 0 ]
then
   echo "Erreur lors de l export des jsons"
   exit 1
fi

#rm commandeTemp.sql

echo "FIN"

