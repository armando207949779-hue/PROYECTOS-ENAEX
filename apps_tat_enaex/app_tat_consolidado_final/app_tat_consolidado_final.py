# app_mejorado.py

import base64
import io
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Dashboard Performance TAT",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent
LOGO_CANDIDATOS = [
    BASE_DIR / "assets" / "logo.svg",
    BASE_DIR / "logo.svg",
    BASE_DIR.parent / "assets" / "logo.svg",
]

ESTADOS_EVALUABLES = ["Cumple", "No cumple"]
COLOR_CUMPLE = "#1F7A4D"
COLOR_NO_CUMPLE = "#D64550"
COLOR_NEUTRO = "#667085"
COLOR_FONDO = "#F6F7FB"
COLOR_TEXTO = "#1F2937"

MESES_NOMBRE = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic",
}


# =========================================================
# ESTILO VISUAL
# =========================================================

def aplicar_estilos():
    st.markdown(
        f"""
        <style>
            .main {{
                background: {COLOR_FONDO};
            }}
            div[data-testid="stMetric"] {{
                background: #FFFFFF;
                border: 1px solid #EAECF0;
                padding: 1.05rem 1.1rem;
                border-radius: 16px;
                box-shadow: 0 8px 22px rgba(16, 24, 40, 0.05);
            }}
            div[data-testid="stMetric"] label {{
                color: #667085;
                font-weight: 600;
            }}
            div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
                color: {COLOR_TEXTO};
                font-size: 1.65rem;
                font-weight: 800;
            }}
            .block-container {{
                padding-top: 1.6rem;
                padding-bottom: 2.2rem;
            }}
            .dashboard-card {{
                background: #FFFFFF;
                border: 1px solid #EAECF0;
                border-radius: 18px;
                padding: 1rem 1.1rem;
                box-shadow: 0 8px 22px rgba(16, 24, 40, 0.05);
            }}
            .section-title {{
                color: {COLOR_TEXTO};
                font-size: 1.25rem;
                font-weight: 800;
                margin-top: 0.5rem;
                margin-bottom: 0.25rem;
            }}
            .section-caption {{
                color: #667085;
                font-size: 0.92rem;
                margin-bottom: 0.9rem;
            }}
            .top-header {{
                background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
                border: 1px solid #EAECF0;
                border-radius: 20px;
                padding: 1.25rem 1.4rem;
                margin-bottom: 1.2rem;
                box-shadow: 0 8px 22px rgba(16, 24, 40, 0.05);
            }}
            .top-title {{
                color: {COLOR_TEXTO};
                font-size: 2rem;
                line-height: 1.1;
                font-weight: 900;
                margin: 0;
            }}
            .top-subtitle {{
                color: #667085;
                margin-top: 0.35rem;
                font-size: 1rem;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_logo(ancho: int = 170):
    for ruta in LOGO_CANDIDATOS:
        if ruta.exists():
            suffix = ruta.suffix.lower()
            raw = ruta.read_bytes()
            encoded = base64.b64encode(raw).decode("utf-8")

            if suffix == ".svg":
                mime = "image/svg+xml"
            elif suffix in [".png"]:
                mime = "image/png"
            elif suffix in [".jpg", ".jpeg"]:
                mime = "image/jpeg"
            else:
                continue

            st.markdown(
                f"""
                <div style="text-align:center; margin: 0.2rem 0 0.9rem 0;">
                    <img src="data:{mime};base64,{encoded}" width="{ancho}">
                </div>
                """,
                unsafe_allow_html=True,
            )
            return

    st.caption("Logo no encontrado. Coloca el archivo en `assets/logo.svg`, `assets/logo.png` o junto a este `app.py`.")


def render_header():
    st.markdown(
        """
        <div class="top-header">
            <p class="top-title">Dashboard Performance TAT</p>
            <div class="top-subtitle">Seguimiento ejecutivo de cumplimiento mensual, etapas e incumplimientos TAT.</div>
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
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
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

    columnas_requeridas = ["fecha_recepcion_final", "performance_tat_total"]
    faltantes = [col for col in columnas_requeridas if col not in df.columns]

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
        df["mes_nombre"].astype(str) + " " + df["anio"].astype("Int64").astype(str),
        pd.NA,
    )

    return df


def detectar_columna_centro(df: pd.DataFrame):
    posibles = ["Centro - ME5A", "Centro", "Centro - NME80FN"]
    return next((col for col in posibles if col in df.columns), None)


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
        evaluable.groupby(["periodo_fecha", "periodo_label", "performance_tat_estado"], dropna=False)
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=["periodo_fecha", "periodo_label"],
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
    tabla["periodo_label"] = tabla["periodo_fecha"].dt.month.map(MESES_NOMBRE) + " " + tabla["periodo_fecha"].dt.year.astype(str)

    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


def completar_meses(tabla: pd.DataFrame, fecha_inicio, fecha_fin) -> pd.DataFrame:
    if fecha_inicio is None or fecha_fin is None:
        return tabla

    periodos = pd.period_range(start=pd.Timestamp(fecha_inicio).to_period("M"), end=pd.Timestamp(fecha_fin).to_period("M"), freq="M")
    base = pd.DataFrame({"periodo_fecha": periodos.to_timestamp()})
    base["periodo_label"] = base["periodo_fecha"].dt.month.map(MESES_NOMBRE) + " " + base["periodo_fecha"].dt.year.astype(str)

    salida = base.merge(tabla, on=["periodo_fecha", "periodo_label"], how="left")
    for col in ["Cumple", "No cumple", "Total", "% Cumple", "% No cumple"]:
        salida[col] = salida[col].fillna(0) if col in salida.columns else 0

    return salida.sort_values("periodo_fecha").reset_index(drop=True)


def detectar_columnas_etapas(df: pd.DataFrame):
    return [
        {
            "Etapa": "Lib. SolPed",
            "col_perf": "performance_liberacion_solped",
            "col_dias": "dias_liberacion_solped",
            "Regla": "Solicitud → liberación",
        },
        {
            "Etapa": "Comprador",
            "col_perf": "performance_comprador",
            "col_dias": "dias_comprador",
            "Regla": "Liberación → pedido",
        },
        {
            "Etapa": "Proveedor",
            "col_perf": "performance_proveedor",
            "col_dias": "dias_proveedor",
            "Regla": "Pedido → facturación",
        },
        {
            "Etapa": "Logística",
            "col_perf": "performance_logistica",
            "col_dias": "dias_logistica",
            "Regla": "Facturación → recepción",
        },
    ]


def crear_resumen_etapas(df: pd.DataFrame) -> pd.DataFrame:
    filas = []

    for etapa in detectar_columnas_etapas(df):
        col_perf = etapa["col_perf"]
        col_dias = etapa["col_dias"]

        if col_perf not in df.columns or col_dias not in df.columns:
            filas.append({**etapa, "Estado": "Faltan columnas", "Cumple": 0, "No cumple": 0, "Total": 0, "% Cumple": 0, "Promedio días": 0})
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

        filas.append({
            **etapa,
            "Estado": "OK",
            "Cumple": cumple,
            "No cumple": no_cumple,
            "Total": total,
            "% Cumple": round(pct_cumple, 2),
            "% No cumple": round(100 - pct_cumple if total else 0, 2),
            "Promedio días": round(promedio, 2),
        })

    return pd.DataFrame(filas)


def crear_resumen_rangos_incumplimiento(df: pd.DataFrame) -> pd.DataFrame:
    if "rango_incumplimiento_tat" not in df.columns:
        return pd.DataFrame()

    orden = ["Sin incumplimiento", "0-5 días", "6-15 días", "16-30 días", "Mayor a un mes", "Sin datos"]
    salida = (
        df["rango_incumplimiento_tat"].fillna("Sin datos")
        .value_counts()
        .rename_axis("Rango")
        .reset_index(name="Cantidad")
    )
    salida["Rango"] = pd.Categorical(salida["Rango"], categories=orden, ordered=True)
    salida = salida.sort_values("Rango")
    salida["%"] = np.where(salida["Cantidad"].sum() > 0, salida["Cantidad"] / salida["Cantidad"].sum() * 100, 0)
    return salida


# =========================================================
# GRÁFICOS
# =========================================================

def tema_base(chart):
    return chart.configure_view(strokeWidth=0).configure_axis(
        labelColor=COLOR_NEUTRO,
        titleColor=COLOR_NEUTRO,
        gridColor="#EEF2F6",
        domain=False,
    ).configure_legend(
        labelColor=COLOR_NEUTRO,
        titleColor=COLOR_NEUTRO,
        orient="bottom",
    )


def grafico_cumplimiento_mensual(tabla: pd.DataFrame):
    if tabla.empty or tabla["Total"].sum() == 0:
        st.warning("No hay datos evaluables para graficar.")
        return

    data = tabla.copy()
    data["% Cumple"] = data["% Cumple"].round(1)
    data["texto"] = data["% Cumple"].map(lambda x: f"{x:.1f}%")

    barras = alt.Chart(data).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8).encode(
        x=alt.X("periodo_label:N", title=None, sort=list(data["periodo_label"]), axis=alt.Axis(labelAngle=0)),
        y=alt.Y("% Cumple:Q", title="% cumplimiento", scale=alt.Scale(domain=[0, 100])),
        color=alt.value(COLOR_CUMPLE),
        tooltip=[
            alt.Tooltip("periodo_label:N", title="Mes"),
            alt.Tooltip("Cumple:Q", title="Cumple", format=",.0f"),
            alt.Tooltip("No cumple:Q", title="No cumple", format=",.0f"),
            alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f"),
            alt.Tooltip("% Cumple:Q", title="% Cumple", format=".1f"),
        ],
    )

    linea = alt.Chart(data).mark_line(point=alt.OverlayMarkDef(size=80), strokeWidth=3).encode(
        x=alt.X("periodo_label:N", sort=list(data["periodo_label"])),
        y=alt.Y("% Cumple:Q"),
        color=alt.value("#2F5597"),
    )

    textos = alt.Chart(data).mark_text(dy=-12, fontSize=12, fontWeight="bold", color=COLOR_TEXTO).encode(
        x=alt.X("periodo_label:N", sort=list(data["periodo_label"])),
        y=alt.Y("% Cumple:Q"),
        text="texto:N",
    )

    chart = (barras + linea + textos).properties(height=390)
    st.altair_chart(tema_base(chart), use_container_width=True)


def grafico_cumple_no_cumple_mensual(tabla: pd.DataFrame):
    if tabla.empty or tabla["Total"].sum() == 0:
        return

    data = tabla.melt(
        id_vars=["periodo_label", "periodo_fecha"],
        value_vars=["Cumple", "No cumple"],
        var_name="Estado",
        value_name="Cantidad",
    )
    orden = tabla.sort_values("periodo_fecha")["periodo_label"].tolist()

    chart = alt.Chart(data).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X("periodo_label:N", title=None, sort=orden, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Cantidad:Q", title="Registros"),
        color=alt.Color(
            "Estado:N",
            scale=alt.Scale(domain=["Cumple", "No cumple"], range=[COLOR_CUMPLE, COLOR_NO_CUMPLE]),
            title=None,
        ),
        tooltip=[
            alt.Tooltip("periodo_label:N", title="Mes"),
            alt.Tooltip("Estado:N", title="Estado"),
            alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
        ],
    ).properties(height=330)

    st.altair_chart(tema_base(chart), use_container_width=True)


def grafico_etapas(tabla_etapas: pd.DataFrame):
    data = tabla_etapas[tabla_etapas["Estado"].eq("OK")].copy()
    if data.empty:
        st.warning("No hay columnas de etapas disponibles para graficar.")
        return

    chart = alt.Chart(data).mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8).encode(
        y=alt.Y("Etapa:N", title=None, sort="-x"),
        x=alt.X("% Cumple:Q", title="% cumplimiento", scale=alt.Scale(domain=[0, 100])),
        color=alt.value(COLOR_CUMPLE),
        tooltip=[
            alt.Tooltip("Etapa:N", title="Etapa"),
            alt.Tooltip("% Cumple:Q", title="% Cumple", format=".1f"),
            alt.Tooltip("Cumple:Q", title="Cumple", format=",.0f"),
            alt.Tooltip("No cumple:Q", title="No cumple", format=",.0f"),
            alt.Tooltip("Promedio días:Q", title="Promedio días", format=".1f"),
        ],
    ).properties(height=260)

    texto = alt.Chart(data).mark_text(align="left", dx=6, fontWeight="bold", color=COLOR_TEXTO).encode(
        y=alt.Y("Etapa:N", sort="-x"),
        x=alt.X("% Cumple:Q"),
        text=alt.Text("% Cumple:Q", format=".1f"),
    )

    st.altair_chart(tema_base(chart + texto), use_container_width=True)


def grafico_rangos_incumplimiento(tabla_rangos: pd.DataFrame):
    if tabla_rangos.empty:
        return

    data = tabla_rangos.copy()
    data["Rango"] = data["Rango"].astype(str)

    chart = alt.Chart(data).mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8).encode(
        y=alt.Y("Rango:N", title=None, sort=None),
        x=alt.X("Cantidad:Q", title="Registros"),
        color=alt.value("#2F5597"),
        tooltip=[
            alt.Tooltip("Rango:N", title="Rango"),
            alt.Tooltip("Cantidad:Q", title="Cantidad", format=",.0f"),
            alt.Tooltip("%:Q", title="%", format=".1f"),
        ],
    ).properties(height=280)

    st.altair_chart(tema_base(chart), use_container_width=True)


def crear_donut_global(cumple: int, no_cumple: int):
    total = cumple + no_cumple
    if total == 0:
        data = pd.DataFrame({"Estado": ["Sin datos"], "Cantidad": [1]})
        pct = 0
    else:
        data = pd.DataFrame({"Estado": ["Cumple", "No cumple"], "Cantidad": [cumple, no_cumple]})
        pct = cumple / total * 100

    donut = alt.Chart(data).mark_arc(innerRadius=72, outerRadius=105, cornerRadius=5).encode(
        theta=alt.Theta("Cantidad:Q"),
        color=alt.Color(
            "Estado:N",
            scale=alt.Scale(domain=["Cumple", "No cumple", "Sin datos"], range=[COLOR_CUMPLE, COLOR_NO_CUMPLE, "#D0D5DD"]),
            title=None,
        ),
        tooltip=[alt.Tooltip("Estado:N"), alt.Tooltip("Cantidad:Q", format=",.0f")],
    )

    centro = alt.Chart(pd.DataFrame({"texto": [f"{pct:.1f}%"], "sub": ["Cumple"]})).mark_text(
        fontSize=31, fontWeight="bold", color=COLOR_TEXTO, dy=-6
    ).encode(text="texto:N")

    sub = alt.Chart(pd.DataFrame({"texto": ["Cumple"]})).mark_text(
        fontSize=12, color=COLOR_NEUTRO, dy=23
    ).encode(text="texto:N")

    st.altair_chart(tema_base((donut + centro + sub).properties(height=285)), use_container_width=True)


# =========================================================
# APP
# =========================================================

aplicar_estilos()
mostrar_logo()
render_header()

with st.sidebar:
    st.header("Filtros")

    separador_label = st.selectbox(
        "Separador CSV",
        options=["Automático", ";", ",", "\t"],
        index=0,
        help="Solo aplica cuando cargas archivos CSV.",
    )

    archivo = st.file_uploader("Carga el archivo", type=["parquet", "xlsx", "csv"])

    st.divider()
    st.caption("Carga un archivo para activar los filtros de centro y fecha.")

if archivo is None:
    st.info("Carga un archivo `.parquet`, `.xlsx` o `.csv` para comenzar.")
    st.stop()

try:
    df_original = leer_archivo_cache(archivo.getvalue(), archivo.name, separador_label)
    df = preparar_dataframe(df_original)
except Exception as e:
    st.error("Error al cargar o preparar el archivo.")
    st.exception(e)
    st.stop()

col_centro = detectar_columna_centro(df)
fechas_validas = df["fecha_recepcion_final"].dropna()

if fechas_validas.empty:
    st.error("No hay fechas válidas en `fecha_recepcion_final`.")
    st.stop()

with st.sidebar:
    if col_centro:
        centros = df[col_centro].dropna().astype(str).str.strip().sort_values().unique().tolist()
        default_centro = ["E002"] if "E002" in centros else []
        centros_sel = st.multiselect("Centro", options=centros, default=default_centro, help="Si no seleccionas centro, se muestran todos.")
    else:
        centros_sel = []
        st.warning("No se encontró columna de centro.")

    rango_fechas = st.date_input(
        "Rango fecha recepción",
        value=(fechas_validas.min().date(), fechas_validas.max().date()),
        min_value=fechas_validas.min().date(),
        max_value=fechas_validas.max().date(),
    )

    mostrar_meses_sin_datos = st.checkbox("Mostrar meses sin datos", value=False)
    filtrar_tat_evaluable_etapas = st.checkbox("Etapas: usar solo TAT evaluable", value=True)
    mostrar_tabla = st.checkbox("Mostrar datos filtrados", value=False)

fecha_inicio, fecha_fin = extraer_rango_fechas(rango_fechas)
if fecha_inicio is None or fecha_fin is None or fecha_inicio > fecha_fin:
    st.warning("Selecciona un rango de fechas válido.")
    st.stop()

df_filtrado = df.copy()

if col_centro and centros_sel:
    df_filtrado = df_filtrado[df_filtrado[col_centro].astype(str).str.strip().isin([str(x).strip() for x in centros_sel])].copy()

df_filtrado = df_filtrado[
    df_filtrado["fecha_recepcion_final"].notna()
    & df_filtrado["fecha_recepcion_final"].between(fecha_inicio, fecha_fin)
].copy()

cumple = int(df_filtrado["performance_tat_estado"].eq("Cumple").sum())
no_cumple = int(df_filtrado["performance_tat_estado"].eq("No cumple").sum())
total_filas = int(len(df_filtrado))
total_evaluable = cumple + no_cumple
no_evaluable = total_filas - total_evaluable
pct_cumple = cumple / total_evaluable * 100 if total_evaluable else 0
pct_no_cumple = no_cumple / total_evaluable * 100 if total_evaluable else 0

tabla_mensual = crear_resumen_mensual(df_filtrado)
if mostrar_meses_sin_datos:
    tabla_mensual = completar_meses(tabla_mensual, fecha_inicio, fecha_fin)

df_etapas = df_filtrado.copy()
if filtrar_tat_evaluable_etapas:
    df_etapas = df_etapas[df_etapas["performance_tat_estado"].isin(ESTADOS_EVALUABLES)].copy()

tabla_etapas = crear_resumen_etapas(df_etapas)
tabla_rangos = crear_resumen_rangos_incumplimiento(df_filtrado)

# =========================================================
# DASHBOARD
# =========================================================

st.markdown('<div class="section-title">Indicadores generales</div>', unsafe_allow_html=True)
st.markdown('<div class="section-caption">Los porcentajes se calculan sobre registros evaluables: Cumple + No cumple. No se usa meta fija ni línea de 65%.</div>', unsafe_allow_html=True)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Filas filtradas", f"{total_filas:,}")
k2.metric("Evaluables", f"{total_evaluable:,}")
k3.metric("Cumple", f"{cumple:,}")
k4.metric("No cumple", f"{no_cumple:,}")
k5.metric("% Cumple", f"{pct_cumple:.1f}%")
k6.metric("No evaluables", f"{no_evaluable:,}")

st.divider()

g1, g2 = st.columns([2, 1], gap="large")

with g1:
    st.markdown('<div class="section-title">Cumplimiento mensual</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Evolución del porcentaje de cumplimiento mensual.</div>', unsafe_allow_html=True)
    grafico_cumplimiento_mensual(tabla_mensual)

with g2:
    st.markdown('<div class="section-title">Composición TAT</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Distribución global del resultado evaluable.</div>', unsafe_allow_html=True)
    crear_donut_global(cumple, no_cumple)

st.divider()

c1, c2 = st.columns(2, gap="large")

with c1:
    st.markdown('<div class="section-title">Cumple vs No cumple por mes</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Volumen mensual de registros evaluables.</div>', unsafe_allow_html=True)
    grafico_cumple_no_cumple_mensual(tabla_mensual)

with c2:
    st.markdown('<div class="section-title">Cumplimiento por etapa</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Ranking de etapas por porcentaje de cumplimiento.</div>', unsafe_allow_html=True)
    grafico_etapas(tabla_etapas)

st.divider()

r1, r2 = st.columns([1, 1], gap="large")

with r1:
    st.markdown('<div class="section-title">Rangos de incumplimiento TAT</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Clasificación del exceso de días contra el umbral TAT, si la columna existe.</div>', unsafe_allow_html=True)
    if tabla_rangos.empty:
        st.info("No existe la columna `rango_incumplimiento_tat` en el archivo cargado.")
    else:
        grafico_rangos_incumplimiento(tabla_rangos)

with r2:
    st.markdown('<div class="section-title">Resumen por etapa</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-caption">Detalle auditable de conteos, porcentajes y promedio de días.</div>', unsafe_allow_html=True)
    columnas_resumen_etapas = ["Etapa", "Regla", "Cumple", "No cumple", "Total", "% Cumple", "% No cumple", "Promedio días"]
    st.dataframe(tabla_etapas[[c for c in columnas_resumen_etapas if c in tabla_etapas.columns]], use_container_width=True, hide_index=True)

with st.expander("Resumen mensual detallado", expanded=False):
    columnas_mensual = ["periodo_fecha", "periodo_label", "Cumple", "No cumple", "Total", "% Cumple", "% No cumple"]
    if tabla_mensual.empty:
        st.info("No hay resumen mensual disponible.")
    else:
        st.dataframe(tabla_mensual[[c for c in columnas_mensual if c in tabla_mensual.columns]], use_container_width=True, hide_index=True)

if mostrar_tabla:
    with st.expander("Datos filtrados", expanded=True):
        st.caption(f"Mostrando primeras 500 filas de {len(df_filtrado):,} registros filtrados.")
        st.dataframe(df_filtrado.head(500), use_container_width=True, hide_index=True)

st.subheader("Descarga")

csv = df_filtrado.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
st.download_button(
    label="Descargar datos filtrados CSV",
    data=csv,
    file_name="performance_tat_filtrado.csv",
    mime="text/csv",
    use_container_width=True,
)
