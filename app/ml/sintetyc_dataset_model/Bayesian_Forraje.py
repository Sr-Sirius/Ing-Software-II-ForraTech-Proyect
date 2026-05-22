import io, base64, os, gc
import pandas as pd
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ─────────────────────────────────────────────
# 1. Load dataset
# ─────────────────────────────────────────────
# Path from this file: app/ml/sintetyc_dataset_model/Bayesian_Forraje.py
# go up 3 levels to reach the project root
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))

# Look for the file in the 'data' folder in the root directory
DATA_PATH = os.path.join(ROOT_DIR, "data", "forrajeo_1000.csv")

df = pd.read_csv(DATA_PATH)

# ─────────────────────────────────────────────
# 2. Feature engineering
# Midpoint of each range variable
# ─────────────────────────────────────────────
df["ph_mid"]      = (df["ph_min"]      + df["ph_max"])      / 2
df["humedad_mid"] = (df["humedad_min"] + df["humedad_max"]) / 2
df["altitud_mid"] = (df["altitud_min"] + df["altitud_max"]) / 2
df["temp_mid"]    = (df["temp_min"]    + df["temp_max"])    / 2

# ─────────────────────────────────────────────
# 3. Composite suitability score (same as LR)
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
# 4. Feature matrix: all 8 range variables
# Bayesian benefits from multiple features
# ─────────────────────────────────────────────
FEATURES = ["ph_min","ph_max","humedad_min","humedad_max",
            "altitud_min","altitud_max","temp_min","temp_max"]

X = df[FEATURES]
y = df["optimal"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ─────────────────────────────────────────────
# 5. Train / test split + Gaussian Naive Bayes
# ─────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42
)

model = GaussianNB()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
train_acc = accuracy_score(y_train, model.predict(X_train))
test_acc  = accuracy_score(y_test, y_pred)


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
    #Builds the 8-feature vector for the user terrain.
    # uses the user value as both min and max
    # point estimate within the range space
    return [[user_ph, user_ph, user_hum, user_hum,
             user_alt, user_alt, user_temp, user_temp]]


def predictCropCategory(user_ph, user_hum, user_alt, user_temp):
    #Naive Bayes prediction: returns (category, probability).
    # mses Bayes theorem:
    # p(optimal | features) = P(features | optimal) * P(optimal) / P(features)
    # gaussianNB estimates P(features | class) as a Gaussian distribution.

    feat_scaled = scaler.transform(user_features(user_ph, user_hum, user_alt, user_temp))
    prob        = model.predict_proba(feat_scaled)[0][1]
    category    = model.predict(feat_scaled)[0]
    return int(category), float(prob)


def getBestCrop(user_ph, user_hum, user_alt, user_temp, top_n=10):
    """Ranks all crops by affinity for the user terrain."""
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
    #Main plot: Bayesian posterior probability curve
    # - Real data scatter (0/1)
    # - Smooth posterior P(optimal | composite) curve
    # - Decision threshold line at 0.5
    # - User prediction point
    fig, ax = plt.subplots(figsize=(10, 6))

    df_sorted = df.sort_values("composite")
    X_plot = df_sorted["composite"].values
    Y_plot = df_sorted["optimal"].values

    # real data scatter
    ax.scatter(X_plot, Y_plot, alpha=0.4, s=20, color="#1D9E75",
               label="Real Data (0 = Not optimal, 1 = Optimal)")

    # smooth posterior curve using composite as proxy feature
    x_min = df["composite"].min() - 0.02
    x_max = df["composite"].max() + 0.02
    X_smooth = np.linspace(x_min, x_max, 500)

    # reconstruct 8-feature vectors along the composite axis
    # keep non-composite features at their dataset mean
    means = df[FEATURES].mean()
    smooth_feats = []
    for c in X_smooth:
        row_feat = [
            means["ph_min"]      * (c / df["composite"].mean()),
            means["ph_max"]      * (c / df["composite"].mean()),
            means["humedad_min"] * (c / df["composite"].mean()),
            means["humedad_max"] * (c / df["composite"].mean()),
            means["altitud_min"] * (c / df["composite"].mean()),
            means["altitud_max"] * (c / df["composite"].mean()),
            means["temp_min"]    * (c / df["composite"].mean()),
            means["temp_max"]    * (c / df["composite"].mean()),
        ]
        smooth_feats.append(row_feat)

    smooth_scaled    = scaler.transform(smooth_feats)
    y_prob_smooth    = model.predict_proba(smooth_scaled)[:, 1]

    ax.plot(X_smooth, y_prob_smooth, color="#0F6E56", linewidth=2.5,
            label="Naive Bayes Posterior P(optimal | terrain)")

    # threshold line
    ax.axhline(y=0.5, color="#EF9F27", linestyle="--", linewidth=1.5,
               label="Threshold (0.5)")

    # user prediction point
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
    ax.set_ylabel("Posterior Probability P(Optimal | Terrain)", fontsize=12)
    ax.set_title(
        f"Naive Bayes (Bayesian Theory) – Forage Crop Suitability\n"
        f"Train acc: {train_acc:.2%}  |  Test acc: {test_acc:.2%}",
        fontsize=13, fontweight="bold"
    )
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(x_min, x_max)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    # Memory optimization: close and cleanup
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
        f"Top {top_n} Forage Crops – Bayesian Affinity\n"
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
    
    # Memory optimization: close and cleanup
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close('all')  # Close all pending figures
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()  # Force memory cleanup
    
    return result


def generateFeatureImportancePlot():
    #Extra Bayesian chart: Feature importance using variance analysis
    # shows which terrain variable has the most discriminative power
    # for the Gaussian Naive Bayes model.
    # Calculate variance ratio for each feature between classes
    class_0 = X_scaled[y == 0]
    class_1 = X_scaled[y == 1]
    
    # Calculate separation power (difference in means normalized by variance)
    importance_scores = []
    for i, feature in enumerate(FEATURES):
        mean_diff = abs(class_1[:, i].mean() - class_0[:, i].mean())
        var_pooled = (class_0[:, i].var() + class_1[:, i].var()) / 2
        if var_pooled > 0:
            score = mean_diff / np.sqrt(var_pooled)
        else:
            score = 0
        importance_scores.append(score)
    
    # Normalize to 0-100%
    importance_scores = np.array(importance_scores)
    importance_scores = (importance_scores / importance_scores.sum()) * 100
    
    # Create DataFrame for plotting
    fi = pd.Series(importance_scores, index=FEATURES).sort_values()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#1D9E75" if v >= fi.mean() else "#9FE1CB" for v in fi]
    bars = ax.barh(fi.index, fi.values, color=colors, edgecolor="white")
    ax.axvline(x=fi.mean(), color="#EF9F27", linestyle="--",
               linewidth=1.5, label=f"Mean importance ({fi.mean():.1f}%)")
    ax.set_xlabel("Feature Importance (%)", fontsize=12)
    ax.set_title("Naive Bayes – Feature Separation Power\n(Gaussian discriminative capacity)",
                 fontsize=13, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)
    for bar, val in zip(bars, fi.values):
        ax.text(val+0.3, bar.get_y()+bar.get_height()/2,
                f"{val:.1f}%", va="center", fontsize=9)
    ax.legend()
    
    # Memory optimization: close and cleanup
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close('all')  # Close all pending figures
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()  # Force memory cleanup
    
    return result