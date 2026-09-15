# services/example_animal_service.py

from copy import deepcopy


EXAMPLE_ANIMALS = {
    "oveja": {
        "identification": "OV-001",
        "species": "Ovino",
        "name": "Luna",
        "breed": "Dorper",
        "sex": "Hembra",
        "birth_date": "2024-03-15",
        "weight": 45.0,
        "observations": (
            "Oveja de ejemplo para mostrar el proceso de registro "
            "y la presentación de su ficha."
        ),
    },
    "cabra": {
        "identification": "CA-001",
        "species": "Caprino",
        "name": "Canela",
        "breed": "Saanen",
        "sex": "Hembra",
        "birth_date": "2024-06-10",
        "weight": 38.0,
        "observations": (
            "Cabra de ejemplo para mostrar el proceso de registro "
            "y la presentación de su ficha."
        ),
    },
}


def get_example_animals():
    """
    Devuelve ambos animales de demostración.

    Retorna copias para evitar que los cambios realizados durante
    una petición modifiquen los ejemplos originales.
    """
    return deepcopy(EXAMPLE_ANIMALS)


def get_example_animal(animal_type="oveja"):
    """
    Devuelve el animal de ejemplo seleccionado.

    Args:
        animal_type (str): 'oveja' o 'cabra'.
            Por defecto se muestra la oveja.

    Returns:
        dict: Datos del animal seleccionado.

    Raises:
        ValueError: Si el tipo de animal no es válido.
    """
    if not isinstance(animal_type, str):
        raise ValueError("El tipo de animal debe ser 'oveja' o 'cabra'.")

    animal_type = animal_type.strip().lower()

    if animal_type not in EXAMPLE_ANIMALS:
        raise ValueError("El tipo de animal debe ser 'oveja' o 'cabra'.")

    return deepcopy(EXAMPLE_ANIMALS[animal_type])