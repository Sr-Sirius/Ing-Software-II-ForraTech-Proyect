# app/ml/DANE_real_dataset_model/utils/dane_paths.py

import os


def get_default_dane_path() -> str:
    """Ruta por defecto al dataset DANE sin depender de Flask."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "..", ".."))
    return os.path.join(root_dir, "data", "DANE_ena_2019_pastos.csv")


def resolve_dane_path(data_path: str = None) -> str:
    """Resuelve la ruta del dataset DANE y valida existencia."""
    if data_path is None:
        data_path = get_default_dane_path()

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No se encontró el archivo: {data_path}")

    return data_path
