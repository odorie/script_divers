import sys
import os
sys.path.append(os.path.dirname(sys.path[0]))
import controle
import datetime
import argparse
import const


def check_kinds(kinds):
    """
    Vérifie la liste des types de contrôles passés en entrée. Renvoie une exception en cas de contrôle non autorisé
    :param kinds:
    :return:
    """
    for kind in kinds:
        if kind not in const.LIST_KINDS:
            raise Exception('Mauvais kind : {}'.format(kind))


def check_depts(depts):
    """
    Vérifie la liste des départements en entrée. Renvoie une exception en cas de département non autorisé
    :param depts:
    :return:
    """
    for dept in depts:
        if dept not in const.LIST_DEPTS:
            raise Exception('Mauvais département : {}'.format(dept))


parser = argparse.ArgumentParser()
parser.add_argument("--kinds", help="Kind à traiter séparés par une virgule. All pour tous",type=str)
parser.add_argument("--depts", help="Numéros des départements à traiter séparés par une virgule, all pour tous",type=str)
args = parser.parse_args()
if args.kinds:
    split_kinds = args.kinds.split(",")
    check_kinds(split_kinds)
else:
    split_kinds = const.LIST_KINDS
if args.depts:
    split_depts = args.depts.split(",")
    check_depts(split_depts)
else:
    split_depts = const.LIST_DEPTS

print("========================================\n")
print("Debut des contrôles ({}) \n".format(str(datetime.datetime.now())))

for kind in split_kinds:
    print("==============\n")
    print('contrôle {}'.format(kind))

    for dep in split_depts:
        print("======\n")
        print('contrôle {} dept {}'.format(kind, dep))
        exec('controle.controle.check_{}({})'.format(kind, dep))

#controle.controle.check_housenumber_5000_9000()
#controle.controle.check_housenumber_number_null()
#controle.controle.check_housenumber_number_0()
#controle.controle.check_housenumber_number_format()
#controle.controle.check_housenumber_without_postcode()
#controle.controle.check_housenumber_ordinal_format()
#controle.controle.check_group_name_format()
#controle.controle.check_housenumber_same_ordinal()
#controle.controle.check_group_kind()
#controle.controle.check_group_same_name()
#controle.controle.check_housenumber_missing_ordinal()
#controle.controle.check_pile()



print("Fin des contrôles ({}) \n".format(str(datetime.datetime.now())))

