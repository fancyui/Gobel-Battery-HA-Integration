---
description: Native Home Assistant Integration for Gobel Power Battery BMS
---

# Gobel Power Battery Home Assistant Integration (JK BMS, Pace BMS, TDT BMS)

[Deutsch](docs/de/README.md) | [简体中文](docs/zh-cn/README.md)

> **Note**: Looking for the ioBroker version? Check out the [ioBroker Gobel BMS Monitor Adapter](https://github.com/fancyui/ioBroker.gobel-bms-monitor).

The ultimate Home Assistant custom integration for smart energy storage monitoring. This integration communicates directly with your LiFePO4 battery banks running Pace BMS, JK BMS, or TDT BMS hardware, registering them as native entities in Home Assistant.

Unlike the previous Add-on version, this integration **does not require an MQTT broker**. It sets up device and sensor entities directly inside Home Assistant, supporting multi-device setups (e.g. multiple battery banks with different IPs/serial ports) via the visual configuration UI.

---

## Key Features & Capabilities:
* **Multi-BMS Compatibility:** Native support for Pace BMS (RS232/RS485/WiFi), JK BMS (55AA passive protocol), and TDT BMS (RS232).
* **Versatile Connectivity Options:** Connect directly via RS232-USB, RS232-to-Ethernet, RS232-to-WiFi, RS485-to-Ethernet, or RS485-to-WiFi.
* **Direct Integration (No MQTT Required):** Create native Home Assistant sensors and binary sensors directly for cell voltages, capacity, current, and faults.
* **Dynamic Multi-Device & Grouping:** Group overall metrics (Total SOC, Total Voltage, Total Current, etc.) under an aggregate Device, and create child Devices for each physical parallel-connected slave battery pack (fully compatible with Master-Slave dial structures).
* **Config Flow GUI Setup:** Easy setup via the HA "Devices & Services" menu. No YAML editing, command-line arguments, or manual configuration file creation required.

---

## Dashboard Example:

![image](https://www.gobelpower.com/images/github/dashboard-gobel-power-home-assistant-addon-1.webp)

---

## Pace BMS Connection Instructions:
- **RS232-WIFI/Ethernet module or RS232-USB cable needed**
- **Connection Port**: Connect Home Assistant to the **RS232** or **WIFI** interface of the Pace BMS.
- **Master BMS**: The connection must be made to the **Master BMS**.
- **DIP Switch Settings**: Ensure the DIP switch (Dial) of the master BMS is set to **1000**.

## JK BMS Connection Instructions:
- **RS485-WIFI/Ethernet module or RS485-USB cable needed**
- **Connection Port**: Connect Home Assistant to the **RS485B** or **RS485C** interface of the JK BMS.
- **Master BMS**: The connection must be made to the **Master BMS**.
- **DIP Switch Settings**: Ensure the DIP switch (Dial) of the master BMS is set to **0000**.

---

## Installation:

### Option 1: Via HACS (Recommended)
1. Ensure [HACS (Home Assistant Community Store)](https://hacs.xyz/) is installed.
2. Go to **HACS -> Integrations** in Home Assistant.
3. Click the three dots in the top-right corner and select **Custom repositories**.
4. Paste the URL of this repository: `https://github.com/fancyui/Gobel-Battery-HA-Integration`
5. Select **Integration** as the Category and click **Add**.
6. Find the **Gobel Battery Monitor** integration in HACS and click **Download**.
7. Restart Home Assistant.

### Option 2: Manual Installation
1. Download the latest release or clone the repository.
2. Copy the `custom_components/gobel_battery` directory into your Home Assistant `/config/custom_components/` folder.
3. Restart Home Assistant.

---

## Configuration:
1. In Home Assistant, go to **Settings -> Devices & Services**.
2. Click **Add Integration** in the bottom-right corner.
3. Search for **Gobel Battery Monitor** and click to set it up.
4. Follow the configuration steps on-screen to choose your BMS type, connection method (Network vs. Serial), and input connection parameters.
5. If you have multiple battery banks with different IPs/ports, simply click **Add Integration** again to configure additional instances.