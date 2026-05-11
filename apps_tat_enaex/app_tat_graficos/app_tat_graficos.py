import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
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


def crear_performance_desde_dias(df: pd.DataFrame, col_dias: str, col_performance: str):
    """
    Crea una columna performance cuando no existe.
    Regla:
    - dias_incumplimiento <= 0  => Cumple
    - dias_incumplimiento > 0   => No cumple
    """
    if col_performance in df.columns:
        return df

    if col_dias not in df.columns:
        return df

    dias = pd.to_numeric(df[col_dias], errors="coerce")

    df[col_performance] = np.where(
        dias.isna(),
        pd.NA,
        dias.fillna(0).le(0)
    )

    return df


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

    # Performance TAT general
    df["performance_tat_estado"] = df["performance_tat"].apply(
        normalizar_performance
    )

    # Crear columnas de performance por etapa si no vienen en el archivo
    df = crear_performance_desde_dias(
        df,
        col_dias="dias_incumplimiento_lib_solped",
        col_performance="performance_lib_solped"
    )

    df = crear_performance_desde_dias(
        df,
        col_dias="dias_incumplimiento_comprador_1",
        col_performance="performance_comprador_1"
    )

    df = crear_performance_desde_dias(
        df,
        col_dias="dias_incumplimiento_logistica",
        col_performance="performance_logistica"
    )

    df = crear_performance_desde_dias(
        df,
        col_dias="dias_incumplimiento_proveedor",
        col_performance="performance_proveedor"
    )

    # Normalizar estados por etapa
    columnas_performance = [
        "performance_lib_solped",
        "performance_comprador_1",
        "performance_proveedor",
        "performance_logistica"
    ]

    for col in columnas_performance:
        if col in df.columns:
            df[f"{col}_estado"] = df[col].apply(normalizar_performance)

    # Variables de fecha
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


# =========================================================
# Resumen mensual TAT
# =========================================================

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


def completar_meses_anios(tabla: pd.DataFrame, anios: list[int]) -> pd.DataFrame:
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

    bases = []

    for anio in sorted(anios):
        base_anio = pd.DataFrame({
            "anio": anio,
            "mes_num": list(range(1, 13)),
            "mes_nombre": [meses[i] for i in range(1, 13)]
        })

        base_anio["periodo_fecha"] = pd.to_datetime(
            [f"{anio}-{mes:02d}-01" for mes in range(1, 13)]
        )

        base_anio["periodo_mes"] = [
            f"{anio}-{mes:02d}" for mes in range(1, 13)
        ]

        base_anio["periodo_label"] = (
            base_anio["mes_nombre"].astype(str)
            + " "
            + base_anio["anio"].astype(str)
        )

        bases.append(base_anio)

    if not bases:
        return tabla

    base = pd.concat(bases, ignore_index=True)

    salida = base.merge(
        tabla,
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
# Donuts de cumplimiento por etapa
# =========================================================

def crear_resumen_cumplimiento_etapa(
    df: pd.DataFrame,
    col_performance_estado: str
):
    if col_performance_estado not in df.columns:
        return None

    estado = df[col_performance_estado]

    total = len(estado)
    cumple = estado.eq("Cumple").sum()
    no_cumple = estado.eq("No cumple").sum()
    sin_info = estado.eq("Sin información").sum()

    pct_cumple = cumple / total * 100 if total > 0 else 0
    pct_no_cumple = no_cumple / total * 100 if total > 0 else 0
    pct_sin_info = sin_info / total * 100 if total > 0 else 0

    return {
        "total": total,
        "cumple": cumple,
        "no_cumple": no_cumple,
        "sin_info": sin_info,
        "pct_cumple": pct_cumple,
        "pct_no_cumple": pct_no_cumple,
        "pct_sin_info": pct_sin_info
    }


def crear_donut_altair(data: pd.DataFrame):
    colores = {
        "Cumple": "#5B5B5B",
        "No cumple": "#D94555",
        "Sin información": "#BDBDBD"
    }

    chart = (
        alt.Chart(data)
        .mark_arc(
            innerRadius=42,
            outerRadius=72
        )
        .encode(
            theta=alt.Theta("valor:Q"),
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
                legend=alt.Legend(
                    title="",
                    orient="bottom"
                )
            ),
            tooltip=[
                alt.Tooltip("estado:N", title="Estado"),
                alt.Tooltip("valor:Q", title="Cantidad", format=",.0f"),
                alt.Tooltip("porcentaje:Q", title="Porcentaje", format=".1f")
            ]
        )
        .properties(
            height=210
        )
        .configure_view(
            strokeWidth=0
        )
    )

    return chart


def tarjeta_donut_cumplimiento(
    df: pd.DataFrame,
    titulo: str,
    col_performance_estado: str,
    col_dias_incumplimiento: str,
    regla: str
):
    resumen = crear_resumen_cumplimiento_etapa(
        df=df,
        col_performance_estado=col_performance_estado
    )

    if resumen is None:
        st.warning(f"No existe la columna {col_performance_estado}")
        return

    data = pd.DataFrame({
        "estado": ["Cumple", "No cumple"],
        "valor": [
            resumen["cumple"],
            resumen["no_cumple"]
        ],
        "porcentaje": [
            resumen["pct_cumple"],
            resumen["pct_no_cumple"]
        ]
    })

    # Evitar gráficos vacíos si no hay datos
    if data["valor"].sum() == 0:
        data = pd.DataFrame({
            "estado": ["Sin información"],
            "valor": [1],
            "porcentaje": [100]
        })

    promedio_dias = 0

    if col_dias_incumplimiento in df.columns:
        promedio_dias = (
            pd.to_numeric(df[col_dias_incumplimiento], errors="coerce")
            .fillna(0)
            .mean()
        )

    st.markdown(
        f"""
        <div style="text-align:center; font-size:12px; color:#222; min-height:34px;">
            • {regla}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <h4 style="text-align:center; margin-bottom:0px; margin-top:0px;">
            Cumplimiento {titulo}
        </h4>
        """,
        unsafe_allow_html=True
    )

    chart = crear_donut_altair(data)
    st.altair_chart(chart, use_container_width=True)

    st.markdown(
        f"""
        <div style="text-align:center; margin-top:-6px;">
            <div style="font-size:34px; font-weight:700; color:#222;">
                {promedio_dias:.0f}
            </div>
            <div style="font-size:12px; color:#666;">
                Promedio de Dx {titulo}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def bloque_donuts_cumplimiento(df: pd.DataFrame):
    st.subheader("Cumplimiento por etapa")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Lib Solped",
            col_performance_estado="performance_lib_solped_estado",
            col_dias_incumplimiento="dias_incumplimiento_lib_solped",
            regla="Nacional e Internacional < 2"
        )

    with col2:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Comprador",
            col_performance_estado="performance_comprador_1_estado",
            col_dias_incumplimiento="dias_incumplimiento_comprador_1",
            regla="Nacional e Internacional < 11"
        )

    with col3:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Prov",
            col_performance_estado="performance_proveedor_estado",
            col_dias_incumplimiento="dias_incumplimiento_proveedor",
            regla="Nacional < 20<br>Internacional < 60"
        )

    with col4:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Logística",
            col_performance_estado="performance_logistica_estado",
            col_dias_incumplimiento="dias_incumplimiento_logistica",
            regla="Nacional e Internacional < 10"
        )


# =========================================================
# Barplot interactivo con Altair
# =========================================================

def crear_data_barplot_interactivo(
    tabla: pd.DataFrame,
    modo_y: str = "Porcentaje",
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
            porcentaje = row.get(f"% {estado}", 0)

            if modo_y == "Recuento":
                valor = row.get(estado, 0)
            else:
                valor = porcentaje

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

    return df_plot


def grafico_barplot_interactivo_altair(
    df_plot: pd.DataFrame,
    modo_y: str = "Porcentaje",
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

    chart = (
        alt.Chart(df_plot)
        .mark_bar()
        .encode(
            x=alt.X(
                "periodo_label:N",
                sort=orden_periodos,
                title="Mes / Año",
                axis=alt.Axis(
                    labelAngle=-45,
                    labelOverlap=False,
                    labelLimit=140
                )
            ),
            y=alt.Y(
                "valor:Q",
                stack="zero",
                title=titulo_y,
                scale=alt.Scale(domain=[0, 100]) if modo_y == "Porcentaje" else alt.Undefined
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
                alt.Tooltip("valor:Q", title=titulo_y, format=".2f"),
                alt.Tooltip("porcentaje:Q", title="Porcentaje", format=".2f"),
                alt.Tooltip("total:Q", title="Total mes", format=",.0f")
            ]
        )
        .properties(
            title=titulo,
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

    modo_y_barplot = st.radio(
        "Métrica barplot interactivo",
        options=[
            "Porcentaje",
            "Recuento"
        ],
        index=0
    )

    mostrar_sin_info = st.checkbox(
        "Mostrar Sin información",
        value=False
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

            anios_sel = st.multiselect(
                "Años recepción",
                options=anios_disponibles,
                default=anios_disponibles,
                help="Por defecto se muestran todos los años juntos. Puedes filtrar uno o varios años."
            )

        if anios_sel:
            df_filtrado = df[
                df["anio"].isin(anios_sel)
            ].copy()
        else:
            df_filtrado = df.copy()
            anios_sel = anios_disponibles

        with st.sidebar:
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

        if mostrar_meses_sin_datos and not tabla_resumen.empty:
            tabla_resumen = completar_meses_anios(
                tabla=tabla_resumen,
                anios=anios_sel
            )

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

        # =========================
        # NUEVO BLOQUE DE DONUTS
        # =========================

        bloque_donuts_cumplimiento(df_filtrado)

        st.divider()

        # =========================
        # BARPLOT MENSUAL TAT
        # =========================

        if tabla_resumen.empty:
            st.warning("No hay datos para graficar con los filtros seleccionados.")
        else:
            df_plot = crear_data_barplot_interactivo(
                tabla=tabla_resumen,
                modo_y=modo_y_barplot,
                mostrar_sin_info=mostrar_sin_info
            )

            grafico_barplot_interactivo_altair(
                df_plot=df_plot,
                modo_y=modo_y_barplot,
                titulo="Barplot interactivo Performance TAT - todos los años seleccionados"
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
