# mock_shelly_server.py
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/rpc/EM.GetStatus', methods=['GET'])
def get_status_pro_3_em():
    return jsonify({
        "total_act_power": 2000  # Mock 2000W power for Shelly Pro 3 EM
    })

@app.route('/api/livedata/status', methods=["GET"])
def getinv():
    inv = request.args.get('inv')
    if inv == "114190658834":
        return jsonify({
  "inverters": [
    {
      "serial": "114190658834",
      "name": "Hannes",
      "order": 0,
      "data_age": 158,
      "poll_enabled": False,
      "reachable": True,
      "producing": False,
      "limit_relative": 0,
      "limit_absolute": 600,
      "AC": {
        "0": {
          "Power": {
            "v": 0,
            "u": "W",
            "d": 1
          },
          "Voltage": {
            "v": 0,
            "u": "V",
            "d": 1
          },
          "Current": {
            "v": 0,
            "u": "A",
            "d": 2
          },
          "Frequency": {
            "v": 0,
            "u": "Hz",
            "d": 2
          },
          "PowerFactor": {
            "v": 0,
            "u": "",
            "d": 3
          },
          "ReactivePower": {
            "v": 0,
            "u": "var",
            "d": 1
          }
        }
      },
      "DC": {
        "0": {
          "name": {
            "u": ""
          },
          "Power": {
            "v": 0,
            "u": "W",
            "d": 1
          },
          "Voltage": {
            "v": 0,
            "u": "V",
            "d": 1
          },
          "Current": {
            "v": 0,
            "u": "A",
            "d": 2
          },
          "YieldDay": {
            "v": 0,
            "u": "Wh",
            "d": 0
          },
          "YieldTotal": {
            "v": 0,
            "u": "kWh",
            "d": 3
          }
        },
        "1": {
          "name": {
            "u": ""
          },
          "Power": {
            "v": 0,
            "u": "W",
            "d": 1
          },
          "Voltage": {
            "v": 0,
            "u": "V",
            "d": 1
          },
          "Current": {
            "v": 0,
            "u": "A",
            "d": 2
          },
          "YieldDay": {
            "v": 0,
            "u": "Wh",
            "d": 0
          },
          "YieldTotal": {
            "v": 0,
            "u": "kWh",
            "d": 3
          }
        }
      },
      "INV": {
        "0": {
          "Power DC": {
            "v": 0,
            "u": "W",
            "d": 1
          },
          "YieldDay": {
            "v": 0,
            "u": "Wh",
            "d": 0
          },
          "YieldTotal": {
            "v": 0,
            "u": "kWh",
            "d": 3
          },
          "Temperature": {
            "v": 0,
            "u": "°C",
            "d": 1
          },
          "Efficiency": {
            "v": 0,
            "u": "%",
            "d": 3
          }
        }
      },
      "events": 0
    }
  ],
  "total": {
    "Power": {
      "v": 0,
      "u": "W",
      "d": 1
    },
    "YieldDay": {
      "v": 0,
      "u": "Wh",
      "d": 0
    },
    "YieldTotal": {
      "v": 0,
      "u": "kWh",
      "d": 3
    }
  },
  "hints": {
    "time_sync": False,
    "radio_problem": False,
    "default_password": False
  }
})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
