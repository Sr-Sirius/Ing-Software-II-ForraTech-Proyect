# app/ml/DANE_real_dataset_model/utils/plot_utils.py

import io
import gc
import base64


def fig_to_base64(fig, plt_module):
    """Convierte una figura matplotlib a base64 y libera memoria."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    plt_module.close(fig)
    plt_module.close("all")
    buf.seek(0)
    result = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    gc.collect()
    return result
