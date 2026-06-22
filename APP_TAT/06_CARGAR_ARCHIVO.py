# ============================================================
# 06_CARGAR_ARCHIVO
# Carga archivo TAT generado por 05_CALCULOS
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
    valores_iniciales = {
        "archivos_tat": {},
        "archivo_tat_activo": None,
        "df_tat": None,
        "nombre_archivo_tat": None,
    }

    for clave, valor in valores_iniciales.items():
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
            margin-top:4px;
            margin-bottom:8px;
        ">
            <img 
                src="data:image/svg+xml;base64,{logo_base64}" 
                style="width:200px;"
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

    raise ValueError("Formato no soportado.")


def preparar_url_descarga_sharepoint(url: str) -> str:
    url = url.strip()

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
        "texto_version": fecha_version.strftime("%d-%m-%Y %H:%M:%S"),
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
    inicio = response.content[:500].lower()

    if "text/html" in content_type or b"<html" in inicio:
        raise ValueError("SharePoint no devolvió un archivo Parquet.")

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


def construir_resumen_archivos() -> pd.DataFrame:
    resumen = []

    for nombre, df in st.session_state["archivos_tat"].items():
        validacion = validar_columnas_tat(df)
        version = obtener_version_desde_nombre_archivo(nombre)

        resumen.append(
            {
                "Archivo": nombre,
                "Versión": version["texto_version"],
                "Filas": df.shape[0],
                "Columnas": df.shape[1],
                "TAT válido": "Sí" if validacion["es_valido"] else "No",
                "Activo": "Sí" if nombre == st.session_state["archivo_tat_activo"] else "No",
            }
        )

    return pd.DataFrame(resumen)


# ============================================================
# APP
# ============================================================

inicializar_estado()
mostrar_logo()

st.markdown(
    """
    <h2 style="text-align:center; margin-bottom:0;">
        06_CARGAR_ARCHIVO
    </h2>
    <p style="text-align:center; color:#6B7280; margin-top:4px;">
        Carga el archivo TAT y déjalo disponible como df_tat.
    </p>
    """,
    unsafe_allow_html=True,
)

st.divider()


# ============================================================
# MÉTODO DE CARGA
# ============================================================

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
        "Archivo TAT",
        type=["xlsx", "xls", "csv", "parquet"],
        accept_multiple_files=True,
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
                    errores.append(
                        f"{archivo.name}: {error}"
                    )

        if errores:
            st.error("Uno o más archivos no pudieron cargarse.")
            with st.expander("Ver errores"):
                for error in errores:
                    st.write(error)
        else:
            version = obtener_version_desde_nombre_archivo(
                st.session_state["nombre_archivo_tat"]
            )

            st.success("Archivo cargado correctamente.")

            if version["version_detectada"]:
                st.caption(
                    f"Última versión detectada: {version['texto_version']}"
                )


# ============================================================
# CONEXIÓN SHAREPOINT
# ============================================================

if opcion_carga == "Conexión SharePoint":
    clave_sharepoint = st.text_input(
        "Clave de conexión",
        type="password",
        placeholder="Ingresa la clave",
    )

    conectar = st.button(
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

                st.success("Archivo cargado correctamente desde SharePoint.")

                if version["version_detectada"]:
                    st.caption(
                        f"Última versión detectada: {version['texto_version']}"
                    )
                else:
                    st.caption("Versión no detectada desde el nombre del archivo.")

        except Exception:
            st.error(
                "No se pudo completar la conexión. "
                "Revisa la clave y la configuración en Secrets."
            )


# ============================================================
# SIN ARCHIVO CARGADO
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
validacion = validar_columnas_tat(df_tat)
version = obtener_version_desde_nombre_archivo(nombre_archivo)

st.markdown("### Archivo activo")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Archivo", nombre_archivo)
col2.metric("Versión", version["texto_version"])
col3.metric("Filas", f"{df_tat.shape[0]:,}")
col4.metric("Columnas", f"{df_tat.shape[1]:,}")

if validacion["es_valido"]:
    st.success("Archivo TAT válido y disponible como df_tat.")
else:
    st.error("Archivo TAT no válido.")


# ============================================================
# DETALLE SIMPLE
# ============================================================

tab_resumen, tab_preview, tab_columnas, tab_gestion = st.tabs(
    [
        "Resumen",
        "Vista previa",
        "Columnas",
        "Gestión",
    ]
)


with tab_resumen:
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.markdown("#### Performance TAT")
        st.dataframe(
            construir_resumen_tat(df_tat),
            use_container_width=True,
            hide_index=True,
        )

    with col_res2:
        st.markdown("#### Rango incumplimiento")
        st.dataframe(
            construir_resumen_rango_incumplimiento(df_tat),
            use_container_width=True,
            hide_index=True,
        )


with tab_preview:
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

    filas_preview = st.slider(
        "Filas a mostrar",
        min_value=5,
        max_value=min(200, max(5, df_tat.shape[0])),
        value=min(50, max(5, df_tat.shape[0])),
        step=5,
    )

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


with tab_columnas:
    st.dataframe(
        construir_tabla_columnas(df_tat),
        use_container_width=True,
        hide_index=True,
    )


with tab_gestion:
    st.dataframe(
        construir_resumen_archivos(),
        use_container_width=True,
        hide_index=True,
    )

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        if st.button(
            "Eliminar archivo activo",
            use_container_width=True,
        ):
            eliminar_archivo_de_sesion(nombre_archivo)
            st.rerun()

    with col_g2:
        if st.button(
            "Eliminar todos",
            use_container_width=True,
        ):
            eliminar_todos_los_archivos()
            st.rerun()
