import io
import base64
from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

# =========================================================
# Configuración general
# =========================================================
# Si esta app vive dentro de st.navigation(), deja st.set_page_config()
# solamente en el archivo principal del portal.

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
# Columnas esperadas
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

ETAPAS = [
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
    "score_riesgo",
    "estado_global",
    "etapa_actual",
    "responsable_sugerido",
    "accion_sugerida",
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
# Estilos visuales
# =========================================================
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1550px;
            margin-left: auto;
            margin-right: auto;
        }

        h1 {
            font-size: 1.9rem !important;
            margin-bottom: 0.1rem !important;
        }

        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #eef2f7;
            border-radius: 14px;
            padding: 12px 14px;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.035);
        }

        .hero {
            text-align: center;
            margin-bottom: 22px;
        }

        .hero-title {
            font-size: 42px;
            font-weight: 850;
            color: #1F2937;
            line-height: 1.12;
        }

        .hero-subtitle {
            font-size: 14px;
            color: #6B7280;
            margin-top: 10px;
        }

        .alert-box {
            border-radius: 18px;
            padding: 16px 18px;
            border: 1px solid #e5e7eb;
            background: #ffffff;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.04);
            margin: 0.8rem 0;
        }

        .alert-red {
            background: #fef2f2;
            border-color: #fecaca;
        }

        .alert-orange {
            background: #fff7ed;
            border-color: #fed7aa;
        }

        .alert-yellow {
            background: #fefce8;
            border-color: #fde68a;
        }

        .alert-green {
            background: #f0fdf4;
            border-color: #bbf7d0;
        }

        .alert-gray {
            background: #f8fafc;
            border-color: #e2e8f0;
        }

        .alert-title {
            color: #0f172a;
            font-size: 1.02rem;
            font-weight: 900;
            margin-bottom: 8px;
        }

        .alert-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(120px, 1fr));
            gap: 10px;
        }

        .alert-label {
            color: #64748b;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .alert-value {
            color: #0f172a;
            font-size: 0.98rem;
            font-weight: 850;
            overflow-wrap: anywhere;
        }

        .action-box {
            margin-top: 12px;
            padding: 12px 14px;
            border-radius: 14px;
            background: rgba(255,255,255,0.65);
            border: 1px solid rgba(148, 163, 184, 0.35);
            color: #334155;
            font-size: 0.92rem;
            line-height: 1.35;
        }

        .pill {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 9px;
            font-size: 0.76rem;
            font-weight: 850;
            border: 1px solid transparent;
            white-space: nowrap;
        }

        .pill-red { background:#fee2e2; color:#991b1b; border-color:#fecaca; }
        .pill-orange { background:#ffedd5; color:#9a3412; border-color:#fed7aa; }
        .pill-yellow { background:#fef9c3; color:#854d0e; border-color:#fde68a; }
        .pill-green { background:#dcfce7; color:#166534; border-color:#bbf7d0; }
        .pill-gray { background:#f1f5f9; color:#475569; border-color:#e2e8f0; }

        @media (max-width: 1000px) {
            .alert-grid { grid-template-columns: repeat(2, minmax(120px, 1fr)); }
            .hero-title { font-size: 32px; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Utilidades
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
    logo_base64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

    st.markdown(
        f"""
        <div style="width:100%; display:flex; justify-content:center; align-items:center; min-height:84px; margin:0 0 16px 0;">
            <img src="data:{mime};base64,{logo_base64}" style="width:{ancho}px; max-width:80%; height:auto; display:block; object-fit:contain;" alt="Logo">
        </div>
        """,
        unsafe_allow_html=True,
    )


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
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
        resultado.loc[mask_texto] = pd.to_datetime(serie.loc[mask_texto], errors="coerce", dayfirst=True)

    return resultado


def convertir_fechas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in FECHAS_CANDIDATAS:
        if col in df.columns:
            convertido = convertir_columna_fecha(df[col])
            if convertido.notna().any():
                df[col] = convertido
    return df


def valor_numerico(valor: Any) -> float:
    try:
        return float(pd.to_numeric(pd.Series([valor]), errors="coerce").iloc[0])
    except Exception:
        return np.nan


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
    return texto[:-2] if texto.endswith(".0") else texto


def formato_valor(valor: Any) -> str:
    if pd.isna(valor):
        return "-"
    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%d-%m-%Y")
    if isinstance(valor, float):
        if np.isfinite(valor) and valor.is_integer():
            return f"{int(valor):,}".replace(",", ".")
        return f"{valor:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if isinstance(valor, int):
        return f"{valor:,}".replace(",", ".")
    return str(valor)


def texto_dias(valor: Any) -> str:
    num = valor_numerico(valor)
    if pd.isna(num):
        return "Sin dato"
    return f"{int(round(num)):,} días".replace(",", ".")


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


def primera_columna_existente(df: pd.DataFrame, columnas: list[str]) -> str | None:
    for col in columnas:
        if col in df.columns:
            return col
    return None


def fecha_inicio_tat(row: pd.Series):
    for col in ["fecha_solicitud_final", "Fecha de solicitud - ME5A"]:
        valor = row.get(col, pd.NaT)
        if pd.notna(valor):
            return pd.to_datetime(valor, errors="coerce")
    return pd.NaT


def fecha_fin_real_o_referencia(row: pd.Series, hoy: pd.Timestamp):
    for col in ["fecha_recepcion_final", "Fecha recepción mercancía - NME80FN"]:
        valor = row.get(col, pd.NaT)
        if pd.notna(valor):
            return pd.to_datetime(valor, errors="coerce"), True
    return hoy, False


def detectar_etapa_actual(row: pd.Series) -> tuple[str, str]:
    for etapa in ETAPAS:
        fecha_fin = row.get(etapa["fecha_fin"], pd.NaT)
        if pd.isna(fecha_fin):
            return etapa["nombre"], etapa["responsable"]
    return "Recepcionado", "Cerrado"


def detectar_etapa_critica(row: pd.Series) -> tuple[str, str, float, float, float]:
    peor_etapa = "Sin etapa crítica"
    responsable = "Sin responsable"
    peor_brecha = -999999.0
    peor_dias = np.nan
    peor_umbral = np.nan

    for etapa in ETAPAS:
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


def accion_sugerida(nivel: str, etapa_actual: str, responsable: str, dias_restantes: float, brecha: float) -> str:
    if nivel == "Crítica":
        return f"Escalar hoy con {responsable}. Bloquear causa raíz en etapa {etapa_actual}, confirmar fecha real comprometida y definir plan de recuperación."
    if nivel == "Alta":
        return f"Contactar a {responsable}, validar hito pendiente y comprometer acción antes de que el pedido supere el umbral."
    if nivel == "Media":
        return f"Monitorear de cerca. Quedan {int(round(dias_restantes))} días contra el umbral; revisar si hay riesgo por proveedor, logística o aprobación."
    if nivel == "Normal":
        return "Sin acción urgente. Mantener seguimiento normal según calendario de compras."
    return "Revisar datos maestros y fechas: no hay información suficiente para calcular alerta confiable."


@st.cache_data(show_spinner=False)
def construir_alertas(df: pd.DataFrame, dias_alerta_temprana: int = 7) -> pd.DataFrame:
    df = limpiar_columnas(df)
    df = convertir_fechas(df)
    hoy = pd.Timestamp.today().normalize()
    salida = df.copy()

    niveles = []
    estados = []
    scores = []
    etapas_actuales = []
    responsables = []
    acciones = []
    dias_transcurridos = []
    dias_restantes = []
    brechas = []

    for _, row in salida.iterrows():
        inicio = fecha_inicio_tat(row)
        fin_ref, cerrado = fecha_fin_real_o_referencia(row, hoy)
        umbral = obtener_umbral_tat(row)
        etapa_actual, responsable_actual = detectar_etapa_actual(row)
        etapa_critica, responsable_critico, brecha_etapa, _, _ = detectar_etapa_critica(row)

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

        accion = accion_sugerida(nivel, etapa_actual, responsable, restante, brecha)

        niveles.append(nivel)
        estados.append(estado)
        scores.append(round(float(score), 1))
        etapas_actuales.append(etapa_actual)
        responsables.append(responsable)
        acciones.append(accion)
        dias_transcurridos.append(transcurrido)
        dias_restantes.append(restante)
        brechas.append(brecha)

    salida["nivel_alerta"] = niveles
    salida["score_riesgo"] = scores
    salida["estado_global"] = estados
    salida["etapa_actual"] = etapas_actuales
    salida["responsable_sugerido"] = responsables
    salida["accion_sugerida"] = acciones
    salida["dias_transcurridos_tat"] = dias_transcurridos
    salida["dias_restantes_tat"] = dias_restantes
    salida["brecha_tat"] = brechas

    orden = {"Crítica": 1, "Alta": 2, "Media": 3, "Normal": 4, "Sin datos": 5}
    salida["_orden_alerta"] = salida["nivel_alerta"].map(orden).fillna(9)
    salida = salida.sort_values(["_orden_alerta", "score_riesgo", "brecha_tat"], ascending=[True, False, False])

    return salida.drop(columns=["_orden_alerta"])


@st.cache_data(show_spinner=False)
def dataframe_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


@st.cache_data(show_spinner=False)
def dataframe_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Alertas")
    return output.getvalue()


def pill_alerta(nivel: str) -> str:
    mapa = {
        "Crítica": "red",
        "Alta": "orange",
        "Media": "yellow",
        "Normal": "green",
        "Sin datos": "gray",
    }
    color = mapa.get(nivel, "gray")
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
    titulo = f"SolPed {formato_id(row.get(COL_SOLPED, np.nan))} · OC {formato_id(oc)} · Pos {formato_id(row.get(COL_POS_SOLPED, np.nan))}"
    return dedent(
        f"""
        <div class="alert-box {clase_alerta(row.get('nivel_alerta', 'Sin datos'))}">
            <div class="alert-title">{escape(titulo)} {pill_alerta(row.get('nivel_alerta', 'Sin datos'))}</div>
            <div class="alert-grid">
                <div><div class="alert-label">Estado</div><div class="alert-value">{escape(formato_valor(row.get('estado_global', np.nan)))}</div></div>
                <div><div class="alert-label">Score riesgo</div><div class="alert-value">{escape(formato_valor(row.get('score_riesgo', np.nan)))}</div></div>
                <div><div class="alert-label">Etapa actual</div><div class="alert-value">{escape(formato_valor(row.get('etapa_actual', np.nan)))}</div></div>
                <div><div class="alert-label">Restante TAT</div><div class="alert-value">{escape(texto_dias(row.get('dias_restantes_tat', np.nan)))}</div></div>
                <div><div class="alert-label">Monto</div><div class="alert-value">{escape(formato_valor(row.get(COL_MONTO, np.nan)))}</div></div>
                <div><div class="alert-label">Centro</div><div class="alert-value">{escape(formato_valor(row.get(COL_CENTRO, np.nan)))}</div></div>
                <div><div class="alert-label">Grupo compras</div><div class="alert-value">{escape(formato_valor(row.get(COL_GRUPO_COMPRAS, np.nan)))}</div></div>
                <div><div class="alert-label">Responsable sugerido</div><div class="alert-value">{escape(formato_valor(row.get('responsable_sugerido', np.nan)))}</div></div>
                <div><div class="alert-label">Material</div><div class="alert-value">{escape(formato_valor(row.get(COL_MATERIAL, np.nan)))}</div></div>
                <div><div class="alert-label">Descripción</div><div class="alert-value">{escape(str(row.get(COL_TEXTO, '-'))[:70])}</div></div>
            </div>
            <div class="action-box"><strong>Acción sugerida:</strong> {escape(formato_valor(row.get('accion_sugerida', np.nan)))}</div>
        </div>
        """
    ).strip()


def aplicar_estilo_tabla(df_tabla: pd.DataFrame):
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


def opciones_columna(df: pd.DataFrame, col: str) -> list[str]:
    if col not in df.columns:
        return []
    return df[col].dropna().astype(str).sort_values().unique().tolist()[:700]


def filtrar_por_texto(df: pd.DataFrame, col: str, texto: str) -> pd.Series:
    if col not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)
    return df[col].astype(str).str.contains(str(texto).strip(), case=False, na=False, regex=False)


def filtrar_por_id(df: pd.DataFrame, col: str, texto: str) -> pd.Series:
    if col not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)
    tokens = str(texto).replace("\n", ",").replace(";", ",").replace(" ", ",").split(",")
    tokens = [t.strip().replace(".0", "") for t in tokens if t.strip()]
    serie = df[col].astype(str).str.replace(".0", "", regex=False)
    mask = pd.Series(False, index=df.index)
    for token in tokens:
        mask |= serie.str.contains(token, case=False, na=False, regex=False)
    return mask


# =========================================================
# Interfaz
# =========================================================
mostrar_logo()

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">Alertas de pedidos con atraso</div>
        <div class="hero-subtitle">Vista global · Riesgo anticipado · Responsable sugerido · Acción recomendada</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Configuración")
    dias_alerta_temprana = st.slider("Ventana de alerta temprana", min_value=1, max_value=30, value=7, step=1)
    limite_vista = st.number_input("Filas en tabla", min_value=25, max_value=5000, value=300, step=25)
    mostrar_todas_columnas = st.checkbox("Mostrar todas las columnas", value=False)

st.markdown("### Archivo")

if "df_tat" in st.session_state:
    df_base = st.session_state["df_tat"].copy()
    nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")
    st.success(f"Archivo activo desde sesión: {nombre_archivo}")
else:
    archivo = st.file_uploader("Carga un CSV, Excel o Parquet para analizar alertas", type=["csv", "xlsx", "xls", "parquet"])
    if archivo is None:
        st.info("También puedes alimentar esta app con st.session_state['df_tat'] desde el módulo de carga principal.")
        st.stop()

    if archivo.name.lower().endswith(".csv"):
        df_base = pd.read_csv(archivo)
    elif archivo.name.lower().endswith(".parquet"):
        df_base = pd.read_parquet(archivo)
    else:
        df_base = pd.read_excel(archivo)
    st.success(f"Archivo cargado: {archivo.name}")

try:
    df_alertas = construir_alertas(df_base, dias_alerta_temprana=dias_alerta_temprana)
except Exception as e:
    st.error("No se pudo construir la matriz de alertas.")
    st.exception(e)
    st.stop()

# =========================================================
# Filtros
# =========================================================
st.markdown("### Filtros")
f1, f2, f3, f4 = st.columns(4)

with f1:
    niveles_sel = st.multiselect(
        "Nivel de alerta",
        ["Crítica", "Alta", "Media", "Normal", "Sin datos"],
        default=["Crítica", "Alta", "Media"],
    )
    txt_solped = st.text_input("SolPed", placeholder="Ej: 1001973319")

with f2:
    centros_sel = st.multiselect("Centro", opciones_columna(df_alertas, COL_CENTRO))
    txt_oc = st.text_input("Orden de compra", placeholder="Ej: 4502321875")

with f3:
    grupos_sel = st.multiselect("Grupo de compras", opciones_columna(df_alertas, COL_GRUPO_COMPRAS))
    etapas_sel = st.multiselect("Etapa actual", opciones_columna(df_alertas, "etapa_actual"))

with f4:
    responsables_sel = st.multiselect("Responsable sugerido", opciones_columna(df_alertas, "responsable_sugerido"))
    txt_material = st.text_input("Material / descripción", placeholder="Ej: bloqueador")

mask = pd.Series(True, index=df_alertas.index)
if niveles_sel:
    mask &= df_alertas["nivel_alerta"].isin(niveles_sel)
if centros_sel and COL_CENTRO in df_alertas.columns:
    mask &= df_alertas[COL_CENTRO].astype(str).isin(centros_sel)
if grupos_sel and COL_GRUPO_COMPRAS in df_alertas.columns:
    mask &= df_alertas[COL_GRUPO_COMPRAS].astype(str).isin(grupos_sel)
if etapas_sel:
    mask &= df_alertas["etapa_actual"].astype(str).isin(etapas_sel)
if responsables_sel:
    mask &= df_alertas["responsable_sugerido"].astype(str).isin(responsables_sel)

mask &= filtrar_por_id(df_alertas, COL_SOLPED, txt_solped)
mask &= (filtrar_por_id(df_alertas, COL_OC_ME5A, txt_oc) | filtrar_por_id(df_alertas, COL_OC_NME, txt_oc))
mask &= (filtrar_por_id(df_alertas, COL_MATERIAL, txt_material) | filtrar_por_texto(df_alertas, COL_TEXTO, txt_material))

df_filtrado = df_alertas.loc[mask].copy()

# =========================================================
# KPIs
# =========================================================
total = len(df_filtrado)
criticas = int((df_filtrado["nivel_alerta"] == "Crítica").sum()) if total else 0
altas = int((df_filtrado["nivel_alerta"] == "Alta").sum()) if total else 0
media_score = df_filtrado["score_riesgo"].mean() if total else 0
monto_riesgo = df_filtrado.loc[df_filtrado["nivel_alerta"].isin(["Crítica", "Alta"]), COL_MONTO].pipe(pd.to_numeric, errors="coerce").sum() if COL_MONTO in df_filtrado.columns else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Pedidos filtrados", f"{total:,}".replace(",", "."))
k2.metric("Críticos", f"{criticas:,}".replace(",", "."))
k3.metric("Alta prioridad", f"{altas:,}".replace(",", "."))
k4.metric("Score promedio", f"{media_score:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
k5.metric("Monto crítico/alto", f"{monto_riesgo:,.0f}".replace(",", "."))

# =========================================================
# Vista ejecutiva
# =========================================================
st.markdown("### Alertas principales")

if df_filtrado.empty:
    st.warning("No hay pedidos con los filtros aplicados.")
else:
    top_alertas = df_filtrado.head(10)
    for _, row in top_alertas.iterrows():
        st.markdown(html_alerta(row), unsafe_allow_html=True)

# =========================================================
# Distribuciones
# =========================================================
with st.expander("Distribuciones y focos", expanded=True):
    d1, d2, d3 = st.columns(3)
    with d1:
        st.markdown("**Alertas por nivel**")
        st.dataframe(df_filtrado["nivel_alerta"].value_counts(dropna=False).rename_axis("Nivel").reset_index(name="Cantidad"), use_container_width=True, hide_index=True)
    with d2:
        st.markdown("**Alertas por etapa actual**")
        st.dataframe(df_filtrado["etapa_actual"].value_counts(dropna=False).rename_axis("Etapa").reset_index(name="Cantidad"), use_container_width=True, hide_index=True)
    with d3:
        st.markdown("**Alertas por responsable**")
        st.dataframe(df_filtrado["responsable_sugerido"].value_counts(dropna=False).rename_axis("Responsable").reset_index(name="Cantidad"), use_container_width=True, hide_index=True)

# =========================================================
# Tabla
# =========================================================
st.markdown("### Matriz de alertas")

columnas_default = df_filtrado.columns.tolist() if mostrar_todas_columnas else [c for c in COLUMNAS_ALERTA if c in df_filtrado.columns]
columnas_visibles = st.multiselect("Columnas visibles", options=df_filtrado.columns.tolist(), default=columnas_default)

if columnas_visibles:
    tabla = df_filtrado[columnas_visibles].head(int(limite_vista)).copy()
    st.dataframe(aplicar_estilo_tabla(tabla), use_container_width=True, hide_index=True)
else:
    st.info("Selecciona al menos una columna.")

# =========================================================
# Descargas
# =========================================================
st.markdown("### Descarga")

x1, x2 = st.columns(2)
with x1:
    st.download_button(
        "Descargar CSV de alertas",
        data=dataframe_a_csv(df_filtrado),
        file_name="alertas_pedidos_atrasos.csv",
        mime="text/csv",
        use_container_width=True,
    )
with x2:
    st.download_button(
        "Descargar Excel de alertas",
        data=dataframe_a_excel(df_filtrado),
        file_name="alertas_pedidos_atrasos.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
