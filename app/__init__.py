from flask import Flask
from flask_mail import Mail

# MAIL GLOBAL
mail = Mail()

def create_app():

    app = Flask(__name__)

    app.secret_key = "supersecretkey"

    # =========================
    # EMAIL CONFIG
    # =========================

    app.config["MAIL_SERVER"] = "smtp.gmail.com"
    app.config["MAIL_PORT"] = 587
    app.config["MAIL_USE_TLS"] = True

    app.config["MAIL_USERNAME"] = "forratech25@gmail.com"

    app.config["MAIL_PASSWORD"] = "jkkc vawz ndbz tuqq"

    # 🔥 INICIALIZAR MAIL
    mail.init_app(app)

    # =========================
    # BLUEPRINTS
    # =========================

    from app.routes.main_routes import main
    from app.routes.auth_routes import auth
    from app.routes.recommendation_routes import recommendation
    from app.routes.encyclopedia_routes import encyclopedia

    app.register_blueprint(main)

    app.register_blueprint(
        auth,
        url_prefix="/auth"
    )

    app.register_blueprint(
        recommendation,
        url_prefix="/recommendation"
    )

    app.register_blueprint(
        encyclopedia,
        url_prefix="/encyclopedia"
    )

    return app