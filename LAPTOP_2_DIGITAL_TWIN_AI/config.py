# ══════════════════════════════════════════════════════════
#  config.py  —  Laptop 2: Digital Twin & AI Settings
# ══════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# DEMO_MODE:
# False = LIVE WIRELESS MQTT MODE (Receives from Arduino over WiFi)
# True  = Offline Self-Test Mode (Simulates stream from CSV for testing)
# ─────────────────────────────────────────────
DEMO_MODE     = False
DEMO_CSV      = "ai4i2020.csv"
DEMO_INTERVAL = 1.0

# ─────────────────────────────────────────────
# MQTT Settings (Matches Arduino's MQTT Publisher)
# ─────────────────────────────────────────────
MQTT_BROKER   = "broker.hivemq.com"   # Free public MQTT broker (zero setup)
MQTT_PORT     = 1883
MQTT_TOPIC    = "pump/sensor/data"
MQTT_USERNAME = ""
MQTT_PASSWORD = ""

# ─────────────────────────────────────────────
# OPC-UA Server
# ─────────────────────────────────────────────
OPCUA_URL     = "opc.tcp://0.0.0.0:4840/pump/twin/"

# ─────────────────────────────────────────────
# Flask Web Dashboard
# ─────────────────────────────────────────────
FLASK_HOST    = "0.0.0.0"
FLASK_PORT    = 5000

# ─────────────────────────────────────────────
# Database & Graphs
# ─────────────────────────────────────────────
DB_FILE       = "pump_twin.db"
MAX_HISTORY   = 60
