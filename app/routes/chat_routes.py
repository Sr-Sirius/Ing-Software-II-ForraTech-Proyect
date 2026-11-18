# app/routes/chat_routes.py
"""
API del chat web (comunicación sincrónica) y webhook de Telegram.

  POST /chat/api/messages        → el visitante envía un mensaje
  GET  /chat/api/messages?after= → el navegador consulta mensajes nuevos
                                   (polling cada pocos segundos)
  POST /chat/telegram/webhook    → Telegram entrega las respuestas del equipo
"""

import hmac
import logging

from flask import Blueprint, current_app, jsonify, request, session

from app.services import chat_service, telegram_service

log = logging.getLogger(__name__)

chat = Blueprint("chat", __name__)

SESSION_KEY = "chat_sid"


def _current_chat():
    return chat_service.get_session(session.get(SESSION_KEY))


@chat.get("/api/messages")
def get_messages():
    chat_session = _current_chat()
    if not chat_session:
        return jsonify(session=None, messages=[])

    try:
        after = int(request.args.get("after", 0))
    except ValueError:
        after = 0

    return jsonify(
        session={
            "id": chat_service.short_id(chat_session["id"]),
            "name": chat_session["name"],
        },
        messages=chat_service.list_messages(chat_session["id"], after),
    )


@chat.post("/api/messages")
def post_message():
    # Exigir JSON obliga a los navegadores a hacer una verificación CORS
    # previa en peticiones de otros sitios: protección básica contra CSRF.
    if not request.is_json:
        return jsonify(error="Se esperaba JSON."), 415

    data = request.get_json(silent=True) or {}
    text = chat_service.clean_text(data.get("text"), chat_service.MAX_TEXT)
    name = chat_service.clean_text(data.get("name"), chat_service.MAX_NAME)

    if not text:
        return jsonify(error="El mensaje está vacío."), 400

    chat_session = _current_chat()
    is_new = chat_session is None
    if is_new:
        chat_session = chat_service.create_session(name or "Visitante")
        session[SESSION_KEY] = chat_session["id"]
        session.permanent = True

    # Límite sencillo contra abuso: 10 mensajes por minuto por sesión.
    if chat_service.recent_visitor_messages(chat_session["id"], 60) >= 10:
        return jsonify(error="Vas muy rápido. Espera un momento."), 429

    chat_service.add_message(
        chat_session["id"], "visitor", chat_session["name"], text
    )

    delivered = False
    try:
        delivered = telegram_service.forward_web_message(chat_session, text)
    except Exception as exc:
        log.warning("Telegram no disponible: %s", exc)

    if is_new:
        if delivered:
            notice = (
                "Tu mensaje llegó al equipo de ForraTech por Telegram. "
                "Te responderemos aquí mismo; deja esta ventana abierta."
            )
        else:
            notice = (
                "Tu mensaje llegó al panel de soporte del equipo. "
                "Te responderemos aquí mismo; deja esta ventana abierta."
            )
        chat_service.add_message(chat_session["id"], "system", "ForraTech", notice)

    return jsonify(ok=True, delivered=delivered), 201


@chat.post("/telegram/webhook")
def telegram_webhook():
    expected = current_app.config.get("TELEGRAM_WEBHOOK_SECRET", "")
    received = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if not expected or not hmac.compare_digest(received, expected):
        return jsonify(error="forbidden"), 403

    update = request.get_json(silent=True) or {}
    try:
        result = telegram_service.process_update(update)
    except Exception as exc:
        # Se responde 200 para que Telegram no reintente sin fin.
        log.exception("Error procesando update de Telegram: %s", exc)
        result = "error"
    return jsonify(ok=True, result=result)
