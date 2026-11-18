import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # HTTPS local opcional con el certificado de scripts/generar_certificado_local.sh
    cert = os.environ.get("LOCAL_TLS_CERT")
    key = os.environ.get("LOCAL_TLS_KEY")
    ssl_context = (cert, key) if cert and key else None

    app.run(debug=True, ssl_context=ssl_context)
