# ============================================================
# 10_ALERTAS
# Dashboard global de alertas TAT
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Objetivo:
# - Mirada global para atacar vencidos y por vencer
# - Priorización operativa clara
# - Visualizaciones intuitivas
# - Ranking de focos por centro y grupo de compras
# - Tablas accionables con menos ruido visual
# - Expediente tipo tracking de pedido online aplicado al TAT
# ============================================================

import io
import base64
from pathlib import Path
from typing import Any
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"

COLOR_CUMPLE = "#EF3E52"
COLOR_NO_CUMPLE = "#BFC3C7"
COLOR_META = "#0057B8"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"

COLOR_CRITICO = "#DC2626"
COLOR_ATENCION = "#F97316"
COLOR_SEGUIMIENTO = "#F4B400"
COLOR_CONTROLADO = "#16A34A"
COLOR_DATOS = "#CA8A04"
COLOR_SIN_DATOS = "#B0B4BB"
COLOR_CERRADO = "#64748B"

COL_SOLPED = "Solicitud de pedido - ME5A"
COL_OC_ME5A = "Pedido - ME5A"
COL_OC_ME80FN = "Documento de compras - ME80FN"
COL_POS_SOLPED = "Posición solicitud de pedido - ME5A"
COL_POS_OC = "Posición de pedido - ME5A"
COL_MATERIAL = "Material - ME5A"
COL_TEXTO = "Texto breve - ME5A"
COL_CENTRO = "Centro - ME5A"
COL_SOLICITANTE = "Solicitante"
COL_AUTOR = "Autor"
COL_GRUPO_COMPRAS = "Grupo de compras"
COL_TIPO_IMPUTACION = "Tipo de imputación"
COL_TIPO_OC = "tipo_oc"
COL_ORIGEN = "origen"
COL_SISTEMA = "sistema"
COL_NOMBRE_TIPO_COMPRA = "nombre_tipo_compra"
COL_PERF_TAT = "performance_tat_total"
COL_RANGO_INC = "rango_incumplimiento_tat"
COL_INC_TAT = "incumplimiento_tat"
COL_DIAS_TAT = "dias_tat_total"
COL_DIAS_INC = "dias_incumplimiento_tat"
COL_UMBRAL_TAT = "umbral_tat_total"
COL_MONTO = "monto"
COL_ESTADO_RECEPCION_ALERTA = "estado_recepcion"

COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

COL_NIVEL_ALERTA_DESC = "nivel_alerta_descriptivo"

NIVELES_ALERTA_ORDEN = [
    "Crítico",
    "Atención",
    "Seguimiento",
    "Controlado",
    "Datos incompletos",
    "Cerrado",
    "Sin datos",
]

NIVEL_ALERTA_DESCRIPCION = {
    "Crítico": "Vencidos sin recepción",
    "Atención": "Vencen en 0 a 7 días sin recepción",
    "Seguimiento": "Vencen en 8 a 30 días sin recepción",
    "Controlado": "Más de 30 días para vencer",
    "Datos incompletos": "Datos incompletos para calcular vencimiento",
    "Cerrado": "Recepcionados",
    "Sin datos": "Sin datos",
}

NIVELES_ALERTA_DESCRIPTIVOS_ORDEN = [
    "Vencidos sin recepción",
    "Vencen en 0 a 7 días sin recepción",
    "Vencen en 8 a 30 días sin recepción",
    "Más de 30 días para vencer",
    "Datos incompletos para calcular vencimiento",
    "Recepcionados",
    "Sin datos",
]

COLORES_ALERTA_DESC = {
    "Vencidos sin recepción": COLOR_CRITICO,
    "Vencen en 0 a 7 días sin recepción": COLOR_ATENCION,
    "Vencen en 8 a 30 días sin recepción": COLOR_SEGUIMIENTO,
    "Más de 30 días para vencer": COLOR_CONTROLADO,
    "Datos incompletos para calcular vencimiento": COLOR_DATOS,
    "Recepcionados": COLOR_CERRADO,
    "Sin datos": COLOR_SIN_DATOS,
}

FECHAS_CANDIDATAS = [
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

ETAPAS_LINEA_PEDIDO = [
    ("Solicitud", COL_FECHA_SOLICITUD_FINAL),
    ("Liberación", COL_FECHA_LIBERACION_FINAL),
    ("Pedido", COL_FECHA_PEDIDO_FINAL),
    ("Facturación", COL_FECHA_FACTURACION_FINAL),
    ("Recepción", COL_FECHA_RECEPCION_FINAL),
]

CENTROS_NOMBRES = {
    "E002": "Prillex",
    "E021": "CM-Enaex Servicios",
    "E024": "Río Loa",
    "E025": "Planta La Chimba",
    "E026": "Teatinos",
    "E029": "Chuquicamata",
    "E030": "El Tesoro",
    "E031": "La Escondida",
    "E032": "Loma Bayas",
    "E033": "Los Pelambres",
    "E034": "Los Sauces",
    "E035": "Mantos Blancos",
    "E036": "Michilla",
    "E037": "RT",
    "E038": "El Soldado",
    "E039": "Polpaico",
    "E040": "Peldehue",
    "E041": "Esperanza",
    "E042": "Gaby",
    "E044": "Atacama Kozan",
    "E045": "Franke",
    "E046": "Manto Verde",
    "E047": "Polvorín Copiapó",
    "E069": "Guanaco",
    "E071": "Teniente",
    "E076": "Mejillones",
    "E077": "Ministro Hales",
    "E078": "Sierra Gorda",
    "E079": "Planta Quebrada Blanca",
    "E081": "Chuqui Subte",
    "E086": "Antucoya",
    "E087": "Alto Maipo",
    "E088": "Encuentro",
    "E089": "Cerro Colorado",
    "E090": "Collahuasi",
    "E091": "Romeral",
    "E095": "Planta Andina",
    "E097": "Andina",
    "E099": "Salvador",
    "E103": "Zaldívar",
    "E104": "Salares Norte",
    "E105": "Los Colorados",
    "E106": "Cerro N.N.",
    "E107": "Pleito",
    "E108": "Plasma Enaex Servicios",
    "E109": "Carola",
    "E110": "Alto Hospicio SKC Enaex Servicios",
    "E113": "Copiapó SKC Enaex Servicios",
    "E114": "FullRPM Nogales Enaex Servicios",
    "E082": "Nittra Casa Matriz",
    "E083": "Nittra Prillex",
    "E084": "Nittra Paine",
    "E101": "Plasma",
    "E003": "Planta Río Loa",
    "E009": "Planta Chuquicamata",
    "E020": "Planta Polpaico",
    "E057": "Esperanza",
    "E102": "SCL Bodega Arriendo",
    "E043": "El Peñón Subte",
    "E115": "Enaex SKC ING",
    "E027": "Faena Teniente Rajo",
    "E052": "Faena Spence",
}


# ============================================================
# ESTILOS
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

        .kpi-critical {
            color: #DC2626;
            font-weight: 700;
        }

        .alert-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 16px 18px;
            margin: 10px 0;
        }

        .alert-card-critical {
            border-left: 6px solid #dc2626;
            background: #fef2f2;
        }

        .alert-card-warning {
            border-left: 6px solid #f97316;
            background: #fff7ed;
        }

        .alert-card-data {
            border-left: 6px solid #ca8a04;
            background: #fefce8;
        }

        .alert-card-ok {
            border-left: 6px solid #16a34a;
            background: #f0fdf4;
        }

        .alert-title {
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
        }

        .alert-main {
            font-size: 1.15rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 5px;
        }

        .alert-text {
            font-size: 0.88rem;
            color: #334155;
            line-height: 1.45;
        }

        .section-transition {
            padding: 18px 20px;
            border-radius: 16px;
            margin-top: 24px;
            margin-bottom: 14px;
            border: 1px solid #e5e7eb;
        }

        .section-danger {
            background: #fef2f2;
            border-left: 7px solid #dc2626;
        }

        .section-warning {
            background: #fff7ed;
            border-left: 7px solid #f97316;
        }

        .section-data {
            background: #fefce8;
            border-left: 7px solid #ca8a04;
        }

        .section-title {
            font-size: 1.15rem;
            font-weight: 900;
            color: #111827;
            margin-bottom: 4px;
        }

        .section-subtitle {
            font-size: 0.90rem;
            color: #4b5563;
            line-height: 1.45;
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


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def normalizar_codigo_centro(valor: Any) -> str:
    if pd.isna(valor):
        return "Sin dato"

    texto = str(valor).strip()

    if not texto or texto.lower() in ["nan", "none", "nat", "<na>"]:
        return "Sin dato"

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto.upper()


def etiqueta_centro(valor: Any) -> str:
    codigo = normalizar_codigo_centro(valor)
    nombre = CENTROS_NOMBRES.get(codigo)

    if nombre:
        return f"{codigo} · {nombre}"

    return codigo


def convertir_columna_fecha(serie: pd.Series) -> pd.Series:
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

    mask_texto = ~mask_num

    if mask_texto.any():
        resultado.loc[mask_texto] = pd.to_datetime(
            serie.loc[mask_texto],
            errors="coerce",
            dayfirst=True,
        )

    return resultado


def convertir_fechas_visuales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in FECHAS_CANDIDATAS:
        col_norm = col.replace("NME80FN", "ME80FN")

        if col_norm in df.columns:
            convertido = convertir_columna_fecha(df[col_norm])

            if convertido.notna().any():
                df[col_norm] = convertido

    return df


def formato_id(valor: Any) -> str:
    if pd.isna(valor):
        return "-"

    texto = str(valor).strip()

    try:
        numero = float(texto)

        if np.isfinite(numero) and numero.is_integer():
            return str(int(numero))
    except Exception:
        pass

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto


def formato_cantidad(valor: Any) -> str:
    try:
        numero = int(valor)
        return f"{numero:,}".replace(",", ".")
    except Exception:
        return "0"


def formatear_entero(valor: Any) -> str:
    try:
        numero = pd.to_numeric(valor, errors="coerce")

        if pd.isna(numero):
            return "—"

        return f"{int(round(numero)):,}".replace(",", ".")
    except Exception:
        return "—"


def formatear_porcentaje(valor: Any) -> str:
    try:
        numero = pd.to_numeric(valor, errors="coerce")

        if pd.isna(numero):
            return "—"

        return f"{numero:.1f}%"
    except Exception:
        return "—"


def valor_numerico(valor: Any) -> float:
    try:
        return float(pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0])
    except Exception:
        return np.nan


def formato_fecha(valor: Any) -> str:
    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return "-"

    return fecha.strftime("%d-%m-%Y")


def extraer_tipo_oc(valor: Any):
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


def texto_tiempo(dias: Any) -> str:
    dias_num = valor_numerico(dias)

    if pd.isna(dias_num):
        return "Sin dato"

    dias_int = int(round(dias_num))

    if abs(dias_int) < 30:
        return f"{dias_int:,} días".replace(",", ".")

    meses = dias_num / 30.44

    if abs(meses) < 12:
        return (
            f"{meses:,.1f} meses"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    anos = meses / 12

    return (
        f"{anos:,.1f} años"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def texto_dias_restantes(valor: Any) -> str:
    dias = valor_numerico(valor)

    if pd.isna(dias):
        return "Sin fecha calculable"

    dias = int(round(dias))

    if dias < 0:
        return f"Vencido hace {abs(dias):,} días".replace(",", ".")

    if dias == 0:
        return "Vence hoy"

    return f"Vence en {dias:,} días".replace(",", ".")


def primera_columna_existente(df: pd.DataFrame, candidatas: list[str]) -> pd.Series:
    for col in candidatas:
        if col in df.columns:
            return df[col]

    return pd.Series(pd.NaT, index=df.index)


def serie_combinada(df: pd.DataFrame, columnas: list[str]) -> pd.Series:
    resultado = pd.Series(pd.NA, index=df.index)

    for col in columnas:
        if col in df.columns:
            resultado = resultado.where(resultado.notna(), df[col])

    return resultado


def opciones_columna(df: pd.DataFrame, col: str, max_opciones: int = 800) -> list:
    if col not in df.columns:
        return []

    return (
        df[col]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()[:max_opciones]
    )


def columnas_existentes(df: pd.DataFrame, columnas: list[str]) -> list[str]:
    return [col for col in columnas if col in df.columns]


def describir_nivel_alerta(nivel: Any) -> str:
    if pd.isna(nivel):
        return "Sin datos"

    texto = str(nivel).strip()

    return NIVEL_ALERTA_DESCRIPCION.get(texto, texto)


def mensaje_vista_previa(
    titulo: str,
    total_registros: int,
    registros_mostrados: int,
    limite: int,
):
    total_txt = formato_cantidad(total_registros)
    mostrados_txt = formato_cantidad(registros_mostrados)

    if total_registros == 0:
        st.info(f"{titulo}: no hay registros disponibles con los filtros actuales.")
        return

    if registros_mostrados < total_registros:
        st.info(
            f"{titulo}: hay **{total_txt} registros disponibles**. "
            f"Se están mostrando **{mostrados_txt} registros** "
            f"por límite de vista previa ({limite})."
        )
    else:
        st.success(
            f"{titulo}: hay **{total_txt} registros disponibles**. "
            f"Se están mostrando **todos los registros**."
        )


def convertir_tabla_a_excel(df: pd.DataFrame, nombre_hoja: str = "Datos") -> bytes:
    salida = io.BytesIO()

    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name=nombre_hoja[:31],
        )

    return salida.getvalue()


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
            sheet_name="Alertas",
        )

    return output.getvalue()


def generar_nombre_salida(extension: str) -> str:
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"10_ALERTAS_{fecha_hora}_GESTION.{extension}"


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_excel(df)


def contiene_texto(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)

    return df[columna].astype(str).str.contains(
        str(texto).strip(),
        case=False,
        na=False,
        regex=False,
    )


def filtrar_por_ids(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)

    tokens = [
        t.strip().replace(".0", "")
        for t in str(texto)
        .replace("\n", ",")
        .replace(";", ",")
        .replace(" ", ",")
        .split(",")
        if t.strip()
    ]

    if not tokens:
        return pd.Series(True, index=df.index)

    serie = df[columna].astype(str).str.replace(".0", "", regex=False)

    mask = pd.Series(False, index=df.index)

    for token in tokens:
        mask = mask | serie.str.contains(
            token,
            case=False,
            na=False,
            regex=False,
        )

    return mask


# ============================================================
# PREPARACIÓN PANEL ALERTAS
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_panel_alertas(df_original: pd.DataFrame, hoy: pd.Timestamp) -> pd.DataFrame:
    df = limpiar_columnas(df_original.copy())
    df = normalizar_columnas_me80fn(df)
    df = convertir_fechas_visuales(df)

    fecha_recepcion = primera_columna_existente(
        df,
        [
            COL_FECHA_RECEPCION_FINAL,
            "Fecha recepción mercancía - ME80FN",
        ],
    )

    fecha_solicitud = primera_columna_existente(
        df,
        [
            COL_FECHA_SOLICITUD_FINAL,
            "Fecha de solicitud - ME5A",
        ],
    )

    fecha_recepcion = pd.to_datetime(fecha_recepcion, errors="coerce")
    fecha_solicitud = pd.to_datetime(fecha_solicitud, errors="coerce")

    df["fecha_inicio_tat"] = fecha_solicitud
    df["fecha_recepcion_alerta"] = fecha_recepcion

    df[COL_ESTADO_RECEPCION_ALERTA] = np.where(
        df["fecha_recepcion_alerta"].notna(),
        "Recepcionado",
        "Sin recepción",
    )

    if COL_TIPO_OC not in df.columns:
        if COL_OC_ME5A in df.columns:
            df[COL_TIPO_OC] = df[COL_OC_ME5A].apply(extraer_tipo_oc)
        elif COL_OC_ME80FN in df.columns:
            df[COL_TIPO_OC] = df[COL_OC_ME80FN].apply(extraer_tipo_oc)
        else:
            df[COL_TIPO_OC] = pd.NA
    else:
        df[COL_TIPO_OC] = df[COL_TIPO_OC].apply(extraer_tipo_oc)

    if COL_UMBRAL_TAT in df.columns:
        umbral = pd.to_numeric(df[COL_UMBRAL_TAT], errors="coerce")
    else:
        umbral = pd.Series(np.nan, index=df.index, dtype="float64")

    tipo_oc = (
        df[COL_TIPO_OC]
        .astype("string")
        .str.strip()
        .str.replace(".0", "", regex=False)
    )

    umbral = umbral.mask(umbral.isna() & tipo_oc.isin(["35", "45"]), 40)
    umbral = umbral.mask(umbral.isna() & tipo_oc.eq("47"), 70)

    df["umbral_tat_calculado"] = umbral

    df["fecha_vencimiento_tat"] = (
        df["fecha_inicio_tat"]
        + pd.to_timedelta(df["umbral_tat_calculado"], unit="D")
    )

    df["dias_restantes_int"] = (
        df["fecha_vencimiento_tat"]
        - hoy
    ).dt.days

    fecha_fin_operativa = df["fecha_recepcion_alerta"].where(
        df["fecha_recepcion_alerta"].notna(),
        hoy,
    )

    df["dias_transcurridos_alerta"] = (
        fecha_fin_operativa
        - df["fecha_inicio_tat"]
    ).dt.days

    df["exceso_umbral_alerta"] = (
        df["dias_transcurridos_alerta"]
        - df["umbral_tat_calculado"]
    )

    df["tiempo_transcurrido_tat"] = df["dias_transcurridos_alerta"].apply(texto_tiempo)

    df["tiempo_excedido_umbral_texto"] = np.where(
        pd.to_numeric(df["exceso_umbral_alerta"], errors="coerce").gt(0),
        df["exceso_umbral_alerta"].apply(texto_tiempo),
        "Sin exceso",
    )

    df["fecha_vencimiento_texto"] = df["fecha_vencimiento_tat"].apply(formato_fecha)
    df["fecha_solicitud_texto"] = df["fecha_inicio_tat"].apply(formato_fecha)
    df["dias_hasta_vencimiento"] = df["dias_restantes_int"].apply(texto_dias_restantes)

    df["clasificacion_vencimiento"] = clasificar_vencimiento_alerta(df)
    df["bucket_vencimiento"] = clasificar_bucket_vencimiento(df)
    df["nivel_alerta"] = clasificar_nivel_alerta(df)
    df[COL_NIVEL_ALERTA_DESC] = df["nivel_alerta"].apply(describir_nivel_alerta)

    df["ultima_etapa_registrada"] = df.apply(obtener_ultima_etapa, axis=1)
    df["fecha_pendiente"] = df.apply(obtener_fecha_pendiente, axis=1)
    df["accion_sugerida"] = df.apply(obtener_accion_sugerida, axis=1)
    df["score_riesgo"] = df.apply(calcular_score_riesgo, axis=1)

    if COL_CENTRO in df.columns:
        df["centro_label"] = df[COL_CENTRO].apply(etiqueta_centro)
    else:
        df["centro_label"] = "Sin centro"

    return df


def clasificar_vencimiento_alerta(df: pd.DataFrame) -> pd.Series:
    estado = df[COL_ESTADO_RECEPCION_ALERTA].astype(str)
    dias = pd.to_numeric(df["dias_restantes_int"], errors="coerce")

    resultado = pd.Series("Sin datos", index=df.index, dtype="object")

    resultado.loc[estado.eq("Recepcionado")] = "Recepcionado"
    resultado.loc[estado.eq("Sin recepción") & dias.isna()] = "Sin datos"
    resultado.loc[estado.eq("Sin recepción") & dias.lt(0)] = "Vencido"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(0)] = "Vence hoy"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(1)] = "1 día"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(2)] = "2 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(3, 7, inclusive="both")] = "7 días"
    resultado.loc[estado.eq("Sin recepción") & dias.gt(7)] = "+7 días"

    return resultado


def clasificar_bucket_vencimiento(df: pd.DataFrame) -> pd.Series:
    estado = df[COL_ESTADO_RECEPCION_ALERTA].astype(str)
    dias = pd.to_numeric(df["dias_restantes_int"], errors="coerce")

    resultado = pd.Series("Sin datos", index=df.index, dtype="object")

    resultado.loc[estado.eq("Recepcionado")] = "Recepcionado"
    resultado.loc[estado.eq("Sin recepción") & dias.isna()] = "Sin datos"
    resultado.loc[estado.eq("Sin recepción") & dias.lt(0)] = "Vencido"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(0)] = "Vence hoy"
    resultado.loc[estado.eq("Sin recepción") & dias.between(1, 7, inclusive="both")] = "1-7 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(8, 30, inclusive="both")] = "8-30 días"
    resultado.loc[estado.eq("Sin recepción") & dias.gt(30)] = "+30 días"

    return resultado


def clasificar_nivel_alerta(df: pd.DataFrame) -> pd.Series:
    estado = df[COL_ESTADO_RECEPCION_ALERTA].astype(str)
    dias = pd.to_numeric(df["dias_restantes_int"], errors="coerce")

    resultado = pd.Series("Sin datos", index=df.index, dtype="object")

    resultado.loc[estado.eq("Recepcionado")] = "Cerrado"
    resultado.loc[estado.eq("Sin recepción") & dias.isna()] = "Datos incompletos"
    resultado.loc[estado.eq("Sin recepción") & dias.lt(0)] = "Crítico"
    resultado.loc[estado.eq("Sin recepción") & dias.between(0, 7, inclusive="both")] = "Atención"
    resultado.loc[estado.eq("Sin recepción") & dias.between(8, 30, inclusive="both")] = "Seguimiento"
    resultado.loc[estado.eq("Sin recepción") & dias.gt(30)] = "Controlado"

    return resultado


def obtener_ultima_etapa(row: pd.Series) -> str:
    ultima = "Sin etapa registrada"

    for nombre, col in ETAPAS_LINEA_PEDIDO:
        if col in row.index and pd.notna(row.get(col, np.nan)):
            ultima = nombre

    return ultima


def obtener_fecha_pendiente(row: pd.Series) -> str:
    if str(row.get(COL_ESTADO_RECEPCION_ALERTA, "")).strip() == "Recepcionado":
        return "Cerrado"

    for nombre, col in ETAPAS_LINEA_PEDIDO:
        if col in row.index and pd.isna(row.get(col, np.nan)):
            return nombre

    return "Sin fecha pendiente"


def obtener_accion_sugerida(row: pd.Series) -> str:
    nivel = str(row.get("nivel_alerta", ""))

    if nivel == "Crítico":
        return "Priorizar gestión inmediata: confirmar recepción, corregir fecha pendiente o escalar."

    if nivel == "Atención":
        return "Gestionar hoy o esta semana para evitar que pase a vencido."

    if nivel == "Seguimiento":
        return "Planificar seguimiento preventivo antes de que entre en tramo crítico."

    if nivel == "Controlado":
        return "Mantener monitoreo preventivo. Revisar solo si hay monto alto o centro crítico."

    if nivel == "Datos incompletos":
        return "Corregir fecha de solicitud, tipo OC, umbral TAT o fechas finales."

    if nivel == "Cerrado":
        return "Sin acción requerida. Pedido recepcionado."

    return "Revisar registro."


def calcular_score_riesgo(row: pd.Series) -> float:
    nivel = str(row.get("nivel_alerta", ""))
    dias = valor_numerico(row.get("dias_restantes_int", np.nan))
    dias_tat = valor_numerico(row.get(COL_DIAS_TAT, np.nan))
    dias_inc = valor_numerico(row.get(COL_DIAS_INC, np.nan))
    monto = valor_numerico(row.get(COL_MONTO, np.nan))

    score = 0

    if nivel == "Crítico":
        score += 1000

        if pd.notna(dias):
            score += abs(min(dias, 0)) * 5

    elif nivel == "Atención":
        score += 700

        if pd.notna(dias):
            score += max(0, 7 - dias) * 10

    elif nivel == "Seguimiento":
        score += 400

    elif nivel == "Datos incompletos":
        score += 300

    elif nivel == "Controlado":
        score += 100

    if pd.notna(dias_inc):
        score += max(dias_inc, 0) * 2

    if pd.notna(dias_tat):
        score += max(dias_tat, 0) * 0.1

    if pd.notna(monto) and monto > 0:
        score += min(np.log10(monto + 1) * 10, 100)

    return round(score, 2)


# ============================================================
# RESÚMENES
# ============================================================

def construir_resumen_ejecutivo(df_total: pd.DataFrame, df_filtrado: pd.DataFrame) -> dict:
    total_archivo = len(df_total)
    total_filtrado = len(df_filtrado)

    pct_filtrado = (
        total_filtrado / total_archivo * 100
        if total_archivo
        else 0
    )

    estado = df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str)

    dias = pd.to_numeric(
        df_filtrado.get("dias_restantes_int", pd.Series(np.nan, index=df_filtrado.index)),
        errors="coerce",
    )

    sin_recepcion = estado.eq("Sin recepción")
    recepcionados = estado.eq("Recepcionado")

    vencidos = int((sin_recepcion & dias.lt(0)).sum())
    vence_hoy = int((sin_recepcion & dias.eq(0)).sum())
    proximos_1_7 = int((sin_recepcion & dias.between(1, 7, inclusive="both")).sum())
    proximos_8_30 = int((sin_recepcion & dias.between(8, 30, inclusive="both")).sum())
    proximos = vence_hoy + proximos_1_7 + proximos_8_30
    preventivo = int((sin_recepcion & dias.gt(30)).sum())
    sin_fecha = int((sin_recepcion & dias.isna()).sum())
    recepcionados_total = int(recepcionados.sum())
    foco_accion = vencidos + proximos + sin_fecha

    if vencidos > 0:
        semaforo = "Crítico"
        mensaje = f"Hay {formato_cantidad(vencidos)} registros vencidos sin recepción."
        accion = "Priorizar vencidos sin recepción, ordenados por score de riesgo."
    elif proximos > 0:
        semaforo = "Atención"
        mensaje = f"Hay {formato_cantidad(proximos)} registros próximos a vencer en los próximos 30 días."
        accion = "Gestionar próximos vencimientos antes de que pasen a vencidos."
    elif sin_fecha > 0:
        semaforo = "Datos incompletos"
        mensaje = f"Hay {formato_cantidad(sin_fecha)} registros sin fecha de vencimiento calculable."
        accion = "Corregir datos base: fecha de solicitud, tipo OC, umbral TAT o fechas finales."
    else:
        semaforo = "Controlado"
        mensaje = "No se observan vencidos ni próximos a vencer sin recepción con los filtros actuales."
        accion = "Mantener seguimiento preventivo."

    return {
        "total_archivo": total_archivo,
        "total_filtrado": total_filtrado,
        "pct_filtrado": pct_filtrado,
        "vencidos": vencidos,
        "vence_hoy": vence_hoy,
        "proximos_1_7": proximos_1_7,
        "proximos_8_30": proximos_8_30,
        "proximos": proximos,
        "preventivo": preventivo,
        "sin_fecha": sin_fecha,
        "recepcionados": recepcionados_total,
        "foco_accion": foco_accion,
        "semaforo": semaforo,
        "semaforo_descriptivo": describir_nivel_alerta(semaforo),
        "mensaje": mensaje,
        "accion": accion,
    }


def crear_desglose_alertas(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    tabla = (
        df[COL_NIVEL_ALERTA_DESC]
        .value_counts()
        .reindex(NIVELES_ALERTA_DESCRIPTIVOS_ORDEN, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Nivel alerta", "Cantidad"]

    total = int(tabla["Cantidad"].sum())

    tabla["% del total filtrado"] = np.where(
        total > 0,
        tabla["Cantidad"] / total * 100,
        0,
    )

    tabla["% del total filtrado"] = tabla["% del total filtrado"].round(2)
    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    return tabla


def crear_plan_ataque(df: pd.DataFrame) -> pd.DataFrame:
    tabla = crear_desglose_alertas(df)

    if tabla.empty:
        return pd.DataFrame()

    acciones = {
        "Vencidos sin recepción": "Atacar primero. Confirmar recepción, desbloquear etapa pendiente o escalar.",
        "Vencen en 0 a 7 días sin recepción": "Gestionar hoy o esta semana. Evitar que pasen a vencidos.",
        "Vencen en 8 a 30 días sin recepción": "Planificar seguimiento preventivo y revisar centros/compradores críticos.",
        "Más de 30 días para vencer": "Monitorear preventivamente.",
        "Datos incompletos para calcular vencimiento": "Corregir datos base para calcular vencimiento.",
        "Recepcionados": "Sin acción requerida.",
        "Sin datos": "Revisar consistencia de datos.",
    }

    prioridad = {
        "Vencidos sin recepción": 1,
        "Vencen en 0 a 7 días sin recepción": 2,
        "Vencen en 8 a 30 días sin recepción": 3,
        "Datos incompletos para calcular vencimiento": 4,
        "Más de 30 días para vencer": 5,
        "Recepcionados": 6,
        "Sin datos": 7,
    }

    tabla["Acción sugerida"] = tabla["Nivel alerta"].map(acciones).fillna("Revisar registros.")
    tabla["Prioridad"] = tabla["Nivel alerta"].map(prioridad).fillna(99)

    tabla = tabla.sort_values("Prioridad").drop(columns="Prioridad").reset_index(drop=True)

    return tabla


def crear_clasificacion_vencimiento_detallada(df: pd.DataFrame) -> pd.Series:
    estado = df[COL_ESTADO_RECEPCION_ALERTA].astype(str)

    dias = pd.to_numeric(
        df.get("dias_restantes_int", pd.Series(np.nan, index=df.index)),
        errors="coerce",
    )

    resultado = pd.Series("Sin datos", index=df.index, dtype="object")

    resultado.loc[estado.eq("Recepcionado")] = "Recepcionado"
    resultado.loc[estado.eq("Sin recepción") & dias.isna()] = "Sin datos"
    resultado.loc[estado.eq("Sin recepción") & dias.lt(0)] = "Vencido"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(0)] = "Vence hoy"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(1)] = "1 día"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(2)] = "2 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(3, 7, inclusive="both")] = "3-7 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(8, 15, inclusive="both")] = "8-15 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(16, 30, inclusive="both")] = "16-30 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(31, 60, inclusive="both")] = "31-60 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(61, 90, inclusive="both")] = "61-90 días"
    resultado.loc[estado.eq("Sin recepción") & dias.gt(90)] = "+90 días"

    return resultado


def crear_resumen_buckets(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    df_temp = df.copy()
    df_temp["vencimiento_detallado"] = crear_clasificacion_vencimiento_detallada(df_temp)

    orden = [
        "Vencido",
        "Vence hoy",
        "1 día",
        "2 días",
        "3-7 días",
        "8-15 días",
        "16-30 días",
        "31-60 días",
        "61-90 días",
        "+90 días",
        "Sin datos",
        "Recepcionado",
    ]

    tabla = (
        df_temp["vencimiento_detallado"]
        .value_counts()
        .reindex(orden, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Clasificación", "Cantidad"]

    total = int(tabla["Cantidad"].sum())

    tabla["%"] = np.where(
        total > 0,
        tabla["Cantidad"] / total * 100,
        0,
    )

    tabla["%"] = tabla["%"].round(2)
    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    return tabla


def crear_tabla_prioridad(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()

    if "score_riesgo" in base.columns:
        base = base.sort_values(
            "score_riesgo",
            ascending=False,
        ).copy()

    solped = serie_combinada(base, [COL_SOLPED]).apply(formato_id)
    pedido = serie_combinada(base, [COL_OC_ME5A, COL_OC_ME80FN]).apply(formato_id)
    posicion = serie_combinada(base, [COL_POS_SOLPED, COL_POS_OC]).apply(formato_id)

    tabla = pd.DataFrame(
        {
            "Nivel alerta": base.get(COL_NIVEL_ALERTA_DESC, pd.Series("-", index=base.index)),
            "Fecha solicitud": base.get("fecha_solicitud_texto", pd.Series("-", index=base.index)),
            "Fecha vencimiento": base.get("fecha_vencimiento_texto", pd.Series("-", index=base.index)),
            "Días hasta vencimiento": base.get("dias_hasta_vencimiento", pd.Series("-", index=base.index)),
            "SolPed": solped,
            "Pedido": pedido,
            "Posición": posicion,
            "Material": serie_combinada(base, [COL_MATERIAL]).fillna("-"),
            "Texto breve": serie_combinada(base, [COL_TEXTO]).fillna("-"),
            "Centro": serie_combinada(base, [COL_CENTRO]).fillna("-"),
            "Grupo de compras": serie_combinada(base, [COL_GRUPO_COMPRAS]).fillna("-"),
            "Tipo OC": serie_combinada(base, [COL_TIPO_OC]).fillna("-"),
            "Sistema": serie_combinada(base, [COL_SISTEMA]).fillna("-"),
            "Origen": serie_combinada(base, [COL_ORIGEN]).fillna("-"),
            "Performance TAT total": serie_combinada(base, [COL_PERF_TAT]).fillna("-"),
            "Días TAT total": serie_combinada(base, [COL_DIAS_TAT]).fillna("-"),
            "Días incumplimiento": serie_combinada(base, [COL_DIAS_INC]).fillna("-"),
            "Umbral TAT": serie_combinada(base, [COL_UMBRAL_TAT, "umbral_tat_calculado"]).fillna("-"),
        }
    )

    return tabla.reset_index(drop=True)


def crear_ranking_centros(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "centro_label" not in df.columns:
        return pd.DataFrame()

    tabla = (
        df
        .groupby("centro_label")
        .agg(
            Registros=("nivel_alerta", "size"),
            Vencidos=("nivel_alerta", lambda s: int(s.eq("Crítico").sum())),
            Proximos=("nivel_alerta", lambda s: int(s.isin(["Atención", "Seguimiento"]).sum())),
            Datos_incompletos=("nivel_alerta", lambda s: int(s.eq("Datos incompletos").sum())),
            Recepcionados=("nivel_alerta", lambda s: int(s.eq("Cerrado").sum())),
            Score_promedio=("score_riesgo", "mean"),
        )
        .reset_index()
        .rename(columns={"centro_label": "Centro"})
    )

    tabla["Foco acción"] = (
        tabla["Vencidos"]
        + tabla["Proximos"]
        + tabla["Datos_incompletos"]
    )

    tabla["% foco acción"] = np.where(
        tabla["Registros"] > 0,
        tabla["Foco acción"] / tabla["Registros"] * 100,
        0,
    )

    tabla["Score_promedio"] = tabla["Score_promedio"].round(2)
    tabla["% foco acción"] = tabla["% foco acción"].round(2)

    tabla = tabla.sort_values(
        ["Foco acción", "Vencidos", "Score_promedio", "Registros"],
        ascending=[False, False, False, False],
    )

    return tabla.reset_index(drop=True)


def crear_ranking_grupo_compras(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or COL_GRUPO_COMPRAS not in df.columns:
        return pd.DataFrame()

    tabla = (
        df
        .groupby(COL_GRUPO_COMPRAS, dropna=False)
        .agg(
            Registros=(COL_GRUPO_COMPRAS, "size"),
            Vencidos=("nivel_alerta", lambda s: int(s.eq("Crítico").sum())),
            Proximos=("nivel_alerta", lambda s: int(s.isin(["Atención", "Seguimiento"]).sum())),
            Datos_incompletos=("nivel_alerta", lambda s: int(s.eq("Datos incompletos").sum())),
            Recepcionados=("nivel_alerta", lambda s: int(s.eq("Cerrado").sum())),
            Score_promedio=("score_riesgo", "mean"),
        )
        .reset_index()
        .rename(columns={COL_GRUPO_COMPRAS: "Grupo de compras"})
    )

    tabla["Foco acción"] = (
        tabla["Vencidos"]
        + tabla["Proximos"]
        + tabla["Datos_incompletos"]
    )

    tabla["% foco acción"] = np.where(
        tabla["Registros"] > 0,
        tabla["Foco acción"] / tabla["Registros"] * 100,
        0,
    )

    tabla["Score_promedio"] = tabla["Score_promedio"].round(2)
    tabla["% foco acción"] = tabla["% foco acción"].round(2)

    tabla = tabla.sort_values(
        ["Foco acción", "Vencidos", "Score_promedio", "Registros"],
        ascending=[False, False, False, False],
    )

    return tabla.reset_index(drop=True)


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
            "% excluido": round((antes - despues) / antes * 100, 2) if antes else 0,
        }
    )


def aplicar_filtros_alertas(
    df_base: pd.DataFrame,
    filtros: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    barra = st.progress(0, text="Preparando filtros...")

    df = df_base.copy()

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

    barra.progress(15, text="Aplicando búsquedas...")

    busquedas_id = [
        ("SolPed", COL_SOLPED, filtros.get("buscar_solped", "")),
        ("Pedido", COL_OC_ME5A, filtros.get("buscar_pedido", "")),
        ("Material", COL_MATERIAL, filtros.get("buscar_material", "")),
    ]

    for nombre, columna, texto in busquedas_id:
        if str(texto).strip() and columna in df.columns:
            antes = df.copy()
            df = df[filtrar_por_ids(df, columna, texto)].copy()

            registrar_paso_filtro(
                resumen,
                f"Filtro búsqueda {nombre}",
                nombre,
                texto,
                antes,
                df,
            )

    texto_breve = filtros.get("buscar_texto", "")

    if str(texto_breve).strip() and COL_TEXTO in df.columns:
        antes = df.copy()
        df = df[contiene_texto(df, COL_TEXTO, texto_breve)].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro búsqueda texto",
            "Texto breve",
            texto_breve,
            antes,
            df,
        )

    barra.progress(35, text="Aplicando rango de vencimiento...")

    rango_vencimiento = filtros.get("rango_vencimiento")

    if rango_vencimiento is not None:
        if isinstance(rango_vencimiento, (tuple, list)) and len(rango_vencimiento) == 2:
            antes = df.copy()

            fecha_ini = pd.Timestamp(rango_vencimiento[0])
            fecha_fin = (
                pd.Timestamp(rango_vencimiento[1])
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
            )

            df = df[
                df["fecha_vencimiento_tat"].notna()
                & df["fecha_vencimiento_tat"].between(fecha_ini, fecha_fin)
            ].copy()

            registrar_paso_filtro(
                resumen,
                "Filtro fecha",
                "Fecha vencimiento TAT",
                f"{fecha_ini.date()} a {fecha_fin.date()}",
                antes,
                df,
            )

    barra.progress(65, text="Aplicando filtros de alerta...")

    filtros_multiselect = [
        ("Tipo de alerta", COL_NIVEL_ALERTA_DESC, filtros.get("niveles", [])),
        ("Clasificación vencimiento", "clasificacion_vencimiento", filtros.get("clasificaciones", [])),
        ("Estado recepción", COL_ESTADO_RECEPCION_ALERTA, filtros.get("estados_recepcion", [])),
        ("Centro", COL_CENTRO, filtros.get("centros", [])),
        ("Grupo compras", COL_GRUPO_COMPRAS, filtros.get("grupos_compras", [])),
        ("Sistema", COL_SISTEMA, filtros.get("sistemas", [])),
        ("Tipo OC", COL_TIPO_OC, filtros.get("tipos_oc", [])),
    ]

    for nombre, columna, seleccion in filtros_multiselect:
        if seleccion and columna in df.columns:
            antes = df.copy()

            seleccion_norm = [str(x) for x in seleccion]

            df = df[
                df[columna].astype(str).isin(seleccion_norm)
            ].copy()

            registrar_paso_filtro(
                resumen,
                f"Filtro {nombre}",
                nombre,
                ", ".join(seleccion_norm),
                antes,
                df,
            )

    barra.progress(90, text="Ordenando por prioridad...")

    if "score_riesgo" in df.columns:
        df = df.sort_values("score_riesgo", ascending=False).copy()

    barra.progress(100, text="Filtros aplicados correctamente.")

    return df, pd.DataFrame(resumen)


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

    cantidades = tabla["Cantidad"].astype(int).to_numpy()
    porcentajes = tabla["%"].astype(float).to_numpy()
    etiquetas = tabla["Categoría"].astype(str).tolist()
    colores = tabla["Categoría"].map(colores_mapa).tolist()

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


def grafico_donut_alertas_porcentual(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay datos para graficar.")
        return

    data = tabla.copy()
    data = data[data["Cantidad"].gt(0)].copy()

    if data.empty:
        st.info("No hay categorías disponibles.")
        return

    data["Color"] = data["Nivel alerta"].map(COLORES_ALERTA_DESC).fillna(COLOR_MUTED)

    total = int(data["Cantidad"].sum())
    cantidades = data["Cantidad"].astype(int).to_numpy()
    etiquetas = data["Nivel alerta"].astype(str).tolist()
    colores = data["Color"].tolist()

    col_grafico, col_tabla = st.columns([1.15, 1])

    with col_grafico:
        fig, ax = plt.subplots(figsize=(8.2, 6.2), dpi=180)

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
            autotext.set_fontsize(9.5)
            autotext.set_color("white")

        ax.text(
            0,
            0.08,
            formato_cantidad(total),
            ha="center",
            va="center",
            fontsize=23,
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
            fontweight="bold",
            color=COLOR_MUTED,
        )

        porcentajes = np.where(
            total > 0,
            cantidades / total * 100,
            0,
        )

        etiquetas_leyenda = [
            f"{etiqueta} · {cantidad:,} · {pct:.1f}%".replace(",", ".")
            for etiqueta, cantidad, pct in zip(etiquetas, cantidades, porcentajes)
        ]

        ax.legend(
            wedges,
            etiquetas_leyenda,
            title="Leyenda",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
            fontsize=8.5,
            title_fontsize=9.5,
        )

        ax.set_title(
            "Distribución porcentual por tipo de alerta",
            fontsize=14,
            fontweight="bold",
            color=COLOR_TEXTO,
            pad=16,
        )

        ax.axis("equal")
        fig.patch.set_alpha(0)
        fig.tight_layout()
        fig.subplots_adjust(right=0.67)

        st.pyplot(fig, clear_figure=True, use_container_width=True)

    with col_tabla:
        st.markdown("#### Tabla de alertas")
        st.caption("Base: registros filtrados.")

        st.dataframe(
            data[
                [
                    "Nivel alerta",
                    "Cantidad",
                    "% del total filtrado",
                ]
            ],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Cantidad": st.column_config.NumberColumn(
                    "Cantidad",
                    format="%d",
                ),
                "% del total filtrado": st.column_config.ProgressColumn(
                    "% del total filtrado",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )


def grafico_alertas_valores_absolutos(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay datos para graficar.")
        return

    data = tabla.copy()
    data = data[data["Cantidad"].gt(0)].copy()

    if data.empty:
        st.info("No hay clasificación de vencimientos.")
        return

    data = data.sort_values("Cantidad", ascending=True)

    colores_mapa = {
        "Vencido": COLOR_CRITICO,
        "Vence hoy": COLOR_CRITICO,
        "1 día": COLOR_ATENCION,
        "2 días": COLOR_ATENCION,
        "3-7 días": COLOR_SEGUIMIENTO,
        "8-15 días": COLOR_SEGUIMIENTO,
        "16-30 días": COLOR_CONTROLADO,
        "31-60 días": COLOR_CONTROLADO,
        "61-90 días": "#15803D",
        "+90 días": "#166534",
        "Sin datos": COLOR_SIN_DATOS,
        "Recepcionado": COLOR_CERRADO,
    }

    y = np.arange(len(data))

    fig, ax = plt.subplots(figsize=(9.5, max(5.8, len(data) * 0.45)), dpi=180)

    ax.barh(
        y,
        data["Cantidad"],
        color=[colores_mapa.get(x, COLOR_MUTED) for x in data["Clasificación"]],
        height=0.55,
    )

    max_cantidad = max(data["Cantidad"]) if len(data) else 0

    for i, cantidad in enumerate(data["Cantidad"]):
        ax.text(
            cantidad + max(max_cantidad * 0.015, 0.5),
            i,
            formato_cantidad(cantidad),
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(data["Clasificación"], color=COLOR_MUTED)
    ax.set_xlabel("Cantidad de registros", color=COLOR_TEXTO)

    ax.set_title(
        "Valores absolutos por vencimiento detallado",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=12,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_plan_ataque(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay datos para graficar plan de ataque.")
        return

    data = tabla.copy()
    data = data[data["Cantidad"].gt(0)].copy()

    if data.empty:
        st.info("No hay categorías con cantidad mayor a cero.")
        return

    data = data.sort_values("Cantidad", ascending=True)

    labels = data["Nivel alerta"].astype(str).tolist()
    valores = data["Cantidad"].astype(int).to_numpy()
    porcentajes = data["% del total filtrado"].astype(float).to_numpy()
    colores = [COLORES_ALERTA_DESC.get(x, COLOR_MUTED) for x in labels]

    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(12, max(5, len(labels) * 0.62)), dpi=180)

    barras = ax.barh(
        y,
        valores,
        color=colores,
        height=0.58,
    )

    max_valor = max(valores) if len(valores) else 0

    ax.set_xlim(0, max(max_valor * 1.25, 10))

    for barra, valor, pct in zip(barras, valores, porcentajes):
        ax.text(
            barra.get_width() + max(max_valor * 0.02, 0.5),
            barra.get_y() + barra.get_height() / 2,
            f"{valor:,} · {pct:.1f}%".replace(",", "."),
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10, color=COLOR_MUTED)

    ax.set_title(
        "Plan de ataque: dónde concentrar la gestión",
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=16,
    )

    ax.set_xlabel("Cantidad de registros", color=COLOR_TEXTO)

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_top_ranking(
    tabla: pd.DataFrame,
    columna_nombre: str,
    titulo: str,
    top_n: int = 12,
):
    if tabla.empty or columna_nombre not in tabla.columns:
        st.info("No hay datos para graficar ranking.")
        return

    data = tabla.head(top_n).copy()

    if data.empty:
        st.info("No hay datos para graficar ranking.")
        return

    data = data.sort_values("Foco acción", ascending=True)

    labels = data[columna_nombre].astype(str).tolist()
    valores = data["Foco acción"].astype(int).to_numpy()

    y = np.arange(len(labels))

    fig, ax = plt.subplots(figsize=(12, max(5.5, len(labels) * 0.42)), dpi=180)

    barras = ax.barh(
        y,
        valores,
        color=COLOR_CRITICO,
        height=0.58,
    )

    max_valor = max(valores) if len(valores) else 0

    ax.set_xlim(0, max(max_valor * 1.25, 10))

    for barra, valor in zip(barras, valores):
        ax.text(
            barra.get_width() + max(max_valor * 0.02, 0.5),
            barra.get_y() + barra.get_height() / 2,
            f"{valor:,}".replace(",", "."),
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9, color=COLOR_MUTED)

    ax.set_title(
        titulo,
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=16,
    )

    ax.set_xlabel("Registros foco acción", color=COLOR_TEXTO)

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_vencidos_por_anio(df_vencidos: pd.DataFrame):
    if df_vencidos.empty:
        st.info("No hay vencidos sin recepción para graficar.")
        return

    df_grafico = df_vencidos.copy()

    df_grafico["fecha_vencimiento_tat"] = pd.to_datetime(
        df_grafico["fecha_vencimiento_tat"],
        errors="coerce",
    )

    df_grafico = df_grafico[df_grafico["fecha_vencimiento_tat"].notna()].copy()

    if df_grafico.empty:
        st.info("No hay fechas de vencimiento válidas para graficar por año.")
        return

    df_grafico["anio_vencimiento"] = df_grafico["fecha_vencimiento_tat"].dt.year

    tabla = (
        df_grafico
        .groupby("anio_vencimiento")
        .size()
        .reset_index(name="Cantidad")
        .sort_values("anio_vencimiento", ascending=True)
    )

    x = np.arange(len(tabla))

    fig, ax = plt.subplots(figsize=(8.4, 4.8), dpi=180)

    ax.bar(
        x,
        tabla["Cantidad"],
        color=COLOR_CRITICO,
        width=0.58,
    )

    max_cantidad = max(tabla["Cantidad"]) if len(tabla) else 0

    for i, cantidad in enumerate(tabla["Cantidad"]):
        ax.text(
            i,
            cantidad + max(max_cantidad * 0.02, 1),
            formato_cantidad(cantidad),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        tabla["anio_vencimiento"].astype(str),
        color=COLOR_MUTED,
    )

    ax.set_ylabel("Cantidad de registros", color=COLOR_TEXTO)

    ax.set_title(
        "Concentración de vencidos sin recepción por año",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=12,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


# ============================================================
# VISUALES NATIVOS
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


def mostrar_card_estado(resumen: dict):
    semaforo = resumen.get("semaforo", "Sin datos")
    semaforo_desc = resumen.get("semaforo_descriptivo", describir_nivel_alerta(semaforo))

    if semaforo == "Crítico":
        clase = "alert-card alert-card-critical"
        color = "#991b1b"
        titulo = "Estado global crítico"
    elif semaforo == "Atención":
        clase = "alert-card alert-card-warning"
        color = "#9a3412"
        titulo = "Estado global en atención"
    elif semaforo == "Datos incompletos":
        clase = "alert-card alert-card-data"
        color = "#854d0e"
        titulo = "Estado global con datos incompletos"
    else:
        clase = "alert-card alert-card-ok"
        color = "#166534"
        titulo = "Estado global controlado"

    st.markdown(
        f"""
        <div class="{clase}">
            <div class="alert-title" style="color:{color};">{titulo}</div>
            <div class="alert-main">{semaforo_desc}</div>
            <div class="alert-text">{resumen.get("mensaje", "")}</div>
            <div class="alert-text" style="margin-top:8px;"><b>Acción sugerida:</b> {resumen.get("accion", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_detalle_filtros_reducido(resumen_filtros_df: pd.DataFrame):
    if resumen_filtros_df.empty:
        st.info("No hay detalle de filtros disponible.")
        return

    columnas = [
        "Filtro aplicado",
        "Valor",
        "% retenido",
        "% excluido",
    ]

    columnas = [
        col for col in columnas
        if col in resumen_filtros_df.columns
    ]

    tabla = resumen_filtros_df[columnas].copy()

    st.dataframe(
        tabla,
        use_container_width=True,
        hide_index=True,
        column_config={
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


def mostrar_tabla_alertas(
    df: pd.DataFrame,
    titulo: str,
    descripcion: str,
    limite: int = 300,
):
    st.markdown(f"### {titulo}")
    st.caption(descripcion)

    tabla = crear_tabla_prioridad(df)

    if tabla.empty:
        st.success("No hay registros para esta categoría con los filtros actuales.")
        return

    total_registros = len(tabla)
    registros_mostrados = min(limite, total_registros)

    mensaje_vista_previa(
        titulo=titulo,
        total_registros=total_registros,
        registros_mostrados=registros_mostrados,
        limite=limite,
    )

    st.dataframe(
        tabla.head(registros_mostrados),
        use_container_width=True,
        hide_index=True,
    )

    nombre_archivo = (
        titulo.lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
        .replace("ñ", "n")
    )

    excel_bytes = convertir_tabla_a_excel(
        tabla,
        nombre_hoja="Datos",
    )

    st.download_button(
        label="Descargar data en Excel",
        data=excel_bytes,
        file_name=f"{nombre_archivo}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        key=f"descargar_excel_{nombre_archivo}",
    )


def mostrar_vencidos_por_anio(df_vencidos: pd.DataFrame):
    st.markdown("### Vencidos sin recepción por año")
    st.caption(
        "Los registros vencidos sin recepción se separan según el año de la fecha de vencimiento TAT."
    )

    if df_vencidos.empty:
        st.success("No hay registros vencidos sin recepción con los filtros actuales.")
        return

    df_temp = df_vencidos.copy()

    df_temp["fecha_vencimiento_tat"] = pd.to_datetime(
        df_temp["fecha_vencimiento_tat"],
        errors="coerce",
    )

    df_temp["anio_vencimiento"] = df_temp["fecha_vencimiento_tat"].dt.year

    df_temp["dias_vencido"] = (
        pd.Timestamp.today().normalize()
        - df_temp["fecha_vencimiento_tat"]
    ).dt.days

    df_temp["dias_vencido"] = pd.to_numeric(
        df_temp["dias_vencido"],
        errors="coerce",
    )

    anios_validos = (
        df_temp["anio_vencimiento"]
        .dropna()
        .astype(int)
        .sort_values(ascending=True)
        .unique()
        .tolist()
    )

    tiene_sin_anio = df_temp["anio_vencimiento"].isna().any()

    total_vencidos = len(df_temp)

    st.info(
        f"Total vencidos sin recepción: **{formato_cantidad(total_vencidos)} registros**."
    )

    for anio in anios_validos:
        df_anio = df_temp[
            df_temp["anio_vencimiento"].eq(anio)
        ].copy()

        dias_validos = df_anio["dias_vencido"].dropna()

        dias_min = int(dias_validos.min()) if not dias_validos.empty else 0
        dias_max = int(dias_validos.max()) if not dias_validos.empty else 0

        with st.expander(
            f"Año {anio} · {formato_cantidad(len(df_anio))} registros",
            expanded=True,
        ):
            m1, m2, m3 = st.columns(3)

            m1.metric("Vencidos", formato_cantidad(len(df_anio)))
            m2.metric("Mínimo días vencido", formato_cantidad(dias_min))
            m3.metric("Máximo días vencido", formato_cantidad(dias_max))

            mostrar_tabla_alertas(
                df_anio,
                f"Vencidos sin recepción {anio}",
                f"Registros vencidos sin recepción con fecha de vencimiento TAT durante {anio}.",
                limite=300,
            )

    if tiene_sin_anio:
        df_sin_anio = df_temp[
            df_temp["anio_vencimiento"].isna()
        ].copy()

        with st.expander(
            f"Sin año de vencimiento · {formato_cantidad(len(df_sin_anio))} registros",
            expanded=True,
        ):
            mostrar_tabla_alertas(
                df_sin_anio,
                "Vencidos sin recepción sin año calculable",
                "Registros vencidos sin recepción sin fecha de vencimiento TAT válida.",
                limite=300,
            )


def mostrar_proximos_por_rango(df_proximos: pd.DataFrame):
    st.markdown("### Vencen en 0 a 30 días sin recepción")
    st.caption(
        "Los próximos vencimientos se separan por rangos de días restantes para priorizar la gestión."
    )

    if df_proximos.empty:
        st.success("No hay registros próximos a vencer con los filtros actuales.")
        return

    df_temp = df_proximos.copy()

    df_temp["dias_restantes_int"] = pd.to_numeric(
        df_temp["dias_restantes_int"],
        errors="coerce",
    )

    rangos = [
        {
            "nombre": "Vence hoy",
            "descripcion": "Registros que vencen hoy y aún no tienen recepción.",
            "mask": df_temp["dias_restantes_int"].eq(0),
        },
        {
            "nombre": "Vencen en 1 a 2 días",
            "descripcion": "Registros que vencen entre 1 y 2 días.",
            "mask": df_temp["dias_restantes_int"].between(1, 2, inclusive="both"),
        },
        {
            "nombre": "Vencen en 3 a 7 días",
            "descripcion": "Registros que vencen entre 3 y 7 días.",
            "mask": df_temp["dias_restantes_int"].between(3, 7, inclusive="both"),
        },
        {
            "nombre": "Vencen en 8 a 15 días",
            "descripcion": "Registros que vencen entre 8 y 15 días.",
            "mask": df_temp["dias_restantes_int"].between(8, 15, inclusive="both"),
        },
        {
            "nombre": "Vencen en 16 a 30 días",
            "descripcion": "Registros que vencen entre 16 y 30 días.",
            "mask": df_temp["dias_restantes_int"].between(16, 30, inclusive="both"),
        },
    ]

    total_proximos = len(df_temp)

    st.info(
        f"Total próximos 0-30 días sin recepción: **{formato_cantidad(total_proximos)} registros**."
    )

    for item in rangos:
        df_rango = df_temp[item["mask"]].copy()

        if df_rango.empty:
            continue

        dias_validos = df_rango["dias_restantes_int"].dropna()

        dias_min = int(dias_validos.min()) if not dias_validos.empty else 0
        dias_max = int(dias_validos.max()) if not dias_validos.empty else 0

        with st.expander(
            f"{item['nombre']} · {formato_cantidad(len(df_rango))} registros",
            expanded=True,
        ):
            r1, r2, r3 = st.columns(3)

            r1.metric("Registros", formato_cantidad(len(df_rango)))
            r2.metric("Mínimo días restantes", formato_cantidad(dias_min))
            r3.metric("Máximo días restantes", formato_cantidad(dias_max))

            mostrar_tabla_alertas(
                df_rango,
                item["nombre"],
                item["descripcion"],
                limite=300,
            )


def mostrar_tracker_tat(row: pd.Series):
    estado_recepcion = str(row.get(COL_ESTADO_RECEPCION_ALERTA, ""))
    pendiente = str(row.get("fecha_pendiente", ""))

    estados_etapas = []

    for nombre, col in ETAPAS_LINEA_PEDIDO:
        fecha = pd.to_datetime(row.get(col, pd.NaT), errors="coerce")

        if pd.notna(fecha):
            estados_etapas.append(
                {
                    "nombre": nombre,
                    "fecha": fecha.strftime("%d-%m-%Y"),
                    "estado": "Completado",
                    "tipo": "done",
                }
            )
        else:
            if estado_recepcion == "Recepcionado":
                estados_etapas.append(
                    {
                        "nombre": nombre,
                        "fecha": "-",
                        "estado": "Sin dato",
                        "tipo": "neutral",
                    }
                )
            elif nombre == pendiente:
                estados_etapas.append(
                    {
                        "nombre": nombre,
                        "fecha": "-",
                        "estado": "Pendiente actual",
                        "tipo": "current",
                    }
                )
            else:
                estados_etapas.append(
                    {
                        "nombre": nombre,
                        "fecha": "-",
                        "estado": "Pendiente",
                        "tipo": "pending",
                    }
                )

    etapas_completadas = sum(1 for etapa in estados_etapas if etapa["tipo"] == "done")
    total_etapas = len(estados_etapas)
    avance_pct = int(round(etapas_completadas / total_etapas * 100)) if total_etapas else 0

    st.progress(
        avance_pct,
        text=f"Avance del recorrido TAT: {etapas_completadas} de {total_etapas} hitos completados ({avance_pct}%).",
    )

    cols = st.columns(total_etapas)

    for idx, etapa in enumerate(estados_etapas):
        with cols[idx]:
            st.markdown(f"**{etapa['nombre']}**")

            if etapa["tipo"] == "done":
                st.success("Completado")
            elif etapa["tipo"] == "current":
                st.error("Pendiente actual")
            elif etapa["tipo"] == "pending":
                st.info("Pendiente")
            else:
                st.warning("Sin dato")

            st.caption(f"Fecha: {etapa['fecha']}")


def mostrar_expediente_registro(row: pd.Series):
    st.markdown("#### KPI Indicators del registro seleccionado")

    dias_restantes = valor_numerico(row.get("dias_restantes_int", np.nan))
    dias_transcurridos = valor_numerico(row.get("dias_transcurridos_alerta", np.nan))

    if pd.isna(dias_restantes):
        dias_restantes_txt = "Sin fecha"
        dias_restantes_sub = "No se puede calcular vencimiento."
        clase_dias = "kpi-warning"
    elif dias_restantes < 0:
        dias_restantes_txt = f"{abs(int(dias_restantes))} días"
        dias_restantes_sub = "Días vencido desde la fecha límite."
        clase_dias = "kpi-critical"
    elif dias_restantes == 0:
        dias_restantes_txt = "Hoy"
        dias_restantes_sub = "El registro vence hoy."
        clase_dias = "kpi-critical"
    else:
        dias_restantes_txt = f"{int(dias_restantes)} días"
        dias_restantes_sub = "Días restantes para vencer."
        clase_dias = "kpi-warning" if dias_restantes <= 7 else ""

    fecha_solicitud_txt = formato_fecha(row.get("fecha_inicio_tat", pd.NaT))
    fecha_vencimiento_txt = formato_fecha(row.get("fecha_vencimiento_tat", pd.NaT))

    dias_desde_inicio_txt = (
        f"{int(dias_transcurridos)} días"
        if pd.notna(dias_transcurridos)
        else "Sin dato"
    )

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        mostrar_kpi_html(
            "En cuántos días vence",
            dias_restantes_txt,
            dias_restantes_sub,
            clase_dias,
        )

    with k2:
        mostrar_kpi_html(
            "Fecha de solicitud",
            fecha_solicitud_txt,
            "Inicio del cálculo TAT.",
        )

    with k3:
        mostrar_kpi_html(
            "Días desde solicitud",
            dias_desde_inicio_txt,
            "Tiempo transcurrido desde el inicio de la solicitud.",
        )

    with k4:
        mostrar_kpi_html(
            "Fecha vencimiento TAT",
            fecha_vencimiento_txt,
            "Fecha límite calculada según umbral TAT.",
        )

    st.markdown("#### Seguimiento TAT del registro")
    st.caption(
        "Vista tipo tracking de pedido online: muestra los hitos del recorrido TAT desde la solicitud hasta la recepción."
    )

    mostrar_tracker_tat(row)

    st.markdown(
        f"""
        <div class="alert-card">
            <div class="alert-title">Acción sugerida</div>
            <div class="alert-text">{row.get("accion_sugerida", "-")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    detalle_cols = [
        COL_SOLPED,
        COL_OC_ME5A,
        COL_OC_ME80FN,
        COL_POS_SOLPED,
        COL_POS_OC,
        COL_MATERIAL,
        COL_TEXTO,
        COL_CENTRO,
        "centro_label",
        COL_SOLICITANTE,
        COL_AUTOR,
        COL_GRUPO_COMPRAS,
        COL_TIPO_OC,
        COL_ORIGEN,
        COL_SISTEMA,
        COL_NOMBRE_TIPO_COMPRA,
        COL_PERF_TAT,
        COL_RANGO_INC,
        COL_DIAS_TAT,
        COL_DIAS_INC,
        COL_UMBRAL_TAT,
        "fecha_inicio_tat",
        "fecha_vencimiento_tat",
        "fecha_recepcion_alerta",
        "dias_restantes_int",
        "dias_transcurridos_alerta",
        "exceso_umbral_alerta",
        "nivel_alerta",
        COL_NIVEL_ALERTA_DESC,
        "bucket_vencimiento",
        "clasificacion_vencimiento",
        "ultima_etapa_registrada",
        "fecha_pendiente",
        "accion_sugerida",
        "score_riesgo",
    ]

    detalle_cols = columnas_existentes(pd.DataFrame([row]), detalle_cols)

    with st.expander("Detalle completo del registro", expanded=False):
        st.dataframe(
            pd.DataFrame([row])[detalle_cols],
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# APP
# ============================================================

mostrar_logo()

st.title("10_ALERTAS")
st.caption(
    "Panel global para priorizar vencidos sin recepción, próximos vencimientos y datos incompletos."
)

if "df_tat" not in st.session_state or st.session_state.get("df_tat") is None:
    st.info("No hay archivo activo en sesión. Primero carga un archivo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

hoy = pd.Timestamp.today().normalize()

try:
    with st.spinner("Preparando panel de alertas..."):
        df_panel = preparar_panel_alertas(df_original, hoy)

except Exception as e:
    st.error("No se pudo preparar el panel de alertas.")
    st.exception(e)
    st.stop()


# ============================================================
# FILTROS EN ENCABEZADO
# ============================================================

st.markdown("### Filtros")
st.caption("Filtros enfocados en gestión de alertas. Puedes buscar SolPed, pedido, material o texto breve.")

fechas_vencimiento = df_panel["fecha_vencimiento_tat"].dropna()

fecha_venc_min = fechas_vencimiento.min().date() if not fechas_vencimiento.empty else None
fecha_venc_max = fechas_vencimiento.max().date() if not fechas_vencimiento.empty else None

opciones_nivel = [
    describir_nivel_alerta(x)
    for x in NIVELES_ALERTA_ORDEN
    if x in df_panel["nivel_alerta"].astype(str).unique()
]

opciones_clasificacion = [
    x for x in [
        "Vencido",
        "Vence hoy",
        "1 día",
        "2 días",
        "7 días",
        "+7 días",
        "Sin datos",
        "Recepcionado",
    ]
    if x in df_panel["clasificacion_vencimiento"].astype(str).unique()
]

clasificaciones_default = [
    x for x in opciones_clasificacion
    if x not in ["Sin datos", "Recepcionado"]
]

opciones_estado_recepcion = opciones_columna(df_panel, COL_ESTADO_RECEPCION_ALERTA)
opciones_centros = opciones_columna(df_panel, COL_CENTRO)
opciones_grupos_compras = opciones_columna(df_panel, COL_GRUPO_COMPRAS)
opciones_sistemas = opciones_columna(df_panel, COL_SISTEMA)
opciones_tipo_oc = opciones_columna(df_panel, COL_TIPO_OC)

centros_default = [
    centro
    for centro in opciones_centros
    if str(centro).strip().upper() == "E002"
]

with st.form("form_filtros_alertas"):
    bq1, bq2, bq3, bq4 = st.columns(4)

    with bq1:
        buscar_solped = st.text_input(
            "Buscar SolPed",
            placeholder="Ej: 1001973319",
            key="alertas_buscar_solped",
        )

    with bq2:
        buscar_pedido = st.text_input(
            "Buscar pedido",
            placeholder="Ej: 4500...",
            key="alertas_buscar_pedido",
        )

    with bq3:
        buscar_material = st.text_input(
            "Buscar material",
            placeholder="Código material",
            key="alertas_buscar_material",
        )

    with bq4:
        buscar_texto = st.text_input(
            "Buscar texto breve",
            placeholder="Descripción",
            key="alertas_buscar_texto",
        )

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        if fecha_venc_min is not None and fecha_venc_max is not None:
            rango_vencimiento = st.date_input(
                "Fecha vencimiento TAT",
                value=(fecha_venc_min, fecha_venc_max),
                min_value=fecha_venc_min,
                max_value=fecha_venc_max,
                key="alertas_rango_vencimiento",
            )
        else:
            rango_vencimiento = None
            st.warning("No hay fechas de vencimiento calculables.")

    with f2:
        niveles = st.multiselect(
            "Tipo de alerta",
            options=opciones_nivel,
            default=opciones_nivel,
            key="alertas_niveles",
        )

    with f3:
        clasificaciones = st.multiselect(
            "Clasificación vencimiento",
            options=opciones_clasificacion,
            default=clasificaciones_default,
            key="alertas_clasificaciones",
            help="Por defecto se excluyen 'Sin datos' y 'Recepcionado'.",
        )

    with f4:
        estados_recepcion = st.multiselect(
            "Estado recepción",
            options=opciones_estado_recepcion,
            default=opciones_estado_recepcion,
            key="alertas_estados_recepcion",
        )

    f5, f6, f7, f8 = st.columns(4)

    with f5:
        centros = st.multiselect(
            "Centro",
            options=opciones_centros,
            default=centros_default,
            key="alertas_centros",
            help="Por defecto se selecciona E002 si existe.",
        )

    with f6:
        grupos_compras = st.multiselect(
            "Grupo compras",
            options=opciones_grupos_compras,
            default=[],
            key="alertas_grupos_compras",
            help="Si no seleccionas grupo, se consideran todos.",
        )

    with f7:
        sistemas = st.multiselect(
            "Sistema",
            options=opciones_sistemas,
            default=[],
            key="alertas_sistemas",
            help="Si no seleccionas sistema, se consideran todos.",
        )

    with f8:
        tipos_oc = st.multiselect(
            "Tipo OC",
            options=opciones_tipo_oc,
            default=[],
            key="alertas_tipos_oc",
            help="Si no seleccionas tipo OC, se consideran todos.",
        )

    b1, b2 = st.columns(2)

    with b1:
        aplicar_filtros = st.form_submit_button(
            "Aplicar filtros",
            use_container_width=True,
            type="primary",
        )

    with b2:
        limpiar_filtros = st.form_submit_button(
            "Limpiar filtros",
            use_container_width=True,
        )


if limpiar_filtros:
    claves = [
        "alertas_buscar_solped",
        "alertas_buscar_pedido",
        "alertas_buscar_material",
        "alertas_buscar_texto",
        "alertas_rango_vencimiento",
        "alertas_niveles",
        "alertas_clasificaciones",
        "alertas_estados_recepcion",
        "alertas_centros",
        "alertas_grupos_compras",
        "alertas_sistemas",
        "alertas_tipos_oc",
        "alertas_df_filtrado",
        "alertas_resumen_filtros",
        "alertas_firma_filtros",
        "alertas_parquet_bytes",
        "alertas_parquet_firma",
        "alertas_csv_bytes",
        "alertas_csv_firma",
        "alertas_excel_bytes",
        "alertas_excel_firma",
    ]

    for clave in claves:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


filtros = {
    "buscar_solped": buscar_solped,
    "buscar_pedido": buscar_pedido,
    "buscar_material": buscar_material,
    "buscar_texto": buscar_texto,
    "rango_vencimiento": rango_vencimiento,
    "niveles": niveles,
    "clasificaciones": clasificaciones,
    "estados_recepcion": estados_recepcion,
    "centros": centros,
    "grupos_compras": grupos_compras,
    "sistemas": sistemas,
    "tipos_oc": tipos_oc,
}

firma_filtros = str(filtros) + f"_{len(df_panel)}"

if aplicar_filtros:
    with st.spinner("Aplicando filtros..."):
        df_filtrado, resumen_filtros_df = aplicar_filtros_alertas(
            df_base=df_panel,
            filtros=filtros,
        )

        st.session_state["alertas_df_filtrado"] = df_filtrado
        st.session_state["alertas_resumen_filtros"] = resumen_filtros_df
        st.session_state["alertas_firma_filtros"] = firma_filtros

    st.success("Filtros aplicados correctamente.")

else:
    if (
        st.session_state.get("alertas_df_filtrado") is not None
        and st.session_state.get("alertas_firma_filtros") == firma_filtros
    ):
        df_filtrado = st.session_state["alertas_df_filtrado"].copy()
        resumen_filtros_df = st.session_state["alertas_resumen_filtros"].copy()
    else:
        df_filtrado, resumen_filtros_df = aplicar_filtros_alertas(
            df_base=df_panel,
            filtros=filtros,
        )


# ============================================================
# INDICADORES Y RESUMEN EJECUTIVO
# ============================================================

resumen_ejecutivo = construir_resumen_ejecutivo(df_panel, df_filtrado)

st.markdown("### Resumen ejecutivo")

mostrar_card_estado(resumen_ejecutivo)

c1, c2, c3, c4 = st.columns(4)

with c1:
    mostrar_kpi_html(
        "Registros filtrados",
        formato_cantidad(resumen_ejecutivo["total_filtrado"]),
        f"{resumen_ejecutivo['pct_filtrado']:.1f}% del total archivo.",
    )

with c2:
    mostrar_kpi_html(
        "Vencidos sin recepción",
        formato_cantidad(resumen_ejecutivo["vencidos"]),
        "Prioridad máxima.",
        "kpi-critical",
    )

with c3:
    mostrar_kpi_html(
        "Por vencer 0-30 días",
        formato_cantidad(resumen_ejecutivo["proximos"]),
        "Vence hoy + próximos 30 días.",
        "kpi-warning",
    )

with c4:
    mostrar_kpi_html(
        "Foco de acción",
        formato_cantidad(resumen_ejecutivo["foco_accion"]),
        "Vencidos + próximos + datos incompletos.",
        "kpi-bad",
    )

c5, c6, c7, c8 = st.columns(4)

with c5:
    mostrar_kpi_html(
        "Vence hoy",
        formato_cantidad(resumen_ejecutivo["vence_hoy"]),
        "Registros sin recepción que vencen hoy.",
        "kpi-critical",
    )

with c6:
    mostrar_kpi_html(
        "Por vencer 1-7 días",
        formato_cantidad(resumen_ejecutivo["proximos_1_7"]),
        "Prioridad semanal.",
        "kpi-warning",
    )

with c7:
    mostrar_kpi_html(
        "Datos incompletos",
        formato_cantidad(resumen_ejecutivo["sin_fecha"]),
        "Sin fecha de vencimiento calculable.",
        "kpi-warning",
    )

with c8:
    mostrar_kpi_html(
        "Recepcionados",
        formato_cantidad(resumen_ejecutivo["recepcionados"]),
        "Registros cerrados.",
        "kpi-good",
    )


# ============================================================
# RETENCIÓN POR FILTROS
# ============================================================

st.markdown("### 1. Retención por filtros")

col_ret1, col_ret2 = st.columns([1.1, 1])

with col_ret1:
    grafico_donut_retencion(
        total_base=len(df_panel),
        total_filtrado=len(df_filtrado),
    )

with col_ret2:
    st.markdown("#### Detalle de filtros aplicado")
    st.caption("Vista reducida a lo más importante: porcentaje retenido y porcentaje excluido.")
    mostrar_detalle_filtros_reducido(resumen_filtros_df)


# ============================================================
# DESGLOSE VISUAL
# ============================================================

st.markdown("### 2. Distribución global de alertas")

desglose_alertas = crear_desglose_alertas(df_filtrado)

grafico_donut_alertas_porcentual(desglose_alertas)


st.markdown("### 3. Valores absolutos por vencimiento")

tabla_buckets = crear_resumen_buckets(df_filtrado)

grafico_alertas_valores_absolutos(tabla_buckets)


# ============================================================
# PLAN DE ATAQUE
# ============================================================

st.markdown("### 4. Plan de ataque")

plan_ataque = crear_plan_ataque(df_filtrado)

if plan_ataque.empty:
    st.info("No hay datos para construir plan de ataque.")
else:
    grafico_plan_ataque(plan_ataque)

    st.dataframe(
        plan_ataque,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Cantidad": st.column_config.NumberColumn(
                "Cantidad",
                format="%d",
            ),
            "% del total filtrado": st.column_config.ProgressColumn(
                "% del total filtrado",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )


# ============================================================
# DÓNDE ATACAR PRIMERO
# ============================================================

st.markdown("### 5. Dónde atacar primero")

col_rank1, col_rank2 = st.columns(2)

with col_rank1:
    st.markdown("#### Centros con mayor foco de acción")

    ranking_centros = crear_ranking_centros(df_filtrado)

    if ranking_centros.empty:
        st.info("No hay ranking de centros disponible.")
    else:
        grafico_top_ranking(
            ranking_centros,
            columna_nombre="Centro",
            titulo="Top centros por foco de acción",
            top_n=10,
        )

        with st.expander("Ver tabla de centros", expanded=False):
            st.dataframe(
                ranking_centros,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Foco acción": st.column_config.NumberColumn(
                        "Foco acción",
                        format="%d",
                    ),
                    "% foco acción": st.column_config.ProgressColumn(
                        "% foco acción",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Score_promedio": st.column_config.NumberColumn(
                        "Score promedio",
                        format="%.2f",
                    ),
                },
            )

with col_rank2:
    st.markdown("#### Grupos de compra con mayor foco")

    ranking_grupos = crear_ranking_grupo_compras(df_filtrado)

    if ranking_grupos.empty:
        st.info("No hay ranking de grupos de compra disponible.")
    else:
        grafico_top_ranking(
            ranking_grupos,
            columna_nombre="Grupo de compras",
            titulo="Top grupos de compra por foco de acción",
            top_n=10,
        )

        with st.expander("Ver tabla de grupos de compra", expanded=False):
            st.dataframe(
                ranking_grupos,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Foco acción": st.column_config.NumberColumn(
                        "Foco acción",
                        format="%d",
                    ),
                    "% foco acción": st.column_config.ProgressColumn(
                        "% foco acción",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Score_promedio": st.column_config.NumberColumn(
                        "Score promedio",
                        format="%.2f",
                    ),
                },
            )


# ============================================================
# ALERTAS PRIORITARIAS
# ============================================================

df_vencidos = df_filtrado[
    df_filtrado["nivel_alerta"].eq("Crítico")
].copy()

df_proximos = df_filtrado[
    df_filtrado["nivel_alerta"].isin(["Atención", "Seguimiento"])
].copy()

df_sin_fecha = df_filtrado[
    df_filtrado["nivel_alerta"].eq("Datos incompletos")
].copy()

st.markdown(
    """
    <div class="section-transition section-danger">
        <div class="section-title">Bloque 1 · Vencidos sin recepción</div>
        <div class="section-subtitle">
            Registros que ya superaron la fecha de vencimiento TAT y todavía no tienen recepción registrada.
            Esta sección representa la prioridad más alta de gestión.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

grafico_vencidos_por_anio(df_vencidos)

mostrar_vencidos_por_anio(df_vencidos)


st.markdown(
    """
    <div class="section-transition section-warning">
        <div class="section-title">Bloque 2 · Por vencer sin recepción</div>
        <div class="section-subtitle">
            Registros que aún no vencen, pero se encuentran dentro de la ventana de gestión preventiva.
            Esta sección permite anticipar acciones antes del incumplimiento.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

mostrar_proximos_por_rango(df_proximos)


st.markdown(
    """
    <div class="section-transition section-data">
        <div class="section-title">Bloque 3 · Datos incompletos</div>
        <div class="section-subtitle">
            Registros donde no se puede calcular el vencimiento TAT. Antes de gestionarlos operativamente,
            se deben corregir fechas, tipo OC o umbral.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

mostrar_tabla_alertas(
    df_sin_fecha,
    "Datos incompletos para calcular vencimiento",
    "Registros sin fecha de vencimiento calculable. Requieren corrección de datos base.",
)


# ============================================================
# EXPEDIENTE / SEGUIMIENTO DE REGISTRO
# ============================================================

st.markdown("### Expediente / seguimiento del registro")
st.caption(
    "Selecciona un registro para revisar sus KPI y el recorrido TAT tipo seguimiento de pedido online."
)

df_expediente = df_filtrado.copy()

if df_expediente.empty:
    st.info("No hay registros disponibles para mostrar expediente con los filtros actuales.")
else:
    df_expediente = df_expediente.sort_values("score_riesgo", ascending=False).copy()

    def construir_label_expediente(row):
        solped = formato_id(row.get(COL_SOLPED, "Sin SolPed"))
        pedido = formato_id(row.get(COL_OC_ME5A, row.get(COL_OC_ME80FN, "Sin pedido")))
        nivel = row.get(COL_NIVEL_ALERTA_DESC, "-")
        dias = row.get("dias_hasta_vencimiento", "-")
        centro = row.get("centro_label", "-")

        return f"{nivel} · {dias} · SolPed {solped} · Pedido {pedido} · {centro}"

    df_expediente["label_expediente"] = df_expediente.apply(construir_label_expediente, axis=1)

    opcion_registro = st.selectbox(
        "Selecciona registro",
        options=df_expediente["label_expediente"].tolist(),
        index=0,
        key="alertas_expediente_registro",
    )

    row = df_expediente[
        df_expediente["label_expediente"].eq(opcion_registro)
    ].iloc[0]

    mostrar_expediente_registro(row)


# ============================================================
# VISTA PREVIA GENERAL
# ============================================================

with st.expander("Vista previa general de datos filtrados", expanded=False):
    total_preview = len(df_filtrado)

    if total_preview == 0:
        st.info("No hay registros para mostrar.")
    else:
        limite_preview = st.number_input(
            "Filas a visualizar",
            min_value=1,
            max_value=min(5000, total_preview),
            value=min(300, total_preview),
            step=50 if total_preview >= 50 else 1,
            key="alertas_preview_general_filas",
        )

        st.info(
            f"Se están visualizando **{formato_cantidad(min(int(limite_preview), total_preview))} registros** "
            f"de un total de **{formato_cantidad(total_preview)} registros filtrados**."
        )

        tabla_preview = crear_tabla_prioridad(df_filtrado)

        st.dataframe(
            tabla_preview.head(int(limite_preview)),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# DESCARGA GENERAL
# ============================================================

with st.expander("Descargar resultado filtrado", expanded=False):
    st.caption(
        "Parquet es recomendado para análisis completo. CSV y Excel se preparan bajo demanda."
    )

    firma_export = f"{len(df_filtrado)}_{firma_filtros}"

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        preparar_parquet = st.button(
            "Preparar Parquet",
            use_container_width=True,
            key="alertas_preparar_parquet",
        )

        if preparar_parquet:
            with st.spinner("Preparando Parquet..."):
                st.session_state["alertas_parquet_bytes"] = convertir_a_parquet_cache(df_filtrado)
                st.session_state["alertas_parquet_firma"] = firma_export
                st.session_state["alertas_parquet_nombre"] = generar_nombre_salida("parquet")

        if (
            st.session_state.get("alertas_parquet_bytes") is not None
            and st.session_state.get("alertas_parquet_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Parquet",
                data=st.session_state["alertas_parquet_bytes"],
                file_name=st.session_state["alertas_parquet_nombre"],
                mime="application/octet-stream",
                type="primary",
                use_container_width=True,
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True,
            key="alertas_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["alertas_csv_bytes"] = convertir_a_csv_cache(df_filtrado)
                st.session_state["alertas_csv_firma"] = firma_export
                st.session_state["alertas_csv_nombre"] = generar_nombre_salida("csv")

        if (
            st.session_state.get("alertas_csv_bytes") is not None
            and st.session_state.get("alertas_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV",
                data=st.session_state["alertas_csv_bytes"],
                file_name=st.session_state["alertas_csv_nombre"],
                mime="text/csv",
                use_container_width=True,
            )

    with col_d3:
        preparar_excel = st.button(
            "Preparar Excel",
            use_container_width=True,
            key="alertas_preparar_excel",
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                st.session_state["alertas_excel_bytes"] = convertir_a_excel_cache(df_filtrado)
                st.session_state["alertas_excel_firma"] = firma_export
                st.session_state["alertas_excel_nombre"] = generar_nombre_salida("xlsx")

        if (
            st.session_state.get("alertas_excel_bytes") is not None
            and st.session_state.get("alertas_excel_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Excel",
                data=st.session_state["alertas_excel_bytes"],
                file_name=st.session_state["alertas_excel_nombre"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
