from flask import Blueprint, render_template, request
from app.services.recommendation_service import get_recommendation
recommendation = Blueprint('recommendation',__name__)

@recommendation.route("/regression", methods=["GET", "POST"])
def recommendationLR():
    
    if request.method == "POST":
        data = request.form.to_dict()
        result_data = get_recommendation(data)  #This function returns data; it does not render
        return render_template("regression.html", **result_data)  #Populate the template with the data
    return render_template(
        "regression.html",
        result=None,
        probability=None,
        plot=None,
        ranking_plot=None,
        top_crops=None,
        ph_value=6.5,
        hum_value=None,
        alt_value=None,
        temp_value=None,
        threshold=None
    )

