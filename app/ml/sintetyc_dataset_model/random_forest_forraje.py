import io, base64, os, gc
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from sklearn.metrics import accuracy_score,precision_score,recall_score,f1_score,confusion_matrix,ConfusionMatrixDisplay,roc_curve,roc_auc_score,classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ─────────────────────────────────────────────
# 1. Load dataset
# ─────────────────────────────────────────────
#Path from this file: app/ml/sintetyc_dataset_model/logistic_regression_forraje.py
# go up 3 levels to reach the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

#Look for the file in the 'data' folder in the root directory
DATA_PATH = os.path.join(ROOT_DIR, "data", "forrajeo_1000.csv")

df = pd.read_csv(DATA_PATH)
# ─────────────────────────────────────────────
# 2. Feature engineering  (midpoints)
# ─────────────────────────────────────────────
df["ph_mid"]      = (df["ph_min"]      + df["ph_max"])      / 2
df["humedad_mid"] = (df["humedad_min"] + df["humedad_max"]) / 2
df["altitud_mid"] = (df["altitud_min"] + df["altitud_max"]) / 2
df["temp_mid"]    = (df["temp_min"]    + df["temp_max"])    / 2

# ─────────────────────────────────────────────
# 3. Composite score + binary target
# ─────────────────────────────────────────────
df["composite"] = (
    0.30 * df["ph_mid"]      / 9    +
    0.20 * df["humedad_mid"] / 100  +
    0.30 * df["altitud_mid"] / 4000 +
    0.20 * df["temp_mid"]    / 45
)

threshold = df["composite"].mean()
df["optimal"] = (df["composite"] > threshold).astype(int)

# ─────────────────────────────────────────────
# 4. All 8 range variables as features
# ─────────────────────────────────────────────
FEATURES = ["ph_min","ph_max","humedad_min","humedad_max",
            "altitud_min","altitud_max","temp_min","temp_max"]

X = df[FEATURES]
y = df["optimal"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ─────────────────────────────────────────────
# 5. Train / test split + Random Forest
# n_estimators=100 trees, same random_state
# for reproducibility
# ─────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

model = RandomForestClassifier(
    n_estimators=100,
    max_depth=None,
    min_samples_split=2,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

y_pred    = model.predict(X_test)
train_acc = accuracy_score(y_train, model.predict(X_train))
test_acc  = accuracy_score(y_test, y_pred)

# feature importances, unique to RF
feat_importances = pd.Series(model.feature_importances_, index=FEATURES)


# ─────────────────────────────────────────────────────────────────
# FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def getThreshold():
    """Returns the composite threshold."""
    return threshold


def compute_affinity(row, user_ph, user_hum, user_alt, user_temp):
    ph_ok  = row["ph_min"]      <= user_ph   <= row["ph_max"]
    hum_ok = row["humedad_min"] <= user_hum  <= row["humedad_max"]
    alt_ok = row["altitud_min"] <= user_alt  <= row["altitud_max"]
    tmp_ok = row["temp_min"]    <= user_temp <= row["temp_max"]
    return 0.30*ph_ok + 0.20*hum_ok + 0.30*alt_ok + 0.20*tmp_ok


def user_features(user_ph, user_hum, user_alt, user_temp):
    """8-feature vector from user terrain point values."""
    return [[user_ph, user_ph, user_hum, user_hum,
             user_alt, user_alt, user_temp, user_temp]]


def predictCropCategory(user_ph, user_hum, user_alt, user_temp):
    """
    Random Forest prediction: returns (category, probability).
    Mirrors predictOilCategory(year).
    RF averages the vote probabilities of all 100 decision trees:
        P(optimal) = (trees voting 1) / total_trees
    """
    feat_scaled = scaler.transform(user_features(user_ph, user_hum, user_alt, user_temp))
    prob        = model.predict_proba(feat_scaled)[0][1]
    category    = model.predict(feat_scaled)[0]
    return int(category), float(prob)


def getBestCrop(user_ph, user_hum, user_alt, user_temp, top_n=10):
    #Ranks all crops by affinity for the user terrain
    df_copy = df.copy()
    df_copy["affinity"] = df_copy.apply(
        lambda row: compute_affinity(row, user_ph, user_hum, user_alt, user_temp), axis=1
    )
    return (
        df_copy.groupby("nombre")["affinity"]
        .mean().reset_index()
        .sort_values("affinity", ascending=False)
        .head(top_n)
    )


def generatePlot(user_ph=None, user_hum=None, user_alt=None, user_temp=None):
    #Main plot: RF vote-probability curve along composite axis
    # - Real data scatter (0/1)
    # - Smooth RF probability curve (avg tree votes)
    # - Decision threshold line at 0.5
    # - User prediction point
    
    fig, ax = plt.subplots(figsize=(10, 6))

    df_sorted = df.sort_values("composite")
    X_plot = df_sorted["composite"].values
    Y_plot = df_sorted["optimal"].values

    ax.scatter(X_plot, Y_plot, alpha=0.4, s=20, color="#1D9E75",
               label="Real Data (0 = Not optimal, 1 = Optimal)")

    # smooth probability curve: vary composite, keep other features at mean
    x_min = df["composite"].min() - 0.02
    x_max = df["composite"].max() + 0.02
    X_smooth = np.linspace(x_min, x_max, 500)

    means = df[FEATURES].mean()
    smooth_feats = [
        [
            means["ph_min"]      * (c / df["composite"].mean()),
            means["ph_max"]      * (c / df["composite"].mean()),
            means["humedad_min"] * (c / df["composite"].mean()),
            means["humedad_max"] * (c / df["composite"].mean()),
            means["altitud_min"] * (c / df["composite"].mean()),
            means["altitud_max"] * (c / df["composite"].mean()),
            means["temp_min"]    * (c / df["composite"].mean()),
            means["temp_max"]    * (c / df["composite"].mean()),
        ]
        for c in X_smooth
    ]

    smooth_scaled = scaler.transform(smooth_feats)
    y_prob_smooth = model.predict_proba(smooth_scaled)[:, 1]

    ax.plot(X_smooth, y_prob_smooth, color="#0F6E56", linewidth=2.5,
            label="Random Forest Probability Curve (100 trees)")

    ax.axhline(y=0.5, color="#EF9F27", linestyle="--", linewidth=1.5,
               label="Threshold (0.5)")

    if all(v is not None for v in [user_ph, user_hum, user_alt, user_temp]):
        category, prob = predictCropCategory(user_ph, user_hum, user_alt, user_temp)
        comp_val = (0.30*user_ph/9 + 0.20*user_hum/100 +
                    0.30*user_alt/4000 + 0.20*user_temp/45)
        point_color = "green" if category == 1 else "orange"

        ax.scatter(comp_val, prob, s=180, color=point_color, zorder=5,
                   label=f"Prediction ({'Optimal' if category==1 else 'Not Optimal'})")
        ax.text(comp_val, prob + 0.05,
                f"({round(comp_val,3)}, {round(prob,3)})",
                ha="center", fontsize=9, fontweight="bold", color=point_color)

        ranked    = getBestCrop(user_ph, user_hum, user_alt, user_temp, top_n=1)
        best_name = ranked.iloc[0]["nombre"]
        best_aff  = ranked.iloc[0]["affinity"]
        ax.annotate(
            f"Best crop: {best_name}\nAffinity: {best_aff:.0%}",
            xy=(comp_val, prob),
            xytext=(comp_val + 0.015, prob - 0.15),
            fontsize=9,
            arrowprops=dict(arrowstyle="->", color="gray"),
            bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray")
        )

    ax.set_xlabel("Composite Terrain Score (pH · Humidity · Altitude · Temp)", fontsize=12)
    ax.set_ylabel("Probability of Optimal Crop (avg. 100 trees)", fontsize=12)
    ax.set_title(
        f"Random Forest – Forage Crop Suitability Classification\n"
        f"Train acc: {train_acc:.2%}  |  Test acc: {test_acc:.2%}  |  Trees: 100",
        fontsize=13, fontweight="bold"
    )
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(x_min, x_max)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close('all')  # Close all pending figures
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()  # Force memory cleanup
    
    return result


def generateRankingPlot(user_ph, user_hum, user_alt, user_temp, top_n=10):
    #Bar chart of top N crops by affinity
    ranked = getBestCrop(user_ph, user_hum, user_alt, user_temp, top_n)
    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#1D9E75" if a >= 0.5 else "#EF9F27" for a in ranked["affinity"]]
    bars = ax.barh(ranked["nombre"][::-1], ranked["affinity"][::-1]*100,
                   color=colors[::-1], edgecolor="white")
    ax.axvline(x=50, color="#EF9F27", linestyle="--", linewidth=1.5, label="Threshold 50%")
    ax.set_xlabel("Affinity Score (%)", fontsize=12)
    ax.set_title(
        f"Top {top_n} Forage Crops – Random Forest Affinity\n"
        f"pH={user_ph} | Hum={user_hum}% | Alt={user_alt}m | Temp={user_temp}°C",
        fontsize=13, fontweight="bold"
    )
    ax.set_xlim(0, 110)
    ax.grid(True, axis="x", alpha=0.3)
    for bar, val in zip(bars[::-1], ranked["affinity"]):
        ax.text(val*100+1, bar.get_y()+bar.get_height()/2,
                f"{val:.0%}", va="center", fontsize=9, fontweight="bold")
    green_p  = mpatches.Patch(color="#1D9E75", label="Optimal (≥50%)")
    orange_p = mpatches.Patch(color="#EF9F27", label="Suboptimal (<50%)")
    ax.legend(handles=[green_p, orange_p], loc="lower right")
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close('all')  # Close all pending figures
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()  # Force memory cleanup
    
    return result


def generateFeatureImportancePlot():
    #Extra RF chart: variable importance across all 100 trees
    # shows which terrain variable matters most for classification.
    fi = feat_importances.sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#1D9E75" if v >= fi.mean() else "#9FE1CB" for v in fi]
    bars = ax.barh(fi.index, fi.values * 100, color=colors, edgecolor="white")
    ax.axvline(x=fi.mean()*100, color="#EF9F27", linestyle="--",
               linewidth=1.5, label=f"Mean importance ({fi.mean()*100:.1f}%)")
    ax.set_xlabel("Feature Importance (%)", fontsize=12)
    ax.set_title("Random Forest – Feature Importance\n(contribution of each variable to the model)",
                 fontsize=13, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)
    for bar, val in zip(bars, fi.values):
        ax.text(val*100+0.3, bar.get_y()+bar.get_height()/2,
                f"{val*100:.1f}%", va="center", fontsize=9)
    ax.legend()
    
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close('all')  # Close all pending figures
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()  # Force memory cleanup
    
    return result
def getModelMetrics():
    """
    Retorna métricas principales del modelo Random Forest.
    """
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    y_prob_test = model.predict_proba(X_test)[:, 1]
    
    accuracy_test = accuracy_score(y_test, y_pred_test)
    precision = precision_score(y_test, y_pred_test, zero_division=0)
    recall = recall_score(y_test, y_pred_test, zero_division=0)
    f1 = f1_score(y_test, y_pred_test, zero_division=0)
    auc = roc_auc_score(y_test, y_prob_test)
    
    return {
        "exactitud": float(accuracy_test),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(auc),
        "train_accuracy": float(accuracy_score(y_train, y_pred_train)),
        "test_accuracy": float(accuracy_test)
    }


def getClassificationReport():
    """
    Retorna el reporte de clasificación como diccionario.
    """
    return classification_report(
        y_test,
        y_pred,
        target_names=["No óptimo", "Óptimo"],
        output_dict=True,
        zero_division=0
    )


def generateConfusionMatrixPlot():
    """
    Genera la matriz de confusión del modelo Random Forest en formato base64.
    """
    cm = confusion_matrix(y_test, y_pred)
    
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
        "Matriz de Confusión – Random Forest",
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
    Genera la curva ROC del modelo Random Forest en formato base64.
    """
    y_prob_test = model.predict_proba(X_test)[:, 1]
    fpr, tpr, thresholds = roc_curve(y_test, y_prob_test)
    auc = roc_auc_score(y_test, y_prob_test)
    
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
        "Curva ROC – Random Forest",
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