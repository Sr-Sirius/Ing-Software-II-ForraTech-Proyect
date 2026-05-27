# ─────────────────────────────────────────────
# Utils DANE
# ─────────────────────────────────────────────
from .utils_dane.dane_features import (
    FEATURES,
    PROTEIN_WEIGHTS,
    normalize_clima,
    clima_to_num,
    add_dane_features,
    build_user_vector,
    add_binary_target,
    validate_dane_input,
)

from .utils_dane.dane_paths import (
    get_default_dane_path,
    resolve_dane_path,
)

from .utils_dane.plot_utils import (
    fig_to_base64,
)

from .utils_forraje.forraje_features import (
    FEATURES_RANGE,
    FEATURES_COMPOSITE,
    FORRAJE_WEIGHTS,
    FORRAJE_NORMALIZERS,
    add_forraje_features,
    add_binary_target,
    user_composite,
    build_user_composite_vector,
    build_user_range_vector,
    compute_affinity,
    get_best_crops,
    validate_forraje_input,
)

from .utils_forraje.forraje_paths import (
    get_default_forraje_path,
    resolve_forraje_path,
)

from .utils_forraje.plot_utils import (
    fig_to_base64,
)

# ─────────────────────────────────────────────
# Utils Forraje
# ─────────────────────────────────────────────
from .utils_forraje.forraje_features import (
    FEATURES_RANGE as FORRAJE_FEATURES_RANGE,
    FEATURES_COMPOSITE as FORRAJE_FEATURES_COMPOSITE,
    FORRAJE_WEIGHTS,
    FORRAJE_NORMALIZERS,
    add_forraje_features,
    add_binary_target as add_forraje_binary_target,
    user_composite,
    build_user_composite_vector,
    build_user_range_vector,
    compute_affinity as compute_forraje_affinity,
    get_best_crops as get_best_forraje_crops,
    validate_forraje_input,
)

from .utils_forraje.forraje_paths import (
    get_default_forraje_path,
    resolve_forraje_path,
)

from .utils_forraje.plot_utils import (
    fig_to_base64 as fig_to_base64_forraje,
)