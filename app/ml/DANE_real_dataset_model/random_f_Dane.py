import io, base64, os, gc
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.model_selection import cross_val_score, StratifiedKFold, train_test_split
from sklearn.metrics import confusion_matrix,ConfusionMatrixDisplay,accuracy_score,precision_score,recall_score,f1_score,roc_curve,roc_auc_score, classification_report, precision_recall_curve
from sklearn.preprocessing import label_binarize
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report

# ─────────────────────────────────────────────
# Variables globales
# ─────────────────────────────────────────────
_df = None
_scaler = None

# Modelo multiclase: recomienda variedad
_model = None
_label_encoder = None
_feat_importances = None
_cv_scores = None

X_test_eval = None
y_test_eval = None
y_pred_eval = None
y_prob_eval = None
train_acc = None
test_acc = None

# Modelo binario: evalúa aptitud alta/baja
_binary_model = None
X_test_binary_eval = None
y_test_binary_eval = None
y_pred_binary_eval = None
y_prob_binary_eval = None
binary_train_acc = None
binary_test_acc = None
_binary_threshold = 0.5
_threshold_optimal = None


# ─────────────────────────────────────────────
# Configuración
# ─────────────────────────────────────────────
N_ESTIMATORS = 200

FEATURES = [
    "log_area",
    "score_proteina",
    "clima_num",
    "prop_pastoreo_continuo",
    "prop_pastoreo_rotacional",
    "prop_corte",
    "prop_banco_proteina",
]


# ─────────────────────────────────────────────
# 1. Cargar dataset y entrenar modelos
# ─────────────────────────────────────────────
def load_model_RF(data_path: str = None):
    """
    Carga el dataset DANE y entrena dos modelos:

    1. Random Forest multiclase:
       Predice la variedad de forraje recomendada.

    2. Random Forest binario:
       Evalúa si la aptitud proteica es Alta o Baja.
       Este modelo se usa para métricas, matriz de confusión y curva ROC.

    Esta separación evita mezclar un problema multiclase
    con métricas binarias.
    """

    global _df, _scaler
    global _model, _label_encoder, _feat_importances, _cv_scores
    global X_test_eval, y_test_eval, y_pred_eval, y_prob_eval, train_acc, test_acc
    global _binary_model, X_test_binary_eval, y_test_binary_eval
    global y_pred_binary_eval, y_prob_binary_eval
    global binary_train_acc, binary_test_acc, _binary_threshold, _threshold_optimal

    if _model is not None and _binary_model is not None:
        return

    if data_path is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
        data_path = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No se encontró el archivo: {data_path}")

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

    _df["clima_num"] = (
        _df["clima"]
        .astype(str)
        .str.lower()
        .map({"frio": 1, "calido": 0})
        .fillna(0)
        .astype(int)
    )

    # Target binario para aptitud
    # 1 = Alta aptitud proteica
    # 0 = Baja aptitud proteica
    # Se usa la mediana para que el umbral sea más robusto que la media.
    _threshold_optimal = float(_df["score_proteina"].quantile(0.50))

    _df["optimal"] = (
        _df["score_proteina"] >= _threshold_optimal
    ).astype(int)

    X = _df[FEATURES].values

    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)

    # ─────────────────────────────────────────────
    # Modelo 1: Random Forest multiclase para variedad
    # ─────────────────────────────────────────────
    _label_encoder = LabelEncoder()
    y_variedad = _label_encoder.fit_transform(_df["variedad"].astype(str))

    unique_var, counts_var = np.unique(y_variedad, return_counts=True)
    stratify_var = y_variedad if counts_var.min() >= 2 else None

    X_train, X_test_eval, y_train, y_test_eval = train_test_split(
        X_scaled,
        y_variedad,
        test_size=0.25,
        random_state=42,
        stratify=stratify_var,
    )

    _model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
    )

    _model.fit(X_train, y_train)

    y_pred_eval = _model.predict(X_test_eval)
    y_prob_eval = _model.predict_proba(X_test_eval)

    train_acc = accuracy_score(y_train, _model.predict(X_train))
    test_acc = accuracy_score(y_test_eval, y_pred_eval)

    _feat_importances = pd.Series(
        _model.feature_importances_,
        index=FEATURES,
    )

    # Cross-validation multiclase segura
    try:
        min_samples_per_class = counts_var.min()

        if min_samples_per_class >= 3:
            n_splits = min(3, min_samples_per_class)
            skf = StratifiedKFold(
                n_splits=n_splits,
                shuffle=True,
                random_state=42,
            )
            _cv_scores = cross_val_score(
                _model,
                X_scaled,
                y_variedad,
                cv=skf,
                scoring="accuracy",
            )
        else:
            _cv_scores = np.array([test_acc])
    except Exception:
        _cv_scores = np.array([test_acc])

    # ─────────────────────────────────────────────
    # Modelo 2: Random Forest binario para aptitud
    # ─────────────────────────────────────────────
    y_binary = _df["optimal"].values

    X_train_b, X_test_binary_eval, y_train_b, y_test_binary_eval = train_test_split(
        X_scaled,
        y_binary,
        test_size=0.25,
        random_state=42,
        stratify=y_binary,
    )

    _binary_model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=4,
        min_samples_split=2,
        min_samples_leaf=1,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    _binary_model.fit(X_train_b, y_train_b)

    y_prob_train_b = _binary_model.predict_proba(X_train_b)[:, 1]

    # Umbral corregido:
    # En vez de usar siempre 0.5, se busca el umbral que mejora el F1
    # en entrenamiento. Esto ayuda cuando el modelo tiende a predecir todo 0.
    _binary_threshold = _find_best_threshold(y_train_b, y_prob_train_b)

    y_prob_binary_eval = _binary_model.predict_proba(X_test_binary_eval)[:, 1]
    y_pred_binary_eval = (y_prob_binary_eval >= _binary_threshold).astype(int)

    binary_train_acc = accuracy_score(
        y_train_b,
        (y_prob_train_b >= _binary_threshold).astype(int),
    )
    binary_test_acc = accuracy_score(
        y_test_binary_eval,
        y_pred_binary_eval,
    )

    gc.collect()


def _find_best_threshold(y_true, y_prob):
    """
    Calcula un umbral óptimo usando F1 en el conjunto de entrenamiento.
    Si no hay suficientes clases, retorna 0.5.
    """

    if len(np.unique(y_true)) < 2:
        return 0.5

    precision, recall, thresholds = precision_recall_curve(y_true, y_prob)

    if len(thresholds) == 0:
        return 0.5

    f1_values = (2 * precision[:-1] * recall[:-1]) / (
        precision[:-1] + recall[:-1] + 1e-12
    )

    best_idx = int(np.nanargmax(f1_values))
    best_threshold = float(thresholds[best_idx])

    # Evita umbrales extremos que puedan generar todo 0 o todo 1
    return float(np.clip(best_threshold, 0.20, 0.80))


# ─────────────────────────────────────────────
# 2. Funciones auxiliares
# ─────────────────────────────────────────────
def getThreshold():
    """
    Retorna el umbral binario de alta aptitud usado por el modelo.
    """

    if _binary_model is None:
        load_model_RF()

    return float(_binary_threshold)


def buildUserVector(area_ha, ganancia_proteina_pct, clima):
    """
    Construye el vector de entrada del usuario con las mismas variables
    usadas durante el entrenamiento.
    """

    gp = ganancia_proteina_pct / 100.0

    prop_banco = min(gp * 0.60, 0.60)
    prop_corte = min(gp * 0.40, 0.40)
    prop_rot = max(1.0 - prop_banco - prop_corte - 0.05, 0.0)
    prop_cont = max(0.05, 1.0 - prop_banco - prop_corte - prop_rot)

    clima_lower = clima.strip().lower()
    clima_num = 1 if clima_lower == "frio" else 0

    log_area = np.log1p(area_ha)

    score_p = (
        0.50 * prop_banco +
        0.30 * prop_corte +
        0.10 * prop_rot +
        0.10 * prop_cont
    )

    return np.array([
        log_area,
        score_p,
        clima_num,
        prop_cont,
        prop_rot,
        prop_corte,
        prop_banco,
    ])


# ─────────────────────────────────────────────
# 3. Predicción principal
# ─────────────────────────────────────────────
def predictCropCategory(area_ha, ganancia_proteina_pct, clima):
    """
    Predicción Random Forest corregida:

    - El modelo multiclase recomienda la variedad.
    - El modelo binario decide si la aptitud es alta o baja.
    """

    global _model, _binary_model, _scaler, _label_encoder, _df

    if _model is None or _binary_model is None:
        load_model_RF()

    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])

    probs = _model.predict_proba(uv_scaled)[0]
    clima_lower = clima.strip().lower()

    adjusted = []

    # Importante:
    # _model.classes_ contiene las clases realmente aprendidas por el modelo.
    for class_id, p in zip(_model.classes_, probs):
        var_name = _label_encoder.inverse_transform([class_id])[0]
        var_row = _df[_df["variedad"].astype(str) == str(var_name)]

        if not var_row.empty:
            clima_var = str(var_row.iloc[0]["clima"]).lower()
            factor = 1.30 if clima_var == clima_lower else 0.70
        else:
            factor = 0.70

        adjusted.append((var_name, float(p * factor)))

    adjusted.sort(key=lambda x: x[1], reverse=True)

    best_var, _ = adjusted[0]

    prob_aptitud_alta = float(_binary_model.predict_proba(uv_scaled)[0][1])
    category = int(prob_aptitud_alta >= _binary_threshold)

    return best_var, prob_aptitud_alta, category


def getBestCrops(area_ha, ganancia_proteina_pct, clima, top_n=10):
    """
    Ranking de variedades por probabilidad ajustada por clima.
    """

    global _model, _scaler, _label_encoder, _df

    if _model is None:
        load_model_RF()

    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])

    probs = _model.predict_proba(uv_scaled)[0]
    clima_lower = clima.strip().lower()

    records = []

    for class_id, p in zip(_model.classes_, probs):
        var_name = _label_encoder.inverse_transform([class_id])[0]
        var_row = _df[_df["variedad"].astype(str) == str(var_name)]

        if not var_row.empty:
            clima_var = str(var_row.iloc[0]["clima"]).lower()
            score_p = float(var_row.iloc[0]["score_proteina"])
        else:
            clima_var = "?"
            score_p = 0.0

        factor = 1.30 if clima_var == clima_lower else 0.70

        records.append({
            "variedad": var_name,
            "probabilidad": float(p * factor),
            "score_proteina": score_p,
            "clima": clima_var,
        })

    return (
        pd.DataFrame(records)
        .sort_values("probabilidad", ascending=False)
        .head(top_n)
    )


# ─────────────────────────────────────────────
# 4. Gráficas del modelo
# ─────────────────────────────────────────────
def generatePlot(area_ha, ganancia_proteina_pct, clima):
    """
    Gráfica principal:
    - Votos de árboles.
    - Importancia de variables.
    - Ranking de variedades.
    """

    global _model, _feat_importances, _df, _scaler, _label_encoder

    if _model is None:
        load_model_RF()

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    best_var, best_prob, category = predictCropCategory(
        area_ha,
        ganancia_proteina_pct,
        clima,
    )

    ranking = getBestCrops(
        area_ha,
        ganancia_proteina_pct,
        clima,
        top_n=8,
    )

    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])

    # ─────────────────────────────────────────────
    # Gráfica 1: votos por árbol
    # ─────────────────────────────────────────────
    ax = axes[0]

    tree_votes = np.array([
        tree.predict_proba(uv_scaled)[0]
        for tree in _model.estimators_
    ])

    mean_votes = tree_votes.mean(axis=0)
    top5_pos = np.argsort(mean_votes)[-5:][::-1]
    colors5 = ["#1D9E75", "#EF9F27", "#4A90D9", "#D85A30", "#9B59B6"]

    for pos, col in zip(top5_pos, colors5):
        class_id = _model.classes_[pos]
        var_label = _label_encoder.inverse_transform([class_id])[0][:22]

        ax.plot(
            range(1, len(_model.estimators_) + 1),
            tree_votes[:, pos],
            alpha=0.4,
            linewidth=0.8,
            color=col,
        )

        ax.axhline(
            y=mean_votes[pos],
            linewidth=1.8,
            color=col,
            linestyle="--",
            label=f"{var_label} ({mean_votes[pos]:.3f})",
        )

    ax.set_xlabel("Árbol de decisión", fontsize=11)
    ax.set_ylabel("Probabilidad por árbol", fontsize=11)
    ax.set_title(
        "Random Forest – Votos por árbol\nTop 5 variedades",
        fontsize=12,
        fontweight="bold",
    )
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # ─────────────────────────────────────────────
    # Gráfica 2: importancia de variables
    # ─────────────────────────────────────────────
    ax2 = axes[1]

    fi = _feat_importances.sort_values()
    cols = ["#1D9E75" if v >= fi.mean() else "#9FE1CB" for v in fi]

    bars = ax2.barh(
        fi.index,
        fi.values * 100,
        color=cols,
        edgecolor="white",
    )

    ax2.axvline(
        x=fi.mean() * 100,
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label=f"Media ({fi.mean() * 100:.1f}%)",
    )

    for bar, val in zip(bars, fi.values):
        ax2.text(
            val * 100 + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{val * 100:.1f}%",
            va="center",
            fontsize=9,
        )

    ax2.set_xlabel("Importancia (%)", fontsize=11)
    ax2.set_title(
        "Importancia de variables\nImpureza Gini",
        fontsize=12,
        fontweight="bold",
    )
    ax2.legend()
    ax2.grid(True, axis="x", alpha=0.3)

    # ─────────────────────────────────────────────
    # Gráfica 3: ranking
    # ─────────────────────────────────────────────
    ax3 = axes[2]

    bar_cols = [
        "#1D9E75" if row["variedad"] == best_var
        else ("#4A90D9" if row["clima"] == clima.lower() else "#EF9F27")
        for _, row in ranking.iterrows()
    ]

    bars3 = ax3.barh(
        ranking["variedad"].str[:28][::-1],
        ranking["probabilidad"][::-1] * 100,
        color=bar_cols[::-1],
        edgecolor="white",
    )

    for bar, val in zip(bars3[::-1], ranking["probabilidad"]):
        ax3.text(
            val * 100 + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{val * 100:.1f}%",
            va="center",
            fontsize=8.5,
        )

    ax3.set_xlabel("Probabilidad ajustada (%)", fontsize=11)
    ax3.set_title(
        f"Top 8 variedades recomendadas\n"
        f"Clima: {clima} | Área: {area_ha} ha | Proteína: {ganancia_proteina_pct}%",
        fontsize=12,
        fontweight="bold",
    )
    ax3.grid(True, axis="x", alpha=0.3)

    p1 = mpatches.Patch(color="#1D9E75", label="Recomendada")
    p2 = mpatches.Patch(color="#4A90D9", label=f"Clima {clima}")
    p3 = mpatches.Patch(color="#EF9F27", label="Otro clima")

    ax3.legend(handles=[p1, p2, p3], fontsize=8)

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    plt.close("all")

    buf.seek(0)
    result_base64 = base64.b64encode(buf.getvalue()).decode()
    buf.close()

    gc.collect()

    return result_base64


def generateFeatureImportancePlot():
    """
    Genera una gráfica independiente de importancia de variables.
    """

    global _feat_importances

    if _feat_importances is None:
        load_model_RF()

    fig, ax = plt.subplots(figsize=(10, 6))

    fi = _feat_importances.sort_values()
    cols = ["#1D9E75" if v >= fi.mean() else "#9FE1CB" for v in fi]

    bars = ax.barh(
        fi.index,
        fi.values * 100,
        color=cols,
        edgecolor="white",
    )

    ax.axvline(
        x=fi.mean() * 100,
        color="#EF9F27",
        linestyle="--",
        linewidth=1.5,
        label=f"Media ({fi.mean() * 100:.1f}%)",
    )

    for bar, val in zip(bars, fi.values):
        ax.text(
            val * 100 + 0.3,
            bar.get_y() + bar.get_height() / 2,
            f"{val * 100:.1f}%",
            va="center",
            fontsize=9,
        )

    ax.set_xlabel("Importancia (%)", fontsize=12)
    ax.set_ylabel("Variables", fontsize=12)
    ax.set_title(
        "Random Forest - Importancia de variables\nImpureza Gini",
        fontsize=13,
        fontweight="bold",
    )
    ax.legend()
    ax.grid(True, axis="x", alpha=0.3)

    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close(fig)
    plt.close("all")

    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()

    gc.collect()

    return result


# ─────────────────────────────────────────────
# 5. Métricas binarias corregidas
# ─────────────────────────────────────────────
def getModelMetrics():
    """
    Retorna métricas binarias reales:
    Baja aptitud vs Alta aptitud.
    """

    if _binary_model is None:
        load_model_RF()

    accuracy = accuracy_score(y_test_binary_eval, y_pred_binary_eval)
    precision = precision_score(
        y_test_binary_eval,
        y_pred_binary_eval,
        zero_division=0,
    )
    recall = recall_score(
        y_test_binary_eval,
        y_pred_binary_eval,
        zero_division=0,
    )
    f1 = f1_score(
        y_test_binary_eval,
        y_pred_binary_eval,
        zero_division=0,
    )

    try:
        auc = roc_auc_score(y_test_binary_eval, y_prob_binary_eval)
    except ValueError:
        auc = 0.0

    cm = confusion_matrix(y_test_binary_eval, y_pred_binary_eval)

    return {
        "exactitud": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "roc_auc": float(auc),
        "train_accuracy": float(binary_train_acc),
        "test_accuracy": float(binary_test_acc),
        "confusion_matrix": cm.tolist(),
        "threshold_optimal": float(_threshold_optimal),
        "classification_threshold": float(_binary_threshold),
        "n_real_bajas": int(np.sum(y_test_binary_eval == 0)),
        "n_real_altas": int(np.sum(y_test_binary_eval == 1)),
        "n_pred_bajas": int(np.sum(y_pred_binary_eval == 0)),
        "n_pred_altas": int(np.sum(y_pred_binary_eval == 1)),
    }


def getClassificationReport():
    """
    Retorna el reporte de clasificación binaria.
    """

    if _binary_model is None:
        load_model_RF()

    return classification_report(
        y_test_binary_eval,
        y_pred_binary_eval,
        target_names=["Baja aptitud", "Alta aptitud"],
        output_dict=True,
        zero_division=0,
    )


def generateConfusionMatrixPlot():
    """
    Genera matriz de confusión binaria.
    """

    if _binary_model is None:
        load_model_RF()

    cm = confusion_matrix(y_test_binary_eval, y_pred_binary_eval)

    fig, ax = plt.subplots(figsize=(6, 5))

    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Baja aptitud", "Alta aptitud"],
    )

    disp.plot(
        ax=ax,
        cmap="Greens",
        colorbar=False,
        values_format="d",
    )

    ax.set_title(
        "Matriz de Confusión – Random Forest Binario",
        fontsize=13,
        fontweight="bold",
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
    Genera curva ROC binaria.
    """

    if _binary_model is None:
        load_model_RF()

    try:
        fpr, tpr, thresholds = roc_curve(
            y_test_binary_eval,
            y_prob_binary_eval,
        )
        auc = roc_auc_score(
            y_test_binary_eval,
            y_prob_binary_eval,
        )
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
        "Curva ROC – Random Forest Binario",
        fontsize=13,
        fontweight="bold",
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
