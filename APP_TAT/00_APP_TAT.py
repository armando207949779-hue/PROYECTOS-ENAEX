# ============================================================
# 00_APP_TAT
# Portal principal TAT
# Dashboard modular de apps
# ============================================================

import base64
from pathlib import Path

import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Portal TAT ENAEX",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# SECCIONES Y APPS DISPONIBLES
# ============================================================

APP_SECTIONS = [
    {
        "grupo": "01 Preparación de datos",
        "descripcion": "Limpieza, cruce y cálculo base para construir la información TAT.",
        "apps": [
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
        ],
    },
    {
        "grupo": "02 Operación y consulta",
        "descripcion": "Carga del archivo final, búsqueda de registros y revisión operativa.",
        "apps": [
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
        ],
    },
    {
        "grupo": "03 Performance",
        "descripcion": "Análisis mensual, comparativo y seguimiento de cumplimiento TAT.",
        "apps": [
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
        ],
    },
    {
        "grupo": "04 Gestión de alertas",
        "descripcion": "Seguimiento de vencimientos, pedidos críticos y alertas TAT.",
        "apps": [
            {
                "nombre": "10_ALERTAS",
                "archivo": "10_ALERTAS.py",
                "titulo": "10 Alertas",
                "icono": "🚨",
                "descripcion": "Gestión, revisión y generación de alertas TAT.",
            },
        ],
    },
]

APPS = [
    app
    for seccion in APP_SECTIONS
    for app in seccion["apps"]
]


# ============================================================
# UTILIDADES DE RUTAS
# ============================================================

def obtener_ruta_app(nombre_archivo: str) -> Path:
    """
    Devuelve la ruta de una app dentro de la carpeta APP_TAT.

    Valida distintas variantes:
    - nombre exacto
    - nombre.py
    - nombre sin .py
    """
    nombre_archivo = str(nombre_archivo).strip()

    candidatos = []

    candidatos.append(BASE_DIR / nombre_archivo)

    if not nombre_archivo.endswith(".py"):
        candidatos.append(BASE_DIR / f"{nombre_archivo}.py")

    if nombre_archivo.endswith(".py"):
        candidatos.append(BASE_DIR / nombre_archivo.replace(".py", ""))

    for ruta in candidatos:
        if ruta.exists():
            return ruta

    return candidatos[0]


def validar_apps_disponibles() -> dict:
    apps_requeridas = {
        app["nombre"]: obtener_ruta_app(app["archivo"])
        for app in APPS
    }

    apps_faltantes = {
        nombre: ruta
        for nombre, ruta in apps_requeridas.items()
        if not ruta.exists()
    }

    return apps_faltantes


# ============================================================
# LOGO
# ============================================================

def mostrar_logo():
    if LOGO_PATH.exists():
        logo_svg = LOGO_PATH.read_text(encoding="utf-8")
        logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")

        st.markdown(
            f"""
            <div style="
                width: 100%;
                display: flex;
                justify-content: center;
                align-items: center;
                margin-top: 5px;
                margin-bottom: 10px;
            ">
                <img 
                    src="data:image/svg+xml;base64,{logo_base64}" 
                    style="width: 220px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# COMPONENTES DE LA PÁGINA DE INICIO
# ============================================================

def mostrar_estado_archivo_activo() -> None:
    if "df_tat" in st.session_state and st.session_state.get("df_tat") is not None:
        nombre = st.session_state.get("nombre_archivo_tat", "Archivo activo")
        filas = len(st.session_state["df_tat"])

        st.success(
            f"Archivo activo en sesión: **{nombre}** · **{filas:,} registros**".replace(",", ".")
        )
    else:
        st.info(
            "No hay archivo activo en sesión. Para analizar datos, primero usa **06 Cargar Archivo**."
        )


def mostrar_apps_disponibles() -> None:
    st.subheader("Apps disponibles")

    for seccion in APP_SECTIONS:
        st.markdown(f"#### {seccion['grupo']}")
        st.caption(seccion["descripcion"])

        columnas = st.columns(2)

        for i, app in enumerate(seccion["apps"]):
            ruta_app = obtener_ruta_app(app["archivo"])
            existe = ruta_app.exists()

            estado = "Disponible" if existe else "No encontrado"

            with columnas[i % 2]:
                st.info(
                    f"""
                    **{app["icono"]} {app["titulo"]}**

                    {app["descripcion"]}

                    Estado: **{estado}**
                    """
                )


def mostrar_validacion_apps(apps_faltantes: dict) -> None:
    if not apps_faltantes:
        return

    st.error("No se encontraron una o más apps requeridas.")

    for nombre, ruta in apps_faltantes.items():
        st.write(f"**{nombre}:** `{ruta}`")


# ============================================================
# PÁGINA DE INICIO
# ============================================================

def pagina_inicio() -> None:
    mostrar_logo()

    st.markdown(
        "<h1 style='text-align: center;'>Portal TAT ENAEX</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px; color: #555;'>
            Portal modular para consultar, analizar y gestionar información
            relacionada con TAT mediante distintas apps operativas.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    mostrar_estado_archivo_activo()

    st.markdown("---")

    mostrar_apps_disponibles()

    st.markdown("---")

    st.success(
        "Para comenzar, selecciona una app desde el menú de navegación del portal."
    )


# ============================================================
# VALIDACIÓN DE APPS
# ============================================================

apps_faltantes = validar_apps_disponibles()

if apps_faltantes:
    mostrar_logo()
    mostrar_validacion_apps(apps_faltantes)
    st.stop()


# ============================================================
# CONSTRUCCIÓN DE PÁGINAS
# ============================================================

def crear_pagina_app(app: dict):
    ruta_app = obtener_ruta_app(app["archivo"])

    return st.Page(
        ruta_app,
        title=app["titulo"],
        icon=app["icono"],
        url_path=app["nombre"].lower(),
    )


def construir_paginas_por_seccion() -> dict:
    paginas = {
        "Inicio": [
            st.Page(
                pagina_inicio,
                title="Inicio",
                icon="🏠",
                url_path="inicio",
            )
        ]
    }

    for seccion in APP_SECTIONS:
        paginas[seccion["grupo"]] = [
            crear_pagina_app(app)
            for app in seccion["apps"]
        ]

    return paginas


paginas_navegacion = construir_paginas_por_seccion()


# ============================================================
# NAVEGACIÓN ENTRE PÁGINAS
# ============================================================

pagina = st.navigation(paginas_navegacion)


# ============================================================
# EJECUTAR PÁGINA SELECCIONADA
# ============================================================

pagina.run()
