import io
import base64
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# =========================================================
# Configuración general
# =========================================================
# IMPORTANTE:
# Si esta app se ejecuta dentro de st.navigation() desde la app principal,
# NO uses st.set_page_config() aquí.
# Debe estar solo en el archivo principal del portal.

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent

LOGO_CANDIDATOS = [
    ROOT_DIR / "assets" / "logo.svg",
    ROOT_DIR / "assets" / "logo.png",
    BASE_DIR / "assets" / "logo.svg",
    BASE_DIR / "assets" / "logo.png",
    BASE_DIR / "logo.svg",
    BASE_DIR / "logo.png",
]


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

ETAPAS_LINEA_PEDIDO = [
    ("Solicitud", "fecha_solicitud_final"),
    ("Liberación", "fecha_liberacion_final"),
    ("Pedido", "fecha_pedido_final"),
    ("Facturación", "fecha_facturacion_final"),
    ("Recepción", "fecha_recepcion_final"),
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


ETAPAS_ALERTA = [
    {
        "nombre": "Liberación SolPed",
        "fecha_inicio": "fecha_solicitud_final",
        "fecha_fin": "fecha_liberacion_final",
        "dias": "dias_liberacion_solped",
        "umbral": "umbral_liberacion_solped",
        "performance": "performance_liberacion_solped",
        "responsable": "Solicitante / Aprobador",
    },
    {
        "nombre": "Comprador",
        "fecha_inicio": "fecha_liberacion_final",
        "fecha_fin": "fecha_pedido_final",
        "dias": "dias_comprador",
        "umbral": "umbral_comprador",
        "performance": "performance_comprador",
        "responsable": "Compras",
    },
    {
        "nombre": "Proveedor",
        "fecha_inicio": "fecha_pedido_final",
        "fecha_fin": "fecha_facturacion_final",
        "dias": "dias_proveedor",
        "umbral": "umbral_proveedor",
        "performance": "performance_proveedor",
        "responsable": "Proveedor",
    },
    {
        "nombre": "Logística",
        "fecha_inicio": "fecha_facturacion_final",
        "fecha_fin": "fecha_recepcion_final",
        "dias": "dias_logistica",
        "umbral": "umbral_logistica",
        "performance": "performance_logistica",
        "responsable": "Logística / Bodega",
    },
]

COLUMNAS_ALERTA = [
    "nivel_alerta",
    "criterio_alerta",
    "score_riesgo",
    "estado_global",
    "etapa_actual",
    "responsable_sugerido",
    "dias_transcurridos_tat",
    "dias_restantes_tat",
    "brecha_tat",
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
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1500px;
            margin-left: auto;
            margin-right: auto;
        }

        h1 {
            font-size: 1.9rem !important;
            margin-bottom: 0.1rem !important;
        }

        h3 {
            font-size: 1.05rem !important;
            margin-top: 1rem !important;
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

        .avance-card {
            background: #ffffff;
            border: 1px solid #dbeafe;
            border-left: 5px solid #2563eb;
            border-radius: 18px;
            padding: 16px 18px;
            margin: 0.75rem 0 0.9rem 0;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
        }

        .avance-title {
            color: #1e3a8a;
            font-size: 0.9rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 10px;
        }

        .avance-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(140px, 1fr));
            gap: 12px;
        }

        .avance-item {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 11px 12px;
        }

        .avance-label {
            color: #64748b;
            font-size: 0.72rem;
            font-weight: 850;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }

        .avance-value {
            color: #0f172a;
            font-size: 1rem;
            font-weight: 900;
            overflow-wrap: anywhere;
        }

        .avance-note {
            color: #334155;
            font-size: 0.88rem;
            line-height: 1.35;
            margin-top: 10px;
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

        .pedido-dot-complete {
            background: #22c55e;
            color: #ffffff;
            border: 4px solid #22c55e;
        }

        .pedido-dot-active {
            background: #ffffff;
            color: #15803d;
            border: 6px solid #22c55e;
        }

        .pedido-dot-pending {
            background: #ffffff;
            color: #94a3b8;
            border: 5px solid #cbd5e1;
        }

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

        .pedido-connector-complete {
            background: #22c55e;
        }

        .pedido-connector-dashed {
            background: repeating-linear-gradient(
                90deg,
                #22c55e 0 18px,
                transparent 18px 30px
            );
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

        .stage-card:last-child::after {
            content: "";
        }

        .stage-green {
            background: #f0fdf4;
            border-color: #bbf7d0;
        }

        .stage-red {
            background: #fef2f2;
            border-color: #fecaca;
        }

        .stage-yellow {
            background: #fefce8;
            border-color: #fde68a;
        }

        .stage-gray {
            background: #f8fafc;
            border-color: #e2e8f0;
        }

        .stage-blue {
            background: #eff6ff;
            border-color: #bfdbfe;
        }

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

        .pill-green {
            background: #dcfce7;
            color: #166534;
            border-color: #bbf7d0;
        }

        .pill-red {
            background: #fee2e2;
            color: #991b1b;
            border-color: #fecaca;
        }

        .pill-yellow {
            background: #fef9c3;
            color: #854d0e;
            border-color: #fde68a;
        }

        .pill-gray {
            background: #f1f5f9;
            color: #475569;
            border-color: #e2e8f0;
        }

        .pill-blue {
            background: #dbeafe;
            color: #1e40af;
            border-color: #bfdbfe;
        }

        @media (max-width: 1200px) {
            .stage-wrap {
                grid-template-columns: repeat(3, minmax(150px, 1fr));
            }

            .head-grid {
                grid-template-columns: repeat(3, minmax(120px, 1fr));
            }
        }

        @media (max-width: 760px) {
            .stage-wrap {
                grid-template-columns: 1fr;
            }

            .stage-card::after {
                content: "↓";
                right: 50%;
                top: auto;
                bottom: -14px;
                transform: translateX(50%);
            }

            .stage-card:last-child::after {
                content: "";
            }

            .head-grid {
                grid-template-columns: 1fr;
            }

            .tat-summary {
                grid-template-columns: 1fr;
            }

            .tat-main {
                font-size: 1.65rem;
            }

            .pedido-line {
                overflow-x: auto;
                padding-bottom: 4px;
            }

            .pedido-step {
                flex-basis: 104px;
            }

            .pedido-dot {
                width: 48px;
                height: 48px;
                font-size: 1.45rem;
            }

            .pedido-connector {
                min-width: 28px;
                margin-top: 21px;
            }
        }


        .alert-box {
            border-radius: 18px;
            padding: 16px 18px;
            border: 1px solid #e5e7eb;
            background: #ffffff;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
            margin: 0.8rem 0;
        }

        .alert-red { background: #fef2f2; border-color: #fecaca; }
        .alert-orange { background: #fff7ed; border-color: #fed7aa; }
        .alert-yellow { background: #fefce8; border-color: #fde68a; }
        .alert-green { background: #f0fdf4; border-color: #bbf7d0; }
        .alert-gray { background: #f8fafc; border-color: #e2e8f0; }

        .alert-title {
            color: #0f172a;
            font-size: 1.02rem;
            font-weight: 900;
            margin-bottom: 8px;
        }

        .alert-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(120px, 1fr));
            gap: 10px;
        }

        .alert-label {
            color: #64748b;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .alert-value {
            color: #0f172a;
            font-size: 0.98rem;
            font-weight: 850;
            overflow-wrap: anywhere;
        }

        .criteria-box {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 14px 16px;
            margin: 0.65rem 0 0.9rem 0;
            color: #334155;
            font-size: 0.92rem;
            line-height: 1.45;
        }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Utilidades generales
# =========================================================
def encontrar_logo():
    for path in LOGO_CANDIDATOS:
        if path.exists():
            return path

    return None


def mostrar_logo(ancho: int = 260):
    logo_path = encontrar_logo()

    if logo_path is None:
        st.warning(f"Logo no encontrado: {ROOT_DIR / 'assets' / 'logo.svg'}")
        return

    suffix = logo_path.suffix.lower()
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"

    raw = logo_path.read_bytes()
    logo_base64 = base64.b64encode(raw).decode("utf-8")

    st.markdown(
        f"""
        <div style="
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 84px;
            margin: 0 0 16px 0;
            overflow: visible;
        ">
            <img
                src="data:{mime};base64,{logo_base64}"
                style="
                    width: {ancho}px;
                    max-width: 80%;
                    height: auto;
                    display: block;
                    object-fit: contain;
                "
                alt="Logo Enaex"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )


def limpiar_filtros_principales():
    st.session_state["filtro_solped"] = ""
    st.session_state["filtro_oc"] = ""
    st.session_state["filtro_pos_solped"] = ""


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def convertir_columna_fecha(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie, errors="coerce")

    resultado = pd.Series(
        pd.NaT,
        index=serie.index,
        dtype="datetime64[ns]",
    )

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
        if col in df.columns:
            convertido = convertir_columna_fecha(df[col])

            if convertido.notna().any():
                df[col] = convertido

    return df


def opciones_columna(
    df: pd.DataFrame,
    col: str,
    max_opciones: int = 700,
) -> list[str]:
    if col not in df.columns:
        return []

    valores = (
        df[col]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )

    return valores[:max_opciones]


@st.cache_data(show_spinner=False)
def construir_opciones_filtros(df: pd.DataFrame) -> dict[str, list[str]]:
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

    return {
        col: opciones_columna(df, col)
        for col in columnas
    }


def filtrar_por_ids(
    df: pd.DataFrame,
    columna: str,
    texto: str,
) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)

    tokens = (
        str(texto)
        .replace("\n", ",")
        .replace(";", ",")
        .replace(" ", ",")
        .split(",")
    )

    tokens = [
        t.strip().replace(".0", "")
        for t in tokens
        if t.strip()
    ]

    if not tokens:
        return pd.Series(True, index=df.index)

    serie = (
        df[columna]
        .astype(str)
        .str.replace(".0", "", regex=False)
    )

    mask = pd.Series(False, index=df.index)

    for token in tokens:
        mask = mask | serie.str.contains(
            token,
            case=False,
            na=False,
            regex=False,
        )

    return mask


def contiene_texto(
    df: pd.DataFrame,
    columna: str,
    texto: str,
) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)

    return (
        df[columna]
        .astype(str)
        .str.contains(
            str(texto).strip(),
            case=False,
            na=False,
            regex=False,
        )
    )


def aplicar_rango_numerico(
    df: pd.DataFrame,
    columna: str,
    minimo: Any,
    maximo: Any,
) -> pd.Series:
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

        return (
            f"{valor:,.1f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    if isinstance(valor, int):
        return f"{valor:,}".replace(",", ".")

    return str(valor)


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


def valor_numerico(valor: Any) -> float:
    try:
        return float(
            pd.to_numeric(
                pd.Series([valor]),
                errors="coerce",
            ).iloc[0]
        )
    except Exception:
        return np.nan


def obtener_umbral_tat(row: pd.Series) -> float:
    umbral = valor_numerico(row.get(COL_UMBRAL_TAT, np.nan))

    if pd.notna(umbral):
        return umbral

    tipo_oc = str(row.get(COL_TIPO_OC, "")).strip().replace(".0", "")

    if tipo_oc in ["35", "45"]:
        return 40

    if tipo_oc == "47":
        return 70

    return np.nan


def texto_dias_y_meses(dias: Any) -> str:
    dias_num = valor_numerico(dias)

    if pd.isna(dias_num):
        return "Sin dato"

    dias_int = int(round(dias_num))
    texto_dias = f"{dias_int:,}".replace(",", ".")

    if dias_int < 0:
        return f"{texto_dias} días · revisar fechas"

    if dias_int >= 30:
        meses = dias_num / 30.44
        texto_meses = (
            f"{meses:,.1f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        return f"{texto_dias} días · {texto_meses} meses aprox."

    return f"{texto_dias} días"


def texto_dias_simple(dias: Any) -> str:
    dias_num = valor_numerico(dias)

    if pd.isna(dias_num):
        return "Sin dato"

    dias_int = int(round(dias_num))

    return f"{dias_int:,} días".replace(",", ".")


def texto_dias_restantes(dias_restantes: Any) -> str:
    valor = valor_numerico(dias_restantes)

    if pd.isna(valor):
        return "Sin dato"

    valor_int = int(round(valor))

    if valor_int >= 0:
        return f"{valor_int:,} días disponibles".replace(",", ".")

    return f"{abs(valor_int):,} días sobre el umbral".replace(",", ".")


def detalle_estado_tat(
    performance: Any,
    umbral_tat: Any,
    dias_inc: Any,
    rango_inc: Any,
) -> str:
    estado = str(performance).strip().lower()
    umbral_txt = texto_dias_simple(umbral_tat)
    inc_txt = texto_dias_y_meses(dias_inc)

    if estado == "cumple":
        return f"Dentro del plazo objetivo. Umbral aplicado: {umbral_txt}."

    if estado == "no cumple":
        return (
            f"Supera el plazo objetivo. Exceso: {inc_txt}. "
            f"Rango: {formato_valor(rango_inc)}."
        )

    if estado == "en proceso":
        return "En proceso: el TAT total queda pendiente hasta registrar la recepción final."

    if "no aplica" in estado:
        return "No aplica al análisis: revisa fechas inconsistentes o valores no evaluables."

    if estado == "sin datos":
        return "Sin datos suficientes para evaluar el TAT total."

    return "Estado pendiente de interpretación según los datos cargados."


def fecha_etapa_texto(row: pd.Series, columna: str) -> str:
    valor = row.get(columna, np.nan)

    if pd.isna(valor):
        return "Pendiente"

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%d-%m-%Y")

    return formato_valor(valor)


def fecha_valida(row: pd.Series, columna: str):
    valor = row.get(columna, np.nan)

    if pd.isna(valor):
        return pd.NaT

    return pd.to_datetime(valor, errors="coerce")


def obtener_avance_pedido(row: pd.Series) -> dict[str, Any]:
    completadas = []

    for nombre, columna in ETAPAS_LINEA_PEDIDO:
        completadas.append(
            (
                nombre,
                columna,
                pd.notna(row.get(columna, np.nan)),
            )
        )

    registradas = [
        item for item in completadas
        if item[2]
    ]

    pendientes = [
        item for item in completadas
        if not item[2]
    ]

    ultima_nombre, ultima_columna, _ = (
        registradas[-1]
        if registradas
        else ("Sin etapa registrada", "", False)
    )

    siguiente_nombre, siguiente_columna, _ = (
        pendientes[0]
        if pendientes
        else ("Cerrado", "", False)
    )

    fecha_inicio = fecha_valida(row, "fecha_solicitud_final")

    fecha_ultima = (
        fecha_valida(row, ultima_columna)
        if ultima_columna
        else pd.NaT
    )

    esta_cerrado = len(pendientes) == 0

    fecha_referencia = fecha_ultima

    if not esta_cerrado and pd.notna(fecha_inicio):
        fecha_referencia = pd.Timestamp.today().normalize()

    dias_parcial = np.nan

    if pd.notna(fecha_inicio) and pd.notna(fecha_referencia):
        dias_parcial = (fecha_referencia - fecha_inicio).days

    umbral = obtener_umbral_tat(row)
    dias_restantes = np.nan

    if pd.notna(dias_parcial) and pd.notna(umbral):
        dias_restantes = int(round(umbral - dias_parcial))

    return {
        "ultima_etapa": ultima_nombre,
        "ultima_fecha": (
            fecha_etapa_texto(row, ultima_columna)
            if ultima_columna
            else "-"
        ),
        "siguiente_etapa": siguiente_nombre,
        "siguiente_columna": siguiente_columna,
        "dias_parcial": dias_parcial,
        "dias_restantes": dias_restantes,
        "umbral_tat": umbral,
        "esta_cerrado": esta_cerrado,
    }


def nombre_fecha_faltante(columna: str) -> str:
    mapa = {
        "fecha_solicitud_final": "fecha de solicitud",
        "fecha_liberacion_final": "fecha de liberación",
        "fecha_pedido_final": "fecha de pedido",
        "fecha_facturacion_final": "fecha de facturación",
        "fecha_recepcion_final": "fecha de recepción",
    }

    return mapa.get(columna, "fecha pendiente")


def texto_tat_total_usuario(performance: Any, dias_tat: Any) -> str:
    estado = str(performance).strip().lower()

    if (
        estado == "en proceso"
        and pd.isna(
            pd.to_numeric(
                pd.Series([dias_tat]),
                errors="coerce",
            ).iloc[0]
        )
    ):
        return "En proceso"

    return texto_dias_y_meses(dias_tat)


def diagnostico_avance(row: pd.Series) -> str:
    avance = obtener_avance_pedido(row)

    if avance["esta_cerrado"]:
        return "El pedido ya tiene recepción registrada. El TAT total está cerrado."

    falta = nombre_fecha_faltante(avance["siguiente_columna"])
    dias_restantes = valor_numerico(avance["dias_restantes"])
    umbral = valor_numerico(avance.get("umbral_tat", np.nan))

    if pd.isna(umbral):
        return (
            f"Falta {falta}. No se pudo determinar el umbral TAT porque falta "
            f"umbral_tat_total o tipo_oc válido."
        )

    if pd.notna(dias_restantes):
        if dias_restantes < 0:
            return (
                f"Falta {falta}. El pedido ya supera el umbral TAT "
                f"de {int(umbral)} días."
            )

        if dias_restantes <= 5:
            return (
                f"Falta {falta}. El pedido está cerca del umbral TAT "
                f"de {int(umbral)} días."
            )

        return (
            f"Falta {falta}. Quedan {int(dias_restantes)} días disponibles "
            f"contra el umbral TAT de {int(umbral)} días."
        )

    return (
        f"Última etapa registrada: {avance['ultima_etapa']}. "
        f"Siguiente etapa: {avance['siguiente_etapa']}."
    )


def html_avance_actual(row: pd.Series) -> str:
    avance = obtener_avance_pedido(row)
    dias_parcial = texto_dias_y_meses(avance["dias_parcial"])
    dias_restantes = texto_dias_restantes(avance["dias_restantes"])
    umbral = avance.get("umbral_tat", np.nan)

    if avance["esta_cerrado"]:
        tat_total_estado = "Cerrado"
    else:
        tat_total_estado = "Pendiente hasta recepción"

    if pd.notna(valor_numerico(umbral)):
        contra_umbral = (
            f"{dias_restantes} · umbral {int(valor_numerico(umbral))} días"
        )
    else:
        contra_umbral = "Sin dato"

    return dedent(
        f"""
        <div class="avance-card">
            <div class="avance-title">Avance actual</div>
            <div class="avance-grid">
                <div class="avance-item">
                    <div class="avance-label">Última etapa registrada</div>
                    <div class="avance-value">{escape(avance['ultima_etapa'])} · {escape(avance['ultima_fecha'])}</div>
                </div>
                <div class="avance-item">
                    <div class="avance-label">Tiempo transcurrido</div>
                    <div class="avance-value">{escape(dias_parcial)}</div>
                </div>
                <div class="avance-item">
                    <div class="avance-label">TAT total</div>
                    <div class="avance-value">{escape(tat_total_estado)}</div>
                </div>
                <div class="avance-item">
                    <div class="avance-label">Contra umbral TAT</div>
                    <div class="avance-value">{escape(contra_umbral)}</div>
                </div>
            </div>
            <div class="avance-note">{escape(diagnostico_avance(row))}</div>
        </div>
        """
    ).strip()


def html_linea_pedido(row: pd.Series) -> str:
    etapas = ETAPAS_LINEA_PEDIDO

    completadas = [
        pd.notna(row.get(col, np.nan))
        for _, col in etapas
    ]

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
            dedent(
                f"""
                <div class="pedido-step">
                    <div class="pedido-dot {dot_class}">{icono}</div>
                    <div class="pedido-label">{escape(label)}</div>
                    <div class="pedido-date">{escape(fecha_etapa_texto(row, col_fecha))}</div>
                </div>
                """
            ).strip()
        )

        if i < len(etapas) - 1:
            if completadas[i] and completadas[i + 1]:
                connector_class = "pedido-connector-complete"
            elif completadas[i] and not completadas[i + 1]:
                connector_class = "pedido-connector-dashed"
            else:
                connector_class = ""

            partes.append(
                f'<div class="pedido-connector {connector_class}"></div>'
            )

    estado_tat = formato_valor(row.get(COL_PERF_TAT, np.nan))

    dias_tat = texto_tat_total_usuario(
        row.get(COL_PERF_TAT, np.nan),
        row.get(COL_DIAS_TAT, np.nan),
    )

    return dedent(
        f"""
        <div class="pedido-line-card">
            <div class="pedido-line-title">Línea de pedido</div>
            <div class="pedido-line">{''.join(partes)}</div>
            <div class="pedido-line-note">
                TAT total: <strong>{escape(dias_tat)}</strong> · Estado: <strong>{escape(estado_tat)}</strong>
            </div>
        </div>
        """
    ).strip()


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
    dias_num = pd.to_numeric(
        pd.Series([dias]),
        errors="coerce",
    ).iloc[0]

    umbral_num = (
        pd.to_numeric(
            pd.Series([umbral]),
            errors="coerce",
        ).iloc[0]
        if umbral is not None
        else np.nan
    )

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
    return (
        f'<span class="pill pill-{color}">'
        f'{escape(formato_valor(texto))}'
        f'</span>'
    )


def html_texto(valor: Any) -> str:
    return escape(formato_valor(valor))


def html_id(valor: Any) -> str:
    return escape(formato_id(valor))


def etapa_color(row: pd.Series, etapa: dict) -> str:
    perf_col = etapa.get("performance")
    dias_col = etapa.get("dias")
    umbral_col = etapa.get("umbral")

    if perf_col and perf_col in row.index:
        return clase_performance(row.get(perf_col))

    if dias_col and dias_col in row.index:
        return clase_dias(
            row.get(dias_col),
            row.get(umbral_col) if umbral_col else None,
        )

    fecha_col = etapa.get("fecha")

    if fecha_col and fecha_col in row.index and pd.notna(row.get(fecha_col)):
        return "blue"

    return "gray"


@st.cache_data(show_spinner=False)
def dataframe_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Resultado",
        )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def dataframe_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow",
    )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def dataframe_a_csv(df: pd.DataFrame) -> bytes:
    return (
        df.to_csv(
            index=False,
            encoding="utf-8-sig",
        )
        .encode("utf-8-sig")
    )




def fecha_inicio_tat_alerta(row: pd.Series):
    for col in ["fecha_solicitud_final", "Fecha de solicitud - ME5A"]:
        valor = row.get(col, pd.NaT)
        if pd.notna(valor):
            return pd.to_datetime(valor, errors="coerce")
    return pd.NaT


def fecha_fin_real_o_referencia_alerta(row: pd.Series, hoy: pd.Timestamp):
    for col in ["fecha_recepcion_final", "Fecha recepción mercancía - NME80FN"]:
        valor = row.get(col, pd.NaT)
        if pd.notna(valor):
            return pd.to_datetime(valor, errors="coerce"), True
    return hoy, False


def detectar_etapa_actual_alerta(row: pd.Series) -> tuple[str, str]:
    for etapa in ETAPAS_ALERTA:
        fecha_fin = row.get(etapa["fecha_fin"], pd.NaT)
        if pd.isna(fecha_fin):
            return etapa["nombre"], etapa["responsable"]
    return "Recepcionado", "Cerrado"


def detectar_etapa_critica_alerta(row: pd.Series) -> tuple[str, str, float, float, float]:
    peor_etapa = "Sin etapa crítica"
    responsable = "Sin responsable"
    peor_brecha = -999999.0
    peor_dias = np.nan
    peor_umbral = np.nan

    for etapa in ETAPAS_ALERTA:
        dias = valor_numerico(row.get(etapa["dias"], np.nan))
        umbral = valor_numerico(row.get(etapa["umbral"], np.nan))
        perf = str(row.get(etapa["performance"], "")).strip().lower()

        if pd.isna(dias) or pd.isna(umbral):
            continue

        brecha = dias - umbral

        if perf == "no cumple" or brecha > peor_brecha:
            if brecha > peor_brecha:
                peor_etapa = etapa["nombre"]
                responsable = etapa["responsable"]
                peor_brecha = brecha
                peor_dias = dias
                peor_umbral = umbral

    return peor_etapa, responsable, peor_brecha, peor_dias, peor_umbral


def criterio_nivel_alerta(nivel: str, dias_alerta_temprana: int) -> str:
    if nivel == "Crítica":
        return "TAT vencido: performance no cumple o días transcurridos superan el umbral."
    if nivel == "Alta":
        return f"Riesgo próximo: quedan {dias_alerta_temprana} días o menos para llegar al umbral."
    if nivel == "Media":
        return f"Seguimiento preventivo: quedan entre {dias_alerta_temprana + 1} y {dias_alerta_temprana * 2} días para el umbral."
    if nivel == "Normal":
        return f"En plazo: quedan más de {dias_alerta_temprana * 2} días frente al umbral."
    return "No clasificable: faltan fechas, umbral o existen inconsistencias de datos."


@st.cache_data(show_spinner=False)
def construir_alertas(df: pd.DataFrame, dias_alerta_temprana: int = 7) -> pd.DataFrame:
    df = limpiar_columnas(df)
    df = convertir_fechas_visuales(df)
    hoy = pd.Timestamp.today().normalize()
    salida = df.copy()

    niveles = []
    estados = []
    scores = []
    etapas_actuales = []
    responsables = []
    criterios = []
    dias_transcurridos = []
    dias_restantes = []
    brechas = []

    for _, row in salida.iterrows():
        inicio = fecha_inicio_tat_alerta(row)
        fin_ref, cerrado = fecha_fin_real_o_referencia_alerta(row, hoy)
        umbral = obtener_umbral_tat(row)
        etapa_actual, responsable_actual = detectar_etapa_actual_alerta(row)
        etapa_critica, responsable_critico, _, _, _ = detectar_etapa_critica_alerta(row)

        dias_tat_real = valor_numerico(row.get(COL_DIAS_TAT, np.nan))

        if pd.notna(dias_tat_real) and cerrado:
            transcurrido = dias_tat_real
        elif pd.notna(inicio) and pd.notna(fin_ref):
            transcurrido = (fin_ref - inicio).days
        else:
            transcurrido = np.nan

        restante = umbral - transcurrido if pd.notna(umbral) and pd.notna(transcurrido) else np.nan
        brecha = transcurrido - umbral if pd.notna(umbral) and pd.notna(transcurrido) else np.nan

        perf_tat = str(row.get(COL_PERF_TAT, "")).strip().lower()
        inconsistente = bool(row.get(COL_FECHAS_INCONSISTENTES, False)) if COL_FECHAS_INCONSISTENTES in row.index else False

        if inconsistente or pd.isna(transcurrido) or pd.isna(umbral):
            nivel = "Sin datos"
            estado = "Datos incompletos"
            score = 0
            responsable = "Datos / Control"
        elif perf_tat == "no cumple" or brecha > 0:
            nivel = "Crítica"
            estado = "Ya atrasado"
            score = min(100, 80 + max(0, brecha) * 2)
            responsable = responsable_critico if etapa_critica != "Sin etapa crítica" else responsable_actual
        elif restante <= dias_alerta_temprana:
            nivel = "Alta"
            estado = "Riesgo de atraso"
            score = max(65, 80 - restante * 2)
            responsable = responsable_actual
        elif restante <= dias_alerta_temprana * 2:
            nivel = "Media"
            estado = "Vigilar"
            score = max(40, 60 - restante)
            responsable = responsable_actual
        else:
            nivel = "Normal"
            estado = "En plazo"
            score = max(5, 30 - min(restante, 30) * 0.5)
            responsable = responsable_actual

        niveles.append(nivel)
        estados.append(estado)
        scores.append(round(float(score), 1))
        etapas_actuales.append(etapa_actual)
        responsables.append(responsable)
        criterios.append(criterio_nivel_alerta(nivel, dias_alerta_temprana))
        dias_transcurridos.append(transcurrido)
        dias_restantes.append(restante)
        brechas.append(brecha)

    salida["nivel_alerta"] = niveles
    salida["criterio_alerta"] = criterios
    salida["score_riesgo"] = scores
    salida["estado_global"] = estados
    salida["etapa_actual"] = etapas_actuales
    salida["responsable_sugerido"] = responsables
    salida["dias_transcurridos_tat"] = dias_transcurridos
    salida["dias_restantes_tat"] = dias_restantes
    salida["brecha_tat"] = brechas

    orden = {
        "Crítica": 1,
        "Alta": 2,
        "Media": 3,
        "Normal": 4,
        "Sin datos": 5,
    }

    salida["_orden_alerta"] = salida["nivel_alerta"].map(orden).fillna(9)
    salida = salida.sort_values(
        ["_orden_alerta", "score_riesgo", "brecha_tat"],
        ascending=[True, False, False],
    )

    return salida.drop(columns=["_orden_alerta"])


def pill_alerta(nivel: str) -> str:
    mapa = {
        "Crítica": "red",
        "Alta": "yellow",
        "Media": "yellow",
        "Normal": "green",
        "Sin datos": "gray",
    }
    color = mapa.get(str(nivel), "gray")
    if str(nivel) == "Alta":
        color = "red"
    return f'<span class="pill pill-{color}">{escape(str(nivel))}</span>'


def clase_alerta(nivel: str) -> str:
    return {
        "Crítica": "alert-red",
        "Alta": "alert-orange",
        "Media": "alert-yellow",
        "Normal": "alert-green",
        "Sin datos": "alert-gray",
    }.get(str(nivel), "alert-gray")


def html_alerta(row: pd.Series) -> str:
    oc = row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan))
    titulo = (
        f"SolPed {formato_id(row.get(COL_SOLPED, np.nan))} · "
        f"OC {formato_id(oc)} · "
        f"Pos {formato_id(row.get(COL_POS_SOLPED, np.nan))}"
    )

    return dedent(
        f"""
        <div class="alert-box {clase_alerta(row.get('nivel_alerta', 'Sin datos'))}">
            <div class="alert-title">{escape(titulo)} {pill_alerta(row.get('nivel_alerta', 'Sin datos'))}</div>
            <div class="alert-grid">
                <div><div class="alert-label">Estado</div><div class="alert-value">{escape(formato_valor(row.get('estado_global', np.nan)))}</div></div>
                <div><div class="alert-label">Score riesgo</div><div class="alert-value">{escape(formato_valor(row.get('score_riesgo', np.nan)))}</div></div>
                <div><div class="alert-label">Criterio</div><div class="alert-value">{escape(formato_valor(row.get('criterio_alerta', np.nan)))}</div></div>
                <div><div class="alert-label">Etapa actual</div><div class="alert-value">{escape(formato_valor(row.get('etapa_actual', np.nan)))}</div></div>
                <div><div class="alert-label">Restante TAT</div><div class="alert-value">{escape(texto_dias_restantes(row.get('dias_restantes_tat', np.nan)))}</div></div>
                <div><div class="alert-label">Centro</div><div class="alert-value">{escape(formato_valor(row.get(COL_CENTRO, np.nan)))}</div></div>
                <div><div class="alert-label">Grupo compras</div><div class="alert-value">{escape(formato_valor(row.get(COL_GRUPO_COMPRAS, np.nan)))}</div></div>
                <div><div class="alert-label">Responsable sugerido</div><div class="alert-value">{escape(formato_valor(row.get('responsable_sugerido', np.nan)))}</div></div>
                <div><div class="alert-label">Material</div><div class="alert-value">{escape(formato_valor(row.get(COL_MATERIAL, np.nan)))}</div></div>
                <div><div class="alert-label">Descripción</div><div class="alert-value">{escape(str(row.get(COL_TEXTO, '-'))[:70])}</div></div>
            </div>
        </div>
        """
    ).strip()


def aplicar_estilo_alertas(df_tabla: pd.DataFrame):
    def color_alerta(valor):
        texto = str(valor).strip()
        if texto == "Crítica":
            return "background-color:#fee2e2; color:#991b1b; font-weight:800;"
        if texto == "Alta":
            return "background-color:#ffedd5; color:#9a3412; font-weight:800;"
        if texto == "Media":
            return "background-color:#fef9c3; color:#854d0e; font-weight:800;"
        if texto == "Normal":
            return "background-color:#dcfce7; color:#166534; font-weight:800;"
        if texto == "Sin datos":
            return "background-color:#f1f5f9; color:#475569; font-weight:800;"
        return ""

    styler = df_tabla.style
    if "nivel_alerta" in df_tabla.columns:
        styler = styler.map(color_alerta, subset=["nivel_alerta"])
    return styler


def html_criterio_alerta(dias_alerta_temprana: int) -> str:
    return dedent(
        f"""
        <div class="criteria-box">
            <strong>Criterio de clasificación del nivel de alerta</strong><br>
            <strong>Crítica:</strong> el pedido ya supera el umbral TAT o su performance TAT es "No cumple".<br>
            <strong>Alta:</strong> el pedido aún no vence, pero le quedan {dias_alerta_temprana} días o menos para llegar al umbral.<br>
            <strong>Media:</strong> quedan entre {dias_alerta_temprana + 1} y {dias_alerta_temprana * 2} días para llegar al umbral.<br>
            <strong>Normal:</strong> quedan más de {dias_alerta_temprana * 2} días contra el umbral.<br>
            <strong>Sin datos:</strong> faltan fechas, falta umbral o hay inconsistencias que impiden calcular una alerta confiable.
        </div>
        """
    ).strip()

def construir_label_registro(row: pd.Series) -> str:
    solped = row.get(COL_SOLPED, "-")
    oc = row.get(COL_OC_ME5A, row.get(COL_OC_NME, "-"))
    pos = row.get(COL_POS_SOLPED, "-")
    perf = row.get(COL_PERF_TAT, "-")
    dias = row.get(COL_DIAS_TAT, "-")
    texto = str(row.get(COL_TEXTO, ""))[:55]

    return (
        f"SolPed {formato_id(solped)} | "
        f"OC {formato_id(oc)} | "
        f"Pos {formato_id(pos)} | "
        f"TAT {texto_dias_y_meses(dias)} | "
        f"{perf} | "
        f"{texto}"
    )


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

        if texto in ["0-5 días", "1-5 días", "6-15 días"]:
            return "background-color: #fef9c3; color: #854d0e; font-weight: 700;"

        if texto in ["16-30 días", "mayor a un mes"]:
            return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"

        return ""

    styler = df_tabla.style

    for col in df_tabla.columns:
        if col.startswith("performance_") or col == COL_PERF_TAT:
            styler = styler.map(
                color_performance,
                subset=[col],
            )

        if col == COL_RANGO_INC:
            styler = styler.map(
                color_incumplimiento,
                subset=[col],
            )

    return styler


def html_estado_pedido(row: pd.Series) -> str:
    cards = []

    for etapa in ETAPAS_PEDIDO:
        color = etapa_color(row, etapa)

        fecha = (
            html_texto(row.get(etapa["fecha"], np.nan))
            if etapa.get("fecha")
            else "-"
        )

        dias_col = etapa.get("dias")
        umbral_col = etapa.get("umbral")
        perf_col = etapa.get("performance")

        if dias_col:
            dias_valor = row.get(dias_col, np.nan)
            umbral = (
                html_texto(row.get(umbral_col, np.nan))
                if umbral_col
                else "-"
            )

            fecha_fin_col = etapa.get("fecha")

            if pd.isna(row.get(fecha_fin_col, np.nan)):
                falta = nombre_fecha_faltante(fecha_fin_col)
                dias_txt = f"Pendiente · falta {escape(falta)}"
            elif dias_col == COL_DIAS_TAT:
                dias_txt = (
                    escape(texto_dias_y_meses(dias_valor))
                    + f" · umbral {umbral} días"
                )
            else:
                dias = html_texto(dias_valor)
                dias_txt = f"{dias} días · umbral {umbral}"
        else:
            dias_txt = "Punto de inicio"

        perf_val = (
            row.get(perf_col, "Registrado")
            if perf_col
            else "Registrado"
        )

        perf_color = (
            clase_performance(perf_val)
            if perf_col
            else color
        )

        cards.append(
            f"""
            <div class="stage-card stage-{color}">
                <div class="stage-title">{escape(etapa['titulo'])}</div>
                <div class="stage-date">{fecha}</div>
                <div class="stage-note">{escape(etapa['nota'])}</div>
                <div class="stage-days">{dias_txt}</div>
                {pill(perf_val, perf_color)}
            </div>
            """
        )

    return f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
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

            .stage-card:last-child::after {{
                content: "";
            }}

            .stage-green {{
                background: #f0fdf4;
                border-color: #bbf7d0;
            }}

            .stage-red {{
                background: #fef2f2;
                border-color: #fecaca;
            }}

            .stage-yellow {{
                background: #fefce8;
                border-color: #fde68a;
            }}

            .stage-gray {{
                background: #f8fafc;
                border-color: #e2e8f0;
            }}

            .stage-blue {{
                background: #eff6ff;
                border-color: #bfdbfe;
            }}

            .stage-title {{
                font-size: 0.82rem;
                font-weight: 850;
                color: #0f172a;
                margin-bottom: 6px;
            }}

            .stage-date {{
                font-size: 1.05rem;
                font-weight: 850;
                color: #111827;
                margin-bottom: 5px;
            }}

            .stage-note {{
                color: #64748b;
                font-size: 0.76rem;
                line-height: 1.25;
                min-height: 28px;
                margin-bottom: 9px;
            }}

            .stage-days {{
                font-size: 0.88rem;
                color: #334155;
                margin-bottom: 7px;
            }}

            .pill {{
                display: inline-block;
                border-radius: 999px;
                padding: 4px 9px;
                font-size: 0.76rem;
                font-weight: 800;
                border: 1px solid transparent;
                white-space: nowrap;
            }}

            .pill-green {{
                background: #dcfce7;
                color: #166534;
                border-color: #bbf7d0;
            }}

            .pill-red {{
                background: #fee2e2;
                color: #991b1b;
                border-color: #fecaca;
            }}

            .pill-yellow {{
                background: #fef9c3;
                color: #854d0e;
                border-color: #fde68a;
            }}

            .pill-gray {{
                background: #f1f5f9;
                color: #475569;
                border-color: #e2e8f0;
            }}

            .pill-blue {{
                background: #dbeafe;
                color: #1e40af;
                border-color: #bfdbfe;
            }}

            @media (max-width: 1200px) {{
                .stage-wrap {{
                    grid-template-columns: repeat(3, minmax(150px, 1fr));
                }}

                html, body {{
                    overflow: auto;
                }}
            }}

            @media (max-width: 760px) {{
                .stage-wrap {{
                    grid-template-columns: 1fr;
                    padding-bottom: 24px;
                }}

                .stage-card::after {{
                    content: "↓";
                    right: 50%;
                    top: auto;
                    bottom: -14px;
                    transform: translateX(50%);
                }}

                .stage-card:last-child::after {{
                    content: "";
                }}
            }}
        </style>
    </head>
    <body>
        <div class="stage-wrap">{''.join(cards)}</div>
    </body>
    </html>
    """


# =========================================================
# Interfaz
# =========================================================
mostrar_logo()

st.markdown(
    """
    <div style="text-align:center; margin-bottom: 22px;">
        <div style="font-size:42px; font-weight:850; color:#1F2937; line-height:1.12;">
            Buscador SolPed / OC
        </div>
        <div style="font-size:14px; color:#6B7280; margin-top:10px;">
            Filtro · Estado del pedido · Seguimiento TAT
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configuración")

    dias_alerta_temprana = st.slider(
        "Ventana de alerta temprana",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
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


# =========================================================
# Leer dataframe global
# =========================================================
st.markdown(
    "<h2 style='font-size:28px; font-weight:800; color:#1F2937;'>Archivo</h2>",
    unsafe_allow_html=True,
)

if "df_tat" not in st.session_state:
    st.warning("Primero debes cargar el archivo base en Análisis TAT > Cargar archivo.")
    st.stop()

nombre_archivo = st.session_state.get(
    "nombre_archivo_tat",
    "Archivo cargado",
)

try:
    df = st.session_state["df_tat"].copy()
    df = limpiar_columnas(df)
    df = convertir_fechas_visuales(df)
    opciones_filtros = construir_opciones_filtros(df)
    df_alertas = construir_alertas(
        df,
        dias_alerta_temprana=dias_alerta_temprana,
    )

    st.success(f"Archivo activo: {nombre_archivo}")

except Exception as e:
    st.error("No se pudo preparar el archivo cargado.")
    st.exception(e)
    st.stop()


# =========================================================
# Filtros principales visibles
# =========================================================
st.markdown("### Filtros principales")

c1, c2, c3, c4 = st.columns([1, 1, 0.8, 0.8])

with c1:
    txt_solped = st.text_input(
        "SolPed",
        placeholder="Ej: 1001973319",
        key="filtro_solped",
    )

with c2:
    txt_oc = st.text_input(
        "Orden de compra / Pedido",
        placeholder="Ej: 4502321875",
        key="filtro_oc",
    )

with c3:
    txt_pos_solped = st.text_input(
        "Posición SolPed",
        placeholder="Ej: 10",
        key="filtro_pos_solped",
    )

with c4:
    opciones_centro = opciones_filtros.get(COL_CENTRO, [])
    centro_default = [
        centro
        for centro in opciones_centro
        if str(centro).strip().upper() == "E002"
    ]
    centro_sel = st.multiselect(
        "Centro",
        opciones_centro,
        default=centro_default,
        help="Por defecto queda E002 cuando existe en el archivo; puedes quitarlo o elegir otros centros.",
    )

st.button(
    "Limpiar filtros principales",
    on_click=limpiar_filtros_principales,
    use_container_width=False,
)


# =========================================================
# Filtros avanzados colapsados
# =========================================================
with st.expander("Filtros avanzados", expanded=False):
    st.caption("Úsalos solo cuando necesites acotar más la búsqueda.")

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        txt_pos_oc = st.text_input(
            "Posición OC",
            placeholder="Ej: 10",
        )

        txt_material = st.text_input(
            "Material",
            placeholder="Ej: 20012021",
        )

        txt_descripcion = st.text_input(
            "Descripción / texto breve",
            placeholder="Ej: bloqueador",
        )

    with a2:
        txt_solicitante = st.text_input(
            "Solicitante",
            placeholder="Ej: c.silva",
        )

        txt_autor = st.text_input(
            "Autor",
            placeholder="Ej: CL17330735",
        )


    with a3:
        tipo_oc_sel = st.multiselect(
            "Tipo OC",
            opciones_filtros.get(COL_TIPO_OC, []),
        )

        origen_sel = st.multiselect(
            "Origen",
            opciones_filtros.get(COL_ORIGEN, []),
        )

        sistema_sel = st.multiselect(
            "Sistema",
            opciones_filtros.get(COL_SISTEMA, []),
        )

    with a4:
        grupo_sel = st.multiselect(
            "Grupo de compras",
            opciones_filtros.get(COL_GRUPO_COMPRAS, []),
        )

        estado_match_sel = st.multiselect(
            "Estado del match",
            opciones_filtros.get(COL_ESTADO_MATCH, []),
        )

        perf_tat_sel = st.multiselect(
            "Performance TAT",
            opciones_filtros.get(COL_PERF_TAT, []),
        )

        rango_inc_sel = st.multiselect(
            "Rango incumplimiento TAT",
            opciones_filtros.get(COL_RANGO_INC, []),
        )

    st.markdown("#### Rango de días / monto")

    r1, r2, r3, r4 = st.columns(4)

    with r1:
        usar_dias_tat_min = st.checkbox(
            "TAT mínimo",
            value=False,
        )

        dias_tat_min = st.number_input(
            "Valor mínimo TAT",
            value=0,
            step=1,
            disabled=not usar_dias_tat_min,
        )

    with r2:
        usar_dias_tat_max = st.checkbox(
            "TAT máximo",
            value=False,
        )

        dias_tat_max = st.number_input(
            "Valor máximo TAT",
            value=9999,
            step=1,
            disabled=not usar_dias_tat_max,
        )

    with r3:
        usar_monto_min = st.checkbox(
            "Monto mínimo",
            value=False,
        )

        monto_min = st.number_input(
            "Valor mínimo monto",
            value=0.0,
            step=1000.0,
            disabled=not usar_monto_min,
        )

    with r4:
        usar_monto_max = st.checkbox(
            "Monto máximo",
            value=False,
        )

        monto_max = st.number_input(
            "Valor máximo monto",
            value=0.0,
            step=1000.0,
            disabled=not usar_monto_max,
        )

    f1, f2 = st.columns(2)

    with f1:
        solo_incumplimiento = st.checkbox(
            "Solo incumplimiento TAT",
            value=False,
        )

    with f2:
        solo_fechas_inconsistentes = st.checkbox(
            "Solo fechas inconsistentes",
            value=False,
        )

    st.markdown("#### Fecha")

    fecha_col_disponibles = [
        c for c in FECHAS_CANDIDATAS
        if c in df.columns and pd.api.types.is_datetime64_any_dtype(df[c])
    ]

    if fecha_col_disponibles:
        usar_filtro_fecha = st.checkbox(
            "Aplicar filtro de fecha",
            value=False,
        )

        col_fecha_filtro = st.selectbox(
            "Columna de fecha",
            fecha_col_disponibles,
            index=0,
            disabled=not usar_filtro_fecha,
        )

        fecha_min_real = df[col_fecha_filtro].min()
        fecha_max_real = df[col_fecha_filtro].max()

        if pd.notna(fecha_min_real) and pd.notna(fecha_max_real):
            fc1, fc2 = st.columns(2)

            with fc1:
                fecha_desde = st.date_input(
                    "Desde",
                    value=fecha_min_real.date(),
                    disabled=not usar_filtro_fecha,
                )

            with fc2:
                fecha_hasta = st.date_input(
                    "Hasta",
                    value=fecha_max_real.date(),
                    disabled=not usar_filtro_fecha,
                )
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
mask &= (
    filtrar_por_ids(df, COL_OC_ME5A, txt_oc)
    | filtrar_por_ids(df, COL_OC_NME, txt_oc)
)
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
    fin = (
        pd.Timestamp(fecha_hasta)
        + pd.Timedelta(days=1)
        - pd.Timedelta(seconds=1)
    )

    mask &= df[col_fecha_filtro].between(
        inicio,
        fin,
        inclusive="both",
    )

df_filtrado = df.loc[mask].copy()
df_alertas_filtrado = df_alertas.loc[mask].copy()


# =========================================================
# Coincidencias destacadas
# =========================================================
porcentaje = (
    len(df_filtrado) / len(df) * 100
    if len(df)
    else 0
)

st.markdown(
    f"""
    <div class="match-box">
        <div class="match-number">{len(df_filtrado):,}</div>
        <div class="match-label">
            coincidencias encontradas de {len(df):,} registros cargados · {porcentaje:.1f}% del archivo
        </div>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True,
)



# =========================================================
# Alertas ejecutivas
# =========================================================
st.markdown("### Alertas ejecutivas")
st.markdown(
    html_criterio_alerta(dias_alerta_temprana),
    unsafe_allow_html=True,
)

if df_alertas_filtrado.empty:
    st.info("No hay alertas para los filtros aplicados.")
else:
    total_alertas = len(df_alertas_filtrado)
    criticas = int((df_alertas_filtrado["nivel_alerta"] == "Crítica").sum())
    altas = int((df_alertas_filtrado["nivel_alerta"] == "Alta").sum())
    media_score = df_alertas_filtrado["score_riesgo"].mean()

    ak1, ak2, ak3, ak4 = st.columns(4)
    ak1.metric("Pedidos filtrados", f"{total_alertas:,}".replace(",", "."))
    ak2.metric("Críticos", f"{criticas:,}".replace(",", "."))
    ak3.metric("Alta prioridad", f"{altas:,}".replace(",", "."))
    ak4.metric(
        "Score promedio",
        f"{media_score:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."),
    )

    for _, row_alerta in df_alertas_filtrado.head(10).iterrows():
        st.markdown(
            html_alerta(row_alerta),
            unsafe_allow_html=True,
        )

    with st.expander("Matriz de alertas", expanded=False):
        columnas_default_alerta = [
            c for c in COLUMNAS_ALERTA
            if c in df_alertas_filtrado.columns
        ]

        columnas_alerta_visibles = st.multiselect(
            "Columnas visibles de alerta",
            options=df_alertas_filtrado.columns.tolist(),
            default=columnas_default_alerta,
        )

        if columnas_alerta_visibles:
            tabla_alertas = (
                df_alertas_filtrado[columnas_alerta_visibles]
                .head(int(limite_vista))
                .copy()
            )
            st.dataframe(
                aplicar_estilo_alertas(tabla_alertas),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("Selecciona al menos una columna de alerta.")

# =========================================================
# Estado del pedido unificado
# =========================================================
idx_sel = None

if df_filtrado.empty:
    st.warning("No hay resultados con los filtros aplicados.")
else:
    opciones_detalle = []

    for idx, row_iter in df_filtrado.head(5000).iterrows():
        opciones_detalle.append(
            (
                idx,
                construir_label_registro(row_iter),
            )
        )

    labels = [
        item[1]
        for item in opciones_detalle
    ]

    label_sel = st.selectbox(
        "Registro",
        labels,
    )

    idx_sel = opciones_detalle[
        labels.index(label_sel)
    ][0]

    row = df_filtrado.loc[idx_sel]

    perf_tat = row.get(COL_PERF_TAT, np.nan)
    perf_color = clase_performance(perf_tat)
    rango_inc = row.get(COL_RANGO_INC, np.nan)
    dias_tat = row.get(COL_DIAS_TAT, np.nan)
    dias_inc = row.get(COL_DIAS_INC, np.nan)
    umbral_tat = obtener_umbral_tat(row)

    tat_total_txt = texto_tat_total_usuario(
        perf_tat,
        dias_tat,
    )

    dias_inc_txt = (
        "Pendiente"
        if (
            str(perf_tat).strip().lower() == "en proceso"
            and pd.isna(
                pd.to_numeric(
                    pd.Series([dias_inc]),
                    errors="coerce",
                ).iloc[0]
            )
        )
        else texto_dias_y_meses(dias_inc)
    )

    detalle_tat = detalle_estado_tat(
        perf_tat,
        umbral_tat,
        dias_inc,
        rango_inc,
    )

    tat_html = dedent(
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
        """
    ).strip()

    order_head_html = dedent(
        f"""
        <div class="order-head">
            <div class="order-title">Datos principales del pedido</div>
            <div class="head-grid">
                <div>
                    <div class="head-label">SolPed</div>
                    <div class="head-value">{html_id(row.get(COL_SOLPED, np.nan))}</div>
                </div>
                <div>
                    <div class="head-label">Orden de compra / Pedido</div>
                    <div class="head-value">{html_id(row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan)))}</div>
                </div>
                <div>
                    <div class="head-label">Posición SolPed</div>
                    <div class="head-value">{html_id(row.get(COL_POS_SOLPED, np.nan))}</div>
                </div>
                <div>
                    <div class="head-label">Material</div>
                    <div class="head-value">{html_id(row.get(COL_MATERIAL, np.nan))}</div>
                </div>
                <div>
                    <div class="head-label">Centro</div>
                    <div class="head-value">{html_texto(row.get(COL_CENTRO, np.nan))}</div>
                </div>
            </div>
        </div>
        """
    ).strip()

    st.markdown(
        tat_html,
        unsafe_allow_html=True,
    )

    st.markdown(
        html_avance_actual(row),
        unsafe_allow_html=True,
    )

    st.markdown(
        dedent(html_linea_pedido(row)).strip(),
        unsafe_allow_html=True,
    )

    st.markdown(
        order_head_html,
        unsafe_allow_html=True,
    )

    components.html(
        html_estado_pedido(row),
        height=230,
        scrolling=False,
    )


# =========================================================
# Distribuciones simples
# =========================================================
with st.expander("Distribuciones del resultado", expanded=False):
    b1, b2, b3 = st.columns(3)

    with b1:
        if COL_PERF_TAT in df_filtrado.columns:
            st.markdown("**Performance TAT**")

            tabla_perf = (
                df_filtrado[COL_PERF_TAT]
                .value_counts(dropna=False)
                .reset_index()
            )

            tabla_perf.columns = [
                "Performance TAT",
                "Cantidad",
            ]

            st.dataframe(
                tabla_perf,
                use_container_width=True,
                hide_index=True,
            )

    with b2:
        if COL_RANGO_INC in df_filtrado.columns:
            st.markdown("**Rango incumplimiento TAT**")

            tabla_rango = (
                df_filtrado[COL_RANGO_INC]
                .value_counts(dropna=False)
                .reset_index()
            )

            tabla_rango.columns = [
                "Rango",
                "Cantidad",
            ]

            st.dataframe(
                tabla_rango,
                use_container_width=True,
                hide_index=True,
            )

    with b3:
        if COL_ESTADO_MATCH in df_filtrado.columns:
            st.markdown("**Estado del match**")

            tabla_estado = (
                df_filtrado[COL_ESTADO_MATCH]
                .value_counts(dropna=False)
                .reset_index()
            )

            tabla_estado.columns = [
                "Estado",
                "Cantidad",
            ]

            st.dataframe(
                tabla_estado,
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# Tabla de resultado filtrado
# =========================================================
with st.expander("Tabla de resultado filtrado", expanded=False):
    columnas_base = [
        c for c in COLUMNAS_TABLA_PRINCIPAL
        if c in df_filtrado.columns
    ]

    columnas_extra = []

    for etapa in ETAPAS_PEDIDO:
        for col in [
            etapa.get("fecha"),
            etapa.get("dias"),
            etapa.get("umbral"),
            etapa.get("performance"),
        ]:
            if (
                col
                and col in df_filtrado.columns
                and col not in columnas_base
                and col not in columnas_extra
            ):
                columnas_extra.append(col)

    columnas_default = (
        df_filtrado.columns.tolist()
        if mostrar_todas_columnas
        else columnas_base + columnas_extra
    )

    columnas_visibles = st.multiselect(
        "Columnas visibles",
        options=df_filtrado.columns.tolist(),
        default=columnas_default,
    )

    if columnas_visibles:
        tabla = (
            df_filtrado[columnas_visibles]
            .head(int(limite_vista))
            .copy()
        )

        st.dataframe(
            aplicar_estilo_tabla(tabla),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Selecciona al menos una columna.")


# =========================================================
# Registro completo transpuesto
# =========================================================
with st.expander("Registro completo transpuesto", expanded=False):
    if df_filtrado.empty or idx_sel is None:
        st.info("No hay registros para visualizar.")
    else:
        registro_t = (
            df_filtrado
            .loc[[idx_sel]]
            .T
            .reset_index()
        )

        registro_t.columns = [
            "Campo",
            "Valor",
        ]

        st.dataframe(
            registro_t,
            use_container_width=True,
            hide_index=True,
        )


# =========================================================
# Descargas
# =========================================================
st.markdown("### Descarga")

csv_bytes = dataframe_a_csv(df_filtrado)
csv_alertas_bytes = dataframe_a_csv(df_alertas_filtrado)

x1, x2, x3 = st.columns(3)

with x1:
    st.download_button(
        "Descargar CSV filtrado",
        data=csv_bytes,
        file_name="resultado_filtrado_solped_oc.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.download_button(
        "Descargar CSV alertas",
        data=csv_alertas_bytes,
        file_name="alertas_filtradas_solped_oc.csv",
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
        st.button(
            "Parquet no disponible",
            disabled=True,
            use_container_width=True,
        )

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
        st.button(
            "Excel no disponible",
            disabled=True,
            use_container_width=True,
        )

        st.caption("Excel se desactiva sobre 250.000 filas.")


# =========================================================
# Info técnica
# =========================================================
with st.expander("Columnas disponibles", expanded=False):
    st.write(df.columns.tolist())
