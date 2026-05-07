import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


# =========================
# Ruta del logo ENAEX
# =========================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================
# Configuración Streamlit
# =========================

st.set_page_config(
    page_title="Match ME5A - ARIBA - NME80FN",
    page_icon="🔗",
    layout="wide"
)


# =========================
# Encabezado con logo ENAEX centrado
# =========================

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
            margin-top: 10px;
            margin-bottom: 20px;
        ">
            <img 
                src="data:image/svg+xml;base64,{logo_base64}" 
                style="width: 260px; display: block;"
            >
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.error(f"Logo no encontrado en ruta correcta: {LOGO_PATH}")


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


def normalizar_entero_str(serie: pd.Series) -> pd.Series:
    return (
        pd.to_numeric(serie, errors="coerce")
        .astype("Int64")
        .astype("string")
    )


def normalizar_numero(serie: pd.Series) -> pd.Series:
    return pd.to_numeric(serie, errors="coerce")


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


def normalizar_material(serie: pd.Series) -> pd.Series:
    return (
        serie
        .astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def validar_columnas(df: pd.DataFrame, columnas: list, nombre_df: str):
    faltantes = [col for col in columnas if col not in df.columns]

    if faltantes:
        raise ValueError(
            f"Faltan columnas en {nombre_df}: {faltantes}"
        )


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

    # Normalizaciones ME5A
    me5a["_pedido_norm"] = normalizar_entero_str(me5a["Pedido"])
    me5a["_posicion_pedido_norm"] = normalizar_entero_str(me5a["Posición de pedido"])
    me5a["_material_norm"] = normalizar_material(me5a["Material"])
    me5a["_centro_norm"] = me5a["Centro"].astype("string").str.strip()
    me5a["_cantidad_norm"] = normalizar_numero(me5a["Cantidad solicitada"])
    me5a["_unidad_norm"] = me5a["Unidad de medida"].astype("string").str.strip()
    me5a["_moneda_norm"] = me5a["Moneda"].astype("string").str.strip()

    # Normalizaciones NME80FN
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
        candidatos["_pedido_norm"].eq(candidatos["_documento_norm"])
    )

    candidatos["_match_nme_posicion"] = (
        candidatos["_posicion_pedido_norm"].eq(candidatos["_posicion_norm"])
    )

    candidatos["_match_nme_material"] = (
        candidatos["_material_norm_me5a"].eq(candidatos["_material_norm_nme"])
    )

    candidatos["_match_nme_centro"] = (
        candidatos["_centro_norm_me5a"].eq(candidatos["_centro_norm_nme"])
    )

    candidatos["_match_nme_cantidad"] = (
        candidatos["_cantidad_norm_me5a"].eq(candidatos["_cantidad_norm_nme"])
    )

    candidatos["_match_nme_unidad"] = (
        candidatos["_unidad_norm_me5a"].eq(candidatos["_unidad_norm_nme"])
    )

    candidatos["_match_nme_moneda"] = (
        candidatos["_moneda_norm_me5a"].eq(candidatos["_moneda_norm_nme"])
    )

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
            "ID de pedido ERP",
            "Número de línea de la solicitud de compra"
        ],
        "ARIBA"
    )

    me5a = me5a.copy()
    ariba = ariba.copy()

    me5a["_id_me5a"] = range(len(me5a))
    ariba["_id_ariba"] = range(len(ariba))

    # Columnas opcionales ARIBA
    col_desc = "Descripción" if "Descripción" in ariba.columns else None
    col_id_pedido = "ID de pedido" if "ID de pedido" in ariba.columns else None
    col_fecha = (
        "Fecha de la solicitud de compra"
        if "Fecha de la solicitud de compra" in ariba.columns
        else None
    )

    # Normalizaciones ME5A
    me5a["_solicitud_norm"] = normalizar_entero_str(me5a["Solicitud de pedido"])
    me5a["_pos_solicitud_num"] = normalizar_numero(me5a["Pos.solicitud pedido"])
    me5a["_linea_esperada_ariba"] = me5a["_pos_solicitud_num"] / 10
    me5a["_texto_me5a_norm"] = me5a["Texto breve"].apply(normalizar_texto)
    me5a["_pedido_norm"] = normalizar_entero_str(me5a["Pedido"])
    me5a["_fecha_solicitud_norm"] = pd.to_datetime(
        me5a["Fecha de solicitud"],
        errors="coerce"
    )

    # Normalizaciones ARIBA
    ariba["_id_erp_norm"] = normalizar_entero_str(ariba["ID de pedido ERP"])
    ariba["_linea_ariba_num"] = normalizar_numero(
        ariba["Número de línea de la solicitud de compra"]
    )

    if col_desc:
        ariba["_descripcion_norm"] = ariba[col_desc].apply(normalizar_texto)
    else:
        ariba["_descripcion_norm"] = ""

    if col_id_pedido:
        ariba["_id_pedido_norm"] = normalizar_entero_str(ariba[col_id_pedido])
    else:
        ariba["_id_pedido_norm"] = pd.NA

    if col_fecha:
        ariba["_fecha_ariba_norm"] = pd.to_datetime(
            ariba[col_fecha],
            errors="coerce"
        )
    else:
        ariba["_fecha_ariba_norm"] = pd.NaT

    columnas_ariba = [
        "_id_ariba",
        "_id_erp_norm",
        "_linea_ariba_num",
        "_descripcion_norm",
        "_id_pedido_norm",
        "_fecha_ariba_norm",
        "ID de pedido ERP",
        "Número de línea de la solicitud de compra"
    ]

    columnas_opcionales = [
        "Descripción",
        "ID de pedido",
        "Fecha de la solicitud de compra",
        "Tipo de Compra",
        "ID de unidad de negocio",
        "Categoria Tipo de Compra",
        "Solicitante",
        "Centro",
        "Material",
        "Cantidad",
        "Precio"
    ]

    for col in columnas_opcionales:
        if col in ariba.columns and col not in columnas_ariba:
            columnas_ariba.append(col)

    candidatos = me5a.merge(
        ariba[columnas_ariba],
        left_on="_solicitud_norm",
        right_on="_id_erp_norm",
        how="left",
        suffixes=("_me5a", "_ariba")
    )

    candidatos["_match_ariba_solicitud"] = (
        candidatos["_solicitud_norm"].eq(candidatos["_id_erp_norm"])
    )

    candidatos["_match_ariba_linea"] = np.isclose(
        candidatos["_linea_esperada_ariba"],
        candidatos["_linea_ariba_num"],
        equal_nan=False
    )

    candidatos["_similitud_ariba_descripcion"] = candidatos.apply(
        lambda row: (
            0.0
            if pd.isna(row.get("_descripcion_norm"))
            else (
                1.0
                if row.get("_texto_me5a_norm") == row.get("_descripcion_norm")
                else 0.0
            )
        ),
        axis=1
    )

    candidatos["_match_ariba_pedido"] = (
        candidatos["_pedido_norm"].eq(candidatos["_id_pedido_norm"])
    )

    candidatos["_dias_ariba_fecha"] = (
        candidatos["_fecha_ariba_norm"] - candidatos["_fecha_solicitud_norm"]
    ).dt.days.abs()

    candidatos["_score_ariba_fecha"] = np.where(
        candidatos["_dias_ariba_fecha"].notna(),
        np.maximum(0, 10 - candidatos["_dias_ariba_fecha"]),
        0
    )

    candidatos["score_ariba"] = (
        np.where(candidatos["_match_ariba_solicitud"], 60, 0)
        + np.where(candidatos["_match_ariba_linea"], 40, 0)
        + np.where(candidatos["_match_ariba_pedido"], 10, 0)
        + candidatos["_score_ariba_fecha"]
        + np.where(candidatos["_similitud_ariba_descripcion"].eq(1), 20, 0)
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
        "_dias_ariba_fecha",
        "ID de pedido ERP",
        "Número de línea de la solicitud de compra",
        "Descripción",
        "ID de pedido",
        "Fecha de la solicitud de compra",
        "Tipo de Compra",
        "ID de unidad de negocio",
        "Categoria Tipo de Compra",
        "Solicitante",
        "Centro",
        "Material",
        "Cantidad",
        "Precio"
    ]

    columnas_resultado = [col for col in columnas_resultado if col in mejor.columns]

    resultado = mejor[columnas_resultado].copy()

    resultado = resultado.rename(columns={
        "ID de pedido ERP": "ariba_id_pedido_erp",
        "Número de línea de la solicitud de compra": "ariba_numero_linea_solicitud",
        "Descripción": "ariba_descripcion",
        "ID de pedido": "ariba_id_pedido",
        "Fecha de la solicitud de compra": "ariba_fecha_solicitud_compra",
        "Tipo de Compra": "ariba_tipo_compra",
        "ID de unidad de negocio": "ariba_id_unidad_negocio",
        "Categoria Tipo de Compra": "ariba_categoria_tipo_compra",
        "Solicitante": "ariba_solicitante",
        "Centro": "ariba_centro",
        "Material": "ariba_material",
        "Cantidad": "ariba_cantidad",
        "Precio": "ariba_precio"
    })

    return resultado


# =========================================================
# Match general entre los 3
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

    resultado["match_ariba_encontrado"] = resultado["score_ariba"].fillna(0).gt(0)
    resultado["match_nme80fn_encontrado"] = resultado["score_nme80fn"].fillna(0).gt(0)

    resultado["score_ariba"] = resultado["score_ariba"].fillna(0)
    resultado["score_nme80fn"] = resultado["score_nme80fn"].fillna(0)

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
# Interfaz
# =========================================================

st.markdown(
    """
    <h1 style='text-align: center;'>
        Match Integrado ME5A - ARIBA - NME80FN
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Sube los tres DataFrames limpios. El resultado final mantiene el
        <b>100% de los registros de ME5A</b> y agrega las mejores coincidencias
        encontradas en <b>ARIBA</b> y <b>NME80FN</b>.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    st.header("Configuración")

    pagina = st.radio(
        "Menú",
        options=[
            "Match",
            "Resumen",
            "Descarga"
        ],
        index=0
    )

    st.divider()

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

    st.caption(
        "El separador solo aplica si subes archivos CSV."
    )


col_a, col_b, col_c = st.columns(3)

with col_a:
    archivo_me5a = st.file_uploader(
        "1. Sube ME5A limpio",
        type=["parquet", "xlsx", "csv"],
        key="me5a"
    )

with col_b:
    archivo_ariba = st.file_uploader(
        "2. Sube ARIBA limpio",
        type=["parquet", "xlsx", "csv"],
        key="ariba"
    )

with col_c:
    archivo_nme = st.file_uploader(
        "3. Sube NME80FN limpio",
        type=["parquet", "xlsx", "csv"],
        key="nme"
    )


if archivo_me5a and archivo_ariba and archivo_nme:
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

        resumen = (
            resultado_final["estado_match"]
            .value_counts(dropna=False)
            .reset_index()
        )

        resumen.columns = [
            "Estado match",
            "Cantidad"
        ]

        resumen["%"] = (
            resumen["Cantidad"] / len(resultado_final) * 100
        ).round(2)

        if pagina == "Match":
            st.success("Match calculado correctamente.")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Filas ME5A",
                f"{len(df_me5a):,}"
            )

            col2.metric(
                "Filas resultado",
                f"{len(resultado_final):,}"
            )

            col3.metric(
                "Match ARIBA",
                f"{resultado_final['match_ariba_encontrado'].sum():,}"
            )

            col4.metric(
                "Match NME80FN",
                f"{resultado_final['match_nme80fn_encontrado'].sum():,}"
            )

            st.subheader("Vista previa ME5A")
            st.dataframe(
                df_me5a.head(50),
                use_container_width=True
            )

            st.subheader("Vista previa ARIBA")
            st.dataframe(
                df_ariba.head(50),
                use_container_width=True
            )

            st.subheader("Vista previa NME80FN")
            st.dataframe(
                df_nme.head(50),
                use_container_width=True
            )

            st.divider()

            st.subheader("Resultado integrado")

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

                "ariba_id_pedido_erp",
                "ariba_numero_linea_solicitud",
                "ariba_descripcion",
                "ariba_id_pedido",
                "ariba_fecha_solicitud_compra",

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

            columnas_preferidas = [
                col for col in columnas_preferidas
                if col in resultado_final.columns
            ]

            st.dataframe(
                resultado_final[columnas_preferidas].head(200),
                use_container_width=True
            )

        elif pagina == "Resumen":
            st.subheader("Resumen de match")

            st.dataframe(
                resumen,
                use_container_width=True
            )

            st.bar_chart(
                resumen.set_index("Estado match")["Cantidad"]
            )

            st.divider()

            st.subheader("Distribución de scores")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Score ARIBA")
                st.bar_chart(
                    resultado_final["score_ariba"].value_counts().sort_index()
                )

            with col2:
                st.markdown("#### Score NME80FN")
                st.bar_chart(
                    resultado_final["score_nme80fn"].value_counts().sort_index()
                )

            st.divider()

            st.subheader("Registros sin match")

            sin_match = resultado_final[
                resultado_final["estado_match"].eq("Sin match")
            ].copy()

            st.write(f"Cantidad sin match: {len(sin_match):,}")

            st.dataframe(
                sin_match.head(100),
                use_container_width=True
            )

        elif pagina == "Descarga":
            st.subheader("Descargar resultado integrado")

            formato_descarga = st.radio(
                "Formato de descarga",
                options=[
                    "Excel",
                    "CSV",
                    "Parquet"
                ],
                horizontal=True
            )

            if formato_descarga == "Excel":
                excel_bytes = convertir_a_excel_cache(
                    resultado_final,
                    resumen
                )

                st.download_button(
                    label="Descargar Excel",
                    data=excel_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            elif formato_descarga == "CSV":
                csv_bytes = convertir_a_csv_cache(resultado_final)

                st.download_button(
                    label="Descargar CSV",
                    data=csv_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn.csv",
                    mime="text/csv"
                )

            elif formato_descarga == "Parquet":
                parquet_bytes = convertir_a_parquet_cache(resultado_final)

                st.download_button(
                    label="Descargar Parquet",
                    data=parquet_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn.parquet",
                    mime="application/octet-stream"
                )

    except Exception as e:
        st.error("Ocurrió un error al procesar los archivos.")
        st.exception(e)

else:
    st.warning("Carga los tres archivos para comenzar.")