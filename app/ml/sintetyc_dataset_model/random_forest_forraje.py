# app/ml/sintetyc_dataset_model/random_forest_forraje.py

import gc

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    ConfusionMatrixDisplay,
    roc_curve,
    roc_auc_score,
    classification_report,
)

from app.ml.pipelines.pipelines_forraje.forraje_preprocessing import (
    prepare_forraje_training_data,
)

from app.ml.utils.utils_forraje.forraje_features import (
    FEATURES_RANGE,
    build_user_range_vector,
    get_best_crops,
    user_composite,
    compute_affinity as compute_forraje_affinity,
)

from app.ml.utils.utils_forraje.plot_utils import fig_to_base64


# ─────────────────────────────────────────────
# 1. Cargar dataset + preparar datos
# ─────────────────────────────────────────────
_data = prepare_forraje_training_data(
    feature_mode="range",
    target_method="mean",
    test_size=0.20,
    random_state=42,
    stratify=True,
)

df = _data["df"]
threshold = _data["threshold"]
FEATURES = FEATURES_RANGE

scaler = _data["scaler"]
X_scaled = _data["X_scaled"]
y = _data["y"]

X_train = _data["X_train"]
X_test = _data["X_test"]
y_train = _data["y_train"]
y_test = _data["y_test"]

# ─────────────────────────────────────────────
# 2. Entrenar Random Forest
# ─────────────────────────────────────────────
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=None,
    min_samples_split=2,
    random_state=42,
    n_jobs=-1,
)

model.fit(X_train, y_train)

y_pred = model.predict(X_test)
train_acc = accuracy_score(y_train, model.predict(X_train))
test_acc = accuracy_score(y_test, y_pred)

feat_importances = pd.Series(
    model.feature_importances_,
    index=FEATURES,
)


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────
def getThreshold():
    return threshold


def compute_affinity(row, user_ph, user_hum, user_alt, user_temp):
    return compute_forraje_affinity(
        row,
        user_ph,
        user_hum,
        user_alt,
        user_temp,
    )


def user_features(user_ph, user_hum, user_alt, user_temp):
    return build_user_range_vector(
        user_ph,
        user_hum,
        user_alt,
        user_temp,
    )


def predictCropCategory(user_ph, user_hum, user_alt, user_temp):
    """
    Random Forest prediction.
    Retorna:
    - category: 1 óptimo / 0 no óptimo
    - probability: P(óptimo)
    """
    feat_scaled = scaler.transform(
        user_features(
            user_ph,
            user_hum,
            user_alt,
            user_temp,
        )
    )

    prob = model.predict_proba(feat_scaled)[0][1]
    category = model.predict(feat_scaled)[0]

    return int(category), float(prob)


def getBestCrop(user_ph, user_hum, user_alt, user_temp, top_n=10):
    return get_best_crops(
        df=df,
        ph=user_ph,
        hum=user_hum,
        alt=user_alt,
        temp=user_temp,
        top_n=top_n,
    )


def generatePlot(user_ph=None, user_hum=None, user_alt=None, user_temp=None):
    fig, ax = plt.subplots(figsize=(10, 6))

    df_sorted = df.sort_values("composite")
    X_plot = df_sorted["composite"].values
    Y_plot = df_sorted["optimal"].values

    ax.scatter(
        X_plot,
        Y_plot,
        alpha=0.4,
        s=20,
        color="#1D9E75",
        label="Real Data (0 = Not optimal, 1 = Optimal)",
    )

    x_min = df["composite"].min() - 0.02
    x_max = df["composite"].max() + 0.02
    X_smooth = np.linspace(x_min, x_max, 500)

    means = df[FEATURES].mean()
    composite_mean = max(float(df["composite"].mean()), 1e-9)

    smooth_feats = []

    for c in X_smooth:
        ratio = c / composite_mean

        smooth_feats.append([
            means["ph_min"] * ratio,
            means["ph_max"] * ratio,
            means["humedad_min"] * ratio,
            means["humedad_max"] * ratio,
            means["altitud_min"] * ratio,
            means["altitud_max"] * ratio,
            means["temp_min"] * ratio,
            means["temp_max"] * ratio,
        ])

    smooth_scaled = scaler.transform(smooth_feats)
    y_prob_smooth = model.predict_proba(smooth_scaled)[:, 1]

    ax.plot(
        X_smooth,
        y_prob_smooth,
        color="#0F6E56",
        linewidth=2.5,
        label="Random Forest Probability Curve (100 trees)",
    )

    ax.axhline(
        y=0.5,
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label="Threshold (0.5)",
    )

    if all(v is not None for v in [user_ph, user_hum, user_alt, user_temp]):
        category, prob = predictCropCategory(
            user_ph,
            user_hum,
            user_alt,
            user_temp,
        )

        comp_val = user_composite(
            user_ph,
            user_hum,
            user_alt,
            user_temp,
        )

        point_color = "green" if category == 1 else "orange"

        ax.scatter(
            comp_val,
            prob,
            s=180,
            color=point_color,
            zorder=5,
            label=f"Prediction ({'Optimal' if category == 1 else 'Not Optimal'})",
        )

        ax.text(
            comp_val,
            prob + 0.05,
            f"({round(comp_val, 3)}, {round(prob, 3)})",
            ha="center",
            fontsize=9,
            fontweight="bold",
            color=point_color,
        )

        ranked = getBestCrop(
            user_ph,
            user_hum,
            user_alt,
            user_temp,
            top_n=1,
        )

        if not ranked.empty:
            best_name = ranked.iloc[0]["nombre"]
            best_aff = ranked.iloc[0]["affinity"]

            ax.annotate(
                f"Best crop: {best_name}\nAffinity: {best_aff:.0%}",
                xy=(comp_val, prob),
                xytext=(comp_val + 0.015, prob - 0.15),
                fontsize=9,
                arrowprops=dict(arrowstyle="->", color="gray"),
                bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray"),
            )

    ax.set_xlabel(
        "Composite Terrain Score (pH · Humidity · Altitude · Temp)",
        fontsize=12,
    )

    ax.set_ylabel(
        "Probability of Optimal Crop (avg. 100 trees)",
        fontsize=12,
    )

    ax.set_title(
        f"Random Forest – Forage Crop Suitability Classification\n"
        f"Train acc: {train_acc:.2%}  |  Test acc: {test_acc:.2%}  |  Trees: 100",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(x_min, x_max)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    return fig_to_base64(fig, plt)


def generateRankingPlot(user_ph, user_hum, user_alt, user_temp, top_n=10):
    ranked = getBestCrop(
        user_ph,
        user_hum,
        user_alt,
        user_temp,
        top_n,
    )

    fig, ax = plt.subplots(figsize=(10, 5))

    colors = ["#1D9E75" if a >= 0.5 else "#EF9F27" for a in ranked["affinity"]]

    bars = ax.barh(
        ranked["nombre"][::-1],
        ranked["affinity"][::-1] * 100,
        color=colors[::-1],
        edgecolor="white",
    )

    ax.axvline(
        x=50,
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label="Threshold 50%",
    )

    ax.set_xlabel("Affinity Score (%)", fontsize=12)

    ax.set_title(
        f"Top {top_n} Forage Crops – Random Forest Affinity\n"
        f"pH={user_ph} | Hum={user_hum}% | Alt={user_alt}m | Temp={user_temp}°C",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlim(0, 110)
    ax.grid(True, axis="x", alpha=0.3)

    for bar, val in zip(bars[::-1], ranked["affinity"]):
        ax.text(
            val * 100 + 1,
            bar.get_y() + bar.get_height() / 2,
            f"{val:.0%}",
            va="center",
            fontsize=9,
            fontweight="bold",
        )

    green_p = mpatches.Patch(color="#1D9E75", label="Optimal (≥50%)")
    orange_p = mpatches.Patch(color="#EF9F27", label="Suboptimal (<50%)")

    ax.legend(handles=[green_p, orange_p], loc="lower right")

    return fig_to_base64(fig, plt)


def generateFeatureImportancePlot():
    fi = feat_importances.sort_values()

    fig, ax = plt.subplots(figsize=(8, 5))

    colors = ["#1D9E75" if v >= fi.mean() else "#9FE1CB" for v in fi]

    bars = ax.barh(
        fi.index,
        fi.values * 100,
        color=colors,
        edgecolor="white",
    )

    ax.axvline(
        x=fi.mean() * 100,
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label=f"Mean importance ({fi.mean() * 100:.1f}%)",
    )

    ax.set_xlabel("Feature Importance (%)", fontsize=12)

    ax.set_title(
        "Random Forest – Feature Importance\n"
        "(contribution of each variable to the model)",
        fontsize=13,
        fontweight="bold",
    )

    ax.grid(True, axis="x", alpha=0.3)

    for bar, val in zip(bars, fi.values):
        ax.text(
            val * 100 + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{val * 100:.1f}%",
            va="center",
            fontsize=9,
        )

    ax.legend()

    return fig_to_base64(fig, plt)


def getModelMetrics():
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    y_prob_test = model.predict_proba(X_test)[:, 1]

    accuracy_test = accuracy_score(y_test, y_pred_test)
    precision = precision_score(y_test, y_pred_test, zero_division=0)
    recall = recall_score(y_test, y_pred_test, zero_division=0)
    f1 = f1_score(y_test, y_pred_test, zero_division=0)

    try:
        auc = roc_auc_score(y_test, y_prob_test)
    except ValueError:
        auc = 0.0

    return {
        "exactitud": float(accuracy_test),
        "accuracy": float(accuracy_test),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "f1": float(f1),
        "roc_auc": float(auc),
        "train_accuracy": float(accuracy_score(y_train, y_pred_train)),
        "test_accuracy": float(accuracy_test),
    }


def getClassificationReport():
    return classification_report(
        y_test,
        y_pred,
        target_names=["No óptimo", "Óptimo"],
        output_dict=True,
        zero_division=0,
    )


def generateConfusionMatrixPlot():
    cm = confusion_matrix(y_test, y_pred)

    fig, ax = plt.subplots(figsize=(6, 5))

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["No óptimo", "Óptimo"],
    )

    disp.plot(
        ax=ax,
        cmap="Greens",
        colorbar=False,
        values_format="d",
    )

    ax.set_title(
        "Matriz de Confusión – Random Forest",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlabel("Predicción")
    ax.set_ylabel("Valor real")

    return fig_to_base64(fig, plt)


def generateROCPlot():
    y_prob_test = model.predict_proba(X_test)[:, 1]

    try:
        fpr, tpr, _ = roc_curve(y_test, y_prob_test)
        auc = roc_auc_score(y_test, y_prob_test)
    except ValueError:
        fpr = [0, 1]
        tpr = [0, 1]
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

    ax.set_title(
        "Curva ROC – Random Forest",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlabel("Tasa de Falsos Positivos")
    ax.set_ylabel("Tasa de Verdaderos Positivos")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")

    return fig_to_base64(fig, plt)


# Aliases compatibles con services nuevos/antiguos
def get_metrics(data_path=None):
    return getModelMetrics()


def generateGeneralPlot():
    return generatePlot()
