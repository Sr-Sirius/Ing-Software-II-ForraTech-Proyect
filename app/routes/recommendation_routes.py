from flask import Blueprint, render_template, request
from app.services.recommendation_service import get_recommendation, get_recommendationR
recommendation = Blueprint('recommendation',__name__)

@recommendation.route("/regression", methods=["GET", "POST"])
def recommendationLR():
    
    if request.method == "POST":
        data = request.form.to_dict()
        result_data = get_recommendation(data)  #This function returns data; it does not render
        return render_template("recommendation/regression.html", **result_data)  #Populate the template with the data
    return render_template(
        "recommendation/regression.html",
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
@recommendation.route("/RandomRF", methods=["GET", "POST"])
def recommendationRF():
    
    if request.method == "POST":
        data = request.form.to_dict()
        result_data = get_recommendationR(data)  # This function returns data; it does not render
        return render_template("recommendation/RandomRF.html", **result_data)  # Populate the template with the data
    from app.ml.sintetyc_dataset_model.random_forest_forraje import generatePlot as generateRFPlot, getThreshold as getRFThreshold
    # GET request - mostrar gráfica vacía (sin punto de predicción)
    empty_plot = generateRFPlot()  # Sin parámetros = solo curva base
    return render_template(
        "recommendation/RandomRF.html",
        result=None,
        probability=None,
        plot=empty_plot,
        ranking_plot=None,
        top_crops=None,
        ph_value=6.5,
        hum_value=60,
        alt_value=1500,
        temp_value=20,
        threshold=getRFThreshold()
    )
