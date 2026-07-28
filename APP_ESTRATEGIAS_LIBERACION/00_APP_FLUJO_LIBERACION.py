# ============================================================
# 00_APP_FLUJO_LIBERACION
# Portal principal de Flujo de Liberación ENAEX
#
# Páginas del portal:
# 01 Cargar archivo
# 02 Simulador aleatorio
# 03 Modificación de liberadores
# ============================================================

from __future__ import annotations

import base64
from pathlib import Path
from textwrap import dedent

import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="Flujo de Liberación ENAEX",
    page_icon="🔄",
    layout="wide",
)


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_CANDIDATES = [
    PROJECT_DIR / "assets" / "logo.svg",
    BASE_DIR / "assets" / "logo.svg",
    PROJECT_DIR / "assets" / "logo.png",
    BASE_DIR / "assets" / "logo.png",
    PROJECT_DIR / "assets" / "logo.jpg",
    BASE_DIR / "assets" / "logo.jpg",
    PROJECT_DIR / "assets" / "logo.jpeg",
    BASE_DIR / "assets" / "logo.jpeg",
]


# ============================================================
# APLICACIONES DEL PORTAL
# ============================================================

APPS = [
    {
        "nombre": "01_CARGAR_ARCHIVO_FLUJO",
        "archivo": "01_CARGAR_ARCHIVO_FLUJO.py",
        "titulo": "01 Cargar archivo",
        "icono": "📤",
        "descripcion": (
            "Carga y valida el archivo Excel de flujo de liberación, "
            "dejándolo activo para la simulación y modificación."
        ),
    },
    {
        "nombre": "02_APP_SIMULADOR_ALEATORIO",
        "archivo": "02_APP_SIMULADOR_ALEATORIO.py",
        "titulo": "02 Simulación",
        "icono": "🎲",
        "descripcion": (
            "Genera casos aleatorios o consulta un flujo por CECO, "
            "tipo de documento y monto."
        ),
    },
    {
        "nombre": "03_APP_MODIFICACION_LIBERADORES",
        "archivo": "03_APP_MODIFICACION_LIBERADORES.py",
        "titulo": "03 Modificación de Liberadores",
        "icono": "✏️",
        "descripcion": (
            "Permite modificar liberadores, actualizar la base activa "
            "y descargar una nueva versión del Excel."
        ),
    },
]


# ============================================================
# ESTILOS
# ============================================================

def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .stMainBlockContainer,
            .block-container {
                padding-top: 6.75rem !important;
                padding-bottom: 2.5rem !important;
            }

            .portal-logo {
                width: 100%;
                min-height: 92px;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0.75rem 0 0.8rem 0;
                overflow: visible;
            }

            .portal-logo img {
                width: 220px;
                max-width: min(60vw, 220px);
                max-height: 90px;
                object-fit: contain;
                display: block;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UTILIDADES DE RUTAS
# ============================================================

def obtener_ruta_app(nombre_archivo: str) -> Path:
    """Obtiene la ruta de una aplicación ubicada junto al portal 00."""
    nombre = str(nombre_archivo).strip()

    candidatos = [BASE_DIR / nombre]

    if not nombre.lower().endswith(".py"):
        candidatos.append(BASE_DIR / f"{nombre}.py")

    for ruta in candidatos:
        if ruta.exists() and ruta.is_file():
            return ruta

    return candidatos[0]


def validar_apps_disponibles() -> dict[str, Path]:
    """Devuelve las aplicaciones requeridas que no existen."""
    faltantes: dict[str, Path] = {}

    for app in APPS:
        ruta = obtener_ruta_app(app["archivo"])
        if not ruta.exists():
            faltantes[app["nombre"]] = ruta

    return faltantes


# ============================================================
# LOGO PARA MENSAJES DE ERROR
# ============================================================

def mostrar_logo() -> None:
    logo_path = next(
        (ruta for ruta in LOGO_CANDIDATES if ruta.exists() and ruta.is_file()),
        None,
    )

    if logo_path is None:
        return

    try:
        extension = logo_path.suffix.lower()

        if extension == ".svg":
            contenido = logo_path.read_text(encoding="utf-8").encode("utf-8")
            mime = "image/svg+xml"
        else:
            contenido = logo_path.read_bytes()
            mime = "image/png" if extension == ".png" else "image/jpeg"

        logo_base64 = base64.b64encode(contenido).decode("utf-8")

        html_logo = dedent(
            f"""
            <div class="portal-logo">
                <img src="data:{mime};base64,{logo_base64}" alt="Logo ENAEX">
            </div>
            """
        ).strip()

        st.markdown(html_logo, unsafe_allow_html=True)

    except (OSError, UnicodeError) as error:
        st.warning(f"No fue posible leer el logo: {error}")


# ============================================================
# CONSTRUCCIÓN DE LAS TRES PÁGINAS
# ============================================================

def crear_pagina(app: dict) -> st.Page:
    return st.Page(
        obtener_ruta_app(app["archivo"]),
        title=app["titulo"],
        icon=app["icono"],
        url_path=app["nombre"].lower(),
    )


def construir_paginas() -> dict[str, list[st.Page]]:
    """Construye las tres páginas en la barra lateral, sin página de inicio."""
    return {
        "Flujo de liberación": [
            crear_pagina(app)
            for app in APPS
        ]
    }


# ============================================================
# VALIDACIÓN DE ARCHIVOS
# ============================================================

aplicar_estilos()

apps_faltantes = validar_apps_disponibles()

if apps_faltantes:
    mostrar_logo()
    st.error("No se encontraron una o más aplicaciones requeridas.")

    for nombre, ruta in apps_faltantes.items():
        st.write(f"**{nombre}:** `{ruta}`")

    st.info(
        "Los cuatro archivos deben estar dentro de la misma carpeta: "
        "`00_APP_FLUJO_LIBERACION.py`, `01_CARGAR_ARCHIVO_FLUJO.py`, "
        "`02_APP_SIMULADOR_ALEATORIO.py` y "
        "`03_APP_MODIFICACION_LIBERADORES.py`."
    )
    st.stop()


# ============================================================
# NAVEGACIÓN
# ============================================================

paginas = construir_paginas()

# Navegación lateral, igual que en el portal TAT original.
# No se agrega una página de Inicio.
pagina_seleccionada = st.navigation(
    paginas,
    position="sidebar",
)


# ============================================================
# EJECUTAR PÁGINA SELECCIONADA
# ============================================================

pagina_seleccionada.run()
