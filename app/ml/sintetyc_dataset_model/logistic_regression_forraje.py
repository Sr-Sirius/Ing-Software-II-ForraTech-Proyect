import io, base64, os, gc
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix,ConfusionMatrixDisplay,accuracy_score,precision_score,recall_score,f1_score,roc_curve,roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
# ── 1. Load dataset ──────────────────────────────────────────────

#Path from this file: app/ml/sintetyc_dataset_model/logistic_regression_forraje.py
# go up 3 levels to reach the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

#Look for the file in the ‘data’ folder in the root directory
DATA_PATH = os.path.join(ROOT_DIR, "data", "forrajeo_1000.csv")

df = pd.read_csv(DATA_PATH)
# ── 2. Feature engineering ───────────────────────────────────────
df["ph_mid"]      = (df["ph_min"]      + df["ph_max"])      / 2
df["humedad_mid"] = (df["humedad_min"] + df["humedad_max"]) / 2
df["altitud_mid"] = (df["altitud_min"] + df["altitud_max"]) / 2
df["temp_mid"]    = (df["temp_min"]    + df["temp_max"])    / 2

# ── 3. Affinity ──────────────────────────────────────────────────
def compute_affinity(row, user_ph, user_hum, user_alt, user_temp):
    ph_ok  = row["ph_min"]      <= user_ph   <= row["ph_max"]
    hum_ok = row["humedad_min"] <= user_hum  <= row["humedad_max"]
    alt_ok = row["altitud_min"] <= user_alt  <= row["altitud_max"]
    tmp_ok = row["temp_min"]    <= user_temp <= row["temp_max"]
    return 0.30 * ph_ok + 0.20 * hum_ok + 0.30 * alt_ok + 0.20 * tmp_ok

# ── 4. Composite score & binary target ───────────────────────────
df["composite"] = (
    0.30 * df["ph_mid"]      / 9    +
    0.20 * df["humedad_mid"] / 100  +
    0.30 * df["altitud_mid"] / 4000 +
    0.20 * df["temp_mid"]    / 45
)
_threshold    = df["composite"].mean()
df["optimal"] = (df["composite"] > _threshold).astype(int)

# ── 5. Train model ───────────────────────────────────────────────
_X = df[["composite"]]
_y = df["optimal"]

_scaler = StandardScaler()
_X_sc = _scaler.fit_transform(_X)

_X_train, _X_test, _y_train, _y_test = train_test_split(
    _X_sc,
    _y,
    test_size=0.25,
    random_state=42,
    stratify=_y
)

_model = LogisticRegression(max_iter=1000)
_model.fit(_X_train, _y_train)

# Predicciones para métricas
_y_pred = _model.predict(_X_test)
_y_prob = _model.predict_proba(_X_test)[:, 1]

# ── Helpers ──────────────────────────────────────────────────────
def _user_composite(ph, hum, alt, temp):
    return (0.30*ph/9 + 0.20*hum/100 + 0.30*alt/4000 + 0.20*temp/45)

# ── Public API ───────────────────────────────────────────────────
def getThreshold():
    return _threshold

def predictCropCategory(ph, hum, alt, temp):
    comp   = _user_composite(ph, hum, alt, temp)
    cs     = _scaler.transform([[comp]])
    prob   = _model.predict_proba(cs)[0][1]
    cat    = _model.predict(cs)[0]
    return int(cat), float(prob)

def getBestCrop(ph, hum, alt, temp, top_n=10):
    scores  = df.apply(lambda r: compute_affinity(r, ph, hum, alt, temp), axis=1)
    df_copy = df.copy()
    df_copy["affinity"] = scores
    return (
        df_copy.groupby("nombre")["affinity"]
        .mean().reset_index()
        .sort_values("affinity", ascending=False)
        .head(top_n)
    )

def generatePlot(ph=None, hum=None, alt=None, temp=None):
    fig, ax = plt.subplots(figsize=(10, 6))
    ds = df.sort_values("composite")
    ax.scatter(ds["composite"], ds["optimal"], alpha=0.4, s=20,
               color="#1D9E75", label="Datos reales (0=No óptimo, 1=Óptimo)")

    x_min = df["composite"].min() - 0.02
    x_max = df["composite"].max() + 0.02
    Xs  = np.linspace(x_min, x_max, 500).reshape(-1,1)
    Xss = _scaler.transform(Xs)
    ax.plot(Xs, _model.predict_proba(Xss)[:,1], color="#0F6E56",
            linewidth=2.5, label="Curva Regresión Logística")
    ax.axhline(0.5, color="#EF9F27", linestyle="--",
               linewidth=1.5, label="Umbral (0.5)")

    if all(v is not None for v in [ph, hum, alt, temp]):
        cat, prob  = predictCropCategory(ph, hum, alt, temp)
        comp_val   = _user_composite(ph, hum, alt, temp)
        pc = "green" if cat == 1 else "orange"
        ax.scatter(comp_val, prob, s=180, color=pc, zorder=5,
                   label=f"Predicción ({cat})")
        ax.text(comp_val, prob+0.05,
                f"({comp_val:.3f}, {prob:.3f})",
                ha="center", fontsize=9, fontweight="bold", color=pc)
        ranked = getBestCrop(ph, hum, alt, temp, top_n=1)
        ax.annotate(
            f"Mejor: {ranked.iloc[0]['nombre']}\nAfinidad: {ranked.iloc[0]['affinity']:.0%}",
            xy=(comp_val, prob), xytext=(comp_val+0.015, prob-0.15),
            fontsize=9, arrowprops=dict(arrowstyle="->", color="gray"),
            bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray")
        )

    ax.set_xlabel("Puntaje Compuesto (pH · Humedad · Altitud · Temp)", fontsize=12)
    ax.set_ylabel("Probabilidad de Condiciones Óptimas", fontsize=12)
    ax.set_title("Regresión Logística – Aptitud de Cultivos Forrajeros",
                 fontsize=14, fontweight="bold")
    ax.set_ylim(-0.05, 1.05); ax.set_xlim(x_min, x_max)
    ax.grid(True, alpha=0.3); ax.legend(loc="best")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    plt.close('all')  #Close all pending items
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()  #Force memory cleanup
    return result

def generateRankingPlot(ph, hum, alt, temp, top_n=10):
    ranked = getBestCrop(ph, hum, alt, temp, top_n)
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#1D9E75" if a>=0.5 else "#EF9F27" for a in ranked["affinity"]]
    bars   = ax.barh(ranked["nombre"][::-1], ranked["affinity"][::-1]*100,
                     color=colors[::-1], edgecolor="white", linewidth=0.5)
    ax.axvline(50, color="#EF9F27", linestyle="--", linewidth=1.5, label="Umbral 50%")
    ax.set_xlabel("Afinidad (%)", fontsize=12)
    ax.set_title(
        f"Top {top_n} Cultivos – Afinidad con el Terreno\n"
        f"pH={ph} | Hum={hum}% | Alt={alt}m | Temp={temp}°C",
        fontsize=13, fontweight="bold"
    )
    ax.set_xlim(0, 105); ax.grid(True, axis="x", alpha=0.3)
    for bar, val in zip(bars[::-1], ranked["affinity"]):
        ax.text(val*100+1, bar.get_y()+bar.get_height()/2,
                f"{val:.0%}", va="center", fontsize=9, fontweight="bold")
    ax.legend(handles=[
        mpatches.Patch(color="#1D9E75", label="Óptimo (≥50%)"),
        mpatches.Patch(color="#EF9F27", label="Subóptimo (<50%)")
    ], loc="lower right")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    plt.close('all')  #Close all pending items
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()  #Force memory cleanup
    return result
def getModelMetrics():
    """
    Retorna métricas principales del modelo:
    exactitud, precisión, recall, F1 y AUC ROC.
    """
    accuracy = accuracy_score(_y_test, _y_pred)
    precision = precision_score(_y_test, _y_pred, zero_division=0)
    recall = recall_score(_y_test, _y_pred, zero_division=0)
    f1 = f1_score(_y_test, _y_pred, zero_division=0)
    auc = roc_auc_score(_y_test, _y_prob)

    return {
        "exactitud": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(auc)
    }


def generateConfusionMatrixPlot():
    """
    Genera matriz de confusión en formato base64.
    """
    cm = confusion_matrix(_y_test, _y_pred)

    fig, ax = plt.subplots(figsize=(6, 5))

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["No óptimo", "Óptimo"]
    )

    disp.plot(
        ax=ax,
        cmap="Greens",
        colorbar=False,
        values_format="d"
    )

    ax.set_title(
        "Matriz de Confusión – Regresión Logística",
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
    fpr, tpr, thresholds = roc_curve(_y_test, _y_prob)
    auc = roc_auc_score(_y_test, _y_prob)

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
        "Curva ROC – Regresión Logística",
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