# ============================================================
# 00_APP_FLUJO_LIBERACION
# Portal principal de Flujo de Liberación ENAEX
#
# Formato maestro de la hoja Flujo:
# CECO | Planta | Desde | Hasta | TipoDoc |
# Lib1 | Lib2 | Lib3 | Lib4 | Lib5
#
# Páginas del portal:
# 01 Cargar archivo
# 02 Simulación
# 03 Modificación de liberadores
# 04 Diccionarios
# 05 Búsqueda ejecutiva
# ============================================================

from __future__ import annotations

import base64
from pathlib import Path
from textwrap import dedent
from typing import Any

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
        "grupo": "Operación",
        "nombre": "01_CARGAR_ARCHIVO_FLUJO",
        "archivo": "01_CARGAR_ARCHIVO_FLUJO.py",
        "titulo": "01 Cargar archivo",
        "icono": "📤",
        "descripcion": (
            "Carga, normaliza y valida el Excel activo usando el formato "
            "simplificado de flujo de liberación."
        ),
    },
    {
        "grupo": "Operación",
        "nombre": "02_APP_SIMULADOR_ALEATORIO",
        "archivo": "02_APP_SIMULADOR_ALEATORIO.py",
        "titulo": "02 Simulación",
        "icono": "🎲",
        "descripcion": (
            "Genera casos aleatorios o busca un flujo por CECO, "
            "tipo de documento y monto."
        ),
    },
    {
        "grupo": "Administración de datos",
        "nombre": "03_APP_MODIFICACION_LIBERADORES",
        "archivo": "03_APP_MODIFICACION_LIBERADORES.py",
        "titulo": "03 Modificación de Liberadores",
        "icono": "✏️",
        "descripcion": (
            "Permite agregar, mover, reemplazar o eliminar liberadores, "
            "realizar reemplazos globales y exportar una nueva versión."
        ),
    },
    {
        "grupo": "Administración de datos",
        "nombre": "04_APP_DICCIONARIOS",
        "archivo": "04_APP_DICCIONARIOS.py",
        "titulo": "04 Diccionarios",
        "icono": "📚",
        "descripcion": (
            "Consulta los catálogos de CECO, usuarios y rangos "
            "contenidos en el Excel activo."
        ),
    },
    {
        "grupo": "Operación",
        "nombre": "05_BUSQUEDA_EJECUTIVA",
        "archivo": "05_BUSQUEDA_EJECUTIVA.py",
        "titulo": "05 Búsqueda Ejecutiva",
        "icono": "🔎",
        "descripcion": (
            "Consulta rápida de un flujo por CECO, tipo de documento "
            "y monto, sin generación aleatoria."
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

            .portal-error-title {
                color: #17365D;
                font-size: 1.35rem;
                font-weight: 850;
                margin-bottom: .35rem;
            }

            .portal-file-card {
                border: 1px solid #D0D5DD;
                border-radius: 12px;
                padding: 11px 13px;
                background: #F8FAFC;
                margin: 6px 0;
            }

            .portal-file-name {
                color: #17365D;
                font-weight: 800;
            }

            .portal-file-path {
                color: #64748B;
                font-size: .85rem;
                overflow-wrap: anywhere;
                margin-top: 3px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UTILIDADES DE RUTAS
# ============================================================

def obtener_ruta_app(nombre_archivo: str) -> Path:
    """Obtiene la ruta de una aplicación ubicada junto al portal."""
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

        if not ruta.exists() or not ruta.is_file():
            faltantes[app["nombre"]] = ruta

    return faltantes


# ============================================================
# LOGO PARA MENSAJES DE ERROR
# ============================================================

def mostrar_logo() -> None:
    logo_path = next(
        (
            ruta
            for ruta in LOGO_CANDIDATES
            if ruta.exists() and ruta.is_file()
        ),
        None,
    )

    if logo_path is None:
        return

    try:
        extension = logo_path.suffix.lower()

        if extension == ".svg":
            contenido = logo_path.read_text(
                encoding="utf-8"
            ).encode("utf-8")
            mime = "image/svg+xml"
        else:
            contenido = logo_path.read_bytes()
            mime = (
                "image/png"
                if extension == ".png"
                else "image/jpeg"
            )

        logo_base64 = base64.b64encode(
            contenido
        ).decode("utf-8")

        html_logo = dedent(
            f"""
            <div class="portal-logo">
                <img
                    src="data:{mime};base64,{logo_base64}"
                    alt="Logo ENAEX"
                >
            </div>
            """
        ).strip()

        st.markdown(
            html_logo,
            unsafe_allow_html=True,
        )

    except (OSError, UnicodeError) as error:
        st.warning(f"No fue posible leer el logo: {error}")


# ============================================================
# CONSTRUCCIÓN DE PÁGINAS
# ============================================================

def crear_pagina(app: dict[str, Any]) -> st.Page:
    """Construye una página navegable de Streamlit."""
    return st.Page(
        obtener_ruta_app(app["archivo"]),
        title=app["titulo"],
        icon=app["icono"],
        url_path=app["nombre"].lower(),
    )


def construir_paginas() -> dict[str, list[st.Page]]:
    """
    Organiza las páginas en grupos intuitivos.

    No se agrega una página de inicio; la primera página disponible
    se abre automáticamente.
    """
    grupos: dict[str, list[st.Page]] = {
        "Operación": [],
        "Administración de datos": [],
    }

    for app in APPS:
        grupos.setdefault(app["grupo"], []).append(
            crear_pagina(app)
        )

    return {
        nombre_grupo: paginas
        for nombre_grupo, paginas in grupos.items()
        if paginas
    }


# ============================================================
# VALIDACIÓN DE ARCHIVOS
# ============================================================

def mostrar_error_archivos(
    apps_faltantes: dict[str, Path],
) -> None:
    """Muestra un diagnóstico claro cuando falta una aplicación."""
    mostrar_logo()

    st.markdown(
        '<div class="portal-error-title">'
        'No se encontraron una o más aplicaciones requeridas.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.error(
        "Revisa que todos los archivos estén guardados en la misma "
        "carpeta que `00_APP_FLUJO_LIBERACION.py`."
    )

    for nombre, ruta in apps_faltantes.items():
        st.markdown(
            dedent(
                f"""
                <div class="portal-file-card">
                    <div class="portal-file-name">{nombre}</div>
                    <div class="portal-file-path">{ruta}</div>
                </div>
                """
            ).strip(),
            unsafe_allow_html=True,
        )

    st.info(
        "Archivos requeridos: "
        "`00_APP_FLUJO_LIBERACION.py`, "
        "`01_CARGAR_ARCHIVO_FLUJO.py`, "
        "`02_APP_SIMULADOR_ALEATORIO.py`, "
        "`03_APP_MODIFICACION_LIBERADORES.py`, "
        "`04_APP_DICCIONARIOS.py` y "
        "`05_BUSQUEDA_EJECUTIVA.py`."
    )


# ============================================================
# INICIALIZACIÓN DEL PORTAL
# ============================================================

aplicar_estilos()

apps_faltantes = validar_apps_disponibles()

if apps_faltantes:
    mostrar_error_archivos(apps_faltantes)
    st.stop()


# ============================================================
# NAVEGACIÓN
# ============================================================

paginas = construir_paginas()

pagina_seleccionada = st.navigation(
    paginas,
    position="sidebar",
)


# ============================================================
# EJECUTAR PÁGINA SELECCIONADA
# ============================================================

pagina_seleccionada.run()
