# ============================================================
# 15_VISTA_EJECUTIVA_MATERIALES
# Vista ejecutiva de materiales TAT
#
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Objetivo:
# - Analizar materiales de forma ejecutiva.
# - Permitir ingresar una lista de materiales de interés.
# - Mostrar estadística por material, SolPed, pedidos, centros, grupos de compra,
#   recurrencia histórica, montos, TAT, vencimientos y gestión sugerida.
# - Entregar visualizaciones y tablas exportables.
# ============================================================

import io
import re
import base64
from pathlib import Path
from typing import Any
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="15_VISTA_EJECUTIVA_MATERIALES",
    page_icon="📦",
    layout="wide",
)


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

COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

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
# Estilos
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
[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button {
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

.info-card {
    background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
    border: 1px solid #bfdbfe;
    border-left: 6px solid #2563eb;
    border-radius: 16px;
    padding: 15px 18px;
    margin-bottom: 15px;
}

.info-card-title {
    color: #1e3a8a;
    font-weight: 900;
    font-size: 0.82rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
}

.info-card-text {
    color: #334155;
    font-size: 0.90rem;
    line-height: 1.42;
}

.quick-card {
    background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 14px 16px;
    margin-bottom: 12px;
}

.quick-card-title {
    color: #0f172a;
    font-size: 1.02rem;
    font-weight: 900;
    margin-bottom: 4px;
}

.quick-card-text {
    color: #475569;
    font-size: 0.88rem;
    line-height: 1.40;
}

.badge {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 10px;
    font-size: 0.74rem;
    font-weight: 900;
    margin-right: 5px;
}

.badge-blue { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }
.badge-red { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
.badge-orange { background: #ffedd5; color: #9a3412; border: 1px solid #fed7aa; }
.badge-green { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
.badge-gray { background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0; }
</style>
"""

st.markdown(ESTILOS_GLOBALES, unsafe_allow_html=True)


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
# Utilidades generales
# ============================================================

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
                df[col] = (
                    df[col]
                    .astype("string")
                    .str.replace("NME80FN", "ME80FN", regex=False)
                )
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


def normalizar_id(valor: Any) -> str:
    if pd.isna(valor):
        return ""

    texto = str(valor).strip()

    if texto.endswith(".0"):
        texto = texto[:-2]

    try:
        numero = float(texto)

        if np.isfinite(numero) and numero.is_integer():
            texto = str(int(numero))
    except Exception:
        pass

    return texto.strip()


def formato_id(valor: Any) -> str:
    texto = normalizar_id(valor)
    return texto if texto else "-"


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


def formato_fecha(valor: Any) -> str:
    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return "-"

    return fecha.strftime("%d-%m-%Y")


def formato_mes(valor: Any) -> str:
    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return "Sin fecha"

    return fecha.strftime("%Y-%m")


def valor_numerico(valor: Any) -> float:
    try:
        return float(pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0])
    except Exception:
        return np.nan


def formato_numero(valor: Any) -> str:
    numero = valor_numerico(valor)

    if pd.isna(numero):
        return "-"

    if float(numero).is_integer():
        return f"{int(numero):,}".replace(",", ".")

    return (
        f"{numero:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def formato_porcentaje(valor: Any) -> str:
    numero = valor_numerico(valor)

    if pd.isna(numero):
        return "-"

    return f"{numero:.1f}%"


def formato_entero_miles(valor: Any) -> str:
    numero = valor_numerico(valor)

    if pd.isna(numero):
        return "-"

    return f"{int(round(numero)):,}".replace(",", ".")


def formato_decimal(valor: Any, decimales: int = 2) -> str:
    numero = valor_numerico(valor)

    if pd.isna(numero):
        return "-"

    return (
        f"{numero:,.{decimales}f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def estilo_estado_alerta(row: pd.Series) -> list[str]:
    nivel = str(row.get("Nivel alerta", row.get("Nivel estado material", ""))).strip()
    vencimiento = str(row.get("Estado vencimiento", row.get("Nivel estado material", ""))).strip()

    # Vencido: rojo
    if nivel == "Crítico" or vencimiento in ["Vencido", "Vence hoy"]:
        return ["background-color: #fee2e2; color: #7f1d1d; font-weight: 800"] * len(row)

    # Por vencer: naranja
    if nivel in ["Atención", "Seguimiento", "Por vencer"] or vencimiento in ["Por vencer", "1-7 días", "8-30 días"]:
        return ["background-color: #ffedd5; color: #7c2d12; font-weight: 800"] * len(row)

    # Recepcionado: verde
    if nivel in ["Cerrado", "Recepcionado"] or vencimiento in ["Recepcionado"]:
        return ["background-color: #dcfce7; color: #14532d; font-weight: 700"] * len(row)

    return [""] * len(row)


def estilo_tat_variabilidad(row: pd.Series) -> list[str]:
    cv = valor_numerico(row.get("Coeficiente variación % TAT", np.nan))
    max_tat = valor_numerico(row.get("Máximo TAT", np.nan))
    media = valor_numerico(row.get("Media TAT", np.nan))

    if pd.notna(cv) and cv >= 80:
        return ["background-color: #fee2e2; color: #7f1d1d; font-weight: 700"] * len(row)

    if pd.notna(cv) and cv >= 40:
        return ["background-color: #ffedd5; color: #7c2d12; font-weight: 700"] * len(row)

    if pd.notna(max_tat) and pd.notna(media) and max_tat > media * 2:
        return ["background-color: #fef9c3; color: #713f12; font-weight: 700"] * len(row)

    return [""] * len(row)


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

    return f"{codigo} · {nombre}" if nombre else codigo


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
        col_norm = col.replace("NME80FN", "ME80FN")

        if col_norm in df.columns:
            return df[col_norm]

    return pd.Series(pd.NaT, index=df.index)


def serie_combinada(df: pd.DataFrame, columnas: list[str]) -> pd.Series:
    resultado = pd.Series(pd.NA, index=df.index)

    for col in columnas:
        col_norm = col.replace("NME80FN", "ME80FN")

        if col_norm in df.columns:
            resultado = resultado.where(resultado.notna(), df[col_norm])

    return resultado


def parsear_valores_multiples(texto: str) -> list[str]:
    if not texto or not str(texto).strip():
        return []

    tokens = re.split(r"[\s,;|]+", str(texto).strip())

    salida = []
    vistos = set()

    for token in tokens:
        normalizado = normalizar_id(token)

        if normalizado and normalizado not in vistos:
            salida.append(normalizado)
            vistos.add(normalizado)

    return salida


def normalizar_serie_busqueda(serie: pd.Series) -> pd.Series:
    return (
        serie
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def obtener_columna_solped(df: pd.DataFrame) -> pd.Series:
    return serie_combinada(df, [COL_SOLPED])


def obtener_columna_pedido(df: pd.DataFrame) -> pd.Series:
    return serie_combinada(
        df,
        [
            COL_OC_ME5A,
            COL_OC_ME80FN,
            COL_OC_NME80FN,
        ],
    )


def obtener_columna_material(df: pd.DataFrame) -> pd.Series:
    if COL_MATERIAL in df.columns:
        return df[COL_MATERIAL]

    candidatas = [
        col for col in df.columns
        if "material" in col.lower()
    ]

    if candidatas:
        return df[candidatas[0]]

    return pd.Series(pd.NA, index=df.index)


def obtener_columna_texto(df: pd.DataFrame) -> pd.Series:
    if COL_TEXTO in df.columns:
        return df[COL_TEXTO]

    candidatas = [
        col for col in df.columns
        if "texto" in col.lower()
        or "descripcion" in col.lower()
        or "descripción" in col.lower()
    ]

    if candidatas:
        return df[candidatas[0]]

    return pd.Series(pd.NA, index=df.index)


def icono_nivel_alerta(valor: Any) -> str:
    texto = str(valor).strip()

    mapa = {
        "Crítico": "🔴 Crítico",
        "Atención": "🟠 Atención",
        "Seguimiento": "🟡 Seguimiento",
        "Controlado": "🔵 Controlado",
        "Datos incompletos": "🟤 Datos incompletos",
        "Cerrado": "🟢 Cerrado",
        "Sin datos": "⚪ Sin datos",
        "No encontrada": "⚫ No encontrada",
    }

    return mapa.get(texto, f"⚪ {texto}" if texto else "⚪ Sin datos")


def icono_estado_vencimiento(valor: Any) -> str:
    texto = str(valor).strip()

    mapa = {
        "Vencido": "🔴 Vencido",
        "Vence hoy": "🔴 Vence hoy",
        "1-7 días": "🟠 1-7 días",
        "8-30 días": "🟡 8-30 días",
        "+30 días": "🔵 +30 días",
        "Sin datos": "🟤 Sin datos",
        "Recepcionado": "🟢 Recepcionado",
        "-": "⚪ -",
        "No encontrada": "⚫ No encontrada",
    }

    return mapa.get(texto, f"⚪ {texto}" if texto else "⚪ -")


# ============================================================
# Preparación de datos
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_base_materiales(df_original: pd.DataFrame, hoy: pd.Timestamp) -> pd.DataFrame:
    df = limpiar_columnas(df_original.copy())
    df = normalizar_columnas_me80fn(df)
    df = convertir_fechas_visuales(df)

    fecha_recepcion = primera_columna_existente(
        df,
        [
            COL_FECHA_RECEPCION_FINAL,
            "Fecha recepción mercancía - ME80FN",
            "Fecha recepción mercancía - NME80FN",
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
        pedido_base = obtener_columna_pedido(df)
        df[COL_TIPO_OC] = pedido_base.apply(extraer_tipo_oc)
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

    df["dias_hasta_vencimiento"] = df["dias_restantes_int"].apply(texto_dias_restantes)
    df["fecha_vencimiento_texto"] = df["fecha_vencimiento_tat"].apply(formato_fecha)
    df["fecha_solicitud_texto"] = df["fecha_inicio_tat"].apply(formato_fecha)
    df["mes_solicitud"] = df["fecha_inicio_tat"].dt.to_period("M").astype("string")
    df["anio_solicitud"] = df["fecha_inicio_tat"].dt.year

    df["nivel_alerta"] = clasificar_nivel_alerta(df)
    df["clasificacion_vencimiento"] = clasificar_vencimiento(df)
    df["ultima_etapa_registrada"] = df.apply(obtener_ultima_etapa, axis=1)
    df["etapa_pendiente"] = df.apply(obtener_etapa_pendiente, axis=1)
    df["porcentaje_avance"] = df.apply(calcular_porcentaje_avance, axis=1)
    df["accion_sugerida"] = df.apply(obtener_accion_sugerida, axis=1)
    df["score_gestion"] = df.apply(calcular_score_gestion, axis=1)

    if COL_CENTRO in df.columns:
        df["centro_label"] = df[COL_CENTRO].apply(etiqueta_centro)
    else:
        df["centro_label"] = "Sin centro"

    df["_material_norm"] = obtener_columna_material(df).apply(normalizar_id)
    df["_solped_norm"] = obtener_columna_solped(df).apply(normalizar_id)
    df["_pedido_norm"] = obtener_columna_pedido(df).apply(normalizar_id)
    df["_texto_norm"] = normalizar_serie_busqueda(obtener_columna_texto(df))

    if COL_GRUPO_COMPRAS in df.columns:
        df["_grupo_compras_norm"] = normalizar_serie_busqueda(df[COL_GRUPO_COMPRAS]).str.upper()
    else:
        df["_grupo_compras_norm"] = ""

    if COL_CENTRO in df.columns:
        df["_centro_norm"] = normalizar_serie_busqueda(df[COL_CENTRO]).str.upper()
    else:
        df["_centro_norm"] = ""

    return df


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


def clasificar_vencimiento(df: pd.DataFrame) -> pd.Series:
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


def obtener_ultima_etapa(row: pd.Series) -> str:
    ultima = "Sin etapa registrada"

    for nombre, col in ETAPAS_LINEA_PEDIDO:
        if col in row.index and pd.notna(row.get(col, np.nan)):
            ultima = nombre

    return ultima


def obtener_etapa_pendiente(row: pd.Series) -> str:
    if str(row.get(COL_ESTADO_RECEPCION_ALERTA, "")).strip() == "Recepcionado":
        return "Cerrado"

    for nombre, col in ETAPAS_LINEA_PEDIDO:
        if col in row.index and pd.isna(row.get(col, np.nan)):
            return nombre

    return "Sin etapa pendiente"


def calcular_porcentaje_avance(row: pd.Series) -> float:
    total = len(ETAPAS_LINEA_PEDIDO)

    if total == 0:
        return 0.0

    completadas = 0

    for _, col in ETAPAS_LINEA_PEDIDO:
        if col in row.index and pd.notna(row.get(col, np.nan)):
            completadas += 1

    return round(completadas / total * 100, 2)


def obtener_accion_sugerida(row: pd.Series) -> str:
    nivel = str(row.get("nivel_alerta", ""))

    if nivel == "Crítico":
        return "Gestionar recepción o regularización inmediata."

    if nivel == "Atención":
        return "Gestionar hoy o esta semana para evitar vencimiento."

    if nivel == "Seguimiento":
        return "Mantener seguimiento preventivo antes de entrar en tramo crítico."

    if nivel == "Controlado":
        return "Monitoreo preventivo. Sin urgencia inmediata."

    if nivel == "Datos incompletos":
        return "Corregir fechas base, tipo OC o umbral TAT."

    if nivel == "Cerrado":
        return "Sin acción urgente. Registro recepcionado."

    return "Revisar registro."


def calcular_score_gestion(row: pd.Series) -> float:
    nivel = str(row.get("nivel_alerta", ""))
    dias = valor_numerico(row.get("dias_restantes_int", np.nan))
    avance = valor_numerico(row.get("porcentaje_avance", np.nan))
    dias_tat = valor_numerico(row.get(COL_DIAS_TAT, np.nan))
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

    elif nivel == "Cerrado":
        score += 10

    if pd.notna(avance):
        score += max(0, 100 - avance)

    if pd.notna(dias_tat):
        score += max(dias_tat, 0) * 0.1

    if pd.notna(monto) and monto > 0:
        score += min(np.log10(monto + 1) * 10, 100)

    return round(score, 2)


# ============================================================
# Filtros
# ============================================================

def filtrar_por_tokens(
    df: pd.DataFrame,
    columna: str,
    tokens: list[str],
    modo: str,
    upper: bool = False,
) -> pd.Series:
    if not tokens:
        return pd.Series(True, index=df.index)

    if columna not in df.columns:
        return pd.Series(False, index=df.index)

    serie = normalizar_serie_busqueda(df[columna])

    if upper:
        serie = serie.str.upper()
        tokens = [token.upper() for token in tokens]

    if modo == "Exacta":
        return serie.isin(tokens)

    mask = pd.Series(False, index=df.index)

    for token in tokens:
        mask = mask | serie.str.contains(
            str(token),
            case=False,
            na=False,
            regex=False,
        )

    return mask


def aplicar_filtros_materiales(
    df: pd.DataFrame,
    materiales: list[str],
    modo_material: str,
    centros: list[str],
    grupos: list[str],
    estados: list[str],
    incluir_cerrados: bool,
) -> pd.DataFrame:
    base = df.copy()

    mask = filtrar_por_tokens(
        base,
        "_material_norm",
        materiales,
        modo_material,
        upper=False,
    )

    if centros:
        mask = mask & filtrar_por_tokens(
            base,
            "_centro_norm",
            centros,
            "Exacta",
            upper=True,
        )

    if grupos:
        mask = mask & filtrar_por_tokens(
            base,
            "_grupo_compras_norm",
            grupos,
            "Exacta",
            upper=True,
        )

    if estados and "nivel_alerta" in base.columns:
        mask = mask & base["nivel_alerta"].astype(str).isin(estados)

    resultado = base[mask].copy()

    if not incluir_cerrados:
        resultado = resultado[
            ~resultado[COL_ESTADO_RECEPCION_ALERTA].astype(str).eq("Recepcionado")
        ].copy()

    return resultado


def construir_resumen_busqueda_materiales(
    df_base: pd.DataFrame,
    df_filtrado: pd.DataFrame,
    materiales: list[str],
    modo_material: str,
) -> pd.DataFrame:
    registros = []

    if not materiales:
        return pd.DataFrame()

    for material in materiales:
        mask_base = filtrar_por_tokens(
            df_base,
            "_material_norm",
            [material],
            modo_material,
        )

        mask_filtrado = (
            filtrar_por_tokens(
                df_filtrado,
                "_material_norm",
                [material],
                modo_material,
            )
            if not df_filtrado.empty
            else pd.Series(False, index=df_filtrado.index)
        )

        registros_archivo = int(mask_base.sum())
        registros_filtrados = int(mask_filtrado.sum())

        if registros_filtrados > 0:
            resultado = "✅ Encontrado en resultado"
        elif registros_archivo > 0:
            resultado = "⚠️ Existe, pero no cumple filtros adicionales"
        else:
            resultado = "❌ No encontrado"

        registros.append(
            {
                "Material ingresado": material,
                "Resultado": resultado,
                "Registros en archivo": registros_archivo,
                "Registros filtrados": registros_filtrados,
            }
        )

    return pd.DataFrame(registros)


# ============================================================
# Estadísticas materiales
# ============================================================

def contar_unicos(series: pd.Series) -> int:
    return int(series.dropna().astype(str).replace("", pd.NA).dropna().nunique())


def primer_valor_frecuente(series: pd.Series) -> str:
    s = series.dropna().astype(str).str.strip()
    s = s[s.ne("")]

    if s.empty:
        return "-"

    return str(s.value_counts().index[0])


def crear_estadistica_materiales(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()

    material = base["_material_norm"].replace("", pd.NA)
    base = base[material.notna()].copy()

    if base.empty:
        return pd.DataFrame()

    base["_pedido_unificado"] = obtener_columna_pedido(base).apply(formato_id)
    base["_solped_unificada"] = obtener_columna_solped(base).apply(formato_id)
    base["_texto_material"] = obtener_columna_texto(base).fillna("-")
    base["_monto_num"] = pd.to_numeric(base.get(COL_MONTO, pd.Series(np.nan, index=base.index)), errors="coerce")
    base["_cantidad_num"] = pd.to_numeric(base.get(COL_CANTIDAD, pd.Series(np.nan, index=base.index)), errors="coerce")
    base["_dias_tat_num"] = pd.to_numeric(base.get(COL_DIAS_TAT, pd.Series(np.nan, index=base.index)), errors="coerce")
    base["_dias_inc_num"] = pd.to_numeric(base.get(COL_DIAS_INC, pd.Series(np.nan, index=base.index)), errors="coerce")

    tabla = (
        base
        .groupby("_material_norm", dropna=False)
        .agg(
            Registros=("_material_norm", "size"),
            SolPed_unicas=("_solped_unificada", contar_unicos),
            Pedidos_unicos=("_pedido_unificado", contar_unicos),
            Centros_unicos=("centro_label", contar_unicos),
            Grupos_compra_unicos=("_grupo_compras_norm", contar_unicos),
            Texto_referencial=("_texto_material", primer_valor_frecuente),
            Centro_principal=("centro_label", primer_valor_frecuente),
            Grupo_compra_principal=("_grupo_compras_norm", primer_valor_frecuente),
            Primera_solicitud=("fecha_inicio_tat", "min"),
            Ultima_solicitud=("fecha_inicio_tat", "max"),
            Cantidad_total=("_cantidad_num", "sum"),
            Monto_total=("_monto_num", "sum"),
            Monto_promedio=("_monto_num", "mean"),
            Dias_TAT_min=("_dias_tat_num", "min"),
            Dias_TAT_promedio=("_dias_tat_num", "mean"),
            Dias_TAT_std=("_dias_tat_num", "std"),
            Dias_TAT_max=("_dias_tat_num", "max"),
            Dias_incumplimiento_total=("_dias_inc_num", "sum"),
            Avance_promedio=("porcentaje_avance", "mean"),
            Score_maximo=("score_gestion", "max"),
            Score_promedio=("score_gestion", "mean"),
            Vencidos=("nivel_alerta", lambda s: int(s.astype(str).eq("Crítico").sum())),
            Por_vencer=("nivel_alerta", lambda s: int(s.astype(str).isin(["Atención", "Seguimiento"]).sum())),
            Datos_incompletos=("nivel_alerta", lambda s: int(s.astype(str).eq("Datos incompletos").sum())),
            Recepcionados=(COL_ESTADO_RECEPCION_ALERTA, lambda s: int(s.astype(str).eq("Recepcionado").sum())),
            Sin_recepcion=(COL_ESTADO_RECEPCION_ALERTA, lambda s: int(s.astype(str).eq("Sin recepción").sum())),
        )
        .reset_index()
        .rename(
            columns={
                "_material_norm": "Material",
                "SolPed_unicas": "SolPed únicas",
                "Pedidos_unicos": "Pedidos únicos",
                "Centros_unicos": "Centros únicos",
                "Grupos_compra_unicos": "Grupos compra únicos",
                "Grupo_compra_principal": "Grupo compra principal",
                "Primera_solicitud": "Primera solicitud",
                "Ultima_solicitud": "Última solicitud",
                "Cantidad_total": "Cantidad total",
                "Monto_total": "Monto total",
                "Monto_promedio": "Monto promedio",
                "Dias_TAT_min": "Días TAT min",
                "Dias_TAT_promedio": "Días TAT promedio",
                "Dias_TAT_std": "Días TAT std",
                "Dias_TAT_max": "Días TAT max",
                "Dias_incumplimiento_total": "Días incumplimiento total",
                "Avance_promedio": "Avance promedio",
                "Score_maximo": "Score máximo",
                "Score_promedio": "Score promedio",
            }
        )
    )

    tabla["Primera solicitud"] = pd.to_datetime(tabla["Primera solicitud"], errors="coerce")
    tabla["Última solicitud"] = pd.to_datetime(tabla["Última solicitud"], errors="coerce")

    tabla["Días desde última solicitud"] = (
        pd.Timestamp.today().normalize()
        - tabla["Última solicitud"]
    ).dt.days

    for col in ["Vencidos", "Por_vencer", "Datos_incompletos"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["Recurrencia"] = np.select(
        [
            tabla["Registros"].ge(20),
            tabla["Registros"].between(10, 19, inclusive="both"),
            tabla["Registros"].between(3, 9, inclusive="both"),
            tabla["Registros"].le(2),
        ],
        [
            "Muy recurrente",
            "Recurrente",
            "Ocasional",
            "Baja frecuencia",
        ],
        default="Sin datos",
    )

    tabla["Por vencer"] = tabla["Por_vencer"]
    tabla["Datos incompletos"] = tabla["Datos_incompletos"]

    tabla["Foco acción"] = (
        tabla["Vencidos"]
        + tabla["Por_vencer"]
        + tabla["Datos_incompletos"]
    )

    tabla["% foco acción"] = np.where(
        tabla["Registros"] > 0,
        tabla["Foco acción"] / tabla["Registros"] * 100,
        0,
    )

    tabla["% recepción"] = np.where(
        tabla["Registros"] > 0,
        tabla["Recepcionados"] / tabla["Registros"] * 100,
        0,
    )

    tabla["Coeficiente variación % TAT"] = np.where(
        pd.to_numeric(tabla["Días TAT promedio"], errors="coerce").abs().gt(0),
        pd.to_numeric(tabla["Días TAT std"], errors="coerce")
        / pd.to_numeric(tabla["Días TAT promedio"], errors="coerce").abs()
        * 100,
        np.nan,
    )

    tabla["Nivel estado material"] = np.select(
        [
            pd.to_numeric(tabla["Vencidos"], errors="coerce").fillna(0).gt(0),
            pd.to_numeric(tabla["Por_vencer"], errors="coerce").fillna(0).gt(0),
            pd.to_numeric(tabla["Datos_incompletos"], errors="coerce").fillna(0).gt(0),
            pd.to_numeric(tabla["Recepcionados"], errors="coerce").fillna(0).eq(tabla["Registros"]),
        ],
        [
            "Vencido",
            "Por vencer",
            "Datos incompletos",
            "Recepcionado",
        ],
        default="Controlado",
    )

    numeric_cols = [
        "Cantidad total",
        "Monto total",
        "Monto promedio",
        "Días TAT min",
        "Días TAT promedio",
        "Días TAT std",
        "Días TAT max",
        "Días incumplimiento total",
        "Avance promedio",
        "Score máximo",
        "Score promedio",
        "% foco acción",
        "% recepción",
        "Coeficiente variación % TAT",
    ]

    for col in numeric_cols:
        if col in tabla.columns:
            tabla[col] = pd.to_numeric(tabla[col], errors="coerce").round(2)

    tabla["Primera solicitud texto"] = tabla["Primera solicitud"].apply(formato_fecha)
    tabla["Última solicitud texto"] = tabla["Última solicitud"].apply(formato_fecha)

    tabla = tabla.sort_values(
        ["Foco acción", "Vencidos", "Score máximo", "Registros"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)

    return tabla


def crear_tabla_detalle_materiales(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()

    pedido = obtener_columna_pedido(base)
    solped = obtener_columna_solped(base)
    material = obtener_columna_material(base)
    texto = obtener_columna_texto(base)
    posicion = serie_combinada(base, [COL_POS_SOLPED, COL_POS_OC])

    tabla = pd.DataFrame(
        {
            "Material": material.apply(formato_id),
            "Texto breve": texto.fillna("-"),
            "Estado visual": base.get("nivel_alerta", pd.Series("-", index=base.index)).apply(icono_nivel_alerta),
            "Vencimiento visual": base.get("clasificacion_vencimiento", pd.Series("-", index=base.index)).apply(icono_estado_vencimiento),
            "% avance": pd.to_numeric(base.get("porcentaje_avance", pd.Series(0, index=base.index)), errors="coerce").fillna(0),
            "SolPed": solped.apply(formato_id),
            "Pedido": pedido.apply(formato_id),
            "Posición": posicion.apply(formato_id),
            "Centro": serie_combinada(base, [COL_CENTRO]).fillna("-"),
            "Centro nombre": base.get("centro_label", pd.Series("-", index=base.index)),
            "Grupo de compras": serie_combinada(base, [COL_GRUPO_COMPRAS]).fillna("-"),
            "Fecha solicitud": base.get("fecha_solicitud_texto", pd.Series("-", index=base.index)),
            "Fecha vencimiento TAT": base.get("fecha_vencimiento_texto", pd.Series("-", index=base.index)),
            "Días hasta vencimiento": base.get("dias_hasta_vencimiento", pd.Series("-", index=base.index)),
            "Estado recepción": base.get(COL_ESTADO_RECEPCION_ALERTA, pd.Series("-", index=base.index)),
            "Nivel alerta": base.get("nivel_alerta", pd.Series("-", index=base.index)),
            "Estado vencimiento": base.get("clasificacion_vencimiento", pd.Series("-", index=base.index)),
            "Última etapa": base.get("ultima_etapa_registrada", pd.Series("-", index=base.index)),
            "Etapa pendiente": base.get("etapa_pendiente", pd.Series("-", index=base.index)),
            "Cantidad": serie_combinada(base, [COL_CANTIDAD]).fillna("-"),
            "Unidad": serie_combinada(base, [COL_UNIDAD]).fillna("-"),
            "Monto": pd.to_numeric(serie_combinada(base, [COL_MONTO]), errors="coerce").fillna(0).round(0).astype(int),
            "Tipo OC": serie_combinada(base, [COL_TIPO_OC]).fillna("-"),
            "Sistema": serie_combinada(base, [COL_SISTEMA]).fillna("-"),
            "Origen": serie_combinada(base, [COL_ORIGEN]).fillna("-"),
            "Performance TAT total": serie_combinada(base, [COL_PERF_TAT]).fillna("-"),
            "Días TAT total": serie_combinada(base, [COL_DIAS_TAT]).fillna("-"),
            "Umbral TAT": serie_combinada(base, [COL_UMBRAL_TAT, "umbral_tat_calculado"]).fillna("-"),
            "Días incumplimiento": serie_combinada(base, [COL_DIAS_INC]).fillna("-"),
            "Acción sugerida": base.get("accion_sugerida", pd.Series("-", index=base.index)),
            "Score gestión": pd.to_numeric(base.get("score_gestion", pd.Series(0, index=base.index)), errors="coerce").fillna(0),
        }
    )

    return tabla.reset_index(drop=True)


def crear_tendencia_materiales(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "mes_solicitud" not in df.columns:
        return pd.DataFrame()

    base = df.copy()
    base = base[base["mes_solicitud"].notna()].copy()

    if base.empty:
        return pd.DataFrame()

    tabla = (
        base
        .groupby("mes_solicitud")
        .agg(
            Registros=("mes_solicitud", "size"),
            Materiales=("_material_norm", contar_unicos),
            SolPed=("_solped_norm", contar_unicos),
            Vencidos=("nivel_alerta", lambda s: int(s.astype(str).eq("Crítico").sum())),
            Sin_recepcion=(COL_ESTADO_RECEPCION_ALERTA, lambda s: int(s.astype(str).eq("Sin recepción").sum())),
            Monto=(COL_MONTO, lambda s: pd.to_numeric(s, errors="coerce").sum() if COL_MONTO in base.columns else 0),
        )
        .reset_index()
        .rename(columns={"mes_solicitud": "Mes"})
        .sort_values("Mes")
    )

    return tabla


def crear_ranking_centros_materiales(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    tabla = (
        df
        .groupby("centro_label", dropna=False)
        .agg(
            Registros=("centro_label", "size"),
            Materiales=("_material_norm", contar_unicos),
            Vencidos=("nivel_alerta", lambda s: int(s.astype(str).eq("Crítico").sum())),
            Por_vencer=("nivel_alerta", lambda s: int(s.astype(str).isin(["Atención", "Seguimiento"]).sum())),
            Sin_recepcion=(COL_ESTADO_RECEPCION_ALERTA, lambda s: int(s.astype(str).eq("Sin recepción").sum())),
        )
        .reset_index()
        .rename(columns={"centro_label": "Centro"})
    )

    tabla["Foco acción"] = tabla["Vencidos"] + tabla["Por_vencer"]
    tabla = tabla.sort_values(["Foco acción", "Registros"], ascending=[False, False])

    return tabla.reset_index(drop=True)


def crear_ranking_grupos_materiales(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or COL_GRUPO_COMPRAS not in df.columns:
        return pd.DataFrame()

    tabla = (
        df
        .groupby(COL_GRUPO_COMPRAS, dropna=False)
        .agg(
            Registros=(COL_GRUPO_COMPRAS, "size"),
            Materiales=("_material_norm", contar_unicos),
            Vencidos=("nivel_alerta", lambda s: int(s.astype(str).eq("Crítico").sum())),
            Por_vencer=("nivel_alerta", lambda s: int(s.astype(str).isin(["Atención", "Seguimiento"]).sum())),
            Sin_recepcion=(COL_ESTADO_RECEPCION_ALERTA, lambda s: int(s.astype(str).eq("Sin recepción").sum())),
        )
        .reset_index()
        .rename(columns={COL_GRUPO_COMPRAS: "Grupo de compras"})
    )

    tabla["Foco acción"] = tabla["Vencidos"] + tabla["Por_vencer"]
    tabla = tabla.sort_values(["Foco acción", "Registros"], ascending=[False, False])

    return tabla.reset_index(drop=True)



def crear_tabla_estadistica_tat_material(tabla_materiales: pd.DataFrame) -> pd.DataFrame:
    if tabla_materiales.empty:
        return pd.DataFrame()

    columnas_necesarias = [
        "Material",
        "Texto_referencial",
        "Registros",
        "Días TAT min",
        "Días TAT promedio",
        "Días TAT std",
        "Coeficiente variación % TAT",
        "Días TAT max",
        "Vencidos",
        "Por_vencer",
        "Nivel estado material",
    ]

    data = tabla_materiales.copy()

    for col in columnas_necesarias:
        if col not in data.columns:
            if col in ["Días TAT min", "Días TAT promedio", "Días TAT std", "Coeficiente variación % TAT", "Días TAT max", "Registros", "Vencidos", "Por_vencer"]:
                data[col] = 0
            else:
                data[col] = "-"

    salida = pd.DataFrame(
        {
            "Material": data["Material"],
            "Texto referencial": data["Texto_referencial"],
            "Nivel alerta": data["Nivel estado material"],
            "Registros": pd.to_numeric(data["Registros"], errors="coerce").fillna(0).round(0).astype(int),
            "Min TAT": pd.to_numeric(data["Días TAT min"], errors="coerce"),
            "Media TAT": pd.to_numeric(data["Días TAT promedio"], errors="coerce"),
            "Desviación estándar TAT": pd.to_numeric(data["Días TAT std"], errors="coerce"),
            "Coeficiente variación % TAT": pd.to_numeric(data["Coeficiente variación % TAT"], errors="coerce"),
            "Máximo TAT": pd.to_numeric(data["Días TAT max"], errors="coerce"),
            "Estado vencimiento": np.select(
                [
                    pd.to_numeric(data["Vencidos"], errors="coerce").fillna(0).gt(0),
                    pd.to_numeric(data["Por_vencer"], errors="coerce").fillna(0).gt(0),
                ],
                [
                    "Vencido",
                    "Por vencer",
                ],
                default="Sin foco",
            ),
        }
    )

    salida = salida.sort_values(
        ["Estado vencimiento", "Coeficiente variación % TAT", "Registros"],
        ascending=[True, False, False],
    ).reset_index(drop=True)

    return salida

# ============================================================
# Visualizaciones
# ============================================================

def preparar_figura():
    fig, ax = plt.subplots(figsize=(11.5, 5.8), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    return fig, ax


def formatear_ejes(ax):
    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0, colors="#475569")


def grafico_barras_horizontales(
    tabla: pd.DataFrame,
    columna_categoria: str,
    columna_valor: str,
    titulo: str,
    top_n: int = 12,
    mostrar_etiquetas: bool = True,
):
    if tabla.empty or columna_categoria not in tabla.columns or columna_valor not in tabla.columns:
        st.info("No hay datos para graficar.")
        return

    data = tabla.copy()
    data[columna_valor] = pd.to_numeric(data[columna_valor], errors="coerce").fillna(0)
    data = data[data[columna_valor].gt(0)].head(top_n).copy()

    if data.empty:
        st.info("No hay valores mayores a cero para graficar.")
        return

    data = data.sort_values(columna_valor, ascending=True)

    fig, ax = preparar_figura()

    valores = data[columna_valor].round(0).astype(int)

    ax.barh(
        data[columna_categoria].astype(str),
        valores,
    )

    max_valor = int(valores.max()) if len(valores) else 0

    if mostrar_etiquetas:
        for i, valor in enumerate(valores):
            ax.text(
                valor + max(max_valor * 0.02, 0.4),
                i,
                formato_entero_miles(valor),
                va="center",
                ha="left",
                fontsize=9.5,
                fontweight="bold",
                color="#0f172a",
            )

        ax.set_xlim(0, max(max_valor * 1.18, 5))
    else:
        ax.set_xlim(0, max(max_valor * 1.06, 5))

    # Eje X entero, sin decimales.
    from matplotlib.ticker import MaxNLocator
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))

    ax.set_title(
        titulo,
        fontsize=15,
        fontweight="bold",
        color="#0f172a",
        pad=16,
    )

    ax.set_xlabel(columna_valor, color="#0f172a")

    # Sin grilla ni borde externo.
    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0, colors="#475569")

    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def grafico_materiales_foco(tabla_materiales: pd.DataFrame, top_n: int = 12):
    if tabla_materiales.empty:
        st.info("No hay materiales para graficar.")
        return

    columnas = [
        "Material",
        "Vencidos",
        "Por_vencer",
        "Datos_incompletos",
        "Recepcionados",
        "Sin_recepcion",
        "Foco acción",
        "% foco acción",
        "Registros",
    ]

    if any(col not in tabla_materiales.columns for col in columnas):
        st.info("Faltan columnas para graficar foco por material.")
        return

    data = tabla_materiales.copy()
    data["Registros"] = pd.to_numeric(data["Registros"], errors="coerce").fillna(0)
    data["Foco acción"] = pd.to_numeric(data["Foco acción"], errors="coerce").fillna(0)
    data["% foco acción"] = pd.to_numeric(data["% foco acción"], errors="coerce").fillna(0)

    data = data[data["Registros"].gt(0)].copy()

    if data.empty:
        st.info("No hay materiales con registros para graficar.")
        return

    data = (
        data
        .sort_values(["Foco acción", "% foco acción", "Registros"], ascending=[False, False, False])
        .head(top_n)
        .copy()
    )

    data = data.sort_values("% foco acción", ascending=True).reset_index(drop=True)

    vencidos = pd.to_numeric(data["Vencidos"], errors="coerce").fillna(0)
    por_vencer = pd.to_numeric(data["Por_vencer"], errors="coerce").fillna(0)
    datos = pd.to_numeric(data["Datos_incompletos"], errors="coerce").fillna(0)
    recepcionados = pd.to_numeric(data["Recepcionados"], errors="coerce").fillna(0)

    registros = pd.to_numeric(data["Registros"], errors="coerce").replace(0, np.nan)

    pct_vencidos = (vencidos / registros * 100).fillna(0).to_numpy()
    pct_por_vencer = (por_vencer / registros * 100).fillna(0).to_numpy()
    pct_datos = (datos / registros * 100).fillna(0).to_numpy()
    pct_recepcionados = (recepcionados / registros * 100).fillna(0).to_numpy()

    y = np.arange(len(data))

    fig, ax = plt.subplots(figsize=(13.4, max(6.2, len(data) * 0.60)), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.barh(y, pct_vencidos, height=0.62, label="Vencido", color="#dc2626")
    ax.barh(y, pct_por_vencer, left=pct_vencidos, height=0.62, label="Por vencer / seguimiento", color="#f97316")
    ax.barh(y, pct_datos, left=pct_vencidos + pct_por_vencer, height=0.62, label="Datos incompletos", color="#ca8a04")
    ax.barh(
        y,
        pct_recepcionados,
        left=pct_vencidos + pct_por_vencer + pct_datos,
        height=0.62,
        label="Recepcionado",
        color="#16a34a",
    )

    for i, row in data.iterrows():
        foco = int(valor_numerico(row.get("Foco acción", 0)))
        total = int(valor_numerico(row.get("Registros", 0)))
        pct_foco = valor_numerico(row.get("% foco acción", 0))

        ax.text(
            101,
            i,
            f"{foco}/{total} foco · {pct_foco:.1f}%",
            va="center",
            ha="left",
            fontsize=9.2,
            fontweight="bold",
            color="#0f172a",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(data["Material"].astype(str), fontsize=9.5, color="#0f172a")

    ax.set_xlim(0, 124)
    ax.set_xlabel("% de registros del material", color="#0f172a", labelpad=10, fontweight="bold")

    ax.set_title(
        "Composición del riesgo por material",
        fontsize=16,
        fontweight="bold",
        color="#0f172a",
        pad=18,
    )

    ax.text(
        0,
        len(data) + 0.10,
        "Lectura: cada barra suma 100% del material. A la derecha se muestra cuántos registros requieren acción.",
        fontsize=9.2,
        color="#475569",
        ha="left",
        va="bottom",
    )

    leyenda = ax.legend(
        loc="upper center",
        frameon=False,
        ncol=4,
        bbox_to_anchor=(0.5, -0.13),
        fontsize=9.3,
        borderaxespad=0.0,
    )

    for texto in leyenda.get_texts():
        texto.set_color("#0f172a")
        texto.set_fontweight("bold")

    formatear_ejes(ax)
    ax.grid(axis="x", alpha=0.18)
    fig.tight_layout(rect=[0.02, 0.10, 0.98, 0.94])

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def grafico_tendencia_mensual(tabla: pd.DataFrame):
    if tabla.empty:
        st.info("No hay tendencia mensual disponible.")
        return

    data = tabla.copy().tail(24)

    fig, ax = plt.subplots(figsize=(12.5, 5.2), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    x = np.arange(len(data))

    ax.plot(
        x,
        data["Registros"],
        marker="o",
        linewidth=2.5,
        label="Registros",
    )

    if "Materiales" in data.columns:
        ax.plot(
            x,
            data["Materiales"],
            marker="o",
            linewidth=2.2,
            label="Materiales únicos",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(data["Mes"].astype(str), rotation=45, ha="right", fontsize=8.5)

    ax.set_title(
        "Evolución mensual de materiales solicitados",
        fontsize=15,
        fontweight="bold",
        color="#0f172a",
        pad=14,
    )

    ax.set_ylabel("Cantidad", color="#0f172a")

    ax.legend(frameon=False)
    formatear_ejes(ax)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)



def grafico_donut_distribucion(
    tabla: pd.DataFrame,
    columna_categoria: str,
    columna_valor: str,
    titulo: str,
    subtitulo: str = "registros foco acción",
    top_n: int = 8,
):
    if tabla.empty or columna_categoria not in tabla.columns or columna_valor not in tabla.columns:
        st.info("No hay datos para graficar donut.")
        return

    data = tabla.copy()
    data[columna_valor] = pd.to_numeric(data[columna_valor], errors="coerce").fillna(0)
    data = data[data[columna_valor].gt(0)].copy()

    if data.empty:
        st.info("No hay valores mayores a cero para graficar donut.")
        return

    data = data.sort_values(columna_valor, ascending=False).copy()

    if len(data) > top_n:
        top = data.head(top_n).copy()
        otros_valor = data.iloc[top_n:][columna_valor].sum()

        if otros_valor > 0:
            otros = pd.DataFrame(
                [
                    {
                        columna_categoria: "Otros",
                        columna_valor: otros_valor,
                    }
                ]
            )
            data = pd.concat([top, otros], ignore_index=True)
        else:
            data = top

    categorias = data[columna_categoria].astype(str).tolist()
    valores = data[columna_valor].round(0).astype(int).to_numpy()
    total = int(valores.sum())

    if total <= 0:
        st.info("No hay total disponible para graficar donut.")
        return

    fig, ax = plt.subplots(figsize=(8.2, 5.8), dpi=130)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    wedges, texts, autotexts = ax.pie(
        valores,
        labels=None,
        startangle=90,
        counterclock=False,
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 4 else "",
        pctdistance=0.78,
        wedgeprops={
            "width": 0.40,
            "linewidth": 2,
            "edgecolor": "white",
        },
    )

    for autotext in autotexts:
        autotext.set_fontweight("bold")
        autotext.set_fontsize(9)
        autotext.set_color("white")

    ax.text(
        0,
        0.08,
        formato_entero_miles(total),
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color="#0f172a",
    )

    ax.text(
        0,
        -0.12,
        subtitulo,
        ha="center",
        va="center",
        fontsize=9.5,
        fontweight="bold",
        color="#64748b",
    )

    etiquetas_leyenda = [
        f"{cat} · {formato_entero_miles(valor)} · {valor / total * 100:.1f}%"
        for cat, valor in zip(categorias, valores)
    ]

    ax.legend(
        wedges,
        etiquetas_leyenda,
        title="Distribución",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=8.5,
        title_fontsize=9.5,
    )

    ax.set_title(
        titulo,
        fontsize=14.5,
        fontweight="bold",
        color="#0f172a",
        pad=14,
    )

    ax.axis("equal")
    fig.tight_layout()
    fig.subplots_adjust(right=0.68)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)



# ============================================================
# Exportación
# ============================================================

def convertir_a_excel(
    detalle: pd.DataFrame,
    estadistica: pd.DataFrame,
    estadistica_tat: pd.DataFrame,
    tendencia: pd.DataFrame,
    resumen_busqueda: pd.DataFrame,
) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        detalle.to_excel(writer, index=False, sheet_name="Detalle")
        estadistica.to_excel(writer, index=False, sheet_name="Estadistica_material")
        estadistica_tat.to_excel(writer, index=False, sheet_name="Estadistica_TAT")
        tendencia.to_excel(writer, index=False, sheet_name="Tendencia")
        resumen_busqueda.to_excel(writer, index=False, sheet_name="Busqueda")

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow",
    )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(
    detalle: pd.DataFrame,
    estadistica: pd.DataFrame,
    estadistica_tat: pd.DataFrame,
    tendencia: pd.DataFrame,
    resumen_busqueda: pd.DataFrame,
) -> bytes:
    return convertir_a_excel(
        detalle=detalle,
        estadistica=estadistica,
        estadistica_tat=estadistica_tat,
        tendencia=tendencia,
        resumen_busqueda=resumen_busqueda,
    )


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


def generar_nombre_salida(extension: str) -> str:
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"15_VISTA_EJECUTIVA_MATERIALES_{fecha_hora}.{extension}"


# ============================================================
# APP
# ============================================================

mostrar_logo()

st.title("15_VISTA_EJECUTIVA_MATERIALES")
st.caption(
    "Vista ejecutiva para entender recurrencia, estado, compras, SolPed, pedidos, TAT y foco de gestión por material."
)

st.markdown(
    """
    <div class="info-card">
        <div class="info-card-title">Objetivo del módulo</div>
        <div class="info-card-text">
            Analiza materiales de forma ejecutiva. Puedes ingresar una lista de materiales de interés
            o revisar todos los materiales del archivo activo. La vista consolida múltiples SolPed y pedidos
            del mismo material para mostrar recurrencia, comportamiento histórico, estado TAT, vencimientos,
            centros, grupos de compra y foco de acción.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

if "df_tat" not in st.session_state or st.session_state.get("df_tat") is None:
    st.info("No hay archivo activo en sesión. Primero carga un archivo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

hoy = pd.Timestamp.today().normalize()

try:
    with st.spinner("Preparando vista ejecutiva de materiales..."):
        df_base = preparar_base_materiales(df_original, hoy)

except Exception as e:
    st.error("No se pudo preparar la base de materiales.")
    st.exception(e)
    st.stop()

if "_material_norm" not in df_base.columns or df_base["_material_norm"].replace("", pd.NA).dropna().empty:
    st.error("No se encontró información de materiales en el archivo activo.")
    st.stop()


# ============================================================
# Filtros
# ============================================================

with st.form("form_vista_materiales"):
    st.markdown("### Materiales de interés")
    st.caption(
        "Puedes pegar una lista de materiales o dejar el campo vacío para analizar todos los materiales del archivo."
    )

    texto_materiales = st.text_area(
        "Lista de materiales",
        placeholder=(
            "Ejemplo:\n"
            "20050351\n"
            "20050352\n\n"
            "También puedes separar por coma, punto y coma, barra vertical o espacios."
        ),
        height=160,
        key="vista_materiales_texto",
    )

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)

    with col_f1:
        modo_material = st.selectbox(
            "Modo material",
            options=["Exacta", "Contiene"],
            index=0,
            key="vista_materiales_modo",
        )

    with col_f2:
        incluir_cerrados = st.checkbox(
            "Incluir recepcionados/cerrados",
            value=True,
            key="vista_materiales_incluir_cerrados",
        )

    with col_f3:
        top_n = st.slider(
            "Top visualizaciones",
            min_value=5,
            max_value=30,
            value=12,
            step=1,
            key="vista_materiales_top_n",
        )

    with col_f4:
        modo_tabla = st.selectbox(
            "Orden estadística",
            options=[
                "Foco acción",
                "Mayor recurrencia",
                "Mayor monto",
                "Mayor TAT promedio",
                "Más reciente",
            ],
            index=0,
            key="vista_materiales_modo_tabla",
        )

    with st.expander("Filtros adicionales", expanded=False):
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            centros = st.multiselect(
                "Centro",
                options=sorted(df_base["_centro_norm"].dropna().astype(str).replace("", pd.NA).dropna().unique().tolist()),
                default=[],
                key="vista_materiales_centros",
            )

        with col_b:
            grupos = st.multiselect(
                "Grupo de compras",
                options=sorted(df_base["_grupo_compras_norm"].dropna().astype(str).replace("", pd.NA).dropna().unique().tolist()),
                default=[],
                key="vista_materiales_grupos",
            )

        with col_c:
            estados = st.multiselect(
                "Nivel alerta",
                options=[
                    "Crítico",
                    "Atención",
                    "Seguimiento",
                    "Controlado",
                    "Datos incompletos",
                    "Cerrado",
                    "Sin datos",
                ],
                default=[],
                key="vista_materiales_estados",
            )

    aplicar = st.form_submit_button(
        "Actualizar vista de materiales",
        type="primary",
        use_container_width=True,
    )


materiales_ingresados = parsear_valores_multiples(texto_materiales)

df_filtrado = aplicar_filtros_materiales(
    df=df_base,
    materiales=materiales_ingresados,
    modo_material=modo_material,
    centros=centros,
    grupos=grupos,
    estados=estados,
    incluir_cerrados=incluir_cerrados,
)

if not materiales_ingresados:
    df_filtrado = aplicar_filtros_materiales(
        df=df_base,
        materiales=[],
        modo_material=modo_material,
        centros=centros,
        grupos=grupos,
        estados=estados,
        incluir_cerrados=incluir_cerrados,
    )

resumen_busqueda = construir_resumen_busqueda_materiales(
    df_base=df_base,
    df_filtrado=df_filtrado,
    materiales=materiales_ingresados,
    modo_material=modo_material,
)


# ============================================================
# Resumen de búsqueda
# ============================================================

if materiales_ingresados:
    st.markdown("### Resultado de búsqueda de materiales")
    st.caption("Valida cuáles materiales ingresados tienen registros en el archivo activo y en el resultado filtrado.")

    col_b1, col_b2, col_b3, col_b4 = st.columns(4)

    encontrados = int(resumen_busqueda["Registros filtrados"].gt(0).sum()) if not resumen_busqueda.empty else 0
    sin_resultado = int(len(resumen_busqueda) - encontrados) if not resumen_busqueda.empty else 0

    col_b1.metric("Materiales ingresados", len(materiales_ingresados))
    col_b2.metric("Con resultado", encontrados)
    col_b3.metric("Sin resultado", sin_resultado)
    col_b4.metric("Registros filtrados", len(df_filtrado))

    with st.expander("Detalle de búsqueda de materiales", expanded=True):
        st.dataframe(
            resumen_busqueda,
            use_container_width=True,
            hide_index=True,
        )


if df_filtrado.empty:
    st.warning("No hay registros para los materiales/filtros seleccionados.")
    st.stop()


# ============================================================
# Estadísticas
# ============================================================

tabla_materiales = crear_estadistica_materiales(df_filtrado)
tabla_tat_material = crear_tabla_estadistica_tat_material(tabla_materiales)
tabla_detalle = crear_tabla_detalle_materiales(df_filtrado)
tabla_tendencia = crear_tendencia_materiales(df_filtrado)
ranking_centros = crear_ranking_centros_materiales(df_filtrado)
ranking_grupos = crear_ranking_grupos_materiales(df_filtrado)

if modo_tabla == "Mayor recurrencia":
    tabla_materiales = tabla_materiales.sort_values(["Registros", "Foco acción"], ascending=[False, False]).reset_index(drop=True)
elif modo_tabla == "Mayor monto":
    tabla_materiales = tabla_materiales.sort_values(["Monto total", "Foco acción"], ascending=[False, False]).reset_index(drop=True)
elif modo_tabla == "Mayor TAT promedio":
    tabla_materiales = tabla_materiales.sort_values(["Días TAT promedio", "Foco acción"], ascending=[False, False]).reset_index(drop=True)
elif modo_tabla == "Más reciente":
    tabla_materiales = tabla_materiales.sort_values(["Última solicitud", "Foco acción"], ascending=[False, False]).reset_index(drop=True)
else:
    tabla_materiales = tabla_materiales.sort_values(["Foco acción", "Vencidos", "Score máximo", "Registros"], ascending=[False, False, False, False]).reset_index(drop=True)


# ============================================================
# KPIs ejecutivos
# ============================================================

total_registros = len(df_filtrado)
total_materiales = int(df_filtrado["_material_norm"].replace("", pd.NA).dropna().nunique())
total_solpeds = int(df_filtrado["_solped_norm"].replace("", pd.NA).dropna().nunique())
total_pedidos = int(df_filtrado["_pedido_norm"].replace("", pd.NA).dropna().nunique())
vencidos = int(df_filtrado["nivel_alerta"].astype(str).eq("Crítico").sum())
por_vencer = int(df_filtrado["nivel_alerta"].astype(str).isin(["Atención", "Seguimiento"]).sum())
sin_recepcion = int(df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str).eq("Sin recepción").sum())
recepcionados = int(df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str).eq("Recepcionado").sum())
monto_total = pd.to_numeric(df_filtrado.get(COL_MONTO, pd.Series(np.nan, index=df_filtrado.index)), errors="coerce").sum()
tat_promedio = pd.to_numeric(df_filtrado.get(COL_DIAS_TAT, pd.Series(np.nan, index=df_filtrado.index)), errors="coerce").mean()

st.markdown("### Resumen ejecutivo")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Registros", f"{total_registros:,}".replace(",", "."))
k2.metric("Materiales únicos", f"{total_materiales:,}".replace(",", "."))
k3.metric("SolPed únicas", f"{total_solpeds:,}".replace(",", "."))
k4.metric("Pedidos únicos", f"{total_pedidos:,}".replace(",", "."))

k5, k6, k7, k8 = st.columns(4)
k5.metric("Vencidos", f"{vencidos:,}".replace(",", "."))
k6.metric("Por vencer / seguimiento", f"{por_vencer:,}".replace(",", "."))
k7.metric("Sin recepción", f"{sin_recepcion:,}".replace(",", "."))
k8.metric("Recepcionados", f"{recepcionados:,}".replace(",", "."))

k9, k10, k11, k12 = st.columns(4)
k9.metric("Monto total", formato_numero(monto_total))
k10.metric("TAT promedio", texto_tiempo(tat_promedio))
k11.metric("Centros", f"{df_filtrado['_centro_norm'].replace('', pd.NA).dropna().nunique():,}".replace(",", "."))
k12.metric("Grupos compra", f"{df_filtrado['_grupo_compras_norm'].replace('', pd.NA).dropna().nunique():,}".replace(",", "."))


# ============================================================
# Lectura ejecutiva
# ============================================================

material_mayor_foco = tabla_materiales.iloc[0]["Material"] if not tabla_materiales.empty else "-"
foco_mayor = int(tabla_materiales.iloc[0]["Foco acción"]) if not tabla_materiales.empty else 0
recurrencia_mayor = tabla_materiales.iloc[0]["Recurrencia"] if not tabla_materiales.empty else "-"

st.markdown(
    f"""
    <div class="quick-card">
        <div class="quick-card-title">Lectura ejecutiva</div>
        <div class="quick-card-text">
            <span class="badge badge-blue">Material foco: {material_mayor_foco}</span>
            <span class="badge badge-red">Foco acción: {foco_mayor}</span>
            <span class="badge badge-green">Recurrencia: {recurrencia_mayor}</span>
            <br><br>
            El análisis consolida todas las apariciones del material en el tiempo. 
            Un mismo material puede tener múltiples SolPed, pedidos, centros o grupos de compra,
            por lo que la estadística permite identificar recurrencia, concentración de riesgo y comportamiento operativo.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)



def crear_tabla_estadistica_tat_material(tabla_materiales: pd.DataFrame) -> pd.DataFrame:
    if tabla_materiales.empty:
        return pd.DataFrame()

    columnas_necesarias = [
        "Material",
        "Texto_referencial",
        "Registros",
        "Días TAT min",
        "Días TAT promedio",
        "Días TAT std",
        "Coeficiente variación % TAT",
        "Días TAT max",
        "Vencidos",
        "Por_vencer",
        "Nivel estado material",
    ]

    data = tabla_materiales.copy()

    for col in columnas_necesarias:
        if col not in data.columns:
            if col in ["Días TAT min", "Días TAT promedio", "Días TAT std", "Coeficiente variación % TAT", "Días TAT max", "Registros", "Vencidos", "Por_vencer"]:
                data[col] = 0
            else:
                data[col] = "-"

    salida = pd.DataFrame(
        {
            "Material": data["Material"],
            "Texto referencial": data["Texto_referencial"],
            "Nivel alerta": data["Nivel estado material"],
            "Registros": pd.to_numeric(data["Registros"], errors="coerce").fillna(0).round(0).astype(int),
            "Min TAT": pd.to_numeric(data["Días TAT min"], errors="coerce"),
            "Media TAT": pd.to_numeric(data["Días TAT promedio"], errors="coerce"),
            "Desviación estándar TAT": pd.to_numeric(data["Días TAT std"], errors="coerce"),
            "Coeficiente variación % TAT": pd.to_numeric(data["Coeficiente variación % TAT"], errors="coerce"),
            "Máximo TAT": pd.to_numeric(data["Días TAT max"], errors="coerce"),
            "Estado vencimiento": np.select(
                [
                    pd.to_numeric(data["Vencidos"], errors="coerce").fillna(0).gt(0),
                    pd.to_numeric(data["Por_vencer"], errors="coerce").fillna(0).gt(0),
                ],
                [
                    "Vencido",
                    "Por vencer",
                ],
                default="Sin foco",
            ),
        }
    )

    salida = salida.sort_values(
        ["Estado vencimiento", "Coeficiente variación % TAT", "Registros"],
        ascending=[True, False, False],
    ).reset_index(drop=True)

    return salida

# ============================================================
# Visualizaciones
# ============================================================

st.markdown("### Visualizaciones ejecutivas")

tab_g1, tab_g2, tab_g3, tab_g4 = st.tabs(
    [
        "Recurrencia",
        "Riesgo interpretativo",
        "Tendencia mensual",
        "Centro / grupo compra",
    ]
)

with tab_g1:
    grafico_barras_horizontales(
        tabla=tabla_materiales,
        columna_categoria="Material",
        columna_valor="Registros",
        titulo="Materiales más recurrentes",
        top_n=top_n,
        mostrar_etiquetas=False,
    )

with tab_g2:
    grafico_materiales_foco(tabla_materiales, top_n=top_n)

with tab_g3:
    grafico_tendencia_mensual(tabla_tendencia)

with tab_g4:
    col_centro, col_grupo = st.columns(2)

    with col_centro:
        grafico_donut_distribucion(
            tabla=ranking_centros,
            columna_categoria="Centro",
            columna_valor="Foco acción",
            titulo="Distribución del foco de acción por centro",
            subtitulo="foco por centro",
            top_n=min(top_n, 8),
        )

    with col_grupo:
        grafico_donut_distribucion(
            tabla=ranking_grupos,
            columna_categoria="Grupo de compras",
            columna_valor="Foco acción",
            titulo="Distribución del foco de acción por grupo de compras",
            subtitulo="foco por grupo",
            top_n=min(top_n, 8),
        )


# ============================================================
# Tabla estadística por material
# ============================================================

st.markdown("### Estadística por material")
st.caption("Consolida cada material considerando todas sus SolPed y pedidos asociados.")

columnas_estadistica_visual = [
    "Material",
    "Texto_referencial",
    "Nivel estado material",
    "Recurrencia",
    "Registros",
    "SolPed únicas",
    "Pedidos únicos",
    "Foco acción",
    "% foco acción",
    "Vencidos",
    "Por vencer",
    "Datos incompletos",
    "Recepcionados",
    "Sin_recepcion",
    "Monto total",
    "Monto promedio",
    "Cantidad total",
    "Días TAT min",
    "Días TAT promedio",
    "Días TAT std",
    "Días TAT max",
    "Coeficiente variación % TAT",
    "Avance promedio",
    "Score máximo",
    "Centro_principal",
    "Grupo compra principal",
    "Primera solicitud texto",
    "Última solicitud texto",
    "Días desde última solicitud",
]

columnas_estadistica_visual = [
    col for col in columnas_estadistica_visual
    if col in tabla_materiales.columns
]

tabla_materiales_visual = tabla_materiales[columnas_estadistica_visual].rename(
    columns={
        "Texto_referencial": "Texto referencial",
        "Centro_principal": "Centro principal",
        "Sin_recepcion": "Sin recepción",
    }
)

st.dataframe(
    tabla_materiales_visual.style.apply(estilo_estado_alerta, axis=1),
    use_container_width=True,
    hide_index=True,
    column_config={
        "Registros": st.column_config.NumberColumn(
            "Registros",
            format="%d",
        ),
        "% foco acción": st.column_config.ProgressColumn(
            "% foco acción",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "% recepción": st.column_config.ProgressColumn(
            "% recepción",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "Avance promedio": st.column_config.ProgressColumn(
            "Avance promedio",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "Monto total": st.column_config.NumberColumn(
            "Monto total",
            format="%d",
        ),
        "Monto promedio": st.column_config.NumberColumn(
            "Monto promedio",
            format="%d",
        ),
        "Score máximo": st.column_config.NumberColumn(
            "Score máximo",
            format="%.2f",
        ),
    },
)



# ============================================================
# Estadística TAT por material
# ============================================================

st.markdown("### Estadística TAT por material")
st.caption(
    "Tabla enfocada en variabilidad del TAT. El coeficiente de variación permite detectar materiales con comportamiento poco estable."
)

if tabla_tat_material.empty:
    st.info("No hay estadística TAT disponible para los materiales filtrados.")
else:
    st.dataframe(
        tabla_tat_material.style.apply(estilo_estado_alerta, axis=1).apply(estilo_tat_variabilidad, axis=1),
        use_container_width=True,
        hide_index=True,
        column_config={
            "Registros": st.column_config.NumberColumn(
                "Registros",
                format="%d",
            ),
            "Min TAT": st.column_config.NumberColumn(
                "Min TAT",
                format="%.2f",
            ),
            "Media TAT": st.column_config.NumberColumn(
                "Media TAT",
                format="%.2f",
            ),
            "Desviación estándar TAT": st.column_config.NumberColumn(
                "Desviación estándar TAT",
                format="%.2f",
            ),
            "Coeficiente variación % TAT": st.column_config.NumberColumn(
                "Coeficiente variación % TAT",
                format="%.2f%%",
            ),
            "Máximo TAT": st.column_config.NumberColumn(
                "Máximo TAT",
                format="%.2f",
            ),
        },
    )


# ============================================================
# Detalle operativo
# ============================================================

with st.expander("Detalle operativo por registro", expanded=False):
    st.caption("Detalle similar al filtro múltiple, pero enfocado en materiales.")

    st.dataframe(
        tabla_detalle,
        use_container_width=True,
        hide_index=True,
        column_config={
            "% avance": st.column_config.ProgressColumn(
                "% avance",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Monto": st.column_config.NumberColumn(
                "Monto",
                format="%d",
            ),
            "Score gestión": st.column_config.NumberColumn(
                "Score gestión",
                format="%.2f",
            ),
        },
    )


with st.expander("Tablas auxiliares", expanded=False):
    tab_aux1, tab_aux2, tab_aux3 = st.tabs(
        [
            "Tendencia",
            "Centros",
            "Grupos compra",
        ]
    )

    with tab_aux1:
        st.dataframe(tabla_tendencia, use_container_width=True, hide_index=True)

    with tab_aux2:
        st.dataframe(ranking_centros, use_container_width=True, hide_index=True)

    with tab_aux3:
        st.dataframe(ranking_grupos, use_container_width=True, hide_index=True)


# ============================================================
# Descarga
# ============================================================

with st.expander("Descargar resultado", expanded=False):
    st.markdown("### Descarga")

    firma_export = (
        f"{len(tabla_detalle)}_"
        f"{len(tabla_materiales)}_"
        f"{len(tabla_tat_material)}_"
        f"{hash(tuple(materiales_ingresados))}_"
        f"{modo_material}_"
        f"{incluir_cerrados}_"
        f"{top_n}_"
        f"{modo_tabla}"
    )

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        preparar_excel = st.button(
            "Preparar Excel",
            use_container_width=True,
            key="vista_materiales_preparar_excel",
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                st.session_state["vista_materiales_excel_bytes"] = convertir_a_excel_cache(
                    detalle=tabla_detalle,
                    estadistica=tabla_materiales,
                    estadistica_tat=tabla_tat_material,
                    tendencia=tabla_tendencia,
                    resumen_busqueda=resumen_busqueda,
                )
                st.session_state["vista_materiales_excel_firma"] = firma_export
                st.session_state["vista_materiales_excel_nombre"] = generar_nombre_salida("xlsx")

        if (
            st.session_state.get("vista_materiales_excel_bytes") is not None
            and st.session_state.get("vista_materiales_excel_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Excel",
                data=st.session_state["vista_materiales_excel_bytes"],
                file_name=st.session_state["vista_materiales_excel_nombre"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV detalle",
            use_container_width=True,
            key="vista_materiales_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["vista_materiales_csv_bytes"] = convertir_a_csv_cache(tabla_detalle)
                st.session_state["vista_materiales_csv_firma"] = firma_export
                st.session_state["vista_materiales_csv_nombre"] = generar_nombre_salida("csv")

        if (
            st.session_state.get("vista_materiales_csv_bytes") is not None
            and st.session_state.get("vista_materiales_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV detalle",
                data=st.session_state["vista_materiales_csv_bytes"],
                file_name=st.session_state["vista_materiales_csv_nombre"],
                mime="text/csv",
                use_container_width=True,
            )

    with col_d3:
        preparar_parquet = st.button(
            "Preparar Parquet detalle",
            use_container_width=True,
            key="vista_materiales_preparar_parquet",
        )

        if preparar_parquet:
            with st.spinner("Preparando Parquet..."):
                st.session_state["vista_materiales_parquet_bytes"] = convertir_a_parquet_cache(tabla_detalle)
                st.session_state["vista_materiales_parquet_firma"] = firma_export
                st.session_state["vista_materiales_parquet_nombre"] = generar_nombre_salida("parquet")

        if (
            st.session_state.get("vista_materiales_parquet_bytes") is not None
            and st.session_state.get("vista_materiales_parquet_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Parquet detalle",
                data=st.session_state["vista_materiales_parquet_bytes"],
                file_name=st.session_state["vista_materiales_parquet_nombre"],
                mime="application/octet-stream",
                use_container_width=True,
            )
