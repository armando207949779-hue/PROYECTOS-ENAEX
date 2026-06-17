# ============================================================
# 10_ALERTAS
# Dashboard de alertas TAT
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

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
COL_MATERIAL = "Material - ME5A"
COL_TEXTO = "Texto breve - ME5A"
COL_CENTRO = "Centro - ME5A"
COL_GRUPO_COMPRAS = "Grupo de compras"
COL_TIPO_OC = "tipo_oc"
COL_ORIGEN = "origen"
COL_SISTEMA = "sistema"
COL_PERF_TAT = "performance_tat_total"
COL_RANGO_INC = "rango_incumplimiento_tat"
COL_DIAS_TAT = "dias_tat_total"
COL_DIAS_INC = "dias_incumplimiento_tat"
COL_UMBRAL_TAT = "umbral_tat_total"
COL_ESTADO_RECEPCION_ALERTA = "estado_recepcion"

COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

COL_NIVEL_ALERTA_DESC = "nivel_alerta_descriptivo"

NIVELES_ALERTA_ORDEN = [
    "Crítico",
    "Atención",
    "Seguimiento",
    "Controlado",
    "Datos incompletos",
    "Cerrado",
    "Sin datos",
]

NIVEL_ALERTA_DESCRIPCION = {
    "Crítico": "Vencidos sin recepción",
    "Atención": "Vencen en 0 a 7 días sin recepción",
    "Seguimiento": "Vencen en 8 a 30 días sin recepción",
    "Controlado": "Más de 30 días para vencer",
    "Datos incompletos": "Datos incompletos para calcular vencimiento",
    "Cerrado": "Recepcionados",
    "Sin datos": "Sin datos",
}

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


def formato_cantidad(valor: Any) -> str:
    try:
        numero = int(valor)
        return f"{numero:,}".replace(",", ".")
    except Exception:
        return "0"


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


def describir_nivel_alerta(nivel: Any) -> str:
    if pd.isna(nivel):
        return "Sin datos"

    texto = str(nivel).strip()

    return NIVEL_ALERTA_DESCRIPCION.get(texto, texto)


def mensaje_vista_previa(
    titulo: str,
    total_registros: int,
    registros_mostrados: int,
    limite: int,
):
    total_txt = formato_cantidad(total_registros)
    mostrados_txt = formato_cantidad(registros_mostrados)

    if total_registros == 0:
        st.info(f"{titulo}: no hay registros disponibles con los filtros actuales.")
        return

    if registros_mostrados < total_registros:
        st.info(
            f"{titulo}: hay **{total_txt} registros disponibles**. "
            f"Se están mostrando **{mostrados_txt} registros** "
            f"por límite de vista previa ({limite})."
        )
    else:
        st.success(
            f"{titulo}: hay **{total_txt} registros disponibles**. "
            f"Se están mostrando **todos los registros**."
        )


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
    df[COL_NIVEL_ALERTA_DESC] = df["nivel_alerta"].apply(describir_nivel_alerta)

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
        mensaje = f"Hay {formato_cantidad(vencidos)} registros vencidos sin recepción."
        accion = "Priorizar pedidos vencidos sin recepción y revisar la etapa pendiente."
    elif proximos > 0:
        semaforo = "Atención"
        mensaje = f"Hay {formato_cantidad(proximos)} registros próximos a vencer en los próximos 30 días."
        accion = "Gestionar próximos vencimientos y confirmar avance de compras/proveedor/logística."
    elif sin_fecha > 0:
        semaforo = "Datos incompletos"
        mensaje = f"Hay {formato_cantidad(sin_fecha)} registros sin fecha de vencimiento calculable."
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
        "semaforo_descriptivo": describir_nivel_alerta(semaforo),
        "mensaje": mensaje,
        "accion": accion,
    }


def crear_desglose_alertas(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    tabla = (
        df["nivel_alerta"]
        .value_counts()
        .reindex(NIVELES_ALERTA_ORDEN, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["codigo_alerta", "Cantidad"]

    total = int(tabla["Cantidad"].sum())

    tabla["Nivel alerta"] = tabla["codigo_alerta"].apply(describir_nivel_alerta)

    tabla["% del total filtrado"] = np.where(
        total > 0,
        tabla["Cantidad"] / total * 100,
        0,
    )

    tabla["% del total filtrado"] = tabla["% del total filtrado"].round(2)

    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    tabla = tabla[
        [
            "Nivel alerta",
            "Cantidad",
            "% del total filtrado",
        ]
    ]

    tabla.loc[len(tabla)] = {
        "Nivel alerta": "Total",
        "Cantidad": total,
        "% del total filtrado": 100.00 if total else 0,
    }

    return tabla


def crear_tabla_prioridad(df: pd.DataFrame) -> pd.DataFrame:
    columnas = [
        COL_NIVEL_ALERTA_DESC,
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

    tabla = (
        df[columnas]
        .sort_values("score_riesgo", ascending=False)
        .reset_index(drop=True)
    )

    if COL_NIVEL_ALERTA_DESC in tabla.columns:
        tabla.insert(
            0,
            "Nivel alerta",
            tabla[COL_NIVEL_ALERTA_DESC],
        )

        tabla = tabla.drop(columns=[COL_NIVEL_ALERTA_DESC])

    if "nivel_alerta" in tabla.columns:
        tabla = tabla.drop(columns=["nivel_alerta"])

    return tabla


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

    barra.progress(25, text="Aplicando rango de vencimiento...")

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

    barra.progress(65, text="Aplicando filtros de alerta...")

    filtros_multiselect = [
        ("Tipo de alerta", COL_NIVEL_ALERTA_DESC, filtros.get("niveles", [])),
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

    barra.progress(90, text="Ordenando por prioridad...")

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


def crear_clasificacion_vencimiento_detallada(df: pd.DataFrame) -> pd.Series:
    estado = df[COL_ESTADO_RECEPCION_ALERTA].astype(str)

    dias = pd.to_numeric(
        df.get("dias_restantes_int", pd.Series(np.nan, index=df.index)),
        errors="coerce",
    )

    resultado = pd.Series("Sin datos", index=df.index, dtype="object")

    resultado.loc[estado.eq("Recepcionado")] = "Recepcionado"
    resultado.loc[estado.eq("Sin recepción") & dias.isna()] = "Sin datos"
    resultado.loc[estado.eq("Sin recepción") & dias.lt(0)] = "Vencido"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(0)] = "Vence hoy"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(1)] = "1 día"
    resultado.loc[estado.eq("Sin recepción") & dias.eq(2)] = "2 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(3, 7, inclusive="both")] = "3-7 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(8, 15, inclusive="both")] = "8-15 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(16, 30, inclusive="both")] = "16-30 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(31, 60, inclusive="both")] = "31-60 días"
    resultado.loc[estado.eq("Sin recepción") & dias.between(61, 90, inclusive="both")] = "61-90 días"
    resultado.loc[estado.eq("Sin recepción") & dias.gt(90)] = "+90 días"

    return resultado


def grafico_donut_alertas_porcentual(df: pd.DataFrame):
    st.markdown("### Porcentaje por tipo de alerta")

    if df.empty or "nivel_alerta" not in df.columns:
        st.info("No hay datos para graficar.")
        return

    colores_mapa = {
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
        .reindex(NIVELES_ALERTA_ORDEN, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Nivel", "Cantidad"]
    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    if tabla.empty:
        st.info("No hay categorías disponibles.")
        return

    tabla["Tipo de alerta"] = tabla["Nivel"].apply(describir_nivel_alerta)
    tabla["Color"] = tabla["Nivel"].map(colores_mapa).fillna(COLOR_MUTED)

    total = int(tabla["Cantidad"].sum())
    cantidades = tabla["Cantidad"].astype(int).to_numpy()
    etiquetas = tabla["Tipo de alerta"].astype(str).tolist()
    colores = tabla["Color"].tolist()

    fig, ax = plt.subplots(figsize=(8.2, 5.8))

    def autopct_func(pct):
        if pct < 4:
            return ""

        return f"{pct:.1f}%"

    wedges, texts, autotexts = ax.pie(
        cantidades,
        labels=None,
        startangle=90,
        counterclock=False,
        colors=colores,
        autopct=autopct_func,
        pctdistance=0.78,
        wedgeprops={
            "width": 0.38,
            "linewidth": 2.5,
            "edgecolor": "white",
        },
    )

    for autotext in autotexts:
        autotext.set_fontweight("bold")
        autotext.set_fontsize(9.5)
        autotext.set_color("white")

    ax.text(
        0,
        0.08,
        formato_cantidad(total),
        ha="center",
        va="center",
        fontsize=23,
        fontweight="bold",
        color=COLOR_TEXTO,
    )

    ax.text(
        0,
        -0.12,
        "registros",
        ha="center",
        va="center",
        fontsize=10,
        fontweight="bold",
        color=COLOR_MUTED,
    )

    porcentajes = np.where(
        total > 0,
        cantidades / total * 100,
        0,
    )

    etiquetas_leyenda = [
        f"{etiqueta} · {pct:.1f}%"
        for etiqueta, pct in zip(etiquetas, porcentajes)
    ]

    legend = ax.legend(
        wedges,
        etiquetas_leyenda,
        title="Leyenda porcentual",
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        fontsize=8.5,
        title_fontsize=9.5,
    )

    for texto in legend.get_texts():
        texto.set_color(COLOR_TEXTO)

    legend.get_title().set_color(COLOR_TEXTO)
    legend.get_title().set_fontweight("bold")

    ax.set_title(
        "Distribución porcentual por tipo de alerta",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=16,
    )

    ax.axis("equal")
    fig.patch.set_alpha(0)
    fig.tight_layout()
    fig.subplots_adjust(right=0.67)

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_alertas_valores_absolutos(df: pd.DataFrame):
    st.markdown("### Valores absolutos por vencimiento")

    if df.empty:
        st.info("No hay datos para graficar.")
        return

    df_grafico = df.copy()
    df_grafico["vencimiento_detallado"] = crear_clasificacion_vencimiento_detallada(df_grafico)

    orden = [
        "Vencido",
        "Vence hoy",
        "1 día",
        "2 días",
        "3-7 días",
        "8-15 días",
        "16-30 días",
        "31-60 días",
        "61-90 días",
        "+90 días",
        "Sin datos",
        "Recepcionado",
    ]

    colores_mapa = {
        "Vencido": COLOR_CRITICO,
        "Vence hoy": COLOR_CRITICO,
        "1 día": COLOR_ATENCION,
        "2 días": COLOR_ATENCION,
        "3-7 días": COLOR_SEGUIMIENTO,
        "8-15 días": COLOR_SEGUIMIENTO,
        "16-30 días": COLOR_CONTROLADO,
        "31-60 días": COLOR_CONTROLADO,
        "61-90 días": "#15803D",
        "+90 días": "#166534",
        "Sin datos": COLOR_SIN_DATOS,
        "Recepcionado": COLOR_CERRADO,
    }

    tabla = (
        df_grafico["vencimiento_detallado"]
        .value_counts()
        .reindex(orden, fill_value=0)
        .reset_index()
    )

    tabla.columns = ["Clasificación", "Cantidad"]
    tabla = tabla[tabla["Cantidad"].gt(0)].copy()

    if tabla.empty:
        st.info("No hay clasificación de vencimientos.")
        return

    tabla = tabla.sort_values("Cantidad", ascending=True)

    y = np.arange(len(tabla))

    fig, ax = plt.subplots(figsize=(8.6, 5.8))

    ax.barh(
        y,
        tabla["Cantidad"],
        color=[colores_mapa.get(x, COLOR_MUTED) for x in tabla["Clasificación"]],
        height=0.55,
    )

    max_cantidad = max(tabla["Cantidad"]) if len(tabla) else 0

    for i, cantidad in enumerate(tabla["Cantidad"]):
        ax.text(
            cantidad + max_cantidad * 0.01,
            i,
            formato_cantidad(cantidad),
            va="center",
            ha="left",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_yticks(y)
    ax.set_yticklabels(tabla["Clasificación"], color=COLOR_MUTED)
    ax.set_xlabel("Cantidad de registros", color=COLOR_TEXTO)

    ax.set_title(
        "Valores absolutos por vencimiento detallado",
        fontsize=14,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=12,
    )

    formatear_ejes(ax)

    fig.patch.set_alpha(0)
    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)


def grafico_vencidos_por_anio(df_vencidos: pd.DataFrame):
    st.markdown("### Vencidos sin recepción por año")

    if df_vencidos.empty:
        st.info("No hay vencidos sin recepción para graficar.")
        return

    df_grafico = df_vencidos.copy()

    df_grafico["fecha_vencimiento_tat"] = pd.to_datetime(
        df_grafico["fecha_vencimiento_tat"],
        errors="coerce",
    )

    df_grafico = df_grafico[df_grafico["fecha_vencimiento_tat"].notna()].copy()

    if df_grafico.empty:
        st.info("No hay fechas de vencimiento válidas para graficar por año.")
        return

    df_grafico["anio_vencimiento"] = df_grafico["fecha_vencimiento_tat"].dt.year

    tabla = (
        df_grafico
        .groupby("anio_vencimiento")
        .size()
        .reset_index(name="Cantidad")
        .sort_values("anio_vencimiento", ascending=False)
    )

    x = np.arange(len(tabla))

    fig, ax = plt.subplots(figsize=(8.4, 4.8))

    ax.bar(
        x,
        tabla["Cantidad"],
        color=COLOR_CRITICO,
        width=0.58,
    )

    max_cantidad = max(tabla["Cantidad"]) if len(tabla) else 0

    for i, cantidad in enumerate(tabla["Cantidad"]):
        ax.text(
            i,
            cantidad + max_cantidad * 0.02,
            formato_cantidad(cantidad),
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(
        tabla["anio_vencimiento"].astype(str),
        color=COLOR_MUTED,
    )

    ax.set_ylabel("Cantidad de registros", color=COLOR_TEXTO)

    ax.set_title(
        "Concentración de vencidos sin recepción por año",
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
    semaforo_desc = resumen.get("semaforo_descriptivo", describir_nivel_alerta(semaforo))

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
            <div class="alert-main">{semaforo_desc}</div>
            <div class="alert-text">{resumen.get("mensaje", "")}</div>
            <div class="alert-text" style="margin-top:8px;"><b>Acción sugerida:</b> {resumen.get("accion", "")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_tabla_alertas(
    df: pd.DataFrame,
    titulo: str,
    descripcion: str,
    limite: int = 300,
):
    st.markdown(f"### {titulo}")
    st.caption(descripcion)

    tabla = crear_tabla_prioridad(df)

    if tabla.empty:
        st.success("No hay registros para esta categoría con los filtros actuales.")
        return

    total_registros = len(tabla)
    registros_mostrados = min(limite, total_registros)

    mensaje_vista_previa(
        titulo=titulo,
        total_registros=total_registros,
        registros_mostrados=registros_mostrados,
        limite=limite,
    )

    st.dataframe(
        tabla.head(registros_mostrados),
        use_container_width=True,
        hide_index=True,
    )


def mostrar_vencidos_por_anio(df_vencidos: pd.DataFrame):
    st.markdown("### Vencidos sin recepción por año")
    st.caption(
        "Los registros vencidos sin recepción se separan según el año de la fecha de vencimiento TAT."
    )

    if df_vencidos.empty:
        st.success("No hay registros vencidos sin recepción con los filtros actuales.")
        return

    df_temp = df_vencidos.copy()

    df_temp["fecha_vencimiento_tat"] = pd.to_datetime(
        df_temp["fecha_vencimiento_tat"],
        errors="coerce",
    )

    df_temp["anio_vencimiento"] = df_temp["fecha_vencimiento_tat"].dt.year

    df_temp["dias_vencido"] = (
        pd.Timestamp.today().normalize()
        - df_temp["fecha_vencimiento_tat"]
    ).dt.days

    df_temp["dias_vencido"] = pd.to_numeric(
        df_temp["dias_vencido"],
        errors="coerce",
    )

    anios_validos = (
        df_temp["anio_vencimiento"]
        .dropna()
        .astype(int)
        .sort_values(ascending=False)
        .unique()
        .tolist()
    )

    tiene_sin_anio = df_temp["anio_vencimiento"].isna().any()

    total_vencidos = len(df_temp)

    st.info(
        f"Total vencidos sin recepción: **{formato_cantidad(total_vencidos)} registros**."
    )

    for anio in anios_validos:
        df_anio = df_temp[
            df_temp["anio_vencimiento"].eq(anio)
        ].copy()

        dias_validos = df_anio["dias_vencido"].dropna()

        dias_min = int(dias_validos.min()) if not dias_validos.empty else 0
        dias_max = int(dias_validos.max()) if not dias_validos.empty else 0

        with st.expander(
            f"Año {anio} · {formato_cantidad(len(df_anio))} registros",
            expanded=True,
        ):
            m1, m2, m3 = st.columns(3)

            m1.metric("Vencidos", formato_cantidad(len(df_anio)))
            m2.metric("Mínimo días vencido", formato_cantidad(dias_min))
            m3.metric("Máximo días vencido", formato_cantidad(dias_max))

            mostrar_tabla_alertas(
                df_anio,
                f"Vencidos sin recepción {anio}",
                f"Registros vencidos sin recepción con fecha de vencimiento TAT durante {anio}.",
                limite=300,
            )

    if tiene_sin_anio:
        df_sin_anio = df_temp[
            df_temp["anio_vencimiento"].isna()
        ].copy()

        with st.expander(
            f"Sin año de vencimiento · {formato_cantidad(len(df_sin_anio))} registros",
            expanded=True,
        ):
            mostrar_tabla_alertas(
                df_sin_anio,
                "Vencidos sin recepción sin año calculable",
                "Registros vencidos sin recepción sin fecha de vencimiento TAT válida.",
                limite=300,
            )


def mostrar_proximos_por_rango(df_proximos: pd.DataFrame):
    st.markdown("### Vencen en 0 a 30 días sin recepción")
    st.caption(
        "Los próximos vencimientos se separan por rangos de días restantes para priorizar la gestión."
    )

    if df_proximos.empty:
        st.success("No hay registros próximos a vencer con los filtros actuales.")
        return

    df_temp = df_proximos.copy()

    df_temp["dias_restantes_int"] = pd.to_numeric(
        df_temp["dias_restantes_int"],
        errors="coerce",
    )

    rangos = [
        {
            "nombre": "Vence hoy",
            "descripcion": "Registros que vencen hoy y aún no tienen recepción.",
            "mask": df_temp["dias_restantes_int"].eq(0),
        },
        {
            "nombre": "Vencen en 1 a 2 días",
            "descripcion": "Registros que vencen entre 1 y 2 días.",
            "mask": df_temp["dias_restantes_int"].between(1, 2, inclusive="both"),
        },
        {
            "nombre": "Vencen en 3 a 7 días",
            "descripcion": "Registros que vencen entre 3 y 7 días.",
            "mask": df_temp["dias_restantes_int"].between(3, 7, inclusive="both"),
        },
        {
            "nombre": "Vencen en 8 a 15 días",
            "descripcion": "Registros que vencen entre 8 y 15 días.",
            "mask": df_temp["dias_restantes_int"].between(8, 15, inclusive="both"),
        },
        {
            "nombre": "Vencen en 16 a 30 días",
            "descripcion": "Registros que vencen entre 16 y 30 días.",
            "mask": df_temp["dias_restantes_int"].between(16, 30, inclusive="both"),
        },
    ]

    total_proximos = len(df_temp)

    st.info(
        f"Total próximos 0-30 días sin recepción: **{formato_cantidad(total_proximos)} registros**."
    )

    for item in rangos:
        df_rango = df_temp[item["mask"]].copy()

        if df_rango.empty:
            continue

        dias_validos = df_rango["dias_restantes_int"].dropna()

        dias_min = int(dias_validos.min()) if not dias_validos.empty else 0
        dias_max = int(dias_validos.max()) if not dias_validos.empty else 0

        with st.expander(
            f"{item['nombre']} · {formato_cantidad(len(df_rango))} registros",
            expanded=True,
        ):
            r1, r2, r3 = st.columns(3)

            r1.metric("Registros", formato_cantidad(len(df_rango)))
            r2.metric("Mínimo días restantes", formato_cantidad(dias_min))
            r3.metric("Máximo días restantes", formato_cantidad(dias_max))

            mostrar_tabla_alertas(
                df_rango,
                item["nombre"],
                item["descripcion"],
                limite=300,
            )


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
st.caption("Filtros enfocados solo en gestión de alertas.")

fechas_vencimiento = df_panel["fecha_vencimiento_tat"].dropna()

fecha_venc_min = fechas_vencimiento.min().date() if not fechas_vencimiento.empty else None
fecha_venc_max = fechas_vencimiento.max().date() if not fechas_vencimiento.empty else None

opciones_nivel = [
    describir_nivel_alerta(x)
    for x in NIVELES_ALERTA_ORDEN
    if x in df_panel["nivel_alerta"].astype(str).unique()
]

opciones_clasificacion = [
    x for x in [
        "Vencido",
        "Vence hoy",
        "1 día",
        "2 días",
        "7 días",
        "+7 días",
        "Sin datos",
        "Recepcionado",
    ]
    if x in df_panel["clasificacion_vencimiento"].astype(str).unique()
]

clasificaciones_default = [
    x for x in opciones_clasificacion
    if x not in ["Sin datos", "Recepcionado"]
]

opciones_estado_recepcion = opciones_columna(df_panel, COL_ESTADO_RECEPCION_ALERTA)
opciones_centros = opciones_columna(df_panel, COL_CENTRO)
opciones_grupos_compras = opciones_columna(df_panel, COL_GRUPO_COMPRAS)
opciones_sistemas = opciones_columna(df_panel, COL_SISTEMA)
opciones_tipo_oc = opciones_columna(df_panel, COL_TIPO_OC)

centros_default = [
    centro
    for centro in opciones_centros
    if str(centro).strip().upper() == "E002"
]

with st.form("form_filtros_alertas"):
    f1, f2, f3, f4 = st.columns(4)

    with f1:
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

    with f2:
        niveles = st.multiselect(
            "Tipo de alerta",
            options=opciones_nivel,
            default=opciones_nivel,
            key="alertas_niveles",
        )

    with f3:
        clasificaciones = st.multiselect(
            "Clasificación vencimiento",
            options=opciones_clasificacion,
            default=clasificaciones_default,
            key="alertas_clasificaciones",
            help="Por defecto se excluyen 'Sin datos' y 'Recepcionado'.",
        )

    with f4:
        estados_recepcion = st.multiselect(
            "Estado recepción",
            options=opciones_estado_recepcion,
            default=opciones_estado_recepcion,
            key="alertas_estados_recepcion",
        )

    f5, f6, f7, f8 = st.columns(4)

    with f5:
        centros = st.multiselect(
            "Centro",
            options=opciones_centros,
            default=centros_default,
            key="alertas_centros",
            help="Por defecto se selecciona E002 si existe.",
        )

    with f6:
        grupos_compras = st.multiselect(
            "Grupo compras",
            options=opciones_grupos_compras,
            default=[],
            key="alertas_grupos_compras",
            help="Si no seleccionas grupo, se consideran todos.",
        )

    with f7:
        sistemas = st.multiselect(
            "Sistema",
            options=opciones_sistemas,
            default=[],
            key="alertas_sistemas",
            help="Si no seleccionas sistema, se consideran todos.",
        )

    with f8:
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
    ]

    for clave in claves:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


filtros = {
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
        df_filtrado, resumen_filtros_df = aplicar_filtros_alertas(
            df_base=df_panel,
            filtros=filtros,
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
    formato_cantidad(filtrados),
    f"{resumen_ejecutivo['pct_filtrado']:.1f}% del total" if total_archivo else "",
)

c2.metric("Vencidos sin recepción", formato_cantidad(vencidos_total))
c3.metric("Próximos 0-30 días", formato_cantidad(proximos_total))
c4.metric("Sin fecha calculable", formato_cantidad(sin_fecha_total))
c5.metric("Recepcionados", formato_cantidad(recepcionados_total))


# ============================================================
# RESUMEN EJECUTIVO
# ============================================================

mostrar_card_estado(resumen_ejecutivo)


# ============================================================
# DESGLOSE VISUAL
# ============================================================

st.markdown("### Desglose visual de alertas")
st.caption(
    "El primer gráfico muestra la distribución porcentual. "
    "El segundo gráfico muestra valores absolutos con mayor detalle en los rangos mayores a 7 días."
)

col_g1, col_g2 = st.columns(2)

with col_g1:
    grafico_donut_alertas_porcentual(df_filtrado)

with col_g2:
    grafico_alertas_valores_absolutos(df_filtrado)

desglose_alertas = crear_desglose_alertas(df_filtrado)

with st.expander("Ver tabla de desglose de alertas", expanded=False):
    if desglose_alertas.empty:
        st.info("No hay desglose disponible.")
    else:
        st.dataframe(
            desglose_alertas,
            use_container_width=True,
            hide_index=True,
        )


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

grafico_vencidos_por_anio(df_vencidos)

mostrar_vencidos_por_anio(df_vencidos)

mostrar_proximos_por_rango(df_proximos)

with st.expander("Datos incompletos para calcular vencimiento", expanded=True):
    mostrar_tabla_alertas(
        df_sin_fecha,
        "Datos incompletos para calcular vencimiento",
        "Registros sin fecha de vencimiento calculable. Requieren corrección de datos base.",
    )
