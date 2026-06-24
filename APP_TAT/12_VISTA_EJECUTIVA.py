DEJA COMO PUNTO EL DECIMAL Y LA COMA COMO SEPARADOR DE MILES 

DIME DONDE HAY QUE ACTUALIZAR ESA INFORMACION EN EL CODIGO 

# ============================================================
# 12_VISTA_EJECUTIVA
# Vista ejecutiva de Performance TAT por centro
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Enfoque:
# - Filtro principal por Centro
# - Default: E002 si existe
# - Default: Cumple + No cumple
# - Base de análisis: registros evaluables
# - Visual ejecutivo Matplotlib
# - Cumple = gris oscuro abajo
# - No cumple = rojo arriba
# - Separación por año
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

COLOR_EN_PROCESO = "#F4B400"
COLOR_NO_APLICA = "#9CA3AF"
COLOR_SIN_DATOS = "#D1D5DB"

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
        .block-container {
            padding-top: 4.25rem;
            padding-bottom: 1.2rem;
            max-width: 1380px;
        }

        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            padding: 14px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
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

    if texto in ["nan", "none", "<na>", "null", ""]:
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
# Cálculo de performance
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

    if "tipo_oc" not in df.columns:
        if COL_PEDIDO in df.columns:
            df["tipo_oc"] = df[COL_PEDIDO].apply(extraer_tipo_oc).astype("string")
        elif COL_DOCUMENTO_COMPRAS in df.columns:
            df["tipo_oc"] = df[COL_DOCUMENTO_COMPRAS].apply(extraer_tipo_oc).astype("string")
        else:
            df["tipo_oc"] = pd.NA

    if "origen" not in df.columns:
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

    if "sistema" not in df.columns:
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

    return df_filtrado, pd.DataFrame(resumen)


# ============================================================
# Resúmenes
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


def calcular_kpis_tat(
    df_base: pd.DataFrame,
    df_filtrado: pd.DataFrame,
) -> dict:

    total_ingresado = int(len(df_base))
    total_retenido = int(len(df_filtrado))
    total_excluido = total_ingresado - total_retenido

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

    pct_retenido = total_retenido / total_ingresado * 100 if total_ingresado else 0
    pct_excluido = total_excluido / total_ingresado * 100 if total_ingresado else 0
    pct_evaluables = evaluables / total_retenido * 100 if total_retenido else 0
    pct_no_evaluables = no_evaluables / total_retenido * 100 if total_retenido else 0
    pct_cumple_evaluable = cumple / evaluables * 100 if evaluables else 0
    pct_no_cumple_evaluable = no_cumple / evaluables * 100 if evaluables else 0

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


def calcular_kpis_ultimo_anio(tabla_ultimo_anio: pd.DataFrame, anio: int | None) -> dict:
    if tabla_ultimo_anio.empty or anio is None:
        return {
            "anio": "—",
            "meses": 0,
            "cumple": 0,
            "no_cumple": 0,
            "evaluables": 0,
            "cumplimiento_acumulado": 0,
            "no_cumplimiento_acumulado": 0,
            "promedio_cumplimiento_mensual": 0,
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

    cumplimiento_acumulado = cumple_total / evaluables_total * 100 if evaluables_total else 0
    no_cumplimiento_acumulado = no_cumple_total / evaluables_total * 100 if evaluables_total else 0

    return {
        "anio": anio,
        "meses": int(len(evaluables_mensuales)),
        "cumple": cumple_total,
        "no_cumple": no_cumple_total,
        "evaluables": evaluables_total,
        "cumplimiento_acumulado": cumplimiento_acumulado,
        "no_cumplimiento_acumulado": no_cumplimiento_acumulado,
        "promedio_cumplimiento_mensual": promedio_cumplimiento,
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
            "desviacion_estandar_dias": 0,
            "coeficiente_variacion_dias": 0,
            "n_promedio": 0,
        }

    temp = df[df[col_perf].isin(["Cumple", "No cumple"])].copy()

    cumple = int(temp[col_perf].eq("Cumple").sum())
    no_cumple = int(temp[col_perf].eq("No cumple").sum())
    evaluables = cumple + no_cumple

    pct_cumple = cumple / evaluables * 100 if evaluables else 0
    pct_no_cumple = no_cumple / evaluables * 100 if evaluables else 0

    if col_dias in temp.columns:
        dias = pd.to_numeric(temp[col_dias], errors="coerce")
        dias = dias[dias > 0]

        promedio = float(dias.mean()) if not dias.empty else 0
        desviacion_estandar = float(dias.std(ddof=1)) if len(dias) > 1 else 0
        coeficiente_variacion = (
            desviacion_estandar / promedio * 100
            if promedio != 0
            else 0
        )
        n_promedio = int(len(dias))
    else:
        promedio = 0
        desviacion_estandar = 0
        coeficiente_variacion = 0
        n_promedio = 0

    return {
        "cumple": cumple,
        "no_cumple": no_cumple,
        "evaluables": evaluables,
        "pct_cumple": pct_cumple,
        "pct_no_cumple": pct_no_cumple,
        "promedio_dias": promedio,
        "desviacion_estandar_dias": desviacion_estandar,
        "coeficiente_variacion_dias": coeficiente_variacion,
        "n_promedio": n_promedio,
    }


# ============================================================
# Visuales ejecutivos
# ============================================================

def titulo_vista_ejecutiva(nombre_archivo: str):
    st.markdown(
        f"""
        <div class="exec-header">
            <div>
                <div class="exec-title">12_VISTA_EJECUTIVA · Performance TAT</div>
                <div class="exec-subtitle">
                    Vista ejecutiva por centro, enfocada en registros evaluables: Cumple y No cumple.
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


def grafico_performance_matplotlib(
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

    cumple_pct = pd.to_numeric(data["% Cumple evaluables"], errors="coerce").fillna(0).to_numpy()
    no_cumple_pct = pd.to_numeric(data["% No cumple evaluables"], errors="coerce").fillna(0).to_numpy()

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


def mostrar_evolucion_por_anio_matplotlib(tabla_mensual: pd.DataFrame):
    st.markdown(
        "<div class='exec-section-title'>Evolución mensual ejecutiva por año</div>",
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

            grafico_performance_matplotlib(
                data_anio,
                titulo=f"Performance TAT {anio}",
            )

            with st.expander(f"Tabla mensual {anio}", expanded=False):
                columnas = [
                    "periodo_label",
                    "Cumple",
                    "No cumple",
                    "Evaluables",
                    "% Cumple evaluables",
                    "% No cumple evaluables",
                ]

                columnas = [c for c in columnas if c in data_anio.columns]

                st.dataframe(
                    data_anio[columnas],
                    use_container_width=True,
                    hide_index=True,
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

    periodos = periodos.sort_values("periodo_fecha", ascending=False).reset_index(drop=True)

    return periodos


def mostrar_detalle_mes_ejecutivo(
    df_dashboard: pd.DataFrame,
    tabla_mensual: pd.DataFrame,
    col_centro: str | None,
):
    st.markdown(
        "<div class='exec-section-title'>Detalle mensual</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='exec-small'>
            Por defecto se muestra el último mes disponible. Puedes cambiar el mes para revisar el detalle.
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
        key="ejecutiva_mes_detalle",
    )

    fila_mes = periodos[periodos["periodo_label"].astype(str).eq(mes_sel)].iloc[0]
    periodo_sel = pd.Timestamp(fila_mes["periodo_fecha"])

    df_mes = df_dashboard[
        df_dashboard["periodo_fecha"].eq(periodo_sel)
    ].copy()

    if df_mes.empty:
        st.info("No hay registros para el mes seleccionado.")
        return

    estado_mes = df_mes["performance_tat_total"].apply(normalizar_estado_performance)

    cumple_mes = int(estado_mes.eq("Cumple").sum())
    no_cumple_mes = int(estado_mes.eq("No cumple").sum())
    evaluables_mes = cumple_mes + no_cumple_mes

    pct_cumple_mes = cumple_mes / evaluables_mes * 100 if evaluables_mes else 0
    pct_no_cumple_mes = no_cumple_mes / evaluables_mes * 100 if evaluables_mes else 0

    if "dias_tat_total" in df_mes.columns:
        dias_tat = pd.to_numeric(df_mes["dias_tat_total"], errors="coerce")
        promedio_dias_tat = dias_tat[dias_tat.ge(0)].mean() if not dias_tat.empty else 0
    else:
        promedio_dias_tat = 0

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)

    with col_m1:
        mostrar_kpi_ejecutivo(
            "Mes seleccionado",
            mes_sel,
            "Detalle de registros evaluables del mes.",
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
            f"No cumplimiento: {formatear_porcentaje(pct_no_cumple_mes)}.",
        )

    with col_m4:
        mostrar_kpi_ejecutivo(
            "Promedio días TAT",
            formatear_entero(promedio_dias_tat),
            "Promedio de días TAT del mes seleccionado.",
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
        if col is not None and col in df_mes.columns
    ]

    st.dataframe(
        df_mes[columnas_preferidas] if columnas_preferidas else df_mes,
        use_container_width=True,
        hide_index=True,
    )

    col_desc1, col_desc2, col_desc3 = st.columns(3)

    periodo_archivo = periodo_sel.strftime("%Y_%m")

    with col_desc1:
        excel_mes = convertir_a_excel_cache(df_mes)

        st.download_button(
            label="Descargar mes seleccionado",
            data=excel_mes,
            file_name=f"12_VISTA_EJECUTIVA_{periodo_archivo}_DETALLE.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )

    with col_desc2:
        df_mes_cumple = df_mes[
            df_mes["performance_tat_total"].apply(normalizar_estado_performance).eq("Cumple")
        ].copy()

        excel_mes_cumple = convertir_a_excel_cache(df_mes_cumple)

        st.download_button(
            label="Descargar Cumple",
            data=excel_mes_cumple,
            file_name=f"12_VISTA_EJECUTIVA_{periodo_archivo}_CUMPLE.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with col_desc3:
        df_mes_no_cumple = df_mes[
            df_mes["performance_tat_total"].apply(normalizar_estado_performance).eq("No cumple")
        ].copy()

        excel_mes_no_cumple = convertir_a_excel_cache(df_mes_no_cumple)

        st.download_button(
            label="Descargar No cumple",
            data=excel_mes_no_cumple,
            file_name=f"12_VISTA_EJECUTIVA_{periodo_archivo}_NO_CUMPLE.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def grafico_donut_etapa_ejecutiva(etapa: dict, datos: dict):
    cumple = int(datos.get("cumple", 0))
    no_cumple = int(datos.get("no_cumple", 0))
    total = cumple + no_cumple

    st.markdown(f"##### Cumplimiento {etapa['titulo']}")

    if total <= 0:
        st.info("Sin evaluables")
        return

    valores = [cumple, no_cumple]
    colores = [COLOR_CUMPLE, COLOR_NO_CUMPLE]

    pct_cumple = cumple / total * 100
    pct_no_cumple = no_cumple / total * 100

    fig, ax = plt.subplots(figsize=(3.05, 2.25), dpi=180)

    ax.pie(
        valores,
        startangle=90,
        counterclock=False,
        colors=colores,
        labels=None,
        wedgeprops={
            "width": 0.42,
            "edgecolor": "white",
            "linewidth": 1.4,
        },
    )

    ax.text(
        1.05,
        -0.55,
        f"Cumple\n{pct_cumple:.0f}%",
        ha="left",
        va="center",
        fontsize=7.0,
        color=COLOR_TEXTO,
    )

    ax.text(
        -1.05,
        0.78,
        f"No cumple\n{pct_no_cumple:.0f}%",
        ha="right",
        va="center",
        fontsize=7.0,
        color=COLOR_TEXTO,
    )

    legend_handles = [
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            label="Cumple",
            markerfacecolor=COLOR_CUMPLE,
            markeredgecolor=COLOR_CUMPLE,
            markersize=5,
        ),
        plt.Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            label="No cumple",
            markerfacecolor=COLOR_NO_CUMPLE,
            markeredgecolor=COLOR_NO_CUMPLE,
            markersize=5,
        ),
    ]

    ax.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.24),
        ncol=2,
        frameon=False,
        fontsize=7.0,
        handlelength=0.8,
        handletextpad=0.3,
        columnspacing=0.8,
    )

    ax.axis("equal")
    fig.patch.set_alpha(0)
    fig.tight_layout(pad=0.15)
    fig.subplots_adjust(bottom=0.22)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)

    promedio = datos.get("promedio_dias", 0)
    desviacion_estandar = datos.get("desviacion_estandar_dias", 0)
    coeficiente_variacion = datos.get("coeficiente_variacion_dias", 0)
    n_promedio = datos.get("n_promedio", 0)

    col_prom_1, col_prom_2, col_prom_3 = st.columns([1, 1.4, 1])

    with col_prom_2:
        st.markdown(f"### {promedio:.0f}")

    st.caption(f"Promedio de Dx {etapa['titulo']}")

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.caption("Desv. estándar")
        st.markdown(f"**{desviacion_estandar:.1f}**")

    with col_s2:
        st.caption("Coef. variación")
        st.markdown(f"**{coeficiente_variacion:.1f}%**")

    st.caption(f"Base promedio: {formatear_entero(n_promedio)} registro(s)")
    st.caption(etapa["regla"])


def mostrar_etapas_ejecutivas(df_dashboard: pd.DataFrame):
    st.markdown("### Cumplimiento por etapa")

    st.caption(
        "Base: registros evaluables filtrados. Cada etapa muestra cumplimiento, "
        "promedio de días, desviación estándar y coeficiente de variación."
    )

    cols = st.columns(4)

    for col, etapa in zip(cols, ETAPAS_DASHBOARD):
        with col:
            datos = datos_etapa(df_dashboard, etapa)
            grafico_donut_etapa_ejecutiva(etapa, datos)


def crear_texto_filtros(
    centros_sel: list,
    sistemas_sel: list,
    fecha_inicio,
    fecha_fin,
    perf_sel: list,
) -> str:

    centros_txt = ", ".join([str(x) for x in centros_sel]) if centros_sel else "Todos"
    sistemas_txt = ", ".join([str(x) for x in sistemas_sel]) if sistemas_sel else "Todos"
    perf_txt = ", ".join([str(x) for x in perf_sel]) if perf_sel else "Todos"
    fechas_txt = f"{fecha_inicio} a {fecha_fin}" if fecha_inicio and fecha_fin else "Todas"

    return (
        f"Centro: {centros_txt} · "
        f"Sistema: {sistemas_txt} · "
        f"Fechas: {fechas_txt} · "
        f"Performance: {perf_txt}"
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
    with st.spinner("Preparando base TAT..."):
        df_final = preparar_base_tat(df_original)

except Exception as e:
    st.error("No se pudo preparar la base para la vista ejecutiva.")
    st.exception(e)
    st.stop()


# ============================================================
# Preparación de filtros
# ============================================================

col_centro = obtener_columna_centro(df_final)

if col_centro is None:
    st.error("No se encontró una columna de Centro para filtrar la vista ejecutiva.")
    st.stop()

fechas_validas = df_final[COL_FECHA_RECEPCION_FINAL].dropna()

fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

sistemas = (
    sorted(df_final["sistema"].dropna().astype(str).unique().tolist())
    if "sistema" in df_final.columns
    else []
)

centros = sorted(
    df_final[col_centro]
    .dropna()
    .astype(str)
    .str.strip()
    .unique()
    .tolist()
)

centros_default = ["E002"] if "E002" in centros else (centros[:1] if centros else [])

perf_options = ["Cumple", "No cumple"]

perf_existentes = (
    [
        x for x in perf_options
        if x in df_final["performance_tat_total"].astype(str).unique()
    ]
    if "performance_tat_total" in df_final.columns
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
    "La vista queda enfocada por defecto en Centro E002 si existe y únicamente en registros evaluables: Cumple + No cumple."
)

with st.form("form_filtros_vista_ejecutiva"):
    col_f1, col_f2, col_f3, col_f4 = st.columns([1.2, 1, 1, 1])

    with col_f1:
        if fecha_min is not None and fecha_max is not None:
            rango_fechas = st.date_input(
                "Fecha recepción",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                key="ejecutiva_rango_fechas",
            )
        else:
            rango_fechas = None
            st.warning("No hay fechas válidas de recepción.")

    with col_f2:
        sistemas_sel = st.multiselect(
            "Sistema",
            options=sistemas,
            default=sistemas,
            key="ejecutiva_sistemas",
        )

    with col_f3:
        centros_sel = st.multiselect(
            "Centro",
            options=centros,
            default=centros_default,
            key="ejecutiva_centros",
        )

    with col_f4:
        perf_sel = st.multiselect(
            "Performance TAT",
            options=perf_options,
            default=perf_default,
            key="ejecutiva_performance",
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
    sistemas_sel=sistemas_sel,
    centros_sel=centros_sel,
    perf_sel=perf_sel,
    col_centro=col_centro,
)

if df_dashboard.empty:
    st.warning("No hay registros con los filtros seleccionados.")
    st.stop()

estado_dashboard = df_dashboard["performance_tat_total"].apply(normalizar_estado_performance)

df_dashboard = df_dashboard[
    estado_dashboard.isin(["Cumple", "No cumple"])
].copy()

if df_dashboard.empty:
    st.warning("No hay registros evaluables con los filtros seleccionados.")
    st.stop()

st.markdown(
    f"""
    <div class='exec-small'>
        {crear_texto_filtros(centros_sel, sistemas_sel, fecha_inicio, fecha_fin, perf_sel)}
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPIs
# ============================================================

tabla_mensual = crear_resumen_mensual(df_dashboard)
tabla_ultimo_anio, ultimo_anio = obtener_tabla_ultimo_anio(tabla_mensual)

kpis = calcular_kpis_tat(df_final, df_dashboard)
kpis_ultimo_anio = calcular_kpis_ultimo_anio(tabla_ultimo_anio, ultimo_anio)

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
        formatear_porcentaje(kpis["pct_cumple_evaluable"]),
        f"Meta ejecutiva: {META_CUMPLIMIENTO}%.",
    )

with col_k3:
    mostrar_kpi_ejecutivo(
        "No cumplimiento TAT",
        formatear_porcentaje(kpis["pct_no_cumple_evaluable"]),
        "Complemento sobre registros evaluables.",
    )

with col_k4:
    mostrar_kpi_ejecutivo(
        "Último año disponible",
        str(kpis_ultimo_anio["anio"]),
        f"Cumplimiento acumulado: {formatear_porcentaje(kpis_ultimo_anio['cumplimiento_acumulado'])}.",
    )


# ============================================================
# Visual 1: Evolución mensual por año
# ============================================================

mostrar_evolucion_por_anio_matplotlib(tabla_mensual)


# ============================================================
# Visual 2: Cumplimiento por etapa
# ============================================================

mostrar_etapas_ejecutivas(df_dashboard)


# ============================================================
# Detalle mensual
# ============================================================

mostrar_detalle_mes_ejecutivo(
    df_dashboard=df_dashboard,
    tabla_mensual=tabla_mensual,
    col_centro=col_centro,
)


# ============================================================
# Detalle mensual consolidado
# ============================================================

with st.expander("Detalle mensual consolidado", expanded=False):
    if tabla_mensual.empty:
        st.info("No hay tabla mensual disponible.")
    else:
        columnas = [
            "periodo_label",
            "Cumple",
            "No cumple",
            "Evaluables",
            "% Cumple evaluables",
            "% No cumple evaluables",
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
                "% Cumple evaluables": st.column_config.ProgressColumn(
                    "% Cumple evaluables",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "% No cumple evaluables": st.column_config.ProgressColumn(
                    "% No cumple evaluables",
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
        key="ejecutiva_limite_vista",
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
# Descarga base filtrada
# ============================================================

with st.expander("Descargar base ejecutiva filtrada", expanded=False):
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
        preparar_excel = st.button(
            "Preparar Excel",
            use_container_width=True,
            key="ejecutiva_preparar_excel",
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                st.session_state["ejecutiva_excel_bytes"] = convertir_a_excel_cache(df_dashboard)
                st.session_state["ejecutiva_excel_firma"] = firma_export

        if (
            st.session_state.get("ejecutiva_excel_bytes") is not None
            and st.session_state.get("ejecutiva_excel_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Excel",
                data=st.session_state["ejecutiva_excel_bytes"],
                file_name="12_VISTA_EJECUTIVA_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True,
            key="ejecutiva_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["ejecutiva_csv_bytes"] = convertir_a_csv_cache(df_dashboard)
                st.session_state["ejecutiva_csv_firma"] = firma_export

        if (
            st.session_state.get("ejecutiva_csv_bytes") is not None
            and st.session_state.get("ejecutiva_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV",
                data=st.session_state["ejecutiva_csv_bytes"],
                file_name="12_VISTA_EJECUTIVA_filtrado.csv",
                mime="text/csv",
                use_container_width=True,
            )
