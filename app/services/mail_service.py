# app/services/mail_service.py
"""
Mensajería asincrónica por correo: IMAP y POP3 sobre TLS.

Restricción del plan gratuito de Render: bloquea la salida a los puertos
SMTP 25, 465 y 587. Por eso ForraTech NO envía correo por SMTP desde el
servidor. En su lugar:

  • Formulario de contacto → IMAP APPEND (puerto 993): el mensaje se
    deposita directamente en la bandeja del buzón de soporte.
  • Bandeja de soporte → IMAP SEARCH / FETCH / STORE (puerto 993):
    listar, leer y marcar mensajes (\\Seen, \\Answered, \\Flagged).
  • Vista POP3 → STAT / LIST / TOP (puerto 995): descarga de encabezados
    con el protocolo POP3, para compararlo con IMAP.
  • Las respuestas se envían desde el cliente de correo del equipo
    (enlace mailto:), y luego se marca el mensaje como \\Answered.

Cada operación devuelve una bitácora ("log") con los comandos de
protocolo ejecutados, sin contraseñas, para usarla como evidencia.
"""

import email
import email.utils
import imaplib
import poplib
import re
import socket
import ssl
import time
from email.header import decode_header, make_header
from email.message import EmailMessage

from flask import current_app


class MailNotConfigured(RuntimeError):
    pass


def _cfg():
    cfg = current_app.config
    if not (cfg.get("MAIL_ADDRESS") and cfg.get("MAIL_APP_PASSWORD")):
        raise MailNotConfigured(
            "Configura MAIL_ADDRESS y MAIL_APP_PASSWORD en las variables de entorno."
        )
    return cfg


def _tls_context():
    # Contexto TLS por defecto: valida el certificado del servidor de correo.
    return ssl.create_default_context()


def decode(value):
    if not value:
        return ""
    try:
        return str(make_header(decode_header(value)))
    except Exception:
        return str(value)


def _tls_details(sock):
    """Versión TLS, cifrado y emisor del certificado del servidor."""
    try:
        cert = sock.getpeercert() or {}
        issuer = dict(x[0] for x in cert.get("issuer", []))
        return {
            "version": sock.version(),
            "cipher": (sock.cipher() or ("",))[0],
            "issuer": issuer.get("organizationName") or issuer.get("commonName", ""),
            "valid_until": cert.get("notAfter", ""),
        }
    except Exception:
        return {}


# ─────────────────────────────────────────────
# IMAP
# ─────────────────────────────────────────────
class ImapSession:
    """Conexión IMAP con bitácora de comandos."""

    def __init__(self):
        cfg = _cfg()
        self.log = []
        self.address = cfg["MAIL_ADDRESS"]
        host, port = cfg["IMAP_HOST"], cfg["IMAP_PORT"]
        self._step(f"Conexión TCP + TLS a {host}:{port}")
        self.conn = imaplib.IMAP4_SSL(
            host, port, ssl_context=_tls_context(), timeout=15
        )
        self.tls = _tls_details(self.conn.sock)
        self._step(
            f"TLS establecido: {self.tls.get('version')} · {self.tls.get('cipher')}"
        )
        self._step(f"LOGIN {self.address} ********")
        self.conn.login(self.address, cfg["MAIL_APP_PASSWORD"])

    def _step(self, text):
        self.log.append(text)

    def cmd(self, label, func, *args):
        self._step(label)
        typ, data = func(*args)
        if typ != "OK":
            raise RuntimeError(f"{label} → {typ}")
        return data

    def close(self):
        try:
            self._step("LOGOUT")
            self.conn.logout()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


FLAG_RE = re.compile(rb"FLAGS \(([^)]*)\)")
UID_RE = re.compile(rb"UID (\d+)")
SIZE_RE = re.compile(rb"RFC822\.SIZE (\d+)")


def _parse_flags(meta):
    match = FLAG_RE.search(meta)
    return match.group(1).decode().split() if match else []


def build_contact_message(to_addr, name, sender_email, subject, body):
    msg = EmailMessage()
    msg["From"] = email.utils.formataddr((f"{name} (vía web)", sender_email))
    msg["Reply-To"] = sender_email
    msg["To"] = to_addr
    msg["Subject"] = f"[Contacto ForraTech] {subject}"
    msg["Date"] = email.utils.formatdate(localtime=True)
    msg["Message-ID"] = email.utils.make_msgid(domain="forratech.local")
    msg["X-ForraTech-Channel"] = "formulario-web"
    msg.set_content(
        f"Nombre: {name}\nCorreo: {sender_email}\n\n{body}\n\n"
        "— Mensaje depositado en el buzón por IMAP APPEND desde la web de ForraTech."
    )
    return msg


def append_contact(name, sender_email, subject, body):
    """Deposita el mensaje del formulario en INBOX usando IMAP APPEND."""
    with ImapSession() as imap:
        msg = build_contact_message(imap.address, name, sender_email, subject, body)
        imap.cmd(
            "APPEND INBOX () <fecha> {mensaje RFC 5322}",
            imap.conn.append,
            "INBOX",
            "",
            imaplib.Time2Internaldate(time.time()),
            msg.as_bytes(),
        )
        return imap.log


def list_inbox(limit=20):
    """Encabezados de los últimos mensajes de INBOX."""
    with ImapSession() as imap:
        data = imap.cmd("SELECT INBOX", imap.conn.select, "INBOX")
        total = int(data[0] or 0)
        data = imap.cmd("UID SEARCH ALL", imap.conn.uid, "SEARCH", None, "ALL")
        uids = data[0].split()[-limit:][::-1]

        messages = []
        if uids:
            fetch = imap.cmd(
                f"UID FETCH {len(uids)} mensajes (FLAGS RFC822.SIZE "
                "BODY.PEEK[HEADER.FIELDS (FROM REPLY-TO SUBJECT DATE)])",
                imap.conn.uid,
                "FETCH",
                b",".join(uids).decode(),
                "(UID FLAGS RFC822.SIZE BODY.PEEK[HEADER.FIELDS (FROM REPLY-TO SUBJECT DATE)])",
            )
            for item in fetch:
                if not isinstance(item, tuple):
                    continue
                meta, raw = item
                headers = email.message_from_bytes(raw)
                uid_match = UID_RE.search(meta)
                size_match = SIZE_RE.search(meta)
                flags = _parse_flags(meta)
                messages.append({
                    "uid": uid_match.group(1).decode() if uid_match else "",
                    "from": decode(headers.get("From")),
                    "reply_to": decode(headers.get("Reply-To") or headers.get("From")),
                    "subject": decode(headers.get("Subject")) or "(sin asunto)",
                    "date": headers.get("Date", ""),
                    "size": int(size_match.group(1)) if size_match else 0,
                    "seen": "\\Seen" in flags,
                    "answered": "\\Answered" in flags,
                    "flagged": "\\Flagged" in flags,
                })
            messages.sort(key=lambda m: int(m["uid"] or 0), reverse=True)

        return {
            "total": total,
            "messages": messages,
            "log": imap.log,
            "tls": imap.tls,
        }


def _plain_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                return part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", "replace"
                )
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                html = part.get_payload(decode=True).decode(
                    part.get_content_charset() or "utf-8", "replace"
                )
                return re.sub(r"<[^>]+>", " ", html)
        return ""
    payload = msg.get_payload(decode=True) or b""
    return payload.decode(msg.get_content_charset() or "utf-8", "replace")


def read_message(uid):
    if not str(uid).isdigit():
        raise ValueError("UID inválido")
    with ImapSession() as imap:
        imap.cmd("SELECT INBOX", imap.conn.select, "INBOX")
        data = imap.cmd(
            f"UID FETCH {uid} (FLAGS BODY.PEEK[])",
            imap.conn.uid,
            "FETCH",
            str(uid),
            "(FLAGS BODY.PEEK[])",
        )
        item = next((d for d in data if isinstance(d, tuple)), None)
        if not item:
            raise LookupError("Mensaje no encontrado")
        meta, raw = item
        msg = email.message_from_bytes(raw)
        flags = _parse_flags(meta)
        reply_to = msg.get("Reply-To") or msg.get("From") or ""
        return {
            "uid": str(uid),
            "from": decode(msg.get("From")),
            "reply_to_addr": email.utils.parseaddr(decode(reply_to))[1],
            "to": decode(msg.get("To")),
            "subject": decode(msg.get("Subject")) or "(sin asunto)",
            "date": msg.get("Date", ""),
            "message_id": msg.get("Message-ID", ""),
            "body": _plain_body(msg)[:20000],
            "flags": flags,
            "seen": "\\Seen" in flags,
            "answered": "\\Answered" in flags,
            "flagged": "\\Flagged" in flags,
            "log": imap.log,
            "tls": imap.tls,
        }


FLAG_ACTIONS = {
    "leido": ("+FLAGS", "(\\Seen)"),
    "no-leido": ("-FLAGS", "(\\Seen)"),
    "respondido": ("+FLAGS", "(\\Answered \\Seen)"),
    "pendiente": ("-FLAGS", "(\\Answered)"),
    "destacar": ("+FLAGS", "(\\Flagged)"),
    "quitar-destacado": ("-FLAGS", "(\\Flagged)"),
}


def update_flags(uid, action):
    if not str(uid).isdigit() or action not in FLAG_ACTIONS:
        raise ValueError("Acción inválida")
    op, flags = FLAG_ACTIONS[action]
    with ImapSession() as imap:
        imap.cmd("SELECT INBOX", imap.conn.select, "INBOX")
        imap.cmd(
            f"UID STORE {uid} {op} {flags}",
            imap.conn.uid,
            "STORE",
            str(uid),
            op,
            flags,
        )
        return imap.log


# ─────────────────────────────────────────────
# POP3
# ─────────────────────────────────────────────
def pop3_summary(limit=5):
    cfg = _cfg()
    log = []
    host, port = cfg["POP3_HOST"], cfg["POP3_PORT"]
    log.append(f"Conexión TCP + TLS a {host}:{port}")
    conn = poplib.POP3_SSL(host, port, context=_tls_context(), timeout=15)
    tls = _tls_details(conn.sock)
    try:
        log.append(f"TLS establecido: {tls.get('version')} · {tls.get('cipher')}")
        log.append(f"Saludo del servidor: {conn.getwelcome().decode(errors='replace')}")
        log.append(f"USER {cfg['MAIL_ADDRESS']}")
        conn.user(cfg["MAIL_ADDRESS"])
        log.append("PASS ********")
        conn.pass_(cfg["MAIL_APP_PASSWORD"])

        log.append("STAT")
        count, size = conn.stat()

        log.append("LIST")
        _, listing, _ = conn.list()

        messages = []
        first = max(1, count - limit + 1)
        for number in range(count, first - 1, -1):
            log.append(f"TOP {number} 0")
            _, lines, _ = conn.top(number, 0)
            headers = email.message_from_bytes(b"\r\n".join(lines))
            messages.append({
                "number": number,
                "from": decode(headers.get("From")),
                "subject": decode(headers.get("Subject")) or "(sin asunto)",
                "date": headers.get("Date", ""),
            })
        return {
            "count": count,
            "size": size,
            "listing": [line.decode() for line in listing[-limit:]],
            "messages": messages,
            "log": log,
            "tls": tls,
        }
    finally:
        log.append("QUIT")
        try:
            conn.quit()
        except Exception:
            pass


# ─────────────────────────────────────────────
# Diagnóstico de puertos (evidencia de la restricción SMTP)
# ─────────────────────────────────────────────
def port_check(host, port, timeout=5):
    started = time.monotonic()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            ok, detail = True, "Conexión TCP establecida"
    except Exception as exc:
        ok, detail = False, f"{type(exc).__name__}: {exc}"
    return {
        "host": host,
        "port": port,
        "ok": ok,
        "detail": detail,
        "ms": round((time.monotonic() - started) * 1000),
    }
