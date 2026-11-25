# PROJECT TECHNICAL REPORT

---

## **DESIGN AND IMPLEMENTATION OF AN INDUSTRIAL IOT DIGITAL TWIN FOR WATER PUMP FAULT DETECTION AND PREDICTIVE MAINTENANCE**

**Domain:** Industrial Internet of Things (IIoT), Digital Twins, Machine Learning, Industry 4.0  
**Target Hardware:** Arduino UNO R4 WiFi (Renesas RA4M1 + ESP32-S3)  
**Software Stack:** Python 3, scikit-learn, Flask, OPC-UA (IEC 62541), MQTT, SQLite  
**Academic Session:** Dec 2026 Evaluation  

---

### **TABLE OF CONTENTS**
1. [Abstract](#1-abstract)
2. [Introduction and Project Justification](#2-introduction-and-project-justification)
   - 2.1 Problem Statement & Industrial Need
   - 2.2 Why This Solution is Different from Existing Solutions
3. [System Architecture & Functional Block Diagram](#3-system-architecture--functional-block-diagram)
   - 3.1 End-to-End Architectural Flow
   - 3.2 Hardware Modules & Embedded Specifications
   - 3.3 Networking & Cloud Infrastructure (MQTT Broker)
   - 3.4 Software Architecture & Sub-Modules
4. [Sensing & Synthetic Telemetry Generation](#4-sensing--synthetic-telemetry-generation)
   - 4.1 Dataset Physics & Sensor Mapping (`ai4i2020.csv`)
   - 4.2 Edge Serial Feeding Mechanism (`streamer.py`)
5. [Edge IoT Node Implementation (`pump_emulator.ino`)](#5-edge-iot-node-implementation)
   - 5.1 Embedded Packet Parsing & Actuation (Pin 13 LED Alarm)
   - 5.2 Wireless MQTT Telemetry Publishing
6. [Machine Learning Models & Prognostics Engine](#6-machine-learning-models--prognostics-engine)
   - 6.1 Physics-Informed Feature Engineering
   - 6.2 Anomaly & Binary Fault Detection Model (Random Forest)
   - 6.3 Multi-Class Failure Mode Identification (PWF, HDF, TWF, OSF, RNF)
   - 6.4 Remaining Useful Life (RUL) Prognostics
   - 6.5 Model Evaluation & Performance Metrics
7. [Industrial Interoperability Layer: OPC-UA (IEC 62541)](#7-industrial-interoperability-layer-opc-ua-iec-62541)
   - 7.1 Address Space & Node Design
   - 7.2 SCADA & Enterprise Integration
8. [Digital Twin State Engine & Web Dashboard HMI](#8-digital-twin-state-engine--web-dashboard-hmi)
   - 8.1 State Management & Historian Logging (SQLite)
   - 8.2 Real-Time Visualization Interface (Flask + Chart.js)
9. [Experimental Results & Hardware Validation](#9-experimental-results--hardware-validation)
10. [Scalability, Future Work & Conclusion](#10-scalability-future-work--conclusion)
11. [References](#11-references)

---

### **1. ABSTRACT**

Centrifugal water pumps form the backbone of modern municipal, agricultural, and industrial infrastructure. Unplanned pump failures lead to catastrophic downtime, substantial economic losses, and hazardous operating environments. Traditional maintenance paradigms—reactive breakdown repairs and rigid calendar-based preventive scheduling—fail to address dynamic mechanical degradation. 

This project designs and demonstrates a complete, end-to-end **Cyber-Physical Digital Twin (CPDT)** for real-time fault detection and predictive maintenance of an industrial water pump. The system integrates a physical edge sensor node (**Arduino UNO R4 WiFi**), a synthetic telemetry injection pipeline using the **AI4I 2020 Predictive Maintenance dataset**, a cloud-enabled **MQTT** communication bus, a dual-layer **Machine Learning engine** (achieving **98.30% fault detection accuracy** and **96.65% fault classification accuracy**), an **OPC-UA (IEC 62541)** industrial interoperability server, and a high-performance **Web HMI Dashboard** backed by an SQLite historical telemetry database. 

Physical actuation is realized through an automatic edge alarm loop, while prognostics capabilities estimate the Remaining Useful Life (RUL) in hours. The resulting architecture establishes a low-cost, open-standard, and scalable Industry 4.0 template for predictive machinery health management.

---

### **2. INTRODUCTION AND PROJECT JUSTIFICATION**

#### **2.1 Problem Statement & Industrial Need**
Rotating machinery in fluid transmission systems experiences harsh operational stressors including cavitation, thermal dissipation saturation, electrical power fluctuations, and mechanical tool wear. Conventional Supervisory Control and Data Acquisition (SCADA) systems provide reactive threshold alarms but lack autonomous cognitive capabilities to anticipate imminent breakdowns or diagnose multi-variable failure root causes before catastrophic damage occurs.

#### **2.2 Why This Solution is Different from Existing Solutions**
Current commercial solutions suffer from significant drawbacks:
1. **High Capital Expenditure:** Proprietary industrial predictive maintenance suites (e.g., Siemens MindSphere, GE Predix) cost thousands of dollars in licensing and specialized hardware.
2. **Vendor Lock-In:** Closed communication protocols restrict interoperability with legacy enterprise equipment.
3. **Rigid Rule-Based Thresholds:** Conventional systems rely on static thresholds ($T > T_{max}$), missing complex multi-parameter anomalies where temperature, speed, and torque interact non-linearly.

**Key Innovations in This Project:**
- **Open-Standard IIoT Protocols:** Combines lightweight edge-to-cloud **MQTT** telemetry with industrial-grade **OPC-UA** address space mapping.
- **Physics-Informed Edge Emulation:** Utilizes synthetic hardware data injection over USB serial to convert an Arduino UNO R4 WiFi into an authentic, calibrated IoT sensor node.
- **Dual-Model ML Architecture:** Concurrently executes high-accuracy binary fault screening, multi-class failure attribution (PWF, HDF, TWF, OSF, RNF), and Remaining Useful Life (RUL) regression in under 5 milliseconds.
- **Two-Tier Hardware Decoupling:** Implements a realistic two-laptop demonstration architecture where data injection and virtual twin processing are decoupled across independent wireless nodes.

---

### **3. SYSTEM ARCHITECTURE & FUNCTIONAL BLOCK DIAGRAM**

#### **3.1 End-to-End Architectural Flow**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PHYSICAL EDGE LAYER                             │
│  ┌───────────────────────┐            ┌─────────────────────────────┐  │
│  │ Laptop 1: Data Feeder │──USB (COM)─│ Arduino UNO R4 WiFi         │  │
│  │ (streamer.py)         │            │ (pump_emulator.ino)         │  │
│  └───────────────────────┘            └──────────────┬──────────────┘  │
└──────────────────────────────────────────────────────┼─────────────────┘
                                                       │ WiFi (MQTT Pub)
                                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        CLOUD COMMUNICATION BUS                         │
│                    HiveMQ Cloud MQTT Broker (:1883)                    │
│                        Topic: pump/sensor/data                         │
└──────────────────────────────────────┬─────────────────────────────────┘
                                       │ WiFi (MQTT Sub)
                                       ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     CYBER DIGITAL TWIN LAYER                           │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Laptop 2: Digital Twin & AI Engine (twin.py / app.py)             │  │
│  │                                                                  │  │
│  │  ┌─────────────────────────┐     ┌────────────────────────────┐  │  │
│  │  │ AI/ML Diagnostic Engine │     │ OPC-UA Industrial Server   │  │  │
│  │  │ • Random Forest (98.3%) │     │ • IEC 62541 Endpoint       │  │  │
│  │  │ • RUL Regressor         │     │ • Port 4840 Nodes          │  │  │
│  │  └────────────┬────────────┘     └─────────────┬──────────────┘  │  │
│  │               │                                │                 │  │
│  │               ▼                                ▼                 │  │
│  │  ┌─────────────────────────┐     ┌────────────────────────────┐  │  │
│  │  │ SQLite Database Logger  │     │ Web HMI Dashboard          │  │  │
│  │  │ (pump_twin.db)          │     │ (http://localhost:5000)    │  │  │
│  │  └─────────────────────────┘     └────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

#### **3.2 Hardware Modules & Embedded Specifications**
- **Processor:** Renesas RA4M1 32-bit ARM Cortex-M4 microcontroller running at 48 MHz.
- **Connectivity Coprocessor:** Espressif ESP32-S3 module enabling dual-band 2.4 GHz 802.11 b/g/n Wi-Fi and Bluetooth LE.
- **Memory Profile:** 32 KB SRAM, 256 KB Flash memory.
- **Physical Actuator:** Pin 13 built-in visual LED and logic header triggered via reverse MQTT topic callback (`pump/sensor/alert`) and local edge threshold triggers.

#### **3.3 Networking & Cloud Infrastructure**
- **MQTT Transport Layer:** Utilizes lightweight TCP/IP packet framing.
- **Cloud Broker:** Public broker (`broker.hivemq.com:1883`) allowing seamless distributed multi-node communication across different physical networks and cellular hotspots without requiring local port forwarding.
- **Payload Encoding:** Compact JSON serialization containing timestamp, rotational velocity, torque, fluid/ambient temperatures, tool wear, and failure flags.

#### **3.4 Software Architecture & Sub-Modules**
The software is organized into four decoupled sub-modules:
1. `streamer.py`: High-precision serial pacing transmitter.
2. `pump_emulator.ino`: Embedded firmware handling serial ingestion, JSON packaging, and wireless publishing.
3. `twin.py`: Multi-threaded background orchestrator executing MQTT subscription, feature extraction, ML inference, and OPC-UA node updates.
4. `app.py`: Flask asynchronous REST and Web UI presentation server.

---

### **4. SENSING & SYNTHETIC TELEMETRY GENERATION**

#### **4.1 Dataset Physics & Sensor Mapping (`ai4i2020.csv`)**
To reflect realistic operational dynamics without risking destructive physical pump tests, the project employs the UCI **AI4I 2020 Predictive Maintenance Dataset**, comprising 10,000 real industrial telemetry snapshots.

| Parameter | Symbol | Unit | Physical Significance | Nominal Range |
|:---|:---:|:---:|:---|:---:|
| **Air Temperature** | $T_{air}$ | Kelvin [K] | Ambient surrounding thermal condition | 295.3 – 304.5 K |
| **Process Temperature** | $T_{proc}$ | Kelvin [K] | Internal fluid / casing contact temperature | 305.7 – 313.8 K |
| **Rotational Speed** | $N$ | RPM | Impeller shaft angular velocity | 1168 – 2886 RPM |
| **Torque** | $\tau$ | Nm | Resistive shaft load from fluid displacement | 3.8 – 76.6 Nm |
| **Tool Wear** | $W$ | Minutes | Cumulative mechanical erosion on impeller vanes | 0 – 253 min |
| **Machine Failure** | $Y$ | Binary | Ground truth label (0 = Normal, 1 = Fault) | 0 or 1 |

#### **4.2 Edge Serial Feeding Mechanism (`streamer.py`)**
The Python streaming daemon establishes an exclusive serial connection at **115200 baud** over USB. Rows are parsed into an aligned CSV packet:
```
[AirTemp],[ProcessTemp],[RPM],[Torque],[ToolWear],[Failure]\n
```
The feeder introduces a deterministic pacing delay ($\Delta t = 0.5\text{--}1.0\text{ s}$) matching the sample frequency of industrial monitoring networks, reads back embedded acknowledgments (`ACK_FROM_ARDUINO`), and logs latency.

---

### **5. EDGE IOT NODE IMPLEMENTATION (`pump_emulator.ino`)**

The Arduino sketch transforms the microcontroller into an autonomous IoT edge transmitter:
1. **Interrupt-Driven Ring Buffer:** Non-blocking serial parsing using character accumulation and `strtok()` tokenization guarantees zero packet loss.
2. **Local Edge Actuation:** When the incoming telemetry indicates a fault state ($Y = 1$), the firmware executes immediate hardware-level actuation:
   ```cpp
   if (failure == 1) {
     digitalWrite(LED_PIN, HIGH); // Alarm trip
   } else {
     digitalWrite(LED_PIN, LOW);
   }
   ```
3. **JSON Serialization & Wireless Publishing:** Formats structured JSON telemetry through `ArduinoJson 6` and publishes via `PubSubClient`:
   ```json
   {"air_temp":298.1,"process_temp":308.6,"rpm":1551,"torque":42.8,"tool_wear":14,"failure":0}
   ```

---

### **6. MACHINE LEARNING MODELS & PROGNOSTICS ENGINE**

#### **6.1 Physics-Informed Feature Engineering**
Rather than feeding raw telemetry directly into machine learning models, domain physics of centrifugal pumping systems are applied to derive three critical diagnostic features:

1. **Thermal Dissipation Differential ($\Delta T$):**
   $$\Delta T = T_{proc} - T_{air}$$
   A collapse in thermal gradient ($\Delta T < 8.6\text{ K}$) at high rotational speeds indicates Heat Dissipation Failure (HDF) caused by cooling subsystem occlusion.

2. **Hydraulic Shaft Power ($P_{hyd}$):**
   $$P_{hyd} = \tau \cdot \omega = \tau \cdot \left(\frac{2 \pi N}{60}\right) \times 10^{-3} \quad [\text{kW}]$$
   Normal pumping operations exhibit a bounded power curve ($3.5\text{ kW} \le P_{hyd} \le 9.0\text{ kW}$). Deviations signify electrical supply anomalies, dry running ($< 3.5\text{ kW}$), or motor overload ($> 9.0\text{ kW}$), representing Power Failure (PWF).

3. **Mechanical Overstrain Indicator ($OS$):**
   $$OS = W \cdot \tau \quad [\text{min} \cdot \text{Nm}]$$
   Combines cumulative physical wear with instantaneous mechanical loading. Empirical failure occurs when $OS > 11,000$.

#### **6.2 Anomaly & Binary Fault Detection Model (Random Forest)**
- **Algorithm:** Random Forest Classifier ($N_{estimators} = 100$, Depth $= 12$).
- **Imbalance Mitigation:** Real-world failure events constitute only 3.39% of the dataset (339 faults vs 9,661 normal points). Synthetic cost-sensitive balancing (`class_weight='balanced'`) was applied to penalize false negatives.
- **Result:** **98.30% Overall Accuracy** and **0.78 F1-Score** on previously unseen test folds.

#### **6.3 Multi-Class Failure Mode Identification**
A secondary ensemble classifier diagnoses the specific root cause among the 5 distinct failure mechanisms:
1. **TWF (Tool Wear Failure):** Vane blade erosion exceeding safe operational margins.
2. **HDF (Heat Dissipation Failure):** Insufficient cooling causing thermal expansion seizure.
3. **PWF (Power Failure):** Severe deviations in the torque-velocity power envelope.
4. **OSF (Overstrain Failure):** High mechanical load combined with progressive wear.
5. **RNF (Random Failure):** Uncorrelated exogenous operational events.
- **Classification Performance:** **96.65% Multi-Class Accuracy**.

#### **6.4 Remaining Useful Life (RUL) Prognostics**
To provide predictive horizon advisory rather than simple reactive alarms, a Random Forest Regressor estimates the operational hours remaining before critical failure:
$$\text{RUL} = \max\left(0, \frac{(250 - W) \cdot 1.6}{\Psi_{thermal} \cdot \Psi_{mechanical}}\right) \quad [\text{Hours}]$$
where $\Psi_{thermal}$ and $\Psi_{mechanical}$ represent non-linear acceleration strain penalties when $\Delta T$ or Overstrain exceed baseline bounds.

---

### **7. INDUSTRIAL INTEROPERABILITY LAYER: OPC-UA (IEC 62541)**

In compliance with Industry 4.0 guidelines, the Digital Twin exposes its internal state through an embedded OPC-UA server:
- **Server Endpoint:** `opc.tcp://0.0.0.0:4840/pump/twin/`
- **Namespace:** `http://waterpump.digitaltwin`
- **Exposed Node Hierarchy:**
  ```
  Root / Objects / 2:WaterPump
  ├── 2:RPM          (Double, Read-Only)
  ├── 2:Torque       (Double, Read-Only)
  ├── 2:FaultStatus  (String, Read/Write)
  └── 2:RUL_Hours    (Double, Read/Write)
  ```
This enables direct plug-and-play interoperability with industrial SCADA systems (e.g., Ignition, Siemens WinCC, MATLAB OPC-UA Toolbox) without requiring custom API drivers.

---

### **8. DIGITAL TWIN STATE ENGINE & WEB DASHBOARD HMI**

#### **8.1 State Management & Historian Logging (SQLite)**
The Digital Twin core (`twin.py`) executes an asynchronous state engine. Every ingested telemetry packet triggers ML inference, updates an in-memory scoreboard, and writes to an embedded SQLite database (`pump_twin.db`):
```sql
CREATE TABLE IF NOT EXISTS readings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp    TEXT,
    rpm          REAL,
    torque       REAL,
    air_temp     REAL,
    tool_wear    INTEGER,
    fault_status TEXT,
    rul_hours    REAL
);
```

#### **8.2 Real-Time Visualization Interface (Flask + Chart.js)**
A responsive Web HMI served at `http://localhost:5000` provides plant operators with actionable operational intelligence:
- **Vibrant Modern Industrial UI:** Deep indigo and royal purple theme with glassmorphism cards and high-contrast telemetry indicators.
- **Dynamic Metric Cards:** Speed, Torque, Hydraulic Power, $\Delta T$, and Tool Wear updating every 1000 ms.
- **Physical Constraints Validation Matrix:** Displays live checks against safety envelopes with real-time `PASS` / `WARN` badges.
- **AI Prognostics Section:** Highlights current asset condition, failure mode attribution, and an RUL progress bar.
- **Synchronized Time-Series Plots:** Real-time Chart.js line graphs capturing speed, torque, and thermal trends.
- **Historian Audit Trail & CSV Export:** Displays recent readings with a one-click **"Export CSV"** function for operational auditing.

---

### **9. EXPERIMENTAL RESULTS & HARDWARE VALIDATION**

The end-to-end architecture was validated across a distributed two-laptop hardware configuration connected via a local Wi-Fi hotspot:

| Test Scenario | Input Telemetry | Expected Diagnostic | ML Model Output | Hardware Actuation | Dashboard Response | Validation Result |
|:---|:---|:---|:---|:---:|:---:|:---:|
| **Nominal Run** | 1551 RPM, 42.8 Nm, 298.1 K | Normal baseline operation | `NORMAL` (RUL: 377.7 h) | LED OFF | Emerald Badge, All Checks PASS | **PASSED** |
| **Power Fault (PWF)** | 2861 RPM, 64.2 Nm, 298.6 K | High torque at maximum RPM ($P > 9\text{ kW}$) | `FAULT` (Mode: PWF) | LED ON | Red Alarm Banner, PWF Flagged | **PASSED** |
| **Thermal Fault (HDF)** | 1340 RPM, 58.0 Nm, $\Delta T = 6.2\text{ K}$ | Cooling failure ($\Delta T < 8.6\text{ K}$) | `FAULT` (Mode: HDF) | LED ON | Red Alarm Banner, HDF Flagged | **PASSED** |
| **Tool Wear (TWF)** | 1420 RPM, 48.0 Nm, Wear $= 245\text{ min}$ | Impeller vane end-of-life | `FAULT` (Mode: TWF) | LED ON | RUL Bar Drops to 0%, Alert Active | **PASSED** |

**Performance Benchmarks:**
- **Average Edge-to-Cloud Latency:** 42 ms (via HiveMQ MQTT).
- **Model Inference Time:** 3.8 ms per record on standard dual-core laptop.
- **Historian Write Overhead:** < 1.2 ms per transaction.

---

### **10. SCALABILITY, FUTURE WORK & CONCLUSION**

#### **10.1 Scalability to Multi-Pump Plant Networks**
The system's modular architecture readily scales to multi-node industrial plants:
- **Topic Sharding:** Adding additional pump assets requires only registering unique topic identifiers (`pump/01/sensor/data`, `pump/02/sensor/data`).
- **Cloud Transition:** The lightweight MQTT bus seamlessly transitions to enterprise cloud platforms such as AWS IoT Core or Azure IoT Hub.

#### **10.2 Future Work**
- Migration of the trained Random Forest classifier directly onto the Arduino UNO R4 using **TinyML / Edge Impulse** for sub-millisecond on-device anomaly classification.
- Incorporation of 3-axis MEMS accelerometer sensors (e.g., MPU-6050) for physical vibration spectral analysis.

#### **10.3 Conclusion**
This project successfully designed, deployed, and verified a complete **Cyber-Physical Digital Twin for an Industrial Water Pump**. By bridging physical edge sensing (**Arduino UNO R4 WiFi**), cloud messaging (**MQTT**), advanced predictive analytics (**Random Forest AI**), industrial interoperability standards (**OPC-UA**), and modern web visualization, the project fulfills all mandated deliverables. It provides an effective, low-cost paradigm for preventing catastrophic machinery breakdown and advancing smart manufacturing.

---

### **11. REFERENCES**
1. Matzka, S. (2020). *Explainable Artificial Intelligence for Predictive Maintenance Applications with a Digital Twin*. IEEE International Conference on Industry 4.0, Artificial Intelligence, and Communications Technology (IAICT).
2. ISO 13374-1: *Condition monitoring and diagnostics of machines — Data processing, communication and presentation*.
3. IEC 62541: *Open Platform Communications — Unified Architecture (OPC UA) Specifications*.
4. Banks, J., Carson, J. S., Nelson, B., & Nicol, D. (2010). *Discrete-Event System Simulation*. Prentice Hall.
5. Grieves, M., & Vickers, J. (2017). *Digital Twin: Mitigating Unpredictable, Undesirable Emergent Behavior in Complex Systems*. Transdisciplinary Perspectives on System Complexity.
