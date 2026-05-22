import io, base64, os, gc
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix,ConfusionMatrixDisplay,accuracy_score,precision_score,recall_score,f1_score,roc_curve,roc_auc_score
from sklearn.neighbors import NearestNeighbors
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# ─────────────────────────────────────────────
# Global variables, initialized as None
# ─────────────────────────────────────────────
_df = None
_scaler = None
_knn = None
_pca = None

_knn_classifier = None
X_test_eval = None
y_test_eval = None
y_pred_eval = None
y_prob_eval = None
train_acc = None
test_acc = None

# Settings
K = 5
FEATURES = [
    "log_area", "score_proteina", "clima_num",
    "prop_pastoreo_continuo", "prop_pastoreo_rotacional",
    "prop_corte", "prop_banco_proteina"
]

# ─────────────────────────────────────────────
# 1. Load dataset with memory optimization
# ─────────────────────────────────────────────
def load_model_K(data_path: str = None):
    """
    Carga el dataset y entrena el modelo KNN una sola vez.
    Implementa optimización de memoria y manejo de rutas.
    """
    global _df, _scaler, _knn, _pca
    
    # If it's already trained, it runs
    if _knn is not None:
        return
    
    # If no path is provided, use the default one
    if data_path is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
        data_path = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")
    
    # Check if the file exists
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No se encontró el archivo: {data_path}")
    
    # Load data
    _df = pd.read_csv(data_path)
    
    # ─────────────────────────────────────────────
    # Feature engineering 
    # ─────────────────────────────────────────────
    _df["score_proteina"] = (
        0.50 * _df["prop_banco_proteina"] +
        0.30 * _df["prop_corte"] +
        0.10 * _df["prop_pastoreo_rotacional"] +
        0.10 * _df["prop_pastoreo_continuo"]
    )
    _df["log_area"] = np.log1p(_df["area_sembrada_ha"])
    
    # Prepare data
    X = _df[FEATURES].values
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)
    
    # ─────────────────────────────────────────────
    # Target binario para evaluación supervisada
    # 1 = Alta aptitud proteica
    # 0 = Baja aptitud proteica
    # ─────────────────────────────────────────────
    _df["optimal"] = (
        _df["score_proteina"] >= _df["score_proteina"].mean()
    ).astype(int)

    y = _df["optimal"].values
    # ─────────────────────────────────────────────
    # Adjust KNN 
    # ─────────────────────────────────────────────
    _knn = NearestNeighbors(n_neighbors=K, metric="euclidean")
    _knn.fit(X_scaled)
    
    # ─────────────────────────────────────────────
    # KNN Classifier para métricas
    # ─────────────────────────────────────────────
    global _knn_classifier, X_test_eval, y_test_eval, y_pred_eval, y_prob_eval
    global train_acc, test_acc

    X_train, X_test_eval, y_train, y_test_eval = train_test_split(
        X_scaled,
        y,
        test_size=0.25,
        random_state=42,
        stratify=y
    )

    _knn_classifier = KNeighborsClassifier(
        n_neighbors=K,
        metric="euclidean"
    )

    _knn_classifier.fit(X_train, y_train)

    y_pred_eval = _knn_classifier.predict(X_test_eval)
    y_prob_eval = _knn_classifier.predict_proba(X_test_eval)[:, 1]

    train_acc = accuracy_score(y_train, _knn_classifier.predict(X_train))
    test_acc = accuracy_score(y_test_eval, y_pred_eval)
    # PCA for visualization
    _pca = PCA(n_components=2, random_state=42)
    X_pca = _pca.fit_transform(X_scaled)
    _df["pca1"] = X_pca[:, 0]
    _df["pca2"] = X_pca[:, 1]
    
    # Clear memory
    gc.collect()


# ─────────────────────────────────────────────
# 2. Helper functions
# ─────────────────────────────────────────────
def buildUserVector(area_ha, ganancia_proteina_pct, clima):
    #Build the user's feature vector
    gp = ganancia_proteina_pct / 100.0
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


def predictKNN(area_ha, ganancia_proteina_pct, clima, k=K):
    #Find the K nearest neighbors to the user and recommend
    # the closest variety.
    global _df, _scaler, _knn
    
    # Ensure that the model is loaded
    if _knn is None:
        load_model_K()
    
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    
    distances, indices = _knn.kneighbors(uv_scaled, n_neighbors=min(k, len(_df)))
    
    vecinos = _df.iloc[indices[0]].copy()
    vecinos["distancia"] = distances[0]
    vecinos["afinidad"] = 1 / (1 + distances[0])
    
    # Weighting based on the user's climate preferences
    clima_lower = clima.strip().lower()
    vecinos["afinidad_ajustada"] = vecinos.apply(
        lambda r: r["afinidad"] * 1.20 if r["clima"] == clima_lower else r["afinidad"] * 0.80,
        axis=1
    )
    vecinos = vecinos.sort_values("afinidad_ajustada", ascending=False)
    best = vecinos.iloc[0]
    
    # Logistic probability of the minimum distance
    prob = float(1 / (1 + np.exp(distances[0][0] - 1)))
    
    return {
        "variedad": best["variedad"],
        "distancia": float(best["distancia"]),
        "afinidad": float(best["afinidad_ajustada"]),
        "probabilidad": prob,
        "categoria": 1 if prob >= 0.5 else 0,
        "ranking": vecinos[["variedad", "distancia", "afinidad_ajustada", "clima", "score_proteina"]].head(k)
    }


def generatePlot(area_ha, ganancia_proteina_pct, clima):
    #Generates a PCA plot with nearest neighbors and a distance curve
    # optimized for memory management
    global _df, _knn, _pca, _scaler
    
    # ensures that the model is loaded
    if _knn is None:
        load_model_K()
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    result = predictKNN(area_ha, ganancia_proteina_pct, clima)
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    uv_pca = _pca.transform(uv_scaled)
    
    distances, indices = _knn.kneighbors(uv_scaled, n_neighbors=K)
    # ─────────────────────────────────────────────
    # Graph 1: PCA with marked neighbors 
    # ─────────────────────────────────────────────

    ax = axes[0]
    ax.scatter(_df["pca1"], _df["pca2"], color="#9FE1CB", s=60,
               alpha=0.6, label="Variedades ENA 2019")
    
    # Select K neighbors
    vecinos_idx = indices[0]
    ax.scatter(_df.iloc[vecinos_idx]["pca1"], _df.iloc[vecinos_idx]["pca2"],
               color="#EF9F27", s=120, zorder=4, label=f"{K} Vecinos más cercanos")
    
    # Select the best
    best_row = _df[_df["variedad"] == result["variedad"]]
    if not best_row.empty:
        ax.scatter(best_row["pca1"], best_row["pca2"],
                   color="#1D9E75", s=180, zorder=5, label="Recomendado")
    
    # Neighborhood labels
    for idx in vecinos_idx:
        row = _df.iloc[idx]
        ax.annotate(row["variedad"].split("(")[0].strip()[:20],
                    (row["pca1"], row["pca2"]),
                    fontsize=7, alpha=0.8,
                    xytext=(5, 5), textcoords="offset points")
    
    # User point
    ax.scatter(uv_pca[0, 0], uv_pca[0, 1], marker="*", s=350,
               color="red", zorder=6, label="Tu terreno")
    ax.text(uv_pca[0, 0], uv_pca[0, 1] + 0.15, "Tu terreno",
            fontsize=9, fontweight="bold", color="red", ha="center")
    
    # User connection lines, neighbors
    for idx in vecinos_idx:
        row = _df.iloc[idx]
        ax.plot([uv_pca[0, 0], row["pca1"]], [uv_pca[0, 1], row["pca2"]],
                "gray", linewidth=0.8, linestyle="--", alpha=0.5)
    
    ax.set_xlabel("PC1", fontsize=11)
    ax.set_ylabel("PC2", fontsize=11)
    ax.set_title(f"KNN (K={K}) – Vecinos más cercanos\n"
                 f"Clima: {clima} | Área: {area_ha} ha | Proteína: {ganancia_proteina_pct}%",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    # ─────────────────────────────────────────────
    # Graph 2: Distance curve, inverse = affinity
    # ─────────────────────────────────────────────

    ax2 = axes[1]
    ranking = result["ranking"]
    x_range = np.linspace(0, ranking["distancia"].max() * 1.5, 300)
    y_afinidad = 1 / (1 + x_range)
    
    ax2.plot(x_range, y_afinidad, color="#0F6E56", linewidth=2.5,
             label="Curva afinidad KNN")
    ax2.axhline(y=0.5, color="#EF9F27", linestyle="--", linewidth=1.5,
                label="Umbral (0.5)")
    
    for _, row in ranking.iterrows():
        color = "#1D9E75" if row["variedad"] == result["variedad"] else "#4A90D9"
        ax2.scatter(row["distancia"], row["afinidad_ajustada"],
                    s=100, color=color, zorder=5)
        ax2.text(row["distancia"], row["afinidad_ajustada"] + 0.02,
                 row["variedad"].split("(")[0].strip()[:18],
                 fontsize=7.5, ha="center")
    
    ax2.set_xlabel("Distancia euclidiana al terreno del usuario", fontsize=11)
    ax2.set_ylabel("Afinidad (1 / 1+distancia)", fontsize=11)
    ax2.set_title("KNN – Curva de Afinidad por Distancia", fontsize=12, fontweight="bold")
    ax2.set_ylim(-0.05, 1.05)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
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


def getClusterInfo():
    """Devuelve información resumida de los clusters (para compatibilidad)."""
    if _df is None:
        load_model_K()
    return _df.groupby("clima")[["score_proteina", "area_sembrada_ha"]].mean()
def getModelMetrics():
    """
    Retorna métricas principales del modelo KNN Classifier.
    """
    if _knn_classifier is None:
        load_model_K()

    accuracy = accuracy_score(y_test_eval, y_pred_eval)
    precision = precision_score(y_test_eval, y_pred_eval, zero_division=0)
    recall = recall_score(y_test_eval, y_pred_eval, zero_division=0)
    f1 = f1_score(y_test_eval, y_pred_eval, zero_division=0)
    auc = roc_auc_score(y_test_eval, y_prob_eval)

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
    Retorna el reporte completo de clasificación.
    """
    if _knn_classifier is None:
        load_model_K()

    return classification_report(
        y_test_eval,
        y_pred_eval,
        target_names=["Baja aptitud", "Alta aptitud"],
        output_dict=True,
        zero_division=0
    )


def generateConfusionMatrixPlot():
    """
    Genera la matriz de confusión del KNN Classifier en formato base64.
    """
    if _knn_classifier is None:
        load_model_K()

    cm = confusion_matrix(y_test_eval, y_pred_eval)

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
        "Matriz de Confusión – KNN",
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
    Genera la curva ROC del KNN Classifier en formato base64.
    """
    if _knn_classifier is None:
        load_model_K()

    fpr, tpr, thresholds = roc_curve(y_test_eval, y_prob_eval)
    auc = roc_auc_score(y_test_eval, y_prob_eval)

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
        "Curva ROC – KNN",
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