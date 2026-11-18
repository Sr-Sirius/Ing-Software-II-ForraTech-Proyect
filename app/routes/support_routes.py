# app/routes/support_routes.py
"""
Panel interno del equipo de soporte (protegido con ADMIN_PASSWORD).

  /soporte/login                  → acceso del equipo
  /soporte/chats                  → conversaciones del chat web (responder)
  /soporte/bandeja                → bandeja del buzón por IMAP
  /soporte/bandeja/<uid>          → lectura de un mensaje (IMAP FETCH)
  /soporte/bandeja/<uid>/estado   → marcar leído / respondido (IMAP STORE)
  /soporte/pop3                   → la misma bandeja vista por POP3
  /soporte/telegram               → estado del bot y registro del webhook
  /soporte/diagnostico            → prueba de puertos desde el servidor
"""

import functools
import hmac
import logging

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.security import check_csrf
from app.services import chat_service, mail_service, telegram_service

log = logging.getLogger(__name__)

support = Blueprint("support", __name__)


def admin_required(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("is_support_admin"):
            return redirect(url_for("support.login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


@support.route("/login", methods=["GET", "POST"])
def login():
    configured = bool(current_app.config.get("ADMIN_PASSWORD"))
    if request.method == "POST":
        check_csrf()
        password = request.form.get("password", "")
        if configured and hmac.compare_digest(
            password, current_app.config["ADMIN_PASSWORD"]
        ):
            session.clear()
            session["is_support_admin"] = True
            target = request.args.get("next", "")
            if not target.startswith("/soporte"):
                target = url_for("support.inbox")
            return redirect(target)
        flash("Contraseña incorrecta.", "error")
    return render_template("support/login.html", configured=configured)


@support.post("/logout")
def logout():
    check_csrf()
    session.pop("is_support_admin", None)
    return redirect(url_for("communications.hub"))


@support.get("/")
@admin_required
def index():
    return redirect(url_for("support.inbox"))


@support.get("/bandeja")
@admin_required
def inbox():
    data, error = None, None
    try:
        data = mail_service.list_inbox()
    except Exception as exc:
        log.warning("IMAP: %s", exc)
        error = f"{type(exc).__name__}: {exc}"
    return render_template("support/inbox.html", data=data, error=error)


@support.get("/bandeja/<uid>")
@admin_required
def message(uid):
    try:
        msg = mail_service.read_message(uid)
    except Exception as exc:
        flash(f"No se pudo leer el mensaje: {exc}", "error")
        return redirect(url_for("support.inbox"))
    return render_template("support/message.html", msg=msg)


@support.post("/bandeja/<uid>/estado")
@admin_required
def message_flags(uid):
    check_csrf()
    action = request.form.get("action", "")
    try:
        log_lines = mail_service.update_flags(uid, action)
        flash("Estado actualizado: " + log_lines[-2], "success")
    except Exception as exc:
        flash(f"No se pudo actualizar: {exc}", "error")
    if request.form.get("back") == "inbox":
        return redirect(url_for("support.inbox"))
    return redirect(url_for("support.message", uid=uid))


@support.get("/pop3")
@admin_required
def pop3():
    data, error = None, None
    try:
        data = mail_service.pop3_summary()
    except Exception as exc:
        log.warning("POP3: %s", exc)
        error = f"{type(exc).__name__}: {exc}"
    return render_template("support/pop3.html", data=data, error=error)


@support.route("/telegram", methods=["GET", "POST"])
@admin_required
def telegram():
    cfg = current_app.config
    webhook_url = url_for("chat.telegram_webhook", _external=True, _scheme="https")

    if request.method == "POST":
        check_csrf()
        try:
            telegram_service.set_webhook(webhook_url, cfg["TELEGRAM_WEBHOOK_SECRET"])
            flash("Webhook registrado en Telegram.", "success")
        except Exception as exc:
            flash(f"No se pudo registrar el webhook: {exc}", "error")
        return redirect(url_for("support.telegram"))

    bot, info, error = None, None, None
    if telegram_service.is_configured():
        try:
            bot = telegram_service.bot_info()
            info = telegram_service.webhook_info()
        except Exception as exc:
            error = str(exc)
    return render_template(
        "support/telegram.html",
        bot=bot,
        info=info,
        error=error,
        webhook_url=webhook_url,
        team_chat_id=cfg.get("TELEGRAM_TEAM_CHAT_ID"),
        has_secret=bool(cfg.get("TELEGRAM_WEBHOOK_SECRET")),
    )


@support.get("/diagnostico")
@admin_required
def diagnostics():
    cfg = current_app.config
    checks = [
        ("Correo IMAP (TLS implícito)", cfg["IMAP_HOST"], cfg["IMAP_PORT"]),
        ("Correo POP3 (TLS implícito)", cfg["POP3_HOST"], cfg["POP3_PORT"]),
        ("SMTP envío (STARTTLS)", "smtp.gmail.com", 587),
        ("SMTP envío (TLS implícito)", "smtp.gmail.com", 465),
        ("SMTP retransmisión", "smtp.gmail.com", 25),
        ("Bot API de Telegram (HTTPS)", "api.telegram.org", 443),
        ("Servidor XMPP / BOSH (HTTPS)", "conversejs.org", 443),
        ("Servidor XMPP cliente-servidor", "conversejs.org", 5222),
    ]
    results = []
    for label, host, port in checks:
        result = mail_service.port_check(host, port)
        result["label"] = label
        results.append(result)

    request_info = {
        "Esquema visto por Flask": request.scheme,
        "X-Forwarded-Proto": request.headers.get("X-Forwarded-Proto", "—"),
        "Host": request.host,
        "IP del cliente (X-Forwarded-For)": request.remote_addr,
        "Servidor en Render": "sí" if cfg.get("ON_RENDER") else "no (local)",
    }
    return render_template(
        "support/diagnostics.html", results=results, request_info=request_info
    )


# ─────────────────────────────────────────────
# Chats web: el equipo responde desde el navegador
# (canal alterno cuando Telegram no está configurado)
# ─────────────────────────────────────────────
@support.get("/chats")
@admin_required
def chats():
    return render_template("support/chats.html", sessions=chat_service.list_sessions())


@support.route("/chats/<sid>", methods=["GET", "POST"])
@admin_required
def chat_detail(sid):
    chat_session = chat_service.get_session(sid)
    if not chat_session:
        abort(404)
    if request.method == "POST":
        check_csrf()
        text = chat_service.clean_text(request.form.get("text"), chat_service.MAX_TEXT)
        author = chat_service.clean_text(request.form.get("author"), 40) or "Soporte"
        if text:
            chat_service.add_message(sid, "agent", author, text, channel="panel")
            session["support_author"] = author
        if request.headers.get("X-Requested-With") == "fetch":
            return jsonify(ok=True)
        return redirect(url_for("support.chat_detail", sid=sid))
    return render_template(
        "support/chat_detail.html",
        chat=chat_session,
        short_id=chat_service.short_id(sid),
        author=session.get("support_author", ""),
    )


@support.get("/chats/<sid>/mensajes")
@admin_required
def chat_messages(sid):
    if not chat_service.get_session(sid):
        abort(404)
    try:
        after = int(request.args.get("after", 0))
    except ValueError:
        after = 0
    return jsonify(messages=chat_service.list_messages(sid, after))
