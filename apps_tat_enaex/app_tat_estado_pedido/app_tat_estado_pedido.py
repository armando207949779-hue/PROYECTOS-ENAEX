import io
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# =========================================================
# Configuración general
# =========================================================

st.set_page_config(
    page_title="Estado visual de pedidos",
    page_icon="📦",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================================================
# Columnas esperadas / compatibles
# =========================================================

COL_FECHA_SOLICITUD_FINAL = "fecha_solicitud_final"
COL_FECHA_LIBERACION_FINAL = "fecha_liberacion_final"
COL_FECHA_PEDIDO_FINAL = "fecha_pedido_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"

COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - NME80FN"
COL_SOLPED = "Solicitud de pedido - ME5A"
COL_POS_SOLPED = "Posición solicitud de pedido - ME5A"
COL_POS_PEDIDO = "Posición de pedido - ME5A"
COL_POS_NME = "Posición - NME80FN"
COL_MATERIAL = "Material - ME5A"
COL_TEXTO_BREVE = "Texto breve - ME5A"
COL_CENTRO = "Centro - ME5A"
COL_GRUPO_COMPRAS = "Grupo de compras"
COL_ESTADO_MATCH = "Estado del match"
COL_INCUMPLIMIENTO = "incumplimiento"
COL_RANGO_INCUMPLIMIENTO = "rango_incumplimiento"
COL_DIAS_INCUMPLIMIENTO_MAX = "dias_incumplimiento_max"
COL_DX_TAT = "dx_tat"
COL_DX_LOGISTICA = "dx_logistica"
COL_DX_PROVEEDOR = "dx_proveedor"
COL_TIPO_OC = "tipo_oc"
COL_ORIGEN_OC = "origen_oc"
COL_SISTEMA_OC = "sistema_oc"

COLUMNAS_FECHA = [
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
    "Fecha de entrada - NME80FN",
    "Fecha de documento - NME80FN",
    "Fecha contabilización - NME80FN",
    "Fecha facturación proveedor - NME80FN",
    "Fecha recepción mercancía - NME80FN",
    "fecha_inicio_proveedor",
]

ETAPAS_BASE = [
    {
        "key": "solicitud",
        "label": "Solicitud",
        "fecha": COL_FECHA_SOLICITUD_FINAL,
        "dx": None,
        "performance": None,
        "incumplimiento": None,
    },
    {
        "key": "liberacion",
        "label": "Liberación SolPed",
        "fecha": COL_FECHA_LIBERACION_FINAL,
        "dx": "dx_lib_solped",
        "performance": "performance_lib_solped",
        "incumplimiento": "dias_incumplimiento_lib_solped",
    },
    {
        "key": "pedido",
        "label": "Pedido OC",
        "fecha": COL_FECHA_PEDIDO_FINAL,
        "dx": "dx_comprador_1",
        "performance": "performance_comprador_1",
        "incumplimiento": "dias_incumplimiento_comprador_1",
    },
    {
        "key": "facturacion",
        "label": "Facturación proveedor",
        "fecha": COL_FECHA_FACTURACION_FINAL,
        "dx": None,
        "performance": None,
        "incumplimiento": None,
    },
    {
        "key": "recepcion",
        "label": "Recepción mercancía",
        "fecha": COL_FECHA_RECEPCION_FINAL,
        "dx": "dx_logistica",
        "performance": "performance_logistica",
        "incumplimiento": "dias_incumplimiento_logistica",
    },
]


# =========================================================
# Utilidades de UI
# =========================================================

def mostrar_logo(ancho: int = 170) -> None:
    if not LOGO_PATH.exists():
        return

    logo_svg = LOGO_PATH.read_text(encoding="utf-8")
    logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")

    st.markdown(
        f"""
        <div style="width: 100%; text-align: center; margin: .25rem 0 1rem 0;">
            <img src="data:image/svg+xml;base64,{logo_base64}" width="{ancho}">
        </div>
        """,
        unsafe_allow_html=True,
    )


def inyectar_css() -> None:
    st.markdown(
        """
        <style>
            .status-card {
                border: 1px solid rgba(49, 51, 63, 0.18);
                border-radius: 18px;
                padding: 18px 18px 10px 18px;
                margin-bottom: 18px;
                background: rgba(255, 255, 255, 0.72);
                box-shadow: 0 1px 8px rgba(0,0,0,0.04);
            }
            .pedido-title {
                font-size: 1.05rem;
                font-weight: 700;
                margin-bottom: .15rem;
            }
            .pedido-subtitle {
                color: #6b7280;
                font-size: .88rem;
                margin-bottom: .8rem;
            }
            .timeline-wrap {
                display: flex;
                align-items: flex-start;
                width: 100%;
                overflow-x: auto;
                padding: 12px 2px 6px 2px;
            }
            .step-wrap {
                display: flex;
                align-items: center;
                min-width: 170px;
            }
            .step-box {
                min-width: 142px;
                text-align: center;
            }
            .dot {
                width: 28px;
                height: 28px;
                border-radius: 999px;
                margin: auto;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 15px;
                font-weight: 800;
            }
            .dot-ok { background: #16a34a; }
            .dot-bad { background: #dc2626; }
            .dot-pending { background: #9ca3af; }
            .dot-info { background: #2563eb; }
            .line {
                height: 4px;
                min-width: 45px;
                flex: 1;
                border-radius: 999px;
                margin: 13px 8px 0 8px;
                background: #d1d5db;
            }
            .line-ok { background: #16a34a; }
            .line-bad { background: #dc2626; }
            .step-label {
                margin-top: 7px;
                font-size: .82rem;
                font-weight: 700;
                line-height: 1.15rem;
            }
            .step-date {
                font-size: .76rem;
                color: #4b5563;
                margin-top: 2px;
            }
            .step-extra {
                font-size: .72rem;
                color: #6b7280;
                margin-top: 2px;
            }
            .badge {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 999px;
                font-size: .75rem;
                font-weight: 700;
                margin: 2px 4px 2px 0;
            }
            .badge-ok { background: #dcfce7; color: #166534; }
            .badge-bad { background: #fee2e2; color: #991b1b; }
            .badge-neutral { background: #e5e7eb; color: #374151; }
            .badge-warn { background: #fef3c7; color: #92400e; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Lectura y preparación
# =========================================================

def obtener_separador(separador_csv: str) -> Optional[str]:
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;)":
        return ";"
    if separador_csv == "Coma (, )" or separador_csv == "Coma (, )".strip():
        return ","
    if separador_csv == "Coma (, )" or separador_csv == "Coma (, )":
        return ","
    if separador_csv == "Coma (, )":
        return ","
    if separador_csv == "Coma (,)":
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner=False)
def leer_archivo_cache(bytes_archivo: bytes, nombre_archivo: str, separador_csv: str) -> pd.DataFrame:
    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(buffer)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)
        try:
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="utf-8-sig", on_bad_lines="skip")
        except Exception:
            buffer.seek(0)
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="latin1", on_bad_lines="skip")

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx, .xls o .csv.")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
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

    mask_no_num = ~mask_num
    if mask_no_num.any():
        resultado.loc[mask_no_num] = pd.to_datetime(serie.loc[mask_no_num], errors="coerce", dayfirst=True)

    return resultado


def convertir_fechas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in COLUMNAS_FECHA:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])
    return df


def coalesce_columnas(df: pd.DataFrame, destino: str, alternativas: List[str]) -> pd.DataFrame:
    df = df.copy()
    if destino in df.columns:
        return df

    serie = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    for col in alternativas:
        if col in df.columns:
            serie = serie.fillna(df[col])
    df[destino] = serie
    return df


def extraer_tipo_oc(valor: Any) -> Any:
    if pd.isna(valor):
        return pd.NA
    texto = str(valor).strip()
    try:
        texto = str(int(float(texto)))
    except Exception:
        texto = texto.replace(".0", "")
    return texto[:2] if len(texto) >= 2 else pd.NA


def bool_array(condicion) -> np.ndarray:
    return pd.Series(condicion).fillna(False).to_numpy(dtype=bool)


def preparar_dataframe(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)
    df = convertir_fechas(df)

    # Permite usar archivos ya procesados o archivos base con nombres de origen.
    df = coalesce_columnas(df, COL_FECHA_SOLICITUD_FINAL, ["Fecha de solicitud - ME5A", "Fecha solicitud de compra - ARIBA"])
    df = coalesce_columnas(df, COL_FECHA_LIBERACION_FINAL, ["Fecha de liberación - ME5A", "Fecha de liberación", "Fecha de aprobación - ARIBA"])
    df = coalesce_columnas(df, COL_FECHA_PEDIDO_FINAL, ["Fecha de pedido - ME5A", "Fecha de documento - NME80FN"])
    df = coalesce_columnas(df, COL_FECHA_FACTURACION_FINAL, ["Fecha facturación proveedor - NME80FN", "Fecha contabilización - NME80FN"])
    df = coalesce_columnas(df, COL_FECHA_RECEPCION_FINAL, ["Fecha recepción mercancía - NME80FN", "Fecha de entrada - NME80FN"])

    for col in [COL_FECHA_SOLICITUD_FINAL, COL_FECHA_LIBERACION_FINAL, COL_FECHA_PEDIDO_FINAL, COL_FECHA_FACTURACION_FINAL, COL_FECHA_RECEPCION_FINAL]:
        if col in df.columns:
            df[col] = convertir_fecha_columna(df[col])

    if COL_TIPO_OC not in df.columns:
        if COL_PEDIDO in df.columns:
            df[COL_TIPO_OC] = df[COL_PEDIDO].apply(extraer_tipo_oc)
        elif COL_DOCUMENTO_COMPRAS in df.columns:
            df[COL_TIPO_OC] = df[COL_DOCUMENTO_COMPRAS].apply(extraer_tipo_oc)
        else:
            df[COL_TIPO_OC] = pd.NA

    df[COL_TIPO_OC] = df[COL_TIPO_OC].astype("string")

    if COL_ORIGEN_OC not in df.columns:
        df[COL_ORIGEN_OC] = np.select(
            [bool_array(df[COL_TIPO_OC].isin(["35", "45"])), bool_array(df[COL_TIPO_OC].eq("47"))],
            ["Nacional", "Internacional"],
            default="Otro",
        )

    if COL_SISTEMA_OC not in df.columns:
        df[COL_SISTEMA_OC] = np.select(
            [bool_array(df[COL_TIPO_OC].eq("35")), bool_array(df[COL_TIPO_OC].isin(["45", "47"]))],
            ["Ariba", "ERP"],
            default="Otro",
        )

    # Cálculos mínimos cuando el archivo no los trae.
    if "dx_lib_solped" not in df.columns:
        df["dx_lib_solped"] = (df[COL_FECHA_LIBERACION_FINAL] - df[COL_FECHA_SOLICITUD_FINAL]).dt.days
    if "dx_comprador_1" not in df.columns:
        df["dx_comprador_1"] = (df[COL_FECHA_PEDIDO_FINAL] - df[COL_FECHA_LIBERACION_FINAL]).dt.days
    if COL_DX_LOGISTICA not in df.columns:
        df[COL_DX_LOGISTICA] = (df[COL_FECHA_RECEPCION_FINAL] - df[COL_FECHA_FACTURACION_FINAL]).dt.days
    if COL_DX_TAT not in df.columns:
        df[COL_DX_TAT] = (df[COL_FECHA_RECEPCION_FINAL] - df[COL_FECHA_SOLICITUD_FINAL]).dt.days

    if COL_INCUMPLIMIENTO not in df.columns:
        df[COL_INCUMPLIMIENTO] = False

    if COL_RANGO_INCUMPLIMIENTO not in df.columns:
        df[COL_RANGO_INCUMPLIMIENTO] = np.where(df[COL_INCUMPLIMIENTO], "Con incumplimiento", "Sin incumplimiento")

    if COL_DIAS_INCUMPLIMIENTO_MAX not in df.columns:
        cols_inc = [c for c in df.columns if c.startswith("dias_incumplimiento_") and c != COL_DIAS_INCUMPLIMIENTO_MAX]
        if cols_inc:
            df[COL_DIAS_INCUMPLIMIENTO_MAX] = df[cols_inc].max(axis=1, skipna=True).fillna(0)
        else:
            df[COL_DIAS_INCUMPLIMIENTO_MAX] = 0

    df["estado_pedido_visual"] = df.apply(calcular_estado_visual, axis=1)
    return df


# =========================================================
# Estado visual
# =========================================================

def tiene_fecha(row: pd.Series, col: str) -> bool:
    return col in row.index and pd.notna(row[col])


def calcular_estado_visual(row: pd.Series) -> str:
    if tiene_fecha(row, COL_FECHA_RECEPCION_FINAL):
        return "Recibido"
    if tiene_fecha(row, COL_FECHA_FACTURACION_FINAL):
        return "Facturado"
    if tiene_fecha(row, COL_FECHA_PEDIDO_FINAL):
        return "Pedido emitido"
    if tiene_fecha(row, COL_FECHA_LIBERACION_FINAL):
        return "SolPed liberada"
    if tiene_fecha(row, COL_FECHA_SOLICITUD_FINAL):
        return "Solicitado"
    return "Sin fecha"


def obtener_id_pedido(row: pd.Series) -> str:
    partes = []
    for col, prefijo in [(COL_SOLPED, "SolPed"), (COL_PEDIDO, "Pedido"), (COL_DOCUMENTO_COMPRAS, "Doc")]:
        if col in row.index and pd.notna(row[col]):
            partes.append(f"{prefijo}: {row[col]}")
    if not partes:
        return f"Línea #{row.name}"
    return " · ".join(partes)


def fmt_fecha(valor: Any) -> str:
    if pd.isna(valor):
        return "Sin fecha"
    try:
        return pd.to_datetime(valor).strftime("%Y-%m-%d")
    except Exception:
        return str(valor)


def fmt_num(valor: Any, decimales: int = 0) -> str:
    if pd.isna(valor):
        return ""
    try:
        return f"{float(valor):,.{decimales}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(valor)


def estado_etapa(row: pd.Series, etapa: Dict[str, Any]) -> Dict[str, str]:
    fecha_col = etapa["fecha"]
    existe_fecha = tiene_fecha(row, fecha_col)
    perf_col = etapa.get("performance")
    inc_col = etapa.get("incumplimiento")
    dx_col = etapa.get("dx")

    performance = row.get(perf_col, pd.NA) if perf_col else pd.NA
    dias_inc = row.get(inc_col, np.nan) if inc_col else np.nan
    dx = row.get(dx_col, np.nan) if dx_col else np.nan

    if not existe_fecha:
        clase = "pending"
        icono = "·"
        estado = "Pendiente"
    elif perf_col and pd.notna(performance) and bool(performance) is False:
        clase = "bad"
        icono = "!"
        estado = "Fuera de plazo"
    elif pd.notna(dias_inc) and float(dias_inc) > 0:
        clase = "bad"
        icono = "!"
        estado = "Fuera de plazo"
    elif perf_col and pd.notna(performance) and bool(performance) is True:
        clase = "ok"
        icono = "✓"
        estado = "Cumple"
    else:
        clase = "info"
        icono = "✓"
        estado = "Con fecha"

    extras = []
    if pd.notna(dx):
        extras.append(f"{fmt_num(dx)} días")
    if pd.notna(dias_inc) and float(dias_inc) > 0:
        extras.append(f"+{fmt_num(dias_inc)} atraso")

    return {
        "clase": clase,
        "icono": icono,
        "estado": estado,
        "fecha": fmt_fecha(row.get(fecha_col, pd.NaT)),
        "extra": " · ".join(extras),
    }


def render_timeline_html(row: pd.Series) -> str:
    html = ["<div class='timeline-wrap'>"]
    estados = [estado_etapa(row, etapa) for etapa in ETAPAS_BASE]

    for i, etapa in enumerate(ETAPAS_BASE):
        estado = estados[i]
        html.append(
            f"""
            <div class="step-wrap">
                <div class="step-box">
                    <div class="dot dot-{estado['clase']}">{estado['icono']}</div>
                    <div class="step-label">{etapa['label']}</div>
                    <div class="step-date">{estado['fecha']}</div>
                    <div class="step-extra">{estado['estado']}</div>
                    <div class="step-extra">{estado['extra']}</div>
                </div>
            """
        )
        if i < len(ETAPAS_BASE) - 1:
            actual = estado["clase"]
            siguiente = estados[i + 1]["clase"]
            line_class = "bad" if "bad" in [actual, siguiente] else "ok" if actual in ["ok", "info"] and siguiente in ["ok", "info", "bad"] else ""
            html.append(f"<div class='line line-{line_class}'></div>")
        html.append("</div>")

    html.append("</div>")
    return "".join(html)


def render_card_pedido(row: pd.Series) -> None:
    incumple = bool(row.get(COL_INCUMPLIMIENTO, False)) if pd.notna(row.get(COL_INCUMPLIMIENTO, pd.NA)) else False
    badge_perf = "badge-bad" if incumple else "badge-ok"
    texto_perf = "Con incumplimiento" if incumple else "Sin incumplimiento"

    subtitulo = []
    for col in [COL_TEXTO_BREVE, COL_MATERIAL, COL_CENTRO, COL_GRUPO_COMPRAS, COL_ESTADO_MATCH]:
        if col in row.index and pd.notna(row[col]):
            subtitulo.append(f"{col}: {row[col]}")

    html = f"""
    <div class="status-card">
        <div class="pedido-title">{obtener_id_pedido(row)}</div>
        <div class="pedido-subtitle">{' · '.join(subtitulo[:5])}</div>
        <span class="badge {badge_perf}">{texto_perf}</span>
        <span class="badge badge-neutral">Estado: {row.get('estado_pedido_visual', 'Sin información')}</span>
        <span class="badge badge-warn">Rango: {row.get(COL_RANGO_INCUMPLIMIENTO, 'Sin información')}</span>
        <span class="badge badge-neutral">Días TAT: {fmt_num(row.get(COL_DX_TAT, np.nan))}</span>
        <span class="badge badge-neutral">Atraso máx.: {fmt_num(row.get(COL_DIAS_INCUMPLIMIENTO_MAX, 0))}</span>
        {render_timeline_html(row)}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# =========================================================
# Gráficos y resúmenes
# =========================================================

def tabla_resumen_estados(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df["estado_pedido_visual"]
        .value_counts(dropna=False)
        .rename_axis("Estado visual")
        .reset_index(name="Cantidad")
    )


def plot_estado_pedidos(df: pd.DataFrame) -> go.Figure:
    resumen = tabla_resumen_estados(df)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=resumen["Estado visual"], y=resumen["Cantidad"], text=resumen["Cantidad"], textposition="auto"))
    fig.update_layout(
        title="Cantidad de líneas por estado visual",
        xaxis_title="Estado",
        yaxis_title="Cantidad",
        height=360,
        margin=dict(l=20, r=20, t=60, b=40),
    )
    return fig


def plot_rangos_incumplimiento(df: pd.DataFrame) -> Optional[go.Figure]:
    if COL_RANGO_INCUMPLIMIENTO not in df.columns:
        return None
    resumen = (
        df[COL_RANGO_INCUMPLIMIENTO]
        .fillna("Sin información")
        .value_counts()
        .rename_axis("Rango")
        .reset_index(name="Cantidad")
    )
    fig = go.Figure(data=[go.Pie(labels=resumen["Rango"], values=resumen["Cantidad"], hole=.45)])
    fig.update_layout(
        title="Distribución por rango de incumplimiento",
        height=360,
        margin=dict(l=20, r=20, t=60, b=20),
    )
    return fig


def descargar_excel(df: pd.DataFrame, resumen_estados: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Estado_pedidos")
        resumen_estados.to_excel(writer, index=False, sheet_name="Resumen_estados")
    return output.getvalue()


# =========================================================
# Interfaz principal
# =========================================================

inyectar_css()
mostrar_logo()

st.title("Estado visual de pedidos por línea")
st.caption("Carga un archivo Parquet, CSV o Excel y revisa cada línea como una línea de estado: solicitud → liberación → pedido → facturación → recepción.")

with st.sidebar:
    st.header("Configuración")

    separador_csv = st.selectbox(
        "Separador CSV",
        options=["Automático", "Punto y coma (;)", "Coma (,)", "Tabulación"],
        index=0,
    )

    limite_cards = st.number_input(
        "Cantidad de líneas visuales",
        min_value=5,
        max_value=200,
        value=30,
        step=5,
    )

    ordenar_por = st.selectbox(
        "Ordenar líneas visuales por",
        options=[
            "Mayor atraso",
            "Fecha recepción más reciente",
            "Fecha solicitud más antigua",
            "Días TAT mayor",
        ],
        index=0,
    )

    st.caption("El separador solo aplica a archivos CSV.")

uploaded_file = st.file_uploader(
    "Selecciona archivo de pedidos",
    type=["parquet", "csv", "xlsx", "xls"],
)

if uploaded_file is None:
    st.info("Carga un archivo para visualizar el estado de los pedidos.")
    st.stop()

try:
    with st.spinner("Leyendo y preparando datos..."):
        df_original = leer_archivo_cache(uploaded_file.getvalue(), uploaded_file.name, separador_csv)
        df = preparar_dataframe(df_original)

    if df.empty:
        st.warning("El archivo no contiene registros.")
        st.stop()

    # -------------------------
    # Filtros
    # -------------------------
    st.sidebar.header("Filtros")

    df_filtrado = df.copy()

    for col, etiqueta in [
        (COL_ORIGEN_OC, "Origen OC"),
        (COL_SISTEMA_OC, "Sistema OC"),
        (COL_TIPO_OC, "Tipo OC"),
        (COL_GRUPO_COMPRAS, "Grupo de compras"),
        (COL_ESTADO_MATCH, "Estado del match"),
        ("estado_pedido_visual", "Estado visual"),
        (COL_RANGO_INCUMPLIMIENTO, "Rango incumplimiento"),
    ]:
        if col in df_filtrado.columns:
            opciones = sorted([str(x) for x in df_filtrado[col].dropna().unique()])
            seleccion = st.sidebar.multiselect(etiqueta, opciones)
            if seleccion:
                df_filtrado = df_filtrado[df_filtrado[col].astype(str).isin(seleccion)]

    texto_busqueda = st.sidebar.text_input("Buscar SolPed, Pedido, material o texto")
    if texto_busqueda:
        cols_busqueda = [c for c in [COL_SOLPED, COL_PEDIDO, COL_DOCUMENTO_COMPRAS, COL_MATERIAL, COL_TEXTO_BREVE] if c in df_filtrado.columns]
        if cols_busqueda:
            mask = pd.Series(False, index=df_filtrado.index)
            for col in cols_busqueda:
                mask = mask | df_filtrado[col].astype(str).str.contains(texto_busqueda, case=False, na=False)
            df_filtrado = df_filtrado[mask]

    st.success(f"Archivo cargado correctamente: {len(df):,} líneas. Filtro actual: {len(df_filtrado):,} líneas.")

    # -------------------------
    # KPIs
    # -------------------------
    total = len(df_filtrado)
    recibidos = int(df_filtrado["estado_pedido_visual"].eq("Recibido").sum())
    incumplen = int(df_filtrado.get(COL_INCUMPLIMIENTO, pd.Series(False, index=df_filtrado.index)).fillna(False).eq(True).sum())
    atraso_prom = df_filtrado.get(COL_DIAS_INCUMPLIMIENTO_MAX, pd.Series(0, index=df_filtrado.index)).fillna(0).mean() if total else 0
    tat_prom = df_filtrado.get(COL_DX_TAT, pd.Series(np.nan, index=df_filtrado.index)).mean() if total else np.nan

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Líneas filtradas", f"{total:,}")
    c2.metric("Recibidas", f"{recibidos:,}")
    c3.metric("Con incumplimiento", f"{incumplen:,}")
    c4.metric("Atraso prom.", f"{atraso_prom:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c5.metric("TAT prom.", "" if pd.isna(tat_prom) else f"{tat_prom:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))

    # -------------------------
    # Gráficos
    # -------------------------
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.plotly_chart(plot_estado_pedidos(df_filtrado), use_container_width=True)
    with col_g2:
        fig_rango = plot_rangos_incumplimiento(df_filtrado)
        if fig_rango:
            st.plotly_chart(fig_rango, use_container_width=True)

    # -------------------------
    # Línea visual de estado
    # -------------------------
    st.subheader("Línea visual de estado de pedido")

    df_cards = df_filtrado.copy()
    if ordenar_por == "Mayor atraso" and COL_DIAS_INCUMPLIMIENTO_MAX in df_cards.columns:
        df_cards = df_cards.sort_values(COL_DIAS_INCUMPLIMIENTO_MAX, ascending=False)
    elif ordenar_por == "Fecha recepción más reciente" and COL_FECHA_RECEPCION_FINAL in df_cards.columns:
        df_cards = df_cards.sort_values(COL_FECHA_RECEPCION_FINAL, ascending=False, na_position="last")
    elif ordenar_por == "Fecha solicitud más antigua" and COL_FECHA_SOLICITUD_FINAL in df_cards.columns:
        df_cards = df_cards.sort_values(COL_FECHA_SOLICITUD_FINAL, ascending=True, na_position="last")
    elif ordenar_por == "Días TAT mayor" and COL_DX_TAT in df_cards.columns:
        df_cards = df_cards.sort_values(COL_DX_TAT, ascending=False, na_position="last")

    if df_cards.empty:
        st.warning("No hay líneas para mostrar con los filtros actuales.")
    else:
        st.caption(f"Mostrando {min(int(limite_cards), len(df_cards)):,} de {len(df_cards):,} líneas filtradas.")
        for _, row in df_cards.head(int(limite_cards)).iterrows():
            render_card_pedido(row)

    # -------------------------
    # Tablas
    # -------------------------
    st.subheader("Tablas")

    resumen_estados = tabla_resumen_estados(df_filtrado)
    with st.expander("Resumen por estado", expanded=True):
        st.dataframe(resumen_estados, use_container_width=True, hide_index=True)

    columnas_preferidas = [
        COL_SOLPED,
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        COL_POS_SOLPED,
        COL_POS_PEDIDO,
        COL_POS_NME,
        COL_MATERIAL,
        COL_TEXTO_BREVE,
        COL_CENTRO,
        COL_GRUPO_COMPRAS,
        COL_ESTADO_MATCH,
        "estado_pedido_visual",
        COL_RANGO_INCUMPLIMIENTO,
        COL_DIAS_INCUMPLIMIENTO_MAX,
        COL_DX_TAT,
        COL_DX_LOGISTICA,
        COL_DX_PROVEEDOR,
        COL_FECHA_SOLICITUD_FINAL,
        COL_FECHA_LIBERACION_FINAL,
        COL_FECHA_PEDIDO_FINAL,
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "performance_lib_solped",
        "performance_comprador_1",
        "performance_logistica",
        "performance_tat",
        "performance_proveedor",
    ]
    columnas_preferidas = [c for c in columnas_preferidas if c in df_filtrado.columns]

    with st.expander("Datos filtrados", expanded=False):
        st.dataframe(df_filtrado[columnas_preferidas] if columnas_preferidas else df_filtrado, use_container_width=True, hide_index=True)

    with st.expander("Columnas disponibles", expanded=False):
        st.write(df_filtrado.columns.tolist())

    # -------------------------
    # Descargas
    # -------------------------
    st.subheader("Descarga")
    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        st.download_button(
            "Descargar CSV filtrado",
            data=df_filtrado.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
            file_name="estado_visual_pedidos_filtrado.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_d2:
        output_parquet = io.BytesIO()
        df_filtrado.to_parquet(output_parquet, index=False, engine="pyarrow")
        st.download_button(
            "Descargar Parquet filtrado",
            data=output_parquet.getvalue(),
            file_name="estado_visual_pedidos_filtrado.parquet",
            mime="application/octet-stream",
            use_container_width=True,
        )

    with col_d3:
        excel_bytes = descargar_excel(df_filtrado, resumen_estados)
        st.download_button(
            "Descargar Excel filtrado",
            data=excel_bytes,
            file_name="estado_visual_pedidos_filtrado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

except Exception as e:
    st.error("No se pudo visualizar el estado de pedidos.")
    st.exception(e)
