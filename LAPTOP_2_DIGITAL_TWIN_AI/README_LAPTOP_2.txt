==============================================================
  LAPTOP 2 INSTRUCTIONS (DIGITAL TWIN & AI/ML RECEIVER)
==============================================================

WHAT THIS LAPTOP DOES:
- Has NO USB cable attached! Totally wireless.
- Receives live sensor telemetry over WiFi via MQTT from the Arduino.
- Runs the trained AI/ML model (pump_ai_model.pkl):
    * Anomaly / Fault Detection (NORMAL vs FAULT)
    * Fault Classification (PWF, HDF, TWF, OSF, RNF)
    * Remaining Useful Life (RUL in hours)
- Hosts the Digital Twin OPC-UA server.
- Hosts the Web Dashboard at http://localhost:5000 with real-time graphs.

STEPS TO RUN:
1. Make sure Laptop 2 is connected to the same WiFi / Internet as Arduino.
2. Double-click "run_laptop_2.bat"
3. Open your browser and go to:
   http://localhost:5000
4. As soon as Laptop 1 starts sending data to Arduino, this dashboard
   will start updating in real time!
==============================================================
