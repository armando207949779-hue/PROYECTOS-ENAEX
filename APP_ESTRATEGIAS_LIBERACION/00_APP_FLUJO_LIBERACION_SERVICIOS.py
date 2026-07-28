# ============================================================
# 00_APP_FLUJO_LIBERACION_SERVICIOS
# Portal principal de Flujo de Liberación de Servicios
#
# Orden de módulos:
# 01 Cargar Archivo
# 02 Simulador Aleatorio
# ============================================================

from __future__ import annotations

import base64
from pathlib import Path
from textwrap import dedent

import streamlit as st

st.set_page_config(
    page_title="Flujo de Liberación ENAEX",
    page_icon="🔄",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_CANDIDATES = [
    PROJECT_DIR / "assets" / "logo.svg", BASE_DIR / "assets" / "logo.svg",
    PROJECT_DIR / "assets" / "logo.png", BASE_DIR / "assets" / "logo.png",
    PROJECT_DIR / "assets" / "logo.jpg", BASE_DIR / "assets" / "logo.jpg",
]

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"

APP_SECTIONS = [
    {
        "grupo": "01 Carga de datos",
        "descripcion": "Carga, validación y activación del archivo Excel de flujo de liberación.",
        "apps": [
            {
                "nombre": "01_CARGAR_ARCHIVO_FLUJO",
                "archivo": "01_CARGAR_ARCHIVO_FLUJO.py",
                "titulo": "01 Cargar Archivo",
                "icono": "📤",
                "descripcion": "Carga el Excel y lo deja disponible para los demás módulos.",
            }
        ],
    },
    {
        "grupo": "02 Simulación",
        "descripcion": "Consulta y simulación de rutas de liberación usando el archivo activo.",
        "apps": [
            {
                "nombre": "02_APP_SIMULADOR_ALEATORIO",
                "archivo": "02_APP_SIMULADOR_ALEATORIO.py",
                "titulo": "02 Simulador Aleatorio",
                "icono": "🎲",
                "descripcion": "Genera casos aleatorios o busca un flujo por CECO, tipo y monto.",
            }
        ],
    },
]
APPS = [app for section in APP_SECTIONS for app in section["apps"]]


def obtener_ruta_app(nombre_archivo: str) -> Path:
    nombre = str(nombre_archivo).strip()
    candidatos = [BASE_DIR / nombre]
    if not nombre.endswith(".py"):
        candidatos.append(BASE_DIR / f"{nombre}.py")
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    return candidatos[0]


def validar_apps_disponibles() -> dict[str, Path]:
    return {
        app["nombre"]: obtener_ruta_app(app["archivo"])
        for app in APPS
        if not obtener_ruta_app(app["archivo"]).exists()
    }


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .stMainBlockContainer, .block-container {
                padding-top: 6.5rem !important; padding-bottom: 2.5rem;
            }
            .portal-logo { width:100%; min-height:90px; display:flex; justify-content:center;
                align-items:center; margin:.6rem 0 12px; overflow:visible; }
            .portal-logo img { width:220px; max-width:min(60vw,220px); max-height:88px;
                object-fit:contain; display:block; }
            .portal-title { text-align:center; color:#17365D; font-size:2.15rem;
                font-weight:800; margin:.2rem 0; }
            .portal-subtitle { text-align:center; color:#64748B; font-size:1rem;
                margin-bottom:1.25rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_logo() -> None:
    path = next((p for p in LOGO_CANDIDATES if p.exists() and p.is_file()), None)
    if path is None:
        return
    try:
        if path.suffix.lower() == ".svg":
            raw, mime = path.read_text(encoding="utf-8").encode("utf-8"), "image/svg+xml"
        else:
            raw = path.read_bytes()
            mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        encoded = base64.b64encode(raw).decode("utf-8")
        st.markdown(
            dedent(f'<div class="portal-logo"><img src="data:{mime};base64,{encoded}" alt="Logo"></div>').strip(),
            unsafe_allow_html=True,
        )
    except (OSError, UnicodeError):
        st.warning(f"No fue posible leer el logo: {path.name}")


def mostrar_estado_archivo_activo() -> None:
    data = st.session_state.get(SESSION_DATA_KEY)
    if data is None:
        st.info("No hay archivo activo. Comienza en **01 Cargar Archivo**.")
        return
    flow = data["flujo"]
    name = st.session_state.get(SESSION_FILE_KEY, "Archivo activo")
    st.success(
        f"Archivo activo: **{name}** · **{len(flow):,} filas** · "
        f"**{flow['CECO'].nunique():,} CECO**".replace(",", ".")
    )


def mostrar_apps_disponibles() -> None:
    st.subheader("Módulos disponibles")
    for section in APP_SECTIONS:
        st.markdown(f"#### {section['grupo']}")
        st.caption(section["descripcion"])
        columns = st.columns(2)
        for index, app in enumerate(section["apps"]):
            exists = obtener_ruta_app(app["archivo"]).exists()
            with columns[index % 2]:
                st.info(
                    f"**{app['icono']} {app['titulo']}**\n\n"
                    f"{app['descripcion']}\n\n"
                    f"Estado: **{'Disponible' if exists else 'No encontrado'}**"
                )


def pagina_inicio() -> None:
    aplicar_estilos()
    mostrar_logo()
    st.markdown('<div class="portal-title">Flujo de Liberación ENAEX</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="portal-subtitle">Portal modular para cargar la base y simular flujos de liberación.</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    mostrar_estado_archivo_activo()
    st.markdown("---")
    mostrar_apps_disponibles()
    st.markdown("---")
    st.success("Selecciona un módulo desde el menú de navegación.")


def crear_pagina_app(app: dict):
    return st.Page(
        obtener_ruta_app(app["archivo"]),
        title=app["titulo"],
        icon=app["icono"],
        url_path=app["nombre"].lower(),
    )


def construir_paginas_por_seccion() -> dict:
    pages = {
        "Inicio": [
            st.Page(pagina_inicio, title="Inicio", icon="🏠", url_path="inicio")
        ]
    }
    for section in APP_SECTIONS:
        pages[section["grupo"]] = [crear_pagina_app(app) for app in section["apps"]]
    return pages


missing = validar_apps_disponibles()
if missing:
    aplicar_estilos()
    mostrar_logo()
    st.error("No se encontraron una o más aplicaciones requeridas.")
    for name, path in missing.items():
        st.write(f"**{name}:** `{path}`")
    st.stop()

pagina = st.navigation(construir_paginas_por_seccion())
pagina.run()
