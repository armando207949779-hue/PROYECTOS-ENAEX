# ============================================================
# 16_VISTA_PROVEEDORES_VERSION_5
# Vista ejecutiva de Performance Proveedor
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Enfoque:
# - Vista ejecutiva inspirada en 13_VISTA_EJECUTIVA_PERFORMANCE_PLANTAS
# - Base de análisis: registros evaluables Cumple + No cumple
# - Resumen global proveedor con desglose por centro
# - Tendencia mensual proveedor
# - Proveedores por cantidad de registros evaluables
# - Tabla ejecutiva de proveedores con buscador, filtro y umbral
# - Filtro ejecutivo por centro: Prillex, Rio Loa, Teatinos y Servicios
# - Priorización de proveedores críticos por volumen y % de incumplimiento con umbral editable
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

META_CUMPLIMIENTO = 65

COL_PROVEEDOR = "Proveedor ERP - ARIBA"
COL_PERFORMANCE_PROVEEDOR = "performance_proveedor"
COL_DIAS_PROVEEDOR = "dias_proveedor"
COL_UMBRAL_PROVEEDOR = "umbral_proveedor"
COL_FECHA_PROVEEDOR = "Fecha facturación proveedor - ME80FN"

COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - ME80FN"

CENTROS_DEFAULT = [
    "Prillex",
    "Rio Loa",
    "Teatinos",
    "Servicios",
]

MAPA_CENTROS_PRINCIPALES = {
    "E002": "Prillex",
    "E024": "Rio Loa",
    "E026": "Teatinos",
}

CENTROS_EXCLUIR_SERVICIOS = [
    "E001",
    "E009",
    "E021",
]

TOP_N_DEFAULT = 20

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


# ============================================================
# Estilos
# ============================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 4.25rem;
            padding-bottom: 1.2rem;
            max-width: 1380px;
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


def obtener_columna_fecha(df: pd.DataFrame) -> str | None:
    candidatos = [
        COL_FECHA_PROVEEDOR,
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "Fecha recepción mercancía - ME80FN",
        "Fecha facturación proveedor - NME80FN",
    ]

    for col in candidatos:
        if col in df.columns:
            return col

    return None


def buscar_columna_centro(df: pd.DataFrame) -> str | None:
    candidatos = [
        "Centro - ME5A",
        "Centro",
        "Centro - ME80FN",
        "me80fn_centro",
    ]

    for col in candidatos:
        if col in df.columns:
            return col

    return None


def obtener_grupo_centro(centro) -> str:
    if pd.isna(centro):
        return "Servicios"

    centro_txt = str(centro).strip().upper()

    if centro_txt in MAPA_CENTROS_PRINCIPALES:
        return MAPA_CENTROS_PRINCIPALES[centro_txt]

    if centro_txt in CENTROS_EXCLUIR_SERVICIOS:
        return "Excluir"

    return "Servicios"


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


def titulo_vista_proveedores(nombre_archivo: str):
    st.markdown(
        f"""
        <div class="exec-header">
            <div>
                <div class="exec-title">16_VISTA_PROVEEDORES · Performance proveedor</div>
                <div class="exec-subtitle">
                    Vista ejecutiva de proveedores: tabla principal, cumplimiento, volumen y evolución mensual.
                </div>
            </div>
            <div class="exec-filter-note">
                Archivo activo: <b>{nombre_archivo}</b><br>
                Base principal: <b>Cumple + No cumple</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def etiqueta_mes_corta(fecha) -> str:
    if pd.isna(fecha):
        return "—"

    fecha = pd.Timestamp(fecha)
    return MESES_NOMBRE.get(int(fecha.month), str(fecha.month))


def preparar_tabla_ejecutiva_display(tabla_proveedores: pd.DataFrame) -> pd.DataFrame:
    if tabla_proveedores.empty:
        return pd.DataFrame()

    salida = tabla_proveedores.copy()

    columnas_orden = [
        "proveedor_grafico",
        "Cumple",
        "No cumple",
        "Evaluables",
        "Umbral proveedor",
        "% Cumple",
        "% No cumple",
        "Promedio días proveedor",
    ]

    columnas_orden = [c for c in columnas_orden if c in salida.columns]

    salida = salida[columnas_orden].copy()
    salida = salida.sort_values(
        ["Evaluables", "% No cumple"],
        ascending=[False, False],
    ).reset_index(drop=True)

    return salida


# ============================================================
# Preparación base proveedores
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_base_proveedores(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)

    columnas_requeridas = [
        COL_PROVEEDOR,
        COL_PERFORMANCE_PROVEEDOR,
    ]

    faltantes = [c for c in columnas_requeridas if c not in df.columns]

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas para la vista de proveedores: {faltantes}"
        )

    df[COL_PROVEEDOR] = (
        df[COL_PROVEEDOR]
        .astype("string")
        .str.strip()
    )

    df["proveedor_grafico"] = df[COL_PROVEEDOR].fillna("Sin proveedor ARIBA")
    df["proveedor_grafico"] = df["proveedor_grafico"].replace("", "Sin proveedor ARIBA")

    col_centro = buscar_columna_centro(df)

    if col_centro is not None:
        df["centro_grafico"] = (
            df[col_centro]
            .astype("string")
            .str.strip()
            .str.upper()
        )
    else:
        df["centro_grafico"] = pd.NA

    df["centro_grafico"] = df["centro_grafico"].fillna("Sin centro")
    df["centro_grupo"] = df["centro_grafico"].apply(obtener_grupo_centro)

    df["performance_proveedor_norm"] = (
        df[COL_PERFORMANCE_PROVEEDOR]
        .apply(normalizar_estado_performance)
    )

    if COL_DIAS_PROVEEDOR in df.columns:
        df[COL_DIAS_PROVEEDOR] = pd.to_numeric(
            df[COL_DIAS_PROVEEDOR],
            errors="coerce",
        )

    if COL_UMBRAL_PROVEEDOR in df.columns:
        df[COL_UMBRAL_PROVEEDOR] = pd.to_numeric(
            df[COL_UMBRAL_PROVEEDOR],
            errors="coerce",
        )

    col_fecha = obtener_columna_fecha(df)

    if col_fecha is not None:
        df["fecha_proveedor_grafico"] = convertir_fecha_columna(df[col_fecha])
        df["periodo_fecha"] = (
            df["fecha_proveedor_grafico"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
        df["anio"] = df["fecha_proveedor_grafico"].dt.year
        df["mes_num"] = df["fecha_proveedor_grafico"].dt.month
        df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)
        df["periodo_label"] = np.where(
            df["anio"].notna() & df["mes_nombre"].notna(),
            df["mes_nombre"].astype(str)
            + " "
            + df["anio"].astype("Int64").astype(str),
            pd.NA,
        )
    else:
        df["fecha_proveedor_grafico"] = pd.NaT
        df["periodo_fecha"] = pd.NaT
        df["anio"] = pd.NA
        df["mes_num"] = pd.NA
        df["mes_nombre"] = pd.NA
        df["periodo_label"] = pd.NA

    return df


# ============================================================
# Filtros
# ============================================================

def aplicar_filtros_proveedores(
    df_base: pd.DataFrame,
    fecha_inicio,
    fecha_fin,
    centros_sel: list,
    proveedores_sel: list,
    perf_sel: list,
    incluir_sin_proveedor: bool,
) -> pd.DataFrame:

    df = df_base.copy()

    if not incluir_sin_proveedor:
        df = df[df["proveedor_grafico"].ne("Sin proveedor ARIBA")].copy()

    if centros_sel:
        df = df[df["centro_grupo"].isin(centros_sel)].copy()

    df = df[df["centro_grupo"].ne("Excluir")].copy()

    if fecha_inicio is not None and fecha_fin is not None:
        fecha_inicio_ts = pd.Timestamp(fecha_inicio)
        fecha_fin_ts = pd.Timestamp(fecha_fin) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

        df = df[
            df["fecha_proveedor_grafico"].notna()
            & df["fecha_proveedor_grafico"].between(fecha_inicio_ts, fecha_fin_ts)
        ].copy()

    if proveedores_sel:
        df = df[df["proveedor_grafico"].isin(proveedores_sel)].copy()

    if perf_sel:
        df = df[df["performance_proveedor_norm"].isin(perf_sel)].copy()

    df = df[df["performance_proveedor_norm"].isin(["Cumple", "No cumple"])].copy()

    return df


# ============================================================
# Resúmenes
# ============================================================


def resumir_umbral_proveedor(serie: pd.Series) -> str:
    valores = (
        pd.to_numeric(serie, errors="coerce")
        .dropna()
        .round(0)
        .astype(int)
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    if not valores:
        return "—"

    return " / ".join(str(v) for v in valores)


def filtrar_tabla_ejecutiva_proveedores(
    tabla: pd.DataFrame,
    texto_busqueda: str,
    proveedores_sel: list,
) -> pd.DataFrame:
    salida = tabla.copy()

    if texto_busqueda:
        texto = str(texto_busqueda).strip().lower()
        if texto:
            salida = salida[
                salida["proveedor_grafico"]
                .astype(str)
                .str.lower()
                .str.contains(texto, na=False)
            ].copy()

    if proveedores_sel:
        salida = salida[
            salida["proveedor_grafico"].astype(str).isin(proveedores_sel)
        ].copy()

    return salida.reset_index(drop=True)


def crear_tabla_prioridad_proveedores(
    tabla: pd.DataFrame,
    umbral_no_cumplimiento: float = 65,
    min_evaluables: int = 2,
) -> pd.DataFrame:
    if tabla.empty:
        return pd.DataFrame()

    salida = tabla.copy()
    salida["Evaluables"] = pd.to_numeric(salida["Evaluables"], errors="coerce").fillna(0)
    salida["% No cumple"] = pd.to_numeric(salida["% No cumple"], errors="coerce").fillna(0)
    salida["No cumple"] = pd.to_numeric(salida["No cumple"], errors="coerce").fillna(0)

    salida = salida[
        salida["Evaluables"].gt(min_evaluables - 1)
        & salida["% No cumple"].gt(umbral_no_cumplimiento)
    ].copy()

    if salida.empty:
        return salida

    salida["Score prioridad"] = (
        salida["% No cumple"] / 100
        * salida["Evaluables"]
    )

    salida["Nivel prioridad"] = np.select(
        [
            salida["Evaluables"].ge(20) & salida["% No cumple"].ge(80),
            salida["Evaluables"].ge(10) & salida["% No cumple"].ge(70),
        ],
        [
            "Alta",
            "Media",
        ],
        default="Seguimiento",
    )

    return salida.sort_values(
        ["Score prioridad", "No cumple", "Evaluables", "% No cumple"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)



def calcular_kpis_proveedores(df_base: pd.DataFrame, df_dashboard: pd.DataFrame) -> dict:
    total_base = int(len(df_base))
    total_filtrado = int(len(df_dashboard))

    cumple = int(df_dashboard["performance_proveedor_norm"].eq("Cumple").sum())
    no_cumple = int(df_dashboard["performance_proveedor_norm"].eq("No cumple").sum())
    evaluables = cumple + no_cumple

    proveedores_identificados = int(
        df_dashboard["proveedor_grafico"]
        .ne("Sin proveedor ARIBA")
        .sum()
    )

    proveedores_unicos = int(
        df_dashboard.loc[
            df_dashboard["proveedor_grafico"].ne("Sin proveedor ARIBA"),
            "proveedor_grafico",
        ]
        .nunique()
    )

    pct_cumple = cumple / evaluables * 100 if evaluables else 0
    pct_no_cumple = no_cumple / evaluables * 100 if evaluables else 0
    pct_proveedor_identificado = proveedores_identificados / total_filtrado * 100 if total_filtrado else 0

    dias_promedio = (
        pd.to_numeric(df_dashboard[COL_DIAS_PROVEEDOR], errors="coerce").mean()
        if COL_DIAS_PROVEEDOR in df_dashboard.columns
        else np.nan
    )

    return {
        "total_base": total_base,
        "total_filtrado": total_filtrado,
        "evaluables": evaluables,
        "cumple": cumple,
        "no_cumple": no_cumple,
        "pct_cumple": pct_cumple,
        "pct_no_cumple": pct_no_cumple,
        "proveedores_identificados": proveedores_identificados,
        "proveedores_unicos": proveedores_unicos,
        "pct_proveedor_identificado": pct_proveedor_identificado,
        "dias_promedio": dias_promedio,
    }


def crear_resumen_proveedores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    resumen = (
        df
        .groupby(["proveedor_grafico", "performance_proveedor_norm"])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index="proveedor_grafico",
        columns="performance_proveedor_norm",
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

    if COL_DIAS_PROVEEDOR in df.columns:
        dias = (
            df
            .groupby("proveedor_grafico")[COL_DIAS_PROVEEDOR]
            .mean()
            .reset_index()
            .rename(columns={COL_DIAS_PROVEEDOR: "Promedio días proveedor"})
        )
        tabla = tabla.merge(dias, on="proveedor_grafico", how="left")
    else:
        tabla["Promedio días proveedor"] = np.nan

    if COL_UMBRAL_PROVEEDOR in df.columns:
        umbral = (
            df
            .groupby("proveedor_grafico")[COL_UMBRAL_PROVEEDOR]
            .agg(resumir_umbral_proveedor)
            .reset_index()
            .rename(columns={COL_UMBRAL_PROVEEDOR: "Umbral proveedor"})
        )
        tabla = tabla.merge(umbral, on="proveedor_grafico", how="left")
    else:
        tabla["Umbral proveedor"] = "—"

    return tabla.sort_values("Evaluables", ascending=False).reset_index(drop=True)


def crear_desglose_cumplimiento_centros(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "Centro",
        "Cumple",
        "No cumple",
        "Evaluables",
        "% Cumple",
        "% No cumple",
    ]

    base_centros = pd.DataFrame({"Centro": CENTROS_DEFAULT})

    if df.empty or "centro_grupo" not in df.columns:
        salida = base_centros.copy()
        salida["Cumple"] = 0
        salida["No cumple"] = 0
        salida["Evaluables"] = 0
        salida["% Cumple"] = 0.0
        salida["% No cumple"] = 0.0
        return salida[columnas]

    base = df[
        df["centro_grupo"].isin(CENTROS_DEFAULT)
        & df["performance_proveedor_norm"].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        salida = base_centros.copy()
        salida["Cumple"] = 0
        salida["No cumple"] = 0
        salida["Evaluables"] = 0
        salida["% Cumple"] = 0.0
        salida["% No cumple"] = 0.0
        return salida[columnas]

    resumen = (
        base
        .groupby(["centro_grupo", "performance_proveedor_norm"])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index="centro_grupo",
        columns="performance_proveedor_norm",
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

    tabla = tabla.rename(columns={"centro_grupo": "Centro"})
    tabla = base_centros.merge(tabla, on="Centro", how="left")

    for col in ["Cumple", "No cumple", "Evaluables"]:
        tabla[col] = pd.to_numeric(tabla[col], errors="coerce").fillna(0).astype(int)

    for col in ["% Cumple", "% No cumple"]:
        tabla[col] = pd.to_numeric(tabla[col], errors="coerce").fillna(0.0)

    tabla["_orden"] = tabla["Centro"].map({centro: i for i, centro in enumerate(CENTROS_DEFAULT)})
    tabla = tabla.sort_values("_orden").drop(columns="_orden").reset_index(drop=True)

    return tabla[columnas]


def crear_resumen_mensual_proveedores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "periodo_fecha" not in df.columns:
        return pd.DataFrame()

    base = df[
        df["periodo_fecha"].notna()
        & df["performance_proveedor_norm"].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        return pd.DataFrame()

    resumen = (
        base
        .groupby(["periodo_fecha", "periodo_label", "performance_proveedor_norm"])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=["periodo_fecha", "periodo_label"],
        columns="performance_proveedor_norm",
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

    return tabla.sort_values("periodo_fecha").reset_index(drop=True)



def preparar_ranking_volumen_proveedores(tabla: pd.DataFrame, top_n: int) -> pd.DataFrame:
    columnas = [
        "proveedor_grafico",
        "Cumple",
        "No cumple",
        "Evaluables",
        "% Cumple",
        "% No cumple",
        "Promedio días proveedor",
    ]

    if tabla.empty:
        return pd.DataFrame(columns=columnas)

    salida = tabla.copy()

    for col in ["Cumple", "No cumple", "Evaluables", "% Cumple", "% No cumple"]:
        if col in salida.columns:
            salida[col] = pd.to_numeric(salida[col], errors="coerce").fillna(0)

    salida = (
        salida[salida["Evaluables"].gt(0)]
        .sort_values(["Evaluables", "% No cumple"], ascending=[False, False])
        .head(int(top_n))
        .reset_index(drop=True)
    )

    columnas = [c for c in columnas if c in salida.columns]
    return salida[columnas]


def preparar_ranking_riesgo_proveedores(
    tabla: pd.DataFrame,
    top_n: int,
    min_evaluables: int = 2,
) -> pd.DataFrame:
    columnas = [
        "proveedor_grafico",
        "Nivel prioridad",
        "Cumple",
        "No cumple",
        "Evaluables",
        "% Cumple",
        "% No cumple",
        "Score riesgo",
        "Lectura ejecutiva",
    ]

    if tabla.empty:
        return pd.DataFrame(columns=columnas)

    salida = tabla.copy()

    for col in ["Cumple", "No cumple", "Evaluables", "% Cumple", "% No cumple"]:
        if col in salida.columns:
            salida[col] = pd.to_numeric(salida[col], errors="coerce").fillna(0)

    salida = salida[salida["Evaluables"].ge(int(min_evaluables))].copy()

    if salida.empty:
        return pd.DataFrame(columns=columnas)

    salida["Score riesgo"] = salida["Evaluables"] * salida["% No cumple"] / 100

    salida["Nivel prioridad"] = np.select(
        [
            salida["Evaluables"].ge(20) & salida["% No cumple"].ge(70),
            salida["Evaluables"].ge(10) & salida["% No cumple"].ge(60),
            salida["Score riesgo"].ge(5),
        ],
        [
            "Alta",
            "Media",
            "Seguimiento",
        ],
        default="Observación",
    )

    salida["Lectura ejecutiva"] = (
        salida["Evaluables"].round(0).astype(int).astype(str)
        + " evaluables · "
        + salida["% No cumple"].round(1).astype(str)
        + "% no cumple · score "
        + salida["Score riesgo"].round(1).astype(str)
    )

    salida = salida.sort_values(
        ["Score riesgo", "No cumple", "Evaluables", "% No cumple"],
        ascending=[False, False, False, False],
    ).head(int(top_n)).reset_index(drop=True)

    columnas = [c for c in columnas if c in salida.columns]
    return salida[columnas]


def clasificar_cuadrante_proveedor(
    evaluables: float,
    pct_no_cumple: float,
    mediana_volumen: float,
    mediana_incumplimiento: float,
) -> str:
    if evaluables >= mediana_volumen and pct_no_cumple >= mediana_incumplimiento:
        return "Alto volumen / Alto incumplimiento"

    if evaluables >= mediana_volumen and pct_no_cumple < mediana_incumplimiento:
        return "Alto volumen / Mejor performance"

    if evaluables < mediana_volumen and pct_no_cumple >= mediana_incumplimiento:
        return "Bajo volumen / Alto incumplimiento"

    return "Bajo volumen / Mejor performance"


def crear_matriz_riesgo_proveedores(tabla: pd.DataFrame) -> pd.DataFrame:
    if tabla.empty:
        return pd.DataFrame()

    salida = tabla.copy()

    for col in ["Evaluables", "% No cumple", "No cumple"]:
        if col in salida.columns:
            salida[col] = pd.to_numeric(salida[col], errors="coerce").fillna(0)

    salida = salida[salida["Evaluables"].gt(0)].copy()

    if salida.empty:
        return pd.DataFrame()

    mediana_volumen = float(salida["Evaluables"].median())
    mediana_incumplimiento = float(salida["% No cumple"].median())

    salida["Score riesgo"] = salida["Evaluables"] * salida["% No cumple"] / 100
    salida["Cuadrante"] = salida.apply(
        lambda fila: clasificar_cuadrante_proveedor(
            fila["Evaluables"],
            fila["% No cumple"],
            mediana_volumen,
            mediana_incumplimiento,
        ),
        axis=1,
    )

    return salida.sort_values("Score riesgo", ascending=False).reset_index(drop=True)


def grafico_ranking_volumen_proveedores(data: pd.DataFrame, top_n: int):
    if data.empty:
        st.info("No hay proveedores con registros evaluables para mostrar.")
        return

    plot_data = data.sort_values("Evaluables", ascending=True).copy()

    fig_height = max(4.5, len(plot_data) * 0.42)
    fig, ax = plt.subplots(figsize=(12, fig_height), dpi=160)

    y = np.arange(len(plot_data))
    cumple = pd.to_numeric(plot_data["Cumple"], errors="coerce").fillna(0)
    no_cumple = pd.to_numeric(plot_data["No cumple"], errors="coerce").fillna(0)
    evaluables = pd.to_numeric(plot_data["Evaluables"], errors="coerce").fillna(0)
    pct_no_cumple = pd.to_numeric(plot_data["% No cumple"], errors="coerce").fillna(0)

    ax.barh(y, cumple, color=COLOR_CUMPLE, label="Cumple")
    ax.barh(y, no_cumple, left=cumple, color=COLOR_NO_CUMPLE, label="No cumple")

    ax.set_yticks(y)
    ax.set_yticklabels(plot_data["proveedor_grafico"].astype(str), fontsize=8)

    for i, (total, pct) in enumerate(zip(evaluables, pct_no_cumple)):
        ax.text(
            total + max(evaluables.max() * 0.01, 0.5),
            i,
            f"{int(total):,} registros · {pct:.1f}% no cumple",
            va="center",
            ha="left",
            fontsize=7.7,
            color=COLOR_TEXTO,
        )

    ax.set_title(
        f"Respuesta 1 · Proveedores con mayor cantidad de registros evaluables (Top {top_n})",
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )
    ax.set_xlabel("Cantidad de registros evaluables", color=COLOR_MUTED)
    ax.legend(frameon=False, loc="lower right")
    ax.grid(axis="x", linestyle=":", linewidth=0.7, color=COLOR_GRID)
    ax.tick_params(axis="x", colors=COLOR_MUTED)
    ax.tick_params(axis="y", colors=COLOR_TEXTO)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def grafico_ranking_riesgo_proveedores(data: pd.DataFrame, top_n: int):
    if data.empty:
        st.info("No hay proveedores suficientes para calcular ranking de riesgo con los criterios actuales.")
        return

    plot_data = data.sort_values("Score riesgo", ascending=True).copy()

    fig_height = max(4.8, len(plot_data) * 0.45)
    fig, ax = plt.subplots(figsize=(12, fig_height), dpi=160)

    y = np.arange(len(plot_data))
    score = pd.to_numeric(plot_data["Score riesgo"], errors="coerce").fillna(0)
    evaluables = pd.to_numeric(plot_data["Evaluables"], errors="coerce").fillna(0)
    pct_no_cumple = pd.to_numeric(plot_data["% No cumple"], errors="coerce").fillna(0)

    ax.barh(y, score, color=COLOR_NO_CUMPLE, alpha=0.92)
    ax.set_yticks(y)
    ax.set_yticklabels(plot_data["proveedor_grafico"].astype(str), fontsize=8)

    for i, (score_val, total, pct) in enumerate(zip(score, evaluables, pct_no_cumple)):
        ax.text(
            score_val + max(score.max() * 0.01, 0.3),
            i,
            f"score {score_val:.1f} · {int(total):,} eval. · {pct:.1f}% no cumple",
            va="center",
            ha="left",
            fontsize=7.7,
            color=COLOR_TEXTO,
        )

    ax.set_title(
        f"Respuesta 2 · Proveedores con mayor volumen y peor performance (Top {top_n})",
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )
    ax.set_xlabel("Score de riesgo = Evaluables × % No cumple", color=COLOR_MUTED)
    ax.grid(axis="x", linestyle=":", linewidth=0.7, color=COLOR_GRID)
    ax.tick_params(axis="x", colors=COLOR_MUTED)
    ax.tick_params(axis="y", colors=COLOR_TEXTO)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def grafico_matriz_riesgo_proveedores(data: pd.DataFrame, top_n_labels: int = 8):
    if data.empty:
        st.info("No hay datos suficientes para construir la matriz de criticidad.")
        return

    plot_data = data.copy()
    x = pd.to_numeric(plot_data["Evaluables"], errors="coerce").fillna(0)
    y = pd.to_numeric(plot_data["% No cumple"], errors="coerce").fillna(0)
    score = pd.to_numeric(plot_data["Score riesgo"], errors="coerce").fillna(0)

    mediana_volumen = float(x.median()) if len(x) else 0
    mediana_incumplimiento = float(y.median()) if len(y) else 0

    tamanos = 45 + (score / score.max() * 430 if score.max() > 0 else 0)

    fig, ax = plt.subplots(figsize=(11.8, 6.0), dpi=160)

    ax.scatter(
        x,
        y,
        s=tamanos,
        alpha=0.62,
        color=COLOR_NO_CUMPLE,
        edgecolors="white",
        linewidth=0.8,
    )

    ax.axvline(mediana_volumen, color=COLOR_MUTED, linestyle=(0, (2, 2)), linewidth=1.2)
    ax.axhline(mediana_incumplimiento, color=COLOR_MUTED, linestyle=(0, (2, 2)), linewidth=1.2)

    etiquetas = plot_data.sort_values("Score riesgo", ascending=False).head(int(top_n_labels))

    for _, fila in etiquetas.iterrows():
        ax.text(
            float(fila["Evaluables"]),
            float(fila["% No cumple"]) + 1.2,
            str(fila["proveedor_grafico"])[:28],
            fontsize=7.2,
            color=COLOR_TEXTO,
            ha="center",
        )

    ax.set_title(
        "Respuesta 3 · Matriz de criticidad: volumen versus % de incumplimiento",
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )
    ax.set_xlabel("Cantidad de registros evaluables", color=COLOR_MUTED)
    ax.set_ylabel("% No cumple", color=COLOR_MUTED)
    ax.set_ylim(0, min(105, max(100, y.max() + 8)))
    ax.grid(True, linestyle=":", linewidth=0.7, color=COLOR_GRID)
    ax.tick_params(axis="x", colors=COLOR_MUTED)
    ax.tick_params(axis="y", colors=COLOR_MUTED)

    ax.text(
        0.99,
        0.97,
        "Más crítico\nAlto volumen + alto incumplimiento",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8.3,
        color=COLOR_NO_CUMPLE,
        fontweight="bold",
    )

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()
    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


# ============================================================
# Gráficos Matplotlib
# ============================================================

def grafico_donut_global(cumple: int, no_cumple: int):
    evaluables = cumple + no_cumple

    if evaluables <= 0:
        st.info("Sin registros evaluables.")
        return

    pct_cumple = cumple / evaluables * 100
    pct_no_cumple = no_cumple / evaluables * 100

    fig, ax = plt.subplots(figsize=(4.2, 3.2), dpi=180)

    ax.pie(
        [cumple, no_cumple],
        startangle=90,
        counterclock=False,
        colors=[COLOR_CUMPLE, COLOR_NO_CUMPLE],
        wedgeprops={
            "width": 0.42,
            "edgecolor": "white",
            "linewidth": 1.4,
        },
    )

    ax.text(
        0,
        0.08,
        f"{pct_cumple:.0f}%",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=COLOR_TEXTO,
    )

    ax.text(
        0,
        -0.16,
        "Cumple",
        ha="center",
        va="center",
        fontsize=9,
        color=COLOR_MUTED,
    )

    ax.text(
        1.05,
        -0.65,
        f"Cumple\n{cumple:,}\n{pct_cumple:.1f}%",
        ha="left",
        va="center",
        fontsize=8,
        color=COLOR_TEXTO,
    )

    ax.text(
        -1.05,
        0.82,
        f"No cumple\n{no_cumple:,}\n{pct_no_cumple:.1f}%",
        ha="right",
        va="center",
        fontsize=8,
        color=COLOR_TEXTO,
    )

    ax.axis("equal")
    fig.patch.set_alpha(0)
    fig.tight_layout(pad=0.2)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def grafico_barras_apiladas_top_proveedores(data: pd.DataFrame, top_n: int):
    if data.empty:
        st.info("No hay datos para graficar.")
        return

    plot_data = (
        data
        .sort_values("Evaluables", ascending=False)
        .head(top_n)
        .sort_values("Evaluables", ascending=True)
    )

    fig_height = max(4.5, len(plot_data) * 0.38)
    fig, ax = plt.subplots(figsize=(11.5, fig_height), dpi=160)

    y = np.arange(len(plot_data))

    cumple = pd.to_numeric(plot_data["Cumple"], errors="coerce").fillna(0)
    no_cumple = pd.to_numeric(plot_data["No cumple"], errors="coerce").fillna(0)

    ax.barh(
        y,
        cumple,
        color=COLOR_CUMPLE,
        label="Cumple",
    )

    ax.barh(
        y,
        no_cumple,
        left=cumple,
        color=COLOR_NO_CUMPLE,
        label="No cumple",
    )

    ax.set_yticks(y)
    ax.set_yticklabels(plot_data["proveedor_grafico"].astype(str), fontsize=8)
    ax.set_title(
        f"Top {top_n} proveedores por cantidad de registros",
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )
    ax.set_xlabel("Cantidad de registros evaluables", color=COLOR_MUTED)
    ax.legend(frameon=False, loc="lower right")

    ax.grid(False)
    ax.tick_params(axis="x", colors=COLOR_MUTED)
    ax.tick_params(axis="y", colors=COLOR_TEXTO)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def grafico_performance_proveedor_matplotlib(
    tabla_mensual: pd.DataFrame,
    titulo: str,
):
    if tabla_mensual.empty:
        st.info("No hay datos mensuales evaluables para graficar.")
        return

    data = tabla_mensual.copy()
    data["periodo_fecha"] = pd.to_datetime(data["periodo_fecha"], errors="coerce")
    data = data[data["periodo_fecha"].notna()].copy()
    data = data[data["Evaluables"].gt(0)].copy()
    data = data.sort_values("periodo_fecha").reset_index(drop=True)

    if data.empty:
        st.info("No hay meses con registros evaluables para graficar.")
        return

    x = np.arange(len(data))

    cumple_pct = pd.to_numeric(data["% Cumple"], errors="coerce").fillna(0).to_numpy()
    no_cumple_pct = pd.to_numeric(data["% No cumple"], errors="coerce").fillna(0).to_numpy()

    cumple_n = pd.to_numeric(data["Cumple"], errors="coerce").fillna(0).astype(int).to_numpy()
    no_cumple_n = pd.to_numeric(data["No cumple"], errors="coerce").fillna(0).astype(int).to_numpy()
    evaluables = pd.to_numeric(data["Evaluables"], errors="coerce").fillna(0).astype(int).to_numpy()

    labels = [etiqueta_mes_corta(v) for v in data["periodo_fecha"]]

    fig_width = max(9.5, len(data) * 0.85)
    fig, ax = plt.subplots(figsize=(fig_width, 4.4), dpi=180)

    bar_width = 0.78

    ax.bar(
        x,
        cumple_pct,
        width=bar_width,
        color=COLOR_CUMPLE,
        label="Cumple",
        edgecolor="white",
        linewidth=1.0,
    )

    ax.bar(
        x,
        no_cumple_pct,
        bottom=cumple_pct,
        width=bar_width,
        color=COLOR_NO_CUMPLE,
        label="No cumple",
        edgecolor="white",
        linewidth=1.0,
    )

    ax.axhline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle=(0, (2, 2)),
        linewidth=1.8,
        alpha=0.95,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    for i, (c_pct, nc_pct, c_n, nc_n, total) in enumerate(
        zip(cumple_pct, no_cumple_pct, cumple_n, no_cumple_n, evaluables)
    ):
        if total <= 0:
            continue

        if c_pct >= 8:
            ax.text(
                i,
                c_pct / 2,
                f"{c_pct:.1f}%",
                ha="center",
                va="center",
                fontsize=7.4,
                color="white",
                fontweight="bold",
            )

        if nc_pct >= 8:
            ax.text(
                i,
                c_pct + nc_pct / 2,
                f"{nc_pct:.1f}%",
                ha="center",
                va="center",
                fontsize=7.4,
                color="white",
                fontweight="bold",
            )
        elif nc_pct > 0:
            ax.text(
                i,
                min(98, c_pct + nc_pct + 1.8),
                f"{nc_pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=6.8,
                color=COLOR_NO_CUMPLE,
                fontweight="bold",
            )

    ax.set_ylim(0, 105)
    ax.set_yticks([0, 50, 100])
    ax.set_yticklabels(["0%", "50%", "100%"], fontsize=8, color=COLOR_MUTED)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, fontsize=8, color=COLOR_MUTED)

    ax.set_title(
        titulo,
        loc="left",
        fontsize=14.5,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )

    ax.grid(axis="y", linestyle=":", linewidth=0.7, color=COLOR_GRID)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=3,
        frameon=False,
        fontsize=8.6,
    )

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def mostrar_evolucion_por_anio_proveedor(tabla_mensual: pd.DataFrame):
    st.markdown(
        "<div class='exec-section-title'>Tendencia mensual proveedor</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='exec-small'>
            Barras 100% apiladas: gris oscuro = Cumple, rojo = No cumple.
            Los años anteriores quedan colapsados y el último año disponible queda visible por defecto.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tabla_mensual.empty:
        st.info("No hay datos mensuales disponibles.")
        return

    data = tabla_mensual.copy()
    data["periodo_fecha"] = pd.to_datetime(data["periodo_fecha"], errors="coerce")
    data = data[data["periodo_fecha"].notna()].copy()
    data = data[data["Evaluables"].gt(0)].copy()

    if data.empty:
        st.info("No hay meses con registros evaluables para graficar.")
        return

    data["anio_grafico"] = data["periodo_fecha"].dt.year
    anios = sorted(data["anio_grafico"].dropna().astype(int).unique().tolist())

    if not anios:
        st.info("No hay años disponibles para graficar.")
        return

    ultimo_anio = max(anios)

    for anio in anios:
        data_anio = (
            data[data["anio_grafico"].eq(anio)]
            .drop(columns=["anio_grafico"])
            .sort_values("periodo_fecha")
            .reset_index(drop=True)
        )

        evaluables_anio = int(pd.to_numeric(data_anio["Evaluables"], errors="coerce").fillna(0).sum())
        cumple_anio = int(pd.to_numeric(data_anio["Cumple"], errors="coerce").fillna(0).sum())
        no_cumple_anio = int(pd.to_numeric(data_anio["No cumple"], errors="coerce").fillna(0).sum())

        pct_cumple_anio = cumple_anio / evaluables_anio * 100 if evaluables_anio else 0
        pct_no_cumple_anio = no_cumple_anio / evaluables_anio * 100 if evaluables_anio else 0

        expanded = anio == ultimo_anio
        titulo_expander = (
            f"Año {anio} · "
            f"Evaluables: {formatear_entero(evaluables_anio)} · "
            f"Cumple: {formatear_porcentaje(pct_cumple_anio)} · "
            f"No cumple: {formatear_porcentaje(pct_no_cumple_anio)}"
        )

        with st.expander(titulo_expander, expanded=expanded):
            col_a1, col_a2, col_a3 = st.columns(3)

            with col_a1:
                mostrar_kpi_ejecutivo(
                    "Evaluables año",
                    formatear_entero(evaluables_anio),
                    f"{len(data_anio)} mes(es) con registros evaluables.",
                )

            with col_a2:
                mostrar_kpi_ejecutivo(
                    "Cumplimiento año",
                    formatear_porcentaje(pct_cumple_anio),
                    f"{formatear_entero(cumple_anio)} registros cumplen.",
                )

            with col_a3:
                mostrar_kpi_ejecutivo(
                    "No cumplimiento año",
                    formatear_porcentaje(pct_no_cumple_anio),
                    f"{formatear_entero(no_cumple_anio)} registros no cumplen.",
                )

            grafico_performance_proveedor_matplotlib(
                data_anio,
                titulo=f"Performance proveedor {anio}",
            )

            with st.expander(f"Tabla mensual proveedor {anio}", expanded=False):
                columnas = [
                    "periodo_label",
                    "Cumple",
                    "No cumple",
                    "Evaluables",
                    "% Cumple",
                    "% No cumple",
                ]

                columnas = [c for c in columnas if c in data_anio.columns]

                st.dataframe(
                    data_anio[columnas],
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


def grafico_prioridad_no_cumplimiento(
    data: pd.DataFrame,
    top_n: int,
    umbral_no_cumplimiento: float = 65,
):
    if data.empty:
        st.info(
            f"No hay proveedores con más de {umbral_no_cumplimiento:.0f}% de no cumplimiento "
            "y más de un registro evaluable."
        )
        return

    plot_data = (
        data
        .head(top_n)
        .sort_values("Evaluables", ascending=True)
        .copy()
    )

    fig_height = max(4.8, len(plot_data) * 0.42)
    fig, ax = plt.subplots(figsize=(11.8, fig_height), dpi=160)

    y = np.arange(len(plot_data))
    evaluables = pd.to_numeric(plot_data["Evaluables"], errors="coerce").fillna(0)
    pct_no_cumple = pd.to_numeric(plot_data["% No cumple"], errors="coerce").fillna(0)

    ax.barh(
        y,
        evaluables,
        color=COLOR_NO_CUMPLE,
        alpha=0.92,
    )

    ax.set_yticks(y)
    ax.set_yticklabels(plot_data["proveedor_grafico"].astype(str), fontsize=8)

    for i, (total, pct) in enumerate(zip(evaluables, pct_no_cumple)):
        ax.text(
            total + max(evaluables.max() * 0.01, 0.5),
            i,
            f"{int(total):,} eval. · {pct:.1f}% no cumple",
            va="center",
            ha="left",
            fontsize=7.8,
            color=COLOR_TEXTO,
        )

    ax.set_title(
        f"Críticos por volumen y % de incumplimiento > {umbral_no_cumplimiento:.0f}%",
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )

    ax.set_xlabel("Cantidad de registros evaluables", color=COLOR_MUTED)
    ax.grid(False)
    ax.tick_params(axis="x", colors=COLOR_MUTED)
    ax.tick_params(axis="y", colors=COLOR_TEXTO)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


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


def convertir_a_excel_criticos(
    tabla_prioridad: pd.DataFrame,
    df_dashboard: pd.DataFrame,
) -> bytes:
    output = io.BytesIO()

    proveedores_criticos = (
        tabla_prioridad["proveedor_grafico"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
        if not tabla_prioridad.empty and "proveedor_grafico" in tabla_prioridad.columns
        else []
    )

    detalle = df_dashboard[
        df_dashboard["proveedor_grafico"].astype(str).isin(proveedores_criticos)
    ].copy()

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        "centro_grafico",
        "centro_grupo",
        COL_PROVEEDOR,
        "proveedor_grafico",
        COL_FECHA_PROVEEDOR,
        "fecha_proveedor_grafico",
        COL_DIAS_PROVEEDOR,
        COL_UMBRAL_PROVEEDOR,
        COL_PERFORMANCE_PROVEEDOR,
        "performance_proveedor_norm",
        "origen",
        "sistema",
        "tipo_oc",
        "monto",
    ]

    columnas_detalle = [
        col for col in columnas_preferidas
        if col in detalle.columns
    ]

    if columnas_detalle:
        detalle = detalle[columnas_detalle].copy()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        tabla_prioridad.to_excel(
            writer,
            index=False,
            sheet_name="Resumen criticos",
        )

        detalle.to_excel(
            writer,
            index=False,
            sheet_name="Detalle registros",
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

titulo_vista_proveedores(nombre_archivo)

try:
    with st.spinner("Preparando base de proveedores..."):
        df_final = preparar_base_proveedores(df_original)

except Exception as e:
    st.error("No se pudo preparar la vista de proveedores.")
    st.exception(e)
    st.stop()


# ============================================================
# Preparación filtros
# ============================================================

df_pre_filtro = df_final.copy()

fechas_validas = df_pre_filtro["fecha_proveedor_grafico"].dropna()

fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

proveedores_disponibles = (
    df_pre_filtro["proveedor_grafico"]
    .dropna()
    .astype(str)
    .sort_values()
    .unique()
    .tolist()
)

centros_disponibles = [
    centro
    for centro in CENTROS_DEFAULT
    if centro in df_pre_filtro["centro_grupo"].dropna().astype(str).unique()
]

if not centros_disponibles:
    centros_disponibles = CENTROS_DEFAULT.copy()

perf_options = ["Cumple", "No cumple"]

st.markdown(
    "<div class='exec-section-title'>Filtros ejecutivos</div>",
    unsafe_allow_html=True,
)

st.caption(
    "La vista se calcula solo sobre registros evaluables: Cumple + No cumple. "
    "Puedes filtrar por centro y también incluir o excluir registros sin proveedor ARIBA."
)

with st.form("form_filtros_vista_proveedores"):
    col_f1, col_f2, col_f3, col_f4, col_f5, col_f6 = st.columns([1.15, 1.05, 1, 1.25, 0.8, 0.75])

    with col_f1:
        if fecha_min is not None and fecha_max is not None:
            rango_fechas = st.date_input(
                "Fecha proveedor",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                key="vista_proveedores_rango_fechas",
            )
        else:
            rango_fechas = None
            st.warning("No hay fechas válidas para filtrar.")

    with col_f2:
        centros_sel = st.multiselect(
            "Centro",
            options=centros_disponibles,
            default=centros_disponibles,
            key="vista_proveedores_centros",
            help="Por defecto considera Prillex, Rio Loa, Teatinos y Servicios.",
        )

    with col_f3:
        perf_sel = st.multiselect(
            "Performance proveedor",
            options=perf_options,
            default=perf_options,
            key="vista_proveedores_performance",
        )

    with col_f4:
        proveedores_sel = st.multiselect(
            "Proveedor",
            options=proveedores_disponibles,
            default=[],
            key="vista_proveedores_proveedor",
            help="Opcional. Si no seleccionas proveedor, se consideran todos.",
        )

    with col_f5:
        incluir_sin_proveedor = st.checkbox(
            "Incluir sin proveedor",
            value=False,
            key="vista_proveedores_incluir_sin_proveedor",
        )

    with col_f6:
        top_n = st.number_input(
            "Top N",
            min_value=5,
            max_value=50,
            value=TOP_N_DEFAULT,
            step=5,
            key="vista_proveedores_top_n",
        )

    st.form_submit_button(
        "Actualizar vista proveedores",
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

df_dashboard = aplicar_filtros_proveedores(
    df_base=df_final,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    centros_sel=centros_sel,
    proveedores_sel=proveedores_sel,
    perf_sel=perf_sel,
    incluir_sin_proveedor=incluir_sin_proveedor,
)

if df_dashboard.empty:
    st.warning("No hay registros evaluables con los filtros seleccionados.")
    st.stop()

tabla_proveedores = crear_resumen_proveedores(df_dashboard)
tabla_mensual = crear_resumen_mensual_proveedores(df_dashboard)
kpis = calcular_kpis_proveedores(df_final, df_dashboard)
st.markdown(
    f"""
    <div class='exec-small'>
        Fechas: {fecha_inicio if fecha_inicio else "Todas"} a {fecha_fin if fecha_fin else "Todas"} ·
        Centro: {", ".join(centros_sel) if centros_sel else "Todos"} ·
        Performance: {", ".join(perf_sel) if perf_sel else "Todas"} ·
        Proveedor: {", ".join(proveedores_sel) if proveedores_sel else "Todos"} ·
        Sin proveedor ARIBA: {"Incluido" if incluir_sin_proveedor else "Excluido"}
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPIs
# ============================================================

col_k1, col_k2, col_k3, col_k4 = st.columns(4)

with col_k1:
    mostrar_kpi_ejecutivo(
        "Registros evaluables",
        formatear_entero(kpis["evaluables"]),
        f"{formatear_entero(kpis['cumple'])} cumplen · {formatear_entero(kpis['no_cumple'])} no cumplen.",
    )

with col_k2:
    mostrar_kpi_ejecutivo(
        "Cumplimiento proveedor",
        formatear_porcentaje(kpis["pct_cumple"]),
        f"Meta referencial: {META_CUMPLIMIENTO}%.",
    )

with col_k3:
    mostrar_kpi_ejecutivo(
        "No cumplimiento proveedor",
        formatear_porcentaje(kpis["pct_no_cumple"]),
        "Complemento sobre registros evaluables.",
    )

with col_k4:
    mostrar_kpi_ejecutivo(
        "Proveedores únicos",
        formatear_entero(kpis["proveedores_unicos"]),
        f"Proveedor identificado en {formatear_porcentaje(kpis['pct_proveedor_identificado'])} de la vista.",
    )


# ============================================================
# Visual 1: Resumen global proveedor
# ============================================================

st.markdown(
    "<div class='exec-section-title'>Resumen global proveedor</div>",
    unsafe_allow_html=True,
)

col_g1, col_g2 = st.columns([1, 2])

with col_g1:
    grafico_donut_global(
        cumple=kpis["cumple"],
        no_cumple=kpis["no_cumple"],
    )

with col_g2:
    tabla_centros = crear_desglose_cumplimiento_centros(df_dashboard)

    st.dataframe(
        tabla_centros,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Centro": st.column_config.TextColumn(
                "Centro",
                width="medium",
            ),
            "Cumple": st.column_config.NumberColumn(
                "Cumple",
                format="%d",
            ),
            "No cumple": st.column_config.NumberColumn(
                "No cumple",
                format="%d",
            ),
            "Evaluables": st.column_config.NumberColumn(
                "Evaluables",
                format="%d",
            ),
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


# ============================================================
# Visual 2: Tendencia mensual proveedor
# ============================================================

mostrar_evolucion_por_anio_proveedor(tabla_mensual)


# ============================================================
# Visual 3: Respuestas ejecutivas de proveedores
# ============================================================

st.markdown(
    "<div class='exec-section-title'>Análisis ejecutivo de proveedores</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Desde aquí la vista responde tres preguntas: quién concentra más registros, "
    "quién combina volumen con peor performance y por qué volumen alto no siempre significa criticidad alta."
)

col_cfg_1, col_cfg_2 = st.columns([1, 1])

with col_cfg_1:
    min_evaluables_riesgo = st.number_input(
        "Mínimo registros para ranking de riesgo",
        min_value=2,
        max_value=1000,
        value=2,
        step=1,
        key="vista_proveedores_min_evaluables_riesgo",
        help="Evita que proveedores con muy pocos registros aparezcan como críticos solo por tener un porcentaje alto.",
    )

with col_cfg_2:
    etiquetas_matriz_riesgo = st.number_input(
        "Etiquetas en matriz de riesgo",
        min_value=3,
        max_value=20,
        value=8,
        step=1,
        key="vista_proveedores_etiquetas_matriz_riesgo",
        help="Cantidad de proveedores con mayor score que se rotulan en la matriz.",
    )

tabla_top_volumen = preparar_ranking_volumen_proveedores(
    tabla=tabla_proveedores,
    top_n=int(top_n),
)

tabla_top_riesgo = preparar_ranking_riesgo_proveedores(
    tabla=tabla_proveedores,
    top_n=int(top_n),
    min_evaluables=int(min_evaluables_riesgo),
)

tabla_matriz_riesgo = crear_matriz_riesgo_proveedores(tabla_proveedores)

col_resp_1, col_resp_2, col_resp_3 = st.columns(3)

with col_resp_1:
    proveedor_mayor_volumen = (
        str(tabla_top_volumen.iloc[0]["proveedor_grafico"])
        if not tabla_top_volumen.empty
        else "—"
    )
    evaluables_mayor_volumen = (
        tabla_top_volumen.iloc[0]["Evaluables"]
        if not tabla_top_volumen.empty
        else 0
    )
    mostrar_kpi_ejecutivo(
        "Mayor cantidad de registros",
        proveedor_mayor_volumen[:34],
        f"{formatear_entero(evaluables_mayor_volumen)} registros evaluables.",
    )

with col_resp_2:
    proveedor_mayor_riesgo = (
        str(tabla_top_riesgo.iloc[0]["proveedor_grafico"])
        if not tabla_top_riesgo.empty
        else "—"
    )
    score_mayor_riesgo = (
        tabla_top_riesgo.iloc[0]["Score riesgo"]
        if not tabla_top_riesgo.empty
        else 0
    )
    mostrar_kpi_ejecutivo(
        "Mayor criticidad combinada",
        proveedor_mayor_riesgo[:34],
        f"Score riesgo: {score_mayor_riesgo:.1f}.",
    )

with col_resp_3:
    total_proveedores_evaluables = int(
        pd.to_numeric(tabla_proveedores["Evaluables"], errors="coerce")
        .fillna(0)
        .gt(0)
        .sum()
        if not tabla_proveedores.empty and "Evaluables" in tabla_proveedores.columns
        else 0
    )
    mostrar_kpi_ejecutivo(
        "Proveedores evaluables",
        formatear_entero(total_proveedores_evaluables),
        "La criticidad cruza volumen y % de incumplimiento.",
    )

st.markdown(
    "<div class='exec-section-title'>1. ¿Cuáles son los proveedores con mayor cantidad de registros?</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Ranking por volumen: muestra dónde está concentrada la operación. "
    "La barra separa Cumple y No cumple para no perder contexto de performance."
)

grafico_ranking_volumen_proveedores(
    data=tabla_top_volumen,
    top_n=int(top_n),
)

with st.expander("Tabla respuesta 1 · Proveedores con mayor cantidad de registros", expanded=False):
    if tabla_top_volumen.empty:
        st.info("No hay proveedores con registros evaluables.")
    else:
        st.dataframe(
            tabla_top_volumen,
            use_container_width=True,
            hide_index=True,
            height=360,
            column_config={
                "proveedor_grafico": st.column_config.TextColumn("Proveedor", width="large"),
                "Evaluables": st.column_config.NumberColumn("Evaluables", format="%d"),
                "Cumple": st.column_config.NumberColumn("Cumple", format="%d"),
                "No cumple": st.column_config.NumberColumn("No cumple", format="%d"),
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
                "Promedio días proveedor": st.column_config.NumberColumn(
                    "Promedio días proveedor",
                    format="%.1f",
                ),
            },
        )

st.markdown(
    "<div class='exec-section-title'>2. ¿Cuáles tienen más registros y menor performance?</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Ranking de riesgo: combina volumen e incumplimiento. "
    "Score riesgo = registros evaluables × % No cumple. Así suben los proveedores que impactan más casos reales."
)

grafico_ranking_riesgo_proveedores(
    data=tabla_top_riesgo,
    top_n=int(top_n),
)

if not tabla_top_riesgo.empty:
    excel_criticos = convertir_a_excel_criticos(
        tabla_prioridad=tabla_top_riesgo.rename(columns={"Score riesgo": "Score prioridad"}),
        df_dashboard=df_dashboard,
    )

    st.download_button(
        label="Descargar Excel detalle proveedores con mayor riesgo",
        data=excel_criticos,
        file_name="16_VISTA_PROVEEDORES_detalle_mayor_riesgo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary",
    )

with st.expander("Tabla respuesta 2 · Proveedores con mayor volumen y menor performance", expanded=False):
    if tabla_top_riesgo.empty:
        st.info("No hay proveedores con los criterios actuales.")
    else:
        st.dataframe(
            tabla_top_riesgo,
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={
                "proveedor_grafico": st.column_config.TextColumn("Proveedor", width="large"),
                "Nivel prioridad": st.column_config.TextColumn("Nivel prioridad"),
                "Evaluables": st.column_config.NumberColumn("Evaluables", format="%d"),
                "Cumple": st.column_config.NumberColumn("Cumple", format="%d"),
                "No cumple": st.column_config.NumberColumn("No cumple", format="%d"),
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
                "Score riesgo": st.column_config.NumberColumn(
                    "Score riesgo",
                    format="%.1f",
                    help="Evaluables × % No cumple.",
                ),
                "Lectura ejecutiva": st.column_config.TextColumn(
                    "Lectura ejecutiva",
                    width="large",
                ),
            },
        )

st.markdown(
    "<div class='exec-section-title'>3. ¿Por qué volumen alto no siempre significa proveedor crítico?</div>",
    unsafe_allow_html=True,
)

st.info(
    "Un proveedor con muchos registros puede tener buen cumplimiento y, por lo tanto, bajo riesgo relativo. "
    "En cambio, un proveedor con menos volumen puede ser crítico si concentra un alto porcentaje de incumplimiento. "
    "Por eso esta vista separa volumen operativo, performance y score de riesgo."
)

grafico_matriz_riesgo_proveedores(
    data=tabla_matriz_riesgo,
    top_n_labels=int(etiquetas_matriz_riesgo),
)

with st.expander("Tabla respuesta 3 · Matriz de criticidad por cuadrante", expanded=False):
    if tabla_matriz_riesgo.empty:
        st.info("No hay datos para matriz de criticidad.")
    else:
        columnas_matriz = [
            "proveedor_grafico",
            "Cuadrante",
            "Cumple",
            "No cumple",
            "Evaluables",
            "% Cumple",
            "% No cumple",
            "Score riesgo",
        ]
        columnas_matriz = [c for c in columnas_matriz if c in tabla_matriz_riesgo.columns]

        st.dataframe(
            tabla_matriz_riesgo[columnas_matriz],
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={
                "proveedor_grafico": st.column_config.TextColumn("Proveedor", width="large"),
                "Cuadrante": st.column_config.TextColumn("Cuadrante", width="medium"),
                "Evaluables": st.column_config.NumberColumn("Evaluables", format="%d"),
                "Cumple": st.column_config.NumberColumn("Cumple", format="%d"),
                "No cumple": st.column_config.NumberColumn("No cumple", format="%d"),
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
                "Score riesgo": st.column_config.NumberColumn("Score riesgo", format="%.1f"),
            },
        )


# ============================================================
# Visual 5: Tabla ejecutiva de proveedores
# ============================================================

st.markdown(
    "<div class='exec-section-title'>Tabla ejecutiva de proveedores</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Tabla principal de la vista. Ordenada por cantidad de registros evaluables y porcentaje de no cumplimiento."
)

tabla_ejecutiva_display = preparar_tabla_ejecutiva_display(tabla_proveedores)

with st.form("form_filtros_tabla_ejecutiva_proveedores"):
    col_busq_1, col_busq_2 = st.columns([1, 1.4])

    with col_busq_1:
        texto_busqueda_proveedor = st.text_input(
            "Buscar proveedor en tabla",
            value="",
            placeholder="Escribe parte del nombre del proveedor",
            key="vista_proveedores_buscar_tabla",
        )

    with col_busq_2:
        proveedores_tabla_sel = st.multiselect(
            "Filtrar proveedor en tabla",
            options=tabla_ejecutiva_display["proveedor_grafico"].astype(str).tolist(),
            default=[],
            key="vista_proveedores_filtrar_tabla",
            help="Filtro específico solo para la tabla ejecutiva. No cambia los gráficos superiores.",
        )

    st.form_submit_button(
        "Filtrar tabla ejecutiva",
        use_container_width=True,
        type="primary",
    )

tabla_ejecutiva_filtrada = filtrar_tabla_ejecutiva_proveedores(
    tabla=tabla_ejecutiva_display,
    texto_busqueda=texto_busqueda_proveedor,
    proveedores_sel=proveedores_tabla_sel,
)

st.caption(
    f"Mostrando {formatear_entero(len(tabla_ejecutiva_filtrada))} de "
    f"{formatear_entero(len(tabla_ejecutiva_display))} proveedores en la tabla."
)

st.dataframe(
    tabla_ejecutiva_filtrada,
    use_container_width=True,
    hide_index=True,
    height=620,
    column_config={
        "proveedor_grafico": st.column_config.TextColumn(
            "Proveedor",
            width="large",
        ),
        "Cumple": st.column_config.NumberColumn(
            "Cumple",
            format="%d",
        ),
        "No cumple": st.column_config.NumberColumn(
            "No cumple",
            format="%d",
        ),
        "Evaluables": st.column_config.NumberColumn(
            "Evaluables",
            format="%d",
        ),
        "Umbral proveedor": st.column_config.TextColumn(
            "Umbral proveedor",
            help="Umbral o umbrales detectados para el proveedor según la base filtrada.",
        ),
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
        "Promedio días proveedor": st.column_config.NumberColumn(
            "Promedio días proveedor",
            format="%.1f",
        ),
    },
)

excel_resumen_principal = convertir_a_excel_cache(tabla_ejecutiva_filtrada)

st.download_button(
    label="Descargar resumen proveedores filtrado",
    data=excel_resumen_principal,
    file_name="16_VISTA_PROVEEDORES_VERSION_5_resumen_proveedores_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
    type="primary",
)


# ============================================================
# Tablas secundarias
# ============================================================


with st.expander("Tabla mensual proveedor", expanded=False):
    if tabla_mensual.empty:
        st.info("No hay tabla mensual disponible.")
    else:
        columnas = [
            "periodo_label",
            "Cumple",
            "No cumple",
            "Evaluables",
            "% Cumple",
            "% No cumple",
        ]

        columnas = [c for c in columnas if c in tabla_mensual.columns]

        st.dataframe(
            tabla_mensual[columnas],
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


with st.expander("Vista previa de registros evaluables filtrados", expanded=False):
    limite_vista = st.number_input(
        "Filas a mostrar",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
        key="vista_proveedores_limite_vista",
    )

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        "centro_grafico",
        "centro_grupo",
        COL_PROVEEDOR,
        "proveedor_grafico",
        COL_FECHA_PROVEEDOR,
        "fecha_proveedor_grafico",
        COL_DIAS_PROVEEDOR,
        COL_UMBRAL_PROVEEDOR,
        COL_PERFORMANCE_PROVEEDOR,
        "performance_proveedor_norm",
        "origen",
        "sistema",
        "tipo_oc",
        "monto",
    ]

    columnas_preferidas = [
        col for col in columnas_preferidas
        if col in df_dashboard.columns
    ]

    if columnas_preferidas:
        st.dataframe(
            df_dashboard[columnas_preferidas].head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(
            df_dashboard.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Descargas
# ============================================================

with st.expander("Descargar base proveedores filtrada", expanded=False):
    firma_export = (
        f"{len(df_dashboard)}_"
        f"{fecha_inicio}_"
        f"{fecha_fin}_"
        f"{','.join(centros_sel)}_"
        f"{','.join(proveedores_sel)}_"
        f"{','.join(perf_sel)}_"
        f"{incluir_sin_proveedor}"
    )

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        preparar_excel = st.button(
            "Preparar Excel registros",
            use_container_width=True,
            key="vista_proveedores_preparar_excel",
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                st.session_state["vista_proveedores_excel_bytes"] = convertir_a_excel_cache(df_dashboard)
                st.session_state["vista_proveedores_excel_firma"] = firma_export

        if (
            st.session_state.get("vista_proveedores_excel_bytes") is not None
            and st.session_state.get("vista_proveedores_excel_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Excel registros",
                data=st.session_state["vista_proveedores_excel_bytes"],
                file_name="16_VISTA_PROVEEDORES_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV registros",
            use_container_width=True,
            key="vista_proveedores_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["vista_proveedores_csv_bytes"] = convertir_a_csv_cache(df_dashboard)
                st.session_state["vista_proveedores_csv_firma"] = firma_export

        if (
            st.session_state.get("vista_proveedores_csv_bytes") is not None
            and st.session_state.get("vista_proveedores_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV registros",
                data=st.session_state["vista_proveedores_csv_bytes"],
                file_name="16_VISTA_PROVEEDORES_filtrado.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col_d3:
        excel_resumen = convertir_a_excel_cache(tabla_ejecutiva_display)

        st.download_button(
            label="Descargar resumen proveedores",
            data=excel_resumen,
            file_name="16_VISTA_PROVEEDORES_VERSION_5_resumen.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
