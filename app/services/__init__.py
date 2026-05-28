# app/services/__init__.py

# ─────────────────────────────────────────────
# Recomendaciones - dataset sintético Forraje
# ─────────────────────────────────────────────
from .recommendation_forraje_service import (
    get_recommendation,
    get_recommendationR,
    get_recommendationB,
)

# ─────────────────────────────────────────────
# Recomendaciones - dataset DANE
# ─────────────────────────────────────────────
from .recommendation_dane_service import (
    get_recommendation_KmeansD,
    get_recommendation_KNN,
    get_recommendation_RandomFD,
    get_recommendation_BayesianDane,
)

# ─────────────────────────────────────────────
# Métricas comparativas
# ─────────────────────────────────────────────
from .metrics_forraje_service import (
    build_metrics_forraje_context,
)

from .metrics_dane_service import (
    build_metrics_dane_context,
)

# ─────────────────────────────────────────────
# Enciclopedia
# ─────────────────────────────────────────────
from .encyclopedia_service import (
    get_all_sheep,
    get_all_goats,
    get_all_fodder,
)


__all__ = [
    # Forraje
    "get_recommendation",
    "get_recommendationR",
    "get_recommendationB",

    # DANE
    "get_recommendation_KmeansD",
    "get_recommendation_KNN",
    "get_recommendation_RandomFD",
    "get_recommendation_BayesianDane",

    # Métricas
    "build_metrics_forraje_context",
    "build_metrics_dane_context",

    # Enciclopedia
    "get_all_sheep",
    "get_all_goats",
    "get_all_fodder",
]