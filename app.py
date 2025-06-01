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

from flask import Flask, render_template, redirect, url_for, flash
try:
    from config import PIHOLE_INSTANCES, NEBULA_SYNC_COMMAND
except ImportError:
    PIHOLE_INSTANCES = None
    NEBULA_SYNC_COMMAND = None
    FLASK_SECRET_KEY = None

from pihole.manager import PiHoleManager
from services.nebula import trigger_nebula_sync

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

@app.route('/')
def index():
    """
    Render the main dashboard page with the status of all Pi-hole instances.

    Returns:
        Response: Rendered HTML page.
    """
    statuses = pihole_manager.get_statuses()
    devices_with_status = []
    first_status = None
    for name, device in PIHOLE_INSTANCES.items():
        status_tuple = next((s for s in statuses if s[0] == name), None)
        status = status_tuple[1] if status_tuple else None
        if first_status is None:
            first_status = status
        devices_with_status.append({
            "name": device["name"],
            "image": device["image"],
            "status": status
        })
    return render_template('index.html', devices=devices_with_status, status=first_status)

@app.route('/pause', methods=['POST'])
def pause():
    """
    Pause (disable) blocking on all Pi-hole instances.

    Returns:
        Response: Redirect to the main page.
    """
    results = pihole_manager.set_blocking_all(enable=False)
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
    results = pihole_manager.set_blocking_all(enable=True)
    success, msg = summarize_blocking_action_status(results, enable=True)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('index'))

@app.route('/sync', methods=['POST'])
def sync():
    """
    Trigger Nebula synchronization.

    Returns:
        Response: Redirect to the main page.
    """
    success, msg = trigger_nebula_sync(NEBULA_SYNC_COMMAND)
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
