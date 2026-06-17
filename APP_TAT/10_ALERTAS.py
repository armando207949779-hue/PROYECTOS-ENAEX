# ============================================================
# 10_ALERTAS
# Dashboard de alertas TAT
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

import io
import base64
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================
# Si esta app se ejecuta dentro de st.navigation(),
# NO uses st.set_page_config aquí.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"

COLOR_CUMPLE = "#EF3E52"
COLOR_NO_CUMPLE = "#BFC3C7"
COLOR_META = "#0057B8"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"

COLOR_CRITICO = "#DC2626"
COLOR_ATENCION = "#F97316"
COLOR_SEGUIMIENTO = "#F4B400"
COLOR_CONTROLADO = "#16A34A"
COLOR_DATOS = "#CA8A04"
COLOR_SIN_DATOS = "#B0B4BB"
COLOR_CERRADO = "#64748B"

COL_SOLPED = "Solicitud de pedido - ME5A"
COL_OC_ME5A = "Pedido - ME5A"
COL_OC_ME80FN = "Documento de compras - ME80FN"
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
# ESTILOS
# No se modifica .block-container.
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            padding: 14px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
        }

        .alert-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 16px 18px;
            margin: 10px 0;
        }

        .alert-card-critical {
            border-left: 6px solid #dc2626;
            background: #fef2f2;
        }

        .alert-card-warning {
            border-left: 6px solid #f97316;
            background: #fff7ed;
        }

        .alert-card-data {
            border-left: 6px solid #ca8a04;
            background: #fefce8;
        }

        .alert-card-ok {
            border-left: 6px solid #16a34a;
            background: #f0fdf4;
        }

        .alert-title {
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 6px;
        }

        .alert-main {
            font-size: 1.15rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 5px;
        }

        .alert-text {
            font-size: 0.88rem;
            color: #334155;
            line-height: 1.45;
        }

        .stage-box {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            padding: 12px;
            min-height: 120px;
            text-align: center;
        }

        .stage-done {
            border-top: 5px solid #16a34a;
        }

        .stage-pending {
            border-top: 5px solid #dc2626;
        }

        .stage-neutral {
            border-top: 5px solid #94a3b8;
        }

        .stage-title {
            font-size: 0.74rem;
            font-weight: 800;
            color: #334155;
            text-transform: uppercase;
            margin-bottom: 6px;
        }

        .stage-date {
            font-size: 0.95rem;
            font-weight: 700;
            color: #0f172a;
        }

        .stage-status {
            margin-top: 8px;
            font-size: 0.78rem;
            font-weight: 700;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOGO
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
# UTILIDADES
# ============================================================

def normalizar_columnas_me80fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    renombrar = {
        col: col.replace("NME80FN", "ME80FN")
        for col in df.columns
        if "NME80FN" in col
    }

    df = df.rename(columns=renombrar)

    for col in ["Estado del match", "estado_match"]:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype("string")
                .str.replace("NME80FN", "ME80FN", regex=False)
            )

    return df


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


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

    if nombre:
        return f"{codigo} · {nombre}"

    return codigo


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


def valor_numerico(valor: Any) -> float:
    try:
        return float(pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0])
    except Exception:
        return np.nan


def formato_fecha(valor: Any) -> str:
    fecha = pd.to_datetime(valor, errors="coerce")

    if pd.isna(fecha):
        return "-"

    return fecha.strftime("%d-%m-%Y")


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
        if col in df.columns:
            return df[col]

    return pd.Series(pd.NaT, index=df.index)


def opciones_columna(df: pd.DataFrame, col: str, max_opciones: int = 800) -> list:
    if col not in df.columns:
        return []

    return (
        df[col]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()[:max_opciones]
    )


def columnas_existentes(df: pd.DataFrame, columnas: list[str]) -> list[str]:
    return [col for col in columnas if col in df.columns]


# ============================================================
# PREPARACIÓN PANEL ALERTAS
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_panel_alertas(df_original: pd.DataFrame, hoy: pd.Timestamp) -> pd.DataFrame:
    df = limpiar_columnas(df_original.copy())
    df = normalizar_columnas_me80fn(df)
    df = convertir_fechas_visuales(df)

    fecha_recepcion = primera_columna_existente(
        df,
        [
            COL_FECHA_RECEPCION_FINAL,
            "Fecha recepción mercancía - ME80FN",
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
        if COL_OC_ME5A in df.columns:
            df[COL_TIPO_OC] = df[COL_OC_ME5A].apply(extraer_tipo_oc)
        elif COL_OC_ME80FN in df.columns:
            df[COL_TIPO_OC] = df[COL_OC_ME80FN].apply(extraer_tipo_oc)
        else:
            df[COL_TIPO_OC] = pd.NA
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

    df["exceso_umbral_alerta"] = (
        df["dias_transcurridos_alerta"]
        - df["umbral_tat_calculado"]
    )

    df["tiempo_transcurrido_tat"] = df["dias_transcurridos_alerta"].apply(texto_tiempo)

    df["tiempo_excedido_umbral_texto"] = np.where(
        pd.to_numeric(df["exceso_umbral_alerta"], errors="coerce").gt(0),
        df["exceso_umbral_alerta"].apply(texto_tiempo),
        "Sin exceso",
    )

    df["fecha_vencimiento_texto"] = df["fecha_vencimiento_tat"].apply(formato_fecha)
    df["dias_hasta_vencimiento"] = df["dias_restantes_int"].apply(texto_dias_restantes)

    df["clasificacion_vencimiento"] = clasificar_vencimiento_alerta(df)
    df["nivel_alerta"] = clasificar_nivel_alerta(df)

    df["ultima_etapa_registrada"] = df.apply(obtener_ultima_etapa, axis=1)
    df["fecha_pendiente"] = df.apply(obtener_fecha_pendiente, axis=1)
    df["accion_sugerida"] = df.apply(obtener_accion_sugerida, axis=1)
    df["score_riesgo"] = df.apply(calcular_score_riesgo, axis=1)

    if COL_CENTRO in df.columns:
        df["centro_label"] = df[COL_CENTRO].apply(etiqueta_centro)
    else:
        df["centro_label"] = "Sin centro"

    return df


def clasificar_vencimiento_alerta(df: pd.DataFrame) -> pd.Series:
    estado = df[COL_ESTADO_RECEPCION_ALERTA].astype(str)
    dias = pd.to_numeric(df["dias_restantes_int"], errors="coerce")

    resultado = pd.Series("Sin datos", index=df.index, dtype="object")

    resultado.loc[estado.eq("Recepcionado")] = "Recepcionado"
    resultado.loc[estado.eq("Sin recepción") & dias.isna()] = "Sin datos"
    resultado.loc[estado.eq("Sin recepción") & dias.lt(0)] = "Vencido"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(0)] = "Vence hoy"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(1)] = "1 día"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(2)] = "2 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(3, 7, inclusive="both")] = "7 días"
    resultado.loc[estado.eq("Sin recepción") & dias.gt(7)] = "+7 días"

    return resultado


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


def obtener_ultima_etapa(row: pd.Series) -> str:
    ultima = "Sin etapa registrada"

    for nombre, col in ETAPAS_LINEA_PEDIDO:
        if col in row.index and pd.notna(row.get(col, np.nan)):
            ultima = nombre

    return ultima


def obtener_fecha_pendiente(row: pd.Series) -> str:
    if str(row.get(COL_ESTADO_RECEPCION_ALERTA, "")).strip() == "Recepcionado":
        return "Cerrado"

    for nombre, col in ETAPAS_LINEA_PEDIDO:
        if col in row.index and pd.isna(row.get(col, np.nan)):
            return nombre

    return "Sin fecha pendiente"


def obtener_accion_sugerida(row: pd.Series) -> str:
    nivel = str(row.get("nivel_alerta", ""))

    if nivel == "Crítico":
        return "Priorizar gestión inmediata y confirmar recepción o fecha pendiente."

    if nivel == "Atención":
        return "Gestionar antes del vencimiento y validar avance de la etapa pendiente."

    if nivel == "Seguimiento":
        return "Mantener seguimiento preventivo y revisar próximos hitos."

    if nivel == "Datos incompletos":
        return "Corregir fecha de solicitud, umbral TAT, tipo OC o fechas finales."

    if nivel == "Cerrado":
        return "Sin acción requerida. Pedido recepcionado."

    return "Revisar registro."


def calcular_score_riesgo(row: pd.Series) -> float:
    nivel = str(row.get("nivel_alerta", ""))
    dias = valor_numerico(row.get("dias_restantes_int", np.nan))
    dias_tat = valor_numerico(row.get(COL_DIAS_TAT, np.nan))
    dias_inc = valor_numerico(row.get(COL_DIAS_INC, np.nan))

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
        score += 250

    elif nivel == "Controlado":
        score += 100

    if pd.notna(dias_inc):
        score += max(dias_inc, 0) * 2

    if pd.notna(dias_tat):
        score += max(dias_tat, 0) * 0.1

    return round(score, 2)


# ============================================================
# RESÚMENES
# ============================================================

def construir_resumen_ejecutivo(df_total: pd.DataFrame, df_filtrado: pd.DataFrame) -> dict:
    total_archivo = len(df_total)
    total_filtrado = len(df_filtrado)

    pct_filtrado = (
        total_filtrado / total_archivo * 100
        if total_archivo
        else 0
    )

    estado = df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str)

    dias = pd.to_numeric(
        df_filtrado.get("dias_restantes_int", pd.Series(np.nan, index=df_filtrado.index)),
        errors="coerce",
    )

    sin_recepcion = estado.eq("Sin recepción")
    recepcionados = estado.eq("Recepcionado")

    vencidos = int((sin_recepcion & dias.lt(0)).sum())
    proximos = int((sin_recepcion & dias.between(0, 30, inclusive="both")).sum())
    sin_fecha = int((sin_recepcion & dias.isna()).sum())
    recepcionados_total = int(recepcionados.sum())

    if vencidos > 0:
        semaforo = "Crítico"
        mensaje = f"Hay {vencidos:,} registros vencidos sin recepción.".replace(",", ".")
        accion = "Priorizar pedidos vencidos sin recepción y revisar la etapa pendiente."
    elif proximos > 0:
        semaforo = "Atención"
        mensaje = f"Hay {proximos:,} registros próximos a vencer en los próximos 30 días.".replace(",", ".")
        accion = "Gestionar próximos vencimientos y confirmar avance de compras/proveedor/logística."
    elif sin_fecha > 0:
        semaforo = "Datos incompletos"
        mensaje = f"Hay {sin_fecha:,} registros sin fecha de vencimiento calculable.".replace(",", ".")
        accion = "Corregir datos base: fecha de solicitud, tipo OC, umbral TAT o fechas finales."
    else:
        semaforo = "Controlado"
        mensaje = "No se observan vencidos ni próximos a vencer sin recepción con los filtros actuales."
        accion = "Mantener seguimiento preventivo."

    return {
        "total_archivo": total_archivo,
        "total_filtrado": total_filtrado,
        "pct_filtrado": pct_filtrado,
        "vencidos": vencidos,
        "proximos": proximos,
        "sin_fecha": sin_fecha,
        "recepcionados": recepcionados_total,
        "semaforo": semaforo,
        "mensaje": mensaje,
        "accion": accion,
    }


def crear_desglose_alertas(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    orden = [
        "Crítico",
        "Atención",
        "Seguimiento",
        "Controlado",
        "Datos incompletos",
        "Cerrado",
        "Sin datos",
    ]

    tabla = (
        df["nivel_alerta"]
        .value_counts()
        .reindex(orden, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Nivel alerta", "Cantidad"]

    total = int(tabla["Cantidad"].sum())

    tabla["% del total filtrado"] = np.where(
        total > 0,
        tabla["Cantidad"] / total * 100,
        0,
    )

    tabla["% del total filtrado"] = tabla["% del total filtrado"].round(2)

    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    tabla.loc[len(tabla)] = {
        "Nivel alerta": "Total",
        "Cantidad": total,
        "% del total filtrado": 100.00 if total else 0,
    }

    return tabla


def crear_tabla_prioridad(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        "nivel_alerta",
        "clasificacion_vencimiento",
        "dias_hasta_vencimiento",
        "fecha_vencimiento_texto",
        "fecha_pendiente",
        "accion_sugerida",
        COL_SOLPED,
        COL_OC_ME5A,
        COL_OC_ME80FN,
        COL_POS_SOLPED,
        COL_MATERIAL,
        COL_TEXTO,
        COL_CENTRO,
        "centro_label",
        COL_GRUPO_COMPRAS,
        COL_TIPO_OC,
        COL_SISTEMA,
        COL_ORIGEN,
        COL_PERF_TAT,
        COL_DIAS_TAT,
        COL_DIAS_INC,
        "score_riesgo",
    ]

    columnas = columnas_existentes(df, columnas)

    if not columnas:
        return pd.DataFrame()

    return (
        df[columnas]
        .sort_values("score_riesgo", ascending=False)
        .reset_index(drop=True)
    )


def resumen_materiales(df: pd.DataFrame) -> pd.DataFrame:
    if COL_MATERIAL not in df.columns:
        return pd.DataFrame()

    columnas_group = [COL_MATERIAL]

    if COL_TEXTO in df.columns:
        columnas_group.append(COL_TEXTO)

    base = df.copy()

    resumen = (
        base
        .groupby(columnas_group, dropna=False)
        .agg(
            Registros=(COL_MATERIAL, "size"),
            Criticos=("nivel_alerta", lambda s: int(s.eq("Crítico").sum())),
            Atencion=("nivel_alerta", lambda s: int(s.eq("Atención").sum())),
            Sin_recepcion=(COL_ESTADO_RECEPCION_ALERTA, lambda s: int(s.eq("Sin recepción").sum())),
            Recepcionados=(COL_ESTADO_RECEPCION_ALERTA, lambda s: int(s.eq("Recepcionado").sum())),
            Score_promedio=("score_riesgo", "mean"),
        )
        .reset_index()
    )

    resumen["Score_promedio"] = resumen["Score_promedio"].round(2)

    resumen = resumen.sort_values(
        ["Criticos", "Atencion", "Score_promedio", "Registros"],
        ascending=[False, False, False, False],
    )

    return resumen.reset_index(drop=True)


# ============================================================
# FILTROS
# ============================================================

def registrar_paso_filtro(
    resumen: list,
    paso: str,
    filtro: str,
    valor,
    df_antes: pd.DataFrame,
    df_despues: pd.DataFrame,
):
    antes = len(df_antes)
    despues = len(df_despues)

    resumen.append(
        {
            "Paso": paso,
            "Filtro aplicado": filtro,
            "Valor": valor,
            "Registros antes": antes,
            "Registros después": despues,
            "Registros excluidos": antes - despues,
            "% retenido": round(despues / antes * 100, 2) if antes else 0,
        }
    )


def contiene_texto(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)

    return df[columna].astype(str).str.contains(
        str(texto).strip(),
        case=False,
        na=False,
        regex=False,
    )


def filtrar_por_ids(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)

    tokens = [
        t.strip().replace(".0", "")
        for t in str(texto)
        .replace("\n", ",")
        .replace(";", ",")
        .replace(" ", ",")
        .split(",")
        if t.strip()
    ]

    if not tokens:
        return pd.Series(True, index=df.index)

    serie = df[columna].astype(str).str.replace(".0", "", regex=False)
    mask = pd.Series(False, index=df.index)

    for token in tokens:
        mask = mask | serie.str.contains(token, case=False, na=False, regex=False)

    return mask


def aplicar_filtros_alertas(
    df_base: pd.DataFrame,
    filtros: dict,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    barra = st.progress(0, text="Preparando filtros...")

    df = df_base.copy()

    resumen = [
        {
            "Paso": "Base inicial",
            "Filtro aplicado": "Sin filtro",
            "Valor": "Base procesada",
            "Registros antes": len(df_base),
            "Registros después": len(df_base),
            "Registros excluidos": 0,
            "% retenido": 100.0,
        }
    ]

    barra.progress(15, text="Aplicando búsquedas...")

    textos = [
        ("SolPed", COL_SOLPED, filtros.get("buscar_solped", "")),
        ("Pedido", COL_OC_ME5A, filtros.get("buscar_pedido", "")),
        ("Material", COL_MATERIAL, filtros.get("buscar_material", "")),
    ]

    for nombre, columna, texto in textos:
        if str(texto).strip() and columna in df.columns:
            antes = df.copy()
            df = df[filtrar_por_ids(df, columna, texto)].copy()

            registrar_paso_filtro(
                resumen,
                f"Filtro búsqueda {nombre}",
                nombre,
                texto,
                antes,
                df,
            )

    if str(filtros.get("buscar_texto", "")).strip() and COL_TEXTO in df.columns:
        antes = df.copy()
        df = df[contiene_texto(df, COL_TEXTO, filtros["buscar_texto"])].copy()

        registrar_paso_filtro(
            resumen,
            "Filtro texto",
            "Texto breve",
            filtros["buscar_texto"],
            antes,
            df,
        )

    barra.progress(35, text="Aplicando rango de vencimiento...")

    rango_vencimiento = filtros.get("rango_vencimiento")

    if rango_vencimiento is not None:
        if isinstance(rango_vencimiento, (tuple, list)) and len(rango_vencimiento) == 2:
            antes = df.copy()

            fecha_ini = pd.Timestamp(rango_vencimiento[0])
            fecha_fin = (
                pd.Timestamp(rango_vencimiento[1])
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
            )

            df = df[
                df["fecha_vencimiento_tat"].notna()
                & df["fecha_vencimiento_tat"].between(fecha_ini, fecha_fin)
            ].copy()

            registrar_paso_filtro(
                resumen,
                "Filtro fecha",
                "Fecha vencimiento TAT",
                f"{fecha_ini.date()} a {fecha_fin.date()}",
                antes,
                df,
            )

    barra.progress(55, text="Aplicando filtros categóricos...")

    filtros_multiselect = [
        ("Nivel alerta", "nivel_alerta", filtros.get("niveles", [])),
        ("Clasificación vencimiento", "clasificacion_vencimiento", filtros.get("clasificaciones", [])),
        ("Estado recepción", COL_ESTADO_RECEPCION_ALERTA, filtros.get("estados_recepcion", [])),
        ("Centro", COL_CENTRO, filtros.get("centros", [])),
        ("Grupo compras", COL_GRUPO_COMPRAS, filtros.get("grupos_compras", [])),
        ("Sistema", COL_SISTEMA, filtros.get("sistemas", [])),
        ("Tipo OC", COL_TIPO_OC, filtros.get("tipos_oc", [])),
    ]

    for nombre, columna, seleccion in filtros_multiselect:
        if seleccion and columna in df.columns:
            antes = df.copy()

            seleccion_norm = [str(x) for x in seleccion]

            df = df[
                df[columna].astype(str).isin(seleccion_norm)
            ].copy()

            registrar_paso_filtro(
                resumen,
                f"Filtro {nombre}",
                nombre,
                ", ".join(seleccion_norm),
                antes,
                df,
            )

    barra.progress(80, text="Ordenando por prioridad...")

    if "score_riesgo" in df.columns:
        df = df.sort_values("score_riesgo", ascending=False).copy()

    barra.progress(100, text="Filtros aplicados correctamente.")

    return df, pd.DataFrame(resumen)


# ============================================================
# GRÁFICOS
# ============================================================

def formatear_ejes(ax):
    ax.grid(False)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.tick_params(axis="both", length=0, colors=COLOR_MUTED)
    ax.set_facecolor("none")


def grafico_distribucion_alertas(df: pd.DataFrame):
    st.markdown("### Distribución de alertas")

    if df.empty or "nivel_alerta" not in df.columns:
        st.info("No hay datos para graficar.")
        return

    orden = [
        "Crítico",
        "Atención",
        "Seguimiento",
        "Controlado",
        "Datos incompletos",
        "Cerrado",
        "Sin datos",
    ]

    colores = {
        "Crítico": COLOR_CRITICO,
        "Atención": COLOR_ATENCION,
        "Seguimiento": COLOR_SEGUIMIENTO,
        "Controlado": COLOR_CONTROLADO,
        "Datos incompletos": COLOR_DATOS,
        "Cerrado": COLOR_CERRADO,
        "Sin datos": COLOR_SIN_DATOS,
    }

    tabla = (
        df["nivel_alerta"]
        .value_counts()
        .reindex(orden, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Nivel", "Cantidad"]
    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    if tabla.empty:
        st.info("No hay categorías disponibles.")
        return

    tabla = tabla.sort_values("Cantidad", ascending=True)

    y = np.arange(len(tabla))

    fig, ax = plt.subplots(figsize=(10, 4.5))

    ax.barh(
        y,
        tabla["Cantidad"],
        color=[colores.get(x, COLOR_MUTED) for x in tabla["Nivel"]],
        height=0.55,
    )

    for i, cantidad in enumerate(tabla["Cantidad"]):
        ax.text(
            cantidad + max(tabla["Cantidad"]) * 0.01,
            i,
            f"{int(cantidad):,}".replace(",", "."),
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(tabla["Nivel"], color=COLOR_MUTED)
    ax.set_xlabel("Cantidad de registros", color=COLOR_TEXTO)

    ax.set_title(
        "Distribución por nivel de alerta",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=12,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_vencimientos(df: pd.DataFrame):
    st.markdown("### Distribución por vencimiento")

    if df.empty or "clasificacion_vencimiento" not in df.columns:
        st.info("No hay datos para graficar.")
        return

    orden = [
        "Vencido",
        "Vence hoy",
        "1 día",
        "2 días",
        "7 días",
        "+7 días",
        "Sin datos",
        "Recepcionado",
    ]

    colores = {
        "Vencido": COLOR_CRITICO,
        "Vence hoy": COLOR_CRITICO,
        "1 día": COLOR_ATENCION,
        "2 días": COLOR_ATENCION,
        "7 días": COLOR_SEGUIMIENTO,
        "+7 días": COLOR_CONTROLADO,
        "Sin datos": COLOR_SIN_DATOS,
        "Recepcionado": COLOR_CERRADO,
    }

    tabla = (
        df["clasificacion_vencimiento"]
        .value_counts()
        .reindex(orden, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Clasificación", "Cantidad"]
    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    if tabla.empty:
        st.info("No hay clasificación de vencimientos.")
        return

    x = np.arange(len(tabla))

    fig, ax = plt.subplots(figsize=(11, 4.5))

    ax.bar(
        x,
        tabla["Cantidad"],
        color=[colores.get(x, COLOR_MUTED) for x in tabla["Clasificación"]],
        width=0.62,
    )

    for i, cantidad in enumerate(tabla["Cantidad"]):
        ax.text(
            i,
            cantidad + max(tabla["Cantidad"]) * 0.015,
            f"{int(cantidad):,}".replace(",", "."),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        tabla["Clasificación"],
        rotation=30,
        ha="right",
        color=COLOR_MUTED,
    )

    ax.set_ylabel("Cantidad", color=COLOR_TEXTO)

    ax.set_title(
        "Distribución por vencimiento TAT",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=12,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


# ============================================================
# VISUALES NATIVOS
# ============================================================

def mostrar_card_estado(resumen: dict):
    semaforo = resumen.get("semaforo", "Sin datos")

    if semaforo == "Crítico":
        clase = "alert-card alert-card-critical"
        color = "#991b1b"
    elif semaforo == "Atención":
        clase = "alert-card alert-card-warning"
        color = "#9a3412"
    elif semaforo == "Datos incompletos":
        clase = "alert-card alert-card-data"
        color = "#854d0e"
    else:
        clase = "alert-card alert-card-ok"
        color = "#166534"

    st.markdown(
        f"""
        <div class="{clase}">
            <div class="alert-title" style="color:{color};">Estado general del análisis</div>
            <div class="alert-main">{semaforo}</div>
            <div class="alert-text">{resumen.get("mensaje", "")}</div>
            <div class="alert-text" style="margin-top:8px;"><b>Acción sugerida:</b> {resumen.get("accion", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_timeline_pedido(row: pd.Series):
    st.markdown("#### Línea de pedido")

    cols = st.columns(len(ETAPAS_LINEA_PEDIDO))

    for idx, (nombre, col_fecha) in enumerate(ETAPAS_LINEA_PEDIDO):
        fecha = row.get(col_fecha, pd.NaT)
        completada = pd.notna(fecha)

        clase = "stage-box stage-done" if completada else "stage-box stage-pending"
        estado = "✓ Registrado" if completada else "Pendiente"
        fecha_txt = formato_fecha(fecha)

        with cols[idx]:
            st.markdown(
                f"""
                <div class="{clase}">
                    <div class="stage-title">{nombre}</div>
                    <div class="stage-date">{fecha_txt}</div>
                    <div class="stage-status">{estado}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def mostrar_expediente(row: pd.Series):
    st.markdown("### Expediente del pedido seleccionado")

    oc_principal = row.get(COL_OC_ME5A, row.get(COL_OC_ME80FN, np.nan))

    col_e1, col_e2, col_e3, col_e4, col_e5 = st.columns(5)

    col_e1.metric("SolPed", formato_id(row.get(COL_SOLPED, np.nan)))
    col_e2.metric("Pedido", formato_id(oc_principal))
    col_e3.metric("Centro", formato_valor(row.get(COL_CENTRO, np.nan)))
    col_e4.metric("Nivel alerta", formato_valor(row.get("nivel_alerta", np.nan)))
    col_e5.metric("Vencimiento", formato_valor(row.get("dias_hasta_vencimiento", np.nan)))

    col_i1, col_i2, col_i3, col_i4 = st.columns(4)

    col_i1.metric("Última etapa", formato_valor(row.get("ultima_etapa_registrada", np.nan)))
    col_i2.metric("Fecha pendiente", formato_valor(row.get("fecha_pendiente", np.nan)))
    col_i3.metric("TAT transcurrido", formato_valor(row.get("tiempo_transcurrido_tat", np.nan)))
    col_i4.metric("Exceso umbral", formato_valor(row.get("tiempo_excedido_umbral_texto", np.nan)))

    st.info(f"Acción sugerida: {formato_valor(row.get('accion_sugerida', np.nan))}")

    mostrar_timeline_pedido(row)

    detalle_cols = [
        COL_SOLPED,
        COL_OC_ME5A,
        COL_OC_ME80FN,
        COL_POS_SOLPED,
        COL_POS_OC,
        COL_MATERIAL,
        COL_TEXTO,
        COL_CENTRO,
        COL_GRUPO_COMPRAS,
        COL_SOLICITANTE,
        COL_AUTOR,
        COL_TIPO_OC,
        COL_SISTEMA,
        COL_ORIGEN,
        COL_PERF_TAT,
        COL_RANGO_INC,
        COL_DIAS_TAT,
        COL_DIAS_INC,
        COL_UMBRAL_TAT,
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_LIBERACION_FINAL,
        COL_FECHA_PEDIDO_FINAL,
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "fecha_vencimiento_tat",
        "nivel_alerta",
        "clasificacion_vencimiento",
        "score_riesgo",
    ]

    detalle_cols = columnas_existentes(pd.DataFrame([row]), detalle_cols)

    with st.expander("Detalle completo del registro", expanded=False):
        st.dataframe(
            pd.DataFrame([row])[detalle_cols],
            use_container_width=True,
            hide_index=True,
        )


def mostrar_tabla_alertas(df: pd.DataFrame, titulo: str, descripcion: str):
    st.markdown(f"### {titulo}")
    st.caption(descripcion)

    tabla = crear_tabla_prioridad(df)

    if tabla.empty:
        st.success("No hay registros para esta categoría con los filtros actuales.")
        return

    st.dataframe(
        tabla.head(300),
        use_container_width=True,
        hide_index=True,
    )

    st.caption(f"Mostrando hasta 300 registros de {len(tabla):,} disponibles.".replace(",", "."))


# ============================================================
# EXPORTACIÓN
# ============================================================

def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow",
    )

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


# ============================================================
# APP
# ============================================================

mostrar_logo()

st.title("10_ALERTAS")
st.caption("Gestión de alertas TAT, vencimientos y seguimiento de pedidos críticos.")

if "df_tat" not in st.session_state or st.session_state.get("df_tat") is None:
    st.info("No hay archivo activo en sesión. Primero carga un archivo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

hoy = pd.Timestamp.today().normalize()

try:
    with st.spinner("Preparando panel de alertas..."):
        df_panel = preparar_panel_alertas(df_original, hoy)

except Exception as e:
    st.error("No se pudo preparar el panel de alertas.")
    st.exception(e)
    st.stop()


# ============================================================
# FILTROS EN ENCABEZADO
# ============================================================

st.markdown("### Filtros")
st.caption("Configura filtros y presiona Aplicar filtros para actualizar el análisis.")

fechas_vencimiento = df_panel["fecha_vencimiento_tat"].dropna()

fecha_venc_min = fechas_vencimiento.min().date() if not fechas_vencimiento.empty else None
fecha_venc_max = fechas_vencimiento.max().date() if not fechas_vencimiento.empty else None

opciones_nivel = [
    x for x in ["Crítico", "Atención", "Seguimiento", "Controlado", "Datos incompletos", "Cerrado", "Sin datos"]
    if x in df_panel["nivel_alerta"].astype(str).unique()
]

opciones_clasificacion = [
    x for x in ["Vencido", "Vence hoy", "1 día", "2 días", "7 días", "+7 días", "Sin datos", "Recepcionado"]
    if x in df_panel["clasificacion_vencimiento"].astype(str).unique()
]

opciones_estado_recepcion = opciones_columna(df_panel, COL_ESTADO_RECEPCION_ALERTA)
opciones_centros = opciones_columna(df_panel, COL_CENTRO)
opciones_grupos_compras = opciones_columna(df_panel, COL_GRUPO_COMPRAS)
opciones_sistemas = opciones_columna(df_panel, COL_SISTEMA)
opciones_tipo_oc = opciones_columna(df_panel, COL_TIPO_OC)

with st.form("form_filtros_alertas"):
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        buscar_solped = st.text_input(
            "Buscar SolPed",
            placeholder="Ej: 10001234",
            key="alertas_buscar_solped",
        )

    with f2:
        buscar_pedido = st.text_input(
            "Buscar pedido",
            placeholder="Ej: 4500...",
            key="alertas_buscar_pedido",
        )

    with f3:
        buscar_material = st.text_input(
            "Buscar material",
            placeholder="Material",
            key="alertas_buscar_material",
        )

    with f4:
        buscar_texto = st.text_input(
            "Buscar texto breve",
            placeholder="Descripción",
            key="alertas_buscar_texto",
        )

    f5, f6, f7, f8 = st.columns(4)

    with f5:
        if fecha_venc_min is not None and fecha_venc_max is not None:
            rango_vencimiento = st.date_input(
                "Fecha vencimiento TAT",
                value=(fecha_venc_min, fecha_venc_max),
                min_value=fecha_venc_min,
                max_value=fecha_venc_max,
                key="alertas_rango_vencimiento",
            )
        else:
            rango_vencimiento = None
            st.warning("No hay fechas de vencimiento calculables.")

    with f6:
        niveles = st.multiselect(
            "Nivel alerta",
            options=opciones_nivel,
            default=opciones_nivel,
            key="alertas_niveles",
        )

    with f7:
        clasificaciones = st.multiselect(
            "Clasificación vencimiento",
            options=opciones_clasificacion,
            default=opciones_clasificacion,
            key="alertas_clasificaciones",
        )

    with f8:
        estados_recepcion = st.multiselect(
            "Estado recepción",
            options=opciones_estado_recepcion,
            default=opciones_estado_recepcion,
            key="alertas_estados_recepcion",
        )

    f9, f10, f11, f12 = st.columns(4)

    with f9:
        centros = st.multiselect(
            "Centro",
            options=opciones_centros,
            default=[],
            key="alertas_centros",
            help="Si no seleccionas centro, se consideran todos.",
        )

    with f10:
        grupos_compras = st.multiselect(
            "Grupo compras",
            options=opciones_grupos_compras,
            default=[],
            key="alertas_grupos_compras",
            help="Si no seleccionas grupo, se consideran todos.",
        )

    with f11:
        sistemas = st.multiselect(
            "Sistema",
            options=opciones_sistemas,
            default=[],
            key="alertas_sistemas",
            help="Si no seleccionas sistema, se consideran todos.",
        )

    with f12:
        tipos_oc = st.multiselect(
            "Tipo OC",
            options=opciones_tipo_oc,
            default=[],
            key="alertas_tipos_oc",
            help="Si no seleccionas tipo OC, se consideran todos.",
        )

    b1, b2 = st.columns(2)

    with b1:
        aplicar_filtros = st.form_submit_button(
            "Aplicar filtros",
            use_container_width=True,
            type="primary",
        )

    with b2:
        limpiar_filtros = st.form_submit_button(
            "Limpiar filtros",
            use_container_width=True,
        )


if limpiar_filtros:
    claves = [
        "alertas_buscar_solped",
        "alertas_buscar_pedido",
        "alertas_buscar_material",
        "alertas_buscar_texto",
        "alertas_rango_vencimiento",
        "alertas_niveles",
        "alertas_clasificaciones",
        "alertas_estados_recepcion",
        "alertas_centros",
        "alertas_grupos_compras",
        "alertas_sistemas",
        "alertas_tipos_oc",
        "alertas_df_filtrado",
        "alertas_resumen_filtros",
        "alertas_firma_filtros",
        "alertas_parquet_bytes",
        "alertas_parquet_firma",
        "alertas_csv_bytes",
        "alertas_csv_firma",
    ]

    for clave in claves:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


filtros = {
    "buscar_solped": buscar_solped,
    "buscar_pedido": buscar_pedido,
    "buscar_material": buscar_material,
    "buscar_texto": buscar_texto,
    "rango_vencimiento": rango_vencimiento,
    "niveles": niveles,
    "clasificaciones": clasificaciones,
    "estados_recepcion": estados_recepcion,
    "centros": centros,
    "grupos_compras": grupos_compras,
    "sistemas": sistemas,
    "tipos_oc": tipos_oc,
}

firma_filtros = str(filtros) + f"_{len(df_panel)}"

if aplicar_filtros:
    with st.spinner("Aplicando filtros..."):
        df_filtrado, resumen_filtros_df = aplicar_filtros_alertas(
            df_base=df_panel,
            filtros=filtros,
        )

        st.session_state["alertas_df_filtrado"] = df_filtrado
        st.session_state["alertas_resumen_filtros"] = resumen_filtros_df
        st.session_state["alertas_firma_filtros"] = firma_filtros

    st.success("Filtros aplicados correctamente.")

else:
    if (
        st.session_state.get("alertas_df_filtrado") is not None
        and st.session_state.get("alertas_firma_filtros") == firma_filtros
    ):
        df_filtrado = st.session_state["alertas_df_filtrado"].copy()
        resumen_filtros_df = st.session_state["alertas_resumen_filtros"].copy()
    else:
        df_filtrado = df_panel.copy()

        resumen_filtros_df = pd.DataFrame(
            [
                {
                    "Paso": "Base inicial",
                    "Filtro aplicado": "Sin filtro aplicado",
                    "Valor": "Base completa procesada",
                    "Registros antes": len(df_panel),
                    "Registros después": len(df_panel),
                    "Registros excluidos": 0,
                    "% retenido": 100.0,
                }
            ]
        )


# ============================================================
# INDICADORES
# ============================================================

resumen_ejecutivo = construir_resumen_ejecutivo(df_panel, df_filtrado)

total_archivo = resumen_ejecutivo["total_archivo"]
filtrados = resumen_ejecutivo["total_filtrado"]

estado_recepcion = df_filtrado[COL_ESTADO_RECEPCION_ALERTA].astype(str)
dias_restantes = pd.to_numeric(
    df_filtrado.get("dias_restantes_int", pd.Series(np.nan, index=df_filtrado.index)),
    errors="coerce",
)

sin_recepcion = estado_recepcion.eq("Sin recepción")
recepcionados = estado_recepcion.eq("Recepcionado")

vencidos_total = int((sin_recepcion & dias_restantes.lt(0)).sum())
proximos_total = int((sin_recepcion & dias_restantes.between(0, 30, inclusive="both")).sum())
sin_fecha_total = int((sin_recepcion & dias_restantes.isna()).sum())
recepcionados_total = int(recepcionados.sum())

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Registros filtrados",
    f"{filtrados:,}".replace(",", "."),
    f"{resumen_ejecutivo['pct_filtrado']:.1f}% del total" if total_archivo else "",
)

c2.metric("Vencidos sin recepción", f"{vencidos_total:,}".replace(",", "."))
c3.metric("Próximos 0-30 días", f"{proximos_total:,}".replace(",", "."))
c4.metric("Sin fecha calculable", f"{sin_fecha_total:,}".replace(",", "."))
c5.metric("Recepcionados", f"{recepcionados_total:,}".replace(",", "."))


# ============================================================
# RESUMEN EJECUTIVO
# ============================================================

mostrar_card_estado(resumen_ejecutivo)

desglose_alertas = crear_desglose_alertas(df_filtrado)

st.markdown("### Desglose de alertas")
st.caption("Cantidad y porcentaje de registros según nivel de alerta.")

if desglose_alertas.empty:
    st.info("No hay desglose disponible.")
else:
    st.dataframe(
        desglose_alertas,
        use_container_width=True,
        hide_index=True,
    )

col_g1, col_g2 = st.columns(2)

with col_g1:
    grafico_distribucion_alertas(df_filtrado)

with col_g2:
    grafico_vencimientos(df_filtrado)


# ============================================================
# ALERTAS PRIORITARIAS
# ============================================================

df_vencidos = df_filtrado[
    df_filtrado["nivel_alerta"].eq("Crítico")
].copy()

df_proximos = df_filtrado[
    df_filtrado["nivel_alerta"].isin(["Atención", "Seguimiento"])
].copy()

df_sin_fecha = df_filtrado[
    df_filtrado["nivel_alerta"].eq("Datos incompletos")
].copy()

mostrar_tabla_alertas(
    df_vencidos,
    "Alertas críticas",
    "Pedidos vencidos sin recepción. Son los casos de mayor prioridad.",
)

mostrar_tabla_alertas(
    df_proximos,
    "Próximos vencimientos",
    "Pedidos sin recepción que están por vencer o requieren seguimiento preventivo.",
)

with st.expander("Registros con datos incompletos", expanded=True):
    mostrar_tabla_alertas(
        df_sin_fecha,
        "Datos incompletos",
        "Registros sin fecha de vencimiento calculable. Requieren corrección de datos base.",
    )


# ============================================================
# EXPEDIENTE / GESTIÓN DE CRÍTICOS
# ============================================================

st.markdown("### Gestión de pedido crítico")
st.caption("Selecciona un registro priorizado para revisar su expediente y etapas TAT.")

df_prioridad = crear_tabla_prioridad(
    df_filtrado[
        df_filtrado["nivel_alerta"].isin(["Crítico", "Atención", "Seguimiento", "Datos incompletos"])
    ].copy()
)

if df_prioridad.empty:
    st.success("No hay pedidos críticos o de atención para gestionar con los filtros actuales.")
else:
    def etiqueta_registro(idx):
        row = df_prioridad.loc[idx]

        solped = formato_id(row.get(COL_SOLPED, np.nan))
        pedido = formato_id(row.get(COL_OC_ME5A, row.get(COL_OC_ME80FN, np.nan)))
        nivel = formato_valor(row.get("nivel_alerta", np.nan))
        venc = formato_valor(row.get("dias_hasta_vencimiento", np.nan))
        centro = formato_valor(row.get(COL_CENTRO, np.nan))

        return f"{nivel} · SolPed {solped} · Pedido {pedido} · {centro} · {venc}"

    indices = list(df_prioridad.index)

    seleccionado_idx = st.selectbox(
        "Registro a revisar",
        options=indices,
        index=0,
        format_func=etiqueta_registro,
        key="alertas_selector_expediente",
    )

    registro = df_prioridad.loc[seleccionado_idx]

    mostrar_expediente(registro)


# ============================================================
# ESTADÍSTICA POR MATERIAL
# ============================================================

st.markdown("### Estadística por material")
st.caption("Materiales con mayor concentración de alertas o registros sin recepción.")

resumen_mat = resumen_materiales(df_filtrado)

if resumen_mat.empty:
    st.info("No hay información de material disponible.")
else:
    st.dataframe(
        resumen_mat.head(100),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# DETALLE DE FILTROS
# ============================================================

with st.expander("Detalle de filtros aplicados", expanded=True):
    st.dataframe(
        resumen_filtros_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# DATOS FILTRADOS
# ============================================================

with st.expander("Datos filtrados", expanded=False):
    limite_vista = st.number_input(
        "Filas a mostrar",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
        key="alertas_limite_vista",
    )

    columnas_preferidas = [
        "nivel_alerta",
        "clasificacion_vencimiento",
        "dias_hasta_vencimiento",
        "fecha_vencimiento_texto",
        "fecha_pendiente",
        "accion_sugerida",
        COL_SOLPED,
        COL_OC_ME5A,
        COL_OC_ME80FN,
        COL_POS_SOLPED,
        COL_MATERIAL,
        COL_TEXTO,
        COL_CENTRO,
        "centro_label",
        COL_GRUPO_COMPRAS,
        COL_SOLICITANTE,
        COL_AUTOR,
        COL_TIPO_OC,
        COL_SISTEMA,
        COL_ORIGEN,
        COL_PERF_TAT,
        COL_RANGO_INC,
        COL_DIAS_TAT,
        COL_DIAS_INC,
        COL_UMBRAL_TAT,
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_LIBERACION_FINAL,
        COL_FECHA_PEDIDO_FINAL,
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "fecha_vencimiento_tat",
        "score_riesgo",
    ]

    columnas_preferidas = columnas_existentes(df_filtrado, columnas_preferidas)

    if columnas_preferidas:
        st.dataframe(
            df_filtrado[columnas_preferidas].head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(
            df_filtrado.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander("Ver columnas disponibles", expanded=False):
        ccol1, ccol2 = st.columns(2)

        with ccol1:
            st.markdown("**Columnas originales**")
            st.write(df_original.columns.tolist())

        with ccol2:
            st.markdown("**Columnas finales**")
            st.write(df_panel.columns.tolist())


# ============================================================
# DESCARGA
# ============================================================

with st.expander("Descargar resultado filtrado", expanded=False):
    st.caption(
        "Parquet es el formato recomendado. CSV se prepara solo cuando lo solicitas. Excel eliminado."
    )

    firma_export = f"{len(df_filtrado)}_{firma_filtros}"

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        preparar_parquet = st.button(
            "Preparar Parquet",
            use_container_width=True,
            key="alertas_preparar_parquet",
        )

        if preparar_parquet:
            with st.spinner("Preparando Parquet..."):
                st.session_state["alertas_parquet_bytes"] = convertir_a_parquet_cache(df_filtrado)
                st.session_state["alertas_parquet_firma"] = firma_export

        if (
            st.session_state.get("alertas_parquet_bytes") is not None
            and st.session_state.get("alertas_parquet_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Parquet",
                data=st.session_state["alertas_parquet_bytes"],
                file_name="alertas_tat_filtrado.parquet",
                mime="application/octet-stream",
                type="primary",
                use_container_width=True,
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV",
            use_container_width=True,
            key="alertas_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["alertas_csv_bytes"] = convertir_a_csv_cache(df_filtrado)
                st.session_state["alertas_csv_firma"] = firma_export

        if (
            st.session_state.get("alertas_csv_bytes") is not None
            and st.session_state.get("alertas_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV",
                data=st.session_state["alertas_csv_bytes"],
                file_name="alertas_tat_filtrado.csv",
                mime="text/csv",
                use_container_width=True,
            )
