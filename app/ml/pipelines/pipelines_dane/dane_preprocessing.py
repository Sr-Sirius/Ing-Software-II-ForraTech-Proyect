# app/ml/DANE_real_dataset_model/pipelines/dane_preprocessing.py

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from app.ml.utils.utils_dane.dane_paths import resolve_dane_path
from app.ml.utils.utils_dane.dane_features import (
    FEATURES,
    add_dane_features,
    add_binary_target,
)


def load_dane_dataframe(data_path: str = None):
    """Carga el CSV DANE y aplica feature engineering común."""
    data_path = resolve_dane_path(data_path)
    df = pd.read_csv(data_path)
    df = add_dane_features(df)
    return df


def build_scaled_matrix(df):
    """Construye X y X_scaled con StandardScaler."""
    X = df[FEATURES].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    return X, X_scaled, scaler


def build_pca_columns(df, X_scaled):
    """Agrega pca1 y pca2 al DataFrame."""
    df = df.copy()
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    df["pca1"] = X_pca[:, 0]
    df["pca2"] = X_pca[:, 1]
    return df, pca


def prepare_dane_training_data(
    data_path: str = None,
    target_method: str | None = None,
    with_pca: bool = False,
):
    """
    Pipeline reutilizable para modelos DANE.

    target_method:
    - None: no agrega target binario
    - "mean": optimal con media
    - "median": optimal con mediana
    """
    df = load_dane_dataframe(data_path)

    threshold = None
    if target_method is not None:
        df, threshold = add_binary_target(df, method=target_method)

    X, X_scaled, scaler = build_scaled_matrix(df)

    pca = None
    if with_pca:
        df, pca = build_pca_columns(df, X_scaled)

    return {
        "df": df,
        "X": X,
        "X_scaled": X_scaled,
        "scaler": scaler,
        "pca": pca,
        "threshold": threshold,
        "features": FEATURES,
    }
