import sys
import os
sys.path.append(os.path.dirname(sys.path[0]))
import controle
import datetime

print("========================================\n")
print("Debut des contrôles ({}) \n".format(str(datetime.datetime.now())))

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
controle.controle.check_pile()

print("Fin des contrôles ({}) \n".format(str(datetime.datetime.now())))

