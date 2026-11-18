# app/security.py
"""
Capa de seguridad HTTP de ForraTech.

Render termina la conexión TLS en su balanceador y reenvía la petición a
Gunicorn por HTTP interno, agregando la cabecera X-Forwarded-Proto. Por eso:

1. ProxyFix hace que Flask "vea" el esquema real (https).
2. Si alguien llega por http, se le redirige a https (Render ya lo hace;
   esto es una segunda línea de defensa).
3. Se agregan cabeceras de seguridad, entre ellas HSTS, que obliga al
   navegador a usar siempre TLS con este dominio.
4. Se ofrece un token CSRF para los formularios propios.
"""

import hmac
import secrets

from flask import abort, redirect, request, session
from werkzeug.middleware.proxy_fix import ProxyFix


# Orígenes externos usados por Converse.js (cliente XMPP en el navegador).
CONVERSE_CDN = "https://cdn.conversejs.org"
CONVERSE_SERVER = "https://conversejs.org"


def build_csp():
    directives = {
        "default-src": ["'self'"],
        # 'unsafe-inline' se mantiene porque las plantillas existentes
        # usan scripts y estilos en línea.
        "script-src": ["'self'", "'unsafe-inline'", CONVERSE_CDN],
        "style-src": ["'self'", "'unsafe-inline'", CONVERSE_CDN],
        "img-src": ["'self'", "data:", "blob:", "https:"],
        "font-src": ["'self'", "data:", CONVERSE_CDN],
        "connect-src": [
            "'self'",
            CONVERSE_CDN,
            CONVERSE_SERVER,
            "wss://conversejs.org",
        ],
        "media-src": ["'self'", "blob:", "https:"],
        "worker-src": ["'self'", "blob:"],
        "frame-ancestors": ["'none'"],
        "base-uri": ["'self'"],
        "form-action": ["'self'"],
        "object-src": ["'none'"],
    }
    policy = "; ".join(f"{k} {' '.join(v)}" for k, v in directives.items())
    return policy + "; upgrade-insecure-requests"


def init_security(app):
    # Confía en una capa de proxy (el balanceador de Render).
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    csp = build_csp()

    @app.before_request
    def enforce_https():
        if not app.config.get("FORCE_HTTPS"):
            return None
        # Solo se redirige cuando el proxy indica que la petición original
        # fue http. Las comprobaciones internas de Render no traen la cabecera.
        forwarded = request.headers.get("X-Forwarded-Proto", "")
        if forwarded.lower() == "http":
            return redirect(request.url.replace("http://", "https://", 1), 301)
        return None

    @app.after_request
    def security_headers(response):
        headers = response.headers

        # HSTS solo en producción (FORCE_HTTPS): en local evitaría volver a
        # usar http://localhost durante un año en ese navegador.
        if request.is_secure and app.config.get("FORCE_HTTPS"):
            headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={app.config['HSTS_MAX_AGE']}; includeSubDomains",
            )

        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=(), payment=()",
        )
        headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")

        if app.config.get("CSP_ENABLED"):
            headers.setdefault("Content-Security-Policy", csp)

        # Las respuestas de la API de chat y del panel no deben guardarse
        # en caché de proxies intermedios.
        if request.path.startswith(("/chat/api", "/soporte")):
            headers["Cache-Control"] = "no-store"

        return response

    app.jinja_env.globals["csrf_token"] = get_csrf_token


# ─────────────────────────────────────────────
# CSRF para formularios
# ─────────────────────────────────────────────
def get_csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token


def check_csrf():
    sent = request.form.get("csrf_token", "")
    expected = session.get("_csrf", "")
    if not expected or not hmac.compare_digest(sent, expected):
        abort(400, description="Token CSRF inválido. Recarga la página.")
