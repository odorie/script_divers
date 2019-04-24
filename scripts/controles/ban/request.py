import requests
import urllib.parse
import ban


def get_anomaly_count(dep, kind):
    """
        Recuperation du nombre d'anomalies BAN par kind et dep
        :param dep: fr => france entière
        :rtype: string
        :param kind:
        :rtype: string
        :return: count
    """
    session = ban.api_session.ApiSession()
    url = session.config['BASE_URL'] + '/anomaly'
    headers = session.get_headers()
    payload = {
        'kind': kind,
        'count': '1'
    }
    if dep != "fr":
        payload["dep"] = dep
    request = requests.get(url, proxies=session.get_proxies(), headers=headers, params=payload)
    if request.status_code == 404 or request.status_code == 410:
        print("Pas d'anomalies de ce type sur le departement")
        exit()
    elif request.status_code != 200:
        raise Exception('Failed to get anomaly de kind {} et de dep {}'.format(kind, dep))
    return request.json()["total"]


def get_anomaly_by_bloc(dep,kind,limit,offset):
    """
        Recuperation par bloc des anomalies BAN pour un kind et un dep donné
        :param dep: fr => france entière
        :rtype: string
        :param kind:
        :rtype: string
        :param limit:
        :rtype: integer
        :param offset:
        :rtype: integer
        :return: liste d'anomalies
        :rtype: dict
    """
    session = ban.api_session.ApiSession()
    url = session.config['BASE_URL'] + '/anomaly'
    headers = session.get_headers()
    payload = {
        'kind': kind,
        'limit': limit,
        'offset': offset
    }
    if dep != "fr":
        payload["dep"] = dep
    request = requests.get(url, proxies=session.get_proxies(), headers=headers, params=payload)
    if request.status_code == 404 or request.status_code == 410:
        print("Pas d'anomalies de ce type sur le departement")
        exit()
    elif request.status_code != 200:
        raise Exception('Failed to get anomaly de kind {} et de dep {}'.format(kind, dep))
    return request.json()["collection"]


def post_anomaly(anomaly):
    """
        Création d'une anomalie BAN
        :param anomaly: anomalie à créer
        :rtype: dict
        :return: anomalie créée
        :rtype: dict
    """
    session = ban.api_session.ApiSession()
    url = session.config['BASE_URL'] + '/anomaly'
    headers = session.get_headers(has_body=True)
    attempt=0
    try:	
        request = requests.post(url, json=anomaly, proxies=session.get_proxies(), headers=headers)
        if request.status_code != 201:
            raise Exception('Failed to create anomaly. {}'.format(request.content))
        return request.json()
    except:
        attempt += 1
        if attempt > 3:
            raise Exception('Failed to post request {} '.format(request.content))	
        print("Error during request post, I will try again")
        sleep(5)
    raise Exception('Failed to create anomaly')


def delete_anomaly(anomaly_id):
    """
        Suppression d une anomalie BAN
        :param anomaly_id: identifiant de l'anomalie a supprimer
    """
    session = ban.api_session.ApiSession()
    url = session.config['BASE_URL'] + '/anomaly/{}'.format(urllib.parse.quote(anomaly_id))
    headers = session.get_headers()
    request = requests.delete(url, proxies=session.get_proxies(), headers=headers)
    if request.status_code != 204:
        raise Exception('Failed to delete anomaly {} : {}'.format(anomaly_id, request.content))
