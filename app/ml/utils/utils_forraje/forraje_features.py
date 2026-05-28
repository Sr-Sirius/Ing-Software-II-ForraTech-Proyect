import numpy as np
import pandas as pd


FEATURES_RANGE = [
    "ph_min",
    "ph_max",
    "humedad_min",
    "humedad_max",
    "altitud_min",
    "altitud_max",
    "temp_min",
    "temp_max",
]

FEATURES_COMPOSITE = ["composite"]

FORRAJE_WEIGHTS = {
    "ph": 0.30,
    "humedad": 0.20,
    "altitud": 0.30,
    "temp": 0.20,
}

FORRAJE_NORMALIZERS = {
    "ph": 9,
    "humedad": 100,
    "altitud": 4000,
    "temp": 45,
}


def add_forraje_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega columnas comunes:
    ph_mid, humedad_mid, altitud_mid, temp_mid y composite.
    """

    df = df.copy()

    df["ph_mid"] = (df["ph_min"] + df["ph_max"]) / 2
    df["humedad_mid"] = (df["humedad_min"] + df["humedad_max"]) / 2
    df["altitud_mid"] = (df["altitud_min"] + df["altitud_max"]) / 2
    df["temp_mid"] = (df["temp_min"] + df["temp_max"]) / 2

    df["composite"] = (
        FORRAJE_WEIGHTS["ph"] * df["ph_mid"] / FORRAJE_NORMALIZERS["ph"] +
        FORRAJE_WEIGHTS["humedad"] * df["humedad_mid"] / FORRAJE_NORMALIZERS["humedad"] +
        FORRAJE_WEIGHTS["altitud"] * df["altitud_mid"] / FORRAJE_NORMALIZERS["altitud"] +
        FORRAJE_WEIGHTS["temp"] * df["temp_mid"] / FORRAJE_NORMALIZERS["temp"]
    )

    return df


def add_binary_target(df: pd.DataFrame, method: str = "mean") -> tuple[pd.DataFrame, float]:
    """
    Agrega columna optimal:
    1 = óptimo
    0 = no óptimo
    """

    df = df.copy()

    if method == "median":
        threshold = float(df["composite"].quantile(0.50))
    else:
        threshold = float(df["composite"].mean())

    df["optimal"] = (df["composite"] > threshold).astype(int)

    return df, threshold


def user_composite(ph, hum, alt, temp) -> float:
    return (
        FORRAJE_WEIGHTS["ph"] * float(ph) / FORRAJE_NORMALIZERS["ph"] +
        FORRAJE_WEIGHTS["humedad"] * float(hum) / FORRAJE_NORMALIZERS["humedad"] +
        FORRAJE_WEIGHTS["altitud"] * float(alt) / FORRAJE_NORMALIZERS["altitud"] +
        FORRAJE_WEIGHTS["temp"] * float(temp) / FORRAJE_NORMALIZERS["temp"]
    )


def build_user_composite_vector(ph, hum, alt, temp):
    return [[user_composite(ph, hum, alt, temp)]]


def build_user_range_vector(ph, hum, alt, temp):
    """
    Vector de 8 features usado por Bayes y Random Forest.
    """

    return [[
        float(ph),
        float(ph),
        float(hum),
        float(hum),
        float(alt),
        float(alt),
        float(temp),
        float(temp),
    ]]


def compute_affinity(row, user_ph, user_hum, user_alt, user_temp) -> float:
    ph_ok = row["ph_min"] <= user_ph <= row["ph_max"]
    hum_ok = row["humedad_min"] <= user_hum <= row["humedad_max"]
    alt_ok = row["altitud_min"] <= user_alt <= row["altitud_max"]
    tmp_ok = row["temp_min"] <= user_temp <= row["temp_max"]

    return (
        FORRAJE_WEIGHTS["ph"] * ph_ok +
        FORRAJE_WEIGHTS["humedad"] * hum_ok +
        FORRAJE_WEIGHTS["altitud"] * alt_ok +
        FORRAJE_WEIGHTS["temp"] * tmp_ok
    )


def get_best_crops(df: pd.DataFrame, ph, hum, alt, temp, top_n: int = 10):
    df_copy = df.copy()

    df_copy["affinity"] = df_copy.apply(
        lambda row: compute_affinity(row, ph, hum, alt, temp),
        axis=1,
    )

    return (
        df_copy.groupby("nombre")["affinity"]
        .mean()
        .reset_index()
        .sort_values("affinity", ascending=False)
        .head(top_n)
    )


def validate_forraje_input(data):
    try:
        ph_value = float(data.get("ph", 6.5))
        hum_value = float(data.get("humedad", 60))
        alt_value = float(data.get("altitud", 1500))
        temp_value = float(data.get("temperatura", 22))
    except (ValueError, TypeError):
        ph_value = 6.5
        hum_value = 60
        alt_value = 1500
        temp_value = 22

    return ph_value, hum_value, alt_value, temp_value