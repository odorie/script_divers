import os
import const
import requests
import datetime
import configparser


class Borg(object):
    """Borg pattern provides singletone-like behavior sharing state between instances."""
    __shared_state = {
        'config': None,
        'token': None,
        'token_expiration_date': None
    }

    def __init__(self):
        self.__dict__ = self.__shared_state


class ApiSession(Borg):
    """
        Gestion des requetes vers l api BAN
    """
    def __init__(self):
        Borg.__init__(self)

        if self.config is None:
            config = configparser.ConfigParser()
            config_path = os.path.join(const.ROOT_DIR, 'config')
            config_path = os.path.join(config_path, 'config.ini')
            if not os.path.isfile(config_path):
                raise IOError('Le fichier de parametre {} est introuvable'.format(config_path))
            config.read(config_path)
            self.config = config['BAN_API']


    def get_token(self):
        """
            :return: token stocke dans l objet ou demande d un nouveau token si invalide
            :rtype: string
        """
        if self.is_available_token():
            return self.token
        url = self.config['BASE_URL'] + '/token'
        data = {
            'client_id': self.config['CLIENT_ID'],
            'client_secret': self.config['CLIENT_SECRET'],
            'email': self.config['MAIL'],
            'contributor_type': self.config['CONTRIBUTOR_TYPE'],
            'grant_type': 'client_credentials'
        }
        request = requests.post(url, proxies=self.get_proxies(), data=data)
        if request.status_code != 200:
            raise Exception('Failed to get token ban')
        response = request.json()
        self.token = response['token_type'] + ' ' + response['access_token']
        date_interval = datetime.timedelta(seconds=response['expires_in'])
        self.token_expiration_date = datetime.datetime.now() + date_interval
        return self.token


    def get_proxies(self):
        """
            Construction du parametre proxy d apres le fichier de conf
            :rtype: dict
        """
        proxies = {
            'http': self.config['PROXY'],
            'https': self.config['PROXY']
        }
        return proxies


    def get_headers(self, has_body=False):
        """
            :return: headers pour requete ban
            :rtype: dict
        """
        token = self.get_token()
        headers = {
            'Authorization': token
        }
        if has_body:
            headers['Content-Type'] = 'application/json'
            headers['accept'] = 'application/json'
        return headers


    def is_available_token(self):
        """
            :return: true si l objet possede un token valide false sinon
            :rtype: bool
        """
        if self.token is None or self.token_expiration_date is None:
            return False
        now = datetime.datetime.now()
        if self.token_expiration_date < now:
            return False
        return True
