import json
import csv
import sys
from pyproj import Proj, transform


def export(
    chemin, dep, doc_municipality, doc_postcode, doc_group, doc_housenumber
):
    municipalities = {}
    postcodes = {}
    groups = {}
    housenumbers = {}
    exportPath = '{}/export_{}.csv'.format(chemin, dep)
    c = csv.writer(
                open(exportPath, 'w'),
                delimiter=',',
                lineterminator='\n'
    )
    c.writerow(['id', 'nom_voie', 'id_fantoir', 'numero', 'rep', 'code_insee',
                'code_post', 'alias', 'nom_ld', 'x', 'y', 'lon', 'lat',
                'nom_commune'])
    with open(chemin+'/'+doc_municipality, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['insee'].startswith(dep):
                municipalities[data['id']] = data
    print('{} municipalities'.format(len(municipalities)))
    with open(chemin+'/'+doc_postcode, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['municipality'] in municipalities.keys():
                postcodes[data['id']] = data
    print('{} postcodes'.format(len(postcodes)))
    with open(chemin+'/'+doc_group, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['municipality'] in municipalities.keys():
                groups[data['id']] = data
    print('{} groups'.format(len(groups)))
    hn_count = 0
    with open(chemin+'/'+doc_housenumber, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if 'number' in data.keys():
                if data['parent'] in groups.keys():
                    housenumbers.setdefault(data['parent'], []).append(data)
                    hn_count += 1
    print('{} housenumbers'.format(hn_count))

    epsg_code = getEPSGCode(dep)

    for group in groups.values():
        group_hns = housenumbers.get(group['id'], [])
        municipality = municipalities.get(group['municipality'], None)
        for housenumber in group_hns:
            position = findPosition(housenumber)
            ancestors = findAncestors(housenumber, groups)
            postcode = postcodes.get(housenumber['postcode'], None)

            writeNewLine(c, housenumber, group, ancestors, municipality, postcode, position, epsg_code)


def writeNewLine(writer, housenumber, group, ancestors, municipality, postcode, position, epsg_code):
    """ecrit une nouvelle ligne dans le fichier d export csv"""
    groupResult = compulseGroups(group, ancestors)
    if position is None:
        lonlat = ('', '')
    else:
        lonlat = (
            position["center"]["coordinates"][0],
            position["center"]["coordinates"][1])
    positionXY = convertPosition(position, epsg_code)

    writer.writerow([housenumber['id'],
                    groupResult[0],
                    group['fantoir'],
                    housenumber['number'],
                    housenumber['ordinal'],
                    municipality['insee'] if municipality is not None else '',
                    postcode['code'] if postcode is not None else '',
                    group['alias'],
                    groupResult[1],
                    positionXY[0],
                    positionXY[1],
                    lonlat[0],
                    lonlat[1],
                    municipality['name'] if municipality is not None else ''])


def convertPosition(position, code):
    """
        pour une position donnee retourne les coordonnees projetees
        selon la projection native
        @return (x,y)
    """
    positionXY = ('', '')
    if position is None:
        return positionXY
    inProj = Proj(init='epsg:4326')
    outProj = Proj(init=code)
    positionXY = transform(
                            inProj,
                            outProj,
                            position["center"]["coordinates"][0],
                            position["center"]["coordinates"][1])
    return positionXY


def getEPSGCode(dep):
    """renvoie le code epsg correspondant pour un departement donne"""
    codes = {
        '971': '4559',
        '972': '4559',
        '973': '2972',
        '974': '2975',
        '975': '4467',
        '976': '4471'
    }
    code = codes.get(dep, '2154')
    return 'epsg:{}'.format(code)


def compulseGroups(group, ancestors):
    """@return (nom_voie, nom_ld)"""
    result = ['', '']

    if group["kind"] == 'way':
        ancestor = findBestAncestor(ancestors, 'area')
        result[0] = group["name"]
        if ancestor is not None:
            result[1] = ancestor["name"]
    elif group["kind"] == 'area':
        ancestor = findBestAncestor(ancestors, 'way')
        result[1] = group["name"]
        if ancestor is None:
            result[0] = group["name"]
        else:
            result[0] = ancestor["name"]
    return result


def findBestAncestor(ancestors, type):
    """
        selectionne l ancestor le plus recent d un type donne
        parmi un tableau d ancestors
    """
    best_ancestor = None
    for ancestor in ancestors:
        if ancestor["kind"] == type and best_ancestor is None:
            best_ancestor = ancestor
        elif ancestor["kind"] == type and ancestor['modified_at'] > best_ancestor['modified_at']:
            best_ancestor = ancestor
    return best_ancestor


def findPosition(housenumber):
    """
        selectionne la position la plus recente
        pour le meilleur kind disponible
    """
    positions = housenumber['positions']
    kinds = [
            "entrance", "building", "staircase", "unit",
            "parcel", "segment", "utility", "area", "postal", "unknown"]
    ids = {}
    bestPosition = None
    for position in positions:
        ids.setdefault(position['kind'], []).append(position)
    for kind in kinds:
        if kind in ids.keys():
            bestPosition = ids[kind][0]
            for position in ids[kind]:
                if position['modified_at'] > bestPosition['modified_at']:
                    bestPosition = position
            break
    return bestPosition


def findAncestors(housenumber, groups):
    """renvoie le tableau d ancestors lie a un housenumber donne"""
    results = []
    anc_ids = housenumber["ancestors"]
    for anc_id in anc_ids:
        results.append(groups.get(anc_id))
    return results


if __name__ == "__main__":
    municipalityFile = sys.argv[3] if len(sys.argv) > 3 else "municipality.ndjson"
    postcodeFile = sys.argv[4] if len(sys.argv) > 4 else "postcode.ndjson"
    groupFile = sys.argv[5] if len(sys.argv) > 5 else "group.ndjson"
    housenumberFile = sys.argv[6] if len(sys.argv) > 6 else "housenumber.ndjson"

    export(sys.argv[1], sys.argv[2], municipalityFile, postcodeFile, groupFile, housenumberFile)
