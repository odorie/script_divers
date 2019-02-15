import os
import psycopg2
import configparser
import const


def db_connect():

    config = configparser.ConfigParser()
    config_path = os.path.join(const.ROOT_DIR, 'config')
    config_path = os.path.join(config_path, 'config.ini')
    if not os.path.isfile(config_path):
        raise IOError('Le fichier de parametre {} est introuvable'.format(config_path))
    config.read(config_path)

    host = config['DEFAULT_DATABASE']['HOST']
    db_name = config['DEFAULT_DATABASE']['DB_NAME']
    port = config['DEFAULT_DATABASE']['PORT']
    user = config['DEFAULT_DATABASE']['USER']

    if not host or not db_name or not port or not user:
        raise ValueError('Missing connection parameter(s).')

    if os.environ.get('PGPASSWORD'):
        conn_string = 'host={} dbname={} port={} user={} password={}'.format(host, db_name, port, user, os.environ['PGPASSWORD'])
    else:
        conn_string = 'host={} dbname={} port={} user={}'.format(host, db_name, port, user)
    try:
        conn = psycopg2.connect(conn_string)
    except Exception as e:
        raise Exception('Impossible de se connecter à la base de données : ' + str(e))

    return conn

