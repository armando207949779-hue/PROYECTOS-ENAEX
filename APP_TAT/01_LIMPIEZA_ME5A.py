# ============================================================
# 01_LIMPIEZA_ME5A
# Limpieza minimalista ME5A
# Flujo: cargar archivo -> procesar -> confirmar -> descargar parquet
# CSV opcional
# Excel eliminado
# ============================================================

import io
import re
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="01_LIMPIEZA_ME5A",
    page_icon="🧹",
    layout="wide",
)


# ============================================================
# Rutas
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# ============================================================
# Estilo visual minimalista
# IMPORTANTE:
# No se modifica .block-container para no afectar el logo.
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

        div[data-testid="stFileUploader"] {
            padding: 10px;
            border-radius: 12px;
        }

        .app-header {
            text-align: center;
            margin-bottom: 1rem;
        }

        .app-title {
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 0;
        }

        .app-subtitle {
            color: #6c757d;
            font-size: 16px;
            margin-top: 4px;
        }

        .step-box {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 16px;
        }

        .small-muted {
            color: #6c757d;
            font-size: 14px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Logo
# Se mantiene la configuración original.
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
            unsafe_allow_html=True
        )


# ============================================================
# Funciones base
# ============================================================

def obtener_separador(separador_csv: str):
    separadores = {
        "Automático": None,
        "Punto y coma (;)": ";",
        "Coma (,)": ",",
        "Tabulación": "\t",
    }

    return separadores.get(separador_csv, None)


def generar_nombre_salida(nombre_archivo: str, extension: str) -> str:
    nombre_base = Path(nombre_archivo).stem

    nombre_base = nombre_base.strip().lower()
    nombre_base = re.sub(r"\s+", "_", nombre_base)
    nombre_base = nombre_base.replace("-", "_")
    nombre_base = re.sub(r"[^a-zA-Z0-9_]", "", nombre_base)
    nombre_base = re.sub(r"_+", "_", nombre_base)
    nombre_base = nombre_base.strip("_")

    if not nombre_base:
        nombre_base = "archivo"

    if nombre_base.startswith("me5a"):
        return f"{nombre_base}_limpio.{extension}"

    return f"me5a_{nombre_base}_limpio.{extension}"


# ============================================================
# Lectura de archivo
# ============================================================

@st.cache_data(show_spinner=False)
def leer_archivo_cache(
    bytes_archivo: bytes,
    nombre_archivo: str,
    separador_csv: str,
) -> pd.DataFrame:

    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".xlsx"):
        return pd.read_excel(buffer)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)

        dtype_csv = {
            "Indicador liberación": "string",
            "Grupo de compras": "string",
            "Tipo de imputación": "string",
            "Fecha de solicitud": "string",
            "Fecha modificación": "string",
            "Fe.liber.Z": "string",
            "Solicitud de pedido": "string",
            "Pedido": "string",
            "Fecha de pedido": "string",
            "Tipo de posición": "string",
            "Pos.solicitud pedido": "string",
            "Posición de pedido": "string",
            "Material": "string",
            "Texto breve": "string",
            "Cantidad solicitada": "string",
            "Unidad de medida": "string",
            "Precio de valoración": "string",
            "Moneda": "string",
            "Solicitante": "string",
            "Autor": "string",
            "Centro": "string",
            "Número de necesidad": "string",
            "Status tratamiento": "string",
            "Fecha de entrega": "string",
            "Fecha de liberación": "string",
        }

        try:
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip",
                dtype=dtype_csv,
            )

        except Exception:
            buffer.seek(0)

            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip",
                dtype=dtype_csv,
            )

    raise ValueError("Formato no soportado. Usa archivos .parquet, .xlsx o .csv")


# ============================================================
# Limpieza de fechas
# ============================================================

def convertir_fecha_segura(serie: pd.Series) -> pd.Series:
    s = serie.astype("string").str.strip()

    s = s.replace(
        {
            "": pd.NA,
            "nan": pd.NA,
            "NaN": pd.NA,
            "None": pd.NA,
            "none": pd.NA,
            "NaT": pd.NA,
        }
    )

    es_yyyymmdd = s.str.match(r"^\d{8}$", na=False)
    es_iso = s.str.match(r"^\d{4}-\d{2}-\d{2}$", na=False)

    resultado = pd.Series(
        pd.NaT,
        index=s.index,
        dtype="datetime64[ns]",
    )

    resultado.loc[es_yyyymmdd] = pd.to_datetime(
        s.loc[es_yyyymmdd],
        format="%Y%m%d",
        errors="coerce",
    )

    resultado.loc[es_iso] = pd.to_datetime(
        s.loc[es_iso],
        format="%Y-%m-%d",
        errors="coerce",
    )

    restantes = ~(es_yyyymmdd | es_iso)

    resultado.loc[restantes] = pd.to_datetime(
        s.loc[restantes],
        errors="coerce",
        dayfirst=True,
    )

    return resultado


# ============================================================
# Limpieza ME5A
# ============================================================

def limpiar_me5a(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = df.columns.astype(str).str.strip()

    df = df.dropna(axis=1, how="all")

    columnas_unnamed = [
        col for col in df.columns
        if str(col).startswith("Unnamed")
    ]

    for col in columnas_unnamed:
        if df[col].isna().all():
            df = df.drop(columns=[col])

    columnas_texto = df.select_dtypes(include=["object", "string"]).columns

    for col in columnas_texto:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
        )

    columnas_fecha = [
        "Fecha de solicitud",
        "Fecha modificación",
        "Fe.liber.Z",
        "Fecha de pedido",
        "Fecha de entrega",
        "Fecha de liberación",
    ]

    for col in columnas_fecha:
        if col in df.columns:
            df[col] = convertir_fecha_segura(df[col])

    columnas_decimales = [
        "Cantidad solicitada",
        "Precio de valoración",
    ]

    for col in columnas_decimales:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .str.replace(",", ".", regex=False)
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    columnas_enteras = [
        "Pedido",
        "Solicitud de pedido",
        "Pos.solicitud pedido",
        "Posición de pedido",
    ]

    for col in columnas_enteras:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.strip()
                .str.replace(r"\.0$", "", regex=True)
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            ).astype("Int64")

    return df


@st.cache_data(show_spinner=False)
def limpiar_cache(df: pd.DataFrame) -> pd.DataFrame:
    return limpiar_me5a(df)


# ============================================================
# Diagnóstico simple
# ============================================================

def columnas_fecha_detectadas(df: pd.DataFrame) -> list[str]:
    return [
        col for col in df.columns
        if is_datetime64_any_dtype(df[col])
    ]


def diagnostico_general(
    df_original: pd.DataFrame,
    df_limpio: pd.DataFrame,
) -> dict:

    columnas_originales = set(df_original.columns.astype(str))
    columnas_limpias = set(df_limpio.columns.astype(str))

    columnas_eliminadas = sorted(
        list(columnas_originales - columnas_limpias)
    )

    columnas_fecha = columnas_fecha_detectadas(df_limpio)

    columnas_numericas = [
        col for col in [
            "Cantidad solicitada",
            "Precio de valoración",
            "Pedido",
            "Solicitud de pedido",
            "Pos.solicitud pedido",
            "Posición de pedido",
        ]
        if col in df_limpio.columns
    ]

    return {
        "filas_originales": len(df_original),
        "columnas_originales": df_original.shape[1],
        "filas_limpias": len(df_limpio),
        "columnas_limpias": df_limpio.shape[1],
        "columnas_eliminadas": columnas_eliminadas,
        "columnas_fecha": columnas_fecha,
        "columnas_numericas": columnas_numericas,
        "duplicados": int(df_limpio.duplicated().sum()),
        "nulos": int(df_limpio.isna().sum().sum()),
    }


def tabla_diagnostico_columnas(df: pd.DataFrame) -> pd.DataFrame:
    total_filas = len(df)

    if total_filas == 0:
        return pd.DataFrame(
            {
                "Columna": df.columns,
                "Tipo de dato": [str(dtype) for dtype in df.dtypes],
                "Nulos": 0,
                "% Nulos": 0,
                "Valores únicos": 0,
            }
        )

    diagnostico = pd.DataFrame(
        {
            "Columna": df.columns,
            "Tipo de dato": [str(dtype) for dtype in df.dtypes],
            "Nulos": df.isna().sum().values,
            "% Nulos": (df.isna().sum().values / total_filas * 100).round(2),
            "Valores únicos": df.nunique(dropna=True).values,
        }
    )

    return diagnostico.sort_values(
        by="% Nulos",
        ascending=False,
    ).reset_index(drop=True)


@st.cache_data(show_spinner=False)
def diagnostico_columnas_cache(df: pd.DataFrame) -> pd.DataFrame:
    return tabla_diagnostico_columnas(df)


# ============================================================
# Exportación
# Excel eliminado
# ============================================================

def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow",
    )

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


# ============================================================
# Encabezado
# ============================================================

mostrar_logo()

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">01_LIMPIEZA_ME5A</div>
        <div class="app-subtitle">
            Carga, limpieza y descarga de archivo ME5A en formato Parquet
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Configuración CSV
# ============================================================

with st.expander("Configuración CSV", expanded=False):
    separador_csv = st.selectbox(
        "Separador para archivos CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación",
        ],
        index=0,
    )


# ============================================================
# Paso 1: Cargar archivo
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">1. Cargar archivo</h4>
        <p class="small-muted">
            Formatos permitidos: Parquet, Excel o CSV.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Selecciona el archivo ME5A",
    type=["parquet", "xlsx", "csv"],
    label_visibility="collapsed",
)

if uploaded_file is None:
    st.info("Carga un archivo ME5A para iniciar el proceso.")
    st.stop()


# ============================================================
# Paso 2: Procesar archivo
# ============================================================

try:
    bytes_archivo = uploaded_file.getvalue()

    firma_archivo = (
        f"{uploaded_file.name}_"
        f"{len(bytes_archivo)}_"
        f"{separador_csv}"
    )

    nombre_archivo = uploaded_file.name

    with st.spinner("Procesando archivo..."):
        df_original = leer_archivo_cache(
            bytes_archivo=bytes_archivo,
            nombre_archivo=nombre_archivo,
            separador_csv=separador_csv,
        )

        df_limpio = limpiar_cache(df_original)

        resumen = diagnostico_general(
            df_original=df_original,
            df_limpio=df_limpio,
        )

        diagnostico_columnas = diagnostico_columnas_cache(df_limpio)

        parquet_bytes = convertir_a_parquet_cache(df_limpio)

        nombre_parquet = generar_nombre_salida(
            nombre_archivo=nombre_archivo,
            extension="parquet",
        )

        nombre_csv = generar_nombre_salida(
            nombre_archivo=nombre_archivo,
            extension="csv",
        )

except Exception as e:
    st.error("No fue posible procesar el archivo.")
    st.exception(e)
    st.stop()


st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">2. Archivo procesado</h4>
        <p class="small-muted">
            La limpieza fue ejecutada correctamente.
            El archivo de salida ya está listo.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.success("Archivo procesado correctamente.")


# ============================================================
# Resumen compacto
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Filas entrada", f"{resumen['filas_originales']:,}")
col2.metric("Columnas entrada", f"{resumen['columnas_originales']:,}")
col3.metric("Filas salida", f"{resumen['filas_limpias']:,}")
col4.metric("Columnas salida", f"{resumen['columnas_limpias']:,}")


# ============================================================
# Paso 3: Descargar salida principal
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">3. Descargar archivo limpio</h4>
        <p class="small-muted">
            El formato principal de salida es Parquet.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.download_button(
    label="Descargar archivo Parquet",
    data=parquet_bytes,
    file_name=nombre_parquet,
    mime="application/octet-stream",
    type="primary",
    use_container_width=True,
)


# ============================================================
# Detalle opcional
# ============================================================

with st.expander("Ver detalle del procesamiento", expanded=False):
    col_a, col_b, col_c = st.columns(3)

    col_a.metric("Celdas nulas", f"{resumen['nulos']:,}")
    col_b.metric("Filas duplicadas", f"{resumen['duplicados']:,}")
    col_c.metric("Columnas fecha", f"{len(resumen['columnas_fecha']):,}")

    st.markdown("#### Cambios aplicados")

    columnas_eliminadas = resumen["columnas_eliminadas"]
    columnas_fecha = resumen["columnas_fecha"]
    columnas_numericas = resumen["columnas_numericas"]

    st.write("- Se limpiaron nombres de columnas.")
    st.write("- Se quitaron columnas completamente vacías.")
    st.write("- Se limpiaron espacios en textos y valores vacíos.")

    st.write(
        f"- Columnas convertidas a fecha: "
        f"{', '.join(columnas_fecha) if columnas_fecha else 'No detectadas'}."
    )

    st.write(
        f"- Columnas convertidas a número: "
        f"{', '.join(columnas_numericas) if columnas_numericas else 'No detectadas'}."
    )

    st.write(
        f"- Columnas eliminadas: "
        f"{', '.join(columnas_eliminadas) if columnas_eliminadas else 'No se eliminaron columnas por nombre'}."
    )


with st.expander("Vista previa de datos", expanded=False):
    tab_entrada, tab_salida = st.tabs(
        [
            "Entrada",
            "Salida limpia",
        ]
    )

    with tab_entrada:
        st.dataframe(
            df_original.head(100),
            use_container_width=True,
        )

    with tab_salida:
        st.dataframe(
            df_limpio.head(100),
            use_container_width=True,
        )


with st.expander("Diagnóstico de columnas", expanded=False):
    st.dataframe(
        diagnostico_columnas,
        use_container_width=True,
    )


# ============================================================
# Descarga opcional CSV
# CSV se genera solo si el usuario lo prepara.
# Excel eliminado.
# ============================================================

with st.expander("Descarga opcional CSV", expanded=False):
    st.caption(
        "El archivo recomendado es Parquet. CSV se prepara solo cuando lo solicitas."
    )

    preparar_csv = st.button(
        "Preparar CSV",
        use_container_width=True,
    )

    if preparar_csv:
        with st.spinner("Preparando CSV..."):
            st.session_state["me5a_csv_bytes"] = convertir_a_csv_cache(df_limpio)
            st.session_state["me5a_csv_firma"] = firma_archivo
            st.session_state["me5a_csv_nombre"] = nombre_csv

    if (
        st.session_state.get("me5a_csv_bytes") is not None
        and st.session_state.get("me5a_csv_firma") == firma_archivo
    ):
        st.download_button(
            label="Descargar CSV",
            data=st.session_state["me5a_csv_bytes"],
            file_name=st.session_state["me5a_csv_nombre"],
            mime="text/csv",
            use_container_width=True,
        )
