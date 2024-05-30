from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import logging
from requests.auth import HTTPBasicAuth
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Configuration settings
config = {
    'serial': '116494406970',
    'maximum_wr': 1600,
    'minimum_wr': 200,
    'dtu_ip': '192.168.17.225',
    'dtu_nutzer': 'admin',
    'dtu_passwort': 'openDTU42',
    'shelly_ip': '192.168.17.230',
    'shelly_type': 'Pro 3 EM',
    'auto_mode': True,
    'manual_limit': 0
}

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class ConfigForm(FlaskForm):
    serial = StringField('Serial', validators=[DataRequired()])
    maximum_wr = IntegerField('Maximum WR', validators=[DataRequired()])
    minimum_wr = IntegerField('Minimum WR', validators=[DataRequired()])
    dtu_ip = StringField('DTU IP', validators=[DataRequired()])
    dtu_nutzer = StringField('DTU Nutzer', validators=[DataRequired()])
    dtu_passwort = StringField('DTU Passwort', validators=[DataRequired()])
    shelly_ip = StringField('Shelly IP', validators=[DataRequired()])
    shelly_type = SelectField('Shelly Type', choices=[('Pro 3 EM', 'Pro 3 EM'), ('3 EM', '3 EM')],
                              validators=[DataRequired()])
    manual_limit = IntegerField('Manual Limit', validators=[DataRequired()])
    submit = SubmitField('Save')
    start_auto = SubmitField('Start AUTO Mode')
    stop_auto = SubmitField('Stop AUTO Mode')


def fetch_dtu_data():
    try:
        url = f'http://{config["dtu_ip"]}/api/livedata/status?inv={config["serial"]}'
        response = requests.get(url).json()
        inverter = response['inverters'][0]

        # Sum up all DC power channels
        total_dc_power = 0
        for key in inverter['DC']:
            total_dc_power += inverter['DC'][key]['Power']['v']

        return {
            'reachable': inverter['reachable'],
            'producing': int(inverter['producing']),
            'altes_limit': int(inverter['limit_absolute']),
            'power_dc': total_dc_power,
            'power': inverter['AC']['0']['Power']['v']
        }
    except Exception as e:
        logging.error(f'Error fetching DTU data: {e}')
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
        logging.error(f'Error fetching Shelly data: {e}')
        return None


def set_inverter_limit(setpoint):
    try:
        url = f'http://{config["dtu_ip"]}/api/limit/config'
        data = f'data={{"serial":"{config["serial"]}", "limit_type":0, "limit_value":{setpoint}}}'
        response = requests.post(url, data=data, auth=HTTPBasicAuth(config['dtu_nutzer'], config['dtu_passwort']),
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        response_data = response.json()
        logging.info(f'Configuration sent ({response_data["type"]})')
        return response_data
    except Exception as e:
        logging.error(f'Error sending inverter configuration: {e}')
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    form = ConfigForm()
    if form.validate_on_submit():
        config['serial'] = form.serial.data
        config['maximum_wr'] = form.maximum_wr.data
        config['minimum_wr'] = form.minimum_wr.data
        config['dtu_ip'] = form.dtu_ip.data
        config['dtu_nutzer'] = form.dtu_nutzer.data
        config['dtu_passwort'] = form.dtu_passwort.data
        config['shelly_ip'] = form.shelly_ip.data
        config['shelly_type'] = form.shelly_type.data
        config['manual_limit'] = form.manual_limit.data

        if form.start_auto.data:
            config['auto_mode'] = True
        elif form.stop_auto.data:
            config['auto_mode'] = False
            set_inverter_limit(config['manual_limit'])

        return redirect(url_for('index'))

    form.serial.data = config['serial']
    form.maximum_wr.data = config['maximum_wr']
    form.minimum_wr.data = config['minimum_wr']
    form.dtu_ip.data = config['dtu_ip']
    form.dtu_nutzer.data = config['dtu_nutzer']
    form.dtu_passwort.data = config['dtu_passwort']
    form.shelly_ip.data = config['shelly_ip']
    form.shelly_type.data = config['shelly_type']
    form.manual_limit.data = config['manual_limit']

    return render_template('index.html', form=form, auto_mode=config['auto_mode'])


@app.route('/data', methods=['GET'])
def get_data():
    dtu_data = fetch_dtu_data()
    if dtu_data is None:
        return jsonify({'error': 'Failed to fetch DTU data'}), 500

    shelly_data = fetch_shelly_data()
    if shelly_data is None:
        return jsonify({'error': 'Failed to fetch Shelly data'}), 500

    return jsonify({
        'dtu': dtu_data,
        'shelly': {'total_act_power': shelly_data},
        'current_limit': config['manual_limit'] if not config['auto_mode'] else dtu_data['altes_limit']
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
