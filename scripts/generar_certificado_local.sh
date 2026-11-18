#!/usr/bin/env bash
# scripts/generar_certificado_local.sh
# ─────────────────────────────────────────────────────────────────────────────
# Crea una PKI mínima para probar ForraTech con HTTPS en local:
#   1. Una Autoridad Certificadora (CA) propia: "ForraTech Local CA".
#   2. Una clave privada y una solicitud de firma (CSR) para "localhost".
#   3. Un certificado de servidor firmado por esa CA (válido 90 días, como
#      Let's Encrypt), con SAN para localhost y 127.0.0.1.
#
# Es el mismo proceso que hace una CA pública, pero con una CA nuestra; por eso
# el navegador mostrará una advertencia hasta que se importe certs/forratech-ca.crt
# como CA de confianza (opcional).
#
# Uso (Linux, macOS o Git Bash en Windows):
#   bash scripts/generar_certificado_local.sh
# Luego en .env:
#   LOCAL_TLS_CERT=certs/localhost.crt
#   LOCAL_TLS_KEY=certs/localhost.key
# y ejecutar: python run.py  → https://127.0.0.1:5000
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
export MSYS_NO_PATHCONV=1   # evita que Git Bash en Windows altere "/CN=..."

DIR="certs"
mkdir -p "$DIR"

echo "1) Clave y certificado de la CA (RSA 4096, 1 año)"
openssl req -x509 -new -newkey rsa:4096 -sha256 -days 365 -nodes \
  -keyout "$DIR/forratech-ca.key" -out "$DIR/forratech-ca.crt" \
  -subj "/C=CO/ST=Cundinamarca/L=Chia/O=ForraTech (proyecto academico)/CN=ForraTech Local CA"

echo "2) Clave privada del servidor (ECDSA P-256) y CSR"
openssl ecparam -name prime256v1 -genkey -noout -out "$DIR/localhost.key"
openssl req -new -key "$DIR/localhost.key" -out "$DIR/localhost.csr" \
  -subj "/C=CO/ST=Cundinamarca/L=Chia/O=ForraTech/CN=localhost"

cat > "$DIR/localhost.ext" <<EXT
basicConstraints=CA:FALSE
keyUsage=digitalSignature
extendedKeyUsage=serverAuth
subjectAltName=DNS:localhost,IP:127.0.0.1
certificatePolicies=2.23.140.1.2.1
EXT

echo "3) La CA firma el certificado del servidor (90 días)"
openssl x509 -req -in "$DIR/localhost.csr" -CA "$DIR/forratech-ca.crt" \
  -CAkey "$DIR/forratech-ca.key" -CAcreateserial -days 90 -sha256 \
  -extfile "$DIR/localhost.ext" -out "$DIR/localhost.crt"

echo
echo "Certificado generado:"
openssl x509 -in "$DIR/localhost.crt" -noout -subject -issuer -dates -ext subjectAltName
echo
echo "Verificación de la cadena:"
openssl verify -CAfile "$DIR/forratech-ca.crt" "$DIR/localhost.crt"
