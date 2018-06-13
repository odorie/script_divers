import json
import sys
import utils
import progressbar


def export(
    chemin, dep, doc_municipality, doc_postcode, doc_group, doc_housenumber, doc_position
):
    '''
    Usage : export <chemin json initial> <departement>
    Exemple : export . 01
    Remarque : le json ban v0 est genere a l'emplacement des json
    '''
    municipalities = {}
    mun_post = {}
    postcodes = {}
    groups = {}
    housenumbers = {}
    housenumbers_id = {}
    positions = {}
    exportPath = '{}/ban_addok_{}.json'.format(chemin, dep)

    with open(chemin+'/'+doc_municipality, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            municipalities[data['id']] = data
    print('{} municipalities'.format(len(municipalities)))

    with open(chemin+'/'+doc_postcode, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['municipality'] in municipalities.keys():
                postcodes[data['id']] = data
                mun_post[data['municipality']]=data['id']
    print('{} postcodes'.format(len(postcodes)))

    with open(chemin+'/'+doc_group, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['municipality'] in municipalities.keys():
                groups[data['id']] = data
    print('{} groups'.format(len(groups)))

    housenumberNb = 0
    with open(chemin+'/'+doc_housenumber, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['parent'] in groups.keys():
                housenumbers.setdefault(data['parent'], []).append(data)
                housenumbers_id[data['id']] = None
                housenumberNb += 1
    print('{} housenumbers'.format(housenumberNb))

    positionNb = 0
    with open(chemin+'/'+doc_position, 'r') as document:
        for ligne in document:
            data = json.loads(ligne)
            if data['housenumber'] in housenumbers_id.keys():
                positionNb += 1
                positions.setdefault(data['housenumber'], []).append(data)
    print('{} positions'.format(positionNb))
    print('{} positions regroupees par hn'.format(len(positions)))

    with open(exportPath, 'w') as result_file:
        # creation des documents associes aux municipalities
        munCount = 0
        munBar = progressbar.ProgressBar(
            widgets=[progressbar.FormatLabel("municipality processed")],
            maxval=len(municipalities)
        )
        munBar.start()
        for municipality in municipalities.values():
            munCount += 1
            munBar.update(munCount)
            json.dump(getAddokMunicipalityDoc(municipality), result_file)
            result_file.write("\n")
        munBar.finish()

        # creation des documents associes aux groups
        count = 0
        bar = progressbar.ProgressBar(
            widgets=[progressbar.FormatLabel("group processed")],
            maxval=len(groups)
        )
        bar.start()
        for group in groups.values():
            count += 1
            bar.update(count)
            group_hns = housenumbers.get(group['id'], [])
            municipality = municipalities.get(group['municipality'], None)
            hn_by_postcode = {}

            for housenumber in group_hns:
                position = utils.findPosition(housenumber, positions)
                if position is None:
                    continue
                housenumber["lon"] = position["center"]["coordinates"][0]
                housenumber["lat"] = position["center"]["coordinates"][1]
                postcode = postcodes.get(housenumber['postcode'], '')
                if postcode=='':
                    postcode_id = mun_post.get(group['municipality'], '')
                    postcode = postcodes.get(postcode_id, '')

                if postcode!='':
                    hn_by_postcode.setdefault(postcode['name'], []).append(housenumber)
           

            for postcode in hn_by_postcode:
                doc = getAddokGroupDoc(
                    group,
                    hn_by_postcode[postcode],
                    municipality,
                    postcode)
                json.dump(doc, result_file)
                result_file.write("\n")

        bar.finish()


def getAddokMunicipalityDoc(municipality):
    # genere le document addok correspondant a la municipality
    # les valeurs lon lat sont laissees vides
    doc = {
        "id": municipality["id"],
        "type": "city",
        "name": municipality["name"],
        "importance": 0.5,
        "lon": 2.0,
        "lat": 47.0
    }

    return doc


def getAddokGroupDoc(group, housenumbers, municipality, postcode):
    # genere le document addok correspondant au group
    # param dict group
    # param array housenumbers
    # param dict municipality
    # param integer postcode
    # chaque housenumber possede un lon lat
    hndoc = {}
    for hn in housenumbers:
        hndoc[hn["number"]] = {
            "lon": hn["lon"],
            "lat": hn["lat"]
        }

    doc = {
        "id": group["id"],
        "type": group["kind"],
        "name": group["name"],
        "postcode": postcode,
        "lon": 2.0,
        "lat": 47.0,
        "city": municipality["name"],
        "importance": 0.5,  # tous les documents ont la meme importance
        "housenumbers": hndoc
    }

    return doc


if __name__ == "__main__":
    municipalityFile = sys.argv[3] if len(sys.argv) > 3 else sys.argv[2]+"_municipality.ndjson"
    postcodeFile = sys.argv[4] if len(sys.argv) > 4 else sys.argv[2]+"_postcode.ndjson"
    groupFile = sys.argv[5] if len(sys.argv) > 5 else sys.argv[2]+"_group.ndjson"
    housenumberFile = sys.argv[6] if len(sys.argv) > 6 else sys.argv[2]+"_housenumber.ndjson"
    positionFile = sys.argv[7] if len(sys.argv) > 7 else sys.argv[2]+"_position.ndjson"
    comment = '''
    Usage : export <chemin json initial> <departement>
    Exemple : export . 01
    Remarque : le json ban v0 est genere a l'emplacement des json
    '''
    try:
        chemin = sys.argv[1]
        dep = sys.argv[2]
    except:
        print (comment)
        sys.exit()
    export(chemin, dep, municipalityFile, postcodeFile, groupFile, housenumberFile, positionFile)
