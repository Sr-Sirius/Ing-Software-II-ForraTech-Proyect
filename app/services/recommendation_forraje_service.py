# app/services/recommendation_forraje_service.py

from app.ml.sintetyc_dataset_model.logistic_regression_forraje import (
    predictCropCategory as predictLR,
    generatePlot as generateLRPlot,
    generateRankingPlot as generateLRRanking,
    getBestCrop as getBestCropLR,
    getThreshold as getLRThreshold,
    getModelMetrics as getModelMetricsLR,
    generateConfusionMatrixPlot as generateConfusionMatrixPlotLR,
    generateROCPlot as generateROCPlotLR,
)

from app.ml.sintetyc_dataset_model.random_forest_forraje import (
    predictCropCategory as predictRF,
    generatePlot as generateRFPlot,
    generateRankingPlot as generateRFRanking,
    getBestCrop as getBestCropRF,
    getThreshold as getRFThreshold,
    getModelMetrics as getModelMetricsRF,
    generateConfusionMatrixPlot as generateConfusionMatrixPlotRF,
    generateROCPlot as generateROCPlotRF,
    generateFeatureImportancePlot as generateFeatureImportancePlotRF,
)

from app.ml.sintetyc_dataset_model.Bayesian_Forraje import (
    predictCropCategory as predictBayes,
    generatePlot as generateBayesPlot,
    generateRankingPlot as generateBayesRanking,
    generateFeatureImportancePlot as generateBayesImportance,
    getBestCrop as getBestCropBayes,
    getThreshold as getBayesThreshold,
    getModelMetrics as getModelMetricsB,
    generateConfusionMatrixPlot as generateConfusionMatrixPlotB,
    generateROCPlot as generateROCPlotB,
)


def get_recommendation(data):
    ph_value = float(data["ph"])
    hum_value = float(data["humedad"])
    alt_value = float(data["altitud"])
    temp_value = float(data["temperatura"])

    result, probability = predictLR(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
    )

    plot = generateLRPlot(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
    )

    ranking_plot = generateLRRanking(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
        top_n=10,
    )

    top_crops = getBestCropLR(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
        top_n=10,
    ).to_dict(orient="records")

    threshold = getLRThreshold()
    metrics = getModelMetricsLR()
    confusion_matrix_plot = generateConfusionMatrixPlotLR()
    roc_plot = generateROCPlotLR()

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
        "metrics": metrics,
        "confusion_matrix_plot": confusion_matrix_plot,
        "roc_plot": roc_plot,
    }


def get_recommendationR(data):
    ph_value = float(data["ph"])
    hum_value = float(data["humedad"])
    alt_value = float(data["altitud"])
    temp_value = float(data["temperatura"])

    result, probability = predictRF(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
    )

    plot = generateRFPlot(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
    )

    ranking_plot = generateRFRanking(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
        top_n=10,
    )

    importance_plot = generateFeatureImportancePlotRF()

    top_crops = getBestCropRF(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
        top_n=10,
    ).to_dict(orient="records")

    threshold = getRFThreshold()
    metrics = getModelMetricsRF()
    confusion_matrix_plot = generateConfusionMatrixPlotRF()
    roc_plot = generateROCPlotRF()

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
        "roc_plot": roc_plot,
    }


def get_recommendationB(data):
    try:
        ph_value = float(data.get("ph", 6.5))
        hum_value = float(data.get("humedad", 60))
        alt_value = float(data.get("altitud", 1500))
        temp_value = float(data.get("temperatura", 20))
    except (ValueError, TypeError):
        ph_value = 6.5
        hum_value = 60
        alt_value = 1500
        temp_value = 20

    result, probability = predictBayes(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
    )

    plot = generateBayesPlot(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
    )

    ranking_plot = generateBayesRanking(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
        top_n=10,
    )

    importance_plot = generateBayesImportance()

    top_crops = getBestCropBayes(
        ph_value,
        hum_value,
        alt_value,
        temp_value,
        top_n=10,
    ).to_dict(orient="records")

    threshold = getBayesThreshold()
    metrics = getModelMetricsB()
    confusion_matrix_plot = generateConfusionMatrixPlotB()
    roc_plot = generateROCPlotB()

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
        "roc_plot": roc_plot,
    }