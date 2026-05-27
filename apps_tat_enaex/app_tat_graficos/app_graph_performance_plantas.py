import base64
from datetime import date
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

# Columnas del dataframe
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


CENTROS_MAESTRO = [
    {"Centro": "E002", "Sociedad": "EC01", "Nombre": "Prillex"},
    {"Centro": "E021", "Sociedad": "EC06", "Nombre": "CM-Enaex Servicios"},
    {"Centro": "E024", "Sociedad": "EC06", "Nombre": "Rio Loa"},
    {"Centro": "E025", "Sociedad": "EC06", "Nombre": "Planta La Chimba"},
    {"Centro": "E026", "Sociedad": "EC06", "Nombre": "Teatinos"},
    {"Centro": "E029", "Sociedad": "EC06", "Nombre": "Chiquicamata"},
    {"Centro": "E030", "Sociedad": "EC06", "Nombre": "El tesoro"},
    {"Centro": "E031", "Sociedad": "EC06", "Nombre": "La escondida"},
    {"Centro": "E032", "Sociedad": "EC06", "Nombre": "Loma Bayas"},
    {"Centro": "E033", "Sociedad": "EC06", "Nombre": "Los Pelambres"},
    {"Centro": "E034", "Sociedad": "EC06", "Nombre": "Los Sauces"},
    {"Centro": "E035", "Sociedad": "EC06", "Nombre": "Mantos Blancos"},
    {"Centro": "E036", "Sociedad": "EC06", "Nombre": "Michilla"},
    {"Centro": "E037", "Sociedad": "EC06", "Nombre": "rt"},
    {"Centro": "E038", "Sociedad": "EC06", "Nombre": "El soldado"},
    {"Centro": "E039", "Sociedad": "EC06", "Nombre": "Polpaico"},
    {"Centro": "E040", "Sociedad": "EC06", "Nombre": "Peldehue"},
    {"Centro": "E041", "Sociedad": "EC06", "Nombre": "Esperanza"},
    {"Centro": "E042", "Sociedad": "EC06", "Nombre": "Gaby"},
    {"Centro": "E044", "Sociedad": "EC06", "Nombre": "Atacama Kozan"},
    {"Centro": "E045", "Sociedad": "EC06", "Nombre": "Franke"},
    {"Centro": "E046", "Sociedad": "EC06", "Nombre": "Manto verde"},
    {"Centro": "E047", "Sociedad": "EC06", "Nombre": "Polvorin Copiapo"},
    {"Centro": "E069", "Sociedad": "EC06", "Nombre": "Guanaco"},
    {"Centro": "E071", "Sociedad": "EC06", "Nombre": "Teniente"},
    {"Centro": "E076", "Sociedad": "EC06", "Nombre": "Mejillones"},
    {"Centro": "E077", "Sociedad": "EC06", "Nombre": "Ministro Hales"},
    {"Centro": "E078", "Sociedad": "EC06", "Nombre": "Sierra Gorda"},
    {"Centro": "E079", "Sociedad": "EC06", "Nombre": "Planta Quebrada Blanca"},
    {"Centro": "E081", "Sociedad": "EC06", "Nombre": "Chuqui Subte"},
    {"Centro": "E086", "Sociedad": "EC06", "Nombre": "Antucoya"},
    {"Centro": "E087", "Sociedad": "EC06", "Nombre": "Alto Maipo"},
    {"Centro": "E088", "Sociedad": "EC06", "Nombre": "Encuentro"},
    {"Centro": "E089", "Sociedad": "EC06", "Nombre": "Cerro Colorado"},
    {"Centro": "E090", "Sociedad": "EC06", "Nombre": "Collahuasi"},
    {"Centro": "E091", "Sociedad": "EC06", "Nombre": "Romeral"},
    {"Centro": "E095", "Sociedad": "EC06", "Nombre": "Planta Andina"},
    {"Centro": "E097", "Sociedad": "EC06", "Nombre": "Andina"},
    {"Centro": "E099", "Sociedad": "EC06", "Nombre": "Salvador"},
    {"Centro": "E103", "Sociedad": "EC06", "Nombre": "Zaldivar"},
    {"Centro": "E104", "Sociedad": "EC06", "Nombre": "Salares Norte"},
    {"Centro": "E105", "Sociedad": "EC06", "Nombre": "Los Colorados"},
    {"Centro": "E106", "Sociedad": "EC06", "Nombre": "Cerro N.N"},
    {"Centro": "E107", "Sociedad": "EC06", "Nombre": "Pleito"},
    {"Centro": "E108", "Sociedad": "EC06", "Nombre": "Plasma Enaex Servicios"},
    {"Centro": "E109", "Sociedad": "EC06", "Nombre": "Carola"},
    {"Centro": "E110", "Sociedad": "EC06", "Nombre": "Alto Hospicio SKC Enaex Serv"},
    {"Centro": "E113", "Sociedad": "EC06", "Nombre": "Copiapo SKC Enaex Serv"},
    {"Centro": "E114", "Sociedad": "EC06", "Nombre": "FullRPM Nogales Enaex Servicio"},
    {"Centro": "E082", "Sociedad": "EC07", "Nombre": "Nittra Casa Matriz"},
    {"Centro": "E083", "Sociedad": "EC07", "Nombre": "Nittra Prillex"},
    {"Centro": "E084", "Sociedad": "EC07", "Nombre": "Nittra Paine"},
    {"Centro": "E101", "Sociedad": "EC10", "Nombre": "Plasma"},
    {"Centro": "E003", "Sociedad": "EC01", "Nombre": "Planta Río Loa"},
    {"Centro": "E009", "Sociedad": "EC01", "Nombre": "Planta Chuquicamata"},
    {"Centro": "E020", "Sociedad": "EC01", "Nombre": "Planta Polpaico"},
    {"Centro": "E057", "Sociedad": "EC01", "Nombre": "Esperanza"},
    {"Centro": "E102", "Sociedad": "EC06", "Nombre": "SCL Bodega Arriendo"},
    {"Centro": "E043", "Sociedad": "EC06", "Nombre": "El peñón subte"},
    {"Centro": "E115", "Sociedad": "EC06", "Nombre": "Enaex SKC ING"},
    {"Centro": "E027", "Sociedad": "EC06", "Nombre": "Faena Teniente Rajo"},
    {"Centro": "E052", "Sociedad": "EC06", "Nombre": "Faena Spence"},
]

# Filtro por defecto, editable en dashboard.
# Este filtro NO define el eje temporal. Solo filtra registros.
FECHA_FILTRO_FACTURACION_DEFAULT = pd.Timestamp("2024-02-01")


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

    raise ValueError(
        "No se encontró columna de centro: Centro - ME5A, Centro - NME80FN o Centro"
    )


def validar_columnas_base(df: pd.DataFrame):
    faltantes = [col for col in COLUMNAS_REQUERIDAS_BASE if col not in df.columns]

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas para calcular Performance TAT: {faltantes}"
        )


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

    # Eje temporal mensual basado en fecha_recepcion_final
    df["periodo_fecha"] = df[COL_FECHA_RECEPCION_FINAL].dt.to_period("M").dt.to_timestamp()
    df["anio"] = df[COL_FECHA_RECEPCION_FINAL].dt.year
    df["mes_num"] = df[COL_FECHA_RECEPCION_FINAL].dt.month
    df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)

    # Semana ISO basada en fecha_recepcion_final
    calendario_iso = df[COL_FECHA_RECEPCION_FINAL].dt.isocalendar()
    df["anio_iso_recepcion"] = calendario_iso["year"].astype("Int64")
    df["semana_iso_recepcion"] = calendario_iso["week"].astype("Int64")

    df["semana_iso_label"] = np.where(
        df["anio_iso_recepcion"].notna() & df["semana_iso_recepcion"].notna(),
        "Año "
        + df["anio_iso_recepcion"].astype(str)
        + " · Semana "
        + df["semana_iso_recepcion"].astype(str).str.zfill(2),
        pd.NA,
    )

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
    centros_sel=None,
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

    grupos_sel = grupos_sel or []
    centros_sel = centros_sel or []

    if grupos_sel or centros_sel:
        mask_grupo = data["grupo_planta"].isin(grupos_sel) if grupos_sel else False
        mask_centro = data["centro_grafico"].isin(centros_sel) if centros_sel else False
        data = data[mask_grupo | mask_centro].copy()
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
    tabla["% Cumple"] = np.where(
        tabla["Total"] > 0,
        tabla["Cumple"] / tabla["Total"] * 100,
        0,
    )
    tabla["% No cumple"] = np.where(
        tabla["Total"] > 0,
        tabla["No cumple"] / tabla["Total"] * 100,
        0,
    )

    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


def grafico_mensual_100_plantas(tabla: pd.DataFrame, titulo: str):
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='chart-title'>{titulo}</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='chart-caption'>
            Eje temporal: fecha_recepcion_final ·
            Filtro disponible: fecha_facturacion_final.
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
                alt.Tooltip("periodo_label:N", title="Mes recepción"),
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


def grafico_temporal_porcentual_performance(df: pd.DataFrame):
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown("<div class='chart-title'>Performance temporal porcentual</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='chart-caption'>
            Evolución mensual del porcentaje de cumplimiento por planta.
            Eje temporal: fecha_recepcion_final.
        </div>
        """,
        unsafe_allow_html=True,
    )

    registros = []

    for grupo in ["Prillex", "Rio Loa", "Plantas de servicios"]:
        tabla = crear_resumen_mensual_grupo(df, grupo)

        if tabla.empty:
            continue

        tabla = tabla[tabla["Total"].gt(0)].copy()

        if tabla.empty:
            continue

        tabla["Planta"] = grupo
        registros.append(tabla)

    if not registros:
        st.info("No hay datos evaluables para visualizar la tendencia porcentual.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    plot = pd.concat(registros, ignore_index=True)
    plot = plot.sort_values(["periodo_fecha", "Planta"]).copy()

    linea_performance = (
        alt.Chart(plot)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X(
                "periodo_fecha:T",
                title="Mes recepción",
                axis=alt.Axis(format="%b %Y", labelAngle=0),
            ),
            y=alt.Y(
                "% Cumple:Q",
                title="% Cumplimiento",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(labelExpr="datum.value + '%'"),
            ),
            color=alt.Color(
                "Planta:N",
                legend=alt.Legend(title=None, orient="top", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes recepción"),
                alt.Tooltip("Planta:N", title="Planta"),
                alt.Tooltip("% Cumple:Q", title="% Cumplimiento", format=".1f"),
                alt.Tooltip("Cumple:Q", title="Cumple", format=",.0f"),
                alt.Tooltip("No cumple:Q", title="No cumple", format=",.0f"),
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
        .encode(y=alt.Y("Meta:Q"))
    )

    chart = (
        (linea_performance + linea_meta)
        .properties(height=300)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def crear_resumen_mensual_centro(df: pd.DataFrame, centro: str) -> pd.DataFrame:
    base = df[
        df["centro_grafico"].astype(str).str.strip().eq(str(centro).strip())
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
    tabla["% Cumple"] = np.where(
        tabla["Total"] > 0,
        tabla["Cumple"] / tabla["Total"] * 100,
        0,
    )
    tabla["% No cumple"] = np.where(
        tabla["Total"] > 0,
        tabla["No cumple"] / tabla["Total"] * 100,
        0,
    )

    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


def grafico_mensual_100_centro(tabla: pd.DataFrame, titulo: str):
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='chart-title'>{titulo}</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='chart-caption'>
            Performance TAT mensual del centro seleccionado. Eje temporal: fecha_recepcion_final.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tabla.empty:
        st.info("No hay datos evaluables para este centro con los filtros actuales.")
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
    plot["Orden"] = plot["Estado"].map({"Cumple": 1, "No Cumple": 2}).fillna(9)

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
                alt.Tooltip("periodo_label:N", title="Mes recepción"),
                alt.Tooltip("Estado:N", title="Estado"),
                alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
                alt.Tooltip("Porcentaje:Q", title="Porcentaje", format=".1f"),
                alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f"),
            ],
        )
    )

    linea_meta = (
        alt.Chart(pd.DataFrame({"Meta": [META_CUMPLIMIENTO]}))
        .mark_rule(color=COLOR_META, strokeDash=[6, 4], strokeWidth=2)
        .encode(y=alt.Y("Meta:Q"))
    )

    chart = (
        (barras + linea_meta)
        .properties(height=230)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def grafico_temporal_porcentual_centros(
    df: pd.DataFrame,
    centros_sel: list[str],
    mapa_etiquetas: dict,
):
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown("<div class='chart-title'>Performance temporal porcentual por centro</div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class='chart-caption'>
            Evolución mensual del porcentaje de cumplimiento para los centros seleccionados.
        </div>
        """,
        unsafe_allow_html=True,
    )

    registros = []

    for centro in centros_sel:
        tabla = crear_resumen_mensual_centro(df, centro)

        if tabla.empty:
            continue

        tabla = tabla[tabla["Total"].gt(0)].copy()

        if tabla.empty:
            continue

        tabla["Centro"] = etiqueta_centro(centro, mapa_etiquetas)
        registros.append(tabla)

    if not registros:
        st.info("No hay datos evaluables para graficar los centros seleccionados.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    plot = pd.concat(registros, ignore_index=True)
    plot = plot.sort_values(["periodo_fecha", "Centro"]).copy()

    linea_performance = (
        alt.Chart(plot)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X(
                "periodo_fecha:T",
                title="Mes recepción",
                axis=alt.Axis(format="%b %Y", labelAngle=0),
            ),
            y=alt.Y(
                "% Cumple:Q",
                title="% Cumplimiento",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(labelExpr="datum.value + '%'"),
            ),
            color=alt.Color(
                "Centro:N",
                legend=alt.Legend(title=None, orient="top", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes recepción"),
                alt.Tooltip("Centro:N", title="Centro"),
                alt.Tooltip("% Cumple:Q", title="% Cumplimiento", format=".1f"),
                alt.Tooltip("Cumple:Q", title="Cumple", format=",.0f"),
                alt.Tooltip("No cumple:Q", title="No cumple", format=",.0f"),
                alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f"),
            ],
        )
    )

    linea_meta = (
        alt.Chart(pd.DataFrame({"Meta": [META_CUMPLIMIENTO]}))
        .mark_rule(color=COLOR_META, strokeDash=[6, 4], strokeWidth=2)
        .encode(y=alt.Y("Meta:Q"))
    )

    chart = (
        (linea_performance + linea_meta)
        .properties(height=300)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================
# TABLA DE CUMPLIMIENTO Y FILTRO SEMANAL
# =========================================================

def crear_tabla_cumplimiento_visual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea tabla resumen:
    Planta | Cumple | No Cumple | % Cumple

    Incluye fila Total.
    Solo considera estados evaluables: Cumple y No cumple.
    """
    tabla = resumen_kpis_plantas(df)

    columnas_salida = ["Planta", "Cumple", "No Cumple", "% Cumple"]

    if tabla.empty:
        return pd.DataFrame(columns=columnas_salida)

    tabla = tabla.rename(
        columns={
            "grupo_planta": "Planta",
            "No cumple": "No Cumple",
        }
    )

    for col in ["Cumple", "No Cumple", "Total evaluable", "% Cumple"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla = tabla[
        ["Planta", "Cumple", "No Cumple", "Total evaluable", "% Cumple"]
    ].copy()

    orden_plantas = {
        "Prillex": 1,
        "Rio Loa": 2,
        "Plantas de servicios": 3,
    }

    tabla["orden"] = tabla["Planta"].map(orden_plantas).fillna(99)
    tabla = tabla.sort_values("orden").drop(columns="orden")

    total_cumple = int(tabla["Cumple"].sum())
    total_no_cumple = int(tabla["No Cumple"].sum())
    total_evaluable = total_cumple + total_no_cumple

    pct_total = (
        total_cumple / total_evaluable * 100
        if total_evaluable > 0
        else 0
    )

    fila_total = pd.DataFrame(
        [
            {
                "Planta": "Total",
                "Cumple": total_cumple,
                "No Cumple": total_no_cumple,
                "Total evaluable": total_evaluable,
                "% Cumple": pct_total,
            }
        ]
    )

    tabla = pd.concat([tabla, fila_total], ignore_index=True)

    tabla["Cumple"] = tabla["Cumple"].astype(int)
    tabla["No Cumple"] = tabla["No Cumple"].astype(int)
    tabla["% Cumple"] = tabla["% Cumple"].round(0)

    return tabla[["Planta", "Cumple", "No Cumple", "% Cumple"]]


def mostrar_tabla_cumplimiento_visual(df: pd.DataFrame):
    """
    Muestra tabla nativa de Streamlit, sin HTML para la tabla.
    """
    tabla = crear_tabla_cumplimiento_visual(df)

    if tabla.empty:
        st.info("No hay datos evaluables para construir la tabla de cumplimiento.")
        return

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Planta": st.column_config.TextColumn(
                "Planta",
                width="medium",
            ),
            "Cumple": st.column_config.NumberColumn(
                "Cumple",
                format="%d",
                width="small",
            ),
            "No Cumple": st.column_config.NumberColumn(
                "No Cumple",
                format="%d",
                width="small",
            ),
            "% Cumple": st.column_config.ProgressColumn(
                "% Cumple",
                format="%.0f%%",
                min_value=0,
                max_value=100,
                width="medium",
            ),
        },
    )


def obtener_rango_fechas_semana_iso(anio_iso: int, semana_iso: int):
    """
    Devuelve lunes y domingo de una semana ISO.
    """
    inicio = pd.Timestamp(date.fromisocalendar(int(anio_iso), int(semana_iso), 1))
    fin = pd.Timestamp(date.fromisocalendar(int(anio_iso), int(semana_iso), 7))
    return inicio, fin


def crear_catalogo_semanas_disponibles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Crea una tabla auxiliar para mostrar qué semanas ISO existen
    en los datos filtrados actuales.
    """
    columnas_requeridas = [
        "anio_iso_recepcion",
        "semana_iso_recepcion",
        COL_FECHA_RECEPCION_FINAL,
    ]

    if df.empty or any(col not in df.columns for col in columnas_requeridas):
        return pd.DataFrame(
            columns=[
                "Año",
                "Semana",
                "Desde",
                "Hasta",
                "Registros",
            ]
        )

    base = df[
        df["anio_iso_recepcion"].notna()
        & df["semana_iso_recepcion"].notna()
        & df[COL_FECHA_RECEPCION_FINAL].notna()
    ].copy()

    if base.empty:
        return pd.DataFrame(
            columns=[
                "Año",
                "Semana",
                "Desde",
                "Hasta",
                "Registros",
            ]
        )

    catalogo = (
        base
        .groupby(["anio_iso_recepcion", "semana_iso_recepcion"])
        .agg(
            Desde=(COL_FECHA_RECEPCION_FINAL, "min"),
            Hasta=(COL_FECHA_RECEPCION_FINAL, "max"),
            Registros=(COL_FECHA_RECEPCION_FINAL, "size"),
        )
        .reset_index()
        .rename(
            columns={
                "anio_iso_recepcion": "Año",
                "semana_iso_recepcion": "Semana",
            }
        )
    )

    catalogo["Año"] = catalogo["Año"].astype(int)
    catalogo["Semana"] = catalogo["Semana"].astype(int)
    catalogo["Desde"] = catalogo["Desde"].dt.strftime("%d-%m-%Y")
    catalogo["Hasta"] = catalogo["Hasta"].dt.strftime("%d-%m-%Y")

    return catalogo.sort_values(["Año", "Semana"]).reset_index(drop=True)


def filtrar_por_anio_y_semana_iso(
    df: pd.DataFrame,
    anio_iso: int | None,
    rango_semanas: tuple[int, int] | list[int] | None,
) -> pd.DataFrame:
    """
    Filtra un dataframe por año ISO y rango de semanas ISO.
    """
    if df.empty:
        return df.copy()

    if anio_iso is None or rango_semanas is None:
        return df.copy()

    if "anio_iso_recepcion" not in df.columns or "semana_iso_recepcion" not in df.columns:
        return df.copy()

    semana_inicio = int(rango_semanas[0])
    semana_fin = int(rango_semanas[1])

    data = df[
        df["anio_iso_recepcion"].eq(int(anio_iso))
        & df["semana_iso_recepcion"].between(semana_inicio, semana_fin)
    ].copy()

    return data


def selector_filtro_semanal_tabla(df: pd.DataFrame) -> pd.DataFrame:
    """
    Selector específico para filtrar solo la tabla de cumplimiento por plantas.
    No afecta los demás gráficos del dashboard.
    """
    if df.empty:
        return df.copy()

    if "anio_iso_recepcion" not in df.columns or "semana_iso_recepcion" not in df.columns:
        st.warning("No existen columnas de año/semana ISO para aplicar este filtro.")
        return df.copy()

    usar_filtro = st.checkbox(
        "Filtrar esta tabla por año y semana ISO",
        value=False,
        key="usar_filtro_semana_tabla_plantas",
    )

    if not usar_filtro:
        return df.copy()

    catalogo = crear_catalogo_semanas_disponibles(df)

    if catalogo.empty:
        st.info("No hay semanas disponibles con los filtros actuales.")
        return df.copy()

    anios_disponibles = sorted(
        catalogo["Año"].dropna().astype(int).unique().tolist()
    )

    anio_sel = st.selectbox(
        "Año ISO",
        options=anios_disponibles,
        index=len(anios_disponibles) - 1,
        key="anio_iso_tabla_plantas",
    )

    catalogo_anio = catalogo[catalogo["Año"].eq(int(anio_sel))].copy()

    semanas_disponibles = sorted(
        catalogo_anio["Semana"].dropna().astype(int).unique().tolist()
    )

    semana_min = min(semanas_disponibles)
    semana_max = max(semanas_disponibles)

    rango_semanas = st.slider(
        "Rango de semanas ISO",
        min_value=semana_min,
        max_value=semana_max,
        value=(semana_min, semana_max),
        step=1,
        key="rango_semanas_tabla_plantas",
    )

    fecha_inicio_semana, _ = obtener_rango_fechas_semana_iso(
        anio_sel,
        rango_semanas[0],
    )
    _, fecha_fin_semana = obtener_rango_fechas_semana_iso(
        anio_sel,
        rango_semanas[1],
    )

    st.caption(
        f"Rango seleccionado: Año {anio_sel}, semana {rango_semanas[0]} "
        f"a semana {rango_semanas[1]} · "
        f"{fecha_inicio_semana.strftime('%d-%m-%Y')} a "
        f"{fecha_fin_semana.strftime('%d-%m-%Y')}"
    )

    with st.expander("Ver semanas disponibles en los datos filtrados", expanded=False):
        st.dataframe(
            catalogo_anio,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Año": st.column_config.NumberColumn("Año", format="%d"),
                "Semana": st.column_config.NumberColumn("Semana", format="%d"),
                "Registros": st.column_config.NumberColumn("Registros", format="%d"),
            },
        )

    return filtrar_por_anio_y_semana_iso(
        df=df,
        anio_iso=anio_sel,
        rango_semanas=rango_semanas,
    )


# =========================================================
# FUNCIONES COMPLEMENTARIAS
# =========================================================

def obtener_maestro_centros_df() -> pd.DataFrame:
    maestro = pd.DataFrame(CENTROS_MAESTRO).copy()
    maestro["Centro"] = maestro["Centro"].astype(str).str.strip()
    maestro["Etiqueta"] = maestro["Centro"] + " — " + maestro["Nombre"]
    return maestro


def obtener_mapa_etiquetas_centros() -> dict:
    maestro = obtener_maestro_centros_df()
    return dict(zip(maestro["Centro"], maestro["Etiqueta"]))


def etiqueta_centro(codigo: str, mapa_etiquetas: dict | None = None) -> str:
    codigo = str(codigo).strip()
    mapa = mapa_etiquetas if mapa_etiquetas is not None else obtener_mapa_etiquetas_centros()
    return mapa.get(codigo, f"{codigo} — Sin nombre en maestro")


def mostrar_exploracion_centros_opcional(
    df_final: pd.DataFrame,
    fecha_facturacion_desde,
    estados_tat_sel,
    rango_recepcion,
    centros_disponibles: list[str],
    centros_opciones: list[str],
    mapa_label_a_centro: dict,
    mapa_etiquetas_centros: dict,
):
    with st.expander("Análisis opcional por centro específico", expanded=False):
        st.caption(
            "Esta sección no cambia los gráficos principales. Sirve para revisar uno o más centros puntuales con los mismos filtros generales de fecha y Performance TAT."
        )

        centros_labels_sel = st.multiselect(
            "Centros específicos opcionales",
            options=centros_opciones,
            default=[],
            help="Selecciona uno o más centros en formato código — nombre.",
        )

        centros_sel = [
            mapa_label_a_centro[label]
            for label in centros_labels_sel
            if label in mapa_label_a_centro
        ]

        if not centros_sel:
            st.info("Selecciona un centro para ver su performance particular.")
            return

        df_centros = aplicar_filtros_dashboard(
            df=df_final,
            fecha_facturacion_desde=fecha_facturacion_desde,
            estados_tat_sel=estados_tat_sel,
            grupos_sel=[],
            centros_sel=centros_sel,
            rango_recepcion=rango_recepcion,
        )

        if df_centros.empty:
            st.warning("No hay datos para los centros seleccionados con los filtros actuales.")
            return

        resumen = []

        for centro in centros_sel:
            data_centro = df_centros[
                df_centros["centro_grafico"].astype(str).str.strip().eq(str(centro).strip())
            ]

            cumple = int(data_centro[COL_PERFORMANCE_TAT].eq("Cumple").sum())
            no_cumple = int(data_centro[COL_PERFORMANCE_TAT].eq("No cumple").sum())
            total = cumple + no_cumple
            pct = cumple / total * 100 if total else 0

            resumen.append({
                "Centro": etiqueta_centro(centro, mapa_etiquetas_centros),
                "Cumple": cumple,
                "No cumple": no_cumple,
                "Total evaluable": total,
                "% Cumple": pct,
            })

        resumen_df = pd.DataFrame(resumen)

        st.dataframe(
            resumen_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "% Cumple": st.column_config.NumberColumn("% Cumple", format="%.1f%%"),
            },
        )

        grafico_temporal_porcentual_centros(
            df_centros,
            centros_sel,
            mapa_etiquetas_centros,
        )

        for centro in centros_sel:
            grafico_mensual_100_centro(
                crear_resumen_mensual_centro(df_centros, centro),
                f"Performance TAT {etiqueta_centro(centro, mapa_etiquetas_centros)}",
            )


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


def mostrar_maestro_centros_colapsable():
    with st.expander("Ver maestro de centros", expanded=False):
        st.dataframe(
            obtener_maestro_centros_df()[["Centro", "Sociedad", "Nombre"]],
            use_container_width=True,
            hide_index=True,
        )


def formatear_fecha(valor) -> str:
    if valor is None:
        return "Sin definir"

    try:
        fecha = pd.Timestamp(valor)
        if pd.isna(fecha):
            return "Sin definir"
        return fecha.strftime("%d-%m-%Y")
    except Exception:
        return str(valor)


def formatear_lista(valores) -> str:
    if valores is None:
        return "Todos"

    if isinstance(valores, (list, tuple, set)):
        valores = list(valores)
        return ", ".join([str(v) for v in valores]) if valores else "Ninguno"

    return str(valores)


def describir_filtros_aplicados(
    fecha_facturacion_desde,
    estados_tat_sel,
    grupos_sel,
    centros_sel,
    rango_recepcion,
) -> pd.DataFrame:
    if isinstance(rango_recepcion, (tuple, list)) and len(rango_recepcion) == 2:
        rango_texto = (
            f"{formatear_fecha(rango_recepcion[0])} a "
            f"{formatear_fecha(rango_recepcion[1])}"
        )
    else:
        rango_texto = "Sin filtro de rango"

    filtros = [
        {
            "Filtro": "Fecha facturación",
            "Criterio aplicado": f"fecha_facturacion_final > {formatear_fecha(fecha_facturacion_desde)}",
        },
        {
            "Filtro": "Performance TAT",
            "Criterio aplicado": formatear_lista(estados_tat_sel),
        },
        {
            "Filtro": "Grupos a mostrar",
            "Criterio aplicado": formatear_lista(grupos_sel),
        },
        {
            "Filtro": "Fecha recepción",
            "Criterio aplicado": rango_texto,
        },
        {
            "Filtro": "Exclusión automática",
            "Criterio aplicado": "Se excluye grupo_planta = Excluir",
        },
    ]

    if centros_sel:
        filtros.append(
            {
                "Filtro": "Centros específicos",
                "Criterio aplicado": formatear_lista(centros_sel),
            }
        )

    return pd.DataFrame(filtros)


def calcular_mejor_planta(df: pd.DataFrame):
    kpis = resumen_kpis_plantas(df)

    if kpis.empty:
        return None

    kpis = kpis[kpis["Total evaluable"].gt(0)].copy()

    if kpis.empty:
        return None

    return kpis.sort_values(
        ["% Cumple", "Total evaluable"],
        ascending=[False, False],
    ).iloc[0]


def calcular_peor_planta(df: pd.DataFrame):
    kpis = resumen_kpis_plantas(df)

    if kpis.empty:
        return None

    kpis = kpis[kpis["Total evaluable"].gt(0)].copy()

    if kpis.empty:
        return None

    return kpis.sort_values(
        ["% Cumple", "Total evaluable"],
        ascending=[True, False],
    ).iloc[0]


def resumen_cumplimiento_plantas(df: pd.DataFrame) -> pd.DataFrame:
    kpis = resumen_kpis_plantas(df)

    if kpis.empty:
        return pd.DataFrame(
            columns=[
                "Planta",
                "Cumple",
                "No cumple",
                "Total evaluable",
                "% Cumplimiento",
            ]
        )

    tabla = kpis.rename(
        columns={
            "grupo_planta": "Planta",
            "% Cumple": "% Cumplimiento",
        }
    )

    columnas = [
        "Planta",
        "Cumple",
        "No cumple",
        "Total evaluable",
        "% Cumplimiento",
    ]

    tabla = tabla[columnas].copy()
    tabla["% Cumplimiento"] = tabla["% Cumplimiento"].round(1)

    return tabla.sort_values("% Cumplimiento", ascending=False).reset_index(drop=True)


def calcular_mejor_mes_planta(df: pd.DataFrame):
    registros = []

    for grupo in ["Prillex", "Rio Loa", "Plantas de servicios"]:
        tabla = crear_resumen_mensual_grupo(df, grupo)

        if tabla.empty:
            continue

        tabla = tabla[tabla["Total"].gt(0)].copy()

        if tabla.empty:
            continue

        tabla["grupo_planta"] = grupo
        registros.append(tabla)

    if not registros:
        return None

    mensual = pd.concat(registros, ignore_index=True)

    return mensual.sort_values(
        ["% Cumple", "Total", "periodo_fecha"],
        ascending=[False, False, True],
    ).iloc[0]


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
# 3) Leer dataframe global cargado previamente
# ---------------------------------------------------------
st.subheader("Archivo")

if "df_tat" not in st.session_state:
    st.warning("Primero debes cargar el archivo base en Análisis TAT > Cargar archivo.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

st.success(f"Archivo activo: {nombre_archivo}")

# ---------------------------------------------------------
# 4) Procesar dataframe global y crear filtros modificables
# ---------------------------------------------------------
try:
    with st.spinner("Aplicando lógica de performance y agrupación de plantas..."):
        df_final = aplicar_logica_performance_plantas(df_original)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    section_header(
        "Filtros del dashboard",
        "Los filtros se aplican antes de calcular indicadores, rankings y gráficos.",
    )

    estados_disponibles = [
        estado
        for estado in [
            "Cumple",
            "No cumple",
            "En proceso",
            "No aplica al análisis",
            "Sin datos",
        ]
        if estado in df_final[COL_PERFORMANCE_TAT]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    ]

    estados_default = [
        estado
        for estado in ["Cumple", "No cumple"]
        if estado in estados_disponibles
    ]

    grupos_todos = ["Prillex", "Rio Loa", "Plantas de servicios"]

    grupos_disponibles = [
        grupo
        for grupo in grupos_todos
        if grupo in df_final["grupo_planta"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    ]

    centros_disponibles = sorted(
        df_final[
            df_final["grupo_planta"].ne("Excluir")
        ]["centro_grafico"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    mapa_etiquetas_centros = obtener_mapa_etiquetas_centros()
    centros_opciones = [
        etiqueta_centro(centro, mapa_etiquetas_centros)
        for centro in centros_disponibles
    ]
    mapa_label_a_centro = dict(zip(centros_opciones, centros_disponibles))

    fechas_recepcion_validas = df_final[COL_FECHA_RECEPCION_FINAL].dropna()

    grupos_default = grupos_disponibles if grupos_disponibles else grupos_todos

    f1, f2 = st.columns(2)

    with f1:
        fecha_facturacion_desde = st.date_input(
            "Fecha facturación posterior a",
            value=FECHA_FILTRO_FACTURACION_DEFAULT.date(),
            help="Este filtro usa fecha_facturacion_final. No modifica el eje temporal.",
        )

    with f2:
        estados_tat_sel = st.multiselect(
            "Performance TAT",
            options=estados_disponibles,
            default=estados_default,
        )

    grupos_sel = st.multiselect(
        "Grupos a mostrar",
        options=grupos_todos,
        default=grupos_default,
        help="Por defecto muestra Prillex, Rio Loa y Plantas de servicios.",
    )

    centros_sel = None
    centros_sel_descripcion = []

    if not fechas_recepcion_validas.empty:
        fecha_recepcion_min = fechas_recepcion_validas.min().date()
        fecha_recepcion_max = fechas_recepcion_validas.max().date()

        rango_recepcion = st.date_input(
            "Fecha recepción para eje temporal",
            value=(fecha_recepcion_min, fecha_recepcion_max),
            min_value=fecha_recepcion_min,
            max_value=fecha_recepcion_max,
            help="Este rango usa fecha_recepcion_final. También es la fecha del eje X.",
        )
    else:
        rango_recepcion = None
        st.warning("No hay fechas válidas de recepción.")

    mostrar_maestro_centros_colapsable()

    st.markdown("</div>", unsafe_allow_html=True)

    with st.spinner("Aplicando filtros del dashboard..."):
        df_dashboard = aplicar_filtros_dashboard(
            df=df_final,
            fecha_facturacion_desde=fecha_facturacion_desde,
            estados_tat_sel=estados_tat_sel,
            grupos_sel=grupos_sel,
            centros_sel=centros_sel,
            rango_recepcion=rango_recepcion,
        )

    if df_dashboard.empty:
        st.warning("No hay datos después de aplicar los filtros seleccionados.")
        st.stop()

    st.success("Performance de Plantas generada correctamente.")

    # -----------------------------------------------------
    # 5) Dashboard
    # -----------------------------------------------------
    tab_dashboard, tab_datos = st.tabs(["Dashboard", "Datos"])

    with tab_dashboard:
        total_original = len(df_original)
        total_filas = len(df_dashboard)
        cumple_tat = int(df_dashboard[COL_PERFORMANCE_TAT].eq("Cumple").sum())
        no_cumple_tat = int(df_dashboard[COL_PERFORMANCE_TAT].eq("No cumple").sum())
        evaluables_tat = cumple_tat + no_cumple_tat
        pct_cumple_tat = cumple_tat / evaluables_tat * 100 if evaluables_tat else 0

        mejor_planta = calcular_mejor_planta(df_dashboard)
        peor_planta = calcular_peor_planta(df_dashboard)
        mejor_mes = calcular_mejor_mes_planta(df_dashboard)

        # =================================================
        # 1) Respuestas clave
        # =================================================
        section_header(
            "Respuestas clave",
            "Resumen ejecutivo del desempeño con los filtros actuales.",
        )

        r1, r2, r3, r4 = st.columns(4)

        with r1:
            card_metric(
                "Cumplimiento global",
                f"{pct_cumple_tat:.1f}%",
                f"Cumple: {cumple_tat:,} · No cumple: {no_cumple_tat:,}",
            )

        with r2:
            if mejor_planta is not None:
                card_metric(
                    "Mejor planta promedio",
                    str(mejor_planta["grupo_planta"]),
                    (
                        f"{float(mejor_planta['% Cumple']):.1f}% cumplimiento · "
                        f"Total evaluable: {int(mejor_planta['Total evaluable']):,}"
                    ),
                )
            else:
                card_metric(
                    "Mejor planta promedio",
                    "Sin datos",
                    "No hay registros evaluables.",
                )

        with r3:
            if peor_planta is not None:
                card_metric(
                    "Planta con mayor brecha",
                    str(peor_planta["grupo_planta"]),
                    (
                        f"{float(peor_planta['% Cumple']):.1f}% cumplimiento · "
                        f"Total evaluable: {int(peor_planta['Total evaluable']):,}"
                    ),
                )
            else:
                card_metric(
                    "Planta con mayor brecha",
                    "Sin datos",
                    "No hay registros evaluables.",
                )

        with r4:
            if mejor_mes is not None:
                card_metric(
                    "Mejor mes y planta",
                    str(mejor_mes["periodo_label"]),
                    (
                        f"{str(mejor_mes['grupo_planta'])} · "
                        f"{float(mejor_mes['% Cumple']):.1f}% cumplimiento · "
                        f"Total: {int(mejor_mes['Total']):,}"
                    ),
                )
            else:
                card_metric(
                    "Mejor mes y planta",
                    "Sin datos",
                    "No hay registros evaluables.",
                )

        st.divider()

        # =================================================
        # 2) Filtros aplicados
        # =================================================
        section_header(
            "Filtros aplicados",
            "Criterios usados para calcular todos los indicadores y visualizaciones.",
        )

        st.dataframe(
            describir_filtros_aplicados(
                fecha_facturacion_desde=fecha_facturacion_desde,
                estados_tat_sel=estados_tat_sel,
                grupos_sel=grupos_sel,
                centros_sel=centros_sel_descripcion,
                rango_recepcion=rango_recepcion,
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()

        # =================================================
        # 3) Cumplimiento a nivel plantas
        # =================================================
        section_header(
            "Cumplimiento a nivel de plantas",
            "Resumen evaluable por planta. Puedes filtrar esta visualización por año y semana ISO.",
        )

        df_tabla_cumplimiento = selector_filtro_semanal_tabla(df_dashboard)

        mostrar_tabla_cumplimiento_visual(df_tabla_cumplimiento)

        st.caption(
            f"Meta referencial de cumplimiento: {META_CUMPLIMIENTO}%."
        )

        st.divider()

        # =================================================
        # 4) Indicadores generales
        # =================================================
        section_header(
            "Indicadores generales",
            "Vista general del volumen de datos usado en el análisis.",
        )

        k1, k2, k3, k4 = st.columns(4)

        with k1:
            card_metric(
                "Datos originales",
                f"{total_original:,}",
                "Registros antes de aplicar filtros.",
            )

        with k2:
            card_metric(
                "Registros filtrados",
                f"{total_filas:,}",
                "Registros que quedan después de filtros.",
            )

        with k3:
            card_metric(
                "TAT evaluable",
                f"{evaluables_tat:,}",
                "Solo Cumple y No cumple.",
            )

        with k4:
            card_metric(
                "No cumplimiento",
                f"{no_cumple_tat:,}",
                (
                    f"{(no_cumple_tat / evaluables_tat * 100):.1f}% del total evaluable"
                    if evaluables_tat
                    else "Sin registros evaluables."
                ),
            )

        st.divider()

        # =================================================
        # 5) Gráfico general
        # =================================================
        section_header(
            "Evolución general del cumplimiento",
            "Comparación mensual del porcentaje de cumplimiento por grupo de planta.",
        )

        grafico_temporal_porcentual_performance(df_dashboard)

        st.divider()

        # =================================================
        # 6) Gráficos específicos por planta
        # =================================================
        section_header(
            "Detalle mensual por planta",
            "Vista mensual 100% apilada de Cumple y No Cumple.",
        )

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

        st.divider()

        # =================================================
        # 7) Análisis opcional por centro
        # =================================================
        section_header(
            "Análisis específico por centro",
            "Profundización opcional para revisar centros puntuales.",
        )

        mostrar_exploracion_centros_opcional(
            df_final=df_final,
            fecha_facturacion_desde=fecha_facturacion_desde,
            estados_tat_sel=estados_tat_sel,
            rango_recepcion=rango_recepcion,
            centros_disponibles=centros_disponibles,
            centros_opciones=centros_opciones,
            mapa_label_a_centro=mapa_label_a_centro,
            mapa_etiquetas_centros=mapa_etiquetas_centros,
        )

        if mostrar_diagnostico_check:
            st.divider()
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

        df_dashboard_vista = df_dashboard.copy()
        df_dashboard_vista["centro_nombre"] = df_dashboard_vista["centro_grafico"].apply(
            lambda centro: etiqueta_centro(centro, mapa_etiquetas_centros)
        )

        columnas_preferidas = [
            "grupo_planta",
            "centro_grafico",
            "centro_nombre",
            COL_FECHA_SOLICITUD_FINAL,
            COL_FECHA_FACTURACION_FINAL,
            COL_FECHA_RECEPCION_FINAL,
            "anio_iso_recepcion",
            "semana_iso_recepcion",
            "semana_iso_label",
            "tipo_oc",
            "dias_tat_total",
            COL_PERFORMANCE_TAT,
            "periodo_fecha",
            "periodo_label",
        ]

        columnas_preferidas = [
            col for col in columnas_preferidas
            if col in df_dashboard_vista.columns
        ]

        st.dataframe(
            df_dashboard_vista[columnas_preferidas].head(300),
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
