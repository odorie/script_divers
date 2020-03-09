#!/bin/sh
# But: produire les fichiers csv d'export pour toute la France
###################################################################################
# ARGUMENT :* $1 : repertoire dans lequel seront genres les fichiers d export 
# dans des dossiers export_json et export_csv
###################################################################################
# REMARQUE :
# - la base PostgreSQL, le port doivent être passés dans les variables d'environnement
#     PGDATABASE et si besoin PGUSER, PGHOST et PGPASSWORD
#############################################################################
exportPath=$1
currentDir=$(dirname "$0")
date=$2
if [ $# -lt 2 ]; then
        echo "Usage : export_csv_fr.sh <outPath> <date>"
        echo "Exemple : export_csv_fr.sh /home/ban/test 20190701"
        exit 1
fi
set -x
deps="01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 2A 2B 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 971 972 973 974 975 976"
for dep in ${deps}
do
	echo $dep
	$currentDir"/export_csv.sh" $exportPath $dep $date
	if [ $? -ne 0 ]
	then
   		echo "Erreur lors de l export du csv"
   		exit 1
	fi

done

echo "FIN"
