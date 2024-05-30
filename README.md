
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

## Setup-Anweisungen (Ubuntu / Raspberry Pi)

### 1. Erforderliche Pakete installieren
```sh
sudo apt update
sudo apt install python3 python3-pip
```

### 2. Python-Abhängigkeiten installieren
```sh
pip3 install Flask Flask-WTF requests WTForms
```

### 3. Erstellen Sie eine Datei namens `app.py` und fügen Sie den Web-Version oder Console-Version Code ein.

### 4. Systemd Service einrichten

Erstellen Sie eine Service-Datei für systemd:

```sh
sudo nano /etc/systemd/system/nulleinspeisung.service
```

Fügen Sie folgenden Inhalt in die Datei ein:

```
[Unit]
Description=Flask Application for Nulleinspeisung Hoymiles
After=network.target

[Service]
ExecStart=/usr/bin/python3 /pfad/zu/ihrem/app.py
WorkingDirectory=/pfad/zu/ihrem/projektverzeichnis
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

### 5. Systemd Service aktivieren und starten

```sh
sudo systemctl daemon-reload
sudo systemctl enable nulleinspeisung.service
sudo systemctl start nulleinspeisung.service
```

### 6. Status des Services überprüfen
```sh
sudo systemctl status nulleinspeisung.service
```

Standardmäßig läuft Flask auf Port 5000. Sie können die Anwendung öffnen, indem Sie in Ihrem Webbrowser zu `http://<Ihre-Raspberry-Pi-IP>:5000/` navigieren.
Falls Sie sich für die Console-Version entschieden haben, läuft diese nur in der Konsole!

## requirements.txt für die Web-Version - für die Console-Version wird dies nicht benötigt !
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
