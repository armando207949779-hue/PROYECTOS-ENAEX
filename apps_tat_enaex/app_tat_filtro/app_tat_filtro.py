import io
import re
import base64
from html import escape
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# =========================================================
# Configuración general
# =========================================================
st.set_page_config(
    page_title="Buscador SolPed / OC",
    page_icon="🔎",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================================================
# Columnas esperadas / principales
# =========================================================
COL_SOLPED = "Solicitud de pedido - ME5A"
COL_OC_ME5A = "Pedido - ME5A"
COL_OC_NME = "Documento de compras - NME80FN"
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
COL_ESTADO_MATCH = "Estado del match"
COL_PERF_TAT = "performance_tat_total"
COL_RANGO_INC = "rango_incumplimiento_tat"
COL_INC_TAT = "incumplimiento_tat"
COL_DIAS_TAT = "dias_tat_total"
COL_DIAS_INC = "dias_incumplimiento_tat"
COL_UMBRAL_TAT = "umbral_tat_total"
COL_MONTO = "monto"
COL_FECHAS_INCONSISTENTES = "tiene_fechas_inconsistentes"

FECHAS_CANDIDATAS = [
    "fecha_solicitud_final",
    "fecha_liberacion_final",
    "fecha_pedido_final",
    "fecha_facturacion_final",
    "fecha_recepcion_final",
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
]

# Estado secuencial del pedido: una sola visualización unificada.
# Incluye la tarjeta inicial "1. Solicitud" para que el flujo no comience en liberación.
ETAPAS_PEDIDO = [
    {
        "titulo": "1. Solicitud",
        "fecha": "fecha_solicitud_final",
        "dias": None,
        "umbral": None,
        "performance": None,
        "nota": "Inicio SolPed",
    },
    {
        "titulo": "2. Liberación SolPed",
        "fecha": "fecha_liberacion_final",
        "dias": "dias_liberacion_solped",
        "umbral": "umbral_liberacion_solped",
        "performance": "performance_liberacion_solped",
        "nota": "Solicitud → Liberación",
    },
    {
        "titulo": "3. Comprador",
        "fecha": "fecha_pedido_final",
        "dias": "dias_comprador",
        "umbral": "umbral_comprador",
        "performance": "performance_comprador",
        "nota": "Liberación → Pedido",
    },
    {
        "titulo": "4. Proveedor",
        "fecha": "fecha_facturacion_final",
        "dias": "dias_proveedor",
        "umbral": "umbral_proveedor",
        "performance": "performance_proveedor",
        "nota": "Pedido → Facturación",
    },
    {
        "titulo": "5. Logística",
        "fecha": "fecha_recepcion_final",
        "dias": "dias_logistica",
        "umbral": "umbral_logistica",
        "performance": "performance_logistica",
        "nota": "Facturación → Recepción",
    },
    {
        "titulo": "6. TAT Total",
        "fecha": "fecha_recepcion_final",
        "dias": "dias_tat_total",
        "umbral": "umbral_tat_total",
        "performance": "performance_tat_total",
        "nota": "Solicitud → Recepción",
    },
]

COLUMNAS_TABLA_PRINCIPAL = [
    COL_SOLPED,
    COL_OC_ME5A,
    COL_OC_NME,
    COL_POS_SOLPED,
    COL_POS_OC,
    COL_MATERIAL,
    COL_TEXTO,
    COL_CENTRO,
    COL_SOLICITANTE,
    COL_GRUPO_COMPRAS,
    COL_TIPO_OC,
    COL_ORIGEN,
    COL_SISTEMA,
    COL_PERF_TAT,
    COL_DIAS_TAT,
    COL_UMBRAL_TAT,
    COL_DIAS_INC,
    COL_RANGO_INC,
    COL_MONTO,
]


# =========================================================
# Estilos visuales
# =========================================================
st.markdown(
    """
    <style>
        .block-container {padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1500px;}
        h1 {font-size: 1.9rem !important; margin-bottom: 0.1rem !important;}
        h3 {font-size: 1.05rem !important; margin-top: 1rem !important;}
        .logo-container {
            width: 100%;
            text-align: center;
            margin-top: 0.25rem;
            margin-bottom: 1.25rem;
            padding: 10px 0 8px 0;
            line-height: normal;
            overflow: visible;
            min-height: 72px;
            box-sizing: border-box;
        }
        .logo-container img {
            display: inline-block;
            width: 220px;
            max-width: min(220px, 60vw);
            height: auto;
            object-fit: contain;
            vertical-align: middle;
        }
        @media (max-width: 760px) {
            .logo-container {
                margin-top: 0.15rem;
                margin-bottom: 0.9rem;
                padding: 8px 0 6px 0;
                min-height: 62px;
            }
            .logo-container img {
                width: 170px;
                max-width: 70vw;
            }
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #eef2f7;
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.035);
        }
        .match-box {
            background: #f0f9ff;
            border: 1px solid #bae6fd;
            border-radius: 16px;
            padding: 14px 18px;
            margin: 0.5rem 0 0.9rem 0;
        }
        .match-number {
            font-size: 2rem;
            font-weight: 850;
            color: #0369a1;
            line-height: 1.05;
        }
        .match-label {
            color: #334155;
            font-size: 0.92rem;
            margin-top: 4px;
        }
        .order-head {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 16px 18px;
            margin: 0.75rem 0 0.85rem 0;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
        }
        .order-title {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 850;
            margin-bottom: 12px;
        }
        .tat-summary {
            display: grid;
            grid-template-columns: 1.15fr 1fr 1fr;
            gap: 12px;
            margin: 0.75rem 0 0.75rem 0;
        }
        .tat-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 16px 18px;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
            min-height: 128px;
        }
        .tat-card-primary {
            background: #eff6ff;
            border-color: #bfdbfe;
        }
        .tat-label {
            color: #64748b;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 800;
            margin-bottom: 6px;
        }
        .tat-main {
            color: #0f172a;
            font-size: 2rem;
            line-height: 1.05;
            font-weight: 900;
            margin-bottom: 6px;
        }
        .tat-main-small {
            color: #0f172a;
            font-size: 1.35rem;
            line-height: 1.1;
            font-weight: 900;
            margin-bottom: 8px;
        }
        .tat-sub {
            color: #334155;
            font-size: 0.92rem;
            line-height: 1.35;
        }
        .tat-muted {
            color: #64748b;
            font-size: 0.82rem;
            line-height: 1.35;
            margin-top: 5px;
        }
        .pedido-line-card {
            background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
            border: 1px solid #bbf7d0;
            border-radius: 20px;
            padding: 18px 20px 16px 20px;
            margin: 0.85rem 0 0.85rem 0;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
        }
        .pedido-line-title {
            font-size: 0.9rem;
            font-weight: 900;
            color: #14532d;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        .pedido-line {
            display: flex;
            align-items: flex-start;
            width: 100%;
        }
        .pedido-step {
            flex: 0 0 116px;
            text-align: center;
            min-width: 0;
        }
        .pedido-dot {
            width: 54px;
            height: 54px;
            border-radius: 999px;
            margin: 0 auto 10px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            font-size: 1.65rem;
            box-sizing: border-box;
        }
        .pedido-dot-complete {background: #22c55e; color: #ffffff; border: 4px solid #22c55e;}
        .pedido-dot-active {background: #ffffff; color: #15803d; border: 6px solid #22c55e;}
        .pedido-dot-pending {background: #ffffff; color: #94a3b8; border: 5px solid #cbd5e1;}
        .pedido-label {
            font-size: 0.86rem;
            font-weight: 900;
            color: #1f2937;
            line-height: 1.15;
            text-transform: uppercase;
        }
        .pedido-date {
            color: #64748b;
            font-size: 0.75rem;
            line-height: 1.2;
            margin-top: 4px;
            overflow-wrap: anywhere;
        }
        .pedido-connector {
            flex: 1 1 auto;
            height: 7px;
            min-width: 32px;
            margin-top: 24px;
            border-radius: 999px;
            background: #cbd5e1;
        }
        .pedido-connector-complete {background: #22c55e;}
        .pedido-connector-dashed {
            background: repeating-linear-gradient(90deg, #22c55e 0 18px, transparent 18px 30px);
            border: 0;
        }
        .pedido-line-note {
            color: #475569;
            font-size: 0.82rem;
            line-height: 1.35;
            margin-top: 14px;
        }
        .head-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(120px, 1fr));
            gap: 10px;
        }
        .head-label {
            color: #64748b;
            font-size: 0.74rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 3px;
        }
        .head-value {
            color: #0f172a;
            font-weight: 800;
            font-size: 1rem;
            overflow-wrap: anywhere;
        }
        .stage-wrap {
            display: grid;
            grid-template-columns: repeat(6, minmax(150px, 1fr));
            gap: 10px;
            align-items: stretch;
            margin-top: 0.55rem;
        }
        .stage-card {
            border-radius: 16px;
            padding: 13px 13px 12px 13px;
            border: 1px solid #e5e7eb;
            min-height: 150px;
            position: relative;
        }
        .stage-card::after {
            content: "→";
            position: absolute;
            right: -9px;
            top: 50%;
            transform: translateY(-50%);
            color: #94a3b8;
            font-weight: 900;
            font-size: 1rem;
            z-index: 2;
        }
        .stage-card:last-child::after {content: "";}
        .stage-green {background: #f0fdf4; border-color: #bbf7d0;}
        .stage-red {background: #fef2f2; border-color: #fecaca;}
        .stage-yellow {background: #fefce8; border-color: #fde68a;}
        .stage-gray {background: #f8fafc; border-color: #e2e8f0;}
        .stage-blue {background: #eff6ff; border-color: #bfdbfe;}
        .stage-title {
            font-size: 0.82rem;
            font-weight: 850;
            color: #0f172a;
            margin-bottom: 6px;
        }
        .stage-date {
            font-size: 1.05rem;
            font-weight: 850;
            color: #111827;
            margin-bottom: 5px;
        }
        .stage-note {
            color: #64748b;
            font-size: 0.76rem;
            line-height: 1.25;
            min-height: 28px;
            margin-bottom: 9px;
        }
        .stage-days {
            font-size: 0.88rem;
            color: #334155;
            margin-bottom: 7px;
        }
        .pill {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 9px;
            font-size: 0.76rem;
            font-weight: 800;
            border: 1px solid transparent;
            white-space: nowrap;
        }
        .pill-green {background: #dcfce7; color: #166534; border-color: #bbf7d0;}
        .pill-red {background: #fee2e2; color: #991b1b; border-color: #fecaca;}
        .pill-yellow {background: #fef9c3; color: #854d0e; border-color: #fde68a;}
        .pill-gray {background: #f1f5f9; color: #475569; border-color: #e2e8f0;}
        .pill-blue {background: #dbeafe; color: #1e40af; border-color: #bfdbfe;}
        .tiny-muted {color:#64748b; font-size:0.78rem;}
        @media (max-width: 1200px) {
            .stage-wrap {grid-template-columns: repeat(3, minmax(150px, 1fr));}
            .head-grid {grid-template-columns: repeat(3, minmax(120px, 1fr));}
        }
        @media (max-width: 760px) {
            .stage-wrap {grid-template-columns: 1fr;}
            .stage-card::after {content: "↓"; right: 50%; top: auto; bottom: -14px; transform: translateX(50%);}
            .stage-card:last-child::after {content: "";}
            .head-grid {grid-template-columns: 1fr;}
            .tat-summary {grid-template-columns: 1fr;}
            .tat-main {font-size: 1.65rem;}
            .pedido-line {overflow-x: auto; padding-bottom: 4px;}
            .pedido-step {flex-basis: 104px;}
            .pedido-dot {width: 48px; height: 48px; font-size: 1.45rem;}
            .pedido-connector {min-width: 28px; margin-top: 21px;}
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Lectura y utilidades
# =========================================================
def obtener_separador(opcion: str):
    """Devuelve el separador elegido para leer archivos CSV."""
    mapa = {
        "Automático": None,
        "Punto y coma (;)": ";",
        "Coma (, )": ",",
        "Coma (,)": ",",
        "Tabulación": "\t",
    }
    return mapa.get(opcion, None)


@st.cache_data(show_spinner=False)
def leer_archivo(bytes_archivo: bytes, nombre_archivo: str, separador_csv: str) -> pd.DataFrame:
    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)
        try:
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="utf-8-sig", on_bad_lines="skip")
        except Exception:
            buffer.seek(0)
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="latin1", on_bad_lines="skip")

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(buffer)

    raise ValueError("Formato no soportado. Usa Parquet, CSV o Excel.")


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


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
            resultado.loc[mask_ms] = pd.to_datetime(serie_num.loc[mask_ms], unit="ms", errors="coerce")
        if mask_s.any():
            resultado.loc[mask_s] = pd.to_datetime(serie_num.loc[mask_s], unit="s", errors="coerce")

    mask_texto = ~mask_num
    if mask_texto.any():
        resultado.loc[mask_texto] = pd.to_datetime(serie.loc[mask_texto], errors="coerce", dayfirst=True)

    return resultado


def convertir_fechas_visuales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in FECHAS_CANDIDATAS:
        if col in df.columns:
            convertido = convertir_columna_fecha(df[col])
            if convertido.notna().any():
                df[col] = convertido
    return df


def opciones_columna(df: pd.DataFrame, col: str, max_opciones: int = 700) -> list[str]:
    if col not in df.columns:
        return []
    valores = df[col].dropna().astype(str).sort_values().unique().tolist()
    return valores[:max_opciones]




@st.cache_data(show_spinner=False)
def construir_opciones_filtros(df: pd.DataFrame) -> dict[str, list[str]]:
    """Calcula una sola vez las opciones de filtros categóricos.

    Antes se recalculaban varios dropna/sort/unique en cada rerun,
    lo que se nota en archivos grandes.
    """
    columnas = [
        COL_CENTRO,
        COL_TIPO_OC,
        COL_ORIGEN,
        COL_SISTEMA,
        COL_GRUPO_COMPRAS,
        COL_ESTADO_MATCH,
        COL_PERF_TAT,
        COL_RANGO_INC,
    ]
    return {col: opciones_columna(df, col) for col in columnas}

def filtrar_por_ids(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)

    tokens = (
        str(texto)
        .replace("\n", ",")
        .replace(";", ",")
        .replace(" ", ",")
        .split(",")
    )
    tokens = [t.strip().replace(".0", "") for t in tokens if t.strip()]

    if not tokens:
        return pd.Series(True, index=df.index)

    serie = df[columna].astype(str).str.replace(".0", "", regex=False)
    mask = pd.Series(False, index=df.index)
    for token in tokens:
        mask = mask | serie.str.contains(token, case=False, na=False, regex=False)
    return mask


def contiene_texto(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)
    return df[columna].astype(str).str.contains(str(texto).strip(), case=False, na=False, regex=False)


def aplicar_rango_numerico(df: pd.DataFrame, columna: str, minimo: Any, maximo: Any) -> pd.Series:
    if columna not in df.columns:
        return pd.Series(True, index=df.index)

    serie = pd.to_numeric(df[columna], errors="coerce")
    mask = pd.Series(True, index=df.index)

    if minimo is not None:
        mask = mask & serie.ge(float(minimo))
    if maximo is not None:
        mask = mask & serie.le(float(maximo))

    return mask


def formato_valor(valor: Any) -> str:
    if pd.isna(valor):
        return "-"
    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%d-%m-%Y")
    if isinstance(valor, float):
        if np.isfinite(valor) and valor.is_integer():
            return f"{int(valor):,}".replace(",", ".")
        return f"{valor:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(valor, int):
        return f"{valor:,}".replace(",", ".")
    return str(valor)


def formato_numero(valor: Any, decimales: int = 0) -> str:
    if pd.isna(valor):
        return "-"
    try:
        valor_float = float(valor)
    except Exception:
        return str(valor)
    texto = f"{valor_float:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def valor_numerico(valor: Any) -> float:
    """Convierte un valor a número; devuelve NaN si no se puede convertir."""
    try:
        return float(pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0])
    except Exception:
        return np.nan


def texto_dias_y_meses(dias: Any) -> str:
    """Muestra duración TAT en días y, cuando aplica, en meses aproximados."""
    dias_num = valor_numerico(dias)

    if pd.isna(dias_num):
        return "Sin dato"

    dias_int = int(round(dias_num))
    texto_dias = f"{dias_int:,}".replace(",", ".")

    if dias_int < 0:
        return f"{texto_dias} días · revisar fechas"

    if dias_int >= 30:
        meses = dias_num / 30.44
        texto_meses = f"{meses:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"{texto_dias} días · {texto_meses} meses aprox."

    return f"{texto_dias} días"


def texto_dias_simple(dias: Any) -> str:
    """Muestra solo días en formato claro."""
    dias_num = valor_numerico(dias)

    if pd.isna(dias_num):
        return "Sin dato"

    dias_int = int(round(dias_num))
    return f"{dias_int:,} días".replace(",", ".")


def detalle_estado_tat(performance: Any, umbral_tat: Any, dias_inc: Any, rango_inc: Any) -> str:
    """Construye una explicación breve del estado TAT para el usuario."""
    estado = str(performance).strip().lower()
    umbral_txt = texto_dias_simple(umbral_tat)
    inc_txt = texto_dias_y_meses(dias_inc)

    if estado == "cumple":
        return f"Dentro del plazo objetivo. Umbral aplicado: {umbral_txt}."

    if estado == "no cumple":
        return f"Supera el plazo objetivo. Exceso: {inc_txt}. Rango: {formato_valor(rango_inc)}."

    if estado == "en proceso":
        return "En proceso: aún falta la fecha de recepción final para cerrar el TAT."

    if "no aplica" in estado:
        return "No aplica al análisis: revisa fechas inconsistentes o valores no evaluables."

    if estado == "sin datos":
        return "Sin datos suficientes para evaluar el TAT total."

    return "Estado pendiente de interpretación según los datos cargados."


def fecha_etapa_texto(row: pd.Series, columna: str) -> str:
    """Devuelve la fecha de una etapa en formato visual."""
    valor = row.get(columna, np.nan)
    if pd.isna(valor):
        return "Pendiente"
    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%d-%m-%Y")
    return formato_valor(valor)


def html_linea_pedido(row: pd.Series) -> str:
    """Construye una línea visual del avance del pedido similar a un tracker."""
    etapas = [
        ("Solicitud", "fecha_solicitud_final"),
        ("Liberación", "fecha_liberacion_final"),
        ("Pedido", "fecha_pedido_final"),
        ("Facturación", "fecha_facturacion_final"),
        ("Recepción", "fecha_recepcion_final"),
    ]

    completadas = [pd.notna(row.get(col, np.nan)) for _, col in etapas]

    try:
        indice_activo = completadas.index(False)
    except ValueError:
        indice_activo = len(etapas) - 1

    partes = []
    for i, (label, col_fecha) in enumerate(etapas):
        esta_completa = completadas[i]
        es_activa = i == indice_activo and not esta_completa

        if esta_completa:
            dot_class = "pedido-dot-complete"
            icono = "✓"
        elif es_activa:
            dot_class = "pedido-dot-active"
            icono = ""
        else:
            dot_class = "pedido-dot-pending"
            icono = ""

        partes.append(
            f"""
            <div class="pedido-step">
                <div class="pedido-dot {dot_class}">{icono}</div>
                <div class="pedido-label">{escape(label)}</div>
                <div class="pedido-date">{escape(fecha_etapa_texto(row, col_fecha))}</div>
            </div>
            """
        )

        if i < len(etapas) - 1:
            if completadas[i] and completadas[i + 1]:
                connector_class = "pedido-connector-complete"
            elif completadas[i] and not completadas[i + 1]:
                connector_class = "pedido-connector-dashed"
            else:
                connector_class = ""
            partes.append(f'<div class="pedido-connector {connector_class}"></div>')

    dias_tat = texto_dias_y_meses(row.get(COL_DIAS_TAT, np.nan))
    estado_tat = formato_valor(row.get(COL_PERF_TAT, np.nan))

    return f"""
    <div class="pedido-line-card">
        <div class="pedido-line-title">Línea de pedido</div>
        <div class="pedido-line">{''.join(partes)}</div>
        <div class="pedido-line-note">
            TAT total: <strong>{escape(dias_tat)}</strong> · Estado: <strong>{escape(estado_tat)}</strong>
        </div>
    </div>
    """


def clase_performance(valor: Any) -> str:
    texto = str(valor).strip().lower()
    if texto == "cumple":
        return "green"
    if texto == "no cumple":
        return "red"
    if texto in ["en proceso", "sin datos"]:
        return "yellow"
    if "no aplica" in texto:
        return "gray"
    return "blue"


def clase_dias(dias: Any, umbral: Any = None) -> str:
    dias_num = pd.to_numeric(pd.Series([dias]), errors="coerce").iloc[0]
    umbral_num = pd.to_numeric(pd.Series([umbral]), errors="coerce").iloc[0] if umbral is not None else np.nan

    if pd.isna(dias_num):
        return "gray"
    if dias_num < 0:
        return "gray"
    if pd.notna(umbral_num):
        if dias_num <= umbral_num:
            return "green"
        return "red"
    if dias_num == 0:
        return "green"
    return "yellow"


def pill(texto: Any, color: str) -> str:
    return f'<span class="pill pill-{color}">{escape(formato_valor(texto))}</span>'


def html_texto(valor: Any) -> str:
    return escape(formato_valor(valor))


def etapa_color(row: pd.Series, etapa: dict) -> str:
    perf_col = etapa.get("performance")
    dias_col = etapa.get("dias")
    umbral_col = etapa.get("umbral")

    if perf_col and perf_col in row.index:
        return clase_performance(row.get(perf_col))

    if dias_col and dias_col in row.index:
        return clase_dias(row.get(dias_col), row.get(umbral_col) if umbral_col else None)

    fecha_col = etapa.get("fecha")
    if fecha_col and fecha_col in row.index and pd.notna(row.get(fecha_col)):
        return "blue"

    return "gray"


@st.cache_data(show_spinner=False)
def dataframe_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return output.getvalue()


@st.cache_data(show_spinner=False)
def dataframe_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_parquet(output, index=False, engine="pyarrow")
    return output.getvalue()


@st.cache_data(show_spinner=False)
def dataframe_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def construir_label_registro(row: pd.Series) -> str:
    solped = row.get(COL_SOLPED, "-")
    oc = row.get(COL_OC_ME5A, row.get(COL_OC_NME, "-"))
    pos = row.get(COL_POS_SOLPED, "-")
    perf = row.get(COL_PERF_TAT, "-")
    dias = row.get(COL_DIAS_TAT, "-")
    texto = str(row.get(COL_TEXTO, ""))[:55]
    return f"SolPed {formato_valor(solped)} | OC {formato_valor(oc)} | Pos {formato_valor(pos)} | TAT {texto_dias_y_meses(dias)} | {perf} | {texto}"


def aplicar_estilo_tabla(df_tabla: pd.DataFrame):
    def color_performance(valor):
        texto = str(valor).strip().lower()
        if texto == "cumple":
            return "background-color: #dcfce7; color: #166534; font-weight: 700;"
        if texto == "no cumple":
            return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
        if texto in ["en proceso", "sin datos"]:
            return "background-color: #fef9c3; color: #854d0e; font-weight: 700;"
        if "no aplica" in texto:
            return "background-color: #f1f5f9; color: #475569; font-weight: 700;"
        return ""

    def color_incumplimiento(valor):
        texto = str(valor).strip().lower()
        if texto == "sin incumplimiento":
            return "background-color: #dcfce7; color: #166534; font-weight: 700;"
        if texto in ["0-5 días", "6-15 días"]:
            return "background-color: #fef9c3; color: #854d0e; font-weight: 700;"
        if texto in ["16-30 días", "mayor a un mes"]:
            return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
        return ""

    styler = df_tabla.style
    for col in df_tabla.columns:
        if col.startswith("performance_") or col == COL_PERF_TAT:
            styler = styler.map(color_performance, subset=[col])
        if col == COL_RANGO_INC:
            styler = styler.map(color_incumplimiento, subset=[col])
    return styler


def html_estado_pedido(row: pd.Series) -> str:
    """Construye el timeline completo como HTML renderizable."""
    cards = []
    for etapa in ETAPAS_PEDIDO:
        color = etapa_color(row, etapa)
        fecha = html_texto(row.get(etapa["fecha"], np.nan)) if etapa.get("fecha") else "-"

        dias_col = etapa.get("dias")
        umbral_col = etapa.get("umbral")
        perf_col = etapa.get("performance")

        if dias_col:
            dias_valor = row.get(dias_col, np.nan)
            umbral = html_texto(row.get(umbral_col, np.nan)) if umbral_col else "-"
            if dias_col == COL_DIAS_TAT:
                dias_txt = escape(texto_dias_y_meses(dias_valor)) + f" · umbral {umbral} días"
            else:
                dias = html_texto(dias_valor)
                dias_txt = f"{dias} días · umbral {umbral}"
        else:
            dias_txt = "Punto de inicio"

        perf_val = row.get(perf_col, "Registrado") if perf_col else "Registrado"
        perf_color = clase_performance(perf_val) if perf_col else color

        cards.append(
            f"""
            <div class=\"stage-card stage-{color}\">
                <div class=\"stage-title\">{escape(etapa['titulo'])}</div>
                <div class=\"stage-date\">{fecha}</div>
                <div class=\"stage-note\">{escape(etapa['nota'])}</div>
                <div class=\"stage-days\">{dias_txt}</div>
                {pill(perf_val, perf_color)}
            </div>
            """
        )

    return f"""
    <!doctype html>
    <html>
    <head>
        <meta charset=\"utf-8\">
        <style>
            html, body {{
                margin: 0;
                padding: 0;
                font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                color: #0f172a;
                background: transparent;
                overflow: hidden;
            }}
            .stage-wrap {{
                display: grid;
                grid-template-columns: repeat(6, minmax(150px, 1fr));
                gap: 10px;
                align-items: stretch;
                margin-top: 0.55rem;
                padding: 2px 0 18px 0;
                box-sizing: border-box;
            }}
            .stage-card {{
                border-radius: 16px;
                padding: 13px 13px 12px 13px;
                border: 1px solid #e5e7eb;
                min-height: 150px;
                position: relative;
                box-sizing: border-box;
            }}
            .stage-card::after {{
                content: "→";
                position: absolute;
                right: -9px;
                top: 50%;
                transform: translateY(-50%);
                color: #94a3b8;
                font-weight: 900;
                font-size: 1rem;
                z-index: 2;
            }}
            .stage-card:last-child::after {{content: "";}}
            .stage-green {{background: #f0fdf4; border-color: #bbf7d0;}}
            .stage-red {{background: #fef2f2; border-color: #fecaca;}}
            .stage-yellow {{background: #fefce8; border-color: #fde68a;}}
            .stage-gray {{background: #f8fafc; border-color: #e2e8f0;}}
            .stage-blue {{background: #eff6ff; border-color: #bfdbfe;}}
            .stage-title {{font-size: 0.82rem; font-weight: 850; color: #0f172a; margin-bottom: 6px;}}
            .stage-date {{font-size: 1.05rem; font-weight: 850; color: #111827; margin-bottom: 5px;}}
            .stage-note {{color: #64748b; font-size: 0.76rem; line-height: 1.25; min-height: 28px; margin-bottom: 9px;}}
            .stage-days {{font-size: 0.88rem; color: #334155; margin-bottom: 7px;}}
            .pill {{
                display: inline-block;
                border-radius: 999px;
                padding: 4px 9px;
                font-size: 0.76rem;
                font-weight: 800;
                border: 1px solid transparent;
                white-space: nowrap;
            }}
            .pill-green {{background: #dcfce7; color: #166534; border-color: #bbf7d0;}}
            .pill-red {{background: #fee2e2; color: #991b1b; border-color: #fecaca;}}
            .pill-yellow {{background: #fef9c3; color: #854d0e; border-color: #fde68a;}}
            .pill-gray {{background: #f1f5f9; color: #475569; border-color: #e2e8f0;}}
            .pill-blue {{background: #dbeafe; color: #1e40af; border-color: #bfdbfe;}}
            @media (max-width: 1200px) {{
                .stage-wrap {{grid-template-columns: repeat(3, minmax(150px, 1fr));}}
                html, body {{overflow: auto;}}
            }}
            @media (max-width: 760px) {{
                .stage-wrap {{grid-template-columns: 1fr; padding-bottom: 24px;}}
                .stage-card::after {{content: "↓"; right: 50%; top: auto; bottom: -14px; transform: translateX(50%);}}
                .stage-card:last-child::after {{content: "";}}
            }}
        </style>
    </head>
    <body>
        <div class=\"stage-wrap\">{''.join(cards)}</div>
    </body>
    </html>
    """



# =========================================================
# UI común
# =========================================================
def agregar_padding_a_svg(svg_texto: str, padding_ratio: float = 0.18) -> str:
    """
    Amplía el viewBox del SVG para evitar que Streamlit/navegador corte el logo.

    Algunos SVG corporativos vienen con un viewBox muy ajustado. Al mostrarlos como
    data-uri dentro de Streamlit, los bordes superiores/inferiores pueden verse
    recortados. Esta función no cambia el arte del logo: solo agrega aire alrededor
    del viewBox.
    """
    match = re.search(r'viewBox=["\']\s*([\-\d.]+)\s+([\-\d.]+)\s+([\d.]+)\s+([\d.]+)\s*["\']', svg_texto)

    if not match:
        return svg_texto

    min_x, min_y, width, height = map(float, match.groups())
    pad_x = width * padding_ratio
    pad_y = height * padding_ratio

    nuevo_viewbox = (
        f'viewBox="{min_x - pad_x:.3f} {min_y - pad_y:.3f} '
        f'{width + (2 * pad_x):.3f} {height + (2 * pad_y):.3f}"'
    )

    return svg_texto[:match.start()] + nuevo_viewbox + svg_texto[match.end():]


@st.cache_data(show_spinner=False)
def obtener_logo_base64() -> str:
    """Lee el logo una sola vez y le agrega margen interno para evitar cortes."""
    if not LOGO_PATH.exists():
        return ""

    logo_svg = LOGO_PATH.read_text(encoding="utf-8")
    logo_svg = agregar_padding_a_svg(logo_svg, padding_ratio=0.22)
    return base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")


def mostrar_logo(ancho: int = 220):
    logo_base64 = obtener_logo_base64()
    if not logo_base64:
        return

    st.markdown(
        f"""
        <div class="logo-container">
            <img
                src="data:image/svg+xml;base64,{logo_base64}"
                style="width: {ancho}px; max-width: min({ancho}px, 60vw);"
                alt="Logo Enaex"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Interfaz
# =========================================================
mostrar_logo()

st.title("Buscador SolPed / OC")
st.caption(
    "Carga un archivo ya procesado. La app solo filtra, visualiza y descarga resultados; no recalcula performance."
)

with st.sidebar:
    st.header("Configuración")

    separador_csv = st.selectbox(
        "Separador CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación",
        ],
        index=0,
    )

    limite_vista = st.number_input(
        "Filas en tabla",
        min_value=25,
        max_value=5000,
        value=300,
        step=25,
    )

    mostrar_todas_columnas = st.checkbox(
        "Mostrar todas las columnas en tabla",
        value=False,
    )

    st.caption("El separador solo aplica a archivos CSV.")

st.subheader("Archivo")

uploaded_file = st.file_uploader(
    "Subir parquet, CSV o Excel",
    type=["parquet", "csv", "xlsx", "xls"],
)

if uploaded_file is None:
    st.info("Sube un archivo `.parquet`, `.csv`, `.xlsx` o `.xls` para comenzar.")
    st.stop()

try:
    df = leer_archivo(uploaded_file.getvalue(), uploaded_file.name, separador_csv)
    df = limpiar_columnas(df)
    df = convertir_fechas_visuales(df)
    opciones_filtros = construir_opciones_filtros(df)
except Exception as e:
    st.error("No se pudo leer el archivo.")
    st.exception(e)
    st.stop()


# =========================================================
# Filtros principales visibles
# =========================================================
st.markdown("### Filtros principales")

c1, c2, c3 = st.columns([1, 1, 0.8])
with c1:
    txt_solped = st.text_input("SolPed", placeholder="Ej: 1001973319")
with c2:
    txt_oc = st.text_input("Orden de compra / Pedido", placeholder="Ej: 4502321875")
with c3:
    txt_pos_solped = st.text_input("Posición SolPed", placeholder="Ej: 10")


# =========================================================
# Filtros avanzados colapsados
# =========================================================
with st.expander("Filtros avanzados", expanded=False):
    st.caption("Úsalos solo cuando necesites acotar más la búsqueda.")

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        txt_pos_oc = st.text_input("Posición OC", placeholder="Ej: 10")
        txt_material = st.text_input("Material", placeholder="Ej: 20012021")
        txt_descripcion = st.text_input("Descripción / texto breve", placeholder="Ej: bloqueador")

    with a2:
        txt_solicitante = st.text_input("Solicitante", placeholder="Ej: c.silva")
        txt_autor = st.text_input("Autor", placeholder="Ej: CL17330735")
        centro_sel = st.multiselect("Centro", opciones_filtros.get(COL_CENTRO, []))

    with a3:
        tipo_oc_sel = st.multiselect("Tipo OC", opciones_filtros.get(COL_TIPO_OC, []))
        origen_sel = st.multiselect("Origen", opciones_filtros.get(COL_ORIGEN, []))
        sistema_sel = st.multiselect("Sistema", opciones_filtros.get(COL_SISTEMA, []))

    with a4:
        grupo_sel = st.multiselect("Grupo de compras", opciones_filtros.get(COL_GRUPO_COMPRAS, []))
        estado_match_sel = st.multiselect("Estado del match", opciones_filtros.get(COL_ESTADO_MATCH, []))
        perf_tat_sel = st.multiselect("Performance TAT", opciones_filtros.get(COL_PERF_TAT, []))
        rango_inc_sel = st.multiselect("Rango incumplimiento TAT", opciones_filtros.get(COL_RANGO_INC, []))

    st.markdown("#### Rango de días / monto")
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        usar_dias_tat_min = st.checkbox("TAT mínimo", value=False)
        dias_tat_min = st.number_input("Valor mínimo TAT", value=0, step=1, disabled=not usar_dias_tat_min)
    with r2:
        usar_dias_tat_max = st.checkbox("TAT máximo", value=False)
        dias_tat_max = st.number_input("Valor máximo TAT", value=9999, step=1, disabled=not usar_dias_tat_max)
    with r3:
        usar_monto_min = st.checkbox("Monto mínimo", value=False)
        monto_min = st.number_input("Valor mínimo monto", value=0.0, step=1000.0, disabled=not usar_monto_min)
    with r4:
        usar_monto_max = st.checkbox("Monto máximo", value=False)
        monto_max = st.number_input("Valor máximo monto", value=0.0, step=1000.0, disabled=not usar_monto_max)

    f1, f2 = st.columns(2)
    with f1:
        solo_incumplimiento = st.checkbox("Solo incumplimiento TAT", value=False)
    with f2:
        solo_fechas_inconsistentes = st.checkbox("Solo fechas inconsistentes", value=False)

    st.markdown("#### Fecha")
    fecha_col_disponibles = [
        c for c in FECHAS_CANDIDATAS
        if c in df.columns and pd.api.types.is_datetime64_any_dtype(df[c])
    ]

    if fecha_col_disponibles:
        usar_filtro_fecha = st.checkbox("Aplicar filtro de fecha", value=False)
        col_fecha_filtro = st.selectbox("Columna de fecha", fecha_col_disponibles, index=0, disabled=not usar_filtro_fecha)
        fecha_min_real = df[col_fecha_filtro].min()
        fecha_max_real = df[col_fecha_filtro].max()

        if pd.notna(fecha_min_real) and pd.notna(fecha_max_real):
            fc1, fc2 = st.columns(2)
            with fc1:
                fecha_desde = st.date_input("Desde", value=fecha_min_real.date(), disabled=not usar_filtro_fecha)
            with fc2:
                fecha_hasta = st.date_input("Hasta", value=fecha_max_real.date(), disabled=not usar_filtro_fecha)
        else:
            usar_filtro_fecha = False
            fecha_desde = None
            fecha_hasta = None
            st.warning("La columna seleccionada no tiene fechas válidas.")
    else:
        usar_filtro_fecha = False
        fecha_desde = None
        fecha_hasta = None
        col_fecha_filtro = None
        st.info("No se encontraron columnas de fecha convertibles para filtrar.")

# Seguridad por si algún widget no existe.
for nombre, default in {
    "txt_pos_oc": "",
    "txt_material": "",
    "txt_descripcion": "",
    "txt_solicitante": "",
    "txt_autor": "",
    "centro_sel": [],
    "tipo_oc_sel": [],
    "origen_sel": [],
    "sistema_sel": [],
    "grupo_sel": [],
    "estado_match_sel": [],
    "perf_tat_sel": [],
    "rango_inc_sel": [],
    "usar_dias_tat_min": False,
    "usar_dias_tat_max": False,
    "dias_tat_min": 0,
    "dias_tat_max": 9999,
    "usar_monto_min": False,
    "usar_monto_max": False,
    "monto_min": 0.0,
    "monto_max": 0.0,
    "solo_incumplimiento": False,
    "solo_fechas_inconsistentes": False,
    "usar_filtro_fecha": False,
}.items():
    if nombre not in locals():
        locals()[nombre] = default


# =========================================================
# Aplicar filtros
# =========================================================
mask = pd.Series(True, index=df.index)

mask &= filtrar_por_ids(df, COL_SOLPED, txt_solped)
mask &= filtrar_por_ids(df, COL_OC_ME5A, txt_oc) | filtrar_por_ids(df, COL_OC_NME, txt_oc)
mask &= filtrar_por_ids(df, COL_POS_SOLPED, txt_pos_solped)
mask &= filtrar_por_ids(df, COL_POS_OC, txt_pos_oc)
mask &= filtrar_por_ids(df, COL_MATERIAL, txt_material)
mask &= contiene_texto(df, COL_TEXTO, txt_descripcion)
mask &= contiene_texto(df, COL_SOLICITANTE, txt_solicitante)
mask &= contiene_texto(df, COL_AUTOR, txt_autor)

if centro_sel and COL_CENTRO in df.columns:
    mask &= df[COL_CENTRO].astype(str).isin(centro_sel)
if tipo_oc_sel and COL_TIPO_OC in df.columns:
    mask &= df[COL_TIPO_OC].astype(str).isin(tipo_oc_sel)
if origen_sel and COL_ORIGEN in df.columns:
    mask &= df[COL_ORIGEN].astype(str).isin(origen_sel)
if sistema_sel and COL_SISTEMA in df.columns:
    mask &= df[COL_SISTEMA].astype(str).isin(sistema_sel)
if grupo_sel and COL_GRUPO_COMPRAS in df.columns:
    mask &= df[COL_GRUPO_COMPRAS].astype(str).isin(grupo_sel)
if estado_match_sel and COL_ESTADO_MATCH in df.columns:
    mask &= df[COL_ESTADO_MATCH].astype(str).isin(estado_match_sel)
if perf_tat_sel and COL_PERF_TAT in df.columns:
    mask &= df[COL_PERF_TAT].astype(str).isin(perf_tat_sel)
if rango_inc_sel and COL_RANGO_INC in df.columns:
    mask &= df[COL_RANGO_INC].astype(str).isin(rango_inc_sel)

mask &= aplicar_rango_numerico(
    df,
    COL_DIAS_TAT,
    dias_tat_min if usar_dias_tat_min else None,
    dias_tat_max if usar_dias_tat_max else None,
)
mask &= aplicar_rango_numerico(
    df,
    COL_MONTO,
    monto_min if usar_monto_min else None,
    monto_max if usar_monto_max else None,
)

if solo_incumplimiento and COL_INC_TAT in df.columns:
    mask &= df[COL_INC_TAT].eq(True)

if solo_fechas_inconsistentes and COL_FECHAS_INCONSISTENTES in df.columns:
    mask &= df[COL_FECHAS_INCONSISTENTES].eq(True)

if usar_filtro_fecha and col_fecha_filtro and fecha_desde and fecha_hasta:
    inicio = pd.Timestamp(fecha_desde)
    fin = pd.Timestamp(fecha_hasta) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    mask &= df[col_fecha_filtro].between(inicio, fin, inclusive="both")

df_filtrado = df.loc[mask].copy()


# =========================================================
# Coincidencias destacadas
# =========================================================
porcentaje = (len(df_filtrado) / len(df) * 100) if len(df) else 0
st.markdown(
    f"""
    <div class="match-box">
        <div class="match-number">{len(df_filtrado):,}</div>
        <div class="match-label">coincidencias encontradas de {len(df):,} registros cargados · {porcentaje:.1f}% del archivo</div>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True,
)


# =========================================================
# Estado del pedido unificado
# =========================================================
if df_filtrado.empty:
    st.warning("No hay resultados con los filtros aplicados.")
else:
    opciones_detalle = []
    for idx, row in df_filtrado.head(5000).iterrows():
        opciones_detalle.append((idx, construir_label_registro(row)))

    labels = [item[1] for item in opciones_detalle]
    label_sel = st.selectbox("Registro", labels)
    idx_sel = opciones_detalle[labels.index(label_sel)][0]
    row = df_filtrado.loc[idx_sel]

    perf_tat = row.get(COL_PERF_TAT, np.nan)
    perf_color = clase_performance(perf_tat)
    rango_inc = row.get(COL_RANGO_INC, np.nan)
    dias_tat = row.get(COL_DIAS_TAT, np.nan)
    dias_inc = row.get(COL_DIAS_INC, np.nan)
    umbral_tat = row.get(COL_UMBRAL_TAT, np.nan)
    tat_total_txt = texto_dias_y_meses(dias_tat)
    dias_inc_txt = texto_dias_y_meses(dias_inc)
    detalle_tat = detalle_estado_tat(perf_tat, umbral_tat, dias_inc, rango_inc)

    st.markdown(
        f"""
        <div class="tat-summary">
            <div class="tat-card tat-card-primary">
                <div class="tat-label">TAT total</div>
                <div class="tat-main">{escape(tat_total_txt)}</div>
                <div class="tat-sub">Duración desde la solicitud hasta la recepción.</div>
                <div class="tat-muted">Umbral aplicado: {escape(texto_dias_simple(umbral_tat))}</div>
            </div>
            <div class="tat-card">
                <div class="tat-label">Estado TAT</div>
                <div class="tat-main-small">{pill(perf_tat, perf_color)}</div>
                <div class="tat-sub">{escape(detalle_tat)}</div>
            </div>
            <div class="tat-card">
                <div class="tat-label">Incumplimiento TAT</div>
                <div class="tat-main-small">{escape(dias_inc_txt)}</div>
                <div class="tat-sub">Rango: {escape(formato_valor(rango_inc))}</div>
                <div class="tat-muted">Solo cuenta exceso sobre el umbral TAT.</div>
            </div>
        </div>

        {html_linea_pedido(row)}

        <div class="order-head">
            <div class="order-title">Datos principales del pedido</div>
            <div class="head-grid">
                <div>
                    <div class="head-label">SolPed</div>
                    <div class="head-value">{html_texto(row.get(COL_SOLPED, np.nan))}</div>
                </div>
                <div>
                    <div class="head-label">Orden de compra / Pedido</div>
                    <div class="head-value">{html_texto(row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan)))}</div>
                </div>
                <div>
                    <div class="head-label">Posición SolPed</div>
                    <div class="head-value">{html_texto(row.get(COL_POS_SOLPED, np.nan))}</div>
                </div>
                <div>
                    <div class="head-label">Material</div>
                    <div class="head-value">{html_texto(row.get(COL_MATERIAL, np.nan))}</div>
                </div>
                <div>
                    <div class="head-label">Centro</div>
                    <div class="head-value">{html_texto(row.get(COL_CENTRO, np.nan))}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    components.html(html_estado_pedido(row), height=230, scrolling=False)


# =========================================================
# Distribuciones simples
# =========================================================
with st.expander("Distribuciones del resultado", expanded=False):
    b1, b2, b3 = st.columns(3)

    with b1:
        if COL_PERF_TAT in df_filtrado.columns:
            st.markdown("**Performance TAT**")
            tabla_perf = df_filtrado[COL_PERF_TAT].value_counts(dropna=False).reset_index()
            tabla_perf.columns = ["Performance TAT", "Cantidad"]
            st.dataframe(tabla_perf, use_container_width=True, hide_index=True)

    with b2:
        if COL_RANGO_INC in df_filtrado.columns:
            st.markdown("**Rango incumplimiento TAT**")
            tabla_rango = df_filtrado[COL_RANGO_INC].value_counts(dropna=False).reset_index()
            tabla_rango.columns = ["Rango", "Cantidad"]
            st.dataframe(tabla_rango, use_container_width=True, hide_index=True)

    with b3:
        if COL_ESTADO_MATCH in df_filtrado.columns:
            st.markdown("**Estado del match**")
            tabla_estado = df_filtrado[COL_ESTADO_MATCH].value_counts(dropna=False).reset_index()
            tabla_estado.columns = ["Estado", "Cantidad"]
            st.dataframe(tabla_estado, use_container_width=True, hide_index=True)


# =========================================================
# Tabla de resultado filtrado
# =========================================================
with st.expander("Tabla de resultado filtrado", expanded=False):
    columnas_base = [c for c in COLUMNAS_TABLA_PRINCIPAL if c in df_filtrado.columns]
    columnas_extra = []
    for etapa in ETAPAS_PEDIDO:
        for col in [etapa.get("fecha"), etapa.get("dias"), etapa.get("umbral"), etapa.get("performance")]:
            if col and col in df_filtrado.columns and col not in columnas_base and col not in columnas_extra:
                columnas_extra.append(col)

    columnas_default = df_filtrado.columns.tolist() if mostrar_todas_columnas else columnas_base + columnas_extra

    columnas_visibles = st.multiselect(
        "Columnas visibles",
        options=df_filtrado.columns.tolist(),
        default=columnas_default,
    )

    if columnas_visibles:
        tabla = df_filtrado[columnas_visibles].head(int(limite_vista)).copy()
        st.dataframe(aplicar_estilo_tabla(tabla), use_container_width=True, hide_index=True)
    else:
        st.info("Selecciona al menos una columna.")


# =========================================================
# Registro completo transpuesto
# =========================================================
with st.expander("Registro completo transpuesto", expanded=False):
    if df_filtrado.empty:
        st.info("No hay registros para visualizar.")
    else:
        registro_t = df_filtrado.loc[[idx_sel]].T.reset_index()
        registro_t.columns = ["Campo", "Valor"]
        st.dataframe(registro_t, use_container_width=True, hide_index=True)


# =========================================================
# Descargas
# =========================================================
st.markdown("### Descarga")

csv_bytes = dataframe_a_csv(df_filtrado)

x1, x2, x3 = st.columns(3)
with x1:
    st.download_button(
        "Descargar CSV filtrado",
        data=csv_bytes,
        file_name="resultado_filtrado_solped_oc.csv",
        mime="text/csv",
        use_container_width=True,
    )

with x2:
    try:
        parquet_bytes = dataframe_a_parquet(df_filtrado)
        st.download_button(
            "Descargar Parquet filtrado",
            data=parquet_bytes,
            file_name="resultado_filtrado_solped_oc.parquet",
            mime="application/octet-stream",
            use_container_width=True,
        )
    except Exception:
        st.button("Parquet no disponible", disabled=True, use_container_width=True)

with x3:
    if len(df_filtrado) <= 250_000:
        excel_bytes = dataframe_a_excel(df_filtrado)
        st.download_button(
            "Descargar Excel filtrado",
            data=excel_bytes,
            file_name="resultado_filtrado_solped_oc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.button("Excel no disponible", disabled=True, use_container_width=True)
        st.caption("Excel se desactiva sobre 250.000 filas.")


# =========================================================
# Info técnica
# =========================================================
with st.expander("Columnas disponibles", expanded=False):
    st.write(df.columns.tolist())
