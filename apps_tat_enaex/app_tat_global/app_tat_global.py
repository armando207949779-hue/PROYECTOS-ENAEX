# ============================================================
# Portal principal TAT ENAEX
# Navegación general entre carga, limpieza, cruce, cálculos,
# análisis gráfico y alertas TAT
# ============================================================

import sys
import base64
from pathlib import Path

import streamlit as st


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from assets.configurar_espanol import configurar_espanol

APP_TAT_CARGAR_ARCHIVO = (
    PROJECT_DIR
    / "app_tat_cargar_archivo"
    / "app_tat_crear_archivo.py"
)

APP_CREAR_FECHAS_CALCULOS_TAT = (
    PROJECT_DIR
    / "app_crear_fechas_calculos_tat"
    / "app_crear_fechas_calculos_tat.py"
)

APP_TAT_ESTADO_PEDIDO = (
    PROJECT_DIR
    / "app_tat_estado_pedido"
    / "app_tat_estado_pedido.py"
)

APP_TAT_FILTRO = (
    PROJECT_DIR
    / "app_tat_filtro"
    / "app_tat_filtro.py"
)

APP_TAT_GRAFICOS = (
    PROJECT_DIR
    / "app_tat_graficos"
    / "app_tat_graficos.py"
)

APP_GRAPH_PERFORMANCE_PLANTAS = (
    PROJECT_DIR
    / "app_tat_graficos"
    / "app_graph_performance_plantas.py"
)

APP_TAT_ALERTAS = (
    PROJECT_DIR
    / "app_tat_alertas"
    / "app_tat_alertas.py"
)

APP_TAT_LIMPIEZA_ARIBA = (
    PROJECT_DIR
    / "app_tat_limpieza_ariba"
    / "app_tat_limpieza_ariba.py"
)

APP_TAT_LIMPIEZA_ME5A = (
    PROJECT_DIR
    / "app_tat_limpieza_me5a"
    / "app_tat_limpieza_me5a.py"
)

APP_TAT_LIMPIEZA_ME80FN = (
    PROJECT_DIR
    / "app_tat_limpieza_me80fn"
    / "app_tat_limpieza_me80fn.py"
)

APP_TAT_MATCH = (
    PROJECT_DIR
    / "app_tat_match"
    / "app_tat_match.py"
)


# =========================
# Configuración general
# =========================

st.set_page_config(
    page_title="TAT ENAEX",
    page_icon="🏢",
    layout="wide"
)

configurar_espanol()


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
        "<h1 style='text-align: center;'>Portal TAT ENAEX</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Selecciona una aplicación desde el menú lateral para cargar archivos,
            limpiar datos, realizar cruces, generar fechas finales, calcular performance TAT,
            filtrar datos, visualizar performance mensual y revisar alertas operacionales del proceso TAT.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            **Cargar archivo**

            Carga el archivo base una sola vez para reutilizarlo en filtros y visualizaciones.
            """
        )

    with col2:
        st.info(
            """
            **Limpieza de datos**

            Prepara la información proveniente de Ariba, ME5A y NME80FN antes del cruce.
            """
        )

    with col3:
        st.info(
            """
            **Match TAT**

            Cruce y validación de información entre las fuentes principales del proceso.
            """
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.info(
            """
            **Fechas + Cálculos TAT**

            Generación de fechas finales, cálculo de indicadores y performance TAT.
            """
        )

    with col5:
        st.info(
            """
            **Filtro TAT**

            Filtrado y depuración de información TAT según criterios definidos.
            """
        )

    with col6:
        st.info(
            """
            **Performance Mensual**

            Visualización y análisis del performance mensual.
            """
        )

    col7, col8, col9 = st.columns(3)

    with col7:
        st.info(
            """
            **Performance de Plantas**

            Visualización del performance TAT para Prillex, Río Loa y plantas de servicios.
            """
        )

    with col8:
        st.info(
            """
            **Alertas TAT**

            Identificación de casos críticos, atrasos, incumplimientos y registros que requieren revisión.
            """
        )

    with col9:
        st.info(
            """
            **Flujo recomendado**

            Limpieza → Cruce → Fechas y cálculos → Performance mensual → Alertas.
            """
        )


# =========================
# Validación rápida de archivos
# =========================

apps_requeridas = {
    "Cargar archivo": APP_TAT_CARGAR_ARCHIVO,
    "Limpieza Ariba": APP_TAT_LIMPIEZA_ARIBA,
    "Limpieza ME5A": APP_TAT_LIMPIEZA_ME5A,
    "Limpieza NME80FN": APP_TAT_LIMPIEZA_ME80FN,
    "Match TAT": APP_TAT_MATCH,
    "Fechas + Cálculos TAT": APP_CREAR_FECHAS_CALCULOS_TAT,
    "Filtro TAT": APP_TAT_FILTRO,
    "Performance Mensual": APP_TAT_GRAFICOS,
    "Performance de Plantas": APP_GRAPH_PERFORMANCE_PLANTAS,
    "Alertas TAT": APP_TAT_ALERTAS,
}

apps_faltantes = {
    nombre: ruta
    for nombre, ruta in apps_requeridas.items()
    if not ruta.exists()
}

if apps_faltantes:
    st.error("No se encontraron una o más apps. Revisa los nombres de carpetas y archivos.")

    for nombre, ruta in apps_faltantes.items():
        st.write(f"**{nombre}:** `{ruta}`")

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
                icon="🏠",
                url_path="inicio"
            )
        ],

        "Limpieza": [
            st.Page(
                APP_TAT_LIMPIEZA_ARIBA,
                title="Limpieza Ariba",
                icon="🧹",
                url_path="limpieza-ariba"
            ),
            st.Page(
                APP_TAT_LIMPIEZA_ME5A,
                title="Limpieza ME5A",
                icon="🧾",
                url_path="limpieza-me5a"
            ),
            st.Page(
                APP_TAT_LIMPIEZA_ME80FN,
                title="Limpieza NME80FN",
                icon="📄",
                url_path="limpieza-nme80fn"
            ),
        ],

        "Cruce": [
            st.Page(
                APP_TAT_MATCH,
                title="Match TAT",
                icon="🔗",
                url_path="match-tat"
            ),
        ],

        "Fechas y cálculos": [
            st.Page(
                APP_CREAR_FECHAS_CALCULOS_TAT,
                title="Fechas + Cálculos TAT",
                icon="📊",
                url_path="fechas-calculos-tat"
            ),
        ],

        "Análisis TAT": [
            st.Page(
                APP_TAT_CARGAR_ARCHIVO,
                title="Cargar archivo",
                icon="📁",
                url_path="cargar-archivo"
            ),
            st.Page(
                APP_TAT_FILTRO,
                title="Filtro TAT",
                icon="🔎",
                url_path="filtro-tat"
            ),
            st.Page(
                APP_TAT_GRAFICOS,
                title="Performance Mensual",
                icon="📊",
                url_path="performance-mensual"
            ),
            st.Page(
                APP_GRAPH_PERFORMANCE_PLANTAS,
                title="Performance de Plantas",
                icon="🏭",
                url_path="performance-plantas"
            ),
            st.Page(
                APP_TAT_ALERTAS,
                title="Alertas TAT",
                icon="🚨",
                url_path="alertas-tat"
            ),
        ],
    }
)

pagina.run()
