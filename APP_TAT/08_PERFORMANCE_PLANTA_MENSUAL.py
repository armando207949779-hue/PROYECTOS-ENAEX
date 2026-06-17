# ============================================================
# 08_PERFORMANCE_PLANTA_MENSUAL
# Dashboard mensual de Performance TAT por planta / centro
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

import io
import base64
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# Configuración general
# ============================================================
# Si esta app se ejecuta dentro de st.navigation(), evita usar
# st.set_page_config aquí. Debe estar solo en la app principal.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"

COLOR_CUMPLE = "#606060"
COLOR_NO_CUMPLE = "#EF3E52"
COLOR_SIN_DATOS = "#BFC3C7"
COLOR_META = "#008060"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"

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
# No se modifica .block-container para no afectar el logo.
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

        div[data-testid="stFileUploader"] {
            padding: 10px;
            border-radius: 12px;
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

    columnas_texto = [
        "Estado del match",
        "estado_match",
    ]

    for col in columnas_texto:
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


def formatear_decimal(valor) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return "—"

    return f"{numero:,.1f}"


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

    if texto in ["no aplica", "no aplica al analisis"]:
        return "No aplica"

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
# Resúmenes y gráficos
# ============================================================

def crear_resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    if "performance_tat_total" not in df.columns:
        return pd.DataFrame()

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


def resumen_performance_general(df: pd.DataFrame) -> pd.DataFrame:
    metricas = [
        ("performance_liberacion_solped", "Liberación SolPed"),
        ("performance_comprador", "Comprador"),
        ("performance_liberacion_pedido", "Liberación Pedido"),
        ("performance_proveedor", "Proveedor"),
        ("performance_logistica", "Logística"),
        ("performance_tat_total", "TAT Total"),
    ]

    data = []

    for col, nombre in metricas:
        if col not in df.columns:
            continue

        serie = df[col].astype("object")

        cumple = int(serie.eq("Cumple").sum())
        no_cumple = int(serie.eq("No cumple").sum())
        no_aplica = int(serie.isin(["No aplica", "No aplica al análisis"]).sum())
        sin_datos = int(serie.isin(["Sin datos", "En proceso"]).sum())

        evaluables = cumple + no_cumple
        pct = cumple / evaluables * 100 if evaluables else 0

        data.append(
            {
                "Métrica": nombre,
                "Cumple": cumple,
                "No cumple": no_cumple,
                "No aplica": no_aplica,
                "Sin datos / En proceso": sin_datos,
                "Evaluables": evaluables,
                "% Cumple": round(pct, 2),
            }
        )

    return pd.DataFrame(data)


def datos_etapa(df: pd.DataFrame, etapa: dict) -> dict:
    col_perf = etapa["col_perf"]
    col_dias = etapa["col_dias"]

    if col_perf not in df.columns:
        return {
            "cumple": 0,
            "no_cumple": 0,
            "evaluables": 0,
            "pct_cumple": 0,
            "promedio_dias": 0,
            "n_promedio": 0,
        }

    temp = df[df[col_perf].isin(["Cumple", "No cumple"])].copy()

    cumple = int(temp[col_perf].eq("Cumple").sum())
    no_cumple = int(temp[col_perf].eq("No cumple").sum())
    evaluables = cumple + no_cumple
    pct = cumple / evaluables * 100 if evaluables else 0

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
        "pct_cumple": pct,
        "promedio_dias": promedio,
        "n_promedio": n_promedio,
    }


def grafico_mensual_principal(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay datos evaluables para el gráfico mensual.")
        return

    plot = tabla.melt(
        id_vars=["periodo_fecha", "periodo_label", "Total"],
        value_vars=["Cumple", "No cumple"],
        var_name="Estado",
        value_name="Cantidad",
    )

    plot["Porcentaje"] = np.where(
        plot["Total"] > 0,
        plot["Cantidad"] / plot["Total"] * 100,
        0,
    )

    plot["Estado gráfico"] = plot["Estado"].replace(
        {
            "No cumple": "No Cumple",
        }
    )

    plot["Orden"] = plot["Estado"].map(
        {
            "Cumple": 1,
            "No cumple": 2,
        }
    )

    orden_meses = tabla["periodo_label"].tolist()

    barras = (
        alt.Chart(plot)
        .mark_bar(
            size=42,
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5,
        )
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_meses,
                title=None,
                axis=alt.Axis(
                    labelAngle=0,
                    labelFontSize=12,
                    labelLimit=120,
                ),
            ),
            y=alt.Y(
                "Porcentaje:Q",
                stack="zero",
                title="% sobre TAT evaluables",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(
                    values=[0, 25, 50, 65, 75, 100],
                    labelExpr="datum.value + '%'",
                    grid=True,
                ),
            ),
            color=alt.Color(
                "Estado gráfico:N",
                scale=alt.Scale(
                    domain=["Cumple", "No Cumple"],
                    range=[COLOR_CUMPLE, COLOR_NO_CUMPLE],
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            order=alt.Order("Orden:Q", sort="ascending"),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes"),
                alt.Tooltip("Estado gráfico:N", title="Estado"),
                alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
                alt.Tooltip("Porcentaje:Q", title="Porcentaje", format=".1f"),
                alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f"),
            ],
        )
    )

    labels = (
        alt.Chart(plot[plot["Cantidad"].gt(0)])
        .mark_text(
            color="white",
            fontWeight="bold",
            fontSize=12,
        )
        .encode(
            x=alt.X("periodo_label:N", sort=orden_meses),
            y=alt.Y("Porcentaje:Q", stack="zero"),
            detail="Estado gráfico:N",
            text=alt.Text("Porcentaje:Q", format=".0f"),
            order=alt.Order("Orden:Q", sort="ascending"),
        )
    )

    linea_meta = (
        alt.Chart(pd.DataFrame({"Meta": [META_CUMPLIMIENTO]}))
        .mark_rule(
            color=COLOR_META,
            strokeDash=[6, 4],
            strokeWidth=2.5,
        )
        .encode(
            y=alt.Y("Meta:Q"),
        )
    )

    texto_meta = (
        alt.Chart(pd.DataFrame({"Meta": [META_CUMPLIMIENTO], "x": [orden_meses[0]]}))
        .mark_text(
            align="left",
            dx=5,
            dy=-8,
            color=COLOR_META,
            fontWeight="bold",
            fontSize=12,
            text=f"Meta {META_CUMPLIMIENTO}%",
        )
        .encode(
            x=alt.X("x:N", sort=orden_meses),
            y=alt.Y("Meta:Q"),
        )
    )

    chart = (
        alt.layer(barras, labels, linea_meta, texto_meta)
        .properties(height=430)
        .configure_view(strokeWidth=0)
        .configure_axis(labelColor=COLOR_MUTED, titleColor=COLOR_TEXTO)
        .configure_legend(labelColor=COLOR_MUTED, titleColor=COLOR_TEXTO)
    )

    st.altair_chart(chart, use_container_width=True)


def grafico_linea_mensual(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay datos evaluables para la serie mensual.")
        return

    plot = tabla.copy()

    plot["% Cumple"] = pd.to_numeric(plot["% Cumple"], errors="coerce").fillna(0)
    plot["% No cumple"] = pd.to_numeric(plot["% No cumple"], errors="coerce").fillna(0)

    lineas = plot.melt(
        id_vars=["periodo_fecha", "periodo_label", "Total"],
        value_vars=["% Cumple", "% No cumple"],
        var_name="Indicador",
        value_name="Porcentaje",
    )

    lineas["Indicador"] = (
        lineas["Indicador"]
        .str.replace("% ", "", regex=False)
        .replace({"No cumple": "No Cumple"})
    )

    chart = (
        alt.Chart(lineas)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X(
                "periodo_fecha:T",
                title=None,
                axis=alt.Axis(format="%b %Y", labelAngle=0),
            ),
            y=alt.Y(
                "Porcentaje:Q",
                title="% sobre TAT evaluables",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(labelExpr="datum.value + '%'"),
            ),
            color=alt.Color(
                "Indicador:N",
                scale=alt.Scale(
                    domain=["Cumple", "No Cumple"],
                    range=[COLOR_CUMPLE, COLOR_NO_CUMPLE],
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes"),
                alt.Tooltip("Indicador:N", title="Indicador"),
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
            y="Meta:Q",
        )
    )

    st.altair_chart(
        (chart + linea_meta).properties(height=300).configure_view(strokeWidth=0),
        use_container_width=True,
    )


def grafico_rangos_incumplimiento(df: pd.DataFrame):
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
                alt.Tooltip("Rango:N", title="Rango"),
                alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
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
        (chart + text).properties(height=290).configure_view(strokeWidth=0),
        use_container_width=True,
    )


def grafico_etapas(resumen_etapas: pd.DataFrame):
    if resumen_etapas.empty:
        st.info("No hay información de etapas para graficar.")
        return

    chart = (
        alt.Chart(resumen_etapas)
        .mark_bar(cornerRadius=5)
        .encode(
            x=alt.X(
                "% Cumple:Q",
                title="% Cumple",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(labelExpr="datum.value + '%'"),
            ),
            y=alt.Y("Etapa:N", sort="-x", title=None),
            color=alt.value(COLOR_CUMPLE),
            tooltip=[
                alt.Tooltip("Etapa:N"),
                alt.Tooltip("% Cumple:Q", format=".1f"),
                alt.Tooltip("Evaluables:Q", format=",.0f"),
                alt.Tooltip("Promedio días > 0:Q", format=".1f"),
            ],
        )
    )

    text = (
        chart
        .mark_text(
            align="left",
            dx=5,
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
                "Promedio días > 0": round(datos["promedio_dias"], 2),
                "N promedio": datos["n_promedio"],
            }
        )

    return pd.DataFrame(registros)


def obtener_mejor_peor_mes(tabla: pd.DataFrame):
    if tabla.empty:
        return None, None

    evaluables = tabla[tabla["Total"].gt(0)].copy()

    if evaluables.empty:
        return None, None

    mejor = evaluables.sort_values(
        ["% Cumple", "Total", "periodo_fecha"],
        ascending=[False, False, True],
    ).iloc[0]

    peor = evaluables.sort_values(
        ["% Cumple", "Total", "periodo_fecha"],
        ascending=[True, False, True],
    ).iloc[0]

    return mejor, peor


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


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


# ============================================================
# App
# ============================================================

mostrar_logo()

st.title("08_PERFORMANCE_PLANTA_MENSUAL")
st.caption(
    "Performance TAT mensual con foco en cumplimiento, filtros por centro/planta y análisis de etapas."
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
# Filtros en encabezado
# ============================================================

st.markdown("### Filtros")
st.caption(
    "Selecciona filtros y presiona Aplicar filtros. "
    "El dashboard no recalcula en cada cambio, solo cuando aplicas."
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
            default=centros,
            key="mensual_centros",
        )

    with col_f4:
        perf_default = [
            x for x in ["Cumple", "No cumple"]
            if x in perf_existentes
        ]

        perf_sel = st.multiselect(
            "Performance TAT",
            options=perf_existentes,
            default=perf_default,
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
        resumen_filtros_df = pd.DataFrame(
            [
                {
                    "Paso": "Base inicial",
                    "Filtro aplicado": "Sin filtro",
                    "Valor": "Base completa",
                    "Registros antes": len(df_final),
                    "Registros después": len(df_final),
                    "Registros excluidos": 0,
                    "% retenido": 100.0,
                }
            ]
        )


# ============================================================
# Indicadores principales
# ============================================================

total_inicial = len(df_final)
total_filtrado = len(df_dashboard)

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

en_proceso_tat = (
    int(df_dashboard["performance_tat_total"].eq("En proceso").sum())
    if "performance_tat_total" in df_dashboard.columns
    else 0
)

evaluables_tat = cumple_tat + no_cumple_tat

pct_cumple_tat = cumple_tat / evaluables_tat * 100 if evaluables_tat else 0
pct_no_cumple_tat = no_cumple_tat / evaluables_tat * 100 if evaluables_tat else 0

pct_filtrado = total_filtrado / total_inicial * 100 if total_inicial else 0

col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)

col_k1.metric("Registros base", f"{total_inicial:,}")
col_k2.metric("Registros filtrados", f"{total_filtrado:,}", f"{pct_filtrado:.1f}%")
col_k3.metric("% Cumple TAT", f"{pct_cumple_tat:.1f}%", f"{cumple_tat:,} registros")
col_k4.metric("% No cumple TAT", f"{pct_no_cumple_tat:.1f}%", f"{no_cumple_tat:,} registros")
col_k5.metric("En proceso", f"{en_proceso_tat:,}")


# ============================================================
# Gráfico mensual principal
# ============================================================

st.markdown("### Performance TAT mensual")
st.caption(
    "Gráfico principal del dashboard. Muestra la distribución mensual de cumplimiento TAT sobre registros evaluables."
)

tabla_mensual = crear_resumen_mensual(df_dashboard)

grafico_mensual_principal(tabla_mensual)

mejor_mes, peor_mes = obtener_mejor_peor_mes(tabla_mensual)

if mejor_mes is not None and peor_mes is not None:
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.success(
            f"Mejor mes: {mejor_mes['periodo_label']} · "
            f"{mejor_mes['% Cumple']:.1f}% de cumplimiento "
            f"({int(mejor_mes['Cumple']):,} de {int(mejor_mes['Total']):,} evaluables)."
        )

    with col_m2:
        st.error(
            f"Peor mes: {peor_mes['periodo_label']} · "
            f"{peor_mes['% Cumple']:.1f}% de cumplimiento "
            f"({int(peor_mes['Cumple']):,} de {int(peor_mes['Total']):,} evaluables)."
        )

else:
    st.info("No hay meses evaluables para identificar mejor y peor mes.")


# ============================================================
# Serie temporal secundaria
# ============================================================

with st.expander("Serie temporal mensual", expanded=False):
    grafico_linea_mensual(tabla_mensual)


# ============================================================
# Etapas del proceso
# ============================================================

st.markdown("### Cumplimiento por etapa")
st.caption("Resumen de cumplimiento por etapa del TAT usando estados Cumple / No cumple.")

resumen_etapas_df = crear_resumen_etapas(df_dashboard)

col_e1, col_e2 = st.columns([1.3, 1])

with col_e1:
    grafico_etapas(resumen_etapas_df)

with col_e2:
    st.dataframe(
        resumen_etapas_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Incumplimiento TAT
# ============================================================

st.markdown("### Incumplimiento TAT")
st.caption("Distribución de los rangos de incumplimiento del TAT total.")

grafico_rangos_incumplimiento(df_dashboard)


# ============================================================
# Auditoría y trazabilidad
# ============================================================

with st.expander("Auditoría de filtros aplicados", expanded=False):
    st.dataframe(
        resumen_filtros_df,
        use_container_width=True,
        hide_index=True,
    )

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
        "Parquet es el formato recomendado. CSV se prepara solo cuando lo solicitas. Excel eliminado."
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
            with st.spinner("Preparando Parquet..."):
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
            with st.spinner("Preparando CSV..."):
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
