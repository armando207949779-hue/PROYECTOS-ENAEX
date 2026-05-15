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

st.set_page_config(
    page_title="Performance TAT 2025",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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
]

COLOR_CUMPLE = "#606060"
COLOR_NO_CUMPLE = "#EF3E52"
COLOR_SIN_DATOS = "#BFC3C7"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"
COLOR_BG = "#F3F4F6"
COLOR_CARD = "#FFFFFF"

MESES_NOMBRE = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

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

COLUMNAS_NUEVAS_ORDENADAS = [
    "tipo_oc", "origen", "sistema", "nombre_tipo_compra", "monto",
    "dias_liberacion_solped", "dias_comprador", "dias_liberacion_pedido",
    "dias_proveedor", "dias_logistica", "dias_tat_total",
    "umbral_liberacion_solped", "umbral_comprador", "umbral_liberacion_pedido",
    "umbral_proveedor", "umbral_logistica", "umbral_tat_total",
    "performance_liberacion_solped", "performance_comprador", "performance_liberacion_pedido",
    "performance_proveedor", "performance_logistica", "performance_tat_total",
    "tiene_fechas_inconsistentes", "dias_incumplimiento_tat", "incumplimiento_tat",
    "rango_incumplimiento_tat",
]

ETAPAS_DASHBOARD = [
    {
        "titulo": "Lib SolPed",
        "titulo_largo": "Cumplimiento Lib SolPed",
        "col_perf": "performance_liberacion_solped",
        "col_dias": "dias_liberacion_solped",
        "regla": "Nacional e Internacional ≤ 2 días",
    },
    {
        "titulo": "Comprador",
        "titulo_largo": "Cumplimiento Comprador",
        "col_perf": "performance_comprador",
        "col_dias": "dias_comprador",
        "regla": "Nacional e Internacional ≤ 10 días",
    },
    {
        "titulo": "Proveedor",
        "titulo_largo": "Cumplimiento Proveedor",
        "col_perf": "performance_proveedor",
        "col_dias": "dias_proveedor",
        "regla": "Nacional ≤ 20 días · Internacional ≤ 60 días",
    },
    {
        "titulo": "Logística",
        "titulo_largo": "Cumplimiento Logística",
        "col_perf": "performance_logistica",
        "col_dias": "dias_logistica",
        "regla": "Nacional e Internacional ≤ 11 días",
    },
]

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
            div[data-testid="stToolbar"] {{
                visibility: hidden;
                height: 0%;
                position: fixed;
            }}
            .block-container {{
                padding-top: 1rem;
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
            .stage-card {{
                background: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 18px;
                padding: 14px;
                box-shadow: 0 8px 18px rgba(15, 23, 42, 0.04);
            }}
            .stage-title {{
                text-align: center;
                font-size: 15px;
                font-weight: 800;
                color: {COLOR_TEXTO};
                margin-bottom: 2px;
            }}
            .stage-rule {{
                text-align: center;
                font-size: 10.5px;
                color: {COLOR_MUTED};
                min-height: 30px;
                margin-bottom: 4px;
            }}
            .stage-days {{
                text-align: center;
                font-size: 30px;
                color: {COLOR_TEXTO};
                font-weight: 850;
                line-height: 1;
                margin-top: 4px;
            }}
            .stage-days-label {{
                text-align: center;
                color: {COLOR_MUTED};
                font-size: 11px;
                margin-top: 4px;
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


def mostrar_logo(ancho: int = 170):
    logo_path = encontrar_logo()
    if logo_path is None:
        st.markdown(
            """
            <div style="font-weight:850;font-size:30px;color:#374151;line-height:1;">Enaex</div>
            <div style="font-size:9px;color:#6B7280;font-weight:700;letter-spacing:.08em;">STRONGER BONDS</div>
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
        <img src="data:{mime};base64,{logo_base64}" width="{ancho}">
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
# LECTURA Y PREPARACIÓN
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;):" or separador_csv == "Punto y coma (;)":
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
    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)
        try:
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="utf-8-sig", on_bad_lines="skip")
        except Exception:
            buffer.seek(0)
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="latin1", on_bad_lines="skip")

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def validar_columnas_requeridas(df: pd.DataFrame):
    faltantes = [col for col in COLUMNAS_REQUERIDAS_PERFORMANCE if col not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas para calcular Performance TAT: {faltantes}")


def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie, errors="coerce")
    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")
    mask_num = serie_num.notna()

    if mask_num.any():
        mask_ms = mask_num & serie_num.abs().ge(10**11)
        mask_s = mask_num & serie_num.abs().lt(10**11)
        if mask_ms.any():
            resultado.loc[mask_ms] = pd.to_datetime(serie_num.loc[mask_ms], unit="ms", errors="coerce")
        if mask_s.any():
            resultado.loc[mask_s] = pd.to_datetime(serie_num.loc[mask_s], unit="s", errors="coerce")

    mask_no_num = ~mask_num
    if mask_no_num.any():
        resultado.loc[mask_no_num] = pd.to_datetime(serie.loc[mask_no_num], errors="coerce", dayfirst=True)

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
    return texto[:2] if len(texto) >= 2 else pd.NA


def diferencia_dias(fecha_fin: pd.Series, fecha_inicio: pd.Series) -> pd.Series:
    return (fecha_fin - fecha_inicio).dt.days


def evaluar_performance_basica(dias: pd.Series, umbral: pd.Series, texto_sin_dato="No aplica", negativos_no_aplican=True) -> pd.Series:
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
    resultado = pd.Series("Sin datos", index=df.index, dtype="object")
    mask_negativos = df["tiene_fechas_inconsistentes"].eq(True)
    mask_en_proceso = df["dias_tat_total"].isna()
    mask_tipo_nacional = df["tipo_oc"].isin(["35", "45"])
    mask_tipo_internacional = df["tipo_oc"].eq("47")
    mask_tipo_valido = df["tipo_oc"].isin(["35", "45", "47"])

    resultado.loc[mask_negativos] = "No aplica al análisis"
    resultado.loc[~mask_negativos & mask_en_proceso] = "En proceso"
    mask_evaluable = ~mask_negativos & ~mask_en_proceso

    resultado.loc[mask_evaluable & mask_tipo_nacional & df["dias_tat_total"].le(40)] = "Cumple"
    resultado.loc[mask_evaluable & mask_tipo_internacional & df["dias_tat_total"].le(70)] = "Cumple"
    resultado.loc[
        mask_evaluable & mask_tipo_valido & (
            (mask_tipo_nacional & df["dias_tat_total"].gt(40)) |
            (mask_tipo_internacional & df["dias_tat_total"].gt(70))
        )
    ] = "No cumple"
    return resultado


def calcular_dias_incumplimiento_tat(dias_tat: pd.Series, umbral_tat: pd.Series) -> pd.Series:
    diferencia = dias_tat - umbral_tat
    resultado = diferencia.where(diferencia > 0, 0)
    return resultado.mask(dias_tat.isna() | umbral_tat.isna(), np.nan)


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
            ["Sin datos", "Sin incumplimiento", "1-5 días", "6-15 días", "16-30 días", "Mayor a un mes"],
            default="Sin datos",
        ),
        index=dias_incumplimiento.index,
    )


@st.cache_data(show_spinner=False)
def aplicar_logica_performance(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    validar_columnas_requeridas(df)

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
        [bool_array(df["tipo_oc"].isin(["35", "45"])), bool_array(df["tipo_oc"].eq("47"))],
        ["Nacional", "Internacional"],
        default="Otro",
    )
    df["sistema"] = np.select(
        [bool_array(df["tipo_oc"].eq("35")), bool_array(df["tipo_oc"].isin(["45", "47"]))],
        ["Ariba", "ERP"],
        default="Otro",
    )

    if COL_TIPO_COMPRA_ARIBA in df.columns:
        tipo_compra_num = pd.to_numeric(df[COL_TIPO_COMPRA_ARIBA], errors="coerce")
    else:
        tipo_compra_num = pd.Series(np.nan, index=df.index)

    df["nombre_tipo_compra"] = np.select(
        [bool_array(tipo_compra_num.eq(1)), bool_array(tipo_compra_num.eq(2)), bool_array(tipo_compra_num.eq(3))],
        ["Catalogada", "No catalogada", "Directa"],
        default="Otro",
    )

    if COL_CANTIDAD_SOLICITADA in df.columns and COL_PRECIO_VALORACION in df.columns:
        df["monto"] = pd.to_numeric(df[COL_CANTIDAD_SOLICITADA], errors="coerce") * pd.to_numeric(df[COL_PRECIO_VALORACION], errors="coerce")
    else:
        df["monto"] = np.nan

    df["dias_liberacion_solped"] = diferencia_dias(df[COL_FECHA_LIBERACION_FINAL], df[COL_FECHA_SOLICITUD_FINAL])
    df["dias_comprador"] = diferencia_dias(df[COL_FECHA_PEDIDO_FINAL], df[COL_FECHA_LIBERACION_FINAL])
    df["dias_liberacion_pedido"] = np.nan
    df["dias_proveedor"] = diferencia_dias(df[COL_FECHA_FACTURACION_FINAL], df[COL_FECHA_PEDIDO_FINAL])
    df["dias_logistica"] = diferencia_dias(df[COL_FECHA_RECEPCION_FINAL], df[COL_FECHA_FACTURACION_FINAL])
    df["dias_tat_total"] = diferencia_dias(df[COL_FECHA_RECEPCION_FINAL], df[COL_FECHA_SOLICITUD_FINAL])

    df["umbral_liberacion_solped"] = 2
    df["umbral_comprador"] = 10
    df["umbral_liberacion_pedido"] = 2
    df["umbral_logistica"] = 11
    df["umbral_proveedor"] = pd.to_numeric(np.select(
        [bool_array(df["tipo_oc"].isin(["35", "45"])), bool_array(df["tipo_oc"].eq("47"))],
        [20, 60],
        default=np.nan,
    ), errors="coerce")
    df["umbral_tat_total"] = pd.to_numeric(np.select(
        [bool_array(df["tipo_oc"].isin(["35", "45"])), bool_array(df["tipo_oc"].eq("47"))],
        [40, 70],
        default=np.nan,
    ), errors="coerce")

    columnas_dias_evaluables = ["dias_liberacion_solped", "dias_comprador", "dias_liberacion_pedido", "dias_proveedor", "dias_logistica", "dias_tat_total"]
    df["tiene_fechas_inconsistentes"] = df[columnas_dias_evaluables].lt(0).any(axis=1, skipna=True)

    df["performance_liberacion_solped"] = evaluar_performance_basica(df["dias_liberacion_solped"], pd.Series(df["umbral_liberacion_solped"], index=df.index), "No aplica")
    df["performance_comprador"] = evaluar_performance_basica(df["dias_comprador"], pd.Series(df["umbral_comprador"], index=df.index), "No aplica")
    df["performance_liberacion_pedido"] = evaluar_performance_basica(pd.Series(df["dias_liberacion_pedido"], index=df.index), pd.Series(df["umbral_liberacion_pedido"], index=df.index), "Sin datos")
    df["performance_proveedor"] = evaluar_performance_basica(df["dias_proveedor"], df["umbral_proveedor"], "Sin datos")
    df["performance_logistica"] = evaluar_performance_basica(df["dias_logistica"], pd.Series(df["umbral_logistica"], index=df.index), "No aplica")
    df["performance_tat_total"] = evaluar_performance_tat(df)

    df["dias_incumplimiento_tat"] = calcular_dias_incumplimiento_tat(df["dias_tat_total"], df["umbral_tat_total"])
    df["incumplimiento_tat"] = df["dias_incumplimiento_tat"].gt(0)
    df["rango_incumplimiento_tat"] = calcular_rango_incumplimiento_tat(df["dias_incumplimiento_tat"])

    df["periodo_fecha"] = df[COL_FECHA_RECEPCION_FINAL].dt.to_period("M").dt.to_timestamp()
    df["anio"] = df[COL_FECHA_RECEPCION_FINAL].dt.year
    df["mes_num"] = df[COL_FECHA_RECEPCION_FINAL].dt.month
    df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)
    df["periodo_label"] = np.where(
        df["anio"].notna() & df["mes_nombre"].notna(),
        df["mes_nombre"].astype(str) + " " + df["anio"].astype("Int64").astype(str),
        pd.NA,
    )
    return df


def reordenar_columnas_performance_al_final(df: pd.DataFrame) -> pd.DataFrame:
    columnas_finales = [col for col in COLUMNAS_NUEVAS_ORDENADAS if col in df.columns]
    columnas_base = [col for col in df.columns if col not in columnas_finales]
    return df[columnas_base + columnas_finales].copy()

# =========================================================
# RESÚMENES Y GRÁFICOS
# =========================================================

def resumen_performance(df: pd.DataFrame) -> pd.DataFrame:
    metricas = [
        ("performance_liberacion_solped", "Liberación SolPed", "Tiempo entre solicitud y liberación de la SolPed."),
        ("performance_comprador", "Comprador", "Tiempo entre liberación de SolPed y creación/emisión del pedido."),
        ("performance_liberacion_pedido", "Liberación Pedido", "No se calcula actualmente porque no hay inputs disponibles."),
        ("performance_proveedor", "Proveedor", "Tiempo entre pedido y facturación."),
        ("performance_logistica", "Logística", "Tiempo entre facturación y recepción de mercancía."),
        ("performance_tat_total", "TAT Total", "Tiempo punta a punta desde solicitud hasta recepción."),
    ]
    data = []
    for col, metrica, descripcion in metricas:
        if col not in df.columns:
            continue
        serie = df[col].astype("object")
        cumple = int(serie.eq("Cumple").sum())
        no_cumple = int(serie.eq("No cumple").sum())
        no_aplica = int(serie.isin(["No aplica", "No aplica al análisis"]).sum())
        sin_datos = int(serie.isin(["Sin datos", "En proceso"]).sum())
        total_evaluable = cumple + no_cumple
        pct_cumple = round(cumple / total_evaluable * 100, 2) if total_evaluable else 0
        data.append({
            "Métrica": metrica,
            "Descripción": descripcion,
            "Cumple": cumple,
            "No cumple": no_cumple,
            "No aplica": no_aplica,
            "Sin datos / En proceso": sin_datos,
            "Evaluables": total_evaluable,
            "% Cumple": pct_cumple,
        })
    return pd.DataFrame(data)


def tabla_inputs_formulas() -> pd.DataFrame:
    return pd.DataFrame([
        ["Liberación SolPed", "dias_liberacion_solped", COL_FECHA_SOLICITUD_FINAL, COL_FECHA_LIBERACION_FINAL, "fecha_liberacion_final - fecha_solicitud_final", "2 días"],
        ["Comprador", "dias_comprador", COL_FECHA_LIBERACION_FINAL, COL_FECHA_PEDIDO_FINAL, "fecha_pedido_final - fecha_liberacion_final", "10 días"],
        ["Liberación Pedido", "dias_liberacion_pedido", "Sin input", "Sin input", "Sin cálculo", "2 días"],
        ["Proveedor", "dias_proveedor", COL_FECHA_PEDIDO_FINAL, COL_FECHA_FACTURACION_FINAL, "fecha_facturacion_final - fecha_pedido_final", "OC 35/45 = 20; OC 47 = 60"],
        ["Logística", "dias_logistica", COL_FECHA_FACTURACION_FINAL, COL_FECHA_RECEPCION_FINAL, "fecha_recepcion_final - fecha_facturacion_final", "11 días"],
        ["TAT Total", "dias_tat_total", COL_FECHA_SOLICITUD_FINAL, COL_FECHA_RECEPCION_FINAL, "fecha_recepcion_final - fecha_solicitud_final", "OC 35/45 = 40; OC 47 = 70"],
    ], columns=["Métrica", "Nombre técnico", "Fecha inicio", "Fecha fin", "Fórmula", "Umbral"])


def resumen_columnas_nuevas(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [col for col in COLUMNAS_NUEVAS_ORDENADAS if col in df.columns]
    return pd.DataFrame({
        "Columna nueva": columnas,
        "Nulos": [int(df[col].isna().sum()) for col in columnas],
        "% Nulos": [round(df[col].isna().mean() * 100, 2) for col in columnas],
        "Tipo dato": [str(df[col].dtype) for col in columnas],
    })


def crear_resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["performance_tat_total"].isin(["Cumple", "No cumple"]) & df["periodo_fecha"].notna()].copy()
    if base.empty:
        return pd.DataFrame()
    resumen = base.groupby(["periodo_fecha", "periodo_label", "performance_tat_total"]).size().reset_index(name="cantidad")
    tabla = resumen.pivot_table(index=["periodo_fecha", "periodo_label"], columns="performance_tat_total", values="cantidad", aggfunc="sum", fill_value=0).reset_index()
    for col in ["Cumple", "No cumple"]:
        if col not in tabla.columns:
            tabla[col] = 0
    tabla["Total"] = tabla["Cumple"] + tabla["No cumple"]
    tabla["% Cumple"] = np.where(tabla["Total"] > 0, tabla["Cumple"] / tabla["Total"] * 100, 0)
    tabla["% No cumple"] = np.where(tabla["Total"] > 0, tabla["No cumple"] / tabla["Total"] * 100, 0)
    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


def grafico_mensual_100(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay datos evaluables para el gráfico mensual.")
        return
    plot = tabla.melt(
        id_vars=["periodo_fecha", "periodo_label", "Total"],
        value_vars=["Cumple", "No cumple"],
        var_name="Estado",
        value_name="Cantidad",
    )
    plot["Porcentaje"] = np.where(plot["Total"] > 0, plot["Cantidad"] / plot["Total"] * 100, 0)
    plot["Etiqueta"] = plot["Porcentaje"].map(lambda x: f"{x:.1f}%" if x >= 4 else "")

    order = tabla["periodo_label"].tolist()
    base = alt.Chart(plot).encode(
        x=alt.X("periodo_label:N", sort=order, title=None, axis=alt.Axis(labelAngle=0, labelFontSize=11)),
        y=alt.Y("Porcentaje:Q", stack="normalize", title="% sobre evaluables", axis=alt.Axis(format="%", grid=True)),
        color=alt.Color(
            "Estado:N",
            scale=alt.Scale(domain=["Cumple", "No cumple"], range=[COLOR_CUMPLE, COLOR_NO_CUMPLE]),
            legend=alt.Legend(title=None, orient="bottom"),
        ),
        order=alt.Order("Estado:N", sort="ascending"),
        tooltip=[
            alt.Tooltip("periodo_label:N", title="Mes"),
            alt.Tooltip("Estado:N", title="Estado"),
            alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
            alt.Tooltip("Porcentaje:Q", title="Porcentaje", format=".1f"),
            alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f"),
        ],
    )

    bars = base.mark_bar(size=34, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
    text = base.mark_text(color="white", fontWeight="bold", fontSize=10).encode(text="Etiqueta:N")

    line_df = tabla[["periodo_label", "% Cumple"]].copy()
    line = alt.Chart(line_df).mark_line(point=True, strokeWidth=2, color="#111827").encode(
        x=alt.X("periodo_label:N", sort=order, title=None),
        y=alt.Y("% Cumple:Q", title="% Cumple"),
        tooltip=[alt.Tooltip("periodo_label:N", title="Mes"), alt.Tooltip("% Cumple:Q", title="% Cumple", format=".1f")],
    )

    chart = (bars + text + line).resolve_scale(y="independent").properties(height=360).configure_view(strokeWidth=0)
    st.altair_chart(chart, use_container_width=True)


def datos_etapa(df: pd.DataFrame, etapa: dict) -> dict:
    col_perf = etapa["col_perf"]
    col_dias = etapa["col_dias"]
    if col_perf not in df.columns:
        return {"cumple": 0, "no_cumple": 0, "sin_datos": 0, "total": 0, "pct": 0, "promedio": 0}
    serie = df[col_perf].astype("object")
    cumple = int(serie.eq("Cumple").sum())
    no_cumple = int(serie.eq("No cumple").sum())
    sin_datos = int((~serie.isin(["Cumple", "No cumple"])).sum())
    total = cumple + no_cumple
    pct = cumple / total * 100 if total else 0
    promedio = 0
    if col_dias in df.columns:
        dias = pd.to_numeric(df[col_dias], errors="coerce")
        dias = dias[dias.ge(0)]
        promedio = dias.mean() if dias.notna().any() else 0
    return {"cumple": cumple, "no_cumple": no_cumple, "sin_datos": sin_datos, "total": total, "pct": pct, "promedio": promedio}


def grafico_donut(cumple: int, no_cumple: int, sin_datos: int = 0):
    data = pd.DataFrame({
        "Estado": ["Cumple", "No cumple", "Sin datos"],
        "Cantidad": [cumple, no_cumple, sin_datos],
    })
    data = data[data["Cantidad"] > 0]
    if data.empty:
        data = pd.DataFrame({"Estado": ["Sin datos"], "Cantidad": [1]})
    total_eval = cumple + no_cumple
    pct = cumple / total_eval * 100 if total_eval else 0

    donut = alt.Chart(data).mark_arc(innerRadius=62, outerRadius=88, cornerRadius=4).encode(
        theta=alt.Theta("Cantidad:Q"),
        color=alt.Color(
            "Estado:N",
            scale=alt.Scale(domain=["Cumple", "No cumple", "Sin datos"], range=[COLOR_CUMPLE, COLOR_NO_CUMPLE, COLOR_SIN_DATOS]),
            legend=alt.Legend(title=None, orient="bottom", labelFontSize=11),
        ),
        tooltip=[alt.Tooltip("Estado:N"), alt.Tooltip("Cantidad:Q", format=",.0f")],
    )
    centro = alt.Chart(pd.DataFrame({"texto": [f"{pct:.0f}%"]})).mark_text(fontSize=26, fontWeight="bold", color=COLOR_TEXTO).encode(text="texto:N")
    sub = alt.Chart(pd.DataFrame({"texto": ["Cumple"]})).mark_text(fontSize=11, color=COLOR_MUTED, dy=24).encode(text="texto:N")
    return (donut + centro + sub).properties(height=220).configure_view(strokeWidth=0)


def grafico_barras_etapas(resumen: pd.DataFrame):
    if resumen.empty:
        st.info("No hay etapas para graficar.")
        return
    chart = alt.Chart(resumen).mark_bar(cornerRadius=5).encode(
        x=alt.X("% Cumple:Q", title="% Cumple", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("Métrica:N", sort="-x", title=None),
        color=alt.value(COLOR_CUMPLE),
        tooltip=["Métrica:N", alt.Tooltip("% Cumple:Q", format=".1f"), alt.Tooltip("Evaluables:Q", format=",.0f")],
    )
    text = chart.mark_text(align="left", dx=4, color=COLOR_TEXTO, fontWeight="bold").encode(text=alt.Text("% Cumple:Q", format=".1f"))
    st.altair_chart((chart + text).properties(height=260).configure_view(strokeWidth=0), use_container_width=True)


def grafico_rangos(df: pd.DataFrame):
    if "rango_incumplimiento_tat" not in df.columns:
        st.info("No existe la columna rango_incumplimiento_tat.")
        return
    orden = ["Sin incumplimiento", "1-5 días", "6-15 días", "16-30 días", "Mayor a un mes", "Sin datos"]
    data = df["rango_incumplimiento_tat"].fillna("Sin datos").value_counts().reset_index()
    data.columns = ["Rango", "Cantidad"]
    data["Rango"] = pd.Categorical(data["Rango"], categories=orden, ordered=True)
    data = data.sort_values("Rango")
    chart = alt.Chart(data).mark_bar(cornerRadius=5).encode(
        x=alt.X("Cantidad:Q", title="Cantidad"),
        y=alt.Y("Rango:N", sort=orden, title=None),
        color=alt.Color("Rango:N", legend=None, scale=alt.Scale(range=[COLOR_CUMPLE, "#9CA3AF", "#F59E0B", "#F97316", COLOR_NO_CUMPLE, COLOR_SIN_DATOS])),
        tooltip=[alt.Tooltip("Rango:N"), alt.Tooltip("Cantidad:Q", format=",.0f")],
    )
    text = chart.mark_text(align="left", dx=4, color=COLOR_TEXTO, fontWeight="bold").encode(text=alt.Text("Cantidad:Q", format=",.0f"))
    st.altair_chart((chart + text).properties(height=270).configure_view(strokeWidth=0), use_container_width=True)

# =========================================================
# EXPORTACIÓN
# =========================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_parquet(output, index=False, engine="pyarrow")
    return output.getvalue()


def convertir_a_excel(df: pd.DataFrame, resumen_perf: pd.DataFrame, resumen_cols: pd.DataFrame, tabla_formulas: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Performance_TAT")
        resumen_perf.to_excel(writer, index=False, sheet_name="Resumen_Performance")
        resumen_cols.to_excel(writer, index=False, sheet_name="Columnas_Nuevas")
        tabla_formulas.to_excel(writer, index=False, sheet_name="Inputs_Formulas")
    return output.getvalue()

@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)

@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)

@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(df: pd.DataFrame, resumen_perf: pd.DataFrame, resumen_cols: pd.DataFrame, tabla_formulas: pd.DataFrame) -> bytes:
    return convertir_a_excel(df, resumen_perf, resumen_cols, tabla_formulas)

# =========================================================
# APP
# =========================================================

aplicar_css()

with st.container():
    st.markdown("<div class='header-card'>", unsafe_allow_html=True)
    h1, h2, h3 = st.columns([1.2, 3.4, 2.4], vertical_alignment="center")
    with h1:
        mostrar_logo(170)
    with h2:
        st.markdown("<p class='title-main'>Performance TAT 2025</p>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle-main'>ME5A · ARIBA · NME80FN · Fechas finales · Dashboard ejecutivo y archivo procesado</div>", unsafe_allow_html=True)
    with h3:
        st.markdown("<span class='status-pill'>Carga, calcula, filtra, visualiza y descarga</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with st.container():
    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    section_header("Carga y configuración", "Sube el archivo integrado. El dashboard calcula la performance y luego permite filtrar el resultado.")
    c_file, c_sep, c_opts = st.columns([2.6, 1.1, 1.3])
    with c_file:
        uploaded_file = st.file_uploader("Archivo con fechas finales", type=["parquet", "xlsx", "xls", "csv"], label_visibility="collapsed")
    with c_sep:
        separador_csv = st.selectbox("Separador CSV", ["Automático", "Punto y coma (;)", "Coma (,)", "Tabulación"], index=0)
    with c_opts:
        ordenar_performance_final = st.checkbox("Mover columnas calculadas al final", value=True)
        limite_vista = st.number_input("Filas en vistas", min_value=50, max_value=5000, value=300, step=50)
    st.markdown("</div>", unsafe_allow_html=True)

if uploaded_file is None:
    st.info("Carga un archivo .parquet, .xlsx o .csv para comenzar.")
    st.stop()

try:
    with st.spinner("Leyendo archivo y aplicando lógica de Performance TAT..."):
        df_original = leer_archivo_cache(uploaded_file.getvalue(), uploaded_file.name, separador_csv)
        columnas_originales = list(df_original.columns)
        df_final = aplicar_logica_performance(df_original)
        columnas_nuevas = [col for col in df_final.columns if col not in columnas_originales]
        if ordenar_performance_final:
            df_final = reordenar_columnas_performance_al_final(df_final)
        resumen_perf = resumen_performance(df_final)
        resumen_cols = resumen_columnas_nuevas(df_final)
        tabla_formulas = tabla_inputs_formulas()

    fechas_validas = df_final[COL_FECHA_RECEPCION_FINAL].dropna()
    fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
    fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

    with st.container():
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        section_header("Filtros del dashboard", "Los filtros se aplican sobre el resultado calculado.")
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            if fecha_min and fecha_max:
                rango_fechas = st.date_input("Fecha recepción", value=(fecha_min, fecha_max), min_value=fecha_min, max_value=fecha_max)
            else:
                rango_fechas = None
        with f2:
            sistemas = sorted(pd.Series(df_final.get("sistema", pd.Series(dtype="object"))).dropna().astype(str).unique().tolist())
            sistema_sel = st.multiselect("Sistema", options=sistemas, default=sistemas)
        with f3:
            centros_col = next((col for col in ["Centro - ME5A", "Centro", "Centro - NME80FN"] if col in df_final.columns), None)
            if centros_col:
                centros = sorted(df_final[centros_col].dropna().astype(str).str.strip().unique().tolist())
                default_centros = ["E002"] if "E002" in centros else centros
                centros_sel = st.multiselect("Centro", options=centros, default=default_centros)
            else:
                centros_sel = []
                st.selectbox("Centro", ["Sin columna de centro"], disabled=True)
        with f4:
            estados_tat = ["Cumple", "No cumple", "En proceso", "No aplica al análisis", "Sin datos"]
            disponibles = [x for x in estados_tat if x in df_final["performance_tat_total"].astype(str).unique().tolist()]
            performance_sel = st.multiselect("Performance TAT", options=disponibles, default=disponibles)
        st.markdown("</div>", unsafe_allow_html=True)

    df_filtrado = df_final.copy()

    if rango_fechas and isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
        inicio = pd.Timestamp(rango_fechas[0])
        fin = pd.Timestamp(rango_fechas[1]) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        df_filtrado = df_filtrado[df_filtrado[COL_FECHA_RECEPCION_FINAL].between(inicio, fin, inclusive="both")].copy()

    if sistema_sel and "sistema" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["sistema"].astype(str).isin(sistema_sel)].copy()

    if centros_col and centros_sel:
        df_filtrado = df_filtrado[df_filtrado[centros_col].astype(str).str.strip().isin(centros_sel)].copy()

    if performance_sel:
        df_filtrado = df_filtrado[df_filtrado["performance_tat_total"].astype(str).isin(performance_sel)].copy()

    tab_dashboard, tab_auditoria, tab_datos, tab_descarga = st.tabs(["Dashboard", "Auditoría", "Datos", "Descarga"])

    with tab_dashboard:
        total_filas = len(df_filtrado)
        cumple_tat = int(df_filtrado["performance_tat_total"].eq("Cumple").sum())
        no_cumple_tat = int(df_filtrado["performance_tat_total"].eq("No cumple").sum())
        evaluables_tat = cumple_tat + no_cumple_tat
        pct_cumple_tat = cumple_tat / evaluables_tat * 100 if evaluables_tat else 0
        en_proceso = int(df_filtrado["performance_tat_total"].eq("En proceso").sum())
        no_aplica = int(df_filtrado["performance_tat_total"].eq("No aplica al análisis").sum())
        incumplimientos = int(df_filtrado.get("incumplimiento_tat", pd.Series(dtype=bool)).eq(True).sum())

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        with k1: card_metric("Filas filtradas", f"{total_filas:,}", "Registros después de filtros")
        with k2: card_metric("Evaluables TAT", f"{evaluables_tat:,}", "Cumple + No cumple")
        with k3: card_metric("% Cumple TAT", f"{pct_cumple_tat:.1f}%", f"{cumple_tat:,} registros")
        with k4: card_metric("No cumple TAT", f"{no_cumple_tat:,}", "Registros fuera de umbral")
        with k5: card_metric("En proceso", f"{en_proceso:,}", "Sin recepción final")
        with k6: card_metric("Incumplimiento", f"{incumplimientos:,}", "TAT total sobre umbral")

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        section_header("Cumplimiento mensual TAT", "Barras apiladas por mes y línea de tendencia del porcentaje de cumplimiento.")
        tabla_mensual = crear_resumen_mensual(df_filtrado)
        grafico_mensual_100(tabla_mensual)
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        section_header("Cumplimiento por etapa", "Cada tarjeta muestra distribución, porcentaje de cumplimiento y promedio de días no negativos.")
        cols_etapas = st.columns(4)
        for col, etapa in zip(cols_etapas, ETAPAS_DASHBOARD):
            with col:
                stats = datos_etapa(df_filtrado, etapa)
                st.markdown("<div class='stage-card'>", unsafe_allow_html=True)
                st.markdown(f"<div class='stage-title'>{etapa['titulo_largo']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='stage-rule'>{etapa['regla']}</div>", unsafe_allow_html=True)
                st.altair_chart(grafico_donut(stats["cumple"], stats["no_cumple"], stats["sin_datos"]), use_container_width=True)
                st.markdown(f"<div class='stage-days'>{stats['promedio']:.0f}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='stage-days-label'>Promedio de días · {stats['titulo'] if 'titulo' in stats else etapa['titulo']}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        d1, d2 = st.columns(2)
        with d1:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            section_header("Ranking de cumplimiento", "Comparación directa entre métricas de performance.")
            grafico_barras_etapas(resumen_performance(df_filtrado))
            st.markdown("</div>", unsafe_allow_html=True)
        with d2:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            section_header("Rango de incumplimiento TAT", "Segmentación de días excedidos respecto del umbral TAT.")
            grafico_rangos(df_filtrado)
            st.markdown("</div>", unsafe_allow_html=True)

    with tab_auditoria:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        section_header("Resumen de performance", "Tabla ejecutiva con conteos y porcentaje de cumplimiento sobre evaluables.")
        st.dataframe(resumen_performance(df_filtrado), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        a1, a2 = st.columns(2)
        with a1:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            section_header("Inputs y fórmulas", "Trazabilidad de fechas, fórmulas y umbrales aplicados.")
            st.dataframe(tabla_formulas, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with a2:
            st.markdown("<div class='section-card'>", unsafe_allow_html=True)
            section_header("Columnas agregadas", "Nulos, porcentaje de nulos y tipo de dato de columnas nuevas.")
            st.dataframe(resumen_columnas_nuevas(df_final), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        section_header("Auditoría de días por etapa", "Revisa los registros que elevan promedios o generan valores negativos.")
        columnas_dias = [col for col in ["dias_liberacion_solped", "dias_comprador", "dias_proveedor", "dias_logistica", "dias_tat_total"] if col in df_filtrado.columns]
        if columnas_dias:
            c_etapa, c_orden = st.columns([1, 1])
            with c_etapa:
                etapa_auditoria = st.selectbox("Etapa", columnas_dias)
            with c_orden:
                modo = st.radio("Orden", ["Días más altos", "Días más bajos / negativos"], horizontal=True)
            asc = modo == "Días más bajos / negativos"
            serie = pd.to_numeric(df_filtrado[etapa_auditoria], errors="coerce")
            col_umbral = etapa_auditoria.replace("dias_", "umbral_")
            total_validos = int(serie.notna().sum())
            total_negativos = int(serie.lt(0).sum())
            total_sobre_umbral = 0
            if col_umbral in df_filtrado.columns:
                total_sobre_umbral = int(serie.gt(pd.to_numeric(df_filtrado[col_umbral], errors="coerce")).sum())
            m1, m2, m3 = st.columns(3)
            with m1: card_metric("Valores válidos", f"{total_validos:,}")
            with m2: card_metric("Días negativos", f"{total_negativos:,}")
            with m3: card_metric("Sobre umbral", f"{total_sobre_umbral:,}")

            columnas_auditoria = [
                "Solicitud de pedido - ME5A", COL_PEDIDO, COL_DOCUMENTO_COMPRAS, "tipo_oc", "origen", "sistema",
                COL_FECHA_SOLICITUD_FINAL, COL_FECHA_LIBERACION_FINAL, COL_FECHA_PEDIDO_FINAL, COL_FECHA_FACTURACION_FINAL,
                COL_FECHA_RECEPCION_FINAL, "dias_liberacion_solped", "dias_comprador", "dias_proveedor", "dias_logistica",
                "dias_tat_total", "umbral_tat_total", "performance_tat_total", "dias_incumplimiento_tat", "rango_incumplimiento_tat",
                "tiene_fechas_inconsistentes",
            ]
            columnas_auditoria = [col for col in columnas_auditoria if col in df_filtrado.columns]
            st.dataframe(
                df_filtrado.assign(_audit=serie).sort_values("_audit", ascending=asc).drop(columns=["_audit"])[columnas_auditoria].head(int(limite_vista)),
                use_container_width=True,
                hide_index=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_datos:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        section_header("Vista previa final", f"Mostrando hasta {int(limite_vista):,} registros filtrados.")
        columnas_preferidas = [
            "Solicitud de pedido - ME5A", COL_PEDIDO, COL_DOCUMENTO_COMPRAS, "tipo_oc", "origen", "sistema", "nombre_tipo_compra",
            COL_CANTIDAD_SOLICITADA, COL_PRECIO_VALORACION, "monto", COL_FECHA_SOLICITUD_FINAL, COL_FECHA_LIBERACION_FINAL,
            COL_FECHA_PEDIDO_FINAL, COL_FECHA_FACTURACION_FINAL, COL_FECHA_RECEPCION_FINAL, "dias_liberacion_solped", "dias_comprador",
            "dias_proveedor", "dias_logistica", "dias_tat_total", "performance_liberacion_solped", "performance_comprador",
            "performance_proveedor", "performance_logistica", "performance_tat_total", "dias_incumplimiento_tat", "rango_incumplimiento_tat",
        ]
        columnas_preferidas = [col for col in columnas_preferidas if col in df_filtrado.columns]
        st.dataframe(df_filtrado[columnas_preferidas].head(int(limite_vista)) if columnas_preferidas else df_filtrado.head(int(limite_vista)), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Ver archivo original"):
            st.dataframe(df_original.head(int(limite_vista)), use_container_width=True, hide_index=True)
        with st.expander("Ver columnas disponibles"):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Columnas originales**")
                st.write(columnas_originales)
            with c2:
                st.markdown("**Columnas finales**")
                st.write(df_final.columns.tolist())

    with tab_descarga:
        st.markdown("<div class='section-card'>", unsafe_allow_html=True)
        section_header("Descargar resultado", "Parquet conserva mejor los tipos de datos. CSV y Excel quedan disponibles como alternativa.")
        parquet_bytes = convertir_a_parquet_cache(df_final)
        st.download_button(
            "Descargar resultado en Parquet",
            data=parquet_bytes,
            file_name="performance_tat_resultado.parquet",
            mime="application/octet-stream",
            use_container_width=True,
        )
        c_csv, c_excel = st.columns(2)
        with c_csv:
            csv_bytes = convertir_a_csv_cache(df_final)
            st.download_button("Descargar CSV", data=csv_bytes, file_name="performance_tat_resultado.csv", mime="text/csv", use_container_width=True)
        with c_excel:
            if len(df_final) > 250_000:
                st.warning("Excel no disponible para más de 250.000 filas. Usa Parquet o CSV.")
            else:
                excel_bytes = convertir_a_excel_cache(df_final, resumen_perf, resumen_cols, tabla_formulas)
                st.download_button("Descargar Excel", data=excel_bytes, file_name="performance_tat_resultado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error("No se pudo calcular la Performance TAT.")
    st.exception(e)
