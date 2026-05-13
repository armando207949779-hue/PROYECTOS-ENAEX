import io
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# Configuracion general
# =========================================================
st.set_page_config(
    page_title="Buscador SolPed / OC",
    page_icon="🔎",
    layout="wide",
)


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

FECHAS_PANEL = [
    ("Solicitud", "fecha_solicitud_final"),
    ("Liberación", "fecha_liberacion_final"),
    ("Pedido", "fecha_pedido_final"),
    ("Facturación", "fecha_facturacion_final"),
    ("Recepción", "fecha_recepcion_final"),
]

DIAS_PANEL = [
    ("Liberación SolPed", "dias_liberacion_solped", "umbral_liberacion_solped"),
    ("Comprador", "dias_comprador", "umbral_comprador"),
    ("Liberación Pedido", "dias_liberacion_pedido", "umbral_liberacion_pedido"),
    ("Proveedor", "dias_proveedor", "umbral_proveedor"),
    ("Logística", "dias_logistica", "umbral_logistica"),
    ("TAT Total", "dias_tat_total", "umbral_tat_total"),
    ("Incumplimiento TAT", "dias_incumplimiento_tat", None),
]

PERFORMANCE_PANEL = [
    ("Liberación SolPed", "performance_liberacion_solped"),
    ("Comprador", "performance_comprador"),
    ("Liberación Pedido", "performance_liberacion_pedido"),
    ("Proveedor", "performance_proveedor"),
    ("Logística", "performance_logistica"),
    ("TAT Total", "performance_tat_total"),
]

COLUMNAS_TABLA_PRINCIPAL = [
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
    COL_PERF_TAT,
    COL_DIAS_TAT,
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
        .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
        h1 {font-size: 2.0rem !important; margin-bottom: 0.1rem !important;}
        h2, h3 {letter-spacing: -0.02em;}
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #eef2f7;
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 1px 4px rgba(15, 23, 42, 0.04);
        }
        .match-box {
            background: #eef7ff;
            border: 1px solid #cde7ff;
            border-radius: 18px;
            padding: 18px 20px;
            margin: 0.3rem 0 1.1rem 0;
        }
        .match-number {
            font-size: 2.2rem;
            font-weight: 800;
            color: #075985;
            line-height: 1.1;
        }
        .match-label {
            color: #334155;
            font-size: 0.95rem;
            margin-top: 4px;
        }
        .section-card {
            background: #ffffff;
            border: 1px solid #edf2f7;
            border-radius: 18px;
            padding: 16px 16px 12px 16px;
            margin-bottom: 10px;
            box-shadow: 0 1px 5px rgba(15, 23, 42, 0.035);
        }
        .mini-title {
            font-size: 0.78rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 4px;
        }
        .mini-value {
            font-size: 1.15rem;
            font-weight: 750;
            color: #0f172a;
            margin-bottom: 2px;
        }
        .mini-note {
            font-size: 0.80rem;
            color: #64748b;
        }
        .pill {
            display: inline-block;
            border-radius: 999px;
            padding: 5px 10px;
            font-size: 0.78rem;
            font-weight: 750;
            margin: 2px 0;
            border: 1px solid transparent;
        }
        .pill-green {background: #dcfce7; color: #166534; border-color: #bbf7d0;}
        .pill-red {background: #fee2e2; color: #991b1b; border-color: #fecaca;}
        .pill-yellow {background: #fef9c3; color: #854d0e; border-color: #fde68a;}
        .pill-gray {background: #f1f5f9; color: #475569; border-color: #e2e8f0;}
        .pill-blue {background: #dbeafe; color: #1e40af; border-color: #bfdbfe;}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Lectura y utilidades
# =========================================================
def obtener_separador(opcion: str):
    if opcion == "Automático":
        return None
    if opcion == "Punto y coma (; )" or opcion == "Punto y coma (; )".strip():
        return ";"
    if opcion == "Punto y coma (; )":
        return ";"
    if opcion == "Punto y coma (;)":
        return ";"
    if opcion == "Coma (,)":
        return ","
    if opcion == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner=False)
def leer_archivo(bytes_archivo: bytes, nombre_archivo: str, separador_csv: str) -> pd.DataFrame:
    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)
        try:
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="utf-8-sig", on_bad_lines="skip")
        except Exception:
            buffer.seek(0)
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="latin1", on_bad_lines="skip")

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(buffer)

    raise ValueError("Formato no soportado. Usa Parquet, CSV o Excel.")


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


def convertir_fechas_visuales(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in FECHAS_CANDIDATAS:
        if col in df.columns:
            convertido = convertir_columna_fecha(df[col])
            if convertido.notna().any():
                df[col] = convertido
    return df


def opciones_columna(df: pd.DataFrame, col: str, max_opciones: int = 700) -> list[str]:
    if col not in df.columns:
        return []
    valores = df[col].dropna().astype(str).sort_values().unique().tolist()
    return valores[:max_opciones]


def filtrar_por_ids(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)

    tokens = (
        str(texto)
        .replace("\n", ",")
        .replace(";", ",")
        .replace(" ", ",")
        .split(",")
    )
    tokens = [t.strip().replace(".0", "") for t in tokens if t.strip()]

    if not tokens:
        return pd.Series(True, index=df.index)

    serie = df[columna].astype(str).str.replace(".0", "", regex=False)
    mask = pd.Series(False, index=df.index)
    for token in tokens:
        mask = mask | serie.str.contains(token, case=False, na=False, regex=False)
    return mask


def contiene_texto(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not str(texto).strip():
        return pd.Series(True, index=df.index)
    return df[columna].astype(str).str.contains(str(texto).strip(), case=False, na=False, regex=False)


def aplicar_rango_numerico(df: pd.DataFrame, columna: str, minimo: Any, maximo: Any) -> pd.Series:
    if columna not in df.columns:
        return pd.Series(True, index=df.index)

    serie = pd.to_numeric(df[columna], errors="coerce")
    mask = pd.Series(True, index=df.index)

    if minimo is not None:
        mask = mask & serie.ge(float(minimo))
    if maximo is not None:
        mask = mask & serie.le(float(maximo))

    return mask


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


def formato_numero(valor: Any, decimales: int = 0) -> str:
    if pd.isna(valor):
        return "-"
    try:
        valor_float = float(valor)
    except Exception:
        return str(valor)
    texto = f"{valor_float:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def clase_performance(valor: Any) -> str:
    texto = str(valor).strip().lower()
    if texto == "cumple":
        return "pill-green"
    if texto == "no cumple":
        return "pill-red"
    if texto in ["en proceso", "sin datos"]:
        return "pill-yellow"
    if "no aplica" in texto:
        return "pill-gray"
    return "pill-blue"


def clase_dias(dias: Any, umbral: Any = None) -> str:
    dias_num = pd.to_numeric(pd.Series([dias]), errors="coerce").iloc[0]
    umbral_num = pd.to_numeric(pd.Series([umbral]), errors="coerce").iloc[0] if umbral is not None else np.nan

    if pd.isna(dias_num):
        return "pill-gray"
    if dias_num < 0:
        return "pill-gray"
    if pd.notna(umbral_num):
        if dias_num <= umbral_num:
            return "pill-green"
        return "pill-red"
    if dias_num == 0:
        return "pill-green"
    return "pill-yellow"


def pill(texto: Any, clase: str) -> str:
    return f'<span class="pill {clase}">{formato_valor(texto)}</span>'


def dataframe_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return output.getvalue()


def dataframe_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_parquet(output, index=False, engine="pyarrow")
    return output.getvalue()


def construir_label_registro(row: pd.Series) -> str:
    solped = row.get(COL_SOLPED, "-")
    oc = row.get(COL_OC_ME5A, row.get(COL_OC_NME, "-"))
    pos = row.get(COL_POS_SOLPED, "-")
    perf = row.get(COL_PERF_TAT, "-")
    dias = row.get(COL_DIAS_TAT, "-")
    texto = row.get(COL_TEXTO, "")
    texto = str(texto)[:55]
    return f"SolPed {formato_valor(solped)} | OC {formato_valor(oc)} | Pos {formato_valor(pos)} | TAT {formato_valor(dias)} días | {perf} | {texto}"


def aplicar_estilo_tabla(df_tabla: pd.DataFrame):
    def color_performance(valor):
        texto = str(valor).strip().lower()
        if texto == "cumple":
            return "background-color: #dcfce7; color: #166534; font-weight: 700;"
        if texto == "no cumple":
            return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
        if texto in ["en proceso", "sin datos"]:
            return "background-color: #fef9c3; color: #854d0e; font-weight: 700;"
        if "no aplica" in texto:
            return "background-color: #f1f5f9; color: #475569; font-weight: 700;"
        return ""

    def color_incumplimiento(valor):
        texto = str(valor).strip().lower()
        if texto == "sin incumplimiento":
            return "background-color: #dcfce7; color: #166534; font-weight: 700;"
        if texto in ["0-5 días", "6-15 días"]:
            return "background-color: #fef9c3; color: #854d0e; font-weight: 700;"
        if texto in ["16-30 días", "mayor a un mes"]:
            return "background-color: #fee2e2; color: #991b1b; font-weight: 700;"
        return ""

    styler = df_tabla.style
    for col in df_tabla.columns:
        if col.startswith("performance_") or col == COL_PERF_TAT:
            styler = styler.map(color_performance, subset=[col])
        if col == COL_RANGO_INC:
            styler = styler.map(color_incumplimiento, subset=[col])
    return styler


# =========================================================
# Header minimalista
# =========================================================
st.title("Buscador SolPed / OC")
st.caption("Carga un archivo ya procesado. La app solo filtra, visualiza y descarga resultados; no recalcula performance.")


# =========================================================
# Carga
# =========================================================
with st.sidebar:
    st.header("Archivo")

    separador_csv = st.selectbox(
        "Separador CSV",
        ["Automático", "Punto y coma (;)", "Coma (,)", "Tabulación"],
        index=0,
    )

    uploaded_file = st.file_uploader(
        "Subir parquet, CSV o Excel",
        type=["parquet", "csv", "xlsx", "xls"],
    )

    st.divider()

    limite_vista = st.number_input(
        "Filas en tabla",
        min_value=25,
        max_value=5000,
        value=300,
        step=25,
    )

    mostrar_todas_columnas = st.checkbox("Mostrar todas las columnas en tabla", value=False)

if uploaded_file is None:
    st.info("Sube un archivo `.parquet`, `.csv`, `.xlsx` o `.xls` para comenzar.")
    st.stop()

try:
    df = leer_archivo(uploaded_file.getvalue(), uploaded_file.name, separador_csv)
    df = limpiar_columnas(df)
    df = convertir_fechas_visuales(df)
except Exception as e:
    st.error("No se pudo leer el archivo.")
    st.exception(e)
    st.stop()


# =========================================================
# Filtros principales visibles
# =========================================================
st.markdown("### Filtros principales")

c1, c2, c3 = st.columns([1, 1, 0.8])
with c1:
    txt_solped = st.text_input("SolPed", placeholder="Ej: 1001973319")
with c2:
    txt_oc = st.text_input("Orden de compra / Pedido", placeholder="Ej: 4502321875")
with c3:
    txt_pos_solped = st.text_input("Posición SolPed", placeholder="Ej: 10")


# =========================================================
# Filtros avanzados colapsados
# =========================================================
with st.expander("Filtros avanzados", expanded=False):
    st.caption("Úsalos solo cuando necesites acotar más la búsqueda.")

    a1, a2, a3, a4 = st.columns(4)

    with a1:
        txt_pos_oc = st.text_input("Posición OC", placeholder="Ej: 10")
        txt_material = st.text_input("Material", placeholder="Ej: 20012021")
        txt_descripcion = st.text_input("Descripción / texto breve", placeholder="Ej: bloqueador")

    with a2:
        txt_solicitante = st.text_input("Solicitante", placeholder="Ej: c.silva")
        txt_autor = st.text_input("Autor", placeholder="Ej: CL17330735")
        centro_sel = st.multiselect("Centro", opciones_columna(df, COL_CENTRO))

    with a3:
        tipo_oc_sel = st.multiselect("Tipo OC", opciones_columna(df, COL_TIPO_OC))
        origen_sel = st.multiselect("Origen", opciones_columna(df, COL_ORIGEN))
        sistema_sel = st.multiselect("Sistema", opciones_columna(df, COL_SISTEMA))

    with a4:
        grupo_sel = st.multiselect("Grupo de compras", opciones_columna(df, COL_GRUPO_COMPRAS))
        estado_match_sel = st.multiselect("Estado del match", opciones_columna(df, COL_ESTADO_MATCH))
        perf_tat_sel = st.multiselect("Performance TAT", opciones_columna(df, COL_PERF_TAT))
        rango_inc_sel = st.multiselect("Rango incumplimiento TAT", opciones_columna(df, COL_RANGO_INC))

    st.markdown("#### Rango de días / monto")
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        usar_dias_tat_min = st.checkbox("TAT mínimo", value=False)
        dias_tat_min = st.number_input("Valor mínimo TAT", value=0, step=1, disabled=not usar_dias_tat_min)
    with r2:
        usar_dias_tat_max = st.checkbox("TAT máximo", value=False)
        dias_tat_max = st.number_input("Valor máximo TAT", value=9999, step=1, disabled=not usar_dias_tat_max)
    with r3:
        usar_monto_min = st.checkbox("Monto mínimo", value=False)
        monto_min = st.number_input("Valor mínimo monto", value=0.0, step=1000.0, disabled=not usar_monto_min)
    with r4:
        usar_monto_max = st.checkbox("Monto máximo", value=False)
        monto_max = st.number_input("Valor máximo monto", value=0.0, step=1000.0, disabled=not usar_monto_max)

    f1, f2 = st.columns(2)
    with f1:
        solo_incumplimiento = st.checkbox("Solo incumplimiento TAT", value=False)
    with f2:
        solo_fechas_inconsistentes = st.checkbox("Solo fechas inconsistentes", value=False)

    st.markdown("#### Fecha")
    fecha_col_disponibles = [
        c for c in FECHAS_CANDIDATAS
        if c in df.columns and pd.api.types.is_datetime64_any_dtype(df[c])
    ]

    if fecha_col_disponibles:
        usar_filtro_fecha = st.checkbox("Aplicar filtro de fecha", value=False)
        col_fecha_filtro = st.selectbox("Columna de fecha", fecha_col_disponibles, index=0, disabled=not usar_filtro_fecha)
        fecha_min_real = df[col_fecha_filtro].min()
        fecha_max_real = df[col_fecha_filtro].max()

        if pd.notna(fecha_min_real) and pd.notna(fecha_max_real):
            fc1, fc2 = st.columns(2)
            with fc1:
                fecha_desde = st.date_input("Desde", value=fecha_min_real.date(), disabled=not usar_filtro_fecha)
            with fc2:
                fecha_hasta = st.date_input("Hasta", value=fecha_max_real.date(), disabled=not usar_filtro_fecha)
        else:
            usar_filtro_fecha = False
            fecha_desde = None
            fecha_hasta = None
            st.warning("La columna seleccionada no tiene fechas válidas.")
    else:
        usar_filtro_fecha = False
        fecha_desde = None
        fecha_hasta = None
        col_fecha_filtro = None
        st.info("No se encontraron columnas de fecha convertibles para filtrar.")

# Defaults cuando el expander no inicializa widgets? Streamlit igual los inicializa, pero dejamos seguridad.
for nombre, default in {
    "txt_pos_oc": "",
    "txt_material": "",
    "txt_descripcion": "",
    "txt_solicitante": "",
    "txt_autor": "",
    "centro_sel": [],
    "tipo_oc_sel": [],
    "origen_sel": [],
    "sistema_sel": [],
    "grupo_sel": [],
    "estado_match_sel": [],
    "perf_tat_sel": [],
    "rango_inc_sel": [],
    "usar_dias_tat_min": False,
    "usar_dias_tat_max": False,
    "dias_tat_min": 0,
    "dias_tat_max": 9999,
    "usar_monto_min": False,
    "usar_monto_max": False,
    "monto_min": 0.0,
    "monto_max": 0.0,
    "solo_incumplimiento": False,
    "solo_fechas_inconsistentes": False,
    "usar_filtro_fecha": False,
}.items():
    if nombre not in locals():
        locals()[nombre] = default


# =========================================================
# Aplicar filtros
# =========================================================
mask = pd.Series(True, index=df.index)

mask &= filtrar_por_ids(df, COL_SOLPED, txt_solped)
mask &= filtrar_por_ids(df, COL_OC_ME5A, txt_oc) | filtrar_por_ids(df, COL_OC_NME, txt_oc)
mask &= filtrar_por_ids(df, COL_POS_SOLPED, txt_pos_solped)
mask &= filtrar_por_ids(df, COL_POS_OC, txt_pos_oc)
mask &= filtrar_por_ids(df, COL_MATERIAL, txt_material)
mask &= contiene_texto(df, COL_TEXTO, txt_descripcion)
mask &= contiene_texto(df, COL_SOLICITANTE, txt_solicitante)
mask &= contiene_texto(df, COL_AUTOR, txt_autor)

if centro_sel and COL_CENTRO in df.columns:
    mask &= df[COL_CENTRO].astype(str).isin(centro_sel)
if tipo_oc_sel and COL_TIPO_OC in df.columns:
    mask &= df[COL_TIPO_OC].astype(str).isin(tipo_oc_sel)
if origen_sel and COL_ORIGEN in df.columns:
    mask &= df[COL_ORIGEN].astype(str).isin(origen_sel)
if sistema_sel and COL_SISTEMA in df.columns:
    mask &= df[COL_SISTEMA].astype(str).isin(sistema_sel)
if grupo_sel and COL_GRUPO_COMPRAS in df.columns:
    mask &= df[COL_GRUPO_COMPRAS].astype(str).isin(grupo_sel)
if estado_match_sel and COL_ESTADO_MATCH in df.columns:
    mask &= df[COL_ESTADO_MATCH].astype(str).isin(estado_match_sel)
if perf_tat_sel and COL_PERF_TAT in df.columns:
    mask &= df[COL_PERF_TAT].astype(str).isin(perf_tat_sel)
if rango_inc_sel and COL_RANGO_INC in df.columns:
    mask &= df[COL_RANGO_INC].astype(str).isin(rango_inc_sel)

mask &= aplicar_rango_numerico(
    df,
    COL_DIAS_TAT,
    dias_tat_min if usar_dias_tat_min else None,
    dias_tat_max if usar_dias_tat_max else None,
)
mask &= aplicar_rango_numerico(
    df,
    COL_MONTO,
    monto_min if usar_monto_min else None,
    monto_max if usar_monto_max else None,
)

if solo_incumplimiento and COL_INC_TAT in df.columns:
    mask &= df[COL_INC_TAT].eq(True)

if solo_fechas_inconsistentes and COL_FECHAS_INCONSISTENTES in df.columns:
    mask &= df[COL_FECHAS_INCONSISTENTES].eq(True)

if usar_filtro_fecha and col_fecha_filtro and fecha_desde and fecha_hasta:
    inicio = pd.Timestamp(fecha_desde)
    fin = pd.Timestamp(fecha_hasta) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    mask &= df[col_fecha_filtro].between(inicio, fin, inclusive="both")

df_filtrado = df.loc[mask].copy()


# =========================================================
# Coincidencias destacadas
# =========================================================
porcentaje = (len(df_filtrado) / len(df) * 100) if len(df) else 0
st.markdown(
    f"""
    <div class="match-box">
        <div class="match-number">{len(df_filtrado):,}</div>
        <div class="match-label">coincidencias encontradas de {len(df):,} registros cargados · {porcentaje:.1f}% del archivo</div>
    </div>
    """.replace(",", "."),
    unsafe_allow_html=True,
)


# =========================================================
# Métricas generales semáforo
# =========================================================
st.markdown("### Indicadores del filtro")

m1, m2, m3, m4, m5 = st.columns(5)

m1.metric("Registros", f"{len(df_filtrado):,}".replace(",", "."))

if COL_PERF_TAT in df_filtrado.columns:
    tat_cumple = int(df_filtrado[COL_PERF_TAT].eq("Cumple").sum())
    tat_no_cumple = int(df_filtrado[COL_PERF_TAT].eq("No cumple").sum())
    tat_proceso = int(df_filtrado[COL_PERF_TAT].eq("En proceso").sum())
else:
    tat_cumple = tat_no_cumple = tat_proceso = 0

m2.metric("TAT cumple", f"{tat_cumple:,}".replace(",", "."))
m3.metric("TAT no cumple", f"{tat_no_cumple:,}".replace(",", "."))
m4.metric("En proceso", f"{tat_proceso:,}".replace(",", "."))

if COL_MONTO in df_filtrado.columns:
    monto_total = pd.to_numeric(df_filtrado[COL_MONTO], errors="coerce").sum()
    m5.metric("Monto", formato_numero(monto_total, 0))
else:
    m5.metric("Monto", "-")

d1, d2, d3, d4 = st.columns(4)
if COL_DIAS_TAT in df_filtrado.columns:
    dias_tat = pd.to_numeric(df_filtrado[COL_DIAS_TAT], errors="coerce")
    d1.metric("TAT promedio", formato_numero(dias_tat.mean(), 1) if dias_tat.notna().any() else "-")
    d2.metric("TAT máximo", formato_numero(dias_tat.max(), 0) if dias_tat.notna().any() else "-")
else:
    d1.metric("TAT promedio", "-")
    d2.metric("TAT máximo", "-")

if COL_DIAS_INC in df_filtrado.columns:
    dias_inc = pd.to_numeric(df_filtrado[COL_DIAS_INC], errors="coerce")
    d3.metric("Incumplimiento prom.", formato_numero(dias_inc.mean(), 1) if dias_inc.notna().any() else "-")
    d4.metric("Incumplimiento máx.", formato_numero(dias_inc.max(), 0) if dias_inc.notna().any() else "-")
else:
    d3.metric("Incumplimiento prom.", "-")
    d4.metric("Incumplimiento máx.", "-")


# =========================================================
# Registro destacado: fechas, dias, performance
# =========================================================
st.markdown("### Lectura clara del registro")

if df_filtrado.empty:
    st.warning("No hay resultados con los filtros aplicados.")
else:
    opciones_detalle = []
    for idx, row in df_filtrado.head(5000).iterrows():
        opciones_detalle.append((idx, construir_label_registro(row)))

    labels = [item[1] for item in opciones_detalle]
    label_sel = st.selectbox("Registro a visualizar", labels)
    idx_sel = opciones_detalle[labels.index(label_sel)][0]
    row = df_filtrado.loc[idx_sel]

    h1, h2, h3, h4 = st.columns(4)
    h1.metric("SolPed", formato_valor(row.get(COL_SOLPED, np.nan)))
    h2.metric("OC / Pedido", formato_valor(row.get(COL_OC_ME5A, row.get(COL_OC_NME, np.nan))))
    h3.metric("Posición SolPed", formato_valor(row.get(COL_POS_SOLPED, np.nan)))
    h4.metric("Performance TAT", formato_valor(row.get(COL_PERF_TAT, np.nan)))

    st.markdown("#### Fechas clave")
    fecha_cols = st.columns(5)
    for i, (titulo, col) in enumerate(FECHAS_PANEL):
        with fecha_cols[i]:
            st.markdown(
                f"""
                <div class="section-card">
                    <div class="mini-title">{titulo}</div>
                    <div class="mini-value">{formato_valor(row.get(col, np.nan))}</div>
                    <div class="mini-note">{col}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("#### Días y umbrales")
    dias_cols = st.columns(4)
    for i, (titulo, col_dias, col_umbral) in enumerate(DIAS_PANEL):
        dias = row.get(col_dias, np.nan)
        umbral = row.get(col_umbral, np.nan) if col_umbral else np.nan
        clase = clase_dias(dias, umbral if col_umbral else None)
        nota = f"Umbral: {formato_valor(umbral)} días" if col_umbral else "Exceso sobre umbral TAT"
        with dias_cols[i % 4]:
            st.markdown(
                f"""
                <div class="section-card">
                    <div class="mini-title">{titulo}</div>
                    <div class="mini-value">{pill(str(formato_valor(dias)) + ' días', clase)}</div>
                    <div class="mini-note">{nota}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("#### Performance por etapa")
    perf_cols = st.columns(3)
    for i, (titulo, col_perf) in enumerate(PERFORMANCE_PANEL):
        valor = row.get(col_perf, np.nan)
        with perf_cols[i % 3]:
            st.markdown(
                f"""
                <div class="section-card">
                    <div class="mini-title">{titulo}</div>
                    <div class="mini-value">{pill(valor, clase_performance(valor))}</div>
                    <div class="mini-note">{col_perf}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# =========================================================
# Distribuciones simples
# =========================================================
with st.expander("Distribuciones del resultado", expanded=False):
    b1, b2, b3 = st.columns(3)

    with b1:
        if COL_PERF_TAT in df_filtrado.columns:
            st.markdown("**Performance TAT**")
            tabla_perf = df_filtrado[COL_PERF_TAT].value_counts(dropna=False).reset_index()
            tabla_perf.columns = ["Performance TAT", "Cantidad"]
            st.dataframe(tabla_perf, use_container_width=True, hide_index=True)

    with b2:
        if COL_RANGO_INC in df_filtrado.columns:
            st.markdown("**Rango incumplimiento TAT**")
            tabla_rango = df_filtrado[COL_RANGO_INC].value_counts(dropna=False).reset_index()
            tabla_rango.columns = ["Rango", "Cantidad"]
            st.dataframe(tabla_rango, use_container_width=True, hide_index=True)

    with b3:
        if COL_ESTADO_MATCH in df_filtrado.columns:
            st.markdown("**Estado del match**")
            tabla_estado = df_filtrado[COL_ESTADO_MATCH].value_counts(dropna=False).reset_index()
            tabla_estado.columns = ["Estado", "Cantidad"]
            st.dataframe(tabla_estado, use_container_width=True, hide_index=True)


# =========================================================
# Tabla de resultado filtrado
# =========================================================
with st.expander("Tabla de resultado filtrado", expanded=True):
    columnas_base = [c for c in COLUMNAS_TABLA_PRINCIPAL if c in df_filtrado.columns]
    columnas_extra = [
        c for c in [x[1] for x in DIAS_PANEL] + [x[1] for x in PERFORMANCE_PANEL] + [x[1] for x in FECHAS_PANEL]
        if c in df_filtrado.columns and c not in columnas_base
    ]

    columnas_default = df_filtrado.columns.tolist() if mostrar_todas_columnas else columnas_base + columnas_extra

    columnas_visibles = st.multiselect(
        "Columnas visibles",
        options=df_filtrado.columns.tolist(),
        default=columnas_default,
    )

    if columnas_visibles:
        tabla = df_filtrado[columnas_visibles].head(int(limite_vista)).copy()
        st.dataframe(aplicar_estilo_tabla(tabla), use_container_width=True, hide_index=True)
    else:
        st.info("Selecciona al menos una columna.")


# =========================================================
# Registro completo transpuesto
# =========================================================
with st.expander("Registro completo transpuesto", expanded=False):
    if df_filtrado.empty:
        st.info("No hay registros para visualizar.")
    else:
        registro_t = df_filtrado.loc[[idx_sel]].T.reset_index()
        registro_t.columns = ["Campo", "Valor"]
        st.dataframe(registro_t, use_container_width=True, hide_index=True)


# =========================================================
# Descargas
# =========================================================
st.markdown("### Descarga")

csv_bytes = df_filtrado.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

x1, x2, x3 = st.columns(3)
with x1:
    st.download_button(
        "Descargar CSV filtrado",
        data=csv_bytes,
        file_name="resultado_filtrado_solped_oc.csv",
        mime="text/csv",
        use_container_width=True,
    )

with x2:
    try:
        parquet_bytes = dataframe_a_parquet(df_filtrado)
        st.download_button(
            "Descargar Parquet filtrado",
            data=parquet_bytes,
            file_name="resultado_filtrado_solped_oc.parquet",
            mime="application/octet-stream",
            use_container_width=True,
        )
    except Exception:
        st.button("Parquet no disponible", disabled=True, use_container_width=True)

with x3:
    if len(df_filtrado) <= 250_000:
        excel_bytes = dataframe_a_excel(df_filtrado)
        st.download_button(
            "Descargar Excel filtrado",
            data=excel_bytes,
            file_name="resultado_filtrado_solped_oc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.button("Excel no disponible", disabled=True, use_container_width=True)
        st.caption("Excel se desactiva sobre 250.000 filas.")


# =========================================================
# Info tecnica
# =========================================================
with st.expander("Columnas disponibles", expanded=False):
    st.write(df.columns.tolist())
