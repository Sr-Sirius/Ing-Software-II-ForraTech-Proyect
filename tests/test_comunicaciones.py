"""Pruebas del módulo de comunicaciones y del panel de soporte.

Ejecutar desde la raíz del repositorio:  python -m pytest -q
"""

import re

import pytest

from app import create_app

# Emojis y pictogramas que ya no deben usarse como íconos en la sección.
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐]")

WIDGET_IDS = ["chat-widget", "cw-launcher", "cw-panel", "cw-messages", "cw-form",
              "cw-name", "cw-text", "cw-unread", "cw-close"]


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.setenv("SECRET_KEY", "clave-de-pruebas")
    monkeypatch.setenv("ADMIN_PASSWORD", "panel-de-pruebas")
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


@pytest.mark.parametrize("url", ["/comunicaciones/", "/comunicaciones/xmpp",
                                 "/comunicaciones/contacto", "/soporte/login"])
def test_paginas_cargan_sin_emojis(client, url):
    r = client.get(url)
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert 'class="ct-shell"' in html
    assert 'id="i-chat"' in html          # el sprite de íconos SVG está incluido
    assert not EMOJI.search(html.split("<main>", 1)[1].split("</main>", 1)[0])


def test_hub_conserva_elementos_funcionales(client):
    html = client.get("/comunicaciones/").get_data(as_text=True)
    assert "data-open-chat" in html
    assert 'id="tls-data"' in html
    assert "/comunicaciones/tls" in html


def test_widget_conserva_ids(client):
    html = client.get("/").get_data(as_text=True)
    for widget_id in WIDGET_IDS:
        assert f'id="{widget_id}"' in html, widget_id
    widget = html[html.index('id="chat-widget"'):]
    assert not EMOJI.search(widget[:widget.index("</section>")])


def test_xmpp_oculta_widget_y_carga_converse(client):
    html = client.get("/comunicaciones/xmpp").get_data(as_text=True)
    assert 'id="chat-widget"' not in html
    assert "converse-root" in html and "cdn.conversejs.org" in html


def test_cabeceras_de_seguridad(client):
    r = client.get("/comunicaciones/")
    csp = r.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp and "cdn.conversejs.org" in csp
    assert r.headers.get("X-Content-Type-Options") == "nosniff"


def test_contacto_exige_csrf(client):
    r = client.post("/comunicaciones/contacto", data={"name": "a", "email": "a@b.co",
                                                      "subject": "x", "message": "y"})
    assert r.status_code in (400, 403)


def test_panel_protegido_y_login(client):
    assert client.get("/soporte/chats").status_code in (302, 303)
    html = client.get("/soporte/login").get_data(as_text=True)
    token = re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)
    r = client.post("/soporte/login", data={"csrf_token": token, "password": "panel-de-pruebas"})
    assert r.status_code in (302, 303)
    chats = client.get("/soporte/chats")
    assert chats.status_code == 200
    assert "#i-inbox" in chats.get_data(as_text=True)


def test_chat_web_ida_y_vuelta(client):
    r = client.get("/chat/api/messages")
    assert r.status_code == 200
