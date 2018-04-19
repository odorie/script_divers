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
if [ $# -lt 1 ]; then
        echo "Usage : export_csv.sh <outPath> <municipality>"
        echo "Exemple : export_csv.sh /home/ban/test 90001"
        exit 1
fi

#set -x
echo "Traitement de l'insee $municipality"

echo "\set ON_ERROR_STOP 1" > ${outPath}/commandeTemp.sql

requete="
select hn.id as id, 
	(
		case 
			when g.kind='way' then g.name
			when g.kind='area' and anc_way.name <> '' then anc_way.name
			when g.kind='area' and anc_area.name <> '' then anc_area.name
			else g.name
		end
	) as nom_voie, 
	g.fantoir as id_fantoir, 
	g.id as id_voie,
	hn.number as numero, 
	hn.ordinal as rep, 
	m.insee as code_insee, 
	pt.code as code_postal, 
	g.alias as alias, 
	(
		case
			when g.kind='area' then g.name
			else anc_area.name
		end
	) as nom_ld, 
	pt.name as libelle_acheminement,
	(
		case 
			when (m.insee='971' or m.insee='972') then st_x(st_transform(st_setsrid(pos.center, 4326), 4559))
			when (m.insee='973') then st_x(st_transform(st_setsrid(pos.center, 4326), 2972))
			when (m.insee='974') then st_x(st_transform(st_setsrid(pos.center, 4326), 2975))
			when (m.insee='975') then st_x(st_transform(st_setsrid(pos.center, 4326), 4467))
			when (m.insee='976') then st_x(st_transform(st_setsrid(pos.center, 4326), 4471))
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
			else st_y(st_transform(st_setsrid(pos.center, 4326), 2154))
		end
	) as y, 
	st_x(pos.center) as lon,
	st_y(pos.center) as lat, 
	m.name as nom_commune
from housenumber as hn
left join
(
	select distinct on (p.housenumber_id)
	p.housenumber_id, 
	p.center,
	p.kind
	from position as p
	left join housenumber as h on p.housenumber_id=h.pk
	left join postcode as pt on h.postcode_id=pt.pk
	left join municipality as mun on pt.municipality_id = mun.pk
	where mun.insee like '${municipality}%' 
	order by p.housenumber_id, array_position(ARRAY['entrance', 'building', 'staircase', 'unit', 'parcel', 'segment', 'utility', 'area', 'postal', 'unknow'], p.kind::text) ASC, p.modified_at DESC
) as pos on pos.housenumber_id=hn.pk
left join \"group\" as g on hn.parent_id = g.pk 
left join
(
	select distinct on (hng.housenumber_id)
	hng.housenumber_id,
	anc.name
	from \"group\" as anc
	left join housenumber_group_through as hng
	on anc.pk = hng.group_id
	left join municipality as mun2
	on anc.municipality_id = mun2.pk
	where anc.kind = 'way'
	and mun2.insee like '${municipality}%'
	order by hng.housenumber_id, anc.modified_at DESC
) as anc_way on hn.pk = anc_way.housenumber_id
left join
(
	select distinct on (hng.housenumber_id)
	hng.housenumber_id,
	anc.name
	from \"group\" as anc
	left join housenumber_group_through as hng
	on anc.pk = hng.group_id
	left join municipality as mun2
	on anc.municipality_id = mun2.pk
	where anc.kind = 'area'
	and mun2.insee like '${municipality}%'
	order by hng.housenumber_id, anc.modified_at DESC
) as anc_area on hn.pk = anc_area.housenumber_id
left join postcode as pt on hn.postcode_id = pt.pk  
left join municipality as m on pt.municipality_id = m.pk
where m.insee like '${municipality}%'
and hn.deleted_at is null
and hn.number is not null"

requete=`echo ${requete}| sed "s/\n//"`

echo "\COPY (${requete}) TO '${outPath}/${municipality}_ban_v0.csv' CSV HEADER" >> ${outPath}/commandeTemp.sql

psql -f ${outPath}/commandeTemp.sql

if [ $? -ne 0 ]
then
   echo "Erreur lors de l export du csv"
   exit 1
fi

rm ${outPath}/commandeTemp.sql

echo "FIN"
