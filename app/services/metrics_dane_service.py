# app/services/metrics_dane_service.py

from app.ml.DANE_real_dataset_model.kmeans_Dane import (
    load_model_KM,
    getModelMetrics as get_metrics_km,
    generatePlot as plot_km,
)

from app.ml.DANE_real_dataset_model.KKN_Dane import (
    load_model_K,
    getModelMetrics as get_metrics_knn,
    generatePlot as plot_knn,
)

from app.ml.DANE_real_dataset_model.Bayesian_Dane import (
    load_model_B,
    getModelMetrics as get_metrics_bayes_dane,
    generatePlot as plot_bayes_dane,
    generateConfusionMatrixPlot as confusion_bayes_dane,
    generateROCPlot as roc_bayes_dane,
)

from app.ml.DANE_real_dataset_model.random_f_Dane import (
    load_model_RF,
    getModelMetrics as get_metrics_rf_dane,
    generatePlot as plot_rf_dane,
    generateFeatureImportancePlot as importance_rf_dane,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def safe_call(func, *args, **kwargs):
    """
    Ejecuta una función de forma flexible.
    Primero intenta con argumentos; si la función no los recibe,
    reintenta sin argumentos.
    """
    try:
        return func(*args, **kwargs)
    except TypeError:
        return func()


def normalize_metrics(metrics: dict) -> dict:
    """
    Normaliza métricas para que K-Means, KNN, Bayes y Random Forest
    tengan la misma estructura en metrics_dane.html.
    """

    if metrics is None:
        metrics = {}

    return {
        "accuracy": float(
            metrics.get(
                "accuracy",
                metrics.get("exactitud", metrics.get("test_accuracy", 0)),
            ) or 0
        ),
        "precision": float(metrics.get("precision", 0) or 0),
        "recall": float(
            metrics.get("recall", metrics.get("sensibilidad", 0)) or 0
        ),
        "f1": float(
            metrics.get("f1", metrics.get("f1_score", 0)) or 0
        ),
        "roc_auc": float(
            metrics.get("roc_auc", metrics.get("auc", 0)) or 0
        ),
        "cv_mean": metrics.get("cv_mean", "—"),
        "cv_std": metrics.get("cv_std", "—"),
        "report": metrics.get("report", []),
        "raw": metrics,
    }


# ─────────────────────────────────────────────
# Service principal
# ─────────────────────────────────────────────

def build_metrics_dane_context(data_path: str) -> dict:
    """
    Construye el contexto completo para recommendation/metrics_dane.html.

    Compara:
    - K-Means
    - KNN
    - Naive Bayes DANE
    - Random Forest DANE
    """

    # Cargar modelos
    load_model_KM(data_path)
    load_model_K(data_path)
    load_model_B(data_path)
    load_model_RF(data_path)

    # Métricas reales de cada modelo
    m_km_raw = safe_call(get_metrics_km)
    m_knn_raw = safe_call(get_metrics_knn)
    m_bayes_raw = safe_call(get_metrics_bayes_dane)
    m_rf_raw = safe_call(get_metrics_rf_dane)

    m_km = normalize_metrics(m_km_raw)
    m_knn = normalize_metrics(m_knn_raw)
    m_bayes = normalize_metrics(m_bayes_raw)
    m_rf = normalize_metrics(m_rf_raw)

    # Mejor modelo supervisado por accuracy
    supervised = [
        ("knn", m_knn),
        ("bayes", m_bayes),
        ("rf", m_rf),
    ]

    best_sup = max(
        supervised,
        key=lambda x: float(x[1].get("accuracy", 0) or 0),
    )[0]

    m_km["is_best"] = False
    m_knn["is_best"] = best_sup == "knn"
    m_bayes["is_best"] = best_sup == "bayes"
    m_rf["is_best"] = best_sup == "rf"

    m_km["is_best_accuracy"] = False
    m_knn["is_best_accuracy"] = best_sup == "knn"
    m_bayes["is_best_accuracy"] = best_sup == "bayes"
    m_rf["is_best_accuracy"] = best_sup == "rf"

    # Valores por defecto para gráficas generales
    area_default = 50.0
    proteina_default = 70.0
    clima_default = "calido"

    # Gráficas generales
    p_km = safe_call(plot_km, area_default, proteina_default, clima_default)
    p_knn = safe_call(plot_knn, area_default, proteina_default, clima_default)
    p_bayes = safe_call(plot_bayes_dane, area_default, proteina_default, clima_default)
    p_rf = safe_call(plot_rf_dane, area_default, proteina_default, clima_default)

    try:
        p_imp = safe_call(importance_rf_dane)
    except Exception:
        p_imp = None

    # Gráficas específicas Bayes DANE
    try:
        confusion_plot_bayes = safe_call(confusion_bayes_dane)
    except Exception:
        confusion_plot_bayes = None

    try:
        roc_plot_bayes = safe_call(roc_bayes_dane)
    except Exception:
        roc_plot_bayes = None

    return {
        # métricas
        "metrics_km": m_km,
        "metrics_knn": m_knn,
        "metrics_bayes": m_bayes,
        "metrics_rf": m_rf,

        # validación cruzada
        "cv_knn": {
            "mean": m_knn.get("cv_mean", "—"),
            "std": m_knn.get("cv_std", "—"),
        },
        "cv_bayes": {
            "mean": m_bayes.get("cv_mean", "—"),
            "std": m_bayes.get("cv_std", "—"),
        },
        "cv_rf": {
            "mean": m_rf.get("cv_mean", "—"),
            "std": m_rf.get("cv_std", "—"),
        },

        # reportes
        "report_knn": m_knn.get("report", []),
        "report_bayes": m_bayes.get("report", []),
        "report_rf": m_rf.get("report", []),

        # gráficas
        "plot_km": p_km,
        "plot_knn": p_knn,
        "plot_bayes": p_bayes,
        "plot_rf": p_rf,
        "importance_plot": p_imp,

        # gráficas opcionales Bayes
        "confusion_plot_bayes": confusion_plot_bayes,
        "roc_plot_bayes": roc_plot_bayes,

        # mejor modelo
        "best_model": best_sup,
    }