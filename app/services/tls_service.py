# app/services/tls_service.py
"""
Inspección del certificado TLS que presenta un host público.

Se usa en /comunicaciones/tls para mostrar, en vivo, qué certificado está
protegiendo la página: emisor (CA), tipo de validación, vigencia, nombres
cubiertos (SAN), versión de TLS y suite de cifrado negociada.
"""

import socket
import ssl
import threading
import time
from datetime import datetime, timezone

_CACHE = {}
_LOCK = threading.Lock()
CACHE_SECONDS = 600

# OIDs de política de certificado (CA/Browser Forum) → tipo de validación
POLICY_TYPES = {
    "2.23.140.1.2.1": "DV · Validación de dominio",
    "2.23.140.1.2.2": "OV · Validación de organización",
    "2.23.140.1.2.3": "IV · Validación individual",
    "2.23.140.1.1": "EV · Validación extendida",
}


def _name(parts):
    return {k: v for rdn in parts for (k, v) in rdn}


def _parse_date(value):
    return datetime.strptime(value, "%b %d %H:%M:%S %Y %Z").replace(
        tzinfo=timezone.utc
    )


def _validation_type(der_bytes, subject):
    """Busca el OID de política en el certificado (sin librerías externas)."""
    for oid, label in POLICY_TYPES.items():
        encoded = _encode_oid(oid)
        if encoded and encoded in der_bytes:
            return label
    # Sin OID reconocible: si el sujeto no tiene organización, es DV.
    if "organizationName" not in subject:
        return "DV · Validación de dominio (deducido: el sujeto solo tiene CN)"
    return "No determinado"


def _encode_oid(oid):
    parts = [int(p) for p in oid.split(".")]
    body = bytes([40 * parts[0] + parts[1]])
    for value in parts[2:]:
        chunk = [value & 0x7F]
        value >>= 7
        while value:
            chunk.insert(0, 0x80 | (value & 0x7F))
            value >>= 7
        body += bytes(chunk)
    return bytes([0x06, len(body)]) + body


def inspect(host, port=443, timeout=8):
    key = (host, port)
    with _LOCK:
        cached = _CACHE.get(key)
        if cached and time.time() - cached["checked_ts"] < CACHE_SECONDS:
            return cached

    context = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as raw:
        with context.wrap_socket(raw, server_hostname=host) as tls:
            cert = tls.getpeercert()
            der = tls.getpeercert(binary_form=True)
            version = tls.version()
            cipher = tls.cipher()

    subject = _name(cert.get("subject", []))
    issuer = _name(cert.get("issuer", []))
    not_before = _parse_date(cert["notBefore"])
    not_after = _parse_date(cert["notAfter"])
    now = datetime.now(timezone.utc)

    result = {
        "host": host,
        "port": port,
        "subject_cn": subject.get("commonName", ""),
        "issuer_org": issuer.get("organizationName", ""),
        "issuer_cn": issuer.get("commonName", ""),
        "san": [v for (k, v) in cert.get("subjectAltName", []) if k == "DNS"],
        "not_before": not_before.strftime("%Y-%m-%d"),
        "not_after": not_after.strftime("%Y-%m-%d"),
        "lifetime_days": (not_after - not_before).days,
        "days_left": (not_after - now).days,
        "serial": cert.get("serialNumber", ""),
        "tls_version": version,
        "cipher": cipher[0] if cipher else "",
        "cipher_bits": cipher[2] if cipher else "",
        "validation": _validation_type(der, subject),
        "checked_at": now.strftime("%Y-%m-%d %H:%M UTC"),
        "checked_ts": time.time(),
    }
    with _LOCK:
        _CACHE[key] = result
    return result
