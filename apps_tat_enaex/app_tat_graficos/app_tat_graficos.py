import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


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
    page_title="Dashboard Performance TAT",
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

    meses_abrev = {
        1: "ene",
        2: "feb",
        3: "mar",
        4: "abr",
        5: "may",
        6: "jun",
        7: "jul",
        8: "ago",
        9: "sep",
        10: "oct",
        11: "nov",
        12: "dic"
    }

    df["mes_nombre"] = df["mes_num"].map(meses)
    df["mes_abrev"] = df["mes_num"].map(meses_abrev)

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


def agrupar_performance_mensual(df: pd.DataFrame) -> pd.DataFrame:
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
                "periodo_mes",
                "anio",
                "mes_num",
                "mes_nombre",
                "mes_abrev",
                "performance_tat_estado"
            ],
            dropna=False
        )
        .size()
        .reset_index(name="cantidad")
    )

    total_mes = (
        resumen
        .groupby("periodo_mes")["cantidad"]
        .sum()
        .reset_index(name="total_mes")
    )

    resumen = resumen.merge(
        total_mes,
        on="periodo_mes",
        how="left"
    )

    resumen["porcentaje"] = np.where(
        resumen["total_mes"].gt(0),
        resumen["cantidad"] / resumen["total_mes"] * 100,
        0
    )

    resumen = resumen.sort_values(["anio", "mes_num"])

    return resumen


def crear_tabla_resumen_mensual(resumen: pd.DataFrame) -> pd.DataFrame:
    if resumen.empty:
        return pd.DataFrame()

    tabla = resumen.pivot_table(
        index=[
            "periodo_mes",
            "anio",
            "mes_num",
            "mes_nombre",
            "mes_abrev"
        ],
        columns="performance_tat_estado",
        values="cantidad",
        aggfunc="sum",
        fill_value=0
    ).reset_index()

    for col in ["Cumple", "No cumple", "Sin información"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["Total"] = tabla["Cumple"] + tabla["No cumple"] + tabla["Sin información"]

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

    tabla = tabla.sort_values(["anio", "mes_num"]).reset_index(drop=True)

    return tabla


# =========================================================
# Gráfico 1: versión estilo dashboard con matplotlib
# =========================================================

def grafico_performance_tat_dashboard(
    tabla: pd.DataFrame,
    meta_cumplimiento: float = 65.0,
    titulo: str = "Performance TAT"
):
    if tabla.empty:
        st.warning("No hay datos para graficar con los filtros seleccionados.")
        return

    tabla = tabla.copy()
    tabla = tabla.sort_values(["anio", "mes_num"]).reset_index(drop=True)

    x = np.arange(len(tabla))

    pct_cumple = tabla["% Cumple"].fillna(0)
    pct_no_cumple = tabla["% No cumple"].fillna(0)

    etiquetas_mes = tabla["mes_abrev"].astype(str).tolist()

    anios = tabla["anio"].dropna().astype(int).unique().tolist()
    texto_anios = " / ".join([str(a) for a in anios])

    ancho = max(12, len(tabla) * 0.55)
    alto = 5.2

    fig, ax = plt.subplots(figsize=(ancho, alto))

    color_cumple = "#1F7A4D"
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

    # Etiquetas internas
    for i, (cumple, no_cumple) in enumerate(zip(pct_cumple, pct_no_cumple)):
        if cumple >= 8:
            ax.text(
                i,
                cumple / 2,
                f"{cumple:.1f}%",
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
                f"{no_cumple:.1f}%",
                ha="center",
                va="center",
                fontsize=8,
                color="white",
                fontweight="bold"
            )

    # Línea objetivo
    ax.axhline(
        meta_cumplimiento,
        color=color_meta,
        linestyle=(0, (2, 2)),
        linewidth=2
    )

    ax.text(
        -0.9,
        meta_cumplimiento + 1.5,
        f"{meta_cumplimiento:.0f}%",
        color=color_meta,
        fontsize=9,
        fontweight="bold"
    )

    # Separadores por año
    cambios_anio = tabla["anio"].ne(tabla["anio"].shift()).to_numpy()

    for i, cambio in enumerate(cambios_anio):
        if i > 0 and cambio:
            ax.axvline(
                i - 0.5,
                color="#BDBDBD",
                linestyle=":",
                linewidth=1
            )

    # Etiquetas de año debajo de bloques
    for anio in anios:
        posiciones = tabla.index[tabla["anio"].eq(anio)].tolist()

        if posiciones:
            centro = np.mean(posiciones)

            ax.text(
                centro,
                -13,
                str(anio),
                ha="center",
                va="top",
                fontsize=9,
                color="#444444",
                fontweight="bold"
            )

    # Ejes
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 50, 100])
    ax.set_yticklabels(["0%", "50%", "100%"], fontsize=9)

    ax.set_xticks(x)
    ax.set_xticklabels(
        etiquetas_mes,
        rotation=0,
        fontsize=8
    )

    ax.set_title(
        f"{titulo} {texto_anios}",
        loc="left",
        fontsize=16,
        fontweight="bold",
        pad=12
    )

    ax.set_xlabel("")
    ax.set_ylabel("")

    ax.grid(
        axis="y",
        linestyle=":",
        linewidth=1,
        alpha=0.55
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
        bbox_to_anchor=(0.5, -0.18),
        ncol=2,
        frameon=False,
        fontsize=10
    )

    fig.subplots_adjust(
        left=0.04,
        right=0.99,
        top=0.86,
        bottom=0.25
    )

    st.pyplot(fig, use_container_width=True)


# =========================================================
# Gráfico 2: versión inicial con st.bar_chart
# =========================================================

def crear_tabla_grafico_bar_chart(
    resumen: pd.DataFrame,
    modo_y: str,
    mostrar_sin_info: bool
) -> pd.DataFrame:
    if resumen.empty:
        return pd.DataFrame()

    data = resumen.copy()

    if not mostrar_sin_info:
        data = data[
            data["performance_tat_estado"].isin(["Cumple", "No cumple"])
        ].copy()

    if data.empty:
        return pd.DataFrame()

    if modo_y == "Recuento":
        valores = data.pivot_table(
            index="periodo_mes",
            columns="performance_tat_estado",
            values="cantidad",
            aggfunc="sum",
            fill_value=0
        )
    else:
        valores = data.pivot_table(
            index="periodo_mes",
            columns="performance_tat_estado",
            values="porcentaje",
            aggfunc="sum",
            fill_value=0
        )

    orden = (
        data[["periodo_mes", "anio", "mes_num", "mes_nombre"]]
        .drop_duplicates()
        .sort_values(["anio", "mes_num"])
    )

    valores = valores.reindex(orden["periodo_mes"])

    valores.index = (
        orden["mes_nombre"].astype(str)
        + " "
        + orden["anio"].astype("Int64").astype(str)
    ).values

    columnas_ordenadas = [
        col for col in ["Cumple", "No cumple", "Sin información"]
        if col in valores.columns
    ]

    valores = valores[columnas_ordenadas]

    return valores


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
        El gráfico usa <b>fecha_recepcion_final</b> como eje temporal y
        <b>performance_tat</b> como estado de cumplimiento.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    st.header("Filtros")

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

    tipo_grafico = st.radio(
        "Tipo de gráfico",
        options=[
            "Dashboard 100%",
            "Bar chart simple"
        ],
        index=0
    )

    modo_y = st.radio(
        "Eje Y",
        options=[
            "Porcentaje",
            "Recuento"
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

    mostrar_sin_info = st.checkbox(
        "Mostrar Sin información",
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

            anios_sel = st.multiselect(
                "Año recepción",
                options=anios_disponibles,
                default=anios_disponibles
            )

            if anios_sel:
                df_filtrado = df[
                    df["anio"].isin(anios_sel)
                ].copy()
            else:
                df_filtrado = df.copy()

            centros_sel = st.multiselect(
                "Centro",
                options=opciones_columna(df_filtrado, "Centro")
            )

            nme_centros_sel = st.multiselect(
                "Centro NME",
                options=opciones_columna(df_filtrado, "nme_centro")
            )

            tipo_oc_sel = st.multiselect(
                "Tipo OC",
                options=opciones_columna(df_filtrado, "tipo_oc")
            )

            origen_sel = st.multiselect(
                "Origen OC",
                options=opciones_columna(df_filtrado, "origen_oc")
            )

            sistema_sel = st.multiselect(
                "Sistema OC",
                options=opciones_columna(df_filtrado, "sistema_oc")
            )

            tipo_compra_sel = st.multiselect(
                "Nombre tipo compra",
                options=opciones_columna(df_filtrado, "nombre_tipo_compra")
            )

            categoria_ariba_sel = st.multiselect(
                "Categoría ARIBA",
                options=opciones_columna(df_filtrado, "ariba_categoria_tipo_compra")
            )

            rango_inc_sel = st.multiselect(
                "Rango incumplimiento",
                options=opciones_columna(df_filtrado, "rango_incumplimiento")
            )

            estado_match_sel = st.multiselect(
                "Estado match",
                options=opciones_columna(df_filtrado, "estado_match")
            )

            proveedor_sel = st.multiselect(
                "Proveedor ARIBA",
                options=opciones_columna(df_filtrado, "ariba_proveedor_erp")
            )

            performance_sel = st.multiselect(
                "Performance TAT",
                options=["Cumple", "No cumple", "Sin información"],
                default=["Cumple", "No cumple"]
            )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "Centro",
            centros_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "nme_centro",
            nme_centros_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "tipo_oc",
            tipo_oc_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "origen_oc",
            origen_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "sistema_oc",
            sistema_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "nombre_tipo_compra",
            tipo_compra_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "ariba_categoria_tipo_compra",
            categoria_ariba_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "rango_incumplimiento",
            rango_inc_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "estado_match",
            estado_match_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "ariba_proveedor_erp",
            proveedor_sel
        )

        if performance_sel:
            df_filtrado = df_filtrado[
                df_filtrado["performance_tat_estado"].isin(performance_sel)
            ].copy()

        resumen = agrupar_performance_mensual(df_filtrado)
        tabla_resumen = crear_tabla_resumen_mensual(resumen)

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

        if tipo_grafico == "Dashboard 100%":
            if modo_y != "Porcentaje":
                st.info(
                    "El gráfico Dashboard 100% usa porcentajes para mantener barras apiladas al 100%."
                )

            grafico_performance_tat_dashboard(
                tabla=tabla_resumen,
                meta_cumplimiento=meta_cumplimiento,
                titulo="Performance TAT"
            )

        elif tipo_grafico == "Bar chart simple":
            tabla_grafico = crear_tabla_grafico_bar_chart(
                resumen=resumen,
                modo_y=modo_y,
                mostrar_sin_info=mostrar_sin_info
            )

            if tabla_grafico.empty:
                st.warning("No hay datos para graficar con los filtros seleccionados.")
            else:
                st.subheader("Performance TAT por mes de recepción")
                st.bar_chart(
                    tabla_grafico,
                    use_container_width=True
                )

        st.subheader("Resumen mensual")

        if tabla_resumen.empty:
            st.info("No hay resumen mensual disponible.")
        else:
            st.dataframe(
                tabla_resumen,
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
