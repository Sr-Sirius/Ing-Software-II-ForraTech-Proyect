# app/services/recommendation_dane_service.py

import os

from app.ml.DANE_real_dataset_model.kmeans_Dane import (
    predictCluster,
    generatePlot as generateKmeansPlot,
    getClusterInfo as getClusterInfoKM,
    load_model_KM,
    getModelMetrics as getModelMetricsKM,
    generateConfusionMatrixPlot as generateConfusionMatrixPlotKM,
    generateROCPlot as generateROCPlotKM,
)

from app.ml.DANE_real_dataset_model.KKN_Dane import (
    load_model_K,
    predictKNN,
    generatePlot as generatePlotKNN,
    getClusterInfo as getClusterInfoKNN,
    getModelMetrics as getModelMetricsKNN,
    generateConfusionMatrixPlot as generateConfusionMatrixPlotKNN,
    generateROCPlot as generateROCPlotKNN,
)

from app.ml.DANE_real_dataset_model.random_f_Dane import (
    predictCropCategory as predictCropCategoryFD,
    generatePlot as generatePlotFD,
    generateFeatureImportancePlot as generateFeatureImportancePlotFD,
    getBestCrops as getBestCropsFD,
    getThreshold as getThresholdFD,
    load_model_RF,
    getModelMetrics as getModelMetricsRD,
    generateConfusionMatrixPlot as generateConfusionMatrixPlotRD,
    generateROCPlot as generateROCPlotRD,
    getClassificationReport as getClassificationReportRD,
)

from app.ml.DANE_real_dataset_model.Bayesian_Dane import (
    load_model_B,
    predictCropCategory as predictCropCategoryBD,
    generatePlot as generatePlotBD,
    getBestCrops as getBestCropsBD,
    getThreshold as getThresholdBD,
    getModelMetrics as getModelMetricsBD,
    generateConfusionMatrixPlot as generateConfusionMatrixPlotBD,
    generateROCPlot as generateROCPlotBD,
    getClassificationReport as getClassificationReportBD,
)

def get_dane_data_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))
    return os.path.join(root_dir, "data", "DANE_ena_2019_pastos.csv")


def parse_dane_form(data):
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

    return area_value, proteina_value, clima_value


def get_recommendation_KmeansD(data):
    data_path = get_dane_data_path()
    load_model_KM(data_path)

    area_value, proteina_value, clima_value = parse_dane_form(data)

    prediction = predictCluster(
        area_value,
        proteina_value,
        clima_value,
    )

    plot = generateKmeansPlot(
        area_value,
        proteina_value,
        clima_value,
    )

    metrics = getModelMetricsKM()
    confusion_matrix_plot = generateConfusionMatrixPlotKM()
    roc_plot = generateROCPlotKM()

    cluster_info = getClusterInfoKM().reset_index().to_dict(orient="records")

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
        "metrics": metrics,
        "confusion_matrix_plot": confusion_matrix_plot,
        "roc_plot": roc_plot,
    }


def get_recommendation_KNN(data):
    data_path = get_dane_data_path()
    load_model_K(data_path)

    area_value, proteina_value, clima_value = parse_dane_form(data)

    prediction = predictKNN(
        area_value,
        proteina_value,
        clima_value,
    )

    plot = generatePlotKNN(
        area_value,
        proteina_value,
        clima_value,
    )

    metrics = getModelMetricsKNN()
    confusion_matrix_plot = generateConfusionMatrixPlotKNN()
    roc_plot = generateROCPlotKNN()

    cluster_info = getClusterInfoKNN().reset_index().to_dict(orient="records")

    return {
        "result": prediction["variedad"],
        "categoria": "ÓPTIMO" if prediction["categoria"] == 1 else "SUBÓPTIMO",
        "distancia": round(prediction["distancia"], 4),
        "afinidad": round(prediction["afinidad"], 4),
        "probabilidad": round(prediction["probabilidad"] * 100, 1),
        "score_proteina": round(prediction["ranking"].iloc[0]["score_proteina"], 4),
        "ranking": prediction["ranking"][
            [
                "variedad",
                "distancia",
                "afinidad_ajustada",
                "clima",
                "score_proteina",
            ]
        ].head(5).to_dict(orient="records"),
        "plot": plot,
        "cluster_info": cluster_info,
        "area_value": area_value,
        "proteina_value": proteina_value,
        "clima_value": clima_value,
        "metrics": metrics,
        "confusion_matrix_plot": confusion_matrix_plot,
        "roc_plot": roc_plot,
    }


def get_recommendation_RandomFD(data):
    data_path = get_dane_data_path()

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No se encontró el dataset: {data_path}")

    load_model_RF(data_path)

    area_value, proteina_value, clima_value = parse_dane_form(data)

    best_var, best_prob, category = predictCropCategoryFD(
        area_value,
        proteina_value,
        clima_value,
    )

    plot = generatePlotFD(
        area_value,
        proteina_value,
        clima_value,
    )

    importance_plot = generateFeatureImportancePlotFD()

    ranking = getBestCropsFD(
        area_value,
        proteina_value,
        clima_value,
        top_n=10,
    )

    threshold = getThresholdFD()
    metrics = getModelMetricsRD()
    confusion_matrix_plot = generateConfusionMatrixPlotRD()
    roc_plot = generateROCPlotRD()
    classification_report_dict = getClassificationReportRD()

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
        "metrics": metrics,
        "confusion_matrix_plot": confusion_matrix_plot,
        "roc_plot": roc_plot,
        "classification_report": classification_report_dict,
    }


def get_recommendation_BayesianDane(data):
    data_path = get_dane_data_path()
    load_model_B(data_path)

    area_value, proteina_value, clima_value = parse_dane_form(data)

    best_var, best_prob, category, ajustadas = predictCropCategoryBD(
        area_value,
        proteina_value,
        clima_value,
    )

    plot = generatePlotBD(
        area_value,
        proteina_value,
        clima_value,
    )

    ranking = getBestCropsBD(
        area_value,
        proteina_value,
        clima_value,
        top_n=10,
    )

    metrics = getModelMetricsBD()
    confusion_matrix_plot = generateConfusionMatrixPlotBD()
    roc_plot = generateROCPlotBD()
    classification_report_dict = getClassificationReportBD()
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
    "metrics": metrics,
    "confusion_matrix_plot": confusion_matrix_plot,
    "roc_plot": roc_plot,
    "classification_report": classification_report_dict,
    }