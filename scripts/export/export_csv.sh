#!/bin/sh
# But : exporter la ban en csv format banv0
################################################################################
# ARGUMENT : $1 : repertoire dans lequel sera genere le fichier
# ARGUMENT : $2 : emprise de l export (deparmtement ou insee commune)
################################################################################
#  Les donnees doivent etre dans la base ban_init en local et avoir la structure provenant
# des csv IGN
#############################################################################
# REMARQUE :
# - la base PostgreSQL, le port doivent être passés dans les variables d'environnement
#     PGDATABASE et si besoin PGUSER, PGHOST et PGPASSWORD
#############################################################################
outPath=$1
municipality=$2
date=$3
if [ $# -lt 3 ]; then
        echo "Usage : export_csv.sh <outPath> <municipality> <date>"
        echo "Exemple : export_csv.sh /home/ban/test 90001 20190701"
        exit 1
fi

#set -x

rm -f ${outPath}/ban_${municipality}_*.csv
rm -f ${outPath}/group_id_ign_${municipality}_*.csv
rm -f ${outPath}/adresse_id_ign_${municipality}_*.csv

echo "Traitement de l'insee $municipality"

echo "\set ON_ERROR_STOP 1" > ${outPath}/commandeTemp.sql
echo "\\\timing " >> ${outPath}/commandeTemp.sql

echo "drop table if exists temp;" >> ${outPath}/commandeTemp.sql

requete="
select  pos.id as id_ban_position,
	hn.id as id_ban_adresse,
	hn.pk as hn_pk,
	(
	      	case
			when hn.cia like '%\_' then substr(hn.cia,1,char_length(hn.cia)-1) 
			else hn.cia
		end
	) as cia_temp, 
	g.id as id_ban_group,
	g.pk as g_pk,
	g.fantoir as id_fantoir,
	hn.number as numero,
        hn.ordinal as suffixe,
	g.name as nom_voie, 
	pt.code as code_postal,
	m.name as nom_commune,
	m.insee as code_insee, 
	group_secondaires.nom_complementaire,
	(
		case 
			when (m.insee='971' or m.insee='972') then st_x(st_transform(st_setsrid(pos.center, 4326), 4559))
			when (m.insee='973') then st_x(st_transform(st_setsrid(pos.center, 4326), 2972))
			when (m.insee='974') then st_x(st_transform(st_setsrid(pos.center, 4326), 2975))
			when (m.insee='975') then st_x(st_transform(st_setsrid(pos.center, 4326), 4467))
			when (m.insee='976') then st_x(st_transform(st_setsrid(pos.center, 4326), 4471))
			when (m.insee='977' or m.insee='978') then st_x(st_transform(st_setsrid(pos.center, 4326), 4559))
			else st_x(st_transform(st_setsrid(pos.center, 4326), 2154))
		end
	) as x, 
	(
		case 
			when (m.insee='971' or m.insee='972') then st_y(st_transform(st_setsrid(pos.center, 4326), 4559))
			when (m.insee='973') then st_y(st_transform(st_setsrid(pos.center, 4326), 2972))
			when (m.insee='974') then st_y(st_transform(st_setsrid(pos.center, 4326), 2975))
			when (m.insee='975') then st_y(st_transform(st_setsrid(pos.center, 4326), 4467))
			when (m.insee='976') then st_y(st_transform(st_setsrid(pos.center, 4326), 4471))
			when (m.insee='977' or m.insee='978') then st_y(st_transform(st_setsrid(pos.center, 4326), 4559))
			else st_y(st_transform(st_setsrid(pos.center, 4326), 2154))
		end
	) as y, 
	st_x(pos.center) as lon,
	st_y(pos.center) as lat,
	pos.kind as typ_loc,
	pos.source_kind as source,
	date(greatest(pos.modified_at,hn.modified_at,g.modified_at)) as date_der_maj, 
	rank() over (partition by pos.housenumber_id, pos.kind order by pos.modified_at DESC) 
from position as pos
left join housenumber as hn on pos.housenumber_id = hn.pk
left join \"group\" as g on hn.parent_id = g.pk 
left join ( 
	select hn_g_s.housenumber_id, string_agg(g.name,'|') as nom_complementaire from housenumber_group_through hn_g_s 
	left join \"group\" g on (g.pk = hn_g_s.group_id)
	left join municipality as m on g.municipality_id = m.pk
	where m.insee like '${municipality}%'
	group by hn_g_s.housenumber_id
) as group_secondaires on group_secondaires.housenumber_id = hn.pk
left join postcode as pt on hn.postcode_id = pt.pk
left join municipality as m on g.municipality_id = m.pk
where m.insee like '${municipality}%'
and hn.deleted_at is null
and hn.number is not null
order by m.insee, g.pk, hn.pk"

requete=`echo ${requete}| sed "s/\n//"`

echo "create table temp as select *, substring(cia_temp from 1 for 11) || lower(substring(cia_temp from 12 )) as cle_interop from (${requete}) as a where rank = 1;" >> ${outPath}/commandeTemp.sql

echo "\COPY (select id_ban_position,id_ban_adresse,cle_interop,id_ban_group,id_fantoir,numero,suffixe,nom_voie,code_postal,nom_commune,code_insee,nom_complementaire,x,y,lon,lat,typ_loc,source,date_der_maj from temp) TO '${outPath}/ban_${municipality}_${date}.csv' CSV HEADER DELIMITER ';'" >> ${outPath}/commandeTemp.sql

echo "drop table if exists temp_group;" >> ${outPath}/commandeTemp.sql
echo "create table temp_group as select id_ban_group,g_pk from temp group by id_ban_group,g_pk;" >> ${outPath}/commandeTemp.sql

echo "\COPY (select t.id_ban_group,g.ign from temp_group t left join \"group\" g on g.pk = t.g_pk where g.ign is not null) TO '${outPath}/group_id_ign_${municipality}_${date}.csv' CSV HEADER DELIMITER ';'" >> ${outPath}/commandeTemp.sql

echo "drop table if exists temp_hn;" >> ${outPath}/commandeTemp.sql
echo "create table temp_hn as select id_ban_adresse,hn_pk from temp group by id_ban_adresse,hn_pk;" >> ${outPath}/commandeTemp.sql

echo "\COPY (select t.id_ban_adresse,h.ign from temp_hn t left join housenumber h on h.pk = t.hn_pk where h.ign is not null) TO '${outPath}/adresse_id_ign_${municipality}_${date}.csv' CSV HEADER DELIMITER ';'" >> ${outPath}/commandeTemp.sql


psql -f ${outPath}/commandeTemp.sql

if [ $? -ne 0 ]
then
   echo "Erreur lors de l export du csv"
   exit 1
fi

rm ${outPath}/commandeTemp.sql

echo "FIN"
