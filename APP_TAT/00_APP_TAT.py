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

# Logo ubicado en:
# PROYECTOS-ENAEX/assets/logo.svg
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Apps disponibles
# ============================================================

APPS = [
    {
        "nombre": "01_LIMPIEZA_ME5A",
        "archivo": "01_LIMPIEZA_ME5A.py",
        "titulo": "01 Limpieza ME5A",
        "icono": "🧹",
        "descripcion": "Limpieza y preparación de datos ME5A.",
    },
    {
        "nombre": "02_LIMPIEZA_ARIBA",
        "archivo": "02_LIMPIEZA_ARIBA",
        "titulo": "02 Limpieza Ariba",
        "icono": "🧹",
        "descripcion": "Limpieza y preparación de información desde Ariba.",
    },
    {
        "nombre": "03_LIMPIEZA_ME80FN",
        "archivo": "03_LIMPIEZA_ME80FN",
        "titulo": "03 Limpieza ME80FN",
        "icono": "🧹",
        "descripcion": "Limpieza y procesamiento de datos ME80FN.",
    },
    {
        "nombre": "04_MATCH",
        "archivo": "04_MATCH.py",
        "titulo": "04 Match",
        "icono": "🔗",
        "descripcion": "Cruce y emparejamiento de información entre fuentes.",
    },
    {
        "nombre": "05_CALCULOS",
        "archivo": "05_CALCULOS.py",
        "titulo": "05 Cálculos",
        "icono": "🧮",
        "descripcion": "Cálculos operativos y generación de resultados TAT.",
    },
    {
        "nombre": "06_CARGAR_ARCHIVO",
        "archivo": "06_CARGAR_ARCHIVO.py",
        "titulo": "06 Cargar Archivo",
        "icono": "📤",
        "descripcion": "Carga de archivos para el flujo operativo.",
    },
    {
        "nombre": "07_FILTRO",
        "archivo": "07_FILTRO.py",
        "titulo": "07 Filtro",
        "icono": "🔎",
        "descripcion": "Aplicación de filtros y segmentación de información.",
    },
    {
        "nombre": "08_PERFORMANCE_PLANTA_MENSUAL",
        "archivo": "08_PERFORMANCE_PLANTA_MENSUAL.py",
        "titulo": "08 Performance Planta Mensual",
        "icono": "📊",
        "descripcion": "Análisis mensual de performance por planta.",
    },
    {
        "nombre": "09_PERFORMANCE_PLANTAS",
        "archivo": "09_PERFORMANCE_PLANTAS.py",
        "titulo": "09 Performance Plantas",
        "icono": "📈",
        "descripcion": "Análisis comparativo de performance por plantas.",
    },
    {
        "nombre": "10_ALERTAS",
        "archivo": "10_ALERTAS.py",
        "titulo": "10 Alertas",
        "icono": "🚨",
        "descripcion": "Gestión, revisión y generación de alertas TAT.",
    },
]


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="Portal TAT ENAEX",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# Utilidades
# ============================================================

def obtener_ruta_app(nombre_archivo: str) -> Path:
    """
    Devuelve la ruta de una app dentro de la carpeta APP_TAT.

    Algunas apps del repositorio aparecen sin extensión .py.
    Esta función permite validar ambas opciones:
    - nombre_archivo
    - nombre_archivo.py
    """
    ruta = BASE_DIR / nombre_archivo

    if ruta.exists():
        return ruta

    if not nombre_archivo.endswith(".py"):
        ruta_py = BASE_DIR / f"{nombre_archivo}.py"
        if ruta_py.exists():
            return ruta_py

    return ruta


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

    st.subheader("Apps disponibles")

    columnas = st.columns(2)

    for i, app in enumerate(APPS):
        with columnas[i % 2]:
            st.info(
                f"""
                **{app["titulo"]}**

                {app["descripcion"]}
                """
            )

    st.markdown("---")

    st.success(
        """
        Para comenzar, selecciona una app desde el menú de navegación del portal.
        """
    )


# ============================================================
# Validación rápida de apps
# ============================================================

apps_requeridas = {
    app["nombre"]: obtener_ruta_app(app["archivo"])
    for app in APPS
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
# Construcción de páginas
# ============================================================

paginas_apps = []

for app in APPS:
    ruta_app = obtener_ruta_app(app["archivo"])

    paginas_apps.append(
        st.Page(
            ruta_app,
            title=app["titulo"],
            icon=app["icono"],
            url_path=app["nombre"].lower(),
        )
    )


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
        "Apps TAT": paginas_apps,
    }
)


# ============================================================
# Ejecutar página seleccionada
# ============================================================

pagina.run()
