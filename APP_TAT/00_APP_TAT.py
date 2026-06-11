# ============================================================
# 00_APP_TAT
# Portal principal TAT
# Dashboard modular de apps
# ============================================================

import base64
from pathlib import Path

import streamlit as st


# ============================================================
# Rutas del proyecto
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Este archivo está en:
# PROYECTOS-ENAEX/APP_TAT/
#
# Por eso las apps están en la MISMA carpeta:
APP_01 = BASE_DIR / "01_APP_TAT.py"
APP_02 = BASE_DIR / "02_APP_TAT.py"

# Logo ubicado en:
# PROYECTOS-ENAEX/assets/logo.svg
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="Portal TAT ENAEX",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# Logo centrado
# ============================================================

def mostrar_logo_centrado() -> None:
    """Muestra el logo corporativo centrado en la página de inicio."""
    if LOGO_PATH.exists():
        logo_svg = LOGO_PATH.read_text(encoding="utf-8")

        logo_base64 = base64.b64encode(
            logo_svg.encode("utf-8")
        ).decode("utf-8")

        st.markdown(
            f"""
            <div style="
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 10px;
                margin-bottom: 20px;
            ">
                <img
                    src="data:image/svg+xml;base64,{logo_base64}"
                    style="width: 260px; display: block;"
                    alt="ENAEX"
                >
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# Página de inicio
# ============================================================

def pagina_inicio() -> None:
    mostrar_logo_centrado()

    st.markdown(
        "<h1 style='text-align: center;'>Portal TAT ENAEX</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Portal modular para consultar, analizar y gestionar información
            relacionada con TAT mediante distintas apps operativas.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            """
            **01_APP_TAT**

            Primera app del portal TAT.

            Permite revisar:
            - Información base de TAT
            - Consultas operativas
            - Visualización de datos
            - Descarga de resultados
            """
        )

    with col2:
        st.info(
            """
            **02_APP_TAT**

            Segunda app del portal TAT.

            Permite revisar:
            - Indicadores asociados
            - Seguimiento de información
            - Análisis por filtros
            - Reportes y exportaciones
            """
        )

    st.markdown("---")

    st.success(
        """
        Para comenzar, entra a una de las pestañas disponibles en **Apps**:

        - **01 App TAT**
        - **02 App TAT**
        """
    )


# ============================================================
# Validación rápida de apps
# ============================================================

apps_requeridas = {
    "01_APP_TAT": APP_01,
    "02_APP_TAT": APP_02,
}

apps_faltantes = {
    nombre: ruta
    for nombre, ruta in apps_requeridas.items()
    if not ruta.exists()
}

if apps_faltantes:
    st.error("No se encontraron una o más apps requeridas.")

    for nombre, ruta in apps_faltantes.items():
        st.write(f"**{nombre}:** `{ruta}`")

    st.stop()


# ============================================================
# Navegación entre páginas
# ============================================================

pagina = st.navigation(
    {
        "Inicio": [
            st.Page(
                pagina_inicio,
                title="Inicio",
                icon="🏠",
                url_path="inicio",
            )
        ],

        "Apps": [
            st.Page(
                APP_01,
                title="01 App TAT",
                icon="📋",
                url_path="app_tat_01",
            ),
            st.Page(
                APP_02,
                title="02 App TAT",
                icon="📈",
                url_path="app_tat_02",
            ),
        ],
    }
)


# ============================================================
# Ejecutar página seleccionada
# ============================================================

pagina.run()
