# ============================================================
# 05_CALCULOS
# Cálculos TAT
# Flujo: cargar match integrado -> generar fechas finales
# -> calcular performance TAT -> descargar Parquet
# CSV opcional
# Excel eliminado
# Nombre de salida único con fecha y hora actual
# Ejemplo: 05_CALCULOS_20260618_132722_TAT.parquet
# ============================================================

import io
import base64
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="05_CALCULOS",
    page_icon="📊",
    layout="wide",
)


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# ============================================================
# Estilo visual minimalista
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
# Se mantiene configuración original de esta app.
# ============================================================

def mostrar_logo(ancho: int = 180):
    if not LOGO_PATH.exists():
        return

    logo_svg = LOGO_PATH.read_text(encoding="utf-8")
    logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")

    st.markdown(
        f"""
        <div style="
            width: 100%;
            text-align: center;
            margin-top: 0.5rem;
            margin-bottom: 1rem;
        ">
            <img 
                src="data:image/svg+xml;base64,{logo_base64}" 
                width="{ancho}"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Columnas esperadas
# ============================================================

COL_SOLICITUD_ME5A = "Solicitud de pedido - ME5A"
COL_FECHA_SOLICITUD_ME5A = "Fecha de solicitud - ME5A"
COL_FECHA_LIBERACION_ME5A = "Fecha de liberación - ME5A"
COL_FECHA_PEDIDO_ME5A = "Fecha de pedido - ME5A"
COL_FECHA_APROBACION_ARIBA = "Fecha de aprobación - ARIBA"

COL_FECHA_FACTURACION_ME80FN = "Fecha facturación proveedor - ME80FN"
COL_FECHA_RECEPCION_ME80FN = "Fecha recepción mercancía - ME80FN"

COL_ESTADO_MATCH = "Estado del match"

COLUMNAS_REQUERIDAS_FECHAS = [
    COL_SOLICITUD_ME5A,
    COL_FECHA_SOLICITUD_ME5A,
    COL_FECHA_LIBERACION_ME5A,
    COL_FECHA_PEDIDO_ME5A,
    COL_FECHA_APROBACION_ARIBA,
    COL_FECHA_FACTURACION_ME80FN,
    COL_FECHA_RECEPCION_ME80FN,
]

COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

COLUMNAS_FECHAS_FINALES = [
    COL_FECHA_SOLICITUD_FINAL,
    COL_FECHA_LIBERACION_FINAL,
    COL_FECHA_PEDIDO_FINAL,
    COL_FECHA_FACTURACION_FINAL,
    COL_FECHA_RECEPCION_FINAL,
]

COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - ME80FN"
COL_TIPO_COMPRA_ARIBA = "Tipo de compra - ARIBA"
COL_CANTIDAD_SOLICITADA = "Cantidad solicitada - ME5A"
COL_PRECIO_VALORACION = "Precio de valoración"

COLUMNAS_REQUERIDAS_PERFORMANCE = [
    COL_FECHA_SOLICITUD_FINAL,
    COL_FECHA_LIBERACION_FINAL,
    COL_FECHA_PEDIDO_FINAL,
    COL_FECHA_FACTURACION_FINAL,
    COL_FECHA_RECEPCION_FINAL,
]

COLUMNAS_FECHA_PERFORMANCE = [
    COL_FECHA_SOLICITUD_FINAL,
    COL_FECHA_LIBERACION_FINAL,
    COL_FECHA_PEDIDO_FINAL,
    COL_FECHA_FACTURACION_FINAL,
    COL_FECHA_RECEPCION_FINAL,

    "Fecha de solicitud - ME5A",
    "Fecha modificación",
    "Fecha de liberación - ME5A",
    "Fecha de pedido - ME5A",
    "Fecha de entrega - ME5A",
    "Fecha de liberación",

    "Fecha solicitud de compra - ARIBA",
    "Fecha de aprobación - ARIBA",

    "Fecha de entrada - ME80FN",
    "Fecha de documento - ME80FN",
    "Fecha contabilización - ME80FN",
    "Fecha facturación proveedor - ME80FN",
    "Fecha recepción mercancía - ME80FN",
]

COLUMNAS_NUEVAS_ORDENADAS = [
    "tipo_oc",
    "origen",
    "sistema",
    "nombre_tipo_compra",
    "monto",

    "dias_liberacion_solped",
    "dias_comprador",
    "dias_liberacion_pedido",
    "dias_proveedor",
    "dias_logistica",
    "dias_tat_total",

    "umbral_liberacion_solped",
    "umbral_comprador",
    "umbral_liberacion_pedido",
    "umbral_proveedor",
    "umbral_logistica",
    "umbral_tat_total",

    "performance_liberacion_solped",
    "performance_comprador",
    "performance_liberacion_pedido",
    "performance_proveedor",
    "performance_logistica",
    "performance_tat_total",

    "tiene_fechas_inconsistentes",
    "dias_incumplimiento_tat",
    "incumplimiento_tat",
    "rango_incumplimiento_tat",
]


# ============================================================
# Funciones generales
# ============================================================

def obtener_separador(separador_csv: str):
    separadores = {
        "Automático": None,
        "Punto y coma (;)": ";",
        "Coma (,)": ",",
        "Tabulación": "\t",
    }

    return separadores.get(separador_csv, None)


def generar_nombre_salida(extension: str) -> str:
    """
    Genera un nombre único para el archivo de salida TAT.

    Formato:
    05_CALCULOS_YYYYMMDD_HHMMSS_TAT.extension

    Ejemplo:
    05_CALCULOS_20260618_132722_TAT.parquet
    """

    fecha_hora_actual = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"05_CALCULOS_{fecha_hora_actual}_TAT.{extension}"


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

    raise ValueError("Formato no soportado. Usa archivos .parquet, .xlsx o .csv")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def normalizar_columnas_me80fn(df: pd.DataFrame) -> pd.DataFrame:
    """
    Corrige compatibilidad con archivos antiguos que aún dicen NME80FN.
    """
    df = df.copy()

    renombrar = {
        col: col.replace("NME80FN", "ME80FN")
        for col in df.columns
        if "NME80FN" in col
    }

    df = df.rename(columns=renombrar)

    if COL_ESTADO_MATCH in df.columns:
        df[COL_ESTADO_MATCH] = (
            df[COL_ESTADO_MATCH]
            .astype("string")
            .str.replace("NME80FN", "ME80FN", regex=False)
        )

    return df


def validar_columnas_requeridas(df: pd.DataFrame, columnas: list[str], contexto: str):
    faltantes = [
        col for col in columnas
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas para {contexto}: {faltantes}"
        )


def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
    """
    Convierte fechas que pueden venir como datetime, texto,
    timestamp en milisegundos o timestamp en segundos.
    """
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie, errors="coerce")
    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")

    mask_num = serie_num.notna()

    if mask_num.any():
        mask_ms = mask_num & serie_num.abs().ge(10**11)
        mask_s = mask_num & serie_num.abs().lt(10**11)

        if mask_ms.any():
            resultado.loc[mask_ms] = pd.to_datetime(
                serie_num.loc[mask_ms],
                unit="ms",
                errors="coerce",
            )

        if mask_s.any():
            resultado.loc[mask_s] = pd.to_datetime(
                serie_num.loc[mask_s],
                unit="s",
                errors="coerce",
            )

    mask_no_num = ~mask_num

    if mask_no_num.any():
        resultado.loc[mask_no_num] = pd.to_datetime(
            serie.loc[mask_no_num],
            errors="coerce",
            dayfirst=True,
        )

    return resultado


def bool_array(condicion) -> np.ndarray:
    return pd.Series(condicion).fillna(False).to_numpy(dtype=bool)


def extraer_tipo_oc(valor):
    if pd.isna(valor):
        return pd.NA

    texto = str(valor).strip()

    try:
        texto = str(int(float(texto)))
    except Exception:
        texto = texto.replace(".0", "")

    if len(texto) >= 2:
        return texto[:2]

    return pd.NA


def diferencia_dias(fecha_fin: pd.Series, fecha_inicio: pd.Series) -> pd.Series:
    return (fecha_fin - fecha_inicio).dt.days


def formatear_valor(valor) -> str:
    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    return str(valor)


# ============================================================
# Fechas finales
# ============================================================

@st.cache_data(show_spinner=False)
def aplicar_logica_fechas_finales(df: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df)
    df = normalizar_columnas_me80fn(df)

    validar_columnas_requeridas(
        df,
        COLUMNAS_REQUERIDAS_FECHAS,
        "fechas finales",
    )

    columnas_fecha_base = [
        COL_FECHA_SOLICITUD_ME5A,
        COL_FECHA_LIBERACION_ME5A,
        COL_FECHA_PEDIDO_ME5A,
        COL_FECHA_APROBACION_ARIBA,
        COL_FECHA_FACTURACION_ME80FN,
        COL_FECHA_RECEPCION_ME80FN,
    ]

    for col in columnas_fecha_base:
        df[col] = convertir_fecha_columna(df[col])

    solped_str = (
        df[COL_SOLICITUD_ME5A]
        .astype("string")
        .str.strip()
    )

    mask_solped_6 = solped_str.str.startswith("6").fillna(False)

    df[COL_FECHA_SOLICITUD_FINAL] = df[COL_FECHA_SOLICITUD_ME5A]

    df[COL_FECHA_LIBERACION_FINAL] = np.where(
        mask_solped_6,
        df[COL_FECHA_APROBACION_ARIBA],
        df[COL_FECHA_LIBERACION_ME5A],
    )

    df[COL_FECHA_PEDIDO_FINAL] = df[COL_FECHA_PEDIDO_ME5A]
    df[COL_FECHA_FACTURACION_FINAL] = df[COL_FECHA_FACTURACION_ME80FN]
    df[COL_FECHA_RECEPCION_FINAL] = df[COL_FECHA_RECEPCION_ME80FN]

    for col in COLUMNAS_FECHAS_FINALES:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    df["criterio_fecha_liberacion"] = np.where(
        mask_solped_6,
        "Solicitud de pedido - ME5A empieza con 6: usa Fecha de aprobación - ARIBA",
        "Solicitud de pedido - ME5A no empieza con 6: usa Fecha de liberación - ME5A",
    )

    df["fuente_fecha_liberacion_final"] = np.where(
        mask_solped_6,
        COL_FECHA_APROBACION_ARIBA,
        COL_FECHA_LIBERACION_ME5A,
    )

    return df


def reordenar_columnas_fechas_al_final(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    columnas_finales = [
        "criterio_fecha_liberacion",
        "fuente_fecha_liberacion_final",
    ] + COLUMNAS_FECHAS_FINALES

    columnas_finales = [
        col for col in columnas_finales
        if col in df.columns
    ]

    columnas_base = [
        col for col in df.columns
        if col not in columnas_finales
    ]

    return df[columnas_base + columnas_finales].copy()


def resumen_fechas(df: pd.DataFrame) -> pd.DataFrame:
    total = int(len(df))
    data = []

    for col in COLUMNAS_FECHAS_FINALES:
        if col not in df.columns:
            continue

        no_nulos = int(df[col].notna().sum())
        nulos = int(df[col].isna().sum())

        porcentaje_nulos = (
            round(df[col].isna().mean() * 100, 2)
            if total
            else 0
        )

        data.append(
            {
                "Mensaje": f"{no_nulos:,} registros de {total:,} tienen {col} informada",
                "Columna": col,
                "No nulos": no_nulos,
                "Nulos": nulos,
                "% Nulos": porcentaje_nulos,
                "Fecha mínima": df[col].min(),
                "Fecha máxima": df[col].max(),
            }
        )

    return pd.DataFrame(data)


def generar_resumen_cambios_fechas(
    df_original: pd.DataFrame,
    df_final: pd.DataFrame,
    columnas_originales: list,
    columnas_nuevas: list,
) -> dict:

    total = int(len(df_final))

    solped_str = (
        df_final[COL_SOLICITUD_ME5A]
        .astype("string")
        .str.strip()
    )

    mask_solped_6 = solped_str.str.startswith("6").fillna(False)

    return {
        "total_original": int(len(df_original)),
        "total_final": total,
        "columnas_originales": int(len(columnas_originales)),
        "columnas_finales": int(len(df_final.columns)),
        "columnas_nuevas": int(len(columnas_nuevas)),
        "duplicados_final": int(df_final.duplicated().sum()),
        "solped_6": int(mask_solped_6.sum()),
        "solped_no_6": int((~mask_solped_6).sum()),
    }


def mostrar_resumen_cambios_fechas(resumen_cambios: dict):
    with st.expander("Cambios realizados y lógica de fechas finales", expanded=False):
        st.markdown(
            f"""
### Archivo cargado

- Se cargaron **{resumen_cambios['total_original']:,} registros** del match integrado.
- El resultado conserva **{resumen_cambios['total_final']:,} registros**.
- Se conservaron las columnas originales y se agregaron **{resumen_cambios['columnas_nuevas']:,} columnas nuevas**.

### Resultado de la lógica de fechas

- **{resumen_cambios['total_final']:,} registros** fueron procesados para generar fechas finales.
- **{resumen_cambios['solped_6']:,} registros** usan **Fecha de aprobación - ARIBA** para la fecha de liberación final.
- **{resumen_cambios['solped_no_6']:,} registros** usan **Fecha de liberación - ME5A** para la fecha de liberación final.

### Regla principal de liberación

- Si **Solicitud de pedido - ME5A** empieza con **6**, entonces **fecha_liberacion_final** usa **Fecha de aprobación - ARIBA**.
- Si **Solicitud de pedido - ME5A** no empieza con **6**, entonces **fecha_liberacion_final** usa **Fecha de liberación - ME5A**.

### Salida generada

- Se generó una salida con **{resumen_cambios['total_final']:,} registros** y **{resumen_cambios['columnas_finales']:,} columnas**.
- Filas duplicadas detectadas en la salida final: **{resumen_cambios['duplicados_final']:,}**.
            """
        )


# ============================================================
# Performance TAT
# ============================================================

def evaluar_performance_basica(
    dias: pd.Series,
    umbral: pd.Series,
    texto_sin_dato: str = "No aplica",
    negativos_no_aplican: bool = False,
) -> pd.Series:

    resultado = pd.Series(
        texto_sin_dato,
        index=dias.index,
        dtype="object",
    )

    mask_sin_dato = dias.isna() | umbral.isna()
    mask_negativo = dias.lt(0)

    if negativos_no_aplican:
        resultado.loc[mask_negativo] = "No aplica"

    mask_evaluable = ~mask_sin_dato

    if negativos_no_aplican:
        mask_evaluable = mask_evaluable & ~mask_negativo

    resultado.loc[mask_evaluable & dias.le(umbral)] = "Cumple"
    resultado.loc[mask_evaluable & dias.gt(umbral)] = "No cumple"

    return resultado


def evaluar_performance_tat(df: pd.DataFrame) -> pd.Series:
    resultado = pd.Series(
        "Sin datos",
        index=df.index,
        dtype="object",
    )

    mask_negativos = df["tiene_fechas_inconsistentes"].eq(True)
    mask_en_proceso = df["dias_tat_total"].isna()

    mask_tipo_nacional = df["tipo_oc"].isin(["35", "45"])
    mask_tipo_internacional = df["tipo_oc"].eq("47")
    mask_tipo_valido = df["tipo_oc"].isin(["35", "45", "47"])

    resultado.loc[mask_negativos] = "No aplica al análisis"
    resultado.loc[~mask_negativos & mask_en_proceso] = "En proceso"

    mask_evaluable = ~mask_negativos & ~mask_en_proceso

    resultado.loc[
        mask_evaluable
        & mask_tipo_nacional
        & df["dias_tat_total"].le(40)
    ] = "Cumple"

    resultado.loc[
        mask_evaluable
        & mask_tipo_internacional
        & df["dias_tat_total"].le(70)
    ] = "Cumple"

    resultado.loc[
        mask_evaluable
        & mask_tipo_valido
        & (
            (mask_tipo_nacional & df["dias_tat_total"].gt(40))
            | (mask_tipo_internacional & df["dias_tat_total"].gt(70))
        )
    ] = "No cumple"

    return resultado


def calcular_dias_incumplimiento_tat(
    dias_tat: pd.Series,
    umbral_tat: pd.Series,
) -> pd.Series:

    diferencia = dias_tat - umbral_tat
    resultado = diferencia.where(diferencia > 0, 0)
    resultado = resultado.mask(dias_tat.isna() | umbral_tat.isna(), np.nan)

    return resultado


def calcular_rango_incumplimiento_tat(dias_incumplimiento: pd.Series) -> pd.Series:
    return pd.Series(
        np.select(
            [
                bool_array(dias_incumplimiento.isna()),
                bool_array(dias_incumplimiento.eq(0)),
                bool_array(dias_incumplimiento.between(1, 5, inclusive="both")),
                bool_array(dias_incumplimiento.between(6, 15, inclusive="both")),
                bool_array(dias_incumplimiento.between(16, 30, inclusive="both")),
                bool_array(dias_incumplimiento.gt(30)),
            ],
            [
                "Sin datos",
                "Sin incumplimiento",
                "0-5 días",
                "6-15 días",
                "16-30 días",
                "Mayor a un mes",
            ],
            default="Sin datos",
        ),
        index=dias_incumplimiento.index,
    )


@st.cache_data(show_spinner=False)
def aplicar_logica_performance(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    df = normalizar_columnas_me80fn(df)

    validar_columnas_requeridas(
        df,
        COLUMNAS_REQUERIDAS_PERFORMANCE,
        "performance TAT",
    )

    for col in COLUMNAS_FECHA_PERFORMANCE:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])

    if COL_PEDIDO in df.columns:
        df["tipo_oc"] = df[COL_PEDIDO].apply(extraer_tipo_oc)
    elif COL_DOCUMENTO_COMPRAS in df.columns:
        df["tipo_oc"] = df[COL_DOCUMENTO_COMPRAS].apply(extraer_tipo_oc)
    else:
        df["tipo_oc"] = pd.NA

    df["tipo_oc"] = df["tipo_oc"].astype("string")

    df["origen"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47")),
        ],
        [
            "Nacional",
            "Internacional",
        ],
        default="Otro",
    )

    df["sistema"] = np.select(
        [
            bool_array(df["tipo_oc"].eq("35")),
            bool_array(df["tipo_oc"].isin(["45", "47"])),
        ],
        [
            "Ariba",
            "ERP",
        ],
        default="Otro",
    )

    if COL_TIPO_COMPRA_ARIBA in df.columns:
        tipo_compra_num = pd.to_numeric(
            df[COL_TIPO_COMPRA_ARIBA],
            errors="coerce",
        )
    else:
        tipo_compra_num = pd.Series(np.nan, index=df.index)

    df["nombre_tipo_compra"] = np.select(
        [
            bool_array(tipo_compra_num.eq(1)),
            bool_array(tipo_compra_num.eq(2)),
            bool_array(tipo_compra_num.eq(3)),
        ],
        [
            "Catalogada",
            "No catalogada",
            "Directa",
        ],
        default="Otro",
    )

    if COL_CANTIDAD_SOLICITADA in df.columns and COL_PRECIO_VALORACION in df.columns:
        df["monto"] = (
            pd.to_numeric(df[COL_CANTIDAD_SOLICITADA], errors="coerce")
            * pd.to_numeric(df[COL_PRECIO_VALORACION], errors="coerce")
        )
    else:
        df["monto"] = np.nan

    df["dias_liberacion_solped"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_LIBERACION_FINAL],
        fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL],
    )

    df["dias_comprador"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_PEDIDO_FINAL],
        fecha_inicio=df[COL_FECHA_LIBERACION_FINAL],
    )

    df["dias_liberacion_pedido"] = np.nan

    df["dias_proveedor"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_FACTURACION_FINAL],
        fecha_inicio=df[COL_FECHA_PEDIDO_FINAL],
    )

    df["dias_logistica"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
        fecha_inicio=df[COL_FECHA_FACTURACION_FINAL],
    )

    df["dias_tat_total"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
        fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL],
    )

    df["umbral_liberacion_solped"] = 2
    df["umbral_comprador"] = 10
    df["umbral_liberacion_pedido"] = 2
    df["umbral_logistica"] = 11

    df["umbral_proveedor"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47")),
        ],
        [
            20,
            60,
        ],
        default=np.nan,
    )

    df["umbral_tat_total"] = np.select(
        [
            bool_array(df["tipo_oc"].isin(["35", "45"])),
            bool_array(df["tipo_oc"].eq("47")),
        ],
        [
            40,
            70,
        ],
        default=np.nan,
    )

    df["umbral_proveedor"] = pd.to_numeric(
        df["umbral_proveedor"],
        errors="coerce",
    )

    df["umbral_tat_total"] = pd.to_numeric(
        df["umbral_tat_total"],
        errors="coerce",
    )

    columnas_dias = [
        "dias_liberacion_solped",
        "dias_comprador",
        "dias_liberacion_pedido",
        "dias_proveedor",
        "dias_logistica",
        "dias_tat_total",
    ]

    df["tiene_fechas_inconsistentes"] = (
        df[columnas_dias]
        .lt(0)
        .any(axis=1, skipna=True)
    )

    df["performance_liberacion_solped"] = evaluar_performance_basica(
        dias=df["dias_liberacion_solped"],
        umbral=pd.Series(df["umbral_liberacion_solped"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=True,
    )

    df["performance_comprador"] = evaluar_performance_basica(
        dias=df["dias_comprador"],
        umbral=pd.Series(df["umbral_comprador"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=True,
    )

    df["performance_liberacion_pedido"] = evaluar_performance_basica(
        dias=pd.Series(df["dias_liberacion_pedido"], index=df.index),
        umbral=pd.Series(df["umbral_liberacion_pedido"], index=df.index),
        texto_sin_dato="Sin datos",
        negativos_no_aplican=True,
    )

    df["performance_proveedor"] = evaluar_performance_basica(
        dias=df["dias_proveedor"],
        umbral=df["umbral_proveedor"],
        texto_sin_dato="Sin datos",
        negativos_no_aplican=True,
    )

    df["performance_logistica"] = evaluar_performance_basica(
        dias=df["dias_logistica"],
        umbral=pd.Series(df["umbral_logistica"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=True,
    )

    df["performance_tat_total"] = evaluar_performance_tat(df)

    df["dias_incumplimiento_tat"] = calcular_dias_incumplimiento_tat(
        dias_tat=df["dias_tat_total"],
        umbral_tat=df["umbral_tat_total"],
    )

    df["incumplimiento_tat"] = df["dias_incumplimiento_tat"].gt(0)

    df["rango_incumplimiento_tat"] = calcular_rango_incumplimiento_tat(
        df["dias_incumplimiento_tat"]
    )

    return df


def reordenar_columnas_performance_al_final(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    columnas_finales = [
        col for col in COLUMNAS_NUEVAS_ORDENADAS
        if col in df.columns
    ]

    columnas_base = [
        col for col in df.columns
        if col not in columnas_finales
    ]

    return df[columnas_base + columnas_finales].copy()


# ============================================================
# Resúmenes
# ============================================================

def tabla_inputs_formulas() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Métrica": "Liberación SolPed",
                "Columna": "dias_liberacion_solped",
                "Fórmula": "fecha_liberacion_final - fecha_solicitud_final",
                "Umbral": "2 días",
            },
            {
                "Métrica": "Comprador",
                "Columna": "dias_comprador",
                "Fórmula": "fecha_pedido_final - fecha_liberacion_final",
                "Umbral": "10 días",
            },
            {
                "Métrica": "Liberación Pedido",
                "Columna": "dias_liberacion_pedido",
                "Fórmula": "Sin cálculo por falta de input",
                "Umbral": "2 días",
            },
            {
                "Métrica": "Proveedor",
                "Columna": "dias_proveedor",
                "Fórmula": "fecha_facturacion_final - fecha_pedido_final",
                "Umbral": "OC 35/45 = 20 días; OC 47 = 60 días",
            },
            {
                "Métrica": "Logística",
                "Columna": "dias_logistica",
                "Fórmula": "fecha_recepcion_final - fecha_facturacion_final",
                "Umbral": "11 días",
            },
            {
                "Métrica": "TAT Total",
                "Columna": "dias_tat_total",
                "Fórmula": "fecha_recepcion_final - fecha_solicitud_final",
                "Umbral": "OC 35/45 = 40 días; OC 47 = 70 días",
            },
        ]
    )


def resumen_performance(df: pd.DataFrame) -> pd.DataFrame:
    metricas = [
        ("performance_liberacion_solped", "Liberación SolPed"),
        ("performance_comprador", "Comprador"),
        ("performance_liberacion_pedido", "Liberación Pedido"),
        ("performance_proveedor", "Proveedor"),
        ("performance_logistica", "Logística"),
        ("performance_tat_total", "TAT Total"),
    ]

    data = []

    for columna, metrica in metricas:
        if columna not in df.columns:
            continue

        serie = df[columna].astype("object")

        cumple = int(serie.eq("Cumple").sum())
        no_cumple = int(serie.eq("No cumple").sum())
        no_aplica = int(serie.isin(["No aplica", "No aplica al análisis"]).sum())
        sin_datos = int(serie.isin(["Sin datos", "En proceso"]).sum())

        total_evaluable = cumple + no_cumple

        porcentaje_cumple = (
            round((cumple / total_evaluable) * 100, 2)
            if total_evaluable
            else 0
        )

        data.append(
            {
                "Métrica": metrica,
                "Cumple": cumple,
                "No cumple": no_cumple,
                "No aplica": no_aplica,
                "Sin datos / En proceso": sin_datos,
                "% Cumple sobre evaluables": porcentaje_cumple,
            }
        )

    return pd.DataFrame(data)


def resumen_columnas_nuevas(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        col for col in COLUMNAS_NUEVAS_ORDENADAS
        if col in df.columns
    ]

    return pd.DataFrame(
        {
            "Columna nueva": columnas,
            "Nulos": [int(df[col].isna().sum()) for col in columnas],
            "% Nulos": [round(df[col].isna().mean() * 100, 2) for col in columnas],
            "Tipo dato": [str(df[col].dtype) for col in columnas],
        }
    )


def generar_resumen_cambios_performance(
    df_original: pd.DataFrame,
    df_final: pd.DataFrame,
    columnas_originales: list,
    columnas_nuevas: list,
) -> dict:

    total = int(len(df_final))

    conteo_tipo_oc = (
        df_final["tipo_oc"]
        .value_counts(dropna=False)
        .to_dict()
        if "tipo_oc" in df_final.columns
        else {}
    )

    incumplimientos_tat = (
        int(df_final["incumplimiento_tat"].eq(True).sum())
        if "incumplimiento_tat" in df_final.columns
        else 0
    )

    return {
        "total_original": int(len(df_original)),
        "total_final": total,
        "columnas_originales": int(len(columnas_originales)),
        "columnas_finales": int(len(df_final.columns)),
        "columnas_nuevas": int(len(columnas_nuevas)),
        "duplicados_final": int(df_final.duplicated().sum()),
        "conteo_tipo_oc": conteo_tipo_oc,
        "incumplimientos_tat": incumplimientos_tat,
        "sin_incumplimiento_tat": int(total - incumplimientos_tat),
    }


def mostrar_resumen_cambios_performance(
    resumen_cambios: dict,
    resumen_cols: pd.DataFrame,
):
    with st.expander("Detalle de lógica de performance", expanded=False):
        conteo_tipo_oc = resumen_cambios.get("conteo_tipo_oc", {})

        texto_tipo_oc = "\n".join(
            [
                f"- **{formatear_valor(tipo)}**: {cantidad:,} registros"
                for tipo, cantidad in conteo_tipo_oc.items()
            ]
        )

        if not texto_tipo_oc:
            texto_tipo_oc = "- No se pudo generar conteo por tipo de OC."

        st.markdown(
            f"""
### 1. Resumen del archivo procesado

- Se cargaron **{resumen_cambios['total_original']:,} registros**.
- El resultado final conserva **{resumen_cambios['total_final']:,} registros**.
- Se agregaron **{resumen_cambios['columnas_nuevas']:,} columnas nuevas**.
- Filas duplicadas detectadas en la salida final: **{resumen_cambios['duplicados_final']:,}**.

### 2. Clasificación de OC

La clasificación se realiza tomando los **dos primeros dígitos** del pedido/documento.

| Columna | Lógica |
|---|---|
| `tipo_oc` | Dos primeros dígitos del pedido/documento |
| `origen` | `35` y `45` = Nacional; `47` = Internacional; otros = Otro |
| `sistema` | `35` = Ariba; `45` y `47` = ERP; otros = Otro |
| `nombre_tipo_compra` | `1` = Catalogada; `2` = No catalogada; `3` = Directa; otros = Otro |
| `monto` | Cantidad solicitada multiplicada por precio de valoración |

### 3. Resultado general de incumplimiento TAT

- Registros con incumplimiento TAT: **{resumen_cambios['incumplimientos_tat']:,}**.
- Registros sin incumplimiento TAT: **{resumen_cambios['sin_incumplimiento_tat']:,}**.

### 4. Distribución por tipo de OC

{texto_tipo_oc}
            """
        )

        st.markdown("### 5. Inputs y fórmulas")
        st.dataframe(
            tabla_inputs_formulas(),
            use_container_width=True,
            hide_index=True,
        )

        st.markdown("### 6. Columnas agregadas")
        st.dataframe(
            resumen_cols,
            use_container_width=True,
            hide_index=True,
        )


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
        <div class="app-title">05_CALCULOS</div>
        <div class="app-subtitle">
            Generación de fechas finales y cálculo de Performance TAT
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Configuración
# ============================================================

with st.expander("Configuración", expanded=False):
    col_conf1, col_conf2, col_conf3 = st.columns(3)

    with col_conf1:
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

    with col_conf2:
        limite_vista = st.number_input(
            "Filas en vista previa",
            min_value=50,
            max_value=1000,
            value=300,
            step=50,
        )

    with col_conf3:
        ordenar_performance_final = st.checkbox(
            "Mover columnas de performance al final",
            value=True,
        )

    ordenar_fechas_final = st.checkbox(
        "Mover columnas de fechas finales al final",
        value=False,
    )

    st.caption("El separador solo aplica a archivos CSV.")


# ============================================================
# Paso 1: cargar archivo
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">1. Cargar archivo</h4>
        <p class="small-muted">
            Carga el archivo generado por 04_MATCH. La app generará fechas finales y luego calculará Performance TAT.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader(
    "Selecciona archivo match integrado",
    type=["parquet", "xlsx", "csv"],
    label_visibility="collapsed",
)

if uploaded_file is None:
    st.info("Carga el archivo match integrado para iniciar el cálculo TAT.")
    st.stop()


# ============================================================
# Paso 2: procesar
# ============================================================

try:
    bytes_archivo = uploaded_file.getvalue()

    firma_archivo = (
        f"{uploaded_file.name}_"
        f"{len(bytes_archivo)}_"
        f"{separador_csv}_"
        f"{ordenar_fechas_final}_"
        f"{ordenar_performance_final}"
    )

    with st.spinner("Leyendo archivo..."):
        df_original = leer_archivo_cache(
            bytes_archivo=bytes_archivo,
            nombre_archivo=uploaded_file.name,
            separador_csv=separador_csv,
        )

        df_original = limpiar_nombres_columnas(df_original)
        df_original = normalizar_columnas_me80fn(df_original)

    columnas_originales = list(df_original.columns)

    with st.spinner("Generando fechas finales..."):
        df_fechas = aplicar_logica_fechas_finales(df_original)

        columnas_nuevas_fechas = [
            col for col in df_fechas.columns
            if col not in columnas_originales
        ]

        resumen_fechas_df = resumen_fechas(df_fechas)

        resumen_cambios_fechas = generar_resumen_cambios_fechas(
            df_original=df_original,
            df_final=df_fechas,
            columnas_originales=columnas_originales,
            columnas_nuevas=columnas_nuevas_fechas,
        )

        if ordenar_fechas_final:
            df_fechas = reordenar_columnas_fechas_al_final(df_fechas)

    with st.spinner("Calculando Performance TAT..."):
        columnas_despues_fechas = list(df_fechas.columns)

        df_final = aplicar_logica_performance(df_fechas)

        columnas_nuevas_performance = [
            col for col in df_final.columns
            if col not in columnas_despues_fechas
        ]

        columnas_nuevas_totales = [
            col for col in df_final.columns
            if col not in columnas_originales
        ]

        if ordenar_performance_final:
            df_final = reordenar_columnas_performance_al_final(df_final)

        resumen_perf_df = resumen_performance(df_final)
        resumen_cols_df = resumen_columnas_nuevas(df_final)

        parquet_bytes = convertir_a_parquet_cache(df_final)

        nombre_parquet = generar_nombre_salida("parquet")
        nombre_csv = generar_nombre_salida("csv")

        resumen_cambios_performance = generar_resumen_cambios_performance(
            df_original=df_fechas,
            df_final=df_final,
            columnas_originales=columnas_despues_fechas,
            columnas_nuevas=columnas_nuevas_performance,
        )

except Exception as e:
    st.error("No se pudo completar el cálculo TAT.")
    st.exception(e)
    st.stop()


st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">2. Cálculos generados</h4>
        <p class="small-muted">
            Se generaron las fechas finales y el cálculo de Performance TAT correctamente.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.success("Proceso completo: cálculos TAT generados correctamente.")


# ============================================================
# Indicadores
# ============================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Filas entrada", f"{len(df_original):,}")
col2.metric("Filas salida", f"{len(df_final):,}")
col3.metric("Columnas entrada", f"{len(columnas_originales):,}")
col4.metric("Columnas nuevas", f"{len(columnas_nuevas_totales):,}")

total_cumple_tat = int(df_final["performance_tat_total"].eq("Cumple").sum())
total_no_cumple_tat = int(df_final["performance_tat_total"].eq("No cumple").sum())
total_en_proceso_tat = int(df_final["performance_tat_total"].eq("En proceso").sum())
total_no_aplica_tat = int(df_final["performance_tat_total"].eq("No aplica al análisis").sum())

t1, t2, t3, t4 = st.columns(4)

t1.metric("TAT cumple", f"{total_cumple_tat:,}")
t2.metric("TAT no cumple", f"{total_no_cumple_tat:,}")
t3.metric("TAT en proceso", f"{total_en_proceso_tat:,}")
t4.metric("TAT no aplica", f"{total_no_aplica_tat:,}")


# ============================================================
# Paso 3: descarga principal
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">3. Descargar resultado final</h4>
        <p class="small-muted">
            El formato principal de salida es Parquet.
            El nombre del archivo incluye fecha, hora y la palabra TAT.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.download_button(
    label="Descargar resultado final en Parquet",
    data=parquet_bytes,
    file_name=nombre_parquet,
    mime="application/octet-stream",
    type="primary",
    use_container_width=True,
)


# ============================================================
# Detalle opcional
# ============================================================

mostrar_resumen_cambios_fechas(resumen_cambios_fechas)

mostrar_resumen_cambios_performance(
    resumen_cambios=resumen_cambios_performance,
    resumen_cols=resumen_cols_df,
)

with st.expander("Resumen de fechas finales", expanded=False):
    st.dataframe(
        resumen_fechas_df,
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Resumen de performance", expanded=False):
    st.dataframe(
        resumen_perf_df,
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Rango de incumplimiento TAT", expanded=False):
    if "rango_incumplimiento_tat" in df_final.columns:
        conteo_rango = (
            df_final["rango_incumplimiento_tat"]
            .value_counts(dropna=False)
            .reset_index()
        )

        conteo_rango.columns = [
            "Rango incumplimiento TAT",
            "Cantidad",
        ]

        st.dataframe(
            conteo_rango,
            use_container_width=True,
            hide_index=True,
        )

with st.expander("Vista previa original", expanded=False):
    st.caption(
        f"Mostrando hasta {int(limite_vista):,} registros de {len(df_original):,} registros originales."
    )

    st.dataframe(
        df_original.head(int(limite_vista)),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Vista previa después de fechas finales", expanded=False):
    st.caption(
        f"Mostrando hasta {int(limite_vista):,} registros de {len(df_fechas):,} registros con fechas finales."
    )

    st.dataframe(
        df_fechas.head(int(limite_vista)),
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Vista previa final", expanded=False):
    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        "tipo_oc",
        "origen",
        "sistema",
        "nombre_tipo_compra",
        COL_CANTIDAD_SOLICITADA,
        COL_PRECIO_VALORACION,
        "monto",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_LIBERACION_FINAL,
        COL_FECHA_PEDIDO_FINAL,
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "dias_liberacion_solped",
        "dias_comprador",
        "dias_liberacion_pedido",
        "dias_proveedor",
        "dias_logistica",
        "dias_tat_total",
        "umbral_liberacion_solped",
        "umbral_comprador",
        "umbral_liberacion_pedido",
        "umbral_proveedor",
        "umbral_logistica",
        "umbral_tat_total",
        "performance_liberacion_solped",
        "performance_comprador",
        "performance_liberacion_pedido",
        "performance_proveedor",
        "performance_logistica",
        "performance_tat_total",
        "tiene_fechas_inconsistentes",
        "dias_incumplimiento_tat",
        "incumplimiento_tat",
        "rango_incumplimiento_tat",
    ]

    columnas_preferidas = [
        col for col in columnas_preferidas
        if col in df_final.columns
    ]

    st.caption(
        f"Mostrando hasta {int(limite_vista):,} registros de {len(df_final):,} registros generados."
    )

    if columnas_preferidas:
        st.dataframe(
            df_final[columnas_preferidas].head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(
            df_final.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )

with st.expander("Ver columnas disponibles", expanded=False):
    col_a, col_b, col_c = st.columns(3)

    with col_a:
        st.markdown("**Columnas originales**")
        st.write(columnas_originales)

    with col_b:
        st.markdown("**Columnas nuevas de fechas**")
        st.write(columnas_nuevas_fechas)

    with col_c:
        st.markdown("**Columnas nuevas de performance**")
        st.write(columnas_nuevas_performance)

with st.expander("Top filas con mayor incumplimiento TAT", expanded=False):
    if "dias_incumplimiento_tat" in df_final.columns:
        columnas_top = [
            "Solicitud de pedido - ME5A",
            COL_PEDIDO,
            COL_DOCUMENTO_COMPRAS,
            "tipo_oc",
            "origen",
            "sistema",
            "dias_tat_total",
            "umbral_tat_total",
            "dias_incumplimiento_tat",
            "rango_incumplimiento_tat",
            "performance_tat_total",
            COL_FECHA_SOLICITUD_FINAL,
            COL_FECHA_RECEPCION_FINAL,
        ]

        columnas_top = [
            col for col in columnas_top
            if col in df_final.columns
        ]

        st.dataframe(
            df_final
            .sort_values("dias_incumplimiento_tat", ascending=False)[columnas_top]
            .head(100),
            use_container_width=True,
            hide_index=True,
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
            st.session_state["calculos_csv_bytes"] = convertir_a_csv_cache(df_final)
            st.session_state["calculos_csv_firma"] = firma_archivo
            st.session_state["calculos_csv_nombre"] = nombre_csv

    if (
        st.session_state.get("calculos_csv_bytes") is not None
        and st.session_state.get("calculos_csv_firma") == firma_archivo
    ):
        st.download_button(
            label="Descargar CSV",
            data=st.session_state["calculos_csv_bytes"],
            file_name=st.session_state["calculos_csv_nombre"],
            mime="text/csv",
            use_container_width=True,
        )
