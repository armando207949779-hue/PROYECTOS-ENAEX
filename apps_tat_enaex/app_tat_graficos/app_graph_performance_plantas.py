import io
import base64
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================
# IMPORTANTE:
# Si esta app se ejecuta dentro de st.navigation() desde app_tat_global.py,
# NO uses st.set_page_config() aquí, porque debe estar solo en la app principal.
#
# Si la ejecutas sola con:
# streamlit run app_graph_performance_plantas.py
# puedes descomentar este bloque.
#
# st.set_page_config(
#     page_title="Performance de Plantas",
#     page_icon="🏭",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

BASE_DIR = Path(__file__).resolve().parent

LOGO_CANDIDATOS = [
    BASE_DIR / "assets" / "logo.svg",
    BASE_DIR / "assets" / "logo.png",
    BASE_DIR / "assets" / "enaex.svg",
    BASE_DIR / "assets" / "enaex.png",
    BASE_DIR / "logo.svg",
    BASE_DIR / "logo.png",
    BASE_DIR.parent / "assets" / "logo.svg",
    BASE_DIR.parent / "assets" / "logo.png",
    BASE_DIR.parent.parent / "assets" / "logo.svg",
    BASE_DIR.parent.parent / "assets" / "logo.png",
]

COLOR_CUMPLE = "#606060"
COLOR_NO_CUMPLE = "#EF3E52"
COLOR_SIN_DATOS = "#BFC3C7"
COLOR_META = "#008060"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"
COLOR_BG = "#F3F4F6"
COLOR_CARD = "#FFFFFF"

META_CUMPLIMIENTO = 65

MESES_NOMBRE = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}

# Columnas del dataframe nuevo
COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

COL_PERFORMANCE_TAT = "performance_tat_total"

COL_CENTRO_ME5A = "Centro - ME5A"
COL_CENTRO_NME80FN = "Centro - NME80FN"
COL_CENTRO_SIMPLE = "Centro"

COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - NME80FN"

COLUMNAS_REQUERIDAS_BASE = [
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
    "Fecha de entrada - NME80FN",
    "Fecha de documento - NME80FN",
    "Fecha contabilización - NME80FN",
    "Fecha facturación proveedor - NME80FN",
    "Fecha recepción mercancía - NME80FN",
    "ariba_fecha_solicitud_compra",
    "ariba_fecha_aprobacion",
    "nme_fecha_entrada",
    "nme_fecha_documento",
    "nme_fecha_contabiliz",
    "nme_fecha_facturacion_proveedor",
    "nme_fecha_entrada_mercancia_recepcion",
]

CENTROS_EXCLUIR_PLANTAS_SERVICIOS = ["E001", "E002", "E009", "E024", "E021"]

FECHA_FILTRO_POWERBI = pd.Timestamp("2024-02-01")


# =========================================================
# ESTILO UI
# =========================================================

def aplicar_css():
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {COLOR_BG};
            }}
            .block-container {{
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1500px;
            }}
            .header-card {{
                background: {COLOR_CARD};
                border: 1px solid #E5E7EB;
                border-radius: 18px;
                padding: 18px 22px;
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
                margin-bottom: 16px;
            }}
            .title-main {{
                font-size: 24px;
                font-weight: 800;
                color: {COLOR_TEXTO};
                margin: 0;
                line-height: 1.15;
            }}
            .subtitle-main {{
                font-size: 13px;
                color: {COLOR_MUTED};
                margin-top: 4px;
            }}
            .section-card {{
                background: {COLOR_CARD};
                border: 1px solid #E5E7EB;
                border-radius: 18px;
                padding: 16px;
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
                margin-bottom: 16px;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: 750;
                color: {COLOR_TEXTO};
                margin-bottom: 2px;
            }}
            .section-caption {{
                font-size: 12px;
                color: {COLOR_MUTED};
                margin-bottom: 12px;
            }}
            .metric-card {{
                background: linear-gradient(180deg, #FFFFFF 0%, #F9FAFB 100%);
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 14px 16px;
                min-height: 102px;
            }}
            .metric-label {{
                color: {COLOR_MUTED};
                font-size: 12px;
                font-weight: 650;
                margin-bottom: 6px;
            }}
            .metric-value {{
                color: {COLOR_TEXTO};
                font-size: 28px;
                font-weight: 850;
                line-height: 1;
            }}
            .metric-note {{
                color: {COLOR_MUTED};
                font-size: 11px;
                margin-top: 7px;
            }}
            .chart-card {{
                background: {COLOR_CARD};
                border: 1px solid #E5E7EB;
                border-radius: 18px;
                padding: 14px 16px 8px 16px;
                box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
                margin-bottom: 16px;
            }}
            .chart-title {{
                font-size: 17px;
                font-weight: 800;
                color: {COLOR_TEXTO};
                margin-bottom: 2px;
            }}
            .chart-caption {{
                font-size: 12px;
                color: {COLOR_MUTED};
                margin-bottom: 10px;
            }}
            .status-pill {{
                display: inline-block;
                border-radius: 999px;
                padding: 5px 10px;
                background: #F3F4F6;
                color: {COLOR_TEXTO};
                font-size: 12px;
                font-weight: 700;
                border: 1px solid #E5E7EB;
            }}
            [data-testid="stFileUploader"] section {{
                border-radius: 14px;
                border-color: #CBD5E1;
                background: #F8FAFC;
            }}
            .stTabs [data-baseweb="tab-list"] {{
                gap: 8px;
            }}
            .stTabs [data-baseweb="tab"] {{
                background: #FFFFFF;
                border-radius: 999px;
                border: 1px solid #E5E7EB;
                padding-left: 18px;
                padding-right: 18px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def encontrar_logo():
    for path in LOGO_CANDIDATOS:
        if path.exists():
            return path
    return None


def mostrar_logo(ancho: int = 220):
    logo_path = encontrar_logo()

    if logo_path is None:
        st.markdown(
            """
            <div style="
                display:flex;
                align-items:center;
                justify-content:center;
                min-height:72px;
                margin:0 0 14px 0;
            ">
                <div style="text-align:center;">
                    <div style="font-weight:850;font-size:30px;color:#374151;line-height:1;">Enaex</div>
                    <div style="font-size:9px;color:#6B7280;font-weight:700;letter-spacing:.08em;">STRONGER BONDS</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    suffix = logo_path.suffix.lower()
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"
    raw = logo_path.read_bytes()
    logo_base64 = base64.b64encode(raw).decode("utf-8")

    st.markdown(
        f"""
        <div style="
            width:100%;
            display:flex;
            justify-content:center;
            align-items:center;
            min-height:84px;
            margin:0 0 16px 0;
            overflow:visible;
        ">
            <img
                src="data:{mime};base64,{logo_base64}"
                style="
                    width:{ancho}px;
                    max-width:80%;
                    height:auto;
                    display:block;
                    object-fit:contain;
                "
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_metric(label: str, value: str, note: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_header(title: str, caption: str = ""):
    st.markdown(f"<div class='section-title'>{title}</div>", unsafe_allow_html=True)
    if caption:
        st.markdown(f"<div class='section-caption'>{caption}</div>", unsafe_allow_html=True)


# =========================================================
# LECTURA
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;)" or separador_csv == "Punto y coma (;):":
        return ";"
    if separador_csv == "Coma (,)":
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner=False)
def leer_archivo_cache(bytes_archivo: bytes, nombre_archivo: str, separador_csv: str) -> pd.DataFrame:
    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(buffer)

    if nombre.endswith(".csv") or nombre.endswith(".txt"):
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

    if nombre.endswith(".json") or nombre.endswith(".jsonl"):
        try:
            return pd.read_json(buffer, lines=True)
        except ValueError:
            buffer.seek(0)
            return pd.read_json(buffer)

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx, .xls, .csv, .txt, .json o .jsonl")


# =========================================================
# LÓGICA PERFORMANCE
# =========================================================

def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie, errors="coerce")

    resultado = pd.Series(
        pd.NaT,
        index=serie.index,
        dtype="datetime64[ns]",
    )

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


def extraer_tipo_oc(valor):
    if pd.isna(valor):
        return pd.NA

    texto = str(valor).strip()

    try:
        texto = str(int(float(texto)))
    except Exception:
        texto = texto.replace(".0", "")

    return texto[:2] if len(texto) >= 2 else pd.NA


def diferencia_dias(fecha_fin: pd.Series, fecha_inicio: pd.Series) -> pd.Series:
    return (fecha_fin - fecha_inicio).dt.days


def evaluar_performance_tat(df: pd.DataFrame) -> pd.Series:
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


def normalizar_estado_tat(valor) -> str:
    texto = str(valor).strip().lower()
    texto = (
        texto.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

    if texto == "cumple":
        return "Cumple"

    if texto in ["no cumple", "nocumple"]:
        return "No cumple"

    if texto in ["no aplica", "no aplica al analisis"]:
        return "No aplica al análisis"

    if texto == "en proceso":
        return "En proceso"

    if texto in ["sin datos", "sin dato"]:
        return "Sin datos"

    return str(valor).strip()


def obtener_columna_centro(df: pd.DataFrame) -> str:
    for col in [COL_CENTRO_ME5A, COL_CENTRO_NME80FN, COL_CENTRO_SIMPLE]:
        if col in df.columns:
            return col

    raise ValueError("No se encontró columna de centro: Centro - ME5A, Centro - NME80FN o Centro")


def validar_columnas_base(df: pd.DataFrame):
    faltantes = [col for col in COLUMNAS_REQUERIDAS_BASE if col not in df.columns]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas para calcular Performance TAT: {faltantes}")


@st.cache_data(show_spinner=False)
def aplicar_logica_performance_plantas(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)

    validar_columnas_base(df)

    for col in COLUMNAS_FECHA_PERFORMANCE:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])

    col_centro = obtener_columna_centro(df)
    df["centro_grafico"] = df[col_centro].astype(str).str.strip()

    if COL_PEDIDO in df.columns:
        df["tipo_oc"] = df[COL_PEDIDO].apply(extraer_tipo_oc)
    elif COL_DOCUMENTO_COMPRAS in df.columns:
        df["tipo_oc"] = df[COL_DOCUMENTO_COMPRAS].apply(extraer_tipo_oc)
    elif "tipo_oc" in df.columns:
        df["tipo_oc"] = df["tipo_oc"].apply(extraer_tipo_oc)
    else:
        df["tipo_oc"] = pd.NA

    df["tipo_oc"] = df["tipo_oc"].astype("string")

    df["dias_tat_total"] = diferencia_dias(
        df[COL_FECHA_RECEPCION_FINAL],
        df[COL_FECHA_SOLICITUD_FINAL],
    )

    df["dias_liberacion_solped"] = diferencia_dias(
        df[COL_FECHA_LIBERACION_FINAL],
        df[COL_FECHA_SOLICITUD_FINAL],
    )

    df["dias_comprador"] = diferencia_dias(
        df[COL_FECHA_PEDIDO_FINAL],
        df[COL_FECHA_LIBERACION_FINAL],
    )

    df["dias_proveedor"] = diferencia_dias(
        df[COL_FECHA_FACTURACION_FINAL],
        df[COL_FECHA_PEDIDO_FINAL],
    )

    df["dias_logistica"] = diferencia_dias(
        df[COL_FECHA_RECEPCION_FINAL],
        df[COL_FECHA_FACTURACION_FINAL],
    )

    columnas_dias_evaluables = [
        "dias_liberacion_solped",
        "dias_comprador",
        "dias_proveedor",
        "dias_logistica",
        "dias_tat_total",
    ]

    df["tiene_fechas_inconsistentes"] = (
        df[columnas_dias_evaluables]
        .lt(0)
        .any(axis=1, skipna=True)
    )

    if COL_PERFORMANCE_TAT not in df.columns:
        df[COL_PERFORMANCE_TAT] = evaluar_performance_tat(df)
    else:
        df[COL_PERFORMANCE_TAT] = df[COL_PERFORMANCE_TAT].apply(normalizar_estado_tat)

    df["periodo_fecha"] = df[COL_FECHA_RECEPCION_FINAL].dt.to_period("M").dt.to_timestamp()
    df["anio"] = df[COL_FECHA_RECEPCION_FINAL].dt.year
    df["mes_num"] = df[COL_FECHA_RECEPCION_FINAL].dt.month
    df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)

    df["periodo_label"] = np.where(
        df["anio"].notna() & df["mes_nombre"].notna(),
        df["mes_nombre"].astype(str) + " " + df["anio"].astype("Int64").astype(str),
        pd.NA,
    )

    df["grupo_planta"] = "Plantas de servicios"
    df.loc[df["centro_grafico"].eq("E002"), "grupo_planta"] = "Prillex"
    df.loc[df["centro_grafico"].eq("E024"), "grupo_planta"] = "Rio Loa"

    df.loc[
        df["centro_grafico"].isin(CENTROS_EXCLUIR_PLANTAS_SERVICIOS)
        & ~df["centro_grafico"].isin(["E002", "E024"]),
        "grupo_planta",
    ] = "Excluir"

    return df


def aplicar_filtros_dashboard(
    df: pd.DataFrame,
    fecha_facturacion_desde,
    estados_tat_sel,
    grupos_sel,
    rango_recepcion=None,
) -> pd.DataFrame:
    fecha_facturacion_desde = pd.Timestamp(fecha_facturacion_desde)

    data = df[
        (df[COL_FECHA_FACTURACION_FINAL] > fecha_facturacion_desde)
        & df[COL_FECHA_RECEPCION_FINAL].notna()
        & df["grupo_planta"].ne("Excluir")
    ].copy()

    if estados_tat_sel:
        data = data[data[COL_PERFORMANCE_TAT].isin(estados_tat_sel)].copy()
    else:
        return pd.DataFrame()

    if grupos_sel:
        data = data[data["grupo_planta"].isin(grupos_sel)].copy()
    else:
        return pd.DataFrame()

    if rango_recepcion is not None:
        if isinstance(rango_recepcion, (tuple, list)) and len(rango_recepcion) == 2:
            fecha_inicio = pd.Timestamp(rango_recepcion[0])
            fecha_fin = (
                pd.Timestamp(rango_recepcion[1])
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
            )

            data = data[
                data[COL_FECHA_RECEPCION_FINAL].between(fecha_inicio, fecha_fin)
            ].copy()

    return data


# =========================================================
# RESÚMENES Y GRÁFICOS
# =========================================================

def resumen_kpis_plantas(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    tabla = (
        df
        .groupby(["grupo_planta", COL_PERFORMANCE_TAT])
        .size()
        .reset_index(name="cantidad")
    )

    pivot = tabla.pivot_table(
        index="grupo_planta",
        columns=COL_PERFORMANCE_TAT,
        values="cantidad",
        fill_value=0,
        aggfunc="sum",
    ).reset_index()

    for col in ["Cumple", "No cumple"]:
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["Total evaluable"] = pivot["Cumple"] + pivot["No cumple"]
    pivot["% Cumple"] = np.where(
        pivot["Total evaluable"] > 0,
        pivot["Cumple"] / pivot["Total evaluable"] * 100,
        0,
    )

    return pivot


def crear_resumen_mensual_grupo(df: pd.DataFrame, grupo: str) -> pd.DataFrame:
    base = df[
        df["grupo_planta"].eq(grupo)
        & df[COL_PERFORMANCE_TAT].isin(["Cumple", "No cumple"])
        & df["periodo_fecha"].notna()
    ].copy()

    if base.empty:
        return pd.DataFrame()

    resumen = (
        base
        .groupby(["periodo_fecha", "periodo_label", COL_PERFORMANCE_TAT])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=["periodo_fecha", "periodo_label"],
        columns=COL_PERFORMANCE_TAT,
        values="cantidad",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for col in ["Cumple", "No cumple"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["Total"] = tabla["Cumple"] + tabla["No cumple"]
    tabla["% Cumple"] = np.where(tabla["Total"] > 0, tabla["Cumple"] / tabla["Total"] * 100, 0)
    tabla["% No cumple"] = np.where(tabla["Total"] > 0, tabla["No cumple"] / tabla["Total"] * 100, 0)

    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


def grafico_mensual_100_plantas(tabla: pd.DataFrame, titulo: str):
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='chart-title'>{titulo}</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='chart-caption'>
            Base evaluable: Performance TAT Cumple / No cumple ·
            Fecha eje: recepción final.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tabla.empty:
        st.info("No hay datos evaluables para este grupo.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    plot = tabla.melt(
        id_vars=["periodo_fecha", "periodo_label", "Total"],
        value_vars=["Cumple", "No cumple"],
        var_name="Estado",
        value_name="Cantidad",
    )

    plot["Estado"] = plot["Estado"].replace({"No cumple": "No Cumple"})

    plot["Porcentaje"] = np.where(
        plot["Total"] > 0,
        plot["Cantidad"] / plot["Total"] * 100,
        0,
    )

    plot["Orden"] = plot["Estado"].map(
        {
            "Cumple": 1,
            "No Cumple": 2,
        }
    ).fillna(9)

    order = tabla["periodo_label"].tolist()

    barras = (
        alt.Chart(plot)
        .mark_bar(size=30, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=order,
                title=None,
                axis=alt.Axis(labelAngle=0, labelFontSize=10),
            ),
            y=alt.Y(
                "Porcentaje:Q",
                stack="zero",
                title="% Performance TAT",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(
                    values=[0, 50, 100],
                    labelExpr="datum.value + '%'",
                    grid=True,
                ),
            ),
            color=alt.Color(
                "Estado:N",
                scale=alt.Scale(
                    domain=["Cumple", "No Cumple"],
                    range=[COLOR_CUMPLE, COLOR_NO_CUMPLE],
                ),
                legend=alt.Legend(title=None, orient="top", direction="horizontal"),
            ),
            order=alt.Order("Orden:Q", sort="ascending"),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes"),
                alt.Tooltip("Estado:N", title="Estado"),
                alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
                alt.Tooltip("Porcentaje:Q", title="Porcentaje", format=".1f"),
                alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f"),
            ],
        )
    )

    linea_meta = (
        alt.Chart(pd.DataFrame({"Meta": [META_CUMPLIMIENTO]}))
        .mark_rule(
            color=COLOR_META,
            strokeDash=[6, 4],
            strokeWidth=2,
        )
        .encode(
            y=alt.Y("Meta:Q"),
        )
    )

    chart = (
        (barras + linea_meta)
        .properties(height=230)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def mostrar_kpis_plantas(df: pd.DataFrame):
    kpis = resumen_kpis_plantas(df)

    orden = ["Prillex", "Rio Loa", "Plantas de servicios"]
    cols = st.columns(3)

    for i, grupo in enumerate(orden):
        data = kpis[kpis["grupo_planta"].eq(grupo)] if not kpis.empty else pd.DataFrame()

        if data.empty:
            cumple = 0
            no_cumple = 0
            total = 0
            pct = 0
        else:
            fila = data.iloc[0]
            cumple = int(fila["Cumple"])
            no_cumple = int(fila["No cumple"])
            total = int(fila["Total evaluable"])
            pct = float(fila["% Cumple"])

        with cols[i]:
            card_metric(
                grupo,
                f"{pct:.1f}%",
                f"Cumple: {cumple:,} · No cumple: {no_cumple:,} · Total: {total:,}",
            )


def mostrar_diagnostico(df: pd.DataFrame):
    with st.expander("Ver diagnóstico de datos", expanded=False):
        st.write("Filas usadas después de filtros:", len(df))

        st.write(
            "Rango fecha recepción:",
            df[COL_FECHA_RECEPCION_FINAL].min(),
            "→",
            df[COL_FECHA_RECEPCION_FINAL].max(),
        )

        st.write(
            "Rango fecha facturación:",
            df[COL_FECHA_FACTURACION_FINAL].min(),
            "→",
            df[COL_FECHA_FACTURACION_FINAL].max(),
        )

        st.write("Performance TAT:")
        perf = df[COL_PERFORMANCE_TAT].value_counts().reset_index()
        perf.columns = ["Estado", "Filas"]
        st.dataframe(perf, use_container_width=True, hide_index=True)

        st.write("Centros principales:")
        centros = df["centro_grafico"].value_counts().reset_index()
        centros.columns = ["Centro", "Filas"]
        st.dataframe(centros, use_container_width=True, hide_index=True)

        st.write("Grupos:")
        grupos = df["grupo_planta"].value_counts().reset_index()
        grupos.columns = ["Grupo", "Filas"]
        st.dataframe(grupos, use_container_width=True, hide_index=True)


# =========================================================
# APP
# =========================================================

aplicar_css()

# ---------------------------------------------------------
# 1) Logo y encabezado
# ---------------------------------------------------------
mostrar_logo(220)

st.markdown(
    """
    <div style="text-align:center; margin-bottom: 22px;">
        <div style="font-size:42px; font-weight:850; color:#1F2937; line-height:1.12;">
            Performance de Plantas
        </div>
        <div style="font-size:14px; color:#6B7280; margin-top:10px;">
            Prillex · Rio Loa · Plantas de servicios
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2) Configuración lateral
# ---------------------------------------------------------
with st.sidebar:
    st.header("Configuración")

    separador_csv = st.selectbox(
        "Separador CSV",
        options=["Automático", "Punto y coma (;)", "Coma (,)", "Tabulación"],
        index=0,
    )

    mostrar_diagnostico_check = st.checkbox(
        "Mostrar diagnóstico",
        value=False,
    )

    st.markdown("---")

    st.caption(
        """
        **Agrupación de centros**

        Prillex = E002  
        Rio Loa = E024  
        Plantas de servicios = todos excepto E001, E002, E009, E024 y E021
        """
    )

# ---------------------------------------------------------
# 3) Subir archivo
# ---------------------------------------------------------
st.subheader("Archivo")

uploaded_file = st.file_uploader(
    "Selecciona archivo con fechas finales",
    type=["parquet", "xlsx", "xls", "csv", "txt", "json", "jsonl"],
)

if uploaded_file is None:
    st.info("Carga el archivo con fechas finales para visualizar Performance de Plantas.")
    st.stop()

# ---------------------------------------------------------
# 4) Procesar archivo y crear filtros modificables
# ---------------------------------------------------------
try:
    with st.spinner("Leyendo archivo..."):
        df_original = leer_archivo_cache(
            bytes_archivo=uploaded_file.getvalue(),
            nombre_archivo=uploaded_file.name,
            separador_csv=separador_csv,
        )

    with st.spinner("Aplicando lógica de performance y agrupación de plantas..."):
        df_final = aplicar_logica_performance_plantas(df_original)

    # -----------------------------------------------------
    # Filtros con valores por defecto, pero modificables
    # -----------------------------------------------------
    with st.sidebar:
        st.markdown("---")
        st.subheader("Filtros del gráfico")

        fecha_facturacion_desde = st.date_input(
            "Fecha facturación posterior a",
            value=FECHA_FILTRO_POWERBI.date(),
        )

        estados_disponibles = [
            estado
            for estado in ["Cumple", "No cumple", "En proceso", "No aplica al análisis", "Sin datos"]
            if estado in df_final[COL_PERFORMANCE_TAT].dropna().astype(str).unique().tolist()
        ]

        estados_default = [
            estado
            for estado in ["Cumple", "No cumple"]
            if estado in estados_disponibles
        ]

        estados_tat_sel = st.multiselect(
            "Performance TAT",
            options=estados_disponibles,
            default=estados_default,
        )

        grupos_disponibles = [
            grupo
            for grupo in ["Prillex", "Rio Loa", "Plantas de servicios"]
            if grupo in df_final["grupo_planta"].dropna().astype(str).unique().tolist()
        ]

        grupos_todos = ["Prillex", "Rio Loa", "Plantas de servicios"]

        grupos_sel = st.multiselect(
            "Grupos a mostrar",
            options=grupos_todos,
            default=grupos_disponibles if grupos_disponibles else grupos_todos,
        )

        fechas_recepcion_validas = df_final[COL_FECHA_RECEPCION_FINAL].dropna()

        if not fechas_recepcion_validas.empty:
            fecha_recepcion_min = fechas_recepcion_validas.min().date()
            fecha_recepcion_max = fechas_recepcion_validas.max().date()

            rango_recepcion = st.date_input(
                "Fecha recepción",
                value=(fecha_recepcion_min, fecha_recepcion_max),
                min_value=fecha_recepcion_min,
                max_value=fecha_recepcion_max,
            )
        else:
            rango_recepcion = None
            st.warning("No hay fechas válidas de recepción.")

    with st.spinner("Aplicando filtros del dashboard..."):
        df_dashboard = aplicar_filtros_dashboard(
            df=df_final,
            fecha_facturacion_desde=fecha_facturacion_desde,
            estados_tat_sel=estados_tat_sel,
            grupos_sel=grupos_sel,
            rango_recepcion=rango_recepcion,
        )

    if df_dashboard.empty:
        st.warning(
            "No hay datos después de aplicar los filtros seleccionados."
        )
        st.stop()

    st.success("Performance de Plantas generada correctamente.")

    # -----------------------------------------------------
    # 5) Dashboard
    # -----------------------------------------------------
    tab_dashboard, tab_datos = st.tabs(["Dashboard", "Datos"])

    with tab_dashboard:
        section_header(
            "Indicadores generales",
            "Base según filtros seleccionados.",
        )

        total_filas = len(df_dashboard)
        cumple_tat = int(df_dashboard[COL_PERFORMANCE_TAT].eq("Cumple").sum())
        no_cumple_tat = int(df_dashboard[COL_PERFORMANCE_TAT].eq("No cumple").sum())
        evaluables_tat = cumple_tat + no_cumple_tat
        pct_cumple_tat = cumple_tat / evaluables_tat * 100 if evaluables_tat else 0

        k1, k2, k3, k4 = st.columns(4)

        with k1:
            card_metric("Filas filtradas", f"{total_filas:,}")

        with k2:
            card_metric("TAT evaluable", f"{evaluables_tat:,}")

        with k3:
            card_metric("Cumple TAT", f"{cumple_tat:,}", f"{pct_cumple_tat:.1f}%")

        with k4:
            card_metric("No cumple TAT", f"{no_cumple_tat:,}")

        st.divider()

        section_header(
            "Resumen por planta",
            "Porcentaje de cumplimiento TAT por grupo.",
        )

        mostrar_kpis_plantas(df_dashboard)

        st.divider()

        graficos_disponibles = {
            "Prillex": "Performance TAT Prillex",
            "Rio Loa": "Performance TAT Rio Loa",
            "Plantas de servicios": "Performance TAT Plantas de servicios",
        }

        for grupo, titulo in graficos_disponibles.items():
            if grupo in grupos_sel:
                grafico_mensual_100_plantas(
                    crear_resumen_mensual_grupo(df_dashboard, grupo),
                    titulo,
                )

        if mostrar_diagnostico_check:
            mostrar_diagnostico(df_dashboard)

    with tab_datos:
        st.subheader("Vista previa original")
        st.caption(f"Mostrando hasta 300 registros de {len(df_original):,} originales.")
        st.dataframe(
            df_original.head(300),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Vista previa final filtrada")

        columnas_preferidas = [
            "grupo_planta",
            "centro_grafico",
            COL_FECHA_SOLICITUD_FINAL,
            COL_FECHA_FACTURACION_FINAL,
            COL_FECHA_RECEPCION_FINAL,
            "tipo_oc",
            "dias_tat_total",
            COL_PERFORMANCE_TAT,
            "periodo_fecha",
            "periodo_label",
        ]

        columnas_preferidas = [
            col for col in columnas_preferidas
            if col in df_dashboard.columns
        ]

        st.dataframe(
            df_dashboard[columnas_preferidas].head(300),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("Ver columnas disponibles", expanded=False):
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**Columnas originales**")
                st.write(df_original.columns.tolist())

            with c2:
                st.markdown("**Columnas finales**")
                st.write(df_final.columns.tolist())

except Exception as e:
    st.error("No se pudo generar Performance de Plantas.")
    st.exception(e)
