# Programme d'export de la ban

## Dump PostgreSQL ##
Le shell dump_ban_prod.sh permet de faire un dump PostgreSQL classique de la ban entière.

L'entête du shell contient la description de celui-ci et son mode d'emploi.

## Export en json ## 
Le shell export_json.sh permet d'exporter la base PostgreSQL de la ban en json.

L'entête du shell contient la description de celui-ci et son mode d'emploi

## Export en csv sur un departement ou une commune ##
Le shell export_csv.sh permet d'exporter la base PostgresSQL de la ban en csv au format v0 sur un département ou une commune.

L'entête du shell contient la description de celui-ci et son mode d'emploi

## Export en csv depuis les fichiers json ##
Le script export_json_to_csv.py permet de générer les exports en csv de la ban au format v0.

### Fonctionnement du script
Ce script fonctionne à partir de l'export en json.
Il nécessite Python 3.x + le package pyproj.

Il prend en entrée les arguments suivants :

- arg1: chemin repertoire pour export et fichiers a traiter
- arg2: departement a traiter
- arg3: nom du fichier des municipality. Argument facultatif. Par défaut le fichier doit être municipality.ndjson. 
- arg4: nom du fichier des postcode. Argument facultatif. Par défaut le fichier doit être postcode.ndjson.
- arg5: nom du fichier des group. Argument facultatif. Par défaut le fichier doit être group.ndjson.
- arg6: nom du fichier des housenumber. Argument facultatif. Par défaut le fichier doit être housenumber.ndjson.

Exemple :  python export_ban_v0.py ~/data/ban_prod/export_json 33

En sortie, le fichier csv est généré à l'emplacement des fichiers json. 

Le fichier généré au format ban v0 odbl (sans le champ nom_afnor).

### Remarques sur le traitement effectué pour l export format v0###
Le fichier généré au format ban v0 odbl (sans le champ nom_afnor).

Pour la géometrie projetée, la projection native est utilisée (Lambert93 pour France métropolitaine...)

En cas de positions multiples sur un housenumber, le script exporte une seule position en utilisant l'ordre de priorité suivant sur le champ kind:
"entrance", "building", "staircase", "unit", "parcel", "segment", "utility", "area", "postal", "unknown"
Si plusieurs positions ont le même kind retenu, le programme retient la position la plus récente (champ modified_at)

Pour le remplissage de nom_voie/lieu dit, le programme se base sur le type du groupe.
On complète les noms avec les ancestors. Si deux ancestors de même type on prend le plus récent
S'il reste vide, on remplit le nom de voie avec le nom du lieu dit
