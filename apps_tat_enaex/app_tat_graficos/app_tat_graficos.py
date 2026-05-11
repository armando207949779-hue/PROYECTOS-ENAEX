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
    """
    Normaliza performance_tat u otras columnas booleanas a texto.
    """
    if pd.isna(valor):
        return "Sin información"

    texto = str(valor).strip().lower()

    if texto in ["true", "1", "cumple", "sí", "si", "yes"]:
        return "Cumple"

    if texto in ["false", "0", "no cumple", "no"]:
        return "No cumple"

    return "Sin información"


def performance_dx_lib_solped(valor):
    """
    Regla visual del dashboard:
    - Nacional e Internacional < 2
    """
    valor = pd.to_numeric(valor, errors="coerce")

    if pd.isna(valor):
        return "Sin información"

    if valor < 2:
        return "Cumple"

    return "No cumple"


def performance_dx_comprador(valor):
    """
    Regla visual del dashboard:
    - Nacional e Internacional < 11
    """
    valor = pd.to_numeric(valor, errors="coerce")

    if pd.isna(valor):
        return "Sin información"

    if valor < 11:
        return "Cumple"

    return "No cumple"


def performance_dx_logistica(valor):
    """
    Regla visual del dashboard:
    - Nacional e Internacional < 10
    """
    valor = pd.to_numeric(valor, errors="coerce")

    if pd.isna(valor) or valor < 0:
        return "Sin información"

    if valor < 10:
        return "Cumple"

    return "No cumple"


def performance_proveedor_dax(dx_proveedor, tipo_oc):
    """
    Regla visual del dashboard:
    - OC 35 / 45: Nacional < 20
    - OC 47: Internacional < 60
    """
    dx_proveedor = pd.to_numeric(dx_proveedor, errors="coerce")

    if pd.isna(dx_proveedor):
        return "Sin información"

    if pd.isna(tipo_oc):
        return "No cumple"

    tipo_oc = str(tipo_oc).strip().replace(".0", "")

    if tipo_oc in ["35", "45"] and dx_proveedor < 20:
        return "Cumple"

    if tipo_oc == "47" and dx_proveedor < 60:
        return "Cumple"

    return "No cumple"


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

    # =========================
    # Performance TAT general
    # =========================

    df["performance_tat_estado"] = df["performance_tat"].apply(
        normalizar_performance
    )

    # =========================
    # Performance por etapa para donuts
    # =========================

    if "dx_lib_solped" in df.columns:
        df["performance_lib_solped_estado"] = df["dx_lib_solped"].apply(
            performance_dx_lib_solped
        )
    elif "performance_lib_solped" in df.columns:
        df["performance_lib_solped_estado"] = df["performance_lib_solped"].apply(
            normalizar_performance
        )

    if "dx_comprador_1" in df.columns:
        df["performance_comprador_1_estado"] = df["dx_comprador_1"].apply(
            performance_dx_comprador
        )
    elif "performance_comprador_1" in df.columns:
        df["performance_comprador_1_estado"] = df["performance_comprador_1"].apply(
            normalizar_performance
        )

    if "dx_proveedor" in df.columns and "tipo_oc" in df.columns:
        df["performance_proveedor_estado"] = df.apply(
            lambda row: performance_proveedor_dax(
                row["dx_proveedor"],
                row["tipo_oc"]
            ),
            axis=1
        )
    elif "performance_proveedor" in df.columns:
        df["performance_proveedor_estado"] = df["performance_proveedor"].apply(
            normalizar_performance
        )

    if "dx_logistica" in df.columns:
        df["performance_logistica_estado"] = df["dx_logistica"].apply(
            performance_dx_logistica
        )
    elif "performance_logistica" in df.columns:
        df["performance_logistica_estado"] = df["performance_logistica"].apply(
            normalizar_performance
        )

    # =========================
    # Variables de fecha
    # =========================

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
        df["mes_nombre"].astype(str)
        + " "
        + df["anio"].astype("Int64").astype(str),
        pd.NA
    )

    return df


def opciones_columna(df: pd.DataFrame, columna: str):
    """
    Devuelve opciones únicas para una columna.

    - Elimina valores nulos.
    - Ordena valores numéricos como números.
    - Ordena valores texto alfabéticamente.
    """
    if columna not in df.columns:
        return []

    serie = df[columna].dropna()

    if serie.empty:
        return []

    serie_str = serie.astype(str).str.strip()

    try:
        serie_num = pd.to_numeric(serie_str, errors="coerce")

        if serie_num.notna().all():
            return (
                serie_num
                .sort_values()
                .astype(str)
                .unique()
                .tolist()
            )
    except Exception:
        pass

    return (
        serie_str
        .sort_values()
        .unique()
        .tolist()
    )


def aplicar_filtro_multiselect(
    df: pd.DataFrame,
    columna: str,
    seleccionados: list
) -> pd.DataFrame:
    """
    Aplica filtro multiselect sobre una columna.
    Si no hay selección, no filtra.
    """
    if columna not in df.columns:
        return df

    if not seleccionados:
        return df

    seleccionados_str = [
        str(valor).strip()
        for valor in seleccionados
    ]

    return df[
        df[columna].astype(str).str.strip().isin(seleccionados_str)
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

    data = (
        df[col_performance_estado]
        .fillna("Sin información")
        .astype(str)
        .value_counts()
        .reset_index()
    )

    data.columns = ["estado", "valor"]

    total = data["valor"].sum()

    data["porcentaje"] = np.where(
        total > 0,
        data["valor"] / total * 100,
        0
    )

    orden = {
        "Cumple": 1,
        "No cumple": 2,
        "Sin información": 3
    }

    data["orden"] = data["estado"].map(orden).fillna(99)

    data = (
        data
        .sort_values("orden")
        .drop(columns="orden")
        .reset_index(drop=True)
    )

    return data


def crear_donut_altair(data: pd.DataFrame):
    colores = {
        "Cumple": "#5B5B5B",
        "No cumple": "#D94555",
        "Sin información": "#BDBDBD"
    }

    estados = [
        "Cumple",
        "No cumple",
        "Sin información"
    ]

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
                    domain=estados,
                    range=[colores[e] for e in estados]
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
    regla: str,
    texto_promedio: str
):
    data = crear_resumen_cumplimiento_etapa(
        df=df,
        col_performance_estado=col_performance_estado
    )

    if data is None:
        st.warning(f"No existe la columna {col_performance_estado}")
        return

    data = data[
        data["estado"].isin(["Cumple", "No cumple"])
    ].copy()

    if data.empty or data["valor"].sum() == 0:
        data = pd.DataFrame({
            "estado": ["Sin información"],
            "valor": [1],
            "porcentaje": [100]
        })

    promedio_dias = 0

    if col_dias_incumplimiento in df.columns:
        promedio_dias = (
            pd.to_numeric(df[col_dias_incumplimiento], errors="coerce")
            .mean()
        )

        if pd.isna(promedio_dias):
            promedio_dias = 0

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
                {texto_promedio}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def bloque_donuts_cumplimiento(df: pd.DataFrame):
    st.markdown(
        """
        <div style="font-size:12px; font-weight:700; margin-bottom:10px;">
            Nacional &lt;40 días<br>
            Internacional &lt;70 días
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Lib Solped",
            col_performance_estado="performance_lib_solped_estado",
            col_dias_incumplimiento="dx_lib_solped",
            regla="Nacional e Internacional &lt; 2",
            texto_promedio="Promedio de Dx Lib solped"
        )

    with col2:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Comprador",
            col_performance_estado="performance_comprador_1_estado",
            col_dias_incumplimiento="dx_comprador_1",
            regla="Nacional e Internacional &lt; 11",
            texto_promedio="Promedio de Dx Comprador 1"
        )

    with col3:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Prov",
            col_performance_estado="performance_proveedor_estado",
            col_dias_incumplimiento="dx_proveedor",
            regla="Nacional &lt; 20<br>Internacional &lt;60",
            texto_promedio="Promedio de Dx Proveedor"
        )

    with col4:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Logística",
            col_performance_estado="performance_logistica_estado",
            col_dias_incumplimiento="dx_logistica",
            regla="Nacional e Internacional &lt; 10",
            texto_promedio="Promedio de Dx Logística"
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

    mostrar_vista_previa = st.checkbox(
        "Mostrar vista previa del dataframe cargado",
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

        # =========================
        # Vista previa opcional
        # =========================

        if mostrar_vista_previa:
            with st.expander("Vista previa del dataframe cargado", expanded=True):
                st.caption(
                    f"Archivo cargado: {uploaded_file.name} | "
                    f"Filas: {len(df_original):,} | "
                    f"Columnas: {len(df_original.columns):,}"
                )

                st.dataframe(
                    df_original.head(200),
                    use_container_width=True
                )

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

            fechas_validas = df["fecha_recepcion_final"].dropna()

            fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
            fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

            fecha_inicio = None
            fecha_fin = None

            if fecha_min and fecha_max:
                fecha_inicio = st.date_input(
                    "Fecha inicio recepción",
                    value=fecha_min,
                    min_value=fecha_min,
                    max_value=fecha_max,
                    help="Fecha inicial para filtrar fecha_recepcion_final."
                )

                fecha_fin = st.date_input(
                    "Fecha fin recepción",
                    value=fecha_max,
                    min_value=fecha_min,
                    max_value=fecha_max,
                    help="Fecha final para filtrar fecha_recepcion_final."
                )
            else:
                st.info(
                    "No hay fechas válidas en fecha_recepcion_final. "
                    "El gráfico mensual no podrá generarse."
                )

        # =========================
        # Filtro por año
        # =========================

        if anios_sel:
            df_filtrado = df[
                df["anio"].isin(anios_sel)
            ].copy()
        else:
            df_filtrado = df.copy()
            anios_sel = anios_disponibles

        # =========================
        # Filtro por fecha inicio / fin
        # =========================

        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                st.error(
                    "La fecha de inicio no puede ser mayor que la fecha de fin."
                )
                st.stop()

            df_filtrado = df_filtrado[
                df_filtrado["fecha_recepcion_final"].notna()
                & df_filtrado["fecha_recepcion_final"].dt.date.between(
                    fecha_inicio,
                    fecha_fin
                )
            ].copy()

        # =========================
        # Filtros dinámicos por columnas
        # =========================

        with st.sidebar:
            st.divider()
            st.subheader("Filtros por columnas")

            columnas_excluir_filtros = [
                "fecha_recepcion_final",
                "periodo_fecha",
                "periodo_mes",
                "periodo_label",
                "anio",
                "mes_num",
                "mes_nombre"
            ]

            columnas_disponibles_filtro = [
                col for col in df_filtrado.columns
                if col not in columnas_excluir_filtros
            ]

            columnas_default = []

            if "Centro" in columnas_disponibles_filtro:
                columnas_default.append("Centro")

            columnas_filtro_sel = st.multiselect(
                "Selecciona columnas para filtrar",
                options=columnas_disponibles_filtro,
                default=columnas_default,
                help=(
                    "Puedes seleccionar una o varias columnas. "
                    "Se creará un filtro para cada columna seleccionada."
                )
            )

            filtros_columnas = {}

            for columna in columnas_filtro_sel:
                valores_disponibles = opciones_columna(
                    df=df_filtrado,
                    columna=columna
                )

                seleccionados = st.multiselect(
                    f"Filtrar {columna}",
                    options=valores_disponibles,
                    key=f"filtro_columna_{columna}"
                )

                filtros_columnas[columna] = seleccionados

        for columna, seleccionados in filtros_columnas.items():
            df_filtrado = aplicar_filtro_multiselect(
                df=df_filtrado,
                columna=columna,
                seleccionados=seleccionados
            )

        # =========================
        # Aviso por registros sin fecha
        # =========================

        registros_sin_fecha_original = df["fecha_recepcion_final"].isna().sum()

        if registros_sin_fecha_original > 0:
            st.warning(
                f"Hay {registros_sin_fecha_original:,} registros sin fecha_recepcion_final "
                "en el archivo original. Estos registros no se muestran en el gráfico mensual "
                "porque no pueden asignarse a un mes. Si aplicas filtro por fecha, también "
                "quedan fuera del análisis filtrado."
            )

        # =========================
        # Resumen mensual
        # =========================

        tabla_resumen = crear_resumen_mensual(df_filtrado)

        if mostrar_meses_sin_datos and not tabla_resumen.empty:
            tabla_resumen = completar_meses_anios(
                tabla=tabla_resumen,
                anios=anios_sel
            )

        # =========================
        # KPIs
        # =========================

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
        # BARPLOT MENSUAL TAT
        # =========================

        st.subheader("Performance TAT mensual")

        with st.expander("Ver lógica del gráfico Performance TAT mensual", expanded=False):
            st.markdown(
                """
                Este gráfico muestra el comportamiento mensual del cumplimiento TAT.

                **Lógica aplicada:**

                1. Se usa la columna `fecha_recepcion_final` como fecha base.
                2. Cada registro se asigna a un mes y año.
                3. La columna `performance_tat` se normaliza en tres estados:
                   - `Cumple`
                   - `No cumple`
                   - `Sin información`
                4. Para cada mes se calcula cuántos registros hay por estado.
                5. Si la métrica seleccionada es **Porcentaje**, cada barra mensual representa el total del mes.
                6. Si la métrica seleccionada es **Recuento**, la barra muestra cantidades absolutas.
                7. Los registros sin `fecha_recepcion_final` no aparecen en este gráfico porque no pueden asignarse a un mes.

                **Interpretación:**

                - Una mayor proporción de `Cumple` indica mejor desempeño TAT mensual.
                - Una mayor proporción de `No cumple` indica desviación respecto al plazo esperado.
                - `Sin información` aparece solo si se activa la opción correspondiente en el filtro lateral.
                """
            )

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
                titulo="Performance TAT mensual - todos los años seleccionados"
            )

        st.divider()

        # =========================
        # CUMPLIMIENTO POR ETAPA
        # =========================

        st.subheader("Cumplimiento por etapa")

        with st.expander("Ver lógica del gráfico Cumplimiento por etapa", expanded=False):
            st.markdown(
                """
                Este bloque muestra el cumplimiento individual de cada etapa del proceso.

                **Etapas evaluadas:**

                - Lib Solped
                - Comprador
                - Proveedor
                - Logística

                **Lógica aplicada:**

                1. Lib Solped:
                   - Si `dx_lib_solped < 2`: `Cumple`.
                   - En caso contrario: `No cumple`.

                2. Comprador:
                   - Si `dx_comprador_1 < 11`: `Cumple`.
                   - En caso contrario: `No cumple`.

                3. Proveedor:
                   - Si `tipo_oc` es 35 o 45 y `dx_proveedor < 20`: `Cumple`.
                   - Si `tipo_oc` es 47 y `dx_proveedor < 60`: `Cumple`.
                   - En caso contrario: `No cumple`.

                4. Logística:
                   - Si `dx_logistica < 10`: `Cumple`.
                   - En caso contrario: `No cumple`.

                **Interpretación:**

                - Un mayor porcentaje de `Cumple` indica que la etapa está dentro del plazo esperado.
                - Un mayor porcentaje de `No cumple` indica retrasos o desviaciones.
                """
            )

        bloque_donuts_cumplimiento(df_filtrado)

        st.divider()

        # =========================
        # TABLA RESUMEN
        # =========================

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

        # =========================
        # DATOS FILTRADOS
        # =========================

        with st.expander("Ver datos filtrados"):
            st.caption(
                f"Mostrando primeras 500 filas de un total filtrado de {len(df_filtrado):,} registros."
            )

            st.dataframe(
                df_filtrado.head(500),
                use_container_width=True
            )

        # =========================
        # DESCARGA
        # =========================

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
