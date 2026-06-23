# ============================================================
# 11_FILTRO_MULTIPLE
# Filtro múltiple de SolPed y tabla ordenada de gestión TAT
#
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Objetivo:
# - Permitir búsqueda múltiple de SolPed
# - Obtener una tabla de gestión ordenada
# - Mostrar fechas clave, estado, avance y acción sugerida
# - Descargar resultado filtrado
# ============================================================

import io
import re
import base64
from pathlib import Path
from typing import Any
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st


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

.block-title {
    font-size: 1.05rem;
    font-weight: 900;
    color: #0f172a;
    margin-bottom: 4px;
}

.block-subtitle {
    font-size: 0.88rem;
    color: #64748b;
    margin-bottom: 12px;
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


def columnas_existentes(df: pd.DataFrame, columnas: list[str]) -> list[str]:
    return [col for col in columnas if col in df.columns]


def parsear_solpeds(texto: str) -> list[str]:
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


def obtener_columna_solped(df: pd.DataFrame) -> str | None:
    if COL_SOLPED in df.columns:
        return COL_SOLPED

    candidatas = [
        col for col in df.columns
        if "solicitud" in col.lower()
        and "pedido" in col.lower()
    ]

    return candidatas[0] if candidatas else None


def obtener_columna_pedido(df: pd.DataFrame) -> pd.Series:
    return serie_combinada(
        df,
        [
            COL_OC_ME5A,
            COL_OC_ME80FN,
            COL_OC_NME80FN,
        ],
    )


# ============================================================
# Preparación de datos
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_base_gestion(df_original: pd.DataFrame, hoy: pd.Timestamp) -> pd.DataFrame:
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

    col_solped = obtener_columna_solped(df)

    if col_solped:
        df["_solped_norm"] = df[col_solped].apply(normalizar_id)
    else:
        df["_solped_norm"] = ""

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
# Tabla de gestión
# ============================================================


def ticket_fecha(valor: Any) -> str:
    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.notna(fecha):
        return "✅"

    return "❌"


def estado_busqueda_visual(encontrado: bool) -> str:
    return "✅ Encontrada" if encontrado else "❌ No encontrada"


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


def construir_resumen_busqueda(
    solpeds_ingresadas: list[str],
    solpeds_encontradas: list[str],
    solpeds_no_encontradas: list[str],
) -> pd.DataFrame:
    encontrados_set = set(solpeds_encontradas)
    no_encontrados_set = set(solpeds_no_encontradas)

    registros = []

    for idx, solped in enumerate(solpeds_ingresadas, start=1):
        encontrada = solped in encontrados_set

        registros.append(
            {
                "Orden": idx,
                "SolPed": solped,
                "Resultado": estado_busqueda_visual(encontrada),
            }
        )

    return pd.DataFrame(registros)


def crear_tabla_gestion(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    base = df.copy()

    pedido = obtener_columna_pedido(base)
    solped = serie_combinada(base, [COL_SOLPED])
    posicion = serie_combinada(base, [COL_POS_SOLPED, COL_POS_OC])

    fecha_solicitud = base.get(COL_FECHA_SOLICITUD_FINAL, pd.Series(pd.NaT, index=base.index))
    fecha_liberacion = base.get(COL_FECHA_LIBERACION_FINAL, pd.Series(pd.NaT, index=base.index))
    fecha_pedido = base.get(COL_FECHA_PEDIDO_FINAL, pd.Series(pd.NaT, index=base.index))
    fecha_facturacion = base.get(COL_FECHA_FACTURACION_FINAL, pd.Series(pd.NaT, index=base.index))
    fecha_recepcion = base.get(COL_FECHA_RECEPCION_FINAL, pd.Series(pd.NaT, index=base.index))

    nivel_alerta = base.get("nivel_alerta", pd.Series("-", index=base.index))
    estado_vencimiento = base.get("clasificacion_vencimiento", pd.Series("-", index=base.index))

    tabla = pd.DataFrame(
        {
            "Estado búsqueda": "✅ Encontrada",
            "SolPed": solped.apply(formato_id),
            "Estado visual": nivel_alerta.apply(icono_nivel_alerta),
            "Vencimiento visual": estado_vencimiento.apply(icono_estado_vencimiento),
            "% avance": pd.to_numeric(base.get("porcentaje_avance", pd.Series(0, index=base.index)), errors="coerce").fillna(0),
            "Fecha solicitud OK": fecha_solicitud.apply(ticket_fecha),
            "Fecha liberación OK": fecha_liberacion.apply(ticket_fecha),
            "Fecha pedido OK": fecha_pedido.apply(ticket_fecha),
            "Fecha facturación OK": fecha_facturacion.apply(ticket_fecha),
            "Fecha recepción OK": fecha_recepcion.apply(ticket_fecha),
            "Pedido": pedido.apply(formato_id),
            "Posición": posicion.apply(formato_id),
            "Estado recepción": base.get(COL_ESTADO_RECEPCION_ALERTA, pd.Series("-", index=base.index)),
            "Nivel alerta": nivel_alerta,
            "Estado vencimiento": estado_vencimiento,
            "Fecha solicitud": base.get("fecha_solicitud_texto", pd.Series("-", index=base.index)),
            "Fecha liberación": fecha_liberacion.apply(formato_fecha),
            "Fecha pedido": fecha_pedido.apply(formato_fecha),
            "Fecha facturación": fecha_facturacion.apply(formato_fecha),
            "Fecha recepción": fecha_recepcion.apply(formato_fecha),
            "Fecha vencimiento TAT": base.get("fecha_vencimiento_texto", pd.Series("-", index=base.index)),
            "Días hasta vencimiento": base.get("dias_hasta_vencimiento", pd.Series("-", index=base.index)),
            "Última etapa": base.get("ultima_etapa_registrada", pd.Series("-", index=base.index)),
            "Etapa pendiente": base.get("etapa_pendiente", pd.Series("-", index=base.index)),
            "Material": serie_combinada(base, [COL_MATERIAL]).fillna("-"),
            "Texto breve": serie_combinada(base, [COL_TEXTO]).fillna("-"),
            "Centro": serie_combinada(base, [COL_CENTRO]).fillna("-"),
            "Centro nombre": base.get("centro_label", pd.Series("-", index=base.index)),
            "Grupo de compras": serie_combinada(base, [COL_GRUPO_COMPRAS]).fillna("-"),
            "Tipo OC": serie_combinada(base, [COL_TIPO_OC]).fillna("-"),
            "Sistema": serie_combinada(base, [COL_SISTEMA]).fillna("-"),
            "Origen": serie_combinada(base, [COL_ORIGEN]).fillna("-"),
            "Performance TAT total": serie_combinada(base, [COL_PERF_TAT]).fillna("-"),
            "Días TAT total": serie_combinada(base, [COL_DIAS_TAT]).fillna("-"),
            "Umbral TAT": serie_combinada(base, [COL_UMBRAL_TAT, "umbral_tat_calculado"]).fillna("-"),
            "Días incumplimiento": serie_combinada(base, [COL_DIAS_INC]).fillna("-"),
            "Monto": serie_combinada(base, [COL_MONTO]).fillna("-"),
            "Acción sugerida": base.get("accion_sugerida", pd.Series("-", index=base.index)),
            "Score gestión": pd.to_numeric(base.get("score_gestion", pd.Series(0, index=base.index)), errors="coerce").fillna(0),
            "_orden_solped": base.get("_orden_solped", pd.Series(999999, index=base.index)),
        }
    )

    return tabla.reset_index(drop=True)


def ordenar_tabla(tabla: pd.DataFrame, modo: str) -> pd.DataFrame:
    if tabla.empty:
        return tabla

    tabla = tabla.copy()

    if modo == "Prioridad de gestión":
        return (
            tabla
            .sort_values(
                ["Score gestión", "% avance"],
                ascending=[False, True],
            )
            .reset_index(drop=True)
        )

    if modo == "Orden ingresado":
        return (
            tabla
            .sort_values(
                ["_orden_solped", "Score gestión"],
                ascending=[True, False],
            )
            .reset_index(drop=True)
        )

    if modo == "Menor avance primero":
        return (
            tabla
            .sort_values(
                ["% avance", "Score gestión"],
                ascending=[True, False],
            )
            .reset_index(drop=True)
        )

    if modo == "Mayor avance primero":
        return (
            tabla
            .sort_values(
                ["% avance", "Score gestión"],
                ascending=[False, False],
            )
            .reset_index(drop=True)
        )

    if modo == "Vencidos primero":
        prioridad_alerta = {
            "Crítico": 1,
            "Atención": 2,
            "Seguimiento": 3,
            "Datos incompletos": 4,
            "Controlado": 5,
            "Cerrado": 6,
            "Sin datos": 7,
        }

        tabla["_prioridad_alerta"] = tabla["Nivel alerta"].map(prioridad_alerta).fillna(99)

        tabla = (
            tabla
            .sort_values(
                ["_prioridad_alerta", "Score gestión"],
                ascending=[True, False],
            )
            .drop(columns=["_prioridad_alerta"])
            .reset_index(drop=True)
        )

        return tabla

    return tabla.reset_index(drop=True)




def reordenar_columnas_tabla_gestion(tabla: pd.DataFrame) -> pd.DataFrame:
    columnas_principales = [
        "SolPed",
        "Pedido",
        "Posición",
        "Texto breve",
    ]

    columnas_principales = [
        col for col in columnas_principales
        if col in tabla.columns
    ]

    columnas_restantes = [
        col for col in tabla.columns
        if col not in columnas_principales
    ]

    return tabla[columnas_principales + columnas_restantes].copy()


# ============================================================
# Exportación
# ============================================================

def preparar_tabla_exportar(tabla: pd.DataFrame) -> pd.DataFrame:
    tabla_export = tabla.copy()

    columnas_ocultas = [
        "_orden_solped",
    ]

    tabla_export = tabla_export.drop(
        columns=[
            col for col in columnas_ocultas
            if col in tabla_export.columns
        ],
        errors="ignore",
    )

    return tabla_export


def convertir_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Gestion",
        )

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
def convertir_a_excel_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_excel(df)


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


def generar_nombre_salida(extension: str) -> str:
    fecha_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"11_FILTRO_MULTIPLE_{fecha_hora}_GESTION.{extension}"


# ============================================================
# APP
# ============================================================

mostrar_logo()

st.title("11_FILTRO_MULTIPLE")
st.caption(
    "Filtro múltiple de SolPed para generar una tabla ordenada de gestión con fechas, estados y porcentaje de avance."
)

st.markdown(
    """
    <div class="info-card">
        <div class="info-card-title">Objetivo del módulo</div>
        <div class="info-card-text">
            Ingresa varias SolPed separadas por salto de línea, coma, punto y coma o espacios.
            El sistema buscará todos los registros asociados y construirá una tabla de gestión ordenada
            con las fechas principales, estado de recepción, nivel de alerta, etapa pendiente,
            porcentaje de avance y acción sugerida.
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
    with st.spinner("Preparando base de gestión..."):
        df_base = preparar_base_gestion(df_original, hoy)

except Exception as e:
    st.error("No se pudo preparar la base de gestión.")
    st.exception(e)
    st.stop()


col_solped_base = obtener_columna_solped(df_base)

if col_solped_base is None:
    st.error("No se encontró una columna de SolPed en el archivo cargado.")
    st.stop()


# ============================================================
# Entrada múltiple de SolPed
# ============================================================

with st.form("form_filtro_multiple_solped"):
    st.markdown("### Ingreso múltiple de SolPed")

    texto_solpeds = st.text_area(
        "Pega aquí las SolPed a gestionar",
        placeholder=(
            "Ejemplo:\n"
            "1001973319\n"
            "1001973320\n"
            "1001973321\n\n"
            "También puedes separarlas por coma, punto y coma o espacios."
        ),
        height=180,
        key="filtro_multiple_texto_solpeds",
    )

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        modo_orden = st.selectbox(
            "Orden de la tabla",
            options=[
                "Prioridad de gestión",
                "Orden ingresado",
                "Vencidos primero",
                "Menor avance primero",
                "Mayor avance primero",
            ],
            index=0,
            key="filtro_multiple_modo_orden",
        )

    with col_f2:
        mostrar_solo_con_resultado = st.checkbox(
            "Mostrar solo SolPed encontradas",
            value=True,
            key="filtro_multiple_solo_encontradas",
        )

    with col_f3:
        incluir_cerrados = st.checkbox(
            "Incluir recepcionados/cerrados",
            value=True,
            key="filtro_multiple_incluir_cerrados",
        )

    aplicar = st.form_submit_button(
        "Buscar SolPed",
        type="primary",
        use_container_width=True,
    )


solpeds_ingresadas = parsear_solpeds(texto_solpeds)

if not solpeds_ingresadas:
    st.info("Ingresa una o más SolPed para generar la tabla de gestión.")
    st.stop()


# ============================================================
# Filtro
# ============================================================

mapa_orden = {
    solped: idx
    for idx, solped in enumerate(solpeds_ingresadas)
}

df_filtrado = df_base[
    df_base["_solped_norm"].isin(solpeds_ingresadas)
].copy()

df_filtrado["_orden_solped"] = df_filtrado["_solped_norm"].map(mapa_orden).fillna(999999)

if not incluir_cerrados:
    df_filtrado = df_filtrado[
        ~df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str).eq("Recepcionado")
    ].copy()


solpeds_encontradas = (
    df_filtrado["_solped_norm"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

solpeds_no_encontradas = [
    solped for solped in solpeds_ingresadas
    if solped not in solpeds_encontradas
]


# ============================================================
# Resultado claro de búsqueda
# ============================================================

resumen_busqueda_df = construir_resumen_busqueda(
    solpeds_ingresadas=solpeds_ingresadas,
    solpeds_encontradas=solpeds_encontradas,
    solpeds_no_encontradas=solpeds_no_encontradas,
)

st.markdown("### Resultado de búsqueda")
st.caption("Identifica rápidamente cuáles SolPed fueron encontradas en el archivo activo y cuáles no.")

col_res_1, col_res_2 = st.columns(2)

with col_res_1:
    st.success(f"Encontradas: {len(solpeds_encontradas)} de {len(solpeds_ingresadas)}")

    if solpeds_encontradas:
        st.dataframe(
            pd.DataFrame({"✅ SolPed encontradas": solpeds_encontradas}),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No se encontraron SolPed en el archivo activo.")

with col_res_2:
    if solpeds_no_encontradas:
        st.error(f"No encontradas: {len(solpeds_no_encontradas)} de {len(solpeds_ingresadas)}")
        st.dataframe(
            pd.DataFrame({"❌ SolPed no encontradas": solpeds_no_encontradas}),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("Todas las SolPed ingresadas fueron encontradas.")

with st.expander("Ver listado completo de búsqueda", expanded=False):
    st.dataframe(
        resumen_busqueda_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# KPIs
# ============================================================

total_ingresadas = len(solpeds_ingresadas)
total_encontradas = len(solpeds_encontradas)
total_no_encontradas = len(solpeds_no_encontradas)
total_registros = len(df_filtrado)

vencidos = int(df_filtrado["nivel_alerta"].astype(str).eq("Crítico").sum()) if not df_filtrado.empty else 0
por_vencer = int(df_filtrado["nivel_alerta"].astype(str).isin(["Atención", "Seguimiento"]).sum()) if not df_filtrado.empty else 0
cerrados = int(df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str).eq("Recepcionado").sum()) if not df_filtrado.empty else 0

avance_promedio = (
    pd.to_numeric(df_filtrado["porcentaje_avance"], errors="coerce").mean()
    if not df_filtrado.empty
    else 0
)

st.markdown("### Resumen de búsqueda")

k1, k2, k3, k4 = st.columns(4)

k1.metric("SolPed ingresadas", total_ingresadas)
k2.metric("SolPed encontradas", total_encontradas)
k3.metric("SolPed no encontradas", total_no_encontradas)
k4.metric("Registros encontrados", total_registros)

k5, k6, k7, k8 = st.columns(4)

k5.metric("Vencidos", vencidos)
k6.metric("Por vencer / seguimiento", por_vencer)
k7.metric("Recepcionados", cerrados)
k8.metric("Avance promedio", formato_porcentaje(avance_promedio))


if solpeds_no_encontradas:
    with st.expander("SolPed no encontradas", expanded=True):
        st.warning(
            "Las siguientes SolPed no fueron encontradas en el archivo activo:"
        )

        st.dataframe(
            pd.DataFrame({"SolPed no encontrada": solpeds_no_encontradas}),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Tabla de gestión
# ============================================================

st.markdown("### Tabla ordenada de gestión")
st.caption(
    "Tabla priorizada con resultado de búsqueda, estado visual, vencimiento, fechas clave con ticket verde/rojo y porcentaje de avance."
)

if df_filtrado.empty:
    st.warning("No se encontraron registros para las SolPed ingresadas.")
    st.stop()

tabla_gestion = crear_tabla_gestion(df_filtrado)
tabla_gestion = ordenar_tabla(tabla_gestion, modo_orden)

if mostrar_solo_con_resultado:
    tabla_visual = tabla_gestion.copy()
else:
    filas_no_encontradas = pd.DataFrame(
        {
            "Estado búsqueda": "❌ No encontrada",
            "SolPed": solpeds_no_encontradas,
            "Estado visual": "⚫ No encontrada",
            "Vencimiento visual": "⚫ No encontrada",
            "% avance": 0,
            "Fecha solicitud OK": "❌",
            "Fecha liberación OK": "❌",
            "Fecha pedido OK": "❌",
            "Fecha facturación OK": "❌",
            "Fecha recepción OK": "❌",
            "Pedido": "-",
            "Posición": "-",
            "Estado recepción": "No encontrada",
            "Nivel alerta": "No encontrada",
            "Estado vencimiento": "No encontrada",
            "Fecha solicitud": "-",
            "Fecha liberación": "-",
            "Fecha pedido": "-",
            "Fecha facturación": "-",
            "Fecha recepción": "-",
            "Fecha vencimiento TAT": "-",
            "Días hasta vencimiento": "-",
            "Última etapa": "-",
            "Etapa pendiente": "-",
            "Material": "-",
            "Texto breve": "No encontrada en archivo activo",
            "Centro": "-",
            "Centro nombre": "-",
            "Grupo de compras": "-",
            "Tipo OC": "-",
            "Sistema": "-",
            "Origen": "-",
            "Performance TAT total": "-",
            "Días TAT total": "-",
            "Umbral TAT": "-",
            "Días incumplimiento": "-",
            "Monto": "-",
            "Acción sugerida": "Revisar número de SolPed o archivo cargado.",
            "Score gestión": 0,
            "_orden_solped": [
                mapa_orden.get(solped, 999999)
                for solped in solpeds_no_encontradas
            ],
        }
    )

    tabla_visual = pd.concat(
        [
            tabla_gestion,
            filas_no_encontradas,
        ],
        ignore_index=True,
    )

    tabla_visual = ordenar_tabla(tabla_visual, modo_orden)


tabla_visual = reordenar_columnas_tabla_gestion(tabla_visual)

st.dataframe(
    tabla_visual.drop(columns=["_orden_solped"], errors="ignore"),
    use_container_width=True,
    hide_index=True,
    column_config={
        "% avance": st.column_config.ProgressColumn(
            "% avance",
            format="%.1f%%",
            min_value=0,
            max_value=100,
        ),
        "Score gestión": st.column_config.NumberColumn(
            "Score gestión",
            format="%.2f",
        ),
    },
)


# ============================================================
# Vista por SolPed
# ============================================================

with st.expander("Vista resumida por SolPed", expanded=False):
    resumen_solped = (
        tabla_gestion
        .groupby("SolPed", dropna=False)
        .agg(
            Registros=("SolPed", "size"),
            Avance_promedio=("% avance", "mean"),
            Score_maximo=("Score gestión", "max"),
            Nivel_alerta_max=("Nivel alerta", lambda s: " | ".join(sorted(set(s.astype(str))))),
            Estado_recepcion=("Estado recepción", lambda s: " | ".join(sorted(set(s.astype(str))))),
        )
        .reset_index()
    )

    resumen_solped["Avance_promedio"] = resumen_solped["Avance_promedio"].round(2)

    resumen_solped = resumen_solped.sort_values(
        ["Score_maximo", "Avance_promedio"],
        ascending=[False, True],
    )

    st.dataframe(
        resumen_solped,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Avance_promedio": st.column_config.ProgressColumn(
                "Avance promedio",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Score_maximo": st.column_config.NumberColumn(
                "Score máximo",
                format="%.2f",
            ),
        },
    )


# ============================================================
# Descarga
# ============================================================

with st.expander("Descargar resultado", expanded=False):
    st.markdown("### Descarga")

    tabla_export = preparar_tabla_exportar(tabla_visual)

    firma_export = f"{len(tabla_export)}_{hash(tuple(solpeds_ingresadas))}_{modo_orden}_{incluir_cerrados}_{mostrar_solo_con_resultado}"

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        preparar_excel = st.button(
            "Preparar Excel",
            use_container_width=True,
            key="filtro_multiple_preparar_excel",
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                st.session_state["filtro_multiple_excel_bytes"] = convertir_a_excel_cache(tabla_export)
                st.session_state["filtro_multiple_excel_firma"] = firma_export
                st.session_state["filtro_multiple_excel_nombre"] = generar_nombre_salida("xlsx")

        if (
            st.session_state.get("filtro_multiple_excel_bytes") is not None
            and st.session_state.get("filtro_multiple_excel_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Excel",
                data=st.session_state["filtro_multiple_excel_bytes"],
                file_name=st.session_state["filtro_multiple_excel_nombre"],
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True,
            key="filtro_multiple_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["filtro_multiple_csv_bytes"] = convertir_a_csv_cache(tabla_export)
                st.session_state["filtro_multiple_csv_firma"] = firma_export
                st.session_state["filtro_multiple_csv_nombre"] = generar_nombre_salida("csv")

        if (
            st.session_state.get("filtro_multiple_csv_bytes") is not None
            and st.session_state.get("filtro_multiple_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV",
                data=st.session_state["filtro_multiple_csv_bytes"],
                file_name=st.session_state["filtro_multiple_csv_nombre"],
                mime="text/csv",
                use_container_width=True,
            )

    with col_d3:
        preparar_parquet = st.button(
            "Preparar Parquet",
            use_container_width=True,
            key="filtro_multiple_preparar_parquet",
        )

        if preparar_parquet:
            with st.spinner("Preparando Parquet..."):
                st.session_state["filtro_multiple_parquet_bytes"] = convertir_a_parquet_cache(tabla_export)
                st.session_state["filtro_multiple_parquet_firma"] = firma_export
                st.session_state["filtro_multiple_parquet_nombre"] = generar_nombre_salida("parquet")

        if (
            st.session_state.get("filtro_multiple_parquet_bytes") is not None
            and st.session_state.get("filtro_multiple_parquet_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Parquet",
                data=st.session_state["filtro_multiple_parquet_bytes"],
                file_name=st.session_state["filtro_multiple_parquet_nombre"],
                mime="application/octet-stream",
                use_container_width=True,
            )
