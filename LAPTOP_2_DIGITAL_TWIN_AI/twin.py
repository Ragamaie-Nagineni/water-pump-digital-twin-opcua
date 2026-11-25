# ══════════════════════════════════════════════════════════
#  twin.py  —  Laptop 2: Digital Twin AI & Wireless Receiver
# ══════════════════════════════════════════════════════════

import json
import time
import threading
import csv
import os
from datetime import datetime
import numpy as np

import config
import database

# ─────────────────────────────────────────────
# LOAD TRAINED AI/ML MODEL BUNDLE
# ─────────────────────────────────────────────
ml_bundle = None
try:
    import joblib
    import pandas as pd
    model_file = "pump_ai_model.pkl"
    if not os.path.exists(model_file):
        model_file = os.path.join(os.path.dirname(__file__), "pump_ai_model.pkl")
    if os.path.exists(model_file):
        ml_bundle = joblib.load(model_file)
        print("=" * 65)
        print("[AI/ML ENGINE] ✅ Model loaded successfully (pump_ai_model.pkl)")
        print("               Fault Detection + Fault Classification + RUL ready.")
        print("=" * 65)
except Exception as e:
    print(f"[AI/ML ENGINE] ⚠️ Warning loading ML model: {e}")

# ─────────────────────────────────────────────
# THE LIVE DIGITAL TWIN STATE
# ─────────────────────────────────────────────
twin_state = {
    "rpm":          0.0,
    "torque":       0.0,
    "air_temp":     0.0,
    "process_temp": 0.0,
    "tool_wear":    0,
    "fault_status": "WAITING FOR ARDUINO...",
    "fault_type":   "—",
    "rul_hours":    0.0,
    "timestamp":    "—",
    "row_number":   0,
    "connected":    False
}

# Smoothed RUL using exponential moving average (alpha=0.15 = very smooth)
_rul_smoothed = None
_RUL_ALPHA    = 0.15

history = []
state_lock = threading.Lock()

def update_state(new_data):
    global history
    with state_lock:
        twin_state.update(new_data)
        twin_state['timestamp'] = datetime.now().strftime("%H:%M:%S")
        twin_state['connected'] = True

        history.append({
            'time':     twin_state['timestamp'],
            'rpm':      twin_state['rpm'],
            'torque':   twin_state['torque'],
            'air_temp': twin_state['air_temp'],
        })
        if len(history) > config.MAX_HISTORY:
            history.pop(0)

        database.save_reading(twin_state.copy())

def get_state():
    with state_lock:
        return twin_state.copy()

def get_history():
    with state_lock:
        return list(history)

# ─────────────────────────────────────────────
# PREDICT WITH AI/ML MODEL
# ─────────────────────────────────────────────
def predict_telemetry(air_temp, proc_temp, rpm, torque, tool_wear):
    """Runs physics-informed feature extraction and predicts using Random Forest models."""
    if not ml_bundle:
        return "NORMAL", "NORMAL", 350.0

    try:
        import pandas as pd
        temp_diff = proc_temp - air_temp
        power_kw = (torque * (2 * np.pi * rpm / 60)) / 1000.0
        overstrain = tool_wear * torque

        df_sample = pd.DataFrame([{
            'Air temperature [K]': air_temp,
            'Process temperature [K]': proc_temp,
            'Rotational speed [rpm]': rpm,
            'Torque [Nm]': torque,
            'Tool wear [min]': tool_wear,
            'Temp_Diff': temp_diff,
            'Power_kW': power_kw,
            'Overstrain': overstrain
        }])[ml_bundle['feature_cols']]

        is_fault = int(ml_bundle['binary_model'].predict(df_sample)[0])
        fault_status = "FAULT" if is_fault == 1 else "NORMAL"

        if is_fault == 1:
            fault_type = str(ml_bundle['mode_model'].predict(df_sample)[0])
            if fault_type == "NORMAL":
                fault_type = "Machine Fault Detected"
        else:
            fault_type = "NORMAL"

        rul = float(ml_bundle['rul_model'].predict(df_sample)[0])
        rul = max(0.0, round(rul, 1))

        # Smooth RUL so it doesn't jump up/down every row
        global _rul_smoothed
        if _rul_smoothed is None:
            _rul_smoothed = rul
        else:
            _rul_smoothed = _RUL_ALPHA * rul + (1 - _RUL_ALPHA) * _rul_smoothed
        rul = round(_rul_smoothed, 1)

        return fault_status, fault_type, rul
    except Exception as e:
        print(f"[AI ERROR] {e}")
        return "NORMAL", "NORMAL", 300.0

# ══════════════════════════════════════════════════════════
#  WIRELESS MQTT RECEIVER (Receives stream from Arduino over WiFi)
# ══════════════════════════════════════════════════════════
packet_count = 0

def start_mqtt():
    global packet_count
    try:
        import paho.mqtt.client as mqtt

        def on_connect(client, userdata, flags, rc):
            if rc == 0:
                print(f"[MQTT] ✅ Connected to broker: {config.MQTT_BROKER}:{config.MQTT_PORT}")
                client.subscribe(config.MQTT_TOPIC)
                print(f"[MQTT] 📡 Listening for Arduino telemetry on topic: '{config.MQTT_TOPIC}'")
            else:
                print(f"[MQTT] ❌ Broker connection failed (code {rc})")

        def on_message(client, userdata, msg):
            global packet_count
            try:
                data = json.loads(msg.payload.decode('utf-8'))
                packet_count += 1

                rpm       = float(data.get('rpm', 1500))
                torque    = float(data.get('torque', 40.0))
                air_temp  = float(data.get('air_temp', 298.1))
                proc_temp = float(data.get('process_temp', air_temp + 10.0))
                tool_wear = int(data.get('tool_wear', 0))

                # Run AI/ML Anomaly Detection + Classification + RUL
                fault_status, fault_type, rul = predict_telemetry(air_temp, proc_temp, rpm, torque, tool_wear)

                update_state({
                    'rpm':          rpm,
                    'torque':       torque,
                    'air_temp':     air_temp,
                    'process_temp': proc_temp,
                    'tool_wear':    tool_wear,
                    'fault_status': fault_status,
                    'fault_type':   fault_type,
                    'rul_hours':    rul,
                    'row_number':   packet_count
                })

                status_tag = f"🔴 {fault_status} ({fault_type})" if fault_status == "FAULT" else "🟢 NORMAL"
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [WIRELESS MQTT <- ARDUINO] #{packet_count:04d} | RPM: {rpm:4.0f} | Torque: {torque:4.1f} | {status_tag} | RUL: {rul} hrs")

            except Exception as e:
                print(f"[MQTT] Error parsing payload: {e}")

        client = mqtt.Client()
        if config.MQTT_USERNAME:
            client.username_pw_set(config.MQTT_USERNAME, config.MQTT_PASSWORD)
        client.on_connect = on_connect
        client.on_message = on_message

        print(f"[MQTT] Connecting to {config.MQTT_BROKER}...")
        client.connect(config.MQTT_BROKER, config.MQTT_PORT, keepalive=60)
        client.loop_forever()

    except ImportError:
        print("[MQTT] paho-mqtt not installed. Run: pip install paho-mqtt")
    except Exception as e:
        print(f"[MQTT] Connection loop error: {e}")

# ══════════════════════════════════════════════════════════
#  OFFLINE DEMO / TEST STREAM (If testing without Arduino)
# ══════════════════════════════════════════════════════════
def start_demo_mode():
    csv_file = config.DEMO_CSV
    if not os.path.exists(csv_file):
        csv_file = os.path.join(os.path.dirname(__file__), "ai4i2020.csv")

    print(f"[DEMO] 🟡 Running in Demo/Self-test mode from {csv_file}")
    row_num = 0
    try:
        with open(csv_file, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    rpm       = float(row['Rotational speed [rpm]'])
                    torque    = float(row['Torque [Nm]'])
                    air_temp  = float(row['Air temperature [K]'])
                    proc_temp = float(row['Process temperature [K]'])
                    tool_wear = int(row['Tool wear [min]'])
                    row_num  += 1

                    fault_status, fault_type, rul = predict_telemetry(air_temp, proc_temp, rpm, torque, tool_wear)

                    update_state({
                        'rpm':          rpm,
                        'torque':       torque,
                        'air_temp':     air_temp,
                        'process_temp': proc_temp,
                        'tool_wear':    tool_wear,
                        'fault_status': fault_status,
                        'fault_type':   fault_type,
                        'rul_hours':    rul,
                        'row_number':   row_num,
                    })

                    status_tag = f"🔴 {fault_status} ({fault_type})" if fault_status == "FAULT" else "🟢 NORMAL"
                    print(f"[DEMO] #{row_num:04d} | RPM: {rpm:4.0f} | Torque: {torque:4.1f} | {status_tag} | RUL: {rul} hrs")
                    time.sleep(config.DEMO_INTERVAL)

                except (ValueError, KeyError):
                    continue
    except FileNotFoundError:
        print(f"[DEMO] CSV not found at {csv_file}")

# ══════════════════════════════════════════════════════════
#  OPC-UA SERVER (Exposes Digital Twin variables via OPC-UA)
# ══════════════════════════════════════════════════════════
def start_opcua_server():
    try:
        import asyncio
        from asyncua import Server as OpcServer

        async def run_server():
            server = OpcServer()
            await server.init()
            server.set_endpoint(config.OPCUA_URL)
            server.set_server_name("Water Pump Digital Twin OPC-UA Server")

            ns = await server.register_namespace("http://waterpump.digitaltwin")
            obj = server.nodes.objects
            pump = await obj.add_object(ns, "WaterPump")

            fault_node = await pump.add_variable(ns, "FaultStatus", "NORMAL")
            rul_node   = await pump.add_variable(ns, "RUL_Hours", 400.0)
            rpm_node   = await pump.add_variable(ns, "RPM", 0.0)
            torque_node = await pump.add_variable(ns, "Torque", 0.0)

            print(f"[OPC-UA] ✅ OPC-UA Server Active at: {config.OPCUA_URL}")

            async with server:
                while True:
                    with state_lock:
                        f_stat = twin_state['fault_status']
                        f_rul  = float(twin_state['rul_hours'])
                        f_rpm  = float(twin_state['rpm'])
                        f_trq  = float(twin_state['torque'])

                    try:
                        await fault_node.write_value(f_stat)
                        await rul_node.write_value(f_rul)
                        await rpm_node.write_value(f_rpm)
                        await torque_node.write_value(f_trq)
                    except Exception:
                        pass
                    await asyncio.sleep(0.5)

        asyncio.run(run_server())
    except Exception as e:
        print(f"[OPC-UA] Server error: {e}")

def start():
    database.init_db()

    # Start data ingestion (Wireless MQTT or Demo CSV)
    if config.DEMO_MODE:
        t_data = threading.Thread(target=start_demo_mode, daemon=True)
    else:
        t_data = threading.Thread(target=start_mqtt, daemon=True)
    t_data.start()

    # Start OPC-UA server
    t_opc = threading.Thread(target=start_opcua_server, daemon=True)
    t_opc.start()
