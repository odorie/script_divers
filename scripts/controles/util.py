import const


def check_kind(kind):
    """
    Vérifie le type de contrôle passé en entrée. Renvoie une exception en cas de contrôle non autorisé
    :param kind:
    :return:
    """
    if kind not in const.PARAM_CONTROLES.keys():
        raise Exception('Mauvais kind : {}'.format(kind))


def check_kinds(kinds):
    """
    Vérifie la liste des types de contrôles passés en entrée. Renvoie une exception en cas de contrôle non autorisé
    :param kinds:
    :return:
    """
    for kind in kinds:
        check_kind(kind)


def get_level(kind):
    """
    Renvoie le niveau du contrôle (inco, alerte ...)
    :param kind:
    :return: level
    """
    controle = const.PARAM_CONTROLES.get(kind)
    if controle is None:
        raise Exception('Mauvais kind : {}'.format(kind))
    return controle.get("type")


def get_resource(kind):
    """
    Renvoie la resource du kind (position_pile => position)
    :param kind:
    :return: resource
    """
    splitted_kind = kind.split('_')
    resource_type = splitted_kind[0]
    if resource_type not in const.LIST_RESOURCES:
        raise Exception("resource unknown")
    return resource_type


def check_depts(depts):
    """
    Vérifie la liste des départements en entrée. Renvoie une exception en cas de département non autorisé
    :param depts:
    :return:
    """
    for dept in depts:
        if dept not in const.LIST_DEPTS:
            raise Exception('Mauvais département : {}'.format(dept))


# Renvoie le srid correspondant au département dept
def get_srid_proj(dept):
    if (dept == '971'):
        return '4559'
    if (dept == '972'):
        return '4559'
    if (dept == '973'):
        return '2972'
    if (dept == '974'):
        return '2975'
    if (dept == '975'):
        return '4467'
    if (dept == '976'):
        return '4471'
    if (dept == '977'):
        return '4559'
    if (dept == '978'):
        return '4559'
    return '2154'