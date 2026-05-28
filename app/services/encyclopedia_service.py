from app.services.data_service import OVINOS, CAPRINOS, FORRAJES

def get_all_sheep():
    return OVINOS

def get_all_goats():
    return CAPRINOS

def get_all_fodder():
    return FORRAJES