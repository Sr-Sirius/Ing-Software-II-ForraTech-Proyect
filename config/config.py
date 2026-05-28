class Config:
    SECRET_KEY = "una_clave_muy_segura_y_larga_123"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_PATH_PASTOS = os.path.join(BASE_DIR, "data", "DANE_ena_2019_pastos.csv")