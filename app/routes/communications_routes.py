# app/routes/communications_routes.py
"""
Páginas públicas del módulo de comunicaciones.

  /comunicaciones/            → centro de comunicaciones (canales + TLS)
  /comunicaciones/xmpp        → sala de chat XMPP con Converse.js
  /comunicaciones/contacto    → formulario de contacto (correo asincrónico)
  /comunicaciones/tls         → certificado TLS en vivo (JSON)
"""

import logging
import re

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from app.security import check_csrf
from app.services import mail_service, telegram_service, tls_service

log = logging.getLogger(__name__)

communications = Blueprint("communications", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@communications.get("/")
def hub():
    return render_template(
        "communications/hub.html",
        is_secure=request.is_secure,
        forwarded_proto=request.headers.get("X-Forwarded-Proto", "—"),
        hsts=(
            current_app.config.get("HSTS_MAX_AGE")
            if current_app.config.get("FORCE_HTTPS")
            else None
        ),
    )


@communications.get("/xmpp")
def xmpp():
    return render_template("communications/xmpp.html")


@communications.route("/contacto", methods=["GET", "POST"])
def contact():
    form = {"name": "", "email": "", "subject": "", "message": ""}

    if request.method == "POST":
        check_csrf()
        form = {k: (request.form.get(k) or "").strip() for k in form}

        # Campo trampa: los bots lo llenan, las personas no lo ven.
        if request.form.get("website"):
            flash("Mensaje enviado. ¡Gracias!", "success")
            return redirect(url_for("communications.contact"))

        errors = []
        if not (2 <= len(form["name"]) <= 80):
            errors.append("Escribe tu nombre.")
        if not EMAIL_RE.match(form["email"]) or len(form["email"]) > 120:
            errors.append("Escribe un correo válido.")
        if not (3 <= len(form["subject"]) <= 120):
            errors.append("Escribe un asunto (3 a 120 caracteres).")
        if not (10 <= len(form["message"]) <= 4000):
            errors.append("El mensaje debe tener entre 10 y 4000 caracteres.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            try:
                mail_service.append_contact(
                    form["name"], form["email"], form["subject"], form["message"]
                )
            except mail_service.MailNotConfigured as exc:
                flash(str(exc), "error")
            except Exception as exc:
                log.exception("Fallo IMAP APPEND: %s", exc)
                flash(
                    "No pudimos dejar tu mensaje en el buzón. "
                    "Intenta más tarde o escríbenos por Telegram.",
                    "error",
                )
            else:
                telegram_service.notify_team(
                    "📧 Nuevo correo de contacto en el buzón de soporte\n"
                    f"De: {form['name']} <{form['email']}>\n"
                    f"Asunto: {form['subject']}"
                )
                flash(
                    "Tu mensaje quedó en nuestro buzón de soporte. "
                    "Te responderemos por correo.",
                    "success",
                )
                return redirect(url_for("communications.contact"))

    return render_template("communications/contact.html", form=form)


@communications.get("/tls")
def tls_info():
    allowed = current_app.config.get("PUBLIC_HOSTS") or []
    host = request.host.split(":")[0].lower()
    if host not in allowed:
        # Evita que la ruta se use para conectarse a hosts arbitrarios.
        host = allowed[0] if allowed else None
    if not host:
        return jsonify(error="Sin hosts públicos configurados."), 404
    try:
        return jsonify(tls_service.inspect(host))
    except Exception as exc:
        return jsonify(error=f"{type(exc).__name__}: {exc}", host=host), 502
