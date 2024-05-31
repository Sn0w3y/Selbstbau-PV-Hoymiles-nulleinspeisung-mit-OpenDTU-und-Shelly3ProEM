import json
import time
import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, Dict, Any
import logging
from config import config, config_lock

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_reachable_status():
    global reachable
    return reachable

def load_user_config():
    with open('user_config.json', 'r') as f:
        return json.load(f)

def get_auto_mode():
    with config_lock:
        return config.get('auto_mode', False)

def get_user_config():
    return load_user_config()

def detect_shelly_type(shelly_ip):
    try:
        response_pro = requests.get(f'http://{shelly_ip}/rpc/EM.GetStatus?id=0',
                                    headers={'Content-Type': 'application/json'})
        if response_pro.status_code == 200:
            logging.info("Shelly Pro 3 EM detected")
            return 'Pro 3 EM'

        response_3em = requests.get(f'http://{shelly_ip}/status',
                                    headers={'Content-Type': 'application/json'})
        if response_3em.status_code == 200:
            logging.info("Shelly 3 EM detected")
            return '3 EM'

        logging.error("Could not detect Shelly type")
    except requests.RequestException as e:
        logging.error(f'Error detecting Shelly type: {e}')
    return None


def fetch_dtu_data(dtu_ip, dtu_nutzer, dtu_passwort, serial) -> Optional[Dict[str, Any]]:
    try:
        url = f'http://{dtu_ip}/api/livedata/status?inv={serial}'
        response = requests.get(url, auth=HTTPBasicAuth(dtu_nutzer, dtu_passwort))
        response.raise_for_status()
        data = response.json()
        inverter = data['inverters'][0]

        total_dc_power = sum(dc['Power']['v'] for dc in inverter['DC'].values())

        return {
            'name': inverter['name'],
            'serial': inverter['serial'],
            'reachable': inverter['reachable'],
            'producing': int(inverter['producing']),
            'altes_limit': int(inverter['limit_absolute']),
            'power_dc': total_dc_power,
            'power': inverter['AC']['0']['Power']['v']
        }
    except (requests.RequestException, KeyError) as e:
        logging.error(f'Error fetching DTU data: {e}')
    return None


def fetch_json_data(url: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(url, headers={'Content-Type': 'application/json'})
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f'Error fetching data from {url}: {e}')
    return None


def fetch_shelly_data(shelly_ip, shelly_type) -> Optional[Dict[str, Any]]:
    if not shelly_ip:
        logging.error("Shelly IP is not configured")
        return None

    if shelly_type is None:
        shelly_type = detect_shelly_type(shelly_ip)

    urls = {
        'Pro 3 EM': f'http://{shelly_ip}/rpc/EM.GetStatus?id=0',
        '3 EM': f'http://{shelly_ip}/status'
    }

    if shelly_type not in urls:
        logging.error("Invalid Shelly type detected")
        return None

    url = urls[shelly_type]
    data = fetch_json_data(url)
    if data:
        if shelly_type == 'Pro 3 EM' and 'total_act_power' in data:
            logging.info(f"{shelly_type} data fetched")
            return {'type': shelly_type, 'total_act_power': data['total_act_power']}
        elif shelly_type == '3 EM' and 'total_power' in data:
            logging.info(f"{shelly_type} data fetched")
            return {'type': shelly_type, 'total_act_power': data['total_power']}

    logging.error("Could not fetch Shelly data")
    return None


def set_inverter_limit(setpoint: int, dtu_ip: str, dtu_nutzer: str, dtu_passwort: str, serial: str) -> Optional[
    Dict[str, Any]]:
    try:
        url = f'http://{dtu_ip}/api/limit/config'
        data = f'data={{"serial":"{serial}", "limit_type":0, "limit_value":{setpoint}}}'
        response = requests.post(url, data=data, auth=HTTPBasicAuth(dtu_nutzer, dtu_passwort),
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        response.raise_for_status()
        response_data = response.json()
        logging.info(f'Configuration sent ({response_data["type"]})')
        return response_data
    except (requests.RequestException, KeyError) as e:
        logging.error(f'Error sending inverter configuration: {e}')
    return None


def get_inverters_data(inverters):
    total_production = 0
    total_capacity = 0
    inverters_data = []
    for inverter in inverters:
        dtu_data = fetch_dtu_data(inverter['dtu_ip'], inverter['dtu_nutzer'], inverter['dtu_passwort'], inverter['serial'])
        if dtu_data is None or not dtu_data['reachable']:
            logging.warning(f"Inverter {inverter['serial']} not reachable")
            continue
        total_production += dtu_data['power']
        total_capacity += int(inverter['maximum_wr'])
        inverters_data.append({'dtu_data': dtu_data, 'inverter': inverter})
    return total_production, total_capacity, inverters_data

def adjust_inverters(inverters_data, power_difference, total_capacity):
    for data in inverters_data:
        dtu_data = data['dtu_data']
        inverter = data['inverter']
        capacity_share = int(inverter['maximum_wr']) / total_capacity
        adjustment = capacity_share * power_difference
        setpoint = dtu_data['altes_limit'] + adjustment
        setpoint = min(max(setpoint, int(inverter['minimum_wr'])), int(inverter['maximum_wr']))
        if setpoint != dtu_data['altes_limit']:
            logging.info(f'Inverter {inverter["serial"]}: Adjusting limit to {setpoint:.1f} W')
            set_inverter_limit(setpoint, inverter['dtu_ip'], inverter['dtu_nutzer'], inverter['dtu_passwort'], inverter['serial'])
        else:
            logging.info(f'Inverter {inverter["serial"]}: Is old limit.')

def auto_mode_loop():
    while True:
        if get_auto_mode():
            logging.info("Auto mode is enabled")
            user_config = get_user_config()
            total_production, total_capacity, inverters_data = get_inverters_data(user_config['inverters'])

            if not inverters_data:
                logging.info("No reachable inverters found. Retrying...")
                time.sleep(1)
                continue

            shelly_data = fetch_shelly_data(user_config['shelly_ip'], user_config.get('shelly_type'))
            if shelly_data is None:
                logging.warning("Failed to fetch Shelly data. Retrying...")
                time.sleep(1)
                continue

            grid_sum = shelly_data['total_act_power']
            total_consumption = grid_sum + total_production
            logging.info(f'Gesamtverbrauch: {total_consumption:.1f} W')

            power_difference = grid_sum - total_production + 5
            logging.info(f'Power difference: {power_difference -5 :.1f} W')

            adjust_inverters(inverters_data, power_difference, total_capacity)
        else:
            logging.info("Auto mode is disabled")

        for _ in range(5):
            time.sleep(1)
            if not get_auto_mode():
                break