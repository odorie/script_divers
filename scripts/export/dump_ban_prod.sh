#!/bin/sh
# But : sauvegarder la ban de prod
################################################################################
# ARGUMENT :
# - le repertoire dans lequel sont sauvegardés les dumps
################################################################################
# ENTREE :
##############################################################################
# SORTIE :
# - le fichier de dump ban_<date>.dump dans le repertoire /var/ban/dump
# - dans le reperttoire des sauvegardes, on fait le menage des dumps
#    pour conserver :
#       - les dumps de la semaine en cours
#       - un dump par semaine (celui du vendredi) au cours du dernier mois
#       - un dump par mois au delà (le plus ancien de chaque mois)
#############################################################################
# # REMARQUE :
# - les variables d'environnement suivante doivent exister :
#      - passworBanApp = mot de passe du compte ban sur la machine vecteurIDC-banData
# - le repertoire de sauvegarde doit exister
#############################################################################
if [ $# -ne 1 ]; then
        echo "Usage : dump_ban_prod.sh <repertoire de sauvegarde>"
	echo "Exemple : dump_ban_prod.sh /home/ban/data/ban_prod/dump"
        exit 1
fi

#set -x

rep=$1

date=`date +"%Y%m%dT%H%M%S"`
echo "================================================================"
echo "Debut de la sauvegarde ${date}"

# Verification des variables d'environnement
if [ -z ${passworBanApp} ]
then
        echo "La variable d'environnement passworBanApp n'est pas définie"
        exit 1
fi

# Vérification de l'existence du répertoire de sauvegarde
if [ ! -d ${rep} ]
then
	echo "Le répertoire $rep n'existe pas"
	exit 1
fi

# Dump
echo "Dump ..."
pg_dump -h 10.13.1.2 -U ban -v -Fc -f ${rep}/ban_${date}.dump ban
if [ $? -ne 0 ]
then
   echo "Erreur lors du dump de la ban"
   exit 1
fi
touch ${rep}/ban_${date}.dump.complete

# Menage des dumps (cf entete du fichier)
echo "Menage"
current_year=`date "+%Y"`
current_month=`date "+%m"`
current_week=`date "+%U"`
sa_current_year_dump=0
sa_current_month_dump=0
sa_current_week_dump=0
# on les classes du plus ancient au plus recent
for fic in `ls ${rep}/ban*.dump | sort `
do
	keep=0
	base=$(basename $fic)
	date_dump_text=`echo ${base} | cut -c5-12`
	date_dump=`date -d ${date_dump_text} +"%Y%m%d"`
	current_year_dump=`date -d ${date_dump} +%Y`
	current_month_dump=`date -d ${date_dump} +%m`
        current_week_dump=`date -d ${date_dump} +%U`

	# si le dump a une annee differente du dump precedent, on le conserve
	if [ ${current_year_dump} -ne ${sa_current_year_dump} ]
	then
		keep=1
	else
		#les annees sont diffentes, on conserve le dump si le dump a un mois different du mois precedent
		if [ ${current_month_dump} -ne ${sa_current_month_dump} ]
		then
			keep=1
		else
			# mois et annnee sont identique par rapport au dump precedent
			
			# on conserve le dump si la semaine est differente de la semaine precedente et de la semaine courante
			# et si le mois du dump vaut le mois actuel et si l'année du dump est identique à l'année en cours
			if [ ${current_week_dump} -ne ${sa_current_week_dump} -a ${current_week_dump} -ne ${current_week} -a ${current_month_dump} -eq ${current_month} -a ${current_year_dump} -eq ${current_year} ]
			then
				keep=1
			fi

			# on conserve le dump si la semaine est identique à la semaine courante et si le mois du dump vaut le mois actuel
                        #et si l'année du dump est identique à l'année en cours
	                if [ ${current_week_dump} -eq ${current_week} -a ${current_month_dump} -eq ${current_month} -a ${current_year_dump} -eq ${current_year} ]
			then
	                        keep=1
                        fi

		fi

	fi

	if [ ${keep} -ne 1 ]
	then
		rm ${fic}
		rm ${fic}.complete
	fi

	sa_current_year_dump=${current_year_dump}
	sa_current_month_dump=${current_month_dump}
	sa_current_week_dump=${current_week_dump}


done


echo "OK : Fin de la sauvegarde"
echo "================================================================"

