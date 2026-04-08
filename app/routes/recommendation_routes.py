from flask import Blueprint, render_template, request
from app.services.recommendation_service import get_recommendation

recommendation = Blueprint('recommendation', __name__)

@recommendation.route("/", methods=["GET", "POST"])
def recommend():
    result = None

    if request.method == "POST":
        data = request.form
        result = get_recommendation(data)

    return render_template("recommendation/form.html", result=result)
