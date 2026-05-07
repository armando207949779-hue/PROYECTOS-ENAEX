import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


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
            margin-bottom: 20px;
        ">
            <img 
                src="data:image/svg+xml;base64,{logo_base64}" 
                style="width: 260px; display: block;"
            >
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.error(f"Logo no encontrado en ruta correcta: {LOGO_PATH}")


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

    df["mes_nombre"] = df["mes_num"].map(meses)

    return df


def opciones_columna(df: pd.DataFrame, columna: str):
    if columna not in df.columns:
        return []

    valores = (
        df[columna]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )

    return valores


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

    orden_periodos = (
        df[["periodo_mes", "anio", "mes_num", "mes_nombre"]]
        .drop_duplicates()
        .sort_values(["anio", "mes_num"])
    )

    resumen = (
        df
        .groupby(
            [
                "periodo_mes",
                "performance_tat_estado"
            ],
            dropna=False
        )
        .size()
        .reset_index(name="cantidad")
    )

    resumen = resumen.merge(
        orden_periodos,
        on="periodo_mes",
        how="left"
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


def crear_grafico_performance(
    resumen: pd.DataFrame,
    modo_y: str,
    mostrar_sin_info: bool
):
    if resumen.empty:
        return None

    data = resumen.copy()

    if not mostrar_sin_info:
        data = data[
            data["performance_tat_estado"].isin(["Cumple", "No cumple"])
        ].copy()

    estados = ["Cumple", "No cumple"]

    if mostrar_sin_info:
        estados.append("Sin información")

    periodos = (
        data[["periodo_mes", "anio", "mes_num", "mes_nombre"]]
        .drop_duplicates()
        .sort_values(["anio", "mes_num"])
    )

    x_labels = [
        f"{row.mes_nombre}<br>{int(row.anio)}"
        for row in periodos.itertuples()
    ]

    fig = go.Figure()

    colores = {
        "Cumple": "#5A5A5A",
        "No cumple": "#D94A5B",
        "Sin información": "#BDBDBD"
    }

    for estado in estados:
        temp = data[
            data["performance_tat_estado"].eq(estado)
        ].copy()

        temp = periodos[["periodo_mes"]].merge(
            temp[["periodo_mes", "cantidad", "porcentaje"]],
            on="periodo_mes",
            how="left"
        )

        temp["cantidad"] = temp["cantidad"].fillna(0)
        temp["porcentaje"] = temp["porcentaje"].fillna(0)

        if modo_y == "Recuento":
            y = temp["cantidad"]
            texto = temp["cantidad"].astype(int).astype(str)
            titulo_y = "Recuento"
        else:
            y = temp["porcentaje"]
            texto = temp["porcentaje"].round(2).astype(str) + "%"
            titulo_y = "% Performance TAT"

        fig.add_trace(
            go.Bar(
                name=estado,
                x=x_labels,
                y=y,
                text=texto,
                textposition="inside",
                marker_color=colores.get(estado),
                hovertemplate=(
                    "Estado: %{fullData.name}<br>"
                    "Periodo: %{x}<br>"
                    f"{titulo_y}: %{{y}}<extra></extra>"
                )
            )
        )

    fig.update_layout(
        barmode="stack",
        title="Performance TAT por mes de recepción",
        xaxis_title="Fecha de recepción: Año / Mes",
        yaxis_title=titulo_y,
        legend_title="Performance TAT",
        height=520,
        margin=dict(l=20, r=20, t=70, b=80)
    )

    if modo_y == "Porcentaje":
        fig.update_yaxes(range=[0, 100], ticksuffix="%")

    return fig


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_parquet(output, index=False, engine="pyarrow")
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
        La app grafica el recuento de <b>performance_tat</b> usando como eje X
        la <b>fecha_recepcion_final</b> agrupada por año y mes.
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

    modo_y = st.radio(
        "Eje Y",
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

            rango_inc_sel = st.multiselect(
                "Rango incumplimiento",
                options=opciones_columna(df_filtrado, "rango_incumplimiento")
            )

            proveedor_sel = st.multiselect(
                "Proveedor ARIBA",
                options=opciones_columna(df_filtrado, "ariba_proveedor_erp")
            )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "Centro",
            centros_sel
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
            "rango_incumplimiento",
            rango_inc_sel
        )

        df_filtrado = aplicar_filtro_multiselect(
            df_filtrado,
            "ariba_proveedor_erp",
            proveedor_sel
        )

        resumen = agrupar_performance_mensual(df_filtrado)

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

        fig = crear_grafico_performance(
            resumen=resumen,
            modo_y=modo_y,
            mostrar_sin_info=mostrar_sin_info
        )

        if fig is None:
            st.warning("No hay datos para graficar con los filtros seleccionados.")
        else:
            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.subheader("Resumen mensual")

        if not resumen.empty:
            tabla_resumen = resumen.pivot_table(
                index=["periodo_mes", "anio", "mes_num", "mes_nombre"],
                columns="performance_tat_estado",
                values="cantidad",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            columnas_estado = [
                col for col in ["Cumple", "No cumple", "Sin información"]
                if col in tabla_resumen.columns
            ]

            tabla_resumen["Total"] = tabla_resumen[columnas_estado].sum(axis=1)

            if "Cumple" in tabla_resumen.columns:
                tabla_resumen["% Cumple"] = (
                    tabla_resumen["Cumple"] / tabla_resumen["Total"] * 100
                ).round(2)
            else:
                tabla_resumen["% Cumple"] = 0

            if "No cumple" in tabla_resumen.columns:
                tabla_resumen["% No cumple"] = (
                    tabla_resumen["No cumple"] / tabla_resumen["Total"] * 100
                ).round(2)
            else:
                tabla_resumen["% No cumple"] = 0

            tabla_resumen = tabla_resumen.sort_values(
                ["anio", "mes_num"]
            )

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