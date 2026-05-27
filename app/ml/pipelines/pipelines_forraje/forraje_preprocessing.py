import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from app.ml.utils.utils_forraje.forraje_paths import resolve_forraje_path
from app.ml.utils.utils_forraje.forraje_features import (
    FEATURES_RANGE,
    FEATURES_COMPOSITE,
    add_forraje_features,
    add_binary_target,
)


def load_forraje_dataframe(data_path: str = None) -> pd.DataFrame:
    data_path = resolve_forraje_path(data_path)
    df = pd.read_csv(data_path)
    df = add_forraje_features(df)

    return df


def build_feature_matrix(df: pd.DataFrame, feature_mode: str = "range"):
    """
    feature_mode:
    - range: 8 variables de rangos.
    - composite: solo el puntaje composite.
    """

    if feature_mode == "composite":
        features = FEATURES_COMPOSITE
    else:
        features = FEATURES_RANGE

    X = df[features].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    return X, X_scaled, scaler, features


def prepare_forraje_training_data(
    data_path: str = None,
    feature_mode: str = "range",
    target_method: str = "mean",
    test_size: float = 0.20,
    random_state: int = 42,
    stratify: bool = True,
):
    df = load_forraje_dataframe(data_path)
    df, threshold = add_binary_target(df, method=target_method)

    X, X_scaled, scaler, features = build_feature_matrix(
        df,
        feature_mode=feature_mode,
    )

    y = df["optimal"].values

    stratify_y = y if stratify else None

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify_y,
    )

    return {
        "df": df,
        "X": X,
        "X_scaled": X_scaled,
        "y": y,
        "scaler": scaler,
        "threshold": threshold,
        "features": features,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
    }