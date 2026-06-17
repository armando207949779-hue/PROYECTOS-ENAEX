# ============================================================
# 07_FILTRO
# Filtro, búsqueda y expediente de seguimiento TAT
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

import base64
from html import escape
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


# ============================================================
# Rutas
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# ============================================================
# Columnas principales
# ============================================================

COL_SOLPED = "Solicitud de pedido - ME5A"
COL_OC_ME5A = "Pedido - ME5A"
COL_OC_ME80FN = "Documento de compras - ME80FN"
COL_OC_NME80FN = "Documento de compras - NME80FN"

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

COL_CANTIDAD = "Cantidad solicitada - ME5A"
COL_UNIDAD = "Unidad de medida - ME5A"
COL_PRECIO_VALORACION = "Precio de valoración"
COL_MONEDA = "Moneda - ME5A"


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
# Estilos Streamlit
# ============================================================

ESTILOS_GLOBALES = """
<style>
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif !important;
}

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
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}

div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #0f172a !important;
    font-size: 1.55rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.02em !important;
}

[data-testid="stDataFrame"] {
    border-radius: 12px !important;
    overflow: hidden !important;
    border: 1px solid #e2e8f0 !important;
}

[data-testid="stForm"] {
    background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(15,23,42,0.04);
}

[data-testid="stFormSubmitButton"] button,
[data-testid="stButton"] button {
    border-radius: 12px !important;
    font-weight: 800 !important;
}

div[data-testid="stInfo"],
div[data-testid="stWarning"],
div[data-testid="stSuccess"],
div[data-testid="stError"] {
    border-radius: 14px !important;
    font-weight: 600 !important;
}
</style>
"""

st.markdown(ESTILOS_GLOBALES, unsafe_allow_html=True)


# ============================================================
# CSS componentes HTML
# ============================================================

CSS_COMPONENTES = """
<style>
html,body{
    margin:0;
    padding:0;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    color:#0f172a;
    background:transparent;
}
*{box-sizing:border-box;}

.hero{
    background:
        radial-gradient(circle at top left,rgba(239,62,82,.18),transparent 30%),
        radial-gradient(circle at top right,rgba(37,99,235,.20),transparent 34%),
        linear-gradient(135deg,#fff7ed 0%,#ffffff 44%,#eff6ff 100%);
    border:1px solid #bfdbfe;
    border-radius:24px;
    padding:22px 26px;
    box-shadow:0 4px 14px rgba(15,23,42,.07);
}
.hero-eyebrow{
    color:#ef3e52;
    font-size:.72rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.08em;
    margin-bottom:6px;
}
.hero-title{
    color:#0f172a;
    font-size:1.65rem;
    font-weight:900;
    letter-spacing:-.03em;
    margin-bottom:6px;
}
.hero-text{
    color:#475569;
    font-size:.95rem;
    line-height:1.45;
    max-width:980px;
}
.hero-pill{
    display:inline-block;
    margin-top:12px;
    padding:6px 12px;
    border-radius:999px;
    background:#fee2e2;
    color:#991b1b;
    border:1px solid #fecaca;
    font-size:.74rem;
    font-weight:900;
}

.message-card{
    background:
        radial-gradient(circle at top right,rgba(37,99,235,.14),transparent 30%),
        linear-gradient(180deg,#eff6ff 0%,#fff 100%);
    border:1px solid #bfdbfe;
    border-left:5px solid #2563eb;
    border-radius:16px;
    padding:14px 16px;
}
.message-title{
    font-size:.86rem;
    font-weight:900;
    color:#1e3a8a;
    margin-bottom:3px;
}
.message-text{
    font-size:.86rem;
    color:#475569;
    line-height:1.4;
}

.search-card{
    background:
        radial-gradient(circle at top right,rgba(6,182,212,.18),transparent 28%),
        linear-gradient(180deg,#f8fafc 0%,#fff 100%);
    border:1px solid #bae6fd;
    border-left:5px solid #06b6d4;
    border-radius:16px;
    padding:14px 16px;
}
.search-title{
    color:#0e7490;
    font-size:.82rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.06em;
    margin-bottom:4px;
}
.search-text{
    color:#475569;
    font-size:.88rem;
    line-height:1.45;
}

.alert-panel{
    border-radius:18px;
    padding:18px 20px;
    box-shadow:0 2px 8px rgba(15,23,42,.07);
}
.alert-red{
    background:radial-gradient(circle at top right,rgba(239,62,82,.22),transparent 32%),linear-gradient(180deg,#fff1f2 0%,#fff 100%);
    border:1px solid #fecdd3;
    border-left:7px solid #ef3e52;
}
.alert-orange{
    background:radial-gradient(circle at top right,rgba(249,115,22,.22),transparent 32%),linear-gradient(180deg,#fff7ed 0%,#fff 100%);
    border:1px solid #fed7aa;
    border-left:7px solid #f97316;
}
.alert-yellow{
    background:radial-gradient(circle at top right,rgba(234,179,8,.22),transparent 32%),linear-gradient(180deg,#fefce8 0%,#fff 100%);
    border:1px solid #fde68a;
    border-left:7px solid #eab308;
}
.alert-green{
    background:radial-gradient(circle at top right,rgba(34,197,94,.22),transparent 32%),linear-gradient(180deg,#f0fdf4 0%,#fff 100%);
    border:1px solid #bbf7d0;
    border-left:7px solid #22c55e;
}
.alert-blue{
    background:radial-gradient(circle at top right,rgba(37,99,235,.22),transparent 32%),linear-gradient(180deg,#eff6ff 0%,#fff 100%);
    border:1px solid #bfdbfe;
    border-left:7px solid #2563eb;
}
.alert-gray{
    background:radial-gradient(circle at top right,rgba(100,116,139,.16),transparent 32%),linear-gradient(180deg,#f8fafc 0%,#fff 100%);
    border:1px solid #e2e8f0;
    border-left:7px solid #64748b;
}
.alert-title{
    font-size:.78rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.07em;
    color:#475569;
    margin-bottom:5px;
}
.alert-main{
    font-size:1.25rem;
    font-weight:900;
    color:#0f172a;
    line-height:1.25;
    margin-bottom:8px;
}
.alert-text{
    font-size:.90rem;
    color:#334155;
    line-height:1.45;
}
.alert-grid{
    display:grid;
    grid-template-columns:repeat(4,minmax(130px,1fr));
    gap:10px;
    margin-top:14px;
}
.alert-item{
    background:rgba(255,255,255,.80);
    border:1px solid rgba(226,232,240,.95);
    border-radius:13px;
    padding:10px 12px;
}

.exp-header{
    background:#fff;
    border:1px solid #e2e8f0;
    border-radius:18px;
    padding:18px 20px;
    box-shadow:0 1px 4px rgba(15,23,42,.04);
}
.exp-header-title{
    font-size:1.08rem;
    font-weight:900;
    color:#0f172a;
    margin-bottom:3px;
}
.exp-header-sub{
    font-size:.84rem;
    color:#64748b;
    margin-bottom:14px;
}
.exp-fields{
    display:grid;
    grid-template-columns:repeat(5,minmax(110px,1fr));
    gap:8px;
}
.exp-field{
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:12px;
    padding:10px 12px;
}
.exp-field-blue{background:#eff6ff;border-color:#bfdbfe;}
.exp-field-red{background:#fff1f2;border-color:#fecdd3;}
.exp-field-green{background:#f0fdf4;border-color:#bbf7d0;}
.exp-field-orange{background:#fff7ed;border-color:#fed7aa;}
.exp-field-purple{background:#faf5ff;border-color:#e9d5ff;}
.exp-field-yellow{background:#fefce8;border-color:#fde68a;}
.exp-field-cyan{background:#ecfeff;border-color:#a5f3fc;}
.exp-field-label{
    color:#64748b;
    font-size:.67rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.05em;
    margin-bottom:4px;
}
.exp-field-value{
    color:#0f172a;
    font-size:.94rem;
    font-weight:850;
    line-height:1.2;
    overflow-wrap:anywhere;
}

.exp-kpis{
    display:grid;
    grid-template-columns:repeat(5,minmax(130px,1fr));
    gap:10px;
}
.exp-kpi{
    background:#fff;
    border:1px solid #e2e8f0;
    border-radius:14px;
    padding:13px 14px;
    position:relative;
    overflow:hidden;
}
.exp-kpi::before{
    content:"";
    position:absolute;
    top:0;
    left:0;
    width:100%;
    height:4px;
    background:#94a3b8;
}
.exp-kpi-blue{background:linear-gradient(180deg,#eff6ff 0%,#fff 100%);border-color:#bfdbfe;}
.exp-kpi-blue::before{background:#2563eb;}
.exp-kpi-red{background:linear-gradient(180deg,#fff1f2 0%,#fff 100%);border-color:#fecdd3;}
.exp-kpi-red::before{background:#ef3e52;}
.exp-kpi-orange{background:linear-gradient(180deg,#fff7ed 0%,#fff 100%);border-color:#fed7aa;}
.exp-kpi-orange::before{background:#f97316;}
.exp-kpi-green{background:linear-gradient(180deg,#f0fdf4 0%,#fff 100%);border-color:#bbf7d0;}
.exp-kpi-green::before{background:#22c55e;}
.exp-kpi-purple{background:linear-gradient(180deg,#faf5ff 0%,#fff 100%);border-color:#e9d5ff;}
.exp-kpi-purple::before{background:#9333ea;}
.exp-kpi-label{
    color:#64748b;
    font-size:.67rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.05em;
    margin-bottom:5px;
}
.exp-kpi-value{
    color:#0f172a;
    font-size:1.05rem;
    font-weight:900;
    line-height:1.2;
    overflow-wrap:anywhere;
}
.exp-kpi-note{
    color:#64748b;
    font-size:.73rem;
    margin-top:4px;
    line-height:1.3;
}

.avance-card{
    background:#fff;
    border:1px solid #dbeafe;
    border-left:5px solid #2563eb;
    border-radius:16px;
    padding:15px 18px;
}
.avance-title{
    color:#1e3a8a;
    font-size:.78rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.05em;
    margin-bottom:10px;
}
.avance-grid{
    display:grid;
    grid-template-columns:repeat(4,minmax(130px,1fr));
    gap:10px;
}
.avance-item{
    background:#f8fafc;
    border:1px solid #e2e8f0;
    border-radius:12px;
    padding:10px 11px;
}
.avance-label{
    color:#64748b;
    font-size:.67rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.04em;
    margin-bottom:3px;
}
.avance-value{
    color:#0f172a;
    font-size:.92rem;
    font-weight:850;
    overflow-wrap:anywhere;
}
.avance-note{
    color:#475569;
    font-size:.84rem;
    line-height:1.4;
    margin-top:10px;
}

.critico-selected{
    background:linear-gradient(180deg,#fef2f2 0%,#fff 100%);
    border:1px solid #fecaca;
    border-left:7px solid #dc2626;
    border-radius:18px;
    padding:15px 18px;
}
.critico-title{
    color:#7f1d1d;
    font-size:.78rem;
    font-weight:900;
    text-transform:uppercase;
    letter-spacing:.05em;
    margin-bottom:10px;
}
.critico-grid{
    display:grid;
    grid-template-columns:repeat(5,minmax(120px,1fr));
    gap:8px;
}
.critico-field{
    background:#fff;
    border:1px solid #fee2e2;
    border-radius:12px;
    padding:9px 11px;
}

.pipe-card{
    background:linear-gradient(180deg,#f0fdf4 0%,#fff 100%);
    border:1px solid #bbf7d0;
    border-radius:18px;
    padding:18px 20px 16px;
}
.pipe-title{
    font-size:.78rem;
    font-weight:900;
    color:#14532d;
    text-transform:uppercase;
    letter-spacing:.06em;
    margin-bottom:14px;
}
.pipe-line{
    display:flex;
    align-items:flex-start;
    width:100%;
    overflow-x:auto;
}
.pipe-step{
    flex:0 0 108px;
    text-align:center;
    min-width:0;
}
.pipe-dot{
    width:48px;
    height:48px;
    border-radius:50%;
    margin:0 auto 8px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:900;
    font-size:1.4rem;
}
.pipe-dot-ok{background:#22c55e;color:#fff;border:3px solid #22c55e;}
.pipe-dot-active{background:#fff;color:#15803d;border:5px solid #22c55e;}
.pipe-dot-nd{background:#fff;color:#94a3b8;border:4px solid #cbd5e1;}
.pipe-label{
    font-size:.78rem;
    font-weight:900;
    color:#1f2937;
    text-transform:uppercase;
}
.pipe-date{
    color:#64748b;
    font-size:.72rem;
    margin-top:3px;
    overflow-wrap:anywhere;
}
.pipe-conn{
    flex:1;
    height:5px;
    min-width:24px;
    margin-top:22px;
    border-radius:99px;
    background:#cbd5e1;
}
.pipe-conn-ok{background:#22c55e;}
.pipe-conn-dashed{background:repeating-linear-gradient(90deg,#22c55e 0 14px,transparent 14px 22px);}
.pipe-note{
    color:#475569;
    font-size:.82rem;
    line-height:1.4;
    margin-top:12px;
}

.tat-card{
    background:
        radial-gradient(circle at top left,rgba(37,99,235,.16),transparent 28%),
        linear-gradient(180deg,#f8fafc 0%,#fff 100%);
    border:1px solid #dbeafe;
    border-radius:18px;
    padding:18px 20px 16px;
}
.tat-card-title{
    font-size:.78rem;
    font-weight:900;
    color:#1e3a8a;
    text-transform:uppercase;
    letter-spacing:.06em;
    margin-bottom:14px;
}
.tat-flow{
    display:flex;
    align-items:stretch;
    width:100%;
    overflow-x:auto;
    padding-bottom:4px;
}
.tat-step{
    flex:0 0 142px;
    text-align:center;
    min-width:0;
}
.tat-dot{
    width:48px;
    height:48px;
    border-radius:50%;
    margin:0 auto 8px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:900;
    font-size:1rem;
}
.tat-dot-ok{background:#22c55e;color:#fff;border:3px solid #22c55e;}
.tat-dot-bad{background:#fef2f2;color:#991b1b;border:4px solid #ef4444;}
.tat-dot-risk{background:#fff7ed;color:#c2410c;border:4px solid #fb923c;}
.tat-dot-active{background:#fff;color:#1d4ed8;border:5px solid #3b82f6;}
.tat-dot-nd{background:#fff;color:#94a3b8;border:4px solid #cbd5e1;}
.tat-step-label{
    font-size:.75rem;
    font-weight:900;
    color:#1f2937;
    text-transform:uppercase;
}
.tat-step-date{
    color:#475569;
    font-size:.70rem;
    line-height:1.22;
    margin-top:3px;
    overflow-wrap:anywhere;
}
.tat-step-detail{
    color:#334155;
    font-size:.70rem;
    line-height:1.22;
    margin-top:4px;
}
.tat-conn{
    flex:1;
    height:5px;
    min-width:28px;
    margin-top:22px;
    border-radius:99px;
    background:#cbd5e1;
}
.tat-conn-ok{background:#22c55e;}
.tat-conn-active{background:repeating-linear-gradient(90deg,#3b82f6 0 14px,transparent 14px 22px);}
.tat-note{
    color:#475569;
    font-size:.82rem;
    line-height:1.4;
    margin-top:12px;
}

.stage-grid{
    display:grid;
    grid-template-columns:repeat(6,minmax(130px,1fr));
    gap:8px;
}
.stage{
    border-radius:14px;
    padding:12px 13px;
    border:1px solid #e5e7eb;
    min-height:140px;
    position:relative;
}
.stage::after{
    content:"→";
    position:absolute;
    right:-7px;
    top:50%;
    transform:translateY(-50%);
    color:#94a3b8;
    font-weight:900;
}
.stage:last-child::after{content:"";}
.stage-green{background:#f0fdf4;border-color:#bbf7d0;}
.stage-red{background:#fef2f2;border-color:#fecaca;}
.stage-yellow{background:#fefce8;border-color:#fde68a;}
.stage-gray{background:#f8fafc;border-color:#e2e8f0;}
.stage-blue{background:#eff6ff;border-color:#bfdbfe;}
.stage-title{
    font-size:.78rem;
    font-weight:900;
    color:#0f172a;
    margin-bottom:5px;
}
.stage-date{
    font-size:1rem;
    font-weight:900;
    color:#111827;
    margin-bottom:4px;
}
.stage-note{
    color:#64748b;
    font-size:.72rem;
    line-height:1.25;
    min-height:26px;
    margin-bottom:8px;
}
.stage-days{
    font-size:.84rem;
    color:#334155;
    margin-bottom:6px;
}
.pill{
    display:inline-block;
    border-radius:999px;
    padding:3px 9px;
    font-size:.72rem;
    font-weight:900;
    border:1px solid transparent;
    white-space:nowrap;
}
.pill-green{background:#dcfce7;color:#166534;border-color:#bbf7d0;}
.pill-red{background:#fee2e2;color:#991b1b;border-color:#fecaca;}
.pill-yellow{background:#fef9c3;color:#854d0e;border-color:#fde68a;}
.pill-gray{background:#f1f5f9;color:#475569;border-color:#e2e8f0;}
.pill-blue{background:#dbeafe;color:#1e40af;border-color:#bfdbfe;}

@media(max-width:1200px){
    .exp-fields,.exp-kpis,.alert-grid,.avance-grid,.critico-grid{grid-template-columns:repeat(2,minmax(120px,1fr));}
    .stage-grid{grid-template-columns:repeat(3,minmax(130px,1fr));}
}
@media(max-width:760px){
    .exp-fields,.exp-kpis,.alert-grid,.avance-grid,.critico-grid,.stage-grid{grid-template-columns:1fr;}
    .stage::after{content:"↓";right:50%;bottom:-12px;top:auto;transform:translateX(50%);}
    .stage:last-child::after{content:"";}
}
</style>
"""


# ============================================================
# Render HTML seguro
# ============================================================

def render_html(contenido: str, height: int, scrolling: bool = False):
    html = f"""
    <!doctype html>
    <html>
    <head>
        <meta charset="utf-8">
        {CSS_COMPONENTES}
    </head>
    <body>
        {contenido}
    </body>
    </html>
    """

    components.html(
        html,
        height=height,
        scrolling=scrolling,
    )


# ============================================================
# Logo exacto
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
# Utilidades
# ============================================================

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

    return f"{codigo} · {nombre}" if nombre else codigo


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
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

    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = df[col].astype("string").str.replace("NME80FN", "ME80FN", regex=False)
            except Exception:
                pass

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

    texto = str(valor).strip()

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto if texto else "-"


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

    return texto if texto else "-"


def valor_numerico(valor: Any) -> float:
    try:
        return float(pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0])
    except Exception:
        return np.nan


def formato_monto(valor: Any, moneda: Any = None) -> str:
    numero = valor_numerico(valor)

    if pd.isna(numero):
        return "-"

    monto = f"{int(round(numero)):,}".replace(",", ".")
    moneda_txt = formato_valor(moneda)

    if moneda_txt == "-":
        return monto

    return f"{monto} {moneda_txt}"


def fecha_texto_simple(valor: Any) -> str:
    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return "Sin fecha calculable"

    return fecha.strftime("%d-%m-%Y")


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


def html_texto(valor: Any) -> str:
    return escape(formato_valor(valor))


def html_id(valor: Any) -> str:
    return escape(formato_id(valor))


def normalizar_valor_busqueda(valor) -> str:
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().lower()

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto


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

        if meses < 12:
            meses_txt = (
                f"{meses:,.1f}"
                .replace(",", "X")
                .replace(".", ",")
                .replace("X", ".")
            )

            return f"{texto_dias} días · {meses_txt} meses aprox."

        anos = meses / 12

        anos_txt = (
            f"{anos:,.1f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        meses_txt = (
            f"{meses:,.1f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        return f"{texto_dias} días · {meses_txt} meses · {anos_txt} años aprox."

    return f"{texto_dias} días"


def formato_tiempo_transcurrido(dias: Any) -> str:
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


def texto_dias_restantes(dias_restantes: Any) -> str:
    valor = valor_numerico(dias_restantes)

    if pd.isna(valor):
        return "Sin dato"

    valor_int = int(round(valor))

    if valor_int >= 0:
        return f"{valor_int:,} días disponibles".replace(",", ".")

    return f"{abs(valor_int):,} días sobre el umbral".replace(",", ".")


def formato_dias_restantes_operativo(dias: Any) -> str:
    valor = valor_numerico(dias)

    if pd.isna(valor):
        return "Sin dato"

    if valor < 0:
        return f"Vencido hace {formato_tiempo_transcurrido(abs(valor))}"

    if valor == 0:
        return "Vence hoy"

    return f"Vence en {formato_tiempo_transcurrido(valor)}"


def formatear_exceso_umbral(valor) -> str:
    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return "Sin dato"

    numero = int(round(float(numero)))

    if numero >= 0:
        return f"{numero:,} días sobre el umbral".replace(",", ".")

    return f"{abs(numero):,} días disponibles".replace(",", ".")


def nombre_fecha_faltante(columna: str) -> str:
    mapa = {
        "fecha_solicitud_final": "fecha de solicitud",
        "fecha_liberacion_final": "fecha de liberación",
        "fecha_pedido_final": "fecha de pedido",
        "fecha_facturacion_final": "fecha de facturación",
        "fecha_recepcion_final": "fecha de recepción",
    }

    return mapa.get(columna, "fecha pendiente")


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
    dias_num = valor_numerico(dias)
    umbral_num = valor_numerico(umbral) if umbral is not None else np.nan

    if pd.isna(dias_num) or dias_num < 0:
        return "gray"

    if pd.notna(umbral_num):
        return "green" if dias_num <= umbral_num else "red"

    return "green" if dias_num == 0 else "yellow"


def pill(texto: Any, color: str) -> str:
    return f'<span class="pill pill-{color}">{escape(formato_valor(texto))}</span>'


# ============================================================
# Preparación panel Filtro + Alertas
# ============================================================

def primera_columna_existente(df: pd.DataFrame, candidatas: list[str]) -> pd.Series:
    for col in candidatas:
        if col in df.columns:
            return df[col]

    return pd.Series(pd.NaT, index=df.index)


@st.cache_data(show_spinner="Preparando datos del filtro...")
def preparar_panel_filtro(df_original: pd.DataFrame, hoy: pd.Timestamp) -> pd.DataFrame:
    df = limpiar_columnas(df_original.copy())
    df = normalizar_columnas_me80fn(df)
    df = convertir_fechas_visuales(df)

    fecha_recepcion = primera_columna_existente(
        df,
        [
            "fecha_recepcion_final",
            "Fecha recepción mercancía - ME80FN",
            "Fecha recepción mercancía - NME80FN",
        ],
    )

    fecha_recepcion_dt = pd.to_datetime(fecha_recepcion, errors="coerce")

    df[COL_ESTADO_RECEPCION_ALERTA] = np.where(
        fecha_recepcion_dt.notna(),
        "Recepcionado",
        "Sin recepción",
    )

    fecha_inicio = primera_columna_existente(
        df,
        [
            "fecha_solicitud_final",
            "Fecha de solicitud - ME5A",
        ],
    )

    df["fecha_inicio_tat"] = pd.to_datetime(fecha_inicio, errors="coerce")

    if COL_UMBRAL_TAT in df.columns:
        umbral = pd.to_numeric(df[COL_UMBRAL_TAT], errors="coerce")
    else:
        umbral = pd.Series(np.nan, index=df.index, dtype="float64")

    tipo_oc = (
        df[COL_TIPO_OC].astype(str).str.strip().str.replace(".0", "", regex=False)
        if COL_TIPO_OC in df.columns
        else pd.Series("", index=df.index)
    )

    umbral = umbral.mask(umbral.isna() & tipo_oc.isin(["35", "45"]), 40)
    umbral = umbral.mask(umbral.isna() & tipo_oc.eq("47"), 70)

    df["umbral_tat_calculado"] = umbral

    umbral_td = pd.to_timedelta(
        pd.to_numeric(df["umbral_tat_calculado"], errors="coerce"),
        unit="D",
    )

    df["fecha_vencimiento_tat"] = df["fecha_inicio_tat"] + umbral_td

    df["dias_restantes_int"] = (
        df["fecha_vencimiento_tat"] - hoy
    ).dt.days

    df["dias_hasta_vencimiento"] = df["dias_restantes_int"].apply(
        formato_dias_restantes_operativo
    )

    df["fecha_vencimiento_texto"] = df["fecha_vencimiento_tat"].apply(fecha_texto_simple)

    df["dias_restantes_texto"] = df["dias_restantes_int"].apply(texto_dias_restantes)

    df["tiempo_transcurrido_dias"] = np.where(
        df[COL_ESTADO_RECEPCION_ALERTA].eq("Recepcionado"),
        (fecha_recepcion_dt - df["fecha_inicio_tat"]).dt.days,
        (hoy - df["fecha_inicio_tat"]).dt.days,
    )

    df["tiempo_transcurrido_tat"] = df["tiempo_transcurrido_dias"].apply(
        texto_dias_y_meses
    )

    df["tiempo_excedido_umbral_dias"] = (
        pd.to_numeric(df["tiempo_transcurrido_dias"], errors="coerce")
        - pd.to_numeric(df["umbral_tat_calculado"], errors="coerce")
    )

    df["tiempo_excedido_umbral_texto"] = df["tiempo_excedido_umbral_dias"].apply(
        formatear_exceso_umbral
    )

    condiciones_clasificacion = [
        df[COL_ESTADO_RECEPCION_ALERTA].eq("Recepcionado"),
        df["dias_restantes_int"].isna(),
        df["dias_restantes_int"].lt(0),
        df["dias_restantes_int"].eq(0),
        df["dias_restantes_int"].between(1, 2),
        df["dias_restantes_int"].between(3, 7),
        df["dias_restantes_int"].gt(7),
    ]

    valores_clasificacion = [
        "Recepcionado",
        "Sin datos",
        "Vencido",
        "Vence hoy",
        "1-2 días",
        "3-7 días",
        "+7 días",
    ]

    df["clasificacion_vencimiento"] = np.select(
        condiciones_clasificacion,
        valores_clasificacion,
        default="Sin datos",
    )

    condiciones_nivel = [
        df[COL_ESTADO_RECEPCION_ALERTA].eq("Recepcionado"),
        df["dias_restantes_int"].isna(),
        df["dias_restantes_int"].lt(0),
        df["dias_restantes_int"].between(0, 7),
        df["dias_restantes_int"].between(8, 30),
        df["dias_restantes_int"].gt(30),
    ]

    valores_nivel = [
        "Cerrado",
        "Datos incompletos",
        "Crítico",
        "Atención",
        "Seguimiento",
        "Controlado",
    ]

    df["nivel_alerta"] = np.select(
        condiciones_nivel,
        valores_nivel,
        default="Sin datos",
    )

    fechas_etapas = [
        ("Solicitud", "fecha_solicitud_final"),
        ("Liberación", "fecha_liberacion_final"),
        ("Pedido", "fecha_pedido_final"),
        ("Facturación", "fecha_facturacion_final"),
        ("Recepción", "fecha_recepcion_final"),
    ]

    ultimas = []
    ultimas_fechas = []
    pendientes = []

    for _, row in df.iterrows():
        ultima = "Sin etapa registrada"
        ultima_fecha = "Sin fecha"
        pendiente = "Flujo cerrado"

        for nombre, col in fechas_etapas:
            fecha = row.get(col, pd.NaT)

            if pd.notna(fecha):
                ultima = nombre
                ultima_fecha = fecha_texto_simple(fecha)
            else:
                pendiente = nombre
                break

        ultimas.append(ultima)
        ultimas_fechas.append(ultima_fecha)
        pendientes.append(pendiente)

    df["ultima_etapa_registrada"] = ultimas
    df["ultima_fecha_registrada"] = ultimas_fechas
    df["fecha_pendiente"] = pendientes

    df["accion_sugerida"] = np.select(
        [
            df["nivel_alerta"].eq("Crítico"),
            df["nivel_alerta"].eq("Atención"),
            df["nivel_alerta"].eq("Seguimiento"),
            df["nivel_alerta"].eq("Controlado"),
            df["nivel_alerta"].eq("Cerrado"),
        ],
        [
            "Gestionar recepción o regularización inmediata",
            "Revisar etapa pendiente y anticipar gestión",
            "Mantener seguimiento preventivo",
            "Control operativo normal",
            "Sin acción urgente",
        ],
        default="Revisar datos base",
    )

    df["causa_probable"] = np.where(
        df["fecha_pendiente"].eq("Liberación"),
        "Pendiente de liberación/aprobación",
        np.where(
            df["fecha_pendiente"].eq("Pedido"),
            "Pendiente de emisión de pedido",
            np.where(
                df["fecha_pendiente"].eq("Facturación"),
                "Pendiente de facturación proveedor",
                np.where(
                    df["fecha_pendiente"].eq("Recepción"),
                    "Pendiente de recepción logística",
                    "Sin causa probable",
                ),
            ),
        ),
    )

    df["score_riesgo"] = 0

    df.loc[df["nivel_alerta"].eq("Crítico"), "score_riesgo"] += 100
    df.loc[df["nivel_alerta"].eq("Atención"), "score_riesgo"] += 70
    df.loc[df["nivel_alerta"].eq("Seguimiento"), "score_riesgo"] += 40
    df.loc[df["nivel_alerta"].eq("Controlado"), "score_riesgo"] += 10

    df["score_riesgo"] += (
        pd.to_numeric(df["tiempo_excedido_umbral_dias"], errors="coerce")
        .fillna(0)
        .clip(lower=0)
        .astype(int)
    )

    return df


# ============================================================
# HTML Expediente
# ============================================================

def html_hero() -> str:
    return """
    <div class="hero">
        <div class="hero-eyebrow">Flujo operativo Alertas → Filtro</div>
        <div class="hero-title">07_FILTRO · Expediente TAT</div>
        <div class="hero-text">
            Alertas identifica los casos críticos, vencidos o próximos a vencer. 
            Filtro permite abrir el expediente específico de la SOLPED para revisar compra, responsables,
            fechas, etapas, estado TAT y acción sugerida.
        </div>
        <div class="hero-pill">Detectar en Alertas → Investigar en Filtro → Gestionar</div>
    </div>
    """


def html_search_intro() -> str:
    return """
    <div class="search-card">
        <div class="search-title">Búsqueda específica de expediente</div>
        <div class="search-text">
            Busca una SOLPED, pedido, posición, material o descripción. 
            Esta vista está pensada para complementar la pestaña Alertas con una revisión más profunda del registro.
        </div>
    </div>
    """


def html_message_card(titulo: str, texto: str) -> str:
    return f"""
    <div class="message-card">
        <div class="message-title">{escape(titulo)}</div>
        <div class="message-text">{escape(texto)}</div>
    </div>
    """


def html_alerta_operativa(row: pd.Series) -> str:
    nivel = formato_valor(row.get("nivel_alerta", np.nan))
    clase = "alert-gray"

    if nivel == "Crítico":
        clase = "alert-red"
        titulo = "Caso crítico detectado"
    elif nivel == "Atención":
        clase = "alert-orange"
        titulo = "Caso por vencer"
    elif nivel == "Seguimiento":
        clase = "alert-yellow"
        titulo = "Caso en seguimiento"
    elif nivel == "Controlado":
        clase = "alert-blue"
        titulo = "Caso controlado"
    elif nivel == "Cerrado":
        clase = "alert-green"
        titulo = "Caso cerrado"
    else:
        titulo = "Caso con datos incompletos"

    mensaje = formato_valor(row.get("accion_sugerida", "Revisar detalle del registro"))

    return f"""
    <div class="alert-panel {clase}">
        <div class="alert-title">Lectura operativa desde Alertas</div>
        <div class="alert-main">{escape(titulo)}</div>
        <div class="alert-text">{escape(mensaje)}</div>

        <div class="alert-grid">
            <div class="alert-item">
                <div class="exp-field-label">Nivel alerta</div>
                <div class="exp-field-value">{html_texto(row.get("nivel_alerta", np.nan))}</div>
            </div>
            <div class="alert-item">
                <div class="exp-field-label">Estado vencimiento</div>
                <div class="exp-field-value">{html_texto(row.get("clasificacion_vencimiento", np.nan))}</div>
            </div>
            <div class="alert-item">
                <div class="exp-field-label">Desde solicitud hasta hoy</div>
                <div class="exp-field-value">{html_texto(row.get("tiempo_transcurrido_tat", np.nan))}</div>
            </div>
            <div class="alert-item">
                <div class="exp-field-label">Vencimiento</div>
                <div class="exp-field-value">{html_texto(row.get("dias_hasta_vencimiento", np.nan))}</div>
            </div>
        </div>
    </div>
    """


def html_resumen_expediente(row: pd.Series) -> str:
    oc_principal = row.get(COL_OC_ME5A, row.get(COL_OC_ME80FN, np.nan))
    moneda = row.get(COL_MONEDA, np.nan)

    campos = [
        ("Solicitud de pedido", row.get(COL_SOLPED, np.nan), "exp-field-blue"),
        ("Pedido", oc_principal, "exp-field-blue"),
        ("Posición SolPed", row.get(COL_POS_SOLPED, np.nan), "exp-field-cyan"),
        ("Posición pedido", row.get(COL_POS_OC, np.nan), "exp-field-cyan"),
        ("Centro", etiqueta_centro(row.get(COL_CENTRO, np.nan)), "exp-field-green"),
        ("Material", row.get(COL_MATERIAL, np.nan), "exp-field-purple"),
        ("Descripción", row.get(COL_TEXTO, np.nan), "exp-field-purple"),
        ("Cantidad solicitada", row.get(COL_CANTIDAD, np.nan), "exp-field-green"),
        ("Unidad de medida", row.get(COL_UNIDAD, np.nan), "exp-field-green"),
        ("Precio valoración", formato_monto(row.get(COL_PRECIO_VALORACION, np.nan), moneda), "exp-field-yellow"),
        ("Monto", formato_monto(row.get(COL_MONTO, np.nan), moneda), "exp-field-yellow"),
        ("Moneda", moneda, "exp-field-yellow"),
        ("Solicitante", row.get(COL_SOLICITANTE, np.nan), "exp-field-orange"),
        ("Autor", row.get(COL_AUTOR, np.nan), "exp-field-orange"),
        ("Grupo compras", row.get(COL_GRUPO_COMPRAS, np.nan), "exp-field-red"),
        ("Tipo OC", row.get(COL_TIPO_OC, np.nan), "exp-field-red"),
        ("Sistema", row.get(COL_SISTEMA, np.nan), "exp-field-blue"),
        ("Origen", row.get(COL_ORIGEN, np.nan), "exp-field-cyan"),
        ("Tipo compra", row.get(COL_NOMBRE_TIPO_COMPRA, np.nan), "exp-field-purple"),
        ("Estado match", row.get(COL_ESTADO_MATCH, np.nan), "exp-field-red"),
    ]

    celdas = []

    for label, value, clase in campos:
        celdas.append(
            f"""
            <div class="exp-field {clase}">
                <div class="exp-field-label">{escape(label)}</div>
                <div class="exp-field-value">{html_texto(value)}</div>
            </div>
            """
        )

    return f"""
    <div class="exp-header">
        <div class="exp-header-title">Expediente · SolPed {html_id(row.get(COL_SOLPED, np.nan))}</div>
        <div class="exp-header-sub">
            Pedido {html_id(oc_principal)} · Posición {html_id(row.get(COL_POS_SOLPED, np.nan))} · Centro {html_texto(etiqueta_centro(row.get(COL_CENTRO, np.nan)))}
        </div>
        <div class="exp-fields">
            {''.join(celdas)}
        </div>
    </div>
    """


def html_kpis_expediente(row: pd.Series) -> str:
    dias_tat = row.get(COL_DIAS_TAT, np.nan)
    performance = row.get(COL_PERF_TAT, np.nan)

    return f"""
    <div class="exp-kpis">
        <div class="exp-kpi exp-kpi-blue">
            <div class="exp-kpi-label">Estado pedido</div>
            <div class="exp-kpi-value">{html_texto(row.get("clasificacion_vencimiento", np.nan))}</div>
            <div class="exp-kpi-note">Vence: {html_texto(row.get("fecha_vencimiento_texto", np.nan))}</div>
        </div>

        <div class="exp-kpi exp-kpi-red">
            <div class="exp-kpi-label">Desde solicitud hasta hoy</div>
            <div class="exp-kpi-value">{html_texto(row.get("tiempo_transcurrido_tat", np.nan))}</div>
            <div class="exp-kpi-note">Cálculo operativo contra la fecha actual</div>
        </div>

        <div class="exp-kpi exp-kpi-orange">
            <div class="exp-kpi-label">Contra umbral</div>
            <div class="exp-kpi-value">{html_texto(row.get("tiempo_excedido_umbral_texto", np.nan))}</div>
            <div class="exp-kpi-note">Umbral: {html_texto(row.get("umbral_tat_calculado", np.nan))} días</div>
        </div>

        <div class="exp-kpi exp-kpi-purple">
            <div class="exp-kpi-label">TAT total</div>
            <div class="exp-kpi-value">{escape(texto_dias_y_meses(dias_tat))}</div>
            <div class="exp-kpi-note">Performance: {html_texto(performance)}</div>
        </div>

        <div class="exp-kpi exp-kpi-green">
            <div class="exp-kpi-label">Última etapa</div>
            <div class="exp-kpi-value">{html_texto(row.get("ultima_etapa_registrada", np.nan))}</div>
            <div class="exp-kpi-note">Pendiente: {html_texto(row.get("fecha_pendiente", np.nan))}</div>
        </div>
    </div>
    """


def obtener_avance_pedido(row: pd.Series) -> dict:
    completadas = [
        (nombre, col, pd.notna(row.get(col, np.nan)))
        for nombre, col in ETAPAS_LINEA_PEDIDO
    ]

    registradas = [i for i in completadas if i[2]]
    pendientes = [i for i in completadas if not i[2]]

    ultima_nombre, ultima_columna, _ = registradas[-1] if registradas else (
        "Sin etapa registrada",
        "",
        False,
    )

    siguiente_nombre, siguiente_columna, _ = pendientes[0] if pendientes else (
        "Cerrado",
        "",
        False,
    )

    fecha_inicio = fecha_valida(row, "fecha_solicitud_final")
    fecha_ultima = fecha_valida(row, ultima_columna) if ultima_columna else pd.NaT

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
        "ultima_fecha": fecha_etapa_texto(row, ultima_columna) if ultima_columna else "-",
        "siguiente_etapa": siguiente_nombre,
        "siguiente_columna": siguiente_columna,
        "dias_parcial": dias_parcial,
        "dias_restantes": dias_restantes,
        "umbral_tat": umbral,
        "esta_cerrado": esta_cerrado,
    }


def diagnostico_avance(row: pd.Series) -> str:
    avance = obtener_avance_pedido(row)

    if avance["esta_cerrado"]:
        return "El pedido ya tiene recepción registrada. El TAT total está cerrado."

    falta = nombre_fecha_faltante(avance["siguiente_columna"])

    dias_restantes = valor_numerico(avance["dias_restantes"])
    umbral = valor_numerico(avance.get("umbral_tat", np.nan))

    if pd.isna(umbral):
        return f"Falta {falta}. No se pudo determinar el umbral TAT."

    if pd.notna(dias_restantes):
        if dias_restantes < 0:
            return f"Falta {falta}. El pedido ya supera el umbral TAT de {int(umbral)} días."

        if dias_restantes <= 5:
            return f"Falta {falta}. El pedido está cerca del umbral TAT de {int(umbral)} días."

        return f"Falta {falta}. Quedan {int(dias_restantes)} días disponibles contra el umbral TAT de {int(umbral)} días."

    return f"Última etapa: {avance['ultima_etapa']}. Siguiente: {avance['siguiente_etapa']}."


def html_avance_actual(row: pd.Series) -> str:
    avance = obtener_avance_pedido(row)

    dias_parcial = formato_tiempo_transcurrido(avance["dias_parcial"])
    dias_restantes = texto_dias_restantes(avance["dias_restantes"])
    umbral = avance.get("umbral_tat", np.nan)

    tat_estado = "Cerrado" if avance["esta_cerrado"] else "Pendiente hasta recepción"

    contra_umbral = (
        f"{dias_restantes} · umbral {int(valor_numerico(umbral))} días"
        if pd.notna(valor_numerico(umbral))
        else "Sin dato"
    )

    return f"""
    <div class="avance-card">
        <div class="avance-title">Avance actual</div>
        <div class="avance-grid">
            <div class="avance-item">
                <div class="avance-label">Última etapa</div>
                <div class="avance-value">{escape(avance["ultima_etapa"])} · {escape(avance["ultima_fecha"])}</div>
            </div>
            <div class="avance-item">
                <div class="avance-label">Tiempo transcurrido</div>
                <div class="avance-value">{escape(dias_parcial)}</div>
            </div>
            <div class="avance-item">
                <div class="avance-label">TAT total</div>
                <div class="avance-value">{escape(tat_estado)}</div>
            </div>
            <div class="avance-item">
                <div class="avance-label">Contra umbral TAT</div>
                <div class="avance-value">{escape(contra_umbral)}</div>
            </div>
        </div>
        <div class="avance-note">{escape(diagnostico_avance(row))}</div>
    </div>
    """


def html_critico_seleccionado(row: pd.Series) -> str:
    return f"""
    <div class="critico-selected">
        <div class="critico-title">Pedido crítico seleccionado</div>
        <div class="critico-grid">
            <div class="critico-field">
                <div class="exp-field-label">Nivel / urgencia</div>
                <div class="exp-field-value">{html_texto(row.get("nivel_alerta", np.nan))} · {html_texto(row.get("dias_hasta_vencimiento", np.nan))}</div>
            </div>
            <div class="critico-field">
                <div class="exp-field-label">Tiempo transcurrido</div>
                <div class="exp-field-value">{html_texto(row.get("tiempo_transcurrido_tat", np.nan))}</div>
            </div>
            <div class="critico-field">
                <div class="exp-field-label">Fecha pendiente</div>
                <div class="exp-field-value">{html_texto(row.get("fecha_pendiente", np.nan))}</div>
            </div>
            <div class="critico-field">
                <div class="exp-field-label">Acción sugerida</div>
                <div class="exp-field-value">{html_texto(row.get("accion_sugerida", np.nan))}</div>
            </div>
            <div class="critico-field">
                <div class="exp-field-label">Causa probable</div>
                <div class="exp-field-value">{html_texto(row.get("causa_probable", np.nan))}</div>
            </div>
        </div>
    </div>
    """


def html_linea_pedido(row: pd.Series) -> str:
    completadas = [
        pd.notna(row.get(c, np.nan))
        for _, c in ETAPAS_LINEA_PEDIDO
    ]

    try:
        indice_activo = completadas.index(False)
    except ValueError:
        indice_activo = len(ETAPAS_LINEA_PEDIDO) - 1

    partes = []

    for i, (label, col_fecha) in enumerate(ETAPAS_LINEA_PEDIDO):
        esta_completa = completadas[i]
        es_activa = i == indice_activo and not esta_completa

        dot_class = (
            "pipe-dot-ok"
            if esta_completa
            else ("pipe-dot-active" if es_activa else "pipe-dot-nd")
        )

        icono = "✓" if esta_completa else ""

        partes.append(
            f"""
            <div class="pipe-step">
                <div class="pipe-dot {dot_class}">{icono}</div>
                <div class="pipe-label">{escape(label)}</div>
                <div class="pipe-date">{escape(fecha_etapa_texto(row, col_fecha))}</div>
            </div>
            """
        )

        if i < len(ETAPAS_LINEA_PEDIDO) - 1:
            conn = (
                "pipe-conn-ok"
                if (completadas[i] and completadas[i + 1])
                else ("pipe-conn-dashed" if (completadas[i] and not completadas[i + 1]) else "")
            )

            partes.append(f'<div class="pipe-conn {conn}"></div>')

    estado_tat = formato_valor(row.get(COL_PERF_TAT, np.nan))
    dias_tat = texto_dias_y_meses(row.get(COL_DIAS_TAT, np.nan))

    return f"""
    <div class="pipe-card">
        <div class="pipe-title">Línea de pedido</div>
        <div class="pipe-line">{''.join(partes)}</div>
        <div class="pipe-note">
            TAT total: <strong>{escape(dias_tat)}</strong> · Estado: <strong>{escape(estado_tat)}</strong>
        </div>
    </div>
    """


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


def dot_class_tat(row: pd.Series, etapa: dict, i: int, indice_activo: int) -> tuple:
    fecha_col = etapa.get("fecha")
    completada = bool(fecha_col and pd.notna(row.get(fecha_col, np.nan)))

    perf_col = etapa.get("performance")
    perf = str(row.get(perf_col, "")).strip().lower() if perf_col else ""

    if completada and perf == "no cumple":
        return "tat-dot-bad", "!"

    if completada and perf in ["en proceso", "sin datos"]:
        return "tat-dot-risk", "…"

    if completada:
        return "tat-dot-ok", "✓"

    if i == indice_activo:
        return "tat-dot-active", ""

    return "tat-dot-nd", ""


def html_diagrama_tat(row: pd.Series) -> str:
    completadas = [
        pd.notna(row.get(e.get("fecha"), np.nan))
        for e in ETAPAS_PEDIDO
    ]

    try:
        indice_activo = completadas.index(False)
    except ValueError:
        indice_activo = len(ETAPAS_PEDIDO) - 1

    partes = []

    for i, etapa in enumerate(ETAPAS_PEDIDO):
        dot_class, icono = dot_class_tat(row, etapa, i, indice_activo)

        fecha_txt = (
            fecha_etapa_texto(row, etapa.get("fecha"))
            if etapa.get("fecha")
            else "-"
        )

        dias_col = etapa.get("dias")
        umbral_col = etapa.get("umbral")
        perf_col = etapa.get("performance")

        if dias_col:
            dias_txt = formato_tiempo_transcurrido(row.get(dias_col, np.nan))
            umbral_txt = formato_valor(row.get(umbral_col, np.nan)) if umbral_col else "-"
            perf_txt = formato_valor(row.get(perf_col, np.nan)) if perf_col else "Registrado"

            detalle = f"{dias_txt} · umbral {umbral_txt}d · {perf_txt}"

        else:
            detalle = "Punto de inicio"

        partes.append(
            f"""
            <div class="tat-step">
                <div class="tat-dot {dot_class}">{escape(icono)}</div>
                <div class="tat-step-label">{escape(str(etapa.get("titulo", "")))}</div>
                <div class="tat-step-date">{escape(fecha_txt)}</div>
                <div class="tat-step-detail">{escape(detalle)}</div>
            </div>
            """
        )

        if i < len(ETAPAS_PEDIDO) - 1:
            conn = (
                "tat-conn-ok"
                if (completadas[i] and completadas[i + 1])
                else ("tat-conn-active" if (completadas[i] and not completadas[i + 1]) else "")
            )

            partes.append(f'<div class="tat-conn {conn}"></div>')

    estado_tat = formato_valor(row.get(COL_PERF_TAT, np.nan))
    dias_tat = texto_dias_y_meses(row.get(COL_DIAS_TAT, np.nan))

    return f"""
    <div class="tat-card">
        <div class="tat-card-title">Etapas TAT</div>
        <div class="tat-flow">{''.join(partes)}</div>
        <div class="tat-note">
            TAT total: <strong>{escape(dias_tat)}</strong> · Estado: <strong>{escape(estado_tat)}</strong>
        </div>
    </div>
    """


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
            umbral = html_texto(row.get(umbral_col, np.nan)) if umbral_col else "-"
            fecha_fin_col = etapa.get("fecha")

            if pd.isna(row.get(fecha_fin_col, np.nan)):
                falta = nombre_fecha_faltante(fecha_fin_col)
                dias_txt = f"Pendiente · falta {escape(falta)}"

            elif dias_col == COL_DIAS_TAT:
                dias_txt = f"{escape(texto_dias_y_meses(dias_valor))} · umbral {umbral} días"

            else:
                dias_txt = f"{html_texto(dias_valor)} días · umbral {umbral}"

        else:
            dias_txt = "Punto de inicio"

        perf_val = row.get(perf_col, "Registrado") if perf_col else "Registrado"
        perf_color = clase_performance(perf_val) if perf_col else color

        cards.append(
            f"""
            <div class="stage stage-{color}">
                <div class="stage-title">{escape(etapa["titulo"])}</div>
                <div class="stage-date">{fecha}</div>
                <div class="stage-note">{escape(etapa["nota"])}</div>
                <div class="stage-days">{dias_txt}</div>
                {pill(perf_val, perf_color)}
            </div>
            """
        )

    return f"""
    <div class="stage-grid">
        {''.join(cards)}
    </div>
    """


# ============================================================
# Render componentes expediente
# ============================================================

def mostrar_hero():
    render_html(html_hero(), height=170, scrolling=False)


def mostrar_search_intro():
    render_html(html_search_intro(), height=105, scrolling=False)


def mostrar_message_card(titulo: str, texto: str):
    render_html(html_message_card(titulo, texto), height=95, scrolling=False)


def mostrar_html_panel(contenido: str, height: int, scrolling: bool = False):
    render_html(contenido, height=height, scrolling=scrolling)


def mostrar_expediente(row: pd.Series):
    mostrar_message_card(
        titulo="Expediente confirmado",
        texto="Se abre la vista de seguimiento del registro seleccionado, rescatando ficha, KPIs, avance, línea de pedido, etapas TAT y detalle completo.",
    )

    mostrar_html_panel(
        html_alerta_operativa(row),
        height=260,
        scrolling=False,
    )

    if row.get("nivel_alerta", "") == "Crítico":
        mostrar_html_panel(
            html_critico_seleccionado(row),
            height=180,
            scrolling=False,
        )

    mostrar_html_panel(
        html_resumen_expediente(row),
        height=520,
        scrolling=True,
    )

    mostrar_html_panel(
        html_kpis_expediente(row),
        height=155,
        scrolling=False,
    )

    mostrar_html_panel(
        html_avance_actual(row),
        height=175,
        scrolling=False,
    )

    mostrar_html_panel(
        html_linea_pedido(row),
        height=210,
        scrolling=True,
    )

    mostrar_html_panel(
        html_diagrama_tat(row),
        height=235,
        scrolling=True,
    )

    st.markdown("### Etapas de estado detalladas")
    st.caption("Detalle visual de cada hito del flujo TAT.")

    mostrar_html_panel(
        html_estado_pedido(row),
        height=250,
        scrolling=True,
    )

    st.markdown("### Tabla de fechas principales")

    tabla_fechas = pd.DataFrame(
        [
            {"Fecha": "Solicitud", "Valor": fecha_texto_simple(row.get("fecha_solicitud_final", pd.NaT))},
            {"Fecha": "Liberación", "Valor": fecha_texto_simple(row.get("fecha_liberacion_final", pd.NaT))},
            {"Fecha": "Pedido", "Valor": fecha_texto_simple(row.get("fecha_pedido_final", pd.NaT))},
            {"Fecha": "Facturación", "Valor": fecha_texto_simple(row.get("fecha_facturacion_final", pd.NaT))},
            {"Fecha": "Recepción", "Valor": fecha_texto_simple(row.get("fecha_recepcion_final", pd.NaT))},
            {"Fecha": "Vencimiento TAT", "Valor": fecha_texto_simple(row.get("fecha_vencimiento_tat", pd.NaT))},
        ]
    )

    st.dataframe(
        tabla_fechas,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("### Tabla técnica de etapas TAT")

    tabla_etapas = []

    for etapa in ETAPAS_PEDIDO:
        tabla_etapas.append(
            {
                "Etapa": etapa["titulo"],
                "Fecha": fecha_texto_simple(row.get(etapa["fecha"], pd.NaT)) if etapa.get("fecha") else "-",
                "Días": formato_valor(row.get(etapa["dias"], np.nan)) if etapa.get("dias") else "-",
                "Umbral": formato_valor(row.get(etapa["umbral"], np.nan)) if etapa.get("umbral") else "-",
                "Performance": formato_valor(row.get(etapa["performance"], np.nan)) if etapa.get("performance") else "Registrado",
                "Nota": etapa["nota"],
            }
        )

    st.dataframe(
        pd.DataFrame(tabla_etapas),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Registro completo del pedido", expanded=False):
        registro_completo = (
            row.to_frame(name="Valor")
            .reset_index()
            .rename(columns={"index": "Campo"})
        )

        registro_completo["Valor"] = registro_completo["Valor"].apply(formato_valor)

        st.dataframe(
            registro_completo,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Filtros
# ============================================================

def aplicar_filtro_texto(df: pd.DataFrame, columna: str, texto: str, modo: str) -> pd.DataFrame:
    if columna not in df.columns:
        return df

    texto = str(texto).strip()

    if not texto:
        return df

    serie = df[columna].apply(normalizar_valor_busqueda)
    texto_norm = normalizar_valor_busqueda(texto)

    if modo == "Exacta":
        return df[serie.eq(texto_norm)].copy()

    return df[serie.str.contains(texto_norm, na=False, regex=False)].copy()


def aplicar_filtro_texto_multi(
    df: pd.DataFrame,
    columnas: list[str],
    texto: str,
    modo: str,
) -> pd.DataFrame:
    texto = str(texto).strip()

    if not texto:
        return df

    texto_norm = normalizar_valor_busqueda(texto)

    mascara = pd.Series(False, index=df.index)

    for columna in columnas:
        if columna in df.columns:
            serie = df[columna].apply(normalizar_valor_busqueda)

            if modo == "Exacta":
                mascara = mascara | serie.eq(texto_norm)
            else:
                mascara = mascara | serie.str.contains(texto_norm, na=False, regex=False)

    if not mascara.any():
        return df.iloc[0:0].copy()

    return df[mascara].copy()


def aplicar_filtros_con_progreso(
    df_base: pd.DataFrame,
    filtro_solped: str,
    filtro_pedido: str,
    filtro_posicion: str,
    filtro_material: str,
    filtro_texto: str,
    modo_busqueda: str,
) -> pd.DataFrame:

    barra = st.progress(0, text="Preparando búsqueda...")

    df = df_base.copy()

    barra.progress(15, text="Filtrando SOLPED...")

    df = aplicar_filtro_texto(df, COL_SOLPED, filtro_solped, modo_busqueda)

    barra.progress(32, text="Filtrando pedido...")

    df = aplicar_filtro_texto_multi(
        df,
        [COL_OC_ME5A, COL_OC_ME80FN, COL_OC_NME80FN],
        filtro_pedido,
        modo_busqueda,
    )

    barra.progress(50, text="Filtrando posición...")

    df = aplicar_filtro_texto_multi(
        df,
        [COL_POS_SOLPED, COL_POS_OC],
        filtro_posicion,
        modo_busqueda,
    )

    barra.progress(68, text="Filtrando material...")

    df = aplicar_filtro_texto(df, COL_MATERIAL, filtro_material, modo_busqueda)

    barra.progress(85, text="Filtrando texto breve...")

    df = aplicar_filtro_texto(df, COL_TEXTO, filtro_texto, "Contiene")

    barra.progress(100, text="Búsqueda finalizada.")

    return df


def hay_criterio_busqueda(
    filtro_solped: str,
    filtro_pedido: str,
    filtro_posicion: str,
    filtro_material: str,
    filtro_texto: str,
) -> bool:
    return any(
        str(x).strip()
        for x in [
            filtro_solped,
            filtro_pedido,
            filtro_posicion,
            filtro_material,
            filtro_texto,
        ]
    )


def etiqueta_selector(row: pd.Series) -> str:
    solped = formato_id(row.get(COL_SOLPED, np.nan))
    pedido = formato_id(row.get(COL_OC_ME5A, row.get(COL_OC_ME80FN, np.nan)))
    pos = formato_id(row.get(COL_POS_SOLPED, row.get(COL_POS_OC, np.nan)))
    nivel = formato_valor(row.get("nivel_alerta", np.nan))
    estado = formato_valor(row.get("clasificacion_vencimiento", np.nan))
    venc = formato_valor(row.get("dias_hasta_vencimiento", np.nan))
    centro = formato_valor(row.get(COL_CENTRO, np.nan))
    material = formato_id(row.get(COL_MATERIAL, np.nan))

    return f"{nivel} · {estado} · SolPed {solped} · Pedido {pedido} · Pos {pos} · Centro {centro} · Material {material} · {venc}"


# ============================================================
# App
# ============================================================

mostrar_logo()
mostrar_hero()

if "df_tat" not in st.session_state or st.session_state.get("df_tat") is None:
    st.info("No hay archivo activo en sesión. Primero carga un archivo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

hoy = pd.Timestamp.today().normalize()

try:
    with st.spinner("Preparando expediente TAT..."):
        df_panel = preparar_panel_filtro(df_original, hoy)

except Exception as e:
    st.error("No se pudo preparar el panel de filtro.")
    st.exception(e)
    st.stop()


faltantes_requeridas = [
    col
    for col in [COL_SOLPED]
    if col not in df_panel.columns
]

if faltantes_requeridas:
    st.error(f"Faltan columnas requeridas: {faltantes_requeridas}")
    st.stop()


# ============================================================
# Filtros
# ============================================================

mostrar_search_intro()

with st.form("form_filtros_solped"):
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        filtro_solped = st.text_input(
            "SOLPED",
            placeholder="Ej: 1002614561",
            key="filtro_solped",
        )

    with col_f2:
        filtro_pedido = st.text_input(
            "Pedido",
            placeholder="Ej: 4500123456",
            key="filtro_pedido",
        )

    with col_f3:
        filtro_posicion = st.text_input(
            "Posición",
            placeholder="Ej: 10",
            key="filtro_posicion",
        )

    col_f4, col_f5, col_f6 = st.columns([1.2, 1.6, 1])

    with col_f4:
        filtro_material = st.text_input(
            "Material",
            placeholder="Ej: 20050351",
            key="filtro_material",
        )

    with col_f5:
        filtro_texto = st.text_input(
            "Texto breve",
            placeholder="Buscar por descripción",
            key="filtro_texto",
        )

    with col_f6:
        modo_busqueda = st.selectbox(
            "Modo",
            options=["Exacta", "Contiene"],
            index=0,
            key="filtro_modo",
        )

    b1, b2 = st.columns(2)

    with b1:
        aplicar_filtros = st.form_submit_button(
            "Buscar expediente",
            use_container_width=True,
            type="primary",
        )

    with b2:
        limpiar_filtros = st.form_submit_button(
            "Limpiar",
            use_container_width=True,
        )


if limpiar_filtros:
    claves = [
        "filtro_solped",
        "filtro_pedido",
        "filtro_posicion",
        "filtro_material",
        "filtro_texto",
        "filtro_modo",
        "df_filtrado_expediente",
        "firma_filtros_expediente",
        "selector_expediente",
        "expediente_id_confirmado",
    ]

    for clave in claves:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


firma_filtros = (
    f"{filtro_solped}_"
    f"{filtro_pedido}_"
    f"{filtro_posicion}_"
    f"{filtro_material}_"
    f"{filtro_texto}_"
    f"{modo_busqueda}_"
    f"{len(df_panel)}"
)


if aplicar_filtros:
    if not hay_criterio_busqueda(
        filtro_solped=filtro_solped,
        filtro_pedido=filtro_pedido,
        filtro_posicion=filtro_posicion,
        filtro_material=filtro_material,
        filtro_texto=filtro_texto,
    ):
        st.warning("Ingresa al menos un criterio de búsqueda para abrir un expediente.")
        st.stop()

    with st.spinner("Buscando expediente..."):
        df_filtrado = aplicar_filtros_con_progreso(
            df_base=df_panel,
            filtro_solped=filtro_solped,
            filtro_pedido=filtro_pedido,
            filtro_posicion=filtro_posicion,
            filtro_material=filtro_material,
            filtro_texto=filtro_texto,
            modo_busqueda=modo_busqueda,
        )

        if "score_riesgo" in df_filtrado.columns:
            df_filtrado = df_filtrado.sort_values(
                "score_riesgo",
                ascending=False,
            ).copy()

        df_filtrado = df_filtrado.reset_index(drop=True)
        df_filtrado["_id_expediente"] = range(len(df_filtrado))

        st.session_state["df_filtrado_expediente"] = df_filtrado
        st.session_state["firma_filtros_expediente"] = firma_filtros

        if "expediente_id_confirmado" in st.session_state:
            del st.session_state["expediente_id_confirmado"]

    st.success("Búsqueda finalizada.")

else:
    if (
        st.session_state.get("df_filtrado_expediente") is not None
        and st.session_state.get("firma_filtros_expediente") == firma_filtros
    ):
        df_filtrado = st.session_state["df_filtrado_expediente"].copy()
    else:
        st.stop()


# ============================================================
# Resultado búsqueda
# ============================================================

if df_filtrado.empty:
    st.warning("No se encontraron expedientes con los criterios ingresados.")
    st.stop()


if len(df_filtrado) == 1:
    registro = df_filtrado.iloc[0]

    mostrar_message_card(
        "Coincidencia única encontrada",
        "Se encontró un único registro. El expediente se muestra automáticamente.",
    )

else:
    mostrar_message_card(
        "Coincidencias encontradas",
        "Se encontró más de un registro. Selecciona el expediente que quieres revisar y confirma.",
    )

    limite_selector = 5000
    df_selector = df_filtrado.head(limite_selector).copy()

    if len(df_filtrado) > limite_selector:
        st.warning(
            f"Se muestran los primeros {limite_selector:,} registros. Refina la búsqueda para reducir resultados."
            .replace(",", ".")
        )

    opciones = dict(
        zip(
            df_selector.apply(etiqueta_selector, axis=1),
            df_selector["_id_expediente"],
        )
    )

    etiqueta = st.selectbox(
        "Expediente a revisar",
        options=list(opciones.keys()),
        index=0,
        key="selector_expediente",
    )

    id_seleccionado = opciones[etiqueta]

    confirmar = st.button(
        "Confirmar expediente",
        type="primary",
        use_container_width=True,
    )

    if confirmar:
        st.session_state["expediente_id_confirmado"] = id_seleccionado

    if st.session_state.get("expediente_id_confirmado") != id_seleccionado:
        st.stop()

    registro = (
        df_filtrado[df_filtrado["_id_expediente"].eq(id_seleccionado)]
        .iloc[0]
    )

    st.success("Expediente confirmado.")


# ============================================================
# Mostrar expediente
# ============================================================

mostrar_expediente(registro)
