
# ============================================================
# 14_VISTA_EJECUTIVA_ZOOM_PROCESOS
# Vista ejecutiva Zoom procesos
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Inspiración visual:
# - Power BI Performance de Procesos
# - Columnas por proceso: TAT, Lib SolPed, Comprador, Proveedor, Logística
# - Barras horizontales 100% apiladas por grupo de compras
# - Cumple = gris, No cumple = rojo
# - Línea de meta ejecutiva
# ============================================================

import io
import base64
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# Configuración general
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"

COLOR_CUMPLE = "#5F6264"
COLOR_NO_CUMPLE = "#E83E51"
COLOR_META = "#00593A"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"
COLOR_GRID = "#D1D5DB"

COLOR_EN_PROCESO = "#F4B400"
COLOR_NO_APLICA = "#9CA3AF"
COLOR_SIN_DATOS = "#D1D5DB"

META_CUMPLIMIENTO = 65

COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - ME80FN"

COLUMNAS_REQUERIDAS_FECHAS = [
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
    "Fecha de entrada - NME80FN",
    "Fecha de documento - NME80FN",
    "Fecha contabilización - NME80FN",
    "Fecha facturación proveedor - NME80FN",
    "Fecha recepción mercancía - NME80FN",
]

PROCESOS_DASHBOARD = [
    {
        "titulo": "Dx TAT",
        "col_perf": "performance_tat_total",
        "col_dias": "dias_tat_total",
    },
    {
        "titulo": "Dx Lib Solped",
        "col_perf": "performance_liberacion_solped",
        "col_dias": "dias_liberacion_solped",
    },
    {
        "titulo": "Dx Comprador",
        "col_perf": "performance_comprador",
        "col_dias": "dias_comprador",
    },
    {
        "titulo": "Dx Proveedor",
        "col_perf": "performance_proveedor",
        "col_dias": "dias_proveedor",
    },
    {
        "titulo": "Dx Logística",
        "col_perf": "performance_logistica",
        "col_dias": "dias_logistica",
    },
]


# ============================================================
# Estilos
# ============================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 4.25rem;
            padding-bottom: 1.2rem;
            max-width: 1450px;
        }

        .exec-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            padding: 12px 16px 8px 16px;
            border-radius: 18px;
            background: linear-gradient(90deg, #F8FAFC 0%, #FFFFFF 100%);
            border: 1px solid #E5E7EB;
            margin-bottom: 12px;
        }

        .exec-title {
            color: #111827;
            font-size: 22px;
            font-weight: 850;
            letter-spacing: .2px;
            margin: 0;
        }

        .exec-subtitle {
            color: #6B7280;
            font-size: 12px;
            margin-top: 2px;
        }

        .exec-filter-note {
            color: #374151;
            font-size: 12px;
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 8px 12px;
        }

        .exec-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 8px 20px rgba(17, 24, 39, 0.04);
            height: 100%;
        }

        .exec-kpi-title {
            color: #6B7280;
            font-size: 12px;
            font-weight: 750;
            margin-bottom: 4px;
        }

        .exec-kpi-value {
            color: #111827;
            font-size: 28px;
            font-weight: 900;
            line-height: 1.0;
        }

        .exec-kpi-subtitle {
            color: #6B7280;
            font-size: 12px;
            margin-top: 6px;
            line-height: 1.3;
        }

        .exec-section-title {
            color: #111827;
            font-size: 17px;
            font-weight: 850;
            margin: 12px 0 2px 0;
        }

        .exec-small {
            color: #6B7280;
            font-size: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Logo
# ============================================================

def mostrar_logo():
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
                margin-top: 5px;
                margin-bottom: 10px;
            ">
                <img 
                    src="data:image/svg+xml;base64,{logo_base64}" 
                    style="width: 220px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# Utilidades
# ============================================================

def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def normalizar_columnas_me80fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    renombrar = {
        col: col.replace("NME80FN", "ME80FN")
        for col in df.columns
        if "NME80FN" in col
    }

    df = df.rename(columns=renombrar)

    for col in ["Estado del match", "estado_match"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.replace("NME80FN", "ME80FN", regex=False)
            )

    return df


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


def formatear_entero(valor) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return "—"

    return f"{int(round(numero)):,}"


def formatear_porcentaje(valor) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return "—"

    return f"{numero:.1f}%"


def normalizar_estado_performance(valor) -> str:
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

    if texto == "en proceso":
        return "En proceso"

    if texto in ["no aplica", "no aplica al analisis", "no aplica al análisis"]:
        return "No aplica"

    if texto in ["nan", "none", "<na>", "null", "", "sin datos"]:
        return "Sin datos"

    return "Sin datos"


def buscar_columna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    for col in candidatos:
        if col in df.columns:
            return col

    return None


def obtener_columna_centro(df: pd.DataFrame) -> str | None:
    return buscar_columna(
        df,
        [
            "Centro - ME5A",
            "Centro",
            "Centro - ME80FN",
            "me80fn_centro",
        ],
    )


def obtener_columna_grupo_compras(df: pd.DataFrame) -> str | None:
    return buscar_columna(
        df,
        [
            "Grupo de compras - ME5A",
            "Grupo de compras",
            "Grupo compras",
            "grupo_compras",
            "grupo_de_compras",
            "Purchasing Group",
        ],
    )


def validar_fechas_finales(df: pd.DataFrame):
    faltantes = [
        col for col in COLUMNAS_REQUERIDAS_FECHAS
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas de fechas finales: {faltantes}. "
            "Primero ejecuta 05_CALCULOS o carga un archivo con fechas finales."
        )


# ============================================================
# Performance
# ============================================================

def evaluar_performance_basica(
    dias: pd.Series,
    umbral: pd.Series,
    texto_sin_dato: str = "No aplica",
    negativos_no_aplican: bool = True,
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

    resultado.loc[mask_negativos] = "No aplica"
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


@st.cache_data(show_spinner=False)
def preparar_base_procesos(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    df = normalizar_columnas_me80fn(df)

    validar_fechas_finales(df)

    for col in COLUMNAS_FECHA_PERFORMANCE:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])

    if "tipo_oc" not in df.columns:
        if COL_PEDIDO in df.columns:
            df["tipo_oc"] = df[COL_PEDIDO].apply(extraer_tipo_oc)
        elif COL_DOCUMENTO_COMPRAS in df.columns:
            df["tipo_oc"] = df[COL_DOCUMENTO_COMPRAS].apply(extraer_tipo_oc)
        else:
            df["tipo_oc"] = pd.NA
    else:
        df["tipo_oc"] = df["tipo_oc"].apply(extraer_tipo_oc)

    df["tipo_oc"] = df["tipo_oc"].astype("string")

    if "dias_liberacion_solped" not in df.columns:
        df["dias_liberacion_solped"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_LIBERACION_FINAL],
            fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL],
        )

    if "dias_comprador" not in df.columns:
        df["dias_comprador"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_PEDIDO_FINAL],
            fecha_inicio=df[COL_FECHA_LIBERACION_FINAL],
        )

    if "dias_proveedor" not in df.columns:
        df["dias_proveedor"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_FACTURACION_FINAL],
            fecha_inicio=df[COL_FECHA_PEDIDO_FINAL],
        )

    if "dias_logistica" not in df.columns:
        df["dias_logistica"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
            fecha_inicio=df[COL_FECHA_FACTURACION_FINAL],
        )

    if "dias_tat_total" not in df.columns:
        df["dias_tat_total"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
            fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL],
        )

    columnas_dias = [
        "dias_liberacion_solped",
        "dias_comprador",
        "dias_proveedor",
        "dias_logistica",
        "dias_tat_total",
    ]

    if "tiene_fechas_inconsistentes" not in df.columns:
        df["tiene_fechas_inconsistentes"] = (
            df[columnas_dias]
            .lt(0)
            .any(axis=1, skipna=True)
        )

    if "performance_liberacion_solped" not in df.columns:
        df["performance_liberacion_solped"] = evaluar_performance_basica(
            dias=df["dias_liberacion_solped"],
            umbral=pd.Series(2, index=df.index),
            texto_sin_dato="No aplica",
        )

    if "performance_comprador" not in df.columns:
        df["performance_comprador"] = evaluar_performance_basica(
            dias=df["dias_comprador"],
            umbral=pd.Series(10, index=df.index),
            texto_sin_dato="No aplica",
        )

    if "performance_proveedor" not in df.columns:
        umbral_proveedor = pd.to_numeric(
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

        df["performance_proveedor"] = evaluar_performance_basica(
            dias=df["dias_proveedor"],
            umbral=umbral_proveedor,
            texto_sin_dato="Sin datos",
        )

    if "performance_logistica" not in df.columns:
        df["performance_logistica"] = evaluar_performance_basica(
            dias=df["dias_logistica"],
            umbral=pd.Series(11, index=df.index),
            texto_sin_dato="No aplica",
        )

    if "performance_tat_total" not in df.columns:
        df["performance_tat_total"] = evaluar_performance_tat(df)

    for proceso in PROCESOS_DASHBOARD:
        col_perf = proceso["col_perf"]

        if col_perf in df.columns:
            df[col_perf] = df[col_perf].apply(normalizar_estado_performance)

    col_grupo_compras = obtener_columna_grupo_compras(df)

    if col_grupo_compras is None:
        df["grupo_compras_zoom"] = "Sin grupo"
    else:
        df["grupo_compras_zoom"] = (
            df[col_grupo_compras]
            .astype("string")
            .str.strip()
            .fillna("Sin grupo")
        )

        df["grupo_compras_zoom"] = df["grupo_compras_zoom"].replace(
            {
                "": "Sin grupo",
                "<NA>": "Sin grupo",
                "nan": "Sin grupo",
                "None": "Sin grupo",
            }
        )

    col_centro = obtener_columna_centro(df)

    if col_centro is None:
        df["centro_zoom"] = "Sin centro"
    else:
        df["centro_zoom"] = (
            df[col_centro]
            .astype("string")
            .str.strip()
            .fillna("Sin centro")
        )

    df["periodo_fecha"] = (
        df[COL_FECHA_RECEPCION_FINAL]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["anio"] = df[COL_FECHA_RECEPCION_FINAL].dt.year
    df["mes_num"] = df[COL_FECHA_RECEPCION_FINAL].dt.month

    return df


# ============================================================
# Filtros y resúmenes
# ============================================================

def aplicar_filtros_zoom(
    df_base: pd.DataFrame,
    fecha_inicio,
    fecha_fin,
    performance_sel: list,
    centros_sel: list,
    grupos_sel: list,
) -> pd.DataFrame:

    df = df_base.copy()

    if fecha_inicio is not None and fecha_fin is not None:
        fecha_inicio_ts = pd.Timestamp(fecha_inicio)
        fecha_fin_ts = pd.Timestamp(fecha_fin) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

        df = df[
            df[COL_FECHA_RECEPCION_FINAL].notna()
            & df[COL_FECHA_RECEPCION_FINAL].between(fecha_inicio_ts, fecha_fin_ts)
        ].copy()

    if performance_sel:
        df = df[
            df["performance_tat_total"].isin(performance_sel)
        ].copy()

    if centros_sel:
        df = df[
            df["centro_zoom"].isin(centros_sel)
        ].copy()

    if grupos_sel:
        df = df[
            df["grupo_compras_zoom"].isin(grupos_sel)
        ].copy()

    return df


def crear_orden_grupos(df: pd.DataFrame, top_n: int) -> list[str]:
    if df.empty:
        return []

    base = df[
        df["performance_tat_total"].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        return []

    orden = (
        base
        .groupby("grupo_compras_zoom")
        .size()
        .sort_values(ascending=False)
        .head(int(top_n))
        .index
        .astype(str)
        .tolist()
    )

    return orden


def crear_resumen_proceso(
    df: pd.DataFrame,
    col_perf: str,
    grupos_ordenados: list[str],
) -> pd.DataFrame:

    columnas = [
        "grupo_compras_zoom",
        "Cumple",
        "No cumple",
        "Evaluables",
        "% Cumple",
        "% No cumple",
    ]

    if df.empty or col_perf not in df.columns:
        return pd.DataFrame(columns=columnas)

    base = df[
        df["grupo_compras_zoom"].isin(grupos_ordenados)
        & df[col_perf].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        return pd.DataFrame(columns=columnas)

    resumen = (
        base
        .groupby(["grupo_compras_zoom", col_perf])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index="grupo_compras_zoom",
        columns=col_perf,
        values="cantidad",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for col in ["Cumple", "No cumple"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["Evaluables"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Evaluables"] > 0,
        tabla["Cumple"] / tabla["Evaluables"] * 100,
        0,
    )

    tabla["% No cumple"] = np.where(
        tabla["Evaluables"] > 0,
        tabla["No cumple"] / tabla["Evaluables"] * 100,
        0,
    )

    tabla["grupo_compras_zoom"] = pd.Categorical(
        tabla["grupo_compras_zoom"],
        categories=grupos_ordenados,
        ordered=True,
    )

    tabla = tabla.sort_values("grupo_compras_zoom").reset_index(drop=True)

    return tabla[columnas]


def calcular_kpis_zoom(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "evaluables": 0,
            "cumple": 0,
            "no_cumple": 0,
            "pct_cumple": 0,
            "pct_no_cumple": 0,
            "grupos": 0,
        }

    estado = df["performance_tat_total"].apply(normalizar_estado_performance)

    cumple = int(estado.eq("Cumple").sum())
    no_cumple = int(estado.eq("No cumple").sum())
    evaluables = cumple + no_cumple

    return {
        "evaluables": evaluables,
        "cumple": cumple,
        "no_cumple": no_cumple,
        "pct_cumple": cumple / evaluables * 100 if evaluables else 0,
        "pct_no_cumple": no_cumple / evaluables * 100 if evaluables else 0,
        "grupos": int(df["grupo_compras_zoom"].nunique()),
    }


# ============================================================
# Visuales
# ============================================================

def titulo_vista_ejecutiva(nombre_archivo: str):
    st.markdown(
        f"""
        <div class="exec-header">
            <div>
                <div class="exec-title">14_VISTA_EJECUTIVA · Zoom procesos</div>
                <div class="exec-subtitle">
                    Vista tipo Power BI por grupo de compras y proceso TAT.
                </div>
            </div>
            <div class="exec-filter-note">
                Archivo activo: <b>{nombre_archivo}</b><br>
                Meta de cumplimiento: <b>{META_CUMPLIMIENTO}%</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_kpi_ejecutivo(titulo: str, valor: str, subtitulo: str):
    st.markdown(
        f"""
        <div class="exec-card">
            <div class="exec-kpi-title">{titulo}</div>
            <div class="exec-kpi-value">{valor}</div>
            <div class="exec-kpi-subtitle">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def grafico_proceso_horizontal(
    tabla: pd.DataFrame,
    titulo: str,
    mostrar_eje_y: bool = True,
):
    if tabla.empty:
        st.info(f"Sin datos para {titulo}.")
        return

    data = tabla.copy().iloc[::-1].reset_index(drop=True)

    y = np.arange(len(data))

    cumple_pct = pd.to_numeric(data["% Cumple"], errors="coerce").fillna(0).to_numpy()
    no_cumple_pct = pd.to_numeric(data["% No cumple"], errors="coerce").fillna(0).to_numpy()

    etiquetas = data["grupo_compras_zoom"].astype(str).tolist()

    fig_height = max(4.35, len(data) * 0.52)
    fig, ax = plt.subplots(figsize=(3.85, fig_height), dpi=180)

    ax.barh(
        y,
        cumple_pct,
        color=COLOR_CUMPLE,
        height=0.70,
        label="Cumple",
        edgecolor="white",
        linewidth=0.7,
    )

    ax.barh(
        y,
        no_cumple_pct,
        left=cumple_pct,
        color=COLOR_NO_CUMPLE,
        height=0.70,
        label="No cumple",
        edgecolor="white",
        linewidth=0.7,
    )

    ax.axvline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle=(0, (2, 2)),
        linewidth=1.8,
        alpha=0.95,
    )

    for i, (c_pct, nc_pct) in enumerate(zip(cumple_pct, no_cumple_pct)):
        if c_pct >= 15:
            ax.text(
                c_pct / 2,
                i,
                f"{c_pct:.1f}%",
                ha="center",
                va="center",
                fontsize=7.2,
                color="white",
                fontweight="bold",
            )

        if nc_pct >= 15:
            ax.text(
                c_pct + nc_pct / 2,
                i,
                f"{nc_pct:.1f}%",
                ha="center",
                va="center",
                fontsize=7.2,
                color="white",
                fontweight="bold",
            )

    ax.set_xlim(0, 100)
    ax.set_xticks([0, 50, 100])
    ax.set_xticklabels(["0%", "50%", "100%"], fontsize=8, color=COLOR_MUTED)

    if mostrar_eje_y:
        ax.set_yticks(y)
        ax.set_yticklabels(etiquetas, fontsize=8, color=COLOR_MUTED)
        ax.set_ylabel("Grupo de compras", fontsize=8, color=COLOR_TEXTO)
    else:
        ax.set_yticks(y)
        ax.set_yticklabels([""] * len(y))

    ax.set_title(
        titulo,
        fontsize=11.5,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )

    ax.grid(axis="x", linestyle=":", linewidth=0.7, color=COLOR_GRID)
    ax.grid(axis="y", visible=False)
    ax.tick_params(axis="both", length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.tight_layout()
    fig.subplots_adjust(top=0.92, bottom=0.10)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def mostrar_zoom_procesos(
    df_dashboard: pd.DataFrame,
    grupos_ordenados: list[str],
):
    st.markdown(
        """
        <div style="
            text-align:center;
            font-size:28px;
            font-weight:900;
            letter-spacing:4px;
            color:#2B2B2B;
            margin-top:4px;
            margin-bottom:2px;
        ">
            PERFORMANCE DE PROCESOS
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='exec-small' style='text-align:center; margin-bottom:10px;'>
            Barras horizontales 100% apiladas por grupo de compras.
            Gris = Cumple, rojo = No cumple, línea segmentada verde = meta.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style="
            display:flex;
            justify-content:center;
            gap:18px;
            align-items:center;
            font-size:12px;
            color:#4B5563;
            margin-bottom:8px;
        ">
            <span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{COLOR_CUMPLE};margin-right:4px;"></span>Cumple</span>
            <span><span style="display:inline-block;width:9px;height:9px;border-radius:50%;background:{COLOR_NO_CUMPLE};margin-right:4px;"></span>No cumple</span>
            <span><span style="display:inline-block;width:16px;height:0;border-top:2px dashed {COLOR_META};margin-right:4px;"></span>Meta {META_CUMPLIMIENTO}%</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not grupos_ordenados:
        st.info("No hay grupos de compras evaluables para mostrar.")
        return

    cols = st.columns(5, gap="small")

    for i, proceso in enumerate(PROCESOS_DASHBOARD):
        resumen = crear_resumen_proceso(
            df=df_dashboard,
            col_perf=proceso["col_perf"],
            grupos_ordenados=grupos_ordenados,
        )

        with cols[i]:
            grafico_proceso_horizontal(
                tabla=resumen,
                titulo=proceso["titulo"],
                mostrar_eje_y=True,
            )


# ============================================================
# Exportación
# ============================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


def convertir_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Registros",
        )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_excel(df)


# ============================================================
# App
# ============================================================

mostrar_logo()

if "df_tat" not in st.session_state or st.session_state.get("df_tat") is None:
    st.info("Primero debes cargar un archivo activo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

titulo_vista_ejecutiva(nombre_archivo)

try:
    with st.spinner("Preparando base de procesos..."):
        df_final = preparar_base_procesos(df_original)

except Exception as e:
    st.error("No se pudo preparar la base para Zoom procesos.")
    st.exception(e)
    st.stop()


# ============================================================
# Preparación de filtros
# ============================================================

fechas_validas = df_final[COL_FECHA_RECEPCION_FINAL].dropna()

fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

performance_options = ["Cumple", "No cumple"]
performance_default = [
    x for x in performance_options
    if x in df_final["performance_tat_total"].astype(str).unique()
]

if not performance_default:
    performance_default = performance_options

centros = sorted(
    df_final["centro_zoom"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

grupos_compras = sorted(
    df_final["grupo_compras_zoom"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)


# ============================================================
# Filtros visuales
# ============================================================

st.markdown(
    "<div class='exec-section-title'>Filtros ejecutivos</div>",
    unsafe_allow_html=True,
)

with st.form("form_filtros_zoom_procesos"):
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1, 1, 1, 1, 0.65])

    with col_f1:
        performance_sel = st.multiselect(
            "Performance TAT",
            options=performance_options,
            default=performance_default,
            key="zoom_procesos_performance",
        )

    with col_f2:
        centros_sel = st.multiselect(
            "Centro",
            options=centros,
            default=[],
            key="zoom_procesos_centros",
            help="Opcional. Si no seleccionas centros, se consideran todos.",
        )

    with col_f3:
        grupos_sel = st.multiselect(
            "Grupo de compras",
            options=grupos_compras,
            default=[],
            key="zoom_procesos_grupos_compras",
            help="Opcional. Si no seleccionas grupos, se muestran los principales por volumen.",
        )

    with col_f4:
        if fecha_min is not None and fecha_max is not None:
            rango_fechas = st.date_input(
                "Filtrar fecha",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                key="zoom_procesos_rango_fechas",
            )
        else:
            rango_fechas = None
            st.warning("No hay fechas válidas.")

    with col_f5:
        top_n = st.number_input(
            "Top grupos",
            min_value=3,
            max_value=25,
            value=9,
            step=1,
            key="zoom_procesos_top_n",
        )

    st.form_submit_button(
        "Actualizar Zoom procesos",
        use_container_width=True,
        type="primary",
    )


if (
    rango_fechas is not None
    and isinstance(rango_fechas, (tuple, list))
    and len(rango_fechas) == 2
):
    fecha_inicio = rango_fechas[0]
    fecha_fin = rango_fechas[1]
else:
    fecha_inicio = None
    fecha_fin = None


# ============================================================
# Aplicar filtros
# ============================================================

df_dashboard = aplicar_filtros_zoom(
    df_base=df_final,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    performance_sel=performance_sel,
    centros_sel=centros_sel,
    grupos_sel=grupos_sel,
)

if df_dashboard.empty:
    st.warning("No hay registros con los filtros seleccionados.")
    st.stop()

if grupos_sel:
    grupos_ordenados = grupos_sel
else:
    grupos_ordenados = crear_orden_grupos(
        df=df_dashboard,
        top_n=int(top_n),
    )

df_dashboard = df_dashboard[
    df_dashboard["grupo_compras_zoom"].isin(grupos_ordenados)
].copy()

if df_dashboard.empty:
    st.warning("No hay registros para los grupos seleccionados.")
    st.stop()


# ============================================================
# KPIs
# ============================================================

kpis = calcular_kpis_zoom(df_dashboard)

col_k1, col_k2, col_k3, col_k4 = st.columns(4)

with col_k1:
    mostrar_kpi_ejecutivo(
        "Registros evaluables",
        formatear_entero(kpis["evaluables"]),
        f"{formatear_entero(kpis['cumple'])} cumplen · {formatear_entero(kpis['no_cumple'])} no cumplen.",
    )

with col_k2:
    mostrar_kpi_ejecutivo(
        "Cumplimiento TAT",
        formatear_porcentaje(kpis["pct_cumple"]),
        f"Meta ejecutiva: {META_CUMPLIMIENTO}%.",
    )

with col_k3:
    mostrar_kpi_ejecutivo(
        "No cumplimiento TAT",
        formatear_porcentaje(kpis["pct_no_cumple"]),
        "Complemento sobre registros evaluables.",
    )

with col_k4:
    mostrar_kpi_ejecutivo(
        "Grupos de compra",
        formatear_entero(kpis["grupos"]),
        f"Visualizando hasta {formatear_entero(top_n)} grupos.",
    )


# ============================================================
# Visual principal
# ============================================================

mostrar_zoom_procesos(
    df_dashboard=df_dashboard,
    grupos_ordenados=grupos_ordenados,
)


# ============================================================
# Tablas y descargas
# ============================================================

with st.expander("Tabla resumen por proceso y grupo de compras", expanded=False):
    tablas = []

    for proceso in PROCESOS_DASHBOARD:
        tabla = crear_resumen_proceso(
            df=df_dashboard,
            col_perf=proceso["col_perf"],
            grupos_ordenados=grupos_ordenados,
        )

        if not tabla.empty:
            tabla = tabla.copy()
            tabla.insert(0, "Proceso", proceso["titulo"])
            tablas.append(tabla)

    if tablas:
        tabla_resumen = pd.concat(tablas, ignore_index=True)

        st.dataframe(
            tabla_resumen,
            use_container_width=True,
            hide_index=True,
            column_config={
                "% Cumple": st.column_config.ProgressColumn(
                    "% Cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "% No cumple": st.column_config.ProgressColumn(
                    "% No cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )
    else:
        st.info("No hay resumen disponible.")


with st.expander("Vista previa de registros filtrados", expanded=False):
    limite_vista = st.number_input(
        "Filas a mostrar",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
        key="zoom_procesos_limite_vista",
    )

    columnas_preferidas = [
        "grupo_compras_zoom",
        "centro_zoom",
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        "tipo_oc",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "dias_tat_total",
        "performance_tat_total",
        "dias_liberacion_solped",
        "performance_liberacion_solped",
        "dias_comprador",
        "performance_comprador",
        "dias_proveedor",
        "performance_proveedor",
        "dias_logistica",
        "performance_logistica",
    ]

    columnas_preferidas = [
        col for col in columnas_preferidas
        if col in df_dashboard.columns
    ]

    st.dataframe(
        df_dashboard[columnas_preferidas].head(int(limite_vista))
        if columnas_preferidas
        else df_dashboard.head(int(limite_vista)),
        use_container_width=True,
        hide_index=True,
    )


with st.expander("Descargar base Zoom procesos filtrada", expanded=False):
    firma_export = (
        f"{len(df_dashboard)}_"
        f"{fecha_inicio}_"
        f"{fecha_fin}_"
        f"{','.join(performance_sel)}_"
        f"{','.join(centros_sel)}_"
        f"{','.join(grupos_sel)}_"
        f"{top_n}"
    )

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        preparar_excel = st.button(
            "Preparar Excel",
            use_container_width=True,
            key="zoom_procesos_preparar_excel",
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                st.session_state["zoom_procesos_excel_bytes"] = convertir_a_excel_cache(df_dashboard)
                st.session_state["zoom_procesos_excel_firma"] = firma_export

        if (
            st.session_state.get("zoom_procesos_excel_bytes") is not None
            and st.session_state.get("zoom_procesos_excel_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Excel",
                data=st.session_state["zoom_procesos_excel_bytes"],
                file_name="14_VISTA_EJECUTIVA_ZOOM_PROCESOS_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True,
            key="zoom_procesos_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["zoom_procesos_csv_bytes"] = convertir_a_csv_cache(df_dashboard)
                st.session_state["zoom_procesos_csv_firma"] = firma_export

        if (
            st.session_state.get("zoom_procesos_csv_bytes") is not None
            and st.session_state.get("zoom_procesos_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV",
                data=st.session_state["zoom_procesos_csv_bytes"],
                file_name="14_VISTA_EJECUTIVA_ZOOM_PROCESOS_filtrado.csv",
                mime="text/csv",
                use_container_width=True,
            )
