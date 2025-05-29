"""
This module provides auth and blocking pause/resume/status functions for across multiple
instances Pi-hole using the Pi-Hole API.
"""


import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
import os

from dotenv import load_dotenv

from flask import Flask, render_template, redirect, url_for, flash
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
try:
    from config import PIHOLE_INSTANCES, NEBULA_SYNC_COMMAND
except ImportError:
    PIHOLE_INSTANCES = None
    NEBULA_SYNC_COMMAND = None

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

def get_retrying_session(
    retries=3,
    backoff_factor=0.5):
    """Gets a HTTP session with a retry policy"""

    status_forcelist=(500, 502, 503, 504, 400)
    allowed_methods=["GET", "POST"]

    retry = Retry(
        total=retries,
        backoff_factor=backoff_factor,  # 0.5s, then 1s, then 2s
        status_forcelist=status_forcelist,
        allowed_methods=allowed_methods,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    return session

def get_auth_token(domain, password):
    """Obtains an auth token from a Pi-Hole instance using the App Password"""

    url = f"https://{domain}/api/auth"
    payload = {"password": password}
    try:
        with get_retrying_session() as session:
            response = session.post(url, json=payload, timeout=5)
            response.raise_for_status()

            data = response.json()
            sid = data['session']['sid']
            csrf = data['session']['csrf']

            return sid, csrf

    except requests.RequestException as e:
        print(f"Auth failed for {domain}: {e}")
        return None, None

def get_pihole_status(target):
    """Gets the blocking status for a Pi-Hole instance"""

    if target not in PIHOLE_INSTANCES:
        return None

    instance = PIHOLE_INSTANCES[target]
    url = f"http://{instance['domain']}/api/dns/blocking"  # Pi-hole v6 blocking status endpoint

    try:
        with get_retrying_session() as session:
            domain = instance["domain"]
            sid, csrf = get_auth_token(domain, instance['token'])

            headers = {
                    "X-FTL-SID": sid,
                    "X-FTL-CSRF": csrf
            }

            r = session.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()

            session.delete(f"https://{domain}/api/auth", headers=headers)

            return data.get("blocking", None), target

    except requests.RequestException as e:
        print(f"Error getting status for {target}: {e}")
        return None, None

def update_pihole_blocking(action, duration=None):
    """Updates the blocking behavior for all Pi-Hole instances"""

    results = []

    with ThreadPoolExecutor(max_workers=min(10, len(PIHOLE_INSTANCES))) as executor:
        future_to_device = {
            executor.submit(update_pihole_instance_blocking, d, action, duration):
               d for d in PIHOLE_INSTANCES
            }

        for future in as_completed(future_to_device):
            result = future.result()
            results.append(result)


    return summarize_blocking_action_status(results)

def update_pihole_instance_blocking(instance_name, action, duration=None):
    """Updates the blocking behavior for a single Pi-Hole instance"""

    instance = PIHOLE_INSTANCES[instance_name]

    domain = instance['domain']
    sid, csrf = get_auth_token(domain, instance['token'])

    if action == "disable":
        url = f"https://{domain}/api/dns/blocking/?blocking=false"
        method = "post"
        payload = {
            "blocking": False
        }
    elif action == "enable":
        url = f"https://{domain}/api/dns/blocking/?blocking=true"
        method = "post"
        payload = {
            "blocking": True,
            "timer": duration
        }
    else:
        return False, "Invalid action"

    try:
        with get_retrying_session() as session:

            headers = {
                "X-FTL-SID": sid,
                "X-FTL-CSRF": csrf
            }

            if method == "post":
                r = session.post(url, headers=headers, json=payload, timeout=5)
            else:
                r = session.get(url, timeout=5)
            r.raise_for_status()

            session.delete(f"https://{domain}/api/auth", headers=headers)

    except requests.RequestException as e:
        return False, str(e)

    return True, f"{action} Pi-Holes successful."

def get_all_device_statuses(devices=PIHOLE_INSTANCES):
    """Gets the blocking status for all Pi-Hole instances"""

    results = []

    with ThreadPoolExecutor(max_workers=min(10, len(devices))) as executor:
        future_to_device = {executor.submit(get_pihole_status, d): d for d in devices}

        for future in as_completed(future_to_device):
            result = future.result()
            results.append(result)

    return results

def summarize_blocking_action_status(action_result):
    """Aggregates the tuple responses from update_pihole_blocking(...)"""

    false_messages = [msg for ok, msg in action_result if not ok]

    if false_messages:
        return (False, ", ".join(false_messages))

    if action_result:
        return (True, action_result[0][1])

    return (True, "")

@app.route('/')
def index():
    """Main page route"""
    first_status = None

    device_statuses = get_all_device_statuses()
    devices_with_status = []

    for instance in PIHOLE_INSTANCES:

        device = PIHOLE_INSTANCES[instance]
        status = next((s for s in device_statuses if s[1] == instance), None)[0]

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
    """Pause blocking route"""
    # success, msg = pihole_action("disable", request.form['duration'])
    success, msg = update_pihole_blocking("disable", "")
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('index'))


@app.route('/resume', methods=['POST'])
def resume():
    """Resume blocking route"""
    success, msg = update_pihole_blocking("enable")
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('index'))


@app.route('/sync', methods=['POST'])
def sync():
    """Trigger Nebula sync route"""
    try:
        subprocess.run(NEBULA_SYNC_COMMAND, check=True)
        flash("NebulaSync triggered.", 'success')
    except subprocess.CalledProcessError as e:
        flash(f"NebulaSync failed: {e}", 'danger')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
