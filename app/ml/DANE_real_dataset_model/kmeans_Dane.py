# app/ml/DANE_real_dataset_model/kmeans_Dane.py

import gc
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.metrics import (
    confusion_matrix,
    ConfusionMatrixDisplay,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_curve,
    roc_auc_score,
    classification_report,
)
from sklearn.cluster import KMeans

from app.ml.utils.utils_dane.dane_features import (
    FEATURES,
    build_user_vector,
)
from app.ml.pipelines.pipelines_dane.dane_preprocessing import (
    prepare_dane_training_data,
)
from app.ml.utils.utils_dane.plot_utils import fig_to_base64


# ─────────────────────────────────────────────
# Variables globales
# ─────────────────────────────────────────────
_df = None
_scaler = None
_kmeans = None
_pca = None

y_true_eval = None
y_pred_eval = None
y_prob_eval = None
train_acc = None
test_acc = None
cluster_quality = None


# ─────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────
K = 4


# ─────────────────────────────────────────────
# 1. Cargar dataset y entrenar modelo
# ─────────────────────────────────────────────
def load_model_KM(data_path: str = None):
    """
    Carga el dataset DANE, aplica pipeline común y entrena K-Means.
    """
    global _df, _scaler, _kmeans, _pca
    global y_true_eval, y_pred_eval, y_prob_eval, train_acc, test_acc, cluster_quality

    if _kmeans is not None:
        return

    data = prepare_dane_training_data(
        data_path=data_path,
        target_method="mean",
        with_pca=True,
    )

    _df = data["df"]
    X_scaled = data["X_scaled"]
    _scaler = data["scaler"]
    _pca = data["pca"]

    _kmeans = KMeans(
        n_clusters=K,
        random_state=42,
        n_init=10,
    )
    _df["cluster"] = _kmeans.fit_predict(X_scaled)

    # Evaluación aproximada: cada cluster se interpreta como alta/baja aptitud.
    cluster_quality = (
        _df.groupby("cluster")["optimal"]
        .mean()
        .to_dict()
    )

    _df["cluster_pred"] = _df["cluster"].map(
        lambda c: 1 if cluster_quality[c] >= 0.5 else 0
    )

    _df["cluster_prob"] = _df["cluster"].map(cluster_quality)

    y_true_eval = _df["optimal"].values
    y_pred_eval = _df["cluster_pred"].values
    y_prob_eval = _df["cluster_prob"].values

    train_acc = accuracy_score(y_true_eval, y_pred_eval)
    test_acc = train_acc

    gc.collect()


# ─────────────────────────────────────────────
# 2. Helpers compatibles
# ─────────────────────────────────────────────
def getClusterInfo():
    """Retorna resumen por cluster."""
    if _df is None:
        load_model_KM()

    return _df.groupby("cluster")[["score_proteina", "log_area"]].mean()


def buildUserVector(area_ha, ganancia_proteina_pct, clima):
    """Wrapper compatible. La lógica vive en utils/dane_features.py."""
    return build_user_vector(area_ha, ganancia_proteina_pct, clima)


# ─────────────────────────────────────────────
# 3. Predicción
# ─────────────────────────────────────────────
def predictCluster(area_ha, ganancia_proteina_pct, clima):
    """Predice el cluster y retorna la variedad más cercana/recomendada."""
    global _df, _scaler, _kmeans

    if _kmeans is None:
        load_model_KM()

    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    cluster = int(_kmeans.predict(uv_scaled)[0])

    clima_lower = str(clima).strip().lower()
    mask = (_df["cluster"] == cluster) & (_df["clima"].astype(str).str.lower() == clima_lower)
    subset = _df[mask].copy()

    if subset.empty:
        subset = _df[_df["cluster"] == cluster].copy()

    subset_scaled = _scaler.transform(subset[FEATURES])
    dists = np.linalg.norm(subset_scaled - uv_scaled, axis=1)

    subset["distancia"] = dists
    subset["afinidad"] = 1 / (1 + dists)
    subset = subset.sort_values("afinidad", ascending=False)

    return {
        "cluster": cluster,
        "variedad": subset.iloc[0]["variedad"],
        "afinidad": float(subset.iloc[0]["afinidad"]),
        "score_proteina": float(subset.iloc[0]["score_proteina"]),
        "ranking": subset[["variedad", "afinidad", "score_proteina"]].head(5),
    }


# ─────────────────────────────────────────────
# 4. Gráfica principal
# ─────────────────────────────────────────────
def generatePlot(area_ha, ganancia_proteina_pct, clima):
    """Genera una gráfica PCA de clusters + punto de usuario."""
    global _df, _kmeans, _pca, _scaler

    if _kmeans is None:
        load_model_KM()

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    result = predictCluster(area_ha, ganancia_proteina_pct, clima)
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    uv_pca = _pca.transform(uv_scaled)

    colors = ["#1D9E75", "#EF9F27", "#4A90D9", "#D85A30"]

    ax = axes[0]

    for c in range(K):
        mask = _df["cluster"] == c
        ax.scatter(
            _df.loc[mask, "pca1"],
            _df.loc[mask, "pca2"],
            color=colors[c % len(colors)],
            s=80,
            alpha=0.8,
            label=f"Cluster {c}",
        )

        for _, row in _df[mask].iterrows():
            ax.annotate(
                str(row["variedad"]).split("(")[0].strip()[:18],
                (row["pca1"], row["pca2"]),
                fontsize=6.5,
                alpha=0.7,
            )

    cent_pca = _pca.transform(_kmeans.cluster_centers_)
    ax.scatter(
        cent_pca[:, 0],
        cent_pca[:, 1],
        marker="X",
        s=160,
        color="black",
        zorder=5,
        label="Centroide",
    )

    ax.scatter(
        uv_pca[0, 0],
        uv_pca[0, 1],
        marker="*",
        s=300,
        color="red",
        zorder=6,
        label="Tu terreno",
    )
    ax.text(
        uv_pca[0, 0],
        uv_pca[0, 1] + 0.1,
        f"Cluster {result['cluster']}",
        fontsize=9,
        fontweight="bold",
        color="red",
    )

    ax.set_xlabel("PC1", fontsize=11)
    ax.set_ylabel("PC2", fontsize=11)
    ax.set_title(
        "K-Means Clustering – Variedades de Pasto\n(PCA 2D)",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    top = result["ranking"]
    bar_colors = ["#1D9E75" if i == 0 else "#9FE1CB" for i in range(len(top))]

    bars = ax2.barh(
        top["variedad"].astype(str).str[:30][::-1],
        top["afinidad"][::-1],
        color=bar_colors[::-1],
        edgecolor="white",
    )

    for bar, val in zip(bars[::-1], top["afinidad"]):
        ax2.text(
            val + 0.002,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.3f}",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    ax2.set_xlabel("Afinidad (inverso distancia)", fontsize=11)
    ax2.set_title(
        f"Top recomendadas – Cluster {result['cluster']}\n"
        f"Clima: {clima} | Área: {area_ha} ha | Proteína: {ganancia_proteina_pct}%",
        fontsize=12,
        fontweight="bold",
    )
    ax2.grid(True, axis="x", alpha=0.3)

    plt.tight_layout()
    return fig_to_base64(fig, plt)


# ─────────────────────────────────────────────
# 5. Métricas
# ─────────────────────────────────────────────
def getModelMetrics():
    """
    Retorna métricas aproximadas del modelo K-Means.
    Nota: K-Means no es supervisado; se evalúa contra un target binario creado por score_proteina.
    """
    if _kmeans is None:
        load_model_KM()

    accuracy = accuracy_score(y_true_eval, y_pred_eval)
    precision = precision_score(y_true_eval, y_pred_eval, zero_division=0)
    recall = recall_score(y_true_eval, y_pred_eval, zero_division=0)
    f1 = f1_score(y_true_eval, y_pred_eval, zero_division=0)

    try:
        auc = roc_auc_score(y_true_eval, y_prob_eval)
    except ValueError:
        auc = 0.0

    return {
        "exactitud": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(auc),
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
    }


def getClassificationReport():
    """Retorna reporte de clasificación para la evaluación aproximada."""
    if _kmeans is None:
        load_model_KM()

    return classification_report(
        y_true_eval,
        y_pred_eval,
        target_names=["Baja aptitud", "Alta aptitud"],
        output_dict=True,
        zero_division=0,
    )


def generateConfusionMatrixPlot():
    """Genera matriz de confusión en base64."""
    if _kmeans is None:
        load_model_KM()

    cm = confusion_matrix(y_true_eval, y_pred_eval)

    fig, ax = plt.subplots(figsize=(6, 5))

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Baja aptitud", "Alta aptitud"],
    )
    disp.plot(ax=ax, cmap="Greens", colorbar=False, values_format="d")

    ax.set_title("Matriz de Confusión – K-Means", fontsize=13, fontweight="bold")
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Valor real")

    return fig_to_base64(fig, plt)


def generateROCPlot():
    """Genera curva ROC en base64."""
    if _kmeans is None:
        load_model_KM()

    fpr, tpr, _ = roc_curve(y_true_eval, y_prob_eval)

    try:
        auc = roc_auc_score(y_true_eval, y_prob_eval)
    except ValueError:
        auc = 0.0

    fig, ax = plt.subplots(figsize=(7, 5))

    ax.plot(
        fpr,
        tpr,
        color="#1D9E75",
        linewidth=2.5,
        label=f"ROC AUC = {auc:.3f}",
    )

    ax.plot(
        [0, 1],
        [0, 1],
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label="Clasificador aleatorio",
    )

    ax.set_title("Curva ROC – K-Means", fontsize=13, fontweight="bold")
    ax.set_xlabel("Tasa de Falsos Positivos")
    ax.set_ylabel("Tasa de Verdaderos Positivos")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")

    return fig_to_base64(fig, plt)
