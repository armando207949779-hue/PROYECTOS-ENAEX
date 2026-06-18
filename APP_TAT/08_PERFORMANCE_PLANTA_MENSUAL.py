# ============================================================
# 08_PERFORMANCE_PLANTA_MENSUAL
# Dashboard mensual de Performance TAT por planta / centro
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Mejoras:
# - Mantiene visión global mensual
# - Agrega zoom del último año disponible debajo de los gráficos globales
# - Agrega KPI Indicators del último año disponible
# - Promedio de cumplimiento mensual del último año
# - Cumplimiento acumulado del último año
# ============================================================

import io
import base64
from pathlib import Path
from datetime import datetime

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

COLOR_CUMPLE = "#EF3E52"
COLOR_NO_CUMPLE = "#BFC3C7"
COLOR_EN_PROCESO = "#F4B400"
COLOR_NO_APLICA = "#9CA3AF"
COLOR_SIN_DATOS = "#D1D5DB"
COLOR_META = "#0057B8"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"
COLOR_LINEA = "#111827"

COLOR_EFICIENCIA_ALTA = "#2E7D32"
COLOR_EFICIENCIA_MEDIA = "#F4B400"
COLOR_EFICIENCIA_BAJA = "#EF3E52"

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
COL_DOCUMENTO_COMPRAS = "Documento de compras - ME80FN"
COL_TIPO_COMPRA_ARIBA = "Tipo de compra - ARIBA"
COL_CANTIDAD_SOLICITADA = "Cantidad solicitada - ME5A"
COL_PRECIO_VALORACION = "Precio de valoración"

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
]

ETAPAS_DASHBOARD = [
    {
        "titulo": "Lib SolPed",
        "col_perf": "performance_liberacion_solped",
        "col_dias": "dias_liberacion_solped",
        "regla": "Umbral: 2 días",
    },
    {
        "titulo": "Comprador",
        "col_perf": "performance_comprador",
        "col_dias": "dias_comprador",
        "regla": "Umbral: 10 días",
    },
    {
        "titulo": "Proveedor",
        "col_perf": "performance_proveedor",
        "col_dias": "dias_proveedor",
        "regla": "Nacional 20 días · Internacional 60 días",
    },
    {
        "titulo": "Logística",
        "col_perf": "performance_logistica",
        "col_dias": "dias_logistica",
        "regla": "Umbral: 11 días",
    },
]


# ============================================================
# Estilos
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            padding: 14px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
        }

        .kpi-box {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 14px;
            padding: 16px;
            height: 100%;
        }

        .kpi-title {
            color: #6B7280;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .kpi-value {
            color: #111827;
            font-size: 28px;
            font-weight: 800;
            margin-bottom: 2px;
        }

        .kpi-subtitle {
            color: #6B7280;
            font-size: 13px;
            line-height: 1.35;
        }

        .kpi-warning {
            color: #B45309;
            font-weight: 700;
        }

        .kpi-good {
            color: #166534;
            font-weight: 700;
        }

        .kpi-bad {
            color: #991B1B;
            font-weight: 700;
        }

        .info-box {
            background-color: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 14px;
            padding: 16px;
            margin-bottom: 14px;
        }

        .info-title {
            font-weight: 800;
            color: #111827;
            font-size: 16px;
            margin-bottom: 6px;
        }

        .info-text {
            color: #4B5563;
            font-size: 14px;
            line-height: 1.45;
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
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# Funciones generales
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

    if texto in ["nan", "none", "<na>", "null", ""]:
        return "Sin datos"

    return "Sin datos"


def normalizar_rango_incumplimiento(serie: pd.Series) -> pd.Series:
    orden_valido = [
        "Sin incumplimiento",
        "1-5 días",
        "6-15 días",
        "16-30 días",
        "Mayor a un mes",
        "Sin datos",
    ]

    texto = serie.astype("string").str.strip()
    texto_lower = texto.str.lower()

    mask_sin_datos = (
        texto.isna()
        | texto.eq("")
        | texto_lower.isin(["nan", "none", "<na>", "null"])
    )

    texto = texto.mask(mask_sin_datos, "Sin datos")

    texto = texto.where(
        texto.isin(orden_valido),
        "Sin datos",
    )

    return texto


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
# Cálculo de performance si no existe
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


def calcular_dias_incumplimiento_tat(
    dias_tat: pd.Series,
    umbral_tat: pd.Series,
) -> pd.Series:

    diferencia = dias_tat - umbral_tat
    resultado = diferencia.where(diferencia > 0, 0)
    resultado = resultado.mask(dias_tat.isna() | umbral_tat.isna(), np.nan)

    return resultado


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
def preparar_base_tat(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    df = normalizar_columnas_me80fn(df)

    validar_fechas_finales(df)

    for col in COLUMNAS_FECHA_PERFORMANCE:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])

    columnas_minimas_perf = [
        "performance_tat_total",
        "dias_tat_total",
        "umbral_tat_total",
        "dias_incumplimiento_tat",
        "rango_incumplimiento_tat",
    ]

    performance_ya_calculada = all(
        col in df.columns
        for col in columnas_minimas_perf
    )

    if not performance_ya_calculada:
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
            fecha_fin=df[COL_FECHA_LIBERACION_FINAL],
            fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL],
        )

        df["dias_comprador"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_PEDIDO_FINAL],
            fecha_inicio=df[COL_FECHA_LIBERACION_FINAL],
        )

        df["dias_liberacion_pedido"] = np.nan

        df["dias_proveedor"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_FACTURACION_FINAL],
            fecha_inicio=df[COL_FECHA_PEDIDO_FINAL],
        )

        df["dias_logistica"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
            fecha_inicio=df[COL_FECHA_FACTURACION_FINAL],
        )

        df["dias_tat_total"] = diferencia_dias(
            fecha_fin=df[COL_FECHA_RECEPCION_FINAL],
            fecha_inicio=df[COL_FECHA_SOLICITUD_FINAL],
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

        columnas_dias = [
            "dias_liberacion_solped",
            "dias_comprador",
            "dias_liberacion_pedido",
            "dias_proveedor",
            "dias_logistica",
            "dias_tat_total",
        ]

        df["tiene_fechas_inconsistentes"] = (
            df[columnas_dias]
            .lt(0)
            .any(axis=1, skipna=True)
        )

        df["performance_liberacion_solped"] = evaluar_performance_basica(
            dias=df["dias_liberacion_solped"],
            umbral=pd.Series(df["umbral_liberacion_solped"], index=df.index),
            texto_sin_dato="No aplica",
        )

        df["performance_comprador"] = evaluar_performance_basica(
            dias=df["dias_comprador"],
            umbral=pd.Series(df["umbral_comprador"], index=df.index),
            texto_sin_dato="No aplica",
        )

        df["performance_liberacion_pedido"] = evaluar_performance_basica(
            dias=pd.Series(df["dias_liberacion_pedido"], index=df.index),
            umbral=pd.Series(df["umbral_liberacion_pedido"], index=df.index),
            texto_sin_dato="Sin datos",
        )

        df["performance_proveedor"] = evaluar_performance_basica(
            dias=df["dias_proveedor"],
            umbral=df["umbral_proveedor"],
            texto_sin_dato="Sin datos",
        )

        df["performance_logistica"] = evaluar_performance_basica(
            dias=df["dias_logistica"],
            umbral=pd.Series(df["umbral_logistica"], index=df.index),
            texto_sin_dato="No aplica",
        )

        df["performance_tat_total"] = evaluar_performance_tat(df)

        df["dias_incumplimiento_tat"] = calcular_dias_incumplimiento_tat(
            dias_tat=df["dias_tat_total"],
            umbral_tat=df["umbral_tat_total"],
        )

        df["incumplimiento_tat"] = df["dias_incumplimiento_tat"].gt(0)

        df["rango_incumplimiento_tat"] = calcular_rango_incumplimiento_tat(
            df["dias_incumplimiento_tat"]
        )

    for col in [
        "performance_tat_total",
        "performance_liberacion_solped",
        "performance_comprador",
        "performance_liberacion_pedido",
        "performance_proveedor",
        "performance_logistica",
    ]:
        if col in df.columns:
            df[col] = df[col].apply(normalizar_estado_performance)

    if "rango_incumplimiento_tat" in df.columns:
        df["rango_incumplimiento_tat"] = normalizar_rango_incumplimiento(
            df["rango_incumplimiento_tat"]
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
    sistemas_sel: list,
    centros_sel: list,
    perf_sel: list,
    col_centro: str | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:

    barra = st.progress(0, text="Preparando filtros...")

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

    barra.progress(15, text="Aplicando filtro de fechas...")

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
            "Filtro 1",
            "Fecha recepción",
            f"{fecha_inicio} a {fecha_fin}",
            antes,
            df_filtrado,
        )

    barra.progress(40, text="Aplicando filtro de sistema...")

    if sistemas_sel and "sistema" in df_filtrado.columns:
        antes = df_filtrado.copy()

        df_filtrado = df_filtrado[
            df_filtrado["sistema"].astype("string").isin(sistemas_sel)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 2",
            "Sistema",
            ", ".join(sistemas_sel),
            antes,
            df_filtrado,
        )

    barra.progress(65, text="Aplicando filtro de centro...")

    if centros_sel and col_centro is not None and col_centro in df_filtrado.columns:
        antes = df_filtrado.copy()

        centros_norm = [str(x).strip() for x in centros_sel]

        df_filtrado = df_filtrado[
            df_filtrado[col_centro]
            .astype("string")
            .str.strip()
            .isin(centros_norm)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 3",
            "Centro",
            ", ".join(centros_norm),
            antes,
            df_filtrado,
        )

    barra.progress(85, text="Aplicando filtro de performance...")

    if perf_sel and "performance_tat_total" in df_filtrado.columns:
        antes = df_filtrado.copy()

        df_filtrado = df_filtrado[
            df_filtrado["performance_tat_total"]
            .astype("string")
            .isin(perf_sel)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 4",
            "Performance TAT",
            ", ".join(perf_sel),
            antes,
            df_filtrado,
        )

    barra.progress(100, text="Filtros aplicados correctamente.")

    return df_filtrado, pd.DataFrame(resumen)


# ============================================================
# Resúmenes TAT
# ============================================================

def crear_resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    if "performance_tat_total" not in df.columns:
        return pd.DataFrame()

    base = df[df["periodo_fecha"].notna()].copy()

    if base.empty:
        return pd.DataFrame()

    base["estado_mensual"] = base["performance_tat_total"].apply(normalizar_estado_performance)

    resumen = (
        base
        .groupby(["periodo_fecha", "periodo_label", "estado_mensual"])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=["periodo_fecha", "periodo_label"],
        columns="estado_mensual",
        values="cantidad",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for col in ["Cumple", "No cumple", "En proceso", "No aplica", "Sin datos"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["No evaluables"] = tabla["En proceso"] + tabla["No aplica"] + tabla["Sin datos"]

    tabla["Total registros"] = (
        tabla["Cumple"]
        + tabla["No cumple"]
        + tabla["No evaluables"]
    )

    tabla["Evaluables"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Evaluables"] = np.where(
        tabla["Total registros"] > 0,
        tabla["Evaluables"] / tabla["Total registros"] * 100,
        0,
    )

    tabla["% Cumple evaluables"] = np.where(
        tabla["Evaluables"] > 0,
        tabla["Cumple"] / tabla["Evaluables"] * 100,
        0,
    )

    tabla["% No cumple evaluables"] = np.where(
        tabla["Evaluables"] > 0,
        tabla["No cumple"] / tabla["Evaluables"] * 100,
        0,
    )

    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


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
        .sort_values("periodo_fecha")
        .reset_index(drop=True)
    )

    return tabla_ultimo_anio, ultimo_anio


def calcular_kpis_ultimo_anio(tabla_ultimo_anio: pd.DataFrame, anio: int | None) -> dict:
    if tabla_ultimo_anio.empty or anio is None:
        return {
            "anio": "—",
            "meses": 0,
            "promedio_cumplimiento_mensual": 0,
            "promedio_no_cumplimiento_mensual": 0,
            "cumple": 0,
            "no_cumple": 0,
            "evaluables": 0,
            "cumplimiento_acumulado": 0,
            "no_cumplimiento_acumulado": 0,
        }

    evaluables_mensuales = tabla_ultimo_anio[
        tabla_ultimo_anio["Evaluables"].gt(0)
    ].copy()

    cumple_total = int(pd.to_numeric(tabla_ultimo_anio["Cumple"], errors="coerce").fillna(0).sum())
    no_cumple_total = int(pd.to_numeric(tabla_ultimo_anio["No cumple"], errors="coerce").fillna(0).sum())
    evaluables_total = int(pd.to_numeric(tabla_ultimo_anio["Evaluables"], errors="coerce").fillna(0).sum())

    promedio_cumplimiento = (
        float(evaluables_mensuales["% Cumple evaluables"].mean())
        if not evaluables_mensuales.empty
        else 0
    )

    promedio_no_cumplimiento = (
        float(evaluables_mensuales["% No cumple evaluables"].mean())
        if not evaluables_mensuales.empty
        else 0
    )

    cumplimiento_acumulado = (
        cumple_total / evaluables_total * 100
        if evaluables_total
        else 0
    )

    no_cumplimiento_acumulado = (
        no_cumple_total / evaluables_total * 100
        if evaluables_total
        else 0
    )

    return {
        "anio": anio,
        "meses": int(len(evaluables_mensuales)),
        "promedio_cumplimiento_mensual": promedio_cumplimiento,
        "promedio_no_cumplimiento_mensual": promedio_no_cumplimiento,
        "cumple": cumple_total,
        "no_cumple": no_cumple_total,
        "evaluables": evaluables_total,
        "cumplimiento_acumulado": cumplimiento_acumulado,
        "no_cumplimiento_acumulado": no_cumplimiento_acumulado,
    }


def crear_desglose_filtrado_tat(df: pd.DataFrame) -> pd.DataFrame:
    if "performance_tat_total" not in df.columns:
        return pd.DataFrame()

    orden = [
        "Cumple",
        "No cumple",
        "En proceso",
        "No aplica",
        "Sin datos",
    ]

    serie = df["performance_tat_total"].apply(normalizar_estado_performance)

    tabla = (
        serie
        .value_counts()
        .reindex(orden, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Categoría", "Cantidad"]

    total_filtrado = int(tabla["Cantidad"].sum())

    evaluables = int(
        tabla.loc[
            tabla["Categoría"].isin(["Cumple", "No cumple"]),
            "Cantidad",
        ].sum()
    )

    tabla["Tipo"] = np.where(
        tabla["Categoría"].isin(["Cumple", "No cumple"]),
        "Evaluable",
        "No evaluable",
    )

    tabla["% sobre filtrados"] = np.where(
        total_filtrado > 0,
        tabla["Cantidad"] / total_filtrado * 100,
        0,
    )

    tabla["% sobre evaluables"] = np.where(
        tabla["Categoría"].isin(["Cumple", "No cumple"]) & (evaluables > 0),
        tabla["Cantidad"] / evaluables * 100,
        np.nan,
    )

    tabla["% sobre filtrados"] = tabla["% sobre filtrados"].round(2)
    tabla["% sobre evaluables"] = tabla["% sobre evaluables"].round(2)

    return tabla


def crear_desglose_evaluables_tat(df: pd.DataFrame) -> pd.DataFrame:
    if "performance_tat_total" not in df.columns:
        return pd.DataFrame()

    estado = df["performance_tat_total"].apply(normalizar_estado_performance)

    tabla = (
        estado[estado.isin(["Cumple", "No cumple"])]
        .value_counts()
        .reindex(["Cumple", "No cumple"], fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Categoría", "Cantidad"]

    total_evaluable = int(tabla["Cantidad"].sum())

    tabla["% sobre evaluables"] = np.where(
        total_evaluable > 0,
        tabla["Cantidad"] / total_evaluable * 100,
        0,
    )

    tabla["% sobre evaluables"] = tabla["% sobre evaluables"].round(2)

    return tabla


def calcular_kpis_tat(
    df_base: pd.DataFrame,
    df_filtrado: pd.DataFrame,
) -> dict:

    total_ingresado = int(len(df_base))
    total_retenido = int(len(df_filtrado))
    total_excluido = total_ingresado - total_retenido

    pct_retenido = (
        total_retenido / total_ingresado * 100
        if total_ingresado
        else 0
    )

    pct_excluido = (
        total_excluido / total_ingresado * 100
        if total_ingresado
        else 0
    )

    if "performance_tat_total" in df_filtrado.columns:
        estado = df_filtrado["performance_tat_total"].apply(normalizar_estado_performance)
    else:
        estado = pd.Series([], dtype="object")

    cumple = int(estado.eq("Cumple").sum())
    no_cumple = int(estado.eq("No cumple").sum())
    en_proceso = int(estado.eq("En proceso").sum())
    no_aplica = int(estado.eq("No aplica").sum())
    sin_datos = int(estado.eq("Sin datos").sum())

    evaluables = cumple + no_cumple
    no_evaluables = en_proceso + no_aplica + sin_datos

    pct_evaluables = (
        evaluables / total_retenido * 100
        if total_retenido
        else 0
    )

    pct_no_evaluables = (
        no_evaluables / total_retenido * 100
        if total_retenido
        else 0
    )

    pct_cumple_evaluable = (
        cumple / evaluables * 100
        if evaluables
        else 0
    )

    pct_no_cumple_evaluable = (
        no_cumple / evaluables * 100
        if evaluables
        else 0
    )

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
        "pct_cumple_evaluable": pct_cumple_evaluable,
        "pct_no_cumple_evaluable": pct_no_cumple_evaluable,
        "en_proceso": en_proceso,
        "no_aplica": no_aplica,
        "sin_datos": sin_datos,
    }


def calcular_kpis_mensuales(tabla_mensual: pd.DataFrame) -> dict:
    if tabla_mensual.empty:
        return {
            "meses": 0,
            "cumplimiento_promedio": 0,
            "no_cumplimiento_promedio": 0,
            "mejor_mes": "—",
            "mejor_mes_pct": 0,
            "peor_mes": "—",
            "peor_mes_pct": 0,
        }

    evaluables = tabla_mensual[
        tabla_mensual["Evaluables"].gt(0)
    ].copy()

    if evaluables.empty:
        return {
            "meses": 0,
            "cumplimiento_promedio": 0,
            "no_cumplimiento_promedio": 0,
            "mejor_mes": "—",
            "mejor_mes_pct": 0,
            "peor_mes": "—",
            "peor_mes_pct": 0,
        }

    cumplimiento_promedio = float(evaluables["% Cumple evaluables"].mean())
    no_cumplimiento_promedio = float(evaluables["% No cumple evaluables"].mean())

    mejor = evaluables.sort_values(
        ["% Cumple evaluables", "Evaluables"],
        ascending=[False, False],
    ).iloc[0]

    peor = evaluables.sort_values(
        ["% Cumple evaluables", "Evaluables"],
        ascending=[True, False],
    ).iloc[0]

    return {
        "meses": int(len(evaluables)),
        "cumplimiento_promedio": cumplimiento_promedio,
        "no_cumplimiento_promedio": no_cumplimiento_promedio,
        "mejor_mes": str(mejor["periodo_label"]),
        "mejor_mes_pct": float(mejor["% Cumple evaluables"]),
        "peor_mes": str(peor["periodo_label"]),
        "peor_mes_pct": float(peor["% Cumple evaluables"]),
    }


def datos_etapa(df: pd.DataFrame, etapa: dict) -> dict:
    col_perf = etapa["col_perf"]
    col_dias = etapa["col_dias"]

    if col_perf not in df.columns:
        return {
            "cumple": 0,
            "no_cumple": 0,
            "evaluables": 0,
            "pct_cumple": 0,
            "pct_no_cumple": 0,
            "promedio_dias": 0,
            "n_promedio": 0,
        }

    temp = df[df[col_perf].isin(["Cumple", "No cumple"])].copy()

    cumple = int(temp[col_perf].eq("Cumple").sum())
    no_cumple = int(temp[col_perf].eq("No cumple").sum())
    evaluables = cumple + no_cumple

    pct_cumple = cumple / evaluables * 100 if evaluables else 0
    pct_no_cumple = no_cumple / evaluables * 100 if evaluables else 0

    if col_dias in df.columns:
        dias = pd.to_numeric(df[col_dias], errors="coerce")
        dias = dias[dias > 0]
        promedio = dias.mean() if not dias.empty else 0
        n_promedio = int(len(dias))
    else:
        promedio = 0
        n_promedio = 0

    return {
        "cumple": cumple,
        "no_cumple": no_cumple,
        "evaluables": evaluables,
        "pct_cumple": pct_cumple,
        "pct_no_cumple": pct_no_cumple,
        "promedio_dias": promedio,
        "n_promedio": n_promedio,
    }


def crear_resumen_etapas(df: pd.DataFrame) -> pd.DataFrame:
    registros = []

    for etapa in ETAPAS_DASHBOARD:
        datos = datos_etapa(df, etapa)

        registros.append(
            {
                "Etapa": etapa["titulo"],
                "Regla": etapa["regla"],
                "Cumple": datos["cumple"],
                "No cumple": datos["no_cumple"],
                "Evaluables": datos["evaluables"],
                "% Cumple": round(datos["pct_cumple"], 2),
                "% No cumple": round(datos["pct_no_cumple"], 2),
                "Promedio días > 0": round(datos["promedio_dias"], 2),
                "N promedio": datos["n_promedio"],
            }
        )

    return pd.DataFrame(registros)


# ============================================================
# Distribuciones TAT vs umbral
# ============================================================

def preparar_base_distribucion_tat(df: pd.DataFrame, estado: str) -> pd.DataFrame:
    columnas_necesarias = [
        "performance_tat_total",
        "dias_tat_total",
        "umbral_tat_total",
    ]

    if any(col not in df.columns for col in columnas_necesarias):
        return pd.DataFrame()

    base = df[
        df["performance_tat_total"].astype("string").eq(estado)
    ].copy()

    if base.empty:
        return pd.DataFrame()

    base["dias_tat_total_num"] = pd.to_numeric(
        base["dias_tat_total"],
        errors="coerce",
    )

    base["umbral_tat_total_num"] = pd.to_numeric(
        base["umbral_tat_total"],
        errors="coerce",
    )

    base = base[
        base["dias_tat_total_num"].notna()
        & base["umbral_tat_total_num"].notna()
        & base["umbral_tat_total_num"].gt(0)
        & base["dias_tat_total_num"].ge(0)
    ].copy()

    return base


def crear_distribucion_eficiencia_cumple(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    base = preparar_base_distribucion_tat(df, "Cumple")

    if base.empty:
        return pd.DataFrame(), {
            "total": 0,
            "total_evaluables": 0,
            "pct_cumple": 0,
            "promedio_uso_umbral": 0,
            "promedio_dias_tat": 0,
            "promedio_umbral": 0,
        }

    estado = df["performance_tat_total"].apply(normalizar_estado_performance)
    total_evaluables = int(estado.isin(["Cumple", "No cumple"]).sum())
    total_cumple = int(len(base))

    base["uso_umbral_pct"] = (
        base["dias_tat_total_num"] / base["umbral_tat_total_num"] * 100
    )

    bins = [-np.inf, 25, 50, 75, 100, np.inf]
    labels = [
        "Muy eficiente: 0% - 25% del umbral",
        "Eficiente: 26% - 50% del umbral",
        "Aceptable: 51% - 75% del umbral",
        "Poco eficiente: 76% - 100% del umbral",
        "Revisar: mayor al umbral",
    ]

    base["Rango"] = pd.cut(
        base["uso_umbral_pct"],
        bins=bins,
        labels=labels,
        right=True,
    )

    tabla = (
        base
        .groupby("Rango", observed=False)
        .agg(
            Cantidad=("Rango", "size"),
            Promedio_dias_TAT=("dias_tat_total_num", "mean"),
            Promedio_umbral=("umbral_tat_total_num", "mean"),
            Promedio_uso_umbral_pct=("uso_umbral_pct", "mean"),
        )
        .reset_index()
    )

    total = tabla["Cantidad"].sum()

    tabla["% sobre Cumple"] = np.where(
        total > 0,
        tabla["Cantidad"] / total * 100,
        0,
    )

    tabla["Interpretación"] = [
        "Mayor eficiencia",
        "Buena eficiencia",
        "Eficiencia media",
        "Bajo margen de cumplimiento",
        "Revisar datos / regla",
    ]

    tabla["Promedio_dias_TAT"] = tabla["Promedio_dias_TAT"].round(2)
    tabla["Promedio_umbral"] = tabla["Promedio_umbral"].round(2)
    tabla["Promedio_uso_umbral_pct"] = tabla["Promedio_uso_umbral_pct"].round(2)
    tabla["% sobre Cumple"] = tabla["% sobre Cumple"].round(2)

    tabla = tabla.rename(
        columns={
            "Promedio_dias_TAT": "Promedio días TAT",
            "Promedio_umbral": "Promedio umbral",
            "Promedio_uso_umbral_pct": "Promedio uso umbral %",
        }
    )

    kpis = {
        "total": total_cumple,
        "total_evaluables": total_evaluables,
        "pct_cumple": total_cumple / total_evaluables * 100 if total_evaluables else 0,
        "promedio_uso_umbral": base["uso_umbral_pct"].mean(),
        "promedio_dias_tat": base["dias_tat_total_num"].mean(),
        "promedio_umbral": base["umbral_tat_total_num"].mean(),
    }

    return tabla, kpis


def crear_distribucion_severidad_no_cumple(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    base = preparar_base_distribucion_tat(df, "No cumple")

    if base.empty:
        return pd.DataFrame(), {
            "total": 0,
            "total_evaluables": 0,
            "pct_no_cumple": 0,
            "promedio_dias_sobre_umbral": 0,
            "promedio_dias_tat": 0,
            "promedio_umbral": 0,
        }

    estado = df["performance_tat_total"].apply(normalizar_estado_performance)
    total_evaluables = int(estado.isin(["Cumple", "No cumple"]).sum())
    total_no_cumple = int(len(base))

    base["dias_sobre_umbral"] = (
        base["dias_tat_total_num"] - base["umbral_tat_total_num"]
    )

    base = base[
        base["dias_sobre_umbral"].gt(0)
    ].copy()

    if base.empty:
        return pd.DataFrame(), {
            "total": 0,
            "total_evaluables": total_evaluables,
            "pct_no_cumple": 0,
            "promedio_dias_sobre_umbral": 0,
            "promedio_dias_tat": 0,
            "promedio_umbral": 0,
        }

    bins = [0, 5, 15, 30, np.inf]
    labels = [
        "Leve: 1 - 5 días sobre umbral",
        "Moderado: 6 - 15 días sobre umbral",
        "Alto: 16 - 30 días sobre umbral",
        "Crítico: más de 30 días sobre umbral",
    ]

    base["Rango"] = pd.cut(
        base["dias_sobre_umbral"],
        bins=bins,
        labels=labels,
        right=True,
        include_lowest=True,
    )

    tabla = (
        base
        .groupby("Rango", observed=False)
        .agg(
            Cantidad=("Rango", "size"),
            Promedio_dias_TAT=("dias_tat_total_num", "mean"),
            Promedio_umbral=("umbral_tat_total_num", "mean"),
            Promedio_dias_sobre_umbral=("dias_sobre_umbral", "mean"),
        )
        .reset_index()
    )

    total = tabla["Cantidad"].sum()

    tabla["% sobre No cumple"] = np.where(
        total > 0,
        tabla["Cantidad"] / total * 100,
        0,
    )

    tabla["Interpretación"] = [
        "Retraso leve",
        "Retraso moderado",
        "Retraso alto",
        "Retraso crítico",
    ]

    tabla["Promedio_dias_TAT"] = tabla["Promedio_dias_TAT"].round(2)
    tabla["Promedio_umbral"] = tabla["Promedio_umbral"].round(2)
    tabla["Promedio_dias_sobre_umbral"] = tabla["Promedio_dias_sobre_umbral"].round(2)
    tabla["% sobre No cumple"] = tabla["% sobre No cumple"].round(2)

    tabla = tabla.rename(
        columns={
            "Promedio_dias_TAT": "Promedio días TAT",
            "Promedio_umbral": "Promedio umbral",
            "Promedio_dias_sobre_umbral": "Promedio días sobre umbral",
        }
    )

    kpis = {
        "total": total_no_cumple,
        "total_evaluables": total_evaluables,
        "pct_no_cumple": total_no_cumple / total_evaluables * 100 if total_evaluables else 0,
        "promedio_dias_sobre_umbral": base["dias_sobre_umbral"].mean(),
        "promedio_dias_tat": base["dias_tat_total_num"].mean(),
        "promedio_umbral": base["umbral_tat_total_num"].mean(),
    }

    return tabla, kpis


# ============================================================
# KPI visuales
# ============================================================

def mostrar_kpi_html(titulo: str, valor: str, subtitulo: str, clase: str = ""):
    clase_css = f" {clase}" if clase else ""

    st.markdown(
        f"""
        <div class="kpi-box">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value{clase_css}">{valor}</div>
            <div class="kpi-subtitle">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_indicadores_tat(kpis: dict):
    st.markdown("### KPI Indicators")
    st.caption(
        "Cumplimiento TAT se calcula solo sobre registros evaluables: Cumple + No cumple. "
        "Los registros En proceso, No aplica y Sin datos no entran al porcentaje de cumplimiento."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mostrar_kpi_html(
            "Registros ingresados",
            formatear_entero(kpis["total_ingresado"]),
            "Total de registros antes de aplicar filtros.",
        )

    with col2:
        mostrar_kpi_html(
            "% retenido por filtros",
            formatear_porcentaje(kpis["pct_retenido"]),
            f"{formatear_entero(kpis['total_retenido'])} retenidos de {formatear_entero(kpis['total_ingresado'])} ingresados.",
        )

    with col3:
        mostrar_kpi_html(
            "Cantidad retenida por filtros",
            formatear_entero(kpis["total_retenido"]),
            f"{formatear_entero(kpis['total_excluido'])} excluidos · {formatear_porcentaje(kpis['pct_excluido'])} excluido.",
        )

    with col4:
        mostrar_kpi_html(
            "% evaluables",
            formatear_porcentaje(kpis["pct_evaluables"]),
            f"{formatear_entero(kpis['evaluables'])} evaluables de {formatear_entero(kpis['total_retenido'])} retenidos.",
        )

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        mostrar_kpi_html(
            "Cantidad evaluables",
            formatear_entero(kpis["evaluables"]),
            f"No evaluables: {formatear_entero(kpis['no_evaluables'])} · {formatear_porcentaje(kpis['pct_no_evaluables'])}.",
        )

    with col6:
        mostrar_kpi_html(
            "Cumple TAT",
            formatear_porcentaje(kpis["pct_cumple_evaluable"]),
            f"{formatear_entero(kpis['cumple'])} cumplen de {formatear_entero(kpis['evaluables'])} evaluables.",
            "kpi-good",
        )

    with col7:
        mostrar_kpi_html(
            "No cumple TAT",
            formatear_porcentaje(kpis["pct_no_cumple_evaluable"]),
            f"{formatear_entero(kpis['no_cumple'])} no cumplen de {formatear_entero(kpis['evaluables'])} evaluables.",
            "kpi-bad",
        )

    with col8:
        mostrar_kpi_html(
            "No evaluables",
            formatear_entero(kpis["no_evaluables"]),
            f"En proceso: {formatear_entero(kpis['en_proceso'])} · No aplica: {formatear_entero(kpis['no_aplica'])} · Sin datos: {formatear_entero(kpis['sin_datos'])}.",
            "kpi-warning",
        )


def mostrar_indicadores_mensuales(kpis_mensuales: dict):
    st.markdown("### KPI Indicators mensuales")
    st.caption(
        "Estos indicadores resumen el comportamiento mensual sobre registros evaluables."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mostrar_kpi_html(
            "Cumplimiento promedio mensual",
            formatear_porcentaje(kpis_mensuales["cumplimiento_promedio"]),
            f"Promedio de {kpis_mensuales['meses']} mes(es) con registros evaluables.",
            "kpi-good",
        )

    with col2:
        mostrar_kpi_html(
            "No cumplimiento promedio mensual",
            formatear_porcentaje(kpis_mensuales["no_cumplimiento_promedio"]),
            "Promedio mensual de registros No cumple sobre evaluables.",
            "kpi-bad",
        )

    with col3:
        mostrar_kpi_html(
            "Mejor mes",
            kpis_mensuales["mejor_mes"],
            f"{formatear_porcentaje(kpis_mensuales['mejor_mes_pct'])} de cumplimiento.",
        )

    with col4:
        mostrar_kpi_html(
            "Peor mes",
            kpis_mensuales["peor_mes"],
            f"{formatear_porcentaje(kpis_mensuales['peor_mes_pct'])} de cumplimiento.",
            "kpi-warning",
        )


def mostrar_indicadores_ultimo_anio(kpis_ultimo_anio: dict):
    st.markdown(f"#### KPI Indicators último año disponible: {kpis_ultimo_anio['anio']}")
    st.caption(
        "Estos indicadores se calculan únicamente sobre el último año disponible en los datos filtrados."
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mostrar_kpi_html(
            "Promedio cumplimiento mensual",
            formatear_porcentaje(kpis_ultimo_anio["promedio_cumplimiento_mensual"]),
            f"Promedio de {kpis_ultimo_anio['meses']} mes(es) con registros evaluables.",
            "kpi-good",
        )

    with col2:
        mostrar_kpi_html(
            "Promedio no cumplimiento mensual",
            formatear_porcentaje(kpis_ultimo_anio["promedio_no_cumplimiento_mensual"]),
            "Promedio mensual de No cumple sobre evaluables.",
            "kpi-bad",
        )

    with col3:
        mostrar_kpi_html(
            "Cumplimiento acumulado año",
            formatear_porcentaje(kpis_ultimo_anio["cumplimiento_acumulado"]),
            f"{formatear_entero(kpis_ultimo_anio['cumple'])} cumplen de {formatear_entero(kpis_ultimo_anio['evaluables'])} evaluables.",
            "kpi-good",
        )

    with col4:
        mostrar_kpi_html(
            "No cumplimiento acumulado año",
            formatear_porcentaje(kpis_ultimo_anio["no_cumplimiento_acumulado"]),
            f"{formatear_entero(kpis_ultimo_anio['no_cumple'])} no cumplen de {formatear_entero(kpis_ultimo_anio['evaluables'])} evaluables.",
            "kpi-bad",
        )


def mostrar_detalle_filtros_aplicados(resumen_filtros_df: pd.DataFrame):
    st.markdown("### Detalle de filtros aplicados")
    st.caption(
        "Esta sección muestra cuántos registros se retienen y cuántos se excluyen en cada filtro."
    )

    if resumen_filtros_df is None or resumen_filtros_df.empty:
        st.info("No hay detalle de filtros disponible.")
        return

    resumen = resumen_filtros_df.copy()

    registros_iniciales = int(resumen.iloc[0]["Registros antes"])
    registros_finales = int(resumen.iloc[-1]["Registros después"])
    registros_excluidos = registros_iniciales - registros_finales

    pct_retenido = (
        registros_finales / registros_iniciales * 100
        if registros_iniciales
        else 0
    )

    pct_excluido = (
        registros_excluidos / registros_iniciales * 100
        if registros_iniciales
        else 0
    )

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    col_f1.metric("Registros ingresados", f"{registros_iniciales:,}".replace(",", "."))
    col_f2.metric("Registros retenidos", f"{registros_finales:,}".replace(",", "."), f"{pct_retenido:.1f}%")
    col_f3.metric("Registros excluidos", f"{registros_excluidos:,}".replace(",", "."), f"{pct_excluido:.1f}%")
    col_f4.metric("Filtros aplicados", f"{max(len(resumen) - 1, 0):,}".replace(",", "."))

    columnas_mostrar = [
        "Paso",
        "Filtro aplicado",
        "Valor",
        "Registros antes",
        "Registros después",
        "Registros excluidos",
        "% retenido",
        "% excluido",
    ]

    columnas_mostrar = [
        col for col in columnas_mostrar
        if col in resumen.columns
    ]

    st.dataframe(
        resumen[columnas_mostrar],
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Calidad de datos
# ============================================================

def generar_resumen_nan_sin_datos(
    df: pd.DataFrame,
    columnas_revision: list[str],
) -> pd.DataFrame:

    registros = []

    for col in columnas_revision:
        if col not in df.columns:
            continue

        serie_original = df[col]

        serie_texto = (
            serie_original
            .astype("string")
            .str.strip()
        )

        serie_texto_lower = serie_texto.str.lower()

        total = len(df)
        nan_real = int(serie_original.isna().sum())

        texto_nan = int(
            serie_texto_lower
            .isin(["nan", "none", "<na>", "null"])
            .sum()
        )

        texto_sin_datos = int(
            serie_texto_lower
            .eq("sin datos")
            .sum()
        )

        vacio_texto = int(
            serie_texto
            .fillna("")
            .eq("")
            .sum()
        )

        total_sin_informacion = (
            nan_real
            + texto_nan
            + texto_sin_datos
            + vacio_texto
        )

        registros.append(
            {
                "Columna": col,
                "Total registros": total,
                "NaN real": nan_real,
                "Texto 'nan'": texto_nan,
                "Texto 'Sin datos'": texto_sin_datos,
                "Texto vacío": vacio_texto,
                "Total sin información": total_sin_informacion,
                "% sin información": round(
                    total_sin_informacion / total * 100,
                    2,
                ) if total else 0,
            }
        )

    return pd.DataFrame(registros)


def mostrar_detalle_nan_sin_datos(df: pd.DataFrame):
    st.markdown("### Calidad de datos: NaN vs Sin datos")

    columnas_revision = [
        "performance_tat_total",
        "rango_incumplimiento_tat",
        "dias_incumplimiento_tat",
        "dias_tat_total",
        "umbral_tat_total",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_RECEPCION_FINAL,
    ]

    columnas_revision = [
        col for col in columnas_revision
        if col in df.columns
    ]

    if not columnas_revision:
        st.info("No hay columnas disponibles para revisar NaN o Sin datos.")
        return

    resumen_calidad = generar_resumen_nan_sin_datos(
        df=df,
        columnas_revision=columnas_revision,
    )

    st.dataframe(
        resumen_calidad,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Gráficos generales
# ============================================================

def grafico_donut_retencion(total_ingresado: int, total_retenido: int):
    total_excluido = total_ingresado - total_retenido

    tabla = pd.DataFrame(
        [
            {
                "Categoría": "Retenidos",
                "Cantidad": total_retenido,
            },
            {
                "Categoría": "Excluidos",
                "Cantidad": total_excluido,
            },
        ]
    )

    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    if tabla.empty:
        st.info("No hay datos para graficar retención.")
        return

    total = int(tabla["Cantidad"].sum())

    tabla["%"] = np.where(
        total > 0,
        tabla["Cantidad"] / total * 100,
        0,
    )

    colores_mapa = {
        "Retenidos": "#2E7D32",
        "Excluidos": "#BFC3C7",
    }

    colores = tabla["Categoría"].map(colores_mapa).tolist()
    cantidades = tabla["Cantidad"].astype(int).to_numpy()
    porcentajes = tabla["%"].astype(float).to_numpy()
    etiquetas = tabla["Categoría"].astype(str).tolist()

    fig, ax = plt.subplots(figsize=(6.5, 4.8), dpi=180)

    wedges, texts, autotexts = ax.pie(
        cantidades,
        labels=None,
        startangle=90,
        counterclock=False,
        colors=colores,
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 4 else "",
        pctdistance=0.78,
        wedgeprops={
            "width": 0.38,
            "linewidth": 2.5,
            "edgecolor": "white",
        },
    )

    for autotext in autotexts:
        autotext.set_fontweight("bold")
        autotext.set_fontsize(10)
        autotext.set_color(COLOR_TEXTO)

    ax.text(
        0,
        0.08,
        f"{total:,}".replace(",", "."),
        ha="center",
        va="center",
        fontsize=20,
        fontweight="bold",
        color=COLOR_TEXTO,
    )

    ax.text(
        0,
        -0.12,
        "ingresados",
        ha="center",
        va="center",
        fontsize=10,
        color=COLOR_MUTED,
    )

    etiquetas_leyenda = [
        f"{cat} · {cant:,} · {pct:.1f}%".replace(",", ".")
        for cat, cant, pct in zip(etiquetas, cantidades, porcentajes)
    ]

    ax.legend(
        wedges,
        etiquetas_leyenda,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=9,
    )

    ax.set_title(
        "Retención por filtros",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXTO,
    )

    ax.axis("equal")
    fig.patch.set_alpha(0)
    fig.tight_layout()
    fig.subplots_adjust(right=0.70)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_donut_desglose_filtrado(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay datos para graficar el desglose filtrado.")
        return

    data = tabla[tabla["Cantidad"].gt(0)].copy()

    if data.empty:
        st.info("No hay categorías con cantidad mayor a cero.")
        return

    colores_mapa = {
        "Cumple": COLOR_CUMPLE,
        "No cumple": COLOR_NO_CUMPLE,
        "En proceso": COLOR_EN_PROCESO,
        "No aplica": COLOR_NO_APLICA,
        "Sin datos": COLOR_SIN_DATOS,
    }

    data["Color"] = data["Categoría"].map(colores_mapa).fillna(COLOR_NO_APLICA)

    cantidades = (
        pd.to_numeric(data["Cantidad"], errors="coerce")
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    porcentajes = (
        pd.to_numeric(data["% sobre filtrados"], errors="coerce")
        .fillna(0)
        .to_numpy()
    )

    colores = data["Color"].tolist()
    etiquetas = data["Categoría"].astype(str).tolist()

    total = int(cantidades.sum())

    col_grafico, col_resumen = st.columns([1.15, 1])

    with col_grafico:
        fig, ax = plt.subplots(figsize=(8.2, 6.4), dpi=180)

        wedges, texts, autotexts = ax.pie(
            cantidades,
            labels=None,
            startangle=90,
            counterclock=False,
            colors=colores,
            autopct=lambda pct: f"{pct:.1f}%" if pct >= 4 else "",
            pctdistance=0.78,
            wedgeprops={
                "width": 0.38,
                "linewidth": 2.5,
                "edgecolor": "white",
            },
        )

        for i, autotext in enumerate(autotexts):
            categoria = etiquetas[i]

            if categoria in ["No cumple", "En proceso", "No aplica", "Sin datos"]:
                autotext.set_color(COLOR_TEXTO)
            else:
                autotext.set_color("white")

            autotext.set_fontweight("bold")
            autotext.set_fontsize(10)

        ax.text(
            0,
            0.08,
            f"{total:,}".replace(",", "."),
            ha="center",
            va="center",
            fontsize=24,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

        ax.text(
            0,
            -0.12,
            "retenidos",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=COLOR_MUTED,
        )

        etiquetas_leyenda = []

        for categoria, cantidad, porcentaje in zip(etiquetas, cantidades, porcentajes):
            cantidad_txt = f"{int(cantidad):,}".replace(",", ".")
            etiquetas_leyenda.append(
                f"{categoria} · {cantidad_txt} · {porcentaje:.1f}%"
            )

        legend = ax.legend(
            wedges,
            etiquetas_leyenda,
            title="Desglose filtrado",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9.5,
            title_fontsize=10,
        )

        for texto in legend.get_texts():
            texto.set_color(COLOR_TEXTO)

        legend.get_title().set_color(COLOR_TEXTO)
        legend.get_title().set_fontweight("bold")

        ax.set_title(
            "Retenidos por Performance TAT",
            fontsize=15,
            fontweight="bold",
            color=COLOR_TEXTO,
            pad=16,
        )

        ax.axis("equal")
        fig.patch.set_alpha(0)
        fig.tight_layout()
        fig.subplots_adjust(right=0.72)

        st.pyplot(fig, clear_figure=True, use_container_width=True)

    with col_resumen:
        st.markdown("#### Desglose de retenidos")
        st.caption(
            "Base: todos los registros retenidos por filtros."
        )

        tabla_resumen = data.copy()

        tabla_resumen["Cantidad"] = (
            pd.to_numeric(tabla_resumen["Cantidad"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        tabla_resumen["% sobre filtrados"] = (
            pd.to_numeric(tabla_resumen["% sobre filtrados"], errors="coerce")
            .fillna(0)
            .round(1)
        )

        tabla_resumen["% sobre evaluables"] = (
            pd.to_numeric(tabla_resumen["% sobre evaluables"], errors="coerce")
            .round(1)
        )

        st.dataframe(
            tabla_resumen[
                [
                    "Categoría",
                    "Tipo",
                    "Cantidad",
                    "% sobre filtrados",
                    "% sobre evaluables",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cantidad": st.column_config.NumberColumn(
                    "Cantidad",
                    format="%d",
                ),
                "% sobre filtrados": st.column_config.ProgressColumn(
                    "% sobre filtrados",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "% sobre evaluables": st.column_config.NumberColumn(
                    "% sobre evaluables",
                    format="%.1f%%",
                ),
            },
        )


def grafico_donut_evaluables_tat(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay registros evaluables para graficar.")
        return

    data = tabla[tabla["Cantidad"].gt(0)].copy()

    if data.empty:
        st.info("No hay registros evaluables con cantidad mayor a cero.")
        return

    colores_mapa = {
        "Cumple": COLOR_CUMPLE,
        "No cumple": COLOR_NO_CUMPLE,
    }

    data["Color"] = data["Categoría"].map(colores_mapa).fillna(COLOR_NO_CUMPLE)

    cantidades = (
        pd.to_numeric(data["Cantidad"], errors="coerce")
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    porcentajes = (
        pd.to_numeric(data["% sobre evaluables"], errors="coerce")
        .fillna(0)
        .to_numpy()
    )

    colores = data["Color"].tolist()
    etiquetas = data["Categoría"].astype(str).tolist()

    total = int(cantidades.sum())

    col_grafico, col_resumen = st.columns([1.15, 1])

    with col_grafico:
        fig, ax = plt.subplots(figsize=(8.2, 6.4), dpi=180)

        wedges, texts, autotexts = ax.pie(
            cantidades,
            labels=None,
            startangle=90,
            counterclock=False,
            colors=colores,
            autopct=lambda pct: f"{pct:.1f}%" if pct >= 4 else "",
            pctdistance=0.78,
            wedgeprops={
                "width": 0.38,
                "linewidth": 2.5,
                "edgecolor": "white",
            },
        )

        for i, autotext in enumerate(autotexts):
            categoria = etiquetas[i]

            if categoria == "No cumple":
                autotext.set_color(COLOR_TEXTO)
            else:
                autotext.set_color("white")

            autotext.set_fontweight("bold")
            autotext.set_fontsize(10)

        ax.text(
            0,
            0.08,
            f"{total:,}".replace(",", "."),
            ha="center",
            va="center",
            fontsize=24,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

        ax.text(
            0,
            -0.12,
            "evaluables",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color=COLOR_MUTED,
        )

        etiquetas_leyenda = []

        for categoria, cantidad, porcentaje in zip(etiquetas, cantidades, porcentajes):
            cantidad_txt = f"{int(cantidad):,}".replace(",", ".")
            etiquetas_leyenda.append(
                f"{categoria} · {cantidad_txt} · {porcentaje:.1f}%"
            )

        legend = ax.legend(
            wedges,
            etiquetas_leyenda,
            title="Base evaluable",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9.5,
            title_fontsize=10,
        )

        for texto in legend.get_texts():
            texto.set_color(COLOR_TEXTO)

        legend.get_title().set_color(COLOR_TEXTO)
        legend.get_title().set_fontweight("bold")

        ax.set_title(
            "TAT sobre registros evaluables",
            fontsize=15,
            fontweight="bold",
            color=COLOR_TEXTO,
            pad=16,
        )

        ax.axis("equal")
        fig.patch.set_alpha(0)
        fig.tight_layout()
        fig.subplots_adjust(right=0.72)

        st.pyplot(fig, clear_figure=True, use_container_width=True)

    with col_resumen:
        st.markdown("#### Cumplimiento sobre evaluables")
        st.caption(
            "Base: Cumple + No cumple."
        )

        tabla_resumen = data.copy()

        tabla_resumen["Cantidad"] = (
            pd.to_numeric(tabla_resumen["Cantidad"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

        tabla_resumen["% sobre evaluables"] = (
            pd.to_numeric(tabla_resumen["% sobre evaluables"], errors="coerce")
            .fillna(0)
            .round(1)
        )

        st.dataframe(
            tabla_resumen[
                [
                    "Categoría",
                    "Cantidad",
                    "% sobre evaluables",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cantidad": st.column_config.NumberColumn(
                    "Cantidad",
                    format="%d",
                ),
                "% sobre evaluables": st.column_config.ProgressColumn(
                    "% sobre evaluables",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )


def grafico_barras_distribucion_intuitiva(
    tabla: pd.DataFrame,
    titulo: str,
    columna_porcentaje: str,
    color_barra: str,
    etiqueta_x: str,
):
    if tabla.empty:
        st.info("No hay datos para graficar esta distribución.")
        return

    data = tabla.copy()

    data["Rango"] = data["Rango"].astype(str)

    cantidades = (
        pd.to_numeric(data["Cantidad"], errors="coerce")
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    porcentajes = (
        pd.to_numeric(data[columna_porcentaje], errors="coerce")
        .fillna(0)
        .to_numpy()
    )

    labels = data["Rango"].tolist()
    y = np.arange(len(labels))

    alto_figura = max(5.2, len(labels) * 0.75)

    fig, ax = plt.subplots(figsize=(12.5, alto_figura), dpi=180)

    barras = ax.barh(
        y,
        cantidades,
        color=color_barra,
        height=0.58,
    )

    max_cantidad = max(cantidades) if len(cantidades) else 0

    ax.set_xlim(0, max(max_cantidad * 1.32, 10))

    for barra, cantidad, porcentaje in zip(barras, cantidades, porcentajes):
        ax.text(
            barra.get_width() + max(max_cantidad * 0.02, 0.5),
            barra.get_y() + barra.get_height() / 2,
            f"{cantidad:,} · {porcentaje:.1f}%".replace(",", "."),
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_yticks(y)

    ax.set_yticklabels(
        labels,
        fontsize=10,
        color=COLOR_MUTED,
    )

    ax.set_xlabel(etiqueta_x, color=COLOR_TEXTO)

    ax.set_title(
        titulo,
        fontsize=15,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=16,
    )

    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0)
    ax.set_facecolor("none")
    fig.patch.set_alpha(0)

    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def mostrar_bloque_distribucion_cumple(df_dashboard: pd.DataFrame):
    tabla, kpis = crear_distribucion_eficiencia_cumple(df_dashboard)

    st.markdown("#### Eficiencia de cumplimiento TAT")
    st.markdown(
        """
        <div class="info-box">
            <div class="info-title">Distribución para registros que tienen cumplimiento</div>
            <div class="info-text">
                Esta visualización muestra los registros que <b>cumplen TAT</b> y qué porcentaje del umbral definido fue necesario para cumplir.
                Se puede interpretar como <b>eficiencia de cumplimiento</b>: valores bajos indican que el registro cumplió con bastante margen,
                mientras que valores altos indican que el registro cumplió, pero estuvo cerca del límite del umbral.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mostrar_kpi_html(
            "Registros que cumplen",
            formatear_entero(kpis["total"]),
            f"De {formatear_entero(kpis['total_evaluables'])} registros evaluables.",
            "kpi-good",
        )

    with col2:
        mostrar_kpi_html(
            "% Cumplimiento",
            formatear_porcentaje(kpis["pct_cumple"]),
            "Porcentaje de registros Cumple sobre evaluables.",
            "kpi-good",
        )

    with col3:
        mostrar_kpi_html(
            "Uso promedio del umbral",
            formatear_porcentaje(kpis["promedio_uso_umbral"]),
            "Menor uso del umbral indica mayor eficiencia.",
        )

    with col4:
        mostrar_kpi_html(
            "Promedio días TAT",
            f"{kpis['promedio_dias_tat']:.1f}",
            f"Umbral promedio: {kpis['promedio_umbral']:.1f} días.",
        )

    if tabla.empty:
        st.info("No hay registros Cumple con días TAT y umbral válidos para graficar.")
        return

    col_grafico, col_tabla = st.columns([1.15, 1])

    with col_grafico:
        grafico_barras_distribucion_intuitiva(
            tabla=tabla,
            titulo="Eficiencia de cumplimiento: uso del umbral TAT",
            columna_porcentaje="% sobre Cumple",
            color_barra=COLOR_CUMPLE,
            etiqueta_x="Cantidad de registros que cumplen",
        )

    with col_tabla:
        st.markdown("##### Tabla de eficiencia de cumplimiento")
        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cantidad": st.column_config.NumberColumn(
                    "Cantidad",
                    format="%d",
                ),
                "% sobre Cumple": st.column_config.ProgressColumn(
                    "% sobre Cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Promedio días TAT": st.column_config.NumberColumn(
                    "Promedio días TAT",
                    format="%.2f",
                ),
                "Promedio umbral": st.column_config.NumberColumn(
                    "Promedio umbral",
                    format="%.2f",
                ),
                "Promedio uso umbral %": st.column_config.ProgressColumn(
                    "Promedio uso umbral %",
                    format="%.1f%%",
                    min_value=0,
                    max_value=120,
                ),
            },
        )


def mostrar_bloque_distribucion_no_cumple(df_dashboard: pd.DataFrame):
    tabla, kpis = crear_distribucion_severidad_no_cumple(df_dashboard)

    st.markdown("#### Severidad de incumplimiento TAT")
    st.markdown(
        """
        <div class="info-box">
            <div class="info-title">Distribución para registros que no cumplen</div>
            <div class="info-text">
                Esta visualización muestra los registros que <b>no cumplen TAT</b> y en qué rangos de días caen después de exceder el umbral definido.
                Se puede interpretar como <b>severidad del incumplimiento</b>: tardarse más días sobre el umbral significa peor rendimiento.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        mostrar_kpi_html(
            "Registros que no cumplen",
            formatear_entero(kpis["total"]),
            f"De {formatear_entero(kpis['total_evaluables'])} registros evaluables.",
            "kpi-bad",
        )

    with col2:
        mostrar_kpi_html(
            "% No cumplimiento",
            formatear_porcentaje(kpis["pct_no_cumple"]),
            "Porcentaje de registros No cumple sobre evaluables.",
            "kpi-bad",
        )

    with col3:
        mostrar_kpi_html(
            "Promedio días sobre umbral",
            f"{kpis['promedio_dias_sobre_umbral']:.1f}",
            "Más días sobre umbral indica peor rendimiento.",
            "kpi-warning",
        )

    with col4:
        mostrar_kpi_html(
            "Promedio días TAT",
            f"{kpis['promedio_dias_tat']:.1f}",
            f"Umbral promedio: {kpis['promedio_umbral']:.1f} días.",
        )

    if tabla.empty:
        st.info("No hay registros No cumple con días TAT y umbral válidos para graficar.")
        return

    col_grafico, col_tabla = st.columns([1.15, 1])

    with col_grafico:
        grafico_barras_distribucion_intuitiva(
            tabla=tabla,
            titulo="Severidad de incumplimiento: días sobre umbral TAT",
            columna_porcentaje="% sobre No cumple",
            color_barra=COLOR_NO_CUMPLE,
            etiqueta_x="Cantidad de registros que no cumplen",
        )

    with col_tabla:
        st.markdown("##### Tabla de severidad de incumplimiento")
        st.dataframe(
            tabla,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cantidad": st.column_config.NumberColumn(
                    "Cantidad",
                    format="%d",
                ),
                "% sobre No cumple": st.column_config.ProgressColumn(
                    "% sobre No cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "Promedio días TAT": st.column_config.NumberColumn(
                    "Promedio días TAT",
                    format="%.2f",
                ),
                "Promedio umbral": st.column_config.NumberColumn(
                    "Promedio umbral",
                    format="%.2f",
                ),
                "Promedio días sobre umbral": st.column_config.NumberColumn(
                    "Promedio días sobre umbral",
                    format="%.2f",
                ),
            },
        )


# ============================================================
# Gráficos mensuales
# ============================================================

def grafico_mensual_barras_evaluables(
    tabla: pd.DataFrame,
    titulo: str = "Volumen mensual de registros evaluables",
):
    if tabla.empty:
        st.info("No hay datos para el gráfico mensual.")
        return

    labels = tabla["periodo_label"].astype(str).tolist()
    x = np.arange(len(labels))

    cumple = (
        pd.to_numeric(tabla["Cumple"], errors="coerce")
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    no_cumple = (
        pd.to_numeric(tabla["No cumple"], errors="coerce")
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    evaluables = (
        pd.to_numeric(tabla["Evaluables"], errors="coerce")
        .fillna(0)
        .astype(int)
        .to_numpy()
    )

    ancho_figura = max(12, min(22, len(labels) * 0.9))

    fig, ax = plt.subplots(figsize=(ancho_figura, 6.8), dpi=180)

    ax.bar(
        x,
        cumple,
        color=COLOR_CUMPLE,
        width=0.62,
        label="Cumple",
    )

    ax.bar(
        x,
        no_cumple,
        bottom=cumple,
        color=COLOR_NO_CUMPLE,
        width=0.62,
        label="No cumple",
    )

    max_evaluables = max(evaluables) if len(evaluables) else 0

    ax.set_ylim(0, max(max_evaluables * 1.22, 10))

    for i, total in enumerate(evaluables):
        if total > 0:
            ax.text(
                i,
                total + max(max_evaluables * 0.025, 1),
                f"{total:,}".replace(",", "."),
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color=COLOR_TEXTO,
            )

    ax.set_title(
        titulo,
        fontsize=17,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=18,
    )

    ax.set_ylabel("Cantidad de registros evaluables", color=COLOR_TEXTO)

    ax.set_xticks(x)
    ax.set_xticklabels(
        labels,
        rotation=45,
        ha="right",
        fontsize=9,
        color=COLOR_MUTED,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=2,
        frameon=False,
        fontsize=10,
    )

    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0)
    ax.set_facecolor("none")
    fig.patch.set_alpha(0)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.30)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_mensual_linea_cumplimiento(
    tabla: pd.DataFrame,
    titulo: str = "Evolución mensual del cumplimiento TAT",
):
    if tabla.empty:
        st.info("No hay datos para el gráfico mensual.")
        return

    labels = tabla["periodo_label"].astype(str).tolist()
    x = np.arange(len(labels))

    pct_cumple = (
        pd.to_numeric(tabla["% Cumple evaluables"], errors="coerce")
        .fillna(0)
        .to_numpy()
    )

    pct_no_cumple = (
        pd.to_numeric(tabla["% No cumple evaluables"], errors="coerce")
        .fillna(0)
        .to_numpy()
    )

    ancho_figura = max(12, min(22, len(labels) * 0.9))

    fig, ax = plt.subplots(figsize=(ancho_figura, 6.6), dpi=180)

    ax.plot(
        x,
        pct_cumple,
        color=COLOR_CUMPLE,
        marker="o",
        linewidth=3,
        label="% Cumple TAT",
    )

    ax.plot(
        x,
        pct_no_cumple,
        color=COLOR_NO_CUMPLE,
        marker="o",
        linewidth=2.5,
        label="% No cumple TAT",
    )

    ax.axhline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle="--",
        linewidth=2.5,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    total_puntos = len(x)

    if total_puntos <= 12:
        paso_etiqueta = 1
    elif total_puntos <= 24:
        paso_etiqueta = 2
    else:
        paso_etiqueta = 3

    for i, valor in enumerate(pct_cumple):
        if i % paso_etiqueta == 0 or i == total_puntos - 1:
            ax.text(
                i,
                min(valor + 3, 104),
                f"{valor:.0f}%",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color=COLOR_CUMPLE,
            )

    ax.set_ylim(0, 108)

    ax.set_title(
        titulo,
        fontsize=17,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=18,
    )

    ax.set_ylabel("% sobre registros evaluables", color=COLOR_TEXTO)

    ax.set_xticks(x)
    ax.set_xticklabels(
        labels,
        rotation=45,
        ha="right",
        fontsize=9,
        color=COLOR_MUTED,
    )

    ax.set_yticks([0, 25, 50, 65, 75, 100])
    ax.set_yticklabels(
        ["0%", "25%", "50%", "65%", "75%", "100%"],
        color=COLOR_MUTED,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=3,
        frameon=False,
        fontsize=10,
    )

    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0)
    ax.set_facecolor("none")
    fig.patch.set_alpha(0)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.30)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def preparar_ranking_mensual(tabla: pd.DataFrame) -> pd.DataFrame:
    if tabla.empty:
        return pd.DataFrame()

    ranking = tabla[tabla["Evaluables"].gt(0)].copy()

    if ranking.empty:
        return pd.DataFrame()

    ranking = ranking.sort_values(
        ["% Cumple evaluables", "Evaluables"],
        ascending=[False, False],
    ).reset_index(drop=True)

    ranking.insert(0, "Ranking", ranking.index + 1)

    columnas = [
        "Ranking",
        "periodo_label",
        "Cumple",
        "No cumple",
        "Evaluables",
        "% Cumple evaluables",
        "% No cumple evaluables",
        "% Evaluables",
        "Total registros",
    ]

    columnas = [
        col for col in columnas
        if col in ranking.columns
    ]

    ranking = ranking[columnas].copy()

    ranking = ranking.rename(
        columns={
            "periodo_label": "Mes",
            "% Cumple evaluables": "% Cumplimiento TAT",
            "% No cumple evaluables": "% No cumplimiento TAT",
            "% Evaluables": "% Evaluables sobre total",
        }
    )

    return ranking


def grafico_ranking_mensual(tabla_ranking: pd.DataFrame):
    if tabla_ranking.empty:
        st.info("No hay datos para generar el ranking mensual.")
        return

    ranking = tabla_ranking.copy()

    ranking = ranking.sort_values(
        "% Cumplimiento TAT",
        ascending=True,
    )

    labels = ranking["Mes"].astype(str).tolist()

    valores = (
        pd.to_numeric(ranking["% Cumplimiento TAT"], errors="coerce")
        .fillna(0)
        .to_numpy()
    )

    y = np.arange(len(labels))

    alto_figura = max(6, min(18, len(labels) * 0.42))

    fig, ax = plt.subplots(figsize=(12, alto_figura), dpi=180)

    barras = ax.barh(
        y,
        valores,
        color=COLOR_CUMPLE,
        height=0.62,
    )

    ax.axvline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle="--",
        linewidth=2,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    for barra, valor in zip(barras, valores):
        ax.text(
            min(valor + 1.5, 103),
            barra.get_y() + barra.get_height() / 2,
            f"{valor:.1f}%",
            ha="left",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_xlim(0, 108)

    ax.set_yticks(y)
    ax.set_yticklabels(
        labels,
        fontsize=9,
        color=COLOR_MUTED,
    )

    ax.set_xticks([0, 25, 50, 65, 75, 100])
    ax.set_xticklabels(
        ["0%", "25%", "50%", "65%", "75%", "100%"],
        color=COLOR_MUTED,
    )

    ax.set_xlabel("% Cumplimiento TAT", color=COLOR_TEXTO)

    ax.set_title(
        "Ranking mensual de cumplimiento TAT",
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=16,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        ncol=1,
        frameon=False,
        fontsize=10,
    )

    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0)
    ax.set_facecolor("none")
    fig.patch.set_alpha(0)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.16)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


# ============================================================
# Gráfico unificado por etapa
# ============================================================

def grafico_etapas_unificado(resumen_etapas_df: pd.DataFrame):
    if resumen_etapas_df.empty:
        st.info("No hay datos de etapas para graficar.")
        return

    data = resumen_etapas_df.copy()

    data = data.sort_values(
        "% Cumple",
        ascending=True,
    )

    labels = data["Etapa"].astype(str).tolist()

    pct_cumple = (
        pd.to_numeric(data["% Cumple"], errors="coerce")
        .fillna(0)
        .to_numpy()
    )

    pct_no_cumple = (
        pd.to_numeric(data["% No cumple"], errors="coerce")
        .fillna(0)
        .to_numpy()
    )

    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(12, 5.8), dpi=180)

    ax.barh(
        y,
        pct_cumple,
        color=COLOR_CUMPLE,
        height=0.58,
        label="% Cumple",
    )

    ax.barh(
        y,
        pct_no_cumple,
        left=pct_cumple,
        color=COLOR_NO_CUMPLE,
        height=0.58,
        label="% No cumple",
    )

    ax.axvline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle="--",
        linewidth=2,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    for i, valor in enumerate(pct_cumple):
        ax.text(
            min(valor + 1.5, 97),
            i,
            f"{valor:.1f}%",
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_xlim(0, 108)

    ax.set_yticks(y)
    ax.set_yticklabels(
        labels,
        fontsize=10,
        color=COLOR_MUTED,
    )

    ax.set_xticks([0, 25, 50, 65, 75, 100])
    ax.set_xticklabels(
        ["0%", "25%", "50%", "65%", "75%", "100%"],
        color=COLOR_MUTED,
    )

    ax.set_xlabel("% sobre registros evaluables por etapa", color=COLOR_TEXTO)

    ax.set_title(
        "Cumplimiento por etapa",
        fontsize=17,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=18,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.13),
        ncol=3,
        frameon=False,
        fontsize=10,
    )

    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0)
    ax.set_facecolor("none")
    fig.patch.set_alpha(0)

    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


# ============================================================
# Exportación
# ============================================================

def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow",
    )

    return output.getvalue()


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


def generar_nombre_excel_mes(periodo_archivo: str, sufijo: str) -> str:
    fecha_descarga = datetime.now().strftime("%Y%m%d_%H%M%S")
    sufijo_limpio = (
        str(sufijo)
        .upper()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )

    return f"08_PERFORMANCE_TAT_{periodo_archivo}_{sufijo_limpio}_{fecha_descarga}.xlsx"


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


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

st.title("08_PERFORMANCE_PLANTA_MENSUAL")
st.caption(
    "Performance TAT mensual enfocada en cumplimiento real: Cumple vs No cumple sobre registros evaluables."
)

if "df_tat" not in st.session_state or st.session_state.get("df_tat") is None:
    st.info("Primero debes cargar un archivo activo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

try:
    with st.spinner("Preparando base TAT..."):
        df_final = preparar_base_tat(df_original)

except Exception as e:
    st.error("No se pudo preparar la base para Performance TAT mensual.")
    st.exception(e)
    st.stop()


# ============================================================
# Filtros
# ============================================================

st.markdown("### Filtros")
st.caption(
    "E002 queda seleccionado por defecto si existe. Puedes agregar o quitar centros antes de aplicar."
)

col_centro = obtener_columna_centro(df_final)

fechas_validas = df_final[COL_FECHA_RECEPCION_FINAL].dropna()

fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

sistemas = (
    sorted(df_final["sistema"].dropna().astype(str).unique().tolist())
    if "sistema" in df_final.columns
    else []
)

centros = (
    sorted(
        df_final[col_centro]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    if col_centro is not None
    else []
)

centros_default = ["E002"] if "E002" in centros else centros

perf_options = [
    "Cumple",
    "No cumple",
    "En proceso",
    "No aplica",
    "Sin datos",
]

perf_existentes = (
    [
        x for x in perf_options
        if x in df_final["performance_tat_total"].astype(str).unique()
    ]
    if "performance_tat_total" in df_final.columns
    else []
)

with st.form("form_filtros_performance_mensual"):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        if fecha_min is not None and fecha_max is not None:
            rango_fechas = st.date_input(
                "Fecha recepción",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                key="mensual_rango_fechas",
            )
        else:
            rango_fechas = None
            st.warning("No hay fechas válidas de recepción.")

    with col_f2:
        sistemas_sel = st.multiselect(
            "Sistema",
            options=sistemas,
            default=sistemas,
            key="mensual_sistemas",
        )

    with col_f3:
        centros_sel = st.multiselect(
            "Centro / Planta",
            options=centros,
            default=centros_default,
            key="mensual_centros",
        )

    with col_f4:
        perf_sel = st.multiselect(
            "Performance TAT",
            options=perf_existentes,
            default=perf_existentes,
            key="mensual_performance",
        )

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        aplicar_filtros = st.form_submit_button(
            "Aplicar filtros",
            use_container_width=True,
            type="primary",
        )

    with col_b2:
        limpiar_filtros = st.form_submit_button(
            "Limpiar filtros",
            use_container_width=True,
        )


if limpiar_filtros:
    claves = [
        "mensual_rango_fechas",
        "mensual_sistemas",
        "mensual_centros",
        "mensual_performance",
        "mensual_df_filtrado",
        "mensual_resumen_filtros",
        "mensual_firma_filtros",
        "mensual_parquet_bytes",
        "mensual_parquet_firma",
        "mensual_csv_bytes",
        "mensual_csv_firma",
        "mensual_excel_mes_completo_bytes",
        "mensual_excel_mes_completo_firma",
        "mensual_excel_mes_completo_nombre",
        "mensual_excel_mes_cumple_bytes",
        "mensual_excel_mes_cumple_firma",
        "mensual_excel_mes_cumple_nombre",
        "mensual_excel_mes_no_cumple_bytes",
        "mensual_excel_mes_no_cumple_firma",
        "mensual_excel_mes_no_cumple_nombre",
    ]

    for clave in claves:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


if rango_fechas is not None and isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
    fecha_inicio = rango_fechas[0]
    fecha_fin = rango_fechas[1]
else:
    fecha_inicio = None
    fecha_fin = None


firma_filtros = (
    f"{fecha_inicio}_"
    f"{fecha_fin}_"
    f"{','.join(sistemas_sel)}_"
    f"{','.join(centros_sel)}_"
    f"{','.join(perf_sel)}_"
    f"{len(df_final)}"
)


if aplicar_filtros:
    with st.spinner("Aplicando filtros..."):
        df_dashboard, resumen_filtros_df = aplicar_filtros_con_progreso(
            df_base=df_final,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            sistemas_sel=sistemas_sel,
            centros_sel=centros_sel,
            perf_sel=perf_sel,
            col_centro=col_centro,
        )

        st.session_state["mensual_df_filtrado"] = df_dashboard
        st.session_state["mensual_resumen_filtros"] = resumen_filtros_df
        st.session_state["mensual_firma_filtros"] = firma_filtros

    st.success("Filtros aplicados correctamente.")

else:
    if (
        st.session_state.get("mensual_df_filtrado") is not None
        and st.session_state.get("mensual_firma_filtros") == firma_filtros
    ):
        df_dashboard = st.session_state["mensual_df_filtrado"].copy()
        resumen_filtros_df = st.session_state["mensual_resumen_filtros"].copy()
    else:
        df_dashboard = df_final.copy()

        if centros_default and col_centro is not None:
            df_dashboard = df_dashboard[
                df_dashboard[col_centro]
                .astype("string")
                .str.strip()
                .isin([str(x).strip() for x in centros_default])
            ].copy()

        if "performance_tat_total" in df_dashboard.columns and perf_existentes:
            df_dashboard = df_dashboard[
                df_dashboard["performance_tat_total"]
                .astype("string")
                .isin(perf_existentes)
            ].copy()

        resumen_filtros_df = pd.DataFrame(
            [
                {
                    "Paso": "Base inicial",
                    "Filtro aplicado": "Filtro por defecto",
                    "Valor": "Centro E002 si existe; Performance todos los estados",
                    "Registros antes": len(df_final),
                    "Registros después": len(df_dashboard),
                    "Registros excluidos": len(df_final) - len(df_dashboard),
                    "% retenido": round(len(df_dashboard) / len(df_final) * 100, 2)
                    if len(df_final)
                    else 0,
                    "% excluido": round((len(df_final) - len(df_dashboard)) / len(df_final) * 100, 2)
                    if len(df_final)
                    else 0,
                }
            ]
        )


# ============================================================
# Indicadores TAT
# ============================================================

kpis = calcular_kpis_tat(
    df_base=df_final,
    df_filtrado=df_dashboard,
)

mostrar_indicadores_tat(kpis)


# ============================================================
# Orden secuencial de gráficos
# ============================================================

st.markdown("### 1. Retención por filtros")
st.caption(
    "Este gráfico muestra cuántos registros ingresaron, cuántos quedaron retenidos y cuántos fueron excluidos por los filtros."
)

col_ret1, col_ret2 = st.columns([1.1, 1])

with col_ret1:
    grafico_donut_retencion(
        total_ingresado=kpis["total_ingresado"],
        total_retenido=kpis["total_retenido"],
    )

with col_ret2:
    st.markdown("#### Resumen filtros")
    resumen_retencion = pd.DataFrame(
        [
            {
                "Métrica": "Registros ingresados",
                "Cantidad": kpis["total_ingresado"],
                "%": 100.0,
            },
            {
                "Métrica": "Registros retenidos",
                "Cantidad": kpis["total_retenido"],
                "%": round(kpis["pct_retenido"], 2),
            },
            {
                "Métrica": "Registros excluidos",
                "Cantidad": kpis["total_excluido"],
                "%": round(kpis["pct_excluido"], 2),
            },
        ]
    )

    st.dataframe(
        resumen_retencion,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Cantidad": st.column_config.NumberColumn(
                "Cantidad",
                format="%d",
            ),
            "%": st.column_config.ProgressColumn(
                "%",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )

with st.expander("Detalle de filtros aplicados", expanded=False):
    mostrar_detalle_filtros_aplicados(resumen_filtros_df)


st.markdown("### 2. Retenidos por Performance TAT")
st.caption(
    "Este gráfico muestra cómo se distribuyen todos los registros retenidos por filtros: "
    "Cumple, No cumple, En proceso, No aplica y Sin datos."
)

desglose_filtrado_df = crear_desglose_filtrado_tat(df_dashboard)

grafico_donut_desglose_filtrado(desglose_filtrado_df)


st.markdown("### 3. TAT sobre registros evaluables")
st.caption(
    "Este gráfico usa como base únicamente los registros evaluables: Cumple + No cumple. "
    "Este es el gráfico principal para interpretar el cumplimiento TAT real."
)

desglose_evaluables_df = crear_desglose_evaluables_tat(df_dashboard)

grafico_donut_evaluables_tat(desglose_evaluables_df)


# ============================================================
# Distribuciones intuitivas debajo de TAT evaluable
# ============================================================

mostrar_bloque_distribucion_cumple(df_dashboard)

mostrar_bloque_distribucion_no_cumple(df_dashboard)


# ============================================================
# Cumplimiento TAT mensual
# ============================================================

st.markdown("### Cumplimiento TAT mensual")
st.caption(
    "Se conserva la vista global completa y se agrega un zoom del último año disponible en los datos filtrados."
)

tabla_mensual = crear_resumen_mensual(df_dashboard)
kpis_mensuales = calcular_kpis_mensuales(tabla_mensual)

tabla_ultimo_anio, ultimo_anio = obtener_tabla_ultimo_anio(tabla_mensual)
kpis_ultimo_anio = calcular_kpis_ultimo_anio(
    tabla_ultimo_anio=tabla_ultimo_anio,
    anio=ultimo_anio,
)

mostrar_indicadores_mensuales(kpis_mensuales)

st.markdown("#### Visión global: volumen mensual de registros evaluables")
st.caption(
    "Este gráfico muestra todos los meses disponibles en los datos filtrados."
)

grafico_mensual_barras_evaluables(
    tabla=tabla_mensual,
    titulo="Visión global: volumen mensual de registros evaluables",
)

if not tabla_ultimo_anio.empty:
    st.markdown(f"#### Zoom último año disponible: volumen mensual {ultimo_anio}")
    st.caption(
        f"Este gráfico muestra únicamente los meses del año {ultimo_anio}, "
        "para facilitar el análisis del período más reciente."
    )

    grafico_mensual_barras_evaluables(
        tabla=tabla_ultimo_anio,
        titulo=f"Zoom {ultimo_anio}: volumen mensual de registros evaluables",
    )
else:
    st.info("No hay datos suficientes para construir el zoom del último año.")


st.markdown("#### Visión global: evolución mensual del cumplimiento TAT")
st.caption(
    "Este gráfico muestra la tendencia completa de % Cumple y % No cumple sobre registros evaluables."
)

grafico_mensual_linea_cumplimiento(
    tabla=tabla_mensual,
    titulo="Visión global: evolución mensual del cumplimiento TAT",
)

if not tabla_ultimo_anio.empty:
    mostrar_indicadores_ultimo_anio(kpis_ultimo_anio)

    st.markdown(f"#### Zoom último año disponible: evolución mensual {ultimo_anio}")
    st.caption(
        f"Este gráfico funciona como un acercamiento al año {ultimo_anio}, "
        "que normalmente es el período de mayor interés para el seguimiento operativo."
    )

    grafico_mensual_linea_cumplimiento(
        tabla=tabla_ultimo_anio,
        titulo=f"Zoom {ultimo_anio}: evolución mensual del cumplimiento TAT",
    )
else:
    st.info("No hay datos suficientes para construir los KPI del último año.")


# ============================================================
# Ranking mensual
# ============================================================

st.markdown("### Ranking mensual de cumplimiento TAT")
st.caption(
    "A diferencia de los gráficos de evolución, aquí sí importa ordenar de mayor a menor cumplimiento."
)

ranking_mensual_df = preparar_ranking_mensual(tabla_mensual)

if ranking_mensual_df.empty:
    st.info("No hay datos evaluables para construir el ranking mensual.")
else:
    grafico_ranking_mensual(ranking_mensual_df)

    st.markdown("#### Tabla ranking mensual")
    st.caption(
        "Ordenada de mayor a menor % Cumplimiento TAT."
    )

    st.dataframe(
        ranking_mensual_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ranking": st.column_config.NumberColumn(
                "Ranking",
                format="%d",
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
            "Total registros": st.column_config.NumberColumn(
                "Total registros",
                format="%d",
            ),
            "% Cumplimiento TAT": st.column_config.ProgressColumn(
                "% Cumplimiento TAT",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "% No cumplimiento TAT": st.column_config.ProgressColumn(
                "% No cumplimiento TAT",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "% Evaluables sobre total": st.column_config.ProgressColumn(
                "% Evaluables sobre total",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )


# ============================================================
# Vista previa y descarga por mes
# ============================================================

st.markdown("### Vista previa y descarga por mes")
st.caption(
    "Selecciona un mes/año para revisar los registros del período. "
    "Además, puedes separar la vista en registros que Cumplen y No cumplen."
)

if tabla_mensual.empty:
    st.info("No hay meses disponibles para seleccionar.")
else:
    meses_disponibles_df = (
        tabla_mensual[["periodo_fecha", "periodo_label"]]
        .dropna()
        .drop_duplicates()
        .sort_values("periodo_fecha")
        .reset_index(drop=True)
    )

    opciones_mes = meses_disponibles_df["periodo_label"].tolist()

    ultimo_mes_label = opciones_mes[-1] if opciones_mes else None

    mes_seleccionado_label = st.selectbox(
        "Selecciona mes/año",
        options=opciones_mes,
        index=opciones_mes.index(ultimo_mes_label) if ultimo_mes_label in opciones_mes else 0,
        key="mensual_selector_mes_descarga",
    )

    periodo_seleccionado = meses_disponibles_df.loc[
        meses_disponibles_df["periodo_label"].eq(mes_seleccionado_label),
        "periodo_fecha",
    ].iloc[0]

    df_mes = df_dashboard[
        df_dashboard["periodo_fecha"].eq(periodo_seleccionado)
    ].copy()

    df_mes_cumple = df_mes[
        df_mes["performance_tat_total"].astype("string").eq("Cumple")
    ].copy()

    df_mes_no_cumple = df_mes[
        df_mes["performance_tat_total"].astype("string").eq("No cumple")
    ].copy()

    total_mes = len(df_mes)
    total_mes_cumple = len(df_mes_cumple)
    total_mes_no_cumple = len(df_mes_no_cumple)

    col_vm1, col_vm2, col_vm3 = st.columns(3)

    col_vm1.metric(
        "Total mes",
        f"{total_mes:,}".replace(",", "."),
    )

    col_vm2.metric(
        "Cumple",
        f"{total_mes_cumple:,}".replace(",", "."),
        f"{(total_mes_cumple / total_mes * 100):.1f}%" if total_mes else "0.0%",
    )

    col_vm3.metric(
        "No cumple",
        f"{total_mes_no_cumple:,}".replace(",", "."),
        f"{(total_mes_no_cumple / total_mes * 100):.1f}%" if total_mes else "0.0%",
    )

    columnas_preferidas_mes = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        col_centro,
        "tipo_oc",
        "origen",
        "sistema",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "dias_tat_total",
        "umbral_tat_total",
        "performance_tat_total",
        "dias_incumplimiento_tat",
        "rango_incumplimiento_tat",
    ]

    columnas_preferidas_mes = [
        col for col in columnas_preferidas_mes
        if col is not None and col in df_mes.columns
    ]

    def mostrar_vista_previa_mes(
        df_vista: pd.DataFrame,
        nombre_vista: str,
        key_prefix: str,
    ):
        total_vista = len(df_vista)

        if total_vista == 0:
            st.info(f"No hay registros para la vista: {nombre_vista}.")
            return

        max_preview = min(1000, max(total_vista, 1))

        filas_preview = st.number_input(
            f"Filas a visualizar - {nombre_vista}",
            min_value=1,
            max_value=max_preview,
            value=min(300, max_preview),
            step=50 if max_preview >= 50 else 1,
            key=f"{key_prefix}_filas_preview",
        )

        st.info(
            f"Se están visualizando **{min(int(filas_preview), total_vista):,} registros** "
            f"de un total de **{total_vista:,} registros** para **{nombre_vista}** en **{mes_seleccionado_label}**."
            .replace(",", ".")
        )

        if columnas_preferidas_mes:
            columnas_disponibles = [
                col for col in columnas_preferidas_mes
                if col in df_vista.columns
            ]

            st.dataframe(
                df_vista[columnas_disponibles].head(int(filas_preview)),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(
                df_vista.head(int(filas_preview)),
                use_container_width=True,
                hide_index=True,
            )

    tab_general, tab_cumple, tab_no_cumple = st.tabs(
        [
            "Vista mes completo",
            "Vista Cumple",
            "Vista No cumple",
        ]
    )

    with tab_general:
        mostrar_vista_previa_mes(
            df_vista=df_mes,
            nombre_vista="Mes completo",
            key_prefix="mensual_mes_completo",
        )

    with tab_cumple:
        mostrar_vista_previa_mes(
            df_vista=df_mes_cumple,
            nombre_vista="Cumple",
            key_prefix="mensual_mes_cumple",
        )

    with tab_no_cumple:
        mostrar_vista_previa_mes(
            df_vista=df_mes_no_cumple,
            nombre_vista="No cumple",
            key_prefix="mensual_mes_no_cumple",
        )

    periodo_archivo = pd.Timestamp(periodo_seleccionado).strftime("%Y%m")

    firma_mes_completo = f"{periodo_archivo}_{len(df_mes)}_COMPLETO"
    firma_mes_cumple = f"{periodo_archivo}_{len(df_mes_cumple)}_CUMPLE"
    firma_mes_no_cumple = f"{periodo_archivo}_{len(df_mes_no_cumple)}_NO_CUMPLE"

    st.markdown("#### Descargas Excel del mes seleccionado")

    col_x1, col_x2, col_x3 = st.columns(3)

    with col_x1:
        preparar_excel_completo = st.button(
            "Preparar Excel mes completo",
            use_container_width=True,
            key="mensual_preparar_excel_mes_completo",
        )

        if preparar_excel_completo:
            nombre_excel = generar_nombre_excel_mes(
                periodo_archivo=periodo_archivo,
                sufijo="MES_COMPLETO",
            )

            with st.spinner("Preparando Excel del mes completo..."):
                st.session_state["mensual_excel_mes_completo_bytes"] = convertir_a_excel_cache(df_mes)
                st.session_state["mensual_excel_mes_completo_firma"] = firma_mes_completo
                st.session_state["mensual_excel_mes_completo_nombre"] = nombre_excel

        if (
            st.session_state.get("mensual_excel_mes_completo_bytes") is not None
            and st.session_state.get("mensual_excel_mes_completo_firma") == firma_mes_completo
        ):
            st.download_button(
                label="Descargar mes completo",
                data=st.session_state["mensual_excel_mes_completo_bytes"],
                file_name=st.session_state["mensual_excel_mes_completo_nombre"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

    with col_x2:
        preparar_excel_cumple = st.button(
            "Preparar Excel Cumple",
            use_container_width=True,
            key="mensual_preparar_excel_mes_cumple",
        )

        if preparar_excel_cumple:
            nombre_excel = generar_nombre_excel_mes(
                periodo_archivo=periodo_archivo,
                sufijo="CUMPLE",
            )

            with st.spinner("Preparando Excel de registros Cumple..."):
                st.session_state["mensual_excel_mes_cumple_bytes"] = convertir_a_excel_cache(df_mes_cumple)
                st.session_state["mensual_excel_mes_cumple_firma"] = firma_mes_cumple
                st.session_state["mensual_excel_mes_cumple_nombre"] = nombre_excel

        if (
            st.session_state.get("mensual_excel_mes_cumple_bytes") is not None
            and st.session_state.get("mensual_excel_mes_cumple_firma") == firma_mes_cumple
        ):
            st.download_button(
                label="Descargar Cumple",
                data=st.session_state["mensual_excel_mes_cumple_bytes"],
                file_name=st.session_state["mensual_excel_mes_cumple_nombre"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with col_x3:
        preparar_excel_no_cumple = st.button(
            "Preparar Excel No cumple",
            use_container_width=True,
            key="mensual_preparar_excel_mes_no_cumple",
        )

        if preparar_excel_no_cumple:
            nombre_excel = generar_nombre_excel_mes(
                periodo_archivo=periodo_archivo,
                sufijo="NO_CUMPLE",
            )

            with st.spinner("Preparando Excel de registros No cumple..."):
                st.session_state["mensual_excel_mes_no_cumple_bytes"] = convertir_a_excel_cache(df_mes_no_cumple)
                st.session_state["mensual_excel_mes_no_cumple_firma"] = firma_mes_no_cumple
                st.session_state["mensual_excel_mes_no_cumple_nombre"] = nombre_excel

        if (
            st.session_state.get("mensual_excel_mes_no_cumple_bytes") is not None
            and st.session_state.get("mensual_excel_mes_no_cumple_firma") == firma_mes_no_cumple
        ):
            st.download_button(
                label="Descargar No cumple",
                data=st.session_state["mensual_excel_mes_no_cumple_bytes"],
                file_name=st.session_state["mensual_excel_mes_no_cumple_nombre"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )


# ============================================================
# Cumplimiento por etapa
# ============================================================

st.markdown("### Cumplimiento por etapa")
st.caption(
    "Visualización consolidada para Lib SolPed, Comprador, Proveedor y Logística."
)

resumen_etapas_df = crear_resumen_etapas(df_dashboard)

if resumen_etapas_df.empty:
    st.info("No hay información de etapas para mostrar.")
else:
    grafico_etapas_unificado(resumen_etapas_df)

    st.markdown("#### Tabla de cumplimiento por etapa")
    st.caption(
        "La tabla incluye barras de progreso para visualizar rápidamente el cumplimiento y no cumplimiento por etapa."
    )

    st.dataframe(
        resumen_etapas_df,
        use_container_width=True,
        hide_index=True,
        column_config={
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
            "Promedio días > 0": st.column_config.NumberColumn(
                "Promedio días > 0",
                format="%.2f",
            ),
            "N promedio": st.column_config.NumberColumn(
                "N promedio",
                format="%d",
            ),
        },
    )


# ============================================================
# Calidad de datos
# ============================================================

with st.expander("Calidad de datos: NaN vs Sin datos", expanded=False):
    mostrar_detalle_nan_sin_datos(df_dashboard)


# ============================================================
# Tabla mensual y datos
# ============================================================

with st.expander("Tabla mensual", expanded=False):
    if tabla_mensual.empty:
        st.info("No hay tabla mensual disponible.")
    else:
        st.dataframe(
            tabla_mensual,
            use_container_width=True,
            hide_index=True,
        )

with st.expander("Vista previa de datos filtrados", expanded=False):
    limite_vista = st.number_input(
        "Filas a mostrar",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
        key="mensual_limite_vista",
    )

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        col_centro,
        "tipo_oc",
        "origen",
        "sistema",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "dias_tat_total",
        "umbral_tat_total",
        "performance_tat_total",
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
# Descarga opcional
# ============================================================

with st.expander("Descargar resultado filtrado", expanded=False):
    st.caption(
        "Parquet es el formato recomendado. CSV se prepara solo cuando lo solicitas."
    )

    firma_export = (
        f"{len(df_dashboard)}_"
        f"{fecha_inicio}_"
        f"{fecha_fin}_"
        f"{','.join(sistemas_sel)}_"
        f"{','.join(centros_sel)}_"
        f"{','.join(perf_sel)}"
    )

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        preparar_parquet = st.button(
            "Preparar Parquet",
            use_container_width=True,
            key="mensual_preparar_parquet",
        )

        if preparar_parquet:
            with st.spinner("Preparando Parquet."):
                st.session_state["mensual_parquet_bytes"] = convertir_a_parquet_cache(df_dashboard)
                st.session_state["mensual_parquet_firma"] = firma_export

        if (
            st.session_state.get("mensual_parquet_bytes") is not None
            and st.session_state.get("mensual_parquet_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Parquet",
                data=st.session_state["mensual_parquet_bytes"],
                file_name="performance_tat_mensual_filtrado.parquet",
                mime="application/octet-stream",
                type="primary",
                use_container_width=True,
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True,
            key="mensual_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV."):
                st.session_state["mensual_csv_bytes"] = convertir_a_csv_cache(df_dashboard)
                st.session_state["mensual_csv_firma"] = firma_export

        if (
            st.session_state.get("mensual_csv_bytes") is not None
            and st.session_state.get("mensual_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV",
                data=st.session_state["mensual_csv_bytes"],
                file_name="performance_tat_mensual_filtrado.csv",
                mime="text/csv",
                use_container_width=True,
            )
