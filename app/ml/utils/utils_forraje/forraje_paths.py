import os


def get_default_forraje_path() -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, "..", "..", "..", ".."))

    return os.path.join(
        root_dir,
        "data",
        "forrajeo_1000.csv",
    )


def resolve_forraje_path(data_path: str = None) -> str:
    if data_path is None:
        data_path = get_default_forraje_path()

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"No se encontró el archivo: {data_path}")

    return data_path