
# Achtung! bei OpenDTU gab es eine API Anpassung

Dieses Skript ist kompatibel mit der neusten Version von OpenDTU ! :)

# Nulleinspeisung Hoymiles HM-1500 mit OpenDTU & Python Steuerung

Dies ist ein Python-Skript, das den aktuellen Hausverbrauch aus einem Shelly 3EM ausliest, die Nulleinspeisung berechnet und die Ausgangsleistung eines Hoymiles-Wechselrichters mit Hilfe der OpenDTU entsprechend anpasst. Somit wird kein unnötiger Strom ins Betreibernetz abgegeben.

![diagramm](media/diagramm.jpg)

## Autoren und Anerkennung
- Dieses Skript ist ein Fork von: https://gitlab.com/p3605/hoymiles-tarnkappe
- Ein großes Lob und Dank an die OpenDTU community: https://github.com/tbnobody/OpenDTU

## Wiki
- Weitere Informationen finden Sie auf unserer Seite: https://selbstbau-pv.de/wissensbasis/nulleinspeisung-hoymiles-hm-1500-mit-opendtu-python-steuerung/

## Setup Instructions

### 1. Create a Virtual Environment (optional but recommended)
```sh
python -m venv venv
```

### 2. Activate the Virtual Environment
- On Windows:
```sh
venv\Scripts\activate
```
- On macOS/Linux:
```sh
source venv/bin/activate
```

### 3. Install Required Packages
```sh
pip install -r requirements.txt
```

### 4. Run the Flask Application
```sh
export FLASK_APP=app.py  # Or set the FLASK_APP environment variable to your Flask app filename
flask run
```

### 5. Development Server
By default, Flask runs on port 5000. You can access the application by navigating to `http://127.0.0.1:5000/` in your web browser.

## requirements.txt
```
Flask==2.1.2
Flask-WTF==1.0.1
requests==2.28.1
WTForms==3.0.1
```

