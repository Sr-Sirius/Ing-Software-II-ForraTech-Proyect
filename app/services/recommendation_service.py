from app.ml.sintetyc_dataset_model.logistic_regression_forraje import predictCropCategory, generatePlot, generateRankingPlot, getBestCrop, getThreshold
from app.ml.sintetyc_dataset_model.random_forest_forraje import predictCropCategory, generatePlot, generateRankingPlot, getBestCrop, getThreshold

def get_recommendation(data):
    #Processes the form data and returns results, without rendering
    #Extract data
    ph_value = float(data["ph"])
    hum_value = float(data["humedad"])
    alt_value = float(data["altitud"])
    temp_value = float(data["temperatura"])
    
    #Calculate everything using logistic_regression_forraje.py
    result, probability = predictCropCategory(ph_value, hum_value, alt_value, temp_value)
    plot = generatePlot(ph_value, hum_value, alt_value, temp_value)
    ranking_plot = generateRankingPlot(ph_value, hum_value, alt_value, temp_value, top_n=10)
    top_crops = getBestCrop(ph_value, hum_value, alt_value, temp_value, top_n=10).to_dict(orient="records")
    threshold = getThreshold()
    
    #Return a dictionary containing data
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
    }
def get_recommendationR(data):
    #Processes the form data and returns results, without rendering.
    # Extract data with validation
    ph_value = float(data["ph"])
    hum_value = float(data["humedad"])
    alt_value = float(data["altitud"])
    temp_value = float(data["temperatura"])
    
    # Calculate everything using random_forest_forraje.py
    result, probability = predictCropCategory(ph_value, hum_value, alt_value, temp_value)

    # Generate plots (pasan por las mejoras de RAM)
    plot = generatePlot(ph_value, hum_value, alt_value, temp_value)
    ranking_plot = generateRankingPlot(ph_value, hum_value, alt_value, temp_value, top_n=10)
    top_crops = getBestCrop(ph_value, hum_value, alt_value, temp_value, top_n=10).to_dict(orient="records")
    threshold = getThreshold()
    
    # Return a dictionary containing data
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
    }