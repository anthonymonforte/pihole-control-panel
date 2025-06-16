"""
app.py

Main Flask application entrypoint for the Pi-hole control panel.
Defines all web routes, initializes core services, and renders templates
 using the modular business logic.

Routes:
    /         : Main status page.
    /pause    : Pause blocking on all Pi-hole instances.
    /resume   : Resume blocking on all Pi-hole instances.
    /sync     : Trigger Nebula synchronization.

Functions:
    summarize_blocking_action_status: Summarize the results of blocking actions
     for UI feedback.
"""

from flask import Flask, render_template, redirect, url_for, flash, jsonify
from utils.config_loader import load_config
from pihole.manager import PiHoleManager

_config = load_config()
PIHOLE_INSTANCES = _config["PIHOLE_INSTANCES"]
FLASK_SECRET_KEY = _config["FLASK_SECRET_KEY"]
BLOCKING_DISABLE_DURATION = _config["BLOCKING_DISABLE_DURATION"]
BLOCKING_ENABLE_DURATION = _config["BLOCKING_ENABLE_DURATION"]

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

# Create the manager instance once, inject for testability
pihole_manager = PiHoleManager(PIHOLE_INSTANCES)

def summarize_blocking_action_status(results, enable):
    """
    Aggregate and summarize the results of blocking/unblocking actions for display.

    Args:
        results (list): List of (name, ok, msg) tuples from manager.
        enable (bool): True if enabling blocking, False if disabling.

    Returns:
        tuple: (success: bool, msg: str)
    """
    failed = [f"{name}: {msg}" for name, ok, msg in results if not ok]
    if failed:
        return False, "; ".join(failed)
    return True, f"{'Enabled' if enable else 'Disabled'} blocking on all Pi-holes."

def generate_instance_id(name):
    """
    Sanitize the instance/device name into a markup friendly format

    Args:
        name (string): name of the device/instance

    Returns:
        name: str
    """
    return '-'.join(name.strip().lower().split())

def get_instance_statuses():
    """
    Retrieve the current blocking status and timer for each configured Pi-hole instance.

    Returns:
        tuple:
            - List of dictionaries, each containing:
                - name (str): Human-readable device name.
                - image (str): Path to the device image.
                - id (str): Sanitized instance ID.
                - status (bool): Blocking status (True/False).
                - timer (int): Remaining seconds until status reverts (0 if none).
            - first_status (bool or None): Blocking status of the first Pi-hole instance found.
    """
    statuses = pihole_manager.get_statuses()
    devices_with_status = []
    first_status = None
    for name, device in PIHOLE_INSTANCES.items():
        status_tuple = next((s for s in statuses if s[0] == name), None)
        status_obj = status_tuple[1] if status_tuple else None
        if first_status is None:
            first_status = status_obj["blocking"]
        devices_with_status.append({
            "name": device["name"],
            "image": device["image"],
            "id": generate_instance_id(device["name"]),
            "status": status_obj["blocking"],
            "timer": int(status_obj["timer"]) if status_obj["timer"] else 0
        })

    return devices_with_status, first_status

@app.route('/')
def index():
    """
    Render the main dashboard page with the status of all Pi-hole instances.

    Returns:
        Response: Rendered HTML page.
    """
    devices_with_status, first_status = get_instance_statuses()
    return render_template('index.html', devices=devices_with_status, status=first_status)

@app.route('/pause', methods=['POST'])
def pause():
    """
    Pause (disable) blocking on all Pi-hole instances.

    Returns:
        Response: Redirect to the main page.
    """
    results = pihole_manager.set_blocking_all(enable=False,
        duration=BLOCKING_DISABLE_DURATION)
    success, msg = summarize_blocking_action_status(results, enable=False)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('index'))

@app.route('/resume', methods=['POST'])
def resume():
    """
    Resume (enable) blocking on all Pi-hole instances.

    Returns:
        Response: Redirect to the main page.
    """
    results = pihole_manager.set_blocking_all(enable=True,
        duration=BLOCKING_ENABLE_DURATION)
    success, msg = summarize_blocking_action_status(results, enable=True)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('index'))

@app.route("/api/statuses")
def api_statuses():
    """
    API endpoint that returns the blocking statuses and timers for all Pi-hole instances.

    Returns:
        flask.Response: JSON response with:
            - statuses (list): List of Pi-hole instance status dictionaries.
            - first_status (bool or None): Blocking status of the first listed instance.
    """
    devices_with_status, first_status = get_instance_statuses()
    return jsonify({
        "statuses": devices_with_status,
         "first_status": first_status
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
