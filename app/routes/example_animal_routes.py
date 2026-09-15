# app/routes/example_animal_routes.py

from flask import Blueprint, render_template

from ..services.example_animal_service import get_example_animals


example_animal_bp = Blueprint("example_animal", __name__)


@example_animal_bp.route("/example-animal", methods=["GET"])
def example_animal():
    examples = get_example_animals()

    return render_template(
        "animals/example_animal.html",
        examples=examples,
        animal=examples["oveja"],
    )