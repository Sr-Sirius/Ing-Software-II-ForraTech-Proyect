import io, base64, os, gc
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.metrics import confusion_matrix,ConfusionMatrixDisplay,accuracy_score,precision_score,recall_score,f1_score,roc_curve,roc_auc_score, classification_report
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# ─────────────────────────────────────────────
# Global variables, initialized as None
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
# Settings
K = 4
FEATURES = [
    "log_area", "score_proteina", "clima_num",
    "prop_pastoreo_continuo", "prop_pastoreo_rotacional",
    "prop_corte", "prop_banco_proteina"
]

# ─────────────────────────────────────────────
# 1. Load dataset
# ─────────────────────────────────────────────
def load_model_KM(data_path: str = None):
    # Upload a CSV file and train once. Avoid retraining
    global _df, _scaler, _kmeans, _pca
    global y_true_eval, y_pred_eval, y_prob_eval, train_acc, test_acc, cluster_quality    
    # If it's already trained, it runs
    if _kmeans is not None:
        return

    # If no path is provided, use the default one
    if data_path is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
        data_path = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")

    # Load data
    _df = pd.read_csv(data_path)

    # Feature engineering
    _df["score_proteina"] = (
        0.50 * _df["prop_banco_proteina"] +
        0.30 * _df["prop_corte"] +
        0.10 * _df["prop_pastoreo_rotacional"] +
        0.10 * _df["prop_pastoreo_continuo"]
    )
    _df["log_area"] = np.log1p(_df["area_sembrada_ha"])
# ─────────────────────────────────────────────
# 5. Train / test split + Random Forest
# ─────────────────────────────────────────────
    X = _df[FEATURES].copy()
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)

    _kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
    _df["cluster"] = _kmeans.fit_predict(X_scaled)
    # ─────────────────────────────────────────────
    # Métricas de evaluación para K-Means
    # K-Means no tiene etiquetas reales, así que creamos
    # una etiqueta binaria basada en score_proteina.
    # 1 = Alta aptitud proteica
    # 0 = Baja aptitud proteica
    # ─────────────────────────────────────────────
    _df["optimal"] = (
        _df["score_proteina"] >= _df["score_proteina"].mean()
    ).astype(int)

    # Cada cluster se interpreta como alta o baja aptitud
    cluster_quality = (
        _df.groupby("cluster")["optimal"]
        .mean()
        .to_dict()
    )

    # Predicción binaria según el promedio de optimal dentro de cada cluster
    _df["cluster_pred"] = _df["cluster"].map(
        lambda c: 1 if cluster_quality[c] >= 0.5 else 0
    )

    # Probabilidad aproximada: proporción de casos óptimos en el cluster
    _df["cluster_prob"] = _df["cluster"].map(cluster_quality)

    y_true_eval = _df["optimal"].values
    y_pred_eval = _df["cluster_pred"].values
    y_prob_eval = _df["cluster_prob"].values

    train_acc = accuracy_score(y_true_eval, y_pred_eval)
    test_acc = train_acc
    _pca = PCA(n_components=2, random_state=42)
    X_pca = _pca.fit_transform(X_scaled)
    _df["pca1"] = X_pca[:, 0]
    _df["pca2"] = X_pca[:, 1]

def getClusterInfo():
    # Returns a summary for each cluster
    if _df is None:
        load_model_KM()
    return _df.groupby("cluster")[["score_proteina", "log_area"]].mean()

def buildUserVector(area_ha, ganancia_proteina_pct, clima):
    # Build the user's feature vector with the same structure as the dataset
    gp = ganancia_proteina_pct / 100.0   # normalizar a 0-1

    # Breakdown of uses by desired protein yield
    prop_banco = min(gp * 0.60, 0.60)
    prop_corte = min(gp * 0.40, 0.40)
    prop_rot = max(1.0 - prop_banco - prop_corte - 0.05, 0.0)
    prop_cont = max(0.05, 1.0 - prop_banco - prop_corte - prop_rot)

    clima_num = 1 if clima.strip().lower() == "frio" else 0
    log_area = np.log1p(area_ha)

    score_p = (0.50 * prop_banco + 0.30 * prop_corte +
               0.10 * prop_rot + 0.10 * prop_cont)

    return np.array([log_area, score_p, clima_num,
                     prop_cont, prop_rot, prop_corte, prop_banco])

def predictCluster(area_ha, ganancia_proteina_pct, clima):
    # Predicts the cluster and returns the most recommended variety
    global _df, _scaler, _kmeans
    
    # Ensure that the model is loaded
    if _kmeans is None:
        load_model_KM()
    
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    cluster = int(_kmeans.predict(uv_scaled)[0])

    # Filter by cluster and climate
    clima_lower = clima.strip().lower()
    mask = (_df["cluster"] == cluster) & (_df["clima"] == clima_lower)
    subset = _df[mask].copy()
    if subset.empty:  # fallback: only cluster
        subset = _df[_df["cluster"] == cluster].copy()

    # Euclidean distance to the user's vector in scaled space
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
        "ranking": subset[["variedad", "afinidad", "score_proteina"]].head(5)
    }

def generatePlot(area_ha, ganancia_proteina_pct, clima):
    # Generate a PCA plot of clusters + user point
    global _df, _kmeans, _pca, _scaler
    
    # Ensure that the model is loaded
    if _kmeans is None:
        load_model_KM()
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    result = predictCluster(area_ha, ganancia_proteina_pct, clima)
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    uv_pca = _pca.transform(uv_scaled)

    colors = ["#1D9E75", "#EF9F27", "#4A90D9", "#D85A30"]

    # ────────────────────────────────────────────────────────────────
    # Graph 1: PCA clusters 
    # ────────────────────────────────────────────────────────────────
    ax = axes[0]
    for c in range(K):
        mask = _df["cluster"] == c
        ax.scatter(_df.loc[mask, "pca1"], _df.loc[mask, "pca2"],
                   color=colors[c], s=80, alpha=0.8, label=f"Cluster {c}")
        for _, row in _df[mask].iterrows():
            ax.annotate(row["variedad"].split("(")[0].strip()[:18],
                        (row["pca1"], row["pca2"]),
                        fontsize=6.5, alpha=0.7)

    # Centroides
    cent_pca = _pca.transform(_kmeans.cluster_centers_)
    ax.scatter(cent_pca[:, 0], cent_pca[:, 1], marker="X", s=160,
               color="black", zorder=5, label="Centroide")

    # User point
    ax.scatter(uv_pca[0, 0], uv_pca[0, 1], marker="*", s=300,
               color="red", zorder=6, label="Tu terreno")
    ax.text(uv_pca[0, 0], uv_pca[0, 1] + 0.1,
            f"Cluster {result['cluster']}", fontsize=9,
            fontweight="bold", color="red")

    ax.set_xlabel("PC1", fontsize=11)
    ax.set_ylabel("PC2", fontsize=11)
    ax.set_title("K-Means Clustering – Variedades de Pasto\n(PCA 2D)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # ────────────────────────────────────────────────────────────────
    # Graph 2: Affinity Ranking 
    # ────────────────────────────────────────────────────────────────
    ax2 = axes[1]
    top = result["ranking"]
    bar_colors = ["#1D9E75" if i == 0 else "#9FE1CB" for i in range(len(top))]
    bars = ax2.barh(top["variedad"].str[:30][::-1],
                    top["afinidad"][::-1], color=bar_colors[::-1], edgecolor="white")
    for bar, val in zip(bars[::-1], top["afinidad"]):
        ax2.text(val + 0.002, bar.get_y() + bar.get_height() / 2,
                 f"{val:.3f}", va="center", fontsize=9, fontweight="bold")
    ax2.set_xlabel("Afinidad (inverso distancia)", fontsize=11)
    ax2.set_title(f"Top recomendadas – Cluster {result['cluster']}\n"
                  f"Clima: {clima} | Área: {area_ha} ha | Proteína: {ganancia_proteina_pct}%",
                  fontsize=12, fontweight="bold")
    ax2.grid(True, axis="x", alpha=0.3)

    plt.tight_layout()

    # Memory optimization: close and cleanup
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close('all')
    buf.seek(0)
    result_base64 = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()

    return result_base64
def getModelMetrics():
    """
    Retorna métricas principales del modelo K-Means.
    Nota: son métricas aproximadas usando una etiqueta binaria creada
    a partir del score_proteina.
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
        "test_accuracy": float(test_acc)
    }


def getClassificationReport():
    """
    Retorna reporte de clasificación para la evaluación aproximada.
    """
    if _kmeans is None:
        load_model_KM()

    return classification_report(
        y_true_eval,
        y_pred_eval,
        target_names=["Baja aptitud", "Alta aptitud"],
        output_dict=True,
        zero_division=0
    )


def generateConfusionMatrixPlot():
    """
    Genera matriz de confusión en formato base64.
    """
    if _kmeans is None:
        load_model_KM()

    cm = confusion_matrix(y_true_eval, y_pred_eval)

    fig, ax = plt.subplots(figsize=(6, 5))

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Baja aptitud", "Alta aptitud"]
    )

    disp.plot(
        ax=ax,
        cmap="Greens",
        colorbar=False,
        values_format="d"
    )

    ax.set_title(
        "Matriz de Confusión – K-Means",
        fontsize=13,
        fontweight="bold"
    )

    ax.set_xlabel("Predicción")
    ax.set_ylabel("Valor real")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    plt.close("all")

    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()

    return result


def generateROCPlot():
    """
    Genera curva ROC en formato base64.
    """
    if _kmeans is None:
        load_model_KM()

    fpr, tpr, thresholds = roc_curve(y_true_eval, y_prob_eval)

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
        label=f"ROC AUC = {auc:.3f}"
    )

    ax.plot(
        [0, 1],
        [0, 1],
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label="Clasificador aleatorio"
    )

    ax.set_title(
        "Curva ROC – K-Means",
        fontsize=13,
        fontweight="bold"
    )

    ax.set_xlabel("Tasa de Falsos Positivos")
    ax.set_ylabel("Tasa de Verdaderos Positivos")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    plt.close("all")

    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()

    return result