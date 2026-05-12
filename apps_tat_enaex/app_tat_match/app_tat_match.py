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


@st.cache_data(show_spinner="Leyendo archivo...")
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


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).upper().strip()

    reemplazos = {
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ñ": "N",
    }

    for origen, destino in reemplazos.items():
        texto = texto.replace(origen, destino)

    return " ".join(texto.split())


def limpiar_booleanos(df: pd.DataFrame, columnas: list) -> pd.DataFrame:
    df = df.copy()

    for col in columnas:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)

    return df


# =========================================================
# Match ME5A vs NME80FN
# =========================================================

@st.cache_data(show_spinner="Calculando match ME5A vs NME80FN...")
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
            "Centro",
            "Cantidad solicitada",
            "Unidad de medida",
            "Moneda"
        ],
        "ME5A"
    )

    validar_columnas(
        nme,
        [
            "Documento compras",
            "Posición",
            "Material",
            "Centro",
            "Cantidad",
            "Unidad medida pedido",
            "Moneda"
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
    me5a["_cantidad_norm"] = normalizar_numero(me5a["Cantidad solicitada"])
    me5a["_unidad_norm"] = me5a["Unidad de medida"].astype("string").str.strip()
    me5a["_moneda_norm"] = me5a["Moneda"].astype("string").str.strip()

    nme["_documento_norm"] = normalizar_entero_str(nme["Documento compras"])
    nme["_posicion_norm"] = normalizar_entero_str(nme["Posición"])
    nme["_material_norm"] = normalizar_material(nme["Material"])
    nme["_centro_norm"] = nme["Centro"].astype("string").str.strip()
    nme["_cantidad_norm"] = normalizar_numero(nme["Cantidad"])
    nme["_unidad_norm"] = nme["Unidad medida pedido"].astype("string").str.strip()
    nme["_moneda_norm"] = nme["Moneda"].astype("string").str.strip()

    columnas_nme = [
        "_id_nme",
        "_documento_norm",
        "_posicion_norm",
        "_material_norm",
        "_centro_norm",
        "_cantidad_norm",
        "_unidad_norm",
        "_moneda_norm",
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

    candidatos["_match_nme_cantidad"] = (
        candidatos["_cantidad_norm_me5a"]
        .eq(candidatos["_cantidad_norm_nme"])
        .fillna(False)
    )

    candidatos["_match_nme_unidad"] = (
        candidatos["_unidad_norm_me5a"].fillna("")
        .eq(candidatos["_unidad_norm_nme"].fillna(""))
    )

    candidatos["_match_nme_moneda"] = (
        candidatos["_moneda_norm_me5a"].fillna("")
        .eq(candidatos["_moneda_norm_nme"].fillna(""))
    )

    cols_bool_nme = [
        "_match_nme_pedido_documento",
        "_match_nme_posicion",
        "_match_nme_material",
        "_match_nme_centro",
        "_match_nme_cantidad",
        "_match_nme_unidad",
        "_match_nme_moneda"
    ]

    candidatos = limpiar_booleanos(candidatos, cols_bool_nme)

    candidatos["score_nme80fn"] = (
        np.where(candidatos["_match_nme_pedido_documento"], 60, 0)
        + np.where(candidatos["_match_nme_posicion"], 25, 0)
        + np.where(candidatos["_match_nme_material"], 20, 0)
        + np.where(candidatos["_match_nme_centro"], 10, 0)
        + np.where(candidatos["_match_nme_cantidad"], 10, 0)
        + np.where(candidatos["_match_nme_unidad"], 5, 0)
        + np.where(candidatos["_match_nme_moneda"], 5, 0)
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
        "_match_nme_cantidad",
        "_match_nme_unidad",
        "_match_nme_moneda",
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
        "Impte.mon.local": "nme_impte_mon_local",
        "Moneda_nme": "nme_moneda",
        "Importe": "nme_importe",
        "Clase de operación": "nme_clase_operacion",
        "Fecha de documento": "nme_fecha_documento",
        "Fecha contabiliz.": "nme_fecha_contabiliz",
        "fecha_facturacion_proveedor": "nme_fecha_facturacion_proveedor",
        "fecha_entrada_mercancia_recepcion": "nme_fecha_entrada_mercancia_recepcion"
    })

    return resultado


# =========================================================
# Match ME5A vs ARIBA
# =========================================================

@st.cache_data(show_spinner="Calculando match ME5A vs ARIBA...")
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
            "Texto breve",
            "Pedido",
            "Fecha de solicitud"
        ],
        "ME5A"
    )

    validar_columnas(
        ariba,
        [
            "ID de solicitud de compra del ERP",
            "Número de línea de la solicitud de compra",
            "Descripción",
            "Fecha de la solicitud de compra"
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

    me5a["_texto_me5a_norm"] = me5a["Texto breve"].apply(normalizar_texto)

    me5a["_pedido_norm"] = normalizar_entero_str(
        me5a["Pedido"]
    )

    me5a["_fecha_solicitud_norm"] = pd.to_datetime(
        me5a["Fecha de solicitud"],
        errors="coerce"
    )

    ariba["_id_erp_norm"] = normalizar_entero_str(
        ariba["ID de solicitud de compra del ERP"]
    )

    ariba["_linea_ariba_num"] = normalizar_numero(
        ariba["Número de línea de la solicitud de compra"]
    )

    ariba["_descripcion_norm"] = ariba["Descripción"].apply(normalizar_texto)

    if "ID de pedido" in ariba.columns:
        ariba["_id_pedido_norm"] = normalizar_entero_str(
            ariba["ID de pedido"]
        )
    else:
        ariba["_id_pedido_norm"] = pd.NA

    ariba["_fecha_ariba_norm"] = pd.to_datetime(
        ariba["Fecha de la solicitud de compra"],
        errors="coerce"
    )

    columnas_ariba = [
        "_id_ariba",
        "_id_erp_norm",
        "_linea_ariba_num",
        "_descripcion_norm",
        "_id_pedido_norm",
        "_fecha_ariba_norm",
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

    candidatos["_similitud_ariba_descripcion"] = (
        candidatos["_texto_me5a_norm"].fillna("")
        .eq(candidatos["_descripcion_norm"].fillna(""))
        & candidatos["_texto_me5a_norm"].fillna("").ne("")
    )

    candidatos["_dias_ariba_fecha"] = (
        candidatos["_fecha_ariba_norm"] - candidatos["_fecha_solicitud_norm"]
    ).dt.days.abs()

    candidatos["_score_ariba_fecha"] = np.where(
        candidatos["_dias_ariba_fecha"].notna(),
        np.maximum(0, 10 - candidatos["_dias_ariba_fecha"]),
        0
    )

    cols_bool_ariba = [
        "_match_ariba_solicitud",
        "_match_ariba_linea",
        "_match_ariba_pedido",
        "_similitud_ariba_descripcion"
    ]

    candidatos = limpiar_booleanos(candidatos, cols_bool_ariba)

    candidatos["score_ariba"] = (
        np.where(candidatos["_match_ariba_solicitud"], 60, 0)
        + np.where(candidatos["_match_ariba_linea"], 40, 0)
        + np.where(candidatos["_match_ariba_pedido"], 10, 0)
        + np.where(candidatos["_similitud_ariba_descripcion"], 20, 0)
        + candidatos["_score_ariba_fecha"].fillna(0)
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
        "_similitud_ariba_descripcion",
        "_dias_ariba_fecha",
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
        "ID de solicitud de compra del ERP": "ariba_id_solicitud_compra_erp",
        "Número de línea de la solicitud de compra": "ariba_numero_linea_solicitud",
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

@st.cache_data(show_spinner="Construyendo resultado final...")
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
# Resumen
# =========================================================

def generar_resumen(resultado_final: pd.DataFrame) -> pd.DataFrame:
    resumen = (
        resultado_final["estado_match"]
        .value_counts(dropna=False)
        .reset_index()
    )

    resumen.columns = ["Estado match", "Cantidad"]

    resumen["%"] = (
        resumen["Cantidad"] / len(resultado_final) * 100
    ).round(2)

    return resumen


def columnas_vista_resultado(df: pd.DataFrame) -> list:
    columnas_preferidas = [
        "estado_match",
        "score_total_integrado",
        "score_ariba",
        "score_nme80fn",

        "Solicitud de pedido",
        "Pos.solicitud pedido",
        "Pedido",
        "Posición de pedido",
        "Material",
        "Texto breve",
        "Cantidad solicitada",
        "Unidad de medida",
        "Moneda",
        "Centro",
        "Fecha de solicitud",
        "Fecha de pedido",
        "Fecha de entrega",

        "ariba_id_solicitud_compra_erp",
        "ariba_numero_linea_solicitud",
        "ariba_descripcion",
        "ariba_id_pedido",
        "ariba_fecha_solicitud_compra",
        "ariba_fecha_aprobacion",
        "ariba_categoria_tipo_compra",
        "ariba_id_unidad_negocio",

        "nme_documento_compras",
        "nme_posicion",
        "nme_material",
        "nme_texto_breve",
        "nme_cantidad",
        "nme_unidad_medida_pedido",
        "nme_importe",
        "nme_fecha_facturacion_proveedor",
        "nme_fecha_entrada_mercancia_recepcion"
    ]

    return [col for col in columnas_preferidas if col in df.columns]


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


@st.cache_data(show_spinner="Preparando CSV...")
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner="Preparando Parquet...")
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner="Preparando Excel...")
def convertir_a_excel_cache(df: pd.DataFrame, resumen: pd.DataFrame) -> bytes:
    return convertir_a_excel(df, resumen)


# =========================================================
# Interfaz minimalista
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

    resultado_final = construir_match_final(
        df_me5a=df_me5a,
        df_ariba=df_ariba,
        df_nme=df_nme
    )

    resumen = generar_resumen(resultado_final)

    st.success("Match generado correctamente.")

    st.subheader("Indicadores")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("ME5A", f"{len(df_me5a):,}")
    m2.metric("Resultado", f"{len(resultado_final):,}")
    m3.metric("Match ARIBA", f"{resultado_final['match_ariba_encontrado'].sum():,}")
    m4.metric("Match NME80FN", f"{resultado_final['match_nme80fn_encontrado'].sum():,}")

    st.subheader("Resumen")

    st.dataframe(
        resumen,
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Resultado")

    columnas_resultado = columnas_vista_resultado(resultado_final)

    st.dataframe(
        resultado_final[columnas_resultado].head(int(limite_vista)),
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
            st.markdown("**Resultado**")
            st.write(resultado_final.columns.tolist())

    st.subheader("Descarga")

    d1, d2, d3 = st.columns(3)

    with d1:
        st.download_button(
            label="Descargar Parquet",
            data=convertir_a_parquet_cache(resultado_final),
            file_name="match_integrado_me5a_ariba_nme80fn.parquet",
            mime="application/octet-stream",
            use_container_width=True
        )

    with d2:
        st.download_button(
            label="Descargar CSV",
            data=convertir_a_csv_cache(resultado_final),
            file_name="match_integrado_me5a_ariba_nme80fn.csv",
            mime="text/csv",
            use_container_width=True
        )

    with d3:
        limite_excel = 250_000

        if len(resultado_final) > limite_excel:
            st.caption(
                f"Excel no disponible para más de {limite_excel:,} filas."
            )
        else:
            st.download_button(
                label="Descargar Excel",
                data=convertir_a_excel_cache(resultado_final, resumen),
                file_name="match_integrado_me5a_ariba_nme80fn.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

except Exception as e:
    st.error("No se pudo generar el match.")
    st.exception(e)
