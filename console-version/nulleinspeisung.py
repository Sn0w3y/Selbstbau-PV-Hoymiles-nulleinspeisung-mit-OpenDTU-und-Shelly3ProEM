import requests
import time
import sys
import logging
from requests.auth import HTTPBasicAuth

# Konfigurationseinstellungen
config = {
    'serial': '116494406970',
    'maximum_wr': 1600,
    'minimum_wr': 200,
    'dtu_ip': '192.168.17.225',
    'dtu_nutzer': 'admin',
    'dtu_passwort': 'openDTU42',
    'shelly_ip': '192.168.17.230',
    'shelly_type': None  # Wird automatisch erkannt
}

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def detect_shelly_type():
    try:
        # Versuche, die Shelly Pro 3 EM API zu erreichen
        url_pro = f'http://{config["shelly_ip"]}/rpc/EM.GetStatus?id=0'
        response_pro = requests.get(url_pro, headers={'Content-Type': 'application/json'})
        if response_pro.status_code == 200:
            logging.info("Shelly Pro 3 EM erkannt")
            return 'Pro 3 EM'

        # Falls oben nicht erfolgreich, versuche die Shelly 3 EM API zu erreichen
        url_3em = f'http://{config["shelly_ip"]}/status'
        response_3em = requests.get(url_3em, headers={'Content-Type': 'application/json'})
        if response_3em.status_code == 200:
            logging.info("Shelly 3 EM erkannt")
            return '3 EM'

        logging.error("Konnte den Shelly-Typ nicht erkennen")
        return None
    except Exception as e:
        logging.error(f'Fehler beim Erkennen des Shelly-Typs: {e}')
        return None


def fetch_dtu_data():
    try:
        url = f'http://{config["dtu_ip"]}/api/livedata/status?inv={config["serial"]}'
        response = requests.get(url).json()
        inverter = response['inverters'][0]
        return {
            'reachable': inverter['reachable'],
            'producing': int(inverter['producing']),
            'altes_limit': int(inverter['limit_absolute']),
            'power_dc': inverter['DC']['0']['Power']['v'],
            'power': inverter['AC']['0']['Power']['v']
        }
    except Exception as e:
        logging.error(f'Fehler beim Abrufen der DTU-Daten: {e}')
        return None


def fetch_shelly_data():
    try:
        if config['shelly_type'] == 'Pro 3 EM':
            url = f'http://{config["shelly_ip"]}/rpc/EM.GetStatus?id=0'
            response = requests.get(url, headers={'Content-Type': 'application/json'}).json()
            return response['total_act_power']
        else:
            url = f'http://{config["shelly_ip"]}/status'
            response = requests.get(url, headers={'Content-Type': 'application/json'}).json()
            return response['total_power']
    except Exception as e:
        logging.error(f'Fehler beim Abrufen der Shelly-Daten: {e}')
        return None


def set_inverter_limit(setpoint):
    try:
        url = f'http://{config["dtu_ip"]}/api/limit/config'
        data = f'data={{"serial":"{config["serial"]}", "limit_type":0, "limit_value":{setpoint}}}'
        response = requests.post(url, data=data, auth=HTTPBasicAuth(config['dtu_nutzer'], config['dtu_passwort']),
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        response_data = response.json()
        logging.info(f'Konfiguration gesendet ({response_data["type"]})')
    except Exception as e:
        logging.error(f'Fehler beim Senden der Inverter-Konfiguration: {e}')


# Erkennung des Shelly-Typs
config['shelly_type'] = detect_shelly_type()
if config['shelly_type'] is None:
    sys.exit("Fehler: Konnte den Shelly-Typ nicht erkennen")

while True:
    dtu_data = fetch_dtu_data()
    if dtu_data is None:
        continue

    shelly_data = fetch_shelly_data()
    if shelly_data is None:
        continue

    reachable = dtu_data['reachable']
    producing = dtu_data['producing']
    altes_limit = dtu_data['altes_limit']
    power = dtu_data['power']

    grid_sum = shelly_data

    logging.info(f'Bezug: {grid_sum:.1f} W, Produktion: {power:.1f} W, Verbrauch: {(grid_sum + power):.1f} W')

    if reachable:
        setpoint = grid_sum + altes_limit - 5

        if setpoint > config['maximum_wr']:
            setpoint = config['maximum_wr']
            logging.info(f'Setpoint auf Maximum: {config["maximum_wr"]} W')
        elif setpoint < config['minimum_wr']:
            setpoint = config['minimum_wr']
            logging.info(f'Setpoint auf Minimum: {config["minimum_wr"]} W')
        else:
            logging.info(f'Setpoint berechnet: {grid_sum:.1f} W + {altes_limit:.1f} W - 5 W = {setpoint:.1f} W')

        if setpoint != altes_limit:
            logging.info(f'Setze Inverterlimit von {altes_limit:.1f} W auf {setpoint:.1f} W... ')
            set_inverter_limit(setpoint)

    sys.stdout.flush()
    time.sleep(5)