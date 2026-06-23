
# ============================================================
# 13_VISTA_EJECUTIVA_PERFORMANCE_PLANTAS
# Vista ejecutiva de Performance TAT por plantas
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Enfoque:
# - Vista ejecutiva inspirada en 12_VISTA_EJECUTIVA
# - Detalle por plantas: Prillex, Rio Loa y Plantas de servicios
# - Prillex = E002
# - Rio Loa = E024
# - Plantas de servicios = centros distintos de E001, E002, E009, E024 y E021
# - Base de análisis: registros evaluables Cumple + No cumple
# - Evolución mensual separada por año
# - Años anteriores colapsados
# - Último año visible por defecto
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

COLOR_PRILLEX = "#E83E51"
COLOR_RIO_LOA = "#0057B8"
COLOR_SERVICIOS = "#F59E0B"

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

ORDEN_PLANTAS = {
    "Prillex": 1,
    "Rio Loa": 2,
    "Planta de servicios": 3,
}

COLORES_PLANTAS = {
    "Prillex": COLOR_PRILLEX,
    "Rio Loa": COLOR_RIO_LOA,
    "Planta de servicios": COLOR_SERVICIOS,
}

CENTROS_EXCLUIR_PLANTA_SERVICIOS = [
    "E001",
    "E002",
    "E009",
    "E024",
    "E021",
]

COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - ME80FN"
COL_PERFORMANCE_TAT = "performance_tat_total"

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

    return f"{int(round(numero)):,}".replace(",", ".")


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


def obtener_grupo_planta(centro) -> str:
    centro = str(centro).strip()

    if centro == "E002":
        return "Prillex"

    if centro == "E024":
        return "Rio Loa"

    if centro in CENTROS_EXCLUIR_PLANTA_SERVICIOS:
        return "Excluir"

    return "Planta de servicios"


def ordenar_plantas(df: pd.DataFrame, col: str = "grupo_planta") -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return df

    salida = df.copy()
    salida["_orden_planta"] = salida[col].map(ORDEN_PLANTAS).fillna(99)
    salida = salida.sort_values("_orden_planta").drop(columns="_orden_planta")

    return salida


# ============================================================
# Performance
# ============================================================

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
def preparar_base_plantas(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    df = normalizar_columnas_me80fn(df)

    validar_fechas_finales(df)

    for col in COLUMNAS_FECHA_PERFORMANCE:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])

    col_centro = buscar_columna_centro(df)

    if col_centro is None:
        raise ValueError(
            "No se encontró una columna de centro. Se esperaba Centro - ME5A, Centro, Centro - ME80FN o me80fn_centro."
        )

    df["centro_grafico"] = (
        df[col_centro]
        .astype("string")
        .str.strip()
    )

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

    if COL_PERFORMANCE_TAT not in df.columns:
        df[COL_PERFORMANCE_TAT] = evaluar_performance_tat(df)

    df[COL_PERFORMANCE_TAT] = df[COL_PERFORMANCE_TAT].apply(normalizar_estado_performance)

    df["grupo_planta"] = df["centro_grafico"].apply(obtener_grupo_planta)

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


# ============================================================
# Filtros
# ============================================================

def registrar_paso_filtro(
    resumen: list,
    paso: str,
    filtro: str,
    valor,
    df_antes: pd.DataFrame,
    df_despues: pd.DataFrame,
):
    antes = len(df_antes)
    despues = len(df_despues)

    resumen.append(
        {
            "Paso": paso,
            "Filtro aplicado": filtro,
            "Valor": valor,
            "Registros antes": antes,
            "Registros después": despues,
            "Registros excluidos": antes - despues,
            "% retenido": round(despues / antes * 100, 2) if antes else 0,
            "% excluido": round((antes - despues) / antes * 100, 2) if antes else 0,
        }
    )


def aplicar_filtros_con_progreso(
    df_base: pd.DataFrame,
    fecha_inicio,
    fecha_fin,
    plantas_sel: list,
    perf_sel: list,
    centros_sel: list,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    df_filtrado = df_base.copy()

    resumen = [
        {
            "Paso": "Base inicial",
            "Filtro aplicado": "Sin filtro",
            "Valor": "Base procesada",
            "Registros antes": len(df_base),
            "Registros después": len(df_base),
            "Registros excluidos": 0,
            "% retenido": 100.0,
            "% excluido": 0.0,
        }
    ]

    antes = df_filtrado.copy()

    df_filtrado = df_filtrado[
        df_filtrado["grupo_planta"].ne("Excluir")
    ].copy()

    registrar_paso_filtro(
        resumen,
        "Filtro 1",
        "Excluir centros no analizables",
        "grupo_planta != Excluir",
        antes,
        df_filtrado,
    )

    if fecha_inicio is not None and fecha_fin is not None:
        antes = df_filtrado.copy()

        fecha_inicio_ts = pd.Timestamp(fecha_inicio)
        fecha_fin_ts = pd.Timestamp(fecha_fin) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

        df_filtrado = df_filtrado[
            df_filtrado[COL_FECHA_RECEPCION_FINAL].notna()
            & df_filtrado[COL_FECHA_RECEPCION_FINAL].between(
                fecha_inicio_ts,
                fecha_fin_ts,
            )
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 2",
            "Fecha recepción",
            f"{fecha_inicio} a {fecha_fin}",
            antes,
            df_filtrado,
        )

    if plantas_sel:
        antes = df_filtrado.copy()

        df_filtrado = df_filtrado[
            df_filtrado["grupo_planta"].isin(plantas_sel)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 3",
            "Planta",
            ", ".join(plantas_sel),
            antes,
            df_filtrado,
        )

    if centros_sel:
        antes = df_filtrado.copy()

        df_filtrado = df_filtrado[
            df_filtrado["centro_grafico"].isin(centros_sel)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 4",
            "Centro específico",
            ", ".join(centros_sel),
            antes,
            df_filtrado,
        )

    if perf_sel and COL_PERFORMANCE_TAT in df_filtrado.columns:
        antes = df_filtrado.copy()

        df_filtrado = df_filtrado[
            df_filtrado[COL_PERFORMANCE_TAT].isin(perf_sel)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 5",
            "Performance TAT",
            ", ".join(perf_sel),
            antes,
            df_filtrado,
        )

    return df_filtrado, pd.DataFrame(resumen)


# ============================================================
# Resúmenes
# ============================================================

def crear_resumen_mensual_plantas(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df[
        df["periodo_fecha"].notna()
        & df["grupo_planta"].isin(ORDEN_PLANTAS.keys())
        & df[COL_PERFORMANCE_TAT].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        return pd.DataFrame()

    resumen = (
        base
        .groupby(["periodo_fecha", "periodo_label", "grupo_planta", COL_PERFORMANCE_TAT])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=["periodo_fecha", "periodo_label", "grupo_planta"],
        columns=COL_PERFORMANCE_TAT,
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

    tabla = ordenar_plantas(tabla, "grupo_planta")

    return tabla.sort_values(["periodo_fecha", "grupo_planta"]).reset_index(drop=True)


def obtener_tabla_ultimo_anio(tabla_mensual: pd.DataFrame) -> tuple[pd.DataFrame, int | None]:
    if tabla_mensual.empty or "periodo_fecha" not in tabla_mensual.columns:
        return pd.DataFrame(), None

    temp = tabla_mensual.copy()
    temp["anio_zoom"] = pd.to_datetime(temp["periodo_fecha"], errors="coerce").dt.year
    temp = temp[temp["anio_zoom"].notna()].copy()

    if temp.empty:
        return pd.DataFrame(), None

    ultimo_anio = int(temp["anio_zoom"].max())

    tabla_ultimo_anio = (
        temp[temp["anio_zoom"].eq(ultimo_anio)]
        .drop(columns=["anio_zoom"])
        .sort_values(["periodo_fecha", "grupo_planta"])
        .reset_index(drop=True)
    )

    return tabla_ultimo_anio, ultimo_anio


def calcular_kpis_plantas(
    df_base: pd.DataFrame,
    df_filtrado: pd.DataFrame,
) -> dict:

    total_ingresado = int(len(df_base))
    total_retenido = int(len(df_filtrado))
    total_excluido = total_ingresado - total_retenido

    estado = (
        df_filtrado[COL_PERFORMANCE_TAT].apply(normalizar_estado_performance)
        if COL_PERFORMANCE_TAT in df_filtrado.columns
        else pd.Series([], dtype="object")
    )

    cumple = int(estado.eq("Cumple").sum())
    no_cumple = int(estado.eq("No cumple").sum())
    en_proceso = int(estado.eq("En proceso").sum())
    no_aplica = int(estado.eq("No aplica").sum())
    sin_datos = int(estado.eq("Sin datos").sum())

    evaluables = cumple + no_cumple
    no_evaluables = en_proceso + no_aplica + sin_datos

    pct_retenido = total_retenido / total_ingresado * 100 if total_ingresado else 0
    pct_excluido = total_excluido / total_ingresado * 100 if total_ingresado else 0
    pct_evaluables = evaluables / total_retenido * 100 if total_retenido else 0
    pct_no_evaluables = no_evaluables / total_retenido * 100 if total_retenido else 0
    pct_cumple = cumple / evaluables * 100 if evaluables else 0
    pct_no_cumple = no_cumple / evaluables * 100 if evaluables else 0

    return {
        "total_ingresado": total_ingresado,
        "total_retenido": total_retenido,
        "total_excluido": total_excluido,
        "pct_retenido": pct_retenido,
        "pct_excluido": pct_excluido,
        "evaluables": evaluables,
        "no_evaluables": no_evaluables,
        "pct_evaluables": pct_evaluables,
        "pct_no_evaluables": pct_no_evaluables,
        "cumple": cumple,
        "no_cumple": no_cumple,
        "pct_cumple": pct_cumple,
        "pct_no_cumple": pct_no_cumple,
    }


def calcular_kpis_por_planta(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "grupo_planta",
        "Cumple",
        "No cumple",
        "Evaluables",
        "% Cumple",
        "% No cumple",
        "Promedio días TAT",
    ]

    if df.empty:
        return pd.DataFrame(columns=columnas)

    base = df[
        df["grupo_planta"].isin(ORDEN_PLANTAS.keys())
        & df[COL_PERFORMANCE_TAT].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        return pd.DataFrame(columns=columnas)

    resumen = (
        base
        .groupby(["grupo_planta", COL_PERFORMANCE_TAT])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index="grupo_planta",
        columns=COL_PERFORMANCE_TAT,
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

    dias = (
        base
        .assign(dias_tat_total_num=pd.to_numeric(base["dias_tat_total"], errors="coerce"))
        .query("dias_tat_total_num >= 0")
        .groupby("grupo_planta")["dias_tat_total_num"]
        .mean()
        .reset_index()
        .rename(columns={"dias_tat_total_num": "Promedio días TAT"})
    )

    tabla = tabla.merge(dias, on="grupo_planta", how="left")
    tabla["Promedio días TAT"] = tabla["Promedio días TAT"].fillna(0)

    tabla = ordenar_plantas(tabla, "grupo_planta")

    return tabla[columnas].reset_index(drop=True)


def crear_texto_filtros(
    plantas_sel: list,
    fecha_inicio,
    fecha_fin,
    perf_sel: list,
    centros_sel: list,
) -> str:

    plantas_txt = ", ".join([str(x) for x in plantas_sel]) if plantas_sel else "Todas"
    perf_txt = ", ".join([str(x) for x in perf_sel]) if perf_sel else "Todas"
    centros_txt = ", ".join([str(x) for x in centros_sel]) if centros_sel else "Todos"
    fechas_txt = f"{fecha_inicio} a {fecha_fin}" if fecha_inicio and fecha_fin else "Todas"

    return (
        f"Planta: {plantas_txt} · "
        f"Centro: {centros_txt} · "
        f"Fechas: {fechas_txt} · "
        f"Performance: {perf_txt}"
    )


# ============================================================
# Visuales ejecutivos
# ============================================================

def titulo_vista_ejecutiva(nombre_archivo: str):
    st.markdown(
        f"""
        <div class="exec-header">
            <div>
                <div class="exec-title">13_VISTA_EJECUTIVA · Performance TAT Plantas</div>
                <div class="exec-subtitle">
                    Vista ejecutiva por planta: Prillex, Rio Loa y Planta de servicios.
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


def etiqueta_mes_corta(fecha) -> str:
    if pd.isna(fecha):
        return "—"

    fecha = pd.Timestamp(fecha)
    return MESES_NOMBRE.get(int(fecha.month), str(fecha.month))


def grafico_barras_apiladas_plantas(
    tabla: pd.DataFrame,
    titulo: str,
):
    if tabla.empty:
        st.info("No hay datos mensuales evaluables para graficar.")
        return

    data = tabla.copy()
    data["periodo_fecha"] = pd.to_datetime(data["periodo_fecha"], errors="coerce")
    data = data[data["periodo_fecha"].notna()].copy()
    data = data[data["Evaluables"].gt(0)].copy()

    if data.empty:
        st.info("No hay meses con registros evaluables para graficar.")
        return

    meses = (
        data[["periodo_fecha", "periodo_label"]]
        .drop_duplicates()
        .sort_values("periodo_fecha")
        .reset_index(drop=True)
    )

    plantas = [
        planta for planta in ORDEN_PLANTAS.keys()
        if planta in data["grupo_planta"].unique()
    ]

    if not plantas:
        st.info("No hay plantas disponibles para graficar.")
        return

    x_base = np.arange(len(meses))
    ancho = 0.22 if len(plantas) >= 3 else 0.30

    fig_width = max(10, len(meses) * 1.05)
    fig, ax = plt.subplots(figsize=(fig_width, 4.8), dpi=180)

    offsets = np.linspace(
        -ancho * (len(plantas) - 1),
        ancho * (len(plantas) - 1),
        len(plantas),
    )

    for offset, planta in zip(offsets, plantas):
        base_planta = (
            data[data["grupo_planta"].eq(planta)]
            .set_index("periodo_fecha")
            .reindex(meses["periodo_fecha"])
            .reset_index()
        )

        cumple_pct = pd.to_numeric(base_planta["% Cumple"], errors="coerce").fillna(0).to_numpy()
        no_cumple_pct = pd.to_numeric(base_planta["% No cumple"], errors="coerce").fillna(0).to_numpy()
        evaluables = pd.to_numeric(base_planta["Evaluables"], errors="coerce").fillna(0).astype(int).to_numpy()

        x = x_base + offset

        color_base = COLORES_PLANTAS.get(planta, COLOR_CUMPLE)

        ax.bar(
            x,
            cumple_pct,
            width=ancho,
            color=color_base,
            label=f"{planta} · Cumple",
            edgecolor="white",
            linewidth=0.7,
        )

        ax.bar(
            x,
            no_cumple_pct,
            bottom=cumple_pct,
            width=ancho,
            color=COLOR_NO_CUMPLE,
            label=f"{planta} · No cumple" if planta == plantas[0] else None,
            edgecolor="white",
            linewidth=0.7,
            alpha=0.85,
        )

        for i, (c_pct, total) in enumerate(zip(cumple_pct, evaluables)):
            if total <= 0:
                continue

            if c_pct >= 15:
                ax.text(
                    x[i],
                    c_pct / 2,
                    f"{c_pct:.0f}%",
                    ha="center",
                    va="center",
                    fontsize=6.5,
                    color="white",
                    fontweight="bold",
                )

    ax.axhline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle=(0, (2, 2)),
        linewidth=1.8,
        alpha=0.95,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    labels = [etiqueta_mes_corta(v) for v in meses["periodo_fecha"]]

    ax.set_ylim(0, 105)
    ax.set_yticks([0, 50, 100])
    ax.set_yticklabels(["0%", "50%", "100%"], fontsize=8, color=COLOR_MUTED)

    ax.set_xticks(x_base)
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

    handles, labels_legend = ax.get_legend_handles_labels()
    pares = [
        (h, l) for h, l in zip(handles, labels_legend)
        if l and not l.startswith("_")
    ]

    if pares:
        handles, labels_legend = zip(*pares)

        ax.legend(
            handles,
            labels_legend,
            loc="upper center",
            bbox_to_anchor=(0.5, -0.17),
            ncol=min(4, len(labels_legend)),
            frameon=False,
            fontsize=8,
        )

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.23)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def mostrar_evolucion_por_anio_plantas(tabla_mensual: pd.DataFrame):
    st.markdown(
        "<div class='exec-section-title'>Evolución mensual ejecutiva por planta</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='exec-small'>
            Barras 100% apiladas por planta. Los años anteriores quedan colapsados
            y el último año disponible queda visible por defecto.
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
            .sort_values(["periodo_fecha", "grupo_planta"])
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
            resumen_planta = calcular_kpis_por_planta(
                data_anio.rename(columns={"Evaluables": "_Evaluables_temp"})
            )

            # En este punto data_anio ya es mensual agregado. Para KPI visual anual se calcula directo.
            kpi_anual_planta = (
                data_anio
                .groupby("grupo_planta", as_index=False)
                .agg(
                    Cumple=("Cumple", "sum"),
                    **{"No cumple": ("No cumple", "sum")},
                    Evaluables=("Evaluables", "sum"),
                )
            )

            kpi_anual_planta["% Cumple"] = np.where(
                kpi_anual_planta["Evaluables"] > 0,
                kpi_anual_planta["Cumple"] / kpi_anual_planta["Evaluables"] * 100,
                0,
            )

            kpi_anual_planta = ordenar_plantas(kpi_anual_planta, "grupo_planta")

            cols = st.columns(3)

            for col, (_, fila) in zip(cols, kpi_anual_planta.iterrows()):
                with col:
                    mostrar_kpi_ejecutivo(
                        str(fila["grupo_planta"]),
                        formatear_porcentaje(fila["% Cumple"]),
                        (
                            f"Evaluables: {formatear_entero(fila['Evaluables'])} · "
                            f"Cumple: {formatear_entero(fila['Cumple'])} · "
                            f"No cumple: {formatear_entero(fila['No cumple'])}"
                        ),
                    )

            grafico_barras_apiladas_plantas(
                data_anio,
                titulo=f"Performance TAT plantas {anio}",
            )

            with st.expander(f"Tabla mensual plantas {anio}", expanded=False):
                columnas = [
                    "periodo_label",
                    "grupo_planta",
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


def grafico_donut_planta(planta: str, datos: pd.Series):
    cumple = int(datos.get("Cumple", 0))
    no_cumple = int(datos.get("No cumple", 0))
    evaluables = cumple + no_cumple

    st.markdown(f"##### {planta}")

    if evaluables <= 0:
        st.info("Sin evaluables")
        return

    pct_cumple = cumple / evaluables * 100
    pct_no_cumple = no_cumple / evaluables * 100

    fig, ax = plt.subplots(figsize=(3.05, 2.4), dpi=180)

    ax.pie(
        [cumple, no_cumple],
        startangle=90,
        counterclock=False,
        colors=[
            COLORES_PLANTAS.get(planta, COLOR_CUMPLE),
            COLOR_NO_CUMPLE,
        ],
        labels=None,
        wedgeprops={
            "width": 0.42,
            "edgecolor": "white",
            "linewidth": 1.4,
        },
    )

    ax.text(
        0,
        0.06,
        f"{pct_cumple:.0f}%",
        ha="center",
        va="center",
        fontsize=18,
        fontweight="bold",
        color=COLOR_TEXTO,
    )

    ax.text(
        0,
        -0.14,
        "Cumple",
        ha="center",
        va="center",
        fontsize=8,
        color=COLOR_MUTED,
    )

    ax.text(
        1.05,
        -0.58,
        f"Cumple\n{pct_cumple:.0f}%",
        ha="left",
        va="center",
        fontsize=7.2,
        color=COLOR_TEXTO,
    )

    ax.text(
        -1.05,
        0.82,
        f"No cumple\n{pct_no_cumple:.0f}%",
        ha="right",
        va="center",
        fontsize=7.2,
        color=COLOR_TEXTO,
    )

    ax.axis("equal")
    fig.patch.set_alpha(0)
    fig.tight_layout(pad=0.2)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)

    promedio = datos.get("Promedio días TAT", 0)

    st.markdown(f"### {promedio:.1f}")
    st.caption("Promedio días TAT")


def mostrar_cumplimiento_plantas(df_dashboard: pd.DataFrame):
    st.markdown(
        "<div class='exec-section-title'>Cumplimiento ejecutivo por planta</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='exec-small'>
            Base: registros evaluables filtrados. Cada planta muestra cumplimiento, no cumplimiento
            y promedio de días TAT.
        </div>
        """,
        unsafe_allow_html=True,
    )

    resumen = calcular_kpis_por_planta(df_dashboard)

    if resumen.empty:
        st.info("No hay datos evaluables por planta.")
        return

    cols = st.columns(3)

    for col, (_, fila) in zip(cols, resumen.iterrows()):
        with col:
            grafico_donut_planta(str(fila["grupo_planta"]), fila)

    with st.expander("Tabla ejecutiva por planta", expanded=False):
        st.dataframe(
            resumen,
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
                "Promedio días TAT": st.column_config.NumberColumn(
                    "Promedio días TAT",
                    format="%.1f",
                ),
            },
        )


def obtener_periodos_disponibles_detalle(tabla_mensual: pd.DataFrame) -> pd.DataFrame:
    if tabla_mensual.empty or "periodo_fecha" not in tabla_mensual.columns:
        return pd.DataFrame()

    periodos = tabla_mensual.copy()
    periodos["periodo_fecha"] = pd.to_datetime(periodos["periodo_fecha"], errors="coerce")
    periodos = periodos[periodos["periodo_fecha"].notna()].copy()
    periodos = periodos[periodos["Evaluables"].gt(0)].copy()

    if periodos.empty:
        return pd.DataFrame()

    periodos = (
        periodos[["periodo_fecha", "periodo_label"]]
        .drop_duplicates()
        .sort_values("periodo_fecha", ascending=False)
        .reset_index(drop=True)
    )

    return periodos


def mostrar_detalle_mes_ejecutivo(
    df_dashboard: pd.DataFrame,
    tabla_mensual: pd.DataFrame,
):
    st.markdown(
        "<div class='exec-section-title'>Detalle mensual por planta</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='exec-small'>
            Por defecto se muestra el último mes disponible. Puedes cambiar el mes para revisar
            el detalle de registros por planta.
        </div>
        """,
        unsafe_allow_html=True,
    )

    periodos = obtener_periodos_disponibles_detalle(tabla_mensual)

    if periodos.empty:
        st.info("No hay meses evaluables disponibles para mostrar detalle.")
        return

    opciones = periodos["periodo_label"].astype(str).tolist()

    mes_sel = st.selectbox(
        "Mes a revisar",
        options=opciones,
        index=0,
        key="ejecutiva_plantas_mes_detalle",
    )

    fila_mes = periodos[periodos["periodo_label"].astype(str).eq(mes_sel)].iloc[0]
    periodo_sel = pd.Timestamp(fila_mes["periodo_fecha"])

    df_mes = df_dashboard[
        df_dashboard["periodo_fecha"].eq(periodo_sel)
    ].copy()

    if df_mes.empty:
        st.info("No hay registros para el mes seleccionado.")
        return

    resumen_mes = calcular_kpis_por_planta(df_mes)

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    estado_mes = df_mes[COL_PERFORMANCE_TAT].apply(normalizar_estado_performance)

    cumple_mes = int(estado_mes.eq("Cumple").sum())
    no_cumple_mes = int(estado_mes.eq("No cumple").sum())
    evaluables_mes = cumple_mes + no_cumple_mes
    pct_cumple_mes = cumple_mes / evaluables_mes * 100 if evaluables_mes else 0

    with col_m1:
        mostrar_kpi_ejecutivo(
            "Mes seleccionado",
            mes_sel,
            "Detalle de plantas del mes.",
        )

    with col_m2:
        mostrar_kpi_ejecutivo(
            "Evaluables mes",
            formatear_entero(evaluables_mes),
            f"{formatear_entero(cumple_mes)} cumplen · {formatear_entero(no_cumple_mes)} no cumplen.",
        )

    with col_m3:
        mostrar_kpi_ejecutivo(
            "Cumplimiento mes",
            formatear_porcentaje(pct_cumple_mes),
            f"Meta ejecutiva: {META_CUMPLIMIENTO}%.",
        )

    with col_m4:
        mostrar_kpi_ejecutivo(
            "Plantas",
            formatear_entero(resumen_mes.shape[0]),
            "Plantas con registros evaluables.",
        )

    if not resumen_mes.empty:
        st.dataframe(
            resumen_mes,
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

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        "centro_grafico",
        "grupo_planta",
        "tipo_oc",
        "origen",
        "sistema",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "dias_tat_total",
        "umbral_tat_total",
        COL_PERFORMANCE_TAT,
        "dias_incumplimiento_tat",
        "rango_incumplimiento_tat",
    ]

    columnas_preferidas = [
        col for col in columnas_preferidas
        if col is not None and col in df_mes.columns
    ]

    with st.expander("Registros del mes seleccionado", expanded=False):
        st.dataframe(
            df_mes[columnas_preferidas] if columnas_preferidas else df_mes,
            use_container_width=True,
            hide_index=True,
        )

    col_desc1, col_desc2 = st.columns(2)

    periodo_archivo = periodo_sel.strftime("%Y_%m")

    with col_desc1:
        excel_mes = convertir_a_excel_cache(df_mes)

        st.download_button(
            label="Descargar mes seleccionado",
            data=excel_mes,
            file_name=f"13_VISTA_EJECUTIVA_PLANTAS_{periodo_archivo}_DETALLE.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )

    with col_desc2:
        excel_resumen_mes = convertir_a_excel_cache(resumen_mes)

        st.download_button(
            label="Descargar resumen plantas del mes",
            data=excel_resumen_mes,
            file_name=f"13_VISTA_EJECUTIVA_PLANTAS_{periodo_archivo}_RESUMEN.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
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
    with st.spinner("Preparando base TAT por plantas..."):
        df_final = preparar_base_plantas(df_original)

except Exception as e:
    st.error("No se pudo preparar la base para la vista ejecutiva de plantas.")
    st.exception(e)
    st.stop()


# ============================================================
# Preparación de filtros
# ============================================================

df_analizable = df_final[df_final["grupo_planta"].ne("Excluir")].copy()

if df_analizable.empty:
    st.warning("No hay registros analizables para Prillex, Rio Loa o Planta de servicios.")
    st.stop()

fechas_validas = df_analizable[COL_FECHA_RECEPCION_FINAL].dropna()

fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

plantas = [
    planta for planta in ORDEN_PLANTAS.keys()
    if planta in df_analizable["grupo_planta"].dropna().astype(str).unique()
]

if not plantas:
    plantas = list(ORDEN_PLANTAS.keys())

centros = sorted(
    df_analizable["centro_grafico"]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
    .tolist()
)

perf_options = ["Cumple", "No cumple"]

perf_existentes = (
    [
        x for x in perf_options
        if x in df_analizable[COL_PERFORMANCE_TAT].astype(str).unique()
    ]
    if COL_PERFORMANCE_TAT in df_analizable.columns
    else perf_options
)

perf_default = perf_existentes if perf_existentes else perf_options


# ============================================================
# Filtros visuales
# ============================================================

st.markdown(
    "<div class='exec-section-title'>Filtros ejecutivos</div>",
    unsafe_allow_html=True,
)

st.caption(
    "La vista se enfoca en Prillex, Rio Loa y Planta de servicios. "
    "Por diseño ejecutivo, el análisis principal usa registros evaluables: Cumple + No cumple."
)

with st.form("form_filtros_vista_ejecutiva_plantas"):
    col_f1, col_f2, col_f3, col_f4 = st.columns([1.2, 1, 1, 1])

    with col_f1:
        if fecha_min is not None and fecha_max is not None:
            rango_fechas = st.date_input(
                "Fecha recepción",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                key="ejecutiva_plantas_rango_fechas",
            )
        else:
            rango_fechas = None
            st.warning("No hay fechas válidas de recepción.")

    with col_f2:
        plantas_sel = st.multiselect(
            "Planta",
            options=plantas,
            default=plantas,
            key="ejecutiva_plantas_grupos",
        )

    with col_f3:
        centros_sel = st.multiselect(
            "Centro específico",
            options=centros,
            default=[],
            key="ejecutiva_plantas_centros",
            help="Opcional. Si no seleccionas centros, se consideran todos los centros de las plantas seleccionadas.",
        )

    with col_f4:
        perf_sel = st.multiselect(
            "Performance TAT",
            options=perf_options,
            default=perf_default,
            key="ejecutiva_plantas_performance",
            help="Por diseño ejecutivo, esta vista se calcula sobre registros evaluables.",
        )

    st.form_submit_button(
        "Actualizar vista ejecutiva",
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

df_dashboard, resumen_filtros_df = aplicar_filtros_con_progreso(
    df_base=df_final,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    plantas_sel=plantas_sel,
    perf_sel=perf_sel,
    centros_sel=centros_sel,
)

if df_dashboard.empty:
    st.warning("No hay registros con los filtros seleccionados.")
    st.stop()

estado_dashboard = df_dashboard[COL_PERFORMANCE_TAT].apply(normalizar_estado_performance)

df_dashboard = df_dashboard[
    estado_dashboard.isin(["Cumple", "No cumple"])
].copy()

if df_dashboard.empty:
    st.warning("No hay registros evaluables con los filtros seleccionados.")
    st.stop()

st.markdown(
    f"""
    <div class='exec-small'>
        {crear_texto_filtros(plantas_sel, fecha_inicio, fecha_fin, perf_sel, centros_sel)}
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPIs
# ============================================================

tabla_mensual = crear_resumen_mensual_plantas(df_dashboard)
tabla_ultimo_anio, ultimo_anio = obtener_tabla_ultimo_anio(tabla_mensual)

kpis = calcular_kpis_plantas(df_final, df_dashboard)
kpis_plantas = calcular_kpis_por_planta(df_dashboard)

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
        "Último año disponible",
        str(ultimo_anio) if ultimo_anio is not None else "—",
        f"Plantas activas: {formatear_entero(kpis_plantas.shape[0])}.",
    )


# ============================================================
# Visual 1: Cumplimiento por planta
# ============================================================

mostrar_cumplimiento_plantas(df_dashboard)


# ============================================================
# Visual 2: Evolución mensual por año
# ============================================================

mostrar_evolucion_por_anio_plantas(tabla_mensual)


# ============================================================
# Detalle mensual
# ============================================================

mostrar_detalle_mes_ejecutivo(
    df_dashboard=df_dashboard,
    tabla_mensual=tabla_mensual,
)


# ============================================================
# Detalle mensual consolidado
# ============================================================

with st.expander("Detalle mensual consolidado por planta", expanded=False):
    if tabla_mensual.empty:
        st.info("No hay tabla mensual disponible.")
    else:
        columnas = [
            "periodo_label",
            "grupo_planta",
            "Cumple",
            "No cumple",
            "Evaluables",
            "% Cumple",
            "% No cumple",
        ]

        columnas = [
            c for c in columnas
            if c in tabla_mensual.columns
        ]

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


# ============================================================
# Detalle de filtros
# ============================================================

with st.expander("Detalle de filtros aplicados", expanded=False):
    if resumen_filtros_df.empty:
        st.info("No hay detalle de filtros disponible.")
    else:
        st.dataframe(
            resumen_filtros_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Vista previa
# ============================================================

with st.expander("Vista previa de registros evaluables filtrados", expanded=False):
    limite_vista = st.number_input(
        "Filas a mostrar",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
        key="ejecutiva_plantas_limite_vista",
    )

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        "centro_grafico",
        "grupo_planta",
        "tipo_oc",
        "origen",
        "sistema",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "dias_tat_total",
        "umbral_tat_total",
        COL_PERFORMANCE_TAT,
        "dias_incumplimiento_tat",
        "rango_incumplimiento_tat",
    ]

    columnas_preferidas = [
        col for col in columnas_preferidas
        if col is not None and col in df_dashboard.columns
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
# Descarga base filtrada
# ============================================================

with st.expander("Descargar base ejecutiva filtrada", expanded=False):
    firma_export = (
        f"{len(df_dashboard)}_"
        f"{fecha_inicio}_"
        f"{fecha_fin}_"
        f"{','.join(plantas_sel)}_"
        f"{','.join(centros_sel)}_"
        f"{','.join(perf_sel)}"
    )

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        preparar_excel = st.button(
            "Preparar Excel",
            use_container_width=True,
            key="ejecutiva_plantas_preparar_excel",
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                st.session_state["ejecutiva_plantas_excel_bytes"] = convertir_a_excel_cache(df_dashboard)
                st.session_state["ejecutiva_plantas_excel_firma"] = firma_export

        if (
            st.session_state.get("ejecutiva_plantas_excel_bytes") is not None
            and st.session_state.get("ejecutiva_plantas_excel_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Excel",
                data=st.session_state["ejecutiva_plantas_excel_bytes"],
                file_name="13_VISTA_EJECUTIVA_PERFORMANCE_PLANTAS_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True,
            key="ejecutiva_plantas_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["ejecutiva_plantas_csv_bytes"] = convertir_a_csv_cache(df_dashboard)
                st.session_state["ejecutiva_plantas_csv_firma"] = firma_export

        if (
            st.session_state.get("ejecutiva_plantas_csv_bytes") is not None
            and st.session_state.get("ejecutiva_plantas_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV",
                data=st.session_state["ejecutiva_plantas_csv_bytes"],
                file_name="13_VISTA_EJECUTIVA_PERFORMANCE_PLANTAS_filtrado.csv",
                mime="text/csv",
                use_container_width=True,
            )
