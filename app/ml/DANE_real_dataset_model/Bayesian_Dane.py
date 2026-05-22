import io, base64, os, gc
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')  # Ignorar warnings de validación cruzada

# ─────────────────────────────────────────────
# Global variables, initialized as None
# ─────────────────────────────────────────────
_df = None
_scaler = None
_model = None
_le = None
_cv_scores = None

# Settings
FEATURES = [
    "log_area", "score_proteina", "clima_num",
    "prop_pastoreo_continuo", "prop_pastoreo_rotacional",
    "prop_corte", "prop_banco_proteina"
]

# ─────────────────────────────────────────────
# 1. Load dataset + train model
# ─────────────────────────────────────────────
def load_model_B(data_path: str = None):
    global _df, _scaler, _model, _le, _cv_scores
    
    # If model already trained
    if _model is not None:
        return
    
    # Default path
    if data_path is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
        data_path = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")
    
    # Validate file
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No se encontró el archivo: {data_path}")
    
    # Load dataset
    _df = pd.read_csv(data_path)
    
    # Feature engineering
    _df["score_proteina"] = (
        0.50 * _df["prop_banco_proteina"] +
        0.30 * _df["prop_corte"] +
        0.10 * _df["prop_pastoreo_rotacional"] +
        0.10 * _df["prop_pastoreo_continuo"]
    )
    
    _df["log_area"] = np.log1p(_df["area_sembrada_ha"])
    
    # Create feature matrix
    X = _df[FEATURES].values
    
    # Scale features
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)
    
    # Encode labels
    _le = LabelEncoder()
    y = _le.fit_transform(_df["variedad"])
    
    # Train Naive Bayes model
    _model = GaussianNB()
    _model.fit(X_scaled, y)
    
    # Validación cruzada con manejo de clases pequeñas
    try:
        # Verificar el mínimo de muestras por clase
        from collections import Counter
        class_counts = Counter(y)
        min_samples_per_class = min(class_counts.values())
        
        # Ajustar número de folds según el mínimo de muestras
        if min_samples_per_class < 3:
            print(f"Advertencia: Clase con solo {min_samples_per_class} muestra(s). Usando cv=2")
            n_folds = 2
        elif min_samples_per_class < 5:
            print(f"Advertencia: Clase con solo {min_samples_per_class} muestras. Usando cv=3")
            n_folds = 3
        else:
            n_folds = 5
        
        # Usar StratifiedKFold para mantener distribución de clases
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=42)
        _cv_scores = cross_val_score(_model, X_scaled, y, cv=skf, scoring="accuracy")
        
    except Exception as e:
        print(f"No se pudo realizar validación cruzada: {e}")
        _cv_scores = None

# ─────────────────────────────────────────────
# 2. Helper Functions
# ─────────────────────────────────────────────

def getThreshold():
    """Probabilidad base prior uniforme"""
    if _le is None:
        raise ValueError("Modelo no cargado. Llame a load_model_B() primero.")
    return 1.0 / len(_le.classes_)

def buildUserVector(area_ha, ganancia_proteina_pct, clima):
    """Construye vector de features del usuario"""
    gp = ganancia_proteina_pct / 100.0
    prop_banco = min(gp * 0.60, 0.60)
    prop_corte = min(gp * 0.40, 0.40)
    prop_rot = max(1.0 - prop_banco - prop_corte - 0.05, 0.0)
    prop_cont = max(0.05, 1.0 - prop_banco - prop_corte - prop_rot)
    clima_num = 1 if clima.strip().lower() == "frio" else 0
    log_area = np.log1p(area_ha)
    score_p = 0.50*prop_banco + 0.30*prop_corte + 0.10*prop_rot + 0.10*prop_cont
    return np.array([log_area, score_p, clima_num,
                     prop_cont, prop_rot, prop_corte, prop_banco])

# ─────────────────────────────────────────────
# 3. Bayesian Prediction Functions
# ─────────────────────────────────────────────

def predictCropCategory(area_ha, ganancia_proteina_pct, clima):
    """
    Predicción usando Naive Bayes con teorema de Bayes:
    P(variedad | features) = P(features | variedad) * P(variedad) / P(features)
    
    Donde:
    - P(variedad) es el prior uniforme (1/n_variedades)
    - P(features | variedad) es la probabilidad calculada por GaussianNB
    """
    if _model is None or _scaler is None or _le is None:
        raise ValueError("Modelo no cargado. Llame a load_model_B() primero.")
    
    # Construir vector del usuario y escalarlo
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    
    # Calcular probabilidades posteriores P(variedad | features)
    # GaussianNB aplica el teorema de Bayes automáticamente
    probs = _model.predict_proba(uv_scaled)[0]
    
    # Obtener la variedad con mayor probabilidad
    pred_idx = np.argmax(probs)
    variedad = _le.inverse_transform([pred_idx])[0]
    prob = float(probs[pred_idx])
    
    # Ajuste adicional por clima (factor de likelihood)
    clima_lower = clima.strip().lower()
    ajustadas = []
    for i, p in enumerate(probs):
        var_name = _le.inverse_transform([i])[0]
        var_row = _df[_df["variedad"] == var_name]
        if not var_row.empty:
            clima_v = var_row.iloc[0]["clima"]
            # Factor de ajuste: 1.25 si el clima coincide, 0.75 si no
            factor = 1.25 if str(clima_v).strip().lower() == clima_lower else 0.75
        else:
            factor = 1.0
        ajustadas.append((var_name, p * factor))
    
    # Re-normalizar probabilidades (actualización bayesiana)
    total = sum(p for _, p in ajustadas)
    if total > 0:
        ajustadas = [(v, p/total) for v, p in ajustadas]
    ajustadas.sort(key=lambda x: x[1], reverse=True)
    
    # Determinar categoría basada en umbral
    best_var, best_prob = ajustadas[0]
    threshold = getThreshold()
    categoria = 1 if best_prob >= threshold else 0
    
    return best_var, float(best_prob), int(categoria), ajustadas

def getBestCrops(area_ha, ganancia_proteina_pct, clima, top_n=10):
    """Ranking posterior bayesiano por variedad"""
    if _df is None:
        raise ValueError("Datos no cargados. Llame a load_model_B() primero.")
    
    _, _, _, ajustadas = predictCropCategory(area_ha, ganancia_proteina_pct, clima)
    records = []
    for var_name, p in ajustadas[:top_n]:
        var_row = _df[_df["variedad"] == var_name]
        if not var_row.empty:
            score_p = var_row.iloc[0]["score_proteina"]
            clima_v = var_row.iloc[0]["clima"]
        else:
            score_p = 0
            clima_v = "?"
        records.append({
            "variedad": var_name, 
            "posterior": p,
            "score_proteina": score_p, 
            "clima": clima_v
        })
    return pd.DataFrame(records)

# ─────────────────────────────────────────────
# 4. Plot Generation Functions
# ─────────────────────────────────────────────

def generatePlot(area_ha, ganancia_proteina_pct, clima):
    """Genera gráficas de análisis bayesiano"""
    if _model is None or _scaler is None or _le is None or _df is None:
        raise ValueError("Modelo no cargado. Llame a load_model_B() primero.")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    best_var, best_prob, categoria, ajustadas = predictCropCategory(
        area_ha, ganancia_proteina_pct, clima)
    ranking = getBestCrops(area_ha, ganancia_proteina_pct, clima, top_n=8)
    
    # Gráfica 1: Posterior bayesiana vs score_proteína
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
    
    ax.scatter(_df["score_proteina"], [0]*len(_df), color="#9FE1CB",
               s=40, alpha=0.6, label="Variedades (score=0 base)")
    ax.scatter(_df["score_proteina"], [1]*len(_df), color="#1D9E75",
               s=40, alpha=0.3)
    ax.plot(x_smooth, posteriors, color="#0F6E56", linewidth=2.5,
            label="Posterior P(variedad óptima | score)")
    ax.axhline(y=getThreshold(), color="#EF9F27", linestyle="--",
               linewidth=1.5, label=f"Prior uniforme ({getThreshold():.3f})")
    
    uv_val = buildUserVector(area_ha, ganancia_proteina_pct, clima)[feat_idx]
    uv_scaled_p = _scaler.transform([buildUserVector(area_ha, ganancia_proteina_pct, clima)])
    uv_post = float(_model.predict_proba(uv_scaled_p)[0].max())
    color_p = "green" if categoria == 1 else "orange"
    ax.scatter(uv_val, uv_post, s=200, color=color_p, zorder=6,
               label=f"Tu terreno (posterior={uv_post:.3f})")
    ax.text(uv_val, uv_post + 0.02,
            f"({uv_val:.3f}, {uv_post:.3f})",
            ha="center", fontsize=9, fontweight="bold", color=color_p)
    
    ax.set_xlabel("Score de proteína del terreno", fontsize=11)
    ax.set_ylabel("Probabilidad posterior máxima", fontsize=11)
    ax.set_title("Naive Bayes – Curva Posterior Bayesiana\n"
                 "P(variedad | features del terreno)",
                 fontsize=12, fontweight="bold")
    ax.set_ylim(-0.05, 1.05)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    
    # Gráfica 2: Distribuciones gaussianas P(x | variedad)
    ax2 = axes[1]
    top5_vars = [v for v, _ in ajustadas[:5]]
    colors5 = ["#1D9E75","#EF9F27","#4A90D9","#D85A30","#9B59B6"]
    x_range = np.linspace(-0.05, 0.65, 300)
    feat_idx2 = FEATURES.index("score_proteina")
    
    for ci, (var, col) in enumerate(zip(top5_vars, colors5)):
        try:
            cls_idx = int(_le.transform([var])[0])
            mu = _model.theta_[cls_idx, feat_idx2]
            sigma = np.sqrt(_model.var_[cls_idx, feat_idx2])
            # Desnormalizar para graficar en escala original
            mu_orig = mu * _scaler.scale_[feat_idx2] + _scaler.mean_[feat_idx2]
            sigma_orig = sigma * _scaler.scale_[feat_idx2]
            y_gauss = norm.pdf(x_range, mu_orig, sigma_orig + 1e-6)
            ax2.plot(x_range, y_gauss, color=col, linewidth=2,
                     label=f"{var[:22]} (μ={mu_orig:.3f})")
            ax2.fill_between(x_range, y_gauss, alpha=0.08, color=col)
        except:
            continue
    
    ax2.axvline(x=uv_val, color="red", linewidth=2, linestyle="--",
                label=f"Tu score ({uv_val:.3f})")
    ax2.set_xlabel("Score de proteína", fontsize=11)
    ax2.set_ylabel("Densidad de probabilidad P(x | variedad)", fontsize=11)
    ax2.set_title("Distribuciones Gaussianas\n"
                  "P(score_proteína | variedad) – Top 5 variedades",
                  fontsize=12, fontweight="bold")
    ax2.legend(fontsize=7.5)
    ax2.grid(True, alpha=0.3)
    
    # Gráfica 3: Ranking posterior
    ax3 = axes[2]
    if len(ranking) > 0:
        bar_cols = ["#1D9E75" if v == best_var else
                    ("#4A90D9" if str(c).strip().lower() == clima.lower() else "#EF9F27")
                    for v, c in zip(ranking["variedad"], ranking["clima"])]
        bars = ax3.barh(ranking["variedad"].str[:28][::-1],
                        ranking["posterior"][::-1] * 100,
                        color=bar_cols[::-1], edgecolor="white")
        ax3.axvline(x=getThreshold()*100, color="#EF9F27", linestyle="--",
                    linewidth=1.5, label=f"Prior ({getThreshold()*100:.1f}%)")
        for bar, val in zip(bars[::-1], ranking["posterior"]):
            ax3.text(val*100 + 0.1, bar.get_y()+bar.get_height()/2,
                     f"{val*100:.2f}%", va="center", fontsize=8.5)
        ax3.set_xlabel("Probabilidad posterior (%)", fontsize=11)
        ax3.set_title(f"Ranking Bayesiano – Top {min(8, len(ranking))} Variedades\n"
                      f"Clima: {clima} | Área: {area_ha} ha | Proteína: {ganancia_proteina_pct}%",
                      fontsize=12, fontweight="bold")
        p1 = mpatches.Patch(color="#1D9E75", label="Recomendada")
        p2 = mpatches.Patch(color="#4A90D9", label=f"Clima {clima}")
        p3 = mpatches.Patch(color="#EF9F27", label="Otro clima")
        ax3.legend(handles=[p1,p2,p3], fontsize=8)
        ax3.grid(True, axis="x", alpha=0.3)
    
    plt.tight_layout()
    
    # Memory optimization
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt.close('all')
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()
    
    return result