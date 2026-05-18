import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io, base64
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
# ─────────────────────────────────────────────
# 1. Load dataset
# ─────────────────────────────────────────────
df = pd.read_csv("forrajeo_1000.csv")
# ─────────────────────────────────────────────
# 2. Feature engineering
# compute the midpoint of each range variable
# ─────────────────────────────────────────────
df["ph_mid"]       = (df["ph_min"]       + df["ph_max"])       / 2
df["humedad_mid"]  = (df["humedad_min"]  + df["humedad_max"])  / 2
df["altitud_mid"]  = (df["altitud_min"]  + df["altitud_max"])  / 2
df["temp_mid"]     = (df["temp_min"]     + df["temp_max"])     / 2
# ─────────────────────────────────────────────
# 3. Build a composite suitability score
# used to create the binary target y
# ─────────────────────────────────────────────
def compute_affinity(row, user_ph, user_hum, user_alt, user_temp):
    # ─────────────────────────────────────────────
    # returns a score 0-1 representing how well the user terrain
    # fits within the crop's tolerance ranges.
    # weights: ph 30%, altitud 30%, humedad 20%, temp 20%
    # ─────────────────────────────────────────────
    ph_ok  = user_ph   >= row["ph_min"]      and user_ph   <= row["ph_max"]
    hum_ok = user_hum  >= row["humedad_min"] and user_hum  <= row["humedad_max"]
    alt_ok = user_alt  >= row["altitud_min"] and user_alt  <= row["altitud_max"]
    tmp_ok = user_temp >= row["temp_min"]    and user_temp <= row["temp_max"]
    return 0.30 * ph_ok + 0.20 * hum_ok + 0.30 * alt_ok + 0.20 * tmp_ok
# ─────────────────────────────────────────────
# 4. Composite X: weighted midpoint score
# the logistic regression model uses a single 
# independent variable (X) to make predictions.
# ─────────────────────────────────────────────
df["composite"] = (
    0.30 * df["ph_mid"] / 9 +          # normalised pH   (max ~9)
    0.20 * df["humedad_mid"] / 100 +   # normalised hum  (max 100)
    0.30 * df["altitud_mid"] / 4000 +  # normalised alt  (max 4000)
    0.20 * df["temp_mid"] / 45         # normalised temp (max 45)
)
# ─────────────────────────────────────────────
# 5. Binary target: 1 = above-median composite
# ─────────────────────────────────────────────
threshold = df["composite"].mean()
df["optimal"] = (df["composite"] > threshold).astype(int)
# ─────────────────────────────────────────────
# 6. Train logistic regression
# ─────────────────────────────────────────────
X = df[["composite"]]   # independent variable (composite score)
y = df["optimal"]       # dependent variable   (0 / 1)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

model = LogisticRegression(max_iter=1000)
model.fit(X_scaled, y)
# ─────────────────────────────────────────────────────────────────
# FUNCTIONS
# ─────────────────────────────────────────────────────────────────
# 7. returns the composite threshold, analog of getThreshold.
# ─────────────────────────────────────────────────────────────────
def getThreshold():
    return threshold
# ─────────────────────────────────────────────────────────────────
# 8.Converts user terrain values into the same composite scorE
# used to train the model.
# ─────────────────────────────────────────────────────────────────
def user_composite(user_ph, user_hum, user_alt, user_temp):
    return (
        0.30 * user_ph   / 9    +
        0.20 * user_hum  / 100  +
        0.30 * user_alt  / 4000 +
        0.20 * user_temp / 45
    )
# ─────────────────────────────────────────────────────────────────
# 9. Predicts whether the terrain is optimal (1) or not (0),
# and returns the logistic probability.
# ─────────────────────────────────────────────────────────────────
def predictCropCategory(user_ph, user_hum, user_alt, user_temp):
    comp = user_composite(user_ph, user_hum, user_alt, user_temp)
    comp_scaled = scaler.transform([[comp]])
    prob     = model.predict_proba(comp_scaled)[0][1]
    category = model.predict(comp_scaled)[0]
    return int(category), float(prob)
# ─────────────────────────────────────────────────────────────────
# 10. Compares user terrain against all 1000 rows in the dataset
# and returns the top_n crops ranked by affinity score.
# ─────────────────────────────────────────────────────────────────
def getBestCrop(user_ph, user_hum, user_alt, user_temp, top_n=10):
    scores = df.apply(
        lambda row: compute_affinity(row, user_ph, user_hum, user_alt, user_temp),
        axis=1
    )
    df_copy = df.copy()
    df_copy["affinity"] = scores
    ranked = (
        df_copy.groupby("nombre")["affinity"]
        .mean()
        .reset_index()
        .sort_values("affinity", ascending=False)
        .head(top_n)
    )
    return ranked
# ─────────────────────────────────────────────────────────────────
# 11. Generates the sigmoid logistic regression plot.
# Mirrors generatePlot:
# - scatter of real data points  (0 / 1)
# - smooth sigmoid curve
# - decision threshold line
# - user prediction point 
# ─────────────────────────────────────────────────────────────────
def generatePlot(user_ph=None, user_hum=None, user_alt=None, user_temp=None):
    fig, ax = plt.subplots(figsize=(10, 6))

    # sort data (mirrors df_sorted = df_grouped.sort_values)
    df_sorted = df.sort_values("composite")

    X_plot = df_sorted["composite"].values   # independent variable
    Y_plot = df_sorted["optimal"].values     # dependent variable (0 / 1)

    # real data scatter
    ax.scatter(X_plot, Y_plot, alpha=0.4, s=20, color="#1D9E75",
               label="Real Data (0 = Not optimal, 1 = Optimal)")

    # smooth x range (mirrors np.linspace approach)
    x_min = df["composite"].min() - 0.02
    x_max = df["composite"].max() + 0.02
    X_smooth = np.linspace(x_min, x_max, 500).reshape(-1, 1)

    # scale for prediction
    X_smooth_scaled = scaler.transform(X_smooth)

    # sigmoid probabilities
    y_prob_smooth = model.predict_proba(X_smooth_scaled)[:, 1]

    # smooth sigmoid curve
    ax.plot(X_smooth, y_prob_smooth, color="#0F6E56", linewidth=2.5,
            label="Logistic Regression Curve")

    # decision threshold line
    ax.axhline(y=0.5, color="#EF9F27", linestyle="--", linewidth=1.5,
               label="Threshold (0.5)")

    # user prediction point
    if all(v is not None for v in [user_ph, user_hum, user_alt, user_temp]):
        category, prob = predictCropCategory(user_ph, user_hum, user_alt, user_temp)
        comp_val = user_composite(user_ph, user_hum, user_alt, user_temp)

        point_color = "green" if category == 1 else "orange"
        label_txt   = f"Prediction ({category})"

        ax.scatter(comp_val, prob, s=180, color=point_color,
                   zorder=5, label=label_txt)
        ax.text(comp_val, prob + 0.05,
                f"({round(comp_val, 3)}, {round(prob, 3)})",
                ha="center", fontsize=9, fontweight="bold", color=point_color)

        # annotate best crop
        ranked = getBestCrop(user_ph, user_hum, user_alt, user_temp, top_n=1)
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

    # labels and title (mirrors original)
    ax.set_xlabel("Composite Terrain Score (pH · Humidity · Altitude · Temp)", fontsize=12)
    ax.set_ylabel("Probability of Optimal Crop Conditions", fontsize=12)
    ax.set_title(
        "Logistic Regression – Forage Crop Suitability Classification",
        fontsize=14, fontweight="bold"
    )

    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(x_min, x_max)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    # save to base64 (mirrors original)
    img = io.BytesIO()
    fig.savefig(img, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()
# ─────────────────────────────────────────────────────────────────
# 13. Bar chart showing top N crops by affinity for the user terrain
# companion chart to the sigmoid plot.
# ─────────────────────────────────────────────────────────────────
def generateRankingPlot(user_ph, user_hum, user_alt, user_temp, top_n=10):
    ranked = getBestCrop(user_ph, user_hum, user_alt, user_temp, top_n)

    fig, ax = plt.subplots(figsize=(10, 5))
    colors = ["#1D9E75" if a >= 0.5 else "#EF9F27" for a in ranked["affinity"]]
    bars = ax.barh(ranked["nombre"][::-1], ranked["affinity"][::-1] * 100,
                   color=colors[::-1], edgecolor="white", linewidth=0.5)

    ax.axvline(x=50, color="#EF9F27", linestyle="--", linewidth=1.5,
               label="Threshold 50%")
    ax.set_xlabel("Affinity Score (%)", fontsize=12)
    ax.set_title(
        f"Top {top_n} Forage Crops – Terrain Affinity\n"
        f"pH={user_ph} | Hum={user_hum}% | Alt={user_alt}m | Temp={user_temp}°C",
        fontsize=13, fontweight="bold"
    )
    ax.set_xlim(0, 105)
    ax.grid(True, axis="x", alpha=0.3)

    for bar, val in zip(bars[::-1], ranked["affinity"]):
        ax.text(val * 100 + 1, bar.get_y() + bar.get_height() / 2,
                f"{val:.0%}", va="center", fontsize=9, fontweight="bold")

    green_patch  = mpatches.Patch(color="#1D9E75", label="Optimal (≥50%)")
    orange_patch = mpatches.Patch(color="#EF9F27", label="Suboptimal (<50%)")
    ax.legend(handles=[green_patch, orange_patch], loc="lower right")

    img = io.BytesIO()
    fig.savefig(img, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()