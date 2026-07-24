# ============================================================
# 05_APP_LIMPIEZA_ARCHIVOS.py
# Preparación, versionado y descarga ZIP de archivos del dashboard
# ============================================================

from __future__ import annotations

from datetime import date, datetime
from io import BytesIO
from pathlib import Path
import base64
import re
import zipfile

import pandas as pd
import streamlit as st


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="05_APP_LIMPIEZA_ARCHIVOS",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"

EXTENSIONES_PERMITIDAS = ["csv", "xlsx", "xls", "parquet"]

ARCHIVOS_ESPERADOS: list[str] = [
    "01_BD_Moneda_Cambio.xlsx",
    "02_ME2N_Ordenes.csv",
    "03_Gasto_Contratos.csv",
    "04_Centros.csv",
    "05_BBDD_X_Categoria_BD.csv",
    "06_BD_Catalogo_Categorias.csv",
    "07_BD_Plan_Ahorro_Gestores.csv",
    "08_BD_Registro_Contratos.csv",
    "09_BD_Hitos.csv",
    "10_BD_Categorias.csv",
    "11_ME3N.csv",
]

SESSION_DEFAULTS = {
    "limpieza_zip_bytes": None,
    "limpieza_zip_nombre": None,
    "limpieza_resumen": pd.DataFrame(),
    "limpieza_errores": [],
    "limpieza_completada": False,
}

for clave, valor in SESSION_DEFAULTS.items():
    if clave not in st.session_state:
        st.session_state[clave] = valor


# ============================================================
# Estilo visual
# ============================================================

def aplicar_estilo() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 1500px;
                padding-top: 2.2rem;
                padding-bottom: 3rem;
            }

            h1, h2, h3 {
                letter-spacing: -0.02em;
            }

            .hero-subtitle {
                text-align: center;
                color: #4B5563;
                font-size: 1rem;
                margin-top: 0.35rem;
                margin-bottom: 1.5rem;
            }
div[data-testid="stFileUploader"] {
                border: 1px dashed #CBD5E1;
                border-radius: 14px;
                padding: 10px;
                background: #FFFFFF;
            }

            div[data-testid="stMetric"] {
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 14px;
                padding: 14px 16px;
                box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            }

            div[data-testid="stExpander"] {
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                overflow: hidden;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_logo_centrado() -> None:
    if not LOGO_PATH.exists():
        return

    try:
        logo_svg = LOGO_PATH.read_text(encoding="utf-8")
        logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")

        st.markdown(
            f"""
            <div style="
                display:flex;
                justify-content:center;
                align-items:center;
                margin:4px 0 14px 0;
            ">
                <img
                    src="data:image/svg+xml;base64,{logo_base64}"
                    style="width:230px;display:block;"
                >
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass


def mostrar_encabezado() -> None:
    mostrar_logo_centrado()

    st.markdown(
        """
        <h1 style="text-align:center;margin-bottom:0;">
            05_LIMPIEZA_ARCHIVOS
        </h1>
        <p class="hero-subtitle">
            Versiona los archivos del dashboard con fecha y descarga una carpeta ZIP lista para respaldo.
        </p>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Funciones auxiliares
# ============================================================

def limpiar_estado() -> None:
    st.session_state["limpieza_zip_bytes"] = None
    st.session_state["limpieza_zip_nombre"] = None
    st.session_state["limpieza_resumen"] = pd.DataFrame()
    st.session_state["limpieza_errores"] = []
    st.session_state["limpieza_completada"] = False


def fecha_compacta(fecha_seleccionada: date) -> str:
    return fecha_seleccionada.strftime("%Y%m%d")


def fecha_legible(fecha_seleccionada: date) -> str:
    return fecha_seleccionada.strftime("%d-%m-%Y")


def normalizar_nombre(nombre: str) -> str:
    """
    Normaliza el nombre solo para comparación:
    - elimina rutas
    - pasa a minúsculas
    - reemplaza espacios por guion bajo
    - elimina una fecha final previa en formato YYYYMMDD o DD-MM-YYYY
    """
    nombre_archivo = Path(str(nombre)).name.strip()
    stem = Path(nombre_archivo).stem
    extension = Path(nombre_archivo).suffix.lower()

    stem = re.sub(r"[\s\-]+", "_", stem)
    stem = re.sub(r"_(\d{8})$", "", stem)
    stem = re.sub(r"_(\d{2}[-_]\d{2}[-_]\d{4})$", "", stem)

    return f"{stem.lower()}{extension}"


def separar_nombre_extension(nombre: str) -> tuple[str, str]:
    ruta = Path(Path(nombre).name)
    return ruta.stem, ruta.suffix


def quitar_fecha_version_previa(stem: str) -> str:
    """
    Evita acumular fechas si se vuelve a procesar un archivo ya versionado.
    Ejemplos:
    archivo_20260724 -> archivo
    archivo_24-07-2026 -> archivo
    """
    stem = re.sub(r"[_\-](\d{8})$", "", stem)
    stem = re.sub(r"[_\-](\d{2}[-_]\d{2}[-_]\d{4})$", "", stem)
    return stem.rstrip("_-")


def construir_nombre_versionado(
    nombre_original: str,
    fecha_seleccionada: date,
) -> str:
    stem, extension = separar_nombre_extension(nombre_original)
    stem_limpio = quitar_fecha_version_previa(stem)
    return f"{stem_limpio}_{fecha_compacta(fecha_seleccionada)}{extension.lower()}"


def construir_mapa_subidos(archivos_subidos) -> dict[str, object]:
    mapa: dict[str, object] = {}

    for archivo in archivos_subidos or []:
        clave = normalizar_nombre(archivo.name)

        # Conserva el primer archivo si hubiera nombres normalizados duplicados.
        if clave not in mapa:
            mapa[clave] = archivo

    return mapa


def obtener_archivo_esperado(
    nombre_esperado: str,
    mapa_subidos: dict[str, object],
):
    return mapa_subidos.get(normalizar_nombre(nombre_esperado))


def validar_archivos(
    archivos_subidos,
    fecha_seleccionada: date,
) -> pd.DataFrame:
    mapa = construir_mapa_subidos(archivos_subidos)
    registros: list[dict[str, object]] = []

    for orden, nombre_esperado in enumerate(ARCHIVOS_ESPERADOS, start=1):
        archivo = obtener_archivo_esperado(nombre_esperado, mapa)
        encontrado = archivo is not None

        nombre_versionado = (
            construir_nombre_versionado(nombre_esperado, fecha_seleccionada)
            if encontrado
            else ""
        )

        registros.append(
            {
                "Orden": orden,
                "Archivo esperado": nombre_esperado,
                "Estado": "Encontrado" if encontrado else "Faltante",
                "Nombre versionado": nombre_versionado,
                "Peso (KB)": round(archivo.size / 1024, 2) if encontrado else None,
            }
        )

    nombres_esperados_normalizados = {
        normalizar_nombre(nombre)
        for nombre in ARCHIVOS_ESPERADOS
    }

    for archivo in archivos_subidos or []:
        if normalizar_nombre(archivo.name) not in nombres_esperados_normalizados:
            registros.append(
                {
                    "Orden": None,
                    "Archivo esperado": archivo.name,
                    "Estado": "No reconocido",
                    "Nombre versionado": construir_nombre_versionado(
                        archivo.name,
                        fecha_seleccionada,
                    ),
                    "Peso (KB)": round(archivo.size / 1024, 2),
                }
            )

    return pd.DataFrame(registros)


def construir_zip(
    archivos_subidos,
    fecha_seleccionada: date,
) -> tuple[bytes, str, pd.DataFrame, list[str]]:
    mapa = construir_mapa_subidos(archivos_subidos)
    fecha_nombre = fecha_compacta(fecha_seleccionada)

    nombre_carpeta = f"BBDD_ARCHIVOS_DASHBOARD_CONTRATOS_{fecha_nombre}"
    nombre_zip = f"{nombre_carpeta}.zip"

    buffer_zip = BytesIO()
    resumen: list[dict[str, object]] = []
    errores: list[str] = []
    procesados_normalizados: set[str] = set()

    with zipfile.ZipFile(
        buffer_zip,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archivo_zip:

        for orden, nombre_esperado in enumerate(ARCHIVOS_ESPERADOS, start=1):
            archivo = obtener_archivo_esperado(nombre_esperado, mapa)

            if archivo is None:
                continue

            try:
                contenido = archivo.getvalue()
                nombre_versionado = construir_nombre_versionado(
                    nombre_esperado,
                    fecha_seleccionada,
                )
                ruta_interna = f"{nombre_carpeta}/{nombre_versionado}"

                archivo_zip.writestr(ruta_interna, contenido)
                procesados_normalizados.add(normalizar_nombre(archivo.name))

                resumen.append(
                    {
                        "Orden": orden,
                        "Archivo original": archivo.name,
                        "Archivo ZIP": nombre_versionado,
                        "Estado": "Incluido",
                        "Peso (KB)": round(len(contenido) / 1024, 2),
                    }
                )
            except Exception as exc:
                errores.append(f"{archivo.name}: {exc}")

        # Archivo informativo dentro del ZIP.
        contenido_manifest = [
            "PAQUETE DE ARCHIVOS DEL DASHBOARD DE CONTRATOS",
            f"Fecha de versión: {fecha_legible(fecha_seleccionada)}",
            f"Fecha de generación: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
            "",
            "Archivos incluidos:",
        ]

        for fila in resumen:
            contenido_manifest.append(
                f"- {fila['Archivo ZIP']} ({fila['Peso (KB)']:.2f} KB)"
            )

        if errores:
            contenido_manifest.extend(["", "Errores:"])
            contenido_manifest.extend(f"- {error}" for error in errores)

        archivo_zip.writestr(
            f"{nombre_carpeta}/LEEME.txt",
            "\n".join(contenido_manifest).encode("utf-8"),
        )

    buffer_zip.seek(0)

    return (
        buffer_zip.getvalue(),
        nombre_zip,
        pd.DataFrame(resumen),
        errores,
    )


def mostrar_metricas_validacion(df_validacion: pd.DataFrame) -> None:
    esperados = len(ARCHIVOS_ESPERADOS)
    encontrados = int((df_validacion["Estado"] == "Encontrado").sum())
    faltantes = esperados - encontrados
    adicionales = int((df_validacion["Estado"] == "No reconocido").sum())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Archivos esperados", esperados)
    col2.metric("Encontrados", encontrados)
    col3.metric("Faltantes", faltantes)
    col4.metric("Adicionales", adicionales)


def mostrar_tabla_validacion(df_validacion: pd.DataFrame) -> None:
    tabla = df_validacion.copy()

    if "Peso (KB)" in tabla.columns:
        tabla["Peso (KB)"] = tabla["Peso (KB)"].map(
            lambda valor: f"{valor:,.2f}" if pd.notna(valor) else ""
        )

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Orden": st.column_config.NumberColumn(
                "N°",
                format="%d",
                width="small",
            ),
            "Archivo esperado": st.column_config.TextColumn(
                "Archivo",
                width="large",
            ),
            "Estado": st.column_config.TextColumn(
                "Estado",
                width="small",
            ),
            "Nombre versionado": st.column_config.TextColumn(
                "Nombre con fecha",
                width="large",
            ),
            "Peso (KB)": st.column_config.TextColumn(
                "Peso (KB)",
                width="small",
            ),
        },
    )


# ============================================================
# App principal
# ============================================================

aplicar_estilo()
mostrar_encabezado()

col_fecha, col_nombre = st.columns([1, 2])

with col_fecha:
    fecha_version = st.date_input(
        "Fecha de versión",
        value=date.today(),
        format="DD/MM/YYYY",
    )

with col_nombre:
    ejemplo_zip = (
        f"BBDD_ARCHIVOS_DASHBOARD_CONTRATOS_"
        f"{fecha_compacta(fecha_version)}.zip"
    )
    st.text_input(
        "Archivo de salida",
        value=ejemplo_zip,
        disabled=True,
    )

archivos_subidos = st.file_uploader(
    "Subir archivos del dashboard",
    type=EXTENSIONES_PERMITIDAS,
    accept_multiple_files=True,
    help="Selecciona los archivos CSV, Excel o Parquet que deseas versionar.",
)

col_generar, col_limpiar = st.columns([3, 1])

with col_generar:
    generar_zip = st.button(
        "Generar paquete ZIP",
        type="primary",
        use_container_width=True,
        disabled=not archivos_subidos,
    )

with col_limpiar:
    limpiar = st.button(
        "Limpiar",
        use_container_width=True,
    )

if limpiar:
    limpiar_estado()
    st.rerun()


if archivos_subidos:
    df_validacion = validar_archivos(
        archivos_subidos=archivos_subidos,
        fecha_seleccionada=fecha_version,
    )

    st.divider()
    st.subheader("Validación")

    mostrar_metricas_validacion(df_validacion)

    faltantes = df_validacion[df_validacion["Estado"] == "Faltante"]
    adicionales = df_validacion[df_validacion["Estado"] == "No reconocido"]

    if faltantes.empty:
        st.success("Todos los archivos esperados fueron encontrados.")
    else:
        st.warning(
            f"Faltan {len(faltantes)} archivo(s). "
            "El ZIP se puede generar con los archivos disponibles."
        )

    if not adicionales.empty:
        st.info(
            f"Se detectaron {len(adicionales)} archivo(s) no reconocido(s). "
            "No serán incluidos en el ZIP."
        )

    with st.expander("Ver validación archivo por archivo", expanded=True):
        mostrar_tabla_validacion(df_validacion)


if generar_zip and archivos_subidos:
    try:
        zip_bytes, zip_nombre, df_resumen, errores = construir_zip(
            archivos_subidos=archivos_subidos,
            fecha_seleccionada=fecha_version,
        )

        if df_resumen.empty:
            st.error(
                "No se pudo incluir ningún archivo en el ZIP. "
                "Verifica los nombres de los archivos seleccionados."
            )
        else:
            st.session_state["limpieza_zip_bytes"] = zip_bytes
            st.session_state["limpieza_zip_nombre"] = zip_nombre
            st.session_state["limpieza_resumen"] = df_resumen
            st.session_state["limpieza_errores"] = errores
            st.session_state["limpieza_completada"] = True

            st.success(
                f"Paquete generado correctamente con {len(df_resumen)} archivo(s)."
            )

    except Exception as exc:
        st.error(f"No se pudo generar el paquete ZIP: {exc}")


if st.session_state["limpieza_completada"]:
    st.divider()
    st.subheader("Descarga")

    zip_bytes = st.session_state["limpieza_zip_bytes"]
    zip_nombre = st.session_state["limpieza_zip_nombre"]
    df_resumen = st.session_state["limpieza_resumen"]
    errores = st.session_state["limpieza_errores"]

    total_archivos = len(df_resumen)
    peso_zip_mb = len(zip_bytes) / 1024**2 if zip_bytes else 0
    total_original_mb = (
        df_resumen["Peso (KB)"].fillna(0).sum() / 1024
        if not df_resumen.empty
        else 0
    )

    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("Archivos incluidos", total_archivos)
    col_r2.metric("Peso original", f"{total_original_mb:.2f} MB")
    col_r3.metric("Peso del ZIP", f"{peso_zip_mb:.2f} MB")

    st.download_button(
        label="Descargar carpeta ZIP",
        data=zip_bytes,
        file_name=zip_nombre,
        mime="application/zip",
        type="primary",
        use_container_width=True,
    )

    with st.expander("Ver contenido del paquete", expanded=False):
        tabla_resumen = df_resumen.copy()
        tabla_resumen["Peso (KB)"] = tabla_resumen["Peso (KB)"].map(
            lambda valor: f"{valor:,.2f}"
        )

        st.dataframe(
            tabla_resumen,
            use_container_width=True,
            hide_index=True,
        )

    if errores:
        with st.expander("Ver errores", expanded=True):
            for error in errores:
                st.error(error)

else:
    st.info(
        "Después de generar el paquete aparecerá aquí el botón de descarga."
    )
