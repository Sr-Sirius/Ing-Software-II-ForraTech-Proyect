from flask import current_app
from app.ml.sintetyc_dataset_model.logistic_regression_forraje import predictCropCategory as predictLR, generatePlot as generateLRPlot, generateRankingPlot as generateLRRanking, getBestCrop as getBestCropLR, getThreshold as getLRThreshold, getModelMetrics as getModelMetricsLR, generateConfusionMatrixPlot as generateConfusionMatrixPlotLR, generateROCPlot as generateROCPlotLR
from app.ml.sintetyc_dataset_model.random_forest_forraje import predictCropCategory as predictRF, generatePlot as generateRFPlot,generateRankingPlot as generateRFRanking,getBestCrop as getBestCropRF, getThreshold as getRFThreshold, generateROCPlot as generateROCPlotRF, generateConfusionMatrixPlot as generateConfusionMatrixPlotRF, getModelMetrics as getModelMetricsRF, generateFeatureImportancePlot as generateFeatureImportancePlotRF
from app.ml.sintetyc_dataset_model.Bayesian_Forraje import predictCropCategory as predictBayes,generatePlot as generateBayesPlot,generateRankingPlot as generateBayesRanking,generateFeatureImportancePlot as generateBayesImportance, getBestCrop as getBestCropBayes, getThreshold as getBayesThreshold,getModelMetrics as getModelMetricsB, generateConfusionMatrixPlot as generateConfusionMatrixPlotB, generateROCPlot as generateROCPlotB
from app.ml.DANE_real_dataset_model.kmeans_Dane import predictCluster, generatePlot as generateKmeansPlot, getClusterInfo, load_model_KM, getModelMetrics as getModelMetricsKM, generateConfusionMatrixPlot as generateConfusionMatrixPlotKM, generateROCPlot as generateROCPlotKM
from app.ml.DANE_real_dataset_model.KKN_Dane import load_model_K, predictKNN, generatePlot as generatePlotKNN, getClusterInfo, getModelMetrics as getModelMetricsKNN, generateConfusionMatrixPlot as generateConfusionMatrixPlotKNN, generateROCPlot as generateROCPlotKNN
from app.ml.DANE_real_dataset_model.random_f_Dane import predictCropCategory as predictCropCategoryFD, generatePlot as generatePlotFD, generateFeatureImportancePlot as generateFeatureImportancePlotFD, getBestCrops as getBestCropsFD, getThreshold as getThresholdFD, load_model_RF
from app.ml.DANE_real_dataset_model.Bayesian_Dane import load_model_B,predictCropCategory as predictCropCategoryBD, generatePlot as generatePlotBD,getBestCrops as getBestCropsBD, getThreshold as getThresholdBD

def get_recommendation(data):
     # Processes the form data and returns results, without rendering
    # Extract data
    ph_value = float(data["ph"])
    hum_value = float(data["humedad"])
    alt_value = float(data["altitud"])
    temp_value = float(data["temperatura"])
    
    # Calculate everything using logistic_regression_forraje.py
    result, probability = predictLR(ph_value, hum_value, alt_value, temp_value)
    plot = generateLRPlot(ph_value, hum_value, alt_value, temp_value)
    ranking_plot = generateLRRanking(ph_value, hum_value, alt_value, temp_value, top_n=10)
    top_crops = getBestCropLR(ph_value, hum_value, alt_value, temp_value, top_n=10).to_dict(orient="records")
    threshold = getLRThreshold()
    
    # Get model metrics (these are independent of user input)
    metrics = getModelMetricsLR()
    confusion_matrix_plot = generateConfusionMatrixPlotLR()
    roc_plot = generateROCPlotLR()
    
    # Return a dictionary containing all data
    return {
        "result": result,
        "probability": probability,
        "plot": plot,
        "ranking_plot": ranking_plot,
        "top_crops": top_crops,
        "ph_value": ph_value,
        "hum_value": hum_value,
        "alt_value": alt_value,
        "temp_value": temp_value,
        "threshold": threshold,
        "metrics": metrics,  # Add metrics dictionary
        "confusion_matrix_plot": confusion_matrix_plot,  # Add confusion matrix
        "roc_plot": roc_plot  # Add ROC curve
    }
def get_recommendationR(data):
    # Processes the form data and returns results, without rendering.
    # Extract data with validation
    ph_value = float(data["ph"])
    hum_value = float(data["humedad"])
    alt_value = float(data["altitud"])
    temp_value = float(data["temperatura"])
    
    # Calculate everything using random_forest_forraje.py
    result, probability = predictRF(ph_value, hum_value, alt_value, temp_value)
    
    # Generate plots
    plot = generateRFPlot(ph_value, hum_value, alt_value, temp_value)
    ranking_plot = generateRFRanking(ph_value, hum_value, alt_value, temp_value, top_n=10)
    importance_plot = generateFeatureImportancePlotRF()  # Add feature importance plot
    top_crops = getBestCropRF(ph_value, hum_value, alt_value, temp_value, top_n=10).to_dict(orient="records")
    threshold = getRFThreshold()
    
    # Get model metrics
    metrics = getModelMetricsRF()  # Llama a getModelMetrics (asegúrate de renombrarla o importarla correctamente)
    confusion_matrix_plot = generateConfusionMatrixPlotRF()
    roc_plot = generateROCPlotRF()
    
    # Return a dictionary containing all data
    return {
        "result": result,
        "probability": probability,
        "plot": plot,
        "ranking_plot": ranking_plot,
        "importance_plot": importance_plot,
        "top_crops": top_crops,
        "ph_value": ph_value,
        "hum_value": hum_value,
        "alt_value": alt_value,
        "temp_value": temp_value,
        "threshold": threshold,
        "metrics": metrics,
        "confusion_matrix_plot": confusion_matrix_plot,
        "roc_plot": roc_plot
    }
def get_recommendationB(data):
    # Processes the form data for Naive Bayes model
    # Extract data with validation
    try:
        ph_value = float(data.get("ph", 6.5))
        hum_value = float(data.get("humedad", 60))
        alt_value = float(data.get("altitud", 1500))
        temp_value = float(data.get("temperatura", 20))
    except (ValueError, TypeError):
        # Valores por defecto si hay error
        ph_value, hum_value, alt_value, temp_value = 6.5, 60, 1500, 20
    
    # Calculate everything using Bayesian_Forraje.py
    result, probability = predictBayes(ph_value, hum_value, alt_value, temp_value)
    
    # Generate plots (con mejoras de RAM)
    plot = generateBayesPlot(ph_value, hum_value, alt_value, temp_value)
    ranking_plot = generateBayesRanking(ph_value, hum_value, alt_value, temp_value, top_n=10)
    importance_plot = generateBayesImportance()  # Gráfica de importancia de features
    top_crops = getBestCropBayes(ph_value, hum_value, alt_value, temp_value, top_n=10).to_dict(orient="records")
    threshold = getBayesThreshold()
    
    # Get model metrics (these are computed from the test set, independent of user input)
    metrics = getModelMetricsB()  # Add this function from your model
    confusion_matrix_plot = generateConfusionMatrixPlotB()  # Add from your model
    roc_plot = generateROCPlotB()  # Add from your model
    
    # Return a dictionary containing all data
    return {
        "result": result,
        "probability": probability,
        "plot": plot,
        "ranking_plot": ranking_plot,
        "importance_plot": importance_plot,
        "top_crops": top_crops,
        "ph_value": ph_value,
        "hum_value": hum_value,
        "alt_value": alt_value,
        "temp_value": temp_value,
        "threshold": threshold,
        "metrics": metrics,  # Add metrics dictionary
        "confusion_matrix_plot": confusion_matrix_plot,  # Add confusion matrix
        "roc_plot": roc_plot  # Add ROC curve
    }
def get_recommendation_KmeansD(data):
        import os
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
        DATA_PATH = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")
        
        # Load model using path
        load_model_KM(DATA_PATH)

        # Extract and validate form inputs
        try:
            area_value = float(data.get("area_ha", 50.0))
            proteina_value = float(data.get("ganancia_proteina_pct", 70.0))
            clima_value = str(data.get("clima", "calido")).strip().lower()
            if clima_value not in ("calido", "frio"):
                clima_value = "calido"
        except (ValueError, TypeError):
            area_value, proteina_value, clima_value = 50.0, 70.0, "calido"

        # Prediction
        prediction = predictCluster(area_value, proteina_value, clima_value)

        # Graph PCA + ranking
        plot = generateKmeansPlot(area_value, proteina_value, clima_value)

        # Get model metrics (these are computed from the clustering evaluation)
        metrics = getModelMetricsKM()  # Add this
        confusion_matrix_plot = generateConfusionMatrixPlotKM()  # Add this
        roc_plot = generateROCPlotKM()  # Add this

        # Cluster Summary
        cluster_info = getClusterInfo().reset_index().to_dict(orient="records")

        # Return the dictionary ready for the template
        return {
            "result": prediction["variedad"],
            "cluster": prediction["cluster"],
            "afinidad": round(prediction["afinidad"], 4),
            "score_proteina": round(prediction["score_proteina"], 4),
            "ranking": prediction["ranking"].to_dict(orient="records"),
            "plot": plot,
            "cluster_info": cluster_info,
            "area_value": area_value,
            "proteina_value": proteina_value,
            "clima_value": clima_value,
            "metrics": metrics,  # Add metrics dictionary
            "confusion_matrix_plot": confusion_matrix_plot,  # Add confusion matrix
            "roc_plot": roc_plot  # Add ROC curve
    }
def get_recommendation_KNN(data):
    # Recommendation using KNN (K-Nearest Neighbors) for pastures
    
    import os    
    # Create a path to the data file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
    DATA_PATH = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")
    
    # Cargar modelo con la ruta
    load_model_K(DATA_PATH)

    # Extraer y validar inputs del formulario
    try:
        area_value = float(data.get("area_ha", 50.0))
        proteina_value = float(data.get("ganancia_proteina_pct", 70.0))
        clima_value = str(data.get("clima", "calido")).strip().lower()
        if clima_value not in ("calido", "frio"):
            clima_value = "calido"
    except (ValueError, TypeError):
        area_value, proteina_value, clima_value = 50.0, 70.0, "calido"

    # Prediction with KNN
    prediction = predictKNN(area_value, proteina_value, clima_value)

    # Generated graph PCA + ranking
    plot = generatePlotKNN(area_value, proteina_value, clima_value)

    # Get model metrics (these are computed from the test set)
    metrics = getModelMetricsKNN()  # Add this
    confusion_matrix_plot = generateConfusionMatrixPlotKNN()  # Add this
    roc_plot = generateROCPlotKNN()  # Add this
    
    # Cluster information, for compatibility
    cluster_info = getClusterInfo().reset_index().to_dict(orient="records")

    # Return the dictionary ready for the template
    return {
        "result": prediction["variedad"],
        "categoria": "ÓPTIMO" if prediction["categoria"] == 1 else "SUBÓPTIMO",
        "distancia": round(prediction["distancia"], 4),
        "afinidad": round(prediction["afinidad"], 4),
        "probabilidad": round(prediction["probabilidad"] * 100, 1),
        "score_proteina": round(prediction["ranking"].iloc[0]["score_proteina"], 4),
        "ranking": prediction["ranking"][["variedad", "distancia", "afinidad_ajustada", "clima", "score_proteina"]].head(5).to_dict(orient="records"),
        "plot": plot,
        "cluster_info": cluster_info,
        "area_value": area_value,
        "proteina_value": proteina_value,
        "clima_value": clima_value,
        "metrics": metrics,  # Add metrics dictionary
        "confusion_matrix_plot": confusion_matrix_plot,  # Add confusion matrix
        "roc_plot": roc_plot  # Add ROC curve
    }
def get_recommendation_RandomFD(data):
    #Recommendation using Naive Bayes for forage crops
    
    import os    
    # Build path to data file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
    DATA_PATH = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")
    
    # Alternative path if file not found
    if not os.path.exists(DATA_PATH):
        DATA_PATH = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")
    
    # Load model with the path
    load_model_RF(DATA_PATH)

    # Extract and validate form inputs
    try:
        area_value = float(data.get("area_ha", 50.0))
        proteina_value = float(data.get("ganancia_proteina_pct", 70.0))
        clima_value = str(data.get("clima", "calido")).strip().lower()
        if clima_value not in ("calido", "frio"):
            clima_value = "calido"
    except (ValueError, TypeError):
        area_value, proteina_value, clima_value = 50.0, 70.0, "calido"

    # Prediction
    best_var, best_prob, category = predictCropCategoryFD(area_value, proteina_value, clima_value)

    # Generate plots
    plot = generatePlotFD(area_value, proteina_value, clima_value)
    importance_plot = generateFeatureImportancePlotFD()
    
    # Get top crops ranking
    ranking = getBestCropsFD(area_value, proteina_value, clima_value, top_n=10)
    
    # Get threshold
    threshold = getThresholdFD()

    # Return dictionary ready for template
    return {
        "result": best_var,
        "categoria": "ÓPTIMO" if category == 1 else "SUBÓPTIMO",
        "probabilidad": round(best_prob * 100, 1),
        "threshold": round(threshold * 100, 1),
        "plot": plot,
        "importance_plot": importance_plot,
        "ranking": ranking.to_dict(orient="records"),
        "area_value": area_value,
        "proteina_value": proteina_value,
        "clima_value": clima_value,
    }
def get_recommendation_BayesianDane(data):
    # Recommendation using Bayesian DANE model
    import os
    
    # Build path to data file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
    DATA_PATH = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")
    
    # Load model with the path
    load_model_B(DATA_PATH)
    
    # PRIMERO: Extraer y validar parámetros del formulario
    try:
        area_value = float(data.get("area_ha", 50.0))
        proteina_value = float(data.get("ganancia_proteina_pct", 70.0))
        clima_value = str(data.get("clima", "calido")).strip().lower()
        if clima_value not in ("calido", "frio"):
            clima_value = "calido"
    except (ValueError, TypeError):
        area_value = 50.0
        proteina_value = 70.0
        clima_value = "calido"
    
    # LUEGO: Usar las variables para las predicciones
    best_var, best_prob, category, ajustadas = predictCropCategoryBD(
        area_value, proteina_value, clima_value
    )
    
    plot = generatePlotBD(area_value, proteina_value, clima_value)
    ranking = getBestCropsBD(area_value, proteina_value, clima_value, top_n=10)
    threshold = getThresholdBD()
    
    return {
        "result": best_var,
        "categoria": "ÓPTIMO" if category == 1 else "SUBÓPTIMO",
        "probabilidad": round(best_prob * 100, 1),
        "threshold": round(threshold * 100, 1),
        "plot": plot,
        "ranking": ranking.to_dict(orient="records"),
        "area_value": area_value,
        "proteina_value": proteina_value,
        "clima_value": clima_value,
    }