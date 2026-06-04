# ============================================================
# 03_APP_GASTOS.py
# Dashboard de gastos, órdenes de compra y vencimiento de contratos
# ============================================================

from pathlib import Path
import base64

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import streamlit as st


# ============================================================
# Rutas del proyecto
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Estilo visual
# ============================================================

def aplicar_estilo():
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 2.8rem;
                padding-bottom: 2.5rem;
                max-width: 1550px;
            }

            .kpi-card {
                background-color: #FFFFFF;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 20px 18px;
                min-height: 118px;
                box-shadow: 0px 2px 8px rgba(0,0,0,0.045);
                display: flex;
                flex-direction: column;
                justify-content: center;
                margin-bottom: 10px;
            }

            .kpi-title {
                font-size: 0.90rem;
                color: #4B5563;
                font-weight: 600;
                margin-bottom: 8px;
                white-space: normal;
                line-height: 1.25;
            }

            .kpi-value {
                font-size: 1.50rem;
                color: #111827;
                font-weight: 800;
                line-height: 1.15;
                white-space: normal;
                word-break: break-word;
            }

            .kpi-subtitle {
                margin-top: 8px;
                font-size: 0.78rem;
                color: #6B7280;
            }

            .filter-card {
                background-color: #F9FAFB;
                border: 1px solid #E5E7EB;
                border-radius: 16px;
                padding: 18px 20px;
                margin-bottom: 18px;
            }

            h1, h2, h3 {
                letter-spacing: -0.02em;
            }
        </style>
        """,
        unsafe_allow_html=True
    )


def mostrar_logo_centrado():
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
                margin-top: 26px;
                margin-bottom: 18px;
                padding-top: 8px;
            ">
                <img
                    src="data:image/svg+xml;base64,{logo_base64}"
                    style="width: 240px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


def kpi_card(titulo, valor, subtitulo=None):
    subtitulo_html = f"<div class='kpi-subtitle'>{subtitulo}</div>" if subtitulo else ""

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{titulo}</div>
            <div class="kpi-value">{valor}</div>
            {subtitulo_html}
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# Funciones auxiliares
# ============================================================

def obtener_dataframe(nombre_df):
    dataframes = st.session_state.get("dataframes_cargados", {})

    if nombre_df not in dataframes:
        st.error(f"No se encontró `{nombre_df}` en `st.session_state['dataframes_cargados']`.")
        return None

    return dataframes[nombre_df].copy()


def validar_columnas(df, columnas, nombre_df):
    faltantes = [col for col in columnas if col not in df.columns]

    if faltantes:
        st.error(f"El DataFrame `{nombre_df}` no contiene las columnas requeridas: {faltantes}")
        return False

    return True


def limpiar_texto_columna(serie):
    return (
        serie
        .astype(str)
        .str.strip()
        .replace(["", "nan", "NaN", "None"], pd.NA)
    )


def convertir_numero(valor):
    if pd.isna(valor):
        return pd.NA

    s = str(valor).strip()

    if s == "" or s.lower() in ["nan", "none"]:
        return pd.NA

    # Formato 1.234,56 -> 1234.56
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")

    # Formato 1234,56 -> 1234.56
    elif "," in s:
        s = s.replace(",", ".")

    return pd.to_numeric(s, errors="coerce")


def formato_usd_compacto(x, pos=None):
    if pd.isna(x):
        return "$0"

    if abs(x) >= 1_000_000:
        return f"${x/1_000_000:.1f}M"

    if abs(x) >= 1_000:
        return f"${x/1_000:.0f}K"

    return f"${x:,.0f}"


def formato_usd(valor):
    if pd.isna(valor):
        return "$0"
    return f"${valor:,.0f}"


def formato_pct(valor):
    if pd.isna(valor):
        return "0,00%"
    return f"{valor:.2%}".replace(".", ",")


def clasificar_estado_contrato(fecha_fin, hoy):
    if pd.isna(fecha_fin):
        return "Sin fecha"

    if fecha_fin < hoy:
        return "Vencido"

    meses_diferencia = (fecha_fin.year - hoy.year) * 12 + (fecha_fin.month - hoy.month)

    if meses_diferencia <= 3:
        return "Por Vencer"

    return "Vigente"


# ============================================================
# Inicio app
# ============================================================

aplicar_estilo()
mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>03_GASTOS</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 16px; color: #4B5563;'>
        Seguimiento de gasto en órdenes de compra, conversión a USD,
        participación por tipo de OC y estado de vigencia de contratos.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")

if "dataframes_cargados" not in st.session_state or not st.session_state["dataframes_cargados"]:
    st.warning("Primero debes cargar las bases desde la pestaña **01_CARGA_ARCHIVOS**.")
    st.stop()


# ============================================================
# Cargar DataFrames desde session_state
# ============================================================

df_moneda_cambio = obtener_dataframe("df_moneda_cambio")
df_ordenes = obtener_dataframe("df_ordenes")
df_bbdd_x_categoria = obtener_dataframe("df_bbdd_x_categoria")
df_me5a = obtener_dataframe("df_me5a")

if (
    df_moneda_cambio is None
    or df_ordenes is None
    or df_bbdd_x_categoria is None
    or df_me5a is None
):
    st.stop()


# ============================================================
# Validación de columnas
# ============================================================

validaciones = [
    validar_columnas(
        df_moneda_cambio,
        ["Moneda", "Factor_USD_por_Unidad"],
        "df_moneda_cambio"
    ),
    validar_columnas(
        df_ordenes,
        ["Fecha_documento", "Documento_compras", "Moneda", "Precio_neto"],
        "df_ordenes"
    ),
    validar_columnas(
        df_bbdd_x_categoria,
        ["Contrato", "Gestor_Contrato"],
        "df_bbdd_x_categoria"
    ),
    validar_columnas(
        df_me5a,
        ["Documento_compras", "Fin_período_validez"],
        "df_me5a"
    ),
]

if not all(validaciones):
    st.stop()


# ============================================================
# Recuento de contratos en BBDD x Categoría
# ============================================================

df_recuento_contratos = df_bbdd_x_categoria.copy()

df_recuento_contratos["Contrato"] = (
    df_recuento_contratos["Contrato"]
    .astype(str)
    .str.strip()
    .str.replace(".0", "", regex=False)
)

df_recuento_contratos["Contrato"] = df_recuento_contratos["Contrato"].replace(
    ["", "nan", "None", "NaN"],
    pd.NA
)

recuento_contratos = df_recuento_contratos["Contrato"].notna().sum()
recuento_contratos_unicos = df_recuento_contratos["Contrato"].dropna().nunique()


# ============================================================
# Conversión de órdenes a USD
# ============================================================

df_ordenes_usd = df_ordenes.copy()

df_ordenes_usd["Moneda"] = (
    df_ordenes_usd["Moneda"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df_moneda_cambio["Moneda"] = (
    df_moneda_cambio["Moneda"]
    .astype(str)
    .str.strip()
    .str.upper()
)

df_ordenes_usd["Precio_neto_num"] = (
    df_ordenes_usd["Precio_neto"]
    .apply(convertir_numero)
)

monedas_registros = set(df_ordenes_usd["Moneda"].dropna().unique())
monedas_tabla = set(df_moneda_cambio["Moneda"].dropna().unique())
monedas_faltantes = sorted(monedas_registros - monedas_tabla)

columnas_cambio = ["Moneda", "Factor_USD_por_Unidad"]

for col in ["Valor_CLP_por_Unidad", "Fecha_Conversion"]:
    if col in df_moneda_cambio.columns:
        columnas_cambio.append(col)

df_ordenes_usd = df_ordenes_usd.merge(
    df_moneda_cambio[columnas_cambio],
    on="Moneda",
    how="left"
)

df_ordenes_usd["Factor_USD_por_Unidad"] = pd.to_numeric(
    df_ordenes
