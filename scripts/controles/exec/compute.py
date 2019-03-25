import sys
import os
sys.path.append(os.path.dirname(sys.path[0]))
import controle
import datetime
import argparse
import util
import const

parser = argparse.ArgumentParser()
parser.add_argument("--kinds", help="Kind à traiter séparés par une virgule. all pour tous",type=str, required=True)
parser.add_argument("--depts", help="Numéros des départements à traiter séparés par une virgule, fr pour lancer France enière",type=str, required=True)
args = parser.parse_args()

if args.kinds != "all":
    split_kinds = args.kinds.split(",")
    util.check_kinds(split_kinds)
else:
    split_kinds = list(const.LIST_KINDS.keys())

if args.depts != "fr":
    split_depts = args.depts.split(",")
    util.check_depts(split_depts)

# on vérifie que les contrôles uniquement lançable France entière ne sont pas lancés sur un département
for kind in split_kinds:
    param = const.PARAM_CONTROLES.get(kind)

    if (args.depts != "fr") and param.get("emprise") == "FR":
        raise Exception('Le contrôle {} ne peut pas être lancé sur un département'.format(kind))

print("========================================\n")
print("Debut des contrôles ({}) \n".format(str(datetime.datetime.now())))

for kind in split_kinds:
    print("==============\n")
    print('contrôle {}'.format(kind))

    param = const.PARAM_CONTROLES.get(kind)
    resource = util.get_resource(kind)

    ##################################################
    # Cas où on demande les contrôles France entière
    if (args.depts == "fr"):
        # on peut lancer le contrôle France entière
        if param.get("emprise") == "FR":
            print('contrôle {} France entière '.format(kind))
            exec('controle.{}.check_{}()'.format(resource, kind))
        # on ne peut pas lancer France entière : on découpe
        else:
            for dep in const.LIST_DEPTS:
                print("======\n")
                print('contrôle {} dept {}'.format(kind, dep))
                exec('controle.{}.check_{}({})'.format(resource, kind, dep))

    ######################################################
    # Cas où l'utilisateur a demandé un contrôle par département
    else:
        for dep in split_depts:
            print("======\n")
            print('contrôle {} dept {}'.format(kind, dep))
            exec('controle.{}.check_{}("{}")'.format(resource, kind, dep))

 
#controle.controle.check_pile()
#controle.controle.check_group_kind()


#controle.controle.check_housenumber_5000_9000()
#controle.controle.check_housenumber_number_null()
#controle.controle.check_housenumber_number_0()
#controle.controle.check_housenumber_number_format()
#controle.controle.check_housenumber_without_postcode()
#controle.controle.check_housenumber_ordinal_format()
#controle.controle.check_group_name_format()
#controle.controle.check_housenumber_same_ordinal()

#controle.controle.check_group_same_name()
#controle.controle.check_housenumber_missing_ordinal()




print("Fin des contrôles ({}) \n".format(str(datetime.datetime.now())))

