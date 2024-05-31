import json
from flask import Flask, render_template, redirect, url_for, jsonify, request
import threading
import logging
import requests
from config import config, config_lock
from utils import fetch_dtu_data, fetch_shelly_data, set_inverter_limit, auto_mode_loop, get_reachable_status

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jsfkhdfkjhdkhsijwd82'

def load_user_config():
    try:
        with open('user_config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def save_user_config(user_config):
    with open('user_config.json', 'w') as f:
        json.dump(user_config, f)

@app.route('/', methods=['GET'])
def check_config():
    if not load_user_config():
        return redirect(url_for('config_page'))
    return redirect(url_for('index'))

@app.route('/index', methods=['GET'])
def index():
    user_config = load_user_config()
    return render_template('index.html', config=user_config)


@app.route('/config', methods=['GET', 'POST'])
def config_page():
    if request.method == 'POST':
        user_config = request.json
        save_user_config(user_config)

        if user_config.get('auto_mode'):
            try:
                with config_lock:
                    config['auto_mode'] = True
                    logging.info("Auto mode started")
            except requests.exceptions.RequestException as e:
                return jsonify({'status': 'failure', 'error': str(e)}), 500

        return jsonify(status='success')
    return render_template('config.html')

@app.route('/api/livedata/status', methods=['POST'])
def api_livedata_status():
    dtu_ip = request.json.get('dtu_ip')
    dtu_user = request.json.get('dtu_user')
    dtu_password = request.json.get('dtu_password')
    if not dtu_ip or not dtu_user or not dtu_password:
        return jsonify({'error': 'DTU IP, user, and password are required'}), 400

    try:
        response = requests.get(f'http://{dtu_ip}/api/livedata/status', auth=(dtu_user, dtu_password))
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

    return jsonify(data)

@app.route('/data', methods=['GET'])
def get_data():
    user_config = load_user_config()
    inverters_data = []

    for inverter in user_config['inverters']:
        dtu_data = fetch_dtu_data(inverter['dtu_ip'], inverter['dtu_nutzer'], inverter['dtu_passwort'], inverter['serial'])
        if dtu_data is None:
            return jsonify({'error': 'Failed to fetch DTU data'}), 500
        inverters_data.append(dtu_data)

    shelly_data = fetch_shelly_data(user_config['shelly_ip'], user_config.get('shelly_type'))
    if shelly_data is None:
        return jsonify({'error': 'Failed to fetch Shelly data'}), 500

    return jsonify({
        'inverters': inverters_data,
        'shelly': shelly_data,
        'auto_mode': config['auto_mode']
    })

@app.route('/start_auto', methods=['POST'])
def start_auto():
    with config_lock:
        config['auto_mode'] = True
        logging.info("Auto mode started")
    return jsonify(status='success')

@app.route('/stop_auto', methods=['POST'])
def stop_auto():
    with config_lock:
        config['auto_mode'] = False
        logging.info("Auto mode stopped")
    return jsonify(status='success')

@app.route('/reachable_inverters', methods=['GET'])
def reachable_inverters():
    user_config = load_user_config()
    reachable_inverters = []

    for inverter in user_config['inverters']:
        dtu_data = fetch_dtu_data(inverter['dtu_ip'], inverter['dtu_nutzer'], inverter['dtu_passwort'], inverter['serial'])
        if dtu_data and dtu_data['reachable']:
            reachable_inverters.append(dtu_data)

    return jsonify(reachable_inverters)

@app.route('/set_manual_limit', methods=['POST'])
def set_manual_limit():
    serial = request.json.get('serial')
    limit = request.json.get('limit')
    if serial and limit is not None:
        with config_lock:
            if not config['auto_mode']:
                user_config = load_user_config()
                inverter = next((inv for inv in user_config['inverters'] if inv['serial'] == serial), None)
                if inverter:
                    dtu_data = fetch_dtu_data(inverter['dtu_ip'], inverter['dtu_nutzer'], inverter['dtu_passwort'], inverter['serial'])
                    if dtu_data and dtu_data['reachable']:
                        response = set_inverter_limit(limit, inverter['dtu_ip'], inverter['dtu_nutzer'], inverter['dtu_passwort'], serial)
                        if response and response.get('type') == 'success':
                            logging.info(f"Setting manual inverter limit for {serial}: {limit} W")
                            return jsonify({'status': 'success'}), 200
                        else:
                            logging.error(f"Failed to set manual inverter limit for {serial}")
                            return jsonify({'status': 'failure', 'reason': 'failed to set limit'}), 400
                    else:
                        logging.error(f"Inverter {serial} not reachable!")
                        return jsonify({'status': 'failure', 'reason': 'inverter not reachable'}), 400
                else:
                    logging.error(f"Inverter {serial} not found in configuration!")
                    return jsonify({'status': 'failure', 'reason': 'inverter not found'}), 400
            else:
                logging.error("Setting manual inverter limit failed - Auto mode is enabled")
                return jsonify({'status': 'failure', 'reason': 'auto mode is enabled'}), 400
    else:
        logging.error("Setting manual inverter limit failed - Invalid request parameters")
        return jsonify({'status': 'failure', 'reason': 'invalid parameters'}), 400

if __name__ == '__main__':
    auto_thread = threading.Thread(target=auto_mode_loop, daemon=True)
    auto_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
