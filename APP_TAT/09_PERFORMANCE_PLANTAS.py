# ============================================================
# 09_PERFORMANCE_PLANTAS
# Dashboard Performance TAT por Prillex, Rio Loa y Plantas de servicios
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Mejoras aplicadas desde 08_PERFORMANCE_PLANTA_MENSUAL:
# - KPI Indicators más claros
# - Retención por filtros
# - Donut de Performance TAT
# - Cumplimiento por planta con tabla y gráfico
# - Evolución mensual comparativa por planta
# - Zoom del último año disponible
# - KPI Indicators del último año por planta
# - Ranking por centro con barras
# - Vista previa y descarga por mes, grupo y estado
# - Mantiene detalle semanal con filtro
# ============================================================

import io
import base64
from datetime import date, datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
# Si esta app se ejecuta dentro de st.navigation(),
# NO uses st.set_page_config aquí.
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

COLOR_PRILLEX = "#EF3E52"
COLOR_RIO_LOA = "#0057B8"
COLOR_SERVICIOS = "#F59E0B"

META_CUMPLIMIENTO = 65

FECHA_FILTRO_FACTURACION_DEFAULT = pd.Timestamp("2024-02-01")

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

COL_PERFORMANCE_TAT = "performance_tat_total"

COL_CENTRO_ME5A = "Centro - ME5A"
COL_CENTRO_ME80FN = "Centro - ME80FN"
COL_CENTRO_SIMPLE = "Centro"

COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - ME80FN"

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
    "ariba_fecha_solicitud_compra",
    "ariba_fecha_aprobacion",
    "nme_fecha_entrada",
    "nme_fecha_documento",
    "nme_fecha_contabiliz",
    "nme_fecha_facturacion_proveedor",
    "nme_fecha_entrada_mercancia_recepcion",
]

CENTROS_EXCLUIR_PLANTAS_SERVICIOS = [
    "E001",
    "E002",
    "E009",
    "E024",
    "E021",
]

# ============================================================
# IMPORTANTE:
# Conserva aquí tu CENTROS_MAESTRO completo original.
# Puedes pegar exactamente el mismo listado que ya tienes en tu 09.
# ============================================================

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
    {"Centro": "E037", "Sociedad": "EC06", "Nombre": "RT"},
    {"Centro": "E038", "Sociedad": "EC06", "Nombre": "El Soldado"},
    {"Centro": "E039", "Sociedad": "EC06", "Nombre": "Polpaico"},
    {"Centro": "E040", "Sociedad": "EC06", "Nombre": "Peldehue"},
    {"Centro": "E041", "Sociedad": "EC06", "Nombre": "Esperanza"},
    {"Centro": "E042", "Sociedad": "EC06", "Nombre": "Gaby"},
    {"Centro": "E044", "Sociedad": "EC06", "Nombre": "Atacama Kozan"},
    {"Centro": "E045", "Sociedad": "EC06", "Nombre": "Franke"},
    {"Centro": "E046", "Sociedad": "EC06", "Nombre": "Manto Verde"},
    {"Centro": "E047", "Sociedad": "EC06", "Nombre": "Polvorín Copiapó"},
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
    {"Centro": "E103", "Sociedad": "EC06", "Nombre": "Zaldívar"},
    {"Centro": "E104", "Sociedad": "EC06", "Nombre": "Salares Norte"},
    {"Centro": "E105", "Sociedad": "EC06", "Nombre": "Los Colorados"},
    {"Centro": "E106", "Sociedad": "EC06", "Nombre": "Cerro N.N"},
    {"Centro": "E107", "Sociedad": "EC06", "Nombre": "Pleito"},
    {"Centro": "E108", "Sociedad": "EC06", "Nombre": "Plasma Enaex Servicios"},
    {"Centro": "E109", "Sociedad": "EC06", "Nombre": "Carola"},
    {"Centro": "E110", "Sociedad": "EC06", "Nombre": "Alto Hospicio SKC Enaex Serv"},
    {"Centro": "E113", "Sociedad": "EC06", "Nombre": "Copiapó SKC Enaex Serv"},
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
    {"Centro": "E043", "Sociedad": "EC06", "Nombre": "El Peñón Subte"},
    {"Centro": "E115", "Sociedad": "EC06", "Nombre": "Enaex SKC ING"},
    {"Centro": "E027", "Sociedad": "EC06", "Nombre": "Faena Teniente Rajo"},
    {"Centro": "E052", "Sociedad": "EC06", "Nombre": "Faena Spence"},
]


# ============================================================
# CSS
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

        .kpi-good {
            color: #166534;
            font-weight: 700;
        }

        .kpi-bad {
            color: #991B1B;
            font-weight: 700;
        }

        .kpi-warning {
            color: #B45309;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOGO
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
# UTILIDADES
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

    if texto in ["no aplica", "no aplica al analisis", "no aplica al análisis"]:
        return "No aplica"

    if texto == "en proceso":
        return "En proceso"

    if texto in ["sin datos", "sin dato", "nan", "none", "<na>", ""]:
        return "Sin datos"

    return str(valor).strip()


def formatear_entero(valor) -> str:
    if pd.isna(valor):
        return "—"

    valor_num = pd.to_numeric(valor, errors="coerce")

    if pd.isna(valor_num):
        return "—"

    return f"{int(round(valor_num)):,}".replace(",", ".")


def formatear_porcentaje(valor) -> str:
    if pd.isna(valor):
        return "—"

    valor_num = pd.to_numeric(valor, errors="coerce")

    if pd.isna(valor_num):
        return "—"

    return f"{valor_num:.1f}%"


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

    if mapa_etiquetas is None:
        mapa_etiquetas = obtener_mapa_etiquetas_centros()

    return mapa_etiquetas.get(codigo, f"{codigo} — Sin nombre en maestro")


def obtener_columna_centro(df: pd.DataFrame) -> str:
    for col in [COL_CENTRO_ME5A, COL_CENTRO_ME80FN, COL_CENTRO_SIMPLE]:
        if col in df.columns:
            return col

    raise ValueError(
        "No se encontró columna de centro: Centro - ME5A, Centro - ME80FN o Centro."
    )


def validar_columnas_base(df: pd.DataFrame):
    faltantes = [
        col for col in COLUMNAS_REQUERIDAS_BASE
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas para calcular Performance TAT: {faltantes}"
        )


def obtener_rango_fechas_semana_iso(anio_iso: int, semana_iso: int):
    inicio = pd.Timestamp(date.fromisocalendar(int(anio_iso), int(semana_iso), 1))
    fin = pd.Timestamp(date.fromisocalendar(int(anio_iso), int(semana_iso), 7))
    return inicio, fin


# ============================================================
# PERFORMANCE
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

    validar_columnas_base(df)

    for col in COLUMNAS_FECHA_PERFORMANCE:
        col_norm = col.replace("NME80FN", "ME80FN")

        if col_norm in df.columns:
            df[col_norm] = convertir_fecha_columna(df[col_norm])

    col_centro = obtener_columna_centro(df)

    df["centro_grafico"] = (
        df[col_centro]
        .astype("string")
        .str.strip()
    )

    if COL_PEDIDO in df.columns:
        df["tipo_oc"] = df[COL_PEDIDO].apply(extraer_tipo_oc)
    elif COL_DOCUMENTO_COMPRAS in df.columns:
        df["tipo_oc"] = df[COL_DOCUMENTO_COMPRAS].apply(extraer_tipo_oc)
    elif "tipo_oc" in df.columns:
        df["tipo_oc"] = df["tipo_oc"].apply(extraer_tipo_oc)
    else:
        df["tipo_oc"] = pd.NA

    df["tipo_oc"] = df["tipo_oc"].astype("string")

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

    df["dias_tat_total"] = diferencia_dias(
        df[COL_FECHA_RECEPCION_FINAL],
        df[COL_FECHA_SOLICITUD_FINAL],
    )

    columnas_dias = [
        "dias_liberacion_solped",
        "dias_comprador",
        "dias_proveedor",
        "dias_logistica",
        "dias_tat_total",
    ]

    df["tiene_fechas_inconsistentes"] = (
        df[columnas_dias]
        .lt(0)
        .any(axis=1, skipna=True)
    )

    if COL_PERFORMANCE_TAT not in df.columns:
        df[COL_PERFORMANCE_TAT] = evaluar_performance_tat(df)
    else:
        df[COL_PERFORMANCE_TAT] = df[COL_PERFORMANCE_TAT].apply(normalizar_estado_tat)

    df[COL_PERFORMANCE_TAT] = df[COL_PERFORMANCE_TAT].apply(normalizar_estado_tat)

    df["grupo_planta"] = "Plantas de servicios"
    df.loc[df["centro_grafico"].eq("E002"), "grupo_planta"] = "Prillex"
    df.loc[df["centro_grafico"].eq("E024"), "grupo_planta"] = "Rio Loa"

    df.loc[
        df["centro_grafico"].isin(CENTROS_EXCLUIR_PLANTAS_SERVICIOS)
        & ~df["centro_grafico"].isin(["E002", "E024"]),
        "grupo_planta",
    ] = "Excluir"

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

    return df


# ============================================================
# FILTROS GENERALES
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
    fecha_facturacion_desde,
    rango_recepcion,
    estados_sel: list[str],
    grupos_sel: list[str],
    centros_sel: list[str],
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

    barra.progress(15, text="Aplicando exclusión de grupos no analizables...")

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

    barra.progress(30, text="Aplicando fecha de facturación...")

    if fecha_facturacion_desde is not None:
        antes = df_filtrado.copy()

        fecha_facturacion_desde = pd.Timestamp(fecha_facturacion_desde)

        df_filtrado = df_filtrado[
            df_filtrado[COL_FECHA_FACTURACION_FINAL].notna()
            & df_filtrado[COL_FECHA_FACTURACION_FINAL].gt(fecha_facturacion_desde)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 2",
            "Fecha facturación desde",
            str(fecha_facturacion_desde.date()),
            antes,
            df_filtrado,
        )

    barra.progress(45, text="Aplicando fecha de recepción...")

    if rango_recepcion is not None:
        if isinstance(rango_recepcion, (tuple, list)) and len(rango_recepcion) == 2:
            antes = df_filtrado.copy()

            fecha_inicio = pd.Timestamp(rango_recepcion[0])
            fecha_fin = (
                pd.Timestamp(rango_recepcion[1])
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
            )

            df_filtrado = df_filtrado[
                df_filtrado[COL_FECHA_RECEPCION_FINAL].notna()
                & df_filtrado[COL_FECHA_RECEPCION_FINAL].between(
                    fecha_inicio,
                    fecha_fin,
                )
            ].copy()

            registrar_paso_filtro(
                resumen,
                "Filtro 3",
                "Fecha recepción",
                f"{fecha_inicio.date()} a {fecha_fin.date()}",
                antes,
                df_filtrado,
            )

    barra.progress(65, text="Aplicando Performance TAT...")

    if estados_sel:
        antes = df_filtrado.copy()

        df_filtrado = df_filtrado[
            df_filtrado[COL_PERFORMANCE_TAT].isin(estados_sel)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 4",
            "Performance TAT",
            ", ".join(estados_sel),
            antes,
            df_filtrado,
        )

    barra.progress(80, text="Aplicando grupo planta...")

    if grupos_sel:
        antes = df_filtrado.copy()

        df_filtrado = df_filtrado[
            df_filtrado["grupo_planta"].isin(grupos_sel)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 5",
            "Grupo planta",
            ", ".join(grupos_sel),
            antes,
            df_filtrado,
        )

    barra.progress(92, text="Aplicando centros específicos...")

    if centros_sel:
        antes = df_filtrado.copy()

        df_filtrado = df_filtrado[
            df_filtrado["centro_grafico"].isin(centros_sel)
        ].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro 6",
            "Centro específico",
            ", ".join(centros_sel),
            antes,
            df_filtrado,
        )

    barra.progress(100, text="Filtros aplicados correctamente.")

    return df_filtrado, pd.DataFrame(resumen)


# ============================================================
# RESÚMENES
# ============================================================

def crear_resumen_performance(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or COL_PERFORMANCE_TAT not in df.columns:
        return pd.DataFrame()

    orden = [
        "Cumple",
        "No cumple",
        "En proceso",
        "No aplica",
        "Sin datos",
    ]

    tabla = (
        df[COL_PERFORMANCE_TAT]
        .value_counts()
        .reindex(orden, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Categoría", "Cantidad"]

    total = int(tabla["Cantidad"].sum())

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
        total > 0,
        tabla["Cantidad"] / total * 100,
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


def crear_resumen_grupos(df: pd.DataFrame) -> pd.DataFrame:
    columnas_salida = [
        "Grupo planta",
        "Cumple",
        "No cumple",
        "Total evaluable",
        "% Cumple",
        "% No cumple",
    ]

    if df.empty:
        return pd.DataFrame(columns=columnas_salida)

    base = df[
        df[COL_PERFORMANCE_TAT].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        return pd.DataFrame(columns=columnas_salida)

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

    tabla["Total evaluable"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Total evaluable"] > 0,
        tabla["Cumple"] / tabla["Total evaluable"] * 100,
        0,
    )

    tabla["% No cumple"] = np.where(
        tabla["Total evaluable"] > 0,
        tabla["No cumple"] / tabla["Total evaluable"] * 100,
        0,
    )

    tabla = tabla.rename(columns={"grupo_planta": "Grupo planta"})

    orden = {
        "Prillex": 1,
        "Rio Loa": 2,
        "Plantas de servicios": 3,
    }

    tabla["orden"] = tabla["Grupo planta"].map(orden).fillna(99)
    tabla = tabla.sort_values("orden").drop(columns="orden")

    total_cumple = int(tabla["Cumple"].sum())
    total_no_cumple = int(tabla["No cumple"].sum())
    total_evaluable = total_cumple + total_no_cumple

    pct_total = (
        total_cumple / total_evaluable * 100
        if total_evaluable
        else 0
    )

    fila_total = pd.DataFrame(
        [
            {
                "Grupo planta": "Total",
                "Cumple": total_cumple,
                "No cumple": total_no_cumple,
                "Total evaluable": total_evaluable,
                "% Cumple": pct_total,
                "% No cumple": 100 - pct_total if total_evaluable else 0,
            }
        ]
    )

    tabla = pd.concat([tabla, fila_total], ignore_index=True)

    tabla["Cumple"] = tabla["Cumple"].astype(int)
    tabla["No cumple"] = tabla["No cumple"].astype(int)
    tabla["Total evaluable"] = tabla["Total evaluable"].astype(int)
    tabla["% Cumple"] = tabla["% Cumple"].round(2)
    tabla["% No cumple"] = tabla["% No cumple"].round(2)

    return tabla[columnas_salida]


def crear_resumen_mensual_grupos(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df[
        df["grupo_planta"].isin(["Prillex", "Rio Loa", "Plantas de servicios"])
        & df[COL_PERFORMANCE_TAT].isin(["Cumple", "No cumple"])
        & df["periodo_fecha"].notna()
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

    tabla["Total evaluable"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Total evaluable"] > 0,
        tabla["Cumple"] / tabla["Total evaluable"] * 100,
        0,
    )

    tabla["% No cumple"] = np.where(
        tabla["Total evaluable"] > 0,
        tabla["No cumple"] / tabla["Total evaluable"] * 100,
        0,
    )

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


def crear_kpis_ultimo_anio_por_grupo(tabla_ultimo_anio: pd.DataFrame) -> pd.DataFrame:
    if tabla_ultimo_anio.empty:
        return pd.DataFrame()

    base = tabla_ultimo_anio.copy()

    resumen = (
        base
        .groupby("grupo_planta")
        .agg(
            Cumple=("Cumple", "sum"),
            **{"No cumple": ("No cumple", "sum")},
            **{"Total evaluable": ("Total evaluable", "sum")},
            **{"Promedio mensual % Cumple": ("% Cumple", "mean")},
        )
        .reset_index()
        .rename(columns={"grupo_planta": "Grupo planta"})
    )

    resumen["% Cumple acumulado"] = np.where(
        resumen["Total evaluable"] > 0,
        resumen["Cumple"] / resumen["Total evaluable"] * 100,
        0,
    )

    resumen["% No cumple acumulado"] = np.where(
        resumen["Total evaluable"] > 0,
        resumen["No cumple"] / resumen["Total evaluable"] * 100,
        0,
    )

    resumen["Promedio mensual % Cumple"] = resumen["Promedio mensual % Cumple"].round(2)
    resumen["% Cumple acumulado"] = resumen["% Cumple acumulado"].round(2)
    resumen["% No cumple acumulado"] = resumen["% No cumple acumulado"].round(2)

    orden = {
        "Prillex": 1,
        "Rio Loa": 2,
        "Plantas de servicios": 3,
    }

    resumen["orden"] = resumen["Grupo planta"].map(orden).fillna(99)
    resumen = resumen.sort_values("orden").drop(columns="orden")

    return resumen


def crear_resumen_centros(df: pd.DataFrame, mapa_etiquetas: dict) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df[
        df[COL_PERFORMANCE_TAT].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        return pd.DataFrame()

    resumen = (
        base
        .groupby(["centro_grafico", "grupo_planta", COL_PERFORMANCE_TAT])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=["centro_grafico", "grupo_planta"],
        columns=COL_PERFORMANCE_TAT,
        values="cantidad",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for col in ["Cumple", "No cumple"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["Total evaluable"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Total evaluable"] > 0,
        tabla["Cumple"] / tabla["Total evaluable"] * 100,
        0,
    )

    tabla["Centro"] = tabla["centro_grafico"].apply(
        lambda x: etiqueta_centro(x, mapa_etiquetas)
    )

    tabla = tabla.sort_values(
        ["% Cumple", "Total evaluable"],
        ascending=[False, False],
    )

    tabla["% Cumple"] = tabla["% Cumple"].round(2)

    return tabla[
        [
            "centro_grafico",
            "Centro",
            "grupo_planta",
            "Cumple",
            "No cumple",
            "Total evaluable",
            "% Cumple",
        ]
    ].rename(
        columns={
            "centro_grafico": "Código centro",
            "grupo_planta": "Grupo planta",
        }
    ).reset_index(drop=True)


def calcular_kpis_generales(df_base: pd.DataFrame, df_filtrado: pd.DataFrame) -> dict:
    total_base = len(df_base)
    total_filtrado = len(df_filtrado)
    total_excluido = total_base - total_filtrado

    pct_retenido = total_filtrado / total_base * 100 if total_base else 0
    pct_excluido = total_excluido / total_base * 100 if total_base else 0

    cumple = int(df_filtrado[COL_PERFORMANCE_TAT].eq("Cumple").sum())
    no_cumple = int(df_filtrado[COL_PERFORMANCE_TAT].eq("No cumple").sum())
    en_proceso = int(df_filtrado[COL_PERFORMANCE_TAT].eq("En proceso").sum())
    no_aplica = int(df_filtrado[COL_PERFORMANCE_TAT].eq("No aplica").sum())
    sin_datos = int(df_filtrado[COL_PERFORMANCE_TAT].eq("Sin datos").sum())

    evaluables = cumple + no_cumple
    no_evaluables = en_proceso + no_aplica + sin_datos

    pct_evaluables = evaluables / total_filtrado * 100 if total_filtrado else 0
    pct_no_evaluables = no_evaluables / total_filtrado * 100 if total_filtrado else 0

    pct_cumple = cumple / evaluables * 100 if evaluables else 0
    pct_no_cumple = no_cumple / evaluables * 100 if evaluables else 0

    return {
        "total_base": total_base,
        "total_filtrado": total_filtrado,
        "total_excluido": total_excluido,
        "pct_retenido": pct_retenido,
        "pct_excluido": pct_excluido,
        "cumple": cumple,
        "no_cumple": no_cumple,
        "en_proceso": en_proceso,
        "no_aplica": no_aplica,
        "sin_datos": sin_datos,
        "evaluables": evaluables,
        "no_evaluables": no_evaluables,
        "pct_evaluables": pct_evaluables,
        "pct_no_evaluables": pct_no_evaluables,
        "pct_cumple": pct_cumple,
        "pct_no_cumple": pct_no_cumple,
    }


# ============================================================
# FILTRO SEMANAL
# ============================================================

def crear_catalogo_semanas_disponibles(df: pd.DataFrame) -> pd.DataFrame:
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
                "Inicio semana",
                "Fin semana",
                "Desde datos",
                "Hasta datos",
                "Registros",
                "Etiqueta",
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
                "Inicio semana",
                "Fin semana",
                "Desde datos",
                "Hasta datos",
                "Registros",
                "Etiqueta",
            ]
        )

    catalogo = (
        base
        .groupby(["anio_iso_recepcion", "semana_iso_recepcion"])
        .agg(
            Desde_datos=(COL_FECHA_RECEPCION_FINAL, "min"),
            Hasta_datos=(COL_FECHA_RECEPCION_FINAL, "max"),
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

    inicios = []
    fines = []

    for _, fila in catalogo.iterrows():
        inicio, fin = obtener_rango_fechas_semana_iso(
            int(fila["Año"]),
            int(fila["Semana"]),
        )

        inicios.append(inicio)
        fines.append(fin)

    catalogo["Inicio semana"] = inicios
    catalogo["Fin semana"] = fines

    catalogo["Etiqueta"] = (
        "Semana "
        + catalogo["Semana"].astype(str).str.zfill(2)
        + " · "
        + catalogo["Inicio semana"].dt.strftime("%d-%m-%Y")
        + " a "
        + catalogo["Fin semana"].dt.strftime("%d-%m-%Y")
        + " · "
        + catalogo["Registros"].astype(str)
        + " registros"
    )

    catalogo["Desde datos"] = catalogo["Desde_datos"].dt.strftime("%d-%m-%Y")
    catalogo["Hasta datos"] = catalogo["Hasta_datos"].dt.strftime("%d-%m-%Y")
    catalogo["Inicio semana"] = catalogo["Inicio semana"].dt.strftime("%d-%m-%Y")
    catalogo["Fin semana"] = catalogo["Fin semana"].dt.strftime("%d-%m-%Y")

    catalogo = catalogo.drop(columns=["Desde_datos", "Hasta_datos"])

    return catalogo.sort_values(["Año", "Semana"]).reset_index(drop=True)


def filtrar_por_fecha_recepcion(
    df: pd.DataFrame,
    fecha_inicio,
    fecha_fin,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    fecha_inicio = pd.Timestamp(fecha_inicio)
    fecha_fin = (
        pd.Timestamp(fecha_fin)
        + pd.Timedelta(days=1)
        - pd.Timedelta(microseconds=1)
    )

    return df[
        df[COL_FECHA_RECEPCION_FINAL].between(fecha_inicio, fecha_fin)
    ].copy()


def filtrar_por_anio_y_semana_iso(
    df: pd.DataFrame,
    anio_iso: int | None,
    semana_inicio: int | None,
    semana_fin: int | None,
) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    if anio_iso is None or semana_inicio is None or semana_fin is None:
        return df.copy()

    if "anio_iso_recepcion" not in df.columns or "semana_iso_recepcion" not in df.columns:
        return df.copy()

    return df[
        df["anio_iso_recepcion"].eq(int(anio_iso))
        & df["semana_iso_recepcion"].between(int(semana_inicio), int(semana_fin))
    ].copy()


def selector_filtro_semanal_tabla(df: pd.DataFrame):
    metadata = {
        "filtro_activo": False,
        "modo": "Sin filtro semanal específico",
        "descripcion": "Se usa la base filtrada general del dashboard.",
    }

    if df.empty:
        return df.copy(), metadata

    if "anio_iso_recepcion" not in df.columns or "semana_iso_recepcion" not in df.columns:
        st.warning("No existen columnas de año/semana ISO para aplicar filtro semanal.")
        return df.copy(), metadata

    catalogo = crear_catalogo_semanas_disponibles(df)

    if catalogo.empty:
        st.info("No hay semanas disponibles con los filtros actuales.")
        return df.copy(), metadata

    st.markdown("#### Filtro del detalle semanal")
    st.caption(
        "Configura el filtro semanal y presiona confirmar. "
        "El detalle no se filtra hasta que confirmes la selección."
    )

    fecha_inicio_cal = None
    fecha_fin_cal = None
    anio_sel = None
    semana_inicio_sel = None
    semana_fin_sel = None

    with st.form("form_filtro_detalle_semanal_plantas"):
        modo_filtro = st.radio(
            "Tipo de filtro semanal",
            options=[
                "Sin filtro semanal",
                "Filtrar por rango de fechas",
                "Filtrar por semana ISO",
            ],
            horizontal=True,
            key="modo_filtro_detalle_semanal_plantas",
        )

        if modo_filtro == "Filtrar por rango de fechas":
            fechas_validas = df[COL_FECHA_RECEPCION_FINAL].dropna()

            fecha_min = fechas_validas.min().date()
            fecha_max = fechas_validas.max().date()

            rango_fecha_tabla = st.date_input(
                "Rango de fechas para el detalle semanal",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                key="rango_fecha_detalle_semanal_plantas",
                help="Se usa fecha_recepcion_final. Luego se agrupa por semana ISO.",
            )

            if isinstance(rango_fecha_tabla, (tuple, list)) and len(rango_fecha_tabla) == 2:
                fecha_inicio_cal = rango_fecha_tabla[0]
                fecha_fin_cal = rango_fecha_tabla[1]

        elif modo_filtro == "Filtrar por semana ISO":
            anios_disponibles = sorted(
                catalogo["Año"]
                .dropna()
                .astype(int)
                .unique()
                .tolist()
            )

            anio_sel = st.selectbox(
                "Año ISO",
                options=anios_disponibles,
                index=len(anios_disponibles) - 1,
                key="anio_iso_detalle_semanal_plantas",
            )

            catalogo_anio = catalogo[catalogo["Año"].eq(int(anio_sel))].copy()

            semanas_disponibles = sorted(
                catalogo_anio["Semana"]
                .dropna()
                .astype(int)
                .unique()
                .tolist()
            )

            mapa_semana_etiqueta = dict(
                zip(
                    catalogo_anio["Semana"].astype(int),
                    catalogo_anio["Etiqueta"].astype(str),
                )
            )

            c1, c2 = st.columns(2)

            with c1:
                semana_inicio_sel = st.selectbox(
                    "Semana inicial",
                    options=semanas_disponibles,
                    format_func=lambda semana: mapa_semana_etiqueta.get(
                        int(semana),
                        f"Semana {int(semana):02d}",
                    ),
                    index=0,
                    key="semana_inicio_detalle_semanal_plantas",
                )

            semanas_fin_disponibles = [
                semana for semana in semanas_disponibles
                if int(semana) >= int(semana_inicio_sel)
            ]

            with c2:
                semana_fin_sel = st.selectbox(
                    "Semana final",
                    options=semanas_fin_disponibles,
                    format_func=lambda semana: mapa_semana_etiqueta.get(
                        int(semana),
                        f"Semana {int(semana):02d}",
                    ),
                    index=len(semanas_fin_disponibles) - 1,
                    key="semana_fin_detalle_semanal_plantas",
                )

            fecha_inicio_semana, _ = obtener_rango_fechas_semana_iso(
                int(anio_sel),
                int(semana_inicio_sel),
            )

            _, fecha_fin_semana = obtener_rango_fechas_semana_iso(
                int(anio_sel),
                int(semana_fin_sel),
            )

            st.info(
                f"El rango seleccionado corresponde a: "
                f"{fecha_inicio_semana.strftime('%d-%m-%Y')} "
                f"a {fecha_fin_semana.strftime('%d-%m-%Y')}."
            )

        confirmar_filtro = st.form_submit_button(
            "Confirmar filtro semanal",
            use_container_width=True,
            type="primary",
        )

    if not confirmar_filtro:
        st.info("Configura el filtro semanal y presiona **Confirmar filtro semanal**.")
        return df.copy(), metadata

    progreso = st.progress(0, text="Validando filtro semanal...")

    progreso.progress(20, text="Leyendo configuración del filtro...")

    if modo_filtro == "Sin filtro semanal":
        progreso.progress(100, text="Detalle semanal preparado sin filtro adicional.")

        metadata = {
            "filtro_activo": False,
            "modo": "Sin filtro semanal",
            "descripcion": "Se usa la base filtrada general del dashboard.",
        }

        return df.copy(), metadata

    if modo_filtro == "Filtrar por rango de fechas":
        progreso.progress(45, text="Aplicando rango de fechas...")

        if fecha_inicio_cal is None or fecha_fin_cal is None:
            st.warning("Selecciona una fecha inicial y una fecha final.")
            return df.copy(), metadata

        df_filtrado = filtrar_por_fecha_recepcion(
            df=df,
            fecha_inicio=fecha_inicio_cal,
            fecha_fin=fecha_fin_cal,
        )

        progreso.progress(75, text="Identificando semanas incluidas...")

        catalogo_filtrado = crear_catalogo_semanas_disponibles(df_filtrado)

        semanas_txt = ", ".join(
            [
                f"{int(row['Año'])}-S{int(row['Semana']):02d}"
                for _, row in catalogo_filtrado.iterrows()
            ]
        )

        progreso.progress(100, text="Filtro semanal aplicado.")

        st.success(
            f"Filtro aplicado: {fecha_inicio_cal.strftime('%d-%m-%Y')} "
            f"a {fecha_fin_cal.strftime('%d-%m-%Y')}."
        )

        st.caption(
            f"Semanas incluidas: {semanas_txt if semanas_txt else 'Sin semanas disponibles'}."
        )

        if not catalogo_filtrado.empty:
            with st.expander("Semanas incluidas en el rango confirmado", expanded=True):
                st.dataframe(
                    catalogo_filtrado,
                    use_container_width=True,
                    hide_index=True,
                )

        metadata = {
            "filtro_activo": True,
            "modo": "Rango de fechas",
            "descripcion": (
                f"{fecha_inicio_cal.strftime('%d-%m-%Y')} "
                f"a {fecha_fin_cal.strftime('%d-%m-%Y')}"
            ),
        }

        return df_filtrado, metadata

    if modo_filtro == "Filtrar por semana ISO":
        progreso.progress(45, text="Aplicando semanas ISO seleccionadas...")

        if anio_sel is None or semana_inicio_sel is None or semana_fin_sel is None:
            st.warning("Selecciona año, semana inicial y semana final.")
            return df.copy(), metadata

        fecha_inicio_semana, _ = obtener_rango_fechas_semana_iso(
            int(anio_sel),
            int(semana_inicio_sel),
        )

        _, fecha_fin_semana = obtener_rango_fechas_semana_iso(
            int(anio_sel),
            int(semana_fin_sel),
        )

        df_filtrado = filtrar_por_anio_y_semana_iso(
            df=df,
            anio_iso=anio_sel,
            semana_inicio=semana_inicio_sel,
            semana_fin=semana_fin_sel,
        )

        progreso.progress(75, text="Preparando detalle semanal filtrado...")

        catalogo_filtrado = crear_catalogo_semanas_disponibles(df_filtrado)

        progreso.progress(100, text="Filtro semanal aplicado.")

        st.success(
            f"Filtro aplicado: Año {anio_sel}, semana {semana_inicio_sel} "
            f"a semana {semana_fin_sel}."
        )

        st.caption(
            f"Rango calendario correspondiente: "
            f"{fecha_inicio_semana.strftime('%d-%m-%Y')} "
            f"a {fecha_fin_semana.strftime('%d-%m-%Y')}."
        )

        if not catalogo_filtrado.empty:
            with st.expander("Semanas incluidas en el rango confirmado", expanded=True):
                st.dataframe(
                    catalogo_filtrado,
                    use_container_width=True,
                    hide_index=True,
                )

        metadata = {
            "filtro_activo": True,
            "modo": "Semana ISO",
            "descripcion": (
                f"Año {anio_sel}, semana {semana_inicio_sel} "
                f"a semana {semana_fin_sel} · "
                f"{fecha_inicio_semana.strftime('%d-%m-%Y')} "
                f"a {fecha_fin_semana.strftime('%d-%m-%Y')}"
            ),
        }

        return df_filtrado, metadata

    return df.copy(), metadata


def crear_detalle_semanal(df: pd.DataFrame) -> pd.DataFrame:
    columnas_salida = [
        "Año",
        "Semana",
        "Inicio semana",
        "Fin semana",
        "Grupo planta",
        "Cumple",
        "No cumple",
        "Total evaluable",
        "% Cumple",
    ]

    if df.empty:
        return pd.DataFrame(columns=columnas_salida)

    base = df[
        df[COL_PERFORMANCE_TAT].isin(["Cumple", "No cumple"])
        & df["anio_iso_recepcion"].notna()
        & df["semana_iso_recepcion"].notna()
    ].copy()

    if base.empty:
        return pd.DataFrame(columns=columnas_salida)

    resumen = (
        base
        .groupby(
            [
                "anio_iso_recepcion",
                "semana_iso_recepcion",
                "grupo_planta",
                COL_PERFORMANCE_TAT,
            ]
        )
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=[
            "anio_iso_recepcion",
            "semana_iso_recepcion",
            "grupo_planta",
        ],
        columns=COL_PERFORMANCE_TAT,
        values="cantidad",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for col in ["Cumple", "No cumple"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla = tabla.rename(
        columns={
            "anio_iso_recepcion": "Año",
            "semana_iso_recepcion": "Semana",
            "grupo_planta": "Grupo planta",
        }
    )

    tabla["Año"] = tabla["Año"].astype(int)
    tabla["Semana"] = tabla["Semana"].astype(int)
    tabla["Cumple"] = tabla["Cumple"].astype(int)
    tabla["No cumple"] = tabla["No cumple"].astype(int)
    tabla["Total evaluable"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Total evaluable"] > 0,
        tabla["Cumple"] / tabla["Total evaluable"] * 100,
        0,
    )

    orden_grupo = {
        "Prillex": 1,
        "Rio Loa": 2,
        "Plantas de servicios": 3,
    }

    tabla["orden_grupo"] = tabla["Grupo planta"].map(orden_grupo).fillna(99)

    totales = (
        tabla
        .groupby(["Año", "Semana"], as_index=False)
        .agg(
            Cumple=("Cumple", "sum"),
            **{"No cumple": ("No cumple", "sum")},
            **{"Total evaluable": ("Total evaluable", "sum")},
        )
    )

    totales["Grupo planta"] = "Total semana"
    totales["% Cumple"] = np.where(
        totales["Total evaluable"] > 0,
        totales["Cumple"] / totales["Total evaluable"] * 100,
        0,
    )
    totales["orden_grupo"] = 999

    tabla_final = pd.concat(
        [
            tabla[
                [
                    "Año",
                    "Semana",
                    "Grupo planta",
                    "Cumple",
                    "No cumple",
                    "Total evaluable",
                    "% Cumple",
                    "orden_grupo",
                ]
            ],
            totales[
                [
                    "Año",
                    "Semana",
                    "Grupo planta",
                    "Cumple",
                    "No cumple",
                    "Total evaluable",
                    "% Cumple",
                    "orden_grupo",
                ]
            ],
        ],
        ignore_index=True,
    )

    inicios = []
    fines = []

    for _, fila in tabla_final.iterrows():
        inicio, fin = obtener_rango_fechas_semana_iso(
            int(fila["Año"]),
            int(fila["Semana"]),
        )

        inicios.append(inicio.strftime("%d-%m-%Y"))
        fines.append(fin.strftime("%d-%m-%Y"))

    tabla_final["Inicio semana"] = inicios
    tabla_final["Fin semana"] = fines
    tabla_final["% Cumple"] = tabla_final["% Cumple"].round(2)

    tabla_final = (
        tabla_final
        .sort_values(["Año", "Semana", "orden_grupo"])
        .drop(columns=["orden_grupo"])
        .reset_index(drop=True)
    )

    return tabla_final[columnas_salida]


# ============================================================
# GRÁFICOS
# ============================================================

def formatear_ejes(ax):
    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0, colors=COLOR_MUTED)
    ax.set_facecolor("none")


def grafico_donut_retencion(total_base: int, total_filtrado: int):
    total_excluido = total_base - total_filtrado

    tabla = pd.DataFrame(
        [
            {"Categoría": "Retenidos", "Cantidad": total_filtrado},
            {"Categoría": "Excluidos", "Cantidad": total_excluido},
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
        "Excluidos": COLOR_NO_CUMPLE,
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
        "registros",
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


def grafico_donut_performance(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay datos para graficar Performance TAT.")
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

            if categoria == "Cumple":
                autotext.set_color("white")
            else:
                autotext.set_color(COLOR_TEXTO)

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
            "filtrados",
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

        ax.legend(
            wedges,
            etiquetas_leyenda,
            title="Performance TAT",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=9.5,
            title_fontsize=10,
        )

        ax.set_title(
            "Desglose de datos filtrados por Performance TAT",
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
        st.markdown("#### Tabla de desglose")
        st.caption("Base: todos los registros filtrados.")

        tabla_resumen = data.copy()

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


def grafico_cumplimiento_grupos(tabla: pd.DataFrame):
    st.markdown("### Cumplimiento TAT por planta")
    st.caption(
        "Porcentaje de cumplimiento sobre registros evaluables. "
        "La línea segmentada indica la meta."
    )

    if tabla.empty:
        st.info("No hay datos evaluables para graficar.")
        return

    data = tabla[tabla["Grupo planta"].ne("Total")].copy()

    if data.empty:
        st.info("No hay datos evaluables para graficar.")
        return

    data = data.sort_values("% Cumple", ascending=True)

    y = np.arange(len(data))
    valores = data["% Cumple"].to_numpy()
    etiquetas = data["Grupo planta"].astype(str).tolist()

    colores_mapa = {
        "Prillex": COLOR_PRILLEX,
        "Rio Loa": COLOR_RIO_LOA,
        "Plantas de servicios": COLOR_SERVICIOS,
    }

    colores = [colores_mapa.get(etiqueta, COLOR_CUMPLE) for etiqueta in etiquetas]

    fig, ax = plt.subplots(figsize=(11, 4.8), dpi=180)

    ax.barh(
        y,
        valores,
        color=colores,
        height=0.55,
        label="Cumplimiento TAT",
    )

    for i, valor in enumerate(valores):
        ax.text(
            min(valor + 1.5, 103),
            i,
            f"{valor:.1f}%",
            va="center",
            ha="left",
            fontsize=11,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.axvline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle="--",
        linewidth=2.5,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    ax.set_xlim(0, 108)
    ax.set_yticks(y)
    ax.set_yticklabels(etiquetas, color=COLOR_MUTED)
    ax.set_xlabel("% Cumple sobre evaluables", color=COLOR_TEXTO)

    ax.set_xticks([0, 25, 50, 65, 75, 100])
    ax.set_xticklabels(
        ["0%", "25%", "50%", "65%", "75%", "100%"],
        color=COLOR_MUTED,
    )

    ax.set_title(
        "Cumplimiento por planta",
        fontsize=15,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=14,
    )

    ax.legend(
        loc="lower right",
        frameon=False,
        fontsize=10,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_evolucion_mensual_comparativa(
    tabla: pd.DataFrame,
    titulo: str,
):
    if tabla.empty:
        st.info("No hay datos mensuales evaluables para graficar.")
        return

    colores = {
        "Prillex": COLOR_PRILLEX,
        "Rio Loa": COLOR_RIO_LOA,
        "Plantas de servicios": COLOR_SERVICIOS,
    }

    grupos_orden = ["Prillex", "Rio Loa", "Plantas de servicios"]

    periodos = (
        tabla[["periodo_fecha", "periodo_label"]]
        .drop_duplicates()
        .sort_values("periodo_fecha")
    )

    labels = periodos["periodo_label"].astype(str).tolist()
    x = np.arange(len(labels))

    ancho = max(12, min(22, len(labels) * 0.85))

    fig, ax = plt.subplots(figsize=(ancho, 6.4), dpi=180)

    for grupo in grupos_orden:
        data_grupo = tabla[tabla["grupo_planta"].eq(grupo)].copy()

        if data_grupo.empty:
            continue

        data_grupo = (
            periodos
            .merge(
                data_grupo[["periodo_fecha", "% Cumple"]],
                on="periodo_fecha",
                how="left",
            )
            .sort_values("periodo_fecha")
        )

        y = data_grupo["% Cumple"].to_numpy(dtype=float)

        ax.plot(
            x,
            y,
            marker="o",
            linewidth=3,
            color=colores.get(grupo, COLOR_CUMPLE),
            label=grupo,
        )

        total_puntos = len(x)

        if total_puntos <= 12:
            paso = 1
        elif total_puntos <= 24:
            paso = 2
        else:
            paso = 3

        for i, valor in enumerate(y):
            if pd.notna(valor) and (i % paso == 0 or i == total_puntos - 1):
                ax.text(
                    i,
                    min(valor + 2.5, 104),
                    f"{valor:.0f}%",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                    color=colores.get(grupo, COLOR_TEXTO),
                )

    ax.axhline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle="--",
        linewidth=2.5,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    ax.set_ylim(0, 108)
    ax.set_ylabel("% Cumple sobre evaluables", color=COLOR_TEXTO)

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

    ax.set_title(
        titulo,
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=14,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=4,
        frameon=False,
        fontsize=10,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.28)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_volumen_mensual_comparativo(
    tabla: pd.DataFrame,
    titulo: str,
):
    if tabla.empty:
        st.info("No hay datos mensuales evaluables para graficar volumen.")
        return

    periodos = (
        tabla[["periodo_fecha", "periodo_label"]]
        .drop_duplicates()
        .sort_values("periodo_fecha")
    )

    grupos_orden = ["Prillex", "Rio Loa", "Plantas de servicios"]

    pivot = tabla.pivot_table(
        index=["periodo_fecha", "periodo_label"],
        columns="grupo_planta",
        values="Total evaluable",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    pivot = (
        periodos
        .merge(pivot, on=["periodo_fecha", "periodo_label"], how="left")
        .fillna(0)
    )

    for grupo in grupos_orden:
        if grupo not in pivot.columns:
            pivot[grupo] = 0

    labels = pivot["periodo_label"].astype(str).tolist()
    x = np.arange(len(labels))
    width = 0.25

    ancho = max(12, min(22, len(labels) * 0.85))

    fig, ax = plt.subplots(figsize=(ancho, 6.4), dpi=180)

    offsets = {
        "Prillex": -width,
        "Rio Loa": 0,
        "Plantas de servicios": width,
    }

    colores = {
        "Prillex": COLOR_PRILLEX,
        "Rio Loa": COLOR_RIO_LOA,
        "Plantas de servicios": COLOR_SERVICIOS,
    }

    max_valor = 0

    for grupo in grupos_orden:
        valores = pivot[grupo].astype(int).to_numpy()
        max_valor = max(max_valor, valores.max() if len(valores) else 0)

        barras = ax.bar(
            x + offsets[grupo],
            valores,
            width=width,
            color=colores[grupo],
            label=grupo,
        )

        for barra, valor in zip(barras, valores):
            if valor > 0:
                ax.text(
                    barra.get_x() + barra.get_width() / 2,
                    barra.get_height() + max(max_valor * 0.02, 1),
                    f"{valor:,}".replace(",", "."),
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                    color=COLOR_TEXTO,
                )

    ax.set_ylim(0, max(max_valor * 1.25, 10))

    ax.set_title(
        titulo,
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=14,
    )

    ax.set_ylabel("Registros evaluables", color=COLOR_TEXTO)

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
        ncol=3,
        frameon=False,
        fontsize=10,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.28)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


# ============================================================
# EXPORTACIÓN
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

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Registros",
        )

    return output.getvalue()


def generar_nombre_excel_mes(periodo_archivo: str, grupo: str, estado: str) -> str:
    fecha_descarga = datetime.now().strftime("%Y%m%d_%H%M%S")

    grupo_limpio = (
        str(grupo)
        .upper()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )

    estado_limpio = (
        str(estado)
        .upper()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )

    return f"09_PERFORMANCE_PLANTAS_{periodo_archivo}_{grupo_limpio}_{estado_limpio}_{fecha_descarga}.xlsx"


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
# APP
# ============================================================

mostrar_logo()

st.title("09_PERFORMANCE_PLANTAS")
st.caption(
    "Dashboard comparativo de cumplimiento TAT por Prillex, Rio Loa y Plantas de servicios."
)

if "df_tat" not in st.session_state or st.session_state.get("df_tat") is None:
    st.info("No hay archivo activo en sesión. Primero carga un archivo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

try:
    with st.spinner("Preparando base de Performance Plantas..."):
        df_final = preparar_base_plantas(df_original)

except Exception as e:
    st.error("No se pudo generar Performance de Plantas.")
    st.exception(e)
    st.stop()


# ============================================================
# FILTROS
# ============================================================

st.markdown("### Filtros")
st.caption(
    "Los filtros se aplican sobre la base activa cargada desde 06_CARGAR_ARCHIVO."
)

fechas_recepcion = df_final[COL_FECHA_RECEPCION_FINAL].dropna()

fecha_recepcion_min = (
    fechas_recepcion.min().date()
    if not fechas_recepcion.empty
    else None
)

fecha_recepcion_max = (
    fechas_recepcion.max().date()
    if not fechas_recepcion.empty
    else None
)

estados_disponibles = [
    estado
    for estado in ["Cumple", "No cumple", "En proceso", "No aplica", "Sin datos"]
    if estado in df_final[COL_PERFORMANCE_TAT].astype(str).unique()
]

grupos_disponibles = [
    grupo
    for grupo in ["Prillex", "Rio Loa", "Plantas de servicios"]
    if grupo in df_final["grupo_planta"].astype(str).unique()
]

centros_disponibles = (
    df_final[df_final["grupo_planta"].ne("Excluir")]["centro_grafico"]
    .dropna()
    .astype(str)
    .str.strip()
    .sort_values()
    .unique()
    .tolist()
)

mapa_etiquetas = obtener_mapa_etiquetas_centros()

opciones_centros = [
    etiqueta_centro(centro, mapa_etiquetas)
    for centro in centros_disponibles
]

mapa_label_a_centro = dict(zip(opciones_centros, centros_disponibles))

with st.form("form_filtros_performance_plantas"):
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        fecha_facturacion_desde = st.date_input(
            "Fecha facturación desde",
            value=FECHA_FILTRO_FACTURACION_DEFAULT.date(),
            key="plantas_fecha_facturacion_desde",
        )

    with col_f2:
        if fecha_recepcion_min is not None and fecha_recepcion_max is not None:
            rango_recepcion = st.date_input(
                "Fecha recepción",
                value=(fecha_recepcion_min, fecha_recepcion_max),
                min_value=fecha_recepcion_min,
                max_value=fecha_recepcion_max,
                key="plantas_rango_recepcion",
            )
        else:
            rango_recepcion = None
            st.warning("No hay fechas válidas de recepción.")

    with col_f3:
        estados_sel = st.multiselect(
            "Performance TAT",
            options=estados_disponibles,
            default=estados_disponibles,
            key="plantas_estados_tat",
        )

    with col_f4:
        grupos_sel = st.multiselect(
            "Grupo planta",
            options=grupos_disponibles,
            default=grupos_disponibles,
            key="plantas_grupos",
        )

    centros_labels_sel = st.multiselect(
        "Centros específicos opcionales",
        options=opciones_centros,
        default=[],
        key="plantas_centros_especificos",
        help="Si seleccionas centros, el dashboard se limita a esos centros dentro de los filtros generales.",
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
        "plantas_fecha_facturacion_desde",
        "plantas_rango_recepcion",
        "plantas_estados_tat",
        "plantas_grupos",
        "plantas_centros_especificos",
        "plantas_df_filtrado",
        "plantas_resumen_filtros",
        "plantas_firma_filtros",
        "plantas_parquet_bytes",
        "plantas_parquet_firma",
        "plantas_csv_bytes",
        "plantas_csv_firma",
        "plantas_excel_mes_bytes",
        "plantas_excel_mes_firma",
        "plantas_excel_mes_nombre",
    ]

    for clave in claves:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


centros_sel = [
    mapa_label_a_centro[label]
    for label in centros_labels_sel
    if label in mapa_label_a_centro
]

firma_filtros = (
    f"{fecha_facturacion_desde}_"
    f"{rango_recepcion}_"
    f"{','.join(estados_sel)}_"
    f"{','.join(grupos_sel)}_"
    f"{','.join(centros_sel)}_"
    f"{len(df_final)}"
)

if aplicar_filtros:
    with st.spinner("Aplicando filtros..."):
        df_dashboard, resumen_filtros_df = aplicar_filtros_con_progreso(
            df_base=df_final,
            fecha_facturacion_desde=fecha_facturacion_desde,
            rango_recepcion=rango_recepcion,
            estados_sel=estados_sel,
            grupos_sel=grupos_sel,
            centros_sel=centros_sel,
        )

        st.session_state["plantas_df_filtrado"] = df_dashboard
        st.session_state["plantas_resumen_filtros"] = resumen_filtros_df
        st.session_state["plantas_firma_filtros"] = firma_filtros

    st.success("Filtros aplicados correctamente.")

else:
    if (
        st.session_state.get("plantas_df_filtrado") is not None
        and st.session_state.get("plantas_firma_filtros") == firma_filtros
    ):
        df_dashboard = st.session_state["plantas_df_filtrado"].copy()
        resumen_filtros_df = st.session_state["plantas_resumen_filtros"].copy()
    else:
        df_dashboard, resumen_filtros_df = aplicar_filtros_con_progreso(
            df_base=df_final,
            fecha_facturacion_desde=fecha_facturacion_desde,
            rango_recepcion=rango_recepcion,
            estados_sel=estados_sel,
            grupos_sel=grupos_sel,
            centros_sel=centros_sel,
        )


# ============================================================
# KPI INDICATORS
# ============================================================

kpis = calcular_kpis_generales(
    df_base=df_final,
    df_filtrado=df_dashboard,
)

st.markdown("### KPI Indicators")
st.caption(
    "El cumplimiento TAT se calcula solo sobre registros evaluables: Cumple + No cumple."
)

col_k1, col_k2, col_k3, col_k4 = st.columns(4)

with col_k1:
    mostrar_kpi_html(
        "Registros base",
        formatear_entero(kpis["total_base"]),
        "Total de registros antes de filtros.",
    )

with col_k2:
    mostrar_kpi_html(
        "% retenido por filtros",
        formatear_porcentaje(kpis["pct_retenido"]),
        f"{formatear_entero(kpis['total_filtrado'])} retenidos de {formatear_entero(kpis['total_base'])}.",
    )

with col_k3:
    mostrar_kpi_html(
        "Registros evaluables",
        formatear_entero(kpis["evaluables"]),
        f"{formatear_porcentaje(kpis['pct_evaluables'])} de los registros filtrados.",
    )

with col_k4:
    mostrar_kpi_html(
        "No evaluables",
        formatear_entero(kpis["no_evaluables"]),
        f"{formatear_porcentaje(kpis['pct_no_evaluables'])} de los registros filtrados.",
        "kpi-warning",
    )

col_k5, col_k6, col_k7, col_k8 = st.columns(4)

with col_k5:
    mostrar_kpi_html(
        "Cumple TAT",
        formatear_porcentaje(kpis["pct_cumple"]),
        f"{formatear_entero(kpis['cumple'])} cumplen de {formatear_entero(kpis['evaluables'])} evaluables.",
        "kpi-good",
    )

with col_k6:
    mostrar_kpi_html(
        "No cumple TAT",
        formatear_porcentaje(kpis["pct_no_cumple"]),
        f"{formatear_entero(kpis['no_cumple'])} no cumplen de {formatear_entero(kpis['evaluables'])} evaluables.",
        "kpi-bad",
    )

with col_k7:
    mostrar_kpi_html(
        "En proceso",
        formatear_entero(kpis["en_proceso"]),
        "Registros todavía no evaluables.",
        "kpi-warning",
    )

with col_k8:
    mostrar_kpi_html(
        "No aplica / Sin datos",
        formatear_entero(kpis["no_aplica"] + kpis["sin_datos"]),
        f"No aplica: {formatear_entero(kpis['no_aplica'])} · Sin datos: {formatear_entero(kpis['sin_datos'])}.",
    )


# ============================================================
# RETENCIÓN POR FILTROS
# ============================================================

st.markdown("### 1. Retención por filtros")

col_ret1, col_ret2 = st.columns([1.1, 1])

with col_ret1:
    grafico_donut_retencion(
        total_base=kpis["total_base"],
        total_filtrado=kpis["total_filtrado"],
    )

with col_ret2:
    st.markdown("#### Resumen de filtros")
    resumen_retencion = pd.DataFrame(
        [
            {
                "Métrica": "Registros base",
                "Cantidad": kpis["total_base"],
                "%": 100.0,
            },
            {
                "Métrica": "Registros retenidos",
                "Cantidad": kpis["total_filtrado"],
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


# ============================================================
# DESGLOSE PERFORMANCE
# ============================================================

st.markdown("### 2. Retenidos por Performance TAT")

desglose_performance = crear_resumen_performance(df_dashboard)

grafico_donut_performance(desglose_performance)


# ============================================================
# CUMPLIMIENTO POR PLANTA
# ============================================================

st.markdown("### 3. Cumplimiento TAT por planta")

resumen_grupos = crear_resumen_grupos(df_dashboard)

grafico_cumplimiento_grupos(resumen_grupos)

st.markdown("#### Tabla de cumplimiento por planta")

if resumen_grupos.empty:
    st.info("No hay tabla de cumplimiento disponible.")
else:
    st.dataframe(
        resumen_grupos,
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
            "Total evaluable": st.column_config.NumberColumn(
                "Total evaluable",
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
# EVOLUCIÓN MENSUAL COMPARATIVA
# ============================================================

st.markdown("### 4. Evolución mensual comparativa")
st.caption(
    "Comparación del % de cumplimiento TAT mensual para Prillex, Rio Loa y Plantas de servicios."
)

tabla_mensual_grupos = crear_resumen_mensual_grupos(df_dashboard)

grafico_volumen_mensual_comparativo(
    tabla=tabla_mensual_grupos,
    titulo="Volumen mensual de registros evaluables por planta",
)

grafico_evolucion_mensual_comparativa(
    tabla=tabla_mensual_grupos,
    titulo="Evolución mensual de cumplimiento TAT por planta",
)


# ============================================================
# ZOOM ÚLTIMO AÑO
# ============================================================

tabla_ultimo_anio, ultimo_anio = obtener_tabla_ultimo_anio(tabla_mensual_grupos)

if not tabla_ultimo_anio.empty:
    st.markdown(f"### 5. Zoom último año disponible: {ultimo_anio}")

    kpis_ultimo_anio_df = crear_kpis_ultimo_anio_por_grupo(tabla_ultimo_anio)

    st.markdown("#### KPI Indicators último año por planta")

    st.dataframe(
        kpis_ultimo_anio_df,
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
            "Total evaluable": st.column_config.NumberColumn(
                "Total evaluable",
                format="%d",
            ),
            "Promedio mensual % Cumple": st.column_config.ProgressColumn(
                "Promedio mensual % Cumple",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "% Cumple acumulado": st.column_config.ProgressColumn(
                "% Cumple acumulado",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "% No cumple acumulado": st.column_config.ProgressColumn(
                "% No cumple acumulado",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )

    grafico_volumen_mensual_comparativo(
        tabla=tabla_ultimo_anio,
        titulo=f"Volumen mensual de registros evaluables por planta - {ultimo_anio}",
    )

    grafico_evolucion_mensual_comparativa(
        tabla=tabla_ultimo_anio,
        titulo=f"Evolución mensual de cumplimiento TAT por planta - {ultimo_anio}",
    )

else:
    st.info("No hay información suficiente para construir el zoom del último año.")


# ============================================================
# ANÁLISIS POR CENTRO
# ============================================================

with st.expander("Análisis por centro específico", expanded=True):
    st.caption(
        "Ranking de centros incluidos en la base filtrada actual."
    )

    resumen_centros = crear_resumen_centros(df_dashboard, mapa_etiquetas)

    if resumen_centros.empty:
        st.info("No hay centros evaluables con los filtros actuales.")
    else:
        st.dataframe(
            resumen_centros,
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
                "Total evaluable": st.column_config.NumberColumn(
                    "Total evaluable",
                    format="%d",
                ),
                "% Cumple": st.column_config.ProgressColumn(
                    "% Cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )


# ============================================================
# VISTA PREVIA Y DESCARGA POR MES, GRUPO Y ESTADO
# ============================================================

st.markdown("### Vista previa y descarga por mes")
st.caption(
    "Selecciona mes, grupo planta y estado TAT para revisar los registros y descargar un Excel."
)

if df_dashboard.empty or df_dashboard["periodo_fecha"].dropna().empty:
    st.info("No hay meses disponibles con los filtros actuales.")
else:
    meses_df = (
        df_dashboard[["periodo_fecha", "periodo_label"]]
        .dropna()
        .drop_duplicates()
        .sort_values("periodo_fecha")
        .reset_index(drop=True)
    )

    opciones_mes = meses_df["periodo_label"].astype(str).tolist()
    ultimo_mes = opciones_mes[-1] if opciones_mes else None

    col_vm1, col_vm2, col_vm3 = st.columns(3)

    with col_vm1:
        mes_sel = st.selectbox(
            "Mes / año",
            options=opciones_mes,
            index=opciones_mes.index(ultimo_mes) if ultimo_mes in opciones_mes else 0,
            key="plantas_selector_mes_preview",
        )

    with col_vm2:
        grupo_preview = st.selectbox(
            "Grupo planta",
            options=["Todos"] + grupos_disponibles,
            index=0,
            key="plantas_selector_grupo_preview",
        )

    with col_vm3:
        estado_preview = st.selectbox(
            "Estado TAT",
            options=["Todos", "Cumple", "No cumple", "En proceso", "No aplica", "Sin datos"],
            index=0,
            key="plantas_selector_estado_preview",
        )

    periodo_sel = meses_df.loc[
        meses_df["periodo_label"].astype(str).eq(mes_sel),
        "periodo_fecha",
    ].iloc[0]

    df_preview = df_dashboard[
        df_dashboard["periodo_fecha"].eq(periodo_sel)
    ].copy()

    if grupo_preview != "Todos":
        df_preview = df_preview[df_preview["grupo_planta"].eq(grupo_preview)].copy()

    if estado_preview != "Todos":
        df_preview = df_preview[df_preview[COL_PERFORMANCE_TAT].eq(estado_preview)].copy()

    total_preview = len(df_preview)

    st.info(
        f"Se encontraron **{formatear_entero(total_preview)} registros** "
        f"para **{mes_sel}**, grupo **{grupo_preview}**, estado **{estado_preview}**."
    )

    if total_preview > 0:
        limite_preview = st.number_input(
            "Filas a visualizar",
            min_value=1,
            max_value=min(1000, total_preview),
            value=min(300, total_preview),
            step=50 if total_preview >= 50 else 1,
            key="plantas_preview_filas_mes",
        )

        columnas_preferidas = [
            "Solicitud de pedido - ME5A",
            COL_PEDIDO,
            COL_DOCUMENTO_COMPRAS,
            "centro_grafico",
            "grupo_planta",
            COL_FECHA_SOLICITUD_FINAL,
            COL_FECHA_FACTURACION_FINAL,
            COL_FECHA_RECEPCION_FINAL,
            "dias_tat_total",
            COL_PERFORMANCE_TAT,
        ]

        columnas_preferidas = [
            col for col in columnas_preferidas
            if col in df_preview.columns
        ]

        if columnas_preferidas:
            st.dataframe(
                df_preview[columnas_preferidas].head(int(limite_preview)),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.dataframe(
                df_preview.head(int(limite_preview)),
                use_container_width=True,
                hide_index=True,
            )

        periodo_archivo = pd.Timestamp(periodo_sel).strftime("%Y%m")

        firma_excel_mes = (
            f"{periodo_archivo}_"
            f"{grupo_preview}_"
            f"{estado_preview}_"
            f"{len(df_preview)}"
        )

        preparar_excel = st.button(
            "Preparar Excel de la vista seleccionada",
            use_container_width=True,
            key="plantas_preparar_excel_mes",
        )

        if preparar_excel:
            nombre_excel = generar_nombre_excel_mes(
                periodo_archivo=periodo_archivo,
                grupo=grupo_preview,
                estado=estado_preview,
            )

            with st.spinner("Preparando Excel..."):
                st.session_state["plantas_excel_mes_bytes"] = convertir_a_excel_cache(df_preview)
                st.session_state["plantas_excel_mes_firma"] = firma_excel_mes
                st.session_state["plantas_excel_mes_nombre"] = nombre_excel

        if (
            st.session_state.get("plantas_excel_mes_bytes") is not None
            and st.session_state.get("plantas_excel_mes_firma") == firma_excel_mes
        ):
            st.download_button(
                label="Descargar Excel",
                data=st.session_state["plantas_excel_mes_bytes"],
                file_name=st.session_state["plantas_excel_mes_nombre"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )


# ============================================================
# DETALLE SEMANAL CON FILTRO
# ============================================================

with st.expander("Detalle semanal con filtro por semanas", expanded=True):
    st.caption(
        "Detalle por semana ISO y grupo planta usando fecha_recepcion_final. "
        "Cada semana muestra explícitamente su fecha de inicio y fin."
    )

    df_semanal, metadata_semanal = selector_filtro_semanal_tabla(df_dashboard)

    if metadata_semanal.get("filtro_activo"):
        st.success(
            f"Filtro semanal activo: {metadata_semanal.get('modo')} · "
            f"{metadata_semanal.get('descripcion')}"
        )
    else:
        st.info("Sin filtro semanal específico. Se usa la base filtrada general.")

    detalle_semanal = crear_detalle_semanal(df_semanal)

    if detalle_semanal.empty:
        st.info("No hay detalle semanal evaluable.")
    else:
        st.dataframe(
            detalle_semanal,
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
                "Total evaluable": st.column_config.NumberColumn(
                    "Total evaluable",
                    format="%d",
                ),
                "% Cumple": st.column_config.ProgressColumn(
                    "% Cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )

        csv_detalle_semanal = detalle_semanal.to_csv(
            index=False,
            encoding="utf-8-sig",
        ).encode("utf-8-sig")

        st.download_button(
            label="Descargar detalle semanal CSV",
            data=csv_detalle_semanal,
            file_name="detalle_semanal_performance_plantas.csv",
            mime="text/csv",
            use_container_width=True,
        )


# ============================================================
# DETALLE DE FILTROS
# ============================================================

with st.expander("Detalle de filtros aplicados", expanded=False):
    mostrar_detalle_filtros_aplicados = True

    if resumen_filtros_df is None or resumen_filtros_df.empty:
        st.info("No hay detalle de filtros disponible.")
    else:
        st.dataframe(
            resumen_filtros_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Registros antes": st.column_config.NumberColumn(
                    "Registros antes",
                    format="%d",
                ),
                "Registros después": st.column_config.NumberColumn(
                    "Registros después",
                    format="%d",
                ),
                "Registros excluidos": st.column_config.NumberColumn(
                    "Registros excluidos",
                    format="%d",
                ),
                "% retenido": st.column_config.ProgressColumn(
                    "% retenido",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "% excluido": st.column_config.ProgressColumn(
                    "% excluido",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )


# ============================================================
# VISTA PREVIA GENERAL
# ============================================================

with st.expander("Vista previa de datos filtrados", expanded=False):
    limite_vista = st.number_input(
        "Filas a mostrar",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
        key="plantas_limite_vista",
    )

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        "centro_grafico",
        "grupo_planta",
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "dias_tat_total",
        COL_PERFORMANCE_TAT,
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
# DESCARGA GENERAL
# ============================================================

with st.expander("Descargar resultado filtrado", expanded=False):
    st.caption(
        "Parquet es el formato recomendado. CSV se prepara solo cuando lo solicitas."
    )

    firma_export = (
        f"{len(df_dashboard)}_"
        f"{fecha_facturacion_desde}_"
        f"{rango_recepcion}_"
        f"{','.join(estados_sel)}_"
        f"{','.join(grupos_sel)}_"
        f"{','.join(centros_sel)}"
    )

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        preparar_parquet = st.button(
            "Preparar Parquet",
            use_container_width=True,
            key="plantas_preparar_parquet",
        )

        if preparar_parquet:
            with st.spinner("Preparando Parquet..."):
                st.session_state["plantas_parquet_bytes"] = convertir_a_parquet_cache(df_dashboard)
                st.session_state["plantas_parquet_firma"] = firma_export

        if (
            st.session_state.get("plantas_parquet_bytes") is not None
            and st.session_state.get("plantas_parquet_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Parquet",
                data=st.session_state["plantas_parquet_bytes"],
                file_name="performance_plantas_filtrado.parquet",
                mime="application/octet-stream",
                type="primary",
                use_container_width=True,
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True,
            key="plantas_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["plantas_csv_bytes"] = convertir_a_csv_cache(df_dashboard)
                st.session_state["plantas_csv_firma"] = firma_export

        if (
            st.session_state.get("plantas_csv_bytes") is not None
            and st.session_state.get("plantas_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV",
                data=st.session_state["plantas_csv_bytes"],
                file_name="performance_plantas_filtrado.csv",
                mime="text/csv",
                use_container_width=True,
            )
