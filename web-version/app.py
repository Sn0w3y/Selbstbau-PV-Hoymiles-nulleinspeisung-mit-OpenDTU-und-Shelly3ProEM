# app.py
from flask import Flask, render_template, redirect, url_for, jsonify, request
from forms import ConfigForm  # Add this line to import ConfigForm
import threading
import logging
from config import config, config_lock
from utils import detect_shelly_type, fetch_dtu_data, fetch_shelly_data, set_inverter_limit, auto_mode_loop

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jsfkhdfkjhdkhsijwd82'

reachable = None

@app.route('/', methods=['GET', 'POST'])
def index():
    form = ConfigForm()
    if form.validate_on_submit():
        with config_lock:
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

    with config_lock:
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
    with config_lock:
        config['auto_mode'] = True
        logging.info("Auto mode started")
    return redirect(url_for('index'))


@app.route('/stop_auto', methods=['POST'])
def stop_auto():
    with config_lock:
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

    with config_lock:
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
    if limit is not None:
        with config_lock:
            if not config['auto_mode']:
                if reachable:
                    config['manual_limit'] = limit
                    logging.info(f"Setting manual inverter limit: {limit} W")
                    set_inverter_limit(limit)
                    return jsonify({'status': 'success'}), 200
                else:
                    logging.info("Setting manual inverter is not possible - inverter not reachable!")
                    return jsonify({'status': 'failure', 'reason': 'unreachable'}), 400
            return jsonify({'status': 'failure', 'reason': 'Auto mode is enabled or invalid limit'}), 400
    return jsonify({'status': 'failure', 'reason': 'Invalid limit value'}), 400


if __name__ == '__main__':
    auto_thread = threading.Thread(target=auto_mode_loop, daemon=True)
    auto_thread.start()
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
