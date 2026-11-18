# app/settings.py
"""
Configuración leída desde variables de entorno.

En local los valores vienen del archivo .env (ver .env.example).
En Render se definen en: Dashboard → servicio → Environment.

Ningún secreto (contraseñas, tokens, claves) debe escribirse en el código.
"""

import os
import secrets


def _bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


def _int(name, default=None):
    value = os.environ.get(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def load_dotenv_if_available():
    """Carga .env en desarrollo. En Render no existe .env y no pasa nada."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def apply_settings(app):
    """Copia la configuración del entorno a app.config."""
    # Render define la variable RENDER=true en todos sus servicios.
    on_render = _bool("RENDER", False)
    production = _bool("PRODUCTION", on_render)

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        if production:
            raise RuntimeError(
                "Falta la variable de entorno SECRET_KEY en producción."
            )
        # Solo para desarrollo local: cambia en cada arranque.
        secret_key = secrets.token_hex(32)
        app.logger.warning("SECRET_KEY no definida: usando una temporal.")

    app.config.update(
        SECRET_KEY=secret_key,
        PRODUCTION=production,
        ON_RENDER=on_render,

        # ── Cookies de sesión ──────────────────────────────
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,

        # ── TLS / cabeceras ────────────────────────────────
        FORCE_HTTPS=_bool("FORCE_HTTPS", production),
        HSTS_MAX_AGE=_int("HSTS_MAX_AGE", 31536000),
        CSP_ENABLED=_bool("CSP_ENABLED", True),
        # Hosts públicos que se pueden inspeccionar en /comunicaciones/tls
        PUBLIC_HOSTS=[
            h.strip().lower()
            for h in os.environ.get(
                "PUBLIC_HOSTS",
                "ing-software-ii-forratech-proyect.onrender.com",
            ).split(",")
            if h.strip()
        ],

        # ── Panel de soporte (bandeja de correo) ───────────
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", ""),

        # ── Telegram (mensajería sincrónica móvil) ─────────
        TELEGRAM_BOT_TOKEN=os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        TELEGRAM_BOT_USERNAME=os.environ.get(
            "TELEGRAM_BOT_USERNAME", ""
        ).lstrip("@"),
        TELEGRAM_TEAM_CHAT_ID=os.environ.get("TELEGRAM_TEAM_CHAT_ID", ""),
        TELEGRAM_WEBHOOK_SECRET=os.environ.get("TELEGRAM_WEBHOOK_SECRET", ""),

        # ── XMPP (Converse.js) ─────────────────────────────
        XMPP_DOMAIN=os.environ.get("XMPP_DOMAIN", "conversejs.org"),
        XMPP_BOSH_URL=os.environ.get(
            "XMPP_BOSH_URL", "https://conversejs.org/http-bind/"
        ),
        XMPP_ROOM=os.environ.get(
            "XMPP_ROOM", "forratech-soporte@conference.conversejs.org"
        ),

        # ── Correo (mensajería asincrónica) ────────────────
        MAIL_ADDRESS=os.environ.get("MAIL_ADDRESS", ""),
        MAIL_APP_PASSWORD=os.environ.get("MAIL_APP_PASSWORD", ""),
        IMAP_HOST=os.environ.get("IMAP_HOST", "imap.gmail.com"),
        IMAP_PORT=_int("IMAP_PORT", 993),
        POP3_HOST=os.environ.get("POP3_HOST", "pop.gmail.com"),
        POP3_PORT=_int("POP3_PORT", 995),
    )


def public_settings(app):
    """Valores no secretos que las plantillas pueden mostrar."""
    cfg = app.config
    username = cfg.get("TELEGRAM_BOT_USERNAME")
    return {
        "telegram_bot_username": username,
        "telegram_bot_url": f"https://t.me/{username}" if username else "",
        "telegram_enabled": bool(cfg.get("TELEGRAM_BOT_TOKEN")),
        "support_email": cfg.get("MAIL_ADDRESS", ""),
        "xmpp_room": cfg.get("XMPP_ROOM", ""),
        "xmpp_domain": cfg.get("XMPP_DOMAIN", ""),
        "xmpp_bosh_url": cfg.get("XMPP_BOSH_URL", ""),
    }
