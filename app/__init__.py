from flask import Flask

def create_app():
    app = Flask(__name__)

    # 🔐 necesario para sesiones y flash
    app.config["SECRET_KEY"] = "super_secret_key"

    # importar blueprints
    from app.routes.main_routes import main
    from app.routes.auth_routes import auth
    from app.routes.recommendation_routes import recommendation
    from app.routes.encyclopedia_routes import encyclopedia
    #example temporal
    from .routes import example_animal_bp
    app.register_blueprint(example_animal_bp)    

    # registrarlos
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(recommendation, url_prefix="/recommendation")
    app.register_blueprint(encyclopedia, url_prefix="/encyclopedia")

    return app