# Pi-hole Control Panel

[![pylint](https://img.shields.io/github/actions/workflow/status/anthonymonforte/pihole-control-panel/pylint.yml?branch=main&label=pylint)](https://github.com/lovelaze/nebula-sync/actions/workflows/go.yml?query=branch%3Amain)
![Python](https://img.shields.io/badge/python-3.12%2B-blue?logo=python)


<img src="static/images/pi-panel-logo-off.png" alt="Pi-hole Control Panel" width="220" height="220">
<strong>A simple web UI to enable/disable blocking on one or more instances of Pi-hole (v6.xx)</strong>
<br>
<br>
<i>This project is not a part of the official Pi-hole project, but uses the api provided by the Pi-hole instance(s).</i>
<br>
<br>
<img src="static/images/UI.png" alt="Pi-hole Control Panel UI" width="250" height="324" style="border: 2px solid white; border-radius: 8px;">
<br>
## Installation

## config.py

Use `config.py.changeme` for reference.  You must have a `config.py` file in the root folder with one or more Pi-hole instances defined.

For each Pi-hole instance you may use your user/admin password as the API token or an App Password.  Create an App Password from the target Pi-hole's UI -> Web Interface / API -> App Password (_You must enable Expert mode_)

### .env

You must create a `.env` file which includes:
```
FLASK_SECRET_KEY=your secret key value
```

You can use python to generate a secret key value:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Installation
You can create and run a Docker image with:
```bash
docker compose up -d --build
```

## License

- **Code**: GPLv3 — see [LICENSE](/LICENSES/LICENSE)
- **Images**: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — see [LICENSES/images.txt](LICENSES/images.txt)
