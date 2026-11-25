# ══════════════════════════════════════════════════════════
#  app.py  —  Main entry point
#
#  Run this file to start everything:
#       python app.py
#
#  Then open your browser at:  http://localhost:5000
# ══════════════════════════════════════════════════════════

from flask import Flask, render_template, jsonify
import database
import twin
import config

app = Flask(__name__)

# ─────────────────────────────────────────────
# PAGE ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def dashboard():
    """Serve the main dashboard page"""
    return render_template('dashboard.html')


# ─────────────────────────────────────────────
# API ROUTES  (dashboard calls these every second)
# ─────────────────────────────────────────────

@app.route('/api/state')
def api_state():
    """
    Returns the current live pump state + graph history.
    The dashboard calls this every 1 second to update itself.
    """
    return jsonify({
        'state':   twin.get_state(),
        'history': twin.get_history()
    })


@app.route('/api/readings')
def api_readings():
    """Returns last 15 readings for the dashboard table"""
    return jsonify(database.get_recent(15))


# ─────────────────────────────────────────────
# START
# ─────────────────────────────────────────────

if __name__ == '__main__':
    print()
    print("=" * 58)
    print("   💧  Water Pump Digital Twin  —  Dashboard")
    print("=" * 58)
    print(f"   Mode    : {'🟡 DEMO (simulated CSV data)' if config.DEMO_MODE else '🟢 LIVE (real MQTT)'}")
    print(f"   Browser : http://localhost:{config.FLASK_PORT}")
    print(f"   OPC-UA  : {config.OPCUA_URL}")
    print("=" * 58)
    print()

    twin.start()   # starts MQTT/demo + OPC-UA in background threads

    app.run(
        host  = config.FLASK_HOST,
        port  = config.FLASK_PORT,
        debug = False,
        use_reloader = False   # important: prevents duplicate threads
    )

