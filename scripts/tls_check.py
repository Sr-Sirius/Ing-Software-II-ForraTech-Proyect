"""
scripts/tls_check.py — Evidencia de TLS y cabeceras de seguridad de un sitio.

Uso:
    python scripts/tls_check.py ing-software-ii-forratech-proyect.onrender.com
    python scripts/tls_check.py forratech.<subdominio>.workers.dev

Muestra: emisor del certificado, tipo de validación (DV/OV/EV), vigencia,
nombres cubiertos, versión de TLS, cifrado y cabeceras HTTP de seguridad.
"""

import socket
import ssl
import sys
import urllib.request
from datetime import datetime, timezone

POLICIES = {
    bytes.fromhex("060667810c010201"): "DV (validación de dominio)",
    bytes.fromhex("060667810c010202"): "OV (validación de organización)",
    bytes.fromhex("060567810c0101"): "EV (validación extendida)",
}
HEADERS = [
    "Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options",
    "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy", "Server",
]


def name(parts):
    return {k: v for rdn in parts for (k, v) in rdn}


def main(host):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=10) as raw:
        with ctx.wrap_socket(raw, server_hostname=host) as tls:
            cert, der = tls.getpeercert(), tls.getpeercert(binary_form=True)
            version, cipher = tls.version(), tls.cipher()

    fmt = "%b %d %H:%M:%S %Y %Z"
    start = datetime.strptime(cert["notBefore"], fmt).replace(tzinfo=timezone.utc)
    end = datetime.strptime(cert["notAfter"], fmt).replace(tzinfo=timezone.utc)
    issuer = name(cert["issuer"])
    kind = next((v for k, v in POLICIES.items() if k in der), "No determinado")

    print(f"\n== Certificado TLS de {host} ==")
    print(f"Sujeto (CN)     : {name(cert['subject']).get('commonName')}")
    print(f"Emisor          : {issuer.get('organizationName')} / {issuer.get('commonName')}")
    print(f"Tipo            : {kind}")
    print(f"Válido desde    : {start:%Y-%m-%d}  hasta {end:%Y-%m-%d}  ({(end - start).days} días)")
    print(f"Días restantes  : {(end - datetime.now(timezone.utc)).days}")
    print(f"SAN             : {', '.join(v for k, v in cert.get('subjectAltName', []) if k == 'DNS')}")
    print(f"Protocolo       : {version}")
    print(f"Cifrado         : {cipher[0]} ({cipher[2]} bits)")

    print(f"\n== Cabeceras HTTP de https://{host}/ ==")
    req = urllib.request.Request(f"https://{host}/", method="GET",
                                 headers={"User-Agent": "ForraTech-TLS-Check"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        print(f"Estado          : {resp.status}")
        for h in HEADERS:
            print(f"{h:<27}: {resp.headers.get(h, '— (no enviada)')}")

    print("\n== Redirección HTTP → HTTPS ==")
    try:
        opener = urllib.request.build_opener(NoRedirect)
        opener.open(f"http://{host}/", timeout=30)
        print("El sitio respondió por HTTP sin redirigir.")
    except urllib.error.HTTPError as exc:
        print(f"http://{host}/ → {exc.code} {exc.headers.get('Location')}")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "ing-software-ii-forratech-proyect.onrender.com")
