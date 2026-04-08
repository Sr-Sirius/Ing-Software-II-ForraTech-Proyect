from flask import Flask, app

def create_app():
    app = Flask(__name__)

    from app.routes.main_routes import main
    from app.routes.auth_routes import auth
    from app.routes.recommendation_routes import recommendation
    from app.routes.encyclopedia_routes import encyclopedia

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix="/auth")
    app.register_blueprint(recommendation, url_prefix="/recommendation")
    app.register_blueprint(encyclopedia, url_prefix="/encyclopedia")

    return app