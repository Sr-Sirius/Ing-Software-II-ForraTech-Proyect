# app/__init__.py

from datetime import timedelta

from flask import Flask

from app.database import init_app as init_database
from app.settings import apply_settings, load_dotenv_if_available, public_settings


def create_app():
    load_dotenv_if_available()

    app = Flask(__name__)

    # Configuración desde variables de entorno (SECRET_KEY, tokens, correo...).
    apply_settings(app)
    app.permanent_session_lifetime = timedelta(days=1)

    # Seguridad HTTP: ProxyFix, redirección a HTTPS, HSTS y demás cabeceras.
    from app.security import init_security
    init_security(app)

    # Inicializar almacenamiento.
    init_database(app)

    from app.services.chat_service import init_chat_schema
    init_chat_schema(app)

    # Importar blueprints.
    from app.routes.main_routes import main
    from app.routes.auth_routes import auth
    from app.routes.recommendation_routes import recommendation
    from app.routes.encyclopedia_routes import encyclopedia
    from .routes import example_animal_bp
    from app.routes.chat_routes import chat
    from app.routes.communications_routes import communications
    from app.routes.support_routes import support

    # Registrar blueprints.
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(
        recommendation,
        url_prefix="/recommendation",
    )
    app.register_blueprint(
        encyclopedia,
        url_prefix="/encyclopedia",
    )

    # Ejemplo temporal.
    app.register_blueprint(example_animal_bp)

    # Módulo de comunicaciones (proyecto final de Comunicación de Datos).
    app.register_blueprint(chat, url_prefix="/chat")
    app.register_blueprint(communications, url_prefix="/comunicaciones")
    app.register_blueprint(support, url_prefix="/soporte")

    @app.context_processor
    def inject_public_settings():
        return {"comms": public_settings(app)}

    return app
