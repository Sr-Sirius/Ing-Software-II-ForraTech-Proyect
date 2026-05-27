# app/services/metrics_forraje_service.py

from app.ml.sintetyc_dataset_model.logistic_regression_forraje import (
    getModelMetrics as get_metrics_lr,
    generatePlot as plot_lr,
    generateRankingPlot as ranking_lr,
    generateConfusionMatrixPlot as confusion_lr,
    generateROCPlot as roc_lr,
)

from app.ml.sintetyc_dataset_model.Bayesian_Forraje import (
    getModelMetrics as get_metrics_bayes_forraje,
    generatePlot as plot_bayes_forraje,
    generateRankingPlot as ranking_bayes_forraje,
    generateFeatureImportancePlot as importance_bayes_forraje,
    generateConfusionMatrixPlot as confusion_bayes_forraje,
    generateROCPlot as roc_bayes_forraje,
)

from app.ml.sintetyc_dataset_model.random_forest_forraje import (
    getModelMetrics as get_metrics_rf_forraje,
    generatePlot as plot_rf_forraje,
    generateRankingPlot as ranking_rf_forraje,
    generateFeatureImportancePlot as importance_rf_forraje,
    generateConfusionMatrixPlot as confusion_rf_forraje,
    generateROCPlot as roc_rf_forraje,
)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def safe_call(func, *args, **kwargs):
    """
    Ejecuta una función de forma segura.
    Primero intenta con argumentos.
    Si la función no recibe argumentos, reintenta sin ellos.
    """
    try:
        return func(*args, **kwargs)
    except TypeError:
        return func()


def normalize_metrics(metrics: dict) -> dict:
    """
    Normaliza las métricas de todos los modelos para que el template
    pueda comparar LR, Bayes y Random Forest con la misma estructura.

    Estructura final esperada:
    accuracy, precision, recall, f1, roc_auc, cv_mean, cv_std, report.
    """

    if metrics is None:
        metrics = {}

    accuracy = metrics.get(
        "accuracy",
        metrics.get("exactitud", metrics.get("test_accuracy", 0))
    )

    precision = metrics.get("precision", 0)

    recall = metrics.get(
        "recall",
        metrics.get("sensibilidad", 0)
    )

    f1 = metrics.get(
        "f1",
        metrics.get("f1_score", 0)
    )

    roc_auc = metrics.get(
        "roc_auc",
        metrics.get("auc", 0)
    )

    return {
        "accuracy": float(accuracy or 0),
        "precision": float(precision or 0),
        "recall": float(recall or 0),
        "f1": float(f1 or 0),
        "roc_auc": float(roc_auc or 0),

        "cv_mean": metrics.get("cv_mean", "—"),
        "cv_std": metrics.get("cv_std", "—"),

        "report": metrics.get("report", []),
        "raw": metrics,
    }


# ─────────────────────────────────────────────
# Service principal
# ─────────────────────────────────────────────

def build_metrics_forraje_context(data_path: str) -> dict:
    """
    Construye el contexto completo para recommendation/metrics_forraje.html.

    Compara los modelos del dataset sintético:
    - Regresión Logística
    - Naive Bayes
    - Random Forest
    """

    # ─────────────────────────────────────────────
    # Métricas
    # ─────────────────────────────────────────────
    m_lr_raw = safe_call(get_metrics_lr, data_path)
    m_bayes_raw = safe_call(get_metrics_bayes_forraje, data_path)
    m_rf_raw = safe_call(get_metrics_rf_forraje, data_path)

    m_lr = normalize_metrics(m_lr_raw)
    m_bayes = normalize_metrics(m_bayes_raw)
    m_rf = normalize_metrics(m_rf_raw)

    # ─────────────────────────────────────────────
    # Mejor modelo por accuracy
    # ─────────────────────────────────────────────
    best = max(
        [
            ("lr", m_lr),
            ("bayes", m_bayes),
            ("rf", m_rf),
        ],
        key=lambda x: float(x[1].get("accuracy", 0) or 0)
    )[0]

    m_lr["is_best_accuracy"] = best == "lr"
    m_bayes["is_best_accuracy"] = best == "bayes"
    m_rf["is_best_accuracy"] = best == "rf"

    # Compatibilidad con templates que usen is_best
    m_lr["is_best"] = best == "lr"
    m_bayes["is_best"] = best == "bayes"
    m_rf["is_best"] = best == "rf"

    # ─────────────────────────────────────────────
    # Valores por defecto para gráficas generales
    # ─────────────────────────────────────────────
    ph_default = 6.5
    hum_default = 60
    alt_default = 1500
    temp_default = 22

    # ─────────────────────────────────────────────
    # Gráficas principales
    # ─────────────────────────────────────────────
    try:
        p_lr = safe_call(
            plot_lr,
            ph_default,
            hum_default,
            alt_default,
            temp_default,
        )
    except Exception:
        p_lr = None

    try:
        p_bayes = safe_call(
            plot_bayes_forraje,
            ph_default,
            hum_default,
            alt_default,
            temp_default,
        )
    except Exception:
        p_bayes = None

    try:
        p_rf = safe_call(
            plot_rf_forraje,
            ph_default,
            hum_default,
            alt_default,
            temp_default,
        )
    except Exception:
        p_rf = None

    # ─────────────────────────────────────────────
    # Ranking plots opcionales
    # ─────────────────────────────────────────────
    try:
        r_lr = safe_call(
            ranking_lr,
            ph_default,
            hum_default,
            alt_default,
            temp_default,
            top_n=10,
        )
    except Exception:
        r_lr = None

    try:
        r_bayes = safe_call(
            ranking_bayes_forraje,
            ph_default,
            hum_default,
            alt_default,
            temp_default,
            top_n=10,
        )
    except Exception:
        r_bayes = None

    try:
        r_rf = safe_call(
            ranking_rf_forraje,
            ph_default,
            hum_default,
            alt_default,
            temp_default,
            top_n=10,
        )
    except Exception:
        r_rf = None

    # ─────────────────────────────────────────────
    # Importancia de variables
    # ─────────────────────────────────────────────
    try:
        p_imp_rf = safe_call(importance_rf_forraje)
    except Exception:
        p_imp_rf = None

    try:
        p_imp_bayes = safe_call(importance_bayes_forraje)
    except Exception:
        p_imp_bayes = None

    # ─────────────────────────────────────────────
    # Matrices de confusión y ROC
    # ─────────────────────────────────────────────
    try:
        confusion_plot_lr = safe_call(confusion_lr)
    except Exception:
        confusion_plot_lr = None

    try:
        roc_plot_lr = safe_call(roc_lr)
    except Exception:
        roc_plot_lr = None

    try:
        confusion_plot_bayes = safe_call(confusion_bayes_forraje)
    except Exception:
        confusion_plot_bayes = None

    try:
        roc_plot_bayes = safe_call(roc_bayes_forraje)
    except Exception:
        roc_plot_bayes = None

    try:
        confusion_plot_rf = safe_call(confusion_rf_forraje)
    except Exception:
        confusion_plot_rf = None

    try:
        roc_plot_rf = safe_call(roc_rf_forraje)
    except Exception:
        roc_plot_rf = None

    return {
        # métricas normalizadas
        "metrics_lr": m_lr,
        "metrics_bayes": m_bayes,
        "metrics_rf": m_rf,

        # validación cruzada
        "cv_lr": {
            "mean": m_lr.get("cv_mean", "—"),
            "std": m_lr.get("cv_std", "—"),
        },
        "cv_bayes": {
            "mean": m_bayes.get("cv_mean", "—"),
            "std": m_bayes.get("cv_std", "—"),
        },
        "cv_rf": {
            "mean": m_rf.get("cv_mean", "—"),
            "std": m_rf.get("cv_std", "—"),
        },

        # reportes por clase
        "report_lr": m_lr.get("report", []),
        "report_bayes": m_bayes.get("report", []),
        "report_rf": m_rf.get("report", []),

        # gráficas generales
        "plot_lr": p_lr,
        "plot_bayes": p_bayes,
        "plot_rf": p_rf,

        # ranking plots
        "ranking_lr": r_lr,
        "ranking_bayes": r_bayes,
        "ranking_rf": r_rf,

        # importancia de variables
        "importance_plot": p_imp_rf,
        "importance_bayes_plot": p_imp_bayes,

        # matriz de confusión y ROC
        "confusion_plot_lr": confusion_plot_lr,
        "roc_plot_lr": roc_plot_lr,

        "confusion_plot_bayes": confusion_plot_bayes,
        "roc_plot_bayes": roc_plot_bayes,

        "confusion_plot_rf": confusion_plot_rf,
        "roc_plot_rf": roc_plot_rf,

        # mejor modelo
        "best_model": best,
    }