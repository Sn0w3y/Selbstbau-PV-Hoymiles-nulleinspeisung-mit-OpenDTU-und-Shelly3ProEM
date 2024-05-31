# config.py
import threading

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

config_lock = threading.Lock()
