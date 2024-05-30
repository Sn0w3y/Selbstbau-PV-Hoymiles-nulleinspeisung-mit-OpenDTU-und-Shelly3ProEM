
# Achtung! bei OpenDTU gab es eine API Anpassung

Dieses Skript ist kompatibel mit der neusten Version von OpenDTU ! :)

# Nulleinspeisung Hoymiles HM-1500 mit OpenDTU & Python Steuerung

Dies ist ein Python-Skript, das den aktuellen Hausverbrauch aus einem Shelly 3EM oder Shelly Pro 3 EM ausliest, die Nulleinspeisung berechnet und die Ausgangsleistung eines Hoymiles-Wechselrichters mit Hilfe der OpenDTU entsprechend anpasst. Somit wird kein unnötiger Strom ins Betreibernetz abgegeben.

![diagramm](media/diagramm.jpg)

## Autoren und Anerkennung
- Dieses Skript ist ein Fork von: https://gitlab.com/p3605/hoymiles-tarnkappe
- Ein großes Lob und Dank an die OpenDTU community: https://github.com/tbnobody/OpenDTU

## Wiki
- Weitere Informationen finden Sie auf unserer Seite: https://selbstbau-pv.de/wissensbasis/nulleinspeisung-hoymiles-hm-1500-mit-opendtu-python-steuerung/

## Setup-Anweisungen

### 1. Erstellen Sie eine virtuelle Umgebung (optional, aber empfohlen)
```sh
python -m venv venv
```

### 2. Aktivieren Sie die virtuelle Umgebung
- Unter Windows:
```sh
venv\Scripts\activate
```
- Unter macOS/Linux:
```sh
source venv/bin/activate
```

### 3. Erforderliche Pakete installieren
```sh
pip install -r requirements.txt
```

### 4. Die Flask-Anwendung ausführen
```sh
export FLASK_APP=app.py  # Oder setzen Sie die FLASK_APP-Umgebungsvariable auf den Namen Ihrer Flask-App-Datei
flask run
```

### 5. Entwicklungsserver
Standardmäßig läuft Flask auf Port 5000. Sie können die Anwendung öffnen, indem Sie in Ihrem Webbrowser zu `http://127.0.0.1:5000/` navigieren.

## requirements.txt
```
Flask==2.1.2
Flask-WTF==1.0.1
requests==2.28.1
WTForms==3.0.1
```

## Konsolenversion mit automatischer Erkennung des Shelly-Typs

- Die Konsolenversion erkennt automatisch, ob ein Shelly 3EM oder ein Shelly Pro 3 EM verwendet wird.
- Die Konfigurationsdaten und der aktuelle Hausverbrauch werden entsprechend angepasst.

## Web-Version (konfigurierbar)

- Die Web-Version bietet eine konfigurierbare Oberfläche, um die Einstellungen vorzunehmen und die Daten anzuzeigen.
- Sie können die Shelly- und DTU-Daten über eine Weboberfläche eingeben und anzeigen.

