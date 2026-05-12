import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# Configuración general
# =========================================================

st.set_page_config(
    page_title="Match Integrado",
    page_icon="🔗",
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


# =========================================================
# Match ME5A vs NME80FN
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

    cols_bool_nme = [
        "_match_nme_pedido_documento",
        "_match_nme_posicion",
        "_match_nme_material",
        "_match_nme_centro"
    ]

    candidatos = limpiar_booleanos(candidatos, cols_bool_nme)

    candidatos["score_nme80fn"] = (
        np.where(candidatos["_match_nme_pedido_documento"], 60, 0)
        + np.where(candidatos["_match_nme_posicion"], 25, 0)
        + np.where(candidatos["_match_nme_material"], 20, 0)
        + np.where(candidatos["_match_nme_centro"], 10, 0)
    )

    idx_mejor = (
        candidatos
        .sort_values("score_nme80fn", ascending=False)
        .groupby("_id_me5a", dropna=False)["score_nme80fn"]
        .idxmax()
    )

    mejor = candidatos.loc[idx_mejor].copy()

    columnas_resultado = [
        "_id_me5a",
        "score_nme80fn",
        "_match_nme_pedido_documento",
        "_match_nme_posicion",
        "_match_nme_material",
        "_match_nme_centro",
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

    cols_bool_ariba = [
        "_match_ariba_solicitud",
        "_match_ariba_linea",
        "_match_ariba_pedido"
    ]

    candidatos = limpiar_booleanos(candidatos, cols_bool_ariba)

    candidatos["score_ariba"] = (
        np.where(candidatos["_match_ariba_solicitud"], 60, 0)
        + np.where(candidatos["_match_ariba_linea"], 40, 0)
        + np.where(candidatos["_match_ariba_pedido"], 10, 0)
    )

    idx_mejor = (
        candidatos
        .sort_values("score_ariba", ascending=False)
        .groupby("_id_me5a", dropna=False)["score_ariba"]
        .idxmax()
    )

    mejor = candidatos.loc[idx_mejor].copy()

    columnas_resultado = [
        "_id_me5a",
        "score_ariba",
        "_match_ariba_solicitud",
        "_match_ariba_linea",
        "_match_ariba_pedido",
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

    resultado["score_ariba"] = resultado["score_ariba"].fillna(0)
    resultado["score_nme80fn"] = resultado["score_nme80fn"].fillna(0)

    resultado["match_ariba_encontrado"] = resultado["score_ariba"].gt(0)
    resultado["match_nme80fn_encontrado"] = resultado["score_nme80fn"].gt(0)

    resultado["score_total_integrado"] = (
        resultado["score_ariba"]
        + resultado["score_nme80fn"]
    )

    resultado["estado_match"] = np.select(
        [
            resultado["match_ariba_encontrado"] & resultado["match_nme80fn_encontrado"],
            resultado["match_ariba_encontrado"] & ~resultado["match_nme80fn_encontrado"],
            ~resultado["match_ariba_encontrado"] & resultado["match_nme80fn_encontrado"]
        ],
        [
            "Match en ARIBA y NME80FN",
            "Match solo en ARIBA",
            "Match solo en NME80FN"
        ],
        default="Sin match"
    )

    return resultado


# =========================================================
# Nombres finales para exportación
# =========================================================

COLUMNAS_EXPORTACION = {
    "estado_match": "Estado del match",
    "score_total_integrado": "Puntaje total del match",
    "score_ariba": "Puntaje del match - ARIBA",
    "score_nme80fn": "Puntaje del match - NME80FN",
    "match_ariba_encontrado": "Match encontrado - ARIBA",
    "match_nme80fn_encontrado": "Match encontrado - NME80FN",

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
    resumen = (
        resultado_final["estado_match"]
        .value_counts(dropna=False)
        .reset_index()
    )

    resumen.columns = ["Estado del match", "Cantidad"]

    resumen["%"] = (
        resumen["Cantidad"] / len(resultado_final) * 100
    ).round(2)

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

    sin_match = (
        int(resultado_final["estado_match"].eq("Sin match").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_ambos = (
        int(resultado_final["estado_match"].eq("Match en ARIBA y NME80FN").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_solo_ariba = (
        int(resultado_final["estado_match"].eq("Match solo en ARIBA").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    match_solo_nme = (
        int(resultado_final["estado_match"].eq("Match solo en NME80FN").sum())
        if "estado_match" in resultado_final.columns
        else 0
    )

    columnas_resultado = int(len(resultado_final.columns))
    duplicados_resultado = int(resultado_final.duplicated().sum())

    return {
        "total_me5a": total_me5a,
        "total_ariba": total_ariba,
        "total_nme": total_nme,
        "total_resultado": total_resultado,
        "match_ariba": match_ariba,
        "match_nme": match_nme,
        "sin_match": sin_match,
        "match_ambos": match_ambos,
        "match_solo_ariba": match_solo_ariba,
        "match_solo_nme": match_solo_nme,
        "columnas_resultado": columnas_resultado,
        "duplicados_resultado": duplicados_resultado
    }


def mostrar_resumen_cambios_match(resumen_cambios: dict):
    with st.expander("Cambios realizados y lógica del match", expanded=False):
        st.info(
            f"""
            **Archivos cargados**

            - Se cargaron **{resumen_cambios['total_me5a']:,} registros** de ME5A.
            - Se cargaron **{resumen_cambios['total_ariba']:,} registros** de ARIBA.
            - Se cargaron **{resumen_cambios['total_nme']:,} registros** de NME80FN.

            **Resultado del match**

            - **{resumen_cambios['match_ariba']:,} registros de {resumen_cambios['total_me5a']:,}** se encontraron en **ARIBA**.
            - **{resumen_cambios['match_nme']:,} registros de {resumen_cambios['total_me5a']:,}** se encontraron en **NME80FN**.
            - **{resumen_cambios['match_ambos']:,} registros de {resumen_cambios['total_me5a']:,}** se encontraron en **ARIBA y NME80FN**.
            - **{resumen_cambios['match_solo_ariba']:,} registros de {resumen_cambios['total_me5a']:,}** se encontraron **solo en ARIBA**.
            - **{resumen_cambios['match_solo_nme']:,} registros de {resumen_cambios['total_me5a']:,}** se encontraron **solo en NME80FN**.
            - **{resumen_cambios['sin_match']:,} registros de {resumen_cambios['total_me5a']:,}** no tuvieron match.

            **Columnas usadas para conectar ME5A con ARIBA**

            - **Solicitud de pedido - ME5A** con **ID de solicitud de compra del ERP - ARIBA**.
            - **Pos.solicitud pedido - ME5A / 10** con **Número de línea de la solicitud de compra - ARIBA**.
            - **Pedido - ME5A** con **ID de pedido - ARIBA**.

            **Score ARIBA**

            - **+60 puntos** si coincide **Solicitud de pedido - ME5A** con **ID de solicitud de compra del ERP - ARIBA**.
            - **+40 puntos** si coincide **Pos.solicitud pedido - ME5A / 10** con **Número de línea de la solicitud de compra - ARIBA**.
            - **+10 puntos** si coincide **Pedido - ME5A** con **ID de pedido - ARIBA**.

            **Columnas usadas para conectar ME5A con NME80FN**

            - **Pedido - ME5A** con **Documento compras - NME80FN**.
            - **Posición de pedido - ME5A** con **Posición - NME80FN**.
            - **Material - ME5A** con **Material - NME80FN**.
            - **Centro - ME5A** con **Centro - NME80FN**.

            **Score NME80FN**

            - **+60 puntos** si coincide **Pedido - ME5A** con **Documento compras - NME80FN**.
            - **+25 puntos** si coincide **Posición de pedido - ME5A** con **Posición - NME80FN**.
            - **+20 puntos** si coincide **Material - ME5A** con **Material - NME80FN**.
            - **+10 puntos** si coincide **Centro - ME5A** con **Centro - NME80FN**.

            **Score total integrado**

            - El **Puntaje total del match** corresponde a: **Score ARIBA + Score NME80FN**.
            - Si ambos scores son 0, el registro queda como **Sin match**.

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
# Interfaz
# =========================================================

mostrar_logo()

st.title("Match integrado")
st.caption("ME5A · ARIBA · NME80FN")

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
        max_value=1000,
        value=300,
        step=50
    )

    ver_vista_previa_archivos = st.checkbox(
        "Ver vista previa de archivos cargados",
        value=True
    )

    st.caption("El separador solo aplica a archivos CSV.")


st.subheader("Archivos")

col1, col2, col3 = st.columns(3)

with col1:
    archivo_me5a = st.file_uploader(
        "ME5A limpio",
        type=["parquet", "xlsx", "csv"],
        key="me5a"
    )

with col2:
    archivo_ariba = st.file_uploader(
        "ARIBA limpio",
        type=["parquet", "xlsx", "csv"],
        key="ariba"
    )

with col3:
    archivo_nme = st.file_uploader(
        "NME80FN limpio",
        type=["parquet", "xlsx", "csv"],
        key="nme"
    )


if not archivo_me5a or not archivo_ariba or not archivo_nme:
    st.info("Carga los tres archivos para generar el match.")
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

    if ver_vista_previa_archivos:
        st.subheader("Vista previa de archivos cargados")

        tab_me5a, tab_ariba, tab_nme = st.tabs(
            [
                "ME5A",
                "ARIBA",
                "NME80FN"
            ]
        )

        with tab_me5a:
            st.caption(f"Filas: {len(df_me5a):,} · Columnas: {len(df_me5a.columns):,}")
            st.dataframe(
                df_me5a.head(int(limite_vista)),
                use_container_width=True,
                hide_index=True
            )

        with tab_ariba:
            st.caption(f"Filas: {len(df_ariba):,} · Columnas: {len(df_ariba.columns):,}")
            st.dataframe(
                df_ariba.head(int(limite_vista)),
                use_container_width=True,
                hide_index=True
            )

        with tab_nme:
            st.caption(f"Filas: {len(df_nme):,} · Columnas: {len(df_nme.columns):,}")
            st.dataframe(
                df_nme.head(int(limite_vista)),
                use_container_width=True,
                hide_index=True
            )

    with st.spinner("Generando match integrado..."):
        resultado_final = construir_match_final(
            df_me5a=df_me5a,
            df_ariba=df_ariba,
            df_nme=df_nme
        )

        resumen = generar_resumen(resultado_final)
        resultado_exportacion = preparar_resultado_exportacion(resultado_final)

        parquet_bytes = convertir_a_parquet_cache(resultado_exportacion)

        resumen_cambios = generar_resumen_cambios_match(
            df_me5a=df_me5a,
            df_ariba=df_ariba,
            df_nme=df_nme,
            resultado_final=resultado_final
        )

    st.success("Match generado correctamente.")

    mostrar_resumen_cambios_match(resumen_cambios)

    st.subheader("Indicadores")

    total_me5a = len(df_me5a)
    total_resultado = len(resultado_final)
    total_ariba_match = int(resultado_final["match_ariba_encontrado"].sum())
    total_nme_match = int(resultado_final["match_nme80fn_encontrado"].sum())

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Registros ME5A", f"{total_me5a:,}")
    m2.metric("Resultado integrado", f"{total_resultado:,}")
    m3.metric("Encontrados en ARIBA", f"{total_ariba_match:,} de {total_me5a:,}")
    m4.metric("Encontrados en NME80FN", f"{total_nme_match:,} de {total_me5a:,}")

    st.subheader("Resumen")

    st.dataframe(
        resumen,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Vista previa del match final")

    st.caption(
        f"Mostrando hasta {int(limite_vista):,} registros de "
        f"{len(resultado_exportacion):,} registros generados en el match final. "
        f"Columnas visibles: {len(resultado_exportacion.columns):,}."
    )

    st.dataframe(
        resultado_exportacion.head(int(limite_vista)),
        use_container_width=True,
        hide_index=True
    )

    with st.expander("Ver columnas disponibles"):
        c1, c2, c3, c4 = st.columns(4)

        with c1:
            st.markdown("**ME5A**")
            st.write(df_me5a.columns.tolist())

        with c2:
            st.markdown("**ARIBA**")
            st.write(df_ariba.columns.tolist())

        with c3:
            st.markdown("**NME80FN**")
            st.write(df_nme.columns.tolist())

        with c4:
            st.markdown("**Resultado exportado**")
            st.write(resultado_exportacion.columns.tolist())

    st.subheader("Descarga")

    st.download_button(
        label="Descargar resultado en Parquet",
        data=parquet_bytes,
        file_name="match_integrado_me5a_ariba_nme80fn.parquet",
        mime="application/octet-stream",
        use_container_width=True
    )

    st.caption(
        "Parquet es el formato principal recomendado para conservar tipos de datos "
        "y trabajar con Python. CSV y Excel se preparan solo si los solicitas."
    )

    with st.expander("Opcional: descargar como CSV o Excel"):
        col_csv, col_excel = st.columns(2)

        with col_csv:
            preparar_csv = st.button(
                "Preparar CSV",
                use_container_width=True
            )

            if preparar_csv:
                with st.spinner("Preparando CSV..."):
                    csv_bytes = convertir_a_csv_cache(resultado_exportacion)

                st.download_button(
                    label="Descargar CSV",
                    data=csv_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn.csv",
                    mime="text/csv",
                    use_container_width=True
                )

        with col_excel:
            limite_excel = 250_000

            if len(resultado_exportacion) > limite_excel:
                st.button(
                    "Excel no disponible",
                    disabled=True,
                    use_container_width=True
                )

                st.warning(
                    f"Excel no está disponible porque la salida tiene más de {limite_excel:,} filas. "
                    "Usa Parquet o CSV."
                )
            else:
                preparar_excel = st.button(
                    "Preparar Excel",
                    use_container_width=True
                )

                if preparar_excel:
                    with st.spinner("Preparando Excel..."):
                        excel_bytes = convertir_a_excel_cache(
                            resultado_exportacion,
                            resumen
                        )

                    st.download_button(
                        label="Descargar Excel",
                        data=excel_bytes,
                        file_name="match_integrado_me5a_ariba_nme80fn.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )

except Exception as e:
    st.error("No se pudo generar el match.")
    st.exception(e)
