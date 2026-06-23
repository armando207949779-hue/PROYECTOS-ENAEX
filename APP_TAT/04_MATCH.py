# ============================================================
# 04_MATCH
# Match integrado ME5A · ARIBA · ME80FN
# Flujo: cargar 3 archivos -> procesar -> confirmar -> descargar parquet
# CSV opcional
# Excel eliminado
# Nombre de salida único con fecha y hora actual
# Ejemplo: 04_MATCH_20260618_132722_MATCH.parquet
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

# Nota: si esta app corre dentro de 00_APP_TAT con st.navigation(),
# no debe ejecutar st.set_page_config aquí para evitar errores de configuración duplicada.
# Si la ejecutas de forma independiente, define st.set_page_config en el portal principal.


# ============================================================
# Rutas
# ============================================================

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
# Se mantiene la configuración original de esta app.
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
    Genera un nombre único para el archivo de salida del match.

    Formato:
    04_MATCH_YYYYMMDD_HHMMSS_MATCH.extension

    Ejemplo:
    04_MATCH_20260618_132722_MATCH.parquet
    """

    fecha_hora_actual = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"04_MATCH_{fecha_hora_actual}_MATCH.{extension}"


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


def validar_columnas(df: pd.DataFrame, columnas: list, nombre_df: str) -> None:
    faltantes = [
        col for col in columnas
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas en {nombre_df}: {faltantes}"
        )


def normalizar_entero_str(serie: pd.Series) -> pd.Series:
    return (
        pd.to_numeric(serie, errors="coerce")
        .astype("Int64")
        .astype("string")
    )


def normalizar_numero(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce")


def normalizar_material(serie: pd.Series) -> pd.Series:
    return (
        serie
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def limpiar_booleanos(df: pd.DataFrame, columnas: list) -> pd.DataFrame:
    df = df.copy()

    for col in columnas:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    return df


def formatear_valor(valor):
    if pd.isna(valor):
        return ""

    return str(valor)


# ============================================================
# Detección de archivos cargados
# ============================================================

def detectar_tipo_archivo(nombre_archivo: str) -> str | None:
    nombre = nombre_archivo.lower()

    if "me5a" in nombre:
        return "ME5A"

    if "ariba" in nombre:
        return "ARIBA"

    if "me80fn" in nombre or "nme80fn" in nombre:
        return "ME80FN"

    return None


def detectar_archivos_cargados(archivos: list) -> dict:
    detectados = {
        "ME5A": None,
        "ARIBA": None,
        "ME80FN": None,
    }

    conflictos = []

    for archivo in archivos:
        tipo = detectar_tipo_archivo(archivo.name)

        if tipo is None:
            continue

        if detectados[tipo] is not None:
            conflictos.append(tipo)
        else:
            detectados[tipo] = archivo

    return {
        "detectados": detectados,
        "conflictos": conflictos,
    }


def archivos_completos(detectados: dict) -> bool:
    return all(
        detectados[tipo] is not None
        for tipo in ["ME5A", "ARIBA", "ME80FN"]
    )


# ============================================================
# Match ME5A vs ME80FN
# Criterio AND estricto:
# Pedido + Posición + Material + Centro
# ============================================================

@st.cache_data(show_spinner=False)
def match_me5a_me80fn(
    df_me5a: pd.DataFrame,
    df_me80fn: pd.DataFrame,
) -> pd.DataFrame:

    me5a = limpiar_nombres_columnas(df_me5a)
    me80fn = limpiar_nombres_columnas(df_me80fn)

    validar_columnas(
        me5a,
        [
            "Pedido",
            "Posición de pedido",
            "Material",
            "Centro",
        ],
        "ME5A",
    )

    validar_columnas(
        me80fn,
        [
            "Documento compras",
            "Posición",
            "Material",
            "Centro",
        ],
        "ME80FN",
    )

    me5a = me5a.copy()
    me80fn = me80fn.copy()

    me5a["_id_me5a"] = range(len(me5a))
    me80fn["_id_me80fn"] = range(len(me80fn))

    me5a["_pedido_norm"] = normalizar_entero_str(me5a["Pedido"])
    me5a["_posicion_pedido_norm"] = normalizar_entero_str(me5a["Posición de pedido"])
    me5a["_material_norm"] = normalizar_material(me5a["Material"])
    me5a["_centro_norm"] = me5a["Centro"].astype("string").str.strip()

    me80fn["_documento_norm"] = normalizar_entero_str(me80fn["Documento compras"])
    me80fn["_posicion_norm"] = normalizar_entero_str(me80fn["Posición"])
    me80fn["_material_norm"] = normalizar_material(me80fn["Material"])
    me80fn["_centro_norm"] = me80fn["Centro"].astype("string").str.strip()

    columnas_me80fn = [
        "_id_me80fn",
        "_documento_norm",
        "_posicion_norm",
        "_material_norm",
        "_centro_norm",
        "Documento compras",
        "Posición",
        "Centro",
        "Fecha de entrada",
        "Material",
        "Texto breve",
        "Cantidad",
        "Unidad medida pedido",
        "Impte.mon.local",
        "Moneda",
        "Importe",
        "Clase de operación",
        "Fecha de documento",
        "Fecha contabiliz.",
        "fecha_facturacion_proveedor",
        "fecha_entrada_mercancia_recepcion",
    ]

    columnas_me80fn = [
        col for col in columnas_me80fn
        if col in me80fn.columns
    ]

    candidatos = me5a.merge(
        me80fn[columnas_me80fn],
        left_on="_pedido_norm",
        right_on="_documento_norm",
        how="left",
        suffixes=("_me5a", "_me80fn"),
    )

    candidatos["_match_me80fn_pedido_documento"] = (
        candidatos["_pedido_norm"].fillna("")
        .eq(candidatos["_documento_norm"].fillna(""))
    )

    candidatos["_match_me80fn_posicion"] = (
        candidatos["_posicion_pedido_norm"].fillna("")
        .eq(candidatos["_posicion_norm"].fillna(""))
    )

    candidatos["_match_me80fn_material"] = (
        candidatos["_material_norm_me5a"].fillna("")
        .eq(candidatos["_material_norm_me80fn"].fillna(""))
    )

    candidatos["_match_me80fn_centro"] = (
        candidatos["_centro_norm_me5a"].fillna("")
        .eq(candidatos["_centro_norm_me80fn"].fillna(""))
    )

    candidatos["_match_me80fn_estricto"] = (
        candidatos["_match_me80fn_pedido_documento"]
        & candidatos["_match_me80fn_posicion"]
        & candidatos["_match_me80fn_material"]
        & candidatos["_match_me80fn_centro"]
    )

    columnas_bool = [
        "_match_me80fn_pedido_documento",
        "_match_me80fn_posicion",
        "_match_me80fn_material",
        "_match_me80fn_centro",
        "_match_me80fn_estricto",
    ]

    candidatos = limpiar_booleanos(candidatos, columnas_bool)

    candidatos["_prioridad_match_me80fn"] = np.where(
        candidatos["_match_me80fn_estricto"],
        1,
        0,
    )

    candidatos["_coincidencias_me80fn"] = (
        candidatos["_match_me80fn_pedido_documento"].astype(int)
        + candidatos["_match_me80fn_posicion"].astype(int)
        + candidatos["_match_me80fn_material"].astype(int)
        + candidatos["_match_me80fn_centro"].astype(int)
    )

    idx_mejor = (
        candidatos
        .sort_values(
            by=[
                "_prioridad_match_me80fn",
                "_coincidencias_me80fn",
            ],
            ascending=[False, False],
        )
        .groupby("_id_me5a", dropna=False)["_coincidencias_me80fn"]
        .idxmax()
    )

    mejor = candidatos.loc[idx_mejor].copy()

    columnas_resultado = [
        "_id_me5a",
        "_match_me80fn_pedido_documento",
        "_match_me80fn_posicion",
        "_match_me80fn_material",
        "_match_me80fn_centro",
        "_match_me80fn_estricto",
        "Documento compras",
        "Posición",
        "Centro_me80fn",
        "Fecha de entrada",
        "Material_me80fn",
        "Texto breve_me80fn",
        "Cantidad",
        "Unidad medida pedido",
        "Impte.mon.local",
        "Moneda_me80fn",
        "Importe",
        "Clase de operación",
        "Fecha de documento",
        "Fecha contabiliz.",
        "fecha_facturacion_proveedor",
        "fecha_entrada_mercancia_recepcion",
    ]

    columnas_resultado = [
        col for col in columnas_resultado
        if col in mejor.columns
    ]

    resultado = mejor[columnas_resultado].copy()

    resultado = resultado.rename(
        columns={
            "Documento compras": "me80fn_documento_compras",
            "Posición": "me80fn_posicion",
            "Centro_me80fn": "me80fn_centro",
            "Fecha de entrada": "me80fn_fecha_entrada",
            "Material_me80fn": "me80fn_material",
            "Texto breve_me80fn": "me80fn_texto_breve",
            "Cantidad": "me80fn_cantidad",
            "Unidad medida pedido": "me80fn_unidad_medida_pedido",
            "Impte.mon.local": "me80fn_importe_moneda_local",
            "Moneda_me80fn": "me80fn_moneda",
            "Importe": "me80fn_importe",
            "Clase de operación": "me80fn_clase_operacion",
            "Fecha de documento": "me80fn_fecha_documento",
            "Fecha contabiliz.": "me80fn_fecha_contabilizacion",
            "fecha_facturacion_proveedor": "me80fn_fecha_facturacion_proveedor",
            "fecha_entrada_mercancia_recepcion": "me80fn_fecha_recepcion_mercancia",
        }
    )

    return resultado


# ============================================================
# Match ME5A vs ARIBA
# Criterio AND estricto:
# Solicitud + Línea + Pedido
# ============================================================

@st.cache_data(show_spinner=False)
def match_me5a_ariba(
    df_me5a: pd.DataFrame,
    df_ariba: pd.DataFrame,
) -> pd.DataFrame:

    me5a = limpiar_nombres_columnas(df_me5a)
    ariba = limpiar_nombres_columnas(df_ariba)

    validar_columnas(
        me5a,
        [
            "Solicitud de pedido",
            "Pos.solicitud pedido",
            "Pedido",
        ],
        "ME5A",
    )

    validar_columnas(
        ariba,
        [
            "ID de solicitud de compra del ERP",
            "Número de línea de la solicitud de compra",
            "ID de pedido",
        ],
        "ARIBA",
    )

    me5a = me5a.copy()
    ariba = ariba.copy()

    me5a["_id_me5a"] = range(len(me5a))
    ariba["_id_ariba"] = range(len(ariba))

    me5a["_solicitud_norm"] = normalizar_entero_str(
        me5a["Solicitud de pedido"]
    )

    me5a["_pos_solicitud_num"] = normalizar_numero(
        me5a["Pos.solicitud pedido"]
    )

    me5a["_linea_esperada_ariba"] = me5a["_pos_solicitud_num"] / 10

    me5a["_pedido_norm"] = normalizar_entero_str(
        me5a["Pedido"]
    )

    ariba["_id_erp_norm"] = normalizar_entero_str(
        ariba["ID de solicitud de compra del ERP"]
    )

    ariba["_linea_ariba_num"] = normalizar_numero(
        ariba["Número de línea de la solicitud de compra"]
    )

    ariba["_id_pedido_norm"] = normalizar_entero_str(
        ariba["ID de pedido"]
    )

    columnas_ariba = [
        "_id_ariba",
        "_id_erp_norm",
        "_linea_ariba_num",
        "_id_pedido_norm",
        "Tipo de Compra",
        "ID de solicitud de compra",
        "ID de solicitud de compra del ERP",
        "Número de línea de la solicitud de compra",
        "Descripción",
        "Fecha de la solicitud de compra",
        "Fecha de aprobación",
        "ID de pedido",
        "Proveedor - Proveedor de ERP",
        "Centro de costes - ID de centro de costes",
        "Centro de costes - Centro de costes",
        "ID de cuenta",
        "Cuenta",
        "ID de unidad de negocio",
        "sum(Coste de variación de precio)",
        "Sample",
        "Categoria Tipo de Compra",
    ]

    columnas_ariba = [
        col for col in columnas_ariba
        if col in ariba.columns
    ]

    candidatos = me5a.merge(
        ariba[columnas_ariba],
        left_on="_solicitud_norm",
        right_on="_id_erp_norm",
        how="left",
        suffixes=("_me5a", "_ariba"),
    )

    candidatos["_match_ariba_solicitud"] = (
        candidatos["_solicitud_norm"].fillna("")
        .eq(candidatos["_id_erp_norm"].fillna(""))
    )

    candidatos["_match_ariba_linea"] = np.isclose(
        pd.to_numeric(candidatos["_linea_esperada_ariba"], errors="coerce"),
        pd.to_numeric(candidatos["_linea_ariba_num"], errors="coerce"),
        equal_nan=False,
    )

    candidatos["_match_ariba_pedido"] = (
        candidatos["_pedido_norm"].fillna("")
        .eq(candidatos["_id_pedido_norm"].fillna(""))
    )

    candidatos["_match_ariba_estricto"] = (
        candidatos["_match_ariba_solicitud"]
        & candidatos["_match_ariba_linea"]
        & candidatos["_match_ariba_pedido"]
    )

    columnas_bool = [
        "_match_ariba_solicitud",
        "_match_ariba_linea",
        "_match_ariba_pedido",
        "_match_ariba_estricto",
    ]

    candidatos = limpiar_booleanos(candidatos, columnas_bool)

    candidatos["_prioridad_match_ariba"] = np.where(
        candidatos["_match_ariba_estricto"],
        1,
        0,
    )

    candidatos["_coincidencias_ariba"] = (
        candidatos["_match_ariba_solicitud"].astype(int)
        + candidatos["_match_ariba_linea"].astype(int)
        + candidatos["_match_ariba_pedido"].astype(int)
    )

    idx_mejor = (
        candidatos
        .sort_values(
            by=[
                "_prioridad_match_ariba",
                "_coincidencias_ariba",
            ],
            ascending=[False, False],
        )
        .groupby("_id_me5a", dropna=False)["_coincidencias_ariba"]
        .idxmax()
    )

    mejor = candidatos.loc[idx_mejor].copy()

    columnas_resultado = [
        "_id_me5a",
        "_match_ariba_solicitud",
        "_match_ariba_linea",
        "_match_ariba_pedido",
        "_match_ariba_estricto",
        "Tipo de Compra",
        "ID de solicitud de compra",
        "ID de solicitud de compra del ERP",
        "Número de línea de la solicitud de compra",
        "Descripción",
        "Fecha de la solicitud de compra",
        "Fecha de aprobación",
        "ID de pedido",
        "Proveedor - Proveedor de ERP",
        "Centro de costes - ID de centro de costes",
        "Centro de costes - Centro de costes",
        "ID de cuenta",
        "Cuenta",
        "ID de unidad de negocio",
        "sum(Coste de variación de precio)",
        "Sample",
        "Categoria Tipo de Compra",
    ]

    columnas_resultado = [
        col for col in columnas_resultado
        if col in mejor.columns
    ]

    resultado = mejor[columnas_resultado].copy()

    resultado = resultado.rename(
        columns={
            "Tipo de Compra": "ariba_tipo_compra",
            "ID de solicitud de compra": "ariba_id_solicitud_compra",
            "ID de solicitud de compra del ERP": "ariba_solicitud_compra_erp",
            "Número de línea de la solicitud de compra": "ariba_linea_solicitud_compra",
            "Descripción": "ariba_descripcion",
            "Fecha de la solicitud de compra": "ariba_fecha_solicitud_compra",
            "Fecha de aprobación": "ariba_fecha_aprobacion",
            "ID de pedido": "ariba_id_pedido",
            "Proveedor - Proveedor de ERP": "ariba_proveedor_erp",
            "Centro de costes - ID de centro de costes": "ariba_id_centro_costes",
            "Centro de costes - Centro de costes": "ariba_centro_costes",
            "ID de cuenta": "ariba_id_cuenta",
            "Cuenta": "ariba_cuenta",
            "ID de unidad de negocio": "ariba_id_unidad_negocio",
            "sum(Coste de variación de precio)": "ariba_coste_variacion_precio",
            "Sample": "ariba_sample",
            "Categoria Tipo de Compra": "ariba_categoria_tipo_compra",
        }
    )

    return resultado


# ============================================================
# Construcción de match final
# ============================================================

@st.cache_data(show_spinner=False)
def construir_match_final(
    df_me5a: pd.DataFrame,
    df_ariba: pd.DataFrame,
    df_me80fn: pd.DataFrame,
) -> pd.DataFrame:

    me5a = limpiar_nombres_columnas(df_me5a).copy()
    me5a["_id_me5a"] = range(len(me5a))

    match_ariba = match_me5a_ariba(me5a, df_ariba)
    match_me80fn = match_me5a_me80fn(me5a, df_me80fn)

    resultado = me5a.merge(
        match_ariba,
        on="_id_me5a",
        how="left",
    )

    resultado = resultado.merge(
        match_me80fn,
        on="_id_me5a",
        how="left",
    )

    columnas_bool = [
        "_match_ariba_solicitud",
        "_match_ariba_linea",
        "_match_ariba_pedido",
        "_match_ariba_estricto",
        "_match_me80fn_pedido_documento",
        "_match_me80fn_posicion",
        "_match_me80fn_material",
        "_match_me80fn_centro",
        "_match_me80fn_estricto",
    ]

    resultado = limpiar_booleanos(resultado, columnas_bool)

    resultado["match_ariba_encontrado"] = resultado["_match_ariba_estricto"]
    resultado["match_me80fn_encontrado"] = resultado["_match_me80fn_estricto"]

    resultado["estado_match"] = np.select(
        [
            resultado["match_ariba_encontrado"] & resultado["match_me80fn_encontrado"],
            resultado["match_ariba_encontrado"] & ~resultado["match_me80fn_encontrado"],
            ~resultado["match_ariba_encontrado"] & resultado["match_me80fn_encontrado"],
        ],
        [
            "Encontrado en ARIBA y ME80FN",
            "Encontrado solo en ARIBA",
            "Encontrado solo en ME80FN",
        ],
        default="No encontrado en ARIBA ni ME80FN",
    )

    return resultado


# ============================================================
# Nombres finales para exportación
# ============================================================

COLUMNAS_EXPORTACION = {
    "estado_match": "Estado del match",
    "match_ariba_encontrado": "Match encontrado - ARIBA",
    "match_me80fn_encontrado": "Match encontrado - ME80FN",

    "_match_ariba_solicitud": "Coincide solicitud - ARIBA",
    "_match_ariba_linea": "Coincide línea - ARIBA",
    "_match_ariba_pedido": "Coincide pedido - ARIBA",
    "_match_ariba_estricto": "Match estricto - ARIBA",

    "_match_me80fn_pedido_documento": "Coincide pedido/documento - ME80FN",
    "_match_me80fn_posicion": "Coincide posición - ME80FN",
    "_match_me80fn_material": "Coincide material - ME80FN",
    "_match_me80fn_centro": "Coincide centro - ME80FN",
    "_match_me80fn_estricto": "Match estricto - ME80FN",

    "Solicitud de pedido": "Solicitud de pedido - ME5A",
    "Pos.solicitud pedido": "Posición solicitud de pedido - ME5A",
    "Pedido": "Pedido - ME5A",
    "Posición de pedido": "Posición de pedido - ME5A",
    "Material": "Material - ME5A",
    "Texto breve": "Texto breve - ME5A",
    "Cantidad solicitada": "Cantidad solicitada - ME5A",
    "Unidad de medida": "Unidad de medida - ME5A",
    "Moneda": "Moneda - ME5A",
    "Centro": "Centro - ME5A",
    "Fecha de solicitud": "Fecha de solicitud - ME5A",
    "Fe.liber.Z": "Fecha de liberación - ME5A",
    "Fecha de pedido": "Fecha de pedido - ME5A",
    "Fecha de entrega": "Fecha de entrega - ME5A",

    "ariba_tipo_compra": "Tipo de compra - ARIBA",
    "ariba_id_solicitud_compra": "ID solicitud de compra - ARIBA",
    "ariba_solicitud_compra_erp": "Solicitud de compra ERP - ARIBA",
    "ariba_linea_solicitud_compra": "Línea solicitud de compra - ARIBA",
    "ariba_descripcion": "Descripción - ARIBA",
    "ariba_fecha_solicitud_compra": "Fecha solicitud de compra - ARIBA",
    "ariba_fecha_aprobacion": "Fecha de aprobación - ARIBA",
    "ariba_id_pedido": "ID pedido - ARIBA",
    "ariba_proveedor_erp": "Proveedor ERP - ARIBA",
    "ariba_id_centro_costes": "ID centro de costes - ARIBA",
    "ariba_centro_costes": "Centro de costes - ARIBA",
    "ariba_id_cuenta": "ID cuenta - ARIBA",
    "ariba_cuenta": "Cuenta - ARIBA",
    "ariba_id_unidad_negocio": "Unidad de negocio - ARIBA",
    "ariba_coste_variacion_precio": "Coste variación precio - ARIBA",
    "ariba_sample": "Sample - ARIBA",
    "ariba_categoria_tipo_compra": "Categoría tipo de compra - ARIBA",

    "me80fn_documento_compras": "Documento de compras - ME80FN",
    "me80fn_posicion": "Posición - ME80FN",
    "me80fn_centro": "Centro - ME80FN",
    "me80fn_fecha_entrada": "Fecha de entrada - ME80FN",
    "me80fn_material": "Material - ME80FN",
    "me80fn_texto_breve": "Texto breve - ME80FN",
    "me80fn_cantidad": "Cantidad - ME80FN",
    "me80fn_unidad_medida_pedido": "Unidad medida pedido - ME80FN",
    "me80fn_importe_moneda_local": "Importe moneda local - ME80FN",
    "me80fn_moneda": "Moneda - ME80FN",
    "me80fn_importe": "Importe - ME80FN",
    "me80fn_clase_operacion": "Clase de operación - ME80FN",
    "me80fn_fecha_documento": "Fecha de documento - ME80FN",
    "me80fn_fecha_contabilizacion": "Fecha contabilización - ME80FN",
    "me80fn_fecha_facturacion_proveedor": "Fecha facturación proveedor - ME80FN",
    "me80fn_fecha_recepcion_mercancia": "Fecha recepción mercancía - ME80FN",
}


def preparar_resultado_exportacion(df: pd.DataFrame) -> pd.DataFrame:
    df_export = df.copy()

    columnas_no_exportar = [
        "score_ariba",
        "score_me80fn",
        "score_total_integrado",
    ]

    df_export = df_export.drop(
        columns=[
            col for col in columnas_no_exportar
            if col in df_export.columns
        ],
        errors="ignore",
    )

    columnas_renombrar = {
        col: nuevo_nombre
        for col, nuevo_nombre in COLUMNAS_EXPORTACION.items()
        if col in df_export.columns
    }

    df_export = df_export.rename(columns=columnas_renombrar)

    return df_export


# ============================================================
# Resumen
# ============================================================

def generar_resumen(resultado_final: pd.DataFrame) -> pd.DataFrame:
    total = int(len(resultado_final))

    if total == 0:
        return pd.DataFrame(
            columns=[
                "Mensaje",
                "Cantidad",
                "%",
            ]
        )

    cantidad_ariba = int(resultado_final["match_ariba_encontrado"].sum())
    cantidad_me80fn = int(resultado_final["match_me80fn_encontrado"].sum())

    cantidad_ambos = int(
        resultado_final["estado_match"].eq("Encontrado en ARIBA y ME80FN").sum()
    )

    cantidad_solo_ariba = int(
        resultado_final["estado_match"].eq("Encontrado solo en ARIBA").sum()
    )

    cantidad_solo_me80fn = int(
        resultado_final["estado_match"].eq("Encontrado solo en ME80FN").sum()
    )

    cantidad_no_encontrado = int(
        resultado_final["estado_match"].eq("No encontrado en ARIBA ni ME80FN").sum()
    )

    registros = [
        {
            "Mensaje": f"{cantidad_ariba:,} registros de {total:,} en ME5A fueron encontrados en ARIBA",
            "Cantidad": cantidad_ariba,
        },
        {
            "Mensaje": f"{cantidad_me80fn:,} registros de {total:,} en ME5A fueron encontrados en ME80FN",
            "Cantidad": cantidad_me80fn,
        },
        {
            "Mensaje": f"{cantidad_ambos:,} registros de {total:,} en ME5A fueron encontrados en ARIBA y ME80FN",
            "Cantidad": cantidad_ambos,
        },
        {
            "Mensaje": f"{cantidad_solo_ariba:,} registros de {total:,} en ME5A fueron encontrados solo en ARIBA",
            "Cantidad": cantidad_solo_ariba,
        },
        {
            "Mensaje": f"{cantidad_solo_me80fn:,} registros de {total:,} en ME5A fueron encontrados solo en ME80FN",
            "Cantidad": cantidad_solo_me80fn,
        },
        {
            "Mensaje": f"{cantidad_no_encontrado:,} registros de {total:,} en ME5A no fueron encontrados en ARIBA ni ME80FN",
            "Cantidad": cantidad_no_encontrado,
        },
    ]

    resumen = pd.DataFrame(registros)
    resumen["%"] = (resumen["Cantidad"] / total * 100).round(2)

    return resumen


# ============================================================
# Mensaje de cambios y lógica del match
# ============================================================

def generar_resumen_cambios_match(
    df_me5a: pd.DataFrame,
    df_ariba: pd.DataFrame,
    df_me80fn: pd.DataFrame,
    resultado_final: pd.DataFrame,
) -> dict:

    total_me5a = int(len(df_me5a))
    total_ariba = int(len(df_ariba))
    total_me80fn = int(len(df_me80fn))
    total_resultado = int(len(resultado_final))

    match_ariba = (
        int(resultado_final["match_ariba_encontrado"].sum())
        if "match_ariba_encontrado" in resultado_final.columns
        else 0
    )

    match_me80fn = (
        int(resultado_final["match_me80fn_encontrado"].sum())
        if "match_me80fn_encontrado" in resultado_final.columns
        else 0
    )

    no_encontrado = (
        int(resultado_final["estado_match"].eq("No encontrado en ARIBA ni ME80FN").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_ambos = (
        int(resultado_final["estado_match"].eq("Encontrado en ARIBA y ME80FN").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_solo_ariba = (
        int(resultado_final["estado_match"].eq("Encontrado solo en ARIBA").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_solo_me80fn = (
        int(resultado_final["estado_match"].eq("Encontrado solo en ME80FN").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    columnas_resultado = int(len(resultado_final.columns))
    duplicados_resultado = int(resultado_final.duplicated().sum())

    ejemplo_match_ambos = None

    if "estado_match" in resultado_final.columns:
        ejemplo_df = resultado_final[
            resultado_final["estado_match"].eq("Encontrado en ARIBA y ME80FN")
        ]

        if not ejemplo_df.empty:
            ejemplo_match_ambos = ejemplo_df.iloc[0].to_dict()

    return {
        "total_me5a": total_me5a,
        "total_ariba": total_ariba,
        "total_me80fn": total_me80fn,
        "total_resultado": total_resultado,
        "match_ariba": match_ariba,
        "match_me80fn": match_me80fn,
        "no_encontrado": no_encontrado,
        "match_ambos": match_ambos,
        "match_solo_ariba": match_solo_ariba,
        "match_solo_me80fn": match_solo_me80fn,
        "columnas_resultado": columnas_resultado,
        "duplicados_resultado": duplicados_resultado,
        "ejemplo_match_ambos": ejemplo_match_ambos,
    }


def generar_texto_ejemplo_match(ejemplo: dict) -> str:
    if not ejemplo:
        return """
### Ejemplo de lógica del match

No se encontró ningún caso con match simultáneo en ARIBA y ME80FN para mostrar como ejemplo.
"""

    pos_solicitud = formatear_valor(
        ejemplo.get("Pos.solicitud pedido", "")
    )

    return f"""
### Ejemplo de lógica del match

Se tomó un registro de ME5A que fue encontrado tanto en ARIBA como en ME80FN.

**Validación ARIBA**

- Solicitud de pedido ME5A: **{formatear_valor(ejemplo.get('Solicitud de pedido', ''))}**.
- Solicitud ERP ARIBA: **{formatear_valor(ejemplo.get('ariba_solicitud_compra_erp', ''))}**.
- Posición solicitud ME5A / 10: **{pos_solicitud} / 10**.
- Línea ARIBA: **{formatear_valor(ejemplo.get('ariba_linea_solicitud_compra', ''))}**.
- Pedido ME5A: **{formatear_valor(ejemplo.get('Pedido', ''))}**.
- Pedido ARIBA: **{formatear_valor(ejemplo.get('ariba_id_pedido', ''))}**.

Resultado: el registro cumple las condiciones de solicitud, línea y pedido, por eso fue encontrado en ARIBA.

**Validación ME80FN**

- Pedido ME5A: **{formatear_valor(ejemplo.get('Pedido', ''))}**.
- Documento compras ME80FN: **{formatear_valor(ejemplo.get('me80fn_documento_compras', ''))}**.
- Posición pedido ME5A: **{formatear_valor(ejemplo.get('Posición de pedido', ''))}**.
- Posición ME80FN: **{formatear_valor(ejemplo.get('me80fn_posicion', ''))}**.
- Material ME5A: **{formatear_valor(ejemplo.get('Material', ''))}**.
- Material ME80FN: **{formatear_valor(ejemplo.get('me80fn_material', ''))}**.
- Centro ME5A: **{formatear_valor(ejemplo.get('Centro', ''))}**.
- Centro ME80FN: **{formatear_valor(ejemplo.get('me80fn_centro', ''))}**.

Resultado: el registro cumple las condiciones de pedido, posición, material y centro, por eso fue encontrado en ME80FN.
"""


def mostrar_resumen_cambios_match(resumen_cambios: dict):
    ejemplo = resumen_cambios.get("ejemplo_match_ambos")
    texto_ejemplo = generar_texto_ejemplo_match(ejemplo)

    with st.expander("Cambios realizados y lógica del match", expanded=False):
        st.markdown(
            f"""
### Archivos cargados

- Se cargaron **{resumen_cambios['total_me5a']:,} registros** de ME5A.
- Se cargaron **{resumen_cambios['total_ariba']:,} registros** de ARIBA.
- Se cargaron **{resumen_cambios['total_me80fn']:,} registros** de ME80FN.

### Resultado del match con AND estricto

- **{resumen_cambios['match_ariba']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados en ARIBA**.
- **{resumen_cambios['match_me80fn']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados en ME80FN**.
- **{resumen_cambios['match_ambos']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados en ARIBA y ME80FN**.
- **{resumen_cambios['match_solo_ariba']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados solo en ARIBA**.
- **{resumen_cambios['match_solo_me80fn']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados solo en ME80FN**.
- **{resumen_cambios['no_encontrado']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A no fueron encontrados en ARIBA ni ME80FN**.

### Condición ARIBA

Para que un registro tenga match en ARIBA, deben cumplirse las 3 condiciones:

- **Solicitud de pedido - ME5A** = **ID de solicitud de compra del ERP - ARIBA**.
- **Pos.solicitud pedido - ME5A / 10** = **Número de línea de la solicitud de compra - ARIBA**.
- **Pedido - ME5A** = **ID de pedido - ARIBA**.

### Condición ME80FN

Para que un registro tenga match en ME80FN, deben cumplirse las 4 condiciones:

- **Pedido - ME5A** = **Documento compras - ME80FN**.
- **Posición de pedido - ME5A** = **Posición - ME80FN**.
- **Material - ME5A** = **Material - ME80FN**.
- **Centro - ME5A** = **Centro - ME80FN**.

{texto_ejemplo}

### Salida generada

- Se generó una salida integrada con **{resumen_cambios['total_resultado']:,} registros** y **{resumen_cambios['columnas_resultado']:,} columnas**.
- Filas duplicadas detectadas en la salida integrada: **{resumen_cambios['duplicados_resultado']:,}**.
            """
        )


# ============================================================
# Exportación
# Excel eliminado
# ============================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow",
    )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


# ============================================================
# Encabezado
# ============================================================

mostrar_logo()

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">04_MATCH</div>
        <div class="app-subtitle">
            Match integrado ME5A · ARIBA · ME80FN
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Configuración
# ============================================================

with st.expander("Configuración", expanded=False):
    col_conf1, col_conf2 = st.columns(2)

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

    st.caption("El separador solo aplica a archivos CSV.")


# ============================================================
# Paso 1: cargar los 3 archivos
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">1. Cargar archivos</h4>
        <p class="small-muted">
            Carga de una sola vez los 3 archivos limpios: ME5A, ARIBA y ME80FN.
            Se aceptan formatos Parquet, Excel o CSV.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

archivos_cargados = st.file_uploader(
    "Selecciona los 3 archivos",
    type=[
        "parquet",
        "xlsx",
        "csv",
    ],
    accept_multiple_files=True,
    label_visibility="collapsed",
)

if not archivos_cargados:
    st.info("Carga los archivos ME5A, ARIBA y ME80FN para iniciar el match.")
    st.stop()

if len(archivos_cargados) < 3:
    st.warning(
        f"Se cargaron {len(archivos_cargados)} archivo(s). "
        "Debes cargar los 3 archivos: ME5A, ARIBA y ME80FN."
    )
    st.stop()


deteccion = detectar_archivos_cargados(archivos_cargados)
archivos_detectados = deteccion["detectados"]
conflictos = deteccion["conflictos"]

if conflictos:
    st.warning(
        "Se detectaron archivos duplicados para: "
        + ", ".join(sorted(set(conflictos)))
        + ". Revisa los nombres o asigna manualmente."
    )

if archivos_completos(archivos_detectados) and not conflictos:
    archivo_me5a = archivos_detectados["ME5A"]
    archivo_ariba = archivos_detectados["ARIBA"]
    archivo_me80fn = archivos_detectados["ME80FN"]

    st.success(
        "Archivos detectados correctamente: "
        f"ME5A = {archivo_me5a.name}, "
        f"ARIBA = {archivo_ariba.name}, "
        f"ME80FN = {archivo_me80fn.name}."
    )

else:
    st.warning(
        "No fue posible detectar automáticamente los 3 archivos. "
        "Asigna cada archivo manualmente."
    )

    nombres_archivos = [
        archivo.name for archivo in archivos_cargados
    ]

    opciones = ["-- Seleccionar --"] + nombres_archivos

    def indice_detectado(tipo: str) -> int:
        archivo = archivos_detectados.get(tipo)

        if archivo is None:
            return 0

        if archivo.name in nombres_archivos:
            return opciones.index(archivo.name)

        return 0

    col_asig1, col_asig2, col_asig3 = st.columns(3)

    with col_asig1:
        nombre_me5a = st.selectbox(
            "Archivo ME5A",
            options=opciones,
            index=indice_detectado("ME5A"),
        )

    with col_asig2:
        nombre_ariba = st.selectbox(
            "Archivo ARIBA",
            options=opciones,
            index=indice_detectado("ARIBA"),
        )

    with col_asig3:
        nombre_me80fn = st.selectbox(
            "Archivo ME80FN",
            options=opciones,
            index=indice_detectado("ME80FN"),
        )

    seleccionados = [
        nombre_me5a,
        nombre_ariba,
        nombre_me80fn,
    ]

    if "-- Seleccionar --" in seleccionados:
        st.info("Asigna los 3 archivos para continuar.")
        st.stop()

    if len(set(seleccionados)) < 3:
        st.error("Cada tipo debe tener un archivo distinto.")
        st.stop()

    archivos_por_nombre = {
        archivo.name: archivo
        for archivo in archivos_cargados
    }

    archivo_me5a = archivos_por_nombre[nombre_me5a]
    archivo_ariba = archivos_por_nombre[nombre_ariba]
    archivo_me80fn = archivos_por_nombre[nombre_me80fn]


# ============================================================
# Paso 2: procesamiento
# ============================================================

try:
    bytes_me5a = archivo_me5a.getvalue()
    bytes_ariba = archivo_ariba.getvalue()
    bytes_me80fn = archivo_me80fn.getvalue()

    firma_archivos = (
        f"{archivo_me5a.name}_{len(bytes_me5a)}_"
        f"{archivo_ariba.name}_{len(bytes_ariba)}_"
        f"{archivo_me80fn.name}_{len(bytes_me80fn)}_"
        f"{separador_csv}"
    )

    with st.spinner("Leyendo archivos..."):
        df_me5a = leer_archivo_cache(
            bytes_archivo=bytes_me5a,
            nombre_archivo=archivo_me5a.name,
            separador_csv=separador_csv,
        )

        df_ariba = leer_archivo_cache(
            bytes_archivo=bytes_ariba,
            nombre_archivo=archivo_ariba.name,
            separador_csv=separador_csv,
        )

        df_me80fn = leer_archivo_cache(
            bytes_archivo=bytes_me80fn,
            nombre_archivo=archivo_me80fn.name,
            separador_csv=separador_csv,
        )

    with st.spinner("Generando match integrado..."):
        resultado_final = construir_match_final(
            df_me5a=df_me5a,
            df_ariba=df_ariba,
            df_me80fn=df_me80fn,
        )

        resumen = generar_resumen(resultado_final)

        resultado_exportacion = preparar_resultado_exportacion(
            resultado_final
        )

        nombre_parquet = generar_nombre_salida("parquet")
        nombre_csv = generar_nombre_salida("csv")

        resumen_cambios = generar_resumen_cambios_match(
            df_me5a=df_me5a,
            df_ariba=df_ariba,
            df_me80fn=df_me80fn,
            resultado_final=resultado_final,
        )

except Exception as e:
    st.error("No se pudo generar el match.")
    st.exception(e)
    st.stop()


st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">2. Match generado</h4>
        <p class="small-muted">
            El cruce ME5A, ARIBA y ME80FN fue ejecutado correctamente.
            El archivo de salida ya está listo.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.success("Match generado correctamente.")
st.caption(
    "Versión anti-crash: el archivo Parquet y el CSV se generan solo bajo demanda, "
    "evitando preparar descargas pesadas automáticamente en cada ejecución."
)


# ============================================================
# Indicadores
# ============================================================

total_me5a = len(df_me5a)
total_resultado = len(resultado_final)
total_ariba_match = int(resultado_final["match_ariba_encontrado"].sum())
total_me80fn_match = int(resultado_final["match_me80fn_encontrado"].sum())

col1, col2, col3, col4 = st.columns(4)

col1.metric("Registros ME5A", f"{total_me5a:,}")
col2.metric("Resultado integrado", f"{total_resultado:,}")
col3.metric("Encontrados en ARIBA", f"{total_ariba_match:,}")
col4.metric("Encontrados en ME80FN", f"{total_me80fn_match:,}")


# ============================================================
# Paso 3: descarga principal
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">3. Descargar resultado integrado</h4>
        <p class="small-muted">
            El formato principal de salida es Parquet.
            El nombre del archivo incluye fecha, hora y la palabra MATCH.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

preparar_parquet = st.button(
    "Preparar Parquet",
    use_container_width=True,
    type="primary",
    key="match_preparar_parquet_principal",
)

if preparar_parquet:
    with st.spinner("Preparando Parquet..."):
        st.session_state["match_parquet_bytes"] = convertir_a_parquet_cache(
            resultado_exportacion
        )
        st.session_state["match_parquet_firma"] = firma_archivos
        st.session_state["match_parquet_nombre"] = nombre_parquet

if (
    st.session_state.get("match_parquet_bytes") is not None
    and st.session_state.get("match_parquet_firma") == firma_archivos
):
    st.download_button(
        label="Descargar resultado en Parquet",
        data=st.session_state["match_parquet_bytes"],
        file_name=st.session_state["match_parquet_nombre"],
        mime="application/octet-stream",
        type="primary",
        use_container_width=True,
    )
else:
    st.info("Presiona **Preparar Parquet** para generar el archivo de descarga solo cuando lo necesites.")


# ============================================================
# Detalle opcional
# ============================================================

mostrar_resumen_cambios_match(resumen_cambios)

with st.expander("Resumen del match", expanded=False):
    st.dataframe(
        resumen,
        use_container_width=True,
        hide_index=True,
    )


with st.expander("Vista previa de archivos cargados", expanded=False):
    tab_me5a, tab_ariba, tab_me80fn = st.tabs(
        [
            "ME5A",
            "ARIBA",
            "ME80FN",
        ]
    )

    with tab_me5a:
        st.caption(
            f"Filas: {len(df_me5a):,} · Columnas: {len(df_me5a.columns):,}"
        )

        st.dataframe(
            df_me5a.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )

    with tab_ariba:
        st.caption(
            f"Filas: {len(df_ariba):,} · Columnas: {len(df_ariba.columns):,}"
        )

        st.dataframe(
            df_ariba.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )

    with tab_me80fn:
        st.caption(
            f"Filas: {len(df_me80fn):,} · Columnas: {len(df_me80fn.columns):,}"
        )

        st.dataframe(
            df_me80fn.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )


with st.expander("Vista previa del match final", expanded=False):
    st.caption(
        f"Mostrando hasta {int(limite_vista):,} registros de "
        f"{len(resultado_exportacion):,} registros generados en el match final. "
        f"Columnas visibles: {len(resultado_exportacion.columns):,}."
    )

    st.dataframe(
        resultado_exportacion.head(int(limite_vista)),
        use_container_width=True,
        hide_index=True,
    )


with st.expander("Ver columnas disponibles", expanded=False):
    col_c1, col_c2, col_c3, col_c4 = st.columns(4)

    with col_c1:
        st.markdown("**ME5A**")
        st.write(df_me5a.columns.tolist())

    with col_c2:
        st.markdown("**ARIBA**")
        st.write(df_ariba.columns.tolist())

    with col_c3:
        st.markdown("**ME80FN**")
        st.write(df_me80fn.columns.tolist())

    with col_c4:
        st.markdown("**Resultado exportado**")
        st.write(resultado_exportacion.columns.tolist())


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
            st.session_state["match_csv_bytes"] = convertir_a_csv_cache(
                resultado_exportacion
            )
            st.session_state["match_csv_firma"] = firma_archivos
            st.session_state["match_csv_nombre"] = nombre_csv

    if (
        st.session_state.get("match_csv_bytes") is not None
        and st.session_state.get("match_csv_firma") == firma_archivos
    ):
        st.download_button(
            label="Descargar CSV",
            data=st.session_state["match_csv_bytes"],
            file_name=st.session_state["match_csv_nombre"],
            mime="text/csv",
            use_container_width=True,
        )
