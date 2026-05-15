# app.py

import io

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt


# =========================================================
# CONFIGURACIÓN
# =========================================================

st.set_page_config(
    page_title="Performance TAT",
    page_icon="📊",
    layout="wide"
)

COLORES_ESTADO = {
    "Cumple": "#5B5B5B",
    "No cumple": "#D94555"
}

ESTADOS_GRAFICO = ["Cumple", "No cumple"]

MESES_NOMBRE = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre"
}


# =========================================================
# FUNCIONES
# =========================================================

@st.cache_data(show_spinner="Leyendo archivo parquet...")
def cargar_parquet(archivo_bytes: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(archivo_bytes)
    return pd.read_parquet(buffer)


def normalizar_performance(valor):
    if pd.isna(valor):
        return "Sin información"

    texto = str(valor).strip().lower()

    if texto in ["cumple", "true", "1", "si", "sí", "yes"]:
        return "Cumple"

    if texto in ["no cumple", "false", "0", "no"]:
        return "No cumple"

    return "Sin información"


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    col_fecha = "fecha_recepcion_final"
    col_performance = "performance_tat_total"

    faltantes = []

    if col_fecha not in df.columns:
        faltantes.append(col_fecha)

    if col_performance not in df.columns:
        faltantes.append(col_performance)

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    df[col_fecha] = pd.to_datetime(
        df[col_fecha],
        errors="coerce"
    )

    df["performance_tat_estado"] = df[col_performance].apply(
        normalizar_performance
    )

    df["anio"] = df[col_fecha].dt.year
    df["mes_num"] = df[col_fecha].dt.month

    df["periodo_fecha"] = (
        df[col_fecha]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)

    df["periodo_label"] = np.where(
        df["anio"].notna() & df["mes_nombre"].notna(),
        df["mes_nombre"].astype(str)
        + " "
        + df["anio"].astype("Int64").astype(str),
        pd.NA
    )

    return df


def detectar_columna_centro(df: pd.DataFrame):
    posibles = [
        "Centro - ME5A",
        "Centro",
        "Centro - NME80FN"
    ]

    for col in posibles:
        if col in df.columns:
            return col

    return None


def crear_resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df[
        df["fecha_recepcion_final"].notna()
        & df["performance_tat_estado"].isin(ESTADOS_GRAFICO)
    ].copy()

    if df.empty:
        return pd.DataFrame()

    resumen = (
        df
        .groupby(
            [
                "periodo_fecha",
                "periodo_label",
                "anio",
                "mes_num",
                "mes_nombre",
                "performance_tat_estado"
            ],
            dropna=False
        )
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=[
            "periodo_fecha",
            "periodo_label",
            "anio",
            "mes_num",
            "mes_nombre"
        ],
        columns="performance_tat_estado",
        values="cantidad",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    for estado in ESTADOS_GRAFICO:
        if estado not in tabla.columns:
            tabla[estado] = 0

    tabla["Total"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Total"] > 0,
        tabla["Cumple"] / tabla["Total"] * 100,
        0
    )

    tabla["% No cumple"] = np.where(
        tabla["Total"] > 0,
        tabla["No cumple"] / tabla["Total"] * 100,
        0
    )

    tabla = tabla.sort_values("periodo_fecha").reset_index(drop=True)

    return tabla


def completar_meses(
    tabla: pd.DataFrame,
    fecha_inicio,
    fecha_fin
) -> pd.DataFrame:
    if fecha_inicio is None or fecha_fin is None:
        return tabla

    fecha_inicio_mes = pd.Timestamp(fecha_inicio).normalize()
    fecha_fin_mes = pd.Timestamp(fecha_fin).normalize()

    periodos = pd.period_range(
        start=fecha_inicio_mes.to_period("M"),
        end=fecha_fin_mes.to_period("M"),
        freq="M"
    )

    base = pd.DataFrame({
        "periodo_fecha": periodos.to_timestamp()
    })

    base["anio"] = base["periodo_fecha"].dt.year
    base["mes_num"] = base["periodo_fecha"].dt.month
    base["mes_nombre"] = base["mes_num"].map(MESES_NOMBRE)
    base["periodo_label"] = (
        base["mes_nombre"].astype(str)
        + " "
        + base["anio"].astype(str)
    )

    if tabla.empty:
        base["Cumple"] = 0
        base["No cumple"] = 0
        base["Total"] = 0
        base["% Cumple"] = 0
        base["% No cumple"] = 0

        return base.sort_values("periodo_fecha").reset_index(drop=True)

    salida = base.merge(
        tabla,
        on=[
            "periodo_fecha",
            "periodo_label",
            "anio",
            "mes_num",
            "mes_nombre"
        ],
        how="left"
    )

    for col in ["Cumple", "No cumple", "Total", "% Cumple", "% No cumple"]:
        if col in salida.columns:
            salida[col] = salida[col].fillna(0)

    salida = salida.sort_values("periodo_fecha").reset_index(drop=True)

    return salida


def crear_data_plot(
    tabla: pd.DataFrame,
    modo_y: str
) -> pd.DataFrame:
    if tabla.empty:
        return pd.DataFrame()

    data = []

    for _, row in tabla.iterrows():
        total = float(row.get("Total", 0) or 0)

        for estado in ESTADOS_GRAFICO:
            cantidad = float(row.get(estado, 0) or 0)

            porcentaje = (
                cantidad / total * 100
                if total > 0
                else 0
            )

            valor = cantidad if modo_y == "Recuento" else porcentaje

            data.append({
                "periodo_fecha": row["periodo_fecha"],
                "periodo_label": row["periodo_label"],
                "estado": estado,
                "valor": valor,
                "cantidad": cantidad,
                "porcentaje": porcentaje,
                "total": total,
                "orden_estado": 1 if estado == "Cumple" else 2
            })

    return pd.DataFrame(data)


def grafico_performance_tat(
    df_plot: pd.DataFrame,
    modo_y: str
):
    if df_plot.empty:
        st.warning("No hay datos evaluables para graficar.")
        return

    orden_periodos = (
        df_plot[["periodo_label", "periodo_fecha"]]
        .drop_duplicates()
        .sort_values("periodo_fecha")["periodo_label"]
        .tolist()
    )

    titulo_y = "Porcentaje" if modo_y == "Porcentaje" else "Recuento"

    barras = (
        alt.Chart(df_plot)
        .mark_bar()
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_periodos,
                title="Mes recepción",
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap=False
                )
            ),
            y=alt.Y(
                "valor:Q",
                stack="zero",
                title=titulo_y,
                scale=alt.Scale(domain=[0, 100])
                if modo_y == "Porcentaje"
                else alt.Undefined
            ),
            color=alt.Color(
                "estado:N",
                scale=alt.Scale(
                    domain=ESTADOS_GRAFICO,
                    range=[
                        COLORES_ESTADO[e]
                        for e in ESTADOS_GRAFICO
                    ]
                ),
                legend=alt.Legend(title="")
            ),
            order=alt.Order(
                "orden_estado:Q",
                sort="ascending"
            ),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes"),
                alt.Tooltip("estado:N", title="Estado"),
                alt.Tooltip("cantidad:Q", title="Cantidad", format=",.0f"),
                alt.Tooltip("porcentaje:Q", title="Porcentaje", format=".2f"),
                alt.Tooltip("total:Q", title="Total evaluable", format=",.0f")
            ]
        )
    )

    if modo_y == "Porcentaje" and orden_periodos:
        linea_objetivo = (
            alt.Chart(pd.DataFrame({"objetivo": [65]}))
            .mark_rule(
                strokeDash=[6, 4],
                color="#006B4F",
                size=2
            )
            .encode(
                y="objetivo:Q"
            )
        )

        texto_objetivo = (
            alt.Chart(pd.DataFrame({
                "periodo_label": [orden_periodos[0]],
                "objetivo": [65],
                "texto": ["65%"]
            }))
            .mark_text(
                align="left",
                baseline="bottom",
                dx=5,
                dy=-5,
                color="#006B4F",
                fontWeight="bold"
            )
            .encode(
                x=alt.X(
                    "periodo_label:N",
                    sort=orden_periodos
                ),
                y="objetivo:Q",
                text="texto:N"
            )
        )

        chart = barras + linea_objetivo + texto_objetivo

    else:
        chart = barras

    chart = (
        chart
        .properties(
            title="Performance TAT mensual",
            height=430
        )
        .configure_axis(
            grid=True,
            gridOpacity=0.25
        )
        .configure_view(
            strokeWidth=0
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


def extraer_rango_fechas(rango_fechas):
    if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
    else:
        fecha_inicio = rango_fechas
        fecha_fin = rango_fechas

    if fecha_inicio is None or fecha_fin is None:
        return None, None

    fecha_inicio = pd.Timestamp(fecha_inicio)
    fecha_fin = (
        pd.Timestamp(fecha_fin)
        + pd.Timedelta(days=1)
        - pd.Timedelta(microseconds=1)
    )

    return fecha_inicio, fecha_fin


# =========================================================
# APP
# =========================================================

st.title("Dashboard Performance TAT")

st.markdown(
    """
    Este dashboard carga un archivo `.parquet`, permite filtrar por centro
    y grafica el cumplimiento mensual usando:

    - Fecha eje X: `fecha_recepcion_final`
    - Estado: `performance_tat_total`
    - Centro: `Centro - ME5A`
    """
)

st.divider()

archivo = st.file_uploader(
    "Carga el archivo parquet",
    type=["parquet"]
)

if archivo is None:
    st.warning("Carga el archivo parquet para comenzar.")
    st.stop()


# =========================================================
# CARGA Y PREPARACIÓN
# =========================================================

try:
    df_original = cargar_parquet(archivo.getvalue())
    df = preparar_dataframe(df_original)

except Exception as e:
    st.error("Error al cargar o preparar el archivo.")
    st.exception(e)
    st.stop()


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("Filtros")

col_centro = detectar_columna_centro(df)

if col_centro is not None:
    centros = (
        df[col_centro]
        .dropna()
        .astype(str)
        .str.strip()
        .sort_values()
        .unique()
        .tolist()
    )

    default_centro = ["E002"] if "E002" in centros else []

    centros_sel = st.sidebar.multiselect(
        "Centro",
        options=centros,
        default=default_centro,
        help="Si no seleccionas centro, se muestran todos."
    )

else:
    centros_sel = []
    st.sidebar.warning("No se encontró columna de centro.")


fechas_validas = df["fecha_recepcion_final"].dropna()

if fechas_validas.empty:
    st.error("No hay fechas válidas en fecha_recepcion_final.")
    st.stop()

fecha_min = fechas_validas.min().date()
fecha_max = fechas_validas.max().date()

rango_fechas = st.sidebar.date_input(
    "Rango fecha recepción",
    value=(fecha_min, fecha_max),
    min_value=fecha_min,
    max_value=fecha_max
)

modo_y = st.sidebar.radio(
    "Métrica",
    options=["Porcentaje", "Recuento"],
    index=0
)

mostrar_meses_sin_datos = st.sidebar.checkbox(
    "Mostrar meses sin datos",
    value=False
)

mostrar_df = st.sidebar.checkbox(
    "Mostrar dataframe filtrado",
    value=True
)


# =========================================================
# APLICAR FILTROS
# =========================================================

df_filtrado = df.copy()

# Filtro centro
if col_centro is not None and centros_sel:
    centros_sel_str = [
        str(x).strip()
        for x in centros_sel
    ]

    df_filtrado = df_filtrado[
        df_filtrado[col_centro]
        .astype(str)
        .str.strip()
        .isin(centros_sel_str)
    ].copy()


# Filtro fecha robusto
fecha_inicio, fecha_fin = extraer_rango_fechas(rango_fechas)

if fecha_inicio is None or fecha_fin is None:
    st.warning("Selecciona un rango de fechas válido.")
    st.stop()

if fecha_inicio > fecha_fin:
    st.error("La fecha de inicio no puede ser mayor que la fecha de fin.")
    st.stop()

df_filtrado["fecha_recepcion_final"] = pd.to_datetime(
    df_filtrado["fecha_recepcion_final"],
    errors="coerce"
)

df_filtrado = df_filtrado[
    df_filtrado["fecha_recepcion_final"].notna()
    & df_filtrado["fecha_recepcion_final"].between(
        fecha_inicio,
        fecha_fin
    )
].copy()


# =========================================================
# KPIS
# =========================================================

total_filas = len(df_filtrado)

cumple = df_filtrado["performance_tat_estado"].eq("Cumple").sum()
no_cumple = df_filtrado["performance_tat_estado"].eq("No cumple").sum()

total_evaluable = cumple + no_cumple
no_evaluable = total_filas - total_evaluable

pct_cumple = (
    cumple / total_evaluable * 100
    if total_evaluable > 0
    else 0
)

pct_no_cumple = (
    no_cumple / total_evaluable * 100
    if total_evaluable > 0
    else 0
)

kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

kpi1.metric("Filas filtradas", f"{total_filas:,}")
kpi2.metric("Evaluables", f"{total_evaluable:,}")
kpi3.metric("Cumple", f"{cumple:,}")
kpi4.metric("No cumple", f"{no_cumple:,}")
kpi5.metric("% Cumple", f"{pct_cumple:.2f}%")
kpi6.metric("% No cumple", f"{pct_no_cumple:.2f}%")

st.caption(
    f"Registros no evaluables excluidos del gráfico: {no_evaluable:,}"
)

st.divider()


# =========================================================
# GRÁFICO
# =========================================================

st.subheader("Performance TAT mensual")

tabla_resumen = crear_resumen_mensual(df_filtrado)

if mostrar_meses_sin_datos:
    tabla_resumen = completar_meses(
        tabla=tabla_resumen,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

df_plot = crear_data_plot(
    tabla=tabla_resumen,
    modo_y=modo_y
)

grafico_performance_tat(
    df_plot=df_plot,
    modo_y=modo_y
)


# =========================================================
# TABLA RESUMEN
# =========================================================

st.subheader("Resumen mensual")

if tabla_resumen.empty:
    st.info("No hay resumen mensual disponible.")
else:
    columnas_resumen = [
        "periodo_fecha",
        "periodo_label",
        "Cumple",
        "No cumple",
        "Total",
        "% Cumple",
        "% No cumple"
    ]

    columnas_resumen = [
        col for col in columnas_resumen
        if col in tabla_resumen.columns
    ]

    st.dataframe(
        tabla_resumen[columnas_resumen],
        use_container_width=True
    )


# =========================================================
# DATAFRAME FILTRADO
# =========================================================

if mostrar_df:
    st.subheader("Dataframe filtrado")

    st.caption(
        f"Mostrando primeras 500 filas de {len(df_filtrado):,} registros filtrados."
    )

    st.dataframe(
        df_filtrado.head(500),
        use_container_width=True
    )


# =========================================================
# DESCARGA
# =========================================================

st.subheader("Descarga")

csv = df_filtrado.to_csv(
    index=False,
    encoding="utf-8-sig"
).encode("utf-8-sig")

st.download_button(
    label="Descargar datos filtrados CSV",
    data=csv,
    file_name="performance_tat_filtrado.csv",
    mime="text/csv"
)
