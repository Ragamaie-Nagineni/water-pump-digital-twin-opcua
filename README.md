# 🏭 Industrial Water Pump Digital Twin & Predictive Maintenance System

An end-to-end cyber-physical **Digital Twin** system for industrial water pump monitoring. The system integrates edge IoT microcontroller hardware, wireless MQTT telemetry, physics-informed machine learning for multi-stage diagnostics and prognostics, SQLite persistent logging, and an industrial-grade **OPC-UA server** for SCADA integration.

---

## 📌 System Architecture

```text
  [ Historical / Live Data ]
              │
              ▼
    [ Python Serial Streamer ] (PC COM Port)
              │  (USB Serial @ 115200 baud)
              ▼
   [ Arduino Uno R4 WiFi ] (Edge Node)
       ├── Actuates onboard Alert LED for faults
       └── Publishes JSON telemetry over Wi-Fi
              │
              ▼ (MQTT: HiveMQ Broker)
      [ Laptop 2 / twin.py ] (Digital Twin Core Engine)
              │
              ├── 🧠 Physics-Informed AI/ML Engine
              │     ├── Binary Fault Detection (Random Forest)
              │     ├── Multi-Class Failure Diagnosis (Random Forest)
              │     └── Remaining Useful Life (RUL) Regressor + EMA Filter
              │
              ├── 💾 SQLite Persistent Storage (readings.db)
              │
              └── 🌐 Industrial OPC-UA Server (asyncua @ opc.tcp://localhost:4840)
                    └── Exposes nodes to SCADA / Factory Automation clients
```

---

## ✨ Key Features

- **Edge IoT Hardware Gateway:** Arduino Uno R4 WiFi parses serial data packets, runs edge logic, controls physical LED indicators, and publishes structured JSON over Wi-Fi.
- **Wireless Telemetry:** Uses lightweight MQTT protocol via `broker.hivemq.com` to stream high-frequency telemetry.
- **Physics-Informed Feature Engineering:** Incorporates domain physics into machine learning:
  - **Thermal Gradient ($\Delta T$):** $T_{\text{process}} - T_{\text{air}}$ (Kelvin)
  - **Hydraulic Shaft Power ($P$):** $\frac{2 \pi \cdot N \cdot \tau}{60,000} \text{ kW}$ (from speed $N$ and torque $\tau$)
  - **Mechanical Overstrain ($\sigma$):** $\text{Tool Wear} \times \text{Torque}$ ($\text{min}\cdot\text{Nm}$)
- **Multi-Stage AI Diagnostics & Prognostics:**
  1. **Binary Classifier:** Real-time health vs. fault detection (balanced for class imbalance).
  2. **Multi-Class Classifier:** Classifies failure mechanisms (Heat Dissipation, Power Failure, Overstrain, Tool Wear, Random).
  3. **RUL Regressor:** Continuous estimation of remaining operational hours with Exponential Moving Average (EMA) smoothing.
- **Industrial Standards Compliance (OPC-UA):** Laptop acts as an active OPC-UA server, exposing digital twin state nodes to industrial SCADA systems (e.g., Ignition, Siemens WinCC, UaExpert).
- **Persistent Storage:** SQLite backend logs historical records with dynamic schema migration.

---

## 🗂️ Project Structure

```text
├── ai4i2020.csv           # UCI Predictive Maintenance Dataset (10,000 cycles)
├── train_model.py         # End-to-end ML training & physics feature pipeline
├── pump_ai_model.pkl      # Serialized ML model bundle (Classifier + Regressor)
├── streamer.py            # Feeds CSV rows over USB Serial to Arduino
├── arduino_gateway.ino    # Arduino Uno R4 WiFi sketch (Serial -> MQTT Bridge)
├── twin.py                # Digital Twin core: MQTT consumer, AI inference, OPC-UA server
├── database.py            # SQLite schema initialization and data persistence
├── config.py              # Central configuration (Broker, Ports, Topics, OPC-UA URL)
└── requirements.txt       # Python dependencies
```

---

## 🧮 Physics & Machine Learning Pipeline

### 1. Physics Features Calculated:

| Feature | Formula | Engineering Significance |
| :--- | :--- | :--- |
| `Temp_Diff` | `Process_Temp - Air_Temp` (K) | Indicates cooling failure or thermal dissipation stress (HDF). |
| `Power_kW` | `(Torque × 2π × RPM / 60) / 1000` | Detects power over-consumption, mechanical stall, or cavitation. |
| `Overstrain` | `Tool_Wear × Torque` (min·Nm) | Measures cumulative mechanical stress and fatigue wear (OSF). |

### 2. Multi-Stage Models:
1. **`binary_model` (`RandomForestClassifier`):**
   - 100 Trees, `class_weight='balanced'`.
   - Distinguishes normal operation from machine fault conditions.
2. **`mode_model` (`RandomForestClassifier`):**
   - Diagnoses the exact root cause: `Heat Dissipation Failure (HDF)`, `Power Failure (PWF)`, `Overstrain Failure (OSF)`, `Tool Wear Failure (TWF)`, or `Random Failure (RNF)`.
3. **`rul_model` (`RandomForestRegressor`):**
   - Estimates Remaining Useful Life (RUL) in hours based on degradation threshold penalised by stress and thermal fatigue.
   - Outputs are stabilized through an Exponential Moving Average (EMA, $\alpha=0.15$) filter.

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.9+
- Arduino IDE (with `WiFiS3` and `PubSubClient` libraries installed)
- Hardware: Arduino Uno R4 WiFi (or compatible ESP32 / Uno board)

### 2. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/YOUR_USERNAME/industrial-digital-twin-predictive-maintenance.git
cd industrial-digital-twin-predictive-maintenance
pip install -r requirements.txt
```

Example `requirements.txt`:
```text
pyserial
paho-mqtt
pandas
numpy
scikit-learn
joblib
asyncua
```

### 3. Training the AI Models
Train the multi-task model bundle from the raw dataset:
```bash
python train_model.py
```
This produces `pump_ai_model.pkl`.

### 4. Running the Complete System

#### Step A: Flash the Microcontroller
Upload `arduino_gateway.ino` to the Arduino Uno R4 WiFi using the Arduino IDE. Ensure your Wi-Fi SSID and password are configured.

#### Step B: Start the Digital Twin Server
Run the digital twin engine on your monitoring computer:
```bash
python twin.py
```
*Note: If testing without the physical Arduino, set `DEMO_MODE = True` in `config.py`.*

#### Step C: Start the Sensor Streamer
Connect the Arduino via USB and launch the streamer:
```bash
python streamer.py
```

---

## 🔌 Connecting via OPC-UA Client (e.g., UaExpert)

1. Open any OPC-UA client (e.g., Unified Automation **UaExpert**).
2. Connect to the server endpoint:
   ```text
   opc.tcp://localhost:4840
   ```
3. Navigate to: `Root` $\rightarrow$ `Objects` $\rightarrow$ `WaterPump`
4. Subscribe to live tags:
   - `FaultStatus` (String: `NORMAL` / `FAULT`)
   - `RUL_Hours` (Float: Real-time estimated remaining hours)
   - `RPM` (Float: Rotational speed)
   - `Torque` (Float: Mechanical torque)

---

## 📜 License
This project is open-source under the [MIT License](LICENSE).

---

## 👤 Author

- **Name:** Ragamaie N
- **Email:** [ragamaie.n@gmail.com](mailto:ragamaie.n@gmail.com)
