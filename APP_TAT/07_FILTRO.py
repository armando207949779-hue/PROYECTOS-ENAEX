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
# Constantes de columnas
# =========================================================
COL_SOLPED          = "Solicitud de pedido - ME5A"
COL_OC_ME5A         = "Pedido - ME5A"
COL_OC_NME          = "Documento de compras - NME80FN"
COL_POS_SOLPED      = "Posición solicitud de pedido - ME5A"
COL_POS_OC          = "Posición de pedido - ME5A"
COL_MATERIAL        = "Material - ME5A"
COL_TEXTO           = "Texto breve - ME5A"
COL_CENTRO          = "Centro - ME5A"
COL_SOLICITANTE     = "Solicitante"
COL_AUTOR           = "Autor"
COL_GRUPO_COMPRAS   = "Grupo de compras"
COL_TIPO_IMPUTACION = "Tipo de imputación"
COL_TIPO_OC         = "tipo_oc"
COL_ORIGEN          = "origen"
COL_SISTEMA         = "sistema"
COL_ESTADO_MATCH    = "Estado del match"
COL_PERF_TAT        = "performance_tat_total"
COL_RANGO_INC       = "rango_incumplimiento_tat"
COL_INC_TAT         = "incumplimiento_tat"
COL_DIAS_TAT        = "dias_tat_total"
COL_DIAS_INC        = "dias_incumplimiento_tat"
COL_UMBRAL_TAT      = "umbral_tat_total"
COL_MONTO           = "monto"
COL_FECHAS_INCONS   = "tiene_fechas_inconsistentes"

FECHAS_CANDIDATAS = [
    "fecha_solicitud_final", "fecha_liberacion_final", "fecha_pedido_final",
    "fecha_facturacion_final", "fecha_recepcion_final",
    "Fecha de solicitud - ME5A", "Fecha modificación",
    "Fecha de liberación - ME5A", "Fecha de pedido - ME5A",
    "Fecha de entrega - ME5A", "Fecha de liberación",
    "Fecha solicitud de compra - ARIBA", "Fecha de aprobación - ARIBA",
    "Fecha de entrada - NME80FN", "Fecha de documento - NME80FN",
    "Fecha contabilización - NME80FN", "Fecha facturación proveedor - NME80FN",
    "Fecha recepción mercancía - NME80FN",
]

ETAPAS_PEDIDO = [
    {"titulo": "1. Solicitud",       "fecha": "fecha_solicitud_final",   "dias": None,                  "umbral": None,                  "performance": None,                       "nota": "Inicio SolPed"},
    {"titulo": "2. Liberación",      "fecha": "fecha_liberacion_final",  "dias": "dias_liberacion_solped","umbral": "umbral_liberacion_solped","performance": "performance_liberacion_solped","nota": "Solicitud → Liberación"},
    {"titulo": "3. Comprador",       "fecha": "fecha_pedido_final",      "dias": "dias_comprador",       "umbral": "umbral_comprador",      "performance": "performance_comprador",    "nota": "Liberación → Pedido"},
    {"titulo": "4. Proveedor",       "fecha": "fecha_facturacion_final", "dias": "dias_proveedor",       "umbral": "umbral_proveedor",      "performance": "performance_proveedor",    "nota": "Pedido → Facturación"},
    {"titulo": "5. Logística",       "fecha": "fecha_recepcion_final",   "dias": "dias_logistica",       "umbral": "umbral_logistica",      "performance": "performance_logistica",    "nota": "Facturación → Recepción"},
    {"titulo": "6. TAT Total",       "fecha": "fecha_recepcion_final",   "dias": "dias_tat_total",       "umbral": "umbral_tat_total",      "performance": "performance_tat_total",    "nota": "Solicitud → Recepción"},
]
ETAPAS_LINEA = [
    ("Solicitud",  "fecha_solicitud_final"),
    ("Liberación", "fecha_liberacion_final"),
    ("Pedido",     "fecha_pedido_final"),
    ("Facturación","fecha_facturacion_final"),
    ("Recepción",  "fecha_recepcion_final"),
]
COLUMNAS_TABLA_BASE = [
    COL_SOLPED, COL_OC_ME5A, COL_OC_NME, COL_POS_SOLPED, COL_POS_OC,
    COL_MATERIAL, COL_TEXTO, COL_CENTRO, COL_SOLICITANTE, COL_GRUPO_COMPRAS,
    COL_TIPO_OC, COL_ORIGEN, COL_SISTEMA, COL_PERF_TAT, COL_DIAS_TAT,
    COL_UMBRAL_TAT, COL_DIAS_INC, COL_RANGO_INC, COL_MONTO,
]

# =========================================================
# Catálogo de centros
# =========================================================
CENTROS_CATALOGO = {
    "E002":{"sociedad":"EC01","nombre":"Prillex"},         "E021":{"sociedad":"EC06","nombre":"CM-Enaex Servicios"},
    "E024":{"sociedad":"EC06","nombre":"Río Loa"},          "E025":{"sociedad":"EC06","nombre":"Planta La Chimba"},
    "E026":{"sociedad":"EC06","nombre":"Teatinos"},         "E029":{"sociedad":"EC06","nombre":"Chuquicamata"},
    "E030":{"sociedad":"EC06","nombre":"El Tesoro"},        "E031":{"sociedad":"EC06","nombre":"La Escondida"},
    "E032":{"sociedad":"EC06","nombre":"Loma Bayas"},       "E033":{"sociedad":"EC06","nombre":"Los Pelambres"},
    "E034":{"sociedad":"EC06","nombre":"Los Sauces"},       "E035":{"sociedad":"EC06","nombre":"Mantos Blancos"},
    "E036":{"sociedad":"EC06","nombre":"Michilla"},         "E037":{"sociedad":"EC06","nombre":"RT"},
    "E038":{"sociedad":"EC06","nombre":"El Soldado"},       "E039":{"sociedad":"EC06","nombre":"Polpaico"},
    "E040":{"sociedad":"EC06","nombre":"Peldehue"},         "E041":{"sociedad":"EC06","nombre":"Esperanza"},
    "E042":{"sociedad":"EC06","nombre":"Gaby"},             "E044":{"sociedad":"EC06","nombre":"Atacama Kozan"},
    "E045":{"sociedad":"EC06","nombre":"Franke"},           "E046":{"sociedad":"EC06","nombre":"Manto Verde"},
    "E047":{"sociedad":"EC06","nombre":"Polvorín Copiapó"},"E069":{"sociedad":"EC06","nombre":"Guanaco"},
    "E071":{"sociedad":"EC06","nombre":"Teniente"},         "E076":{"sociedad":"EC06","nombre":"Mejillones"},
    "E077":{"sociedad":"EC06","nombre":"Ministro Hales"},   "E078":{"sociedad":"EC06","nombre":"Sierra Gorda"},
    "E079":{"sociedad":"EC06","nombre":"Planta Quebrada Blanca"},"E081":{"sociedad":"EC06","nombre":"Chuqui Subte"},
    "E086":{"sociedad":"EC06","nombre":"Antucoya"},         "E087":{"sociedad":"EC06","nombre":"Alto Maipo"},
    "E088":{"sociedad":"EC06","nombre":"Encuentro"},        "E089":{"sociedad":"EC06","nombre":"Cerro Colorado"},
    "E090":{"sociedad":"EC06","nombre":"Collahuasi"},       "E091":{"sociedad":"EC06","nombre":"Romeral"},
    "E095":{"sociedad":"EC06","nombre":"Planta Andina"},    "E097":{"sociedad":"EC06","nombre":"Andina"},
    "E099":{"sociedad":"EC06","nombre":"Salvador"},         "E103":{"sociedad":"EC06","nombre":"Zaldívar"},
    "E104":{"sociedad":"EC06","nombre":"Salares Norte"},    "E105":{"sociedad":"EC06","nombre":"Los Colorados"},
    "E106":{"sociedad":"EC06","nombre":"Cerro N.N."},       "E107":{"sociedad":"EC06","nombre":"Pleito"},
    "E108":{"sociedad":"EC06","nombre":"Plasma Enaex Servicios"},
    "E109":{"sociedad":"EC06","nombre":"Carola"},
    "E110":{"sociedad":"EC06","nombre":"Alto Hospicio SKC Enaex Servicios"},
    "E113":{"sociedad":"EC06","nombre":"Copiapó SKC Enaex Servicios"},
    "E114":{"sociedad":"EC06","nombre":"FullRPM Nogales Enaex Servicios"},
    "E082":{"sociedad":"EC07","nombre":"Nittra Casa Matriz"},"E083":{"sociedad":"EC07","nombre":"Nittra Prillex"},
    "E084":{"sociedad":"EC07","nombre":"Nittra Paine"},      "E101":{"sociedad":"EC10","nombre":"Plasma"},
    "E003":{"sociedad":"EC01","nombre":"Planta Río Loa"},    "E009":{"sociedad":"EC01","nombre":"Planta Chuquicamata"},
    "E020":{"sociedad":"EC01","nombre":"Planta Polpaico"},   "E057":{"sociedad":"EC01","nombre":"Esperanza"},
    "E102":{"sociedad":"EC06","nombre":"SCL Bodega Arriendo"},"E043":{"sociedad":"EC06","nombre":"El Peñón Subte"},
    "E115":{"sociedad":"EC06","nombre":"Enaex SKC ING"},     "E027":{"sociedad":"EC06","nombre":"Faena Teniente Rajo"},
    "E052":{"sociedad":"EC06","nombre":"Faena Spence"},
}

# =========================================================
# Sistema de diseño unificado
# =========================================================
ESTILOS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important; }

.block-container { padding: 1.5rem 2rem 2rem 2rem !important; max-width: 1600px !important; }

/* ── Sidebar oscura ── */
section[data-testid="stSidebar"] { background: #0f172a !important; border-right: 1px solid #1e293b; }
section[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 { color: #f8fafc !important; font-weight: 700 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] .stCheckbox label {
    color: #94a3b8 !important; font-size: 0.72rem !important;
    font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.06em !important;
}
section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button {
    background: #2563eb !important; color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 700 !important; width: 100% !important; padding: 0.65rem !important;
}
section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button:hover { background: #1d4ed8 !important; }

/* ── Pestañas ── */
.stTabs [data-baseweb="tab-list"] { gap: 4px; background: #f1f5f9; padding: 5px; border-radius: 14px; border: none; margin-bottom: 1.5rem; }
.stTabs [data-baseweb="tab"] { border-radius: 10px !important; padding: 0.55rem 1.1rem !important; font-weight: 600 !important; font-size: 0.88rem !important; color: #64748b !important; background: transparent !important; border: none !important; transition: all 0.15s ease !important; }
.stTabs [aria-selected="true"] { background: #ffffff !important; color: #0f172a !important; box-shadow: 0 1px 4px rgba(15,23,42,0.10) !important; }

/* ── Métricas ── */
div[data-testid="metric-container"] { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px 16px; box-shadow: 0 1px 3px rgba(15,23,42,0.04); }
div[data-testid="metric-container"] label { color: #64748b !important; font-size: 0.72rem !important; font-weight: 600 !important; text-transform: uppercase !important; letter-spacing: 0.05em !important; }
div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #0f172a !important; font-size: 1.6rem !important; font-weight: 700 !important; letter-spacing: -0.02em !important; }
div[data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 0.8rem !important; font-weight: 500 !important; }

/* ── Títulos ── */
h1 { font-size: 1.75rem !important; font-weight: 700 !important; letter-spacing: -0.02em !important; color: #0f172a !important; }
h2 { font-size: 1.25rem !important; font-weight: 700 !important; letter-spacing: -0.01em !important; color: #0f172a !important; }
h3 { font-size: 1.05rem !important; font-weight: 600 !important; color: #1e293b !important; margin-top: 0.75rem !important; }
h4 { font-size: 0.92rem !important; font-weight: 600 !important; color: #334155 !important; }

/* ── Expanders ── */
.streamlit-expanderHeader { background: #f8fafc !important; border: 1px solid #e2e8f0 !important; border-radius: 12px !important; font-weight: 600 !important; font-size: 0.88rem !important; color: #334155 !important; padding: 0.65rem 1rem !important; }
.streamlit-expanderContent { border: 1px solid #e2e8f0 !important; border-top: none !important; border-radius: 0 0 12px 12px !important; padding: 1rem !important; }

/* ── Botones descarga ── */
[data-testid="stDownloadButton"] button { background: #f8fafc !important; color: #334155 !important; border: 1px solid #e2e8f0 !important; border-radius: 10px !important; font-weight: 600 !important; font-size: 0.84rem !important; padding: 0.55rem 1rem !important; transition: all 0.15s ease !important; width: 100% !important; }
[data-testid="stDownloadButton"] button:hover { background: #e2e8f0 !important; border-color: #cbd5e1 !important; }

/* ── Botón primario verde (Confirmar búsqueda) ── */
[data-testid="stButton"] > button[kind="primary"],
div.stButton > button[kind="primary"] {
    background-color: #2563eb !important; border-color: #1d4ed8 !important;
    color: #ffffff !important; font-weight: 700 !important; border-radius: 10px !important;
}
[data-testid="stButton"] > button[kind="primary"]:hover,
div.stButton > button[kind="primary"]:hover { background-color: #1d4ed8 !important; }

/* ── Info/Warning/Success ── */
div[data-testid="stInfo"], div[data-testid="stWarning"], div[data-testid="stSuccess"] { border-radius: 12px !important; font-size: 0.9rem !important; font-weight: 500 !important; }

/* ── Dataframes ── */
[data-testid="stDataFrame"] { border-radius: 12px !important; overflow: hidden !important; border: 1px solid #e2e8f0 !important; }

/* ── Caption ── */
.stCaption, [data-testid="stCaptionContainer"] { color: #94a3b8 !important; font-size: 0.78rem !important; font-weight: 400 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 99px; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* ── Cards genéricas ── */
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 18px 20px; margin: 0.6rem 0; box-shadow: 0 1px 4px rgba(15,23,42,0.04); }

/* ── Ficha expediente ── */
.exp-header { background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 18px 20px; margin: 0.75rem 0; }
.exp-header-title { font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 3px; }
.exp-header-sub   { font-size: 0.84rem; color: #64748b; margin-bottom: 14px; }
.exp-badge { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; }
.exp-badge-rec  { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
.exp-badge-sinr { background: #fef9c3; color: #854d0e; border: 1px solid #fde68a; }
.exp-fields { display: grid; grid-template-columns: repeat(5, minmax(110px, 1fr)); gap: 8px; }
.exp-field { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; }
.exp-field-label { color: #94a3b8; font-size: 0.67rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.exp-field-value { color: #0f172a; font-size: 0.94rem; font-weight: 700; line-height: 1.2; overflow-wrap: anywhere; }

/* ── TAT summary cards ── */
.tat-summary { display: grid; grid-template-columns: 1.15fr 1fr 1fr; gap: 12px; margin: 0.75rem 0; }
.tat-card    { background: #fff; border: 1px solid #e5e7eb; border-radius: 18px; padding: 16px 18px; box-shadow: 0 1px 5px rgba(15,23,42,0.04); }
.tat-card-primary { background: #eff6ff; border-color: #bfdbfe; }
.tat-label   { color: #64748b; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 700; margin-bottom: 6px; }
.tat-main    { color: #0f172a; font-size: 2rem; line-height: 1.05; font-weight: 800; margin-bottom: 6px; }
.tat-main-sm { color: #0f172a; font-size: 1.35rem; line-height: 1.1;  font-weight: 800; margin-bottom: 8px; }
.tat-sub     { color: #334155; font-size: 0.92rem; line-height: 1.35; }
.tat-muted   { color: #64748b; font-size: 0.82rem; line-height: 1.35; margin-top: 5px; }

/* ── Avance actual ── */
.avance-card  { background: #fff; border: 1px solid #dbeafe; border-left: 4px solid #2563eb; border-radius: 16px; padding: 15px 18px; margin: 0.75rem 0; }
.avance-title { color: #1e3a8a; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; }
.avance-grid  { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 10px; }
.avance-item  { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 11px; }
.avance-label { color: #94a3b8; font-size: 0.67rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 3px; }
.avance-value { color: #0f172a; font-size: 0.92rem; font-weight: 700; overflow-wrap: anywhere; }
.avance-note  { color: #475569; font-size: 0.84rem; line-height: 1.4; margin-top: 10px; }

/* ── Pipeline ── */
.pipe-card  { background: linear-gradient(180deg,#f0fdf4 0%,#fff 100%); border: 1px solid #bbf7d0; border-radius: 18px; padding: 18px 20px 16px; margin: 0.75rem 0; }
.pipe-title { font-size: 0.78rem; font-weight: 700; color: #14532d; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 14px; }
.pipe-line  { display: flex; align-items: flex-start; width: 100%; }
.pipe-step  { flex: 0 0 108px; text-align: center; min-width: 0; }
.pipe-dot   { width: 48px; height: 48px; border-radius: 50%; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.4rem; box-sizing: border-box; }
.pipe-dot-ok     { background: #22c55e; color: #fff; border: 3px solid #22c55e; }
.pipe-dot-active { background: #fff; color: #15803d; border: 5px solid #22c55e; }
.pipe-dot-nd     { background: #fff; color: #94a3b8; border: 4px solid #cbd5e1; }
.pipe-label { font-size: 0.78rem; font-weight: 700; color: #1f2937; text-transform: uppercase; }
.pipe-date  { color: #64748b; font-size: 0.72rem; margin-top: 3px; overflow-wrap: anywhere; }
.pipe-conn  { flex: 1; height: 5px; min-width: 24px; margin-top: 22px; border-radius: 99px; background: #cbd5e1; }
.pipe-conn-ok     { background: #22c55e; }
.pipe-conn-dashed { background: repeating-linear-gradient(90deg,#22c55e 0 14px,transparent 14px 22px); }
.pipe-note  { color: #475569; font-size: 0.82rem; line-height: 1.4; margin-top: 12px; }

/* ── TAT flow ── */
.tat-flow-card  { background: linear-gradient(180deg,#f8fafc 0%,#fff 100%); border: 1px solid #dbeafe; border-radius: 18px; padding: 18px 20px 16px; margin: 0.75rem 0; }
.tat-flow-title { font-size: 0.78rem; font-weight: 700; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 14px; }
.tat-flow       { display: flex; align-items: stretch; width: 100%; overflow-x: auto; padding-bottom: 4px; }
.tat-flow-step  { flex: 0 0 150px; text-align: center; min-width: 0; }
.tat-flow-dot   { width: 48px; height: 48px; border-radius: 50%; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1rem; box-sizing: border-box; }
.tat-flow-dot-ok      { background: #22c55e; color: #fff; border: 3px solid #22c55e; }
.tat-flow-dot-bad     { background: #fef2f2; color: #991b1b; border: 4px solid #ef4444; }
.tat-flow-dot-risk    { background: #fff7ed; color: #c2410c; border: 4px solid #fb923c; }
.tat-flow-dot-active  { background: #fff; color: #1d4ed8; border: 5px solid #3b82f6; }
.tat-flow-dot-pending { background: #fff; color: #94a3b8; border: 4px solid #cbd5e1; }
.tat-flow-label  { font-size: 0.75rem; font-weight: 700; color: #1f2937; text-transform: uppercase; }
.tat-flow-date   { color: #475569; font-size: 0.7rem; line-height: 1.22; margin-top: 3px; overflow-wrap: anywhere; }
.tat-flow-detail { color: #334155; font-size: 0.7rem; line-height: 1.22; margin-top: 4px; }
.tat-flow-conn   { flex: 1; height: 5px; min-width: 28px; margin-top: 22px; border-radius: 99px; background: #cbd5e1; }
.tat-flow-conn-ok     { background: #22c55e; }
.tat-flow-conn-active { background: repeating-linear-gradient(90deg,#3b82f6 0 14px,transparent 14px 22px); }
.tat-flow-note   { color: #475569; font-size: 0.82rem; line-height: 1.4; margin-top: 12px; }

/* ── Pills ── */
.pill { display: inline-block; border-radius: 999px; padding: 3px 9px; font-size: 0.72rem; font-weight: 700; border: 1px solid transparent; white-space: nowrap; }
.pill-green  { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
.pill-red    { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
.pill-yellow { background: #fef9c3; color: #854d0e; border-color: #fde68a; }
.pill-gray   { background: #f1f5f9; color: #475569; border-color: #e2e8f0; }
.pill-blue   { background: #dbeafe; color: #1e40af; border-color: #bfdbfe; }

/* ── Selector context banner ── */
.selector-context { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin: 0.5rem 0 1rem 0; }
.selector-card { border-radius: 12px; padding: 13px 16px; }

/* ── Estadísticas etapa ── */
.etapa-stat { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px 14px; margin-bottom: 8px; }
.etapa-stat-title { font-size: 0.75rem; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; }
.etapa-stat-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 6px; }
.etapa-stat-cell { background: #fff; border: 1px solid #e2e8f0; border-radius: 9px; padding: 7px 9px; text-align: center; }
.etapa-stat-label { font-size: 0.62rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; margin-bottom: 3px; }
.etapa-stat-val   { font-size: 0.92rem; font-weight: 700; color: #0f172a; }

/* ── Responsive ── */
@media (max-width: 1200px) {
    .exp-fields  { grid-template-columns: repeat(3, minmax(110px, 1fr)); }
    .avance-grid { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
    .tat-summary { grid-template-columns: 1fr; }
    .etapa-stat-grid { grid-template-columns: repeat(3, 1fr); }
    .selector-context { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
    .exp-fields   { grid-template-columns: 1fr; }
    .avance-grid  { grid-template-columns: 1fr; }
    .etapa-stat-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
"""
st.markdown(ESTILOS, unsafe_allow_html=True)


# =========================================================
# Utilidades
# =========================================================
def _fmt_id(valor: Any) -> str:
    if pd.isna(valor): return "-"
    texto = str(valor).strip()
    try:
        n = float(texto)
        if np.isfinite(n) and n.is_integer(): return str(int(n))
    except Exception: pass
    return texto[:-2] if texto.endswith(".0") else texto

def _fmt(valor: Any) -> str:
    if pd.isna(valor): return "-"
    if isinstance(valor, pd.Timestamp): return valor.strftime("%d-%m-%Y")
    if isinstance(valor, float):
        if np.isfinite(valor) and valor.is_integer(): return f"{int(valor):,}".replace(",",".")
        return f"{valor:,.1f}".replace(",","X").replace(".",",").replace("X",".")
    if isinstance(valor, int): return f"{valor:,}".replace(",",".")
    return str(valor)

def _fmt_int(v: Any) -> str:
    try: return f"{int(v):,}".replace(",",".")
    except: return "0"

def _fmt_pct(v: Any) -> str:
    try: return f"{float(v):.1f}".replace(".",",") + "%"
    except: return "0,0%"

def _vn(valor: Any) -> float:
    try: return float(pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0])
    except: return np.nan

def _esc(v: Any) -> str: return escape(_fmt(v))
def _esc_id(v: Any) -> str: return escape(_fmt_id(v))

def _codigo_centro(valor: Any) -> str:
    t = _fmt_id(valor).strip()
    return "-" if t == "-" else t.upper()

def _etiqueta_centro(valor: Any, sociedad: bool = False) -> str:
    codigo = _codigo_centro(valor)
    if codigo == "-": return "-"
    info = CENTROS_CATALOGO.get(codigo)
    if not info: return codigo
    base = f"{codigo} · {info['nombre']}"
    return f"{base} · {info['sociedad']}" if sociedad else base

def _opciones_centro(df: pd.DataFrame) -> list:
    if COL_CENTRO not in df.columns: return []
    return [_etiqueta_centro(c) for c in df[COL_CENTRO].dropna().astype(str).sort_values().unique().tolist()[:700]]

def _codigos_centro(etiquetas: list) -> list:
    return [str(e).split("·",1)[0].strip() for e in (etiquetas or []) if str(e).strip()]

def _opciones(df: pd.DataFrame, col: str) -> list:
    if col not in df.columns: return []
    return df[col].dropna().astype(str).sort_values().unique().tolist()[:700]

@st.cache_data(show_spinner=False)
def _cache_opciones(df: pd.DataFrame) -> dict:
    return {c: _opciones(df, c) for c in [COL_TIPO_OC, COL_ORIGEN, COL_SISTEMA, COL_GRUPO_COMPRAS, COL_ESTADO_MATCH, COL_PERF_TAT, COL_RANGO_INC]}

def _filtrar_ids(df: pd.DataFrame, col: str, txt: str) -> pd.Series:
    if col not in df.columns or not str(txt).strip(): return pd.Series(True, index=df.index)
    tokens = [t.strip().replace(".0","") for t in str(txt).replace("\n",",").replace(";"," ").replace(" ",",").split(",") if t.strip()]
    if not tokens: return pd.Series(True, index=df.index)
    serie = df[col].astype(str).str.replace(".0","",regex=False)
    m = pd.Series(False, index=df.index)
    for t in tokens: m = m | serie.str.contains(t, case=False, na=False, regex=False)
    return m

def _contiene(df: pd.DataFrame, col: str, txt: str) -> pd.Series:
    if col not in df.columns or not str(txt).strip(): return pd.Series(True, index=df.index)
    return df[col].astype(str).str.contains(str(txt).strip(), case=False, na=False, regex=False)

def _rango_num(df: pd.DataFrame, col: str, mn: Any, mx: Any) -> pd.Series:
    if col not in df.columns: return pd.Series(True, index=df.index)
    s = pd.to_numeric(df[col], errors="coerce"); m = pd.Series(True, index=df.index)
    if mn is not None: m &= s.ge(float(mn))
    if mx is not None: m &= s.le(float(mx))
    return m

def _umbral_tat(row: pd.Series) -> float:
    u = _vn(row.get(COL_UMBRAL_TAT, np.nan))
    if pd.notna(u): return u
    tipo = str(row.get(COL_TIPO_OC,"")).strip().replace(".0","")
    if tipo in ["35","45"]: return 40
    if tipo == "47": return 70
    return np.nan

def _perf_color(valor: Any) -> str:
    t = str(valor).strip().lower()
    if t == "cumple": return "green"
    if t == "no cumple": return "red"
    if t in ["en proceso","sin datos"]: return "yellow"
    if "no aplica" in t: return "gray"
    return "blue"

def _dias_color(dias: Any, umbral: Any = None) -> str:
    d = pd.to_numeric(pd.Series([dias]), errors="coerce").iloc[0]
    u = pd.to_numeric(pd.Series([umbral]), errors="coerce").iloc[0] if umbral is not None else np.nan
    if pd.isna(d) or d < 0: return "gray"
    if pd.notna(u): return "green" if d <= u else "red"
    return "green" if d == 0 else "yellow"

def _pill(txt: Any, color: str) -> str:
    return f'<span class="pill pill-{color}">{escape(_fmt(txt))}</span>'

def _texto_dias(dias: Any) -> str:
    d = _vn(dias)
    if pd.isna(d): return "Sin dato"
    di = int(round(d)); td = f"{di:,}".replace(",",".")
    if di < 0: return f"{td} días · revisar fechas"
    if di >= 30:
        m = d / 30.44
        tm = f"{m:,.1f}".replace(",","X").replace(".",",").replace("X",".")
        return f"{td} días · {tm} meses"
    return f"{td} días"

def _texto_dias_simple(dias: Any) -> str:
    d = _vn(dias)
    if pd.isna(d): return "Sin dato"
    return f"{int(round(d)):,} días".replace(",",".")

def _oc_principal(row: pd.Series) -> Any:
    oc1 = row.get(COL_OC_ME5A, np.nan)
    if _fmt_id(oc1) not in ["-","","nan","None"]: return oc1
    return row.get(COL_OC_NME, np.nan)

def _recepcion(row: pd.Series) -> str:
    for col in ["fecha_recepcion_final","Fecha recepción mercancía - NME80FN"]:
        if col in row.index and pd.notna(row.get(col, pd.NaT)): return "Recepcionado"
    return "Sin recepción"

def _fecha_etapa(row: pd.Series, col: str) -> str:
    v = row.get(col, np.nan)
    if pd.isna(v): return "Pendiente"
    if isinstance(v, pd.Timestamp): return v.strftime("%d-%m-%Y")
    return _fmt(v)

def _fecha_val(row: pd.Series, col: str):
    v = row.get(col, np.nan)
    if pd.isna(v): return pd.NaT
    return pd.to_datetime(v, errors="coerce")

def _nombre_faltante(col: str) -> str:
    return {"fecha_solicitud_final":"fecha de solicitud","fecha_liberacion_final":"fecha de liberación",
            "fecha_pedido_final":"fecha de pedido","fecha_facturacion_final":"fecha de facturación",
            "fecha_recepcion_final":"fecha de recepción"}.get(col,"fecha pendiente")

def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(); df.columns = df.columns.astype(str).str.strip(); return df

def convertir_fecha_col(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie): return pd.to_datetime(serie, errors="coerce")
    sn = pd.to_numeric(serie, errors="coerce")
    res = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")
    mn = sn.notna()
    if mn.any():
        mms = mn & sn.abs().ge(10**11); ms = mn & sn.abs().lt(10**11)
        if mms.any(): res.loc[mms] = pd.to_datetime(sn.loc[mms], unit="ms", errors="coerce")
        if ms.any():  res.loc[ms]  = pd.to_datetime(sn.loc[ms],  unit="s",  errors="coerce")
    mt = ~mn
    if mt.any(): res.loc[mt] = pd.to_datetime(serie.loc[mt], errors="coerce", dayfirst=True)
    return res

def convertir_fechas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in FECHAS_CANDIDATAS:
        if col in df.columns:
            c = convertir_fecha_col(df[col])
            if c.notna().any(): df[col] = c
    return df

@st.cache_data(show_spinner=False)
def _to_excel(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w: df.to_excel(w, index=False, sheet_name="Resultado")
    return buf.getvalue()

@st.cache_data(show_spinner=False)
def _to_parquet(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO(); df.to_parquet(buf, index=False, engine="pyarrow"); return buf.getvalue()

@st.cache_data(show_spinner=False)
def _to_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


# =========================================================
# Constructores HTML
# =========================================================
def html_cabecera_expediente(row: pd.Series) -> str:
    oc = _oc_principal(row)
    rec = _recepcion(row)
    badge_cls = "exp-badge-rec" if rec == "Recepcionado" else "exp-badge-sinr"
    return dedent(f"""
    <div class="exp-header">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;margin-bottom:14px;">
            <div>
                <div class="exp-header-title">Expediente · SolPed {_esc_id(row.get(COL_SOLPED,np.nan))}</div>
                <div class="exp-header-sub">OC {_esc_id(oc)} · Pos {_esc_id(row.get(COL_POS_SOLPED,np.nan))} · {escape(_etiqueta_centro(row.get(COL_CENTRO,np.nan)))}</div>
            </div>
            <span class="exp-badge {badge_cls}">{escape(rec)}</span>
        </div>
        <div class="exp-fields">
            <div class="exp-field"><div class="exp-field-label">Solicitud de pedido</div><div class="exp-field-value">{_esc_id(row.get(COL_SOLPED,np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Pedido / OC</div><div class="exp-field-value">{_esc_id(oc)}</div></div>
            <div class="exp-field"><div class="exp-field-label">Posición SolPed</div><div class="exp-field-value">{_esc_id(row.get(COL_POS_SOLPED,np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Centro</div><div class="exp-field-value">{escape(_etiqueta_centro(row.get(COL_CENTRO,np.nan)))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Grupo compras</div><div class="exp-field-value">{_esc(row.get(COL_GRUPO_COMPRAS,np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Material</div><div class="exp-field-value">{_esc_id(row.get(COL_MATERIAL,np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Descripción</div><div class="exp-field-value">{_esc(row.get(COL_TEXTO,np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Monto</div><div class="exp-field-value">{_esc(row.get(COL_MONTO,np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Solicitante</div><div class="exp-field-value">{_esc(row.get(COL_SOLICITANTE,np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Tipo OC</div><div class="exp-field-value">{_esc(row.get(COL_TIPO_OC,np.nan))}</div></div>
        </div>
    </div>""").strip()

def html_tat_summary(row: pd.Series) -> str:
    perf = row.get(COL_PERF_TAT, np.nan)
    dias_tat = row.get(COL_DIAS_TAT, np.nan)
    dias_inc = row.get(COL_DIAS_INC, np.nan)
    rango_inc = row.get(COL_RANGO_INC, np.nan)
    umbral = _umbral_tat(row)
    estado = str(perf).strip().lower()
    tat_txt = "En proceso" if (estado == "en proceso" and pd.isna(_vn(dias_tat))) else _texto_dias(dias_tat)
    inc_txt = "Pendiente"  if (estado == "en proceso" and pd.isna(_vn(dias_inc)))  else _texto_dias(dias_inc)
    pcolor = _perf_color(perf)
    return dedent(f"""
    <div class="tat-summary">
        <div class="tat-card tat-card-primary">
            <div class="tat-label">TAT total</div>
            <div class="tat-main">{escape(tat_txt)}</div>
            <div class="tat-sub">Desde la solicitud hasta la recepción.</div>
            <div class="tat-muted">Umbral: {escape(_texto_dias_simple(umbral))}</div>
        </div>
        <div class="tat-card">
            <div class="tat-label">Estado TAT</div>
            <div class="tat-main-sm">{_pill(perf, pcolor)}</div>
            <div class="tat-sub">Umbral aplicado: {escape(_texto_dias_simple(umbral))}</div>
        </div>
        <div class="tat-card">
            <div class="tat-label">Incumplimiento TAT</div>
            <div class="tat-main-sm">{escape(inc_txt)}</div>
            <div class="tat-sub">Rango: {_esc(rango_inc)}</div>
            <div class="tat-muted">Solo el exceso sobre el umbral TAT.</div>
        </div>
    </div>""").strip()

def html_avance(row: pd.Series) -> str:
    completadas = [(n, c, pd.notna(row.get(c, np.nan))) for n, c in ETAPAS_LINEA]
    registradas = [i for i in completadas if i[2]]
    pendientes  = [i for i in completadas if not i[2]]
    ul_n, ul_c, _ = registradas[-1] if registradas else ("Sin etapa","",False)
    sig_n, sig_c, _ = pendientes[0] if pendientes else ("Cerrado","",False)
    cerrado = len(pendientes) == 0
    fecha_inicio = _fecha_val(row, "fecha_solicitud_final")
    fecha_ul = _fecha_val(row, ul_c) if ul_c else pd.NaT
    ref = fecha_ul if cerrado else (pd.Timestamp.today().normalize() if pd.notna(fecha_inicio) else pd.NaT)
    dias_p = (ref - fecha_inicio).days if pd.notna(fecha_inicio) and pd.notna(ref) else np.nan
    umbral = _umbral_tat(row)
    dias_r = int(round(umbral - dias_p)) if pd.notna(dias_p) and pd.notna(umbral) else np.nan
    tat_txt = "Cerrado" if cerrado else "Pendiente hasta recepción"
    contra = f"{_vn(dias_r):+.0f} días vs umbral {int(umbral)}" if pd.notna(_vn(dias_r)) and pd.notna(umbral) else "Sin dato"

    # Diagnóstico
    if cerrado: diag = "El pedido ya tiene recepción registrada. TAT cerrado."
    elif pd.isna(umbral): diag = f"Falta {_nombre_faltante(sig_c)}. No se pudo determinar el umbral TAT."
    elif pd.notna(dias_r):
        if dias_r < 0: diag = f"Falta {_nombre_faltante(sig_c)}. El pedido supera el umbral de {int(umbral)} días."
        elif dias_r <= 5: diag = f"Falta {_nombre_faltante(sig_c)}. Muy cerca del umbral de {int(umbral)} días."
        else: diag = f"Falta {_nombre_faltante(sig_c)}. Quedan {int(dias_r)} días vs umbral de {int(umbral)} días."
    else: diag = f"Última etapa: {ul_n}. Siguiente: {sig_n}."

    return dedent(f"""
    <div class="avance-card">
        <div class="avance-title">Avance actual</div>
        <div class="avance-grid">
            <div class="avance-item"><div class="avance-label">Última etapa</div><div class="avance-value">{escape(ul_n)} · {escape(_fecha_etapa(row, ul_c) if ul_c else '-')}</div></div>
            <div class="avance-item"><div class="avance-label">Tiempo transcurrido</div><div class="avance-value">{escape(_texto_dias(dias_p))}</div></div>
            <div class="avance-item"><div class="avance-label">TAT total</div><div class="avance-value">{escape(tat_txt)}</div></div>
            <div class="avance-item"><div class="avance-label">Contra umbral</div><div class="avance-value">{escape(contra)}</div></div>
        </div>
        <div class="avance-note">{escape(diag)}</div>
    </div>""").strip()

def html_linea_pedido(row: pd.Series) -> str:
    completadas = [pd.notna(row.get(c, np.nan)) for _, c in ETAPAS_LINEA]
    try: ia = completadas.index(False)
    except ValueError: ia = len(ETAPAS_LINEA)-1
    partes = []
    for i, (lbl, col) in enumerate(ETAPAS_LINEA):
        ok = completadas[i]; activa = (i == ia) and not ok
        dc = "pipe-dot-ok" if ok else ("pipe-dot-active" if activa else "pipe-dot-nd")
        ic = "✓" if ok else ""
        partes.append(f'<div class="pipe-step"><div class="pipe-dot {dc}">{ic}</div><div class="pipe-label">{escape(lbl)}</div><div class="pipe-date">{escape(_fecha_etapa(row,col))}</div></div>')
        if i < len(ETAPAS_LINEA)-1:
            conn = "pipe-conn-ok" if (ok and completadas[i+1]) else ("pipe-conn-dashed" if (ok and not completadas[i+1]) else "")
            partes.append(f'<div class="pipe-conn {conn}"></div>')
    perf = row.get(COL_PERF_TAT, np.nan); dias_tat = row.get(COL_DIAS_TAT, np.nan)
    estado_txt = str(perf).strip().lower()
    tat_txt = "En proceso" if (estado_txt == "en proceso" and pd.isna(_vn(dias_tat))) else _texto_dias(dias_tat)
    return dedent(f"""
    <div class="pipe-card">
        <div class="pipe-title">Línea de pedido</div>
        <div class="pipe-line">{''.join(partes)}</div>
        <div class="pipe-note">TAT total: <strong>{escape(tat_txt)}</strong> · Estado: <strong>{_esc(perf)}</strong></div>
    </div>""").strip()

def html_diagrama_tat(row: pd.Series) -> str:
    completadas = [pd.notna(row.get(e.get("fecha"), np.nan)) for e in ETAPAS_PEDIDO]
    try: ia = completadas.index(False)
    except ValueError: ia = len(ETAPAS_PEDIDO)-1
    partes = []
    for i, etapa in enumerate(ETAPAS_PEDIDO):
        fc = etapa.get("fecha"); dc_col = etapa.get("dias"); uc = etapa.get("umbral"); pc = etapa.get("performance")
        ok = completadas[i]; perf = str(row.get(pc,"")).strip().lower() if pc else ""
        if ok and perf == "no cumple": dot,ico = "tat-flow-dot-bad","!"
        elif ok and perf in ["en proceso","sin datos"]: dot,ico = "tat-flow-dot-risk","…"
        elif ok: dot,ico = "tat-flow-dot-ok","✓"
        elif i == ia: dot,ico = "tat-flow-dot-active",""
        else: dot,ico = "tat-flow-dot-pending",""
        fecha_txt = _fecha_etapa(row, fc) if fc else "-"
        if dc_col:
            det = f"{_texto_dias(row.get(dc_col,np.nan))} · umbral {_fmt(row.get(uc,np.nan))}d · {_fmt(row.get(pc,np.nan))}"
        else: det = "Punto de inicio"
        partes.append(dedent(f"""
        <div class="tat-flow-step">
            <div class="tat-flow-dot {dot}">{escape(ico)}</div>
            <div class="tat-flow-label">{escape(str(etapa.get('titulo','')))}</div>
            <div class="tat-flow-date">{escape(fecha_txt)}</div>
            <div class="tat-flow-detail">{escape(det)}</div>
        </div>""").strip())
        if i < len(ETAPAS_PEDIDO)-1:
            conn = "tat-flow-conn-ok" if (completadas[i] and completadas[i+1]) else ("tat-flow-conn-active" if (completadas[i] and not completadas[i+1]) else "")
            partes.append(f'<div class="tat-flow-conn {conn}"></div>')
    perf = row.get(COL_PERF_TAT, np.nan); dias_tat = row.get(COL_DIAS_TAT, np.nan)
    estado = str(perf).strip().lower()
    tat_txt = "En proceso" if (estado == "en proceso" and pd.isna(_vn(dias_tat))) else _texto_dias(dias_tat)
    return dedent(f"""
    <div class="tat-flow-card">
        <div class="tat-flow-title">Etapas TAT</div>
        <div class="tat-flow">{''.join(partes)}</div>
        <div class="tat-flow-note">TAT total: <strong>{escape(tat_txt)}</strong> · Estado: <strong>{_esc(perf)}</strong></div>
    </div>""").strip()

def html_etapa_stat(etapa: str, col: str, serie: pd.Series) -> str:
    if serie is None or serie.empty:
        return ""
    serie = pd.to_numeric(serie, errors="coerce").dropna()
    if serie.empty: return ""
    vals = {
        "Min":    f"{serie.min():.1f}",
        "Media":  f"{serie.mean():.1f}",
        "Mediana":f"{serie.median():.1f}",
        "Max":    f"{serie.max():.1f}",
        "Desv":   f"{serie.std():.1f}" if len(serie) > 1 else "-",
        "N":      f"{len(serie):,}".replace(",","."),
    }
    celdas = "".join(
        f'<div class="etapa-stat-cell"><div class="etapa-stat-label">{k}</div><div class="etapa-stat-val">{v}</div></div>'
        for k, v in vals.items()
    )
    return f'<div class="etapa-stat"><div class="etapa-stat-title">{escape(etapa)}</div><div class="etapa-stat-grid">{celdas}</div></div>'

def html_label_registro(row: pd.Series) -> str:
    """Etiqueta del selector: estado TAT → IDs → centro → tiempo → descripción."""
    perf   = _fmt(row.get(COL_PERF_TAT, np.nan))
    dias   = _texto_dias(row.get(COL_DIAS_TAT, np.nan))
    solped = _fmt_id(row.get(COL_SOLPED, np.nan))
    oc     = _fmt_id(_oc_principal(row))
    pos    = _fmt_id(row.get(COL_POS_SOLPED, np.nan))
    centro = _codigo_centro(row.get(COL_CENTRO, np.nan))
    desc   = str(row.get(COL_TEXTO,""))[:50]
    return f"[{perf}] {dias}  ·  {solped} / OC {oc} / Pos {pos}  ·  {centro}  ·  {desc}"


# =========================================================
# Logo + utilidades de presentación
# =========================================================
def encontrar_logo():
    for p in LOGO_CANDIDATOS:
        if p.exists(): return p
    return None

def mostrar_logo(ancho: int = 260):
    lp = encontrar_logo()
    if lp is None: return
    suffix = lp.suffix.lower()
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"
    logo_b64 = base64.b64encode(lp.read_bytes()).decode("utf-8")
    st.markdown(
        f'<div style="width:100%;display:flex;justify-content:center;align-items:center;min-height:84px;margin:0 0 16px 0;">'
        f'<img src="data:{mime};base64,{logo_b64}" style="width:{ancho}px;max-width:80%;height:auto;display:block;" alt="Logo"></div>',
        unsafe_allow_html=True,
    )


# =========================================================
# ■  INICIO DE LA APP
# =========================================================
if "df_tat" not in st.session_state:
    st.error("Primero debes cargar el archivo base en Análisis TAT > Cargar archivo.")
    st.stop()

nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

try:
    df_raw = st.session_state["df_tat"].copy()
    df_raw = limpiar_columnas(df_raw)
    df_raw = convertir_fechas(df_raw)
    _opts  = _cache_opciones(df_raw)
except Exception as e:
    st.error("No se pudo preparar el archivo cargado."); st.exception(e); st.stop()

total_archivo = len(df_raw)
mostrar_logo()

# ── Cabecera principal ───────────────────────────────────
st.markdown("""
<div style="margin-bottom:1.2rem;">
    <div style="font-size:1.65rem;font-weight:700;color:#0f172a;letter-spacing:-0.025em;line-height:1.1;">
        Buscador SolPed / OC
    </div>
    <div style="font-size:0.88rem;color:#64748b;margin-top:5px;">
        Busca expedientes por solicitud de pedido, orden de compra o posición · visualiza su trazabilidad TAT completa
    </div>
</div>
""", unsafe_allow_html=True)


# =========================================================
# SIDEBAR — Filtros
# =========================================================
with st.sidebar:
    st.markdown(
        f'<div style="padding:0 4px 12px 4px;">'
        f'<div style="font-size:0.65rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:2px;">ARCHIVO ACTIVO</div>'
        f'<div style="font-size:0.85rem;font-weight:600;color:#e2e8f0;word-break:break-all;">{escape(nombre_archivo)}</div>'
        f'<div style="font-size:0.75rem;color:#64748b;margin-top:2px;">{total_archivo:,} registros totales</div>'
        f'</div><hr style="border:none;border-top:1px solid #1e293b;margin:0 0 14px 0;">'.replace(",","."),
        unsafe_allow_html=True,
    )
    st.markdown('<div style="font-size:0.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:10px;">Búsqueda y filtros</div>', unsafe_allow_html=True)

    with st.form("form_buscador"):
        # ── Búsqueda principal ──
        st.markdown('<div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">Búsqueda principal</div>', unsafe_allow_html=True)
        sb_solped    = st.text_input("SolPed",         placeholder="Ej: 1001973319", key="sb_solped")
        sb_oc        = st.text_input("OC / Pedido",    placeholder="Ej: 4502321875", key="sb_oc")
        sb_pos_solped= st.text_input("Posición SolPed",placeholder="Ej: 10",         key="sb_pos_solped")
        sb_pos_oc    = st.text_input("Posición OC",    placeholder="Ej: 10",         key="sb_pos_oc")
        sb_material  = st.text_input("Material",       placeholder="Ej: 20012021",   key="sb_material")
        sb_texto     = st.text_input("Descripción",    placeholder="Texto libre",    key="sb_texto")
        sb_solicitante=st.text_input("Solicitante",    placeholder="Ej: c.silva",    key="sb_solicitante")

        st.markdown('<div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;margin:10px 0 6px 0;">Filtros de clasificación</div>', unsafe_allow_html=True)
        sb_centros   = st.multiselect("Centro", _opciones_centro(df_raw), key="sb_centros")
        sb_grupo     = st.multiselect("Grupo compras", _opts.get(COL_GRUPO_COMPRAS, []), key="sb_grupo")
        sb_tipo_oc   = st.multiselect("Tipo OC",       _opts.get(COL_TIPO_OC, []),       key="sb_tipo_oc")
        sb_origen    = st.multiselect("Origen",         _opts.get(COL_ORIGEN, []),         key="sb_origen")
        sb_sistema   = st.multiselect("Sistema",        _opts.get(COL_SISTEMA, []),        key="sb_sistema")
        sb_perf_tat  = st.multiselect("Performance TAT",_opts.get(COL_PERF_TAT, []),      key="sb_perf_tat")
        sb_rango_inc = st.multiselect("Rango incumplimiento", _opts.get(COL_RANGO_INC, []),key="sb_rango_inc")
        sb_estado_m  = st.multiselect("Estado match",  _opts.get(COL_ESTADO_MATCH, []),   key="sb_estado_m")

        st.markdown('<div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;margin:10px 0 6px 0;">Rangos numéricos</div>', unsafe_allow_html=True)
        sb_tat_min_on = st.checkbox("Activar TAT mínimo", key="sb_tat_min_on")
        sb_tat_min    = st.number_input("TAT mínimo (días)", value=0, step=1, disabled=not sb_tat_min_on, key="sb_tat_min")
        sb_tat_max_on = st.checkbox("Activar TAT máximo", key="sb_tat_max_on")
        sb_tat_max    = st.number_input("TAT máximo (días)", value=9999, step=1, disabled=not sb_tat_max_on, key="sb_tat_max")
        sb_monto_min_on=st.checkbox("Activar monto mínimo", key="sb_monto_min_on")
        sb_monto_min  = st.number_input("Monto mínimo", value=0.0, step=1000.0, disabled=not sb_monto_min_on, key="sb_monto_min")
        sb_monto_max_on=st.checkbox("Activar monto máximo", key="sb_monto_max_on")
        sb_monto_max  = st.number_input("Monto máximo", value=0.0, step=1000.0, disabled=not sb_monto_max_on, key="sb_monto_max")

        st.markdown('<div style="font-size:0.68rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.06em;margin:10px 0 6px 0;">Opciones adicionales</div>', unsafe_allow_html=True)
        sb_solo_inc   = st.checkbox("Solo incumplimiento TAT", key="sb_solo_inc")
        sb_solo_incons= st.checkbox("Solo fechas inconsistentes", key="sb_solo_incons")
        sb_limite     = st.number_input("Filas en tabla", min_value=25, max_value=5000, value=300, step=25, key="sb_limite")

        # ── Filtro de fecha ──
        _fecha_cols = [c for c in FECHAS_CANDIDATAS if c in df_raw.columns and pd.api.types.is_datetime64_any_dtype(df_raw[c])]
        if _fecha_cols:
            sb_fecha_on = st.checkbox("Filtrar por fecha", key="sb_fecha_on")
            sb_fecha_col= st.selectbox("Columna de fecha", _fecha_cols, disabled=not sb_fecha_on, key="sb_fecha_col")
            _fmin = df_raw[sb_fecha_col].min() if sb_fecha_on else None
            _fmax = df_raw[sb_fecha_col].max() if sb_fecha_on else None
            if _fmin and _fmax and pd.notna(_fmin) and pd.notna(_fmax):
                sb_fecha_desde = st.date_input("Desde", value=_fmin.date(), disabled=not sb_fecha_on, key="sb_fecha_desde")
                sb_fecha_hasta = st.date_input("Hasta", value=_fmax.date(), disabled=not sb_fecha_on, key="sb_fecha_hasta")
            else:
                sb_fecha_on = False; sb_fecha_desde = None; sb_fecha_hasta = None
        else:
            sb_fecha_on = False; sb_fecha_col = None; sb_fecha_desde = None; sb_fecha_hasta = None

        st.form_submit_button("🔍  Buscar / Aplicar filtros", use_container_width=True, type="primary")

    st.markdown('<hr style="border:none;border-top:1px solid #1e293b;margin:16px 0 12px 0;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.68rem;color:#475569;text-align:center;padding-bottom:8px;">Buscador SolPed / OC</div>', unsafe_allow_html=True)


# =========================================================
# APLICAR FILTROS
# =========================================================
mask = pd.Series(True, index=df_raw.index)
mask &= _filtrar_ids(df_raw, COL_SOLPED,    st.session_state.get("sb_solped",""))
mask &= (_filtrar_ids(df_raw, COL_OC_ME5A,  st.session_state.get("sb_oc","")) |
         _filtrar_ids(df_raw, COL_OC_NME,   st.session_state.get("sb_oc","")))
mask &= _filtrar_ids(df_raw, COL_POS_SOLPED,st.session_state.get("sb_pos_solped",""))
mask &= _filtrar_ids(df_raw, COL_POS_OC,    st.session_state.get("sb_pos_oc",""))
mask &= _filtrar_ids(df_raw, COL_MATERIAL,  st.session_state.get("sb_material",""))
mask &= _contiene(df_raw, COL_TEXTO,        st.session_state.get("sb_texto",""))
mask &= _contiene(df_raw, COL_SOLICITANTE,  st.session_state.get("sb_solicitante",""))

_centros_sel = _codigos_centro(st.session_state.get("sb_centros",[]))
if _centros_sel and COL_CENTRO in df_raw.columns:
    mask &= df_raw[COL_CENTRO].astype(str).isin(_centros_sel)

for _col, _key in [(COL_GRUPO_COMPRAS,"sb_grupo"),(COL_TIPO_OC,"sb_tipo_oc"),(COL_ORIGEN,"sb_origen"),
                    (COL_SISTEMA,"sb_sistema"),(COL_PERF_TAT,"sb_perf_tat"),(COL_RANGO_INC,"sb_rango_inc"),(COL_ESTADO_MATCH,"sb_estado_m")]:
    _sel = st.session_state.get(_key,[])
    if _sel and _col in df_raw.columns: mask &= df_raw[_col].astype(str).isin(_sel)

mask &= _rango_num(df_raw, COL_DIAS_TAT, st.session_state.get("sb_tat_min",0) if st.session_state.get("sb_tat_min_on",False) else None,
                                          st.session_state.get("sb_tat_max",9999) if st.session_state.get("sb_tat_max_on",False) else None)
mask &= _rango_num(df_raw, COL_MONTO,    st.session_state.get("sb_monto_min",0.0) if st.session_state.get("sb_monto_min_on",False) else None,
                                          st.session_state.get("sb_monto_max",0.0) if st.session_state.get("sb_monto_max_on",False) else None)

if st.session_state.get("sb_solo_inc",False) and COL_INC_TAT in df_raw.columns:
    mask &= df_raw[COL_INC_TAT].eq(True)
if st.session_state.get("sb_solo_incons",False) and COL_FECHAS_INCONS in df_raw.columns:
    mask &= df_raw[COL_FECHAS_INCONS].eq(True)

if st.session_state.get("sb_fecha_on",False) and sb_fecha_col and sb_fecha_desde and sb_fecha_hasta:
    mask &= df_raw[sb_fecha_col].between(pd.Timestamp(sb_fecha_desde), pd.Timestamp(sb_fecha_hasta) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1), inclusive="both")

df_filtrado = df_raw.loc[mask].copy()
n_filtrado  = len(df_filtrado)
n_limite    = int(st.session_state.get("sb_limite", 300))


# =========================================================
# KPIs rápidos
# =========================================================
_serie_perf = df_filtrado[COL_PERF_TAT].fillna("").astype(str).str.strip().str.lower() if (COL_PERF_TAT in df_filtrado.columns and n_filtrado > 0) else pd.Series(dtype=str)
_n_cumple    = int(_serie_perf.eq("cumple").sum())
_n_no_cumple = int(_serie_perf.eq("no cumple").sum())
_n_eval      = _n_cumple + _n_no_cumple
_pct_cumple  = _n_cumple    / _n_eval * 100 if _n_eval else 0
_pct_nc      = _n_no_cumple / _n_eval * 100 if _n_eval else 0

mk1, mk2, mk3, mk4 = st.columns(4)
mk1.metric("Archivo total",      _fmt_int(total_archivo))
mk2.metric("Resultados filtrados", _fmt_int(n_filtrado), f"{n_filtrado/total_archivo*100:.1f}% del archivo" if total_archivo else "")
mk3.metric("% Cumplimiento TAT",  _fmt_pct(_pct_cumple),  f"{_fmt_int(_n_cumple)} de {_fmt_int(_n_eval)} evaluados")
mk4.metric("% Incumplimiento TAT",_fmt_pct(_pct_nc),      f"{_fmt_int(_n_no_cumple)} de {_fmt_int(_n_eval)} evaluados")

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)


# =========================================================
# PESTAÑAS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍  Resultados y selector",
    "📋  Expediente TAT",
    "📊  Estadística",
    "⬇  Descarga y datos",
])


# ══════════════════════════════════════════════════════════
# TAB 1 — RESULTADOS Y SELECTOR
# ══════════════════════════════════════════════════════════
with tab1:
    if df_filtrado.empty:
        st.warning("No hay resultados con los filtros aplicados. Ajusta los criterios en la barra lateral.")
    else:
        st.markdown("#### Seleccionar registro")

        n_sel = min(5000, n_filtrado)
        _pct_sel  = n_sel    / total_archivo * 100 if total_archivo else 0
        _pct_filt = n_filtrado/ total_archivo * 100 if total_archivo else 0

        # Contexto de cobertura
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin:0.5rem 0 1rem 0;">
                <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:13px 16px;">
                    <div style="font-size:0.65rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Total en archivo</div>
                    <div style="font-size:1.35rem;font-weight:800;color:#0f172a;">{total_archivo:,}</div>
                    <div style="font-size:0.78rem;color:#94a3b8;margin-top:2px;">registros cargados</div>
                </div>
                <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:12px;padding:13px 16px;">
                    <div style="font-size:0.65rem;font-weight:700;color:#1e40af;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Resultado filtrado</div>
                    <div style="font-size:1.35rem;font-weight:800;color:#1e40af;">{n_filtrado:,}
                        <span style="font-size:0.85rem;font-weight:600;"> ({_pct_filt:.1f}%)</span>
                    </div>
                    <div style="font-size:0.78rem;color:#3b82f6;margin-top:2px;">registros que cumplen los filtros</div>
                </div>
                <div style="background:{'#fefce8' if n_sel < n_filtrado else '#f0fdf4'};border:1px solid {'#fde68a' if n_sel < n_filtrado else '#bbf7d0'};border-radius:12px;padding:13px 16px;">
                    <div style="font-size:0.65rem;font-weight:700;color:#{'854d0e' if n_sel < n_filtrado else '166534'};text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">En el selector</div>
                    <div style="font-size:1.35rem;font-weight:800;color:#{'854d0e' if n_sel < n_filtrado else '166534'};">{n_sel:,}
                        <span style="font-size:0.85rem;font-weight:600;"> ({_pct_sel:.1f}%)</span>
                    </div>
                    <div style="font-size:0.78rem;color:#{'ca8a04' if n_sel < n_filtrado else '16a34a'};margin-top:2px;">{'Limitado · usa filtros para acotar más' if n_sel < n_filtrado else 'Todos los resultados disponibles'}</div>
                </div>
            </div>
            """.replace(",","."),
            unsafe_allow_html=True,
        )

        _labels_t1 = {idx: html_label_registro(row) for idx, row in df_filtrado.head(5000).iterrows()}
        _opciones_t1 = list(_labels_t1.keys())

        idx_sel = st.selectbox(
            f"Registro ({n_sel:,} en selector · {n_filtrado:,} en filtrado · {total_archivo:,} en archivo)".replace(",","."),
            _opciones_t1,
            format_func=lambda i: _labels_t1.get(i, str(i)),
            key="idx_sel_t1",
        )
        st.session_state["buscador_idx_sel"] = idx_sel

        row_sel = df_filtrado.loc[idx_sel]

        # ── Vista previa del registro ────────────────────
        st.markdown("#### Vista previa del registro seleccionado")
        st.markdown(html_cabecera_expediente(row_sel), unsafe_allow_html=True)

        # ── Resumen rápido de distribución ──────────────
        st.markdown("#### Distribución del resultado filtrado")
        st.caption("Distribución del performance TAT en los registros que cumplen los filtros actuales.")

        if COL_PERF_TAT in df_filtrado.columns:
            _dist = (
                df_filtrado[COL_PERF_TAT].fillna("Sin dato").astype(str)
                .value_counts().reset_index()
            )
            _dist.columns = ["Performance TAT", "Cantidad"]
            _dist["% del filtrado"] = (_dist["Cantidad"] / n_filtrado * 100).round(1)
            _PERF_COLORS = {
                "cumple":     ("#dcfce7","#bbf7d0","#166534"),
                "no cumple":  ("#fee2e2","#fecaca","#991b1b"),
                "en proceso": ("#fef9c3","#fde68a","#854d0e"),
                "sin datos":  ("#f8fafc","#e2e8f0","#475569"),
            }
            _dist_html = ""
            _acum = 0
            for _, dr in _dist.iterrows():
                _key_perf = str(dr["Performance TAT"]).strip().lower()
                _bg, _brd, _cl = _PERF_COLORS.get(_key_perf, ("#f8fafc","#e2e8f0","#475569"))
                _p = float(dr["% del filtrado"]); _acum += int(dr["Cantidad"])
                _pa = _acum / n_filtrado * 100 if n_filtrado else 0
                _dist_html += (
                    f'<div style="display:grid;grid-template-columns:2fr 70px 70px 82px 1fr;align-items:center;gap:10px;'
                    f'padding:9px 14px;background:{_bg};border:1px solid {_brd};border-radius:11px;margin-bottom:5px;">'
                    f'<div style="font-size:0.88rem;font-weight:600;color:{_cl};">{escape(str(dr["Performance TAT"]))}</div>'
                    f'<div style="font-size:0.95rem;font-weight:800;color:{_cl};text-align:right;">{int(dr["Cantidad"]):,}</div>'
                    f'<div style="font-size:0.84rem;color:#64748b;text-align:right;">{_p:.1f}%</div>'
                    f'<div style="font-size:0.82rem;color:#94a3b8;text-align:right;">{_pa:.1f}% acum.</div>'
                    f'<div style="background:#e2e8f0;border-radius:99px;height:7px;overflow:hidden;">'
                    f'<div style="background:{_cl};width:{max(2,_p):.1f}%;height:100%;border-radius:99px;opacity:0.65;"></div>'
                    f'</div></div>'
                ).replace(",",".")
            _dist_html += (
                f'<div style="display:grid;grid-template-columns:2fr 70px 70px 82px 1fr;align-items:center;gap:10px;'
                f'padding:9px 14px;background:#f1f5f9;border:2px solid #94a3b8;border-radius:11px;">'
                f'<div style="font-size:0.88rem;font-weight:800;color:#0f172a;">TOTAL FILTRADO</div>'
                f'<div style="font-size:0.95rem;font-weight:900;color:#0f172a;text-align:right;">{n_filtrado:,}</div>'
                f'<div style="font-size:0.84rem;font-weight:700;color:#334155;text-align:right;">100%</div>'
                f'<div></div><div></div></div>'
            ).replace(",",".")
            st.markdown(f'<div style="margin:0.5rem 0 0.5rem 0;">{_dist_html}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# TAB 2 — EXPEDIENTE TAT
# ══════════════════════════════════════════════════════════
with tab2:
    _idx = st.session_state.get("buscador_idx_sel")
    if df_filtrado.empty or _idx is None or _idx not in df_filtrado.index:
        st.info("Selecciona un registro en la pestaña «Resultados y selector» para ver su expediente.")
    else:
        row = df_filtrado.loc[_idx]
        st.markdown("#### Trazabilidad TAT del registro seleccionado")
        st.markdown(html_tat_summary(row),    unsafe_allow_html=True)
        st.markdown(html_avance(row),          unsafe_allow_html=True)
        st.markdown(html_linea_pedido(row),    unsafe_allow_html=True)
        st.markdown(html_diagrama_tat(row),    unsafe_allow_html=True)

        with st.expander("Registro completo (todos los campos)", expanded=False):
            reg = row.to_frame(name="Valor").reset_index().rename(columns={"index":"Campo"})
            reg.loc[reg["Campo"].eq(COL_CENTRO), "Valor"] = reg.loc[reg["Campo"].eq(COL_CENTRO), "Valor"].apply(_etiqueta_centro)
            reg["Valor"] = reg["Valor"].apply(_fmt)
            st.dataframe(reg, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════
# TAB 3 — ESTADÍSTICA
# ══════════════════════════════════════════════════════════
with tab3:
    if df_filtrado.empty:
        st.info("Sin resultados para calcular estadísticas.")
    else:
        st.markdown("#### Estadísticas descriptivas por etapa")
        st.caption("Min, Media, Mediana, Max, Desv. estándar y N de días por etapa — calculados sobre el filtrado activo.")

        _etapas_stat = [
            ("Liberación SolPed","dias_liberacion_solped"),
            ("Comprador",        "dias_comprador"),
            ("Proveedor",        "dias_proveedor"),
            ("Logística",        "dias_logistica"),
            ("TAT Total",        COL_DIAS_TAT),
        ]
        _stat_html = ""
        for _en, _ec in _etapas_stat:
            if _ec in df_filtrado.columns:
                _stat_html += html_etapa_stat(_en, _ec, df_filtrado[_ec])
        if _stat_html:
            st.markdown(_stat_html, unsafe_allow_html=True)
        else:
            st.info("No se encontraron columnas de duración de etapas en el archivo.")

        st.markdown("---")
        st.markdown("#### Distribuciones del resultado filtrado")

        _dc1, _dc2, _dc3, _dc4 = st.columns(4)

        def _dist_tab(df_b, col, nombre, col_st):
            with col_st:
                st.markdown(f"**{nombre}**")
                if col not in df_b.columns or df_b.empty:
                    st.info("Sin datos."); return
                t = df_b[col].fillna("Sin dato").astype(str)
                if col == COL_CENTRO: t = t.apply(_etiqueta_centro)
                d = t.value_counts().reset_index(); d.columns = [nombre,"Cantidad"]
                d["% total"] = (d["Cantidad"] / len(df_b) * 100).round(1)
                st.dataframe(d, use_container_width=True, hide_index=True)
                if not d.empty: st.bar_chart(d.set_index(nombre)["% total"])

        _dist_tab(df_filtrado, COL_PERF_TAT,  "Performance TAT",    _dc1)
        _dist_tab(df_filtrado, COL_RANGO_INC, "Rango incumplimiento",_dc2)
        _dist_tab(df_filtrado, COL_ESTADO_MATCH,"Estado match",      _dc3)
        _dist_tab(df_filtrado, COL_CENTRO,    "Centro",              _dc4)


# ══════════════════════════════════════════════════════════
# TAB 4 — DESCARGA Y DATOS
# ══════════════════════════════════════════════════════════
with tab4:
    st.markdown("#### Tabla de resultados filtrados")
    st.markdown(
        f'<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;padding:12px 16px;margin-bottom:1rem;'
        f'display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">'
        f'<div>'
        f'<div style="font-size:0.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:3px;">Vista previa</div>'
        f'<div style="font-size:1.05rem;font-weight:700;color:#0f172a;">Mostrando <span style="color:#2563eb;">{min(n_limite,n_filtrado):,}</span> de <span style="color:#0f172a;">{n_filtrado:,}</span> registros filtrados</div>'
        f'<div style="font-size:0.8rem;color:#64748b;margin-top:2px;">{n_filtrado - min(n_limite,n_filtrado):,} registros adicionales disponibles en la descarga</div>'
        f'</div>'
        f'<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:8px 14px;text-align:center;">'
        f'<div style="font-size:0.68rem;font-weight:700;color:#1e40af;text-transform:uppercase;letter-spacing:0.05em;">Total archivo</div>'
        f'<div style="font-size:1.2rem;font-weight:700;color:#1e40af;">{total_archivo:,}</div>'
        f'</div></div>'.replace(",","."),
        unsafe_allow_html=True,
    )

    # Selector de columnas
    _cols_base = [c for c in COLUMNAS_TABLA_BASE if c in df_filtrado.columns]
    _cols_extra = []
    for etapa in ETAPAS_PEDIDO:
        for _fc in [etapa.get("fecha"), etapa.get("dias"), etapa.get("umbral"), etapa.get("performance")]:
            if _fc and _fc in df_filtrado.columns and _fc not in _cols_base and _fc not in _cols_extra:
                _cols_extra.append(_fc)

    _todas_cols = st.checkbox("Mostrar todas las columnas", value=False, key="t4_todas_cols")
    _cols_vis = st.multiselect(
        "Columnas visibles",
        options=df_filtrado.columns.tolist(),
        default=df_filtrado.columns.tolist() if _todas_cols else _cols_base + _cols_extra,
        key="t4_cols_vis",
    )

    if _cols_vis:
        _tabla_vis = df_filtrado[_cols_vis].head(n_limite).copy()
        if COL_CENTRO in _tabla_vis.columns:
            _tabla_vis[COL_CENTRO] = _tabla_vis[COL_CENTRO].apply(_etiqueta_centro)

        def _estilo_tabla(df_t):
            def _cp(v):
                t = str(v).strip().lower()
                if t == "cumple":      return "background-color:#dcfce7;color:#166534;font-weight:700;"
                if t == "no cumple":   return "background-color:#fee2e2;color:#991b1b;font-weight:700;"
                if t in ["en proceso","sin datos"]: return "background-color:#fef9c3;color:#854d0e;font-weight:700;"
                if "no aplica" in t:   return "background-color:#f1f5f9;color:#475569;font-weight:700;"
                return ""
            def _ci(v):
                t = str(v).strip().lower()
                if t == "sin incumplimiento": return "background-color:#dcfce7;color:#166534;font-weight:700;"
                if t in ["0-5 días","1-5 días","6-15 días"]: return "background-color:#fef9c3;color:#854d0e;font-weight:700;"
                if t in ["16-30 días","mayor a un mes"]:     return "background-color:#fee2e2;color:#991b1b;font-weight:700;"
                return ""
            s = df_t.style
            for c in df_t.columns:
                if c.startswith("performance_") or c == COL_PERF_TAT: s = s.map(_cp, subset=[c])
                if c == COL_RANGO_INC: s = s.map(_ci, subset=[c])
            return s

        st.dataframe(_estilo_tabla(_tabla_vis), use_container_width=True, hide_index=True)
    else:
        st.info("Selecciona al menos una columna.")

    st.markdown("#### Descargas")
    st.caption("Las descargas incluyen la totalidad de los registros filtrados, no solo las filas visibles.")
    _d1, _d2, _d3 = st.columns(3)
    with _d1:
        st.download_button("⬇ CSV filtrado", data=_to_csv(df_filtrado), file_name="buscador_solped_oc_filtrado.csv", mime="text/csv", use_container_width=True)
    with _d2:
        try:
            st.download_button("⬇ Parquet filtrado", data=_to_parquet(df_filtrado), file_name="buscador_solped_oc_filtrado.parquet", mime="application/octet-stream", use_container_width=True)
        except Exception:
            st.button("Parquet no disponible", disabled=True, use_container_width=True)
    with _d3:
        if n_filtrado <= 250_000:
            st.download_button("⬇ Excel filtrado", data=_to_excel(df_filtrado), file_name="buscador_solped_oc_filtrado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.button("Excel no disponible (>250k filas)", disabled=True, use_container_width=True)
            st.caption("Excel se desactiva sobre 250.000 filas. Usa CSV.")

    with st.expander("Columnas disponibles en el archivo", expanded=False):
        st.write(df_raw.columns.tolist())
