# app/ml/DANE_real_dataset_model/kmeans_Dane.py
import io, base64, os, gc
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
def load_model(data_path: str = None):
    # Upload a CSV file and train once. Avoid retraining
    global _df, _scaler, _kmeans, _pca
    
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

    X = _df[FEATURES].copy()
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)

    _kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
    _df["cluster"] = _kmeans.fit_predict(X_scaled)

    _pca = PCA(n_components=2, random_state=42)
    X_pca = _pca.fit_transform(X_scaled)
    _df["pca1"] = X_pca[:, 0]
    _df["pca2"] = X_pca[:, 1]

def getClusterInfo():
    # Returns a summary for each cluster
    if _df is None:
        load_model()
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
        load_model()
    
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
        load_model()
    
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