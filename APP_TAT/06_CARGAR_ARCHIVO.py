# ============================================================
# 06_CARGAR_ARCHIVO
# Carga del archivo TAT generado por 05_CALCULOS
# Guarda archivo activo en sesión como df_tat
# Archivo esperado ejemplo:
# 05_CALCULOS_20260618_132722_TAT.parquet
# ============================================================

import base64
from pathlib import Path
from io import BytesIO
from urllib.parse import urlparse

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
# CONFIGURACIÓN SHAREPOINT
# ============================================================

URL_PARQUET_TAT_SHAREPOINT = (
    "https://empresassk-my.sharepoint.com/:u:/g/personal/"
    "enrique_brun_aep_enaex_com/"
    "IQC5EjhhupQsRIoiSgySri7uAbJDT60Jgc6xlieg9wwrq-Y?e=svCDl8"
)


# ============================================================
# ESTILOS
# No se modifica .block-container para no afectar el logo.
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #fafafa;
            padding: 12px;
            border-radius: 12px;
            border: 1px solid #eeeeee;
        }

        div[data-testid="stFileUploader"] {
            padding: 6px;
            border-radius: 12px;
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
            margin-bottom: 18px;
        }

        .section-caption {
            color: #6B7280;
            font-size: 14px;
            margin-top: -6px;
            margin-bottom: 10px;
        }

        .step-box {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 16px;
        }

        .small-muted {
            color: #6B7280;
            font-size: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


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
# COLUMNAS ESPERADAS DEL ARCHIVO TAT
# Archivo generado por 05_CALCULOS
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
    if "archivos_tat" not in st.session_state:
        st.session_state["archivos_tat"] = {}

    if "archivo_tat_activo" not in st.session_state:
        st.session_state["archivo_tat_activo"] = None

    if "df_tat" not in st.session_state:
        st.session_state["df_tat"] = None

    if "nombre_archivo_tat" not in st.session_state:
        st.session_state["nombre_archivo_tat"] = None


# ============================================================
# FUNCIONES BASE
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
    """
    Convierte un link compartido de SharePoint/OneDrive en intento
    de descarga directa.

    Si ya tiene parámetros, agrega &download=1.
    Si no tiene parámetros, agrega ?download=1.
    """

    url = url.strip()

    if not url:
        raise ValueError("La URL de SharePoint está vacía.")

    if "download=1" in url.lower():
        return url

    separador = "&" if "?" in url else "?"

    return f"{url}{separador}download=1"


def detectar_nombre_desde_url(url: str) -> str:
    """
    Intenta obtener el nombre del archivo desde la URL final.
    Si no puede, usa un nombre estándar.
    """

    try:
        path = urlparse(url).path
        nombre = Path(path).name

        if nombre.lower().endswith(".parquet"):
            return nombre

    except Exception:
        pass

    return "05_CALCULOS_SHAREPOINT_TAT.parquet"


@st.cache_data(show_spinner=False)
def leer_parquet_sharepoint_cache(url: str):
    """
    Descarga un Parquet desde SharePoint usando requests.

    Devuelve:
    - DataFrame
    - Nombre detectado del archivo
    - URL final resuelta
    """

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
        raise ValueError(
            "SharePoint devolvió HTML, no el archivo Parquet. "
            "Verifica que el link permita descarga directa."
        )

    if not (
        response.content[:4] == b"PAR1"
        and response.content[-4:] == b"PAR1"
    ):
        raise ValueError(
            "El archivo descargado no parece ser un Parquet válido. "
            "No se encontró la firma PAR1 al inicio y al final."
        )

    df = pd.read_parquet(BytesIO(response.content))

    nombre_archivo = detectar_nombre_desde_url(response.url)

    return df, nombre_archivo, response.url


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def detectar_nombre_archivo_tat(nombre_archivo: str) -> bool:
    """
    Detecta si el nombre del archivo corresponde al patrón esperado
    del archivo generado por 05_CALCULOS.

    Ejemplo esperado:
    05_CALCULOS_20260618_132722_TAT.parquet
    """

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
    """
    Limpia nombres de columnas y normaliza columnas principales
    del archivo TAT.
    """

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
            "El archivo no parece ser un resultado TAT válido generado por 05_CALCULOS. "
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
    if nombre_archivo in st.session_state["archivos_tat"]:
        st.session_state["archivos_tat"].pop(nombre_archivo)

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

        resumen.append(
            {
                "Archivo": nombre,
                "Archivo 05_CALCULOS_TAT": detectar_nombre_archivo_tat(nombre),
                "TAT válido": validacion["es_valido"],
                "Filas": df.shape[0],
                "Columnas": df.shape[1],
                "Memoria aproximada MB": round(
                    df.memory_usage(deep=True).sum() / 1024 / 1024,
                    2,
                ),
                "Activo": nombre == st.session_state.get("archivo_tat_activo"),
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
    if "performance_tat_total" in df.columns:
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

    return pd.DataFrame(
        columns=[
            "performance_tat_total",
            "Cantidad",
            "%",
        ]
    )


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


# ============================================================
# CONFIGURACIÓN DE LECTURA
# ============================================================

with st.expander("Configuración CSV", expanded=False):
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

    st.caption("Esta configuración solo aplica a archivos CSV.")


# ============================================================
# CARGA DE ARCHIVO TAT
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">1. Cargar archivo TAT</h4>
        <p class="small-muted">
            Carga el archivo generado por 05_CALCULOS.
            Ejemplo esperado: 05_CALCULOS_20260618_132722_TAT.parquet.
            Puedes subirlo manualmente o cargarlo directamente desde SharePoint.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_subir, tab_sharepoint = st.tabs(
    [
        "Subir archivo",
        "Cargar desde SharePoint",
    ]
)


# ============================================================
# OPCIÓN 1: SUBIR ARCHIVO MANUALMENTE
# ============================================================

with tab_subir:
    st.caption(
        "Usa esta opción si quieres cargar manualmente uno o varios archivos "
        "CSV, XLSX, XLS o PARQUET."
    )

    archivos = st.file_uploader(
        "Selecciona uno o varios archivos TAT",
        type=["xlsx", "xls", "csv", "parquet"],
        accept_multiple_files=True,
        key="archivos_base_tat_uploader",
        label_visibility="collapsed",
    )

    if archivos:
        archivos_cargados = []
        archivos_con_error = []
        archivos_con_advertencia = []

        with st.spinner("Leyendo y validando archivos TAT..."):
            for archivo in archivos:
                try:
                    archivo_bytes = archivo.getvalue()

                    df = leer_archivo_cache(
                        archivo_bytes=archivo_bytes,
                        nombre_archivo=archivo.name,
                        separador_csv=separador_csv,
                    )

                    es_nombre_tat = detectar_nombre_archivo_tat(archivo.name)

                    if not es_nombre_tat:
                        archivos_con_advertencia.append(
                            {
                                "archivo": archivo.name,
                                "advertencia": (
                                    "El nombre no sigue el patrón esperado "
                                    "05_CALCULOS_YYYYMMDD_HHMMSS_TAT, "
                                    "pero se validará por columnas."
                                ),
                            }
                        )

                    guardar_archivo_en_sesion(
                        df=df,
                        nombre_archivo=archivo.name,
                    )

                    archivos_cargados.append(archivo.name)

                except Exception as error:
                    archivos_con_error.append(
                        {
                            "archivo": archivo.name,
                            "error": str(error),
                        }
                    )

        if archivos_cargados:
            st.success(
                f"{len(archivos_cargados)} archivo(s) TAT cargado(s). "
                f"Activo: {st.session_state['nombre_archivo_tat']}"
            )

        if archivos_con_advertencia:
            st.warning(
                f"{len(archivos_con_advertencia)} archivo(s) fueron cargados, "
                "pero su nombre no sigue el patrón esperado."
            )

            with st.expander("Ver advertencias de nombre", expanded=False):
                for item in archivos_con_advertencia:
                    st.write(f"**{item['archivo']}**")
                    st.code(item["advertencia"])

        if archivos_con_error:
            st.error(
                f"No se pudieron cargar {len(archivos_con_error)} archivo(s)."
            )

            with st.expander("Ver errores de carga", expanded=False):
                for item in archivos_con_error:
                    st.write(f"**{item['archivo']}**")
                    st.code(item["error"])


# ============================================================
# OPCIÓN 2: CARGAR DESDE SHAREPOINT
# ============================================================

with tab_sharepoint:
    st.caption(
        "Usa esta opción para cargar el archivo Parquet directamente desde "
        "SharePoint sin subirlo manualmente."
    )

    url_sharepoint = st.text_input(
        "URL del archivo Parquet en SharePoint",
        value=URL_PARQUET_TAT_SHAREPOINT,
        key="url_parquet_tat_sharepoint",
    )

    cargar_sharepoint = st.button(
        "Cargar Parquet desde SharePoint",
        use_container_width=True,
        key="boton_cargar_sharepoint_tat",
    )

    if cargar_sharepoint:
        try:
            with st.spinner("Descargando y validando archivo Parquet desde SharePoint..."):
                df, nombre_archivo, url_final = leer_parquet_sharepoint_cache(
                    url_sharepoint
                )

                es_nombre_tat = detectar_nombre_archivo_tat(nombre_archivo)

                if not es_nombre_tat:
                    st.warning(
                        "El nombre del archivo no sigue el patrón esperado "
                        "05_CALCULOS_YYYYMMDD_HHMMSS_TAT, "
                        "pero se validará por columnas."
                    )

                guardar_archivo_en_sesion(
                    df=df,
                    nombre_archivo=nombre_archivo,
                )

            st.success(
                f"Archivo TAT cargado correctamente desde SharePoint: "
                f"**{nombre_archivo}**"
            )

            with st.expander("Detalle de conexión SharePoint", expanded=False):
                st.write("**URL final resuelta:**")
                st.code(url_final)

                st.write("**Dimensiones del archivo:**")
                st.code(f"{df.shape[0]:,} filas x {df.shape[1]:,} columnas")

                st.write("**Vista previa:**")
                st.dataframe(
                    df.head(),
                    use_container_width=True,
                )

        except Exception as error:
            st.error("No se pudo cargar el archivo desde SharePoint.")
            st.code(str(error))


# ============================================================
# SIN ARCHIVOS
# ============================================================

if not st.session_state["archivos_tat"]:
    st.info("Todavía no hay archivos TAT cargados.")
    st.stop()


# ============================================================
# ARCHIVO ACTIVO
# ============================================================

st.divider()

st.markdown("### Archivo activo")
st.caption("Este archivo queda disponible para las demás apps como df_tat.")

archivos_disponibles = list(st.session_state["archivos_tat"].keys())

archivo_activo_actual = st.session_state.get("archivo_tat_activo")

if archivo_activo_actual not in archivos_disponibles:
    archivo_activo_actual = archivos_disponibles[0]
    activar_archivo(archivo_activo_actual)

archivo_seleccionado = st.selectbox(
    "Seleccionar archivo activo",
    options=archivos_disponibles,
    index=archivos_disponibles.index(st.session_state["archivo_tat_activo"]),
    key="selector_archivo_tat",
)

activar_archivo(archivo_seleccionado)

df_tat = st.session_state["df_tat"]
nombre_archivo = st.session_state["nombre_archivo_tat"]
validacion_activa = validar_columnas_tat(df_tat)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Archivo activo", nombre_archivo)
col2.metric("Filas", f"{df_tat.shape[0]:,}")
col3.metric("Columnas", f"{df_tat.shape[1]:,}")
col4.metric("TAT válido", "Sí" if validacion_activa["es_valido"] else "No")

st.success(
    f"Archivo activo guardado correctamente como **df_tat**: **{nombre_archivo}**"
)

if validacion_activa["faltantes_recomendadas"]:
    with st.expander("Columnas recomendadas no encontradas", expanded=False):
        st.write(validacion_activa["faltantes_recomendadas"])


# ============================================================
# ARCHIVOS CARGADOS
# ============================================================

with st.expander("Archivos cargados en sesión", expanded=False):
    resumen_df = obtener_resumen_archivos()

    st.dataframe(
        resumen_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# RESUMEN TAT
# ============================================================

with st.expander("Resumen TAT del archivo activo", expanded=True):
    col_res1, col_res2 = st.columns(2)

    with col_res1:
        st.markdown("#### Performance TAT")
        resumen_tat = construir_resumen_tat(df_tat)

        st.dataframe(
            resumen_tat,
            use_container_width=True,
            hide_index=True,
        )

    with col_res2:
        st.markdown("#### Rango incumplimiento TAT")
        resumen_rango = construir_resumen_rango_incumplimiento(df_tat)

        st.dataframe(
            resumen_rango,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# VISTA PREVIA
# ============================================================

with st.expander("Vista previa del archivo activo", expanded=False):
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


# ============================================================
# COLUMNAS
# ============================================================

with st.expander("Columnas disponibles del archivo activo", expanded=False):
    columnas_df = construir_tabla_columnas(df_tat)

    st.dataframe(
        columnas_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ACCIONES
# ============================================================

with st.expander("Acciones", expanded=False):
    col1, col2 = st.columns(2)

    with col1:
        eliminar_activo = st.button(
            "Eliminar archivo activo",
            use_container_width=True,
        )

        if eliminar_activo:
            eliminar_archivo_de_sesion(archivo_seleccionado)
            st.success("Archivo activo eliminado de la sesión.")
            st.rerun()

    with col2:
        eliminar_todos = st.button(
            "Eliminar todos los archivos",
            use_container_width=True,
        )

        if eliminar_todos:
            eliminar_todos_los_archivos()
            st.success("Todos los archivos fueron eliminados de la sesión.")
            st.rerun()
