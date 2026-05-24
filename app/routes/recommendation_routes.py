from flask import Blueprint, render_template, request
from app.services.recommendation_service import get_recommendation, get_recommendationR, get_recommendationB, get_recommendation_KmeansD, get_recommendation_KNN, get_recommendation_RandomFD, get_recommendation_BayesianDane
recommendation = Blueprint('recommendation',__name__)

@recommendation.route("/Menu", methods=["GET"])
def recommendationM(): 
    return render_template("recommendation/recomendation_menu.html")

@recommendation.route("/menu_M", methods=["GET", "POST"])
def recommendationMM(): 
    return render_template("recommendation/menu_metrics.html")

@recommendation.route("/ml_docs", methods=["GET", "POST"])
def recommendationMLd(): 
    return render_template("recommendation/ml_docs.html")

@recommendation.route("/docs", methods=["GET", "POST"])
def recommendationDs(): 
    return render_template("recommendation/docs.html")

@recommendation.route("/Mforraje", methods=["GET", "POST"])
def recommendationMTF(): 
    return render_template("recommendation/metrics_forraje.html")

@recommendation.route("/Mdane", methods=["GET", "POST"])
def recommendationMTD(): 
    return render_template("recommendation/metrics_dane.html")

@recommendation.route("/menu_F", methods=["GET", "POST"])
def recommendationMF(): 
    return render_template("recommendation/menu_Models_F.html")

@recommendation.route("/menu_D", methods=["GET", "POST"])
def recommendationMD(): 
    return render_template("recommendation/menu_Models_D.html")


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
    #GET request - display an empty chart with no forecast points
    empty_plot = generateRFPlot()  # No parameters = base curve only
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
@recommendation.route("/TeoBayesian", methods=["GET", "POST"])
def recommendationB():
    
    if request.method == "POST":
        data = request.form.to_dict()
        result_data = get_recommendationB(data)  # This function returns data; it does not render
        return render_template("recommendation/TeoBayesian.html", **result_data)  # Populate the template with the data
    
    # GET request - display an empty chart with no forecast points
    from app.ml.sintetyc_dataset_model.Bayesian_Forraje import generatePlot as generateBayesPlot, getThreshold as getBayesThreshold
    
    empty_plot = generateBayesPlot()  # No parameters = base curve only
    return render_template(
        "recommendation/TeoBayesian.html",
        result=None,
        probability=None,
        plot=empty_plot,
        ranking_plot=None,
        importance_plot=None,
        top_crops=None,
        ph_value=6.5,
        hum_value=60,
        alt_value=1500,
        temp_value=20,
        threshold=getBayesThreshold()
    )
@recommendation.route("/KmeansD", methods=["GET", "POST"])
def recommendationKD():
    if request.method == "POST":
        data = request.form.to_dict()
        result_data = get_recommendation_KmeansD(data)
        return render_template("recommendation/KmeansD.html", **result_data)
    return render_template(
        "recommendation/KmeansD.html",
        result=None,
        cluster=None,
        afinidad=None,
        score_proteina=None,
        plot=None,
        ranking=None,
        area_value=50.0,
        proteina_value=70.0,
        clima_value="calido",
        cluster_info=None,
    )
@recommendation.route("/KNN", methods=["GET", "POST"])
def recommendationKNN():
    """
    Ruta para el modelo KNN (K-Vecinos Cercanos)
    """
    if request.method == "POST":
        data = request.form.to_dict()
        result_data = get_recommendation_KNN(data)
        return render_template("recommendation/KNN.html", **result_data)
    
    # GET request - mostrar formulario vacío
    return render_template(
        "recommendation/KNN.html",
        result=None,
        categoria=None,
        distancia=None,
        afinidad=None,
        probabilidad=None,
        score_proteina=None,
        plot=None,
        ranking=None,
        area_value=50.0,
        proteina_value=70.0,
        clima_value="calido",
        cluster_info=None,
    )
@recommendation.route("/RandomFD", methods=["GET", "POST"])
def recommendationBayesian():
    #Route for Naive Bayes model
    
    if request.method == "POST":
        data = request.form.to_dict()
        result_data = get_recommendation_RandomFD(data)
        return render_template("recommendation/RandomFD.html", **result_data)
    
    # GET request - show empty form
    return render_template(
        "recommendation/RandomFD.html",
        result=None,
        categoria=None,
        probabilidad=None,
        threshold=None,
        plot=None,
        importance_plot=None,
        ranking=None,
        area_value=50.0,
        proteina_value=70.0,
        clima_value="calido",
    )
@recommendation.route("/DaneBayesian", methods=["GET", "POST"])
def recommendationBayesianDane():
    # Route for Bayesian DANE forage recommendation model

    if request.method == "POST":
        data = request.form.to_dict()
        result_data = get_recommendation_BayesianDane(data)

        return render_template(
            "recommendation/DaneBayesian.html",
            **result_data
        )

    # GET request
    return render_template(
        "recommendation/DaneBayesian.html",
        result=None,
        categoria=None,
        probabilidad=None,
        threshold=None,
        plot=None,
        ranking=None,
        area_value=50.0,
        proteina_value=70.0,
        clima_value="calido",
    )