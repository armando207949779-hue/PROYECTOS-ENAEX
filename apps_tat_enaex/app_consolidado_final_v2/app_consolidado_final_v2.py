import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# App única: Match Integrado + Performance TAT
# =========================================================

st.set_page_config(
    page_title="Nueva App - Match + Performance TAT",
    page_icon="📊",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"

# =========================================================
# UI común
# =========================================================

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
        unsafe_allow_html=True
    )


# =========================================================
# Funciones generales
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;)":
        return ";"
    if separador_csv == "Coma (,)":
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner=False)
def leer_archivo_cache(
    bytes_archivo: bytes,
    nombre_archivo: str,
    separador_csv: str
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
                on_bad_lines="skip"
            )
        except Exception:
            buffer.seek(0)

            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip"
            )

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def validar_columnas(df: pd.DataFrame, columnas: list, nombre_df: str):
    faltantes = [col for col in columnas if col not in df.columns]

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


# =========================================================
# Match ME5A vs NME80FN
# Criterio AND estricto:
# Pedido + Posición + Material + Centro
# =========================================================

@st.cache_data(show_spinner=False)
def match_me5a_nme80fn(
    df_me5a: pd.DataFrame,
    df_nme: pd.DataFrame
) -> pd.DataFrame:
    me5a = limpiar_nombres_columnas(df_me5a)
    nme = limpiar_nombres_columnas(df_nme)

    validar_columnas(
        me5a,
        [
            "Pedido",
            "Posición de pedido",
            "Material",
            "Centro"
        ],
        "ME5A"
    )

    validar_columnas(
        nme,
        [
            "Documento compras",
            "Posición",
            "Material",
            "Centro"
        ],
        "NME80FN"
    )

    me5a = me5a.copy()
    nme = nme.copy()

    me5a["_id_me5a"] = range(len(me5a))
    nme["_id_nme"] = range(len(nme))

    me5a["_pedido_norm"] = normalizar_entero_str(me5a["Pedido"])
    me5a["_posicion_pedido_norm"] = normalizar_entero_str(me5a["Posición de pedido"])
    me5a["_material_norm"] = normalizar_material(me5a["Material"])
    me5a["_centro_norm"] = me5a["Centro"].astype("string").str.strip()

    nme["_documento_norm"] = normalizar_entero_str(nme["Documento compras"])
    nme["_posicion_norm"] = normalizar_entero_str(nme["Posición"])
    nme["_material_norm"] = normalizar_material(nme["Material"])
    nme["_centro_norm"] = nme["Centro"].astype("string").str.strip()

    columnas_nme = [
        "_id_nme",
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
        "fecha_entrada_mercancia_recepcion"
    ]

    columnas_nme = [col for col in columnas_nme if col in nme.columns]

    candidatos = me5a.merge(
        nme[columnas_nme],
        left_on="_pedido_norm",
        right_on="_documento_norm",
        how="left",
        suffixes=("_me5a", "_nme")
    )

    candidatos["_match_nme_pedido_documento"] = (
        candidatos["_pedido_norm"].fillna("")
        .eq(candidatos["_documento_norm"].fillna(""))
    )

    candidatos["_match_nme_posicion"] = (
        candidatos["_posicion_pedido_norm"].fillna("")
        .eq(candidatos["_posicion_norm"].fillna(""))
    )

    candidatos["_match_nme_material"] = (
        candidatos["_material_norm_me5a"].fillna("")
        .eq(candidatos["_material_norm_nme"].fillna(""))
    )

    candidatos["_match_nme_centro"] = (
        candidatos["_centro_norm_me5a"].fillna("")
        .eq(candidatos["_centro_norm_nme"].fillna(""))
    )

    candidatos["_match_nme_estricto"] = (
        candidatos["_match_nme_pedido_documento"]
        & candidatos["_match_nme_posicion"]
        & candidatos["_match_nme_material"]
        & candidatos["_match_nme_centro"]
    )

    cols_bool_nme = [
        "_match_nme_pedido_documento",
        "_match_nme_posicion",
        "_match_nme_material",
        "_match_nme_centro",
        "_match_nme_estricto"
    ]

    candidatos = limpiar_booleanos(candidatos, cols_bool_nme)

    # Campo auxiliar interno para elegir el mejor candidato.
    # No se muestra ni se exporta.
    candidatos["_prioridad_match_nme"] = np.where(
        candidatos["_match_nme_estricto"],
        1,
        0
    )

    candidatos["_coincidencias_nme"] = (
        candidatos["_match_nme_pedido_documento"].astype(int)
        + candidatos["_match_nme_posicion"].astype(int)
        + candidatos["_match_nme_material"].astype(int)
        + candidatos["_match_nme_centro"].astype(int)
    )

    idx_mejor = (
        candidatos
        .sort_values(
            by=["_prioridad_match_nme", "_coincidencias_nme"],
            ascending=[False, False]
        )
        .groupby("_id_me5a", dropna=False)["_coincidencias_nme"]
        .idxmax()
    )

    mejor = candidatos.loc[idx_mejor].copy()

    columnas_resultado = [
        "_id_me5a",
        "_match_nme_pedido_documento",
        "_match_nme_posicion",
        "_match_nme_material",
        "_match_nme_centro",
        "_match_nme_estricto",
        "Documento compras",
        "Posición",
        "Centro_nme",
        "Fecha de entrada",
        "Material_nme",
        "Texto breve_nme",
        "Cantidad",
        "Unidad medida pedido",
        "Impte.mon.local",
        "Moneda_nme",
        "Importe",
        "Clase de operación",
        "Fecha de documento",
        "Fecha contabiliz.",
        "fecha_facturacion_proveedor",
        "fecha_entrada_mercancia_recepcion"
    ]

    columnas_resultado = [col for col in columnas_resultado if col in mejor.columns]

    resultado = mejor[columnas_resultado].copy()

    resultado = resultado.rename(columns={
        "Documento compras": "nme_documento_compras",
        "Posición": "nme_posicion",
        "Centro_nme": "nme_centro",
        "Fecha de entrada": "nme_fecha_entrada",
        "Material_nme": "nme_material",
        "Texto breve_nme": "nme_texto_breve",
        "Cantidad": "nme_cantidad",
        "Unidad medida pedido": "nme_unidad_medida_pedido",
        "Impte.mon.local": "nme_importe_moneda_local",
        "Moneda_nme": "nme_moneda",
        "Importe": "nme_importe",
        "Clase de operación": "nme_clase_operacion",
        "Fecha de documento": "nme_fecha_documento",
        "Fecha contabiliz.": "nme_fecha_contabilizacion",
        "fecha_facturacion_proveedor": "nme_fecha_facturacion_proveedor",
        "fecha_entrada_mercancia_recepcion": "nme_fecha_recepcion_mercancia"
    })

    return resultado


# =========================================================
# Match ME5A vs ARIBA
# Criterio AND estricto:
# Solicitud + Línea + Pedido
# =========================================================

@st.cache_data(show_spinner=False)
def match_me5a_ariba(
    df_me5a: pd.DataFrame,
    df_ariba: pd.DataFrame
) -> pd.DataFrame:
    me5a = limpiar_nombres_columnas(df_me5a)
    ariba = limpiar_nombres_columnas(df_ariba)

    validar_columnas(
        me5a,
        [
            "Solicitud de pedido",
            "Pos.solicitud pedido",
            "Pedido"
        ],
        "ME5A"
    )

    validar_columnas(
        ariba,
        [
            "ID de solicitud de compra del ERP",
            "Número de línea de la solicitud de compra",
            "ID de pedido"
        ],
        "ARIBA"
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
        "Categoria Tipo de Compra"
    ]

    columnas_ariba = [col for col in columnas_ariba if col in ariba.columns]

    candidatos = me5a.merge(
        ariba[columnas_ariba],
        left_on="_solicitud_norm",
        right_on="_id_erp_norm",
        how="left",
        suffixes=("_me5a", "_ariba")
    )

    candidatos["_match_ariba_solicitud"] = (
        candidatos["_solicitud_norm"].fillna("")
        .eq(candidatos["_id_erp_norm"].fillna(""))
    )

    candidatos["_match_ariba_linea"] = np.isclose(
        pd.to_numeric(candidatos["_linea_esperada_ariba"], errors="coerce"),
        pd.to_numeric(candidatos["_linea_ariba_num"], errors="coerce"),
        equal_nan=False
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

    cols_bool_ariba = [
        "_match_ariba_solicitud",
        "_match_ariba_linea",
        "_match_ariba_pedido",
        "_match_ariba_estricto"
    ]

    candidatos = limpiar_booleanos(candidatos, cols_bool_ariba)

    # Campo auxiliar interno para elegir el mejor candidato.
    # No se muestra ni se exporta.
    candidatos["_prioridad_match_ariba"] = np.where(
        candidatos["_match_ariba_estricto"],
        1,
        0
    )

    candidatos["_coincidencias_ariba"] = (
        candidatos["_match_ariba_solicitud"].astype(int)
        + candidatos["_match_ariba_linea"].astype(int)
        + candidatos["_match_ariba_pedido"].astype(int)
    )

    idx_mejor = (
        candidatos
        .sort_values(
            by=["_prioridad_match_ariba", "_coincidencias_ariba"],
            ascending=[False, False]
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
        "Categoria Tipo de Compra"
    ]

    columnas_resultado = [col for col in columnas_resultado if col in mejor.columns]

    resultado = mejor[columnas_resultado].copy()

    resultado = resultado.rename(columns={
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
        "Categoria Tipo de Compra": "ariba_categoria_tipo_compra"
    })

    return resultado


# =========================================================
# Construcción de match final
# =========================================================

@st.cache_data(show_spinner=False)
def construir_match_final(
    df_me5a: pd.DataFrame,
    df_ariba: pd.DataFrame,
    df_nme: pd.DataFrame
) -> pd.DataFrame:
    me5a = limpiar_nombres_columnas(df_me5a).copy()
    me5a["_id_me5a"] = range(len(me5a))

    match_ariba = match_me5a_ariba(me5a, df_ariba)
    match_nme = match_me5a_nme80fn(me5a, df_nme)

    resultado = me5a.merge(
        match_ariba,
        on="_id_me5a",
        how="left"
    )

    resultado = resultado.merge(
        match_nme,
        on="_id_me5a",
        how="left"
    )

    columnas_bool = [
        "_match_ariba_solicitud",
        "_match_ariba_linea",
        "_match_ariba_pedido",
        "_match_ariba_estricto",
        "_match_nme_pedido_documento",
        "_match_nme_posicion",
        "_match_nme_material",
        "_match_nme_centro",
        "_match_nme_estricto"
    ]

    resultado = limpiar_booleanos(resultado, columnas_bool)

    resultado["match_ariba_encontrado"] = resultado["_match_ariba_estricto"]
    resultado["match_nme80fn_encontrado"] = resultado["_match_nme_estricto"]

    resultado["estado_match"] = np.select(
        [
            resultado["match_ariba_encontrado"] & resultado["match_nme80fn_encontrado"],
            resultado["match_ariba_encontrado"] & ~resultado["match_nme80fn_encontrado"],
            ~resultado["match_ariba_encontrado"] & resultado["match_nme80fn_encontrado"]
        ],
        [
            "Encontrado en ARIBA y NME80FN",
            "Encontrado solo en ARIBA",
            "Encontrado solo en NME80FN"
        ],
        default="No encontrado en ARIBA ni NME80FN"
    )

    return resultado


# =========================================================
# Nombres finales para exportación
# =========================================================

COLUMNAS_EXPORTACION = {
    "estado_match": "Estado del match",
    "match_ariba_encontrado": "Match encontrado - ARIBA",
    "match_nme80fn_encontrado": "Match encontrado - NME80FN",

    "_match_ariba_solicitud": "Coincide solicitud - ARIBA",
    "_match_ariba_linea": "Coincide línea - ARIBA",
    "_match_ariba_pedido": "Coincide pedido - ARIBA",
    "_match_ariba_estricto": "Match estricto - ARIBA",

    "_match_nme_pedido_documento": "Coincide pedido/documento - NME80FN",
    "_match_nme_posicion": "Coincide posición - NME80FN",
    "_match_nme_material": "Coincide material - NME80FN",
    "_match_nme_centro": "Coincide centro - NME80FN",
    "_match_nme_estricto": "Match estricto - NME80FN",

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

    "nme_documento_compras": "Documento de compras - NME80FN",
    "nme_posicion": "Posición - NME80FN",
    "nme_centro": "Centro - NME80FN",
    "nme_fecha_entrada": "Fecha de entrada - NME80FN",
    "nme_material": "Material - NME80FN",
    "nme_texto_breve": "Texto breve - NME80FN",
    "nme_cantidad": "Cantidad - NME80FN",
    "nme_unidad_medida_pedido": "Unidad medida pedido - NME80FN",
    "nme_importe_moneda_local": "Importe moneda local - NME80FN",
    "nme_moneda": "Moneda - NME80FN",
    "nme_importe": "Importe - NME80FN",
    "nme_clase_operacion": "Clase de operación - NME80FN",
    "nme_fecha_documento": "Fecha de documento - NME80FN",
    "nme_fecha_contabilizacion": "Fecha contabilización - NME80FN",
    "nme_fecha_facturacion_proveedor": "Fecha facturación proveedor - NME80FN",
    "nme_fecha_recepcion_mercancia": "Fecha recepción mercancía - NME80FN",
}


def preparar_resultado_exportacion(df: pd.DataFrame) -> pd.DataFrame:
    df_export = df.copy()

    columnas_no_exportar = [
        "score_ariba",
        "score_nme80fn",
        "score_total_integrado"
    ]

    df_export = df_export.drop(
        columns=[col for col in columnas_no_exportar if col in df_export.columns],
        errors="ignore"
    )

    columnas_renombrar = {
        col: nuevo_nombre
        for col, nuevo_nombre in COLUMNAS_EXPORTACION.items()
        if col in df_export.columns
    }

    df_export = df_export.rename(columns=columnas_renombrar)

    return df_export


# =========================================================
# Resumen
# =========================================================

def generar_resumen(resultado_final: pd.DataFrame) -> pd.DataFrame:
    total = int(len(resultado_final))

    if total == 0:
        return pd.DataFrame(
            columns=["Mensaje", "Cantidad", "%"]
        )

    cantidad_ariba = int(resultado_final["match_ariba_encontrado"].sum())
    cantidad_nme = int(resultado_final["match_nme80fn_encontrado"].sum())
    cantidad_ambos = int(
        resultado_final["estado_match"].eq("Encontrado en ARIBA y NME80FN").sum()
    )
    cantidad_solo_ariba = int(
        resultado_final["estado_match"].eq("Encontrado solo en ARIBA").sum()
    )
    cantidad_solo_nme = int(
        resultado_final["estado_match"].eq("Encontrado solo en NME80FN").sum()
    )
    cantidad_no_encontrado = int(
        resultado_final["estado_match"].eq("No encontrado en ARIBA ni NME80FN").sum()
    )

    registros = [
        {
            "Mensaje": f"{cantidad_ariba:,} registros de {total:,} en ME5A fueron encontrados en ARIBA",
            "Cantidad": cantidad_ariba
        },
        {
            "Mensaje": f"{cantidad_nme:,} registros de {total:,} en ME5A fueron encontrados en NME80FN",
            "Cantidad": cantidad_nme
        },
        {
            "Mensaje": f"{cantidad_ambos:,} registros de {total:,} en ME5A fueron encontrados en ARIBA y NME80FN",
            "Cantidad": cantidad_ambos
        },
        {
            "Mensaje": f"{cantidad_solo_ariba:,} registros de {total:,} en ME5A fueron encontrados solo en ARIBA",
            "Cantidad": cantidad_solo_ariba
        },
        {
            "Mensaje": f"{cantidad_solo_nme:,} registros de {total:,} en ME5A fueron encontrados solo en NME80FN",
            "Cantidad": cantidad_solo_nme
        },
        {
            "Mensaje": f"{cantidad_no_encontrado:,} registros de {total:,} en ME5A no fueron encontrados en ARIBA ni NME80FN",
            "Cantidad": cantidad_no_encontrado
        }
    ]

    resumen = pd.DataFrame(registros)
    resumen["%"] = (resumen["Cantidad"] / total * 100).round(2)

    return resumen


# =========================================================
# Mensaje de cambios y lógica del match
# =========================================================

def generar_resumen_cambios_match(
    df_me5a: pd.DataFrame,
    df_ariba: pd.DataFrame,
    df_nme: pd.DataFrame,
    resultado_final: pd.DataFrame
) -> dict:

    total_me5a = int(len(df_me5a))
    total_ariba = int(len(df_ariba))
    total_nme = int(len(df_nme))
    total_resultado = int(len(resultado_final))

    match_ariba = (
        int(resultado_final["match_ariba_encontrado"].sum())
        if "match_ariba_encontrado" in resultado_final.columns
        else 0
    )

    match_nme = (
        int(resultado_final["match_nme80fn_encontrado"].sum())
        if "match_nme80fn_encontrado" in resultado_final.columns
        else 0
    )

    no_encontrado = (
        int(resultado_final["estado_match"].eq("No encontrado en ARIBA ni NME80FN").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_ambos = (
        int(resultado_final["estado_match"].eq("Encontrado en ARIBA y NME80FN").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_solo_ariba = (
        int(resultado_final["estado_match"].eq("Encontrado solo en ARIBA").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_solo_nme = (
        int(resultado_final["estado_match"].eq("Encontrado solo en NME80FN").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    columnas_resultado = int(len(resultado_final.columns))
    duplicados_resultado = int(resultado_final.duplicated().sum())

    ejemplo_match_ambos = None

    if "estado_match" in resultado_final.columns:
        ejemplo_df = resultado_final[
            resultado_final["estado_match"].eq("Encontrado en ARIBA y NME80FN")
        ]

        if not ejemplo_df.empty:
            ejemplo_match_ambos = ejemplo_df.iloc[0].to_dict()

    return {
        "total_me5a": total_me5a,
        "total_ariba": total_ariba,
        "total_nme": total_nme,
        "total_resultado": total_resultado,
        "match_ariba": match_ariba,
        "match_nme": match_nme,
        "no_encontrado": no_encontrado,
        "match_ambos": match_ambos,
        "match_solo_ariba": match_solo_ariba,
        "match_solo_nme": match_solo_nme,
        "columnas_resultado": columnas_resultado,
        "duplicados_resultado": duplicados_resultado,
        "ejemplo_match_ambos": ejemplo_match_ambos
    }


def generar_texto_ejemplo_match(ejemplo: dict) -> str:
    if not ejemplo:
        return """
            **Ejemplo de lógica del match**

            No se encontró ningún caso con match simultáneo en ARIBA y NME80FN para mostrar como ejemplo.
        """

    pos_solicitud = formatear_valor(ejemplo.get("Pos.solicitud pedido", ""))

    return f"""
            **Ejemplo de lógica del match**

            Se tomó un registro de ME5A que fue encontrado tanto en ARIBA como en NME80FN.

            **Validación ARIBA**

            - Solicitud de pedido ME5A: **{formatear_valor(ejemplo.get('Solicitud de pedido', ''))}**.
            - Solicitud ERP ARIBA: **{formatear_valor(ejemplo.get('ariba_solicitud_compra_erp', ''))}**.
            - Posición solicitud ME5A / 10: **{pos_solicitud} / 10**.
            - Línea ARIBA: **{formatear_valor(ejemplo.get('ariba_linea_solicitud_compra', ''))}**.
            - Pedido ME5A: **{formatear_valor(ejemplo.get('Pedido', ''))}**.
            - Pedido ARIBA: **{formatear_valor(ejemplo.get('ariba_id_pedido', ''))}**.

            Resultado: el registro cumple las condiciones de solicitud, línea y pedido, por eso fue encontrado en ARIBA.

            **Validación NME80FN**

            - Pedido ME5A: **{formatear_valor(ejemplo.get('Pedido', ''))}**.
            - Documento compras NME80FN: **{formatear_valor(ejemplo.get('nme_documento_compras', ''))}**.
            - Posición pedido ME5A: **{formatear_valor(ejemplo.get('Posición de pedido', ''))}**.
            - Posición NME80FN: **{formatear_valor(ejemplo.get('nme_posicion', ''))}**.
            - Material ME5A: **{formatear_valor(ejemplo.get('Material', ''))}**.
            - Material NME80FN: **{formatear_valor(ejemplo.get('nme_material', ''))}**.
            - Centro ME5A: **{formatear_valor(ejemplo.get('Centro', ''))}**.
            - Centro NME80FN: **{formatear_valor(ejemplo.get('nme_centro', ''))}**.

            Resultado: el registro cumple las condiciones de pedido, posición, material y centro, por eso fue encontrado en NME80FN.
    """


def mostrar_resumen_cambios_match(resumen_cambios: dict):
    ejemplo = resumen_cambios.get("ejemplo_match_ambos")
    texto_ejemplo = generar_texto_ejemplo_match(ejemplo)

    with st.expander("Cambios realizados y lógica del match", expanded=False):
        st.info(
            f"""
            **Archivos cargados**

            - Se cargaron **{resumen_cambios['total_me5a']:,} registros** de ME5A.
            - Se cargaron **{resumen_cambios['total_ariba']:,} registros** de ARIBA.
            - Se cargaron **{resumen_cambios['total_nme']:,} registros** de NME80FN.

            **Resultado del match con AND estricto**

            - **{resumen_cambios['match_ariba']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados en ARIBA**.
            - **{resumen_cambios['match_nme']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados en NME80FN**.
            - **{resumen_cambios['match_ambos']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados en ARIBA y NME80FN**.
            - **{resumen_cambios['match_solo_ariba']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados solo en ARIBA**.
            - **{resumen_cambios['match_solo_nme']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A fueron encontrados solo en NME80FN**.
            - **{resumen_cambios['no_encontrado']:,} registros de {resumen_cambios['total_me5a']:,} en ME5A no fueron encontrados en ARIBA ni NME80FN**.

            **Condición ARIBA**

            Para que un registro tenga match en ARIBA, deben cumplirse las 3 condiciones:

            - **Solicitud de pedido - ME5A** = **ID de solicitud de compra del ERP - ARIBA**.
            - **Pos.solicitud pedido - ME5A / 10** = **Número de línea de la solicitud de compra - ARIBA**.
            - **Pedido - ME5A** = **ID de pedido - ARIBA**.

            **Condición NME80FN**

            Para que un registro tenga match en NME80FN, deben cumplirse las 4 condiciones:

            - **Pedido - ME5A** = **Documento compras - NME80FN**.
            - **Posición de pedido - ME5A** = **Posición - NME80FN**.
            - **Material - ME5A** = **Material - NME80FN**.
            - **Centro - ME5A** = **Centro - NME80FN**.

            {texto_ejemplo}

            **Salida generada**

            - Se generó una salida integrada con **{resumen_cambios['total_resultado']:,} registros** y **{resumen_cambios['columnas_resultado']:,} columnas**.
            - Filas duplicadas detectadas en la salida integrada: **{resumen_cambios['duplicados_resultado']:,}**.
            """
        )


# =========================================================
# Exportación
# =========================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow"
    )

    return output.getvalue()


def convertir_a_excel(df: pd.DataFrame, resumen: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Match_Final"
        )

        resumen.to_excel(
            writer,
            index=False,
            sheet_name="Resumen"
        )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(df: pd.DataFrame, resumen: pd.DataFrame) -> bytes:
    return convertir_a_excel(df, resumen)




# =========================================================
# Columnas esperadas
# =========================================================

# Fechas finales usadas por el cálculo principal.
COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

# Columnas de origen reales del dataframe integrado.
COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - NME80FN"
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
    # Fechas finales usadas por el cálculo de performance.
    COL_FECHA_SOLICITUD_FINAL,
    COL_FECHA_LIBERACION_FINAL,
    COL_FECHA_PEDIDO_FINAL,
    COL_FECHA_FACTURACION_FINAL,
    COL_FECHA_RECEPCION_FINAL,

    # Fechas de origen ME5A.
    "Fecha de solicitud - ME5A",
    "Fecha modificación",
    "Fecha de liberación - ME5A",
    "Fecha de pedido - ME5A",
    "Fecha de entrega - ME5A",
    "Fecha de liberación",

    # Fechas de origen ARIBA.
    "Fecha solicitud de compra - ARIBA",
    "Fecha de aprobación - ARIBA",

    # Fechas de origen NME80FN.
    "Fecha de entrada - NME80FN",
    "Fecha de documento - NME80FN",
    "Fecha contabilización - NME80FN",
    "Fecha facturación proveedor - NME80FN",
    "Fecha recepción mercancía - NME80FN",

    # Nombres antiguos, por compatibilidad con archivos anteriores.
    "Fecha de solicitud",
    "Fe.liber.Z",
    "Fecha de pedido",
    "Fecha de entrega",
    "ariba_fecha_solicitud_compra",
    "ariba_fecha_aprobacion",
    "nme_fecha_entrada",
    "nme_fecha_documento",
    "nme_fecha_contabiliz",
    "nme_fecha_facturacion_proveedor",
    "nme_fecha_entrada_mercancia_recepcion",
]


# =========================================================
# Columnas nuevas ordenadas
# =========================================================

COLUMNAS_NUEVAS_ORDENADAS = [
    # Clasificación y datos base.
    "tipo_oc",
    "origen",
    "sistema",
    "nombre_tipo_compra",
    "monto",

    # Días calculados.
    "dias_liberacion_solped",
    "dias_comprador",
    "dias_liberacion_pedido",
    "dias_proveedor",
    "dias_logistica",
    "dias_tat_total",

    # Umbrales.
    "umbral_liberacion_solped",
    "umbral_comprador",
    "umbral_liberacion_pedido",
    "umbral_proveedor",
    "umbral_logistica",
    "umbral_tat_total",

    # Performance.
    "performance_liberacion_solped",
    "performance_comprador",
    "performance_liberacion_pedido",
    "performance_proveedor",
    "performance_logistica",
    "performance_tat_total",

    # Validación e incumplimiento.
    "tiene_fechas_inconsistentes",
    "dias_incumplimiento_tat",
    "incumplimiento_tat",
    "rango_incumplimiento_tat",
]


# =========================================================
# UI común
# =========================================================

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
        unsafe_allow_html=True
    )


# =========================================================
# Funciones generales
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv in ["Punto y coma (;)", "Punto y coma (;):"]:
        return ";"
    if separador_csv in ["Coma (,)", "Coma (,):", "Coma (, )"]:
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner=False)
def leer_archivo_cache(
    bytes_archivo: bytes,
    nombre_archivo: str,
    separador_csv: str
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
                on_bad_lines="skip"
            )
        except Exception:
            buffer.seek(0)
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip"
            )

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def validar_columnas_requeridas(df: pd.DataFrame):
    faltantes = [
        col for col in COLUMNAS_REQUERIDAS_PERFORMANCE
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(
            "Faltan columnas requeridas para calcular performance TAT: "
            f"{faltantes}"
        )


def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
    """
    Convierte fechas que pueden venir como:
    - datetime
    - texto de fecha
    - timestamp numérico en milisegundos
    - timestamp numérico en segundos
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
                errors="coerce"
            )

        if mask_s.any():
            resultado.loc[mask_s] = pd.to_datetime(
                serie_num.loc[mask_s],
                unit="s",
                errors="coerce"
            )

    mask_no_num = ~mask_num

    if mask_no_num.any():
        resultado.loc[mask_no_num] = pd.to_datetime(
            serie.loc[mask_no_num],
            errors="coerce",
            dayfirst=True
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
    """
    Calcula días calendario entre dos fechas.
    Fórmula: fecha_fin - fecha_inicio.
    Si falta alguna fecha, el resultado queda vacío.
    """
    return (fecha_fin - fecha_inicio).dt.days


def formatear_valor(valor) -> str:
    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    return str(valor)


# =========================================================
# Evaluaciones de performance
# =========================================================

def evaluar_performance_basica(
    dias: pd.Series,
    umbral: pd.Series,
    texto_sin_dato: str = "No aplica",
    negativos_no_aplican: bool = False
) -> pd.Series:
    """
    Evalúa una métrica simple contra su umbral.

    Reglas:
    - Si no hay días o no hay umbral: texto_sin_dato.
    - Si hay días negativos y negativos_no_aplican=True: No aplica.
    - Recomendado para etapas: usar negativos_no_aplican=True para evitar que días negativos queden como Cumple.
    - Si días <= umbral: Cumple.
    - Si días > umbral: No cumple.
    """
    resultado = pd.Series(texto_sin_dato, index=dias.index, dtype="object")

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
    """
    Evalúa el TAT total según tipo de OC.

    Reglas:
    - Si alguna etapa tiene días negativos: No aplica al análisis.
    - Si TAT total está vacío: En proceso.
    - OC 35 o 45 cumple si TAT <= 40.
    - OC 47 cumple si TAT <= 70.
    - Si es OC 35, 45 o 47 y supera el umbral: No cumple.
    - Otros tipos de OC: Sin datos.
    """
    resultado = pd.Series("Sin datos", index=df.index, dtype="object")

    mask_negativos = df["tiene_fechas_inconsistentes"].eq(True)
    mask_en_proceso = df["dias_tat_total"].isna()

    mask_tipo_nacional = df["tipo_oc"].isin(["35", "45"])
    mask_tipo_internacional = df["tipo_oc"].eq("47")
    mask_tipo_valido = df["tipo_oc"].isin(["35", "45", "47"])

    resultado.loc[mask_negativos] = "No aplica al análisis"
    resultado.loc[~mask_negativos & mask_en_proceso] = "En proceso"

    mask_evaluable = ~mask_negativos & ~mask_en_proceso

    resultado.loc[
        mask_evaluable & mask_tipo_nacional & df["dias_tat_total"].le(40)
    ] = "Cumple"

    resultado.loc[
        mask_evaluable & mask_tipo_internacional & df["dias_tat_total"].le(70)
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
    umbral_tat: pd.Series
) -> pd.Series:
    """
    Calcula días de incumplimiento solo contra el TAT total.

    Reglas:
    - Si no hay TAT o no hay umbral, queda vacío.
    - Si TAT no supera el umbral, queda 0.
    - Si TAT supera el umbral, queda TAT - umbral.
    """
    diferencia = dias_tat - umbral_tat
    resultado = diferencia.where(diferencia > 0, 0)
    resultado = resultado.mask(dias_tat.isna() | umbral_tat.isna(), np.nan)
    return resultado


def calcular_rango_incumplimiento_tat(dias_incumplimiento: pd.Series) -> pd.Series:
    """
    Clasifica los días de incumplimiento TAT.
    """
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
            default="Sin datos"
        ),
        index=dias_incumplimiento.index
    )


# =========================================================
# Tabla conceptual de fórmulas
# =========================================================

def tabla_inputs_formulas() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "Métrica": "Liberación SolPed",
            "Nombre técnico": "dias_liberacion_solped",
            "Fecha inicio": COL_FECHA_SOLICITUD_FINAL,
            "Fecha fin": COL_FECHA_LIBERACION_FINAL,
            "Fórmula": "fecha_liberacion_final - fecha_solicitud_final",
            "Descripción": "Mide los días calendario entre la solicitud y la liberación de la SolPed.",
            "Umbral": "2 días",
            "Resultado esperado": "Cumple si los días son menores o iguales a 2.",
        },
        {
            "Métrica": "Comprador",
            "Nombre técnico": "dias_comprador",
            "Fecha inicio": COL_FECHA_LIBERACION_FINAL,
            "Fecha fin": COL_FECHA_PEDIDO_FINAL,
            "Fórmula": "fecha_pedido_final - fecha_liberacion_final",
            "Descripción": "Mide los días calendario entre la liberación de la SolPed y la creación/emisión del pedido.",
            "Umbral": "10 días",
            "Resultado esperado": "Cumple si los días son menores o iguales a 10.",
        },
        {
            "Métrica": "Liberación Pedido",
            "Nombre técnico": "dias_liberacion_pedido",
            "Fecha inicio": "Sin input disponible",
            "Fecha fin": "Sin input disponible",
            "Fórmula": "Sin cálculo",
            "Descripción": "No se calcula porque actualmente no existe la información necesaria.",
            "Umbral": "2 días",
            "Resultado esperado": "Sin datos.",
        },
        {
            "Métrica": "Proveedor",
            "Nombre técnico": "dias_proveedor",
            "Fecha inicio": COL_FECHA_PEDIDO_FINAL,
            "Fecha fin": COL_FECHA_FACTURACION_FINAL,
            "Fórmula": "fecha_facturacion_final - fecha_pedido_final",
            "Descripción": "Mide los días calendario entre la fecha de pedido y la fecha de facturación.",
            "Umbral": "OC 35/45 = 20 días; OC 47 = 60 días",
            "Resultado esperado": "Cumple si está dentro del umbral correspondiente al tipo de OC.",
        },
        {
            "Métrica": "Logística",
            "Nombre técnico": "dias_logistica",
            "Fecha inicio": COL_FECHA_FACTURACION_FINAL,
            "Fecha fin": COL_FECHA_RECEPCION_FINAL,
            "Fórmula": "fecha_recepcion_final - fecha_facturacion_final",
            "Descripción": "Mide los días calendario entre la facturación y la recepción de mercancía.",
            "Umbral": "11 días",
            "Resultado esperado": "Cumple si los días son menores o iguales a 11. Si el valor es negativo, no aplica.",
        },
        {
            "Métrica": "TAT Total",
            "Nombre técnico": "dias_tat_total",
            "Fecha inicio": COL_FECHA_SOLICITUD_FINAL,
            "Fecha fin": COL_FECHA_RECEPCION_FINAL,
            "Fórmula": "fecha_recepcion_final - fecha_solicitud_final",
            "Descripción": "Mide el ciclo completo punta a punta, desde la solicitud hasta la recepción.",
            "Umbral": "OC 35/45 = 40 días; OC 47 = 70 días",
            "Resultado esperado": "Cumple si está dentro del umbral correspondiente al tipo de OC.",
        },
    ])


# =========================================================
# Lógica principal de performance
# =========================================================

@st.cache_data(show_spinner=False)
def aplicar_logica_performance(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    validar_columnas_requeridas(df)

    # Convertir columnas de fecha.
    for col in COLUMNAS_FECHA_PERFORMANCE:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])

    # =====================================================
    # Tipo de OC
    # 35 = Ariba / Nacional
    # 45 = ERP / Nacional
    # 47 = ERP / Internacional
    # =====================================================

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
        default="Otro"
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
        default="Otro"
    )

    # Tipo de compra ARIBA.
    if COL_TIPO_COMPRA_ARIBA in df.columns:
        tipo_compra_num = pd.to_numeric(df[COL_TIPO_COMPRA_ARIBA], errors="coerce")
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
        default="Otro"
    )

    # Monto.
    if COL_CANTIDAD_SOLICITADA in df.columns and COL_PRECIO_VALORACION in df.columns:
        df["monto"] = (
            pd.to_numeric(df[COL_CANTIDAD_SOLICITADA], errors="coerce")
            * pd.to_numeric(df[COL_PRECIO_VALORACION], errors="coerce")
        )
    else:
        df["monto"] = np.nan

    # =====================================================
    # Cálculos de días
    # =====================================================

    df["dias_liberacion_solped"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_LIBERACION_FINAL],
        fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL]
    )

    df["dias_comprador"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_PEDIDO_FINAL],
        fecha_inicio=df[COL_FECHA_LIBERACION_FINAL]
    )

    # No se calcula porque no hay inputs disponibles.
    df["dias_liberacion_pedido"] = np.nan

    df["dias_proveedor"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_FACTURACION_FINAL],
        fecha_inicio=df[COL_FECHA_PEDIDO_FINAL]
    )

    df["dias_logistica"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
        fecha_inicio=df[COL_FECHA_FACTURACION_FINAL]
    )

    df["dias_tat_total"] = diferencia_dias(
        fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
        fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL]
    )

    # =====================================================
    # Umbrales
    # =====================================================

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
        default=np.nan
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
        default=np.nan
    )

    df["umbral_proveedor"] = pd.to_numeric(
        df["umbral_proveedor"],
        errors="coerce"
    )

    df["umbral_tat_total"] = pd.to_numeric(
        df["umbral_tat_total"],
        errors="coerce"
    )

    # =====================================================
    # Validación de fechas inconsistentes
    # =====================================================

    columnas_dias_evaluables = [
        "dias_liberacion_solped",
        "dias_comprador",
        "dias_liberacion_pedido",
        "dias_proveedor",
        "dias_logistica",
        "dias_tat_total",
    ]

    df["tiene_fechas_inconsistentes"] = (
        df[columnas_dias_evaluables]
        .lt(0)
        .any(axis=1, skipna=True)
    )

    # =====================================================
    # Performance
    # =====================================================

    df["performance_liberacion_solped"] = evaluar_performance_basica(
        dias=df["dias_liberacion_solped"],
        umbral=pd.Series(df["umbral_liberacion_solped"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=True
    )

    df["performance_comprador"] = evaluar_performance_basica(
        dias=df["dias_comprador"],
        umbral=pd.Series(df["umbral_comprador"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=True
    )

    df["performance_liberacion_pedido"] = evaluar_performance_basica(
        dias=pd.Series(df["dias_liberacion_pedido"], index=df.index),
        umbral=pd.Series(df["umbral_liberacion_pedido"], index=df.index),
        texto_sin_dato="Sin datos",
        negativos_no_aplican=True
    )

    df["performance_proveedor"] = evaluar_performance_basica(
        dias=df["dias_proveedor"],
        umbral=df["umbral_proveedor"],
        texto_sin_dato="Sin datos",
        negativos_no_aplican=True
    )

    df["performance_logistica"] = evaluar_performance_basica(
        dias=df["dias_logistica"],
        umbral=pd.Series(df["umbral_logistica"], index=df.index),
        texto_sin_dato="No aplica",
        negativos_no_aplican=True
    )

    df["performance_tat_total"] = evaluar_performance_tat(df)

    # =====================================================
    # Incumplimiento TAT
    # =====================================================

    df["dias_incumplimiento_tat"] = calcular_dias_incumplimiento_tat(
        dias_tat=df["dias_tat_total"],
        umbral_tat=df["umbral_tat_total"]
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


# =========================================================
# Resúmenes
# =========================================================

def resumen_performance(df: pd.DataFrame) -> pd.DataFrame:
    metricas = [
        {
            "columna": "performance_liberacion_solped",
            "metrica": "Liberación SolPed",
            "descripcion": "Tiempo entre solicitud y liberación de la SolPed.",
        },
        {
            "columna": "performance_comprador",
            "metrica": "Comprador",
            "descripcion": "Tiempo entre liberación de SolPed y creación/emisión del pedido.",
        },
        {
            "columna": "performance_liberacion_pedido",
            "metrica": "Liberación Pedido",
            "descripcion": "No se calcula actualmente porque no hay inputs disponibles.",
        },
        {
            "columna": "performance_proveedor",
            "metrica": "Proveedor",
            "descripcion": "Tiempo entre pedido y facturación.",
        },
        {
            "columna": "performance_logistica",
            "metrica": "Logística",
            "descripcion": "Tiempo entre facturación y recepción de mercancía.",
        },
        {
            "columna": "performance_tat_total",
            "metrica": "TAT Total",
            "descripcion": "Tiempo punta a punta desde solicitud hasta recepción.",
        },
    ]

    data = []

    for item in metricas:
        col = item["columna"]

        if col not in df.columns:
            continue

        serie = df[col].astype("object")

        cumple = int(serie.eq("Cumple").sum())
        no_cumple = int(serie.eq("No cumple").sum())
        no_aplica = int(serie.isin(["No aplica", "No aplica al análisis"]).sum())
        sin_datos = int(serie.isin(["Sin datos", "En proceso"]).sum())

        total_evaluable = cumple + no_cumple
        porcentaje_cumple = round((cumple / total_evaluable) * 100, 2) if total_evaluable else 0

        data.append({
            "Métrica": item["metrica"],
            "Descripción": item["descripcion"],
            "Cumple": cumple,
            "No cumple": no_cumple,
            "No aplica": no_aplica,
            "Sin datos / En proceso": sin_datos,
            "% Cumple sobre evaluables": porcentaje_cumple,
        })

    return pd.DataFrame(data)


def resumen_columnas_nuevas(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        col for col in COLUMNAS_NUEVAS_ORDENADAS
        if col in df.columns
    ]

    return pd.DataFrame({
        "Columna nueva": columnas,
        "Nulos": [int(df[col].isna().sum()) for col in columnas],
        "% Nulos": [round(df[col].isna().mean() * 100, 2) for col in columnas],
        "Tipo dato": [str(df[col].dtype) for col in columnas],
    })


def generar_resumen_cambios_performance(
    df_original: pd.DataFrame,
    df_final: pd.DataFrame,
    columnas_originales: list,
    columnas_nuevas: list
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

    ejemplo = None
    if not df_final.empty:
        candidatos = df_final[df_final.get("incumplimiento_tat", False) == True].copy()
        if candidatos.empty:
            candidatos = df_final.copy()
        ejemplo = candidatos.iloc[0].to_dict()

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
        "ejemplo": ejemplo,
    }


def generar_tabla_ejemplo_performance(ejemplo: dict) -> pd.DataFrame:
    if not ejemplo:
        return pd.DataFrame(
            columns=[
                "Métrica",
                "Fecha inicio",
                "Fecha fin",
                "Días calculados",
                "Umbral",
                "Performance",
            ]
        )

    return pd.DataFrame([
        {
            "Métrica": "Liberación SolPed",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_SOLICITUD_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_LIBERACION_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_liberacion_solped")),
            "Umbral": formatear_valor(ejemplo.get("umbral_liberacion_solped")),
            "Performance": formatear_valor(ejemplo.get("performance_liberacion_solped")),
        },
        {
            "Métrica": "Comprador",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_LIBERACION_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_PEDIDO_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_comprador")),
            "Umbral": formatear_valor(ejemplo.get("umbral_comprador")),
            "Performance": formatear_valor(ejemplo.get("performance_comprador")),
        },
        {
            "Métrica": "Liberación Pedido",
            "Fecha inicio": "Sin input",
            "Fecha fin": "Sin input",
            "Días calculados": formatear_valor(ejemplo.get("dias_liberacion_pedido")),
            "Umbral": formatear_valor(ejemplo.get("umbral_liberacion_pedido")),
            "Performance": formatear_valor(ejemplo.get("performance_liberacion_pedido")),
        },
        {
            "Métrica": "Proveedor",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_PEDIDO_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_FACTURACION_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_proveedor")),
            "Umbral": formatear_valor(ejemplo.get("umbral_proveedor")),
            "Performance": formatear_valor(ejemplo.get("performance_proveedor")),
        },
        {
            "Métrica": "Logística",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_FACTURACION_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_logistica")),
            "Umbral": formatear_valor(ejemplo.get("umbral_logistica")),
            "Performance": formatear_valor(ejemplo.get("performance_logistica")),
        },
        {
            "Métrica": "TAT Total",
            "Fecha inicio": formatear_valor(ejemplo.get(COL_FECHA_SOLICITUD_FINAL)),
            "Fecha fin": formatear_valor(ejemplo.get(COL_FECHA_RECEPCION_FINAL)),
            "Días calculados": formatear_valor(ejemplo.get("dias_tat_total")),
            "Umbral": formatear_valor(ejemplo.get("umbral_tat_total")),
            "Performance": formatear_valor(ejemplo.get("performance_tat_total")),
        },
    ])


def mostrar_resumen_cambios_performance(
    resumen_cambios: dict,
    resumen_cols: pd.DataFrame
):
    with st.expander("Cambios realizados y lógica de performance", expanded=True):
        conteo_tipo_oc = resumen_cambios.get("conteo_tipo_oc", {})
        texto_tipo_oc = "\n".join(
            [f"- **{tipo}**: {cantidad:,} registros" for tipo, cantidad in conteo_tipo_oc.items()]
        )

        if not texto_tipo_oc:
            texto_tipo_oc = "- No se pudo generar conteo por tipo de OC."

        st.markdown("### 1. Resumen del archivo procesado")

        st.info(
            f"""
            - Se cargaron **{resumen_cambios['total_original']:,} registros**.
            - El resultado final conserva **{resumen_cambios['total_final']:,} registros**.
            - Se conservaron las columnas originales.
            - Se agregaron **{resumen_cambios['columnas_nuevas']:,} columnas nuevas**.
            - Filas duplicadas detectadas en la salida final: **{resumen_cambios['duplicados_final']:,}**.
            """
        )

        st.markdown("### 2. Inputs utilizados por cada métrica")

        st.caption(
            "Esta tabla permite auditar qué fechas usa cada indicador, cuál es su fórmula y cuál es el umbral aplicado."
        )

        st.dataframe(
            tabla_inputs_formulas(),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 3. Columnas agregadas")

        st.caption(
            "Esta tabla muestra las columnas nuevas creadas por la lógica de performance, "
            "incluyendo cantidad de nulos, porcentaje de nulos y tipo de dato."
        )

        st.dataframe(
            resumen_cols,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### 4. Clasificación de OC")

        st.markdown(
            f"""
            La clasificación se realiza tomando los **dos primeros dígitos** del pedido/documento.

            Primero se intenta usar `{COL_PEDIDO}`.  
            Si esa columna no existe, se usa `{COL_DOCUMENTO_COMPRAS}`.

            | Columna | Lógica |
            |---|---|
            | `tipo_oc` | Dos primeros dígitos del pedido/documento |
            | `origen` | `35` y `45` = Nacional; `47` = Internacional; otros = Otro |
            | `sistema` | `35` = Ariba; `45` y `47` = ERP; otros = Otro |
            | `nombre_tipo_compra` | `1` = Catalogada; `2` = No catalogada; `3` = Directa; otros = Otro |
            | `monto` | Cantidad solicitada multiplicada por precio de valoración |
            """
        )

        st.markdown("### 5. Fórmulas de días calculados")

        st.markdown(
            f"""
            | Métrica | Columna generada | Fórmula aplicada |
            |---|---|---|
            | Liberación SolPed | `dias_liberacion_solped` | `{COL_FECHA_LIBERACION_FINAL} - {COL_FECHA_SOLICITUD_FINAL}` |
            | Comprador | `dias_comprador` | `{COL_FECHA_PEDIDO_FINAL} - {COL_FECHA_LIBERACION_FINAL}` |
            | Liberación Pedido | `dias_liberacion_pedido` | Sin cálculo porque no hay input disponible |
            | Proveedor | `dias_proveedor` | `{COL_FECHA_FACTURACION_FINAL} - {COL_FECHA_PEDIDO_FINAL}` |
            | Logística | `dias_logistica` | `{COL_FECHA_RECEPCION_FINAL} - {COL_FECHA_FACTURACION_FINAL}` |
            | TAT Total | `dias_tat_total` | `{COL_FECHA_RECEPCION_FINAL} - {COL_FECHA_SOLICITUD_FINAL}` |
            """
        )

        st.markdown("### 6. Umbrales aplicados")

        st.markdown(
            """
            | Métrica | Umbral |
            |---|---|
            | Liberación SolPed | 2 días |
            | Comprador | 10 días |
            | Liberación Pedido | 2 días, aunque queda sin datos por falta de input |
            | Proveedor | OC 35/45 = 20 días; OC 47 = 60 días |
            | Logística | 11 días |
            | TAT Total | OC 35/45 = 40 días; OC 47 = 70 días |
            """
        )

        st.markdown("### 7. Reglas de performance")

        st.markdown(
            """
            | Resultado | Significado |
            |---|---|
            | `Cumple` | La métrica tiene datos y está dentro del umbral |
            | `No cumple` | La métrica tiene datos y supera el umbral |
            | `No aplica` | No hay datos suficientes o el cálculo no es válido para esa métrica |
            | `Sin datos` | No existe input suficiente para calcular la métrica |
            | `En proceso` | El TAT Total aún no tiene fecha de recepción |
            | `No aplica al análisis` | Existe alguna fecha inconsistente que genera días negativos |
            """
        )

        st.markdown("### 8. Incumplimiento TAT")

        st.markdown(
            """
            El incumplimiento oficial se calcula usando únicamente el **TAT Total**.

            ```text
            dias_incumplimiento_tat = max(dias_tat_total - umbral_tat_total, 0)
            ```

            | Condición | Rango |
            |---|---|
            | Sin dato suficiente | Sin datos |
            | 0 días de exceso | Sin incumplimiento |
            | 1 a 5 días de exceso | 0-5 días |
            | 6 a 15 días de exceso | 6-15 días |
            | 16 a 30 días de exceso | 16-30 días |
            | Más de 30 días de exceso | Mayor a un mes |
            """
        )

        st.markdown("### 9. Resultado general de incumplimiento TAT")

        st.info(
            f"""
            - Registros con incumplimiento TAT: **{resumen_cambios['incumplimientos_tat']:,}**.
            - Registros sin incumplimiento TAT: **{resumen_cambios['sin_incumplimiento_tat']:,}**.

            **Distribución por tipo de OC**

            {texto_tipo_oc}
            """
        )

        st.markdown("### 10. Ejemplo de cálculo de performance")

        tabla_ejemplo = generar_tabla_ejemplo_performance(
            resumen_cambios.get("ejemplo")
        )

        if tabla_ejemplo.empty:
            st.warning("No se encontró un registro para mostrar como ejemplo.")
        else:
            st.table(tabla_ejemplo)


# =========================================================
# Exportación
# =========================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow"
    )

    return output.getvalue()


def convertir_a_excel(
    df: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame,
    tabla_formulas: pd.DataFrame
) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Performance_TAT"
        )

        resumen_perf.to_excel(
            writer,
            index=False,
            sheet_name="Resumen_Performance"
        )

        resumen_cols.to_excel(
            writer,
            index=False,
            sheet_name="Columnas_Nuevas"
        )

        tabla_formulas.to_excel(
            writer,
            index=False,
            sheet_name="Inputs_Formulas"
        )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(
    df: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame,
    tabla_formulas: pd.DataFrame
) -> bytes:
    return convertir_a_excel(
        df=df,
        resumen_perf=resumen_perf,
        resumen_cols=resumen_cols,
        tabla_formulas=tabla_formulas
    )




# =========================================================
# Helpers app integrada
# =========================================================

def primera_columna_existente(df: pd.DataFrame, columnas: list[str]):
    for col in columnas:
        if col in df.columns:
            return col
    return None


def completar_fechas_finales_para_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea las columnas fecha_*_final si no existen, usando las columnas
    disponibles del resultado integrado.

    La performance TAT usa estas cinco columnas:
    - fecha_solicitud_final
    - fecha_liberacion_final
    - fecha_pedido_final
    - fecha_facturacion_final
    - fecha_recepcion_final
    """
    df = df.copy()

    reglas = {
        COL_FECHA_SOLICITUD_FINAL: [
            "Fecha de solicitud - ME5A",
            "Fecha solicitud de compra - ARIBA",
            "Fecha de solicitud",
        ],
        COL_FECHA_LIBERACION_FINAL: [
            "Fecha de liberación - ME5A",
            "Fecha de aprobación - ARIBA",
            "Fe.liber.Z",
            "Fecha de liberación",
        ],
        COL_FECHA_PEDIDO_FINAL: [
            "Fecha de pedido - ME5A",
            "Fecha de pedido",
            "Fecha de documento - NME80FN",
        ],
        COL_FECHA_FACTURACION_FINAL: [
            "Fecha facturación proveedor - NME80FN",
            "Fecha de documento - NME80FN",
            "nme_fecha_facturacion_proveedor",
        ],
        COL_FECHA_RECEPCION_FINAL: [
            "Fecha recepción mercancía - NME80FN",
            "Fecha de entrada - NME80FN",
            "Fecha contabilización - NME80FN",
            "nme_fecha_entrada_mercancia_recepcion",
        ],
    }

    for col_final, candidatas in reglas.items():
        if col_final not in df.columns:
            col_origen = primera_columna_existente(df, candidatas)
            if col_origen:
                df[col_final] = df[col_origen]
            else:
                df[col_final] = pd.NaT

    return df


def convertir_resultado_integrado_a_excel(
    df_match: pd.DataFrame,
    resumen_match: pd.DataFrame,
    df_performance: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame,
    tabla_formulas_df: pd.DataFrame
) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_match.to_excel(writer, index=False, sheet_name="Match_Final")
        resumen_match.to_excel(writer, index=False, sheet_name="Resumen_Match")
        df_performance.to_excel(writer, index=False, sheet_name="Performance_TAT")
        resumen_perf.to_excel(writer, index=False, sheet_name="Resumen_Performance")
        resumen_cols.to_excel(writer, index=False, sheet_name="Columnas_Nuevas")
        tabla_formulas_df.to_excel(writer, index=False, sheet_name="Inputs_Formulas")

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_resultado_integrado_a_excel_cache(
    df_match: pd.DataFrame,
    resumen_match: pd.DataFrame,
    df_performance: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame,
    tabla_formulas_df: pd.DataFrame
) -> bytes:
    return convertir_resultado_integrado_a_excel(
        df_match=df_match,
        resumen_match=resumen_match,
        df_performance=df_performance,
        resumen_perf=resumen_perf,
        resumen_cols=resumen_cols,
        tabla_formulas_df=tabla_formulas_df
    )


def mostrar_metricas_match(resumen_match: pd.DataFrame):
    if resumen_match.empty:
        return

    cols = st.columns(min(3, len(resumen_match)))

    for i, fila in resumen_match.head(3).iterrows():
        with cols[i % len(cols)]:
            st.metric(
                label=fila["Mensaje"].split(" fueron ")[-1],
                value=f"{int(fila['Cantidad']):,}",
                delta=f"{fila['%']}%"
            )


def mostrar_metricas_performance(resumen_perf: pd.DataFrame):
    if resumen_perf.empty:
        return

    cols = st.columns(min(3, len(resumen_perf)))

    for i, fila in resumen_perf.head(3).iterrows():
        with cols[i % len(cols)]:
            st.metric(
                label=fila["Métrica"],
                value=f"{fila['% Cumple sobre evaluables']}%",
                delta=f"Cumple: {int(fila['Cumple']):,}"
            )


# =========================================================
# Interfaz única
# =========================================================

mostrar_logo()

st.title("Nueva App Integrada")
st.caption("Match ME5A · ARIBA · NME80FN + Performance TAT en un solo flujo")

with st.sidebar:
    st.header("Configuración")

    separador_csv = st.selectbox(
        "Separador CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación"
        ],
        index=0
    )

    limite_vista = st.number_input(
        "Filas en vista previa",
        min_value=50,
        max_value=5000,
        value=300,
        step=50
    )

    ver_vista_previa_archivos = st.checkbox(
        "Ver vista previa de archivos cargados",
        value=False
    )

    st.caption("El separador solo aplica a archivos CSV.")

st.subheader("1. Carga de archivos base")

col1, col2, col3 = st.columns(3)

with col1:
    archivo_me5a = st.file_uploader(
        "ME5A limpio",
        type=["parquet", "xlsx", "csv"],
        key="me5a_integrado"
    )

with col2:
    archivo_ariba = st.file_uploader(
        "ARIBA limpio",
        type=["parquet", "xlsx", "csv"],
        key="ariba_integrado"
    )

with col3:
    archivo_nme = st.file_uploader(
        "NME80FN limpio",
        type=["parquet", "xlsx", "csv"],
        key="nme_integrado"
    )

if not archivo_me5a or not archivo_ariba or not archivo_nme:
    st.info("Carga los tres archivos para ejecutar el match y calcular la performance TAT.")
    st.stop()

try:
    with st.spinner("Leyendo archivos..."):
        df_me5a = leer_archivo_cache(
            archivo_me5a.getvalue(),
            archivo_me5a.name,
            separador_csv
        )

        df_ariba = leer_archivo_cache(
            archivo_ariba.getvalue(),
            archivo_ariba.name,
            separador_csv
        )

        df_nme = leer_archivo_cache(
            archivo_nme.getvalue(),
            archivo_nme.name,
            separador_csv
        )

    df_me5a = limpiar_nombres_columnas(df_me5a)
    df_ariba = limpiar_nombres_columnas(df_ariba)
    df_nme = limpiar_nombres_columnas(df_nme)

    if ver_vista_previa_archivos:
        with st.expander("Vista previa de archivos cargados", expanded=False):
            t1, t2, t3 = st.tabs(["ME5A", "ARIBA", "NME80FN"])

            with t1:
                st.dataframe(df_me5a.head(int(limite_vista)), use_container_width=True)
            with t2:
                st.dataframe(df_ariba.head(int(limite_vista)), use_container_width=True)
            with t3:
                st.dataframe(df_nme.head(int(limite_vista)), use_container_width=True)

    with st.spinner("Generando match integrado..."):
        resultado_match = construir_match_final(
            df_me5a=df_me5a,
            df_ariba=df_ariba,
            df_nme=df_nme
        )

        resultado_match_export = preparar_resultado_exportacion(resultado_match)
        resumen_match = generar_resumen(resultado_match)

    with st.spinner("Preparando fechas finales y calculando Performance TAT..."):
        base_performance = completar_fechas_finales_para_performance(
            resultado_match_export
        )

        resultado_performance = aplicar_logica_performance(base_performance)
        resultado_performance = reordenar_columnas_performance_al_final(
            resultado_performance
        )

        resumen_perf = resumen_performance(resultado_performance)
        columnas_originales = list(base_performance.columns)
        columnas_nuevas = [
            col for col in resultado_performance.columns
            if col not in columnas_originales
        ]
        resumen_cols = resumen_columnas_nuevas(resultado_performance)
        resumen_cambios_perf = generar_resumen_cambios_performance(
            df_original=base_performance,
            df_final=resultado_performance,
            columnas_originales=columnas_originales,
            columnas_nuevas=columnas_nuevas
        )

    st.success("Proceso integrado completado.")

    tab_match, tab_perf, tab_auditoria, tab_descarga = st.tabs(
        [
            "Match integrado",
            "Performance TAT",
            "Auditoría",
            "Descarga"
        ]
    )

    with tab_match:
        st.subheader("2. Resultado del match")
        mostrar_metricas_match(resumen_match)

        st.dataframe(
            resultado_match_export.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True
        )

        with st.expander("Resumen completo del match", expanded=False):
            st.dataframe(resumen_match, use_container_width=True, hide_index=True)

        resumen_cambios_match = generar_resumen_cambios_match(
            df_me5a=df_me5a,
            df_ariba=df_ariba,
            df_nme=df_nme,
            resultado_final=resultado_match
        )
        mostrar_resumen_cambios_match(resumen_cambios_match)

    with tab_perf:
        st.subheader("3. Resultado Performance TAT")
        mostrar_metricas_performance(resumen_perf)

        st.dataframe(
            resultado_performance.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True
        )

        with st.expander("Resumen de performance", expanded=True):
            st.dataframe(resumen_perf, use_container_width=True, hide_index=True)

        mostrar_resumen_cambios_performance(
            resumen_cambios=resumen_cambios_perf,
            resumen_cols=resumen_cols
        )

    with tab_auditoria:
        st.subheader("4. Auditoría de datos")

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Registros ME5A", f"{len(df_me5a):,}")
        col_b.metric("Registros Match", f"{len(resultado_match_export):,}")
        col_c.metric("Registros Performance", f"{len(resultado_performance):,}")

        with st.expander("Columnas finales usadas para Performance TAT", expanded=True):
            columnas_fecha_final = [
                COL_FECHA_SOLICITUD_FINAL,
                COL_FECHA_LIBERACION_FINAL,
                COL_FECHA_PEDIDO_FINAL,
                COL_FECHA_FACTURACION_FINAL,
                COL_FECHA_RECEPCION_FINAL,
            ]
            auditoria_fechas = pd.DataFrame({
                "Columna final": columnas_fecha_final,
                "Existe": [col in resultado_performance.columns for col in columnas_fecha_final],
                "Nulos": [
                    int(resultado_performance[col].isna().sum())
                    if col in resultado_performance.columns else None
                    for col in columnas_fecha_final
                ],
            })
            st.dataframe(auditoria_fechas, use_container_width=True, hide_index=True)

        with st.expander("Filas con fechas inconsistentes", expanded=False):
            if "tiene_fechas_inconsistentes" in resultado_performance.columns:
                df_inconsistentes = resultado_performance[
                    resultado_performance["tiene_fechas_inconsistentes"].eq(True)
                ]
                st.caption(
                    f"Filas con fechas inconsistentes detectadas: {len(df_inconsistentes):,}"
                )
                st.dataframe(
                    df_inconsistentes.head(int(limite_vista)),
                    use_container_width=True,
                    hide_index=True
                )

    with tab_descarga:
        st.subheader("5. Descarga")

        st.markdown("### Descarga principal")
        st.caption("Formato recomendado por defecto: Parquet.")

        parquet_bytes = convertir_a_parquet_cache(resultado_performance)

        st.download_button(
            label="Descargar Parquet Performance TAT",
            data=parquet_bytes,
            file_name="performance_tat_integrado.parquet",
            mime="application/octet-stream",
            use_container_width=True
        )

        st.markdown("### Opciones secundarias")

        col_csv, col_excel = st.columns(2)

        with col_csv:
            csv_bytes = convertir_a_csv_cache(resultado_performance)

            st.download_button(
                label="Descargar CSV Performance TAT",
                data=csv_bytes,
                file_name="performance_tat_integrado.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_excel:
            excel_bytes = convertir_resultado_integrado_a_excel_cache(
                df_match=resultado_match_export,
                resumen_match=resumen_match,
                df_performance=resultado_performance,
                resumen_perf=resumen_perf,
                resumen_cols=resumen_cols,
                tabla_formulas_df=tabla_inputs_formulas()
            )

            st.download_button(
                label="Descargar Excel integrado",
                data=excel_bytes,
                file_name="nueva_app_match_performance_tat.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

except Exception as e:
    st.error("No se pudo ejecutar la app integrada.")
    st.exception(e)
