# app/services/telegram_service.py
"""
Integración móvil con Telegram (comunicación sincrónica).

Flujo:
  Chat web (JS) ──POST──> Flask ──HTTPS 443──> Bot API ──> grupo del equipo
  Grupo (respuesta) ──webhook HTTPS──> Flask ──> SQLite ──polling──> chat web

  Productor en Telegram ──> bot ──webhook──> Flask ──> grupo del equipo
  Grupo (respuesta) ──> Flask ──> bot ──> chat privado del productor

Todo viaja por HTTPS (puerto 443), que el plan gratuito de Render permite.
Se usa solo la librería estándar (urllib), sin dependencias nuevas.
"""

import json
import logging
import urllib.error
import urllib.request

from flask import current_app

from app.services import chat_service

log = logging.getLogger(__name__)

API_URL = "https://api.telegram.org/bot{token}/{method}"


# ─────────────────────────────────────────────
# Llamadas a la Bot API
# ─────────────────────────────────────────────
def is_configured():
    return bool(current_app.config.get("TELEGRAM_BOT_TOKEN"))


def team_chat_id():
    value = current_app.config.get("TELEGRAM_TEAM_CHAT_ID", "")
    return value.strip() or None


def call(method, payload=None, token=None, timeout=10):
    token = token or current_app.config.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN no está configurado.")

    data = json.dumps(payload or {}).encode("utf-8")
    req = urllib.request.Request(
        API_URL.format(token=token, method=method),
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = json.loads(exc.read().decode("utf-8") or "{}")
    if not body.get("ok"):
        raise RuntimeError(body.get("description", "Error de Telegram"))
    return body.get("result")


def send_message(chat_id, text, reply_to=None):
    payload = {
        "chat_id": chat_id,
        "text": text[:4000],
        "disable_web_page_preview": True,
    }
    if reply_to:
        payload["reply_parameters"] = {
            "message_id": reply_to,
            "allow_sending_without_reply": True,
        }
    return call("sendMessage", payload)


# ─────────────────────────────────────────────
# Mensajes hacia el equipo
# ─────────────────────────────────────────────
def forward_web_message(session, text):
    """Publica en el grupo del equipo un mensaje del chat web."""
    chat_id = team_chat_id()
    if not (is_configured() and chat_id):
        return False
    body = (
        f"💬 Chat web · sesión #{chat_service.short_id(session['id'])}\n"
        f"👤 {session['name']}\n\n{text}\n\n"
        "↩️ Responde a ESTE mensaje para contestarle en la página."
    )
    result = send_message(chat_id, body)
    chat_service.save_link(result["message_id"], "web", session["id"])
    return True


def notify_team(text):
    """Aviso simple al grupo (por ejemplo, un correo de contacto nuevo)."""
    chat_id = team_chat_id()
    if not (is_configured() and chat_id):
        return False
    try:
        send_message(chat_id, text)
        return True
    except Exception as exc:  # el aviso nunca debe romper la petición
        log.warning("No se pudo notificar a Telegram: %s", exc)
        return False


# ─────────────────────────────────────────────
# Procesamiento de actualizaciones (webhook)
# ─────────────────────────────────────────────
def _help_text():
    cfg = current_app.config
    web = (cfg.get("PUBLIC_HOSTS") or [""])[0]
    lines = [
        "🌱 ForraTech · Soporte",
        "",
        "Escribe tu pregunta aquí y un integrante del equipo te responderá "
        "en este mismo chat.",
        "",
        "Comandos:",
        "/ayuda – ver este mensaje",
        "/web – enlace a la plataforma",
        "/xmpp – sala de chat XMPP",
        "/correo – correo de soporte (respuesta asincrónica)",
    ]
    if web:
        lines += ["", f"🌐 https://{web}"]
    return "\n".join(lines)


def _sender_name(message):
    user = message.get("from") or {}
    name = " ".join(
        p for p in [user.get("first_name"), user.get("last_name")] if p
    )
    return name or user.get("username") or "Usuario"


def _command(text):
    if not text.startswith("/"):
        return None
    # "/start@MiBot argumento" → "start"
    return text.split()[0][1:].split("@")[0].lower()


def process_update(update):
    """Procesa un Update de Telegram. Devuelve una descripción breve."""
    message = update.get("message") or update.get("edited_message")
    if not message:
        return "ignorado"

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    text = (message.get("text") or "").strip()
    command = _command(text)

    # /id funciona en cualquier chat: sirve para obtener TELEGRAM_TEAM_CHAT_ID
    if command == "id":
        send_message(chat_id, f"ID de este chat: {chat_id}")
        return "id"

    team = team_chat_id()

    # ── Mensajes en el grupo del equipo ─────────────────
    if team and str(chat_id) == str(team):
        reply = message.get("reply_to_message")
        if not reply or not text or command:
            if command in {"ayuda", "help", "start"}:
                send_message(
                    chat_id,
                    "Responde (reply) a un mensaje del bot para contestar al "
                    "usuario por el mismo canal en el que escribió.",
                )
            return "grupo-sin-respuesta"

        link = chat_service.find_link(reply["message_id"])
        if not link:
            send_message(
                chat_id,
                "⚠️ No encontré esa conversación. Es posible que el servidor "
                "se haya reiniciado (el disco de Render gratuito es efímero).",
                reply_to=message["message_id"],
            )
            return "enlace-no-encontrado"

        agent = _sender_name(message)
        if link["kind"] == "web":
            chat_service.add_message(
                link["target"], "agent", agent, text, channel="telegram"
            )
        else:
            send_message(int(link["target"]), f"👩‍🌾 {agent} (ForraTech):\n{text}")
        return f"respuesta-{link['kind']}"

    # ── Chat privado con el bot (productor desde el celular) ──
    if chat.get("type") == "private":
        cfg = current_app.config
        if command in {"start", "ayuda", "help"}:
            send_message(chat_id, _help_text())
            return "ayuda"
        if command == "web":
            hosts = cfg.get("PUBLIC_HOSTS") or []
            send_message(chat_id, f"🌐 https://{hosts[0]}" if hosts else "—")
            return "web"
        if command == "xmpp":
            send_message(
                chat_id,
                f"💬 Sala XMPP: {cfg.get('XMPP_ROOM')}\n"
                "Puedes entrar con apps como Conversations (Android), "
                "Monal (iOS) o Gajim (PC).",
            )
            return "xmpp"
        if command == "correo":
            mail = cfg.get("MAIL_ADDRESS") or "no configurado"
            send_message(chat_id, f"📧 Soporte por correo: {mail}")
            return "correo"
        if not text:
            send_message(chat_id, "Por ahora solo puedo reenviar texto.")
            return "no-texto"

        if not team:
            send_message(chat_id, "El canal de soporte aún no está configurado.")
            return "sin-grupo"

        username = (message.get("from") or {}).get("username")
        who = _sender_name(message) + (f" (@{username})" if username else "")
        result = send_message(
            team,
            f"📱 Telegram · {who}\n\n{text}\n\n"
            "↩️ Responde a ESTE mensaje para contestarle por Telegram.",
        )
        chat_service.save_link(result["message_id"], "telegram", chat_id)
        send_message(chat_id, "✅ Recibido. El equipo te responderá aquí.")
        return "reenviado"

    return "ignorado"


# ─────────────────────────────────────────────
# Administración del webhook
# ─────────────────────────────────────────────
def set_webhook(url, secret):
    return call(
        "setWebhook",
        {
            "url": url,
            "secret_token": secret,
            "allowed_updates": ["message", "edited_message"],
            "drop_pending_updates": True,
        },
    )


def webhook_info():
    return call("getWebhookInfo")


def bot_info():
    return call("getMe")
