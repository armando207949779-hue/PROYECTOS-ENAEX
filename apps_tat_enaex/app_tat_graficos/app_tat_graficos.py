import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import altair as alt


# =========================
# Ruta del logo ENAEX
# =========================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================
# Configuración Streamlit
# =========================

st.set_page_config(
    page_title="Performance TAT",
    page_icon="📊",
    layout="wide"
)


# =========================
# Encabezado con logo ENAEX centrado
# =========================

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
            margin-top: 10px;
            margin-bottom: 15px;
        ">
            <img 
                src="data:image/svg+xml;base64,{logo_base64}" 
                style="width: 230px; display: block;"
            >
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.error(f"Logo no encontrado: {LOGO_PATH}")


# =========================================================
# Funciones generales
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;)":
        return ";"
    if separador_csv == "Coma (,)":
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner="Leyendo archivo...")
def leer_archivo_cache(
    bytes_archivo: bytes,
    nombre_archivo: str,
    separador_csv: str
) -> pd.DataFrame:
    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".xlsx"):
        return pd.read_excel(buffer)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)

        try:
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip"
            )
        except Exception:
            buffer.seek(0)
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip"
            )

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


def normalizar_performance(valor):
    if pd.isna(valor):
        return "Sin información"

    texto = str(valor).strip().lower()

    if texto in ["true", "1", "cumple", "sí", "si", "yes"]:
        return "Cumple"

    if texto in ["false", "0", "no cumple", "no"]:
        return "No cumple"

    return "Sin información"


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    columnas_requeridas = [
        "fecha_recepcion_final",
        "performance_tat"
    ]

    faltantes = [
        col for col in columnas_requeridas
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    df["fecha_recepcion_final"] = pd.to_datetime(
        df["fecha_recepcion_final"],
        errors="coerce"
    )

    df["performance_tat_estado"] = df["performance_tat"].apply(
        normalizar_performance
    )

    df["anio"] = df["fecha_recepcion_final"].dt.year
    df["mes_num"] = df["fecha_recepcion_final"].dt.month

    df["periodo_fecha"] = (
        df["fecha_recepcion_final"]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["periodo_mes"] = (
        df["fecha_recepcion_final"]
        .dt.to_period("M")
        .astype("string")
    )

    meses = {
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

    df["mes_nombre"] = df["mes_num"].map(meses)

    df["periodo_label"] = np.where(
        df["anio"].notna() & df["mes_nombre"].notna(),
        df["mes_nombre"].astype(str) + " " + df["anio"].astype("Int64").astype(str),
        pd.NA
    )

    return df


def opciones_columna(df: pd.DataFrame, columna: str):
    if columna not in df.columns:
        return []

    return (
        df[columna]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )


def aplicar_filtro_multiselect(
    df: pd.DataFrame,
    columna: str,
    seleccionados: list
) -> pd.DataFrame:
    if columna not in df.columns:
        return df

    if not seleccionados:
        return df

    return df[
        df[columna].astype(str).isin(seleccionados)
    ].copy()


def crear_resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df = df[
        df["fecha_recepcion_final"].notna()
    ].copy()

    if df.empty:
        return pd.DataFrame()

    resumen = (
        df
        .groupby(
            [
                "periodo_fecha",
                "periodo_mes",
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
            "periodo_mes",
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

    for col in ["Cumple", "No cumple", "Sin información"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["Total"] = (
        tabla["Cumple"]
        + tabla["No cumple"]
        + tabla["Sin información"]
    )

    tabla["% Cumple"] = np.where(
        tabla["Total"].gt(0),
        tabla["Cumple"] / tabla["Total"] * 100,
        0
    )

    tabla["% No cumple"] = np.where(
        tabla["Total"].gt(0),
        tabla["No cumple"] / tabla["Total"] * 100,
        0
    )

    tabla["% Sin información"] = np.where(
        tabla["Total"].gt(0),
        tabla["Sin información"] / tabla["Total"] * 100,
        0
    )

    tabla = tabla.sort_values("periodo_fecha").reset_index(drop=True)

    return tabla


def completar_meses_anio(tabla: pd.DataFrame, anio: int) -> pd.DataFrame:
    meses = {
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

    base = pd.DataFrame({
        "anio": anio,
        "mes_num": list(range(1, 13)),
        "mes_nombre": [meses[i] for i in range(1, 13)]
    })

    base["periodo_fecha"] = pd.to_datetime(
        [f"{anio}-{mes:02d}-01" for mes in range(1, 13)]
    )

    base["periodo_mes"] = [
        f"{anio}-{mes:02d}" for mes in range(1, 13)
    ]

    base["periodo_label"] = (
        base["mes_nombre"].astype(str)
        + " "
        + base["anio"].astype(str)
    )

    tabla_anio = tabla[
        tabla["anio"].eq(anio)
    ].copy()

    salida = base.merge(
        tabla_anio,
        on=[
            "anio",
            "mes_num",
            "mes_nombre",
            "periodo_fecha",
            "periodo_mes",
            "periodo_label"
        ],
        how="left"
    )

    columnas_rellenar = [
        "Cumple",
        "No cumple",
        "Sin información",
        "Total",
        "% Cumple",
        "% No cumple",
        "% Sin información"
    ]

    for col in columnas_rellenar:
        if col in salida.columns:
            salida[col] = salida[col].fillna(0)

    salida = salida.sort_values("periodo_fecha").reset_index(drop=True)

    return salida


# =========================================================
# Gráfico Performance 100% con matplotlib
# =========================================================

def grafico_performance_original(
    tabla: pd.DataFrame,
    meta_cumplimiento: float = 65.0,
    titulo: str = "Performance TAT"
):
    if tabla.empty:
        st.warning("No hay datos para graficar con los filtros seleccionados.")
        return

    tabla = tabla.copy()
    tabla = tabla.sort_values("periodo_fecha").reset_index(drop=True)

    x = np.arange(len(tabla))

    pct_cumple = tabla["% Cumple"].fillna(0)
    pct_no_cumple = tabla["% No cumple"].fillna(0)

    etiquetas_mes = tabla["mes_nombre"].astype(str).tolist()

    anios = tabla["anio"].dropna().astype(int).unique().tolist()
    titulo_anios = " / ".join(str(a) for a in anios)

    ancho = max(10, len(tabla) * 0.7)

    fig, ax = plt.subplots(figsize=(ancho, 4.4))

    color_cumple = "#5B5B5B"
    color_no_cumple = "#D94555"
    color_meta = "#006B3F"

    ax.bar(
        x,
        pct_cumple,
        color=color_cumple,
        label="Cumple",
        width=0.72
    )

    ax.bar(
        x,
        pct_no_cumple,
        bottom=pct_cumple,
        color=color_no_cumple,
        label="No cumple",
        width=0.72
    )

    for i, (cumple, no_cumple, total) in enumerate(
        zip(pct_cumple, pct_no_cumple, tabla["Total"].fillna(0))
    ):
        if total == 0:
            continue

        if cumple >= 8:
            ax.text(
                i,
                cumple / 2,
                f"{cumple:.2f}%",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
                fontweight="bold"
            )

        if no_cumple >= 8:
            ax.text(
                i,
                cumple + no_cumple / 2,
                f"{no_cumple:.2f}%",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
                fontweight="bold"
            )

    ax.axhline(
        meta_cumplimiento,
        color=color_meta,
        linestyle=(0, (2, 2)),
        linewidth=2
    )

    ax.text(
        -0.45,
        meta_cumplimiento + 1,
        f"{meta_cumplimiento:.0f}%",
        color=color_meta,
        fontsize=9,
        fontweight="bold"
    )

    cambios_anio = tabla["anio"].ne(tabla["anio"].shift()).to_numpy()

    for i, cambio in enumerate(cambios_anio):
        if i > 0 and cambio:
            ax.axvline(
                i - 0.5,
                color="#BDBDBD",
                linestyle=":",
                linewidth=1
            )

    for anio in anios:
        posiciones = tabla.index[tabla["anio"].eq(anio)].tolist()

        if posiciones:
            centro = np.mean(posiciones)

            ax.text(
                centro,
                -11,
                str(anio),
                ha="center",
                va="top",
                fontsize=8,
                color="#444444"
            )

    ax.set_ylim(0, 100)
    ax.set_yticks([0, 50, 100])
    ax.set_yticklabels(["0%", "50%", "100%"])

    ax.set_xticks(x)

    rotacion = 0 if len(tabla) <= 14 else 45

    ax.set_xticklabels(
        etiquetas_mes,
        rotation=rotacion,
        ha="right" if rotacion else "center",
        fontsize=8
    )

    ax.set_title(
        f"{titulo} {titulo_anios}",
        loc="left",
        fontsize=13,
        fontweight="bold"
    )

    ax.grid(
        axis="y",
        linestyle=":",
        linewidth=1,
        alpha=0.6
    )

    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", length=0)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.20),
        ncol=2,
        frameon=False,
        fontsize=9
    )

    fig.subplots_adjust(
        left=0.04,
        right=0.99,
        top=0.86,
        bottom=0.30
    )

    st.pyplot(fig, use_container_width=True)


# =========================================================
# Barplot interactivo con Altair
# =========================================================

def crear_data_barplot_interactivo(
    tabla: pd.DataFrame,
    modo_y: str = "Recuento",
    mostrar_sin_info: bool = False
) -> pd.DataFrame:
    if tabla.empty:
        return pd.DataFrame()

    tabla = tabla.copy()
    tabla = tabla.sort_values("periodo_fecha").reset_index(drop=True)

    estados = ["Cumple", "No cumple"]

    if mostrar_sin_info:
        estados.append("Sin información")

    data = []

    for _, row in tabla.iterrows():
        for estado in estados:
            if modo_y == "Recuento":
                valor = row.get(estado, 0)
                porcentaje = row.get(f"% {estado}", 0)
            else:
                valor = row.get(f"% {estado}", 0)
                porcentaje = row.get(f"% {estado}", 0)

            data.append({
                "periodo_fecha": row["periodo_fecha"],
                "periodo_label": row["periodo_label"],
                "anio": row["anio"],
                "mes_num": row["mes_num"],
                "mes_nombre": row["mes_nombre"],
                "estado": estado,
                "valor": valor,
                "porcentaje": porcentaje,
                "total": row.get("Total", 0)
            })

    df_plot = pd.DataFrame(data)

    orden_estado = {
        "Cumple": 1,
        "No cumple": 2,
        "Sin información": 3
    }

    df_plot["orden_estado"] = df_plot["estado"].map(orden_estado)

    df_plot = df_plot.sort_values(
        ["periodo_fecha", "orden_estado"]
    ).reset_index(drop=True)

    df_plot["texto_barra"] = (
        df_plot["porcentaje"]
        .round(1)
        .astype(str)
        + "%"
    )

    # Ocultar etiquetas muy pequeñas para no saturar el gráfico
    df_plot["texto_barra_visible"] = np.where(
        df_plot["porcentaje"] >= 5,
        df_plot["texto_barra"],
        ""
    )

    return df_plot


def grafico_barplot_interactivo_altair(
    df_plot: pd.DataFrame,
    modo_y: str = "Recuento",
    titulo: str = "Barplot interactivo Performance TAT"
):
    if df_plot.empty:
        st.warning("No hay datos para graficar con los filtros seleccionados.")
        return

    titulo_y = "Recuento" if modo_y == "Recuento" else "Porcentaje"

    colores = {
        "Cumple": "#5B5B5B",
        "No cumple": "#D94555",
        "Sin información": "#BDBDBD"
    }

    orden_periodos = (
        df_plot[["periodo_label", "periodo_fecha"]]
        .drop_duplicates()
        .sort_values("periodo_fecha")["periodo_label"]
        .tolist()
    )

    base = (
        alt.Chart(df_plot)
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_periodos,
                title="Mes / Año",
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap=False
                )
            ),
            y=alt.Y(
                "valor:Q",
                stack="zero",
                title=titulo_y
            ),
            color=alt.Color(
                "estado:N",
                scale=alt.Scale(
                    domain=["Cumple", "No cumple", "Sin información"],
                    range=[
                        colores["Cumple"],
                        colores["No cumple"],
                        colores["Sin información"]
                    ]
                ),
                legend=alt.Legend(title="")
            ),
            order=alt.Order(
                "orden_estado:Q",
                sort="ascending"
            ),
            tooltip=[
                alt.Tooltip("periodo_label:N", title="Periodo"),
                alt.Tooltip("estado:N", title="Estado"),
                alt.Tooltip("valor:Q", title=titulo_y, format=",.2f"),
                alt.Tooltip("porcentaje:Q", title="Porcentaje", format=".2f"),
                alt.Tooltip("total:Q", title="Total mes", format=",.0f")
            ]
        )
    )

    barras = base.mark_bar()

    etiquetas = (
        base
        .mark_text(
            color="white",
            fontWeight="bold",
            fontSize=11
        )
        .encode(
            text=alt.Text("texto_barra_visible:N")
        )
    )

    chart = (
        (barras + etiquetas)
        .properties(
            title=titulo,
            height=420
        )
        .interactive()
    )

    st.altair_chart(
        chart,
        use_container_width=True
    )


# =========================================================
# Exportación
# =========================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow"
    )

    return output.getvalue()


# =========================================================
# Interfaz
# =========================================================

st.markdown(
    """
    <h1 style='text-align: center;'>
        Dashboard Performance TAT
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Sube el archivo <b>match_integrado_me5a_ariba_nme80fn_performance.parquet</b>.
        El gráfico usa <b>fecha_recepcion_final</b> como eje temporal mensual y
        <b>performance_tat</b> como estado de cumplimiento.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    st.header("Filtros")

    pagina = st.radio(
        "Vista",
        options=[
            "Performance 100%",
            "Barplot interactivo"
        ],
        index=0
    )

    separador_csv = st.selectbox(
        "Separador CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación"
        ],
        index=0
    )

    meta_cumplimiento = st.number_input(
        "Meta cumplimiento (%)",
        min_value=0.0,
        max_value=100.0,
        value=65.0,
        step=1.0
    )

    modo_y_barplot = st.radio(
        "Métrica barplot interactivo",
        options=[
            "Recuento",
            "Porcentaje"
        ],
        index=0
    )

    mostrar_sin_info = st.checkbox(
        "Mostrar Sin información",
        value=False
    )

    modo_visualizacion = st.radio(
        "Visualización",
        options=[
            "Un gráfico por año",
            "Año específico",
            "Todos los años juntos"
        ],
        index=0
    )

    mostrar_meses_sin_datos = st.checkbox(
        "Mostrar meses sin datos",
        value=False
    )


uploaded_file = st.file_uploader(
    "Selecciona archivo performance TAT",
    type=["parquet", "xlsx", "csv"]
)


if uploaded_file is not None:
    try:
        df_original = leer_archivo_cache(
            bytes_archivo=uploaded_file.getvalue(),
            nombre_archivo=uploaded_file.name,
            separador_csv=separador_csv
        )

        df = preparar_dataframe(df_original)

        with st.sidebar:
            st.divider()

            anios_disponibles = (
                df["anio"]
                .dropna()
                .astype(int)
                .sort_values()
                .unique()
                .tolist()
            )

            if modo_visualizacion == "Año específico":
                anio_especifico = st.selectbox(
                    "Año a visualizar",
                    options=anios_disponibles,
                    index=len(anios_disponibles) - 1 if anios_disponibles else 0
                )
                anios_sel = [anio_especifico]

            else:
                anios_sel = st.multiselect(
                    "Años recepción",
                    options=anios_disponibles,
                    default=anios_disponibles
                )

            if anios_sel:
                df_filtrado = df[
                    df["anio"].isin(anios_sel)
                ].copy()
            else:
                df_filtrado = df.copy()

            centros_disponibles = opciones_columna(df_filtrado, "Centro")

            centros_sel = st.multiselect(
                "Centro",
                options=centros_disponibles
            )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "Centro",
            centros_sel
        )

        tabla_resumen = crear_resumen_mensual(df_filtrado)

        total = len(df_filtrado)
        cumple = df_filtrado["performance_tat_estado"].eq("Cumple").sum()
        no_cumple = df_filtrado["performance_tat_estado"].eq("No cumple").sum()
        sin_info = df_filtrado["performance_tat_estado"].eq("Sin información").sum()

        pct_cumple = round(cumple / total * 100, 2) if total > 0 else 0
        pct_no_cumple = round(no_cumple / total * 100, 2) if total > 0 else 0

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric("Filas filtradas", f"{total:,}")
        col2.metric("Cumple", f"{cumple:,}")
        col3.metric("No cumple", f"{no_cumple:,}")
        col4.metric("% Cumple", f"{pct_cumple}%")
        col5.metric("% No cumple", f"{pct_no_cumple}%")

        st.divider()

        if tabla_resumen.empty:
            st.warning("No hay datos para graficar con los filtros seleccionados.")

        elif modo_visualizacion == "Un gráfico por año":
            for anio in sorted(tabla_resumen["anio"].dropna().astype(int).unique()):
                tabla_anio = tabla_resumen[
                    tabla_resumen["anio"].eq(anio)
                ].copy()

                if mostrar_meses_sin_datos:
                    tabla_anio = completar_meses_anio(tabla_resumen, anio)

                if pagina == "Performance 100%":
                    grafico_performance_original(
                        tabla=tabla_anio,
                        meta_cumplimiento=meta_cumplimiento,
                        titulo="Performance TAT"
                    )

                elif pagina == "Barplot interactivo":
                    df_plot = crear_data_barplot_interactivo(
                        tabla=tabla_anio,
                        modo_y=modo_y_barplot,
                        mostrar_sin_info=mostrar_sin_info
                    )

                    grafico_barplot_interactivo_altair(
                        df_plot=df_plot,
                        modo_y=modo_y_barplot,
                        titulo=f"Barplot interactivo {anio}"
                    )

        elif modo_visualizacion == "Año específico":
            tabla_anio = tabla_resumen[
                tabla_resumen["anio"].eq(anios_sel[0])
            ].copy()

            if mostrar_meses_sin_datos:
                tabla_anio = completar_meses_anio(tabla_resumen, anios_sel[0])

            if pagina == "Performance 100%":
                grafico_performance_original(
                    tabla=tabla_anio,
                    meta_cumplimiento=meta_cumplimiento,
                    titulo="Performance TAT"
                )

            elif pagina == "Barplot interactivo":
                df_plot = crear_data_barplot_interactivo(
                    tabla=tabla_anio,
                    modo_y=modo_y_barplot,
                    mostrar_sin_info=mostrar_sin_info
                )

                grafico_barplot_interactivo_altair(
                    df_plot=df_plot,
                    modo_y=modo_y_barplot,
                    titulo=f"Barplot interactivo {anios_sel[0]}"
                )

        elif modo_visualizacion == "Todos los años juntos":
            if pagina == "Performance 100%":
                grafico_performance_original(
                    tabla=tabla_resumen,
                    meta_cumplimiento=meta_cumplimiento,
                    titulo="Performance TAT"
                )

            elif pagina == "Barplot interactivo":
                df_plot = crear_data_barplot_interactivo(
                    tabla=tabla_resumen,
                    modo_y=modo_y_barplot,
                    mostrar_sin_info=mostrar_sin_info
                )

                grafico_barplot_interactivo_altair(
                    df_plot=df_plot,
                    modo_y=modo_y_barplot,
                    titulo="Barplot interactivo todos los años"
                )

        st.subheader("Resumen mensual ordenado cronológicamente")

        if tabla_resumen.empty:
            st.info("No hay resumen mensual disponible.")
        else:
            columnas_tabla = [
                "periodo_fecha",
                "periodo_mes",
                "periodo_label",
                "anio",
                "mes_num",
                "mes_nombre",
                "Cumple",
                "No cumple",
                "Sin información",
                "Total",
                "% Cumple",
                "% No cumple",
                "% Sin información"
            ]

            columnas_tabla = [
                col for col in columnas_tabla
                if col in tabla_resumen.columns
            ]

            st.dataframe(
                tabla_resumen[columnas_tabla],
                use_container_width=True
            )

        st.divider()

        with st.expander("Ver datos filtrados"):
            st.dataframe(
                df_filtrado.head(500),
                use_container_width=True
            )

        st.subheader("Descarga")

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            csv_bytes = convertir_a_csv(df_filtrado)

            st.download_button(
                label="Descargar datos filtrados CSV",
                data=csv_bytes,
                file_name="performance_tat_filtrado.csv",
                mime="text/csv"
            )

        with col_d2:
            parquet_bytes = convertir_a_parquet(df_filtrado)

            st.download_button(
                label="Descargar datos filtrados Parquet",
                data=parquet_bytes,
                file_name="performance_tat_filtrado.parquet",
                mime="application/octet-stream"
            )

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga el archivo de performance para comenzar.")
