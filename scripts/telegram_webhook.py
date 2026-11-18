"""
scripts/telegram_webhook.py — Administración del bot de Telegram.

Lee TELEGRAM_BOT_TOKEN y TELEGRAM_WEBHOOK_SECRET del archivo .env.

  python scripts/telegram_webhook.py info
  python scripts/telegram_webhook.py set https://ing-software-ii-forratech-proyect.onrender.com
  python scripts/telegram_webhook.py delete
  python scripts/telegram_webhook.py poll http://127.0.0.1:5000

"poll" sirve para probar en LOCAL: borra el webhook, pide los mensajes a
Telegram con getUpdates (long polling) y los entrega a tu Flask local tal
como lo haría el webhook. Al terminar las pruebas, vuelve a ejecutar "set"
con la URL de Render.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")


def api(method, payload=None, timeout=40):
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def main():
    if not TOKEN:
        sys.exit("Falta TELEGRAM_BOT_TOKEN en .env")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"

    if cmd == "info":
        print(json.dumps(api("getMe"), indent=2, ensure_ascii=False))
        print(json.dumps(api("getWebhookInfo"), indent=2, ensure_ascii=False))

    elif cmd == "set":
        base = sys.argv[2].rstrip("/")
        url = f"{base}/chat/telegram/webhook"
        print(api("setWebhook", {
            "url": url,
            "secret_token": SECRET,
            "allowed_updates": ["message", "edited_message"],
            "drop_pending_updates": True,
        }))
        print("Webhook →", url)

    elif cmd == "delete":
        print(api("deleteWebhook"))

    elif cmd == "poll":
        local = (sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:5000").rstrip("/")
        print(api("deleteWebhook"))
        print(f"Escuchando Telegram y entregando a {local} … (Ctrl+C para salir)")
        offset = 0
        while True:
            try:
                data = api("getUpdates", {"offset": offset, "timeout": 30}, timeout=40)
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    req = urllib.request.Request(
                        f"{local}/chat/telegram/webhook",
                        data=json.dumps(update).encode(),
                        headers={
                            "Content-Type": "application/json",
                            "X-Telegram-Bot-Api-Secret-Token": SECRET,
                        },
                    )
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        print("update", update["update_id"], "→", resp.read().decode())
            except KeyboardInterrupt:
                break
            except Exception as exc:
                print("Error:", exc)
                time.sleep(3)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
