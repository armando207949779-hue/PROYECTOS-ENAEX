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
# Si esta app se ejecuta dentro de st.navigation() desde la app principal,
# NO uses st.set_page_config() aquí.
# Debe estar solo en el archivo principal del portal.

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

ETAPAS_DASHBOARD = [
    {
        "titulo": "Lib SolPed",
        "titulo_largo": "Cumplimiento Lib SolPed",
        "col_perf": "performance_liberacion_solped",
        "col_dias": "dias_liberacion_solped",
        "regla": "• Nacional e Internacional < 2",
        "texto_promedio": "Promedio de Dx Lib SolPed",
    },
    {
        "titulo": "Comprador",
        "titulo_largo": "Cumplimiento Comprador",
        "col_perf": "performance_comprador",
        "col_dias": "dias_comprador",
        "regla": "• Nacional e Internacional < 11",
        "texto_promedio": "Promedio de Dx Comprador",
    },
    {
        "titulo": "Proveedor",
        "titulo_largo": "Cumplimiento Proveedor",
        "col_perf": "performance_proveedor",
        "col_dias": "dias_proveedor",
        "regla": "• Nacional < 20<br>• Internacional < 60",
        "texto_promedio": "Promedio de Dx Proveedor",
    },
    {
        "titulo": "Logística",
        "titulo_largo": "Cumplimiento Logística",
        "col_perf": "performance_logistica",
        "col_dias": "dias_logistica",
        "regla": "• Nacional e Internacional < 10",
        "texto_promedio": "Promedio de Dx Logística",
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
# PREPARACIÓN Y LÓGICA
# =========================================================

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
            f"Faltan columnas requeridas para calcular Performance TAT: {faltantes}"
        )


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


def evaluar_performance_basica(
    dias: pd.Series,
    umbral: pd.Series,
    texto_sin_dato="No aplica",
    negativos_no_aplican=True,
) -> pd.Series:
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
    return resultado.mask(dias_tat.isna() | umbral_tat.isna(), np.nan)


def calcular_rango_incumplimiento_tat(
    dias_incumplimiento: pd.Series,
) -> pd.Series:
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
                "1-5 días",
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
        df[COL_FECHA_LIBERACION_FINAL],
        df[COL_FECHA_SOLICITUD_FINAL],
    )

    df["dias_comprador"] = diferencia_dias(
        df[COL_FECHA_PEDIDO_FINAL],
        df[COL_FECHA_LIBERACION_FINAL],
    )

    df["dias_liberacion_pedido"] = np.nan

    df["dias_proveedor"] = diferencia_dias(
        df[COL_FECHA_FACTURACION_FINAL],
        df[COL_FECHA_PEDIDO_FINAL],
    )

    df["dias_logistica"] = diferencia_dias(
        df[COL_FECHA_RECEPCION_FINAL],
        df[COL_FECHA_FACTURACION_FINAL],
    )

    df["dias_tat_total"] = diferencia_dias(
        df[COL_FECHA_RECEPCION_FINAL],
        df[COL_FECHA_SOLICITUD_FINAL],
    )

    df["umbral_liberacion_solped"] = 2
    df["umbral_comprador"] = 10
    df["umbral_liberacion_pedido"] = 2
    df["umbral_logistica"] = 11

    df["umbral_proveedor"] = pd.to_numeric(
        np.select(
            [
                bool_array(df["tipo_oc"].isin(["35", "45"])),
                bool_array(df["tipo_oc"].eq("47")),
            ],
            [
                20,
                60,
            ],
            default=np.nan,
        ),
        errors="coerce",
    )

    df["umbral_tat_total"] = pd.to_numeric(
        np.select(
            [
                bool_array(df["tipo_oc"].isin(["35", "45"])),
                bool_array(df["tipo_oc"].eq("47")),
            ],
            [
                40,
                70,
            ],
            default=np.nan,
        ),
        errors="coerce",
    )

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

    df["performance_liberacion_solped"] = evaluar_performance_basica(
        df["dias_liberacion_solped"],
        pd.Series(df["umbral_liberacion_solped"], index=df.index),
        "No aplica",
    )

    df["performance_comprador"] = evaluar_performance_basica(
        df["dias_comprador"],
        pd.Series(df["umbral_comprador"], index=df.index),
        "No aplica",
    )

    df["performance_liberacion_pedido"] = evaluar_performance_basica(
        pd.Series(df["dias_liberacion_pedido"], index=df.index),
        pd.Series(df["umbral_liberacion_pedido"], index=df.index),
        "Sin datos",
    )

    df["performance_proveedor"] = evaluar_performance_basica(
        df["dias_proveedor"],
        df["umbral_proveedor"],
        "Sin datos",
    )

    df["performance_logistica"] = evaluar_performance_basica(
        df["dias_logistica"],
        pd.Series(df["umbral_logistica"], index=df.index),
        "No aplica",
    )

    df["performance_tat_total"] = evaluar_performance_tat(df)

    df["dias_incumplimiento_tat"] = calcular_dias_incumplimiento_tat(
        df["dias_tat_total"],
        df["umbral_tat_total"],
    )

    df["incumplimiento_tat"] = df["dias_incumplimiento_tat"].gt(0)

    df["rango_incumplimiento_tat"] = calcular_rango_incumplimiento_tat(
        df["dias_incumplimiento_tat"]
    )

    df["periodo_fecha"] = (
        df[COL_FECHA_RECEPCION_FINAL]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["anio"] = df[COL_FECHA_RECEPCION_FINAL].dt.year
    df["mes_num"] = df[COL_FECHA_RECEPCION_FINAL].dt.month
    df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)

    df["periodo_label"] = np.where(
        df["anio"].notna() & df["mes_nombre"].notna(),
        df["mes_nombre"].astype(str)
        + " "
        + df["anio"].astype("Int64").astype(str),
        pd.NA,
    )

    return df


def reordenar_columnas_performance_al_final(df: pd.DataFrame) -> pd.DataFrame:
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
# RESÚMENES Y GRÁFICOS
# =========================================================

def resumen_performance(df: pd.DataFrame) -> pd.DataFrame:
    metricas = [
        (
            "performance_liberacion_solped",
            "Liberación SolPed",
            "Tiempo entre solicitud y liberación de la SolPed.",
        ),
        (
            "performance_comprador",
            "Comprador",
            "Tiempo entre liberación de SolPed y creación/emisión del pedido.",
        ),
        (
            "performance_liberacion_pedido",
            "Liberación Pedido",
            "No se calcula actualmente porque no hay inputs disponibles.",
        ),
        (
            "performance_proveedor",
            "Proveedor",
            "Tiempo entre pedido y facturación.",
        ),
        (
            "performance_logistica",
            "Logística",
            "Tiempo entre facturación y recepción de mercancía.",
        ),
        (
            "performance_tat_total",
            "TAT Total",
            "Tiempo punta a punta desde solicitud hasta recepción.",
        ),
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

        data.append(
            {
                "Métrica": metrica,
                "Descripción": descripcion,
                "Cumple": cumple,
                "No cumple": no_cumple,
                "No aplica": no_aplica,
                "Sin datos / En proceso": sin_datos,
                "Evaluables": total_evaluable,
                "% Cumple": pct_cumple,
            }
        )

    return pd.DataFrame(data)


def tabla_inputs_formulas() -> pd.DataFrame:
    return pd.DataFrame(
        [
            [
                "Liberación SolPed",
                "dias_liberacion_solped",
                COL_FECHA_SOLICITUD_FINAL,
                COL_FECHA_LIBERACION_FINAL,
                "fecha_liberacion_final - fecha_solicitud_final",
                "2 días",
            ],
            [
                "Comprador",
                "dias_comprador",
                COL_FECHA_LIBERACION_FINAL,
                COL_FECHA_PEDIDO_FINAL,
                "fecha_pedido_final - fecha_liberacion_final",
                "10 días",
            ],
            [
                "Liberación Pedido",
                "dias_liberacion_pedido",
                "Sin input",
                "Sin input",
                "Sin cálculo",
                "2 días",
            ],
            [
                "Proveedor",
                "dias_proveedor",
                COL_FECHA_PEDIDO_FINAL,
                COL_FECHA_FACTURACION_FINAL,
                "fecha_facturacion_final - fecha_pedido_final",
                "OC 35/45 = 20; OC 47 = 60",
            ],
            [
                "Logística",
                "dias_logistica",
                COL_FECHA_FACTURACION_FINAL,
                COL_FECHA_RECEPCION_FINAL,
                "fecha_recepcion_final - fecha_facturacion_final",
                "11 días",
            ],
            [
                "TAT Total",
                "dias_tat_total",
                COL_FECHA_SOLICITUD_FINAL,
                COL_FECHA_RECEPCION_FINAL,
                "fecha_recepcion_final - fecha_solicitud_final",
                "OC 35/45 = 40; OC 47 = 70",
            ],
        ],
        columns=[
            "Métrica",
            "Nombre técnico",
            "Fecha inicio",
            "Fecha fin",
            "Fórmula",
            "Umbral",
        ],
    )


def resumen_columnas_nuevas(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        col for col in COLUMNAS_NUEVAS_ORDENADAS
        if col in df.columns
    ]

    return pd.DataFrame(
        {
            "Columna nueva": columnas,
            "Nulos": [int(df[col].isna().sum()) for col in columnas],
            "% Nulos": [
                round(df[col].isna().mean() * 100, 2)
                for col in columnas
            ],
            "Tipo dato": [str(df[col].dtype) for col in columnas],
        }
    )


def crear_resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    base = df[
        df["performance_tat_total"].isin(["Cumple", "No cumple"])
        & df["periodo_fecha"].notna()
    ].copy()

    if base.empty:
        return pd.DataFrame()

    resumen = (
        base
        .groupby(["periodo_fecha", "periodo_label", "performance_tat_total"])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=["periodo_fecha", "periodo_label"],
        columns="performance_tat_total",
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
        .mark_bar(size=34, cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=order,
                title=None,
                axis=alt.Axis(labelAngle=0, labelFontSize=11),
            ),
            y=alt.Y(
                "Porcentaje:Q",
                stack="zero",
                title="% sobre evaluables",
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
                legend=alt.Legend(title=None, orient="bottom"),
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
            y=alt.Y("Meta:Q")
        )
    )

    chart = (
        (barras + linea_meta)
        .properties(height=340)
        .configure_view(strokeWidth=0)
    )

    st.altair_chart(chart, use_container_width=True)
def normalizar_estado_donut(valor) -> str:
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
        return "No Cumple"

    if texto in ["no aplica", "no aplica al analisis"]:
        return "No aplica"

    return "Sin información"


def datos_etapa(df: pd.DataFrame, etapa: dict) -> dict:
    col_perf = etapa["col_perf"]
    col_dias = etapa["col_dias"]

    salida_vacia = {
        "cumple": 0,
        "no_cumple": 0,
        "total": 0,
        "pct_cumple": 0.0,
        "pct_no_cumple": 0.0,
        "promedio": 0.0,
        "n_promedio": 0,
        "sin_info": 0,
    }

    if col_perf not in df.columns:
        return salida_vacia

    temp = df.copy()

    if "performance_tat_total" in temp.columns:
        tat_norm = temp["performance_tat_total"].apply(normalizar_estado_donut)
        temp = temp[tat_norm.isin(["Cumple", "No Cumple"])].copy()

    temp["estado_donut"] = temp[col_perf].apply(normalizar_estado_donut)

    temp_eval = temp[temp["estado_donut"].isin(["Cumple", "No Cumple"])].copy()

    conteo = (
        temp_eval["estado_donut"]
        .value_counts()
        .reindex(["Cumple", "No Cumple"], fill_value=0)
    )

    cumple = int(conteo["Cumple"])
    no_cumple = int(conteo["No Cumple"])
    total = cumple + no_cumple

    pct_cumple = cumple / total * 100 if total > 0 else 0.0
    pct_no_cumple = no_cumple / total * 100 if total > 0 else 0.0

    sin_info = int((~temp["estado_donut"].isin(["Cumple", "No Cumple"])).sum())

    promedio = 0.0
    n_promedio = 0

    if col_dias in temp.columns:
        dias = pd.to_numeric(temp[col_dias], errors="coerce").dropna()
        dias = dias[dias > 0]
        n_promedio = int(len(dias))
        promedio = float(dias.mean()) if not dias.empty else 0.0

    return {
        "cumple": cumple,
        "no_cumple": no_cumple,
        "total": total,
        "pct_cumple": pct_cumple,
        "pct_no_cumple": pct_no_cumple,
        "promedio": promedio,
        "n_promedio": n_promedio,
        "sin_info": sin_info,
    }


def grafico_donut(cumple: int, no_cumple: int):
    data = pd.DataFrame(
        {
            "Estado": ["Cumple", "No Cumple"],
            "Cantidad": [int(cumple), int(no_cumple)],
            "Orden": [1, 2],
        }
    )

    total = int(data["Cantidad"].sum())

    if total <= 0:
        data = pd.DataFrame(
            {
                "Estado": ["Sin datos"],
                "Cantidad": [1],
                "Orden": [3],
                "Porcentaje": [0.0],
                "Etiqueta": [""],
            }
        )

        domain = ["Cumple", "No Cumple", "Sin datos"]
        colors = [COLOR_CUMPLE, COLOR_NO_CUMPLE, COLOR_SIN_DATOS]

    else:
        data["Porcentaje"] = data["Cantidad"] / total * 100

        data["Etiqueta"] = data.apply(
            lambda r: (
                f"{r['Estado']} {r['Porcentaje']:.0f}%"
                if r["Cantidad"] > 0
                else ""
            ),
            axis=1,
        )

        data = data[data["Cantidad"] > 0].copy()

        domain = ["Cumple", "No Cumple"]
        colors = [COLOR_CUMPLE, COLOR_NO_CUMPLE]

    donut = (
        alt.Chart(data)
        .mark_arc(
            innerRadius=58,
            outerRadius=86,
            cornerRadius=3,
            stroke="white",
            strokeWidth=2,
        )
        .encode(
            theta=alt.Theta("Cantidad:Q", stack=True),
            color=alt.Color(
                "Estado:N",
                scale=alt.Scale(domain=domain, range=colors),
                legend=alt.Legend(
                    title=None,
                    orient="bottom",
                    labelFontSize=11,
                ),
            ),
            order=alt.Order("Orden:Q", sort="ascending"),
            tooltip=[
                alt.Tooltip("Estado:N", title="Estado"),
                alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
                alt.Tooltip("Porcentaje:Q", title="Porcentaje", format=".1f"),
            ],
        )
    )

    labels = (
        alt.Chart(data)
        .mark_text(radius=112, fontSize=10, color=COLOR_MUTED)
        .encode(
            theta=alt.Theta("Cantidad:Q", stack=True),
            order=alt.Order("Orden:Q", sort="ascending"),
            text="Etiqueta:N",
        )
    )

    return (donut + labels).properties(height=230).configure_view(strokeWidth=0)


def grafico_barras_etapas(resumen: pd.DataFrame):
    if resumen.empty:
        st.info("No hay etapas para graficar.")
        return

    chart = (
        alt.Chart(resumen)
        .mark_bar(cornerRadius=5)
        .encode(
            x=alt.X(
                "% Cumple:Q",
                title="% Cumple",
                scale=alt.Scale(domain=[0, 100]),
            ),
            y=alt.Y("Métrica:N", sort="-x", title=None),
            color=alt.value(COLOR_CUMPLE),
            tooltip=[
                "Métrica:N",
                alt.Tooltip("% Cumple:Q", format=".1f"),
                alt.Tooltip("Evaluables:Q", format=",.0f"),
            ],
        )
    )

    text = (
        chart
        .mark_text(
            align="left",
            dx=4,
            color=COLOR_TEXTO,
            fontWeight="bold",
        )
        .encode(
            text=alt.Text("% Cumple:Q", format=".1f")
        )
    )

    st.altair_chart(
        (chart + text).properties(height=260).configure_view(strokeWidth=0),
        use_container_width=True,
    )


def grafico_rangos(df: pd.DataFrame):
    if "rango_incumplimiento_tat" not in df.columns:
        st.info("No existe la columna rango_incumplimiento_tat.")
        return

    orden = [
        "Sin incumplimiento",
        "1-5 días",
        "6-15 días",
        "16-30 días",
        "Mayor a un mes",
        "Sin datos",
    ]

    data = (
        df["rango_incumplimiento_tat"]
        .fillna("Sin datos")
        .value_counts()
        .reset_index()
    )

    data.columns = ["Rango", "Cantidad"]

    data["Rango"] = pd.Categorical(
        data["Rango"],
        categories=orden,
        ordered=True,
    )

    data = data.sort_values("Rango")

    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadius=5)
        .encode(
            x=alt.X("Cantidad:Q", title="Cantidad"),
            y=alt.Y("Rango:N", sort=orden, title=None),
            color=alt.Color(
                "Rango:N",
                legend=None,
                scale=alt.Scale(
                    range=[
                        COLOR_CUMPLE,
                        "#9CA3AF",
                        "#F59E0B",
                        "#F97316",
                        COLOR_NO_CUMPLE,
                        COLOR_SIN_DATOS,
                    ]
                ),
            ),
            tooltip=[
                alt.Tooltip("Rango:N"),
                alt.Tooltip("Cantidad:Q", format=",.0f"),
            ],
        )
    )

    text = (
        chart
        .mark_text(
            align="left",
            dx=4,
            color=COLOR_TEXTO,
            fontWeight="bold",
        )
        .encode(
            text=alt.Text("Cantidad:Q", format=",.0f")
        )
    )

    st.altair_chart(
        (chart + text).properties(height=270).configure_view(strokeWidth=0),
        use_container_width=True,
    )


# =========================================================
# EXPORTACIÓN
# =========================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_parquet(output, index=False, engine="pyarrow")
    return output.getvalue()


def convertir_a_excel(
    df: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame,
    tabla_formulas: pd.DataFrame,
) -> bytes:
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
def convertir_a_excel_cache(
    df: pd.DataFrame,
    resumen_perf: pd.DataFrame,
    resumen_cols: pd.DataFrame,
    tabla_formulas: pd.DataFrame,
) -> bytes:
    return convertir_a_excel(
        df,
        resumen_perf,
        resumen_cols,
        tabla_formulas,
    )


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
            Performance TAT - Match Integrado
        </div>
        <div style="font-size:14px; color:#6B7280; margin-top:10px;">
            ME5A · ARIBA · NME80FN · Fechas finales
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

    limite_vista = st.number_input(
        "Filas en vista previa",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
    )

    ordenar_performance_final = st.checkbox(
        "Mover columnas de performance al final",
        value=True,
    )

    mostrar_resumen_logica = st.checkbox(
        "Mostrar lógica de cálculo al iniciar",
        value=False,
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
# 4) Procesar dataframe global
# ---------------------------------------------------------
try:
    columnas_originales = list(df_original.columns)

    with st.spinner("Aplicando lógica de performance..."):
        df_final = aplicar_logica_performance(df_original)

        columnas_nuevas = [
            col for col in df_final.columns
            if col not in columnas_originales
        ]

        if ordenar_performance_final:
            df_final = reordenar_columnas_performance_al_final(df_final)

        resumen_perf = resumen_performance(df_final)
        resumen_cols = resumen_columnas_nuevas(df_final)
        tabla_formulas = tabla_inputs_formulas()
        parquet_bytes = convertir_a_parquet_cache(df_final)

    st.success("Performance TAT calculada correctamente.")

    # -----------------------------------------------------
    # 5) Filtros del dashboard
    # -----------------------------------------------------
    st.subheader("Filtros del dashboard")

    df_dashboard = df_final.copy()

    col_centro = None

    for candidato in ["Centro", "Centro - ME5A", "Centro - NME80FN"]:
        if candidato in df_dashboard.columns:
            col_centro = candidato
            break

    fechas_validas = df_dashboard[COL_FECHA_RECEPCION_FINAL].dropna()
    fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
    fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        if fecha_min is not None and fecha_max is not None:
            rango_fechas = st.date_input(
                "Fecha recepción",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
            )
        else:
            rango_fechas = None
            st.warning("No hay fechas válidas de recepción.")

    with f2:
        if "sistema" in df_dashboard.columns:
            sistemas = sorted(
                df_dashboard["sistema"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            sistemas_sel = st.multiselect(
                "Sistema",
                sistemas,
                default=sistemas,
            )
        else:
            sistemas_sel = []
            st.info("Sin columna sistema")

    with f3:
        if col_centro is not None:
            centros = sorted(
                df_dashboard[col_centro]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            default_centros = ["E002"] if "E002" in centros else centros

            centros_sel = st.multiselect(
                "Centro",
                centros,
                default=default_centros,
            )
        else:
            centros_sel = []
            st.info("Sin columna centro")

    with f4:
        perf_options = [
            "Cumple",
            "No cumple",
            "En proceso",
            "No aplica al análisis",
            "Sin datos",
        ]

        if "performance_tat_total" in df_dashboard.columns:
            perf_existentes = [
                x for x in perf_options
                if x in df_dashboard["performance_tat_total"].astype(str).unique()
            ]
        else:
            perf_existentes = []

        perf_sel = st.multiselect(
            "Performance TAT",
            perf_existentes,
            default=[
                x for x in ["Cumple", "No cumple"]
                if x in perf_existentes
            ],
        )

    # -----------------------------------------------------
    # Aplicar filtros
    # -----------------------------------------------------
    if rango_fechas is not None:
        if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
            fecha_inicio = pd.Timestamp(rango_fechas[0])
            fecha_fin = (
                pd.Timestamp(rango_fechas[1])
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
            )

            df_dashboard = df_dashboard[
                df_dashboard[COL_FECHA_RECEPCION_FINAL].notna()
                & df_dashboard[COL_FECHA_RECEPCION_FINAL].between(
                    fecha_inicio,
                    fecha_fin,
                )
            ].copy()

    if "sistema" in df_dashboard.columns and sistemas_sel:
        df_dashboard = df_dashboard[
            df_dashboard["sistema"].astype(str).isin(sistemas_sel)
        ].copy()

    if col_centro is not None and centros_sel:
        df_dashboard = df_dashboard[
            df_dashboard[col_centro]
            .astype(str)
            .str.strip()
            .isin([str(x).strip() for x in centros_sel])
        ].copy()

    if "performance_tat_total" in df_dashboard.columns and perf_sel:
        df_dashboard = df_dashboard[
            df_dashboard["performance_tat_total"]
            .astype(str)
            .isin(perf_sel)
        ].copy()

    # -----------------------------------------------------
    # 6) Tabs principales
    # -----------------------------------------------------
    tab_dashboard, tab_auditoria, tab_datos, tab_descarga = st.tabs(
        [
            "Dashboard",
            "Auditoría",
            "Datos",
            "Descarga",
        ]
    )

    with tab_dashboard:
        st.subheader("Indicadores generales")

        total_filas = len(df_dashboard)

        cumple_tat = (
            int(df_dashboard["performance_tat_total"].eq("Cumple").sum())
            if "performance_tat_total" in df_dashboard.columns
            else 0
        )

        no_cumple_tat = (
            int(df_dashboard["performance_tat_total"].eq("No cumple").sum())
            if "performance_tat_total" in df_dashboard.columns
            else 0
        )

        evaluables_tat = cumple_tat + no_cumple_tat
        pct_cumple_tat = cumple_tat / evaluables_tat * 100 if evaluables_tat else 0

        incumplimientos_tat = (
            int(df_dashboard["incumplimiento_tat"].eq(True).sum())
            if "incumplimiento_tat" in df_dashboard.columns
            else 0
        )

        k1, k2, k3, k4, k5 = st.columns(5)

        with k1:
            card_metric("Filas filtradas", f"{total_filas:,}")

        with k2:
            card_metric("TAT evaluable", f"{evaluables_tat:,}")

        with k3:
            card_metric("Cumple TAT", f"{cumple_tat:,}", f"{pct_cumple_tat:.1f}%")

        with k4:
            card_metric("No cumple TAT", f"{no_cumple_tat:,}")

        with k5:
            card_metric("Incumplimiento TAT", f"{incumplimientos_tat:,}")

        st.divider()

        st.subheader("Performance TAT mensual")
        tabla_mensual = crear_resumen_mensual(df_dashboard)
        grafico_mensual_100(tabla_mensual)

        st.divider()

        st.subheader("Cumplimiento por etapa")

        st.caption(
            "Las donas replican la lógica solicitada: se consideran solo estados "
            "Cumple / No Cumple de cada etapa, y el promedio usa únicamente días positivos, Dx > 0."
        )

        resumen_etapas = []
        cols_etapas = st.columns(4)

        for i, etapa in enumerate(ETAPAS_DASHBOARD):
            datos = datos_etapa(df_dashboard, etapa)

            resumen_etapas.append(
                {
                    "Métrica": etapa["titulo"],
                    "Cumple": datos["cumple"],
                    "No Cumple": datos["no_cumple"],
                    "Evaluables": datos["total"],
                    "% Cumple": datos["pct_cumple"],
                    "% No Cumple": datos["pct_no_cumple"],
                    "Promedio Dx > 0": datos["promedio"],
                    "N promedio": datos["n_promedio"],
                }
            )

            with cols_etapas[i]:
                st.markdown(f"**{etapa['titulo_largo']}**")

                st.markdown(
                    f"""
                    <div style='font-size:12px;color:#555;min-height:36px'>
                        {etapa['regla']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.altair_chart(
                    grafico_donut(datos["cumple"], datos["no_cumple"]),
                    use_container_width=True,
                )

                st.markdown(
                    f"""
                    <div style="text-align:center; margin-top:-6px;">
                        <div style="font-size:32px; font-weight:800; color:#1f2937;">
                            {datos['promedio']:.0f}
                        </div>
                        <div style="font-size:12px; color:#6b7280;">
                            {etapa['texto_promedio']}
                        </div>
                        <div style="font-size:11px; color:#6b7280; margin-top:4px;">
                            Evaluables: {datos['total']:,} · Promedio Dx &gt; 0: {datos['n_promedio']:,}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        resumen_etapas_df = pd.DataFrame(resumen_etapas)

        c_rank, c_rangos = st.columns([1.1, 1])

        with c_rank:
            st.subheader("Ranking de cumplimiento por etapa")
            grafico_barras_etapas(resumen_etapas_df)

        with c_rangos:
            st.subheader("Rango de incumplimiento TAT")
            grafico_rangos(df_dashboard)

        with st.expander("Ver tabla resumen por etapa", expanded=False):
            st.dataframe(
                resumen_etapas_df,
                use_container_width=True,
                hide_index=True,
            )

    with tab_auditoria:
        st.subheader("Lógica y trazabilidad")

        if mostrar_resumen_logica:
            st.info(
                f"Se cargaron {len(df_original):,} registros. "
                f"El resultado final conserva {len(df_final):,} registros y agrega "
                f"{len(columnas_nuevas):,} columnas calculadas."
            )

        with st.expander("Inputs y fórmulas aplicadas", expanded=True):
            st.dataframe(
                tabla_formulas,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Columnas nuevas agregadas", expanded=False):
            st.dataframe(
                resumen_cols,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Resumen de performance", expanded=True):
            st.dataframe(
                resumen_perf,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Top filas con mayor incumplimiento TAT", expanded=False):
            if "dias_incumplimiento_tat" in df_dashboard.columns:
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
                    if col in df_dashboard.columns
                ]

                st.dataframe(
                    df_dashboard
                    .sort_values("dias_incumplimiento_tat", ascending=False)[columnas_top]
                    .head(int(limite_vista)),
                    use_container_width=True,
                    hide_index=True,
                )

        with st.expander("Auditoría de días altos por etapa", expanded=False):
            columnas_dias = [
                "dias_liberacion_solped",
                "dias_comprador",
                "dias_proveedor",
                "dias_logistica",
                "dias_tat_total",
            ]

            columnas_dias = [
                col for col in columnas_dias
                if col in df_dashboard.columns
            ]

            if columnas_dias:
                etapa_auditoria = st.selectbox(
                    "Selecciona etapa",
                    columnas_dias,
                )

                modo = st.radio(
                    "Ordenar por",
                    ["Días más altos", "Días más bajos / negativos"],
                    horizontal=True,
                )

                asc = modo == "Días más bajos / negativos"

                serie = pd.to_numeric(
                    df_dashboard[etapa_auditoria],
                    errors="coerce",
                )

                col_umbral = etapa_auditoria.replace("dias_", "umbral_")

                sobre_umbral = 0

                if col_umbral in df_dashboard.columns:
                    sobre_umbral = int(
                        serie.gt(
                            pd.to_numeric(
                                df_dashboard[col_umbral],
                                errors="coerce",
                            )
                        ).sum()
                    )

                a1, a2, a3 = st.columns(3)

                a1.metric("Valores válidos", f"{int(serie.notna().sum()):,}")
                a2.metric("Días negativos", f"{int(serie.lt(0).sum()):,}")
                a3.metric("Sobre umbral", f"{sobre_umbral:,}")

                columnas_auditoria = [
                    "Solicitud de pedido - ME5A",
                    COL_PEDIDO,
                    COL_DOCUMENTO_COMPRAS,
                    "tipo_oc",
                    "origen",
                    "sistema",
                    COL_FECHA_SOLICITUD_FINAL,
                    COL_FECHA_LIBERACION_FINAL,
                    COL_FECHA_PEDIDO_FINAL,
                    COL_FECHA_FACTURACION_FINAL,
                    COL_FECHA_RECEPCION_FINAL,
                    "dias_liberacion_solped",
                    "dias_comprador",
                    "dias_proveedor",
                    "dias_logistica",
                    "dias_tat_total",
                    "performance_tat_total",
                ]

                columnas_auditoria = [
                    col for col in columnas_auditoria
                    if col in df_dashboard.columns
                ]

                st.dataframe(
                    df_dashboard
                    .assign(_orden=serie)
                    .sort_values("_orden", ascending=asc)
                    .drop(columns=["_orden"])[columnas_auditoria]
                    .head(int(limite_vista)),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No hay columnas de días disponibles para auditar.")

    with tab_datos:
        st.subheader("Vista previa original")

        st.caption(
            f"Mostrando hasta {int(limite_vista):,} registros de "
            f"{len(df_original):,} originales."
        )

        st.dataframe(
            df_original.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Vista previa final filtrada")

        columnas_preferidas = [
            "Solicitud de pedido - ME5A",
            COL_PEDIDO,
            COL_DOCUMENTO_COMPRAS,
            "tipo_oc",
            "origen",
            "sistema",
            "nombre_tipo_compra",
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
            "umbral_proveedor",
            "umbral_logistica",
            "umbral_tat_total",
            "performance_liberacion_solped",
            "performance_comprador",
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
            if col in df_dashboard.columns
        ]

        st.dataframe(
            df_dashboard[columnas_preferidas].head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("Ver columnas disponibles", expanded=False):
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**Columnas originales**")
                st.write(columnas_originales)

            with c2:
                st.markdown("**Columnas finales**")
                st.write(df_final.columns.tolist())

    with tab_descarga:
        st.subheader("Descarga")

        st.download_button(
            label="Descargar resultado completo en Parquet",
            data=parquet_bytes,
            file_name="match_integrado_me5a_ariba_nme80fn_performance.parquet",
            mime="application/octet-stream",
            use_container_width=True,
        )

        col_csv, col_excel = st.columns(2)

        with col_csv:
            csv_bytes = convertir_a_csv_cache(df_final)

            st.download_button(
                label="Descargar resultado completo en CSV",
                data=csv_bytes,
                file_name="match_integrado_me5a_ariba_nme80fn_performance.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_excel:
            limite_excel = 250_000

            if len(df_final) > limite_excel:
                st.warning(
                    f"Excel no disponible porque la salida supera "
                    f"{limite_excel:,} filas. Usa Parquet o CSV."
                )
            else:
                excel_bytes = convertir_a_excel_cache(
                    df_final,
                    resumen_perf,
                    resumen_cols,
                    tabla_formulas,
                )

                st.download_button(
                    label="Descargar resultado completo en Excel",
                    data=excel_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn_performance.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

except Exception as e:
    st.error("No se pudo calcular la performance TAT.")
    st.exception(e)
