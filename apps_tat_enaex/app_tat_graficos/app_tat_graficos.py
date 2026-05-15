# app_powerbi_style.py

import base64
import io
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Performance TAT 2025",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_CANDIDATOS = [
    BASE_DIR / "assets" / "logo.svg",
    BASE_DIR / "assets" / "logo.png",
    BASE_DIR / "logo.svg",
    BASE_DIR / "logo.png",
    BASE_DIR.parent / "assets" / "logo.svg",
    BASE_DIR.parent / "assets" / "logo.png",
]

ESTADOS_EVALUABLES = ["Cumple", "No cumple"]
COLOR_CUMPLE = "#666666"
COLOR_NO_CUMPLE = "#E44555"
COLOR_META = "#007A53"
COLOR_FONDO = "#E6E6E6"
COLOR_PANEL = "#E9E9E9"
COLOR_TEXTO = "#2B2B2B"
COLOR_TEXTO_SUAVE = "#666666"

MESES_NOMBRE = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}

# =========================================================
# ESTILO VISUAL SIMILAR A POWER BI
# =========================================================

def aplicar_estilos():
    st.markdown(
        f"""
        <style>
            .stApp {{
                background: {COLOR_FONDO};
                color: {COLOR_TEXTO};
            }}
            .block-container {{
                padding-top: 0.25rem;
                padding-left: 0.55rem;
                padding-right: 0.55rem;
                padding-bottom: 0.7rem;
                max-width: 100%;
            }}
            header[data-testid="stHeader"] {{
                background: transparent;
                height: 0rem;
            }}
            [data-testid="stToolbar"] {{
                display: none;
            }}
            div[data-testid="stVerticalBlock"] {{
                gap: 0.35rem;
            }}
            div[data-testid="column"] {{
                padding-left: 0.15rem;
                padding-right: 0.15rem;
            }}
            .top-zone {{
                display: flex;
                align-items: flex-start;
                justify-content: space-between;
                width: 100%;
                margin-bottom: 0.15rem;
            }}
            .logo-box {{
                min-width: 230px;
                height: 72px;
                display: flex;
                flex-direction: column;
                align-items: flex-start;
                justify-content: flex-start;
            }}
            .dashboard-title {{
                font-size: 13px;
                font-weight: 600;
                margin-top: -2px;
                letter-spacing: 0.1px;
            }}
            .filter-label {{
                font-size: 12px;
                font-weight: 600;
                color: {COLOR_TEXTO};
                margin-bottom: -6px;
            }}
            .section-note {{
                font-size: 11px;
                line-height: 1.35;
                color: #111111;
                font-weight: 600;
                margin-top: 0.15rem;
                margin-bottom: 0.15rem;
            }}
            .stage-title {{
                text-align: center;
                font-size: 17px;
                font-weight: 500;
                color: {COLOR_TEXTO};
                margin-top: 0.2rem;
                margin-bottom: 0.2rem;
            }}
            .stage-rule {{
                text-align: center;
                font-size: 10px;
                color: #111111;
                min-height: 26px;
                margin-bottom: 0.1rem;
            }}
            .stage-kpi {{
                text-align: center;
                font-size: 38px;
                line-height: 1.0;
                font-weight: 600;
                color: #222222;
                margin-top: 0.05rem;
            }}
            .stage-kpi-caption {{
                text-align: center;
                font-size: 12px;
                color: {COLOR_TEXTO_SUAVE};
                margin-top: 0.1rem;
            }}
            .panel-soft {{
                background: {COLOR_PANEL};
                border-radius: 2px;
                padding: 0.1rem 0.25rem;
            }}
            div[data-baseweb="select"] > div {{
                background: {COLOR_PANEL};
                border: 0 !important;
                box-shadow: none !important;
                min-height: 34px;
            }}
            div[data-testid="stDateInput"] input {{
                background: {COLOR_PANEL};
                border: 0;
                box-shadow: none;
                min-height: 32px;
            }}
            div[data-testid="stFileUploader"] section {{
                background: {COLOR_PANEL};
                border: 1px dashed #A0A0A0;
            }}
            .small-divider {{
                border-top: 1px dashed #BDBDBD;
                margin: 0.25rem 0 0.15rem 0;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def obtener_logo_html(ancho: int = 175) -> str:
    for ruta in LOGO_CANDIDATOS:
        if ruta.exists():
            suffix = ruta.suffix.lower()
            raw = ruta.read_bytes()
            encoded = base64.b64encode(raw).decode("utf-8")
            if suffix == ".svg":
                mime = "image/svg+xml"
            elif suffix == ".png":
                mime = "image/png"
            elif suffix in [".jpg", ".jpeg"]:
                mime = "image/jpeg"
            else:
                continue
            return f'<img src="data:{mime};base64,{encoded}" width="{ancho}" style="display:block; margin-left:0;">'

    return "<div style='font-size:34px; font-weight:800; color:#FFFFFF;'>Enaex</div>"


def render_logo_y_titulo():
    st.markdown(
        f"""
        <div class="logo-box">
            {obtener_logo_html()}
            <div class="dashboard-title">Performance TAT 2025</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# CARGA Y NORMALIZACIÓN
# =========================================================

@st.cache_data(show_spinner=False)
def leer_archivo_cache(bytes_archivo: bytes, nombre_archivo: str, separador_csv: str) -> pd.DataFrame:
    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)
    if nombre.endswith(".xlsx"):
        return pd.read_excel(buffer)
    if nombre.endswith(".csv"):
        sep = None if separador_csv == "Automático" else separador_csv
        try:
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="utf-8-sig", on_bad_lines="skip")
        except Exception:
            buffer.seek(0)
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="latin1", on_bad_lines="skip")

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


def normalizar_estado(valor):
    if pd.isna(valor):
        return "Sin información"

    texto = (
        str(valor).strip().lower()
        .replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    )

    if texto in ["cumple", "true", "1", "si", "sí", "yes"]:
        return "Cumple"
    if texto in ["no cumple", "nocumple", "false", "0", "no"]:
        return "No cumple"
    if texto in ["no aplica", "no aplica al analisis", "no aplica al análisis"]:
        return "No aplica"
    if texto in ["sin datos", "sin informacion", "sin información", "en proceso"]:
        return "Sin datos / En proceso"

    return "Sin información"


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    faltantes = [col for col in ["fecha_recepcion_final", "performance_tat_total"] if col not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    df["fecha_recepcion_final"] = pd.to_datetime(df["fecha_recepcion_final"], errors="coerce")
    df["performance_tat_estado"] = df["performance_tat_total"].apply(normalizar_estado)
    df["anio"] = df["fecha_recepcion_final"].dt.year
    df["mes_num"] = df["fecha_recepcion_final"].dt.month
    df["periodo_fecha"] = df["fecha_recepcion_final"].dt.to_period("M").dt.to_timestamp()
    df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)
    df["periodo_label"] = np.where(
        df["anio"].notna() & df["mes_nombre"].notna(),
        df["mes_nombre"].astype(str),
        pd.NA,
    )
    return df


def detectar_columna(df: pd.DataFrame, candidatos: list[str]):
    return next((col for col in candidatos if col in df.columns), None)


def extraer_rango_fechas(rango_fechas):
    if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
    else:
        fecha_inicio = rango_fechas
        fecha_fin = rango_fechas
    if fecha_inicio is None or fecha_fin is None:
        return None, None
    fecha_inicio = pd.Timestamp(fecha_inicio)
    fecha_fin = pd.Timestamp(fecha_fin) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    return fecha_inicio, fecha_fin

# =========================================================
# RESÚMENES
# =========================================================

def crear_resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    evaluable = df[
        df["fecha_recepcion_final"].notna()
        & df["performance_tat_estado"].isin(ESTADOS_EVALUABLES)
    ].copy()
    if evaluable.empty:
        return pd.DataFrame()

    resumen = (
        evaluable.groupby(["periodo_fecha", "periodo_label", "anio", "performance_tat_estado"], dropna=False)
        .size()
        .reset_index(name="cantidad")
    )
    tabla = resumen.pivot_table(
        index=["periodo_fecha", "periodo_label", "anio"],
        columns="performance_tat_estado",
        values="cantidad",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for estado in ESTADOS_EVALUABLES:
        if estado not in tabla.columns:
            tabla[estado] = 0

    tabla["Total"] = tabla["Cumple"] + tabla["No cumple"]
    tabla["% Cumple"] = np.where(tabla["Total"] > 0, tabla["Cumple"] / tabla["Total"] * 100, 0)
    tabla["% No cumple"] = np.where(tabla["Total"] > 0, tabla["No cumple"] / tabla["Total"] * 100, 0)
    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


def completar_meses(tabla: pd.DataFrame, fecha_inicio, fecha_fin) -> pd.DataFrame:
    if fecha_inicio is None or fecha_fin is None:
        return tabla
    periodos = pd.period_range(start=pd.Timestamp(fecha_inicio).to_period("M"), end=pd.Timestamp(fecha_fin).to_period("M"), freq="M")
    base = pd.DataFrame({"periodo_fecha": periodos.to_timestamp()})
    base["anio"] = base["periodo_fecha"].dt.year
    base["periodo_label"] = base["periodo_fecha"].dt.month.map(MESES_NOMBRE)
    salida = base.merge(tabla, on=["periodo_fecha", "periodo_label", "anio"], how="left")
    for col in ["Cumple", "No cumple", "Total", "% Cumple", "% No cumple"]:
        salida[col] = salida[col].fillna(0) if col in salida.columns else 0
    return salida.sort_values("periodo_fecha").reset_index(drop=True)


def detectar_columnas_etapas(df: pd.DataFrame):
    return [
        {"Etapa": "Lib Solped", "col_perf": "performance_liberacion_solped", "col_dias": "dias_liberacion_solped", "Regla": "• Nacional e Internacional < 2"},
        {"Etapa": "Comprador", "col_perf": "performance_comprador", "col_dias": "dias_comprador", "Regla": "• Nacional e Internacional < 11"},
        {"Etapa": "Prov", "col_perf": "performance_proveedor", "col_dias": "dias_proveedor", "Regla": "• Nacional < 20<br>• Internacional <60"},
        {"Etapa": "Logística", "col_perf": "performance_logistica", "col_dias": "dias_logistica", "Regla": "• Nacional e Internacional < 10"},
    ]


def crear_resumen_etapas(df: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for etapa in detectar_columnas_etapas(df):
        col_perf = etapa["col_perf"]
        col_dias = etapa["col_dias"]
        if col_perf not in df.columns or col_dias not in df.columns:
            filas.append({**etapa, "Estado": "Faltan columnas", "Cumple": 0, "No cumple": 0, "Total": 0, "% Cumple": 0, "% No cumple": 0, "Promedio días": 0})
            continue

        estado = df[col_perf].apply(normalizar_estado)
        evaluable = estado[estado.isin(ESTADOS_EVALUABLES)]
        cumple = int(evaluable.eq("Cumple").sum())
        no_cumple = int(evaluable.eq("No cumple").sum())
        total = cumple + no_cumple
        pct_cumple = cumple / total * 100 if total else 0
        dias = pd.to_numeric(df[col_dias], errors="coerce")
        dias = dias[dias > 0]
        promedio = float(dias.mean()) if not dias.empty else 0
        filas.append({**etapa, "Estado": "OK", "Cumple": cumple, "No cumple": no_cumple, "Total": total, "% Cumple": round(pct_cumple, 2), "% No cumple": round(100 - pct_cumple if total else 0, 2), "Promedio días": round(promedio, 1)})
    return pd.DataFrame(filas)

# =========================================================
# GRÁFICOS
# =========================================================

def tema_powerbi(chart):
    return chart.configure_view(strokeWidth=0).configure_axis(
        labelColor=COLOR_TEXTO_SUAVE,
        titleColor=COLOR_TEXTO_SUAVE,
        gridColor="#BFBFBF",
        gridDash=[1, 3],
        domain=False,
        tickColor="#BFBFBF",
    ).configure_legend(
        orient="bottom",
        labelColor=COLOR_TEXTO_SUAVE,
        title=None,
        symbolType="circle",
    )


def grafico_stacked_mensual(tabla: pd.DataFrame, mostrar_meta: bool = False, meta: int = 65):
    if tabla.empty or tabla["Total"].sum() == 0:
        st.warning("No hay datos evaluables para graficar.")
        return

    data = tabla.copy().sort_values("periodo_fecha")
    data["orden"] = np.arange(len(data))
    data["mes"] = data["periodo_label"].astype(str)
    data["anio_label"] = data["anio"].astype("Int64").astype(str)
    data["pct_cumple_label"] = data["% Cumple"].map(lambda x: f"{x:.2f}%".replace(".", ","))
    data["pct_no_cumple_label"] = data["% No cumple"].map(lambda x: f"{x:.2f}%".replace(".", ","))

    plot = data.melt(
        id_vars=["periodo_fecha", "mes", "anio", "anio_label", "orden", "pct_cumple_label", "pct_no_cumple_label", "Cumple", "No cumple", "Total"],
        value_vars=["% Cumple", "% No cumple"],
        var_name="Estado_pct",
        value_name="Porcentaje",
    )
    plot["Estado"] = np.where(plot["Estado_pct"].eq("% Cumple"), "Cumple", "No cumple")
    plot["label"] = np.where(plot["Estado"].eq("Cumple"), plot["pct_cumple_label"], plot["pct_no_cumple_label"])
    plot["centro_y"] = np.where(plot["Estado"].eq("Cumple"), plot["Porcentaje"] / 2, data.loc[plot.index % len(data), "% Cumple"].to_numpy() + plot["Porcentaje"] / 2)

    orden_meses = data["mes"].tolist()

    barras = alt.Chart(plot).mark_bar(size=48).encode(
        x=alt.X("mes:N", title=None, sort=orden_meses, axis=alt.Axis(labelAngle=0, labelFontSize=11)),
        y=alt.Y("Porcentaje:Q", title=None, stack="zero", scale=alt.Scale(domain=[0, 100]), axis=alt.Axis(values=[0, 50, 100], format=".0f")),
        color=alt.Color("Estado:N", scale=alt.Scale(domain=["Cumple", "No cumple"], range=[COLOR_CUMPLE, COLOR_NO_CUMPLE]), legend=alt.Legend(title=None)),
        order=alt.Order("Estado:N", sort="ascending"),
        tooltip=[
            alt.Tooltip("mes:N", title="Mes"),
            alt.Tooltip("anio_label:N", title="Año"),
            alt.Tooltip("Estado:N", title="Estado"),
            alt.Tooltip("Porcentaje:Q", title="Porcentaje", format=".2f"),
            alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f"),
        ],
    )

    labels = alt.Chart(plot).mark_text(fontSize=11, fontWeight="bold", color="white", baseline="middle").encode(
        x=alt.X("mes:N", sort=orden_meses),
        y=alt.Y("centro_y:Q", scale=alt.Scale(domain=[0, 100])),
        text="label:N",
    )

    chart = barras + labels

    if mostrar_meta:
        meta_df = pd.DataFrame({"meta": [meta], "texto": [f"{meta}%"]})
        linea = alt.Chart(meta_df).mark_rule(color=COLOR_META, strokeDash=[6, 5], strokeWidth=2).encode(y="meta:Q")
        texto_meta = alt.Chart(meta_df).mark_text(align="left", dx=4, dy=-6, fontSize=11, color=COLOR_META, fontWeight="bold").encode(
            x=alt.value(12), y="meta:Q", text="texto:N"
        )
        chart = chart + linea + texto_meta

    st.altair_chart(tema_powerbi(chart.properties(height=155)), use_container_width=True)


def grafico_donut_etapa(cumple: int, no_cumple: int):
    total = cumple + no_cumple
    if total <= 0:
        data = pd.DataFrame({"Estado": ["Sin datos"], "Cantidad": [1], "Porcentaje": [0.0], "Etiqueta": ["Sin datos"]})
    else:
        pct_c = cumple / total * 100
        pct_n = no_cumple / total * 100
        data = pd.DataFrame({
            "Estado": ["Cumple", "No Cumple"],
            "Cantidad": [cumple, no_cumple],
            "Porcentaje": [pct_c, pct_n],
            "Etiqueta": [f"Cumple\n{pct_c:.0f}%", f"No Cumple\n{pct_n:.0f}%"],
        })

    donut = alt.Chart(data).mark_arc(innerRadius=46, outerRadius=70).encode(
        theta=alt.Theta("Cantidad:Q"),
        color=alt.Color("Estado:N", scale=alt.Scale(domain=["Cumple", "No Cumple", "Sin datos"], range=[COLOR_CUMPLE, COLOR_NO_CUMPLE, "#BDBDBD"]), legend=alt.Legend(title=None, orient="bottom")),
        tooltip=[alt.Tooltip("Estado:N"), alt.Tooltip("Cantidad:Q", format=",.0f"), alt.Tooltip("Porcentaje:Q", format=".1f")],
    )

    # Etiquetas externas discretas, para parecerse al gráfico de dona de Power BI.
    etiquetas = alt.Chart(data[data["Estado"].ne("Sin datos")]).mark_text(fontSize=10, color=COLOR_TEXTO_SUAVE).encode(
        theta=alt.Theta("Cantidad:Q", stack=True),
        radius=alt.value(92),
        text="Etiqueta:N",
    )

    st.altair_chart(tema_powerbi((donut + etiquetas).properties(height=165)), use_container_width=True)


def render_etapa_card(row: pd.Series):
    st.markdown(f"<div class='stage-rule'>{row.get('Regla', '')}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='stage-title'>Cumplimiento {row.get('Etapa', '')}</div>", unsafe_allow_html=True)
    grafico_donut_etapa(int(row.get("Cumple", 0)), int(row.get("No cumple", 0)))
    st.markdown(f"<div class='stage-kpi'>{row.get('Promedio días', 0):.0f}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='stage-kpi-caption'>Promedio de Dx {row.get('Etapa', '')}</div>", unsafe_allow_html=True)

# =========================================================
# APP
# =========================================================

aplicar_estilos()

# Fila superior: logo + filtros horizontales
col_logo, col_sistema, col_centro, col_tat = st.columns([1.55, 1.55, 1.55, 1.55], gap="large")
with col_logo:
    render_logo_y_titulo()

with col_sistema:
    st.markdown("<div class='filter-label'>Archivo</div>", unsafe_allow_html=True)
    archivo = st.file_uploader("Archivo", type=["parquet", "xlsx", "csv"], label_visibility="collapsed")

with st.sidebar:
    st.header("Configuración")
    separador_label = st.selectbox("Separador CSV", options=["Automático", ";", ",", "\t"], index=0)
    mostrar_meta = st.checkbox("Mostrar línea de referencia 65%", value=False)
    mostrar_meses_sin_datos = st.checkbox("Mostrar meses sin datos", value=False)
    filtrar_tat_evaluable_etapas = st.checkbox("Etapas: usar solo TAT evaluable", value=True)
    mostrar_tablas = st.checkbox("Mostrar tablas de detalle", value=False)

if archivo is None:
    with col_centro:
        st.markdown("<div class='filter-label'>Centro</div>", unsafe_allow_html=True)
        st.selectbox("Centro", options=["Todas"], label_visibility="collapsed")
    with col_tat:
        st.markdown("<div class='filter-label'>Performance TAT</div>", unsafe_allow_html=True)
        st.multiselect("Performance TAT", options=["Cumple", "No cumple"], default=[], label_visibility="collapsed")
    st.info("Carga el archivo para visualizar el dashboard.")
    st.stop()

try:
    df_original = leer_archivo_cache(archivo.getvalue(), archivo.name, separador_label)
    df = preparar_dataframe(df_original)
except Exception as e:
    st.error("Error al cargar o preparar el archivo.")
    st.exception(e)
    st.stop()

col_centro_nombre = detectar_columna(df, ["Centro - ME5A", "Centro", "Centro - NME80FN"])
col_sistema_nombre = detectar_columna(df, ["sistema", "Sistema", "Origen", "origen"])
fechas_validas = df["fecha_recepcion_final"].dropna()
if fechas_validas.empty:
    st.error("No hay fechas válidas en `fecha_recepcion_final`.")
    st.stop()

# Filtros que dependen de datos, ubicados en la misma franja superior
with col_sistema:
    if col_sistema_nombre:
        sistemas = df[col_sistema_nombre].dropna().astype(str).str.strip().sort_values().unique().tolist()
        sistema_sel = st.selectbox("Sistema", options=["Todas"] + sistemas, index=0, label_visibility="visible")
    else:
        sistema_sel = "Todas"
        st.selectbox("Sistema", options=["Todas"], index=0)

with col_centro:
    if col_centro_nombre:
        centros = df[col_centro_nombre].dropna().astype(str).str.strip().sort_values().unique().tolist()
        centro_default = centros.index("E002") + 1 if "E002" in centros else 0
        centro_sel = st.selectbox("Centro", options=["Todas"] + centros, index=centro_default)
    else:
        centro_sel = "Todas"
        st.selectbox("Centro", options=["Todas"], index=0)

with col_tat:
    estados_tat = ["Cumple", "No cumple", "No aplica", "Sin datos / En proceso", "Sin información"]
    tat_sel = st.multiselect("Performance TAT", options=estados_tat, default=[])

fecha_cols = st.columns([1.65, 1, 1, 3.35])
with fecha_cols[0]:
    rango_fechas = st.date_input(
        "",
        value=(fechas_validas.min().date(), fechas_validas.max().date()),
        min_value=fechas_validas.min().date(),
        max_value=fechas_validas.max().date(),
        label_visibility="collapsed",
    )

fecha_inicio, fecha_fin = extraer_rango_fechas(rango_fechas)
if fecha_inicio is None or fecha_fin is None or fecha_inicio > fecha_fin:
    st.warning("Selecciona un rango de fechas válido.")
    st.stop()

# Aplicar filtros
df_filtrado = df.copy()
if col_sistema_nombre and sistema_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_sistema_nombre].astype(str).str.strip().eq(str(sistema_sel).strip())].copy()
if col_centro_nombre and centro_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado[col_centro_nombre].astype(str).str.strip().eq(str(centro_sel).strip())].copy()
if tat_sel:
    df_filtrado = df_filtrado[df_filtrado["performance_tat_estado"].isin(tat_sel)].copy()

df_filtrado = df_filtrado[
    df_filtrado["fecha_recepcion_final"].notna()
    & df_filtrado["fecha_recepcion_final"].between(fecha_inicio, fecha_fin)
].copy()

tabla_mensual = crear_resumen_mensual(df_filtrado)
if mostrar_meses_sin_datos:
    tabla_mensual = completar_meses(tabla_mensual, fecha_inicio, fecha_fin)

df_etapas = df_filtrado.copy()
if filtrar_tat_evaluable_etapas:
    df_etapas = df_etapas[df_etapas["performance_tat_estado"].isin(ESTADOS_EVALUABLES)].copy()
tabla_etapas = crear_resumen_etapas(df_etapas)

# Gráfico principal mensual
st.markdown("<div class='small-divider'></div>", unsafe_allow_html=True)
grafico_stacked_mensual(tabla_mensual, mostrar_meta=mostrar_meta, meta=65)

# Reglas globales como en la captura
st.markdown(
    """
    <div class='section-note'>
        Nacional &lt;40 días<br>
        Internacional &lt;70 días
    </div>
    """,
    unsafe_allow_html=True,
)

# Tarjetas de dona en 4 columnas
cols = st.columns(4, gap="large")
for idx, (_, row) in enumerate(tabla_etapas.iterrows()):
    if idx >= 4:
        break
    with cols[idx]:
        render_etapa_card(row)

# Detalle opcional
if mostrar_tablas:
    st.markdown("<div class='small-divider'></div>", unsafe_allow_html=True)
    st.subheader("Detalle")
    c1, c2 = st.columns(2)
    with c1:
        st.caption("Resumen mensual")
        st.dataframe(tabla_mensual, use_container_width=True, hide_index=True)
    with c2:
        st.caption("Resumen por etapa")
        st.dataframe(tabla_etapas, use_container_width=True, hide_index=True)

    st.caption(f"Datos filtrados: {len(df_filtrado):,} registros")
    st.dataframe(df_filtrado.head(500), use_container_width=True, hide_index=True)

