# utils.py
import time

import requests
from requests.auth import HTTPBasicAuth
from typing import Optional, Dict, Any
import logging
from config import config, config_lock

def detect_shelly_type():
    try:
        response_pro = requests.get(f'http://{config["shelly_ip"]}/rpc/EM.GetStatus?id=0',
                                    headers={'Content-Type': 'application/json'})
        if response_pro.status_code == 200:
            logging.info("Shelly Pro 3 EM detected")
            return 'Pro 3 EM'

        response_3em = requests.get(f'http://{config["shelly_ip"]}/status',
                                    headers={'Content-Type': 'application/json'})
        if response_3em.status_code == 200:
            logging.info("Shelly 3 EM detected")
            return '3 EM'

        logging.error("Could not detect Shelly type")
    except requests.RequestException as e:
        logging.error(f'Error detecting Shelly type: {e}')
    return None

def fetch_dtu_data() -> Optional[Dict[str, Any]]:
    try:
        url = f'http://{config["dtu_ip"]}/api/livedata/status?inv={config["serial"]}'
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        inverter = data['inverters'][0]

        total_dc_power = sum(dc['Power']['v'] for dc in inverter['DC'].values())

        return {
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

def fetch_shelly_data() -> Optional[Dict[str, Any]]:
    shelly_ip = config.get("shelly_ip")
    if not shelly_ip:
        logging.error("Shelly IP is not configured")
        return None

    if config['shelly_type'] is None:
        config['shelly_type'] = detect_shelly_type()

    urls = {
        'Pro 3 EM': f'http://{shelly_ip}/rpc/EM.GetStatus?id=0',
        '3 EM': f'http://{shelly_ip}/status'
    }

    if config['shelly_type'] not in urls:
        logging.error("Invalid Shelly type detected")
        return None

    url = urls[config['shelly_type']]
    data = fetch_json_data(url)
    if data:
        if config['shelly_type'] == 'Pro 3 EM' and 'total_act_power' in data:
            logging.info(f"{config['shelly_type']} data fetched")
            return {'type': config['shelly_type'], 'total_act_power': data['total_act_power']}
        elif config['shelly_type'] == '3 EM' and 'total_power' in data:
            logging.info(f"{config['shelly_type']} data fetched")
            return {'type': config['shelly_type'], 'total_act_power': data['total_power']}

    logging.error("Could not fetch Shelly data")
    return None

def set_inverter_limit(setpoint: int) -> Optional[Dict[str, Any]]:
    try:
        url = f'http://{config["dtu_ip"]}/api/limit/config'
        data = f'data={{"serial":"{config["serial"]}", "limit_type":0, "limit_value":{setpoint}}}'
        response = requests.post(url, data=data, auth=HTTPBasicAuth(config['dtu_nutzer'], config['dtu_passwort']),
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        response.raise_for_status()
        response_data = response.json()
        logging.info(f'Configuration sent ({response_data["type"]})')
        return response_data
    except (requests.RequestException, KeyError) as e:
        logging.error(f'Error sending inverter configuration: {e}')
    return None

def auto_mode_loop():
    global reachable
    while True:
        with config_lock:
            if config['auto_mode']:
                logging.info("Auto mode is enabled")
                dtu_data = fetch_dtu_data()
                if dtu_data is None:
                    time.sleep(5)
                    continue

                shelly_data = fetch_shelly_data()
                if shelly_data is None:
                    time.sleep(5)
                    continue

                reachable = dtu_data['reachable']
                altes_limit = dtu_data['altes_limit']
                grid_sum = shelly_data['total_act_power']
                power = dtu_data['power']

                logging.info(
                    f'Bezug: {grid_sum:.1f} W, Produktion: {power:.1f} W, Verbrauch: {(grid_sum + power):.1f} W')

                if reachable:
                    setpoint = grid_sum + altes_limit - 5
                    setpoint = min(max(setpoint, config['minimum_wr']), config['maximum_wr'])
                    logging.info(f'Setpoint calculated: {setpoint:.1f} W')

                    if setpoint != altes_limit:
                        logging.info(f'Setting inverter limit from {altes_limit:.1f} W to {setpoint:.1f} W...')
                        set_inverter_limit(setpoint)
            else:
                logging.info("Auto mode is disabled")
        time.sleep(5)
