import base64
from pathlib import Path

import streamlit as st


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"

APP_DOLAR = PROJECT_DIR / "app_sii_dolar" / "app_sii_dolar.py"
APP_UTM = PROJECT_DIR / "app_sii_utm" / "app_sii_utm.py"
APP_IPC = PROJECT_DIR / "app_ine_ipc" / "app_ine_ipc.py"
APP_ICL = PROJECT_DIR / "app_ine_icl" / "app_ine_icl.py"
APP_MOP = PROJECT_DIR / "app_indice_polinomico_mop" / "app_indice_polinomico_mop.py"
APP_SIEVO = PROJECT_DIR / "app_sievo" / "app_sievo.py"
APP_CONSOLIDADO = PROJECT_DIR / "app_consolidado_temporal" / "app_consolidado_temporal.py"
APP_TAT_ENAEX = PROJECT_DIR / "apps_tat_enaex" / "app_crear_fechas_calculos_tat" / "app_crear_fechas_calculos_tat.py"


# =========================
# Configuración general
# =========================

st.set_page_config(
    page_title="Proyectos ENAEX",
    page_icon="🏢",
    layout="wide"
)


# =========================
# Logo centrado
# =========================

def mostrar_logo_centrado():
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
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# =========================
# Página principal
# =========================

def pagina_inicio():
    mostrar_logo_centrado()

    st.markdown(
        "<h1 style='text-align: center;'>Portal de Aplicaciones ENAEX</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Selecciona una aplicación desde el menú lateral para consultar indicadores,
            generar resúmenes, visualizar gráficos y descargar archivos Excel o Parquet.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            **Dólar SII**

            Consulta del dólar observado por año y mes.
            """
        )

    with col2:
        st.info(
            """
            **UTM SII**

            Consulta de UTM, UTA e IPC valor puntos.
            """
        )

    with col3:
        st.info(
            """
            **IPC INE**

            Consulta automática del IPC General publicado por el INE.
            """
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.info(
            """
            **ICL INE**

            Índice de Remuneraciones y Costos Laborales.
            """
        )

    with col5:
        st.info(
            """
            **MOP Reajuste Polinómico**

            Índices y precios para cálculo de reajuste polinómico.
            """
        )

    with col6:
        st.info(
            """
            **Savings Bridge**

            Generación de gráfico Savings Bridge desde tabla pegada.
            """
        )

    col7, col8, col9 = st.columns(3)

    with col7:
        st.info(
            """
            **Consolidado Temporal**

            Unifica indicadores SII, INE y MOP en una base mensual.
            """
        )

    with col8:
        st.info(
            """
            **TAT ENAEX**

            Genera fechas finales del match integrado y calcula Performance TAT.
            """
        )


# =========================
# Validación rápida de archivos
# =========================

apps_requeridas = {
    "Dólar SII": APP_DOLAR,
    "UTM SII": APP_UTM,
    "IPC INE": APP_IPC,
    "ICL INE": APP_ICL,
    "MOP Reajuste": APP_MOP,
    "Savings Bridge": APP_SIEVO,
    "Consolidado Temporal": APP_CONSOLIDADO,
    "TAT ENAEX": APP_TAT_ENAEX,
}

apps_faltantes = {
    nombre: ruta
    for nombre, ruta in apps_requeridas.items()
    if not ruta.exists()
}

if apps_faltantes:
    st.error("No se encontraron una o más apps. Revisa los nombres de carpetas y archivos.")

    for nombre, ruta in apps_faltantes.items():
        st.write(f"**{nombre}:** {ruta}")

    st.stop()


# =========================
# Navegación entre apps
# =========================

pagina = st.navigation(
    {
        "Inicio": [
            st.Page(
                pagina_inicio,
                title="Inicio",
                icon="🏠"
            )
        ],
        "Consolidado": [
            st.Page(
                APP_CONSOLIDADO,
                title="Consolidado Temporal",
                icon="🧩"
            ),
        ],
        "TAT ENAEX": [
            st.Page(
                APP_TAT_ENAEX,
                title="Fechas + Performance TAT",
                icon="📊"
            ),
        ],
        "Indicadores SII": [
            st.Page(
                APP_DOLAR,
                title="Dólar SII",
                icon="💵"
            ),
            st.Page(
                APP_UTM,
                title="UTM SII",
                icon="📊"
            ),
        ],
        "Indicadores INE": [
            st.Page(
                APP_IPC,
                title="IPC INE",
                icon="📈"
            ),
            st.Page(
                APP_ICL,
                title="ICL INE",
                icon="📉"
            ),
        ],
        "MOP": [
            st.Page(
                APP_MOP,
                title="Reajuste Polinómico MOP",
                icon="🏗️"
            ),
        ],
        "Análisis": [
            st.Page(
                APP_SIEVO,
                title="Savings Bridge",
                icon="🌉"
            ),
        ],
    }
)

pagina.run()
