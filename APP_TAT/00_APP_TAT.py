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

    # 1. Nombre tal como viene configurado
    candidatos.append(BASE_DIR / nombre_archivo)

    # 2. Si viene sin .py, probar con .py
    if not nombre_archivo.endswith(".py"):
        candidatos.append(BASE_DIR / f"{nombre_archivo}.py")

    # 3. Si viene con .py, probar sin .py
    if nombre_archivo.endswith(".py"):
        candidatos.append(BASE_DIR / nombre_archivo.replace(".py", ""))

    for ruta in candidatos:
        if ruta.exists():
            return ruta

    return candidatos[0]


def validar_apps_disponibles() -> dict:
    """
    Valida que todos los archivos configurados existan.
    Retorna un diccionario con las apps faltantes.
    """
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
# ESTILOS DEL PORTAL
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            padding: 14px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
        }

        .tat-home-title {
            text-align: center;
            font-size: 2.1rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 0.25rem;
        }

        .tat-home-subtitle {
            text-align: center;
            font-size: 1rem;
            color: #6b7280;
            margin-bottom: 1.5rem;
        }

        .tat-section-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 18px 20px;
            margin-bottom: 16px;
        }

        .tat-section-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 4px;
        }

        .tat-section-description {
            color: #6b7280;
            font-size: 0.88rem;
            margin-bottom: 12px;
        }

        .tat-app-card {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 14px 16px;
            min-height: 132px;
            margin-bottom: 12px;
        }

        .tat-app-title {
            font-size: 0.98rem;
            font-weight: 800;
            color: #111827;
            margin-bottom: 6px;
        }

        .tat-app-description {
            color: #4b5563;
            font-size: 0.86rem;
            line-height: 1.35;
        }

        .tat-flow-card {
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 16px 18px;
            margin-bottom: 12px;
            min-height: 145px;
        }

        .tat-flow-step {
            font-size: 0.82rem;
            font-weight: 700;
            color: #374151;
            margin-bottom: 4px;
        }

        .tat-flow-detail {
            font-size: 0.82rem;
            color: #6b7280;
            line-height: 1.35;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# COMPONENTES DE LA PÁGINA DE INICIO
# ============================================================

def estado_archivo_activo() -> str:
    """
    Retorna un texto simple indicando si existe df_tat en sesión.
    """
    if "df_tat" in st.session_state and st.session_state.get("df_tat") is not None:
        nombre = st.session_state.get("nombre_archivo_tat", "Archivo activo")
        filas = len(st.session_state["df_tat"])

        return f"{nombre} · {filas:,} registros".replace(",", ".")

    return "Sin archivo activo"


def mostrar_resumen_portal() -> None:
    total_apps = len(APPS)
    total_secciones = len(APP_SECTIONS)
    archivo_activo = estado_archivo_activo()

    col1, col2, col3 = st.columns(3)

    col1.metric("Apps disponibles", total_apps)
    col2.metric("Secciones", total_secciones)
    col3.metric("Archivo activo", archivo_activo)


def mostrar_flujo_recomendado() -> None:
    st.markdown("### Flujo recomendado")

    pasos = [
        {
            "titulo": "1. Preparar datos",
            "detalle": "Ejecutar limpieza ME5A, Ariba y ME80FN. Luego cruzar fuentes en Match y calcular indicadores TAT.",
        },
        {
            "titulo": "2. Cargar archivo final",
            "detalle": "Usar 06_CARGAR_ARCHIVO para dejar disponible el archivo consolidado en sesión.",
        },
        {
            "titulo": "3. Consultar registros",
            "detalle": "Usar 07_FILTRO para buscar SolPed, pedidos, posiciones, materiales y revisar el estado detallado.",
        },
        {
            "titulo": "4. Analizar performance",
            "detalle": "Revisar 08 y 09 para análisis mensual, cumplimiento por planta y detalle semanal.",
        },
        {
            "titulo": "5. Gestionar alertas",
            "detalle": "Usar 10_ALERTAS para revisar vencimientos, pedidos críticos y expedientes de seguimiento.",
        },
    ]

    cols = st.columns(len(pasos))

    for col, paso in zip(cols, pasos):
        with col:
            st.markdown(
                f"""
                <div class="tat-flow-card">
                    <div class="tat-flow-step">{paso["titulo"]}</div>
                    <div class="tat-flow-detail">{paso["detalle"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def mostrar_catalogo_apps() -> None:
    st.markdown("### Apps disponibles por sección")

    for seccion in APP_SECTIONS:
        st.markdown(
            f"""
            <div class="tat-section-card">
                <div class="tat-section-title">{seccion["grupo"]}</div>
                <div class="tat-section-description">{seccion["descripcion"]}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        columnas = st.columns(2)

        for i, app in enumerate(seccion["apps"]):
            ruta_app = obtener_ruta_app(app["archivo"])
            existe = ruta_app.exists()

            estado = "Disponible" if existe else "No encontrado"
            estado_color = "#16a34a" if existe else "#dc2626"

            with columnas[i % 2]:
                st.markdown(
                    f"""
                    <div class="tat-app-card">
                        <div class="tat-app-title">
                            {app["icono"]} {app["titulo"]}
                        </div>
                        <div class="tat-app-description">
                            {app["descripcion"]}
                        </div>
                        <div style="
                            margin-top: 10px;
                            font-size: 0.76rem;
                            font-weight: 700;
                            color: {estado_color};
                        ">
                            {estado}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def mostrar_validacion_apps(apps_faltantes: dict) -> None:
    if not apps_faltantes:
        st.success("Todas las apps configuradas fueron encontradas correctamente.")
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
        """
        <div class="tat-home-title">
            Portal TAT ENAEX
        </div>
        <div class="tat-home-subtitle">
            Portal modular para preparar, consultar, analizar y gestionar información TAT.
        </div>
        """,
        unsafe_allow_html=True,
    )

    mostrar_resumen_portal()

    st.divider()

    mostrar_flujo_recomendado()

    st.divider()

    mostrar_catalogo_apps()

    st.divider()

    st.info(
        "Selecciona una app desde el menú lateral de navegación para comenzar."
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
