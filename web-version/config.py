# config.py
import threading

config = {
    'shelly_type': None,
    'auto_mode': False,
    'manual_limit': None
}

config_lock = threading.Lock()
