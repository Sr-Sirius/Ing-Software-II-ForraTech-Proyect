# Guía de puesta en marcha · Módulo de comunicaciones ForraTech

Proyecto final de **Comunicación de Datos**. Rama: `feature/comunicaciones` (creada desde `feature/my-animals`).

| Requisito del tablero | Implementación | Dónde verlo |
|---|---|---|
| Hosting operando | Render (Web Service, Python, Gunicorn) | URL de Render |
| Dominio operando | Subdominio `ing-software-ii-forratech-proyect.onrender.com` (+ opcional `*.workers.dev`) | URL |
| Certificado de dominio (DV) | Render: Let's Encrypt / Google Trust Services, 90 días | `/comunicaciones/` → "Certificado TLS" |
| Certificado adicional | Cloudflare Worker (otro certificado, otra CA) + CA local con OpenSSL | `cloudflare/worker.js`, `scripts/generar_certificado_local.sh` |
| OV / EV | No aplicados (de pago, exigen empresa constituida); justificados en el informe | — |
| Cabeceras TLS | HSTS, CSP, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy | `scripts/tls_check.py` |
| Sincrónica · Web (JS) | Chat flotante en todas las páginas (`fetch` + polling) | burbuja verde |
| Sincrónica · Integración móvil | Bot de Telegram con webhook HTTPS | `@TU_BOT` |
| Sincrónica · XMPP | Converse.js + sala pública en conversejs.org | `/comunicaciones/xmpp` |
| Asincrónica · IMAP/POP3 | Contacto → IMAP APPEND; bandeja IMAP; vista POP3 | `/comunicaciones/contacto`, `/soporte` |

---

## 0. Antes de empezar (seguridad)

1. **Revocar la contraseña de aplicación expuesta** del correo `forratech25@gmail.com`
   (estaba escrita en `app/__init__.py` de la rama `database-and-login`):
   Cuenta de Google → Seguridad → Verificación en 2 pasos → Contraseñas de aplicaciones → eliminar.
2. Desde ahora ningún secreto va en el código: todo va en `.env` (local) o en *Environment* (Render).

## 1. Buzón de soporte (correo)

1. Usar `forratech25@gmail.com` u otra cuenta Gmail del equipo, con verificación en 2 pasos activa.
2. Crear una **contraseña de aplicación** nueva (16 letras) → será `MAIL_APP_PASSWORD`.
3. Gmail → Configuración → *Reenvío y correo POP/IMAP* → **Habilitar POP** (IMAP ya viene activo).

## 2. Bot de Telegram

1. En Telegram, abrir **@BotFather** → `/newbot` → nombre `ForraTech Soporte` → usuario terminado en `bot`.
   Guardar el **token** (`TELEGRAM_BOT_TOKEN`) y el usuario (`TELEGRAM_BOT_USERNAME`).
2. Crear un grupo `ForraTech · Soporte` con los integrantes y **agregar el bot**.
3. Con el webhook ya configurado (paso 5), escribir `/id` en el grupo: el bot responde el ID
   (número negativo) → `TELEGRAM_TEAM_CHAT_ID`. Guardarlo en Render y volver a desplegar.
   *En local se puede obtener antes con `python scripts/telegram_webhook.py poll`.*
4. Para contestar: en el grupo, **Responder** (reply) sobre el mensaje que publicó el bot.

## 3. Secretos aleatorios

```bash
python -c "import secrets; print(secrets.token_hex(32))"   # SECRET_KEY
python -c "import secrets; print(secrets.token_hex(24))"   # TELEGRAM_WEBHOOK_SECRET
```

## 4. Prueba en local

```bash
git checkout feature/comunicaciones
python -m venv venv && venv\Scripts\activate        # Windows (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env                               # Linux/Mac: cp .env.example .env  → llenar valores
python run.py                                        # http://127.0.0.1:5000/comunicaciones/
```

Telegram en local (otra terminal): `python scripts/telegram_webhook.py poll http://127.0.0.1:5000`
(al terminar, registrar de nuevo el webhook de Render, paso 5).

HTTPS local con certificado propio (Git Bash): `bash scripts/generar_certificado_local.sh`,
descomentar `LOCAL_TLS_CERT` y `LOCAL_TLS_KEY` en `.env` y abrir `https://127.0.0.1:5000`.

## 5. Despliegue en Render

1. Servicio → **Settings → Branch**: `feature/comunicaciones`.
2. **Start Command**: `gunicorn run:app` (sin `-w`; la configuración está en `gunicorn.conf.py`).
3. **Environment**: crear `SECRET_KEY`, `ADMIN_PASSWORD`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`,
   `TELEGRAM_TEAM_CHAT_ID`, `TELEGRAM_WEBHOOK_SECRET`, `MAIL_ADDRESS`, `MAIL_APP_PASSWORD`
   (los demás tienen valores por defecto).
4. **Manual Deploy → Deploy latest commit**.
5. Abrir `/soporte/login` → **Telegram** → *Registrar / actualizar webhook*.
6. Abrir `/soporte/diagnostico` y comprobar: 993/995/443 abiertos, 25/465/587 bloqueados.

## 6. Sala XMPP

1. Abrir `/comunicaciones/xmpp` → *Crear cuenta* en `conversejs.org` (una por integrante).
2. Al entrar, la sala `forratech-soporte@conference.conversejs.org` se crea con el primer ingreso.
   En la configuración de la sala, marcarla como **persistente** para que no desaparezca.
3. Opcional móvil: Conversations (Android) / Monal (iOS) con la misma cuenta.

## 7. Segundo certificado: Cloudflare Worker (opcional, ~5 min)

1. Cuenta gratis en Cloudflare → *Workers & Pages* → *Create Worker* → nombre `forratech`.
2. *Edit code* → pegar `cloudflare/worker.js` → *Deploy*.
3. Agregar el host a `PUBLIC_HOSTS` en Render: `ing-software-ii-forratech-proyect.onrender.com,forratech.<sub>.workers.dev`.
4. Comparar: `python scripts/tls_check.py <host>` para ambos hosts (emisores distintos).

## 8. Evidencias a capturar

- [ ] Candado del navegador + visor del certificado (Render y Worker).
- [ ] Panel "Certificado TLS" de `/comunicaciones/`.
- [ ] Salida de `python scripts/tls_check.py` (cabeceras y redirección HTTP→HTTPS).
- [ ] Prueba en SSL Labs: `https://www.ssllabs.com/ssltest/` con el host de Render.
- [ ] Chat web: mensaje enviado, aparece en el grupo de Telegram, respuesta vuelve a la web.
- [ ] Chat privado con el bot desde el celular (`/start` y una pregunta respondida).
- [ ] Sala XMPP con dos integrantes conversando.
- [ ] Formulario de contacto → mensaje en Gmail → bandeja `/soporte/bandeja` con bitácora IMAP.
- [ ] Mensaje marcado como *Respondido* (flag `\Answered`).
- [ ] Vista POP3 con bitácora (`STAT`, `LIST`, `TOP`).
- [ ] Diagnóstico de puertos (SMTP bloqueado, IMAP/POP3/HTTPS abiertos).
- [ ] Variables de entorno en Render (con valores ocultos) y rama desplegada.

## Limitaciones conocidas (plan gratuito de Render)

- El servicio se suspende tras 15 min sin tráfico y tarda ~1 min en despertar (Telegram reintenta el webhook).
- El disco es efímero: el historial del chat web se borra al reiniciar; el historial completo queda en Telegram y en el buzón.
- SMTP saliente bloqueado (25/465/587): por eso se usa IMAP APPEND y las respuestas salen del cliente de correo del equipo.
