# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import requests
import subprocess
from config import PIHOLE_INSTANCES, NEBULA_SYNC_COMMAND
from dotenv import load_dotenv

import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

def get_auth_token(domain, password):
    url = f"https://{domain}/api/auth"
    payload = {"password": password}
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()

        data = response.json()
        sid = data['session']['sid']
        csrf = data['session']['csrf']

        return sid, csrf

    except Exception as e:
        print(f"Auth failed for {domain}: {e}")
        return None, None


def pihole_action(action, duration=None):

    for instance_name in PIHOLE_INSTANCES:

        print(f"{action} with duration: {duration}")
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
            if method == "post":
                headers = {
                    "X-FTL-SID": sid,
                    "X-FTL-CSRF": csrf
                }

                r = requests.post(url, headers=headers, json=payload, timeout=5)
            else:
                r = requests.get(url, timeout=5)
            r.raise_for_status()

        except Exception as e:
            return False, str(e)

    return True, f"{action} Pi-Holes successful."

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/pause', methods=['POST'])
def pause():
    success, msg = pihole_action("disable", request.form['duration'])
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('index'))


@app.route('/resume', methods=['POST'])
def resume():
    success, msg = pihole_action("enable")
    flash(msg, 'success' if success else 'danger')
    return redirect(url_for('index'))


@app.route('/sync', methods=['POST'])
def sync():
    try:
        subprocess.run(NEBULA_SYNC_COMMAND, check=True)
        flash("NebulaSync triggered.", 'success')
    except subprocess.CalledProcessError as e:
        flash(f"NebulaSync failed: {e}", 'danger')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
