from flask import Blueprint, render_template
from app.services.encyclopedia_service import (
    get_all_sheep,
    get_all_goats,
    get_all_fodder
)

encyclopedia = Blueprint('encyclopedia', __name__)

@encyclopedia.route("/")
def index():
    return render_template("encyclopedia/index.html")

@encyclopedia.route("/sheep")
def sheep():
    data = get_all_sheep()
    return render_template("encyclopedia/sheep.html", data=data)

@encyclopedia.route("/goats")
def goats():
    data = get_all_goats()
    return render_template("encyclopedia/goats.html", data=data)

@encyclopedia.route("/fodder")
def fodder():
    data = get_all_fodder()
    return render_template("encyclopedia/fodder.html", data=data)