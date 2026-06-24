# ============================================================
# 06_CARGAR_ARCHIVO
# Carga del archivo TAT generado por 05_CALCULOS
# Guarda archivo activo en sesión como df_tat
# ============================================================

import base64
import re
import hashlib
import hmac
from pathlib import Path
from io import BytesIO
from urllib.parse import urlparse
from datetime import datetime

import requests
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="06_CARGAR_ARCHIVO",
    page_icon="📂",
    layout="wide",
)


# ============================================================
# RUTAS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# ============================================================
# ESTILOS MÍNIMOS
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #fafafa;
            padding: 10px;
            border-radius: 10px;
            border: 1px solid #eeeeee;
        }

        .page-title {
            text-align: center;
            font-size: 30px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 2px;
        }

        .page-subtitle {
            text-align: center;
            color: #6B7280;
            font-size: 15px;
            margin-bottom: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# COLUMNAS ESPERADAS
# ============================================================

COLUMNAS_REQUERIDAS_TAT = [
    "fecha_solicitud_final",
    "fecha_liberacion_final",
    "fecha_pedido_final",
    "fecha_facturacion_final",
    "fecha_recepcion_final",
    "tipo_oc",
    "origen",
    "sistema",
    "dias_tat_total",
    "umbral_tat_total",
    "performance_tat_total",
    "incumplimiento_tat",
    "rango_incumplimiento_tat",
]

COLUMNAS_RECOMENDADAS_TAT = [
    "Solicitud de pedido - ME5A",
    "Pedido - ME5A",
    "Documento de compras - ME80FN",
    "Estado del match",
    "monto",
    "dias_liberacion_solped",
    "dias_comprador",
    "dias_proveedor",
    "dias_logistica",
    "dias_incumplimiento_tat",
]


# ============================================================
# ESTADO DE SESIÓN
# ============================================================

def inicializar_estado():
    valores = {
        "archivos_tat": {},
        "archivo_tat_activo": None,
        "df_tat": None,
        "nombre_archivo_tat": None,
        "mensaje_carga_tat": None,
    }

    for clave, valor in valores.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor


# ============================================================
# LOGO
# ============================================================

def mostrar_logo():
    if not LOGO_PATH.exists():
        return

    logo_svg = LOGO_PATH.read_text(encoding="utf-8")
    logo_base64 = base64.b64encode(
        logo_svg.encode("utf-8")
    ).decode("utf-8")

    st.markdown(
        f"""
        <div style="
            width:100%;
            display:flex;
            justify-content:center;
            align-items:center;
            margin-top:5px;
            margin-bottom:10px;
        ">
            <img 
                src="data:image/svg+xml;base64,{logo_base64}" 
                style="width:210px; display:block;"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# SEGURIDAD SHAREPOINT
# ============================================================

def obtener_url_sharepoint_segura() -> str:
    try:
        url = st.secrets["sharepoint_tat"]["url"]
    except Exception:
        raise ValueError("No se encontró la URL de SharePoint en Secrets.")

    url = str(url).strip()

    if not url:
        raise ValueError("La URL de SharePoint está vacía en Secrets.")

    return url


def obtener_hash_clave_sharepoint() -> str:
    try:
        clave_hash = st.secrets["sharepoint_tat"]["access_key_sha256"]
    except Exception:
        raise ValueError("No se encontró la clave de SharePoint en Secrets.")

    clave_hash = str(clave_hash).strip()

    if not clave_hash:
        raise ValueError("La clave de SharePoint está vacía en Secrets.")

    return clave_hash


def calcular_sha256(texto: str) -> str:
    return hashlib.sha256(
        texto.encode("utf-8")
    ).hexdigest()


def validar_clave_sharepoint(clave_ingresada: str) -> bool:
    if not clave_ingresada:
        return False

    hash_esperado = obtener_hash_clave_sharepoint()
    hash_ingresado = calcular_sha256(clave_ingresada)

    return hmac.compare_digest(
        hash_ingresado,
        hash_esperado,
    )


# ============================================================
# FUNCIONES DE LECTURA
# ============================================================

def obtener_separador(separador_csv: str):
    separadores = {
        "Automático": None,
        "Punto y coma (;)": ";",
        "Coma (,)": ",",
        "Tabulación": "\t",
    }

    return separadores.get(separador_csv, None)


@st.cache_data(show_spinner=False)
def leer_archivo_cache(
    archivo_bytes: bytes,
    nombre_archivo: str,
    separador_csv: str,
) -> pd.DataFrame:

    extension = Path(nombre_archivo).suffix.lower()
    buffer = BytesIO(archivo_bytes)

    if extension == ".parquet":
        return pd.read_parquet(buffer)

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(buffer)

    if extension == ".csv":
        sep = obtener_separador(separador_csv)

        try:
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip",
            )

        except Exception:
            buffer.seek(0)

            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip",
            )

    raise ValueError("Formato no soportado. Usa CSV, XLSX, XLS o PARQUET.")


def preparar_url_descarga_sharepoint(url: str) -> str:
    url = url.strip()

    if not url:
        raise ValueError("La URL de SharePoint está vacía.")

    if "download=1" in url.lower():
        return url

    separador = "&" if "?" in url else "?"

    return f"{url}{separador}download=1"


def detectar_nombre_desde_url(url: str) -> str:
    try:
        path = urlparse(url).path
        nombre = Path(path).name

        if nombre.lower().endswith(".parquet"):
            return nombre

    except Exception:
        pass

    return "05_CALCULOS_SHAREPOINT_TAT.parquet"


def obtener_version_desde_nombre_archivo(nombre_archivo: str) -> dict:
    patron = r"05_CALCULOS_(\d{8})_(\d{6})_TAT"
    match = re.search(patron, nombre_archivo.upper())

    if not match:
        return {
            "version_detectada": False,
            "fecha_version": None,
            "texto_version": "No detectada",
        }

    fecha_txt = match.group(1)
    hora_txt = match.group(2)

    fecha_version = datetime.strptime(
        fecha_txt + hora_txt,
        "%Y%m%d%H%M%S",
    )

    return {
        "version_detectada": True,
        "fecha_version": fecha_version,
        "texto_version": fecha_version.strftime("%d-%m-%Y"),
    }


@st.cache_data(show_spinner=False)
def leer_parquet_sharepoint_cache(url: str):
    url_descarga = preparar_url_descarga_sharepoint(url)

    response = requests.get(
        url_descarga,
        allow_redirects=True,
        timeout=90,
    )

    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    contenido_inicio = response.content[:500].lower()

    if "text/html" in content_type or b"<html" in contenido_inicio:
        raise ValueError("SharePoint no devolvió el archivo Parquet.")

    if not (
        response.content[:4] == b"PAR1"
        and response.content[-4:] == b"PAR1"
    ):
        raise ValueError("El archivo descargado no parece ser Parquet válido.")

    df = pd.read_parquet(BytesIO(response.content))

    nombre_archivo = detectar_nombre_desde_url(response.url)
    version = obtener_version_desde_nombre_archivo(nombre_archivo)

    return df, nombre_archivo, version


# ============================================================
# FUNCIONES TAT
# ============================================================

def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def detectar_nombre_archivo_tat(nombre_archivo: str) -> bool:
    nombre = Path(nombre_archivo).stem.upper()

    return (
        nombre.startswith("05_CALCULOS_")
        and nombre.endswith("_TAT")
    )


def validar_columnas_tat(df: pd.DataFrame) -> dict:
    columnas = list(df.columns)

    faltantes_requeridas = [
        col for col in COLUMNAS_REQUERIDAS_TAT
        if col not in columnas
    ]

    faltantes_recomendadas = [
        col for col in COLUMNAS_RECOMENDADAS_TAT
        if col not in columnas
    ]

    return {
        "es_valido": len(faltantes_requeridas) == 0,
        "faltantes_requeridas": faltantes_requeridas,
        "faltantes_recomendadas": faltantes_recomendadas,
    }


def preparar_archivo_tat(df: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df)

    columnas_fecha = [
        "fecha_solicitud_final",
        "fecha_liberacion_final",
        "fecha_pedido_final",
        "fecha_facturacion_final",
        "fecha_recepcion_final",
    ]

    for col in columnas_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce",
            )

    columnas_booleanas = [
        "tiene_fechas_inconsistentes",
        "incumplimiento_tat",
    ]

    for col in columnas_booleanas:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    return df


def guardar_archivo_en_sesion(df: pd.DataFrame, nombre_archivo: str):
    df = preparar_archivo_tat(df)
    validacion = validar_columnas_tat(df)

    if not validacion["es_valido"]:
        raise ValueError(
            "El archivo no parece ser un resultado TAT válido. "
            f"Faltan columnas requeridas: {validacion['faltantes_requeridas']}"
        )

    st.session_state["archivos_tat"][nombre_archivo] = df
    st.session_state["archivo_tat_activo"] = nombre_archivo
    st.session_state["df_tat"] = df
    st.session_state["nombre_archivo_tat"] = nombre_archivo


def activar_archivo(nombre_archivo: str):
    df = st.session_state["archivos_tat"][nombre_archivo]

    st.session_state["archivo_tat_activo"] = nombre_archivo
    st.session_state["df_tat"] = df
    st.session_state["nombre_archivo_tat"] = nombre_archivo


def eliminar_archivo_de_sesion(nombre_archivo: str):
    st.session_state["archivos_tat"].pop(nombre_archivo, None)

    archivos_restantes = list(st.session_state["archivos_tat"].keys())

    if archivos_restantes:
        activar_archivo(archivos_restantes[0])
    else:
        st.session_state["archivo_tat_activo"] = None
        st.session_state["df_tat"] = None
        st.session_state["nombre_archivo_tat"] = None


def eliminar_todos_los_archivos():
    st.session_state["archivos_tat"] = {}
    st.session_state["archivo_tat_activo"] = None
    st.session_state["df_tat"] = None
    st.session_state["nombre_archivo_tat"] = None


def obtener_resumen_archivos() -> pd.DataFrame:
    resumen = []

    for nombre, df in st.session_state["archivos_tat"].items():
        validacion = validar_columnas_tat(df)
        version = obtener_version_desde_nombre_archivo(nombre)

        resumen.append(
            {
                "Archivo": nombre,
                "Versión detectada": version["texto_version"],
                "TAT válido": "Sí" if validacion["es_valido"] else "No",
                "Filas": df.shape[0],
                "Columnas": df.shape[1],
                "Activo": "Sí" if nombre == st.session_state.get("archivo_tat_activo") else "No",
            }
        )

    return pd.DataFrame(resumen)


def construir_tabla_columnas(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "N°": range(1, len(df.columns) + 1),
            "Columna": list(df.columns),
            "Tipo de dato": [str(df[col].dtype) for col in df.columns],
            "Valores no nulos": [int(df[col].notna().sum()) for col in df.columns],
            "Valores nulos": [int(df[col].isna().sum()) for col in df.columns],
        }
    )


def construir_resumen_tat(df: pd.DataFrame) -> pd.DataFrame:
    if "performance_tat_total" not in df.columns:
        return pd.DataFrame(
            columns=[
                "performance_tat_total",
                "Cantidad",
                "%",
            ]
        )

    conteo = (
        df["performance_tat_total"]
        .value_counts(dropna=False)
        .reset_index()
    )

    conteo.columns = [
        "performance_tat_total",
        "Cantidad",
    ]

    conteo["%"] = (
        conteo["Cantidad"] / len(df) * 100
    ).round(2) if len(df) else 0

    return conteo


def construir_resumen_rango_incumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    if "rango_incumplimiento_tat" not in df.columns:
        return pd.DataFrame(
            columns=[
                "rango_incumplimiento_tat",
                "Cantidad",
                "%",
            ]
        )

    conteo = (
        df["rango_incumplimiento_tat"]
        .value_counts(dropna=False)
        .reset_index()
    )

    conteo.columns = [
        "rango_incumplimiento_tat",
        "Cantidad",
    ]

    conteo["%"] = (
        conteo["Cantidad"] / len(df) * 100
    ).round(2) if len(df) else 0

    return conteo


def mostrar_estado_archivo(df: pd.DataFrame, nombre_archivo: str):
    version = obtener_version_desde_nombre_archivo(nombre_archivo)
    validacion = validar_columnas_tat(df)

    st.success("Conexión realizada correctamente. Archivo cargado.")

    st.caption(f"Archivo activo: **{nombre_archivo}**")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Versión", version["texto_version"])
    col2.metric("Filas", f"{df.shape[0]:,}")
    col3.metric("Columnas", f"{df.shape[1]:,}")
    col4.metric("TAT válido", "Sí" if validacion["es_valido"] else "No")


# ============================================================
# APP
# ============================================================

inicializar_estado()
mostrar_logo()

st.markdown(
    """
    <div class="page-title">06_CARGAR_ARCHIVO</div>
    <div class="page-subtitle">
        Carga el archivo TAT generado por 05_CALCULOS y déjalo disponible como df_tat.
    </div>
    """,
    unsafe_allow_html=True,
)

opcion_carga = st.radio(
    "Método de carga",
    options=[
        "Cargar archivo",
        "Conexión SharePoint",
    ],
    horizontal=True,
)


# ============================================================
# CARGA MANUAL
# ============================================================

if opcion_carga == "Cargar archivo":
    with st.expander("Opciones de archivo", expanded=True):
        separador_csv = st.selectbox(
            "Separador CSV",
            options=[
                "Automático",
                "Punto y coma (;)",
                "Coma (,)",
                "Tabulación",
            ],
            index=0,
        )

        archivos = st.file_uploader(
            "Selecciona uno o varios archivos TAT",
            type=["xlsx", "xls", "csv", "parquet"],
            accept_multiple_files=True,
            key="archivos_base_tat_uploader",
        )

    if archivos:
        errores = []

        with st.spinner("Cargando archivo..."):
            for archivo in archivos:
                try:
                    df = leer_archivo_cache(
                        archivo_bytes=archivo.getvalue(),
                        nombre_archivo=archivo.name,
                        separador_csv=separador_csv,
                    )

                    guardar_archivo_en_sesion(
                        df=df,
                        nombre_archivo=archivo.name,
                    )

                except Exception as error:
                    errores.append(f"{archivo.name}: {error}")

        if errores:
            st.error("Uno o más archivos no pudieron cargarse.")
            with st.expander("Ver errores", expanded=False):
                for error in errores:
                    st.write(error)
        else:
            st.session_state["mensaje_carga_tat"] = "Archivo cargado correctamente."


# ============================================================
# CONEXIÓN SHAREPOINT
# ============================================================

if opcion_carga == "Conexión SharePoint":
    with st.form("form_sharepoint_tat"):
        clave_sharepoint = st.text_input(
            "Clave de conexión",
            type="password",
            placeholder="Ingresa la clave autorizada",
        )

        conectar = st.form_submit_button(
            "Conectar y cargar archivo",
            use_container_width=True,
        )

    if conectar:
        try:
            if not validar_clave_sharepoint(clave_sharepoint):
                st.error("Clave incorrecta.")
            else:
                with st.spinner("Conectando con SharePoint..."):
                    url_sharepoint = obtener_url_sharepoint_segura()

                    df, nombre_archivo, version = leer_parquet_sharepoint_cache(
                        url_sharepoint
                    )

                    guardar_archivo_en_sesion(
                        df=df,
                        nombre_archivo=nombre_archivo,
                    )

                st.session_state["mensaje_carga_tat"] = (
                    "Conexión realizada correctamente. Archivo cargado."
                )

        except Exception:
            st.error(
                "No se pudo cargar el archivo desde SharePoint. "
                "Revisa la clave y la configuración en Secrets."
            )


# ============================================================
# SIN ARCHIVO
# ============================================================

if not st.session_state["archivos_tat"]:
    st.stop()


# ============================================================
# ARCHIVO ACTIVO
# ============================================================

st.divider()

archivos_disponibles = list(st.session_state["archivos_tat"].keys())

if st.session_state["archivo_tat_activo"] not in archivos_disponibles:
    activar_archivo(archivos_disponibles[0])

if len(archivos_disponibles) > 1:
    archivo_seleccionado = st.selectbox(
        "Archivo activo",
        options=archivos_disponibles,
        index=archivos_disponibles.index(
            st.session_state["archivo_tat_activo"]
        ),
    )

    activar_archivo(archivo_seleccionado)

df_tat = st.session_state["df_tat"]
nombre_archivo = st.session_state["nombre_archivo_tat"]

mostrar_estado_archivo(
    df=df_tat,
    nombre_archivo=nombre_archivo,
)


# ============================================================
# DETALLE COLAPSADO
# ============================================================

with st.expander("Resumen TAT", expanded=False):
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.markdown("#### Performance TAT")
        st.dataframe(
            construir_resumen_tat(df_tat),
            use_container_width=True,
            hide_index=True,
        )

    with col_res2:
        st.markdown("#### Rango incumplimiento TAT")
        st.dataframe(
            construir_resumen_rango_incumplimiento(df_tat),
            use_container_width=True,
            hide_index=True,
        )


with st.expander("Vista previa", expanded=False):
    max_filas = min(200, max(5, df_tat.shape[0]))

    filas_preview = st.slider(
        "Cantidad de filas a mostrar",
        min_value=5,
        max_value=max_filas,
        value=min(50, max_filas),
        step=5,
    )

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        "Pedido - ME5A",
        "Documento de compras - ME80FN",
        "tipo_oc",
        "origen",
        "sistema",
        "monto",
        "fecha_solicitud_final",
        "fecha_recepcion_final",
        "dias_tat_total",
        "umbral_tat_total",
        "performance_tat_total",
        "dias_incumplimiento_tat",
        "incumplimiento_tat",
        "rango_incumplimiento_tat",
    ]

    columnas_preferidas = [
        col for col in columnas_preferidas
        if col in df_tat.columns
    ]

    if columnas_preferidas:
        st.dataframe(
            df_tat[columnas_preferidas].head(filas_preview),
            use_container_width=True,
        )
    else:
        st.dataframe(
            df_tat.head(filas_preview),
            use_container_width=True,
        )


with st.expander("Columnas", expanded=False):
    st.dataframe(
        construir_tabla_columnas(df_tat),
        use_container_width=True,
        hide_index=True,
    )


with st.expander("Gestión", expanded=False):
    resumen_df = obtener_resumen_archivos()

    st.dataframe(
        resumen_df,
        use_container_width=True,
        hide_index=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        eliminar_activo = st.button(
            "Eliminar archivo activo",
            use_container_width=True,
        )

        if eliminar_activo:
            eliminar_archivo_de_sesion(nombre_archivo)
            st.rerun()

    with col2:
        eliminar_todos = st.button(
            "Eliminar todos los archivos",
            use_container_width=True,
        )

        if eliminar_todos:
            eliminar_todos_los_archivos()
            st.rerun()
