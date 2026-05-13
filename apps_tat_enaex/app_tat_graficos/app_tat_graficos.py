import io
import base64
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import altair as alt


COLORES_ESTADO = {
    "Cumple": "#2E7D32",
    "No cumple": "#D94555",
    "Sin información": "#BDBDBD"
}



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


def convertir_fecha_robusta(serie: pd.Series) -> pd.Series:
    """
    Convierte fechas que pueden venir como:
    - datetime
    - texto de fecha
    - timestamp Unix en milisegundos, segundos o nanosegundos
    """
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_no_nula = serie.dropna()

    if serie_no_nula.empty:
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie_no_nula, errors="coerce")

    if serie_num.notna().mean() >= 0.9:
        mediana = serie_num.dropna().abs().median()

        if mediana > 1e17:
            unidad = "ns"
        elif mediana > 1e14:
            unidad = "us"
        elif mediana > 1e11:
            unidad = "ms"
        else:
            unidad = "s"

        return pd.to_datetime(
            pd.to_numeric(serie, errors="coerce"),
            unit=unidad,
            errors="coerce"
        )

    return pd.to_datetime(serie, errors="coerce")


def preparar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()

    # =========================
    # Mapeo columnas antiguas / nuevas
    # =========================

    columnas_alias = {
        "performance_tat": [
            "performance_tat",
            "performance_tat_total"
        ],
        "dx_lib_solped": [
            "dx_lib_solped",
            "dias_liberacion_solped"
        ],
        "dx_comprador_1": [
            "dx_comprador_1",
            "dias_comprador"
        ],
        "dx_proveedor": [
            "dx_proveedor",
            "dias_proveedor"
        ],
        "dx_logistica": [
            "dx_logistica",
            "dias_logistica"
        ],
        "performance_lib_solped": [
            "performance_lib_solped",
            "performance_liberacion_solped"
        ],
        "performance_comprador_1": [
            "performance_comprador_1",
            "performance_comprador"
        ],
        "performance_proveedor": [
            "performance_proveedor"
        ],
        "performance_logistica": [
            "performance_logistica"
        ]
    }

    def obtener_columna(nombre_estandar: str):
        for col in columnas_alias.get(nombre_estandar, [nombre_estandar]):
            if col in df.columns:
                return col
        return None

    col_fecha = "fecha_recepcion_final"
    col_performance_tat = obtener_columna("performance_tat")

    faltantes = []

    if col_fecha not in df.columns:
        faltantes.append(col_fecha)

    if col_performance_tat is None:
        faltantes.append("performance_tat o performance_tat_total")

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")

    # =========================
    # Fecha base
    # =========================

    df[col_fecha] = convertir_fecha_robusta(df[col_fecha])

    # =========================
    # Performance TAT general
    # =========================

    df["performance_tat_estado"] = df[col_performance_tat].apply(
        normalizar_performance
    )

    # =========================
    # Performance por etapa para donuts
    # Prioridad: columnas performance ya calculadas.
    # Fallback: columnas de días.
    # =========================

    col_dias_lib_solped = obtener_columna("dx_lib_solped")
    col_perf_lib_solped = obtener_columna("performance_lib_solped")

    if col_perf_lib_solped is not None:
        df["performance_lib_solped_estado"] = df[col_perf_lib_solped].apply(
            normalizar_performance
        )
    elif col_dias_lib_solped is not None:
        df["performance_lib_solped_estado"] = df[col_dias_lib_solped].apply(
            performance_dx_lib_solped
        )

    col_dias_comprador = obtener_columna("dx_comprador_1")
    col_perf_comprador = obtener_columna("performance_comprador_1")

    if col_perf_comprador is not None:
        df["performance_comprador_1_estado"] = df[col_perf_comprador].apply(
            normalizar_performance
        )
    elif col_dias_comprador is not None:
        df["performance_comprador_1_estado"] = df[col_dias_comprador].apply(
            performance_dx_comprador
        )

    col_dias_proveedor = obtener_columna("dx_proveedor")
    col_perf_proveedor = obtener_columna("performance_proveedor")

    if col_perf_proveedor is not None:
        df["performance_proveedor_estado"] = df[col_perf_proveedor].apply(
            normalizar_performance
        )
    elif col_dias_proveedor is not None and "tipo_oc" in df.columns:
        df["performance_proveedor_estado"] = df.apply(
            lambda row: performance_proveedor_dax(
                row[col_dias_proveedor],
                row["tipo_oc"]
            ),
            axis=1
        )

    col_dias_logistica = obtener_columna("dx_logistica")
    col_perf_logistica = obtener_columna("performance_logistica")

    if col_perf_logistica is not None:
        df["performance_logistica_estado"] = df[col_perf_logistica].apply(
            normalizar_performance
        )
    elif col_dias_logistica is not None:
        df["performance_logistica_estado"] = df[col_dias_logistica].apply(
            performance_dx_logistica
        )

    # =========================
    # Columnas estándar para que el resto del dashboard siga funcionando
    # =========================

    if col_dias_lib_solped is not None:
        df["dx_lib_solped"] = df[col_dias_lib_solped]

    if col_dias_comprador is not None:
        df["dx_comprador_1"] = df[col_dias_comprador]

    if col_dias_proveedor is not None:
        df["dx_proveedor"] = df[col_dias_proveedor]

    if col_dias_logistica is not None:
        df["dx_logistica"] = df[col_dias_logistica]

    # Si alguna etapa no existe, se crea como Sin información para evitar errores visuales.
    columnas_estado_etapas = [
        "performance_lib_solped_estado",
        "performance_comprador_1_estado",
        "performance_proveedor_estado",
        "performance_logistica_estado"
    ]

    for col in columnas_estado_etapas:
        if col not in df.columns:
            df[col] = "Sin información"

    # =========================
    # Variables de fecha
    # =========================

    df["anio"] = df[col_fecha].dt.year
    df["mes_num"] = df[col_fecha].dt.month

    df["periodo_fecha"] = (
        df[col_fecha]
        .dt.to_period("M")
        .dt.to_timestamp()
    )

    df["periodo_mes"] = (
        df[col_fecha]
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
    Devuelve opciones únicas para una columna categórica.
    Ordena numéricos como números y textos alfabéticamente.
    """
    if columna not in df.columns:
        return []

    serie = df[columna].dropna()

    if serie.empty:
        return []

    serie_str = serie.astype(str).str.strip()

    try:
        serie_num = pd.to_numeric(
            serie_str.str.replace(",", ".", regex=False),
            errors="coerce"
        )

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


def detectar_tipo_columna(df: pd.DataFrame, columna: str) -> str:
    """
    Detecta el tipo de filtro más adecuado para una columna.
    Retorna:
    - fecha
    - numero
    - categoria
    - texto
    """
    if columna not in df.columns:
        return "texto"

    serie = df[columna].dropna()

    if serie.empty:
        return "texto"

    if pd.api.types.is_datetime64_any_dtype(serie):
        return "fecha"

    if pd.api.types.is_bool_dtype(serie):
        return "categoria"

    serie_num = pd.to_numeric(
        serie.astype(str).str.replace(",", ".", regex=False),
        errors="coerce"
    )

    pct_numerico = serie_num.notna().mean()

    if pct_numerico >= 0.9:
        return "numero"

    valores_unicos = serie.astype(str).nunique()

    if valores_unicos <= 50:
        return "categoria"

    return "texto"


def aplicar_filtro_flexible(
    df: pd.DataFrame,
    columna: str,
    config: dict
) -> pd.DataFrame:
    """
    Aplica filtros flexibles según configuración generada en sidebar.
    """
    if columna not in df.columns:
        return df

    if not config:
        return df

    df_out = df.copy()

    tipo = config.get("tipo")
    modo = config.get("modo")
    incluir_vacios = config.get("incluir_vacios", True)

    if not incluir_vacios:
        df_out = df_out[df_out[columna].notna()].copy()

    # =========================
    # Filtro categórico
    # =========================

    if tipo == "categoria":
        seleccionados = config.get("seleccionados", [])

        if seleccionados:
            seleccionados_str = [
                str(x).strip()
                for x in seleccionados
            ]

            df_out = df_out[
                df_out[columna]
                .astype(str)
                .str.strip()
                .isin(seleccionados_str)
            ].copy()

        return df_out

    # =========================
    # Filtro de texto
    # =========================

    if tipo == "texto":
        texto = str(config.get("texto", "")).strip()
        sensible_mayusculas = config.get("sensible_mayusculas", False)

        if not texto:
            return df_out

        serie_texto = df_out[columna].fillna("").astype(str)

        if not sensible_mayusculas:
            serie_texto = serie_texto.str.lower()
            texto_busqueda = texto.lower()
        else:
            texto_busqueda = texto

        if modo == "Contiene":
            mask = serie_texto.str.contains(
                texto_busqueda,
                na=False,
                regex=False
            )

        elif modo == "No contiene":
            mask = ~serie_texto.str.contains(
                texto_busqueda,
                na=False,
                regex=False
            )

        elif modo == "Igual a":
            mask = serie_texto == texto_busqueda

        elif modo == "Distinto de":
            mask = serie_texto != texto_busqueda

        elif modo == "Empieza con":
            mask = serie_texto.str.startswith(
                texto_busqueda,
                na=False
            )

        elif modo == "Termina con":
            mask = serie_texto.str.endswith(
                texto_busqueda,
                na=False
            )

        else:
            mask = pd.Series(True, index=df_out.index)

        return df_out[mask].copy()

    # =========================
    # Filtro numérico
    # =========================

    if tipo == "numero":
        serie_num = pd.to_numeric(
            df_out[columna]
            .astype(str)
            .str.replace(",", ".", regex=False),
            errors="coerce"
        )

        valor = config.get("valor")
        valor_min = config.get("valor_min")
        valor_max = config.get("valor_max")

        if modo == "Entre":
            mask = serie_num.between(valor_min, valor_max)

        elif modo == "Mayor o igual que":
            mask = serie_num >= valor

        elif modo == "Menor o igual que":
            mask = serie_num <= valor

        elif modo == "Mayor que":
            mask = serie_num > valor

        elif modo == "Menor que":
            mask = serie_num < valor

        elif modo == "Igual a":
            mask = serie_num == valor

        elif modo == "Distinto de":
            mask = serie_num != valor

        else:
            mask = pd.Series(True, index=df_out.index)

        return df_out[mask.fillna(False)].copy()

    # =========================
    # Filtro de fecha
    # =========================

    if tipo == "fecha":
        serie_fecha = pd.to_datetime(
            df_out[columna],
            errors="coerce"
        )

        fecha_inicio = config.get("fecha_inicio")
        fecha_fin = config.get("fecha_fin")

        if fecha_inicio and fecha_fin:
            mask = (
                serie_fecha.notna()
                & serie_fecha.dt.date.between(
                    fecha_inicio,
                    fecha_fin
                )
            )

            return df_out[mask].copy()

        return df_out

    return df_out


def crear_filtro_sidebar_columna(
    df: pd.DataFrame,
    columna: str,
    prefijo_key: str = "filtro_flexible"
) -> dict:
    """
    Crea controles Streamlit para una columna y devuelve configuración de filtro.
    """
    tipo_detectado = detectar_tipo_columna(df, columna)

    with st.expander(f"Filtro: {columna}", expanded=True):
        tipo = st.selectbox(
            "Tipo de filtro",
            options=[
                "Automático",
                "Texto",
                "Categoría",
                "Número",
                "Fecha"
            ],
            index=0,
            key=f"{prefijo_key}_{columna}_tipo_selector"
        )

        if tipo == "Automático":
            tipo = tipo_detectado
        else:
            tipo = {
                "Texto": "texto",
                "Categoría": "categoria",
                "Número": "numero",
                "Fecha": "fecha"
            }[tipo]

        incluir_vacios = st.checkbox(
            "Incluir valores vacíos",
            value=True,
            key=f"{prefijo_key}_{columna}_incluir_vacios"
        )

        config = {
            "tipo": tipo,
            "incluir_vacios": incluir_vacios
        }

        st.caption(f"Tipo aplicado: {tipo}")

        # =========================
        # Controles categoría
        # =========================

        if tipo == "categoria":
            opciones = opciones_columna(df, columna)

            seleccionados = st.multiselect(
                "Valores",
                options=opciones,
                key=f"{prefijo_key}_{columna}_categoria_valores"
            )

            config["seleccionados"] = seleccionados

            return config

        # =========================
        # Controles texto
        # =========================

        if tipo == "texto":
            modo = st.selectbox(
                "Condición",
                options=[
                    "Contiene",
                    "No contiene",
                    "Igual a",
                    "Distinto de",
                    "Empieza con",
                    "Termina con"
                ],
                key=f"{prefijo_key}_{columna}_texto_modo"
            )

            texto = st.text_input(
                "Texto a buscar",
                key=f"{prefijo_key}_{columna}_texto_valor"
            )

            sensible_mayusculas = st.checkbox(
                "Distinguir mayúsculas/minúsculas",
                value=False,
                key=f"{prefijo_key}_{columna}_texto_case"
            )

            config["modo"] = modo
            config["texto"] = texto
            config["sensible_mayusculas"] = sensible_mayusculas

            return config

        # =========================
        # Controles número
        # =========================

        if tipo == "numero":
            serie_num = pd.to_numeric(
                df[columna]
                .dropna()
                .astype(str)
                .str.replace(",", ".", regex=False),
                errors="coerce"
            ).dropna()

            if serie_num.empty:
                st.info("No hay valores numéricos válidos en esta columna.")
                return config

            minimo = float(serie_num.min())
            maximo = float(serie_num.max())

            modo = st.selectbox(
                "Condición",
                options=[
                    "Entre",
                    "Mayor o igual que",
                    "Menor o igual que",
                    "Mayor que",
                    "Menor que",
                    "Igual a",
                    "Distinto de"
                ],
                key=f"{prefijo_key}_{columna}_numero_modo"
            )

            config["modo"] = modo

            if modo == "Entre":
                valor_min, valor_max = st.slider(
                    "Rango",
                    min_value=minimo,
                    max_value=maximo,
                    value=(minimo, maximo),
                    key=f"{prefijo_key}_{columna}_numero_rango"
                )

                config["valor_min"] = valor_min
                config["valor_max"] = valor_max

            else:
                valor = st.number_input(
                    "Valor",
                    value=minimo,
                    key=f"{prefijo_key}_{columna}_numero_valor"
                )

                config["valor"] = valor

            return config

        # =========================
        # Controles fecha
        # =========================

        if tipo == "fecha":
            serie_fecha = pd.to_datetime(
                df[columna],
                errors="coerce"
            ).dropna()

            if serie_fecha.empty:
                st.info("No hay fechas válidas en esta columna.")
                return config

            fecha_min = serie_fecha.min().date()
            fecha_max = serie_fecha.max().date()

            fecha_inicio = st.date_input(
                "Desde",
                value=fecha_min,
                min_value=fecha_min,
                max_value=fecha_max,
                key=f"{prefijo_key}_{columna}_fecha_inicio"
            )

            fecha_fin = st.date_input(
                "Hasta",
                value=fecha_max,
                min_value=fecha_min,
                max_value=fecha_max,
                key=f"{prefijo_key}_{columna}_fecha_fin"
            )

            config["fecha_inicio"] = fecha_inicio
            config["fecha_fin"] = fecha_fin

            return config

    return {}


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
    colores = COLORES_ESTADO

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
    texto_promedio: str,
    promedio_solo_dx_positivos: bool = True
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
    pct_negativos = 0
    total_dx_validos = 0
    total_dx_negativos = 0

    if col_dias_incumplimiento in df.columns:
        serie_dx = pd.to_numeric(df[col_dias_incumplimiento], errors="coerce")
        serie_dx_valida = serie_dx.dropna()
        total_dx_validos = int(len(serie_dx_valida))
        total_dx_negativos = int((serie_dx_valida < 0).sum())

        if total_dx_validos > 0:
            pct_negativos = total_dx_negativos / total_dx_validos * 100

        if promedio_solo_dx_positivos:
            serie_promedio = serie_dx_valida[serie_dx_valida >= 0]
        else:
            serie_promedio = serie_dx_valida

        if not serie_promedio.empty:
            promedio_dias = serie_promedio.mean()

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

    etiqueta_promedio = (
        f"{texto_promedio} (solo Dx ≥ 0)"
        if promedio_solo_dx_positivos
        else texto_promedio
    )

    st.markdown(
        f"""
        <div style="text-align:center; margin-top:-6px;">
            <div style="font-size:34px; font-weight:700; color:#222;">
                {promedio_dias:.0f}
            </div>
            <div style="font-size:12px; color:#666;">
                {etiqueta_promedio}
            </div>
            <div style="font-size:12px; color:#D94555; margin-top:4px; font-weight:600;">
                Dx negativos: {pct_negativos:.1f}% ({total_dx_negativos:,}/{total_dx_validos:,})
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def bloque_donuts_cumplimiento(df: pd.DataFrame, promedio_solo_dx_positivos: bool = True):
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
            texto_promedio="Promedio de Dx Lib solped",
            promedio_solo_dx_positivos=promedio_solo_dx_positivos
        )

    with col2:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Comprador",
            col_performance_estado="performance_comprador_1_estado",
            col_dias_incumplimiento="dx_comprador_1",
            regla="Nacional e Internacional &lt; 11",
            texto_promedio="Promedio de Dx Comprador 1",
            promedio_solo_dx_positivos=promedio_solo_dx_positivos
        )

    with col3:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Prov",
            col_performance_estado="performance_proveedor_estado",
            col_dias_incumplimiento="dx_proveedor",
            regla="Nacional &lt; 20<br>Internacional &lt;60",
            texto_promedio="Promedio de Dx Proveedor",
            promedio_solo_dx_positivos=promedio_solo_dx_positivos
        )

    with col4:
        tarjeta_donut_cumplimiento(
            df=df,
            titulo="Logística",
            col_performance_estado="performance_logistica_estado",
            col_dias_incumplimiento="dx_logistica",
            regla="Nacional e Internacional &lt; 10",
            texto_promedio="Promedio de Dx Logística",
            promedio_solo_dx_positivos=promedio_solo_dx_positivos
        )


# =========================================================
# Barplot interactivo con Altair
# =========================================================

def crear_data_barplot_interactivo(
    tabla: pd.DataFrame,
    modo_y: str = "Porcentaje",
    mostrar_sin_info: bool = False
) -> pd.DataFrame:
    """
    Crea la data larga para el barplot mensual.

    Importante:
    - Por defecto NO incluye "Sin información" en el gráfico.
    - Cuando "Sin información" está excluido, los porcentajes se recalculan usando
      solo Cumple + No cumple como total visible.
    - Si se activa mostrar_sin_info, el porcentaje usa Cumple + No cumple + Sin información.
    """
    if tabla.empty:
        return pd.DataFrame()

    tabla = tabla.copy()
    tabla = tabla.sort_values("periodo_fecha").reset_index(drop=True)

    estados = ["Cumple", "No cumple"]

    if mostrar_sin_info:
        estados.append("Sin información")

    data = []

    for _, row in tabla.iterrows():
        total_visible = sum(float(row.get(estado, 0) or 0) for estado in estados)
        total_original = float(row.get("Total", 0) or 0)

        for estado in estados:
            cantidad_estado = float(row.get(estado, 0) or 0)

            porcentaje = (
                cantidad_estado / total_visible * 100
                if total_visible > 0
                else 0
            )

            if modo_y == "Recuento":
                valor = cantidad_estado
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
                "cantidad": cantidad_estado,
                "porcentaje": porcentaje,
                "total_visible": total_visible,
                "total_original": total_original
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

    colores = COLORES_ESTADO

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
                alt.Tooltip("cantidad:Q", title="Cantidad", format=",.0f"),
                alt.Tooltip("porcentaje:Q", title="Porcentaje visible", format=".2f"),
                alt.Tooltip("total_visible:Q", title="Total visible", format=",.0f"),
                alt.Tooltip("total_original:Q", title="Total original", format=",.0f")
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
        <b>performance_tat_total</b> como estado de cumplimiento.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    st.header("Filtros generales")

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

        # =========================
        # Filtros flexibles generales en sidebar
        # =========================

        with st.sidebar:
            st.divider()
            st.subheader("Filtros flexibles por columnas")

            columnas_excluir_filtros = [
                "periodo_fecha",
                "periodo_mes",
                "periodo_label",
                "mes_nombre"
            ]

            columnas_disponibles_filtro = [
                col for col in df.columns
                if col not in columnas_excluir_filtros
            ]

            columnas_filtro_sel = st.multiselect(
                "Selecciona columnas para filtrar",
                options=columnas_disponibles_filtro,
                default=[],
                help=(
                    "Puedes seleccionar columnas de texto, numéricas, fechas o categorías. "
                    "Cada columna tendrá opciones de filtro según su tipo."
                )
            )

            filtros_columnas = {}

            for columna in columnas_filtro_sel:
                filtros_columnas[columna] = crear_filtro_sidebar_columna(
                    df=df,
                    columna=columna,
                    prefijo_key="filtro_flexible"
                )

        df_base = df.copy()

        for columna, config in filtros_columnas.items():
            df_base = aplicar_filtro_flexible(
                df=df_base,
                columna=columna,
                config=config
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

        st.divider()

        # =========================
        # FILTROS POR DEFECTO PARA AMBOS GRÁFICOS
        # =========================

        st.subheader("Filtros por defecto")
        st.caption(
            "Estos filtros aplican tanto al gráfico Performance TAT mensual "
            "como al gráfico Cumplimiento por etapa."
        )

        df_grafico = df_base.copy()

        fechas_validas = df_grafico["fecha_recepcion_final"].dropna()
        fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
        fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

        anios_disponibles = (
            df_grafico["anio"]
            .dropna()
            .astype(int)
            .sort_values()
            .unique()
            .tolist()
        )

        meses_disponibles = (
            df_grafico["mes_num"]
            .dropna()
            .astype(int)
            .sort_values()
            .unique()
            .tolist()
        )

        col_centro = None

        for posible_col_centro in ["Centro - ME5A", "Centro", "Centro - NME80FN"]:
            if posible_col_centro in df_grafico.columns:
                col_centro = posible_col_centro
                break

        centros_disponibles = (
            opciones_columna(df_grafico, col_centro)
            if col_centro is not None
            else []
        )

        with st.container(border=True):
            filtro_col1, filtro_col2, filtro_col3, filtro_col4 = st.columns([1.1, 1.2, 1.6, 1.6])

            with filtro_col1:
                anios_sel = st.multiselect(
                    "Años recepción",
                    options=anios_disponibles,
                    default=anios_disponibles,
                    key="filtros_default_anios_recepcion"
                )

            with filtro_col2:
                meses_sel = st.multiselect(
                    "Meses recepción",
                    options=meses_disponibles,
                    default=meses_disponibles,
                    format_func=lambda x: MESES_NOMBRE.get(int(x), str(x)),
                    key="filtros_default_meses_recepcion"
                )

            with filtro_col3:
                if fecha_min and fecha_max:
                    rango_fechas = st.date_input(
                        "Rango fecha recepción",
                        value=(fecha_min, fecha_max),
                        min_value=fecha_min,
                        max_value=fecha_max,
                        key="filtros_default_rango_fecha_recepcion"
                    )
                else:
                    rango_fechas = None
                    st.info("No hay fechas válidas.")

            with filtro_col4:
                if col_centro is not None and centros_disponibles:
                    centros_sel = st.multiselect(
                        col_centro,
                        options=centros_disponibles,
                        default=[],
                        help="Sin selección = todos los centros.",
                        key="filtros_default_centro_me5a"
                    )
                else:
                    centros_sel = []
                    st.info("No existe columna de centro para filtrar.")

            filtro_col5, filtro_col6, filtro_col7, filtro_col8 = st.columns([1.2, 1.4, 1.4, 1.6])

            with filtro_col5:
                modo_y_barplot = st.radio(
                    "Métrica gráfico mensual",
                    options=[
                        "Porcentaje",
                        "Recuento"
                    ],
                    index=0,
                    horizontal=True,
                    key="filtros_default_modo_y_barplot"
                )

            with filtro_col6:
                mostrar_sin_info = st.checkbox(
                    "Incluir Sin información en mensual",
                    value=False,
                    help=(
                        "Por defecto, el gráfico mensual excluye Sin información "
                        "y recalcula los porcentajes solo con Cumple + No cumple."
                    ),
                    key="filtros_default_mostrar_sin_info"
                )

            with filtro_col7:
                mostrar_meses_sin_datos = st.checkbox(
                    "Mostrar meses sin datos",
                    value=False,
                    key="filtros_default_mostrar_meses_sin_datos"
                )

            with filtro_col8:
                promedio_solo_dx_positivos = st.checkbox(
                    "Promedios de etapa solo con Dx ≥ 0",
                    value=True,
                    help=(
                        "Aplica solo al número promedio mostrado bajo cada donut. "
                        "El porcentaje de Dx negativos se informa debajo de cada promedio."
                    ),
                    key="filtros_default_promedio_dx_positivos"
                )

        # =========================
        # Aplicación filtros por defecto
        # =========================

        if anios_sel:
            df_grafico = df_grafico[df_grafico["anio"].isin(anios_sel)].copy()
        else:
            anios_sel = anios_disponibles

        if meses_sel:
            df_grafico = df_grafico[df_grafico["mes_num"].isin(meses_sel)].copy()
        else:
            meses_sel = meses_disponibles

        if rango_fechas:
            if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
                fecha_inicio, fecha_fin = rango_fechas
            else:
                fecha_inicio = rango_fechas
                fecha_fin = rango_fechas

            if fecha_inicio and fecha_fin:
                if fecha_inicio > fecha_fin:
                    st.error("La fecha de inicio no puede ser mayor que la fecha de fin.")
                    st.stop()

                df_grafico = df_grafico[
                    df_grafico["fecha_recepcion_final"].notna()
                    & df_grafico["fecha_recepcion_final"].dt.date.between(
                        fecha_inicio,
                        fecha_fin
                    )
                ].copy()

        if col_centro is not None and centros_sel:
            centros_sel_str = [str(x).strip() for x in centros_sel]

            df_grafico = df_grafico[
                df_grafico[col_centro]
                .astype(str)
                .str.strip()
                .isin(centros_sel_str)
            ].copy()

        st.divider()

        # =========================
        # BARPLOT MENSUAL TAT
        # =========================

        st.subheader("Performance TAT mensual")

        # =========================
        # Resumen mensual del gráfico
        # =========================

        tabla_resumen = crear_resumen_mensual(df_grafico)

        if mostrar_meses_sin_datos and not tabla_resumen.empty:
            tabla_resumen = completar_meses_anios(
                tabla=tabla_resumen,
                anios=anios_sel
            )

            if meses_sel:
                tabla_resumen = tabla_resumen[
                    tabla_resumen["mes_num"].isin(meses_sel)
                ].copy()

        # =========================
        # KPIs del gráfico
        # =========================

        total_grafico = len(df_grafico)
        cumple = df_grafico["performance_tat_estado"].eq("Cumple").sum()
        no_cumple = df_grafico["performance_tat_estado"].eq("No cumple").sum()
        sin_info = df_grafico["performance_tat_estado"].eq("Sin información").sum()
        total_evaluable = cumple + no_cumple

        pct_cumple = round(cumple / total_evaluable * 100, 2) if total_evaluable > 0 else 0
        pct_no_cumple = round(no_cumple / total_evaluable * 100, 2) if total_evaluable > 0 else 0

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        col1.metric("Filas filtradas", f"{total_grafico:,}")
        col2.metric("Evaluables", f"{total_evaluable:,}")
        col3.metric("Cumple", f"{cumple:,}")
        col4.metric("No cumple", f"{no_cumple:,}")
        col5.metric("% Cumple", f"{pct_cumple}%")
        col6.metric("Sin información", f"{sin_info:,}")

        with st.expander("Ver lógica del gráfico Performance TAT mensual", expanded=False):
            st.markdown(
                """
                Este gráfico muestra el comportamiento mensual del cumplimiento TAT.

                **Lógica aplicada:**

                1. Se usa la columna `fecha_recepcion_final` como fecha base.
                2. Cada registro se asigna a un mes y año.
                3. La columna `performance_tat_total` se normaliza en tres estados:
                   - `Cumple`
                   - `No cumple`
                   - `Sin información`
                4. Por defecto, el gráfico excluye `Sin información`.
                5. Si la métrica seleccionada es **Porcentaje**, el porcentaje se calcula sobre el total visible:
                   - Por defecto: `Cumple + No cumple`.
                   - Si activas `Incluir Sin información`: `Cumple + No cumple + Sin información`.
                6. Si la métrica seleccionada es **Recuento**, la barra muestra cantidades absolutas.
                7. Los registros sin `fecha_recepcion_final` no aparecen en este gráfico porque no pueden asignarse a un mes.

                **Interpretación:**

                - Una mayor proporción de `Cumple` indica mejor desempeño TAT mensual.
                - Una mayor proporción de `No cumple` indica desviación respecto al plazo esperado.
                - `Sin información` aparece solo si se activa la opción correspondiente en el bloque de filtros por defecto.
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
                titulo="Performance TAT mensual"
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
                   - Si `dias_liberacion_solped < 2`: `Cumple`.
                   - En caso contrario: `No cumple`.

                2. Comprador:
                   - Si `dias_comprador < 11`: `Cumple`.
                   - En caso contrario: `No cumple`.

                3. Proveedor:
                   - Si `tipo_oc` es 35 o 45 y `dias_proveedor < 20`: `Cumple`.
                   - Si `tipo_oc` es 47 y `dias_proveedor < 60`: `Cumple`.
                   - En caso contrario: `No cumple`.

                4. Logística:
                   - Si `dias_logistica < 10`: `Cumple`.
                   - En caso contrario: `No cumple`.

                **Promedios de días:**

                - Por defecto, el promedio mostrado bajo cada donut se calcula solo con Dx mayores o iguales a cero.
                - Debajo de cada promedio se informa qué porcentaje de registros tiene Dx negativo.
                - Puedes desactivar ese filtro en el bloque de filtros por defecto para calcular el promedio con todos los Dx válidos.

                **Interpretación:**

                - Un mayor porcentaje de `Cumple` indica que la etapa está dentro del plazo esperado.
                - Un mayor porcentaje de `No cumple` indica retrasos o desviaciones.
                """
            )

        bloque_donuts_cumplimiento(
            df=df_grafico,
            promedio_solo_dx_positivos=promedio_solo_dx_positivos
        )

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
                f"Mostrando primeras 500 filas de un total filtrado de {len(df_grafico):,} registros."
            )

            st.dataframe(
                df_grafico.head(500),
                use_container_width=True
            )

        # =========================
        # DESCARGA
        # =========================

        st.subheader("Descarga")

        col_d1, col_d2 = st.columns(2)

        with col_d1:
            csv_bytes = convertir_a_csv(df_grafico)

            st.download_button(
                label="Descargar datos filtrados CSV",
                data=csv_bytes,
                file_name="performance_tat_filtrado.csv",
                mime="text/csv"
            )

        with col_d2:
            parquet_bytes = convertir_a_parquet(df_grafico)

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
