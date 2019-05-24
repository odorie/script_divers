import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

LIST_DEPTS = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','2A','2B','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37','38','39','40','41','42','43','44','45','46','47','48','49','50','51','52','53','54','55','56','57','58','59','60','61','62','63','64','65','66','67','68','69','70','71','72','73','74','75','76','77','78','79','80','81','82','83','84','85','86','87','88','89','90','91','92','93','94','95','971','972','973','974','975','976','977','978']

PARAM_CONTROLES = {
    'group_kind': {
        'emprise': 'FR',
        'type': 'incoherence'
    },
    'group_name_format': {
        'emprise': 'FR',
        'type': 'incoherence'
    },
    'group_same_name': {
        'emprise': 'FR',
        'type': 'alert'
    },
    'housenumber_number_0': {
        'emprise': 'FR',
        'type': 'alert'
    },
    'housenumber_5000_9000': {
        'emprise': 'FR',
        'type': 'alert'
    },
    'housenumber_missing_ordinal': {
        'emprise': 'FR',
        'type': 'incoherence'
    },
    'housenumber_number_format': {
        'emprise': 'FR',
        'type': 'alert'
    },
    'housenumber_number_null': {
        'emprise': 'FR',
        'type': 'alert'
    },
    'housenumber_ordinal_format': {
        'emprise': 'FR',
        'type': 'incoherence'
    },
    'housenumber_same_ordinal': {
        'emprise': 'FR',
        'type': 'incoherence'
    },
    'housenumber_without_postcode': {
        'emprise': 'FR',
        'type': 'incoherence'
    },
    'position_outside_municipality': {
        'emprise': 'DEP',
        'type': 'incoherence'
    },
    'position_pile':  {
        'emprise': 'DEP',
        'type': 'incoherence'
    }
}


LIST_RESOURCES = [
    "housenumber",
    "group",
    "position",
    "postcode",
    "municipality"
]