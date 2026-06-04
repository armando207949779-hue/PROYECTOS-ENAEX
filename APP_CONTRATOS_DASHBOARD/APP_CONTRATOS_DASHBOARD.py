# ============================================================
# APP_CONTRATOS_DASHBOARD
# Portal principal ENAEX
# Dashboard modular por pestañas
# ============================================================

import base64
from pathlib import Path

import streamlit as st


# ============================================================
# Rutas del proyecto
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Apps ubicadas en:
# PROYECTOS-ENAEX/APP_CONTRATOS_DASHBOARD/
APP_CARGAR_ARCHIVO = BASE_DIR / "01_APP_CARGAR_ARCHIVO.py"
APP_AHORRO = BASE_DIR / "02_APP_AHORRO.py"

# Logo ubicado en:
# PROYECTOS-ENAEX/assets/logo.svg
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="Dashboard Contratos ENAEX",
    page_icon="🏢",
    layout="wide"
)


# ============================================================
# Logo centrado
# ============================================================

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


# ============================================================
# Página de inicio
# ============================================================

def pagina_inicio():
    mostrar_logo_centrado()

    st.markdown(
        "<h1 style='text-align: center;'>Dashboard Contratos ENAEX</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Portal modular para cargar bases, validar información y construir análisis
            de contratos, órdenes de compra, ahorros, hitos y vencimientos.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            **01_CARGA_ARCHIVOS**

            Carga y validación de las bases locales del dashboard.

            Permite revisar:
            - Archivos encontrados
            - DataFrames cargados
            - Columnas
            - Tipos de datos
            - Vista previa
            """
        )

    with col2:
        st.info(
            """
            **02_AHORRO**

            Análisis de ahorro planificado, ahorro real,
            cumplimiento, eficiencia, acumulados y distribución
            por gestor, contrato y tipo de proceso.
            """
        )

    with col3:
        st.info(
            """
            **Arquitectura modular**

            Cada pestaña se conecta a un archivo Python independiente.

            Esto permite mantener el proyecto ordenado y escalable.
            """
        )

    st.markdown("---")

    st.success(
        """
        Para comenzar, entra a **01_CARGA_ARCHIVOS**, carga las bases y luego revisa
        los indicadores en **02_AHORRO**.
        """
    )


# ============================================================
# Validación rápida de apps
# ============================================================

apps_requeridas = {
    "01_CARGA_ARCHIVOS": APP_CARGAR_ARCHIVO,
    "02_AHORRO": APP_AHORRO,
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
                url_path="inicio"
            )
        ],

        "Dashboard": [
            st.Page(
                APP_CARGAR_ARCHIVO,
                title="01_CARGA_ARCHIVOS",
                icon="📁",
                url_path="carga_archivos"
            ),
            st.Page(
                APP_AHORRO,
                title="02_AHORRO",
                icon="💰",
                url_path="ahorro"
            ),
        ],
    }
)


# ============================================================
# Ejecutar página seleccionada
# ============================================================

pagina.run()
