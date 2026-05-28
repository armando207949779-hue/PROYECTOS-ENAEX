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
    {"titulo": "1. Solicitud", "fecha": "fecha_solicitud_final", "dias": None, "umbral": None, "performance": None, "nota": "Inicio SolPed"},
    {"titulo": "2. Liberación SolPed", "fecha": "fecha_liberacion_final", "dias": "dias_liberacion_solped", "umbral": "umbral_liberacion_solped", "performance": "performance_liberacion_solped", "nota": "Solicitud → Liberación"},
    {"titulo": "3. Comprador", "fecha": "fecha_pedido_final", "dias": "dias_comprador", "umbral": "umbral_comprador", "performance": "performance_comprador", "nota": "Liberación → Pedido"},
    {"titulo": "4. Proveedor", "fecha": "fecha_facturacion_final", "dias": "dias_proveedor", "umbral": "umbral_proveedor", "performance": "performance_proveedor", "nota": "Pedido → Facturación"},
    {"titulo": "5. Logística", "fecha": "fecha_recepcion_final", "dias": "dias_logistica", "umbral": "umbral_logistica", "performance": "performance_logistica", "nota": "Facturación → Recepción"},
    {"titulo": "6. TAT Total", "fecha": "fecha_recepcion_final", "dias": "dias_tat_total", "umbral": "umbral_tat_total", "performance": "performance_tat_total", "nota": "Solicitud → Recepción"},
]

ETAPAS_LINEA_PEDIDO = [
    ("Solicitud", "fecha_solicitud_final"),
    ("Liberación", "fecha_liberacion_final"),
    ("Pedido", "fecha_pedido_final"),
    ("Facturación", "fecha_facturacion_final"),
    ("Recepción", "fecha_recepcion_final"),
]

ETAPAS_ALERTA = [
    {"nombre": "Liberación SolPed", "fecha_inicio": "fecha_solicitud_final", "fecha_fin": "fecha_liberacion_final", "dias": "dias_liberacion_solped", "umbral": "umbral_liberacion_solped", "performance": "performance_liberacion_solped", "responsable": "Solicitante / Aprobador"},
    {"nombre": "Comprador", "fecha_inicio": "fecha_liberacion_final", "fecha_fin": "fecha_pedido_final", "dias": "dias_comprador", "umbral": "umbral_comprador", "performance": "performance_comprador", "responsable": "Compras"},
    {"nombre": "Proveedor", "fecha_inicio": "fecha_pedido_final", "fecha_fin": "fecha_facturacion_final", "dias": "dias_proveedor", "umbral": "umbral_proveedor", "performance": "performance_proveedor", "responsable": "Proveedor"},
    {"nombre": "Logística", "fecha_inicio": "fecha_facturacion_final", "fecha_fin": "fecha_recepcion_final", "dias": "dias_logistica", "umbral": "umbral_logistica", "performance": "performance_logistica", "responsable": "Logística / Bodega"},
]

BUCKETS_DIAS_VENCIMIENTO = ["Vencido", "1 día", "2 días", "7 días", "+7 días", "Sin datos"]

CENTROS_NOMBRES = {
    "E002": "Prillex", "E021": "CM-Enaex Servicios", "E024": "Río Loa", "E025": "Planta La Chimba",
    "E026": "Teatinos", "E029": "Chuquicamata", "E030": "El Tesoro", "E031": "La Escondida",
    "E032": "Loma Bayas", "E033": "Los Pelambres", "E034": "Los Sauces", "E035": "Mantos Blancos",
    "E036": "Michilla", "E037": "RT", "E038": "El Soldado", "E039": "Polpaico", "E040": "Peldehue",
    "E041": "Esperanza", "E042": "Gaby", "E044": "Atacama Kozan", "E045": "Franke",
    "E046": "Manto Verde", "E047": "Polvorín Copiapó", "E069": "Guanaco", "E071": "Teniente",
    "E076": "Mejillones", "E077": "Ministro Hales", "E078": "Sierra Gorda",
    "E079": "Planta Quebrada Blanca", "E081": "Chuqui Subte", "E086": "Antucoya",
    "E087": "Alto Maipo", "E088": "Encuentro", "E089": "Cerro Colorado", "E090": "Collahuasi",
    "E091": "Romeral", "E095": "Planta Andina", "E097": "Andina", "E099": "Salvador",
    "E103": "Zaldívar", "E104": "Salares Norte", "E105": "Los Colorados", "E106": "Cerro N.N.",
    "E107": "Pleito", "E108": "Plasma Enaex Servicios", "E109": "Carola",
    "E110": "Alto Hospicio SKC Enaex Servicios", "E113": "Copiapó SKC Enaex Servicios",
    "E114": "FullRPM Nogales Enaex Servicios", "E082": "Nittra Casa Matriz",
    "E083": "Nittra Prillex", "E084": "Nittra Paine", "E101": "Plasma",
    "E003": "Planta Río Loa", "E009": "Planta Chuquicamata", "E020": "Planta Polpaico",
    "E057": "Esperanza", "E102": "SCL Bodega Arriendo", "E043": "El Peñón Subte",
    "E115": "Enaex SKC ING", "E027": "Faena Teniente Rajo", "E052": "Faena Spence",
}


# =========================================================
# CSS Mejorado — Sistema de diseño limpio y profesional
# =========================================================
ESTILOS_GLOBALES = """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=DM+Mono:wght@400;500&display=swap');

/* ── Reset y base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── Layout principal ── */
.block-container {
    padding: 1.5rem 2rem 2rem 2rem !important;
    max-width: 1600px !important;
}

/* ── Sidebar refinada ── */
section[data-testid="stSidebar"] {
    background: #0f172a !important;
    border-right: 1px solid #1e293b;
}

section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

section[data-testid="stSidebar"] .stMarkdown h1,
section[data-testid="stSidebar"] .stMarkdown h2,
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #f8fafc !important;
    font-weight: 700 !important;
}

section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stMultiSelect label,
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stNumberInput label {
    color: #94a3b8 !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button {
    background: #2563eb !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    width: 100% !important;
    padding: 0.65rem !important;
    transition: background 0.15s ease !important;
}

section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button:hover {
    background: #1d4ed8 !important;
}

/* ── Pestañas ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f1f5f9;
    padding: 5px;
    border-radius: 14px;
    border: none;
    margin-bottom: 1.5rem;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 10px !important;
    padding: 0.55rem 1.1rem !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #64748b !important;
    background: transparent !important;
    border: none !important;
    transition: all 0.15s ease !important;
}

.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #0f172a !important;
    box-shadow: 0 1px 4px rgba(15,23,42,0.10) !important;
}

/* ── Métricas ── */
div[data-testid="metric-container"] {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 14px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}

div[data-testid="metric-container"] label {
    color: #64748b !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
}

div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
}

/* ── Títulos ── */
h1 { font-size: 1.75rem !important; font-weight: 700 !important; letter-spacing: -0.02em !important; color: #0f172a !important; }
h2 { font-size: 1.25rem !important; font-weight: 700 !important; letter-spacing: -0.01em !important; color: #0f172a !important; }
h3 { font-size: 1.05rem !important; font-weight: 600 !important; color: #1e293b !important; margin-top: 0.75rem !important; }
h4 { font-size: 0.92rem !important; font-weight: 600 !important; color: #334155 !important; }

/* ── Expanders ── */
.streamlit-expanderHeader {
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    color: #334155 !important;
    padding: 0.65rem 1rem !important;
}

.streamlit-expanderContent {
    border: 1px solid #e2e8f0 !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
    padding: 1rem !important;
}

/* ── Botones de descarga ── */
[data-testid="stDownloadButton"] button {
    background: #f8fafc !important;
    color: #334155 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}

[data-testid="stDownloadButton"] button:hover {
    background: #e2e8f0 !important;
    border-color: #cbd5e1 !important;
}

/* ── Info / Warning / Success ── */
div[data-testid="stInfo"],
div[data-testid="stWarning"],
div[data-testid="stSuccess"] {
    border-radius: 12px !important;
    font-size: 0.9rem !important;
    font-weight: 500 !important;
}

/* ── Dataframes ── */
[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #e2e8f0 !important;
}

/* ── Caption ── */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    font-weight: 400 !important;
}

/* ── Scrollbar personalizada ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #f1f5f9; border-radius: 99px; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

/* ── Tarjetas de sección ── */
.tat-section-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 20px 22px;
    margin: 0.75rem 0;
    box-shadow: 0 1px 4px rgba(15,23,42,0.04);
}

/* ── Semáforo / estado global ── */
.semaforo-critico  { border-left: 5px solid #dc2626 !important; }
.semaforo-atencion { border-left: 5px solid #f97316 !important; }
.semaforo-datos    { border-left: 5px solid #ca8a04 !important; }
.semaforo-ok       { border-left: 5px solid #16a34a !important; }
.semaforo-nd       { border-left: 5px solid #64748b !important; }

/* ── Badges de estado ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.73rem;
    font-weight: 700;
    letter-spacing: 0.03em;
    white-space: nowrap;
}
.badge-red    { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
.badge-orange { background: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; }
.badge-yellow { background: #fef9c3; color: #854d0e; border: 1px solid #fde68a; }
.badge-green  { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
.badge-blue   { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
.badge-gray   { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }

/* ── Alerta de urgencia ── */
.alerta-urgente {
    border-radius: 14px;
    padding: 15px 18px;
    margin: 12px 0;
    font-weight: 600;
    font-size: 0.9rem;
    display: flex;
    align-items: center;
    gap: 10px;
}
.alerta-roja    { background: #fef2f2; border: 1px solid #fca5a5; border-left: 5px solid #dc2626; color: #7f1d1d; }
.alerta-naranja { background: #fff7ed; border: 1px solid #fdba74; border-left: 5px solid #f97316; color: #7c2d12; }

/* ── Pipeline de etapas ── */
.pipe-card {
    background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
    border: 1px solid #bbf7d0;
    border-radius: 18px;
    padding: 18px 20px 16px;
    margin: 0.75rem 0;
}
.pipe-title {
    font-size: 0.78rem;
    font-weight: 700;
    color: #14532d;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 14px;
}
.pipe-line { display: flex; align-items: flex-start; width: 100%; }
.pipe-step { flex: 0 0 108px; text-align: center; min-width: 0; }
.pipe-dot {
    width: 48px; height: 48px;
    border-radius: 50%;
    margin: 0 auto 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1.4rem;
    box-sizing: border-box;
}
.pipe-dot-ok     { background: #22c55e; color: #fff; border: 3px solid #22c55e; }
.pipe-dot-active { background: #fff; color: #15803d; border: 5px solid #22c55e; }
.pipe-dot-nd     { background: #fff; color: #94a3b8; border: 4px solid #cbd5e1; }
.pipe-label { font-size: 0.78rem; font-weight: 700; color: #1f2937; text-transform: uppercase; }
.pipe-date  { color: #64748b; font-size: 0.72rem; margin-top: 3px; overflow-wrap: anywhere; }
.pipe-conn  { flex: 1; height: 5px; min-width: 24px; margin-top: 22px; border-radius: 99px; background: #cbd5e1; }
.pipe-conn-ok     { background: #22c55e; }
.pipe-conn-dashed { background: repeating-linear-gradient(90deg,#22c55e 0 14px,transparent 14px 22px); }
.pipe-note { color: #475569; font-size: 0.82rem; line-height: 1.4; margin-top: 12px; }

/* ── TAT flow ── */
.tat-card {
    background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    border: 1px solid #dbeafe;
    border-radius: 18px;
    padding: 18px 20px 16px;
    margin: 0.75rem 0;
}
.tat-card-title {
    font-size: 0.78rem; font-weight: 700;
    color: #1e3a8a;
    text-transform: uppercase; letter-spacing: 0.06em;
    margin-bottom: 14px;
}
.tat-flow { display: flex; align-items: stretch; width: 100%; overflow-x: auto; padding-bottom: 4px; }
.tat-step { flex: 0 0 142px; text-align: center; min-width: 0; }
.tat-dot {
    width: 48px; height: 48px; border-radius: 50%;
    margin: 0 auto 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 1rem;
    box-sizing: border-box;
}
.tat-dot-ok     { background: #22c55e; color: #fff; border: 3px solid #22c55e; }
.tat-dot-bad    { background: #fef2f2; color: #991b1b; border: 4px solid #ef4444; }
.tat-dot-risk   { background: #fff7ed; color: #c2410c; border: 4px solid #fb923c; }
.tat-dot-active { background: #fff; color: #1d4ed8; border: 5px solid #3b82f6; }
.tat-dot-nd     { background: #fff; color: #94a3b8; border: 4px solid #cbd5e1; }
.tat-step-label  { font-size: 0.75rem; font-weight: 700; color: #1f2937; text-transform: uppercase; }
.tat-step-date   { color: #475569; font-size: 0.7rem; line-height: 1.22; margin-top: 3px; overflow-wrap: anywhere; }
.tat-step-detail { color: #334155; font-size: 0.7rem; line-height: 1.22; margin-top: 4px; }
.tat-conn        { flex: 1; height: 5px; min-width: 28px; margin-top: 22px; border-radius: 99px; background: #cbd5e1; }
.tat-conn-ok     { background: #22c55e; }
.tat-conn-active { background: repeating-linear-gradient(90deg,#3b82f6 0 14px,transparent 14px 22px); }
.tat-note { color: #475569; font-size: 0.82rem; line-height: 1.4; margin-top: 12px; }

/* ── Etapas de estado ── */
.stages-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(130px, 1fr));
    gap: 8px;
    margin-top: 0.5rem;
}
.stage {
    border-radius: 14px;
    padding: 12px 13px;
    border: 1px solid #e5e7eb;
    min-height: 140px;
    position: relative;
}
.stage::after { content: "→"; position: absolute; right: -7px; top: 50%; transform: translateY(-50%); color: #94a3b8; font-weight: 700; z-index: 2; }
.stage:last-child::after { content: ""; }
.stage-green  { background: #f0fdf4; border-color: #bbf7d0; }
.stage-red    { background: #fef2f2; border-color: #fecaca; }
.stage-yellow { background: #fefce8; border-color: #fde68a; }
.stage-gray   { background: #f8fafc; border-color: #e2e8f0; }
.stage-blue   { background: #eff6ff; border-color: #bfdbfe; }
.stage-title { font-size: 0.78rem; font-weight: 700; color: #0f172a; margin-bottom: 5px; }
.stage-date  { font-size: 1rem; font-weight: 700; color: #111827; margin-bottom: 4px; }
.stage-note  { color: #64748b; font-size: 0.72rem; line-height: 1.25; min-height: 26px; margin-bottom: 8px; }
.stage-days  { font-size: 0.84rem; color: #334155; margin-bottom: 6px; }
.pill { display: inline-block; border-radius: 999px; padding: 3px 9px; font-size: 0.72rem; font-weight: 700; border: 1px solid transparent; white-space: nowrap; }
.pill-green  { background: #dcfce7; color: #166534; border-color: #bbf7d0; }
.pill-red    { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
.pill-yellow { background: #fef9c3; color: #854d0e; border-color: #fde68a; }
.pill-gray   { background: #f1f5f9; color: #475569; border-color: #e2e8f0; }
.pill-blue   { background: #dbeafe; color: #1e40af; border-color: #bfdbfe; }

/* ── Cabecera del expediente ── */
.exp-header {
    background: #fff;
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 18px 20px;
    margin: 0.75rem 0;
}
.exp-header-title   { font-size: 1.05rem; font-weight: 700; color: #0f172a; margin-bottom: 3px; }
.exp-header-sub     { font-size: 0.84rem; color: #64748b; margin-bottom: 14px; }
.exp-fields         { display: grid; grid-template-columns: repeat(5, minmax(110px, 1fr)); gap: 8px; }
.exp-field          { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 12px; }
.exp-field-label    { color: #94a3b8; font-size: 0.67rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.exp-field-value    { color: #0f172a; font-size: 0.94rem; font-weight: 700; line-height: 1.2; overflow-wrap: anywhere; }

/* ── KPIs del expediente ── */
.exp-kpis { display: grid; grid-template-columns: repeat(5, minmax(130px, 1fr)); gap: 10px; margin: 0.75rem 0; }
.exp-kpi  { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 13px 14px; }
.exp-kpi-primary { background: linear-gradient(180deg,#eff6ff 0%,#fff 100%); border-color: #bfdbfe; }
.exp-kpi-label { color: #94a3b8; font-size: 0.67rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px; }
.exp-kpi-value { color: #0f172a; font-size: 1.05rem; font-weight: 700; line-height: 1.2; overflow-wrap: anywhere; }
.exp-kpi-note  { color: #94a3b8; font-size: 0.73rem; margin-top: 4px; line-height: 1.3; }

/* ── Avance actual ── */
.avance-card {
    background: #fff;
    border: 1px solid #dbeafe;
    border-left: 4px solid #2563eb;
    border-radius: 16px;
    padding: 15px 18px;
    margin: 0.75rem 0;
}
.avance-title  { color: #1e3a8a; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; }
.avance-grid   { display: grid; grid-template-columns: repeat(4, minmax(130px, 1fr)); gap: 10px; }
.avance-item   { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px 11px; }
.avance-label  { color: #94a3b8; font-size: 0.67rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 3px; }
.avance-value  { color: #0f172a; font-size: 0.92rem; font-weight: 700; overflow-wrap: anywhere; }
.avance-note   { color: #475569; font-size: 0.84rem; line-height: 1.4; margin-top: 10px; }

/* ── Pedido crítico seleccionado ── */
.critico-selected {
    background: linear-gradient(180deg,#fef2f2 0%,#fff 100%);
    border: 1px solid #fecaca;
    border-left: 6px solid #dc2626;
    border-radius: 18px;
    padding: 15px 18px;
    margin: 0.75rem 0;
}
.critico-title  { color: #7f1d1d; font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px; }
.critico-grid   { display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 8px; }
.critico-field  { background: #fff; border: 1px solid #fee2e2; border-radius: 12px; padding: 9px 11px; }

/* ── Responsive ── */
@media (max-width: 1200px) {
    .stages-grid { grid-template-columns: repeat(3, minmax(130px, 1fr)); }
    .exp-fields  { grid-template-columns: repeat(3, minmax(110px, 1fr)); }
    .exp-kpis    { grid-template-columns: repeat(3, minmax(130px, 1fr)); }
    .avance-grid { grid-template-columns: repeat(2, minmax(130px, 1fr)); }
    .critico-grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
}
@media (max-width: 760px) {
    .stages-grid  { grid-template-columns: 1fr; }
    .exp-fields   { grid-template-columns: 1fr; }
    .exp-kpis     { grid-template-columns: 1fr; }
    .avance-grid  { grid-template-columns: 1fr; }
    .critico-grid { grid-template-columns: 1fr; }
    .stage::after { content: "↓"; right: 50%; bottom: -12px; top: auto; transform: translateX(50%); }
    .stage:last-child::after { content: ""; }
}
</style>
"""

st.markdown(ESTILOS_GLOBALES, unsafe_allow_html=True)


# =========================================================
# Utilidades generales (sin cambios de lógica)
# =========================================================
def normalizar_codigo_centro(valor: Any) -> str:
    if pd.isna(valor): return "Sin dato"
    texto = str(valor).strip()
    if not texto or texto.lower() in ["nan", "none", "nat"]: return "Sin dato"
    if texto.endswith(".0"): texto = texto[:-2]
    return texto.upper()

def etiqueta_centro(valor: Any) -> str:
    codigo = normalizar_codigo_centro(valor)
    nombre = CENTROS_NOMBRES.get(codigo)
    return f"{codigo} · {nombre}" if nombre else codigo

def lista_centros_corta(valores: Any, max_items: int = 4) -> str:
    if valores is None: return "Todos"
    if isinstance(valores, str): valores = [valores]
    etiquetas = [etiqueta_centro(v) for v in valores if str(v).strip()]
    if not etiquetas: return "Todos"
    if len(etiquetas) <= max_items: return ", ".join(etiquetas)
    return ", ".join(etiquetas[:max_items]) + f" +{len(etiquetas) - max_items} más"

def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy(); df.columns = df.columns.astype(str).str.strip(); return df

def convertir_columna_fecha(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")
    serie_num = pd.to_numeric(serie, errors="coerce")
    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")
    mask_num = serie_num.notna()
    if mask_num.any():
        mask_ms = mask_num & serie_num.abs().ge(10**11)
        mask_s  = mask_num & serie_num.abs().lt(10**11)
        if mask_ms.any(): resultado.loc[mask_ms] = pd.to_datetime(serie_num.loc[mask_ms], unit="ms", errors="coerce")
        if mask_s.any():  resultado.loc[mask_s]  = pd.to_datetime(serie_num.loc[mask_s],  unit="s",  errors="coerce")
    mask_texto = ~mask_num
    if mask_texto.any():
        resultado.loc[mask_texto] = pd.to_datetime(serie.loc[mask_texto], errors="coerce", dayfirst=True)
    return resultado

def convertir_fechas_visuales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in FECHAS_CANDIDATAS:
        if col in df.columns:
            convertido = convertir_columna_fecha(df[col])
            if convertido.notna().any(): df[col] = convertido
    return df

def opciones_columna(df: pd.DataFrame, col: str, max_opciones: int = 700) -> list:
    if col not in df.columns: return []
    return df[col].dropna().astype(str).sort_values().unique().tolist()[:max_opciones]

@st.cache_data(show_spinner=False)
def opciones_filtros_rapidas(df_base: pd.DataFrame) -> dict:
    columnas = [COL_CENTRO, COL_GRUPO_COMPRAS, COL_TIPO_OC, COL_ORIGEN, COL_SISTEMA,
                "clasificacion_vencimiento", "ultima_etapa_registrada", "fecha_pendiente", COL_ESTADO_RECEPCION_ALERTA]
    return {col: opciones_columna(df_base, col) for col in columnas if col in df_base.columns}

def filtrar_por_ids(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip(): return pd.Series(True, index=df.index)
    tokens = [t.strip().replace(".0","") for t in str(texto).replace("\n",",").replace(";"," ").replace(" ",",").split(",") if t.strip()]
    if not tokens: return pd.Series(True, index=df.index)
    serie = df[columna].astype(str).str.replace(".0","",regex=False)
    mask = pd.Series(False, index=df.index)
    for t in tokens: mask = mask | serie.str.contains(t, case=False, na=False, regex=False)
    return mask

def contiene_texto(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip(): return pd.Series(True, index=df.index)
    return df[columna].astype(str).str.contains(str(texto).strip(), case=False, na=False, regex=False)

def formato_valor(valor: Any) -> str:
    if pd.isna(valor): return "-"
    if isinstance(valor, pd.Timestamp): return valor.strftime("%d-%m-%Y")
    if isinstance(valor, float):
        if np.isfinite(valor) and valor.is_integer(): return f"{int(valor):,}".replace(",",".")
        return f"{valor:,.1f}".replace(",","X").replace(".",",").replace("X",".")
    if isinstance(valor, int): return f"{valor:,}".replace(",",".")
    return str(valor)

def formato_id(valor: Any) -> str:
    if pd.isna(valor): return "-"
    texto = str(valor).strip()
    try:
        numero = float(texto)
        if np.isfinite(numero) and numero.is_integer(): return str(int(numero))
    except: pass
    if texto.endswith(".0"): texto = texto[:-2]
    return texto

def valor_numerico(valor: Any) -> float:
    try: return float(pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0])
    except: return np.nan

def obtener_umbral_tat(row: pd.Series) -> float:
    umbral = valor_numerico(row.get(COL_UMBRAL_TAT, np.nan))
    if pd.notna(umbral): return umbral
    tipo_oc = str(row.get(COL_TIPO_OC, "")).strip().replace(".0","")
    if tipo_oc in ["35","45"]: return 40
    if tipo_oc == "47": return 70
    return np.nan

def texto_dias_y_meses(dias: Any) -> str:
    dias_num = valor_numerico(dias)
    if pd.isna(dias_num): return "Sin dato"
    dias_int = int(round(dias_num))
    texto_dias = f"{dias_int:,}".replace(",",".")
    if dias_int < 0: return f"{texto_dias} días · revisar fechas"
    if dias_int >= 30:
        meses = dias_num / 30.44
        return f"{texto_dias} días · {f'{meses:,.1f}'.replace(',','X').replace('.',',').replace('X','.')} meses aprox."
    return f"{texto_dias} días"

def texto_dias_simple(dias: Any) -> str:
    dias_num = valor_numerico(dias)
    if pd.isna(dias_num): return "Sin dato"
    return f"{int(round(dias_num)):,} días".replace(",",".")

def texto_dias_restantes(dias_restantes: Any) -> str:
    valor = valor_numerico(dias_restantes)
    if pd.isna(valor): return "Sin dato"
    valor_int = int(round(valor))
    if valor_int >= 0: return f"{valor_int:,} días disponibles".replace(",",".")
    return f"{abs(valor_int):,} días sobre el umbral".replace(",",".")

def formato_tiempo_transcurrido(dias: Any) -> str:
    valor = valor_numerico(dias)
    if pd.isna(valor): return "Sin dato"
    signo = "-" if valor < 0 else ""
    abs_dias = abs(float(valor))
    if abs_dias <= 30: return f"{signo}{int(round(abs_dias)):,} días".replace(",",".")
    meses = abs_dias / 30.44
    if meses <= 12: return f"{signo}{meses:,.1f} meses".replace(",","X").replace(".",",").replace("X",".")
    anos = meses / 12
    return f"{signo}{anos:,.1f} años".replace(",","X").replace(".",",").replace("X",".")

def formato_dias_restantes_operativo(dias: Any) -> str:
    valor = valor_numerico(dias)
    if pd.isna(valor): return "Sin dato"
    if valor < 0: return f"Vencido hace {formato_tiempo_transcurrido(abs(valor))}"
    if valor == 0: return "Vence hoy"
    return f"Vence en {formato_tiempo_transcurrido(valor)}"

def formato_numero_corto(valor: Any, decimales: int = 0) -> str:
    numero = valor_numerico(valor)
    if pd.isna(numero): return "-"
    if decimales == 0: return f"{int(round(numero)):,}".replace(",",".")
    return f"{numero:,.{decimales}f}".replace(",","X").replace(".",",").replace("X",".")

def fecha_etapa_texto(row: pd.Series, columna: str) -> str:
    valor = row.get(columna, np.nan)
    if pd.isna(valor): return "Pendiente"
    if isinstance(valor, pd.Timestamp): return valor.strftime("%d-%m-%Y")
    return formato_valor(valor)

def fecha_valida(row: pd.Series, columna: str):
    valor = row.get(columna, np.nan)
    if pd.isna(valor): return pd.NaT
    return pd.to_datetime(valor, errors="coerce")

def nombre_fecha_faltante(columna: str) -> str:
    mapa = {"fecha_solicitud_final":"fecha de solicitud","fecha_liberacion_final":"fecha de liberación",
            "fecha_pedido_final":"fecha de pedido","fecha_facturacion_final":"fecha de facturación",
            "fecha_recepcion_final":"fecha de recepción"}
    return mapa.get(columna, "fecha pendiente")

def html_texto(valor: Any) -> str: return escape(formato_valor(valor))
def html_id(valor: Any) -> str: return escape(formato_id(valor))

def clase_performance(valor: Any) -> str:
    texto = str(valor).strip().lower()
    if texto == "cumple": return "green"
    if texto == "no cumple": return "red"
    if texto in ["en proceso","sin datos"]: return "yellow"
    if "no aplica" in texto: return "gray"
    return "blue"

def clase_dias(dias: Any, umbral: Any = None) -> str:
    dias_num = pd.to_numeric(pd.Series([dias]), errors="coerce").iloc[0]
    umbral_num = pd.to_numeric(pd.Series([umbral]), errors="coerce").iloc[0] if umbral is not None else np.nan
    if pd.isna(dias_num) or dias_num < 0: return "gray"
    if pd.notna(umbral_num): return "green" if dias_num <= umbral_num else "red"
    return "green" if dias_num == 0 else "yellow"

def pill(texto: Any, color: str) -> str:
    return f'<span class="pill pill-{color}">{escape(formato_valor(texto))}</span>'

def etapa_color(row: pd.Series, etapa: dict) -> str:
    perf_col = etapa.get("performance"); dias_col = etapa.get("dias"); umbral_col = etapa.get("umbral")
    if perf_col and perf_col in row.index: return clase_performance(row.get(perf_col))
    if dias_col and dias_col in row.index: return clase_dias(row.get(dias_col), row.get(umbral_col) if umbral_col else None)
    fecha_col = etapa.get("fecha")
    if fecha_col and fecha_col in row.index and pd.notna(row.get(fecha_col)): return "blue"
    return "gray"

def texto_tat_total_usuario(performance: Any, dias_tat: Any) -> str:
    estado = str(performance).strip().lower()
    if estado == "en proceso" and pd.isna(pd.to_numeric(pd.Series([dias_tat]), errors="coerce").iloc[0]): return "En proceso"
    return texto_dias_y_meses(dias_tat)

def lista_valores_corta(valores: Any, max_items: int = 4) -> str:
    if valores is None: return "Todos"
    if isinstance(valores, str): valores = [valores]
    valores = [str(v) for v in valores if str(v).strip()]
    if not valores: return "Todos"
    if len(valores) <= max_items: return ", ".join(valores)
    return ", ".join(valores[:max_items]) + f" +{len(valores) - max_items} más"

def fecha_texto_simple(valor: Any) -> str:
    fecha = pd.to_datetime(valor, errors="coerce")
    if pd.isna(fecha): return "Sin fecha calculable"
    return fecha.strftime("%d-%m-%Y")

def columnas_existentes(df_base: pd.DataFrame, columnas: list) -> list:
    return [c for c in columnas if c in df_base.columns]

def _serie_texto(df: pd.DataFrame, col: str) -> pd.Series:
    if col in df.columns: return df[col].astype(str)
    return pd.Series("", index=df.index, dtype="object")

def _normalizar_tipo_oc(serie: pd.Series) -> pd.Series:
    return serie.astype(str).str.strip().str.replace(".0","",regex=False)

def _formatear_fecha_serie(serie: pd.Series) -> pd.Series:
    fechas = pd.to_datetime(serie, errors="coerce")
    return fechas.dt.strftime("%d-%m-%Y").fillna("Sin fecha calculable")

def _primera_columna_existente(df: pd.DataFrame, candidatas: list) -> pd.Series:
    for col in candidatas:
        if col in df.columns: return df[col]
    return pd.Series(pd.NaT, index=df.index)

def rango_fechas_texto(df_base: pd.DataFrame) -> str:
    if df_base.empty or "fecha_vencimiento_tat" not in df_base.columns: return "Sin casos"
    fechas = pd.to_datetime(df_base["fecha_vencimiento_tat"], errors="coerce").dropna()
    if fechas.empty: return "Sin casos"
    fmin = fecha_texto_simple(fechas.min()); fmax = fecha_texto_simple(fechas.max())
    return fmin if fmin == fmax else f"{fmin} a {fmax}"

@st.cache_data(show_spinner=False)
def dataframe_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return output.getvalue()

@st.cache_data(show_spinner=False)
def dataframe_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

def obtener_avance_pedido(row: pd.Series) -> dict:
    completadas = [(n, c, pd.notna(row.get(c, np.nan))) for n, c in ETAPAS_LINEA_PEDIDO]
    registradas = [i for i in completadas if i[2]]
    pendientes  = [i for i in completadas if not i[2]]
    ultima_nombre, ultima_columna, _ = registradas[-1] if registradas else ("Sin etapa registrada","",False)
    siguiente_nombre, siguiente_columna, _ = pendientes[0] if pendientes else ("Cerrado","",False)
    fecha_inicio = fecha_valida(row, "fecha_solicitud_final")
    fecha_ultima = fecha_valida(row, ultima_columna) if ultima_columna else pd.NaT
    esta_cerrado = len(pendientes) == 0
    fecha_referencia = fecha_ultima
    if not esta_cerrado and pd.notna(fecha_inicio): fecha_referencia = pd.Timestamp.today().normalize()
    dias_parcial = np.nan
    if pd.notna(fecha_inicio) and pd.notna(fecha_referencia): dias_parcial = (fecha_referencia - fecha_inicio).days
    umbral = obtener_umbral_tat(row)
    dias_restantes = np.nan
    if pd.notna(dias_parcial) and pd.notna(umbral): dias_restantes = int(round(umbral - dias_parcial))
    return {"ultima_etapa": ultima_nombre, "ultima_fecha": fecha_etapa_texto(row, ultima_columna) if ultima_columna else "-",
            "siguiente_etapa": siguiente_nombre, "siguiente_columna": siguiente_columna,
            "dias_parcial": dias_parcial, "dias_restantes": dias_restantes, "umbral_tat": umbral, "esta_cerrado": esta_cerrado}

def diagnostico_avance(row: pd.Series) -> str:
    avance = obtener_avance_pedido(row)
    if avance["esta_cerrado"]: return "El pedido ya tiene recepción registrada. El TAT total está cerrado."
    falta = nombre_fecha_faltante(avance["siguiente_columna"])
    dias_restantes = valor_numerico(avance["dias_restantes"])
    umbral = valor_numerico(avance.get("umbral_tat", np.nan))
    if pd.isna(umbral): return f"Falta {falta}. No se pudo determinar el umbral TAT."
    if pd.notna(dias_restantes):
        if dias_restantes < 0: return f"Falta {falta}. El pedido ya supera el umbral TAT de {int(umbral)} días."
        if dias_restantes <= 5: return f"Falta {falta}. El pedido está cerca del umbral TAT de {int(umbral)} días."
        return f"Falta {falta}. Quedan {int(dias_restantes)} días disponibles contra el umbral TAT de {int(umbral)} días."
    return f"Última etapa: {avance['ultima_etapa']}. Siguiente: {avance['siguiente_etapa']}."


# =========================================================
# Constructores HTML mejorados
# =========================================================
def html_avance_actual(row: pd.Series) -> str:
    avance = obtener_avance_pedido(row)
    dias_parcial = formato_tiempo_transcurrido(avance["dias_parcial"])
    dias_restantes = texto_dias_restantes(avance["dias_restantes"])
    umbral = avance.get("umbral_tat", np.nan)
    tat_estado = "Cerrado" if avance["esta_cerrado"] else "Pendiente hasta recepción"
    contra_umbral = f"{dias_restantes} · umbral {int(valor_numerico(umbral))} días" if pd.notna(valor_numerico(umbral)) else "Sin dato"
    return dedent(f"""
    <div class="avance-card">
        <div class="avance-title">Avance actual</div>
        <div class="avance-grid">
            <div class="avance-item"><div class="avance-label">Última etapa</div><div class="avance-value">{escape(avance['ultima_etapa'])} · {escape(avance['ultima_fecha'])}</div></div>
            <div class="avance-item"><div class="avance-label">Tiempo transcurrido</div><div class="avance-value">{escape(dias_parcial)}</div></div>
            <div class="avance-item"><div class="avance-label">TAT total</div><div class="avance-value">{escape(tat_estado)}</div></div>
            <div class="avance-item"><div class="avance-label">Contra umbral TAT</div><div class="avance-value">{escape(contra_umbral)}</div></div>
        </div>
        <div class="avance-note">{escape(diagnostico_avance(row))}</div>
    </div>""").strip()

def html_linea_pedido(row: pd.Series) -> str:
    completadas = [pd.notna(row.get(c, np.nan)) for _, c in ETAPAS_LINEA_PEDIDO]
    try: indice_activo = completadas.index(False)
    except ValueError: indice_activo = len(ETAPAS_LINEA_PEDIDO) - 1
    partes = []
    for i, (label, col_fecha) in enumerate(ETAPAS_LINEA_PEDIDO):
        esta_completa = completadas[i]
        es_activa = i == indice_activo and not esta_completa
        dot_class = "pipe-dot-ok" if esta_completa else ("pipe-dot-active" if es_activa else "pipe-dot-nd")
        icono = "✓" if esta_completa else ""
        partes.append(dedent(f"""
        <div class="pipe-step">
            <div class="pipe-dot {dot_class}">{icono}</div>
            <div class="pipe-label">{escape(label)}</div>
            <div class="pipe-date">{escape(fecha_etapa_texto(row, col_fecha))}</div>
        </div>""").strip())
        if i < len(ETAPAS_LINEA_PEDIDO) - 1:
            conn = "pipe-conn-ok" if (completadas[i] and completadas[i+1]) else ("pipe-conn-dashed" if (completadas[i] and not completadas[i+1]) else "")
            partes.append(f'<div class="pipe-conn {conn}"></div>')
    estado_tat = formato_valor(row.get(COL_PERF_TAT, np.nan))
    dias_tat = texto_tat_total_usuario(row.get(COL_PERF_TAT, np.nan), row.get(COL_DIAS_TAT, np.nan))
    return dedent(f"""
    <div class="pipe-card">
        <div class="pipe-title">Línea de pedido</div>
        <div class="pipe-line">{''.join(partes)}</div>
        <div class="pipe-note">TAT total: <strong>{escape(dias_tat)}</strong> · Estado: <strong>{escape(estado_tat)}</strong></div>
    </div>""").strip()

def _dot_class_tat(row: pd.Series, etapa: dict, i: int, indice_activo: int) -> tuple:
    fecha_col = etapa.get("fecha")
    completada = bool(fecha_col and pd.notna(row.get(fecha_col, np.nan)))
    perf_col = etapa.get("performance")
    perf = str(row.get(perf_col,"")).strip().lower() if perf_col else ""
    if completada and perf == "no cumple": return "tat-dot-bad", "!"
    if completada and perf in ["en proceso","sin datos"]: return "tat-dot-risk", "…"
    if completada: return "tat-dot-ok", "✓"
    if i == indice_activo: return "tat-dot-active", ""
    return "tat-dot-nd", ""

def html_diagrama_tat(row: pd.Series) -> str:
    completadas = [pd.notna(row.get(e.get("fecha"), np.nan)) for e in ETAPAS_PEDIDO]
    try: indice_activo = completadas.index(False)
    except ValueError: indice_activo = len(ETAPAS_PEDIDO) - 1
    partes = []
    for i, etapa in enumerate(ETAPAS_PEDIDO):
        dot_class, icono = _dot_class_tat(row, etapa, i, indice_activo)
        fecha_txt = fecha_etapa_texto(row, etapa.get("fecha")) if etapa.get("fecha") else "-"
        dias_col = etapa.get("dias"); umbral_col = etapa.get("umbral"); perf_col = etapa.get("performance")
        if dias_col:
            dias_txt = formato_tiempo_transcurrido(row.get(dias_col, np.nan))
            umbral_txt = formato_valor(row.get(umbral_col, np.nan)) if umbral_col else "-"
            perf_txt = formato_valor(row.get(perf_col, np.nan)) if perf_col else "Registrado"
            detalle = f"{dias_txt} · umbral {umbral_txt}d · {perf_txt}"
        else: detalle = "Punto de inicio"
        partes.append(dedent(f"""
        <div class="tat-step">
            <div class="tat-dot {dot_class}">{escape(icono)}</div>
            <div class="tat-step-label">{escape(str(etapa.get('titulo','')))}</div>
            <div class="tat-step-date">{escape(fecha_txt)}</div>
            <div class="tat-step-detail">{escape(detalle)}</div>
        </div>""").strip())
        if i < len(ETAPAS_PEDIDO) - 1:
            conn = "tat-conn-ok" if (completadas[i] and completadas[i+1]) else ("tat-conn-active" if (completadas[i] and not completadas[i+1]) else "")
            partes.append(f'<div class="tat-conn {conn}"></div>')
    estado_tat = formato_valor(row.get(COL_PERF_TAT, np.nan))
    dias_tat = texto_tat_total_usuario(row.get(COL_PERF_TAT, np.nan), row.get(COL_DIAS_TAT, np.nan))
    return dedent(f"""
    <div class="tat-card">
        <div class="tat-card-title">Etapas TAT</div>
        <div class="tat-flow">{''.join(partes)}</div>
        <div class="tat-note">TAT total: <strong>{escape(dias_tat)}</strong> · Estado: <strong>{escape(estado_tat)}</strong></div>
    </div>""").strip()

def html_estado_pedido_iframe(row: pd.Series) -> str:
    cards = []
    for etapa in ETAPAS_PEDIDO:
        color = etapa_color(row, etapa)
        fecha = html_texto(row.get(etapa["fecha"], np.nan)) if etapa.get("fecha") else "-"
        dias_col = etapa.get("dias"); umbral_col = etapa.get("umbral"); perf_col = etapa.get("performance")
        if dias_col:
            dias_valor = row.get(dias_col, np.nan)
            umbral = html_texto(row.get(umbral_col, np.nan)) if umbral_col else "-"
            fecha_fin_col = etapa.get("fecha")
            if pd.isna(row.get(fecha_fin_col, np.nan)):
                falta = nombre_fecha_faltante(fecha_fin_col)
                dias_txt = f"Pendiente · falta {escape(falta)}"
            elif dias_col == COL_DIAS_TAT:
                dias_txt = f"{escape(texto_dias_y_meses(dias_valor))} · umbral {umbral} días"
            else:
                dias_txt = f"{html_texto(dias_valor)} días · umbral {umbral}"
        else: dias_txt = "Punto de inicio"
        perf_val = row.get(perf_col,"Registrado") if perf_col else "Registrado"
        perf_color = clase_performance(perf_val) if perf_col else color
        cards.append(f"""
        <div class="stage stage-{color}">
            <div class="stage-title">{escape(etapa['titulo'])}</div>
            <div class="stage-date">{fecha}</div>
            <div class="stage-note">{escape(etapa['nota'])}</div>
            <div class="stage-days">{dias_txt}</div>
            {pill(perf_val, perf_color)}
        </div>""")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
    html,body{{margin:0;padding:0;font-family:'DM Sans',-apple-system,sans-serif;color:#0f172a;background:transparent;overflow:hidden;}}
    .stages-grid{{display:grid;grid-template-columns:repeat(6,minmax(130px,1fr));gap:8px;padding:2px 0 16px 0;box-sizing:border-box;}}
    .stage{{border-radius:14px;padding:12px 13px;border:1px solid #e5e7eb;min-height:140px;position:relative;box-sizing:border-box;}}
    .stage::after{{content:"→";position:absolute;right:-7px;top:50%;transform:translateY(-50%);color:#94a3b8;font-weight:700;}}
    .stage:last-child::after{{content:"";}}
    .stage-green{{background:#f0fdf4;border-color:#bbf7d0;}}.stage-red{{background:#fef2f2;border-color:#fecaca;}}
    .stage-yellow{{background:#fefce8;border-color:#fde68a;}}.stage-gray{{background:#f8fafc;border-color:#e2e8f0;}}
    .stage-blue{{background:#eff6ff;border-color:#bfdbfe;}}
    .stage-title{{font-size:0.78rem;font-weight:700;color:#0f172a;margin-bottom:5px;}}
    .stage-date{{font-size:1rem;font-weight:700;color:#111827;margin-bottom:4px;}}
    .stage-note{{color:#64748b;font-size:0.72rem;line-height:1.25;min-height:26px;margin-bottom:8px;}}
    .stage-days{{font-size:0.84rem;color:#334155;margin-bottom:6px;}}
    .pill{{display:inline-block;border-radius:999px;padding:3px 9px;font-size:0.72rem;font-weight:700;border:1px solid transparent;white-space:nowrap;}}
    .pill-green{{background:#dcfce7;color:#166534;border-color:#bbf7d0;}}.pill-red{{background:#fee2e2;color:#991b1b;border-color:#fecaca;}}
    .pill-yellow{{background:#fef9c3;color:#854d0e;border-color:#fde68a;}}.pill-gray{{background:#f1f5f9;color:#475569;border-color:#e2e8f0;}}
    .pill-blue{{background:#dbeafe;color:#1e40af;border-color:#bfdbfe;}}
    @media(max-width:1200px){{.stages-grid{{grid-template-columns:repeat(3,minmax(130px,1fr));}}html,body{{overflow:auto;}}}}
    </style></head><body><div class="stages-grid">{''.join(cards)}</div></body></html>"""

def html_resumen_expediente(row: pd.Series) -> str:
    oc_principal = row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan))
    return dedent(f"""
    <div class="exp-header">
        <div class="exp-header-title">Resumen · SolPed {html_id(row.get(COL_SOLPED, np.nan))}</div>
        <div class="exp-header-sub">Pedido {html_id(oc_principal)} · Posición {html_id(row.get(COL_POS_SOLPED, np.nan))} · Centro {html_texto(row.get(COL_CENTRO, np.nan))}</div>
        <div class="exp-fields">
            <div class="exp-field"><div class="exp-field-label">Solicitud de pedido</div><div class="exp-field-value">{html_id(row.get(COL_SOLPED, np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Pedido</div><div class="exp-field-value">{html_id(oc_principal)}</div></div>
            <div class="exp-field"><div class="exp-field-label">Centro</div><div class="exp-field-value">{html_texto(row.get(COL_CENTRO, np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Grupo compras</div><div class="exp-field-value">{html_texto(row.get(COL_GRUPO_COMPRAS, np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Nivel alerta</div><div class="exp-field-value">{html_texto(row.get('nivel_alerta', np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Estado recepción</div><div class="exp-field-value">{html_texto(row.get('clasificacion_vencimiento', row.get(COL_ESTADO_RECEPCION_ALERTA, np.nan)))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Fecha pendiente</div><div class="exp-field-value">{html_texto(row.get('fecha_pendiente', np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Acción sugerida</div><div class="exp-field-value">{html_texto(row.get('accion_sugerida', np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Vencimiento</div><div class="exp-field-value">{html_texto(row.get('dias_restantes_texto', np.nan))}</div></div>
            <div class="exp-field"><div class="exp-field-label">Tiempo transcurrido</div><div class="exp-field-value">{html_texto(row.get('tiempo_transcurrido_tat', np.nan))}</div></div>
        </div>
    </div>""").strip()

def html_kpis_expediente(row: pd.Series) -> str:
    return dedent(f"""
    <div class="exp-kpis">
        <div class="exp-kpi exp-kpi-primary"><div class="exp-kpi-label">Estado pedido</div><div class="exp-kpi-value">{html_texto(row.get('clasificacion_vencimiento', np.nan))}</div><div class="exp-kpi-note">Vence: {html_texto(row.get('fecha_vencimiento_texto', np.nan))}</div></div>
        <div class="exp-kpi exp-kpi-primary"><div class="exp-kpi-label">Tiempo desde inicio</div><div class="exp-kpi-value">{html_texto(row.get('tiempo_transcurrido_tat', np.nan))}</div><div class="exp-kpi-note">Solicitud → recepción o hoy</div></div>
        <div class="exp-kpi exp-kpi-primary"><div class="exp-kpi-label">Exceso del umbral</div><div class="exp-kpi-value">{html_texto(row.get('tiempo_excedido_umbral_texto', np.nan))}</div><div class="exp-kpi-note">Sobre umbral TAT total</div></div>
        <div class="exp-kpi"><div class="exp-kpi-label">Última etapa</div><div class="exp-kpi-value">{html_texto(row.get('ultima_etapa_registrada', np.nan))}</div><div class="exp-kpi-note">{html_texto(row.get('ultima_fecha_registrada', np.nan))}</div></div>
        <div class="exp-kpi"><div class="exp-kpi-label">Fecha pendiente</div><div class="exp-kpi-value">{html_texto(row.get('fecha_pendiente', np.nan))}</div><div class="exp-kpi-note">Siguiente hito requerido</div></div>
    </div>""").strip()

def html_critico_seleccionado(row: pd.Series) -> str:
    return dedent(f"""
    <div class="critico-selected">
        <div class="critico-title">Pedido crítico seleccionado</div>
        <div class="critico-grid">
            <div class="critico-field"><div class="exp-field-label">Nivel / urgencia</div><div class="exp-field-value">{html_texto(row.get('nivel_alerta', np.nan))} · {html_texto(row.get('dias_hasta_vencimiento', np.nan))}</div></div>
            <div class="critico-field"><div class="exp-field-label">Tiempo transcurrido</div><div class="exp-field-value">{html_texto(row.get('tiempo_transcurrido_tat', np.nan))}</div></div>
            <div class="critico-field"><div class="exp-field-label">Fecha pendiente</div><div class="exp-field-value">{html_texto(row.get('fecha_pendiente', np.nan))}</div></div>
            <div class="critico-field"><div class="exp-field-label">Acción sugerida</div><div class="exp-field-value">{html_texto(row.get('accion_sugerida', np.nan))}</div></div>
            <div class="critico-field"><div class="exp-field-label">Score riesgo</div><div class="exp-field-value">{html_texto(row.get('score_riesgo', np.nan))}</div></div>
        </div>
    </div>""").strip()


# =========================================================
# Preparación rápida cacheada
# =========================================================
@st.cache_data(show_spinner="Preparando datos TAT…")
def preparar_panel_tat_rapido(df_original: pd.DataFrame, hoy: pd.Timestamp) -> pd.DataFrame:
    df_base = limpiar_columnas(df_original.copy())
    df_base = convertir_fechas_visuales(df_base)
    fecha_recepcion = _primera_columna_existente(df_base, ["fecha_recepcion_final","Fecha recepción mercancía - NME80FN"])
    fecha_recepcion_dt = pd.to_datetime(fecha_recepcion, errors="coerce")
    df_base[COL_ESTADO_RECEPCION_ALERTA] = np.where(fecha_recepcion_dt.notna(), "Recepcionado", "Sin recepción")
    fecha_inicio = _primera_columna_existente(df_base, ["fecha_solicitud_final","Fecha de solicitud - ME5A"])
    df_base["fecha_inicio_tat"] = pd.to_datetime(fecha_inicio, errors="coerce")
    if COL_UMBRAL_TAT in df_base.columns:
        umbral = pd.to_numeric(df_base[COL_UMBRAL_TAT], errors="coerce")
    else:
        umbral = pd.Series(np.nan, index=df_base.index, dtype="float64")
    tipo_oc = _normalizar_tipo_oc(_serie_texto(df_base, COL_TIPO_OC))
    umbral = umbral.mask(umbral.isna() & tipo_oc.isin(["35","45"]), 40)
    umbral = umbral.mask(umbral.isna() & tipo_oc.eq("47"), 70)
    df_base["umbral_tat_calculado"] = umbral
    fecha_pedido_base = _primera_columna_existente(df_base, ["fecha_pedido_final","Fecha de pedido - ME5A"])
    df_base["fecha_pedido_base_vencimiento"] = pd.to_datetime(fecha_pedido_base, errors="coerce")
    fv_sol = df_base["fecha_inicio_tat"] + pd.to_timedelta(df_base["umbral_tat_calculado"], unit="D")
    fv_ped = df_base["fecha_pedido_base_vencimiento"] + pd.to_timedelta(df_base["umbral_tat_calculado"], unit="D")
    usar_ped = fv_sol.isna() & fv_ped.notna()
    df_base["fecha_vencimiento_tat"] = fv_sol.where(~usar_ped, fv_ped)
    df_base["fuente_calculo_vencimiento"] = np.select(
        [fv_sol.notna().fillna(False).to_numpy(dtype=bool), usar_ped.fillna(False).to_numpy(dtype=bool)],
        ["Calculado desde fecha de solicitud", "Estimado desde fecha de pedido"], default="Sin fecha calculable")
    df_base["fecha_vencimiento_texto"] = _formatear_fecha_serie(df_base["fecha_vencimiento_tat"])
    df_base["dias_restantes_int"] = (df_base["fecha_vencimiento_tat"] - hoy).dt.days.astype("Int64")
    df_base["dias_restantes_texto"] = df_base["dias_restantes_int"].apply(formato_dias_restantes_operativo)
    fecha_fin_ref = fecha_recepcion_dt.where(fecha_recepcion_dt.notna(), hoy)
    df_base["tiempo_transcurrido_tat_dias"] = (fecha_fin_ref - df_base["fecha_inicio_tat"]).dt.days.astype("Int64")
    df_base["tiempo_transcurrido_tat"] = df_base["tiempo_transcurrido_tat_dias"].apply(formato_tiempo_transcurrido)
    exceso = (df_base["tiempo_transcurrido_tat_dias"].astype("float64") - df_base["umbral_tat_calculado"].astype("float64"))
    exceso = exceso.where(exceso.gt(0), 0)
    df_base["tiempo_excedido_umbral_dias"] = exceso
    df_base["tiempo_excedido_umbral_texto"] = exceso.apply(lambda x: "Dentro del umbral" if pd.notna(x) and float(x) <= 0 else formato_tiempo_transcurrido(x))
    dias = df_base["dias_restantes_int"].astype("float64")
    condiciones = [dias.lt(0).fillna(False).to_numpy(dtype=bool), dias.eq(0).fillna(False).to_numpy(dtype=bool),
                   dias.eq(1).fillna(False).to_numpy(dtype=bool), dias.eq(2).fillna(False).to_numpy(dtype=bool),
                   dias.eq(3).fillna(False).to_numpy(dtype=bool), dias.eq(4).fillna(False).to_numpy(dtype=bool),
                   dias.eq(5).fillna(False).to_numpy(dtype=bool), dias.eq(6).fillna(False).to_numpy(dtype=bool),
                   dias.eq(7).fillna(False).to_numpy(dtype=bool),
                   dias.between(8,30,inclusive="both").fillna(False).to_numpy(dtype=bool),
                   dias.gt(30).fillna(False).to_numpy(dtype=bool)]
    etiquetas = ["Vencido","Vence hoy","1 día","2 días","3 días","4 días","5 días","6 días","7 días","7 a 30 días","Más de 1 mes"]
    df_base["clasificacion_vencimiento"] = np.select(condiciones, etiquetas, default="Sin datos")
    etapas = [("Solicitud","fecha_solicitud_final"),("Liberación","fecha_liberacion_final"),
              ("Pedido","fecha_pedido_final"),("Facturación","fecha_facturacion_final"),("Recepción","fecha_recepcion_final")]
    ultima_etapa  = pd.Series("Sin fecha registrada", index=df_base.index, dtype="object")
    ultima_fecha  = pd.Series(pd.NaT, index=df_base.index, dtype="datetime64[ns]")
    fecha_pendiente = pd.Series("Cerrado", index=df_base.index, dtype="object")
    faltante_asignado = pd.Series(False, index=df_base.index)
    for nombre, col in etapas:
        if col in df_base.columns:
            fecha_col = pd.to_datetime(df_base[col], errors="coerce")
        else:
            fecha_col = pd.Series(pd.NaT, index=df_base.index, dtype="datetime64[ns]")
        tiene_fecha = fecha_col.notna()
        ultima_etapa  = ultima_etapa.mask(tiene_fecha, nombre)
        ultima_fecha  = ultima_fecha.mask(tiene_fecha, fecha_col)
        falta = fecha_col.isna() & ~faltante_asignado
        fecha_pendiente = fecha_pendiente.mask(falta, nombre)
        faltante_asignado = faltante_asignado | falta
    df_base["ultima_etapa_registrada"] = ultima_etapa
    df_base["ultima_fecha_registrada_dt"] = ultima_fecha
    df_base["ultima_fecha_registrada"] = _formatear_fecha_serie(ultima_fecha)
    df_base["fecha_pendiente"] = fecha_pendiente
    df_base["esta_vencido"] = dias.lt(0).fillna(False)
    df_base["tiene_fecha_vencimiento"] = dias.notna()
    if "dias_restantes_tat" not in df_base.columns: df_base["dias_restantes_tat"] = df_base["dias_restantes_int"]
    if "brecha_tat" not in df_base.columns: df_base["brecha_tat"] = -df_base["dias_restantes_int"].astype("float64")
    if "etapa_actual" not in df_base.columns:
        df_base["etapa_actual"] = df_base["fecha_pendiente"].replace(
            {"Solicitud":"Solicitud","Liberación":"Liberación SolPed","Pedido":"Comprador",
             "Facturación":"Proveedor","Recepción":"Logística","Cerrado":"Recepcionado"})
    orden = {"Vencido":1,"Vence hoy":2,"1 día":3,"2 días":4,"3 días":5,"4 días":6,"5 días":7,"6 días":8,
             "7 días":9,"7 a 30 días":10,"Más de 1 mes":11,"Sin datos":12}
    df_base["_orden_vencimiento"] = df_base["clasificacion_vencimiento"].map(orden).fillna(99)
    df_base = df_base.sort_values(["_orden_vencimiento","dias_restantes_int"], ascending=[True,True])
    return df_base.drop(columns=["_orden_vencimiento"])


# =========================================================
# Filtrado
# =========================================================
def aplicar_filtros_panel(df_base: pd.DataFrame, centro_sel, recepcion_sel, vencimiento_sel,
                           grupo_sel, tipo_oc_sel, ultima_fecha_sel, fecha_pendiente_sel,
                           solped_txt, oc_txt, texto_txt) -> pd.DataFrame:
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
        mask &= filtrar_por_ids(df_base, COL_OC_ME5A, oc_txt) | filtrar_por_ids(df_base, COL_OC_NME, oc_txt)
    if str(texto_txt).strip():
        texto_mask = pd.Series(False, index=df_base.index)
        for col in [COL_MATERIAL, COL_TEXTO, COL_SOLICITANTE]:
            if col in df_base.columns: texto_mask |= contiene_texto(df_base, col, texto_txt)
        mask &= texto_mask
    return df_base.loc[mask].copy()


# =========================================================
# Funciones operativas (causa, acción, prioridad)
# =========================================================
def clasificar_dias_hasta_vencimiento(row: pd.Series) -> str:
    dias = valor_numerico(row.get("dias_restantes_tat", np.nan))
    if pd.isna(dias): return "Sin datos"
    if dias < 0: return "Vencido"
    if dias <= 1: return "1 día"
    if dias <= 2: return "2 días"
    if dias <= 7: return "7 días"
    return "+7 días"

def causa_probable(row: pd.Series) -> str:
    if COL_FECHAS_INCONSISTENTES in row.index and bool(row.get(COL_FECHAS_INCONSISTENTES, False)): return "Fechas inconsistentes"
    etapa = str(row.get("etapa_actual","")).strip()
    fecha_pendiente = str(row.get("fecha_pendiente","")).strip()
    umbral = obtener_umbral_tat(row)
    if etapa == "Recepcionado" or fecha_pendiente == "Cerrado": return "Pedido cerrado"
    if fecha_pendiente and fecha_pendiente != "Cerrado":
        mapa = {"Liberación":"Falta fecha de liberación de SolPed","Pedido":"Falta fecha de pedido / emisión de OC",
                "Facturación":"Falta fecha de facturación","Recepción":"Falta fecha de recepción en sistema"}
        causa = mapa.get(fecha_pendiente, f"Falta fecha de {fecha_pendiente.lower()}")
        if pd.isna(umbral): causa += " · además falta umbral TAT o tipo OC válido"
        return causa
    if pd.isna(umbral): return "Falta umbral TAT o tipo OC válido"
    mapa_etapa = {"Liberación SolPed":"Falta liberación de SolPed","Comprador":"Falta creación o emisión de OC",
                  "Proveedor":"Falta gestión de proveedor / facturación","Logística":"Falta recepción en sistema"}
    return mapa_etapa.get(etapa, "Revisar datos del pedido")

def accion_sugerida_fn(row: pd.Series) -> str:
    etapa = str(row.get("etapa_actual","")).strip()
    fecha_pendiente = str(row.get("fecha_pendiente","")).strip()
    if etapa == "Recepcionado" or fecha_pendiente == "Cerrado": return "Sin acción: pedido cerrado"
    if fecha_pendiente == "Liberación" or etapa == "Liberación SolPed": return "Escalar liberación de SolPed"
    if fecha_pendiente == "Pedido" or etapa == "Comprador": return "Escalar creación o emisión de OC"
    if fecha_pendiente == "Facturación" or etapa == "Proveedor": return "Contactar proveedor y confirmar fecha"
    if fecha_pendiente == "Recepción" or etapa == "Logística": return "Validar recepción con logística/bodega"
    dias_bucket = str(row.get("dias_hasta_vencimiento",""))
    if dias_bucket == "Sin datos": return "Corregir datos para calcular vencimiento"
    if dias_bucket in ["Vencido","1 día"]: return "Gestionar hoy"
    if dias_bucket in ["2 días","7 días"]: return "Programar seguimiento"
    return "Sin acción urgente"

def prioridad_operativa(row: pd.Series) -> int:
    mapa_dias = {"Vencido":1,"1 día":2,"2 días":3,"7 días":4,"+7 días":5,"Sin datos":6}
    mapa_nivel = {"Crítica":1,"Alta":2,"Media":3,"Normal":4,"Sin datos":6}
    return min(mapa_dias.get(str(row.get("dias_hasta_vencimiento","")),9), mapa_nivel.get(str(row.get("nivel_alerta","")),9))

def preparar_alertas_operativas(df_base: pd.DataFrame) -> pd.DataFrame:
    salida = df_base.copy()
    salida["dias_hasta_vencimiento"] = salida.apply(clasificar_dias_hasta_vencimiento, axis=1)
    salida["causa_probable"] = salida.apply(causa_probable, axis=1)
    salida["accion_sugerida"] = salida.apply(accion_sugerida_fn, axis=1)
    salida["prioridad_operativa"] = salida.apply(prioridad_operativa, axis=1)
    return salida.sort_values(["prioridad_operativa","brecha_tat"], ascending=[True,False])

def ordenar_expediente_critico(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty: return df_base.copy()
    salida = df_base.copy()
    if "prioridad_operativa" not in salida.columns:
        salida["prioridad_operativa"] = salida.apply(prioridad_operativa, axis=1)
    cols_orden = ["prioridad_operativa"]
    asc = [True]
    for col in ["score_riesgo","brecha_tat","tiempo_transcurrido_tat_dias"]:
        if col in salida.columns: cols_orden.append(col); asc.append(False)
    return salida.sort_values(cols_orden, ascending=asc)

def construir_label_critico(row: pd.Series) -> str:
    solped  = formato_id(row.get(COL_SOLPED, np.nan))
    oc      = formato_id(row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan)))
    pos     = formato_id(row.get(COL_POS_SOLPED, np.nan))
    nivel   = formato_valor(row.get("nivel_alerta", np.nan))
    venc    = formato_valor(row.get("dias_hasta_vencimiento", np.nan))
    pendiente = formato_valor(row.get("fecha_pendiente", np.nan))
    desc    = str(row.get(COL_TEXTO,""))[:60]
    return f"{nivel} · {venc} | SolPed {solped} | OC {oc} | Pos {pos} | Pendiente {pendiente} | {desc}"


# =========================================================
# Constructores de tablas para descargas
# =========================================================
def tabla_resumen_filtrada(df_base: pd.DataFrame) -> pd.DataFrame:
    columnas = columnas_existentes(df_base, [
        COL_SOLPED, COL_OC_ME5A, COL_POS_SOLPED, "clasificacion_vencimiento", "dias_restantes_texto",
        "tiempo_transcurrido_tat", "dias_restantes_int", COL_OC_NME, COL_POS_OC, "fecha_vencimiento_texto",
        COL_ESTADO_RECEPCION_ALERTA, "ultima_etapa_registrada", "ultima_fecha_registrada",
        "fecha_pendiente", COL_MATERIAL, COL_TEXTO, COL_CENTRO, COL_GRUPO_COMPRAS, COL_TIPO_OC,
        COL_DIAS_TAT, COL_UMBRAL_TAT, "umbral_tat_calculado", COL_MONTO,
    ])
    return df_base[columnas].rename(columns={
        COL_SOLPED:"Solicitud de pedido", COL_OC_ME5A:"Pedido", COL_POS_SOLPED:"Posición solicitud de pedido",
        "clasificacion_vencimiento":"Días hasta vencimiento", "dias_restantes_texto":"Días restantes",
        "tiempo_transcurrido_tat":"Tiempo transcurrido", "dias_restantes_int":"Días restantes numérico",
        COL_OC_NME:"Documento compras NME", COL_POS_OC:"Posición pedido",
        "fecha_vencimiento_texto":"Fecha de vencimiento", COL_ESTADO_RECEPCION_ALERTA:"Recepción",
        "ultima_etapa_registrada":"Última etapa registrada", "ultima_fecha_registrada":"Fecha última registrada",
        "fecha_pendiente":"Fecha pendiente", COL_DIAS_TAT:"Días TAT total",
        COL_UMBRAL_TAT:"Umbral TAT original", "umbral_tat_calculado":"Umbral TAT usado",
    })

def construir_conciliacion(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty: return pd.DataFrame(columns=["Grupo","Cantidad","% del filtrado","Explicación"])
    estado_recepcion = df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str) if COL_ESTADO_RECEPCION_ALERTA in df_base.columns else pd.Series("Sin recepción", index=df_base.index)
    dias = pd.to_numeric(df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)), errors="coerce")
    recepcionados = estado_recepcion.eq("Recepcionado")
    sin_recepcion = estado_recepcion.eq("Sin recepción")
    con_dias = dias.notna(); vencidos = dias.lt(0); proximos = dias.between(0,30,inclusive="both")
    mas_mes = dias.gt(30)
    filas = [
        {"Grupo":"Vencidos y recepcionados","Cantidad":int((vencidos&recepcionados).sum()),"Explicación":"Con recepción, pero fecha de vencimiento ya superada."},
        {"Grupo":"Vencidos y sin recepcionar","Cantidad":int((vencidos&sin_recepcion).sum()),"Explicación":"Sin recepción y con fecha de vencimiento ya superada."},
        {"Grupo":"Próximos a vencer sin recepción (0-30d)","Cantidad":int((proximos&sin_recepcion).sum()),"Explicación":"Abiertos que vencen entre hoy y 30 días."},
        {"Grupo":"No vencidos recepcionados","Cantidad":int((~vencidos&con_dias&recepcionados).sum()),"Explicación":"Cerrados con vencimiento calculable y no vencida."},
        {"Grupo":"Sin recepción, vencen en +1 mes","Cantidad":int((mas_mes&sin_recepcion).sum()),"Explicación":"Abiertos sin urgencia en 30 días."},
        {"Grupo":"Sin fecha calculable — recepcionados","Cantidad":int((~con_dias&recepcionados).sum()),"Explicación":"Falta fecha de solicitud, umbral o tipo OC."},
        {"Grupo":"Sin fecha calculable — sin recepción","Cantidad":int((~con_dias&sin_recepcion).sum()),"Explicación":"Sin recepción y sin información para calcular vencimiento."},
    ]
    salida = pd.DataFrame(filas)
    total = len(df_base)
    salida["% del filtrado"] = np.where(total > 0, salida["Cantidad"]/total*100, 0).round(1)
    total_fila = pd.DataFrame([{"Grupo":"TOTAL FILTRADO","Cantidad":int(salida["Cantidad"].sum()),"% del filtrado":100.0,"Explicación":"Suma de todos los grupos."}])
    return pd.concat([salida, total_fila], ignore_index=True)[["Grupo","Cantidad","% del filtrado","Explicación"]]

def detalle_vencidos(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty: return pd.DataFrame()
    estado = df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str) if COL_ESTADO_RECEPCION_ALERTA in df_base.columns else pd.Series("Sin recepción", index=df_base.index)
    dias = pd.to_numeric(df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)), errors="coerce")
    det = df_base.loc[estado.eq("Sin recepción") & dias.lt(0)].copy()
    return tabla_resumen_filtrada(det) if not det.empty else pd.DataFrame()

def detalle_proximos(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty: return pd.DataFrame()
    estado = df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str) if COL_ESTADO_RECEPCION_ALERTA in df_base.columns else pd.Series("Sin recepción", index=df_base.index)
    dias = pd.to_numeric(df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)), errors="coerce")
    det = df_base.loc[estado.eq("Sin recepción") & dias.between(0,30,inclusive="both")].copy()
    return tabla_resumen_filtrada(det) if not det.empty else pd.DataFrame()

def detalle_sin_fecha(df_base: pd.DataFrame) -> pd.DataFrame:
    if df_base.empty: return pd.DataFrame()
    estado = df_base[COL_ESTADO_RECEPCION_ALERTA].astype(str) if COL_ESTADO_RECEPCION_ALERTA in df_base.columns else pd.Series("Sin recepción", index=df_base.index)
    dias = pd.to_numeric(df_base.get("dias_restantes_int", pd.Series(np.nan, index=df_base.index)), errors="coerce")
    mask = estado.eq("Sin recepción") & dias.isna()
    det = df_base.loc[mask].copy()
    if det.empty: return pd.DataFrame()
    fecha_inicio = pd.to_datetime(det.get("fecha_inicio_tat", pd.Series(pd.NaT, index=det.index)), errors="coerce")
    umbral_calc = pd.to_numeric(det.get("umbral_tat_calculado", pd.Series(np.nan, index=det.index)), errors="coerce")
    razones = []
    for idx in det.index:
        faltantes = []
        if pd.isna(fecha_inicio.loc[idx]): faltantes.append("falta fecha de solicitud")
        if pd.isna(umbral_calc.loc[idx]): faltantes.append("falta umbral TAT o tipo OC válido")
        if not faltantes: faltantes.append("revisar datos")
        razones.append("; ".join(faltantes))
    det["motivo"] = razones
    cols = columnas_existentes(det, ["motivo", COL_SOLPED, COL_OC_ME5A, COL_POS_SOLPED,
                                      "ultima_etapa_registrada","fecha_pendiente","tiempo_transcurrido_tat",
                                      COL_TIPO_OC, COL_CENTRO, COL_GRUPO_COMPRAS, COL_MATERIAL, COL_TEXTO])
    return det[cols].rename(columns={"motivo":"Motivo sin fecha","ultima_etapa_registrada":"Última etapa",
                                      "fecha_pendiente":"Fecha pendiente","tiempo_transcurrido_tat":"Tiempo transcurrido",
                                      COL_SOLPED:"Solicitud de pedido",COL_OC_ME5A:"Pedido",COL_POS_SOLPED:"Posición"})

def aplicar_estilo_urgencia(df_tabla: pd.DataFrame):
    def color_dias(valor):
        t = str(valor).strip()
        if t == "Vencido": return "background-color:#fee2e2;color:#991b1b;font-weight:800;"
        if t in ["1 día","Vence hoy"]: return "background-color:#ffedd5;color:#9a3412;font-weight:800;"
        if t in ["2 días","3 días","4 días","5 días","6 días","7 días"]: return "background-color:#fef9c3;color:#854d0e;font-weight:700;"
        if t == "Sin datos": return "background-color:#f1f5f9;color:#475569;"
        return ""
    styler = df_tabla.style
    for col in ["clasificacion_vencimiento","Días hasta vencimiento","dias_hasta_vencimiento"]:
        if col in df_tabla.columns: styler = styler.map(color_dias, subset=[col])
    return styler


# =========================================================
# Resumen ejecutivo
# =========================================================
def _porcentaje_texto(valor: float) -> str:
    return f"{valor:,.1f}%".replace(",","X").replace(".",",").replace("X",".")

def _entero_texto(valor: Any) -> str:
    try: return f"{int(valor):,}".replace(",",".")
    except: return "0"

def _top_valor(df_base: pd.DataFrame, columna: str, default: str = "-") -> str:
    if df_base.empty or columna not in df_base.columns: return default
    serie = df_base[columna].dropna().astype(str).str.strip()
    serie = serie[~serie.str.lower().isin(["","-","nan","none","nat"])]
    return serie.value_counts().index[0] if not serie.empty else default

def construir_resumen_ejecutivo(df_total: pd.DataFrame, df_filtrado: pd.DataFrame, hoy: pd.Timestamp) -> dict:
    total_archivo = int(len(df_total)); total_filtrado = int(len(df_filtrado))
    pct_filtrado = total_filtrado / total_archivo * 100 if total_archivo else 0.0
    if df_filtrado.empty:
        return {"total_archivo":total_archivo,"total_filtrado":0,"pct_filtrado":0,"recepcionados":0,
                "sin_recepcion":0,"vencidos_sin_recepcion":0,"proximos_sin_recepcion":0,
                "sin_fecha_calculable":0,"solped_sin_pedido":0,"semaforo":"Sin datos",
                "mensaje":"No hay registros con los filtros actuales.",
                "accion_sugerida":"Amplía o ajusta los filtros.","etapa_critica":"-",
                "grupo_critico":"-","centro_critico":"-","solicitante_critico":"-","pct_filtrado":pct_filtrado}
    estado_recepcion = df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str) if COL_ESTADO_RECEPCION_ALERTA in df_filtrado.columns else pd.Series("Sin recepción", index=df_filtrado.index)
    dias_restantes = pd.to_numeric(df_filtrado.get("dias_restantes_int", pd.Series(np.nan, index=df_filtrado.index)), errors="coerce")
    recepcionados_mask = estado_recepcion.eq("Recepcionado")
    sin_recepcion_mask = estado_recepcion.eq("Sin recepción")
    vencidos_mask = dias_restantes.lt(0)
    proximos_mask = dias_restantes.between(0,30,inclusive="both") & sin_recepcion_mask
    sin_fecha_mask = dias_restantes.isna() & sin_recepcion_mask
    oc_me5a = _serie_texto(df_filtrado, COL_OC_ME5A).str.strip()
    oc_nme  = _serie_texto(df_filtrado, COL_OC_NME).str.strip()
    sin_pedido = oc_me5a.str.lower().isin({"","-","nan","none","nat","0","0.0"}) & oc_nme.str.lower().isin({"","-","nan","none","nat","0","0.0"})
    base_riesgo = df_filtrado.loc[sin_recepcion_mask & (vencidos_mask | proximos_mask | sin_fecha_mask)].copy()
    recepcionados = int(recepcionados_mask.sum()); sin_recepcion = int(sin_recepcion_mask.sum())
    vencidos_sin_recepcion = int((vencidos_mask & sin_recepcion_mask).sum())
    proximos_sin_recepcion = int(proximos_mask.sum()); sin_fecha_calculable = int(sin_fecha_mask.sum())
    solped_sin_pedido = int(sin_pedido.sum())
    etapa_critica = _top_valor(base_riesgo, "fecha_pendiente")
    grupo_critico = _top_valor(base_riesgo, COL_GRUPO_COMPRAS)
    centro_critico = etiqueta_centro(_top_valor(base_riesgo, COL_CENTRO))
    solicitante_critico = _top_valor(base_riesgo, COL_SOLICITANTE)
    if vencidos_sin_recepcion > 0:
        semaforo = "Crítico"
        mensaje = f"Hay {_entero_texto(vencidos_sin_recepcion)} registros vencidos sin recepción que requieren gestión prioritaria."
        accion_sugerida = "Priorizar pedidos vencidos sin recepción, comenzando por el grupo y centro con mayor riesgo."
    elif proximos_sin_recepcion > 0:
        semaforo = "Atención"
        mensaje = f"Hay {_entero_texto(proximos_sin_recepcion)} registros próximos a vencer sin recepción en los próximos 30 días."
        accion_sugerida = "Gestionar vencimientos de 0 a 30 días y confirmar avance de etapa pendiente."
    elif sin_fecha_calculable > 0:
        semaforo = "Datos incompletos"
        mensaje = f"Hay {_entero_texto(sin_fecha_calculable)} registros sin fecha de vencimiento calculable."
        accion_sugerida = "Corregir fecha de solicitud, umbral TAT o tipo OC para habilitar el seguimiento."
    else:
        semaforo = "Controlado"
        mensaje = "No se observan vencidos ni próximos a vencer sin recepción con los filtros actuales."
        accion_sugerida = "Mantener seguimiento preventivo."
    return {"total_archivo":total_archivo,"total_filtrado":total_filtrado,"pct_filtrado":pct_filtrado,
            "recepcionados":recepcionados,"sin_recepcion":sin_recepcion,
            "vencidos_sin_recepcion":vencidos_sin_recepcion,"proximos_sin_recepcion":proximos_sin_recepcion,
            "sin_fecha_calculable":sin_fecha_calculable,"solped_sin_pedido":solped_sin_pedido,
            "semaforo":semaforo,"mensaje":mensaje,"accion_sugerida":accion_sugerida,
            "etapa_critica":etapa_critica,"grupo_critico":grupo_critico,
            "centro_critico":centro_critico,"solicitante_critico":solicitante_critico}


# =========================================================
# Encontrar logo
# =========================================================
def encontrar_logo():
    for path in LOGO_CANDIDATOS:
        if path.exists(): return path
    return None

def mostrar_logo_sidebar(ancho: int = 180):
    logo_path = encontrar_logo()
    if logo_path is None: return
    suffix = logo_path.suffix.lower()
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"
    raw = logo_path.read_bytes()
    logo_b64 = base64.b64encode(raw).decode("utf-8")
    st.sidebar.markdown(
        f'<div style="display:flex;justify-content:center;padding:16px 0 8px 0;">'
        f'<img src="data:{mime};base64,{logo_b64}" style="width:{ancho}px;max-width:80%;height:auto;" alt="Logo"></div>',
        unsafe_allow_html=True)


# =========================================================
# ■  INICIO DE LA APLICACIÓN
# =========================================================
if "df_tat" not in st.session_state:
    st.error("Primero debes cargar el archivo base en Análisis TAT > Cargar archivo.")
    st.stop()

nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")
hoy = pd.Timestamp.today().normalize()

try:
    df_original = st.session_state["df_tat"].copy()
    df_panel = preparar_panel_tat_rapido(df_original, hoy)
    opciones_filtros = opciones_filtros_rapidas(df_panel)
except Exception as e:
    st.error("No se pudo preparar el archivo cargado.")
    st.exception(e); st.stop()

total_archivo = len(df_panel)
opciones_centro_panel = opciones_filtros.get(COL_CENTRO, [])
centro_default_panel  = [c for c in opciones_centro_panel if normalizar_codigo_centro(c) == "E002"]


# ── Estado inicial de filtros ──
_defaults = {
    "f_centro": centro_default_panel, "f_recepcion": "Sin recepción", "f_vencimiento": [],
    "f_grupo": [], "f_tipo_oc": [], "f_ultima_fecha": [], "f_fecha_pendiente": [],
    "f_limite": 300, "f_solped": "", "f_oc": "", "f_texto": "",
}
for k, v in _defaults.items():
    if k not in st.session_state: st.session_state[k] = v


# =========================================================
# SIDEBAR — Filtros
# =========================================================
with st.sidebar:
    st.markdown("""
    <div style="padding:0 4px 12px 4px;">
        <div style="font-size:0.65rem;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:2px;">ARCHIVO ACTIVO</div>
        <div style="font-size:0.85rem;font-weight:600;color:#e2e8f0;word-break:break-all;">{}</div>
        <div style="font-size:0.75rem;color:#64748b;margin-top:2px;">{:,} registros totales</div>
    </div>
    <hr style="border:none;border-top:1px solid #1e293b;margin:0 0 14px 0;">
    """.format(nombre_archivo, total_archivo).replace(",","."), unsafe_allow_html=True)

    st.markdown('<div style="font-size:0.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:10px;">Filtros globales</div>', unsafe_allow_html=True)

    with st.form("form_sidebar_filtros"):
        st.multiselect("Centro", opciones_centro_panel, key="f_centro", format_func=etiqueta_centro)
        st.selectbox("Recepción", ["Todos","Sin recepción","Recepcionado"], key="f_recepcion")
        st.multiselect("Urgencia / días hasta vencimiento",
            ["Vencido","Vence hoy","1 día","2 días","3 días","4 días","5 días","6 días",
             "7 días","7 a 30 días","Más de 1 mes","Sin datos"], key="f_vencimiento")
        st.multiselect("Grupo de compras", opciones_filtros.get(COL_GRUPO_COMPRAS,[]), key="f_grupo")
        st.multiselect("Tipo OC", opciones_filtros.get(COL_TIPO_OC,[]), key="f_tipo_oc")
        st.multiselect("Última etapa registrada", opciones_filtros.get("ultima_etapa_registrada",[]), key="f_ultima_fecha")
        st.multiselect("Fecha pendiente", opciones_filtros.get("fecha_pendiente",[]), key="f_fecha_pendiente")
        st.text_input("SolPed", placeholder="Ej: 1001973319", key="f_solped")
        st.text_input("OC / Pedido", placeholder="Ej: 4502321875", key="f_oc")
        st.text_input("Material / descripción / solicitante", placeholder="Texto libre", key="f_texto")
        st.number_input("Filas visibles en tablas", min_value=50, max_value=2000, step=50, key="f_limite")
        st.form_submit_button("✦  Aplicar filtros", use_container_width=True, type="primary")

    st.markdown('<hr style="border:none;border-top:1px solid #1e293b;margin:16px 0 12px 0;">', unsafe_allow_html=True)
    st.markdown('<div style="font-size:0.68rem;color:#475569;text-align:center;padding-bottom:8px;">Control TAT · SolPed / OC</div>', unsafe_allow_html=True)


# ── Aplicar filtros ──
df_filtrado = aplicar_filtros_panel(
    df_panel,
    centro_sel        = st.session_state["f_centro"],
    recepcion_sel     = st.session_state["f_recepcion"],
    vencimiento_sel   = st.session_state["f_vencimiento"],
    grupo_sel         = st.session_state["f_grupo"],
    tipo_oc_sel       = st.session_state["f_tipo_oc"],
    ultima_fecha_sel  = st.session_state["f_ultima_fecha"],
    fecha_pendiente_sel = st.session_state["f_fecha_pendiente"],
    solped_txt        = st.session_state["f_solped"],
    oc_txt            = st.session_state["f_oc"],
    texto_txt         = st.session_state["f_texto"],
)
filtrados = len(df_filtrado)


# ── Logo centrado en cabecera (igual que el original) ──
def mostrar_logo_principal(ancho: int = 260):
    logo_path = encontrar_logo()
    if logo_path is None:
        return
    suffix = logo_path.suffix.lower()
    mime = "image/svg+xml" if suffix == ".svg" else "image/png"
    raw = logo_path.read_bytes()
    logo_b64 = base64.b64encode(raw).decode("utf-8")
    st.markdown(
        f"""
        <div style="
            width:100%;
            display:flex;
            justify-content:center;
            align-items:center;
            min-height:84px;
            margin:0 0 16px 0;
            overflow:visible;
        ">
            <img
                src="data:{mime};base64,{logo_b64}"
                style="width:{ancho}px;max-width:80%;height:auto;display:block;object-fit:contain;"
                alt="Logo Enaex"
            >
        </div>
        """,
        unsafe_allow_html=True,
    )

mostrar_logo_principal()

# =========================================================
# CABECERA PRINCIPAL
# =========================================================
st.markdown("""
<div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:1.25rem;gap:16px;">
    <div>
        <div style="font-size:1.65rem;font-weight:700;color:#0f172a;letter-spacing:-0.025em;line-height:1.1;">
            Control TAT · SolPed / OC
        </div>
        <div style="font-size:0.88rem;color:#64748b;margin-top:5px;">
            Seguimiento de tiempos de atención de solicitudes y órdenes de compra
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Barra de estado rápida
estado_recepcion_global = df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str) if COL_ESTADO_RECEPCION_ALERTA in df_filtrado.columns else pd.Series("Sin recepción", index=df_filtrado.index)
dias_global = pd.to_numeric(df_filtrado.get("dias_restantes_int", pd.Series(np.nan, index=df_filtrado.index)), errors="coerce")
vencidos_total   = int((dias_global.lt(0) & estado_recepcion_global.eq("Sin recepción")).sum())
proximos_total   = int((dias_global.between(0,30,inclusive="both") & estado_recepcion_global.eq("Sin recepción")).sum())
sin_fecha_total  = int((dias_global.isna() & estado_recepcion_global.eq("Sin recepción")).sum())
recepcionados_total = int(estado_recepcion_global.eq("Recepcionado").sum())

mc1, mc2, mc3, mc4, mc5 = st.columns(5)
mc1.metric("Registros filtrados", f"{filtrados:,}".replace(",","."), f"{filtrados/total_archivo*100:.1f}% del total" if total_archivo else "")
mc2.metric("⚠ Vencidos sin recepción",   f"{vencidos_total:,}".replace(",","."))
mc3.metric("⏱ Próximos (0–30 d)",         f"{proximos_total:,}".replace(",","."))
mc4.metric("❓ Sin fecha calculable",      f"{sin_fecha_total:,}".replace(",","."))
mc5.metric("✓ Recepcionados",             f"{recepcionados_total:,}".replace(",","."))

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)


# =========================================================
# PESTAÑAS PRINCIPALES
# =========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Resumen ejecutivo",
    "🚨  Alertas y vencimientos",
    "📋  Datos filtrados",
    "🔍  Expediente",
    "📈  Estadística por material",
])


# ══════════════════════════════════════════════════════════
# TAB 1 — RESUMEN EJECUTIVO
# ══════════════════════════════════════════════════════════
with tab1:
    resumen = construir_resumen_ejecutivo(df_panel, df_filtrado, hoy)

    COLOR_SEMAFORO = {
        "Crítico": "#dc2626", "Atención": "#f97316",
        "Datos incompletos": "#ca8a04", "Controlado": "#16a34a", "Sin datos": "#64748b",
    }
    color = COLOR_SEMAFORO.get(str(resumen.get("semaforo","")), "#2563eb")

    st.markdown(f"""
    <div class="tat-section-card" style="border-left:6px solid {color};margin-bottom:0.5rem;">
        <div style="font-size:0.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:4px;">Estado general</div>
        <div style="font-size:1.4rem;font-weight:700;color:#0f172a;letter-spacing:-0.02em;margin-bottom:6px;">{escape(str(resumen.get('semaforo','Sin datos')))}</div>
        <div style="font-size:0.94rem;color:#334155;line-height:1.5;margin-bottom:8px;">{escape(str(resumen.get('mensaje','')))}</div>
        <div style="font-size:0.9rem;font-weight:600;color:#0f172a;">Acción sugerida: {escape(str(resumen.get('accion_sugerida','')))}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Métricas del filtrado")
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("Universo total",       _entero_texto(resumen.get("total_archivo",0)))
    e2.metric("Analizados",           _entero_texto(resumen.get("total_filtrado",0)), _porcentaje_texto(float(resumen.get("pct_filtrado",0))))
    e3.metric("Recepcionados",        _entero_texto(resumen.get("recepcionados",0)))
    e4.metric("Sin recepción",        _entero_texto(resumen.get("sin_recepcion",0)))

    r1, r2, r3 = st.columns(3)
    r1.metric("Vencidos sin recepción",   _entero_texto(resumen.get("vencidos_sin_recepcion",0)))
    r2.metric("Próximos 0-30 días",       _entero_texto(resumen.get("proximos_sin_recepcion",0)))
    r3.metric("Sin fecha calculable",     _entero_texto(resumen.get("sin_fecha_calculable",0)))

    st.markdown("#### Focos de riesgo")
    f1, f2, f3, f4 = st.columns(4)
    f1.info(f"**Etapa pendiente dominante**\n\n{resumen.get('etapa_critica','-')}")
    f2.info(f"**Grupo con más riesgo**\n\n{resumen.get('grupo_critico','-')}")
    f3.info(f"**Centro con más riesgo**\n\n{resumen.get('centro_critico','-')}")
    f4.info(f"**Solicitante con más riesgo**\n\n{resumen.get('solicitante_critico','-')}")

    st.markdown("#### Radiografía del archivo completo")
    col_rad1, col_rad2 = st.columns(2)
    with col_rad1:
        st.metric("Total de registros en archivo", f"{total_archivo:,}".replace(",","."))
        if COL_CENTRO in df_panel.columns:
            centros_dist = df_panel[COL_CENTRO].dropna().astype(str).value_counts().reset_index()
            centros_dist.columns = ["Centro","Cantidad"]
            centros_dist["Centro"] = centros_dist["Centro"].map(etiqueta_centro)
            centros_dist["% total"] = (centros_dist["Cantidad"] / total_archivo * 100).round(1)
            with st.expander(f"Distribución por centro ({centros_dist['Centro'].nunique()} centros)", expanded=False):
                st.dataframe(centros_dist, use_container_width=True, hide_index=True)
    with col_rad2:
        if COL_ESTADO_RECEPCION_ALERTA in df_panel.columns:
            rec_dist = df_panel[COL_ESTADO_RECEPCION_ALERTA].value_counts().reset_index()
            rec_dist.columns = ["Recepción","Cantidad"]
            rec_dist["% total"] = (rec_dist["Cantidad"] / total_archivo * 100).round(1)
            for _, frow in rec_dist.iterrows():
                label = str(frow["Recepción"])
                st.metric(label, f"{int(frow['Cantidad']):,}".replace(",","."), f"{frow['% total']:.1f}%")

    st.markdown("#### Conciliación del total filtrado")
    df_conc = construir_conciliacion(df_filtrado)
    def estilo_conc(row):
        g = str(row.get("Grupo","")).lower()
        base = [""] * len(row)
        if g == "total filtrado": return ["background-color:#f1f5f9;font-weight:800;border-top:2px solid #94a3b8;"]*len(row)
        if "vencidos" in g: return ["background-color:#fee2e2;color:#991b1b;font-weight:700;"]*len(row)
        if "próximos" in g or "proximos" in g: return ["background-color:#ffedd5;color:#9a3412;font-weight:700;"]*len(row)
        return base
    st.dataframe(df_conc.style.apply(estilo_conc, axis=1), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════
# TAB 2 — ALERTAS Y VENCIMIENTOS
# ══════════════════════════════════════════════════════════
with tab2:
    df_vencidos  = detalle_vencidos(df_filtrado)
    df_proximos  = detalle_proximos(df_filtrado)
    df_sin_fecha = detalle_sin_fecha(df_filtrado)
    n_venc = len(df_vencidos); n_prox = len(df_proximos); n_sf = len(df_sin_fecha)

    st.markdown("#### Panorama de urgencias")
    av1, av2, av3 = st.columns(3)
    av1.metric("🔴 Vencidos sin recepción", f"{n_venc:,}".replace(",","."))
    av2.metric("🟠 Próximos 0–30 días",     f"{n_prox:,}".replace(",","."))
    av3.metric("⚪ Sin fecha calculable",    f"{n_sf:,}".replace(",","."))

    # ── Vencidos ──
    st.markdown("---")
    st.markdown("#### 🔴 Vencidos sin recepción")
    if n_venc > 0:
        st.markdown(f"""
        <div class="alerta-urgente alerta-roja">
            <span style="font-size:1.1rem;">⚠</span>
            <span>{n_venc:,} registros ya superaron su fecha de vencimiento TAT y no tienen recepción. Requieren gestión inmediata.</span>
        </div>""".replace(",","."), unsafe_allow_html=True)
        with st.expander(f"Ver los {n_venc:,} registros vencidos".replace(",","."), expanded=True):
            _limite = int(st.session_state["f_limite"])
            st.dataframe(aplicar_estilo_urgencia(df_vencidos.head(_limite)), use_container_width=True, hide_index=True)
        cv1, cv2 = st.columns(2)
        with cv1: st.download_button("⬇ CSV · Vencidos", data=dataframe_a_csv(df_vencidos), file_name="vencidos_sin_recepcion.csv", mime="text/csv", use_container_width=True)
        with cv2: st.download_button("⬇ Excel · Vencidos", data=dataframe_a_excel(df_vencidos), file_name="vencidos_sin_recepcion.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.success("No hay registros vencidos sin recepción con los filtros actuales.")

    # ── Próximos ──
    st.markdown("---")
    st.markdown("#### 🟠 Próximos a vencer sin recepción (0–30 días)")
    if n_prox > 0:
        st.markdown(f"""
        <div class="alerta-urgente alerta-naranja">
            <span style="font-size:1.1rem;">⏱</span>
            <span>{n_prox:,} registros vencen entre hoy y los próximos 30 días y no tienen recepción.</span>
        </div>""".replace(",","."), unsafe_allow_html=True)
        with st.expander(f"Ver los {n_prox:,} registros próximos".replace(",","."), expanded=False):
            _limite = int(st.session_state["f_limite"])
            st.dataframe(aplicar_estilo_urgencia(df_proximos.head(_limite)), use_container_width=True, hide_index=True)
        cp1, cp2 = st.columns(2)
        with cp1: st.download_button("⬇ CSV · Próximos", data=dataframe_a_csv(df_proximos), file_name="proximos_vencer.csv", mime="text/csv", use_container_width=True)
        with cp2: st.download_button("⬇ Excel · Próximos", data=dataframe_a_excel(df_proximos), file_name="proximos_vencer.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.success("No hay registros próximos a vencer sin recepción con los filtros actuales.")

    # ── Sin fecha ──
    st.markdown("---")
    st.markdown("#### ⚪ Sin fecha de vencimiento calculable y sin recepción")
    if n_sf > 0:
        st.info(f"{n_sf:,} registros no entran en el seguimiento TAT porque falta fecha de solicitud, umbral o tipo OC válido. Corrija los datos para habilitarlos.".replace(",","."))
        with st.expander(f"Ver {n_sf:,} registros sin fecha".replace(",","."), expanded=False):
            st.dataframe(df_sin_fecha.head(int(st.session_state["f_limite"])), use_container_width=True, hide_index=True)
        csf1, csf2 = st.columns(2)
        with csf1: st.download_button("⬇ CSV · Sin fecha", data=dataframe_a_csv(df_sin_fecha), file_name="sin_fecha_vencimiento.csv", mime="text/csv", use_container_width=True)
        with csf2: st.download_button("⬇ Excel · Sin fecha", data=dataframe_a_excel(df_sin_fecha), file_name="sin_fecha_vencimiento.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    else:
        st.success("No hay registros sin fecha de vencimiento calculable y sin recepción con los filtros actuales.")


# ══════════════════════════════════════════════════════════
# TAB 3 — DATOS FILTRADOS
# ══════════════════════════════════════════════════════════
with tab3:
    tabla_resumen = tabla_resumen_filtrada(df_filtrado)
    limite = int(st.session_state["f_limite"])
    registros_visibles = min(limite, filtrados)

    # ── Cabecera informativa ──
    st.markdown(
        f"""
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:14px;padding:14px 18px;margin-bottom:1rem;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:10px;">
            <div>
                <div style="font-size:0.72rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:3px;">Vista previa de datos filtrados</div>
                <div style="font-size:1.05rem;font-weight:700;color:#0f172a;">
                    Mostrando <span style="color:#2563eb;">{registros_visibles:,}</span> de <span style="color:#0f172a;">{filtrados:,}</span> registros filtrados
                </div>
                <div style="font-size:0.8rem;color:#64748b;margin-top:2px;">
                    {filtrados - registros_visibles:,} registros adicionales disponibles · ajusta «Filas visibles» en la barra lateral para ver más
                </div>
            </div>
            <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:8px 14px;text-align:center;">
                <div style="font-size:0.68rem;font-weight:700;color:#1e40af;text-transform:uppercase;letter-spacing:0.05em;">Total en archivo</div>
                <div style="font-size:1.2rem;font-weight:700;color:#1e40af;">{total_archivo:,}</div>
            </div>
        </div>
        """.replace(",", "."),
        unsafe_allow_html=True,
    )

    st.dataframe(aplicar_estilo_urgencia(tabla_resumen.head(limite)), use_container_width=True, hide_index=True)

    st.markdown("#### Descargas")
    st.caption("La descarga incluye la totalidad del filtrado, no solo las filas visibles.")
    dc1, dc2 = st.columns(2)
    with dc1:
        st.download_button(
            f"⬇ CSV · {filtrados:,} registros filtrados".replace(",","."),
            data=dataframe_a_csv(tabla_resumen),
            file_name="control_tat_filtrado.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with dc2:
        if st.button("Preparar Excel", use_container_width=True):
            st.download_button(
                f"⬇ Excel · {filtrados:,} registros filtrados".replace(",","."),
                data=dataframe_a_excel(tabla_resumen),
                file_name="control_tat_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with st.expander("Ver filtros aplicados", expanded=False):
        filtros_df = pd.DataFrame([
            {"Filtro":"Centro",                     "Selección": lista_centros_corta(st.session_state["f_centro"])},
            {"Filtro":"Recepción",                  "Selección": st.session_state["f_recepcion"]},
            {"Filtro":"Urgencia",                   "Selección": lista_valores_corta(st.session_state["f_vencimiento"])},
            {"Filtro":"Grupo compras",               "Selección": lista_valores_corta(st.session_state["f_grupo"])},
            {"Filtro":"Tipo OC",                    "Selección": lista_valores_corta(st.session_state["f_tipo_oc"])},
            {"Filtro":"Última etapa registrada",    "Selección": lista_valores_corta(st.session_state["f_ultima_fecha"])},
            {"Filtro":"Fecha pendiente",             "Selección": lista_valores_corta(st.session_state["f_fecha_pendiente"])},
            {"Filtro":"SolPed",                     "Selección": st.session_state["f_solped"] or "Todos"},
            {"Filtro":"OC / Pedido",                "Selección": st.session_state["f_oc"] or "Todos"},
            {"Filtro":"Material / descripción",     "Selección": st.session_state["f_texto"] or "Todos"},
        ])
        st.dataframe(filtros_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════
# TAB 4 — EXPEDIENTE
# ══════════════════════════════════════════════════════════
with tab4:
    if df_filtrado.empty:
        st.info("No hay pedidos disponibles con los filtros actuales.")
    else:
        df_exp_base = df_filtrado.copy()
        # Asegurar columnas operativas
        if "dias_hasta_vencimiento" not in df_exp_base.columns:
            df_exp_base["dias_hasta_vencimiento"] = df_exp_base.apply(clasificar_dias_hasta_vencimiento, axis=1)
        if "accion_sugerida" not in df_exp_base.columns:
            df_exp_base["accion_sugerida"] = df_exp_base.apply(accion_sugerida_fn, axis=1)
        if "causa_probable" not in df_exp_base.columns:
            df_exp_base["causa_probable"] = df_exp_base.apply(causa_probable, axis=1)
        if "nivel_alerta" not in df_exp_base.columns:
            df_exp_base["nivel_alerta"] = "Sin datos"
        if "score_riesgo" not in df_exp_base.columns:
            df_exp_base["score_riesgo"] = 0.0
        df_exp_base = ordenar_expediente_critico(df_exp_base)

        # ── Helper para subtabla de prioridad ──
        def _tabla_prioridad(df_sub: pd.DataFrame) -> pd.DataFrame:
            cols = columnas_existentes(df_sub, [
                "dias_hasta_vencimiento", "nivel_alerta", "accion_sugerida",
                "ultima_etapa_registrada", "fecha_pendiente",
                COL_ESTADO_RECEPCION_ALERTA, COL_SOLPED, COL_OC_ME5A, COL_POS_SOLPED,
                COL_CENTRO, COL_GRUPO_COMPRAS,
                "tiempo_transcurrido_tat", "dias_restantes_texto", "fecha_vencimiento_texto",
                COL_MATERIAL, COL_TEXTO, COL_MONTO,
            ])
            return df_sub[cols].copy().rename(columns={
                "dias_hasta_vencimiento":      "Urgencia",
                "nivel_alerta":                "Nivel alerta",
                "accion_sugerida":             "Acción sugerida",
                "ultima_etapa_registrada":     "Última etapa",
                "fecha_pendiente":             "Fecha pendiente",
                COL_ESTADO_RECEPCION_ALERTA:   "Recepción",
                COL_SOLPED:                    "SolPed",
                COL_OC_ME5A:                   "Pedido",
                COL_POS_SOLPED:                "Posición",
                COL_CENTRO:                    "Centro",
                COL_GRUPO_COMPRAS:             "Grupo compras",
                "tiempo_transcurrido_tat":     "Tiempo transcurrido",
                "dias_restantes_texto":        "Días restantes",
                "fecha_vencimiento_texto":     "Fecha vencimiento",
                COL_MATERIAL:                  "Material",
                COL_TEXTO:                     "Descripción",
                COL_MONTO:                     "Monto",
            })

        def _estilo_prioridad(df_tabla: pd.DataFrame):
            def color_urgencia(valor):
                t = str(valor).strip()
                if t == "Vencido":  return "background-color:#fee2e2;color:#991b1b;font-weight:800;"
                if t in ["Vence hoy","1 día"]: return "background-color:#ffedd5;color:#9a3412;font-weight:800;"
                if t in ["2 días","3 días","4 días","5 días","6 días","7 días"]: return "background-color:#fef9c3;color:#854d0e;font-weight:700;"
                if t == "Sin datos": return "background-color:#f1f5f9;color:#475569;"
                return ""
            styler = df_tabla.style
            if "Urgencia" in df_tabla.columns:
                styler = styler.map(color_urgencia, subset=["Urgencia"])
            return styler

        # Máscaras de clasificación
        _estado_rec = df_exp_base[COL_ESTADO_RECEPCION_ALERTA].astype(str) if COL_ESTADO_RECEPCION_ALERTA in df_exp_base.columns else pd.Series("Sin recepción", index=df_exp_base.index)
        _dias_exp   = pd.to_numeric(df_exp_base.get("dias_restantes_int", pd.Series(np.nan, index=df_exp_base.index)), errors="coerce")
        _sin_rec    = _estado_rec.eq("Sin recepción")

        df_venc_exp  = df_exp_base.loc[_sin_rec & _dias_exp.lt(0)].copy()
        df_prox_exp  = df_exp_base.loc[_sin_rec & _dias_exp.between(0, 30, inclusive="both")].copy()
        df_mas30_exp = df_exp_base.loc[_sin_rec & _dias_exp.gt(30)].copy()

        n_venc_exp  = len(df_venc_exp)
        n_prox_exp  = len(df_prox_exp)
        n_mas30_exp = len(df_mas30_exp)

        # ── Métricas de cabecera ──
        st.markdown("#### Prioridades operativas del filtrado")
        ep1, ep2, ep3 = st.columns(3)
        ep1.metric("🔴 Vencidos sin recepción",        f"{n_venc_exp:,}".replace(",","."))
        ep2.metric("🟠 Próximos a vencer (0–30 días)", f"{n_prox_exp:,}".replace(",","."))
        ep3.metric("🟡 Por vencer (>30 días)",          f"{n_mas30_exp:,}".replace(",","."))

        # ── 🔴 Vencidos sin recepción ──
        st.markdown("---")
        st.markdown("#### 🔴 Vencidos sin recepción")
        if n_venc_exp > 0:
            st.markdown(
                f'<div class="alerta-urgente alerta-roja">'
                f'<span style="font-size:1.1rem;">⚠</span>'
                f'<span>{n_venc_exp:,} registros ya superaron su fecha de vencimiento TAT y no tienen recepción. Requieren gestión inmediata.</span>'
                f'</div>'.replace(",","."),
                unsafe_allow_html=True,
            )
            with st.expander(f"Ver {n_venc_exp:,} vencidos sin recepción".replace(",","."), expanded=True):
                limite_exp = int(st.session_state["f_limite"])
                st.caption(f"Mostrando {min(limite_exp, n_venc_exp):,} de {n_venc_exp:,} registros.".replace(",","."))
                st.dataframe(_estilo_prioridad(_tabla_prioridad(df_venc_exp).head(limite_exp)), use_container_width=True, hide_index=True)
            cv1, cv2 = st.columns(2)
            with cv1: st.download_button("⬇ CSV · Vencidos", data=dataframe_a_csv(_tabla_prioridad(df_venc_exp)), file_name="expediente_vencidos.csv", mime="text/csv", use_container_width=True)
            with cv2: st.download_button("⬇ Excel · Vencidos", data=dataframe_a_excel(_tabla_prioridad(df_venc_exp)), file_name="expediente_vencidos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.success("No hay registros vencidos sin recepción con los filtros actuales.")

        # ── 🟠 Próximos a vencer sin recepción (0–30 días) ──
        st.markdown("---")
        st.markdown("#### 🟠 Próximos a vencer sin recepción (0–30 días)")
        if n_prox_exp > 0:
            st.markdown(
                f'<div class="alerta-urgente alerta-naranja">'
                f'<span style="font-size:1.1rem;">⏱</span>'
                f'<span>{n_prox_exp:,} registros vencen entre hoy y los próximos 30 días sin recepción.</span>'
                f'</div>'.replace(",","."),
                unsafe_allow_html=True,
            )
            with st.expander(f"Ver {n_prox_exp:,} próximos a vencer (0–30 d)".replace(",","."), expanded=False):
                limite_exp = int(st.session_state["f_limite"])
                st.caption(f"Mostrando {min(limite_exp, n_prox_exp):,} de {n_prox_exp:,} registros.".replace(",","."))
                st.dataframe(_estilo_prioridad(_tabla_prioridad(df_prox_exp).head(limite_exp)), use_container_width=True, hide_index=True)
            cp1, cp2 = st.columns(2)
            with cp1: st.download_button("⬇ CSV · Próximos 0–30d", data=dataframe_a_csv(_tabla_prioridad(df_prox_exp)), file_name="expediente_proximos_0_30.csv", mime="text/csv", use_container_width=True)
            with cp2: st.download_button("⬇ Excel · Próximos 0–30d", data=dataframe_a_excel(_tabla_prioridad(df_prox_exp)), file_name="expediente_proximos_0_30.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.success("No hay registros próximos a vencer (0–30 días) sin recepción con los filtros actuales.")

        # ── 🟡 Por vencer >30 días ──
        st.markdown("---")
        st.markdown("#### 🟡 Por vencer sin recepción (>30 días)")
        if n_mas30_exp > 0:
            st.info(f"{n_mas30_exp:,} registros sin recepción con fecha de vencimiento en más de 30 días. Sin urgencia inmediata, pero en seguimiento preventivo.".replace(",","."))
            with st.expander(f"Ver {n_mas30_exp:,} registros por vencer (>30 d)".replace(",","."), expanded=False):
                limite_exp = int(st.session_state["f_limite"])
                st.caption(f"Mostrando {min(limite_exp, n_mas30_exp):,} de {n_mas30_exp:,} registros.".replace(",","."))
                st.dataframe(_estilo_prioridad(_tabla_prioridad(df_mas30_exp).head(limite_exp)), use_container_width=True, hide_index=True)
            cm1, cm2 = st.columns(2)
            with cm1: st.download_button("⬇ CSV · Por vencer >30d", data=dataframe_a_csv(_tabla_prioridad(df_mas30_exp)), file_name="expediente_mas30.csv", mime="text/csv", use_container_width=True)
            with cm2: st.download_button("⬇ Excel · Por vencer >30d", data=dataframe_a_excel(_tabla_prioridad(df_mas30_exp)), file_name="expediente_mas30.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        else:
            st.success("No hay registros por vencer en más de 30 días sin recepción con los filtros actuales.")

        # ── Gestión visual de críticos ──
        st.markdown("---")
        st.markdown("#### Gestión visual de críticos")
        st.caption("Filtra, prioriza y elige el pedido a expeditar. Los filtros aquí solo afectan el selector del expediente.")

        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        niveles_disp   = sorted(df_exp_base["nivel_alerta"].dropna().astype(str).unique().tolist()) if "nivel_alerta" in df_exp_base.columns else []
        urgencias_disp = [u for u in ["Vencido","Vence hoy","1 día","2 días","3 días","4 días","5 días","6 días","7 días","7 a 30 días","Más de 1 mes","Sin datos"]
                          if u in (df_exp_base["dias_hasta_vencimiento"].dropna().astype(str).unique().tolist() if "dias_hasta_vencimiento" in df_exp_base.columns else [])]
        recep_disp     = sorted(df_exp_base[COL_ESTADO_RECEPCION_ALERTA].dropna().astype(str).unique().tolist()) if COL_ESTADO_RECEPCION_ALERTA in df_exp_base.columns else []
        pend_disp      = sorted(df_exp_base["fecha_pendiente"].dropna().astype(str).unique().tolist()) if "fecha_pendiente" in df_exp_base.columns else []

        with col_g1: g_niveles   = st.multiselect("Nivel alerta",   niveles_disp,   default=[v for v in ["Crítica","Alta"] if v in niveles_disp],  key="g_nivel")
        with col_g2: g_urgencias = st.multiselect("Urgencia",       urgencias_disp, default=[v for v in ["Vencido","1 día","2 días","7 días"] if v in urgencias_disp], key="g_urgencia")
        with col_g3: g_recepcion = st.multiselect("Recepción",      recep_disp,     default=[v for v in ["Sin recepción"] if v in recep_disp],      key="g_recepcion")
        with col_g4: g_pendiente = st.multiselect("Fecha pendiente",pend_disp,      key="g_pendiente")
        g_top = st.number_input("Máximo a visualizar en tabla", min_value=10, max_value=1000, value=100, step=10, key="g_top")

        mask_g = pd.Series(True, index=df_exp_base.index)
        if g_niveles   and "nivel_alerta"            in df_exp_base.columns: mask_g &= df_exp_base["nivel_alerta"].astype(str).isin(g_niveles)
        if g_urgencias and "dias_hasta_vencimiento"  in df_exp_base.columns: mask_g &= df_exp_base["dias_hasta_vencimiento"].astype(str).isin(g_urgencias)
        if g_recepcion and COL_ESTADO_RECEPCION_ALERTA in df_exp_base.columns: mask_g &= df_exp_base[COL_ESTADO_RECEPCION_ALERTA].astype(str).isin(g_recepcion)
        if g_pendiente and "fecha_pendiente"         in df_exp_base.columns: mask_g &= df_exp_base["fecha_pendiente"].astype(str).isin(g_pendiente)

        df_gestion = ordenar_expediente_critico(df_exp_base.loc[mask_g].copy())

        mg1, mg2, mg3, mg4 = st.columns(4)
        mg1.metric("Visualizados",   f"{len(df_gestion):,}".replace(",","."))
        mg2.metric("Vencidos",       f"{int(df_gestion.get('dias_hasta_vencimiento', pd.Series(dtype=str)).astype(str).eq('Vencido').sum()):,}".replace(",","."))
        mg3.metric("Sin recepción",  f"{int(df_gestion.get(COL_ESTADO_RECEPCION_ALERTA, pd.Series(dtype=str)).astype(str).eq('Sin recepción').sum()):,}".replace(",","."))
        mg4.metric("Crítica / Alta", f"{int(df_gestion.get('nivel_alerta', pd.Series(dtype=str)).astype(str).isin(['Crítica','Alta']).sum()):,}".replace(",","."))

        if df_gestion.empty:
            st.warning("No hay pedidos con los filtros de gestión aplicados.")
        else:
            cols_tabla_gestion = columnas_existentes(df_gestion, [
                "nivel_alerta","dias_hasta_vencimiento","accion_sugerida","causa_probable",
                "ultima_etapa_registrada","fecha_pendiente",COL_ESTADO_RECEPCION_ALERTA,
                COL_SOLPED, COL_OC_ME5A, COL_POS_SOLPED, COL_CENTRO, COL_GRUPO_COMPRAS, COL_MONTO,
            ])
            tabla_g = df_gestion.head(int(g_top))[cols_tabla_gestion].copy()

            def color_nivel(valor):
                t = str(valor).strip()
                if t == "Crítica": return "background-color:#fee2e2;color:#991b1b;font-weight:800;"
                if t == "Alta":    return "background-color:#ffedd5;color:#9a3412;font-weight:800;"
                if t == "Media":   return "background-color:#fef9c3;color:#854d0e;font-weight:700;"
                if t == "Normal":  return "background-color:#dcfce7;color:#166534;font-weight:700;"
                return "background-color:#f1f5f9;color:#475569;"

            styler_g = tabla_g.style
            if "nivel_alerta" in tabla_g.columns: styler_g = styler_g.map(color_nivel, subset=["nivel_alerta"])
            st.dataframe(styler_g, use_container_width=True, hide_index=True)
            sugerido = df_gestion.index[0] if not df_gestion.empty else None
            if sugerido is not None: st.session_state["exp_sugerido"] = sugerido

        # ══ EXPEDIENTE DETALLADO ══════════════════════════════
        st.markdown("---")
        st.markdown("#### Expediente detallado del pedido")

        max_sel = 5000
        opciones = df_exp_base.index.tolist()[:max_sel]
        sugerido = st.session_state.get("exp_sugerido")
        if sugerido in df_exp_base.index and sugerido not in opciones: opciones = [sugerido] + opciones[:-1]
        elif sugerido in opciones: opciones = [sugerido] + [i for i in opciones if i != sugerido]
        if len(df_exp_base) > max_sel:
            st.caption(f"Selector muestra los primeros {max_sel:,} de {len(df_exp_base):,} registros.".replace(",","."))

        labels_sel  = {idx: construir_label_critico(df_exp_base.loc[idx]) for idx in opciones}
        idx_default = opciones.index(sugerido) if sugerido in opciones else 0
        seleccionado = st.selectbox("Seleccionar pedido", opciones, index=idx_default, format_func=lambda i: labels_sel.get(i, str(i)))
        row = df_exp_base.loc[seleccionado]

        # ── Ficha resumen de campos clave ──
        CAMPOS_CLAVE = [
            # (etiqueta, nombre_columna_o_campo_calculado)
            ("SolPed",                    COL_SOLPED),
            ("Pedido",                    COL_OC_ME5A),
            ("Material",                  COL_MATERIAL),
            ("Descripción",               COL_TEXTO),
            ("Precio de valoración",      "Precio de valoración"),
            ("Monto",                     COL_MONTO),
            ("Cantidad solicitada",       "Cantidad solicitada - ME5A"),
            ("Unidad de medida",          "Unidad de medida - ME5A"),
            ("Fecha inicio TAT",          "fecha_inicio_tat"),
            ("Fecha solicitud",           "fecha_solicitud_final"),
            ("Fecha vencimiento",         "fecha_vencimiento_texto"),
            ("Días restantes",            "dias_restantes_texto"),
            ("Urgencia",                  "dias_hasta_vencimiento"),
            ("Tiempo transcurrido",       "tiempo_transcurrido_tat"),
            ("Días transcurridos",        "tiempo_transcurrido_tat_dias"),
            ("Performance TAT total",     COL_PERF_TAT),
            ("Última etapa registrada",   "ultima_etapa_registrada"),
            ("Fecha pendiente",           "fecha_pendiente"),
            ("Acción sugerida",           "accion_sugerida"),
        ]

        def _val_campo(row, col):
            val = row.get(col, np.nan)
            if pd.isna(val): return "-"
            if isinstance(val, pd.Timestamp): return val.strftime("%d-%m-%Y")
            return formato_valor(val)

        # Renderizar en 4 columnas
        n_cols_ficha = 4
        ficha_items = [(lbl, _val_campo(row, col)) for lbl, col in CAMPOS_CLAVE if col in row.index or col in [c for _, c in CAMPOS_CLAVE]]
        # Solo incluir si existe en el row
        ficha_items = [(lbl, _val_campo(row, col)) for lbl, col in CAMPOS_CLAVE]

        filas_ficha = [ficha_items[i:i+n_cols_ficha] for i in range(0, len(ficha_items), n_cols_ficha)]
        celdas_html = ""
        for fila in filas_ficha:
            celdas_html += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px;">'
            for lbl, val in fila:
                # Colorear campos de urgencia
                color_val = "#0f172a"
                bg_val = "#f8fafc"
                brd_val = "#e2e8f0"
                if lbl == "Urgencia":
                    if val == "Vencido":        bg_val,brd_val,color_val = "#fee2e2","#fecaca","#991b1b"
                    elif val in ["Vence hoy","1 día"]: bg_val,brd_val,color_val = "#ffedd5","#fed7aa","#9a3412"
                    elif val in ["2 días","3 días","4 días","5 días","6 días","7 días"]: bg_val,brd_val,color_val = "#fef9c3","#fde68a","#854d0e"
                elif lbl == "Performance TAT total":
                    t = str(val).strip().lower()
                    if t == "cumple":       bg_val,brd_val,color_val = "#dcfce7","#bbf7d0","#166534"
                    elif t == "no cumple":  bg_val,brd_val,color_val = "#fee2e2","#fecaca","#991b1b"
                    elif t in ["en proceso","sin datos"]: bg_val,brd_val,color_val = "#fef9c3","#fde68a","#854d0e"
                celdas_html += (
                    f'<div style="background:{bg_val};border:1px solid {brd_val};border-radius:12px;padding:10px 13px;">'
                    f'<div style="font-size:0.67rem;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">{escape(lbl)}</div>'
                    f'<div style="font-size:0.94rem;font-weight:700;color:{color_val};line-height:1.2;overflow-wrap:anywhere;">{escape(str(val))}</div>'
                    f'</div>'
                )
            # Rellenar columnas vacías en última fila
            resto = n_cols_ficha - len(fila)
            for _ in range(resto):
                celdas_html += '<div></div>'
            celdas_html += "</div>"

        st.markdown(
            f'<div style="background:#fff;border:1px solid #e2e8f0;border-radius:18px;padding:18px 20px;margin:0.75rem 0;">'
            f'<div style="font-size:0.78rem;font-weight:700;color:#0f172a;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:14px;">Ficha del pedido seleccionado</div>'
            f'{celdas_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Resto de vistas del expediente ──
        st.markdown(html_avance_actual(row), unsafe_allow_html=True)
        st.markdown(html_linea_pedido(row), unsafe_allow_html=True)
        st.markdown(html_diagrama_tat(row), unsafe_allow_html=True)

        st.markdown("#### Etapas de estado detalladas")
        components.html(html_estado_pedido_iframe(row), height=220, scrolling=False)

        with st.expander("Registro completo del pedido (todos los campos)", expanded=False):
            reg = row.to_frame(name="Valor").reset_index().rename(columns={"index":"Campo"})
            reg["Valor"] = reg["Valor"].apply(formato_valor)
            st.dataframe(reg, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════
# TAB 5 — ESTADÍSTICA POR MATERIAL
# ══════════════════════════════════════════════════════════
with tab5:
    st.markdown("#### Estadística por Material · tiempo desde inicio del pedido")
    st.caption("Tiempo en días desde la fecha de solicitud hasta recepción (o hasta hoy si no hay recepción).")

    if COL_MATERIAL not in df_filtrado.columns or "tiempo_transcurrido_tat_dias" not in df_filtrado.columns:
        st.warning("Faltan columnas necesarias para esta estadística.")
    else:
        base_mat = df_filtrado.copy()
        base_mat["_mat"] = base_mat[COL_MATERIAL].apply(formato_id)
        base_mat["_dias"] = pd.to_numeric(base_mat["tiempo_transcurrido_tat_dias"], errors="coerce")
        base_mat = base_mat[base_mat["_dias"].notna() & base_mat["_mat"].astype(str).str.strip().ne("") & ~base_mat["_mat"].astype(str).str.lower().isin(["-","nan","none","nat"])]

        if base_mat.empty:
            st.info("No hay datos suficientes para calcular estadísticas por material.")
        else:
            stats = (
                base_mat.groupby("_mat",dropna=False)["_dias"]
                .agg(Registros="count", Min="min", Media="mean", Mediana="median", Max="max", Desv_Std="std")
                .reset_index().rename(columns={"_mat":"Material"})
            )
            stats["Desv_Std"] = stats["Desv_Std"].fillna(0)
            if COL_TEXTO in base_mat.columns:
                desc = base_mat.sort_values("_dias",ascending=False).groupby("_mat")[COL_TEXTO].first().reset_index().rename(columns={"_mat":"Material",COL_TEXTO:"Descripción"})
                stats = stats.merge(desc, on="Material", how="left")
            for c in ["Min","Media","Mediana","Max","Desv_Std"]: stats[c] = stats[c].round(1)
            stats = stats.sort_values(["Media","Max"], ascending=[False,False])
            cols_ordenadas = columnas_existentes(stats, ["Material","Descripción","Registros","Min","Media","Mediana","Max","Desv_Std"])
            stats = stats[cols_ordenadas]

            tiempo_global = base_mat["_dias"]
            sg1, sg2, sg3, sg4, sg5, sg6 = st.columns(6)
            sg1.metric("Materiales",      f"{len(stats):,}".replace(",","."))
            sg2.metric("Registros",       f"{len(base_mat):,}".replace(",","."))
            sg3.metric("MIN días",        formato_numero_corto(tiempo_global.min(),1))
            sg4.metric("MEDIA días",      formato_numero_corto(tiempo_global.mean(),1))
            sg5.metric("MEDIANA días",    formato_numero_corto(tiempo_global.median(),1))
            sg6.metric("MAX días",        formato_numero_corto(tiempo_global.max(),1))

            st.markdown("---")
            st.dataframe(stats, use_container_width=True, hide_index=True)

            sm1, sm2 = st.columns(2)
            with sm1: st.download_button("⬇ CSV · Estadística por material", data=dataframe_a_csv(stats), file_name="estadistica_material.csv", mime="text/csv", use_container_width=True)
            with sm2: st.download_button("⬇ Excel · Estadística por material", data=dataframe_a_excel(stats), file_name="estadistica_material.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

            with st.expander("Distribución visual por número de registros (Top 20)", expanded=False):
                top20 = stats.head(20).set_index("Material")["Registros"]
                st.bar_chart(top20)
