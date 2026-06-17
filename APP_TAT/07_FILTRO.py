# ============================================================
# 07_FILTRO
# Filtro, búsqueda y seguimiento de solicitudes de compra
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

import base64
from html import escape
from pathlib import Path

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
# Estilos Streamlit nativos
# No se modifica .block-container para no afectar el logo.
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
            padding: 14px 16px;
            border-radius: 14px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stMetric"] label {
            color: #64748b !important;
            font-size: 0.72rem !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #0f172a !important;
            font-size: 1.35rem !important;
            font-weight: 800 !important;
        }

        [data-testid="stDataFrame"] {
            border-radius: 14px !important;
            overflow: hidden !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
        }

        [data-testid="stForm"] {
            background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
            border: 1px solid #e2e8f0;
            border-radius: 18px;
            padding: 18px 20px;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
        }

        [data-testid="stFormSubmitButton"] button,
        [data-testid="stButton"] button {
            border-radius: 12px !important;
            font-weight: 800 !important;
            border: 1px solid #dbeafe !important;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
        }

        div[data-testid="stInfo"],
        div[data-testid="stWarning"],
        div[data-testid="stSuccess"],
        div[data-testid="stError"] {
            border-radius: 14px !important;
            font-weight: 600 !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CSS para componentes HTML
# ============================================================

CSS_COMPONENTES = """
<style>
    html, body {
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #0f172a;
    }

    * {
        box-sizing: border-box;
    }

    .modern-hero {
        background:
            radial-gradient(circle at top left, rgba(239, 62, 82, 0.14), transparent 30%),
            radial-gradient(circle at top right, rgba(37, 99, 235, 0.18), transparent 34%),
            linear-gradient(135deg, #fff7ed 0%, #ffffff 45%, #eff6ff 100%);
        border: 1px solid #bfdbfe;
        border-radius: 24px;
        padding: 22px 26px;
        margin: 0;
        box-shadow: 0 4px 14px rgba(15, 23, 42, 0.07);
    }

    .modern-eyebrow {
        color: #ef3e52;
        font-size: 0.72rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        margin-bottom: 6px;
    }

    .modern-title {
        color: #0f172a;
        font-size: 1.70rem;
        font-weight: 950;
        letter-spacing: -0.035em;
        margin-bottom: 6px;
    }

    .modern-subtitle {
        color: #475569;
        font-size: 0.95rem;
        line-height: 1.48;
        max-width: 960px;
    }

    .flow-bridge {
        display: inline-block;
        margin-top: 12px;
        padding: 6px 12px;
        border-radius: 999px;
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
        font-size: 0.74rem;
        font-weight: 900;
    }

    .modern-section {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 18px;
        padding: 18px 20px;
        margin: 0;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.05);
    }

    .modern-section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
    }

    .modern-section-icon {
        width: 34px;
        height: 34px;
        border-radius: 12px;
        background: #dbeafe;
        color: #1e40af;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 950;
        font-size: 0.95rem;
        flex: 0 0 auto;
    }

    .modern-section-title {
        font-size: 1.05rem;
        font-weight: 950;
        color: #0f172a;
        margin-bottom: 1px;
    }

    .modern-section-subtitle {
        font-size: 0.82rem;
        color: #64748b;
        line-height: 1.35;
    }

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(140px, 1fr));
        gap: 10px;
        margin-top: 8px;
    }

    .summary-card {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 12px 14px;
        min-height: 84px;
        position: relative;
        overflow: hidden;
    }

    .summary-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: #cbd5e1;
    }

    .card-blue {
        background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
        border-color: #bfdbfe;
    }

    .card-blue::before {
        background: #2563eb;
    }

    .card-red {
        background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%);
        border-color: #fecdd3;
    }

    .card-red::before {
        background: #ef3e52;
    }

    .card-orange {
        background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
        border-color: #fed7aa;
    }

    .card-orange::before {
        background: #f97316;
    }

    .card-green {
        background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
        border-color: #bbf7d0;
    }

    .card-green::before {
        background: #22c55e;
    }

    .card-purple {
        background: linear-gradient(180deg, #faf5ff 0%, #ffffff 100%);
        border-color: #e9d5ff;
    }

    .card-purple::before {
        background: #9333ea;
    }

    .card-cyan {
        background: linear-gradient(180deg, #ecfeff 0%, #ffffff 100%);
        border-color: #a5f3fc;
    }

    .card-cyan::before {
        background: #06b6d4;
    }

    .card-yellow {
        background: linear-gradient(180deg, #fefce8 0%, #ffffff 100%);
        border-color: #fde68a;
    }

    .card-yellow::before {
        background: #eab308;
    }

    .summary-label {
        color: #64748b;
        font-size: 0.66rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }

    .summary-value {
        color: #0f172a;
        font-size: 0.96rem;
        font-weight: 850;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }

    .summary-note {
        color: #64748b;
        font-size: 0.74rem;
        line-height: 1.30;
        margin-top: 4px;
    }

    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(5, minmax(130px, 1fr));
        gap: 10px;
        margin-top: 8px;
    }

    .kpi-card {
        background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 13px 14px;
        position: relative;
        overflow: hidden;
    }

    .kpi-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        height: 4px;
        width: 100%;
        background: #94a3b8;
    }

    .kpi-blue {
        background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
        border-color: #bfdbfe;
    }

    .kpi-blue::before {
        background: #2563eb;
    }

    .kpi-red {
        background: linear-gradient(180deg, #fff1f2 0%, #ffffff 100%);
        border-color: #fecdd3;
    }

    .kpi-red::before {
        background: #ef3e52;
    }

    .kpi-orange {
        background: linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
        border-color: #fed7aa;
    }

    .kpi-orange::before {
        background: #f97316;
    }

    .kpi-green {
        background: linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
        border-color: #bbf7d0;
    }

    .kpi-green::before {
        background: #22c55e;
    }

    .kpi-purple {
        background: linear-gradient(180deg, #faf5ff 0%, #ffffff 100%);
        border-color: #e9d5ff;
    }

    .kpi-purple::before {
        background: #9333ea;
    }

    .kpi-label {
        color: #64748b;
        font-size: 0.66rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }

    .kpi-value {
        color: #0f172a;
        font-size: 1.08rem;
        font-weight: 950;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }

    .status-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 950;
        margin-top: 6px;
    }

    .status-green {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    .status-red {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #fecaca;
    }

    .status-yellow {
        background: #fef9c3;
        color: #854d0e;
        border: 1px solid #fde68a;
    }

    .status-orange {
        background: #ffedd5;
        color: #9a3412;
        border: 1px solid #fed7aa;
    }

    .status-blue {
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }

    .status-gray {
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
    }

    .alert-panel {
        border-radius: 18px;
        padding: 18px 20px;
        margin: 0;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.07);
    }

    .alert-red {
        background:
            radial-gradient(circle at top right, rgba(239, 62, 82, 0.18), transparent 32%),
            linear-gradient(180deg, #fff1f2 0%, #ffffff 100%);
        border: 1px solid #fecdd3;
        border-left: 6px solid #ef3e52;
    }

    .alert-orange {
        background:
            radial-gradient(circle at top right, rgba(249, 115, 22, 0.18), transparent 32%),
            linear-gradient(180deg, #fff7ed 0%, #ffffff 100%);
        border: 1px solid #fed7aa;
        border-left: 6px solid #f97316;
    }

    .alert-yellow {
        background:
            radial-gradient(circle at top right, rgba(234, 179, 8, 0.18), transparent 32%),
            linear-gradient(180deg, #fefce8 0%, #ffffff 100%);
        border: 1px solid #fde68a;
        border-left: 6px solid #eab308;
    }

    .alert-green {
        background:
            radial-gradient(circle at top right, rgba(34, 197, 94, 0.18), transparent 32%),
            linear-gradient(180deg, #f0fdf4 0%, #ffffff 100%);
        border: 1px solid #bbf7d0;
        border-left: 6px solid #22c55e;
    }

    .alert-blue {
        background:
            radial-gradient(circle at top right, rgba(37, 99, 235, 0.18), transparent 32%),
            linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
        border: 1px solid #bfdbfe;
        border-left: 6px solid #2563eb;
    }

    .alert-gray {
        background:
            radial-gradient(circle at top right, rgba(100, 116, 139, 0.14), transparent 32%),
            linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid #e2e8f0;
        border-left: 6px solid #64748b;
    }

    .alert-title {
        font-size: 0.78rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: #475569;
        margin-bottom: 5px;
    }

    .alert-main {
        font-size: 1.25rem;
        font-weight: 950;
        color: #0f172a;
        line-height: 1.25;
        margin-bottom: 8px;
    }

    .alert-text {
        font-size: 0.90rem;
        color: #334155;
        line-height: 1.45;
    }

    .alert-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(130px, 1fr));
        gap: 10px;
        margin-top: 14px;
    }

    .alert-item {
        background: rgba(255,255,255,0.76);
        border: 1px solid rgba(226,232,240,0.95);
        border-radius: 13px;
        padding: 10px 12px;
    }

    .alert-item-label {
        color: #64748b;
        font-size: 0.66rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
    }

    .alert-item-value {
        color: #0f172a;
        font-size: 0.94rem;
        font-weight: 900;
        line-height: 1.25;
    }

    .message-card {
        background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
        border: 1px solid #bfdbfe;
        border-left: 5px solid #2563eb;
        border-radius: 16px;
        padding: 14px 16px;
        margin: 0;
    }

    .message-title {
        font-size: 0.86rem;
        font-weight: 950;
        color: #1e3a8a;
        margin-bottom: 3px;
    }

    .message-text {
        font-size: 0.86rem;
        color: #475569;
        line-height: 1.4;
    }

    .search-card {
        background:
            radial-gradient(circle at top right, rgba(6, 182, 212, 0.16), transparent 28%),
            linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid #bae6fd;
        border-left: 5px solid #06b6d4;
        border-radius: 16px;
        padding: 14px 16px;
        margin: 0;
    }

    .search-title {
        color: #0e7490;
        font-size: 0.82rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 4px;
    }

    .search-text {
        color: #475569;
        font-size: 0.88rem;
        line-height: 1.45;
    }

    .flow-shell {
        background:
            radial-gradient(circle at top left, rgba(37, 99, 235, 0.16), transparent 28%),
            linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
        border: 1px solid #dbeafe;
        border-radius: 18px;
        padding: 18px 20px 16px;
        margin: 0;
        box-shadow: 0 1px 4px rgba(15, 23, 42, 0.06);
    }

    .flow-title {
        font-size: 0.78rem;
        font-weight: 900;
        color: #1e3a8a;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 14px;
    }

    .flow-track {
        display: flex;
        align-items: flex-start;
        width: 100%;
        overflow-x: auto;
        padding-bottom: 8px;
    }

    .flow-step {
        flex: 0 0 145px;
        text-align: center;
        min-width: 0;
    }

    .flow-dot {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        margin: 0 auto 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 950;
        font-size: 1rem;
    }

    .flow-dot-ok {
        background: #22c55e;
        color: #ffffff;
        border: 3px solid #22c55e;
    }

    .flow-dot-active {
        background: #ffffff;
        color: #2563eb;
        border: 5px solid #3b82f6;
    }

    .flow-dot-pending {
        background: #ffffff;
        color: #94a3b8;
        border: 4px solid #cbd5e1;
    }

    .flow-label {
        font-size: 0.74rem;
        font-weight: 900;
        color: #1f2937;
        text-transform: uppercase;
        line-height: 1.2;
    }

    .flow-date {
        color: #475569;
        font-size: 0.72rem;
        line-height: 1.25;
        margin-top: 4px;
        overflow-wrap: anywhere;
    }

    .flow-detail {
        color: #64748b;
        font-size: 0.70rem;
        line-height: 1.25;
        margin-top: 4px;
    }

    .flow-connector {
        flex: 1;
        height: 5px;
        min-width: 28px;
        margin-top: 23px;
        border-radius: 999px;
        background: #cbd5e1;
    }

    .flow-connector-ok {
        background: #22c55e;
    }

    .flow-connector-active {
        background: repeating-linear-gradient(
            90deg,
            #3b82f6 0 14px,
            transparent 14px 22px
        );
    }

    .flow-summary {
        margin-top: 16px;
        display: grid;
        grid-template-columns: repeat(4, minmax(120px, 1fr));
        gap: 10px;
    }

    .flow-summary-item {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 10px 12px;
    }

    .flow-summary-label {
        color: #64748b;
        font-size: 0.67rem;
        font-weight: 950;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }

    .flow-summary-value {
        color: #0f172a;
        font-size: 0.92rem;
        font-weight: 900;
        line-height: 1.25;
        overflow-wrap: anywhere;
    }

    .flow-note {
        margin-top: 12px;
        color: #475569;
        font-size: 0.84rem;
        line-height: 1.45;
    }

    .badge-flow {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 999px;
        font-size: 0.70rem;
        font-weight: 900;
        margin-top: 5px;
    }

    .badge-ok {
        background: #dcfce7;
        color: #166534;
        border: 1px solid #bbf7d0;
    }

    .badge-active {
        background: #dbeafe;
        color: #1e40af;
        border: 1px solid #bfdbfe;
    }

    .badge-pending {
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
    }

    @media (max-width: 1100px) {
        .summary-grid {
            grid-template-columns: repeat(2, minmax(140px, 1fr));
        }

        .kpi-grid {
            grid-template-columns: repeat(2, minmax(130px, 1fr));
        }

        .flow-summary {
            grid-template-columns: repeat(2, minmax(120px, 1fr));
        }

        .alert-grid {
            grid-template-columns: repeat(2, minmax(130px, 1fr));
        }
    }

    @media (max-width: 680px) {
        .summary-grid {
            grid-template-columns: 1fr;
        }

        .kpi-grid {
            grid-template-columns: 1fr;
        }

        .flow-summary {
            grid-template-columns: 1fr;
        }

        .alert-grid {
            grid-template-columns: 1fr;
        }

        .modern-title {
            font-size: 1.35rem;
        }
    }
</style>
"""


# ============================================================
# Render HTML seguro con components
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

def formatear_valor(valor) -> str:
    if pd.isna(valor):
        return "—"

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    texto = str(valor).strip()

    if texto == "":
        return "—"

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto


def formatear_entero(valor) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return formatear_valor(valor)

    return f"{int(round(numero)):,}".replace(",", ".")


def formatear_decimal(valor, decimales: int = 1) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return formatear_valor(valor)

    return (
        f"{numero:,.{decimales}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def formatear_monto(valor, moneda) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return formatear_valor(valor)

    moneda_txt = formatear_valor(moneda)

    if moneda_txt == "—":
        moneda_txt = ""

    monto = f"{int(round(numero)):,}".replace(",", ".")

    return f"{monto} {moneda_txt}".strip()


def formatear_fecha(valor) -> str:
    if pd.isna(valor):
        return "Sin fecha"

    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return "Sin fecha"

    return fecha.strftime("%Y-%m-%d")


def formatear_fecha_corta(valor) -> str:
    if pd.isna(valor):
        return "Pendiente"

    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return "Pendiente"

    return fecha.strftime("%d-%m-%Y")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def normalizar_columnas_me80fn(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compatibilidad con archivos antiguos que aún tengan NME80FN.
    """
    df = df.copy()

    renombrar = {
        col: col.replace("NME80FN", "ME80FN")
        for col in df.columns
        if "NME80FN" in col
    }

    df = df.rename(columns=renombrar)

    if "Estado del match" in df.columns:
        df["Estado del match"] = (
            df["Estado del match"]
            .astype("string")
            .str.replace("NME80FN", "ME80FN", regex=False)
        )

    return df


def buscar_columna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    for col in candidatos:
        if col in df.columns:
            return col

    return None


def obtener_valor(registro: pd.Series, columna: str | None):
    if columna is None:
        return pd.NA

    if columna not in registro.index:
        return pd.NA

    return registro.get(columna)


def valor_html(valor) -> str:
    return escape(formatear_valor(valor))


def normalizar_valor_busqueda(valor) -> str:
    if pd.isna(valor):
        return ""

    texto = str(valor).strip().lower()

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto


def normalizar_serie_busqueda(serie: pd.Series) -> pd.Series:
    return serie.apply(normalizar_valor_busqueda)


def aplicar_filtro_texto(
    df: pd.DataFrame,
    columna: str | None,
    texto: str,
    modo: str = "Exacta",
) -> pd.DataFrame:

    if columna is None or columna not in df.columns:
        return df

    texto = str(texto).strip()

    if not texto:
        return df

    serie = normalizar_serie_busqueda(df[columna])
    texto_norm = normalizar_valor_busqueda(texto)

    if modo == "Exacta":
        return df[serie.eq(texto_norm)].copy()

    return df[serie.str.contains(texto_norm, na=False, regex=False)].copy()


def hay_criterio_busqueda(
    filtro_solped: str,
    filtro_pedido: str,
    filtro_posicion: str,
    filtro_material: str,
    filtro_texto_breve: str,
) -> bool:
    valores = [
        filtro_solped,
        filtro_pedido,
        filtro_posicion,
        filtro_material,
        filtro_texto_breve,
    ]

    return any(str(valor).strip() for valor in valores)


def texto_tiempo_extendido(dias) -> str:
    if pd.isna(dias):
        return "Sin fecha de solicitud"

    dias = int(dias)

    if dias < 0:
        return "La fecha de solicitud está en el futuro"

    if dias < 30:
        return f"{dias:,} días".replace(",", ".")

    meses = dias / 30.44

    if dias < 365:
        meses_txt = (
            f"{meses:,.1f}"
            .replace(",", "X")
            .replace(".", ",")
            .replace("X", ".")
        )

        return f"{dias:,} días · {meses_txt} meses aprox.".replace(",", ".")

    anos = dias / 365.25

    meses_txt = (
        f"{meses:,.1f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    anos_txt = (
        f"{anos:,.1f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )

    return f"{dias:,} días · {meses_txt} meses · {anos_txt} años aprox.".replace(",", ".")


def obtener_umbral_operativo(registro: pd.Series, columnas_clave: dict):
    umbral = pd.to_numeric(
        obtener_valor(registro, columnas_clave["umbral_tat_total"]),
        errors="coerce",
    )

    if pd.notna(umbral):
        return float(umbral)

    tipo_oc = str(
        obtener_valor(registro, columnas_clave["tipo_oc"])
    ).strip().replace(".0", "")

    if tipo_oc in ["35", "45"]:
        return 40.0

    if tipo_oc == "47":
        return 70.0

    return pd.NA


def calcular_estado_alerta_registro(registro: pd.Series, columnas_clave: dict) -> dict:
    hoy = pd.Timestamp.today().normalize()

    fecha_solicitud = pd.to_datetime(
        obtener_valor(registro, columnas_clave["fecha_solicitud"]),
        errors="coerce",
    )

    fecha_recepcion = pd.to_datetime(
        obtener_valor(registro, columnas_clave["fecha_recepcion"]),
        errors="coerce",
    )

    umbral = obtener_umbral_operativo(registro, columnas_clave)

    dias_desde_solicitud = pd.NA

    if pd.notna(fecha_solicitud):
        dias_desde_solicitud = int((hoy - fecha_solicitud).days)

    fecha_vencimiento = pd.NaT

    if pd.notna(fecha_solicitud) and pd.notna(umbral):
        fecha_vencimiento = fecha_solicitud + pd.to_timedelta(int(round(umbral)), unit="D")

    dias_restantes = pd.NA

    if pd.notna(fecha_vencimiento):
        dias_restantes = int((fecha_vencimiento - hoy).days)

    if pd.notna(fecha_recepcion):
        estado = "Recepcionado"
        clase = "alert-green"
        titulo = "Pedido recepcionado"
        mensaje = (
            "El registro ya tiene recepción registrada. "
            "La revisión en Filtro sirve para validar el historial y la trazabilidad completa."
        )

    elif pd.isna(fecha_solicitud):
        estado = "Sin fecha de solicitud"
        clase = "alert-gray"
        titulo = "No se puede calcular vencimiento"
        mensaje = (
            "No existe una fecha de solicitud válida. "
            "Revisa la data base para calcular el avance TAT."
        )

    elif pd.isna(umbral):
        estado = "Sin umbral TAT"
        clase = "alert-gray"
        titulo = "No se puede calcular vencimiento"
        mensaje = (
            "Existe fecha de solicitud, pero no hay umbral TAT disponible. "
            "Revisa el tipo OC o el campo umbral_tat_total."
        )

    elif dias_restantes < 0:
        estado = "Vencido"
        clase = "alert-red"
        titulo = f"Vencido hace {abs(dias_restantes):,} días".replace(",", ".")
        mensaje = (
            "Este registro ya superó su fecha estimada de vencimiento TAT y no tiene recepción. "
            "Desde Alertas se identifica como prioridad, y desde Filtro puedes revisar el detalle específico de la SOLPED."
        )

    elif dias_restantes == 0:
        estado = "Vence hoy"
        clase = "alert-orange"
        titulo = "Vence hoy"
        mensaje = (
            "Este registro vence hoy y todavía no tiene recepción. "
            "Conviene revisar la etapa pendiente y gestionar el cierre operativo."
        )

    elif dias_restantes <= 7:
        estado = "Por vencer"
        clase = "alert-orange"
        titulo = f"Por vencer en {dias_restantes:,} días".replace(",", ".")
        mensaje = (
            "Este registro está próximo a vencer. "
            "Alertas ayuda a detectarlo y Filtro permite revisar el detalle de la SOLPED."
        )

    elif dias_restantes <= 30:
        estado = "Seguimiento"
        clase = "alert-yellow"
        titulo = f"Vence en {dias_restantes:,} días".replace(",", ".")
        mensaje = (
            "Este registro aún no vence, pero está dentro de la ventana de seguimiento preventivo."
        )

    else:
        estado = "Controlado"
        clase = "alert-blue"
        titulo = f"Vence en {dias_restantes:,} días".replace(",", ".")
        mensaje = (
            "Este registro todavía tiene margen antes del vencimiento TAT. "
            "Se recomienda mantener seguimiento preventivo."
        )

    return {
        "estado": estado,
        "clase": clase,
        "titulo": titulo,
        "mensaje": mensaje,
        "dias_desde_solicitud": dias_desde_solicitud,
        "dias_desde_solicitud_texto": texto_tiempo_extendido(dias_desde_solicitud),
        "umbral": umbral,
        "fecha_vencimiento": fecha_vencimiento,
        "fecha_vencimiento_texto": formatear_fecha_corta(fecha_vencimiento),
        "dias_restantes": dias_restantes,
    }


def aplicar_filtros_con_progreso(
    df_base: pd.DataFrame,
    columnas_clave: dict,
    filtro_solped: str,
    filtro_pedido: str,
    filtro_posicion: str,
    filtro_material: str,
    filtro_texto_breve: str,
    modo_busqueda: str,
) -> pd.DataFrame:

    barra = st.progress(0, text="Preparando búsqueda...")

    df_filtrado = df_base.copy()

    barra.progress(15, text="Cargando base activa...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["solped"],
        texto=filtro_solped,
        modo=modo_busqueda,
    )

    barra.progress(35, text="Buscando SOLPED...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["pedido"],
        texto=filtro_pedido,
        modo=modo_busqueda,
    )

    barra.progress(50, text="Buscando pedido...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["posicion"],
        texto=filtro_posicion,
        modo=modo_busqueda,
    )

    barra.progress(65, text="Buscando posición...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["material"],
        texto=filtro_material,
        modo=modo_busqueda,
    )

    barra.progress(80, text="Buscando material...")

    df_filtrado = aplicar_filtro_texto(
        df=df_filtrado,
        columna=columnas_clave["texto_breve"],
        texto=filtro_texto_breve,
        modo="Contiene",
    )

    barra.progress(100, text="Búsqueda finalizada.")

    return df_filtrado


# ============================================================
# Detección de columnas
# ============================================================

def detectar_columnas_clave(df: pd.DataFrame) -> dict:
    return {
        "solped": buscar_columna(
            df,
            [
                "Solicitud de pedido - ME5A",
                "Solicitud de pedido",
                "Solicitud de compra ERP - ARIBA",
                "ariba_solicitud_compra_erp",
            ],
        ),
        "pedido": buscar_columna(
            df,
            [
                "Pedido - ME5A",
                "Pedido",
                "ID pedido - ARIBA",
                "ariba_id_pedido",
                "Documento de compras - ME80FN",
            ],
        ),
        "posicion": buscar_columna(
            df,
            [
                "Posición solicitud de pedido - ME5A",
                "Pos.solicitud pedido",
                "Posición de pedido - ME5A",
                "Posición de pedido",
                "Línea solicitud de compra - ARIBA",
            ],
        ),
        "material": buscar_columna(
            df,
            [
                "Material - ME5A",
                "Material",
                "Material - ME80FN",
            ],
        ),
        "texto_breve": buscar_columna(
            df,
            [
                "Texto breve - ME5A",
                "Texto breve",
                "Descripción - ARIBA",
                "Texto breve - ME80FN",
            ],
        ),
        "centro": buscar_columna(
            df,
            [
                "Centro - ME5A",
                "Centro",
                "Centro - ME80FN",
            ],
        ),
        "grupo_compras": buscar_columna(
            df,
            [
                "Grupo de compras",
                "Grupo compras",
                "Grupo de compras - ME5A",
            ],
        ),
        "tipo_oc": buscar_columna(
            df,
            [
                "tipo_oc",
                "Tipo OC",
                "Clase de documento",
            ],
        ),
        "sistema": buscar_columna(
            df,
            [
                "sistema",
                "Sistema",
            ],
        ),
        "origen": buscar_columna(
            df,
            [
                "origen",
                "Origen",
            ],
        ),
        "estado_match": buscar_columna(
            df,
            [
                "Estado del match",
                "estado_match",
            ],
        ),
        "fecha_solicitud": buscar_columna(
            df,
            [
                "fecha_solicitud_final",
                "Fecha de solicitud - ME5A",
                "Fecha de solicitud",
            ],
        ),
        "fecha_liberacion": buscar_columna(
            df,
            [
                "fecha_liberacion_final",
                "Fecha de liberación - ME5A",
                "Fecha de liberación",
            ],
        ),
        "fecha_pedido": buscar_columna(
            df,
            [
                "fecha_pedido_final",
                "Fecha de pedido - ME5A",
                "Fecha de pedido",
            ],
        ),
        "fecha_facturacion": buscar_columna(
            df,
            [
                "fecha_facturacion_final",
                "Fecha facturación proveedor - ME80FN",
                "Fecha facturación",
            ],
        ),
        "fecha_recepcion": buscar_columna(
            df,
            [
                "fecha_recepcion_final",
                "Fecha recepción mercancía - ME80FN",
                "Fecha recepción",
            ],
        ),
        "dias_tat_total": buscar_columna(
            df,
            [
                "dias_tat_total",
            ],
        ),
        "umbral_tat_total": buscar_columna(
            df,
            [
                "umbral_tat_total",
            ],
        ),
        "performance_tat_total": buscar_columna(
            df,
            [
                "performance_tat_total",
            ],
        ),
        "dias_incumplimiento": buscar_columna(
            df,
            [
                "dias_incumplimiento_tat",
            ],
        ),
        "rango_incumplimiento": buscar_columna(
            df,
            [
                "rango_incumplimiento_tat",
            ],
        ),
        "cantidad_solicitada": buscar_columna(
            df,
            [
                "Cantidad solicitada - ME5A",
                "Cantidad solicitada",
            ],
        ),
        "unidad_medida": buscar_columna(
            df,
            [
                "Unidad de medida - ME5A",
                "Unidad de medida",
            ],
        ),
        "precio_valoracion": buscar_columna(
            df,
            [
                "Precio de valoración",
                "Precio valoración",
                "Precio valorización",
            ],
        ),
        "moneda": buscar_columna(
            df,
            [
                "Moneda - ME5A",
                "Moneda",
            ],
        ),
        "solicitante": buscar_columna(
            df,
            [
                "Solicitante",
                "Solicitante - ME5A",
            ],
        ),
        "autor": buscar_columna(
            df,
            [
                "Autor",
                "Autor - ME5A",
            ],
        ),
    }


# ============================================================
# Construcción de etiquetas y tablas
# ============================================================

def construir_etiqueta_observacion(row: pd.Series, columnas_clave: dict) -> str:
    solped = formatear_valor(obtener_valor(row, columnas_clave["solped"]))
    pedido = formatear_valor(obtener_valor(row, columnas_clave["pedido"]))
    posicion = formatear_valor(obtener_valor(row, columnas_clave["posicion"]))
    material = formatear_valor(obtener_valor(row, columnas_clave["material"]))
    texto = formatear_valor(obtener_valor(row, columnas_clave["texto_breve"]))
    fila = formatear_valor(row.get("_id_observacion", ""))

    etiqueta = f"SOLPED {solped}"

    if pedido != "—":
        etiqueta += f" | Pedido {pedido}"

    if posicion != "—":
        etiqueta += f" | Pos {posicion}"

    if material != "—":
        etiqueta += f" | Material {material}"

    if texto != "—":
        texto_corto = texto[:45] + "..." if len(texto) > 45 else texto
        etiqueta += f" | {texto_corto}"

    etiqueta += f" | Fila {fila}"

    return etiqueta


def construir_tabla_fechas(registro: pd.Series, columnas_clave: dict) -> pd.DataFrame:
    datos = [
        {
            "Etapa": "Solicitud",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_solicitud"])),
        },
        {
            "Etapa": "Liberación",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_liberacion"])),
        },
        {
            "Etapa": "Pedido",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_pedido"])),
        },
        {
            "Etapa": "Facturación",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_facturacion"])),
        },
        {
            "Etapa": "Recepción",
            "Fecha": formatear_fecha(obtener_valor(registro, columnas_clave["fecha_recepcion"])),
        },
    ]

    return pd.DataFrame(datos)


def obtener_etapas_flujo(registro: pd.Series, columnas_clave: dict) -> list[dict]:
    definicion = [
        {
            "nombre": "Solicitud",
            "columna": columnas_clave["fecha_solicitud"],
        },
        {
            "nombre": "Liberación",
            "columna": columnas_clave["fecha_liberacion"],
        },
        {
            "nombre": "Pedido",
            "columna": columnas_clave["fecha_pedido"],
        },
        {
            "nombre": "Facturación",
            "columna": columnas_clave["fecha_facturacion"],
        },
        {
            "nombre": "Recepción",
            "columna": columnas_clave["fecha_recepcion"],
        },
    ]

    etapas = []

    for item in definicion:
        fecha = pd.to_datetime(
            obtener_valor(registro, item["columna"]),
            errors="coerce",
        )

        etapas.append(
            {
                "nombre": item["nombre"],
                "fecha": fecha,
                "fecha_texto": formatear_fecha_corta(fecha),
                "completada": pd.notna(fecha),
                "dias_desde_anterior": pd.NA,
                "estado": "Completado" if pd.notna(fecha) else "Pendiente",
            }
        )

    indice_pendiente_actual = None

    for i, etapa in enumerate(etapas):
        if not etapa["completada"]:
            indice_pendiente_actual = i
            break

    if indice_pendiente_actual is not None:
        etapas[indice_pendiente_actual]["estado"] = "Pendiente actual"

    fecha_anterior = pd.NaT

    for etapa in etapas:
        fecha_actual = etapa["fecha"]

        if pd.notna(fecha_actual) and pd.notna(fecha_anterior):
            etapa["dias_desde_anterior"] = int((fecha_actual - fecha_anterior).days)

        if pd.notna(fecha_actual):
            fecha_anterior = fecha_actual

    return etapas


def construir_tabla_etapas_tat(registro: pd.Series, columnas_clave: dict) -> pd.DataFrame:
    etapas = obtener_etapas_flujo(registro, columnas_clave)

    registros = []

    for etapa in etapas:
        dias = etapa["dias_desde_anterior"]

        registros.append(
            {
                "Etapa": etapa["nombre"],
                "Fecha TAT": etapa["fecha_texto"],
                "Estado": etapa["estado"],
                "Días desde etapa anterior": "—" if pd.isna(dias) else dias,
            }
        )

    return pd.DataFrame(registros)


def construir_validacion_temporal_tat(
    registro: pd.Series,
    columnas_clave: dict,
) -> pd.DataFrame:

    etapas = {
        "Solicitud": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_solicitud"]),
            errors="coerce",
        ),
        "Liberación": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_liberacion"]),
            errors="coerce",
        ),
        "Pedido": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_pedido"]),
            errors="coerce",
        ),
        "Facturación": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_facturacion"]),
            errors="coerce",
        ),
        "Recepción": pd.to_datetime(
            obtener_valor(registro, columnas_clave["fecha_recepcion"]),
            errors="coerce",
        ),
    }

    comparaciones = [
        ("Solicitud", "Liberación"),
        ("Liberación", "Pedido"),
        ("Pedido", "Facturación"),
        ("Facturación", "Recepción"),
        ("Solicitud", "Facturación"),
        ("Solicitud", "Recepción"),
    ]

    validaciones = []

    for inicio, fin in comparaciones:
        fecha_inicio = etapas[inicio]
        fecha_fin = etapas[fin]

        if pd.isna(fecha_inicio) or pd.isna(fecha_fin):
            estado = "Sin datos"
            detalle = "No evaluable por fecha faltante"
            dias = pd.NA

        else:
            dias = int((fecha_fin - fecha_inicio).days)

            if fecha_fin >= fecha_inicio:
                estado = "Correcto"
                detalle = "Orden temporal válido"
            else:
                estado = "Revisar"
                detalle = "La fecha final ocurre antes que la fecha inicial"

        validaciones.append(
            {
                "Validación": f"{inicio} → {fin}",
                "Fecha inicial": formatear_fecha(fecha_inicio),
                "Fecha final": formatear_fecha(fecha_fin),
                "Días entre fechas": dias,
                "Estado": estado,
                "Detalle": detalle,
            }
        )

    return pd.DataFrame(validaciones)


# ============================================================
# HTML moderno
# ============================================================

def html_section_header(icono: str, titulo: str, subtitulo: str) -> str:
    return f"""
    <div class="modern-section-header">
        <div class="modern-section-icon">{escape(icono)}</div>
        <div>
            <div class="modern-section-title">{escape(titulo)}</div>
            <div class="modern-section-subtitle">{escape(subtitulo)}</div>
        </div>
    </div>
    """


def clase_estado_tat(valor: str) -> str:
    texto = str(valor).strip().lower()

    if texto == "cumple":
        return "status-green"

    if texto == "no cumple":
        return "status-red"

    if texto in ["en proceso", "sin datos"]:
        return "status-yellow"

    return "status-gray"


def html_hero() -> str:
    return """
    <div class="modern-hero">
        <div class="modern-eyebrow">Flujo operativo Alertas → Filtro</div>
        <div class="modern-title">07_FILTRO</div>
        <div class="modern-subtitle">
            Alertas identifica las SOLPED críticas o próximas a vencer. Filtro permite entrar al detalle específico:
            compra, responsable, cantidades, valor, estado TAT, fechas y seguimiento completo de la solicitud.
        </div>
        <div class="flow-bridge">
            Alertas y Filtro funcionan como pestañas hermanas: detectar → investigar → gestionar.
        </div>
    </div>
    """


def html_search_intro() -> str:
    return """
    <div class="search-card">
        <div class="search-title">Búsqueda específica de SOLPED</div>
        <div class="search-text">
            Usa esta pestaña después de revisar Alertas. Busca por SOLPED, pedido, posición, material o texto breve
            para abrir el expediente operativo de esa línea.
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


def html_alerta_operativa(registro: pd.Series, columnas_clave: dict) -> str:
    alerta = calcular_estado_alerta_registro(registro, columnas_clave)

    umbral = alerta["umbral"]

    if pd.isna(umbral):
        umbral_txt = "Sin umbral"
    else:
        umbral_txt = f"{int(round(umbral)):,} días".replace(",", ".")

    dias_restantes = alerta["dias_restantes"]

    if pd.isna(dias_restantes):
        dias_restantes_txt = "Sin dato"
    elif dias_restantes < 0:
        dias_restantes_txt = f"{abs(dias_restantes):,} días vencido".replace(",", ".")
    elif dias_restantes == 0:
        dias_restantes_txt = "Vence hoy"
    else:
        dias_restantes_txt = f"{dias_restantes:,} días restantes".replace(",", ".")

    return f"""
    <div class="alert-panel {escape(alerta["clase"])}">
        <div class="alert-title">Lectura operativa desde Alertas</div>
        <div class="alert-main">{escape(alerta["titulo"])}</div>
        <div class="alert-text">{escape(alerta["mensaje"])}</div>

        <div class="alert-grid">
            <div class="alert-item">
                <div class="alert-item-label">Estado alerta</div>
                <div class="alert-item-value">{escape(alerta["estado"])}</div>
            </div>

            <div class="alert-item">
                <div class="alert-item-label">Desde solicitud hasta hoy</div>
                <div class="alert-item-value">{escape(alerta["dias_desde_solicitud_texto"])}</div>
            </div>

            <div class="alert-item">
                <div class="alert-item-label">Fecha vencimiento</div>
                <div class="alert-item-value">{escape(alerta["fecha_vencimiento_texto"])}</div>
            </div>

            <div class="alert-item">
                <div class="alert-item-label">Contra umbral</div>
                <div class="alert-item-value">{escape(dias_restantes_txt)} · {escape(umbral_txt)}</div>
            </div>
        </div>
    </div>
    """


def html_resumen_general(registro: pd.Series, columnas_clave: dict) -> str:
    estado_match = formatear_valor(obtener_valor(registro, columnas_clave["estado_match"]))
    moneda = obtener_valor(registro, columnas_clave["moneda"])

    campos = [
        ("SOLPED", obtener_valor(registro, columnas_clave["solped"]), "card-blue"),
        ("Pedido", obtener_valor(registro, columnas_clave["pedido"]), "card-blue"),
        ("Posición", obtener_valor(registro, columnas_clave["posicion"]), "card-cyan"),
        ("Centro", obtener_valor(registro, columnas_clave["centro"]), "card-cyan"),
        ("Material", obtener_valor(registro, columnas_clave["material"]), "card-purple"),
        ("Texto breve", obtener_valor(registro, columnas_clave["texto_breve"]), "card-purple"),
        ("Cantidad solicitada", formatear_decimal(obtener_valor(registro, columnas_clave["cantidad_solicitada"])), "card-green"),
        ("Unidad de medida", obtener_valor(registro, columnas_clave["unidad_medida"]), "card-green"),
        ("Precio valoración", formatear_monto(obtener_valor(registro, columnas_clave["precio_valoracion"]), moneda), "card-yellow"),
        ("Moneda", moneda, "card-yellow"),
        ("Solicitante", obtener_valor(registro, columnas_clave["solicitante"]), "card-orange"),
        ("Autor", obtener_valor(registro, columnas_clave["autor"]), "card-orange"),
        ("Grupo de compras", obtener_valor(registro, columnas_clave["grupo_compras"]), "card-red"),
        ("Tipo OC", obtener_valor(registro, columnas_clave["tipo_oc"]), "card-red"),
        ("Sistema", obtener_valor(registro, columnas_clave["sistema"]), "card-blue"),
        ("Origen", obtener_valor(registro, columnas_clave["origen"]), "card-cyan"),
        ("Estado del match", estado_match, "card-red"),
    ]

    cards = []

    for label, value, extra_class in campos:
        cards.append(
            f"""
            <div class="summary-card {extra_class}">
                <div class="summary-label">{escape(label)}</div>
                <div class="summary-value">{valor_html(value)}</div>
            </div>
            """
        )

    return f"""
    <div class="modern-section">
        {html_section_header("1", "Información general y datos de compra", "Datos principales del registro confirmado, incluyendo cantidad, valor, responsables y origen.")}
        <div class="summary-grid">
            {''.join(cards)}
        </div>
    </div>
    """


def html_indicadores_tat(registro: pd.Series, columnas_clave: dict) -> str:
    performance = formatear_valor(
        obtener_valor(registro, columnas_clave["performance_tat_total"])
    )

    estado_class = clase_estado_tat(performance)
    alerta = calcular_estado_alerta_registro(registro, columnas_clave)

    kpis = [
        (
            "Días desde solicitud",
            alerta["dias_desde_solicitud_texto"],
            "Solicitud hasta hoy",
            "kpi-red" if alerta["estado"] == "Vencido" else "kpi-blue",
        ),
        (
            "Fecha vencimiento",
            alerta["fecha_vencimiento_texto"],
            "Según fecha solicitud + umbral TAT",
            "kpi-orange",
        ),
        (
            "Días TAT total",
            formatear_entero(obtener_valor(registro, columnas_clave["dias_tat_total"])),
            "Solicitud a recepción",
            "kpi-blue",
        ),
        (
            "Umbral TAT total",
            formatear_entero(alerta["umbral"]),
            "Límite definido o inferido",
            "kpi-purple",
        ),
        (
            "Performance TAT",
            performance,
            f'<span class="status-pill {estado_class}">{escape(performance)}</span>',
            "kpi-green",
        ),
        (
            "Días incumplimiento",
            formatear_entero(obtener_valor(registro, columnas_clave["dias_incumplimiento"])),
            "Días sobre umbral",
            "kpi-red",
        ),
        (
            "Rango incumplimiento",
            formatear_valor(obtener_valor(registro, columnas_clave["rango_incumplimiento"])),
            "Clasificación TAT",
            "kpi-orange",
        ),
    ]

    cards = []

    for label, value, note, extra_class in kpis:
        cards.append(
            f"""
            <div class="kpi-card {extra_class}">
                <div class="kpi-label">{escape(label)}</div>
                <div class="kpi-value">{escape(str(value))}</div>
                <div class="summary-note">{note}</div>
            </div>
            """
        )

    return f"""
    <div class="modern-section">
        {html_section_header("4", "Indicadores TAT y lectura temporal", "Resumen de tiempos, umbrales, vencimiento y cumplimiento del registro.")}
        <div class="kpi-grid">
            {''.join(cards)}
        </div>
    </div>
    """


# ============================================================
# Visualización profesional de flujo
# ============================================================

def calcular_resumen_flujo(registro: pd.Series, columnas_clave: dict) -> dict:
    etapas = obtener_etapas_flujo(registro, columnas_clave)

    completadas = [
        etapa
        for etapa in etapas
        if etapa["completada"]
    ]

    pendientes = [
        etapa
        for etapa in etapas
        if not etapa["completada"]
    ]

    ultima_etapa = completadas[-1]["nombre"] if completadas else "Sin etapa registrada"
    ultima_fecha = completadas[-1]["fecha_texto"] if completadas else "—"

    siguiente_etapa = pendientes[0]["nombre"] if pendientes else "Flujo cerrado"

    fecha_inicio = etapas[0]["fecha"] if etapas else pd.NaT
    fecha_fin = etapas[-1]["fecha"] if etapas and etapas[-1]["completada"] else pd.Timestamp.today().normalize()

    dias_transcurridos = pd.NA

    if pd.notna(fecha_inicio) and pd.notna(fecha_fin):
        dias_transcurridos = int((fecha_fin - fecha_inicio).days)

    estado_recepcion = "Recepcionado" if etapas and etapas[-1]["completada"] else "Sin recepción"

    return {
        "ultima_etapa": ultima_etapa,
        "ultima_fecha": ultima_fecha,
        "siguiente_etapa": siguiente_etapa,
        "dias_transcurridos": dias_transcurridos,
        "estado_recepcion": estado_recepcion,
    }


def html_diagrama_flujo_solped(registro: pd.Series, columnas_clave: dict) -> str:
    etapas = obtener_etapas_flujo(registro, columnas_clave)
    resumen = calcular_resumen_flujo(registro, columnas_clave)

    partes = []

    for i, etapa in enumerate(etapas):
        if etapa["estado"] == "Completado":
            dot_class = "flow-dot-ok"
            icono = "✓"
            badge_class = "badge-ok"
        elif etapa["estado"] == "Pendiente actual":
            dot_class = "flow-dot-active"
            icono = ""
            badge_class = "badge-active"
        else:
            dot_class = "flow-dot-pending"
            icono = ""
            badge_class = "badge-pending"

        dias = etapa["dias_desde_anterior"]

        if pd.isna(dias):
            detalle = "Inicio del flujo" if i == 0 else "Sin fecha registrada"
        else:
            detalle = f"{dias} días desde etapa anterior"

        partes.append(
            f"""
            <div class="flow-step">
                <div class="flow-dot {dot_class}">{escape(icono)}</div>
                <div class="flow-label">{escape(etapa["nombre"])}</div>
                <div class="flow-date">{escape(etapa["fecha_texto"])}</div>
                <div class="flow-detail">{escape(detalle)}</div>
                <span class="badge-flow {badge_class}">{escape(etapa["estado"])}</span>
            </div>
            """
        )

        if i < len(etapas) - 1:
            actual_completa = etapa["completada"]
            siguiente_completa = etapas[i + 1]["completada"]

            if actual_completa and siguiente_completa:
                conn_class = "flow-connector-ok"
            elif actual_completa and not siguiente_completa:
                conn_class = "flow-connector-active"
            else:
                conn_class = ""

            partes.append(
                f'<div class="flow-connector {conn_class}"></div>'
            )

    dias_transcurridos = resumen["dias_transcurridos"]

    if pd.isna(dias_transcurridos):
        dias_texto = "Sin dato"
    else:
        dias_texto = texto_tiempo_extendido(dias_transcurridos)

    nota = (
        f"Última etapa registrada: {resumen['ultima_etapa']} "
        f"({resumen['ultima_fecha']}). "
        f"Siguiente etapa: {resumen['siguiente_etapa']}."
    )

    html = f"""
    <div class="flow-shell">
        <div class="flow-title">Seguimiento visual de la SOLPED</div>

        <div class="flow-track">
            {''.join(partes)}
        </div>

        <div class="flow-summary">
            <div class="flow-summary-item">
                <div class="flow-summary-label">Última etapa</div>
                <div class="flow-summary-value">{escape(resumen["ultima_etapa"])}</div>
            </div>

            <div class="flow-summary-item">
                <div class="flow-summary-label">Fecha última etapa</div>
                <div class="flow-summary-value">{escape(resumen["ultima_fecha"])}</div>
            </div>

            <div class="flow-summary-item">
                <div class="flow-summary-label">Estado recepción</div>
                <div class="flow-summary-value">{escape(resumen["estado_recepcion"])}</div>
            </div>

            <div class="flow-summary-item">
                <div class="flow-summary-label">Tiempo transcurrido</div>
                <div class="flow-summary-value">{escape(dias_texto)}</div>
            </div>
        </div>

        <div class="flow-note">
            {escape(nota)}
        </div>
    </div>
    """

    return html


# ============================================================
# Render de bloques modernos
# ============================================================

def mostrar_hero():
    render_html(
        html_hero(),
        height=170,
        scrolling=False,
    )


def mostrar_search_intro():
    render_html(
        html_search_intro(),
        height=105,
        scrolling=False,
    )


def mostrar_message_card(titulo: str, texto: str):
    render_html(
        html_message_card(titulo, texto),
        height=95,
        scrolling=False,
    )


def mostrar_resumen_general_moderno(registro: pd.Series, columnas_clave: dict):
    render_html(
        html_resumen_general(
            registro=registro,
            columnas_clave=columnas_clave,
        ),
        height=565,
        scrolling=True,
    )


def mostrar_alerta_operativa_moderno(registro: pd.Series, columnas_clave: dict):
    render_html(
        html_alerta_operativa(
            registro=registro,
            columnas_clave=columnas_clave,
        ),
        height=265,
        scrolling=False,
    )


def mostrar_indicadores_tat_moderno(registro: pd.Series, columnas_clave: dict):
    render_html(
        html_indicadores_tat(
            registro=registro,
            columnas_clave=columnas_clave,
        ),
        height=335,
        scrolling=True,
    )


def mostrar_flujo_profesional_solped(registro: pd.Series, columnas_clave: dict):
    render_html(
        html_diagrama_flujo_solped(
            registro=registro,
            columnas_clave=columnas_clave,
        ),
        height=405,
        scrolling=True,
    )


def mostrar_validacion_temporal_tat(
    registro: pd.Series,
    columnas_clave: dict,
):
    st.markdown("### 6. Validación temporal")
    st.caption("Revisión automática del orden lógico de fechas entre etapas.")

    validacion_df = construir_validacion_temporal_tat(
        registro=registro,
        columnas_clave=columnas_clave,
    )

    total_revisar = int(validacion_df["Estado"].eq("Revisar").sum())
    total_sin_datos = int(validacion_df["Estado"].eq("Sin datos").sum())

    if total_revisar > 0:
        st.error(
            "Se detectaron fechas fuera de orden temporal. "
            "Revisa los casos marcados como 'Revisar'."
        )

    elif total_sin_datos > 0:
        st.warning(
            "Las fechas disponibles están ordenadas, pero existen etapas sin fecha. "
            "El flujo no se puede validar completamente."
        )

    else:
        st.success(
            "Las fechas TAT están ordenadas temporalmente."
        )

    st.dataframe(
        validacion_df,
        use_container_width=True,
        hide_index=True,
    )


def mostrar_detalle_observacion(registro: pd.Series, columnas_clave: dict):
    mostrar_message_card(
        titulo="Registro confirmado",
        texto="Se muestra el expediente operativo de la observación seleccionada. Esta vista complementa Alertas con detalle específico para investigar y gestionar.",
    )

    mostrar_alerta_operativa_moderno(
        registro=registro,
        columnas_clave=columnas_clave,
    )

    mostrar_resumen_general_moderno(
        registro=registro,
        columnas_clave=columnas_clave,
    )

    st.markdown("### 2. Seguimiento visual de la SOLPED")
    st.caption("Vista profesional del avance por etapas: solicitud, liberación, pedido, facturación y recepción.")

    mostrar_flujo_profesional_solped(
        registro=registro,
        columnas_clave=columnas_clave,
    )

    st.markdown("### 3. Fechas principales")
    st.caption("Fechas registradas para cada etapa del flujo TAT.")

    st.dataframe(
        construir_tabla_fechas(registro, columnas_clave),
        use_container_width=True,
        hide_index=True,
    )

    mostrar_indicadores_tat_moderno(
        registro=registro,
        columnas_clave=columnas_clave,
    )

    st.markdown("### 5. Estado de etapas")
    st.caption("Detalle tabular del estado de cada hito y los días entre etapas.")

    st.dataframe(
        construir_tabla_etapas_tat(registro, columnas_clave),
        use_container_width=True,
        hide_index=True,
    )

    mostrar_validacion_temporal_tat(
        registro=registro,
        columnas_clave=columnas_clave,
    )

    with st.expander("Ver registro completo", expanded=False):
        registro_df = (
            registro
            .drop(labels=["_id_observacion"], errors="ignore")
            .to_frame(name="Valor")
            .reset_index()
            .rename(columns={"index": "Campo"})
        )

        st.dataframe(
            registro_df,
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Encabezado
# ============================================================

mostrar_logo()
mostrar_hero()


# ============================================================
# Obtener dataframe activo
# ============================================================

df_tat = st.session_state.get("df_tat")
nombre_archivo_tat = st.session_state.get("nombre_archivo_tat")

if df_tat is None:
    st.info("No hay archivo activo en sesión. Primero carga un archivo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_tat = limpiar_nombres_columnas(df_tat)
df_tat = normalizar_columnas_me80fn(df_tat)

df_base = df_tat.copy()
df_base["_id_observacion"] = range(len(df_base))

columnas_clave = detectar_columnas_clave(df_base)

if columnas_clave["solped"] is None:
    st.error(
        "No se encontró columna SOLPED. Se esperaba una columna como "
        "'Solicitud de pedido - ME5A' o 'Solicitud de pedido'."
    )
    st.stop()


# ============================================================
# Filtros iniciales
# ============================================================

mostrar_search_intro()

with st.form("form_busqueda_solped"):
    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        filtro_solped = st.text_input(
            "SOLPED",
            placeholder="Ej: 6000123456",
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
            placeholder="Ej: 123456",
            key="filtro_material",
        )

    with col_f5:
        filtro_texto_breve = st.text_input(
            "Texto breve",
            placeholder="Buscar por descripción",
            key="filtro_texto_breve",
        )

    with col_f6:
        modo_busqueda = st.selectbox(
            "Modo",
            options=[
                "Exacta",
                "Contiene",
            ],
            index=0,
            key="filtro_modo",
        )

    col_b1, col_b2 = st.columns(2)

    with col_b1:
        buscar = st.form_submit_button(
            "Buscar",
            use_container_width=True,
            type="primary",
        )

    with col_b2:
        limpiar = st.form_submit_button(
            "Limpiar",
            use_container_width=True,
        )


if limpiar:
    claves_filtros = [
        "filtro_solped",
        "filtro_pedido",
        "filtro_posicion",
        "filtro_material",
        "filtro_texto_breve",
        "filtro_modo",
        "selector_observacion",
        "df_filtrado_solped",
        "firma_filtros_solped",
        "filtro_id_confirmado",
        "filtro_detalle_confirmado",
    ]

    for clave in claves_filtros:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


firma_filtros_actual = (
    f"{filtro_solped}_"
    f"{filtro_pedido}_"
    f"{filtro_posicion}_"
    f"{filtro_material}_"
    f"{filtro_texto_breve}_"
    f"{modo_busqueda}_"
    f"{len(df_base)}"
)


if buscar:
    if not hay_criterio_busqueda(
        filtro_solped=filtro_solped,
        filtro_pedido=filtro_pedido,
        filtro_posicion=filtro_posicion,
        filtro_material=filtro_material,
        filtro_texto_breve=filtro_texto_breve,
    ):
        st.warning("Ingresa al menos un criterio de búsqueda antes de continuar.")
        st.stop()

    with st.spinner("Buscando coincidencias..."):
        df_filtrado = aplicar_filtros_con_progreso(
            df_base=df_base,
            columnas_clave=columnas_clave,
            filtro_solped=filtro_solped,
            filtro_pedido=filtro_pedido,
            filtro_posicion=filtro_posicion,
            filtro_material=filtro_material,
            filtro_texto_breve=filtro_texto_breve,
            modo_busqueda=modo_busqueda,
        )

        st.session_state["df_filtrado_solped"] = df_filtrado
        st.session_state["firma_filtros_solped"] = firma_filtros_actual

        if "filtro_id_confirmado" in st.session_state:
            del st.session_state["filtro_id_confirmado"]

        if "filtro_detalle_confirmado" in st.session_state:
            del st.session_state["filtro_detalle_confirmado"]

    st.success("Búsqueda finalizada.")

else:
    if (
        st.session_state.get("df_filtrado_solped") is not None
        and st.session_state.get("firma_filtros_solped") == firma_filtros_actual
    ):
        df_filtrado = st.session_state["df_filtrado_solped"].copy()
    else:
        st.stop()


# ============================================================
# Validación de resultados
# ============================================================

if df_filtrado.empty:
    st.warning("No se encontraron coincidencias con los criterios ingresados.")
    st.stop()


# ============================================================
# Selección y confirmación de coincidencia
# ============================================================

total_resultados = len(df_filtrado)

if total_resultados == 1:
    registro_seleccionado = df_filtrado.iloc[0]

    mostrar_message_card(
        titulo="Coincidencia única encontrada",
        texto="Se encontró un único registro con los criterios ingresados. Se muestra el detalle automáticamente.",
    )

else:
    mostrar_message_card(
        titulo="Coincidencias encontradas",
        texto="Se encontró más de una coincidencia. Selecciona cuál registro quieres revisar y confirma para desplegar el detalle.",
    )

    st.info(
        f"Se encontraron **{total_resultados:,} coincidencias**. "
        "Selecciona una observación para continuar."
    )

    limite_selector = 500
    df_selector = df_filtrado.head(limite_selector).copy()

    if len(df_filtrado) > limite_selector:
        st.warning(
            f"Se muestran las primeras {limite_selector:,} coincidencias en el selector. "
            "Refina la búsqueda para reducir resultados."
        )

    df_selector["_etiqueta_observacion"] = df_selector.apply(
        lambda row: construir_etiqueta_observacion(row, columnas_clave),
        axis=1,
    )

    opciones_selector = dict(
        zip(
            df_selector["_etiqueta_observacion"],
            df_selector["_id_observacion"],
        )
    )

    etiqueta_seleccionada = st.selectbox(
        "Coincidencia",
        options=list(opciones_selector.keys()),
        index=0,
        key="selector_observacion",
    )

    id_observacion_seleccionada = opciones_selector[etiqueta_seleccionada]

    confirmar = st.button(
        "Confirmar y ver detalle",
        type="primary",
        use_container_width=True,
    )

    if confirmar:
        st.session_state["filtro_id_confirmado"] = id_observacion_seleccionada
        st.session_state["filtro_detalle_confirmado"] = True

    id_confirmado = st.session_state.get("filtro_id_confirmado")

    if id_confirmado != id_observacion_seleccionada:
        st.stop()

    registro_seleccionado = (
        df_filtrado[df_filtrado["_id_observacion"].eq(id_observacion_seleccionada)]
        .iloc[0]
    )

    st.success("Registro confirmado. Se muestra el detalle seleccionado.")


# ============================================================
# Resultado confirmado
# ============================================================

mostrar_detalle_observacion(
    registro=registro_seleccionado,
    columnas_clave=columnas_clave,
)
