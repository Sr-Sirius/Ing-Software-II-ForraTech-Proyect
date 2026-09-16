# app/__init__.py

from flask import Flask

from app.database import init_app as init_database


def create_app():
    app = Flask(__name__)

    # Necesario para sesiones y flash.
    app.config["SECRET_KEY"] = "super_secret_key"

    # Inicializar almacenamiento.
    init_database(app)

    # Importar blueprints.
    from app.routes.main_routes import main
    from app.routes.auth_routes import auth
    from app.routes.recommendation_routes import recommendation
    from app.routes.encyclopedia_routes import encyclopedia
    from .routes import example_animal_bp

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

    return app