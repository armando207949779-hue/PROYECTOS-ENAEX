import base64
from pathlib import Path

import streamlit as st


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"

APP_TAT_CONSOLIDADO = PROJECT_DIR / "app_tat_consolidado" / "app_tat_consolidado.py"
APP_TAT_CONSOLIDADO_FINAL = PROJECT_DIR / "app_tat_consolidado_final" / "app_tat_consolidado_final.py"
APP_TAT_GRAFICOS = PROJECT_DIR / "app_tat_graficos" / "app_tat_graficos.py"
APP_TAT_LIMPIEZA_ARIBA = PROJECT_DIR / "app_tat_limpieza_ariba" / "app_tat_limpieza_ariba.py"
APP_TAT_LIMPIEZA_ME5A = PROJECT_DIR / "app_tat_limpieza_me5a" / "app_tat_limpieza_me5a.py"
APP_TAT_LIMPIEZA_ME80FN = PROJECT_DIR / "app_tat_limpieza_me80fn" / "app_tat_limpieza_me80fn.py"
APP_TAT_MATCH = PROJECT_DIR / "app_tat_match" / "app_tat_match.py"


# =========================
# Configuración general
# =========================

st.set_page_config(
    page_title="TAT ENAEX",
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
        "<h1 style='text-align: center;'>Portal TAT ENAEX</h1>",
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Selecciona una aplicación desde el menú lateral para limpiar archivos,
            consolidar información, realizar cruces, generar gráficos y preparar
            reportes relacionados con el análisis TAT.
        </p>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            **Limpieza Ariba**

            Limpieza y preparación de datos provenientes de Ariba.
            """
        )

    with col2:
        st.info(
            """
            **Limpieza ME5A**

            Limpieza y preparación de información desde ME5A.
            """
        )

    with col3:
        st.info(
            """
            **Limpieza ME80FN**

            Limpieza y preparación de información desde ME80FN.
            """
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.info(
            """
            **Match TAT**

            Cruce y validación de información para análisis TAT.
            """
        )

    with col5:
        st.info(
            """
            **Consolidado TAT**

            Consolidación inicial de archivos procesados.
            """
        )

    with col6:
        st.info(
            """
            **Consolidado Final**

            Generación de base final consolidada para análisis.
            """
        )

    col7, col8, col9 = st.columns(3)

    with col7:
        st.info(
            """
            **Gráficos TAT**

            Visualización y análisis gráfico de resultados TAT.
            """
        )


# =========================
# Validación rápida de archivos
# =========================

apps_requeridas = {
    "Limpieza Ariba": APP_TAT_LIMPIEZA_ARIBA,
    "Limpieza ME5A": APP_TAT_LIMPIEZA_ME5A,
    "Limpieza ME80FN": APP_TAT_LIMPIEZA_ME80FN,
    "Match TAT": APP_TAT_MATCH,
    "Consolidado TAT": APP_TAT_CONSOLIDADO,
    "Consolidado Final": APP_TAT_CONSOLIDADO_FINAL,
    "Gráficos TAT": APP_TAT_GRAFICOS,
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
                icon="🏠"
            )
        ],
        "Limpieza": [
            st.Page(
                APP_TAT_LIMPIEZA_ARIBA,
                title="Limpieza Ariba",
                icon="🧹"
            ),
            st.Page(
                APP_TAT_LIMPIEZA_ME5A,
                title="Limpieza ME5A",
                icon="🧾"
            ),
            st.Page(
                APP_TAT_LIMPIEZA_ME80FN,
                title="Limpieza ME80FN",
                icon="📄"
            ),
        ],
        "Cruce": [
            st.Page(
                APP_TAT_MATCH,
                title="Match TAT",
                icon="🔗"
            ),
        ],
        "Consolidado": [
            st.Page(
                APP_TAT_CONSOLIDADO,
                title="Consolidado TAT",
                icon="🧩"
            ),
            st.Page(
                APP_TAT_CONSOLIDADO_FINAL,
                title="Consolidado Final",
                icon="✅"
            ),
        ],
        "Visualización": [
            st.Page(
                APP_TAT_GRAFICOS,
                title="Gráficos TAT",
                icon="📊"
            ),
        ],
    }
)

pagina.run()
