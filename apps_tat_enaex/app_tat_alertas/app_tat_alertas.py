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
COL_ESTADO_RECEPCION_ALERTA = "estado_recepcion"

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
    COL_ESTADO_RECEPCION_ALERTA,
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
# Catálogo de centros
# =========================================================
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


def normalizar_codigo_centro(valor: Any) -> str:
    if pd.isna(valor):
        return "Sin dato"

    texto = str(valor).strip()
    if not texto or texto.lower() in ["nan", "none", "nat"]:
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


def lista_centros_corta(valores: Any, max_items: int = 4) -> str:
    if valores is None:
        return "Todos"
    if isinstance(valores, str):
        valores = [valores]

    etiquetas = [etiqueta_centro(v) for v in valores if str(v).strip()]
    if not etiquetas:
        return "Todos"
    if len(etiquetas) <= max_items:
        return ", ".join(etiquetas)
    return ", ".join(etiquetas[:max_items]) + f" +{len(etiquetas) - max_items} más"


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

        .exp-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 22px;
            padding: 18px 20px;
            margin: 0.75rem 0 0.9rem 0;
            box-shadow: 0 1px 6px rgba(15, 23, 42, 0.045);
        }

        .exp-title-row {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 16px;
            margin-bottom: 14px;
        }

        .exp-title {
            color: #0f172a;
            font-size: 1.12rem;
            line-height: 1.15;
            font-weight: 950;
        }

        .exp-subtitle {
            color: #64748b;
            font-size: 0.86rem;
            line-height: 1.35;
            margin-top: 4px;
        }

        .exp-status-pill {
            display: inline-block;
            background: #eff6ff;
            color: #1e40af;
            border: 1px solid #bfdbfe;
            border-radius: 999px;
            padding: 6px 11px;
            font-size: 0.8rem;
            font-weight: 900;
            white-space: nowrap;
        }

        .exp-main-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(120px, 1fr));
            gap: 10px;
        }

        .exp-field {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 16px;
            padding: 11px 12px;
            min-height: 68px;
        }

        .exp-field-label {
            color: #64748b;
            font-size: 0.7rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.045em;
            margin-bottom: 5px;
        }

        .exp-field-value {
            color: #0f172a;
            font-size: 0.98rem;
            font-weight: 900;
            line-height: 1.2;
            overflow-wrap: anywhere;
        }

        .exp-kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(160px, 1fr));
            gap: 12px;
            margin: 0.7rem 0 0.9rem 0;
        }

        .exp-kpi-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 14px 15px;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
            min-height: 96px;
        }

        .exp-kpi-card-primary {
            background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
            border-color: #bfdbfe;
        }

        .exp-kpi-label {
            color: #64748b;
            font-size: 0.72rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.045em;
            margin-bottom: 7px;
        }

        .exp-kpi-value {
            color: #0f172a;
            font-size: 1.15rem;
            line-height: 1.18;
            font-weight: 950;
            overflow-wrap: anywhere;
        }

        .exp-kpi-note {
            color: #64748b;
            font-size: 0.78rem;
            line-height: 1.3;
            margin-top: 5px;
        }

        .tat-flow-card {
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
            border: 1px solid #dbeafe;
            border-radius: 22px;
            padding: 18px 20px 16px 20px;
            margin: 0.85rem 0 0.95rem 0;
            box-shadow: 0 1px 6px rgba(15, 23, 42, 0.045);
        }

        .tat-flow-title {
            font-size: 0.9rem;
            font-weight: 950;
            color: #1e3a8a;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.045em;
        }

        .tat-flow {
            display: flex;
            align-items: stretch;
            width: 100%;
            overflow-x: auto;
            padding-bottom: 4px;
        }

        .tat-flow-step {
            flex: 0 0 154px;
            text-align: center;
            min-width: 0;
        }

        .tat-flow-dot {
            width: 54px;
            height: 54px;
            border-radius: 999px;
            margin: 0 auto 10px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            font-size: 1.1rem;
            box-sizing: border-box;
        }

        .tat-flow-dot-ok {
            background: #22c55e;
            color: #ffffff;
            border: 4px solid #22c55e;
        }

        .tat-flow-dot-risk {
            background: #fff7ed;
            color: #c2410c;
            border: 5px solid #fb923c;
        }

        .tat-flow-dot-bad {
            background: #fef2f2;
            color: #991b1b;
            border: 5px solid #ef4444;
        }

        .tat-flow-dot-active {
            background: #ffffff;
            color: #1d4ed8;
            border: 6px solid #3b82f6;
        }

        .tat-flow-dot-pending {
            background: #ffffff;
            color: #94a3b8;
            border: 5px solid #cbd5e1;
        }

        .tat-flow-label {
            font-size: 0.82rem;
            font-weight: 950;
            color: #1f2937;
            line-height: 1.15;
            text-transform: uppercase;
        }

        .tat-flow-date {
            color: #475569;
            font-size: 0.76rem;
            line-height: 1.22;
            margin-top: 4px;
            overflow-wrap: anywhere;
        }

        .tat-flow-detail {
            color: #334155;
            font-size: 0.76rem;
            line-height: 1.25;
            margin-top: 6px;
        }

        .tat-flow-connector {
            flex: 1 1 auto;
            height: 7px;
            min-width: 34px;
            margin-top: 24px;
            border-radius: 999px;
            background: #cbd5e1;
        }

        .tat-flow-connector-ok {
            background: #22c55e;
        }

        .tat-flow-connector-active {
            background: repeating-linear-gradient(90deg, #3b82f6 0 18px, transparent 18px 30px);
        }

        .tat-flow-note {
            color: #475569;
            font-size: 0.84rem;
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

        @media (max-width: 1200px) {
            .exp-main-grid {
                grid-template-columns: repeat(3, minmax(120px, 1fr));
            }

            .exp-kpi-grid {
                grid-template-columns: repeat(2, minmax(160px, 1fr));
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

            .exp-main-grid,
            .exp-kpi-grid,
            .exp-kpi-grid-5 {
                grid-template-columns: 1fr;
            }

            .exp-title-row {
                flex-direction: column;
                align-items: flex-start;
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


        .exp-filter-hero {
            background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
            border: 1px solid #93c5fd;
            border-left: 7px solid #2563eb;
            border-radius: 22px;
            padding: 18px 20px;
            margin: 0.8rem 0 0.9rem 0;
            box-shadow: 0 2px 10px rgba(37, 99, 235, 0.08);
        }

        .exp-filter-hero-title {
            color: #1e3a8a;
            font-size: 1.05rem;
            line-height: 1.25;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.035em;
            margin-bottom: 6px;
        }

        .exp-filter-hero-text {
            color: #334155;
            font-size: 0.93rem;
            line-height: 1.45;
        }

        .exp-filter-help {
            background: #fff7ed;
            border: 1px solid #fed7aa;
            border-left: 6px solid #f97316;
            border-radius: 18px;
            padding: 13px 15px;
            margin: 0.45rem 0 0.8rem 0;
            color: #7c2d12;
            font-size: 0.9rem;
            line-height: 1.4;
            font-weight: 750;
        }


        .alert-box {
            border-radius: 14px;
            padding: 11px 13px;
            border: 1px solid #e5e7eb;
            background: #ffffff;
            box-shadow: none;
            margin: 0.45rem 0;
        }

        .alert-red { background: #fffafa; border-left: 4px solid #ef4444; }
        .alert-orange { background: #fffaf5; border-left: 4px solid #f97316; }
        .alert-yellow { background: #fffdf2; border-left: 4px solid #eab308; }
        .alert-green { background: #f8fff9; border-left: 4px solid #22c55e; }
        .alert-gray { background: #f8fafc; border-left: 4px solid #94a3b8; }

        .alert-title {
            color: #0f172a;
            font-size: 0.94rem;
            font-weight: 850;
            margin-bottom: 7px;
        }

        .alert-grid {
            display: grid;
            grid-template-columns: 1fr 0.9fr 1.2fr 1fr;
            gap: 8px 14px;
        }

        .alert-label {
            color: #64748b;
            font-size: 0.67rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 800;
            margin-bottom: 2px;
        }

        .alert-value {
            color: #0f172a;
            font-size: 0.88rem;
            font-weight: 780;
            overflow-wrap: anywhere;
            line-height: 1.25;
        }


        .critical-hero {
            background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
            border: 1px solid #fdba74;
            border-left: 8px solid #ea580c;
            border-radius: 22px;
            padding: 18px 20px;
            margin: 0.85rem 0 1rem 0;
            box-shadow: 0 2px 10px rgba(234, 88, 12, 0.08);
        }

        .critical-hero-title {
            color: #7c2d12;
            font-size: 1.02rem;
            line-height: 1.25;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.035em;
            margin-bottom: 6px;
        }

        .critical-hero-text {
            color: #334155;
            font-size: 0.92rem;
            line-height: 1.45;
        }

        .critical-selected-card {
            background: linear-gradient(180deg, #fef2f2 0%, #ffffff 100%);
            border: 1px solid #fecaca;
            border-left: 8px solid #dc2626;
            border-radius: 22px;
            padding: 16px 18px;
            margin: 0.8rem 0 0.9rem 0;
            box-shadow: 0 2px 10px rgba(220, 38, 38, 0.08);
        }

        .critical-selected-title {
            color: #7f1d1d;
            font-size: 0.94rem;
            font-weight: 950;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 10px;
        }

        .critical-selected-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(130px, 1fr));
            gap: 10px;
        }

        .critical-selected-field {
            background: #ffffff;
            border: 1px solid #fee2e2;
            border-radius: 14px;
            padding: 10px 12px;
        }

        .critical-selected-label {
            color: #64748b;
            font-size: 0.68rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0.045em;
            margin-bottom: 4px;
        }

        .critical-selected-value {
            color: #0f172a;
            font-size: 0.96rem;
            font-weight: 900;
            line-height: 1.22;
            overflow-wrap: anywhere;
        }

        @media (max-width: 1200px) {
            .critical-selected-grid {
                grid-template-columns: repeat(2, minmax(130px, 1fr));
            }
        }

        @media (max-width: 760px) {
            .critical-selected-grid {
                grid-template-columns: 1fr;
            }
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
    st.session_state["filtro_estado_recepcion"] = "Sin recepción"


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
    dias_parcial = formato_tiempo_transcurrido(avance["dias_parcial"])
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




def html_resumen_pedido_expediente(row: pd.Series) -> str:
    oc_principal = row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan))
    pos_principal = row.get(COL_POS_SOLPED, np.nan)
    estado_recepcion = row.get("estado_recepcion_simple", row.get(COL_ESTADO_RECEPCION_ALERTA, np.nan))
    tiempo_transcurrido = row.get("tiempo_transcurrido_tat", np.nan)
    dias_restantes = row.get("dias_restantes_texto", row.get("dias_restantes_tat", np.nan))

    return dedent(
        f"""
        <div class="exp-card">
            <div class="exp-title-row">
                <div>
                    <div class="exp-title">Resumen del pedido · SolPed {html_id(row.get(COL_SOLPED, np.nan))}</div>
                    <div class="exp-subtitle">Pedido {html_id(oc_principal)} · Posición solicitud de pedido {html_id(pos_principal)} · Centro {html_texto(row.get(COL_CENTRO, np.nan))}</div>
                </div>
                <div class="exp-status-pill">{html_texto(estado_recepcion)}</div>
            </div>
            <div class="exp-main-grid">
                <div class="exp-field">
                    <div class="exp-field-label">Solicitud de pedido</div>
                    <div class="exp-field-value">{html_id(row.get(COL_SOLPED, np.nan))}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Pedido</div>
                    <div class="exp-field-value">{html_id(oc_principal)}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Tiempo transcurrido</div>
                    <div class="exp-field-value">{html_texto(tiempo_transcurrido)}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Vencimiento / plazo</div>
                    <div class="exp-field-value">{html_texto(dias_restantes)}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Centro</div>
                    <div class="exp-field-value">{html_texto(row.get(COL_CENTRO, np.nan))}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Posición solicitud de pedido</div>
                    <div class="exp-field-value">{html_id(pos_principal)}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Grupo compras</div>
                    <div class="exp-field-value">{html_texto(row.get(COL_GRUPO_COMPRAS, np.nan))}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Nivel alerta</div>
                    <div class="exp-field-value">{html_texto(row.get('nivel_alerta', np.nan))}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Fecha pendiente</div>
                    <div class="exp-field-value">{html_texto(row.get('fecha_pendiente', np.nan))}</div>
                </div>
                <div class="exp-field">
                    <div class="exp-field-label">Acción sugerida</div>
                    <div class="exp-field-value">{html_texto(row.get('accion_sugerida', np.nan))}</div>
                </div>
            </div>
        </div>
        """
    ).strip()

def html_kpis_expediente(row: pd.Series) -> str:
    estado_pedido = row.get("clasificacion_vencimiento", np.nan)
    fecha_vencimiento = row.get("fecha_vencimiento_texto", np.nan)
    fuente_vencimiento = row.get("fuente_calculo_vencimiento", np.nan)
    tiempo_transcurrido = row.get("tiempo_transcurrido_tat", np.nan)
    exceso_umbral = row.get("tiempo_excedido_umbral_texto", np.nan)

    return dedent(
        f"""
        <div class="exp-kpi-grid exp-kpi-grid-5">
            <div class="exp-kpi-card exp-kpi-card-primary">
                <div class="exp-kpi-label">Estado pedido</div>
                <div class="exp-kpi-value">{html_texto(estado_pedido)}</div>
                <div class="exp-kpi-note">Fecha vencimiento: {html_texto(fecha_vencimiento)} · {html_texto(fuente_vencimiento)}</div>
            </div>
            <div class="exp-kpi-card exp-kpi-card-primary">
                <div class="exp-kpi-label">Tiempo desde inicio del pedido</div>
                <div class="exp-kpi-value">{html_texto(tiempo_transcurrido)}</div>
                <div class="exp-kpi-note">Desde la fecha de solicitud hasta recepción o hasta hoy</div>
            </div>
            <div class="exp-kpi-card exp-kpi-card-primary">
                <div class="exp-kpi-label">Tiempo pasado del umbral</div>
                <div class="exp-kpi-value">{html_texto(exceso_umbral)}</div>
                <div class="exp-kpi-note">Exceso sobre el umbral TAT total</div>
            </div>
            <div class="exp-kpi-card">
                <div class="exp-kpi-label">Última etapa registrada</div>
                <div class="exp-kpi-value">{html_texto(row.get('ultima_etapa_registrada', np.nan))}</div>
                <div class="exp-kpi-note">Última fecha: {html_texto(row.get('ultima_fecha_registrada_texto', np.nan))}</div>
            </div>
            <div class="exp-kpi-card">
                <div class="exp-kpi-label">Fecha pendiente</div>
                <div class="exp-kpi-value">{html_texto(row.get('fecha_pendiente', np.nan))}</div>
                <div class="exp-kpi-note">Siguiente hito requerido</div>
            </div>
        </div>
        """
    ).strip()

def _estado_visual_etapa_tat(row: pd.Series, etapa: dict, indice: int, indice_activo: int) -> tuple[str, str]:
    fecha_col = etapa.get("fecha")
    completada = bool(fecha_col and pd.notna(row.get(fecha_col, np.nan)))
    perf_col = etapa.get("performance")
    perf = str(row.get(perf_col, "")).strip().lower() if perf_col else ""

    if completada and perf == "no cumple":
        return "tat-flow-dot-bad", "!"
    if completada and perf in ["en proceso", "sin datos"]:
        return "tat-flow-dot-risk", "…"
    if completada:
        return "tat-flow-dot-ok", "✓"
    if indice == indice_activo:
        return "tat-flow-dot-active", ""
    return "tat-flow-dot-pending", ""


def html_diagrama_tat_unificado(row: pd.Series) -> str:
    etapas = ETAPAS_PEDIDO
    completadas = [pd.notna(row.get(etapa.get("fecha"), np.nan)) for etapa in etapas]
    try:
        indice_activo = completadas.index(False)
    except ValueError:
        indice_activo = len(etapas) - 1

    partes = []
    for i, etapa in enumerate(etapas):
        dot_class, icono = _estado_visual_etapa_tat(row, etapa, i, indice_activo)
        fecha_txt = fecha_etapa_texto(row, etapa.get("fecha")) if etapa.get("fecha") else "-"
        dias_col = etapa.get("dias")
        umbral_col = etapa.get("umbral")
        perf_col = etapa.get("performance")

        if dias_col:
            dias_txt = formato_tiempo_transcurrido(row.get(dias_col, np.nan))
            umbral_txt = formato_valor(row.get(umbral_col, np.nan)) if umbral_col else "-"
            perf_txt = formato_valor(row.get(perf_col, np.nan)) if perf_col else "Registrado"
            detalle = f"{dias_txt} · umbral {umbral_txt} días · {perf_txt}"
        else:
            detalle = "Punto de inicio"

        partes.append(
            dedent(
                f"""
                <div class="tat-flow-step">
                    <div class="tat-flow-dot {dot_class}">{escape(icono)}</div>
                    <div class="tat-flow-label">{escape(str(etapa.get('titulo', '')))}</div>
                    <div class="tat-flow-date">{escape(fecha_txt)}</div>
                    <div class="tat-flow-detail">{escape(detalle)}</div>
                </div>
                """
            ).strip()
        )

        if i < len(etapas) - 1:
            if completadas[i] and completadas[i + 1]:
                connector_class = "tat-flow-connector-ok"
            elif completadas[i] and not completadas[i + 1]:
                connector_class = "tat-flow-connector-active"
            else:
                connector_class = ""
            partes.append(f'<div class="tat-flow-connector {connector_class}"></div>')

    estado_tat = formato_valor(row.get(COL_PERF_TAT, np.nan))
    dias_tat = texto_tat_total_usuario(row.get(COL_PERF_TAT, np.nan), row.get(COL_DIAS_TAT, np.nan))
    return dedent(
        f"""
        <div class="tat-flow-card">
            <div class="tat-flow-title">Etapas TAT</div>
            <div class="tat-flow">{''.join(partes)}</div>
            <div class="tat-flow-note">
                TAT total: <strong>{escape(dias_tat)}</strong> · Estado: <strong>{escape(estado_tat)}</strong>. Las etapas respetan el orden original: Solicitud, Liberación SolPed, Comprador, Proveedor, Logística y TAT Total.
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


def tiene_recepcion_registrada_alerta(row: pd.Series) -> bool:
    """Identifica si el registro ya tiene recepción real.

    Se usa para ocultar por defecto pedidos ya recepcionados aunque falten
    hitos intermedios, como liberación. El usuario puede modificar el filtro.
    """
    for col in ["fecha_recepcion_final", "Fecha recepción mercancía - NME80FN"]:
        if col in row.index and pd.notna(row.get(col, pd.NaT)):
            return True
    return False


def estado_recepcion_alerta(row: pd.Series) -> str:
    return "Recepcionado" if tiene_recepcion_registrada_alerta(row) else "Sin recepción"


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
    estados_recepcion = []
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
        estados_recepcion.append(estado_recepcion_alerta(row))
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
    salida[COL_ESTADO_RECEPCION_ALERTA] = estados_recepcion
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
    criterio = str(formato_valor(row.get("criterio_alerta", np.nan)))
    if len(criterio) > 105:
        criterio = criterio[:102].rstrip() + "..."

    return dedent(
        f"""
        <div class="alert-box {clase_alerta(row.get('nivel_alerta', 'Sin datos'))}">
            <div class="alert-title">{escape(titulo)} {pill_alerta(row.get('nivel_alerta', 'Sin datos'))}</div>
            <div class="alert-grid">
                <div><div class="alert-label">Estado global</div><div class="alert-value">{escape(formato_valor(row.get('estado_global', np.nan)))}</div></div>
                <div><div class="alert-label">Etapa actual</div><div class="alert-value">{escape(formato_valor(row.get('etapa_actual', np.nan)))}</div></div>
                <div><div class="alert-label">Criterio</div><div class="alert-value">{escape(criterio)}</div></div>
                <div><div class="alert-label">Restante TAT</div><div class="alert-value">{escape(texto_dias_restantes(row.get('dias_restantes_tat', np.nan)))}</div></div>
                <div><div class="alert-label">Centro</div><div class="alert-value">{escape(formato_valor(row.get(COL_CENTRO, np.nan)))}</div></div>
                <div><div class="alert-label">Grupo compras</div><div class="alert-value">{escape(formato_valor(row.get(COL_GRUPO_COMPRAS, np.nan)))}</div></div>
                <div><div class="alert-label">Material</div><div class="alert-value">{escape(formato_valor(row.get(COL_MATERIAL, np.nan)))}</div></div>
                <div><div class="alert-label">Descripción</div><div class="alert-value">{escape(str(row.get(COL_TEXTO, '-'))[:58])}</div></div>
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




def construir_label_registro_critico(row: pd.Series) -> str:
    solped = formato_id(row.get(COL_SOLPED, np.nan))
    oc = formato_id(row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan)))
    pos = formato_id(row.get(COL_POS_SOLPED, np.nan))
    nivel = formato_valor(row.get("nivel_alerta", np.nan))
    vencimiento = formato_valor(row.get("dias_hasta_vencimiento", np.nan))
    tiempo = formato_valor(row.get("tiempo_transcurrido_tat", np.nan))
    pendiente = formato_valor(row.get("fecha_pendiente", np.nan))
    accion = formato_valor(row.get("accion_sugerida", np.nan))
    descripcion = str(row.get(COL_TEXTO, ""))[:70]

    return (
        f"{nivel} · {vencimiento} | "
        f"SolPed {solped} | OC {oc} | Pos {pos} | "
        f"Transcurrido {tiempo} | Pendiente {pendiente} | "
        f"{accion} | {descripcion}"
    )


def columnas_gestion_expediente(df_base: pd.DataFrame) -> list[str]:
    return columnas_existentes(
        df_base,
        [
            "nivel_alerta",
            "dias_hasta_vencimiento",
            "score_riesgo",
            "tiempo_transcurrido_tat",
            "dias_restantes_texto",
            "fecha_vencimiento_texto",
            "fecha_pendiente",
            "accion_sugerida",
            "causa_probable",
            "etapa_actual",
            COL_ESTADO_RECEPCION_ALERTA,
            COL_SOLPED,
            COL_OC_ME5A,
            COL_OC_NME,
            COL_POS_SOLPED,
            COL_MATERIAL,
            COL_TEXTO,
            COL_CENTRO,
            COL_GRUPO_COMPRAS,
            COL_TIPO_OC,
            COL_MONTO,
        ],
    )


def tabla_gestion_expediente(df_base: pd.DataFrame) -> pd.DataFrame:
    columnas = columnas_gestion_expediente(df_base)
    tabla = df_base[columnas].copy() if columnas else pd.DataFrame(index=df_base.index)
    renombres = {
        "nivel_alerta": "Nivel alerta",
        "dias_hasta_vencimiento": "Urgencia",
        "score_riesgo": "Score riesgo",
        "tiempo_transcurrido_tat": "Tiempo transcurrido",
        "dias_restantes_texto": "Días restantes",
        "fecha_vencimiento_texto": "Fecha vencimiento",
        "fecha_pendiente": "Fecha pendiente",
        "accion_sugerida": "Acción sugerida",
        "causa_probable": "Causa probable",
        "etapa_actual": "Etapa actual",
        COL_ESTADO_RECEPCION_ALERTA: "Recepción",
        COL_SOLPED: "SolPed",
        COL_OC_ME5A: "Pedido ME5A",
        COL_OC_NME: "Pedido NME80FN",
        COL_POS_SOLPED: "Posición SolPed",
        COL_MATERIAL: "Material",
        COL_TEXTO: "Descripción",
        COL_CENTRO: "Centro",
        COL_GRUPO_COMPRAS: "Grupo compras",
        COL_TIPO_OC: "Tipo OC",
        COL_MONTO: "Monto",
    }
    return tabla.rename(columns=renombres)


def aplicar_estilo_gestion_expediente(df_tabla: pd.DataFrame):
    styler = df_tabla.style

    def color_nivel(valor):
        texto = str(valor).strip()
        if texto == "Crítica":
            return "background-color:#fee2e2; color:#991b1b; font-weight:900;"
        if texto == "Alta":
            return "background-color:#ffedd5; color:#9a3412; font-weight:900;"
        if texto == "Media":
            return "background-color:#fef9c3; color:#854d0e; font-weight:850;"
        if texto == "Normal":
            return "background-color:#dcfce7; color:#166534; font-weight:850;"
        if texto == "Sin datos":
            return "background-color:#f1f5f9; color:#475569; font-weight:850;"
        return ""

    def color_urgencia(valor):
        texto = str(valor).strip()
        if texto == "Vencido":
            return "background-color:#fee2e2; color:#991b1b; font-weight:900;"
        if texto in ["1 día", "2 días"]:
            return "background-color:#ffedd5; color:#9a3412; font-weight:900;"
        if texto == "7 días":
            return "background-color:#fef3c7; color:#92400e; font-weight:900;"
        if texto == "+7 días":
            return "background-color:#dcfce7; color:#166534; font-weight:850;"
        if texto == "Sin datos":
            return "background-color:#f1f5f9; color:#475569; font-weight:850;"
        return ""

    for col in ["Nivel alerta"]:
        if col in df_tabla.columns:
            styler = styler.map(color_nivel, subset=[col])
    for col in ["Urgencia"]:
        if col in df_tabla.columns:
            styler = styler.map(color_urgencia, subset=[col])
    return styler


def html_pedido_critico_seleccionado(row: pd.Series) -> str:
    return dedent(
        f"""
        <div class="critical-selected-card">
            <div class="critical-selected-title">Pedido crítico seleccionado para expediente</div>
            <div class="critical-selected-grid">
                <div class="critical-selected-field">
                    <div class="critical-selected-label">Nivel / urgencia</div>
                    <div class="critical-selected-value">{html_texto(row.get('nivel_alerta', np.nan))} · {html_texto(row.get('dias_hasta_vencimiento', np.nan))}</div>
                </div>
                <div class="critical-selected-field">
                    <div class="critical-selected-label">Tiempo transcurrido</div>
                    <div class="critical-selected-value">{html_texto(row.get('tiempo_transcurrido_tat', np.nan))}</div>
                </div>
                <div class="critical-selected-field">
                    <div class="critical-selected-label">Fecha pendiente</div>
                    <div class="critical-selected-value">{html_texto(row.get('fecha_pendiente', np.nan))}</div>
                </div>
                <div class="critical-selected-field">
                    <div class="critical-selected-label">Acción sugerida</div>
                    <div class="critical-selected-value">{html_texto(row.get('accion_sugerida', np.nan))}</div>
                </div>
                <div class="critical-selected-field">
                    <div class="critical-selected-label">Score riesgo</div>
                    <div class="critical-selected-value">{html_texto(row.get('score_riesgo', np.nan))}</div>
                </div>
            </div>
        </div>
        """
    ).strip()


def ordenar_expediente_critico(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty:
        return df_base.copy()

    salida = df_base.copy()
    if "prioridad_operativa" not in salida.columns:
        salida["prioridad_operativa"] = salida.apply(prioridad_operativa, axis=1)

    columnas_orden = ["prioridad_operativa"]
    ascendentes = [True]
    for col in ["score_riesgo", "brecha_tat", "tiempo_transcurrido_tat_dias"]:
        if col in salida.columns:
            columnas_orden.append(col)
            ascendentes.append(False)

    return salida.sort_values(columnas_orden, ascending=ascendentes)

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
# Funciones UX operativas
# =========================================================
BUCKETS_DIAS_VENCIMIENTO = [
    "Vencido",
    "1 día",
    "2 días",
    "7 días",
    "+7 días",
    "Sin datos",
]


def etapa_label_desde_columna_fecha(columna: str) -> str:
    mapa = {
        "fecha_solicitud_final": "Solicitud",
        "fecha_liberacion_final": "Liberación",
        "fecha_pedido_final": "Pedido",
        "fecha_facturacion_final": "Facturación",
        "fecha_recepcion_final": "Recepción",
    }
    return mapa.get(str(columna), str(columna).replace("fecha_", "").replace("_final", "").replace("_", " ").title())


def obtener_estado_fechas_operativo(row: pd.Series) -> dict[str, Any]:
    """Devuelve la última fecha real registrada y la próxima fecha pendiente.

    Esto hace explícito un caso común: el pedido puede tener solo fecha de solicitud
    y, por lo tanto, no está "sin datos"; está pendiente de liberación.
    """
    ultima_etapa = "Sin fecha registrada"
    ultima_fecha = pd.NaT
    pendiente = "Cerrado"

    for nombre, columna in ETAPAS_LINEA_PEDIDO:
        valor = row.get(columna, pd.NaT)
        fecha = pd.to_datetime(valor, errors="coerce") if pd.notna(valor) else pd.NaT

        if pd.notna(fecha):
            ultima_etapa = nombre
            ultima_fecha = fecha
        elif pendiente == "Cerrado":
            pendiente = nombre

    return {
        "ultima_etapa_registrada": ultima_etapa,
        "ultima_fecha_registrada_dt": ultima_fecha,
        "ultima_fecha_registrada": fecha_etapa_texto(pd.Series({"fecha": ultima_fecha}), "fecha") if pd.notna(ultima_fecha) else "Sin fecha",
        "fecha_pendiente": pendiente,
    }


def clasificar_dias_hasta_vencimiento(row: pd.Series) -> str:
    dias = valor_numerico(row.get("dias_restantes_tat", np.nan))

    if pd.isna(dias):
        return "Sin datos"
    if dias < 0:
        return "Vencido"
    if dias <= 1:
        return "1 día"
    if dias <= 2:
        return "2 días"
    if dias <= 7:
        return "7 días"
    return "+7 días"


def causa_probable(row: pd.Series) -> str:
    if bool(row.get(COL_FECHAS_INCONSISTENTES, False)) if COL_FECHAS_INCONSISTENTES in row.index else False:
        return "Fechas inconsistentes"

    etapa = str(row.get("etapa_actual", "")).strip()
    fecha_pendiente = str(row.get("fecha_pendiente", "")).strip()
    umbral = obtener_umbral_tat(row)

    if etapa == "Recepcionado" or fecha_pendiente == "Cerrado":
        return "Pedido cerrado"

    # Si existe al menos una fecha registrada, el problema no es necesariamente "sin datos".
    # Se explicita qué hito falta primero.
    if fecha_pendiente and fecha_pendiente != "Cerrado":
        mapa_pendiente = {
            "Liberación": "Falta fecha de liberación de SolPed",
            "Pedido": "Falta fecha de pedido / emisión de OC",
            "Facturación": "Falta fecha de facturación",
            "Recepción": "Falta fecha de recepción en sistema",
        }
        causa = mapa_pendiente.get(fecha_pendiente, f"Falta fecha de {fecha_pendiente.lower()}")
        if pd.isna(umbral):
            causa += " · además falta umbral TAT o tipo OC válido"
        return causa

    if pd.isna(umbral):
        return "Falta umbral TAT o tipo OC válido"

    mapa_etapa = {
        "Liberación SolPed": "Falta liberación de SolPed",
        "Comprador": "Falta creación o emisión de OC",
        "Proveedor": "Falta gestión de proveedor / facturación",
        "Logística": "Falta recepción en sistema",
    }
    return mapa_etapa.get(etapa, "Revisar datos del pedido")


def accion_sugerida(row: pd.Series) -> str:
    dias_bucket = str(row.get("dias_hasta_vencimiento", "")).strip()
    etapa = str(row.get("etapa_actual", "")).strip()
    fecha_pendiente = str(row.get("fecha_pendiente", "")).strip()

    if etapa == "Recepcionado" or fecha_pendiente == "Cerrado":
        return "Sin acción: pedido cerrado"

    if fecha_pendiente == "Liberación" or etapa == "Liberación SolPed":
        return "Escalar liberación de SolPed"
    if fecha_pendiente == "Pedido" or etapa == "Comprador":
        return "Escalar creación o emisión de OC"
    if fecha_pendiente == "Facturación" or etapa == "Proveedor":
        return "Contactar proveedor y confirmar fecha"
    if fecha_pendiente == "Recepción" or etapa == "Logística":
        return "Validar recepción con logística/bodega"

    if dias_bucket == "Sin datos":
        return "Corregir datos para calcular vencimiento"
    if dias_bucket in ["Vencido", "1 día"]:
        return "Gestionar hoy"
    if dias_bucket in ["2 días", "7 días"]:
        return "Programar seguimiento"
    return "Sin acción urgente"


def prioridad_operativa(row: pd.Series) -> int:
    dias_bucket = str(row.get("dias_hasta_vencimiento", ""))
    nivel = str(row.get("nivel_alerta", ""))
    mapa_dias = {
        "Vencido": 1,
        "1 día": 2,
        "2 días": 3,
        "7 días": 4,
        "+7 días": 5,
        "Sin datos": 6,
    }
    mapa_nivel = {
        "Crítica": 1,
        "Alta": 2,
        "Media": 3,
        "Normal": 4,
        "Sin datos": 6,
    }
    return min(mapa_dias.get(dias_bucket, 9), mapa_nivel.get(nivel, 9))


def preparar_alertas_operativas(df_alertas_base: pd.DataFrame) -> pd.DataFrame:
    salida = df_alertas_base.copy()

    estados_fecha = salida.apply(obtener_estado_fechas_operativo, axis=1, result_type="expand")
    for col in estados_fecha.columns:
        salida[col] = estados_fecha[col]

    salida["dias_hasta_vencimiento"] = salida.apply(clasificar_dias_hasta_vencimiento, axis=1)
    # Alias técnico temporal para compatibilidad si alguna parte antigua lo usa.
    salida["horizonte_accion"] = salida["dias_hasta_vencimiento"]
    salida["causa_probable"] = salida.apply(causa_probable, axis=1)
    salida["accion_sugerida"] = salida.apply(accion_sugerida, axis=1)
    salida["prioridad_operativa"] = salida.apply(prioridad_operativa, axis=1)
    salida = salida.sort_values(
        ["prioridad_operativa", "score_riesgo", "brecha_tat"],
        ascending=[True, False, False],
    )
    return salida


def columnas_existentes(df_base: pd.DataFrame, columnas: list[str]) -> list[str]:
    return [col for col in columnas if col in df_base.columns]


def formato_numero_corto(valor: Any, decimales: int = 0) -> str:
    numero = valor_numerico(valor)
    if pd.isna(numero):
        return "-"
    if decimales == 0:
        return f"{int(round(numero)):,}".replace(",", ".")
    return f"{numero:,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formato_tiempo_transcurrido(dias: Any) -> str:
    """Muestra días, meses o años según magnitud.

    Reglas solicitadas:
    - Hasta 30 días: días.
    - Sobre 30 días: meses aproximados.
    - Sobre 12 meses: años aproximados.
    """
    valor = valor_numerico(dias)
    if pd.isna(valor):
        return "Sin dato"

    signo = "-" if valor < 0 else ""
    abs_dias = abs(float(valor))

    if abs_dias <= 30:
        return f"{signo}{int(round(abs_dias)):,} días".replace(",", ".")

    meses = abs_dias / 30.44
    if meses <= 12:
        return (
            f"{signo}{meses:,.1f} meses"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

    anos = meses / 12
    return (
        f"{signo}{anos:,.1f} años"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def formato_dias_restantes_operativo(dias: Any) -> str:
    valor = valor_numerico(dias)
    if pd.isna(valor):
        return "Sin dato"
    if valor < 0:
        return f"Vencido hace {formato_tiempo_transcurrido(abs(valor))}"
    if valor == 0:
        return "Vence hoy"
    return f"Vence en {formato_tiempo_transcurrido(valor)}"


def resumen_caso_para_copiar(row: pd.Series) -> str:
    oc = row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan))
    dias_restantes = valor_numerico(row.get("dias_restantes_tat", np.nan))

    if pd.notna(dias_restantes) and dias_restantes < 0:
        estado_tiempo = f"Vencido por {abs(int(round(dias_restantes)))} días"
    elif pd.notna(dias_restantes):
        estado_tiempo = f"Quedan {int(round(dias_restantes))} días para el umbral"
    else:
        estado_tiempo = "Sin datos suficientes para calcular días restantes"

    return dedent(
        f"""
        Caso TAT
        SolPed: {formato_id(row.get(COL_SOLPED, np.nan))}
        OC/Pedido: {formato_id(oc)}
        Posición SolPed: {formato_id(row.get(COL_POS_SOLPED, np.nan))}
        Centro: {formato_valor(row.get(COL_CENTRO, np.nan))}
        Grupo compras: {formato_valor(row.get(COL_GRUPO_COMPRAS, np.nan))}
        Material: {formato_id(row.get(COL_MATERIAL, np.nan))}
        Descripción: {formato_valor(row.get(COL_TEXTO, np.nan))}
        Nivel alerta: {formato_valor(row.get('nivel_alerta', np.nan))}
        Días hasta vencimiento: {formato_valor(row.get('dias_hasta_vencimiento', np.nan))}
        Estado tiempo: {estado_tiempo}
        Última fecha registrada: {formato_valor(row.get('ultima_etapa_registrada', np.nan))} · {formato_valor(row.get('ultima_fecha_registrada', np.nan))}
        Fecha pendiente: {formato_valor(row.get('fecha_pendiente', np.nan))}
        Etapa actual: {formato_valor(row.get('etapa_actual', np.nan))}
        Causa probable: {formato_valor(row.get('causa_probable', np.nan))}
        Acción sugerida: {formato_valor(row.get('accion_sugerida', np.nan))}
        """
    ).strip()


def dataframe_operativo(df_base: pd.DataFrame) -> pd.DataFrame:
    columnas = columnas_existentes(
        df_base,
        [
            "dias_hasta_vencimiento",
            "nivel_alerta",
            "accion_sugerida",
            "causa_probable",
            "ultima_etapa_registrada",
            "ultima_fecha_registrada",
            "fecha_pendiente",
            "etapa_actual",
            "dias_restantes_tat",
            "brecha_tat",
            COL_ESTADO_RECEPCION_ALERTA,
            COL_SOLPED,
            COL_OC_ME5A,
            COL_OC_NME,
            COL_POS_SOLPED,
            COL_MATERIAL,
            COL_TEXTO,
            COL_CENTRO,
            COL_GRUPO_COMPRAS,
            COL_TIPO_OC,
            COL_MONTO,
        ],
    )
    tabla = df_base[columnas].copy()
    renombres = {
        "dias_hasta_vencimiento": "Días hasta vencimiento",
        "nivel_alerta": "Nivel alerta",
        "accion_sugerida": "Acción sugerida",
        "causa_probable": "Causa probable",
        "ultima_etapa_registrada": "Última etapa registrada",
        "ultima_fecha_registrada": "Última fecha registrada",
        "fecha_pendiente": "Fecha pendiente",
        "etapa_actual": "Etapa actual",
        "dias_restantes_tat": "Días restantes TAT",
        "brecha_tat": "Brecha TAT",
        COL_ESTADO_RECEPCION_ALERTA: "Recepción",
    }
    return tabla.rename(columns=renombres)


def aplicar_estilo_operativo(df_tabla: pd.DataFrame):
    styler = aplicar_estilo_alertas(df_tabla)

    def color_dias(valor):
        texto = str(valor).strip()
        if texto == "Vencido":
            return "background-color:#fee2e2; color:#991b1b; font-weight:900;"
        if texto == "1 día":
            return "background-color:#ffedd5; color:#9a3412; font-weight:900;"
        if texto == "2 días":
            return "background-color:#fef3c7; color:#92400e; font-weight:900;"
        if texto == "7 días":
            return "background-color:#dbeafe; color:#1e40af; font-weight:900;"
        if texto == "Sin datos":
            return "background-color:#f1f5f9; color:#475569; font-weight:900;"
        return ""

    for col in ["dias_hasta_vencimiento", "Días hasta vencimiento"]:
        if col in df_tabla.columns:
            styler = styler.map(color_dias, subset=[col])
    return styler


def mostrar_metricas_accion(df_base: pd.DataFrame):
    total = len(df_base)
    serie = df_base.get("dias_hasta_vencimiento", pd.Series(dtype=str)).astype(str)
    vencidos = int(serie.eq("Vencido").sum())
    un_dia = int(serie.eq("1 día").sum())
    dos_dias = int(serie.eq("2 días").sum())
    semana = int(serie.eq("7 días").sum())
    mas_7 = int(serie.eq("+7 días").sum())
    sin_datos = int(serie.eq("Sin datos").sum())

    k1, k2, k3, k4, k5, k6, k7 = st.columns(7)
    k1.metric("Filtrados", f"{total:,}".replace(",", "."))
    k2.metric("Vencidos", f"{vencidos:,}".replace(",", "."))
    k3.metric("1 día", f"{un_dia:,}".replace(",", "."))
    k4.metric("2 días", f"{dos_dias:,}".replace(",", "."))
    k5.metric("7 días", f"{semana:,}".replace(",", "."))
    k6.metric("+7 días", f"{mas_7:,}".replace(",", "."))
    k7.metric("Sin datos", f"{sin_datos:,}".replace(",", "."))


def mostrar_pareto_dias_vencimiento(df_base: pd.DataFrame):
    st.markdown("#### Pareto de días hasta vencimiento")

    if df_base.empty or "dias_hasta_vencimiento" not in df_base.columns:
        st.info("No hay datos para construir el Pareto.")
        return

    conteo = (
        df_base["dias_hasta_vencimiento"]
        .astype(str)
        .value_counts()
        .reindex(BUCKETS_DIAS_VENCIMIENTO, fill_value=0)
    )
    conteo = conteo[conteo > 0]

    if conteo.empty:
        st.info("No hay datos para construir el Pareto.")
        return

    pareto = conteo.sort_values(ascending=False).reset_index()
    pareto.columns = ["Días hasta vencimiento", "Pedidos"]
    pareto["% acumulado"] = pareto["Pedidos"].cumsum() / pareto["Pedidos"].sum() * 100

    try:
        import matplotlib.pyplot as plt

        fig, ax1 = plt.subplots(figsize=(8.5, 3.5))
        ax1.bar(pareto["Días hasta vencimiento"], pareto["Pedidos"])
        ax1.set_ylabel("Pedidos")
        ax1.set_xlabel("Días hasta vencimiento")
        ax1.tick_params(axis="x", rotation=25)

        ax2 = ax1.twinx()
        ax2.plot(pareto["Días hasta vencimiento"], pareto["% acumulado"], marker="o")
        ax2.set_ylabel("% acumulado")
        ax2.set_ylim(0, 105)

        fig.tight_layout()
        st.pyplot(fig, clear_figure=True)
    except Exception:
        st.bar_chart(pareto.set_index("Días hasta vencimiento")["Pedidos"])

    st.dataframe(pareto, use_container_width=True, hide_index=True)


def crear_excel_multivista(df_base: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        dataframe_operativo(df_base).to_excel(writer, index=False, sheet_name="Lista trabajo")
        df_base[df_base["dias_hasta_vencimiento"].eq("Vencido")].to_excel(writer, index=False, sheet_name="Vencidos")
        df_base[df_base["dias_hasta_vencimiento"].isin(["1 día", "2 días", "7 días"])].to_excel(writer, index=False, sheet_name="Proximos 7 dias")
        df_base[df_base["dias_hasta_vencimiento"].eq("+7 días")].to_excel(writer, index=False, sheet_name="Mas de 7 dias")
        df_base[df_base["dias_hasta_vencimiento"].eq("Sin datos")].to_excel(writer, index=False, sheet_name="Sin datos")
    return output.getvalue()



# =========================================================
# Interfaz optimizada: una sola pestaña
# =========================================================
mostrar_logo()

st.markdown(
    """
    <div style="text-align:center; margin-bottom: 18px;">
        <div style="font-size:36px; font-weight:850; color:#111827; line-height:1.12;">
            Control TAT · SolPed / OC
        </div>
        <div style="font-size:14px; color:#6B7280; margin-top:8px;">
            Panel único optimizado: filtros, vencidos, próximos a vencer, expediente y estadística por material
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Preparación rápida y cacheada
# =========================================================
def _primera_columna_existente(df_base: pd.DataFrame, candidatas: list[str]) -> pd.Series:
    for col in candidatas:
        if col in df_base.columns:
            return df_base[col]
    return pd.Series(pd.NaT, index=df_base.index)


def _serie_texto(df_base: pd.DataFrame, col: str) -> pd.Series:
    if col in df_base.columns:
        return df_base[col].astype(str)
    return pd.Series("", index=df_base.index, dtype="object")


def _formatear_fecha_serie(serie: pd.Series) -> pd.Series:
    fechas = pd.to_datetime(serie, errors="coerce")
    salida = fechas.dt.strftime("%d-%m-%Y")
    return salida.fillna("Sin fecha calculable")


def _normalizar_tipo_oc(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.replace(".0", "", regex=False)


@st.cache_data(show_spinner="Preparando datos TAT una sola vez...")
def preparar_panel_tat_rapido(df_original: pd.DataFrame, hoy: pd.Timestamp) -> pd.DataFrame:
    """Prepara las columnas usadas por el panel sin recalcularlas en cada filtro.

    La idea es preparar una vez y filtrar después con máscaras vectorizadas.
    Evita construir alertas con iterrows para que la interacción sea más rápida.
    """
    df_base = limpiar_columnas(df_original.copy())
    df_base = convertir_fechas_visuales(df_base)

    # Recepción.
    fecha_recepcion = _primera_columna_existente(
        df_base,
        ["fecha_recepcion_final", "Fecha recepción mercancía - NME80FN"],
    )
    fecha_recepcion_dt = pd.to_datetime(fecha_recepcion, errors="coerce")
    df_base[COL_ESTADO_RECEPCION_ALERTA] = np.where(
        fecha_recepcion_dt.notna(),
        "Recepcionado",
        "Sin recepción",
    )

    # Fecha de inicio y umbral TAT.
    fecha_inicio = _primera_columna_existente(
        df_base,
        ["fecha_solicitud_final", "Fecha de solicitud - ME5A"],
    )
    df_base["fecha_inicio_tat"] = pd.to_datetime(fecha_inicio, errors="coerce")

    if COL_UMBRAL_TAT in df_base.columns:
        umbral = pd.to_numeric(df_base[COL_UMBRAL_TAT], errors="coerce")
    else:
        umbral = pd.Series(np.nan, index=df_base.index, dtype="float64")

    tipo_oc = _normalizar_tipo_oc(_serie_texto(df_base, COL_TIPO_OC))
    umbral = umbral.copy()
    umbral = umbral.mask(umbral.isna() & tipo_oc.isin(["35", "45"]), 40)
    umbral = umbral.mask(umbral.isna() & tipo_oc.eq("47"), 70)
    df_base["umbral_tat_calculado"] = umbral

    # Fecha de vencimiento TAT.
    # Regla principal: fecha de solicitud + umbral TAT total.
    # Regla paralela confirmada por negocio: si no existe fecha de solicitud,
    # pero sí existe fecha_pedido_final, usar fecha_pedido_final + umbral TAT total.
    # Para otras fechas intermedias no se aplica esta lógica.
    fecha_pedido_base = _primera_columna_existente(
        df_base,
        ["fecha_pedido_final", "Fecha de pedido - ME5A"],
    )
    df_base["fecha_pedido_base_vencimiento"] = pd.to_datetime(fecha_pedido_base, errors="coerce")

    fecha_vencimiento_solicitud = (
        df_base["fecha_inicio_tat"] + pd.to_timedelta(df_base["umbral_tat_calculado"], unit="D")
    )
    fecha_vencimiento_pedido = (
        df_base["fecha_pedido_base_vencimiento"] + pd.to_timedelta(df_base["umbral_tat_calculado"], unit="D")
    )

    usar_vencimiento_desde_pedido = fecha_vencimiento_solicitud.isna() & fecha_vencimiento_pedido.notna()
    df_base["fecha_vencimiento_tat"] = fecha_vencimiento_solicitud.where(
        ~usar_vencimiento_desde_pedido,
        fecha_vencimiento_pedido,
    )
    condiciones_fuente_vencimiento = [
        fecha_vencimiento_solicitud.notna().fillna(False).to_numpy(dtype=bool),
        usar_vencimiento_desde_pedido.fillna(False).to_numpy(dtype=bool),
    ]
    df_base["fuente_calculo_vencimiento"] = np.select(
        condiciones_fuente_vencimiento,
        [
            "Calculado desde fecha de solicitud",
            "Estimado desde fecha de pedido",
        ],
        default="Sin fecha calculable",
    )
    df_base["fecha_vencimiento_texto"] = _formatear_fecha_serie(df_base["fecha_vencimiento_tat"])
    df_base["dias_restantes_int"] = (
        df_base["fecha_vencimiento_tat"] - hoy
    ).dt.days.astype("Int64")
    df_base["dias_restantes_texto"] = df_base["dias_restantes_int"].apply(formato_dias_restantes_operativo)

    fecha_fin_referencia = fecha_recepcion_dt.where(fecha_recepcion_dt.notna(), hoy)
    df_base["tiempo_transcurrido_tat_dias"] = (
        fecha_fin_referencia - df_base["fecha_inicio_tat"]
    ).dt.days.astype("Int64")
    df_base["tiempo_transcurrido_tat"] = df_base["tiempo_transcurrido_tat_dias"].apply(formato_tiempo_transcurrido)

    exceso_umbral = (
        df_base["tiempo_transcurrido_tat_dias"].astype("float64")
        - df_base["umbral_tat_calculado"].astype("float64")
    )
    exceso_umbral = exceso_umbral.where(exceso_umbral.gt(0), 0)
    df_base["tiempo_excedido_umbral_dias"] = exceso_umbral
    df_base["tiempo_excedido_umbral_texto"] = exceso_umbral.apply(
        lambda x: "Dentro del umbral" if pd.notna(x) and float(x) <= 0 else formato_tiempo_transcurrido(x)
    )

    dias = df_base["dias_restantes_int"].astype("float64")
    condiciones = [
        dias.lt(0).fillna(False).to_numpy(dtype=bool),
        dias.eq(0).fillna(False).to_numpy(dtype=bool),
        dias.eq(1).fillna(False).to_numpy(dtype=bool),
        dias.eq(2).fillna(False).to_numpy(dtype=bool),
        dias.eq(3).fillna(False).to_numpy(dtype=bool),
        dias.eq(4).fillna(False).to_numpy(dtype=bool),
        dias.eq(5).fillna(False).to_numpy(dtype=bool),
        dias.eq(6).fillna(False).to_numpy(dtype=bool),
        dias.eq(7).fillna(False).to_numpy(dtype=bool),
        dias.between(8, 30, inclusive="both").fillna(False).to_numpy(dtype=bool),
        dias.gt(30).fillna(False).to_numpy(dtype=bool),
    ]
    etiquetas = [
        "Vencido",
        "Vence hoy",
        "1 día",
        "2 días",
        "3 días",
        "4 días",
        "5 días",
        "6 días",
        "7 días",
        "7 a 30 días",
        "Más de 1 mes",
    ]
    df_base["clasificacion_vencimiento"] = np.select(condiciones, etiquetas, default="Sin datos")

    # Última etapa registrada y próxima fecha pendiente.
    etapas = [
        ("Solicitud", "fecha_solicitud_final"),
        ("Liberación", "fecha_liberacion_final"),
        ("Pedido", "fecha_pedido_final"),
        ("Facturación", "fecha_facturacion_final"),
        ("Recepción", "fecha_recepcion_final"),
    ]

    ultima_etapa = pd.Series("Sin fecha registrada", index=df_base.index, dtype="object")
    ultima_fecha = pd.Series(pd.NaT, index=df_base.index, dtype="datetime64[ns]")
    fecha_pendiente = pd.Series("Cerrado", index=df_base.index, dtype="object")

    faltante_asignado = pd.Series(False, index=df_base.index)
    for nombre, col in etapas:
        if col in df_base.columns:
            fecha_col = pd.to_datetime(df_base[col], errors="coerce")
        else:
            fecha_col = pd.Series(pd.NaT, index=df_base.index, dtype="datetime64[ns]")

        tiene_fecha = fecha_col.notna()
        ultima_etapa = ultima_etapa.mask(tiene_fecha, nombre)
        ultima_fecha = ultima_fecha.mask(tiene_fecha, fecha_col)

        falta = fecha_col.isna() & ~faltante_asignado
        fecha_pendiente = fecha_pendiente.mask(falta, nombre)
        faltante_asignado = faltante_asignado | falta

    df_base["ultima_etapa_registrada"] = ultima_etapa
    df_base["ultima_fecha_registrada_dt"] = ultima_fecha
    df_base["ultima_fecha_registrada"] = _formatear_fecha_serie(ultima_fecha)
    df_base["fecha_pendiente"] = fecha_pendiente

    # Campos de ayuda para tablas, sin responsable sugerido.
    df_base["esta_vencido"] = dias.lt(0).fillna(False)
    df_base["tiene_fecha_vencimiento"] = dias.notna()

    # Mantener compatibilidad con funciones del expediente.
    if "dias_restantes_tat" not in df_base.columns:
        df_base["dias_restantes_tat"] = df_base["dias_restantes_int"]
    if "brecha_tat" not in df_base.columns:
        df_base["brecha_tat"] = -df_base["dias_restantes_int"].astype("float64")
    if "etapa_actual" not in df_base.columns:
        df_base["etapa_actual"] = df_base["fecha_pendiente"].replace({
            "Solicitud": "Solicitud",
            "Liberación": "Liberación SolPed",
            "Pedido": "Comprador",
            "Facturación": "Proveedor",
            "Recepción": "Logística",
            "Cerrado": "Recepcionado",
        })

    # Orden operativo estable.
    orden = {
        "Vencido": 1,
        "Vence hoy": 2,
        "1 día": 3,
        "2 días": 4,
        "3 días": 5,
        "4 días": 6,
        "5 días": 7,
        "6 días": 8,
        "7 días": 9,
        "7 a 30 días": 10,
        "Más de 1 mes": 11,
        "Sin datos": 12,
    }
    df_base["_orden_vencimiento"] = df_base["clasificacion_vencimiento"].map(orden).fillna(99)
    df_base = df_base.sort_values(["_orden_vencimiento", "dias_restantes_int"], ascending=[True, True])
    return df_base.drop(columns=["_orden_vencimiento"])


@st.cache_data(show_spinner=False)
def opciones_filtros_rapidas(df_base: pd.DataFrame) -> dict[str, list[str]]:
    columnas = [
        COL_CENTRO,
        COL_GRUPO_COMPRAS,
        COL_TIPO_OC,
        COL_ORIGEN,
        COL_SISTEMA,
        "clasificacion_vencimiento",
        "ultima_etapa_registrada",
        "fecha_pendiente",
        COL_ESTADO_RECEPCION_ALERTA,
    ]
    return {col: opciones_columna(df_base, col) for col in columnas if col in df_base.columns}


def fecha_texto(valor: Any) -> str:
    fecha = pd.to_datetime(valor, errors="coerce")
    if pd.isna(fecha):
        return "Sin fecha calculable"
    return fecha.strftime("%d-%m-%Y")


def lista_valores_corta(valores: Any, max_items: int = 4) -> str:
    if valores is None:
        return "Todos"
    if isinstance(valores, str):
        valores = [valores]
    valores = [str(v) for v in valores if str(v).strip()]
    if not valores:
        return "Todos"
    if len(valores) <= max_items:
        return ", ".join(valores)
    return ", ".join(valores[:max_items]) + f" +{len(valores) - max_items} más"


def rango_fechas_texto(df_base: pd.DataFrame) -> str:
    if df_base.empty or "fecha_vencimiento_tat" not in df_base.columns:
        return "Sin casos"
    fechas = pd.to_datetime(df_base["fecha_vencimiento_tat"], errors="coerce").dropna()
    if fechas.empty:
        return "Sin casos"
    fecha_min = fecha_texto(fechas.min())
    fecha_max = fecha_texto(fechas.max())
    return fecha_min if fecha_min == fecha_max else f"{fecha_min} a {fecha_max}"


def aplicar_filtros_panel(
    df_base: pd.DataFrame,
    centro_sel: list[str],
    recepcion_sel: str,
    vencimiento_sel: list[str],
    grupo_sel: list[str],
    tipo_oc_sel: list[str],
    ultima_fecha_sel: list[str],
    fecha_pendiente_sel: list[str],
    solped_txt: str,
    oc_txt: str,
    texto_txt: str,
) -> pd.DataFrame:
    mask = pd.Series(True, index=df_base.index)

    if centro_sel and COL_CENTRO in df_base.columns:
        mask &= df_base[COL_CENTRO].astype(str).isin([str(v) for v in centro_sel])
    if recepcion_sel != "Todos" and COL_ESTADO_RECEPCION_ALERTA in df_base.columns:
        mask &= df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str).eq(recepcion_sel)
    if vencimiento_sel and "clasificacion_vencimiento" in df_base.columns:
        mask &= df_base["clasificacion_vencimiento"].astype(str).isin([str(v) for v in vencimiento_sel])
    if grupo_sel and COL_GRUPO_COMPRAS in df_base.columns:
        mask &= df_base[COL_GRUPO_COMPRAS].astype(str).isin([str(v) for v in grupo_sel])
    if tipo_oc_sel and COL_TIPO_OC in df_base.columns:
        mask &= df_base[COL_TIPO_OC].astype(str).isin([str(v) for v in tipo_oc_sel])
    if ultima_fecha_sel and "ultima_etapa_registrada" in df_base.columns:
        mask &= df_base["ultima_etapa_registrada"].astype(str).isin([str(v) for v in ultima_fecha_sel])
    if fecha_pendiente_sel and "fecha_pendiente" in df_base.columns:
        mask &= df_base["fecha_pendiente"].astype(str).isin([str(v) for v in fecha_pendiente_sel])

    if str(solped_txt).strip():
        mask &= filtrar_por_ids(df_base, COL_SOLPED, solped_txt)
    if str(oc_txt).strip():
        mask &= (
            filtrar_por_ids(df_base, COL_OC_ME5A, oc_txt)
            | filtrar_por_ids(df_base, COL_OC_NME, oc_txt)
        )
    if str(texto_txt).strip():
        texto_mask = pd.Series(False, index=df_base.index)
        for col in [COL_MATERIAL, COL_TEXTO, COL_SOLICITANTE]:
            if col in df_base.columns:
                texto_mask |= contiene_texto(df_base, col, texto_txt)
        mask &= texto_mask

    return df_base.loc[mask].copy()


def construir_conciliacion(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty:
        return pd.DataFrame(columns=["Grupo", "Cantidad", "% del filtrado", "Explicación"])

    recepcion_col = COL_ESTADO_RECEPCION_ALERTA
    estado_recepcion = (
        df_base[recepcion_col].astype(str)
        if recepcion_col in df_base.columns
        else pd.Series("Sin recepción", index=df_base.index)
    )

    recepcionados = estado_recepcion.eq("Recepcionado")
    sin_recepcion = estado_recepcion.eq("Sin recepción")

    dias = pd.to_numeric(
        df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)),
        errors="coerce",
    )

    con_dias = dias.notna()
    vencidos = dias.lt(0)
    proximos = dias.between(0, 30, inclusive="both")
    mas_mes = dias.gt(30)

    filas = [
        {
            "Grupo": "Vencidos y recepcionados",
            "Cantidad": int((vencidos & recepcionados).sum()),
            "Explicación": "Registros con recepción registrada, pero cuya fecha de vencimiento calculada ya quedó atrás.",
        },
        {
            "Grupo": "Vencidos y sin recepcionar",
            "Cantidad": int((vencidos & sin_recepcion).sum()),
            "Explicación": "Registros sin recepción y con fecha de vencimiento ya superada.",
        },
        {
            "Grupo": "Próximos a vencer sin recepción, hoy a 30 días",
            "Cantidad": int((proximos & sin_recepcion).sum()),
            "Explicación": "Registros abiertos que vencen entre hoy y los próximos 30 días.",
        },
        {
            "Grupo": "No vencidos recepcionados",
            "Cantidad": int((~vencidos & con_dias & recepcionados).sum()),
            "Explicación": "Registros cerrados con fecha de vencimiento calculable y no vencida contra la fecha de referencia.",
        },
        {
            "Grupo": "Sin recepción y vencen en más de 1 mes",
            "Cantidad": int((mas_mes & sin_recepcion).sum()),
            "Explicación": "Registros abiertos, pero sin urgencia dentro de los próximos 30 días.",
        },
        {
            "Grupo": "Sin fecha de vencimiento calculable y recepcionados",
            "Cantidad": int((~con_dias & recepcionados).sum()),
            "Explicación": "Tienen recepción, pero falta fecha de solicitud, umbral TAT o tipo OC para calcular vencimiento.",
        },
        {
            "Grupo": "Sin fecha de vencimiento calculable y sin recepción",
            "Cantidad": int((~con_dias & sin_recepcion).sum()),
            "Explicación": "No tienen recepción y falta información para calcular vencimiento.",
        },
    ]

    otros = ~(recepcionados | sin_recepcion)
    if int(otros.sum()) > 0:
        filas.append(
            {
                "Grupo": "Otros estados de recepción",
                "Cantidad": int(otros.sum()),
                "Explicación": "Registros con un estado de recepción distinto a Recepcionado o Sin recepción.",
            }
        )

    salida = pd.DataFrame(filas)
    total = len(df_base)
    salida["% del filtrado"] = np.where(total > 0, salida["Cantidad"] / total * 100, 0)
    salida["% del filtrado"] = salida["% del filtrado"].map(
        lambda x: f"{x:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    )

    total_fila = pd.DataFrame(
        [
            {
                "Grupo": "TOTAL FILTRADO",
                "Cantidad": int(salida["Cantidad"].sum()),
                "% del filtrado": "100,0%" if total > 0 else "0,0%",
                "Explicación": "Suma de todos los grupos de conciliación.",
            }
        ]
    )
    salida = pd.concat([salida, total_fila], ignore_index=True)

    return salida[["Grupo", "Cantidad", "% del filtrado", "Explicación"]]


def aplicar_estilo_conciliacion(df_tabla: pd.DataFrame):
    def estilo_fila(row: pd.Series) -> list[str]:
        grupo = str(row.get("Grupo", "")).strip().lower()
        base = [""] * len(row)

        if grupo == "total filtrado":
            return [
                "background-color:#f1f5f9; color:#0f172a; font-weight:900; border-top:2px solid #94a3b8;"
            ] * len(row)

        if grupo.startswith("vencidos y"):
            return [
                "background-color:#fee2e2; color:#991b1b; font-weight:800;"
            ] * len(row)

        if "próximos a vencer sin recepción" in grupo or "proximos a vencer sin recepcion" in grupo:
            return [
                "background-color:#ffedd5; color:#9a3412; font-weight:800;"
            ] * len(row)

        return base

    return df_tabla.style.apply(estilo_fila, axis=1)



def construir_detalle_filtro_3(df_base: pd.DataFrame) -> pd.DataFrame:
    """Detalle anidado para que el usuario entienda qué selecciona en Filtro 3."""
    if df_base.empty:
        return pd.DataFrame(
            columns=["Grupo", "Selección Filtro 3", "Cantidad", "% de la base"]
        )

    dias = pd.to_numeric(
        df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)),
        errors="coerce",
    )
    total = len(df_base)

    definiciones = [
        ("Urgencia vencida", "Vencido", dias.lt(0)),
        ("Urgencia próxima", "Vence hoy", dias.eq(0)),
        ("Urgencia próxima", "1 día", dias.eq(1)),
        ("Urgencia próxima", "2 días", dias.eq(2)),
        ("Semana actual", "3 días", dias.eq(3)),
        ("Semana actual", "4 días", dias.eq(4)),
        ("Semana actual", "5 días", dias.eq(5)),
        ("Semana actual", "6 días", dias.eq(6)),
        ("Semana actual", "7 días", dias.eq(7)),
        ("Próximos 30 días", "7 a 30 días", dias.between(8, 30, inclusive="both")),
        ("Sin urgencia próxima", "Más de 1 mes", dias.gt(30)),
        ("No calculable", "Sin datos", dias.isna()),
    ]

    filas = []
    for grupo, seleccion, mask in definiciones:
        cantidad = int(mask.sum())
        porcentaje = cantidad / total * 100 if total else 0
        filas.append(
            {
                "Grupo": grupo,
                "Selección Filtro 3": seleccion,
                "Cantidad": cantidad,
                "% de la base": f"{porcentaje:,.1f}%".replace(",", "X").replace(".", ",").replace("X", "."),
            }
        )

    salida = pd.DataFrame(filas)
    salida = salida[salida["Cantidad"].gt(0)].copy()
    if salida.empty:
        return pd.DataFrame(
            columns=["Grupo", "Selección Filtro 3", "Cantidad", "% de la base"]
        )

    total_fila = pd.DataFrame(
        [
            {
                "Grupo": "TOTAL DISPONIBLE",
                "Selección Filtro 3": "Todas las opciones visibles",
                "Cantidad": int(salida["Cantidad"].sum()),
                "% de la base": "100,0%" if total > 0 else "0,0%",
            }
        ]
    )
    salida = pd.concat([salida, total_fila], ignore_index=True)
    return salida


def aplicar_estilo_detalle_filtro_3(df_tabla: pd.DataFrame):
    def estilo_fila(row: pd.Series) -> list[str]:
        grupo = str(row.get("Grupo", "")).strip().lower()
        if grupo == "total disponible":
            return ["background-color:#f1f5f9; color:#0f172a; font-weight:900; border-top:2px solid #94a3b8;"] * len(row)
        if "vencida" in grupo:
            return ["background-color:#fee2e2; color:#991b1b; font-weight:850;"] * len(row)
        if "próxima" in grupo or "proxima" in grupo or "semana" in grupo or "30" in grupo:
            return ["background-color:#ffedd5; color:#9a3412; font-weight:800;"] * len(row)
        if "no calculable" in grupo:
            return ["background-color:#f1f5f9; color:#475569; font-weight:800;"] * len(row)
        return [""] * len(row)

    return df_tabla.style.apply(estilo_fila, axis=1)



# =========================================================
# Panel resumen ejecutivo
# =========================================================
def _porcentaje_texto(valor: float) -> str:
    return f"{valor:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")


def _entero_texto(valor: Any) -> str:
    try:
        return f"{int(valor):,}".replace(",", ".")
    except Exception:
        return "0"


def _top_valor(df_base: pd.DataFrame, columna: str, default: str = "-") -> str:
    if df_base.empty or columna not in df_base.columns:
        return default

    serie = (
        df_base[columna]
        .dropna()
        .astype(str)
        .str.strip()
    )
    serie = serie[~serie.str.lower().isin(["", "-", "nan", "none", "nat"])]

    if serie.empty:
        return default

    return serie.value_counts().index[0]


def construir_resumen_ejecutivo(
    df_total: pd.DataFrame,
    df_filtrado: pd.DataFrame,
    hoy: pd.Timestamp,
) -> dict[str, Any]:
    """Construye una lectura ejecutiva desde lo general a lo accionable.

    Usa únicamente columnas ya preparadas por preparar_panel_tat_rapido para no
    recalcular fechas ni alertas pesadas en cada interacción.
    """
    total_archivo = int(len(df_total))
    total_filtrado = int(len(df_filtrado))
    pct_filtrado = total_filtrado / total_archivo * 100 if total_archivo else 0.0

    base_vacia = {
        "total_archivo": total_archivo,
        "total_filtrado": total_filtrado,
        "pct_filtrado": pct_filtrado,
        "recepcionados": 0,
        "sin_recepcion": 0,
        "vencidos_recepcionados": 0,
        "vencidos_sin_recepcion": 0,
        "proximos_sin_recepcion": 0,
        "sin_fecha_calculable": 0,
        "solped_sin_pedido": 0,
        "con_pedido": 0,
        "pct_sin_pedido": 0.0,
        "etapa_critica": "-",
        "grupo_critico": "-",
        "centro_critico": "-",
        "solicitante_critico": "-",
        "semaforo": "Sin datos",
        "mensaje": "No hay registros con los filtros actuales.",
        "accion_sugerida": "Amplía o ajusta los filtros para revisar el universo de pedidos.",
    }

    if df_filtrado.empty:
        return base_vacia

    estado_recepcion = (
        df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str)
        if COL_ESTADO_RECEPCION_ALERTA in df_filtrado.columns
        else pd.Series("Sin recepción", index=df_filtrado.index)
    )
    dias_restantes = pd.to_numeric(
        df_filtrado.get("dias_restantes_int", pd.Series(np.nan, index=df_filtrado.index)),
        errors="coerce",
    )

    recepcionados_mask = estado_recepcion.eq("Recepcionado")
    sin_recepcion_mask = estado_recepcion.eq("Sin recepción")
    vencidos_mask = dias_restantes.lt(0)
    proximos_mask = dias_restantes.between(0, 30, inclusive="both") & sin_recepcion_mask
    sin_fecha_mask = dias_restantes.isna() & sin_recepcion_mask

    oc_me5a = _serie_texto(df_filtrado, COL_OC_ME5A).str.strip()
    oc_nme = _serie_texto(df_filtrado, COL_OC_NME).str.strip()
    valores_sin_pedido = {"", "-", "nan", "none", "nat", "0", "0.0"}
    sin_pedido_mask = (
        oc_me5a.str.lower().isin(valores_sin_pedido)
        & oc_nme.str.lower().isin(valores_sin_pedido)
    )

    base_riesgo = df_filtrado.loc[
        sin_recepcion_mask & (vencidos_mask | proximos_mask | sin_fecha_mask)
    ].copy()

    recepcionados = int(recepcionados_mask.sum())
    sin_recepcion = int(sin_recepcion_mask.sum())
    vencidos_recepcionados = int((vencidos_mask & recepcionados_mask).sum())
    vencidos_sin_recepcion = int((vencidos_mask & sin_recepcion_mask).sum())
    proximos_sin_recepcion = int(proximos_mask.sum())
    sin_fecha_calculable = int(sin_fecha_mask.sum())
    solped_sin_pedido = int(sin_pedido_mask.sum())
    con_pedido = int(total_filtrado - solped_sin_pedido)
    pct_sin_pedido = solped_sin_pedido / total_filtrado * 100 if total_filtrado else 0.0

    etapa_critica = _top_valor(base_riesgo, "fecha_pendiente")
    grupo_critico = _top_valor(base_riesgo, COL_GRUPO_COMPRAS)
    centro_critico = etiqueta_centro(_top_valor(base_riesgo, COL_CENTRO))
    solicitante_critico = _top_valor(base_riesgo, COL_SOLICITANTE)

    if vencidos_sin_recepcion > 0:
        semaforo = "Crítico"
        mensaje = (
            f"Hay {_entero_texto(vencidos_sin_recepcion)} registros vencidos sin recepción. "
            "La prioridad es gestionar esos casos antes de revisar próximos vencimientos."
        )
        accion_sugerida = (
            "Priorizar pedidos vencidos sin recepción, comenzando por el grupo y centro con mayor concentración de riesgo."
        )
    elif proximos_sin_recepcion > 0:
        semaforo = "Atención"
        mensaje = (
            f"Hay {_entero_texto(proximos_sin_recepcion)} registros próximos a vencer sin recepción. "
            "El foco debe estar en prevenir que pasen a estado vencido."
        )
        accion_sugerida = "Gestionar vencimientos de 0 a 30 días y confirmar recepción o avance de etapa pendiente."
    elif sin_fecha_calculable > 0:
        semaforo = "Datos incompletos"
        mensaje = (
            f"Hay {_entero_texto(sin_fecha_calculable)} registros sin fecha de vencimiento calculable. "
            "La gestión depende de corregir fecha de solicitud, umbral TAT o tipo OC."
        )
        accion_sugerida = "Corregir datos maestros o fechas faltantes para que el pedido entre al seguimiento TAT."
    else:
        semaforo = "Controlado"
        mensaje = "No se observan vencidos ni próximos a vencer sin recepción con los filtros actuales."
        accion_sugerida = "Mantener seguimiento preventivo y revisar SolPed sin pedido o datos incompletos si existen."

    return {
        "total_archivo": total_archivo,
        "total_filtrado": total_filtrado,
        "pct_filtrado": pct_filtrado,
        "recepcionados": recepcionados,
        "sin_recepcion": sin_recepcion,
        "vencidos_recepcionados": vencidos_recepcionados,
        "vencidos_sin_recepcion": vencidos_sin_recepcion,
        "proximos_sin_recepcion": proximos_sin_recepcion,
        "sin_fecha_calculable": sin_fecha_calculable,
        "solped_sin_pedido": solped_sin_pedido,
        "con_pedido": con_pedido,
        "pct_sin_pedido": pct_sin_pedido,
        "etapa_critica": etapa_critica,
        "grupo_critico": grupo_critico,
        "centro_critico": centro_critico,
        "solicitante_critico": solicitante_critico,
        "semaforo": semaforo,
        "mensaje": mensaje,
        "accion_sugerida": accion_sugerida,
    }


def construir_top_prioridades_ejecutivas(df_filtrado: pd.DataFrame, limite: int = 20) -> pd.DataFrame:
    """Lista corta para acción ejecutiva: primero vencidos, luego próximos y luego sin datos."""
    if df_filtrado.empty:
        return pd.DataFrame()

    df = df_filtrado.copy()
    estado_recepcion = (
        df[COL_ESTADO_RECEPCION_ALERTA].astype(str)
        if COL_ESTADO_RECEPCION_ALERTA in df.columns
        else pd.Series("Sin recepción", index=df.index)
    )
    dias = pd.to_numeric(
        df.get("dias_restantes_int", pd.Series(np.nan, index=df.index)),
        errors="coerce",
    )

    # np.select necesita arreglos booleanos puros. En algunas combinaciones
    # pandas/numpy, las Series booleanas con valores NA o dtype de extensión
    # pueden levantar TypeError: should be boolean ndarray.
    sin_recepcion = estado_recepcion.eq("Sin recepción").fillna(False)
    condiciones_prioridad = [
        (sin_recepcion & dias.lt(0).fillna(False)).to_numpy(dtype=bool),
        (sin_recepcion & dias.between(0, 7, inclusive="both").fillna(False)).to_numpy(dtype=bool),
        (sin_recepcion & dias.between(8, 30, inclusive="both").fillna(False)).to_numpy(dtype=bool),
        (sin_recepcion & dias.isna().fillna(False)).to_numpy(dtype=bool),
    ]

    df["_orden_prioridad_ejecutiva"] = np.select(
        condiciones_prioridad,
        [1, 2, 3, 4],
        default=9,
    )
    df["_dias_orden"] = dias.fillna(999999)

    columnas = columnas_existentes(
        df,
        [
            COL_SOLPED,
            COL_OC_ME5A,
            COL_OC_NME,
            COL_POS_SOLPED,
            COL_CENTRO,
            COL_GRUPO_COMPRAS,
            COL_SOLICITANTE,
            "clasificacion_vencimiento",
            "dias_restantes_texto",
            "fecha_vencimiento_texto",
            COL_ESTADO_RECEPCION_ALERTA,
            "ultima_etapa_registrada",
            "fecha_pendiente",
            "causa_raiz_probable",
            "accion_sugerida",
        ],
    )

    salida = (
        df.sort_values(["_orden_prioridad_ejecutiva", "_dias_orden"], ascending=[True, True])
        .head(limite)
        [columnas]
        .copy()
    )

    if COL_CENTRO in salida.columns:
        salida[COL_CENTRO] = salida[COL_CENTRO].map(etiqueta_centro)

    return salida.rename(
        columns={
            COL_SOLPED: "Solicitud de pedido",
            COL_OC_ME5A: "Pedido ME5A",
            COL_OC_NME: "Pedido NME80FN",
            COL_POS_SOLPED: "Posición SolPed",
            COL_CENTRO: "Centro",
            COL_GRUPO_COMPRAS: "Grupo compras",
            COL_SOLICITANTE: "Solicitante",
            "clasificacion_vencimiento": "Urgencia",
            "dias_restantes_texto": "Días restantes",
            "fecha_vencimiento_texto": "Fecha vencimiento",
            COL_ESTADO_RECEPCION_ALERTA: "Recepción",
            "ultima_etapa_registrada": "Última etapa",
            "fecha_pendiente": "Fecha pendiente",
            "causa_raiz_probable": "Causa probable",
            "accion_sugerida": "Acción sugerida",
        }
    )


def mostrar_panel_resumen_ejecutivo(resumen: dict[str, Any], df_filtrado: pd.DataFrame) -> None:
    color = {
        "Crítico": "#dc2626",
        "Atención": "#f97316",
        "Datos incompletos": "#ca8a04",
        "Controlado": "#16a34a",
        "Sin datos": "#64748b",
    }.get(str(resumen.get("semaforo", "")), "#2563eb")

    st.markdown("### Resumen ejecutivo")
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
            border: 1px solid #e2e8f0;
            border-left: 8px solid {color};
            border-radius: 22px;
            padding: 18px 20px;
            margin: 0.8rem 0 1rem 0;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.06);
        ">
            <div style="
                font-size: 0.82rem;
                font-weight: 900;
                color: #64748b;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 6px;
            ">
                Lectura ejecutiva del universo analizado
            </div>
            <div style="
                font-size: 1.35rem;
                font-weight: 950;
                color: #0f172a;
                margin-bottom: 6px;
            ">
                Estado general: {escape(str(resumen.get("semaforo", "Sin datos")))}
            </div>
            <div style="
                font-size: 0.98rem;
                color: #334155;
                line-height: 1.45;
            ">
                {escape(str(resumen.get("mensaje", "")))}
            </div>
            <div style="
                margin-top: 10px;
                font-size: 0.92rem;
                color: #0f172a;
                line-height: 1.45;
                font-weight: 800;
            ">
                Acción sugerida: {escape(str(resumen.get("accion_sugerida", "")))}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    g1, g2, g3, g4 = st.columns(4)
    g1.metric("Universo total", _entero_texto(resumen.get("total_archivo", 0)))
    g2.metric(
        "Registros analizados",
        _entero_texto(resumen.get("total_filtrado", 0)),
        _porcentaje_texto(float(resumen.get("pct_filtrado", 0))),
    )
    g3.metric("Recepcionados", _entero_texto(resumen.get("recepcionados", 0)))
    g4.metric("Sin recepción", _entero_texto(resumen.get("sin_recepcion", 0)))

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Vencidos sin recepción", _entero_texto(resumen.get("vencidos_sin_recepcion", 0)))
    r2.metric("Próximos 0 a 30 días", _entero_texto(resumen.get("proximos_sin_recepcion", 0)))
    r3.metric("Sin fecha calculable", _entero_texto(resumen.get("sin_fecha_calculable", 0)))
    r4.metric("SolPed sin pedido", _entero_texto(resumen.get("solped_sin_pedido", 0)), _porcentaje_texto(float(resumen.get("pct_sin_pedido", 0))))

    e1, e2, e3, e4 = st.columns(4)
    e1.info(f"**Etapa pendiente dominante:** {resumen.get('etapa_critica', '-')}")
    e2.info(f"**Grupo compras con más riesgo:** {resumen.get('grupo_critico', '-')}")
    e3.info(f"**Centro con más riesgo:** {resumen.get('centro_critico', '-')}")
    e4.info(f"**Solicitante con más riesgo:** {resumen.get('solicitante_critico', '-')}")

    with st.expander("Top 20 prioridades ejecutivas", expanded=False):
        tabla_prioridad = construir_top_prioridades_ejecutivas(df_filtrado, limite=20)
        if tabla_prioridad.empty:
            st.info("No hay prioridades para mostrar con los filtros actuales.")
        else:
            st.dataframe(tabla_prioridad, use_container_width=True, hide_index=True)

def construir_vencimientos_sin_recepcion(df_base: pd.DataFrame, hoy: pd.Timestamp) -> pd.DataFrame:
    if df_base.empty:
        base_abiertos = df_base.copy()
    else:
        base_abiertos = df_base[df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str).eq("Sin recepción")].copy()

    dias = pd.to_numeric(base_abiertos.get("dias_restantes_int", pd.Series(np.nan, index=base_abiertos.index)), errors="coerce")
    filas = []

    subset = base_abiertos[dias.lt(0)]
    filas.append({
        "Pregunta": "Vencidos y sin recepcionar",
        "Cantidad": len(subset),
        "Fecha de vencimiento": rango_fechas_texto(subset),
    })

    subset_proximos = base_abiertos[dias.between(0, 30, inclusive="both")]
    filas.append({
        "Pregunta": "Próximos a vencer sin recepción, hoy a 30 días",
        "Cantidad": len(subset_proximos),
        "Fecha de vencimiento": rango_fechas_texto(subset_proximos),
    })

    for d in range(0, 8):
        subset = base_abiertos[dias.eq(d)]
        if d == 0:
            etiqueta = "Vencen hoy"
        elif d == 1:
            etiqueta = "Vencen en 1 día"
        else:
            etiqueta = f"Vencen en {d} días"
        filas.append({
            "Pregunta": etiqueta,
            "Cantidad": len(subset),
            "Fecha de vencimiento": rango_fechas_texto(subset) if len(subset) else fecha_texto(hoy + pd.Timedelta(days=d)),
        })

    subset_7_30 = base_abiertos[dias.between(8, 30, inclusive="both")]
    subset_mas_mes = base_abiertos[dias.gt(30)]
    subset_sin_dato = base_abiertos[dias.isna()]

    filas.extend([
        {
            "Pregunta": "Vencen en 7 a 30 días",
            "Cantidad": len(subset_7_30),
            "Fecha de vencimiento": rango_fechas_texto(subset_7_30),
        },
        {
            "Pregunta": "Vencen en más de 1 mes",
            "Cantidad": len(subset_mas_mes),
            "Fecha de vencimiento": f"Desde {fecha_texto(subset_mas_mes['fecha_vencimiento_tat'].min())}" if len(subset_mas_mes) else "Sin casos",
        },
        {
            "Pregunta": "Sin fecha de vencimiento calculable y sin recepción",
            "Cantidad": len(subset_sin_dato),
            "Fecha de vencimiento": "Sin dato calculable",
        },
    ])

    return pd.DataFrame(filas)


def tabla_resumen_filtrada(df_base: pd.DataFrame) -> pd.DataFrame:
    columnas = columnas_existentes(
        df_base,
        [
            # Primeras columnas solicitadas.
            COL_SOLPED,
            COL_OC_ME5A,
            COL_POS_SOLPED,
            "clasificacion_vencimiento",
            "dias_restantes_texto",
            "tiempo_transcurrido_tat",
            "dias_restantes_int",
            # Columnas complementarias para gestión.
            COL_OC_NME,
            COL_POS_OC,
            "fecha_vencimiento_texto",
            COL_ESTADO_RECEPCION_ALERTA,
            "ultima_etapa_registrada",
            "ultima_fecha_registrada",
            "fecha_pendiente",
            COL_MATERIAL,
            COL_TEXTO,
            COL_CENTRO,
            COL_GRUPO_COMPRAS,
            COL_TIPO_OC,
            COL_DIAS_TAT,
            COL_UMBRAL_TAT,
            "umbral_tat_calculado",
            COL_MONTO,
        ],
    )
    tabla = df_base[columnas].copy()
    return tabla.rename(
        columns={
            COL_SOLPED: "Solicitud de pedido",
            COL_OC_ME5A: "Pedido",
            COL_POS_SOLPED: "Posición solicitud de pedido",
            "clasificacion_vencimiento": "Días hasta vencimiento",
            "dias_restantes_texto": "Días restantes",
            "tiempo_transcurrido_tat": "Tiempo transcurrido",
            "dias_restantes_int": "Días restantes numérico",
            COL_OC_NME: "Documento compras NME",
            COL_POS_OC: "Posición pedido",
            "fecha_vencimiento_texto": "Fecha de vencimiento",
            COL_ESTADO_RECEPCION_ALERTA: "Recepción",
            "ultima_etapa_registrada": "Última etapa registrada",
            "ultima_fecha_registrada": "Fecha última registrada",
            "fecha_pendiente": "Fecha pendiente",
            COL_DIAS_TAT: "Días TAT total",
            COL_UMBRAL_TAT: "Umbral TAT original",
            "umbral_tat_calculado": "Umbral TAT usado",
        }
    )



def construir_zoom_sin_fecha_sin_recepcion(df_base: pd.DataFrame) -> pd.DataFrame:
    """Detalle de registros sin fecha de vencimiento calculable y sin recepción.

    Un registro cae aquí cuando está abierto y no se pudo calcular la fecha de
    vencimiento TAT, normalmente porque falta fecha de solicitud, umbral TAT o
    tipo OC válido para inferir el umbral.
    """
    if df_base.empty:
        return pd.DataFrame()

    estado_recepcion = (
        df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str)
        if COL_ESTADO_RECEPCION_ALERTA in df_base.columns
        else pd.Series("Sin recepción", index=df_base.index)
    )

    dias = pd.to_numeric(
        df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)),
        errors="coerce",
    )

    mask = estado_recepcion.eq("Sin recepción") & dias.isna()
    detalle = df_base.loc[mask].copy()

    if detalle.empty:
        return pd.DataFrame()

    fecha_inicio = pd.to_datetime(
        detalle.get("fecha_inicio_tat", pd.Series(pd.NaT, index=detalle.index)),
        errors="coerce",
    )
    umbral = pd.to_numeric(
        detalle.get("umbral_tat_calculado", pd.Series(np.nan, index=detalle.index)),
        errors="coerce",
    )

    razones = []
    for idx in detalle.index:
        faltantes = []
        if pd.isna(fecha_inicio.loc[idx]):
            faltantes.append("falta fecha de solicitud")
        if pd.isna(umbral.loc[idx]):
            faltantes.append("falta umbral TAT o tipo OC válido")
        if not faltantes:
            faltantes.append("revisar datos de vencimiento")
        razones.append("; ".join(faltantes))

    detalle["motivo_sin_fecha_vencimiento"] = razones

    columnas = columnas_existentes(
        detalle,
        [
            COL_SOLPED,
            COL_OC_ME5A,
            COL_POS_SOLPED,
            COL_POS_OC,
            "motivo_sin_fecha_vencimiento",
            "ultima_etapa_registrada",
            "ultima_fecha_registrada",
            "fecha_pendiente",
            "tiempo_transcurrido_tat",
            "fecha_inicio_tat",
            COL_UMBRAL_TAT,
            "umbral_tat_calculado",
            COL_TIPO_OC,
            COL_CENTRO,
            COL_GRUPO_COMPRAS,
            COL_MATERIAL,
            COL_TEXTO,
            COL_SOLICITANTE,
            COL_ORIGEN,
            COL_SISTEMA,
        ],
    )

    salida = detalle[columnas].copy()
    return salida.rename(
        columns={
            COL_SOLPED: "Solicitud de pedido",
            COL_OC_ME5A: "Pedido",
            COL_POS_SOLPED: "Posición solicitud de pedido",
            COL_POS_OC: "Posición pedido",
            "motivo_sin_fecha_vencimiento": "Motivo sin fecha de vencimiento",
            "ultima_etapa_registrada": "Última etapa registrada",
            "ultima_fecha_registrada": "Fecha última registrada",
            "fecha_pendiente": "Fecha pendiente",
            "tiempo_transcurrido_tat": "Tiempo transcurrido",
            "fecha_inicio_tat": "Fecha inicio TAT",
            COL_UMBRAL_TAT: "Umbral TAT original",
            "umbral_tat_calculado": "Umbral TAT usado",
            COL_TIPO_OC: "Tipo OC",
            COL_CENTRO: "Centro",
            COL_GRUPO_COMPRAS: "Grupo compras",
            COL_MATERIAL: "Material",
            COL_TEXTO: "Descripción",
            COL_SOLICITANTE: "Solicitante",
            COL_ORIGEN: "Origen",
            COL_SISTEMA: "Sistema",
        }
    )



def construir_distribucion_porcentual(
    df_base: pd.DataFrame,
    columna: str,
    nombre_columna: str,
) -> pd.DataFrame:
    if df_base.empty or columna not in df_base.columns:
        return pd.DataFrame(columns=[nombre_columna, "Cantidad", "% del total"])

    total = len(df_base)
    serie_distribucion = (
        df_base[columna]
        .fillna("Sin dato")
        .astype(str)
        .str.strip()
    )

    if columna == COL_CENTRO:
        serie_distribucion = serie_distribucion.map(etiqueta_centro)

    conteo = (
        serie_distribucion
        .value_counts(dropna=False)
        .rename_axis(nombre_columna)
        .reset_index(name="Cantidad")
    )
    conteo["% del total"] = np.where(total > 0, conteo["Cantidad"] / total * 100, 0)
    conteo["% del total"] = conteo["% del total"].map(
        lambda x: f"{x:,.1f}%".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    return conteo


def detalle_proximos_sin_recepcion(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty:
        return pd.DataFrame()

    estado_recepcion = (
        df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str)
        if COL_ESTADO_RECEPCION_ALERTA in df_base.columns
        else pd.Series("Sin recepción", index=df_base.index)
    )
    dias = pd.to_numeric(
        df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)),
        errors="coerce",
    )
    detalle = df_base.loc[estado_recepcion.eq("Sin recepción") & dias.between(0, 30, inclusive="both")].copy()
    return tabla_resumen_filtrada(detalle) if not detalle.empty else pd.DataFrame()


def detalle_vencidos_sin_recepcion(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty:
        return pd.DataFrame()

    estado_recepcion = (
        df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str)
        if COL_ESTADO_RECEPCION_ALERTA in df_base.columns
        else pd.Series("Sin recepción", index=df_base.index)
    )
    dias = pd.to_numeric(
        df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)),
        errors="coerce",
    )
    detalle = df_base.loc[estado_recepcion.eq("Sin recepción") & dias.lt(0)].copy()
    return tabla_resumen_filtrada(detalle) if not detalle.empty else pd.DataFrame()



# =========================================================
# Lectura del dataframe global
# =========================================================
if "df_tat" not in st.session_state:
    st.warning("Primero debes cargar el archivo base en Análisis TAT > Cargar archivo.")
    st.stop()

nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")
hoy = pd.Timestamp.today().normalize()

try:
    df_original = st.session_state["df_tat"].copy()
    df_panel = preparar_panel_tat_rapido(df_original, hoy)
    opciones_filtros = opciones_filtros_rapidas(df_panel)
except Exception as e:
    st.error("No se pudo preparar el archivo cargado.")
    st.exception(e)
    st.stop()

total_archivo = len(df_panel)
st.success(f"Archivo activo: {nombre_archivo}")

# Valores iniciales/persistentes de filtros.
# El resumen ejecutivo aparece antes del formulario, pero se calcula con estos
# mismos filtros. En primera carga el centro queda fijado en E002 · Prillex.
opciones_centro_panel = opciones_filtros.get(COL_CENTRO, [])
centro_default_panel = [
    c for c in opciones_centro_panel
    if normalizar_codigo_centro(c) == "E002"
]

if "filtro_panel_centro" not in st.session_state:
    st.session_state["filtro_panel_centro"] = centro_default_panel
if "filtro_panel_recepcion" not in st.session_state:
    st.session_state["filtro_panel_recepcion"] = "Sin recepción"
if "filtro_panel_vencimiento" not in st.session_state:
    st.session_state["filtro_panel_vencimiento"] = []
if "filtro_panel_grupo" not in st.session_state:
    st.session_state["filtro_panel_grupo"] = []
if "filtro_panel_tipo_oc" not in st.session_state:
    st.session_state["filtro_panel_tipo_oc"] = []
if "filtro_panel_ultima_fecha" not in st.session_state:
    st.session_state["filtro_panel_ultima_fecha"] = []
if "filtro_panel_fecha_pendiente" not in st.session_state:
    st.session_state["filtro_panel_fecha_pendiente"] = []
if "filtro_panel_limite_tabla" not in st.session_state:
    st.session_state["filtro_panel_limite_tabla"] = 300
if "filtro_panel_solped" not in st.session_state:
    st.session_state["filtro_panel_solped"] = ""
if "filtro_panel_oc" not in st.session_state:
    st.session_state["filtro_panel_oc"] = ""
if "filtro_panel_texto" not in st.session_state:
    st.session_state["filtro_panel_texto"] = ""


# =========================================================
# Resumen ejecutivo inicial · conectado a filtros activos
# =========================================================
df_resumen_ejecutivo = aplicar_filtros_panel(
    df_panel,
    centro_sel=st.session_state.get("filtro_panel_centro", centro_default_panel),
    recepcion_sel=st.session_state.get("filtro_panel_recepcion", "Sin recepción"),
    vencimiento_sel=st.session_state.get("filtro_panel_vencimiento", []),
    grupo_sel=st.session_state.get("filtro_panel_grupo", []),
    tipo_oc_sel=st.session_state.get("filtro_panel_tipo_oc", []),
    ultima_fecha_sel=st.session_state.get("filtro_panel_ultima_fecha", []),
    fecha_pendiente_sel=st.session_state.get("filtro_panel_fecha_pendiente", []),
    solped_txt=st.session_state.get("filtro_panel_solped", ""),
    oc_txt=st.session_state.get("filtro_panel_oc", ""),
    texto_txt=st.session_state.get("filtro_panel_texto", ""),
)

resumen_ejecutivo_global = construir_resumen_ejecutivo(
    df_total=df_panel,
    df_filtrado=df_resumen_ejecutivo,
    hoy=hoy,
)
st.caption(
    "Resumen calculado con filtros activos: "
    f"Centro: {lista_centros_corta(st.session_state.get('filtro_panel_centro', centro_default_panel))} · "
    f"Recepción: {st.session_state.get('filtro_panel_recepcion', 'Sin recepción')}"
)
mostrar_panel_resumen_ejecutivo(resumen_ejecutivo_global, df_resumen_ejecutivo)


# =========================================================
# Preguntas sobre el total de datos
# =========================================================
st.markdown("### Radiografía del archivo completo")

centros_dist = construir_distribucion_porcentual(df_panel, COL_CENTRO, "Centro")
recepcion_dist_total = construir_distribucion_porcentual(df_panel, COL_ESTADO_RECEPCION_ALERTA, "Recepción")

col_total_1, col_total_2 = st.columns(2)
with col_total_1:
    cantidad_centros = centros_dist["Centro"].nunique() if not centros_dist.empty else 0
    st.metric("Centros en el archivo", f"{cantidad_centros:,}".replace(",", "."))
    with st.expander("Distribución porcentual por centro · total de datos", expanded=False):
        st.dataframe(centros_dist, use_container_width=True, hide_index=True)

with col_total_2:
    st.metric("Datos totales", f"{total_archivo:,}".replace(",", "."))
    with st.expander("Distribución porcentual Recepción / Sin recepción · total de datos", expanded=False):
        st.dataframe(recepcion_dist_total, use_container_width=True, hide_index=True)


# =========================================================
# Filtros en formulario para evitar recálculos por cada cambio
# =========================================================
st.markdown("### Filtros")
st.caption("Cambia todos los filtros que necesites y luego presiona Aplicar filtros. Esto evita recalcular la pantalla con cada clic.")

with st.form("form_filtros_panel_unico"):
    f1, f2, f3, f4 = st.columns([1.1, 1.1, 1.6, 1.1])

    with f1:
        opciones_centro = opciones_centro_panel
        centro_sel = st.multiselect(
            "Filtro 1 · Centro",
            opciones_centro,
            key="filtro_panel_centro",
            format_func=etiqueta_centro,
        )

    with f2:
        recepcion_sel = st.selectbox(
            "Filtro 2 · Recepción",
            ["Todos", "Sin recepción", "Recepcionado"],
            key="filtro_panel_recepcion",
        )

    with f3:
        opciones_vencimiento = [
            "Vencido",
            "Vence hoy",
            "1 día",
            "2 días",
            "3 días",
            "4 días",
            "5 días",
            "6 días",
            "7 días",
            "7 a 30 días",
            "Más de 1 mes",
            "Sin datos",
        ]
        vencimiento_sel = st.multiselect(
            "Filtro 3 · Urgencia / días hasta vencimiento",
            opciones_vencimiento,
            key="filtro_panel_vencimiento",
            help=(
                "Puedes seleccionar una o varias urgencias. "
                "Déjalo vacío para no filtrar por días hasta vencimiento."
            ),
        )
        st.caption("Selecciona una o varias urgencias y confirma con Aplicar filtros.")

    with f4:
        grupo_sel = st.multiselect(
            "Filtro 4 · Grupo compras",
            opciones_filtros.get(COL_GRUPO_COMPRAS, []),
            key="filtro_panel_grupo",
        )

    f5, f6, f7, f8 = st.columns([1.1, 1.1, 1, 1])

    with f5:
        tipo_oc_sel = st.multiselect(
            "Filtro 5 · Tipo OC",
            opciones_filtros.get(COL_TIPO_OC, []),
            key="filtro_panel_tipo_oc",
        )

    with f6:
        ultima_fecha_sel = st.multiselect(
            "Filtro 6 · Última etapa registrada",
            opciones_filtros.get("ultima_etapa_registrada", []),
            key="filtro_panel_ultima_fecha",
        )

    with f7:
        fecha_pendiente_sel = st.multiselect(
            "Filtro 7 · Fecha pendiente",
            opciones_filtros.get("fecha_pendiente", []),
            key="filtro_panel_fecha_pendiente",
        )

    with f8:
        limite_tabla = st.number_input(
            "Filas visibles",
            min_value=50,
            max_value=2000,
            step=50,
            key="filtro_panel_limite_tabla",
            help="Mostrar menos filas acelera la visualización. La descarga puede incluir todo el filtrado.",
        )

    f9, f10, f11 = st.columns([1, 1, 1.4])
    with f9:
        solped_txt = st.text_input(
            "Filtro 8 · SolPed",
            placeholder="Buscar SolPed",
            key="filtro_panel_solped",
        )
    with f10:
        oc_txt = st.text_input(
            "Filtro 9 · OC / Pedido",
            placeholder="Buscar OC",
            key="filtro_panel_oc",
        )
    with f11:
        texto_txt = st.text_input(
            "Filtro 10 · Material / descripción / solicitante",
            placeholder="Buscar texto",
            key="filtro_panel_texto",
        )

    # Detalle anidado del Filtro 3 para elegir rápidamente según urgencia.
    base_detalle_filtro_3 = df_panel.copy()
    if centro_sel and COL_CENTRO in base_detalle_filtro_3.columns:
        base_detalle_filtro_3 = base_detalle_filtro_3[
            base_detalle_filtro_3[COL_CENTRO].astype(str).isin([str(v) for v in centro_sel])
        ]
    if recepcion_sel != "Todos" and COL_ESTADO_RECEPCION_ALERTA in base_detalle_filtro_3.columns:
        base_detalle_filtro_3 = base_detalle_filtro_3[
            base_detalle_filtro_3[COL_ESTADO_RECEPCION_ALERTA].astype(str).eq(recepcion_sel)
        ]

    with st.expander("Detalle anidado del Filtro 3 · urgencia disponible", expanded=False):
        st.caption(
            "Este detalle muestra cuántos registros existen por cada opción del Filtro 3, "
            "considerando Filtro 1 Centro y Filtro 2 Recepción. Puedes seleccionar varias opciones arriba."
        )
        detalle_filtro_3 = construir_detalle_filtro_3(base_detalle_filtro_3)
        st.dataframe(
            aplicar_estilo_detalle_filtro_3(detalle_filtro_3),
            use_container_width=True,
            hide_index=True,
        )

    aplicar = st.form_submit_button("Aplicar filtros", type="primary")


# =========================================================
# Aplicación de filtros
# =========================================================
df_filtrado = aplicar_filtros_panel(
    df_panel,
    centro_sel=centro_sel,
    recepcion_sel=recepcion_sel,
    vencimiento_sel=vencimiento_sel,
    grupo_sel=grupo_sel,
    tipo_oc_sel=tipo_oc_sel,
    ultima_fecha_sel=ultima_fecha_sel,
    fecha_pendiente_sel=fecha_pendiente_sel,
    solped_txt=solped_txt,
    oc_txt=oc_txt,
    texto_txt=texto_txt,
)

filtrados = len(df_filtrado)
porcentaje_filtrado = filtrados / total_archivo * 100 if total_archivo else 0


# =========================================================
# Respuestas principales
# =========================================================
st.markdown("### Respuestas del filtrado actual")

k1, k2, k3, k4, k5 = st.columns([1, 1, 1, 1, 1])

estado_recepcion = df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str) if COL_ESTADO_RECEPCION_ALERTA in df_filtrado.columns else pd.Series("Sin recepción", index=df_filtrado.index)
dias_filtrados = pd.to_numeric(df_filtrado.get("dias_restantes_int", pd.Series(np.nan, index=df_filtrado.index)), errors="coerce")
vencidos_mask = dias_filtrados.lt(0)
recepcionados_mask = estado_recepcion.eq("Recepcionado")
sin_recepcion_mask = estado_recepcion.eq("Sin recepción")
proximos_mask = dias_filtrados.between(0, 30, inclusive="both") & sin_recepcion_mask

vencidos_recepcionados = int((vencidos_mask & recepcionados_mask).sum())
vencidos_sin_recepcion = int((vencidos_mask & sin_recepcion_mask).sum())
proximos_sin_recepcion = int(proximos_mask.sum())
otros_casos = int(filtrados - vencidos_recepcionados - vencidos_sin_recepcion - proximos_sin_recepcion)

k1.metric("Datos totales en archivo", f"{total_archivo:,}".replace(",", "."))
k2.metric(
    "Datos filtrados",
    f"{filtrados:,}".replace(",", "."),
    f"{porcentaje_filtrado:,.1f}% del total".replace(",", "X").replace(".", ",").replace("X", "."),
)
k3.metric("Vencidos y recepcionados", f"{vencidos_recepcionados:,}".replace(",", "."))
k4.metric("Vencidos y sin recepcionar", f"{vencidos_sin_recepcion:,}".replace(",", "."))
k5.metric("Próximos a vencer sin recepción", f"{proximos_sin_recepcion:,}".replace(",", "."))

st.info(
    f"Según estos filtros hay **{filtrados:,} datos filtrados** de **{total_archivo:,} datos totales**. "
    f"La diferencia entre los filtrados y los grupos principales se explica en la conciliación: "
    f"**{otros_casos:,} otros casos**."
    .replace(",", ".")
)

# Pregunta adicional: SolPed sin pedido.
oc_me5a = _serie_texto(df_filtrado, COL_OC_ME5A).str.strip()
oc_nme = _serie_texto(df_filtrado, COL_OC_NME).str.strip()
valores_sin_pedido = {"", "-", "nan", "none", "nat", "0", "0.0"}
sin_pedido_mask = oc_me5a.str.lower().isin(valores_sin_pedido) & oc_nme.str.lower().isin(valores_sin_pedido)
sin_pedido_cantidad = int(sin_pedido_mask.sum())
con_pedido_cantidad = int(filtrados - sin_pedido_cantidad)
sin_pedido_pct = (sin_pedido_cantidad / filtrados * 100) if filtrados else 0

sp1, sp2, sp3 = st.columns(3)
sp1.metric("SolPed sin pedido", f"{sin_pedido_cantidad:,}".replace(",", "."))
sp2.metric("% SolPed sin pedido", f"{sin_pedido_pct:,.1f}%".replace(",", "X").replace(".", ",").replace("X", "."))
sp3.metric("SolPed con pedido", f"{con_pedido_cantidad:,}".replace(",", "."))
st.caption(
    "Esta respuesta considera como SolPed sin pedido aquellos registros filtrados sin valor en Pedido - ME5A y sin valor en Documento de compras - NME80FN. "
    "En esos casos puede no existir tipo de OC asociado al pedido."
)

filtros_resumen = pd.DataFrame(
    [
        {"Filtro": "Filtro 1", "Campo": "Centro", "Selección": lista_centros_corta(centro_sel)},
        {"Filtro": "Filtro 2", "Campo": "Recepción", "Selección": recepcion_sel},
        {"Filtro": "Filtro 3", "Campo": "Días hasta vencimiento", "Selección": lista_valores_corta(vencimiento_sel)},
        {"Filtro": "Filtro 4", "Campo": "Grupo compras", "Selección": lista_valores_corta(grupo_sel)},
        {"Filtro": "Filtro 5", "Campo": "Tipo OC", "Selección": lista_valores_corta(tipo_oc_sel)},
        {"Filtro": "Filtro 6", "Campo": "Última etapa registrada", "Selección": lista_valores_corta(ultima_fecha_sel)},
        {"Filtro": "Filtro 7", "Campo": "Fecha pendiente", "Selección": lista_valores_corta(fecha_pendiente_sel)},
        {"Filtro": "Filtro 8", "Campo": "SolPed", "Selección": solped_txt.strip() or "Todos"},
        {"Filtro": "Filtro 9", "Campo": "OC / Pedido", "Selección": oc_txt.strip() or "Todos"},
        {"Filtro": "Filtro 10", "Campo": "Material / descripción / solicitante", "Selección": texto_txt.strip() or "Todos"},
    ]
)

with st.expander("Ver filtros aplicados", expanded=False):
    st.dataframe(filtros_resumen, use_container_width=True, hide_index=True)


# =========================================================
# Resumen consolidado: conciliación + vencimientos
# =========================================================
st.markdown("#### Resumen consolidado del total filtrado")
st.caption(
    "Unifica la conciliación del total filtrado con los vencidos sin recepción y los próximos a vencer. "
    "Los casos próximos a vencer consideran pedidos sin recepción entre hoy y 30 días."
)

df_conciliacion = construir_conciliacion(df_filtrado)
st.dataframe(
    aplicar_estilo_conciliacion(df_conciliacion),
    use_container_width=True,
    hide_index=True,
)

if not df_conciliacion.empty and "TOTAL FILTRADO" in df_conciliacion["Grupo"].astype(str).values:
    suma_conciliacion = int(
        df_conciliacion.loc[
            df_conciliacion["Grupo"].astype(str).eq("TOTAL FILTRADO"),
            "Cantidad",
        ].iloc[0]
    )
else:
    suma_conciliacion = int(df_conciliacion["Cantidad"].sum()) if not df_conciliacion.empty else 0

if suma_conciliacion != filtrados:
    st.warning(
        f"La conciliación suma {suma_conciliacion:,} registros y el filtrado tiene {filtrados:,}. "
        "Revisa estados de recepción o valores no clasificados."
        .replace(",", ".")
    )

df_vencimientos = construir_vencimientos_sin_recepcion(df_filtrado, hoy)
with st.expander("Detalle anidado · Vencidos y próximos a vencer sin recepción", expanded=False):
    st.caption(
        "Incluye solo pedidos sin recepción. La fecha de vencimiento se calcula como fecha de solicitud + umbral TAT. "
        "Los pedidos recepcionados se consideran cerrados para este detalle."
    )
    st.dataframe(df_vencimientos, use_container_width=True, hide_index=True)


# =========================================================
# Alerta y descarga de vencidos sin recepción
# =========================================================
df_vencidos_sin_recepcion_detalle = detalle_vencidos_sin_recepcion(df_filtrado)
cantidad_vencidos_sin_recepcion_alerta = len(df_vencidos_sin_recepcion_detalle)

if cantidad_vencidos_sin_recepcion_alerta > 0:
    mensaje_vencidos = (
        f"ALERTA: hay {cantidad_vencidos_sin_recepcion_alerta:,} registros vencidos sin recepción. "
        "Estos casos ya superaron su fecha de vencimiento TAT y requieren gestión prioritaria."
    ).replace(",", ".")
    st.markdown(
        f"""
        <div style="
            background:#fee2e2;
            border:1px solid #fca5a5;
            border-left:7px solid #dc2626;
            color:#7f1d1d;
            border-radius:16px;
            padding:16px 18px;
            margin:14px 0 12px 0;
            font-weight:850;
            box-shadow:0 1px 5px rgba(15, 23, 42, 0.06);
        ">
            {escape(mensaje_vencidos)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Vista previa · Vencidos sin recepción", expanded=False):
        st.caption(
            f"Mostrando {cantidad_vencidos_sin_recepcion_alerta:,} registros vencidos sin recepción. "
            "Abre esta sección solo si necesitas revisar el detalle."
            .replace(",", ".")
        )

        st.dataframe(
            df_vencidos_sin_recepcion_detalle,
            use_container_width=True,
            hide_index=True,
        )

    v1, v2 = st.columns(2)
    with v1:
        st.download_button(
            "Descargar vencidos sin recepción CSV",
            data=dataframe_a_csv(df_vencidos_sin_recepcion_detalle),
            file_name="vencidos_sin_recepcion.csv",
            mime="text/csv",
        )
    with v2:
        st.download_button(
            "Descargar vencidos sin recepción Excel",
            data=dataframe_a_excel(df_vencidos_sin_recepcion_detalle),
            file_name="vencidos_sin_recepcion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
else:
    st.success("No hay registros vencidos sin recepción con los filtros actuales.")


# =========================================================
# Alerta y descarga de próximos a vencer sin recepción
# =========================================================
df_proximos_sin_recepcion_detalle = detalle_proximos_sin_recepcion(df_filtrado)
cantidad_proximos_alerta = len(df_proximos_sin_recepcion_detalle)

if cantidad_proximos_alerta > 0:
    mensaje_proximos = (
        f"ALERTA: hay {cantidad_proximos_alerta:,} registros próximos a vencer sin recepción entre hoy y 30 días."
        .replace(",", ".")
    )
    st.markdown(
        f"""
        <div style="
            background:#ffedd5;
            border:1px solid #fdba74;
            border-left:7px solid #f97316;
            color:#7c2d12;
            border-radius:16px;
            padding:16px 18px;
            margin:14px 0 12px 0;
            font-weight:850;
            box-shadow:0 1px 5px rgba(15, 23, 42, 0.06);
        ">
            {escape(mensaje_proximos)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Vista previa · Próximos a vencer sin recepción", expanded=False):
        st.caption(
            f"Mostrando {cantidad_proximos_alerta:,} registros próximos a vencer sin recepción entre hoy y 30 días. "
            "Abre esta sección solo si necesitas revisar el detalle."
            .replace(",", ".")
        )

        st.dataframe(
            df_proximos_sin_recepcion_detalle,
            use_container_width=True,
            hide_index=True,
        )

    a1, a2 = st.columns(2)
    with a1:
        st.download_button(
            "Descargar próximos a vencer CSV",
            data=dataframe_a_csv(df_proximos_sin_recepcion_detalle),
            file_name="proximos_a_vencer_sin_recepcion.csv",
            mime="text/csv",
        )
    with a2:
        st.download_button(
            "Descargar próximos a vencer Excel",
            data=dataframe_a_excel(df_proximos_sin_recepcion_detalle),
            file_name="proximos_a_vencer_sin_recepcion.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
else:
    st.success("No hay registros próximos a vencer sin recepción entre hoy y 30 días con los filtros actuales.")


# =========================================================
# Zoom: sin fecha de vencimiento calculable y sin recepción
# =========================================================
df_zoom_sin_fecha = construir_zoom_sin_fecha_sin_recepcion(df_filtrado)

with st.expander("Zoom · Sin fecha de vencimiento calculable y sin recepción", expanded=False):
    st.caption(
        "Detalle de pedidos abiertos donde no fue posible calcular fecha de vencimiento. "
        "Normalmente ocurre porque falta fecha de solicitud, falta umbral TAT o el tipo OC no permite inferir el umbral."
    )

    if df_zoom_sin_fecha.empty:
        st.success("No hay pedidos sin fecha de vencimiento calculable y sin recepción con los filtros actuales.")
    else:
        z1, z2 = st.columns([1, 3])
        z1.metric(
            "Casos sin fecha calculable",
            f"{len(df_zoom_sin_fecha):,}".replace(",", "."),
        )
        z2.info(
            "Estos casos no entran en vencidos ni próximos a vencer porque no tienen fecha de vencimiento TAT calculable. "
            "Revise el motivo para corregir el dato de origen."
        )

        limite_zoom = st.number_input(
            "Filas visibles en zoom sin fecha",
            min_value=25,
            max_value=2000,
            value=min(300, max(25, len(df_zoom_sin_fecha))),
            step=25,
        )

        st.dataframe(
            df_zoom_sin_fecha.head(int(limite_zoom)),
            use_container_width=True,
            hide_index=True,
        )

        zcsv, zexcel = st.columns(2)
        with zcsv:
            st.download_button(
                "Descargar zoom sin fecha calculable CSV",
                data=dataframe_a_csv(df_zoom_sin_fecha),
                file_name="zoom_sin_fecha_vencimiento_sin_recepcion.csv",
                mime="text/csv",
            )
        with zexcel:
            st.download_button(
                "Descargar zoom sin fecha calculable Excel",
                data=dataframe_a_excel(df_zoom_sin_fecha),
                file_name="zoom_sin_fecha_vencimiento_sin_recepcion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

# =========================================================
# Datos filtrados mínimos
# =========================================================
tabla_resumen = tabla_resumen_filtrada(df_filtrado)

with st.expander("Datos filtrados", expanded=False):
    st.caption(
        f"Mostrando {min(int(limite_tabla), filtrados):,} de {filtrados:,} registros filtrados. "
        "Reducir filas visibles mejora la velocidad."
        .replace(",", ".")
    )

    st.dataframe(
        tabla_resumen.head(int(limite_tabla)),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("#### Descargas del filtrado")
    st.caption("Las descargas se preparan solo cuando se muestran estos controles, para evitar lentitud al filtrar.")
    col_csv, col_excel = st.columns(2)

    with col_csv:
        csv_bytes = dataframe_a_csv(tabla_resumen)
        st.download_button(
            "Descargar CSV filtrado",
            data=csv_bytes,
            file_name="control_tat_filtrado.csv",
            mime="text/csv",
        )

    with col_excel:
        preparar_excel = st.button("Preparar Excel filtrado")
        if preparar_excel:
            excel_bytes = dataframe_a_excel(tabla_resumen)
            st.download_button(
                "Descargar Excel filtrado",
                data=excel_bytes,
                file_name="control_tat_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# =========================================================
# Expediente del pedido
# =========================================================
st.markdown("### Expediente del pedido")

if df_filtrado.empty:
    st.info("No hay pedidos disponibles con los filtros actuales.")
else:
    total_expediente_base = len(df_filtrado)

    st.markdown("#### Gestión visual y selección de pedidos críticos")
    st.caption(
        (
            f"El expediente parte desde los {total_expediente_base:,} registros que quedaron después de los filtros generales. "
            "La gestión visual prioriza vencidos, alertas críticas y pedidos sin recepción para que puedas elegir rápidamente el caso a revisar."
        ).replace(",", ".")
    )

    st.markdown(
        """
        <div class="critical-hero">
            <div class="critical-hero-title">Gestión visual para identificar pedidos críticos</div>
            <div class="critical-hero-text">
                Filtra por nivel de alerta, urgencia, recepción, etapa pendiente y responsable operativo. Luego revisa la tabla priorizada y selecciona el pedido crítico para abrir su expediente completo.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    df_expediente_base = ordenar_expediente_critico(df_filtrado)

    with st.expander("🚦 Gestión visual de críticos · filtrar, visualizar y elegir", expanded=True):
        g1, g2, g3, g4 = st.columns(4)

        niveles_disponibles = (
            df_expediente_base["nivel_alerta"].dropna().astype(str).sort_values().unique().tolist()
            if "nivel_alerta" in df_expediente_base.columns else []
        )
        niveles_default = [v for v in ["Crítica", "Alta"] if v in niveles_disponibles]

        urgencias_disponibles = (
            df_expediente_base["dias_hasta_vencimiento"].dropna().astype(str).unique().tolist()
            if "dias_hasta_vencimiento" in df_expediente_base.columns else []
        )
        urgencias_disponibles = [u for u in BUCKETS_DIAS_VENCIMIENTO if u in urgencias_disponibles] + [
            u for u in sorted(urgencias_disponibles) if u not in BUCKETS_DIAS_VENCIMIENTO
        ]
        urgencias_default = [u for u in ["Vencido", "1 día", "2 días", "7 días"] if u in urgencias_disponibles]

        recepcion_disponible = (
            df_expediente_base[COL_ESTADO_RECEPCION_ALERTA].dropna().astype(str).sort_values().unique().tolist()
            if COL_ESTADO_RECEPCION_ALERTA in df_expediente_base.columns else []
        )
        recepcion_default = [v for v in ["Sin recepción"] if v in recepcion_disponible]

        pendiente_disponible = (
            df_expediente_base["fecha_pendiente"].dropna().astype(str).sort_values().unique().tolist()
            if "fecha_pendiente" in df_expediente_base.columns else []
        )

        with g1:
            gestion_niveles = st.multiselect(
                "Nivel de alerta",
                niveles_disponibles,
                default=niveles_default,
                key="gestion_niveles_expediente",
            )

        with g2:
            gestion_urgencias = st.multiselect(
                "Urgencia",
                urgencias_disponibles,
                default=urgencias_default,
                key="gestion_urgencias_expediente",
            )

        with g3:
            gestion_recepcion = st.multiselect(
                "Recepción",
                recepcion_disponible,
                default=recepcion_default,
                key="gestion_recepcion_expediente",
            )

        with g4:
            gestion_pendiente = st.multiselect(
                "Fecha pendiente",
                pendiente_disponible,
                key="gestion_pendiente_expediente",
            )

        gg1, gg2, gg3, gg4 = st.columns(4)
        with gg1:
            gestion_centro = st.multiselect(
                "Centro crítico",
                sorted(df_expediente_base[COL_CENTRO].dropna().astype(str).unique().tolist())
                if COL_CENTRO in df_expediente_base.columns else [],
                key="gestion_centro_expediente",
            )
        with gg2:
            gestion_grupo = st.multiselect(
                "Grupo compras",
                sorted(df_expediente_base[COL_GRUPO_COMPRAS].dropna().astype(str).unique().tolist())
                if COL_GRUPO_COMPRAS in df_expediente_base.columns else [],
                key="gestion_grupo_expediente",
            )
        with gg3:
            gestion_accion = st.multiselect(
                "Acción sugerida",
                sorted(df_expediente_base["accion_sugerida"].dropna().astype(str).unique().tolist())
                if "accion_sugerida" in df_expediente_base.columns else [],
                key="gestion_accion_expediente",
            )
        with gg4:
            gestion_top_n = st.number_input(
                "Máximo a visualizar",
                min_value=10,
                max_value=1000,
                value=100,
                step=10,
                key="gestion_top_n_expediente",
            )

        mask_gestion = pd.Series(True, index=df_expediente_base.index)
        if gestion_niveles and "nivel_alerta" in df_expediente_base.columns:
            mask_gestion &= df_expediente_base["nivel_alerta"].astype(str).isin([str(v) for v in gestion_niveles])
        if gestion_urgencias and "dias_hasta_vencimiento" in df_expediente_base.columns:
            mask_gestion &= df_expediente_base["dias_hasta_vencimiento"].astype(str).isin([str(v) for v in gestion_urgencias])
        if gestion_recepcion and COL_ESTADO_RECEPCION_ALERTA in df_expediente_base.columns:
            mask_gestion &= df_expediente_base[COL_ESTADO_RECEPCION_ALERTA].astype(str).isin([str(v) for v in gestion_recepcion])
        if gestion_pendiente and "fecha_pendiente" in df_expediente_base.columns:
            mask_gestion &= df_expediente_base["fecha_pendiente"].astype(str).isin([str(v) for v in gestion_pendiente])
        if gestion_centro and COL_CENTRO in df_expediente_base.columns:
            mask_gestion &= df_expediente_base[COL_CENTRO].astype(str).isin([str(v) for v in gestion_centro])
        if gestion_grupo and COL_GRUPO_COMPRAS in df_expediente_base.columns:
            mask_gestion &= df_expediente_base[COL_GRUPO_COMPRAS].astype(str).isin([str(v) for v in gestion_grupo])
        if gestion_accion and "accion_sugerida" in df_expediente_base.columns:
            mask_gestion &= df_expediente_base["accion_sugerida"].astype(str).isin([str(v) for v in gestion_accion])

        df_gestion = ordenar_expediente_critico(df_expediente_base.loc[mask_gestion].copy())
        df_gestion_preview = df_gestion.head(int(gestion_top_n)).copy()

        mg1, mg2, mg3, mg4, mg5 = st.columns(5)
        with mg1:
            st.metric("Críticos visualizados", f"{len(df_gestion):,}".replace(",", "."))
        with mg2:
            vencidos_gestion = int(df_gestion.get("dias_hasta_vencimiento", pd.Series(dtype=str)).astype(str).eq("Vencido").sum())
            st.metric("Vencidos", f"{vencidos_gestion:,}".replace(",", "."))
        with mg3:
            sin_recepcion_gestion = int(df_gestion.get(COL_ESTADO_RECEPCION_ALERTA, pd.Series(dtype=str)).astype(str).eq("Sin recepción").sum())
            st.metric("Sin recepción", f"{sin_recepcion_gestion:,}".replace(",", "."))
        with mg4:
            alta_critica_gestion = int(df_gestion.get("nivel_alerta", pd.Series(dtype=str)).astype(str).isin(["Crítica", "Alta"]).sum())
            st.metric("Crítica / alta", f"{alta_critica_gestion:,}".replace(",", "."))
        with mg5:
            score_promedio = valor_numerico(df_gestion["score_riesgo"].mean()) if "score_riesgo" in df_gestion.columns and not df_gestion.empty else np.nan
            st.metric("Score prom.", formato_numero_corto(score_promedio, 1))

        if df_gestion.empty:
            st.warning("No hay pedidos críticos con los filtros visuales aplicados.")
        else:
            st.caption("Tabla priorizada: los primeros registros son los más urgentes según prioridad operativa, score de riesgo, brecha TAT y tiempo transcurrido.")
            tabla_visual = tabla_gestion_expediente(df_gestion_preview)
            st.dataframe(
                aplicar_estilo_gestion_expediente(tabla_visual),
                use_container_width=True,
                hide_index=True,
            )

            labels_gestion = {idx: construir_label_registro_critico(df_gestion.loc[idx]) for idx in df_gestion.index.tolist()}
            seleccionado_gestion = st.selectbox(
                "Elegir pedido crítico desde la gestión visual",
                df_gestion.index.tolist(),
                format_func=lambda idx: labels_gestion.get(idx, str(idx)),
                key="selector_gestion_visual_expediente",
            )
            st.session_state["expediente_idx_sugerido"] = seleccionado_gestion

    st.markdown("#### Filtros finos del expediente")
    st.caption(
        "Usa estos filtros si quieres buscar por identificadores exactos o acotar aún más el selector del expediente."
    )

    with st.expander("🔎 Filtros del expediente · búsqueda detallada", expanded=False):
        st.caption("Estos filtros solo afectan el selector del expediente; no modifican las alertas ni las tablas superiores.")

        with st.form("form_filtros_expediente"):
            e1, e2, e3 = st.columns([1, 1, 0.85])

            with e1:
                exp_solped = st.text_input(
                    "SolPed",
                    placeholder="Ej: 1001973319",
                    key="exp_filtro_solped",
                )

            with e2:
                exp_oc = st.text_input(
                    "Orden de compra / Pedido",
                    placeholder="Ej: 4502321875",
                    key="exp_filtro_oc",
                )

            with e3:
                exp_pos_solped = st.text_input(
                    "Posición solicitud de pedido",
                    placeholder="Ej: 10",
                    key="exp_filtro_pos_solped",
                )

            ae1, ae2, ae3, ae4 = st.columns(4)

            with ae1:
                exp_material = st.text_input(
                    "Material",
                    placeholder="Ej: 20012021",
                    key="exp_filtro_material",
                )

            with ae2:
                exp_descripcion = st.text_input(
                    "Descripción / texto breve",
                    placeholder="Ej: bloqueador",
                    key="exp_filtro_descripcion",
                )

            with ae3:
                exp_centro = st.multiselect(
                    "Centro",
                    sorted(df_filtrado[COL_CENTRO].dropna().astype(str).unique().tolist())
                    if COL_CENTRO in df_filtrado.columns else [],
                    key="exp_filtro_centro",
                )

            with ae4:
                exp_grupo = st.multiselect(
                    "Grupo de compras",
                    sorted(df_filtrado[COL_GRUPO_COMPRAS].dropna().astype(str).unique().tolist())
                    if COL_GRUPO_COMPRAS in df_filtrado.columns else [],
                    key="exp_filtro_grupo",
                )

            be1, be2, be3 = st.columns(3)

            with be1:
                exp_estado_recepcion = st.multiselect(
                    "Recepción",
                    sorted(df_filtrado[COL_ESTADO_RECEPCION_ALERTA].dropna().astype(str).unique().tolist())
                    if COL_ESTADO_RECEPCION_ALERTA in df_filtrado.columns else [],
                    key="exp_filtro_recepcion",
                )

            with be2:
                exp_urgencia = st.multiselect(
                    "Estado pedido",
                    sorted(df_filtrado["clasificacion_vencimiento"].dropna().astype(str).unique().tolist())
                    if "clasificacion_vencimiento" in df_filtrado.columns else [],
                    key="exp_filtro_urgencia",
                )

            with be3:
                exp_fecha_pendiente = st.multiselect(
                    "Fecha pendiente",
                    sorted(df_filtrado["fecha_pendiente"].dropna().astype(str).unique().tolist())
                    if "fecha_pendiente" in df_filtrado.columns else [],
                    key="exp_filtro_fecha_pendiente",
                )

            aplicar_exp = st.form_submit_button("Aplicar filtros del expediente", use_container_width=True)

    mask_exp = pd.Series(True, index=df_filtrado.index)

    mask_exp &= filtrar_por_ids(df_filtrado, COL_SOLPED, exp_solped)
    mask_exp &= (
        filtrar_por_ids(df_filtrado, COL_OC_ME5A, exp_oc)
        | filtrar_por_ids(df_filtrado, COL_OC_NME, exp_oc)
    )
    mask_exp &= filtrar_por_ids(df_filtrado, COL_POS_SOLPED, exp_pos_solped)
    mask_exp &= filtrar_por_ids(df_filtrado, COL_MATERIAL, exp_material)
    mask_exp &= contiene_texto(df_filtrado, COL_TEXTO, exp_descripcion)

    if exp_centro and COL_CENTRO in df_filtrado.columns:
        mask_exp &= df_filtrado[COL_CENTRO].astype(str).isin([str(v) for v in exp_centro])

    if exp_grupo and COL_GRUPO_COMPRAS in df_filtrado.columns:
        mask_exp &= df_filtrado[COL_GRUPO_COMPRAS].astype(str).isin([str(v) for v in exp_grupo])

    if exp_estado_recepcion and COL_ESTADO_RECEPCION_ALERTA in df_filtrado.columns:
        mask_exp &= df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str).isin([str(v) for v in exp_estado_recepcion])

    if exp_urgencia and "clasificacion_vencimiento" in df_filtrado.columns:
        mask_exp &= df_filtrado["clasificacion_vencimiento"].astype(str).isin([str(v) for v in exp_urgencia])

    if exp_fecha_pendiente and "fecha_pendiente" in df_filtrado.columns:
        mask_exp &= df_filtrado["fecha_pendiente"].astype(str).isin([str(v) for v in exp_fecha_pendiente])

    df_expediente = ordenar_expediente_critico(df_filtrado.loc[mask_exp].copy())

    # Si la gestión visual ya eligió un caso, lo mantenemos arriba del selector cuando también cumple los filtros finos.
    sugerido = st.session_state.get("expediente_idx_sugerido")

    total_expediente_filtrado = len(df_expediente)
    max_selector = 5000
    opciones_registro = df_expediente.index.tolist()[:max_selector]
    if sugerido in df_expediente.index and sugerido not in opciones_registro:
        opciones_registro = [sugerido] + opciones_registro[:-1]
    elif sugerido in opciones_registro:
        opciones_registro = [sugerido] + [idx for idx in opciones_registro if idx != sugerido]

    registros_selector = len(opciones_registro)

    mexp1, mexp2, mexp3 = st.columns(3)
    with mexp1:
        st.metric("Registros del filtrado general", f"{total_expediente_base:,}".replace(",", "."))
    with mexp2:
        st.metric("Registros disponibles para expediente", f"{total_expediente_filtrado:,}".replace(",", "."))
    with mexp3:
        st.metric("Registros cargados en selector", f"{registros_selector:,}".replace(",", "."))

    if total_expediente_filtrado > max_selector:
        st.warning(
            (
                f"El selector muestra los primeros {max_selector:,} registros de {total_expediente_filtrado:,}. "
                "Usa la gestión visual o los filtros finos del expediente para acotar la búsqueda."
            ).replace(",", ".")
        )

    if df_expediente.empty:
        st.warning("No hay pedidos disponibles para el expediente con los filtros locales aplicados.")
    else:
        labels = {idx: construir_label_registro_critico(df_expediente.loc[idx]) for idx in opciones_registro}

        index_default = 0
        if sugerido in opciones_registro:
            index_default = opciones_registro.index(sugerido)

        seleccionado = st.selectbox(
            "Pedido disponible según filtros del expediente",
            opciones_registro,
            index=index_default,
            format_func=lambda idx: labels.get(idx, str(idx)),
        )

        row = df_expediente.loc[seleccionado]

        st.markdown(html_pedido_critico_seleccionado(row), unsafe_allow_html=True)
        st.markdown(html_resumen_pedido_expediente(row), unsafe_allow_html=True)
        st.markdown(html_avance_actual(row), unsafe_allow_html=True)
        st.markdown(html_linea_pedido(row), unsafe_allow_html=True)
        st.markdown(html_diagrama_tat_unificado(row), unsafe_allow_html=True)
        st.markdown(html_kpis_expediente(row), unsafe_allow_html=True)

        with st.expander("Registro completo del pedido", expanded=False):
            registro = row.to_frame(name="Valor").reset_index().rename(columns={"index": "Campo"})
            registro["Valor"] = registro["Valor"].apply(formato_valor)
            st.dataframe(registro, use_container_width=True, hide_index=True)



# =========================================================
# Detalle estadístico por material
# =========================================================
st.markdown("### Detalle por Material - ME5A · tiempo desde el inicio del pedido")
st.caption(
    "Estadística calculada sobre los registros del filtrado actual. El tiempo desde el inicio del pedido se mide en días desde la fecha de solicitud hasta la recepción; si no existe recepción, se calcula hasta hoy."
)

if COL_MATERIAL not in df_filtrado.columns:
    st.warning("No existe la columna Material - ME5A en el archivo cargado, por lo que no se puede construir el detalle por material.")
elif "tiempo_transcurrido_tat_dias" not in df_filtrado.columns:
    st.warning("No existe la columna calculada tiempo_transcurrido_tat_dias, por lo que no se puede calcular la estadística por material.")
else:
    df_material_stats_base = df_filtrado.copy()
    df_material_stats_base["_material_estadistica"] = df_material_stats_base[COL_MATERIAL].apply(formato_id)
    df_material_stats_base["_tiempo_inicio_pedido_dias"] = pd.to_numeric(
        df_material_stats_base["tiempo_transcurrido_tat_dias"],
        errors="coerce",
    )

    df_material_stats_base = df_material_stats_base[
        df_material_stats_base["_tiempo_inicio_pedido_dias"].notna()
        & df_material_stats_base["_material_estadistica"].astype(str).str.strip().ne("")
        & ~df_material_stats_base["_material_estadistica"].astype(str).str.lower().isin(["-", "nan", "none", "nat"])
    ].copy()

    if df_material_stats_base.empty:
        st.info("No hay datos suficientes para calcular MIN, MEDIA, MEDIANA, MAX y desviación estándar por material con los filtros actuales.")
    else:
        estadistica_material = (
            df_material_stats_base
            .groupby("_material_estadistica", dropna=False)["_tiempo_inicio_pedido_dias"]
            .agg(
                Registros="count",
                Min="min",
                Media="mean",
                Mediana="median",
                Max="max",
                Desviacion_estandar="std",
            )
            .reset_index()
            .rename(columns={"_material_estadistica": "Material - ME5A"})
        )

        estadistica_material["Desviacion_estandar"] = estadistica_material["Desviacion_estandar"].fillna(0)

        if COL_TEXTO in df_material_stats_base.columns:
            descripcion_material = (
                df_material_stats_base
                .sort_values("_tiempo_inicio_pedido_dias", ascending=False)
                .groupby("_material_estadistica")[COL_TEXTO]
                .first()
                .reset_index()
                .rename(columns={"_material_estadistica": "Material - ME5A", COL_TEXTO: "Descripción muestra"})
            )
            estadistica_material = estadistica_material.merge(
                descripcion_material,
                on="Material - ME5A",
                how="left",
            )

        columnas_ordenadas_material = [
            "Material - ME5A",
            "Descripción muestra",
            "Registros",
            "Min",
            "Media",
            "Mediana",
            "Max",
            "Desviacion_estandar",
        ]
        columnas_ordenadas_material = [c for c in columnas_ordenadas_material if c in estadistica_material.columns]
        estadistica_material = estadistica_material[columnas_ordenadas_material].copy()
        estadistica_material = estadistica_material.sort_values(
            ["Media", "Max", "Registros"],
            ascending=[False, False, False],
        )

        for col in ["Min", "Media", "Mediana", "Max", "Desviacion_estandar"]:
            if col in estadistica_material.columns:
                estadistica_material[col] = estadistica_material[col].round(1)

        tiempo_global = df_material_stats_base["_tiempo_inicio_pedido_dias"]
        g1, g2, g3, g4, g5, g6 = st.columns(6)
        g1.metric("Materiales", f"{len(estadistica_material):,}".replace(",", "."))
        g2.metric("Registros", f"{len(df_material_stats_base):,}".replace(",", "."))
        g3.metric("MIN días", formato_numero_corto(tiempo_global.min(), 1))
        g4.metric("MEDIA días", formato_numero_corto(tiempo_global.mean(), 1))
        g5.metric("MEDIANA días", formato_numero_corto(tiempo_global.median(), 1))
        g6.metric("MAX días", formato_numero_corto(tiempo_global.max(), 1))

        st.dataframe(
            estadistica_material,
            use_container_width=True,
            hide_index=True,
        )

        cmat1, cmat2 = st.columns(2)
        with cmat1:
            st.download_button(
                "Descargar estadística por material CSV",
                data=dataframe_a_csv(estadistica_material),
                file_name="estadistica_material_tiempo_inicio_pedido.csv",
                mime="text/csv",
            )
        with cmat2:
            st.download_button(
                "Descargar estadística por material Excel",
                data=dataframe_a_excel(estadistica_material),
                file_name="estadistica_material_tiempo_inicio_pedido.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
