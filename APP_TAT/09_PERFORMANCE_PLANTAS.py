# ============================================================
# 09_PERFORMANCE_PLANTAS
# Dashboard Performance TAT por plantas / centros
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

import io
import base64
from datetime import date
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

COLOR_CUMPLE = "#EF3E52"        # Rojo original
COLOR_NO_CUMPLE = "#BFC3C7"
COLOR_EN_PROCESO = "#F4B400"
COLOR_NO_APLICA = "#9CA3AF"
COLOR_SIN_DATOS = "#B0B4BB"
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
# FILTROS
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

    tabla["% del total filtrado"] = np.where(
        total > 0,
        tabla["Cantidad"] / total * 100,
        0,
    )

    tabla["% del total filtrado"] = tabla["% del total filtrado"].round(2)

    tabla.loc[len(tabla)] = {
        "Categoría": "Total",
        "Cantidad": total,
        "% del total filtrado": 100.00 if total else 0,
    }

    return tabla


def crear_resumen_grupos(df: pd.DataFrame) -> pd.DataFrame:
    columnas_salida = [
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
            }
        ]
    )

    tabla = pd.concat([tabla, fila_total], ignore_index=True)

    tabla["Cumple"] = tabla["Cumple"].astype(int)
    tabla["No cumple"] = tabla["No cumple"].astype(int)
    tabla["Total evaluable"] = tabla["Total evaluable"].astype(int)
    tabla["% Cumple"] = tabla["% Cumple"].round(2)

    return tabla[columnas_salida]


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

    tabla["Total evaluable"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Total evaluable"] > 0,
        tabla["Cumple"] / tabla["Total evaluable"] * 100,
        0,
    )

    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


def crear_resumen_temporal_grupos(df: pd.DataFrame) -> pd.DataFrame:
    registros = []

    for grupo in ["Prillex", "Rio Loa", "Plantas de servicios"]:
        tabla = crear_resumen_mensual_grupo(df, grupo)

        if tabla.empty:
            continue

        tabla = tabla[tabla["Total evaluable"].gt(0)].copy()

        if tabla.empty:
            continue

        tabla["Grupo planta"] = grupo
        registros.append(tabla)

    if not registros:
        return pd.DataFrame()

    return pd.concat(registros, ignore_index=True)


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
        .groupby(["centro_grafico", COL_PERFORMANCE_TAT])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index="centro_grafico",
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

    return tabla[
        [
            "centro_grafico",
            "Centro",
            "Cumple",
            "No cumple",
            "Total evaluable",
            "% Cumple",
        ]
    ].reset_index(drop=True)


def crear_detalle_semanal(df: pd.DataFrame) -> pd.DataFrame:
    columnas_salida = [
        "Año",
        "Semana",
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

    tabla["% Cumple"] = tabla["% Cumple"].round(2)

    return tabla[columnas_salida].sort_values(
        ["Año", "Semana", "Grupo planta"]
    ).reset_index(drop=True)


def mostrar_detalle_filtros_aplicados(resumen_filtros_df: pd.DataFrame):
    st.markdown("### Detalle de filtros aplicados")
    st.caption(
        "Esta sección muestra cómo cambia la cantidad de registros después de cada filtro."
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

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    col_f1.metric("Registros iniciales", f"{registros_iniciales:,}")
    col_f2.metric("Registros finales", f"{registros_finales:,}")
    col_f3.metric("Registros excluidos", f"{registros_excluidos:,}")
    col_f4.metric("% retenido", f"{pct_retenido:.1f}%")

    st.dataframe(
        resumen,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# GRÁFICOS MATPLOTLIB
# ============================================================

def formatear_ejes(ax):
    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0, colors=COLOR_MUTED)
    ax.set_facecolor("none")


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

    fig, ax = plt.subplots(figsize=(11, 4.6))

    ax.barh(
        y,
        valores,
        color=COLOR_CUMPLE,
        height=0.55,
        label="Cumplimiento TAT",
    )

    for i, valor in enumerate(valores):
        ax.text(
            valor + 1,
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

    ax.set_xlim(0, 105)
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


def grafico_temporal_grupos(tabla: pd.DataFrame):
    st.markdown("### Evolución mensual del cumplimiento por planta")
    st.caption(
        "Evolución mensual del porcentaje de cumplimiento TAT por planta."
    )

    if tabla.empty:
        st.info("No hay datos mensuales evaluables.")
        return

    colores = {
        "Prillex": COLOR_PRILLEX,
        "Rio Loa": COLOR_RIO_LOA,
        "Plantas de servicios": COLOR_SERVICIOS,
    }

    tabla = tabla.sort_values("periodo_fecha").copy()

    periodos = (
        tabla[["periodo_fecha", "periodo_label"]]
        .drop_duplicates()
        .sort_values("periodo_fecha")
    )

    labels = periodos["periodo_label"].astype(str).tolist()
    x_map = {
        periodo: i
        for i, periodo in enumerate(periodos["periodo_fecha"])
    }

    fig, ax = plt.subplots(figsize=(14, 5.4))

    for grupo, data_grupo in tabla.groupby("Grupo planta"):
        data_grupo = data_grupo.sort_values("periodo_fecha").copy()
        x = data_grupo["periodo_fecha"].map(x_map).to_numpy()
        y = data_grupo["% Cumple"].to_numpy()

        ax.plot(
            x,
            y,
            marker="o",
            linewidth=2.8,
            color=colores.get(grupo, COLOR_MUTED),
            label=grupo,
        )

        for xi, yi in zip(x, y):
            ax.text(
                xi,
                yi + 2,
                f"{yi:.0f}%",
                ha="center",
                va="bottom",
                fontsize=8,
                fontweight="bold",
                color=COLOR_TEXTO,
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

    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(
        labels,
        rotation=90,
        ha="center",
        fontsize=9,
        color=COLOR_MUTED,
    )

    ax.set_yticks([0, 25, 50, 65, 75, 100])
    ax.set_yticklabels(
        ["0%", "25%", "50%", "65%", "75%", "100%"],
        color=COLOR_MUTED,
    )

    ax.set_title(
        "Evolución mensual por planta",
        fontsize=15,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=14,
    )

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.38),
        ncol=4,
        frameon=False,
        fontsize=10,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.42)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_mensual_grupo(tabla: pd.DataFrame, grupo: str):
    st.markdown(f"#### {grupo}")

    if tabla.empty:
        st.info("No hay datos evaluables para este grupo.")
        return

    labels = tabla["periodo_label"].astype(str).tolist()
    x = np.arange(len(labels))

    y = tabla["% Cumple"].to_numpy()
    cumple = tabla["Cumple"].astype(int).to_numpy()

    fig, ax = plt.subplots(figsize=(13, 4.8))

    ax.bar(
        x,
        y,
        color=COLOR_CUMPLE,
        width=0.58,
        label="Cumplimiento TAT",
    )

    for i, valor in enumerate(y):
        ax.text(
            i,
            valor + 2,
            f"{valor:.0f}%",
            ha="center",
            va="bottom",
            fontsize=9,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

        if valor >= 8:
            ax.text(
                i,
                valor / 2,
                f"{cumple[i]:,}",
                ha="center",
                va="center",
                fontsize=9,
                color="white",
                fontweight="bold",
            )

    ax.axhline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle="--",
        linewidth=2.5,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    ax.set_ylim(0, 108)
    ax.set_ylabel("% Cumple", color=COLOR_TEXTO)

    ax.set_xticks(x)
    ax.set_xticklabels(
        labels,
        rotation=90,
        ha="center",
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
        bbox_to_anchor=(0.5, -0.35),
        ncol=2,
        frameon=False,
        fontsize=10,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.38)

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


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


# ============================================================
# APP
# ============================================================

mostrar_logo()

st.title("09_PERFORMANCE_PLANTAS")
st.caption(
    "Dashboard de cumplimiento TAT por Prillex, Rio Loa y Plantas de servicios."
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
# INDICADORES
# ============================================================

total_base = len(df_final)
total_filtrado = len(df_dashboard)

cumple = int(df_dashboard[COL_PERFORMANCE_TAT].eq("Cumple").sum())
no_cumple = int(df_dashboard[COL_PERFORMANCE_TAT].eq("No cumple").sum())
en_proceso = int(df_dashboard[COL_PERFORMANCE_TAT].eq("En proceso").sum())
otros = int(df_dashboard[COL_PERFORMANCE_TAT].isin(["No aplica", "Sin datos"]).sum())

total_evaluable = cumple + no_cumple

pct_cumple = cumple / total_evaluable * 100 if total_evaluable else 0
pct_no_cumple = no_cumple / total_evaluable * 100 if total_evaluable else 0
pct_filtrado = total_filtrado / total_base * 100 if total_base else 0

col_k1, col_k2, col_k3, col_k4, col_k5, col_k6 = st.columns(6)

col_k1.metric("Registros base", f"{total_base:,}")
col_k2.metric("Registros filtrados", f"{total_filtrado:,}", f"{pct_filtrado:.1f}%")
col_k3.metric("% Cumple evaluable", f"{pct_cumple:.1f}%", f"{cumple:,} cumple")
col_k4.metric("% No cumple evaluable", f"{pct_no_cumple:.1f}%", f"{no_cumple:,} no cumple")
col_k5.metric("En proceso", f"{en_proceso:,}")
col_k6.metric("Otros / sin datos", f"{otros:,}")


# ============================================================
# DESGLOSE PERFORMANCE
# ============================================================

st.markdown("#### Desglose de datos filtrados por Performance TAT")
st.caption(
    "Cantidad y porcentaje que representa cada categoría sobre la base filtrada."
)

desglose_performance = crear_resumen_performance(df_dashboard)

if desglose_performance.empty:
    st.info("No hay desglose disponible.")
else:
    st.dataframe(
        desglose_performance,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# CUMPLIMIENTO POR PLANTA
# ============================================================

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
            "% Cumple": st.column_config.ProgressColumn(
                "% Cumple",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )


# ============================================================
# EVOLUCIÓN MENSUAL
# ============================================================

resumen_temporal_grupos = crear_resumen_temporal_grupos(df_dashboard)

grafico_temporal_grupos(resumen_temporal_grupos)


# ============================================================
# DETALLE MENSUAL POR GRUPO
# ============================================================

st.markdown("### Detalle mensual por planta")
st.caption(
    "Cada gráfico muestra el cumplimiento mensual individual para cada planta o grupo."
)

for grupo in ["Prillex", "Rio Loa", "Plantas de servicios"]:
    tabla_grupo = crear_resumen_mensual_grupo(df_dashboard, grupo)
    grafico_mensual_grupo(tabla_grupo, grupo)


# ============================================================
# ANÁLISIS POR CENTRO
# ============================================================

with st.expander("Análisis por centro específico", expanded=False):
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
                "% Cumple": st.column_config.ProgressColumn(
                    "% Cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )


# ============================================================
# DETALLE SEMANAL
# ============================================================

with st.expander("Detalle semanal", expanded=False):
    st.caption(
        "Detalle por semana ISO y grupo planta usando fecha_recepcion_final."
    )

    detalle_semanal = crear_detalle_semanal(df_dashboard)

    if detalle_semanal.empty:
        st.info("No hay detalle semanal evaluable.")
    else:
        st.dataframe(
            detalle_semanal,
            use_container_width=True,
            hide_index=True,
            column_config={
                "% Cumple": st.column_config.ProgressColumn(
                    "% Cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )


# ============================================================
# DETALLE DE FILTROS
# ============================================================

with st.expander("Detalle de filtros aplicados", expanded=False):
    mostrar_detalle_filtros_aplicados(resumen_filtros_df)


# ============================================================
# VISTA PREVIA
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
        "tipo_oc",
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "anio_iso_recepcion",
        "semana_iso_recepcion",
        "dias_tat_total",
        COL_PERFORMANCE_TAT,
        "periodo_fecha",
        "periodo_label",
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

    with st.expander("Ver columnas disponibles", expanded=False):
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("**Columnas originales**")
            st.write(df_original.columns.tolist())

        with c2:
            st.markdown("**Columnas finales**")
            st.write(df_final.columns.tolist())


# ============================================================
# DESCARGA
# ============================================================

with st.expander("Descargar resultado filtrado", expanded=False):
    st.caption(
        "Parquet es el formato recomendado. CSV se prepara solo cuando lo solicitas. Excel eliminado."
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
