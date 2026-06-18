# Gobel Power Battery Home Assistant Integration (JK BMS, Pace BMS, TDT BMS)

[English](../../README.md) | [简体中文](../zh-cn/README.md)

> **Hinweis**: Suchen Sie nach der ioBroker-Version? Besuchen Sie den [ioBroker Gobel BMS Monitor Adapter](https://github.com/fancyui/ioBroker.gobel-bms-monitor).

Die ultimative Home Assistant-Integration für die intelligente Überwachung von Energiespeichern. Diese benutzerdefinierte Integration kommuniziert direkt mit Ihren LiFePO4-Batteriebänken mit Pace BMS-, JK BMS- oder TDT BMS-Hardware und registriert sie als native Entitäten in Home Assistant.

Im Gegensatz zur vorherigen Add-on-Version **benötigt diese Integration keinen MQTT-Broker**. Sie erstellt Geräte- und Sensorentitäten direkt in Home Assistant und unterstützt über die visuelle Benutzeroberfläche Konfigurationen mit mehreren Geräten (z. B. Überwachung mehrerer Batteriebänke mit unterschiedlichen IPs/seriellen Anschlüssen).

---

## Hauptmerkmale & Funktionen:
* **Multi-BMS-Kompatibilität:** Native Unterstützung für Pace BMS (RS232/RS485/WiFi), JK BMS (55AA-Passivprotokoll) und TDT BMS (RS232).
* **Vielseitige Konnektivitätsoptionen:** Verbinden Sie Ihre Hardware über RS232-USB, RS232-zu-Ethernet, RS232-zu-WiFi, RS485-zu-Ethernet oder RS485-zu-WiFi.
* **Direkte Integration (kein MQTT erforderlich):** Erstellt native Home Assistant-Sensoren und Binärsensoren direkt für Zellspannungen, Kapazität, Strom, Temperaturen und Fehlermeldungen.
* **Dynamische Gerätegruppierung:** Gruppiert Gesamtmetriken (Gesamt-SOC, Gesamtspannung, Gesamtstrom, Gesamtleistung) unter einem übergeordneten Gerät und erstellt untergeordnete Geräte für jedes physische, parallel geschaltete Slave-Batteriepack.
* **Config Flow GUI Einrichtung:** Einfache Einrichtung über das Menü „Geräte & Dienste“ in HA. Es sind keine YAML-Änderungen, Befehlszeilen oder manuellen Konfigurationsdateien erforderlich.

---

## Dashboard-Beispiel:

![image](https://www.gobelpower.com/images/github/dashboard-gobel-power-home-assistant-addon-1.webp)

---

## Anschlussanleitung für Pace BMS:
- **RS232-WIFI/Ethernet-Modul oder RS232-USB-Kabel erforderlich**
- **Anschlussport**: Verbinden Sie Home Assistant mit der **RS232**- oder **WIFI**-Schnittstelle des Pace BMS.
- **Master-BMS**: Die Verbindung muss mit dem **Master-BMS** hergestellt werden.
- **DIP-Schalter-Einstellungen**: Stellen Sie sicher, dass die DIP-Schalter (Wahlschalter) des Master-BMS auf **1000** eingestellt sind.

## Anschlussanleitung für JK BMS:
- **RS485-WIFI/Ethernet-Modul oder RS485-USB-Kabel erforderlich**
- **Anschlussport**: Verbinden Sie Home Assistant mit der **RS485B**- oder **RS485C**-Schnittstelle des JK BMS.
- **Master-BMS**: Die Verbindung muss mit dem **Master-BMS** hergestellt werden.
- **DIP-Schalter-Einstellungen**: Stellen Sie sicher, dass die DIP-Schalter (Wahlschalter) des Master-BMS auf **0000** eingestellt sind.

---

## Installation:

### Option 1: Über HACS (empfohlen)
1. Stellen Sie sicher, dass [HACS (Home Assistant Community Store)](https://hacs.xyz/) installiert ist.
2. Gehen Sie in Home Assistant auf **HACS -> Integrationen**.
3. Klicken Sie auf die drei Punkte in der oberen rechten Ecke und wählen Sie **Benutzerdefinierte Repositories**.
4. Fügen Sie die URL dieses Repositories ein: `https://github.com/fancyui/Gobel-Battery-HA-Integration`
5. Wählen Sie **Integration** als Kategorie aus und klicken Sie auf **Hinzufügen**.
6. Suchen Sie nach der Integration **Gobel Battery Monitor** in HACS und klicken Sie auf **Herunterladen**.
7. Starten Sie Home Assistant neu.

### Option 2: Manuelle Installation
1. Laden Sie die neueste Version (Zip-Datei) herunter.
2. Kopieren Sie das Verzeichnis `custom_components/gobel_battery` in das Verzeichnis `/config/custom_components/` Ihres Home Assistant.
3. Starten Sie Home Assistant neu.

---

## Konfiguration:
1. Gehen Sie in Home Assistant auf **Einstellungen -> Geräte & Dienste**.
2. Klicken Sie unten rechts auf **Integration hinzufügen**.
3. Suchen Sie nach **Gobel Battery Monitor** und klicken Sie darauf.
4. Folgen Sie den Schritten auf dem Bildschirm, um Ihren BMS-Typ und Ihre Verbindungsmethode auszuwählen, und geben Sie die Verbindungsparameter ein.
5. Wenn Sie mehrere Batteriebänke mit unterschiedlichen IPs/Ports haben, klicken Sie einfach erneut auf **Integration hinzufügen**, um weitere Instanzen einzurichten.
