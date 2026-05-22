import io, base64, os, gc
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report

# ─────────────────────────────────────────────
# Global variables, initialized as None
# ─────────────────────────────────────────────
_df = None
_scaler = None
_model = None
_label_encoder = None
_feat_importances = None
_cv_scores = None

# Settings
FEATURES = [
    "log_area", "score_proteina", "clima_num",
    "prop_pastoreo_continuo", "prop_pastoreo_rotacional",
    "prop_corte", "prop_banco_proteina"
]

# ─────────────────────────────────────────────
# 1. Load dataset with memory optimization
# ─────────────────────────────────────────────
def load_model_RF(data_path: str = None):
    #Loads the dataset and trains the Random Forest model once.
    # Implements memory optimization and path handling.

    global _df, _scaler, _model, _label_encoder, _feat_importances, _cv_scores
    
    # If already trained → exit
    if _model is not None:
        return
    
    # If no path provided, use default
    if data_path is None:
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "..", ".."))
        data_path = os.path.join(ROOT_DIR, "data", "DANE_ena_2019_pastos.csv")
    
    # Check if file exists
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"File not found: {data_path}")
    
    print(f"Loading data from: {data_path}")
    
    # Load data
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
    
    # Prepare data
    X = _df[FEATURES].values
    _scaler = StandardScaler()
    X_scaled = _scaler.fit_transform(X)
    # ─────────────────────────────────────────────
    # Multi-class label: variety 
    # ─────────────────────────────────────────────

    _label_encoder = LabelEncoder()
    y = _label_encoder.fit_transform(_df["variedad"])
    # ─────────────────────────────────────────────
    # Train Random Forest 
    # ─────────────────────────────────────────────
    _model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1
    )
    _model.fit(X_scaled, y)
    
    # Calculate feature importance
    _feat_importances = pd.Series(_model.feature_importances_, index=FEATURES)
    # ─────────────────────────────────────────────
    # Cross-validation with error handling 
    # ─────────────────────────────────────────────
    try:
        # Check minimum samples per class
        unique, counts = np.unique(y, return_counts=True)
        min_samples_per_class = counts.min()
        
        if min_samples_per_class >= 3:
            # Use stratified k-fold with safe number of splits
            n_splits = min(3, min_samples_per_class - 1)
            if n_splits >= 2:
                skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
                _cv_scores = cross_val_score(_model, X_scaled, y, cv=skf, scoring="accuracy")
                print(f"Cross-validation scores: {_cv_scores}")
                print(f"Mean CV accuracy: {_cv_scores.mean():.3f}")
            else:
                _cv_scores = np.array([1.0])
                print("Warning: Not enough samples per class for cross-validation")
        else:
            _cv_scores = np.array([1.0])
            print(f"Warning: Minimum samples per class = {min_samples_per_class}. Skipping cross-validation.")
    except Exception as e:
        print(f"Warning: Cross-validation failed: {e}")
        _cv_scores = np.array([1.0])
    
    # Clean memory
    gc.collect()
# ─────────────────────────────────────────────
# 2. Helper functions
# ─────────────────────────────────────────────
def getThreshold():
    #Returns the minimum probability to consider a variety optimal
    if _label_encoder is None:
        load_model_RF()
    return 1.0 / len(_label_encoder.classes_)


def buildUserVector(area_ha, ganancia_proteina_pct, clima):
    #Builds the user feature vector
    gp = ganancia_proteina_pct / 100.0
    prop_banco = min(gp * 0.60, 0.60)
    prop_corte = min(gp * 0.40, 0.40)
    prop_rot = max(1.0 - prop_banco - prop_corte - 0.05, 0.0)
    prop_cont = max(0.05, 1.0 - prop_banco - prop_corte - prop_rot)
    clima_num = 1 if clima.strip().lower() == "frio" else 0
    log_area = np.log1p(area_ha)
    score_p = 0.50 * prop_banco + 0.30 * prop_corte + 0.10 * prop_rot + 0.10 * prop_cont
    return np.array([log_area, score_p, clima_num,
                     prop_cont, prop_rot, prop_corte, prop_banco])


def predictCropCategory(area_ha, ganancia_proteina_pct, clima):
    #Random Forest prediction: returns recommended_variety, probability, category
    
    global _model, _scaler, _label_encoder, _df
    
    # Ensure model is loaded
    if _model is None:
        load_model_RF()
    
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    probs = _model.predict_proba(uv_scaled)[0]
    
    # Adjust by climate
    clima_lower = clima.strip().lower()
    adjusted = []
    for i, p in enumerate(probs):
        var_name = _label_encoder.inverse_transform([i])[0]
        var_row = _df[_df["variedad"] == var_name]
        if not var_row.empty and var_row.iloc[0]["clima"] == clima_lower:
            adjusted.append((var_name, p * 1.30))
        else:
            adjusted.append((var_name, p * 0.70))
    
    adjusted.sort(key=lambda x: x[1], reverse=True)
    best_var, best_prob = adjusted[0]
    category = 1 if best_prob >= getThreshold() else 0
    return best_var, float(best_prob), int(category)


def getBestCrops(area_ha, ganancia_proteina_pct, clima, top_n=10):
    #Ranking of varieties by adjusted probability
    global _model, _scaler, _label_encoder, _df
    
    # Ensure model is loaded
    if _model is None:
        load_model_RF()
    
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    probs = _model.predict_proba(uv_scaled)[0]
    clima_lower = clima.strip().lower()
    
    records = []
    for i, p in enumerate(probs):
        var_name = _label_encoder.inverse_transform([i])[0]
        var_row = _df[_df["variedad"] == var_name]
        clima_var = var_row.iloc[0]["clima"] if not var_row.empty else "?"
        score_p = var_row.iloc[0]["score_proteina"] if not var_row.empty else 0
        factor = 1.30 if clima_var == clima_lower else 0.70
        records.append({
            "variedad": var_name,
            "probabilidad": p * factor,
            "score_proteina": score_p,
            "clima": clima_var
        })
    
    return pd.DataFrame(records).sort_values("probabilidad", ascending=False).head(top_n)


def generatePlot(area_ha, ganancia_proteina_pct, clima):
    #Main Random Forest plot: tree votes + feature importance + ranking
    # Optimized with memory management

    global _model, _feat_importances, _df, _scaler, _label_encoder
    
    # Ensure model is loaded
    if _model is None:
        load_model_RF()
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    best_var, best_prob, category = predictCropCategory(area_ha, ganancia_proteina_pct, clima)
    ranking = getBestCrops(area_ha, ganancia_proteina_pct, clima, top_n=8)
    # ─────────────────────────────────────────────
    # Plot 1: Tree votes probabilities per tree
    # ─────────────────────────────────────────────
    ax = axes[0]
    uv = buildUserVector(area_ha, ganancia_proteina_pct, clima)
    uv_scaled = _scaler.transform([uv])
    
    # Collect votes tree by tree
    tree_votes = np.array([
        tree.predict_proba(uv_scaled)[0]
        for tree in _model.estimators_
    ])
    
    # Get top 5 classes
    top5_idx = np.argsort(tree_votes.mean(axis=0))[-5:][::-1]
    colors5 = ["#1D9E75", "#EF9F27", "#4A90D9", "#D85A30", "#9B59B6"]
    
    for ci, (cls_idx, col) in enumerate(zip(top5_idx, colors5)):
        var_label = _label_encoder.inverse_transform([cls_idx])[0][:22]
        ax.plot(range(1, len(_model.estimators_) + 1), tree_votes[:, cls_idx],
                alpha=0.4, linewidth=0.8, color=col)
        ax.axhline(y=tree_votes[:, cls_idx].mean(),
                   linewidth=1.8, color=col, linestyle="--",
                   label=f"{var_label} ({tree_votes[:,cls_idx].mean():.3f})")
    
    ax.axhline(y=0.5, color="gray", linestyle=":", linewidth=1.2, label="Threshold 0.5")
    ax.set_xlabel("Decision Tree (1-100)", fontsize=11)
    ax.set_ylabel("Tree Probability", fontsize=11)
    ax.set_title("Random Forest – Tree Votes\n(Top 5 varieties)",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)
    # ─────────────────────────────────────────────
    # Plot 2: Feature importance 
    # ─────────────────────────────────────────────

    ax2 = axes[1]
    fi = _feat_importances.sort_values()
    cols = ["#1D9E75" if v >= fi.mean() else "#9FE1CB" for v in fi]
    bars = ax2.barh(fi.index, fi.values * 100, color=cols, edgecolor="white")
    ax2.axvline(x=fi.mean() * 100, color="#EF9F27", linestyle="--",
                linewidth=1.5, label=f"Mean ({fi.mean()*100:.1f}%)")
    for bar, val in zip(bars, fi.values):
        ax2.text(val*100+0.3, bar.get_y()+bar.get_height()/2,
                 f"{val*100:.1f}%", va="center", fontsize=9)
    ax2.set_xlabel("Importance (%)", fontsize=11)
    ax2.set_title("Feature Importance\n(Gini Impurity)",
                  fontsize=12, fontweight="bold")
    ax2.legend()
    ax2.grid(True, axis="x", alpha=0.3)
    # ─────────────────────────────────────────────
    # Plot 3: Top varieties ranking
    # ─────────────────────────────────────────────

    ax3 = axes[2]
    bar_cols = ["#1D9E75" if v["variedad"] == best_var else
                ("#4A90D9" if v["clima"] == clima.lower() else "#EF9F27")
                for _, v in ranking.iterrows()]
    bars3 = ax3.barh(ranking["variedad"].str[:28][::-1],
                     ranking["probabilidad"][::-1] * 100,
                     color=bar_cols[::-1], edgecolor="white")
    for bar, val in zip(bars3[::-1], ranking["probabilidad"]):
        ax3.text(val*100+0.3, bar.get_y()+bar.get_height()/2,
                 f"{val*100:.1f}%", va="center", fontsize=8.5)
    ax3.set_xlabel("Adjusted Probability (%)", fontsize=11)
    ax3.set_title(f"Top 8 recommended varieties\n"
                  f"Climate: {clima} | Area: {area_ha} ha | Protein: {ganancia_proteina_pct}%",
                  fontsize=12, fontweight="bold")
    ax3.grid(True, axis="x", alpha=0.3)
    p1 = mpatches.Patch(color="#1D9E75", label="Recommended")
    p2 = mpatches.Patch(color="#4A90D9", label=f"Climate {clima}")
    p3 = mpatches.Patch(color="#EF9F27", label="Other climate")
    ax3.legend(handles=[p1, p2, p3], fontsize=8)
    
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
def generateFeatureImportancePlot():
    #Generates a standalone feature importance plot.
    #Optimized with memory management.
    
    global _feat_importances
    
    if _feat_importances is None:
        load_model_RF()
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    fi = _feat_importances.sort_values()
    cols = ["#1D9E75" if v >= fi.mean() else "#9FE1CB" for v in fi]
    bars = ax.barh(fi.index, fi.values * 100, color=cols, edgecolor="white")
    ax.axvline(x=fi.mean() * 100, color="#EF9F27", linestyle="--",
               linewidth=1.5, label=f"Mean ({fi.mean()*100:.1f}%)")
    
    for bar, val in zip(bars, fi.values):
        ax.text(val*100+0.3, bar.get_y()+bar.get_height()/2,
                f"{val*100:.1f}%", va="center", fontsize=9)
    
    ax.set_xlabel("Importance (%)", fontsize=12)
    ax.set_ylabel("Features", fontsize=12)
    ax.set_title("Random Forest - Feature Importance\n(Gini Impurity)", 
                 fontsize=13, fontweight="bold")
    ax.legend()
    ax.grid(True, axis="x", alpha=0.3)
    
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