"""Utilidades compartidas para configurar el idioma español en apps Streamlit."""

from __future__ import annotations

import locale
import sys
from pathlib import Path

import streamlit.components.v1 as components

_LOCALES_ES = (
    "es_CL.UTF-8",
    "es_ES.UTF-8",
    "es.UTF-8",
    "es_CL",
    "es_ES",
    "es",
)

_LANG_SCRIPT = """
<script>
(function () {
    const doc = window.parent.document;
    if (!doc || !doc.documentElement) {
        return;
    }
    doc.documentElement.lang = "es";
})();
</script>
"""


def _configurar_locale_sistema() -> None:
    for codigo in _LOCALES_ES:
        try:
            locale.setlocale(locale.LC_ALL, codigo)
            return
        except locale.Error:
            continue


def _configurar_matplotlib() -> None:
    try:
        import matplotlib as mpl
    except ImportError:
        return

    mpl.rcParams["axes.formatter.use_locale"] = True

    for codigo in _LOCALES_ES:
        try:
            mpl.rcParams["locale.language"] = codigo.split(".")[0].replace("_", "-")
            break
        except Exception:
            continue


def configurar_espanol() -> None:
    """Marca la app como español y ajusta locale del sistema y gráficos."""
    _configurar_locale_sistema()
    _configurar_matplotlib()
    components.html(_LANG_SCRIPT, height=0, width=0)


def importar_desde_proyecto(project_dir: Path):
    """Importa este módulo cuando la app no tiene el directorio raíz en sys.path."""
    project_dir = project_dir.resolve()
    project_key = str(project_dir)

    if project_key not in sys.path:
        sys.path.insert(0, project_key)

    from assets.configurar_espanol import configurar_espanol as _configurar

    return _configurar
