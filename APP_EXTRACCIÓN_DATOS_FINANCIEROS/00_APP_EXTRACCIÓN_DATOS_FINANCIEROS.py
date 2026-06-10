# ============================================================
# 00_APP_EXTRACCIÓN_DATOS_FINANCIEROS
# Portal principal ENAEX
# Dashboard modular de datos financieros
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
# PROYECTOS-ENAEX/APP_EXTRACCIÓN_DATOS_FINANCIEROS/
#
# Por eso las apps están en la MISMA carpeta:
APP_MONEDAS_BANCO_CENTRAL = BASE_DIR / "01_APP_MONEDAS_BANCO_CENTRAL.py"
APP_INDICADORES_FINANCIEROS = BASE_DIR / "02_APP_INDICADORES_FINANCIEROS_BANCO_CENTRAL.py"

# Logo ubicado en:
# PROYECTOS-ENAEX/assets/logo.svg
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="Extracción Datos Financieros ENAEX",
    page_icon="💱",
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
        "<h1 style='text-align: center;'>Extracción Datos Financieros ENAEX</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Portal modular para consultar, transformar y descargar datos financieros
            desde fuentes oficiales, incluyendo Banco Central de Chile.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.info(
            """
            **01_DATA_CAMBIO_DOLAR_MONEDAS_BANCO_CENTRAL**

            Consulta datos desde la BDE del Banco Central de Chile.

            Permite revisar:
            - Dólar observado
            - Monedas internacionales
            - UF
            - UTM
            - Valor CLP por unidad
            - Factor USD por unidad
            - Fecha de conversión
            """
        )

    with col2:
        st.info(
            """
            **02_INDICADORES_FINANCIEROS_BANCO_CENTRAL**

            Consulta series temporales desde la BDE del Banco Central.

            Permite revisar:
            - Dólar observado diario, mensual y anual
            - UF
            - UTM
            - IPC
            - ICL
            - IR
            - Histórico por rango de fechas
            - Últimos valores disponibles
            """
        )

    st.markdown("---")

    st.success(
        """
        Para comenzar, entra a una de las pestañas disponibles en **Datos Financieros**:

        - **Data Cambio Dólar Monedas Banco Central**
        - **Indicadores Financieros Banco Central**
        """
    )


# ============================================================
# Validación rápida de apps
# ============================================================

apps_requeridas = {
    "01_APP_MONEDAS_BANCO_CENTRAL": APP_MONEDAS_BANCO_CENTRAL,
    "02_APP_INDICADORES_FINANCIEROS_BANCO_CENTRAL": APP_INDICADORES_FINANCIEROS,
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

        "Datos Financieros": [
            st.Page(
                APP_MONEDAS_BANCO_CENTRAL,
                title="Data Cambio Dólar Monedas Banco Central",
                icon="💱",
                url_path="data_cambio_dolar_monedas_banco_central",
            ),
            st.Page(
                APP_INDICADORES_FINANCIEROS,
                title="Indicadores Financieros Banco Central",
                icon="📈",
                url_path="indicadores_financieros_banco_central",
            ),
        ],
    }
)


# ============================================================
# Ejecutar página seleccionada
# ============================================================

pagina.run()
