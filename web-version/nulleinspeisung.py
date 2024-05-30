from flask import Flask, render_template, redirect, url_for, jsonify, request
import threading
import time
from requests.auth import HTTPBasicAuth
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField
from wtforms.validators import DataRequired
import requests
import logging
from typing import Optional, Dict, Any

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jsfkhdfkjhdkhsijwd82'

# Configuration settings
config = {
    'serial': '116494406970',
    'maximum_wr': 1600,
    'minimum_wr': 200,
    'dtu_ip': '192.168.17.225',
    'dtu_nutzer': 'admin',
    'dtu_passwort': 'openDTU42',
    'shelly_ip': '192.168.17.230',
    'shelly_type': None,
    'auto_mode': True,
    'manual_limit': None
}

reachable = None

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ConfigForm(FlaskForm):
    serial = StringField('Seriennummer:', validators=[DataRequired()])
    maximum_wr = IntegerField('WR max. Leistung:', validators=[DataRequired()])
    minimum_wr = IntegerField('WR min. Leistung:', validators=[DataRequired()])
    dtu_ip = StringField('DTU IP:', validators=[DataRequired()])
    dtu_nutzer = StringField('DTU Benutzer:', validators=[DataRequired()])
    dtu_passwort = StringField('DTU Passwort:', validators=[DataRequired()])
    shelly_ip = StringField('Shelly IP:', validators=[DataRequired()])
    manual_limit = IntegerField('Manuelles Limit (W):', validators=[DataRequired()])
    submit = SubmitField('Speichern')


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

            logging.info(f'Bezug: {grid_sum:.1f} W, Produktion: {power:.1f} W, Verbrauch: {(grid_sum + power):.1f} W')

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


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ConfigForm()
    if form.validate_on_submit():
        config.update(
            serial=form.serial.data,
            maximum_wr=form.maximum_wr.data,
            minimum_wr=form.minimum_wr.data,
            dtu_ip=form.dtu_ip.data,
            dtu_nutzer=form.dtu_nutzer.data,
            dtu_passwort=form.dtu_passwort.data,
            shelly_ip=form.shelly_ip.data,
            manual_limit=form.manual_limit.data
        )
        if config['shelly_type'] is None:
            config['shelly_type'] = detect_shelly_type()

        if not config['auto_mode'] and config['manual_limit'] is not None:
            logging.info(f"Setting manual inverter limit: {config['manual_limit']} W")
            set_inverter_limit(config['manual_limit'])

        return redirect(url_for('index'))

    form.serial.data = config['serial']
    form.maximum_wr.data = config['maximum_wr']
    form.minimum_wr.data = config['minimum_wr']
    form.dtu_ip.data = config['dtu_ip']
    form.dtu_nutzer.data = config['dtu_nutzer']
    form.dtu_passwort.data = config['dtu_passwort']
    form.shelly_ip.data = config['shelly_ip']
    form.manual_limit.data = config['manual_limit']

    return render_template('index.html', form=form, auto_mode=config['auto_mode'])


@app.route('/start_auto', methods=['POST'])
def start_auto():
    config['auto_mode'] = True
    logging.info("Auto mode started")
    return redirect(url_for('index'))


@app.route('/stop_auto', methods=['POST'])
def stop_auto():
    config['auto_mode'] = False
    logging.info("Auto mode stopped")
    return redirect(url_for('index'))


@app.route('/data', methods=['GET'])
def get_data():
    dtu_data = fetch_dtu_data()
    if dtu_data is None:
        return jsonify({'error': 'Failed to fetch DTU data'}), 500

    shelly_data = fetch_shelly_data()
    if shelly_data is None:
        return jsonify({'error': 'Failed to fetch Shelly data'}), 500

    if config['auto_mode']:
        current_limit = dtu_data['altes_limit']
    elif config['manual_limit'] is not None:
        current_limit = config['manual_limit']
    else:
        current_limit = dtu_data['altes_limit']

    return jsonify({
        'dtu': dtu_data,
        'shelly': shelly_data,
        'current_limit': current_limit,
        'auto_mode': config['auto_mode']
    })


@app.route('/set_manual_limit', methods=['POST'])
def set_manual_limit():
    limit = request.json.get('limit')
    if limit is not None and not config['auto_mode']:
        if reachable:
            config['manual_limit'] = limit
            logging.info(f"Setting manual inverter limit: {limit} W")
            set_inverter_limit(limit)
            return jsonify({'status': 'success'}), 200
        else:
            logging.info("Setting manual inverter is not possible - inverter not reachable!")
            return jsonify({'status': 'failure', 'reason': 'unreachable'}), 400
    return jsonify({'status': 'failure', 'reason': 'Auto mode is enabled or invalid limit'}), 400


if __name__ == '__main__':
    auto_thread = threading.Thread(target=auto_mode_loop, daemon=True)
    auto_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True)
