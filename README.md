# Pi-Hole Control Panel
A simple service and UI to control one or more instances of Pi-Hole

## Configuration

### config.py

Use `config.py.changeme` for reference.  You must have a `config.py` file in the root folder with one or more Pi-Hole instances defined.

### .env file

You must create a `.env` file which includes:
---
FLASK_SECRET_KEY=your secret key value
---

You can use python to generate a secret key value:
---
python3 -c "import secrets; print(secrets.token_hex(32))"
---

## License

- **Code**: GPLv3 — see [LICENSE](/LICENSES/LICENSE)
- **Images**: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) — see [LICENSES/images.txt](LICENSES/images.txt)
