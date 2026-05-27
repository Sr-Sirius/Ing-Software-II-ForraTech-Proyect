# app/ml/DANE_real_dataset_model/utils/dane_features.py

import numpy as np
import pandas as pd


FEATURES = [
    "log_area",
    "score_proteina",
    "clima_num",
    "prop_pastoreo_continuo",
    "prop_pastoreo_rotacional",
    "prop_corte",
    "prop_banco_proteina",
]


PROTEIN_WEIGHTS = {
    "prop_banco_proteina": 0.50,
    "prop_corte": 0.30,
    "prop_pastoreo_rotacional": 0.10,
    "prop_pastoreo_continuo": 0.10,
}


def normalize_clima(clima: str) -> str:
    """Normaliza el clima a los valores usados por el dataset DANE."""
    clima = str(clima).strip().lower()
    return clima if clima in ("calido", "frio") else "calido"


def clima_to_num(clima: str) -> int:
    """frio = 1, calido = 0."""
    return 1 if normalize_clima(clima) == "frio" else 0


def add_dane_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columnas comunes usadas por todos los modelos DANE:
    score_proteina, log_area y clima_num.
    """
    df = df.copy()

    df["score_proteina"] = (
        PROTEIN_WEIGHTS["prop_banco_proteina"] * df["prop_banco_proteina"] +
        PROTEIN_WEIGHTS["prop_corte"] * df["prop_corte"] +
        PROTEIN_WEIGHTS["prop_pastoreo_rotacional"] * df["prop_pastoreo_rotacional"] +
        PROTEIN_WEIGHTS["prop_pastoreo_continuo"] * df["prop_pastoreo_continuo"]
    )

    df["log_area"] = np.log1p(df["area_sembrada_ha"])

    df["clima_num"] = (
        df["clima"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({"frio": 1, "calido": 0})
        .fillna(0)
        .astype(int)
    )

    return df


def build_user_vector(area_ha, ganancia_proteina_pct, clima):
    """
    Construye el vector DANE en el mismo orden de FEATURES.
    """
    gp = float(ganancia_proteina_pct) / 100.0

    prop_banco = min(gp * 0.60, 0.60)
    prop_corte = min(gp * 0.40, 0.40)
    prop_rot = max(1.0 - prop_banco - prop_corte - 0.05, 0.0)
    prop_cont = max(0.05, 1.0 - prop_banco - prop_corte - prop_rot)

    clima_num = clima_to_num(clima)
    log_area = np.log1p(float(area_ha))

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


def add_binary_target(df: pd.DataFrame, method: str = "median") -> tuple[pd.DataFrame, float]:
    """
    Agrega columna optimal:
    1 = Alta aptitud proteica
    0 = Baja aptitud proteica
    """
    df = df.copy()

    if method == "mean":
        threshold = float(df["score_proteina"].mean())
    else:
        threshold = float(df["score_proteina"].quantile(0.50))

    df["optimal"] = (df["score_proteina"] >= threshold).astype(int)
    return df, threshold


def validate_dane_input(data):
    """Valida inputs DANE desde request.form o dict."""
    try:
        area_value = float(data.get("area_ha", 50.0))
        proteina_value = float(data.get("ganancia_proteina_pct", 70.0))
        clima_value = normalize_clima(data.get("clima", "calido"))
    except (ValueError, TypeError):
        area_value = 50.0
        proteina_value = 70.0
        clima_value = "calido"

    return area_value, proteina_value, clima_value
