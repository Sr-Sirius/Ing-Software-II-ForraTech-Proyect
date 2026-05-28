from flask import Blueprint, render_template

main = Blueprint('main', __name__)

#  LANDING PAGE
@main.route("/")
def home():
    return render_template("home.html", show_footer=True)

#  DASHBOARD (APP INTERNA)
@main.route("/dashboard")
def dashboard():
    return render_template("dashboard/index.html",  show_sidebar=True, show_footer=False)