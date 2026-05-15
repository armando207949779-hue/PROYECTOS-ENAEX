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

COLOR_CUMPLE = "#5B5B5B"
COLOR_NO_CUMPLE = "#D94555"
COLOR_OBJETIVO = "#006B4F"
COLOR_NEUTRO = "#F3F4F6"
COLOR_TEXTO = "#222222"
COLOR_MUTED = "#666666"
COLOR_BORDE = "#E5E7EB"

OBJETIVO_CUMPLIMIENTO = 65

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
# FUNCIONES BASE
# =========================================================

@st.cache_data(show_spinner="Leyendo archivo parquet...")
def cargar_parquet(archivo_bytes: bytes) -> pd.DataFrame:
    buffer = io.BytesIO(archivo_bytes)
    return pd.read_parquet(buffer)


def normalizar_texto(valor):
    if pd.isna(valor):
        return ""

    return (
        str(valor)
        .strip()
        .lower()
        .replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )


def normalizar_performance(valor):
    texto = normalizar_texto(valor)

    if texto in ["cumple", "true", "1", "si", "sí", "yes"]:
        return "Cumple"

    if texto in ["no cumple", "nocumple", "false", "0", "no"]:
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


def formato_numero(valor):
    return f"{int(valor):,}".replace(",", ".")


def formato_pct(valor, decimales=1):
    if pd.isna(valor):
        valor = 0

    return f"{float(valor):.{decimales}f}%"


def estado_vs_objetivo(pct, objetivo=OBJETIVO_CUMPLIMIENTO):
    if pct >= objetivo:
        return "Supera 65%"

    return "Bajo 65%"


# =========================================================
# RESUMEN MENSUAL TAT
# =========================================================

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


def crear_data_plot_mensual(tabla: pd.DataFrame) -> pd.DataFrame:
    if tabla.empty:
        return pd.DataFrame()

    df_plot = tabla.copy()

    for col in ["Cumple", "No cumple", "Total", "% Cumple", "% No cumple"]:
        if col in df_plot.columns:
            df_plot[col] = pd.to_numeric(
                df_plot[col],
                errors="coerce"
            ).fillna(0)

    df_plot["pct_cumple"] = np.where(
        df_plot["Total"] > 0,
        df_plot["Cumple"] / df_plot["Total"] * 100,
        0
    )

    df_plot["supero_65"] = df_plot["pct_cumple"] >= OBJETIVO_CUMPLIMIENTO

    df_plot["estado_objetivo"] = np.where(
        df_plot["supero_65"],
        "Superó 65%",
        "No superó 65%"
    )

    df_plot["texto_pct"] = df_plot["pct_cumple"].map(
        lambda x: f"{x:.1f}%"
    )

    df_plot["texto_estado"] = np.where(
        df_plot["supero_65"],
        "Sí",
        "No"
    )

    df_plot = df_plot.sort_values("periodo_fecha").reset_index(drop=True)

    return df_plot


def grafico_cumplimiento_mensual(df_plot: pd.DataFrame):
    if df_plot.empty:
        st.warning("No hay datos evaluables para graficar.")
        return

    if df_plot["Total"].sum() == 0:
        st.warning("No hay registros Cumple / No cumple para graficar.")
        return

    orden_periodos = (
        df_plot[["periodo_label", "periodo_fecha"]]
        .drop_duplicates()
        .sort_values("periodo_fecha")["periodo_label"]
        .tolist()
    )

    barras = (
        alt.Chart(df_plot)
        .mark_bar(
            size=34,
            cornerRadiusTopLeft=5,
            cornerRadiusTopRight=5
        )
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_periodos,
                title="Mes recepción",
                axis=alt.Axis(
                    labelAngle=-35,
                    labelOverlap=False,
                    labelFontSize=11,
                    titleFontSize=12
                )
            ),
            y=alt.Y(
                "pct_cumple:Q",
                title="% Cumplimiento",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(
                    labelFontSize=11,
                    titleFontSize=12,
                    format=".0f"
                )
            ),
            color=alt.Color(
                "estado_objetivo:N",
                scale=alt.Scale(
                    domain=["Superó 65%", "No superó 65%"],
                    range=[COLOR_CUMPLE, COLOR_NO_CUMPLE]
                ),
                legend=alt.Legend(
                    title="Resultado objetivo",
                    orient="bottom",
                    labelFontSize=12,
                    titleFontSize=12
                )
            ),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Mes"),
                alt.Tooltip("pct_cumple:Q", title="% Cumplimiento", format=".1f"),
                alt.Tooltip("estado_objetivo:N", title="¿Superó 65%?"),
                alt.Tooltip("Cumple:Q", title="Cumple", format=",.0f"),
                alt.Tooltip("Total:Q", title="Total evaluable", format=",.0f")
            ]
        )
    )

    etiquetas_pct = (
        alt.Chart(df_plot)
        .mark_text(
            dy=-10,
            fontSize=11,
            fontWeight="bold",
            color=COLOR_TEXTO
        )
        .encode(
            x=alt.X("periodo_label:N", sort=orden_periodos),
            y=alt.Y("pct_cumple:Q"),
            text="texto_pct:N"
        )
    )

    linea_objetivo = (
        alt.Chart(pd.DataFrame({"objetivo": [OBJETIVO_CUMPLIMIENTO]}))
        .mark_rule(
            strokeDash=[10, 5],
            color=COLOR_OBJETIVO,
            size=3
        )
        .encode(
            y="objetivo:Q"
        )
    )

    texto_objetivo = (
        alt.Chart(pd.DataFrame({
            "periodo_label": [orden_periodos[0]],
            "objetivo": [OBJETIVO_CUMPLIMIENTO],
            "texto": [f"Objetivo {OBJETIVO_CUMPLIMIENTO}%"]
        }))
        .mark_text(
            align="left",
            baseline="bottom",
            dx=8,
            dy=-8,
            color=COLOR_OBJETIVO,
            fontWeight="bold",
            fontSize=13
        )
        .encode(
            x=alt.X("periodo_label:N", sort=orden_periodos),
            y="objetivo:Q",
            text="texto:N"
        )
    )

    chart = barras + etiquetas_pct + linea_objetivo + texto_objetivo

    chart = (
        chart
        .properties(
            title=alt.TitleParams(
                text="% Cumplimiento TAT mensual",
                subtitle=(
                    "Se muestra solo el porcentaje de cumplimiento. "
                    f"Color según si el mes superó o no el {OBJETIVO_CUMPLIMIENTO}%."
                ),
                fontSize=18,
                subtitleFontSize=12,
                fontWeight="bold",
                anchor="start"
            ),
            height=430
        )
        .configure_axis(
            grid=True,
            gridOpacity=0.18
        )
        .configure_view(
            strokeWidth=0
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


# =========================================================
# RESUMEN POR ETAPA
# =========================================================

def detectar_columnas_etapas(df: pd.DataFrame):
    etapas = [
        {
            "titulo": "Lib Solped",
            "col_perf": "performance_liberacion_solped",
            "col_dias": "dias_liberacion_solped",
            "regla": "Nacional e Internacional < 2 días",
            "texto_promedio": "Promedio días Lib Solped"
        },
        {
            "titulo": "Comprador",
            "col_perf": "performance_comprador",
            "col_dias": "dias_comprador",
            "regla": "Nacional e Internacional < 11 días",
            "texto_promedio": "Promedio días Comprador"
        },
        {
            "titulo": "Proveedor",
            "col_perf": "performance_proveedor",
            "col_dias": "dias_proveedor",
            "regla": "Nacional < 20 días | Internacional < 60 días",
            "texto_promedio": "Promedio días Proveedor"
        },
        {
            "titulo": "Logística",
            "col_perf": "performance_logistica",
            "col_dias": "dias_logistica",
            "regla": "Nacional e Internacional < 10 días",
            "texto_promedio": "Promedio días Logística"
        }
    ]

    return etapas


def normalizar_estado_etapa(valor):
    texto = normalizar_texto(valor)

    if texto == "cumple":
        return "Cumple"

    if texto == "no cumple":
        return "No cumple"

    if texto in ["no aplica", "no aplica al analisis"]:
        return "No aplica"

    if texto in ["sin datos", "en proceso"]:
        return "Sin datos"

    return "Sin información"


def calcular_resumen_etapa(
    df_base: pd.DataFrame,
    col_perf: str,
    col_dias: str
):
    temp = df_base.copy()

    temp["estado_etapa"] = temp[col_perf].apply(normalizar_estado_etapa)

    temp_eval = temp[
        temp["estado_etapa"].isin(["Cumple", "No cumple"])
    ].copy()

    conteo = (
        temp_eval["estado_etapa"]
        .value_counts()
        .reindex(["Cumple", "No cumple"], fill_value=0)
    )

    total = int(conteo.sum())

    pct_cumple = (
        float(conteo["Cumple"] / total * 100)
        if total > 0
        else 0.0
    )

    pct_no_cumple = (
        float(conteo["No cumple"] / total * 100)
        if total > 0
        else 0.0
    )

    dias = pd.to_numeric(
        temp[col_dias],
        errors="coerce"
    ).dropna()

    dias = dias[dias > 0]

    promedio = float(dias.mean()) if not dias.empty else 0.0

    return {
        "Cumple": int(conteo["Cumple"]),
        "No cumple": int(conteo["No cumple"]),
        "Total evaluable": total,
        "% Cumple": pct_cumple,
        "% No cumple": pct_no_cumple,
        "Promedio días Dx > 0": promedio,
        "N usado promedio": int(len(dias)),
        "Superó 65%": pct_cumple >= OBJETIVO_CUMPLIMIENTO,
        "Estado objetivo": estado_vs_objetivo(pct_cumple)
    }


def crear_resumen_etapas(df_base: pd.DataFrame) -> pd.DataFrame:
    etapas = detectar_columnas_etapas(df_base)
    data = []

    for etapa in etapas:
        col_perf = etapa["col_perf"]
        col_dias = etapa["col_dias"]

        if col_perf not in df_base.columns or col_dias not in df_base.columns:
            data.append({
                "Etapa": etapa["titulo"],
                "Regla": etapa["regla"],
                "Estado": "Faltan columnas",
                "Cumple": 0,
                "No cumple": 0,
                "Total evaluable": 0,
                "% Cumple": 0.0,
                "% No cumple": 0.0,
                "Promedio días Dx > 0": 0.0,
                "N usado promedio": 0,
                "Superó 65%": False,
                "Estado objetivo": "Sin datos",
                "Columna performance": col_perf,
                "Columna días": col_dias
            })
            continue

        resumen = calcular_resumen_etapa(
            df_base=df_base,
            col_perf=col_perf,
            col_dias=col_dias
        )

        data.append({
            "Etapa": etapa["titulo"],
            "Regla": etapa["regla"],
            "Estado": "OK",
            **resumen,
            "Columna performance": col_perf,
            "Columna días": col_dias
        })

    tabla = pd.DataFrame(data)

    tabla["Orden"] = np.arange(len(tabla))
    tabla["Brecha vs 65%"] = tabla["% Cumple"] - OBJETIVO_CUMPLIMIENTO
    tabla["Texto cumplimiento"] = tabla["% Cumple"].map(lambda x: f"{x:.1f}%")
    tabla["Texto objetivo"] = np.where(
        tabla["Superó 65%"],
        "Sí superó 65%",
        "No superó 65%"
    )

    return tabla


def render_tarjeta_etapa(row):
    pct = float(row["% Cumple"])
    cumple = int(row["Cumple"])
    no_cumple = int(row["No cumple"])
    total = int(row["Total evaluable"])
    promedio = float(row["Promedio días Dx > 0"])
    supera = bool(row["Superó 65%"])
    color_estado = COLOR_OBJETIVO if supera else COLOR_NO_CUMPLE
    estado = "Superó 65%" if supera else "No superó 65%"
    barra_width = max(0, min(100, pct))

    if total == 0:
        color_estado = COLOR_MUTED
        estado = "Sin datos evaluables"

    html = f"""
    <div style="
        border: 1px solid {COLOR_BORDE};
        border-radius: 16px;
        padding: 18px 18px 16px 18px;
        background: white;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        min-height: 255px;
    ">
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 8px;
        ">
            <div>
                <div style="
                    font-size: 18px;
                    font-weight: 800;
                    color: {COLOR_TEXTO};
                    line-height: 1.15;
                ">
                    {row["Etapa"]}
                </div>
                <div style="
                    font-size: 12px;
                    color: {COLOR_MUTED};
                    margin-top: 6px;
                    min-height: 34px;
                ">
                    {row["Regla"]}
                </div>
            </div>
            <div style="
                background: {color_estado};
                color: white;
                border-radius: 999px;
                padding: 6px 10px;
                font-size: 11px;
                font-weight: 700;
                white-space: nowrap;
            ">
                {estado}
            </div>
        </div>

        <div style="
            margin-top: 16px;
            font-size: 38px;
            font-weight: 900;
            color: {COLOR_TEXTO};
            line-height: 1;
        ">
            {pct:.1f}%
        </div>

        <div style="
            margin-top: 7px;
            font-size: 12px;
            color: {COLOR_MUTED};
        ">
            Cumplimiento de la etapa
        </div>

        <div style="
            margin-top: 14px;
            width: 100%;
            height: 12px;
            background: {COLOR_NEUTRO};
            border-radius: 999px;
            overflow: hidden;
            position: relative;
        ">
            <div style="
                width: {barra_width:.1f}%;
                height: 12px;
                background: {color_estado};
                border-radius: 999px;
            "></div>
        </div>

        <div style="
            margin-top: 8px;
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: {COLOR_MUTED};
        ">
            <span>0%</span>
            <span style="font-weight: 700; color: {COLOR_OBJETIVO};">Objetivo 65%</span>
            <span>100%</span>
        </div>

        <div style="
            margin-top: 16px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 12px;
        ">
            <div style="background: {COLOR_NEUTRO}; border-radius: 12px; padding: 10px;">
                <div style="color: {COLOR_MUTED};">Cumple</div>
                <div style="font-size: 18px; font-weight: 800; color: {COLOR_TEXTO};">{formato_numero(cumple)}</div>
            </div>
            <div style="background: {COLOR_NEUTRO}; border-radius: 12px; padding: 10px;">
                <div style="color: {COLOR_MUTED};">No cumple</div>
                <div style="font-size: 18px; font-weight: 800; color: {COLOR_TEXTO};">{formato_numero(no_cumple)}</div>
            </div>
        </div>

        <div style="
            margin-top: 12px;
            font-size: 12px;
            color: {COLOR_MUTED};
        ">
            Total evaluable: <b>{formato_numero(total)}</b> · Promedio días: <b>{promedio:.1f}</b>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)


def render_tarjetas_etapas(tabla_etapas: pd.DataFrame):
    if tabla_etapas.empty:
        st.warning("No hay datos por etapa para mostrar.")
        return

    cols = st.columns(4)

    for idx, (_, row) in enumerate(tabla_etapas.iterrows()):
        with cols[idx % 4]:
            render_tarjeta_etapa(row)


def grafico_ranking_etapas(tabla_etapas: pd.DataFrame):
    if tabla_etapas.empty:
        st.warning("No hay datos por etapa para graficar.")
        return

    plot = tabla_etapas.copy()

    plot = plot[plot["Estado"].eq("OK")].copy()

    if plot.empty:
        st.warning("No hay etapas con columnas válidas para graficar.")
        return

    plot["Estado objetivo"] = np.where(
        plot["% Cumple"] >= OBJETIVO_CUMPLIMIENTO,
        "Superó 65%",
        "No superó 65%"
    )

    orden_etapas = (
        plot
        .sort_values("% Cumple", ascending=True)["Etapa"]
        .tolist()
    )

    barras = (
        alt.Chart(plot)
        .mark_bar(
            height=32,
            cornerRadiusTopRight=5,
            cornerRadiusBottomRight=5
        )
        .encode(
            y=alt.Y(
                "Etapa:N",
                sort=orden_etapas,
                title="",
                axis=alt.Axis(
                    labelFontSize=12,
                    labelFontWeight="bold"
                )
            ),
            x=alt.X(
                "% Cumple:Q",
                title="% Cumplimiento",
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(format=".0f", labelFontSize=11)
            ),
            color=alt.Color(
                "Estado objetivo:N",
                scale=alt.Scale(
                    domain=["Superó 65%", "No superó 65%"],
                    range=[COLOR_CUMPLE, COLOR_NO_CUMPLE]
                ),
                legend=alt.Legend(
                    title="Resultado objetivo",
                    orient="bottom"
                )
            ),
            tooltip=[
                alt.Tooltip("Etapa:N", title="Etapa"),
                alt.Tooltip("% Cumple:Q", title="% Cumple", format=".1f"),
                alt.Tooltip("Estado objetivo:N", title="¿Superó 65%?"),
                alt.Tooltip("Cumple:Q", title="Cumple", format=",.0f"),
                alt.Tooltip("No cumple:Q", title="No cumple", format=",.0f"),
                alt.Tooltip("Total evaluable:Q", title="Total evaluable", format=",.0f"),
                alt.Tooltip("Promedio días Dx > 0:Q", title="Promedio días", format=".1f")
            ]
        )
    )

    etiquetas = (
        alt.Chart(plot)
        .mark_text(
            align="left",
            dx=7,
            fontSize=12,
            fontWeight="bold",
            color=COLOR_TEXTO
        )
        .encode(
            y=alt.Y("Etapa:N", sort=orden_etapas),
            x=alt.X("% Cumple:Q"),
            text="Texto cumplimiento:N"
        )
    )

    linea_objetivo = (
        alt.Chart(pd.DataFrame({"objetivo": [OBJETIVO_CUMPLIMIENTO]}))
        .mark_rule(
            strokeDash=[10, 5],
            color=COLOR_OBJETIVO,
            size=3
        )
        .encode(
            x="objetivo:Q"
        )
    )

    texto_objetivo = (
        alt.Chart(pd.DataFrame({
            "objetivo": [OBJETIVO_CUMPLIMIENTO],
            "Etapa": [orden_etapas[-1]],
            "texto": [f"Objetivo {OBJETIVO_CUMPLIMIENTO}%"]
        }))
        .mark_text(
            align="left",
            baseline="bottom",
            dx=6,
            dy=-10,
            color=COLOR_OBJETIVO,
            fontWeight="bold",
            fontSize=12
        )
        .encode(
            x="objetivo:Q",
            y=alt.Y("Etapa:N", sort=orden_etapas),
            text="texto:N"
        )
    )

    chart = barras + etiquetas + linea_objetivo + texto_objetivo

    chart = (
        chart
        .properties(
            title=alt.TitleParams(
                text="Ranking de cumplimiento por etapa",
                subtitle=(
                    "Muestra solamente el % Cumple y si cada etapa superó "
                    f"el objetivo de {OBJETIVO_CUMPLIMIENTO}%."
                ),
                fontSize=18,
                subtitleFontSize=12,
                fontWeight="bold",
                anchor="start"
            ),
            height=280
        )
        .configure_axis(
            grid=True,
            gridOpacity=0.16
        )
        .configure_view(
            strokeWidth=0
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


def crear_tabla_diagnostico_etapas(df_base: pd.DataFrame) -> pd.DataFrame:
    tabla = crear_resumen_etapas(df_base)

    columnas = [
        "Etapa",
        "Estado",
        "Cumple",
        "No cumple",
        "Total evaluable",
        "% Cumple",
        "% No cumple",
        "Superó 65%",
        "Brecha vs 65%",
        "Promedio días Dx > 0",
        "N usado promedio",
        "Regla",
        "Columna performance",
        "Columna días"
    ]

    columnas = [col for col in columnas if col in tabla.columns]

    return tabla[columnas].copy()


# =========================================================
# APP
# =========================================================

st.title("Dashboard Performance TAT")

st.markdown(
    """
    Este dashboard carga un archivo `.parquet`, permite filtrar por centro
    y muestra el cumplimiento TAT con una lectura más directa:

    - **Gráfico mensual:** solo `% Cumple` y validación contra el objetivo de 65%.
    - **Etapas:** tarjetas comparativas y ranking horizontal en lugar de donas.
    - **Fecha eje X:** `fecha_recepcion_final`.
    - **Estado TAT:** `performance_tat_total`.
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

mostrar_meses_sin_datos = st.sidebar.checkbox(
    "Mostrar meses sin datos",
    value=False
)

mostrar_df = st.sidebar.checkbox(
    "Mostrar dataframe filtrado",
    value=True
)

filtrar_tat_evaluable_etapas = st.sidebar.checkbox(
    "Etapas: filtrar Performance TAT Cumple / No cumple",
    value=True,
    help=(
        "Replica el filtro usado para evaluar etapas: "
        "performance_tat_total debe ser Cumple o No cumple."
    )
)

mostrar_diagnostico_tat = st.sidebar.checkbox(
    "Mostrar diagnóstico Performance TAT",
    value=False
)


# =========================================================
# APLICAR FILTROS GENERALES
# =========================================================

df_filtrado = df.copy()

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
# TABS
# =========================================================

tab_dashboard, tab_datos = st.tabs(
    [
        "Dashboard",
        "Datos filtrados"
    ]
)


# =========================================================
# TAB 1: DASHBOARD COMPLETO
# =========================================================

with tab_dashboard:

    # =====================================================
    # KPIS PRINCIPALES
    # =====================================================

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

    supera_objetivo_global = pct_cumple >= OBJETIVO_CUMPLIMIENTO

    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

    kpi1.metric("Filas filtradas", f"{total_filas:,}")
    kpi2.metric("Evaluables", f"{total_evaluable:,}")
    kpi3.metric("Cumple", f"{cumple:,}")
    kpi4.metric("% Cumple", f"{pct_cumple:.2f}%")
    kpi5.metric(
        "¿Supera 65%?",
        "Sí" if supera_objetivo_global else "No"
    )

    st.caption(
        f"Registros no evaluables excluidos de los gráficos de cumplimiento: {no_evaluable:,}"
    )

    if mostrar_diagnostico_tat:
        with st.expander("Diagnóstico rápido Performance TAT", expanded=True):
            st.write("Distribución original de performance_tat_total filtrado:")

            if "performance_tat_total" in df_filtrado.columns:
                st.write(
                    df_filtrado["performance_tat_total"]
                    .astype(str)
                    .str.strip()
                    .value_counts(dropna=False)
                )

            st.write("Distribución normalizada:")
            st.write(
                df_filtrado["performance_tat_estado"]
                .value_counts(dropna=False)
            )

    st.divider()

    # =====================================================
    # GRÁFICO MENSUAL
    # =====================================================

    st.subheader("Cumplimiento mensual")

    tabla_resumen = crear_resumen_mensual(df_filtrado)

    if mostrar_meses_sin_datos:
        tabla_resumen = completar_meses(
            tabla=tabla_resumen,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

    df_plot = crear_data_plot_mensual(tabla_resumen)

    grafico_cumplimiento_mensual(df_plot=df_plot)

    with st.expander("Ver resumen mensual", expanded=False):
        if tabla_resumen.empty:
            st.info("No hay resumen mensual disponible.")
        else:
            tabla_mensual = crear_data_plot_mensual(tabla_resumen)

            columnas_resumen = [
                "periodo_fecha",
                "periodo_label",
                "Cumple",
                "No cumple",
                "Total",
                "pct_cumple",
                "estado_objetivo"
            ]

            columnas_resumen = [
                col for col in columnas_resumen
                if col in tabla_mensual.columns
            ]

            st.dataframe(
                tabla_mensual[columnas_resumen].rename(
                    columns={
                        "periodo_fecha": "Periodo fecha",
                        "periodo_label": "Mes",
                        "pct_cumple": "% Cumple",
                        "estado_objetivo": "Resultado objetivo"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    # =====================================================
    # VISUALIZACIÓN POR ETAPA
    # =====================================================

    st.subheader("Cumplimiento por etapa")

    df_etapas = df_filtrado.copy()

    if filtrar_tat_evaluable_etapas:
        df_etapas = df_etapas[
            df_etapas["performance_tat_estado"].isin(
                ["Cumple", "No cumple"]
            )
        ].copy()

    etapa_kpi1, etapa_kpi2, etapa_kpi3 = st.columns(3)

    etapa_kpi1.metric(
        "Filas usadas en etapas",
        f"{len(df_etapas):,}"
    )

    etapa_kpi2.metric(
        "TAT Cumple",
        f"{df_etapas['performance_tat_estado'].eq('Cumple').sum():,}"
    )

    etapa_kpi3.metric(
        "TAT No cumple",
        f"{df_etapas['performance_tat_estado'].eq('No cumple').sum():,}"
    )

    st.caption(
        "Las tarjetas y el ranking consideran solo Cumple / No cumple por etapa. "
        "Los promedios usan días > 0 sobre el dataframe filtrado."
    )

    if df_etapas.empty:
        st.warning("No hay datos para mostrar con los filtros seleccionados.")
    else:
        tabla_etapas = crear_resumen_etapas(df_etapas)

        render_tarjetas_etapas(tabla_etapas)

        st.markdown("")

        grafico_ranking_etapas(tabla_etapas)

    with st.expander("Ver diagnóstico de etapas", expanded=False):
        tabla_diag = crear_tabla_diagnostico_etapas(df_etapas)

        st.dataframe(
            tabla_diag,
            use_container_width=True,
            hide_index=True
        )


# =========================================================
# TAB 2: DATOS FILTRADOS
# =========================================================

with tab_datos:

    if mostrar_df:
        st.subheader("Dataframe filtrado")

        st.caption(
            f"Mostrando primeras 500 filas de {len(df_filtrado):,} registros filtrados."
        )

        st.dataframe(
            df_filtrado.head(500),
            use_container_width=True
        )
    else:
        st.info("Activa 'Mostrar dataframe filtrado' en el panel lateral para ver la tabla.")

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

