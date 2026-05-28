
import gc

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from sklearn.linear_model import LogisticRegression
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

from app.ml.pipelines.pipelines_forraje.forraje_preprocessing import (
    prepare_forraje_training_data,
)

from app.ml.utils.utils_forraje.forraje_features import (
    user_composite,
    build_user_composite_vector,
    get_best_crops,
)

from app.ml.utils.utils_forraje.plot_utils import fig_to_base64


# ─────────────────────────────────────────────
# 1. Cargar dataset + preparar datos
# ─────────────────────────────────────────────
_data = prepare_forraje_training_data(
    feature_mode="composite",
    target_method="mean",
    test_size=0.25,
    random_state=42,
    stratify=True,
)

df = _data["df"]
_threshold = _data["threshold"]
_scaler = _data["scaler"]

_X_train = _data["X_train"]
_X_test = _data["X_test"]
_y_train = _data["y_train"]
_y_test = _data["y_test"]

# ─────────────────────────────────────────────
# 2. Entrenar modelo
# ─────────────────────────────────────────────
_model = LogisticRegression(max_iter=1000)
_model.fit(_X_train, _y_train)

_y_pred = _model.predict(_X_test)
_y_prob = _model.predict_proba(_X_test)[:, 1]

_train_acc = accuracy_score(_y_train, _model.predict(_X_train))
_test_acc = accuracy_score(_y_test, _y_pred)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _user_composite(ph, hum, alt, temp):
    return user_composite(ph, hum, alt, temp)


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────
def getThreshold():
    return _threshold


def predictCropCategory(ph, hum, alt, temp):
    comp_vector = build_user_composite_vector(ph, hum, alt, temp)
    cs = _scaler.transform(comp_vector)

    prob = _model.predict_proba(cs)[0][1]
    cat = _model.predict(cs)[0]

    return int(cat), float(prob)


def getBestCrop(ph, hum, alt, temp, top_n=10):
    return get_best_crops(
        df=df,
        ph=ph,
        hum=hum,
        alt=alt,
        temp=temp,
        top_n=top_n,
    )


def generatePlot(ph=None, hum=None, alt=None, temp=None):
    fig, ax = plt.subplots(figsize=(10, 6))

    ds = df.sort_values("composite")

    ax.scatter(
        ds["composite"],
        ds["optimal"],
        alpha=0.4,
        s=20,
        color="#1D9E75",
        label="Datos reales (0=No óptimo, 1=Óptimo)",
    )

    x_min = df["composite"].min() - 0.02
    x_max = df["composite"].max() + 0.02

    Xs = np.linspace(x_min, x_max, 500).reshape(-1, 1)
    Xss = _scaler.transform(Xs)

    ax.plot(
        Xs,
        _model.predict_proba(Xss)[:, 1],
        color="#0F6E56",
        linewidth=2.5,
        label="Curva Regresión Logística",
    )

    ax.axhline(
        0.5,
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label="Umbral (0.5)",
    )

    if all(v is not None for v in [ph, hum, alt, temp]):
        cat, prob = predictCropCategory(ph, hum, alt, temp)
        comp_val = _user_composite(ph, hum, alt, temp)
        pc = "green" if cat == 1 else "orange"

        ax.scatter(
            comp_val,
            prob,
            s=180,
            color=pc,
            zorder=5,
            label=f"Predicción ({cat})",
        )

        ax.text(
            comp_val,
            prob + 0.05,
            f"({comp_val:.3f}, {prob:.3f})",
            ha="center",
            fontsize=9,
            fontweight="bold",
            color=pc,
        )

        ranked = getBestCrop(ph, hum, alt, temp, top_n=1)

        if not ranked.empty:
            ax.annotate(
                f"Mejor: {ranked.iloc[0]['nombre']}\n"
                f"Afinidad: {ranked.iloc[0]['affinity']:.0%}",
                xy=(comp_val, prob),
                xytext=(comp_val + 0.015, prob - 0.15),
                fontsize=9,
                arrowprops=dict(arrowstyle="->", color="gray"),
                bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="gray"),
            )

    ax.set_xlabel("Puntaje Compuesto (pH · Humedad · Altitud · Temp)", fontsize=12)
    ax.set_ylabel("Probabilidad de Condiciones Óptimas", fontsize=12)
    ax.set_title(
        "Regresión Logística – Aptitud de Cultivos Forrajeros",
        fontsize=14,
        fontweight="bold",
    )

    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(x_min, x_max)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    return fig_to_base64(fig, plt)


def generateRankingPlot(ph, hum, alt, temp, top_n=10):
    ranked = getBestCrop(ph, hum, alt, temp, top_n)

    fig, ax = plt.subplots(figsize=(10, 5))

    colors = ["#1D9E75" if a >= 0.5 else "#EF9F27" for a in ranked["affinity"]]

    bars = ax.barh(
        ranked["nombre"][::-1],
        ranked["affinity"][::-1] * 100,
        color=colors[::-1],
        edgecolor="white",
        linewidth=0.5,
    )

    ax.axvline(
        50,
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label="Umbral 50%",
    )

    ax.set_xlabel("Afinidad (%)", fontsize=12)

    ax.set_title(
        f"Top {top_n} Cultivos – Afinidad con el Terreno\n"
        f"pH={ph} | Hum={hum}% | Alt={alt}m | Temp={temp}°C",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlim(0, 105)
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

    ax.legend(
        handles=[
            mpatches.Patch(color="#1D9E75", label="Óptimo (≥50%)"),
            mpatches.Patch(color="#EF9F27", label="Subóptimo (<50%)"),
        ],
        loc="lower right",
    )

    return fig_to_base64(fig, plt)


def getModelMetrics():
    accuracy = accuracy_score(_y_test, _y_pred)
    precision = precision_score(_y_test, _y_pred, zero_division=0)
    recall = recall_score(_y_test, _y_pred, zero_division=0)
    f1 = f1_score(_y_test, _y_pred, zero_division=0)
    auc = roc_auc_score(_y_test, _y_prob)

    return {
        "exactitud": float(accuracy),
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "f1": float(f1),
        "roc_auc": float(auc),
        "train_accuracy": float(_train_acc),
        "test_accuracy": float(_test_acc),
    }


def getClassificationReport():
    return classification_report(
        _y_test,
        _y_pred,
        target_names=["No óptimo", "Óptimo"],
        output_dict=True,
        zero_division=0,
    )


def generateConfusionMatrixPlot():
    cm = confusion_matrix(_y_test, _y_pred)

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
        "Matriz de Confusión – Regresión Logística",
        fontsize=13,
        fontweight="bold",
    )

    ax.set_xlabel("Predicción")
    ax.set_ylabel("Valor real")

    return fig_to_base64(fig, plt)


def generateROCPlot():
    fpr, tpr, _ = roc_curve(_y_test, _y_prob)
    auc = roc_auc_score(_y_test, _y_prob)

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
        "Curva ROC – Regresión Logística",
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
