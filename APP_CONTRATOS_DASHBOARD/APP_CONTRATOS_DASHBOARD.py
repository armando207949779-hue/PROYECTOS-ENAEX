# ============================================================
# Portal principal ENAEX
# Dashboard modular por pestañas
# Cada pestaña llama a un código/app independiente
# ============================================================

import base64
from pathlib import Path

import streamlit as st


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"

APP_AHORRO = (
    PROJECT_DIR
    / "app_ahorro"
    / "app_ahorro.py"
)


# =========================
# Configuración general
# =========================

st.set_page_config(
    page_title="Dashboard ENAEX",
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
        "<h1 style='text-align: center;'>Dashboard ENAEX</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Portal principal para integrar aplicaciones analíticas por pestañas.
            Cada pestaña llamará a un módulo independiente del dashboard.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            **AHORRO**

            Análisis de ahorro real, ahorro planificado,
            cumplimiento, eficiencia y acumulados.
            """
        )

    with col2:
        st.info(
            """
            **Próxima pestaña**

            Espacio reservado para integrar un nuevo módulo.
            """
        )

    with col3:
        st.info(
            """
            **Arquitectura modular**

            Cada pestaña se conecta a un archivo Python separado.
            """
        )


# =========================
# Validación rápida de archivos
# =========================

apps_requeridas = {
    "AHORRO": APP_AHORRO,
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

        "Dashboard": [
            st.Page(
                APP_AHORRO,
                title="AHORRO",
                icon="💰",
                url_path="ahorro"
            ),
        ],
    }
)

pagina.run()
