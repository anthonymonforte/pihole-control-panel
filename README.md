# Pi-hole Control Panel

![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)


<img src="static/images/pi-panel-logo-off.png" alt="Pi-hole Control Panel" width="220" height="220">
<strong>A simple web UI to enable/disable blocking on one or more instances of Pi-hole</strong>
<br>
<br>
<i>This project is not a part of the official Pi-hole project, but uses the api provided by the Pi-hole instances.</i>
<br>

## Configuration

## config.py

Use `config.py.changeme` for reference.  You must have a `config.py` file in the root folder with one or more Pi-hole instances defined.

Each Pi-hole instance must also contain an API token which is obtained from the target Pi-hole's UI -> Web Interface / API -> App Password
- _You must enable Expert mode_

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
