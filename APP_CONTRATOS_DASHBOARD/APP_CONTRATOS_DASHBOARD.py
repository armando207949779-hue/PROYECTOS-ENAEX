# ============================================================
# APP_CONTRATOS_DASHBOARD
# Portal principal ENAEX
# Dashboard modular por pestañas
# ============================================================

import sys
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
APP_GASTOS = BASE_DIR / "03_APP_GASTOS.py"
APP_SALUD_CONTRATOS = BASE_DIR / "04_APP_SALUD_CONTRATOS.py"

# Logo ubicado en:
# PROYECTOS-ENAEX/assets/logo.svg
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from assets.configurar_espanol import configurar_espanol


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="Panel Contratos ENAEX",
    page_icon="🏢",
    layout="wide",
)

configurar_espanol()


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
        "<h1 style='text-align: center;'>Panel Contratos ENAEX</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Portal modular para cargar bases, validar información y construir análisis
            de contratos, órdenes de compra, ahorros, hitos y vencimientos.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

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

    col3, col4 = st.columns(2)

    with col3:
        st.info(
            """
            **03_GASTOS**

            Análisis de órdenes de compra, gasto anual,
            gasto mensual, conversión a USD y participación
            según tipo de orden de compra.
            """
        )

    with col4:
        st.info(
            """
            **04_SALUD_CONTRATOS**

            Análisis de vigencia contractual, contratos vencidos,
            próximos a vencer, cobertura ME5A y distribución
            de contratos por gestor y estado.
            """
        )

    st.markdown("---")

    st.success(
        """
        Para comenzar, entra a **01_CARGA_ARCHIVOS** y carga las bases.

        Luego revisa los módulos **02_AHORRO**, **03_GASTOS**
        y **04_SALUD_CONTRATOS**.
        """
    )


# ============================================================
# Validación rápida de apps
# ============================================================

apps_requeridas = {
    "01_CARGA_ARCHIVOS": APP_CARGAR_ARCHIVO,
    "02_AHORRO": APP_AHORRO,
    "03_GASTOS": APP_GASTOS,
    "04_SALUD_CONTRATOS": APP_SALUD_CONTRATOS,
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

        "Panel": [
            st.Page(
                APP_CARGAR_ARCHIVO,
                title="01_CARGA_ARCHIVOS",
                icon="📁",
                url_path="carga_archivos",
            ),
            st.Page(
                APP_AHORRO,
                title="02_AHORRO",
                icon="💰",
                url_path="ahorro",
            ),
            st.Page(
                APP_GASTOS,
                title="03_GASTOS",
                icon="📊",
                url_path="gastos",
            ),
            st.Page(
                APP_SALUD_CONTRATOS,
                title="04_SALUD_CONTRATOS",
                icon="🩺",
                url_path="salud_contratos",
            ),
        ],
    }
)


# ============================================================
# Ejecutar página seleccionada
# ============================================================

pagina.run()
