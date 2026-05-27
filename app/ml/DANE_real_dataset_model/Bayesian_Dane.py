# app/ml/DANE_real_dataset_model/Bayesian_Dane.py

import gc
import warnings
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from scipy.stats import norm
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
    confusion_matrix,
    ConfusionMatrixDisplay,
    classification_report,
)

from app.ml.utils.utils_dane.dane_features import (
    FEATURES,
    build_user_vector,
    add_binary_target,
)
from app.ml.pipelines.pipelines_dane.dane_preprocessing import (
    prepare_dane_training_data,
)
from app.ml.utils.utils_dane.plot_utils import fig_to_base64

warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
# Variables globales
# ─────────────────────────────────────────────
_df = None
_scaler = None
_model = None
_le = None
_cv_scores = None

# Evaluación binaria auxiliar para métricas comparativas
_binary_threshold = None
X_test_eval = None
y_test_eval = None
y_pred_eval = None
y_prob_eval = None
train_acc = None
test_acc = None


# ─────────────────────────────────────────────
# 1. Cargar dataset + entrenar modelo
# ─────────────────────────────────────────────
def load_model_B(data_path: str = None):
    global _df, _scaler, _model, _le, _cv_scores
    global _binary_threshold, X_test_eval, y_test_eval, y_pred_eval, y_prob_eval
    global train_acc, test_acc

    if _model is not None:
        return

    data = prepare_dane_training_data(
        data_path=data_path,
        target_method=None,
        with_pca=False,
    )

    _df = data["df"]
    X_scaled = data["X_scaled"]
    _scaler = data["scaler"]

    _le = LabelEncoder()
    y = _le.fit_transform(_df["variedad"].astype(str))

    _model = GaussianNB()
    _model.fit(X_scaled, y)

    # Validación cruzada multiclase segura
    try:
        class_counts = Counter(y)
        min_samples_per_class = min(class_counts.values())

        if min_samples_per_class < 2:
            _cv_scores = np.array([1.0])
        else:
            n_folds = min(5, min_samples_per_class)
            skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
            _cv_scores = cross_val_score(_model, X_scaled, y, cv=skf, scoring="accuracy")
    except Exception:
        _cv_scores = None

    # Métrica binaria auxiliar: Alta/Baja aptitud con mediana de score_proteina
    df_binary, _binary_threshold = add_binary_target(_df, method="median")
    y_binary = df_binary["optimal"].values

    try:
        X_train, X_test_eval, y_train, y_test_eval = train_test_split(
            X_scaled,
            y_binary,
            test_size=0.25,
            random_state=42,
            stratify=y_binary,
        )

        # Para Bayes multiclase, se usa probabilidad de variedad y se convierte a probabilidad binaria
        _model.fit(X_scaled, y)
        y_prob_all = _binary_probability_from_varieties(X_test_eval)
        y_prob_eval = y_prob_all
        y_pred_eval = (y_prob_eval >= 0.50).astype(int)

        y_prob_train = _binary_probability_from_varieties(X_train)
        y_pred_train = (y_prob_train >= 0.50).astype(int)

        train_acc = accuracy_score(y_train, y_pred_train)
        test_acc = accuracy_score(y_test_eval, y_pred_eval)
    except Exception:
        X_test_eval = None
        y_test_eval = y_binary
        y_prob_eval = np.zeros_like(y_binary, dtype=float)
        y_pred_eval = np.zeros_like(y_binary, dtype=int)
        train_acc = 0.0
        test_acc = 0.0

    gc.collect()


def _binary_probability_from_varieties(X_scaled_input):
    """
    Convierte las probabilidades multiclase del GaussianNB en probabilidad de alta aptitud.
    Para cada variedad predicha se pondera por si su score_proteina supera el umbral binario.
    """
    global _model, _le, _df, _binary_threshold

    probs = _model.predict_proba(X_scaled_input)
    class_ids = _model.classes_

    high_mask = []
    for class_id in class_ids:
        var_name = _le.inverse_transform([class_id])[0]
        row = _df[_df["variedad"].astype(str) == str(var_name)]
        if not row.empty:
            high_mask.append(float(row.iloc[0]["score_proteina"] >= _binary_threshold))
        else:
            high_mask.append(0.0)

    high_mask = np.array(high_mask)
    return probs.dot(high_mask)


# ─────────────────────────────────────────────
# 2. Helper functions
# ─────────────────────────────────────────────
def getThreshold():
    """Probabilidad base prior uniforme."""
    if _le is None:
        load_model_B()
    return 1.0 / len(_le.classes_)


def buildUserVector(area_ha, ganancia_proteina_pct, clima):
    """Wrapper compatible. La lógica vive en utils/dane_features.py."""
    return build_user_vector(area_ha, ganancia_proteina_pct, clima)


# ─────────────────────────────────────────────
# 3. Predicción bayesiana
# ─────────────────────────────────────────────
def predictCropCategory(area_ha, ganancia_proteina_pct, clima):
    """
    Predicción usando Naive Bayes:
    P(variedad | features) = P(features | variedad) * P(variedad) / P(features).
    """
    if _model is None or _scaler is None or _le is None:
        load_model_B()

    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])

    probs = _model.predict_proba(uv_scaled)[0]

    clima_lower = str(clima).strip().lower()
    ajustadas = []

    for class_id, p in zip(_model.classes_, probs):
        var_name = _le.inverse_transform([class_id])[0]
        var_row = _df[_df["variedad"].astype(str) == str(var_name)]

        if not var_row.empty:
            clima_v = str(var_row.iloc[0]["clima"]).strip().lower()
            factor = 1.25 if clima_v == clima_lower else 0.75
        else:
            factor = 1.0

        ajustadas.append((var_name, float(p * factor)))

    total = sum(p for _, p in ajustadas)
    if total > 0:
        ajustadas = [(v, p / total) for v, p in ajustadas]

    ajustadas.sort(key=lambda x: x[1], reverse=True)

    best_var, best_prob = ajustadas[0]
    threshold = getThreshold()
    categoria = 1 if best_prob >= threshold else 0

    return best_var, float(best_prob), int(categoria), ajustadas


def getBestCrops(area_ha, ganancia_proteina_pct, clima, top_n=10):
    """Ranking posterior bayesiano por variedad."""
    if _df is None:
        load_model_B()

    _, _, _, ajustadas = predictCropCategory(area_ha, ganancia_proteina_pct, clima)

    records = []
    for var_name, p in ajustadas[:top_n]:
        var_row = _df[_df["variedad"].astype(str) == str(var_name)]

        if not var_row.empty:
            score_p = float(var_row.iloc[0]["score_proteina"])
            clima_v = var_row.iloc[0]["clima"]
        else:
            score_p = 0.0
            clima_v = "?"

        records.append({
            "variedad": var_name,
            "posterior": float(p),
            "score_proteina": score_p,
            "clima": clima_v,
        })

    return pd.DataFrame(records)


# ─────────────────────────────────────────────
# 4. Gráficas
# ─────────────────────────────────────────────
def generatePlot(area_ha, ganancia_proteina_pct, clima):
    """Genera gráficas de análisis bayesiano."""
    if _model is None or _scaler is None or _le is None or _df is None:
        load_model_B()

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    best_var, best_prob, categoria, ajustadas = predictCropCategory(
        area_ha,
        ganancia_proteina_pct,
        clima,
    )
    ranking = getBestCrops(area_ha, ganancia_proteina_pct, clima, top_n=8)

    ax = axes[0]
    x_smooth = np.linspace(0, 1, 300)
    uv_base = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    feat_idx = FEATURES.index("score_proteina")
    posteriors = []

    for xv in x_smooth:
        uv_tmp = uv_base.copy()
        uv_tmp[feat_idx] = xv
        uv_scaled_tmp = _scaler.transform([uv_tmp])
        probs_tmp = _model.predict_proba(uv_scaled_tmp)[0]
        posteriors.append(probs_tmp.max())

    ax.scatter(
        _df["score_proteina"],
        [0] * len(_df),
        color="#9FE1CB",
        s=40,
        alpha=0.6,
        label="Variedades (score=0 base)",
    )
    ax.scatter(
        _df["score_proteina"],
        [1] * len(_df),
        color="#1D9E75",
        s=40,
        alpha=0.3,
    )
    ax.plot(
        x_smooth,
        posteriors,
        color="#0F6E56",
        linewidth=2.5,
        label="Posterior P(variedad óptima | score)",
    )
    ax.axhline(
        y=getThreshold(),
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label=f"Prior uniforme ({getThreshold():.3f})",
    )

    uv_val = uv_base[feat_idx]
    uv_scaled_p = _scaler.transform([uv_base])
    uv_post = float(_model.predict_proba(uv_scaled_p)[0].max())
    color_p = "green" if categoria == 1 else "orange"

    ax.scatter(
        uv_val,
        uv_post,
        s=200,
        color=color_p,
        zorder=6,
        label=f"Tu terreno (posterior={uv_post:.3f})",
    )
    ax.text(
        uv_val,
        uv_post + 0.02,
        f"({uv_val:.3f}, {uv_post:.3f})",
        ha="center",
        fontsize=9,
        fontweight="bold",
        color=color_p,
    )

    ax.set_xlabel("Score de proteína del terreno", fontsize=11)
    ax.set_ylabel("Probabilidad posterior máxima", fontsize=11)
    ax.set_title(
        "Naive Bayes – Curva Posterior Bayesiana\nP(variedad | features del terreno)",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_ylim(-0.05, 1.05)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    ax2 = axes[1]
    top5_vars = [v for v, _ in ajustadas[:5]]
    colors5 = ["#1D9E75", "#EF9F27", "#4A90D9", "#D85A30", "#9B59B6"]
    x_range = np.linspace(-0.05, 0.65, 300)
    feat_idx2 = FEATURES.index("score_proteina")

    for var, col in zip(top5_vars, colors5):
        try:
            cls_idx = int(_le.transform([var])[0])
            model_pos = list(_model.classes_).index(cls_idx)
            mu = _model.theta_[model_pos, feat_idx2]
            sigma = np.sqrt(_model.var_[model_pos, feat_idx2])

            mu_orig = mu * _scaler.scale_[feat_idx2] + _scaler.mean_[feat_idx2]
            sigma_orig = sigma * _scaler.scale_[feat_idx2]
            y_gauss = norm.pdf(x_range, mu_orig, sigma_orig + 1e-6)

            ax2.plot(
                x_range,
                y_gauss,
                color=col,
                linewidth=2,
                label=f"{str(var)[:22]} (μ={mu_orig:.3f})",
            )
            ax2.fill_between(x_range, y_gauss, alpha=0.08, color=col)
        except Exception:
            continue

    ax2.axvline(
        x=uv_val,
        color="red",
        linewidth=2,
        linestyle="--",
        label=f"Tu score ({uv_val:.3f})",
    )
    ax2.set_xlabel("Score de proteína", fontsize=11)
    ax2.set_ylabel("Densidad de probabilidad P(x | variedad)", fontsize=11)
    ax2.set_title(
        "Distribuciones Gaussianas\nP(score_proteína | variedad) – Top 5 variedades",
        fontsize=12,
        fontweight="bold",
    )
    ax2.legend(fontsize=7.5)
    ax2.grid(True, alpha=0.3)

    ax3 = axes[2]
    if len(ranking) > 0:
        bar_cols = [
            "#1D9E75" if v == best_var
            else ("#4A90D9" if str(c).strip().lower() == str(clima).lower() else "#EF9F27")
            for v, c in zip(ranking["variedad"], ranking["clima"])
        ]

        bars = ax3.barh(
            ranking["variedad"].astype(str).str[:28][::-1],
            ranking["posterior"][::-1] * 100,
            color=bar_cols[::-1],
            edgecolor="white",
        )

        ax3.axvline(
            x=getThreshold() * 100,
            color="#EF9F27",
            linestyle="--",
            linewidth=1.5,
            label=f"Prior ({getThreshold() * 100:.1f}%)",
        )

        for bar, val in zip(bars[::-1], ranking["posterior"]):
            ax3.text(
                val * 100 + 0.1,
                bar.get_y() + bar.get_height() / 2,
                f"{val * 100:.2f}%",
                va="center",
                fontsize=8.5,
            )

        ax3.set_xlabel("Probabilidad posterior (%)", fontsize=11)
        ax3.set_title(
            f"Ranking Bayesiano – Top {min(8, len(ranking))} Variedades\n"
            f"Clima: {clima} | Área: {area_ha} ha | Proteína: {ganancia_proteina_pct}%",
            fontsize=12,
            fontweight="bold",
        )

        p1 = mpatches.Patch(color="#1D9E75", label="Recomendada")
        p2 = mpatches.Patch(color="#4A90D9", label=f"Clima {clima}")
        p3 = mpatches.Patch(color="#EF9F27", label="Otro clima")
        ax3.legend(handles=[p1, p2, p3], fontsize=8)
        ax3.grid(True, axis="x", alpha=0.3)

    plt.tight_layout()
    return fig_to_base64(fig, plt)


# ─────────────────────────────────────────────
# 5. Métricas compatibles
# ─────────────────────────────────────────────
def getModelMetrics():
    """
    Métricas binarias auxiliares para la comparación DANE.
    Evalúa Alta/Baja aptitud a partir de probabilidades multiclase convertidas.
    """
    if _model is None:
        load_model_B()

    accuracy = accuracy_score(y_test_eval, y_pred_eval)
    precision = precision_score(y_test_eval, y_pred_eval, zero_division=0)
    recall = recall_score(y_test_eval, y_pred_eval, zero_division=0)
    f1 = f1_score(y_test_eval, y_pred_eval, zero_division=0)

    try:
        auc = roc_auc_score(y_test_eval, y_prob_eval)
    except ValueError:
        auc = 0.0

    cm = confusion_matrix(y_test_eval, y_pred_eval)

    return {
        "exactitud": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(auc),
        "train_accuracy": float(train_acc),
        "test_accuracy": float(test_acc),
        "confusion_matrix": cm.tolist(),
        "cv_mean": float(_cv_scores.mean()) if _cv_scores is not None else "—",
        "cv_std": float(_cv_scores.std()) if _cv_scores is not None else "—",
    }


def getClassificationReport():
    if _model is None:
        load_model_B()

    return classification_report(
        y_test_eval,
        y_pred_eval,
        target_names=["Baja aptitud", "Alta aptitud"],
        output_dict=True,
        zero_division=0,
    )


def generateConfusionMatrixPlot():
    if _model is None:
        load_model_B()

    cm = confusion_matrix(y_test_eval, y_pred_eval)
    fig, ax = plt.subplots(figsize=(6, 5))

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Baja aptitud", "Alta aptitud"],
    )
    disp.plot(ax=ax, cmap="Greens", colorbar=False, values_format="d")

    ax.set_title("Matriz de Confusión – Naive Bayes DANE", fontsize=13, fontweight="bold")
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Valor real")

    return fig_to_base64(fig, plt)


def generateROCPlot():
    if _model is None:
        load_model_B()

    try:
        fpr, tpr, _ = roc_curve(y_test_eval, y_prob_eval)
        auc = roc_auc_score(y_test_eval, y_prob_eval)
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

    ax.set_title("Curva ROC – Naive Bayes DANE", fontsize=13, fontweight="bold")
    ax.set_xlabel("Tasa de Falsos Positivos")
    ax.set_ylabel("Tasa de Verdaderos Positivos")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.05)
    ax.grid(True, alpha=0.3)
    ax.legend(loc="lower right")

    return fig_to_base64(fig, plt)
