#!/bin/sh
# But : sauvegarder la ban de prod
if [ $# -ne 0 ]; then
        echo "Usage : dump_ban_prod.sh "
        exit 1
fi

set -x

rep=/var/ban/dump

date=`date +"%Y%m%dT%H%M%S"`
echo "================================================================"
echo "debut de la sauvegarde ${date}"

#####################################################
pg_dump -h 10.13.1.2 -U ban -t municipality -v -Fc -f ${rep}/ban_${date}.dump
if [ $? -ne 0 ]
then
   echo "Erreur lors du dump de la ban"
   exit 1
fi


echo "OK : Fin de la sauvegarde"
echo "================================================================"

