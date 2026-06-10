# ============================================================
# 02_APP_INDICADORES_FINANCIEROS_BANCO_CENTRAL
# Consulta indicadores financieros Banco Central de Chile
# Dólar, UF, UTM, IPC, ICL, IR
# ============================================================

import base64
from pathlib import Path
from datetime import date, timedelta
from io import BytesIO
from typing import Callable

import pandas as pd
import requests
import streamlit as st


# ============================================================
# Rutas del proyecto
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

# Logo ubicado en:
# PROYECTOS-ENAEX/assets/logo.svg
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# Configuración general
# ============================================================

st.set_page_config(
    page_title="Indicadores Financieros Banco Central",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# Constantes Banco Central
# ============================================================

URL_BDE = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"


# ============================================================
# Diccionario de indicadores financieros
# ============================================================

SERIES_INDICADORES = {
    "USD_DIARIO": {
        "seriesId": "F073.TCO.PRE.Z.D",
        "nombre": "Dólar observado diario",
        "grupo": "Dólar observado",
        "frecuencia": "DAILY",
        "unidad": "CLP por USD",
        "descripcion_corta": "Tipo de cambio nominal diario, dólar observado.",
    },
    "USD_MENSUAL": {
        "seriesId": "F073.TCO.PRE.HIST.M",
        "nombre": "Dólar observado mensual histórico",
        "grupo": "Dólar observado",
        "frecuencia": "MONTHLY",
        "unidad": "CLP por USD",
        "descripcion_corta": "Promedio mensual histórico del dólar observado.",
    },
    "USD_ANUAL": {
        "seriesId": "F073.TCO.PRE.Z.A",
        "nombre": "Dólar observado anual",
        "grupo": "Dólar observado",
        "frecuencia": "ANNUAL",
        "unidad": "CLP por USD",
        "descripcion_corta": "Serie anual del dólar observado.",
    },
    "UF": {
        "seriesId": "F073.UFF.PRE.Z.D",
        "nombre": "Unidad de Fomento",
        "grupo": "UF / UTM",
        "frecuencia": "DAILY",
        "unidad": "CLP por UF",
        "descripcion_corta": "Valor diario de la Unidad de Fomento.",
    },
    "UTM": {
        "seriesId": "F073.UTR.PRE.Z.M",
        "nombre": "Unidad Tributaria Mensual",
        "grupo": "UF / UTM",
        "frecuencia": "MONTHLY",
        "unidad": "CLP por UTM",
        "descripcion_corta": "Valor mensual de la Unidad Tributaria Mensual.",
    },
    "IPC": {
        "seriesId": "F074.IPC.IND.Z.2023.C.M",
        "nombre": "IPC general",
        "grupo": "IPC",
        "frecuencia": "MONTHLY",
        "unidad": "Índice base 2023=100",
        "descripcion_corta": "Índice de Precios al Consumidor general.",
    },
    "IPC_VAR_MENSUAL": {
        "seriesId": "F074.IPC.VAR.Z.2023.C.M",
        "nombre": "IPC variación mensual",
        "grupo": "IPC",
        "frecuencia": "MONTHLY",
        "unidad": "Porcentaje",
        "descripcion_corta": "Variación mensual del IPC.",
    },
    "IPC_VAR_ANUAL": {
        "seriesId": "F074.IPC.VAR.Z.Z.C.A",
        "nombre": "IPC variación anual",
        "grupo": "IPC",
        "frecuencia": "ANNUAL",
        "unidad": "Porcentaje",
        "descripcion_corta": "Variación anual histórica del IPC.",
    },
    "ICL": {
        "seriesId": "G049.CMH.IND.INE23.Z.M",
        "nombre": "Índice de Costos Laborales",
        "grupo": "ICL",
        "frecuencia": "MONTHLY",
        "unidad": "Índice base 2023=100",
        "descripcion_corta": "ICL referencial INE, base 2023=100.",
    },
    "ICL_EMPALMADA": {
        "seriesId": "G049.CMH.IND.INE23.NE.M",
        "nombre": "Índice de Costos Laborales empalmada",
        "grupo": "ICL",
        "frecuencia": "MONTHLY",
        "unidad": "Índice base 2023=100",
        "descripcion_corta": "ICL empalmado INE, base 2023=100.",
    },
    "ICL_VAR_ANUAL": {
        "seriesId": "G049.CMH.V12.INE23.Z.M",
        "nombre": "ICL variación anual",
        "grupo": "ICL",
        "frecuencia": "MONTHLY",
        "unidad": "Porcentaje",
        "descripcion_corta": "Variación en 12 meses del ICL.",
    },
    "ICL_VAR_MENSUAL": {
        "seriesId": "G049.CMH.VAR.INE23.Z.M",
        "nombre": "ICL variación mensual",
        "grupo": "ICL",
        "frecuencia": "MONTHLY",
        "unidad": "Porcentaje",
        "descripcion_corta": "Variación mensual del ICL.",
    },
    "IR": {
        "seriesId": "G049.RMM.IND.INE23.Z.M",
        "nombre": "Índice de Remuneraciones nominal",
        "grupo": "IR",
        "frecuencia": "MONTHLY",
        "unidad": "Índice base 2023=100",
        "descripcion_corta": "IR nominal referencial INE, base 2023=100.",
    },
    "IR_EMPALMADA": {
        "seriesId": "G049.RMM.IND.INE23.NE.M",
        "nombre": "Índice de Remuneraciones nominal empalmada",
        "grupo": "IR",
        "frecuencia": "MONTHLY",
        "unidad": "Índice base 2023=100",
        "descripcion_corta": "IR nominal empalmado INE, base 2023=100.",
    },
    "IR_REAL": {
        "seriesId": "G049.RMM.IND.INE23.82.M",
        "nombre": "Índice real de remuneraciones",
        "grupo": "IR",
        "frecuencia": "MONTHLY",
        "unidad": "Índice real",
        "descripcion_corta": "IR real referencial INE.",
    },
    "IR_REAL_EMPALMADA": {
        "seriesId": "G049.RMM.IND.INE23.R.M",
        "nombre": "Índice real de remuneraciones empalmada",
        "grupo": "IR",
        "frecuencia": "MONTHLY",
        "unidad": "Índice real",
        "descripcion_corta": "IR real empalmado INE.",
    },
    "IR_VAR_ANUAL": {
        "seriesId": "G049.RMM.V12.INE23.Z.M",
        "nombre": "IR variación anual",
        "grupo": "IR",
        "frecuencia": "MONTHLY",
        "unidad": "Porcentaje",
        "descripcion_corta": "Variación en 12 meses del IR nominal.",
    },
    "IR_VAR_MENSUAL": {
        "seriesId": "G049.RMM.VAR.INE23.Z.M",
        "nombre": "IR variación mensual",
        "grupo": "IR",
        "frecuencia": "MONTHLY",
        "unidad": "Porcentaje",
        "descripcion_corta": "Variación mensual del IR nominal.",
    },
}


# ============================================================
# Logo centrado
# ============================================================

def mostrar_logo_centrado() -> None:
    """Muestra el logo corporativo centrado."""
    if LOGO_PATH.exists():
        logo_svg = LOGO_PATH.read_text(encoding="utf-8")

        logo_base64 = base64.b64encode(
            logo_svg.encode("utf-8")
        ).decode("utf-8")

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
                    alt="ENAEX"
                >
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# Credenciales
# ============================================================

def obtener_credenciales() -> tuple[str, str]:
    """
    Obtiene credenciales desde Streamlit Secrets.

    En .streamlit/secrets.toml local o en Streamlit Cloud → Settings → Secrets:

    [bde]
    user = "TU_USUARIO"
    password = "TU_CLAVE"
    """
    try:
        user = st.secrets["bde"]["user"]
        password = st.secrets["bde"]["password"]

        if not user or not password:
            st.error("Credenciales BDE vacías en secrets.")
            st.stop()

        return user, password

    except Exception:
        st.error(
            """
            No se encontraron credenciales BDE en Streamlit Secrets.

            Debes configurar:

            [bde]
            user = "TU_USUARIO"
            password = "TU_CLAVE"
            """
        )
        st.stop()


# ============================================================
# Utilidades
# ============================================================

def obtener_catalogo_indicadores() -> pd.DataFrame:
    """Convierte el diccionario de indicadores en DataFrame."""

    registros = []

    for codigo, meta in SERIES_INDICADORES.items():
        registros.append(
            {
                "codigo": codigo,
                "nombre": meta["nombre"],
                "grupo": meta["grupo"],
                "frecuencia": meta["frecuencia"],
                "unidad": meta["unidad"],
                "seriesId": meta["seriesId"],
                "descripcion_corta": meta["descripcion_corta"],
            }
        )

    df_catalogo = pd.DataFrame(registros)
    df_catalogo = df_catalogo.sort_values(
        by=["grupo", "codigo"]
    ).reset_index(drop=True)

    return df_catalogo


def formatear_fecha(fecha: date) -> str:
    """Convierte una fecha a formato yyyy-mm-dd para la API."""
    return fecha.strftime("%Y-%m-%d")


def obtener_meses() -> dict[str, int]:
    """Devuelve diccionario de meses en español."""
    return {
        "Enero": 1,
        "Febrero": 2,
        "Marzo": 3,
        "Abril": 4,
        "Mayo": 5,
        "Junio": 6,
        "Julio": 7,
        "Agosto": 8,
        "Septiembre": 9,
        "Octubre": 10,
        "Noviembre": 11,
        "Diciembre": 12,
    }


def ultimo_dia_mes(anio: int, mes: int) -> date:
    """Devuelve el último día de un mes."""
    if mes == 12:
        return date(anio, 12, 31)

    primer_dia_mes_siguiente = date(anio, mes + 1, 1)
    return primer_dia_mes_siguiente - timedelta(days=1)


def construir_rango_desde_anios_meses(
    anio_desde: int,
    anio_hasta: int,
    mes_desde: int,
    mes_hasta: int,
) -> tuple[date, date]:
    """
    Construye fecha desde y fecha hasta usando año y mes.

    - Fecha desde: primer día del mes desde.
    - Fecha hasta: último día del mes hasta.
    - Si la fecha hasta supera la fecha actual, se ajusta a hoy.
    """

    fecha_desde = date(anio_desde, mes_desde, 1)
    fecha_hasta = ultimo_dia_mes(anio_hasta, mes_hasta)

    if fecha_hasta > date.today():
        fecha_hasta = date.today()

    return fecha_desde, fecha_hasta


def validar_rango_fechas(fecha_desde: date, fecha_hasta: date) -> None:
    """Valida que el rango de fechas sea correcto."""

    if fecha_desde > fecha_hasta:
        st.error(
            """
            El rango seleccionado no es válido.

            Revisa que el año/mes inicial no sea posterior al año/mes final.
            """
        )
        st.stop()

    if fecha_hasta > date.today():
        st.error("La fecha hasta no puede ser posterior a hoy.")
        st.stop()


def formato_valor(valor: float, unidad: str) -> str:
    """Formatea un valor según unidad."""

    if pd.isna(valor):
        return "-"

    if "CLP" in unidad:
        return f"{valor:,.2f}"

    if "Porcentaje" in unidad:
        return f"{valor:,.4f}%"

    return f"{valor:,.4f}"


# ============================================================
# Selección de indicadores con checkbox
# ============================================================

def obtener_codigos_dolar() -> list[str]:
    """Indicadores marcados por defecto."""
    return [
        codigo
        for codigo, meta in SERIES_INDICADORES.items()
        if meta["grupo"] == "Dólar observado"
    ]


def seleccionar_indicadores_con_checkboxes(
    df_catalogo: pd.DataFrame,
) -> list[str]:
    """
    Permite seleccionar indicadores usando checkboxes.

    Por defecto quedan marcados los indicadores de dólar observado.
    """

    st.subheader("Selección de indicadores")

    st.caption(
        """
        Por defecto quedan marcados los indicadores de dólar observado.
        Puedes marcar UF, UTM, IPC, ICL, IR u otros indicadores adicionales.
        """
    )

    codigos_dolar = obtener_codigos_dolar()
    codigos_seleccionados = []

    grupos = sorted(df_catalogo["grupo"].unique().tolist())

    for grupo in grupos:
        df_grupo = df_catalogo[df_catalogo["grupo"] == grupo].copy()

        expanded = grupo == "Dólar observado"

        with st.expander(f"{grupo}", expanded=expanded):
            for row in df_grupo.itertuples(index=False):
                codigo = row.codigo
                nombre = row.nombre
                frecuencia = row.frecuencia
                unidad = row.unidad
                descripcion = row.descripcion_corta

                marcado_default = codigo in codigos_dolar

                seleccionado = st.checkbox(
                    label=f"{codigo} - {nombre}",
                    value=marcado_default,
                    key=f"chk_indicador_{codigo}",
                    help=f"{descripcion} | Frecuencia: {frecuencia} | Unidad: {unidad}",
                )

                if seleccionado:
                    codigos_seleccionados.append(codigo)

    if not codigos_seleccionados:
        st.warning("Debes seleccionar al menos un indicador.")
        st.stop()

    return codigos_seleccionados


# ============================================================
# Consulta API BDE
# ============================================================

@st.cache_data(ttl=3600, show_spinner=False)
def consultar_serie_temporal_bde(
    user: str,
    password: str,
    codigo: str,
    series_id: str,
    nombre: str,
    grupo: str,
    frecuencia: str,
    unidad: str,
    fecha_desde: date,
    fecha_hasta: date,
) -> pd.DataFrame:
    """
    Consulta una serie BDE y devuelve todo el histórico dentro del rango.
    """

    params = {
        "user": user,
        "pass": password,
        "function": "GetSeries",
        "timeseries": series_id,
        "firstdate": formatear_fecha(fecha_desde),
        "lastdate": formatear_fecha(fecha_hasta),
    }

    try:
        response = requests.get(URL_BDE, params=params, timeout=60)
        response.raise_for_status()

        data = response.json()

        if data.get("Codigo") != 0:
            return pd.DataFrame(
                [
                    {
                        "codigo": codigo,
                        "nombre": nombre,
                        "grupo": grupo,
                        "frecuencia": frecuencia,
                        "unidad": unidad,
                        "fecha": pd.NaT,
                        "valor": pd.NA,
                        "descripcion_bde": data.get("Descripcion"),
                        "seriesId": series_id,
                        "estado": "ERROR_BDE",
                    }
                ]
            )

        obs = data.get("Series", {}).get("Obs", [])

        if not obs:
            return pd.DataFrame(
                [
                    {
                        "codigo": codigo,
                        "nombre": nombre,
                        "grupo": grupo,
                        "frecuencia": frecuencia,
                        "unidad": unidad,
                        "fecha": pd.NaT,
                        "valor": pd.NA,
                        "descripcion_bde": "Sin observaciones para el rango consultado",
                        "seriesId": series_id,
                        "estado": "SIN_DATOS",
                    }
                ]
            )

        df = pd.DataFrame(obs)

        df["fecha"] = pd.to_datetime(
            df["indexDateString"],
            format="%d-%m-%Y",
            errors="coerce",
        )

        df["valor"] = pd.to_numeric(
            df["value"],
            errors="coerce",
        )

        df = df.dropna(subset=["fecha", "valor"])

        if df.empty:
            return pd.DataFrame(
                [
                    {
                        "codigo": codigo,
                        "nombre": nombre,
                        "grupo": grupo,
                        "frecuencia": frecuencia,
                        "unidad": unidad,
                        "fecha": pd.NaT,
                        "valor": pd.NA,
                        "descripcion_bde": "Sin observaciones válidas",
                        "seriesId": series_id,
                        "estado": "SIN_DATOS",
                    }
                ]
            )

        df = df[
            (df["fecha"].dt.date >= fecha_desde)
            & (df["fecha"].dt.date <= fecha_hasta)
        ].copy()

        descripcion_bde = data.get("Series", {}).get("descripEsp")
        series_id_real = data.get("Series", {}).get("seriesId", series_id)

        df["codigo"] = codigo
        df["nombre"] = nombre
        df["grupo"] = grupo
        df["frecuencia"] = frecuencia
        df["unidad"] = unidad
        df["descripcion_bde"] = descripcion_bde
        df["seriesId"] = series_id_real
        df["estado"] = "OK"

        df = df[
            [
                "codigo",
                "nombre",
                "grupo",
                "frecuencia",
                "unidad",
                "fecha",
                "valor",
                "descripcion_bde",
                "seriesId",
                "estado",
            ]
        ].sort_values("fecha").reset_index(drop=True)

        return df

    except Exception as e:
        return pd.DataFrame(
            [
                {
                    "codigo": codigo,
                    "nombre": nombre,
                    "grupo": grupo,
                    "frecuencia": frecuencia,
                    "unidad": unidad,
                    "fecha": pd.NaT,
                    "valor": pd.NA,
                    "descripcion_bde": f"Error de consulta: {e}",
                    "seriesId": series_id,
                    "estado": "ERROR_CONSULTA",
                }
            ]
        )


def consultar_indicadores_bde(
    user: str,
    password: str,
    codigos_seleccionados: list[str],
    fecha_desde: date,
    fecha_hasta: date,
    progress_callback: Callable[[int, int, str], None] | None = None,
) -> pd.DataFrame:
    """
    Consulta uno o más indicadores financieros de la BDE.
    """

    resultados = []
    total = len(codigos_seleccionados)

    for i, codigo in enumerate(codigos_seleccionados, start=1):
        meta = SERIES_INDICADORES[codigo]

        if progress_callback is not None:
            progress_callback(i, total, codigo)

        df_serie = consultar_serie_temporal_bde(
            user=user,
            password=password,
            codigo=codigo,
            series_id=meta["seriesId"],
            nombre=meta["nombre"],
            grupo=meta["grupo"],
            frecuencia=meta["frecuencia"],
            unidad=meta["unidad"],
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
        )

        resultados.append(df_serie)

    if not resultados:
        return pd.DataFrame()

    df_final = pd.concat(resultados, ignore_index=True)
    df_final = df_final.sort_values(
        by=["grupo", "codigo", "fecha"]
    ).reset_index(drop=True)

    return df_final


# ============================================================
# Resúmenes
# ============================================================

def crear_resumen_ultimos_valores(df_historico: pd.DataFrame) -> pd.DataFrame:
    """
    Crea resumen con último valor disponible por indicador.
    """

    if df_historico.empty:
        return pd.DataFrame()

    df_ok = df_historico[
        (df_historico["estado"] == "OK")
        & df_historico["fecha"].notna()
        & df_historico["valor"].notna()
    ].copy()

    if df_ok.empty:
        return pd.DataFrame()

    df_resumen = (
        df_ok.sort_values("fecha")
        .groupby(
            [
                "codigo",
                "nombre",
                "grupo",
                "frecuencia",
                "unidad",
                "seriesId",
            ],
            as_index=False,
        )
        .tail(1)
        .reset_index(drop=True)
    )

    df_resumen = df_resumen[
        [
            "codigo",
            "nombre",
            "grupo",
            "frecuencia",
            "unidad",
            "fecha",
            "valor",
            "seriesId",
        ]
    ].sort_values(["grupo", "codigo"]).reset_index(drop=True)

    return df_resumen


def crear_resumen_estadistico(df_historico: pd.DataFrame) -> pd.DataFrame:
    """
    Crea estadísticas básicas por indicador.
    """

    if df_historico.empty:
        return pd.DataFrame()

    df_ok = df_historico[
        (df_historico["estado"] == "OK")
        & df_historico["fecha"].notna()
        & df_historico["valor"].notna()
    ].copy()

    if df_ok.empty:
        return pd.DataFrame()

    resumen = (
        df_ok.groupby(
            ["codigo", "nombre", "grupo", "frecuencia", "unidad"],
            as_index=False,
        )
        .agg(
            observaciones=("valor", "count"),
            fecha_min=("fecha", "min"),
            fecha_max=("fecha", "max"),
            valor_min=("valor", "min"),
            valor_max=("valor", "max"),
            valor_promedio=("valor", "mean"),
            ultimo_valor=("valor", "last"),
        )
    )

    resumen = resumen.sort_values(
        by=["grupo", "codigo"]
    ).reset_index(drop=True)

    return resumen


def crear_resumen_calidad_datos(df_historico: pd.DataFrame) -> pd.DataFrame:
    """
    Resume estados de consulta por indicador.
    """

    if df_historico.empty:
        return pd.DataFrame()

    resumen = (
        df_historico.groupby(
            ["codigo", "nombre", "grupo", "frecuencia", "unidad", "estado"],
            as_index=False,
        )
        .agg(
            registros=("codigo", "count"),
            fecha_min=("fecha", "min"),
            fecha_max=("fecha", "max"),
        )
        .sort_values(["grupo", "codigo", "estado"])
        .reset_index(drop=True)
    )

    return resumen


# ============================================================
# Gráficos
# ============================================================

def preparar_pivot_serie_temporal(df_ok: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte histórico largo a matriz fecha x indicador.
    """

    df_plot = df_ok.copy()
    df_plot["fecha"] = pd.to_datetime(df_plot["fecha"])
    df_plot = df_plot.sort_values(["fecha", "codigo"])

    pivot = df_plot.pivot_table(
        index="fecha",
        columns="codigo",
        values="valor",
        aggfunc="mean",
    )

    pivot = pivot.sort_index()

    return pivot


def preparar_base_100(df_ok: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza cada indicador a base 100 usando su primer valor disponible.
    Esto permite comparar indicadores con distintas unidades.
    """

    df_base = df_ok[
        (df_ok["estado"] == "OK")
        & df_ok["fecha"].notna()
        & df_ok["valor"].notna()
    ].copy()

    if df_base.empty:
        return pd.DataFrame()

    df_base = df_base.sort_values(["codigo", "fecha"])

    primeros = (
        df_base.groupby("codigo", as_index=False)
        .first()[["codigo", "valor"]]
        .rename(columns={"valor": "valor_inicial"})
    )

    df_base = df_base.merge(primeros, on="codigo", how="left")

    df_base = df_base[
        df_base["valor_inicial"].notna()
        & (df_base["valor_inicial"] != 0)
    ].copy()

    df_base["valor_base_100"] = (
        df_base["valor"] / df_base["valor_inicial"]
    ) * 100

    pivot_base_100 = df_base.pivot_table(
        index="fecha",
        columns="codigo",
        values="valor_base_100",
        aggfunc="mean",
    )

    pivot_base_100 = pivot_base_100.sort_index()

    return pivot_base_100


def mostrar_graficos_series_temporales(df_ok: pd.DataFrame) -> None:
    """
    Muestra gráficos de serie temporal para todos los indicadores seleccionados.
    """

    st.subheader("Gráficos de series temporales")

    if df_ok.empty:
        st.warning("No hay datos válidos para graficar.")
        return

    tab_base_100, tab_por_unidad, tab_matriz = st.tabs(
        [
            "Comparativo base 100",
            "Valores originales por unidad",
            "Matriz temporal",
        ]
    )

    with tab_base_100:
        st.caption(
            """
            Este gráfico normaliza cada indicador a 100 en su primer dato disponible.
            Es ideal para comparar tendencias aunque las unidades sean distintas.
            """
        )

        pivot_base_100 = preparar_base_100(df_ok)

        if pivot_base_100.empty:
            st.warning("No fue posible construir el gráfico base 100.")
        else:
            st.line_chart(
                pivot_base_100,
                use_container_width=True,
            )

    with tab_por_unidad:
        st.caption(
            """
            Los valores originales se grafican agrupados por unidad.
            Esto evita mezclar escalas incompatibles en un mismo eje.
            """
        )

        unidades = sorted(df_ok["unidad"].dropna().unique().tolist())

        for unidad in unidades:
            df_unidad = df_ok[df_ok["unidad"] == unidad].copy()

            if df_unidad.empty:
                continue

            codigos_unidad = sorted(df_unidad["codigo"].unique().tolist())

            with st.expander(
                f"{unidad} | {len(codigos_unidad)} indicador(es)",
                expanded=True,
            ):
                pivot_unidad = preparar_pivot_serie_temporal(df_unidad)

                if pivot_unidad.empty:
                    st.warning(f"No hay datos para graficar unidad: {unidad}")
                else:
                    st.line_chart(
                        pivot_unidad,
                        use_container_width=True,
                    )

    with tab_matriz:
        st.caption(
            """
            Matriz fecha x indicador con valores originales.
            Útil para revisar rápidamente datos faltantes y comparar observaciones.
            """
        )

        pivot_original = preparar_pivot_serie_temporal(df_ok)

        if pivot_original.empty:
            st.warning("No fue posible construir la matriz temporal.")
        else:
            st.dataframe(
                pivot_original.round(6),
                use_container_width=True,
            )


# ============================================================
# Exportación Excel
# ============================================================

def dataframe_a_excel(
    df_historico: pd.DataFrame,
    df_ultimos: pd.DataFrame,
    df_resumen: pd.DataFrame,
    df_calidad: pd.DataFrame,
    df_catalogo: pd.DataFrame,
    df_base_100: pd.DataFrame,
    df_matriz_original: pd.DataFrame,
) -> bytes:
    """Genera un archivo Excel en memoria con varias hojas."""

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_historico.to_excel(
            writer,
            index=False,
            sheet_name="Historico",
        )

        df_ultimos.to_excel(
            writer,
            index=False,
            sheet_name="Ultimos_Valores",
        )

        df_resumen.to_excel(
            writer,
            index=False,
            sheet_name="Resumen_Estadistico",
        )

        df_calidad.to_excel(
            writer,
            index=False,
            sheet_name="Calidad_Datos",
        )

        df_catalogo.to_excel(
            writer,
            index=False,
            sheet_name="Catalogo_Indicadores",
        )

        if not df_base_100.empty:
            df_base_100.to_excel(
                writer,
                index=True,
                sheet_name="Serie_Base_100",
            )

        if not df_matriz_original.empty:
            df_matriz_original.to_excel(
                writer,
                index=True,
                sheet_name="Matriz_Original",
            )

    return output.getvalue()


# ============================================================
# Página principal
# ============================================================

def main() -> None:
    mostrar_logo_centrado()

    st.markdown(
        "<h1 style='text-align: center;'>Indicadores Financieros Banco Central</h1>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px;'>
            Consulta, compara y descarga indicadores financieros del Banco Central de Chile.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    user, password = obtener_credenciales()

    df_catalogo = obtener_catalogo_indicadores()

    # --------------------------------------------------------
    # Sidebar: configuración de rango temporal
    # --------------------------------------------------------

    st.sidebar.header("Configuración de consulta")

    meses = obtener_meses()
    nombres_meses = list(meses.keys())

    anio_actual = date.today().year

    anio_minimo = 2010
    anio_maximo = max(2026, anio_actual)

    anios_disponibles = list(range(anio_minimo, anio_maximo + 1))

    anio_desde_default = 2024
    anio_hasta_default = 2026

    if anio_desde_default not in anios_disponibles:
        anio_desde_default = anios_disponibles[0]

    if anio_hasta_default not in anios_disponibles:
        anio_hasta_default = anio_actual

    with st.sidebar:
        st.subheader("Rango temporal")

        col_sb_1, col_sb_2 = st.columns(2)

        with col_sb_1:
            anio_desde = st.selectbox(
                "Año desde",
                options=anios_disponibles,
                index=anios_disponibles.index(anio_desde_default),
            )

        with col_sb_2:
            anio_hasta = st.selectbox(
                "Año hasta",
                options=anios_disponibles,
                index=anios_disponibles.index(anio_hasta_default),
            )

        col_sb_3, col_sb_4 = st.columns(2)

        with col_sb_3:
            mes_desde_nombre = st.selectbox(
                "Mes desde",
                options=nombres_meses,
                index=0,
            )

        with col_sb_4:
            mes_hasta_nombre = st.selectbox(
                "Mes hasta",
                options=nombres_meses,
                index=11,
            )

    fecha_desde, fecha_hasta = construir_rango_desde_anios_meses(
        anio_desde=anio_desde,
        anio_hasta=anio_hasta,
        mes_desde=meses[mes_desde_nombre],
        mes_hasta=meses[mes_hasta_nombre],
    )

    validar_rango_fechas(fecha_desde, fecha_hasta)

    # --------------------------------------------------------
    # Selección de indicadores
    # --------------------------------------------------------

    col_sel, col_info = st.columns([2, 1])

    with col_sel:
        codigos_seleccionados = seleccionar_indicadores_con_checkboxes(
            df_catalogo=df_catalogo,
        )

    with col_info:
        st.subheader("Resumen de selección")

        st.metric(
            "Indicadores seleccionados",
            len(codigos_seleccionados),
        )

        st.metric(
            "Desde",
            fecha_desde.strftime("%Y-%m-%d"),
        )

        st.metric(
            "Hasta",
            fecha_hasta.strftime("%Y-%m-%d"),
        )

        df_seleccion = df_catalogo[
            df_catalogo["codigo"].isin(codigos_seleccionados)
        ].copy()

        st.dataframe(
            df_seleccion[
                [
                    "codigo",
                    "nombre",
                    "grupo",
                    "frecuencia",
                    "unidad",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    # --------------------------------------------------------
    # Catálogo completo
    # --------------------------------------------------------

    with st.expander("Ver catálogo completo de indicadores disponibles", expanded=False):
        st.dataframe(
            df_catalogo,
            use_container_width=True,
            hide_index=True,
        )

    consultar = st.button(
        "Consultar Banco Central",
        type="primary",
        use_container_width=True,
    )

    st.markdown("---")

    if not consultar:
        st.success(
            """
            Selecciona los indicadores con checkbox y presiona
            **Consultar Banco Central** para cargar las series temporales.
            """
        )
        return

    # --------------------------------------------------------
    # Barra de progreso
    # --------------------------------------------------------

    st.subheader("Progreso de consulta")

    progress_bar = st.progress(0)
    progress_text = st.empty()

    def actualizar_progreso(actual: int, total: int, codigo: str) -> None:
        porcentaje = int((actual / total) * 100)
        progress_bar.progress(porcentaje)
        progress_text.info(
            f"Consultando {codigo}... {actual} de {total} series procesadas ({porcentaje}%)."
        )

    with st.spinner("Consultando datos en Banco Central..."):
        df_historico = consultar_indicadores_bde(
            user=user,
            password=password,
            codigos_seleccionados=codigos_seleccionados,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            progress_callback=actualizar_progreso,
        )

        progress_text.info("Construyendo resúmenes, matrices y gráficos...")
        progress_bar.progress(90)

        df_ultimos = crear_resumen_ultimos_valores(df_historico)
        df_resumen = crear_resumen_estadistico(df_historico)
        df_calidad = crear_resumen_calidad_datos(df_historico)

        progress_bar.progress(100)
        progress_text.success("Consulta finalizada correctamente.")

    # --------------------------------------------------------
    # Validación resultados
    # --------------------------------------------------------

    if df_historico.empty:
        st.warning("La consulta no devolvió datos.")
        return

    df_ok = df_historico[df_historico["estado"] == "OK"].copy()

    if df_ok.empty:
        st.error("No se obtuvieron observaciones válidas para el rango seleccionado.")
        st.dataframe(df_historico, use_container_width=True, hide_index=True)
        return

    # --------------------------------------------------------
    # KPIs principales
    # --------------------------------------------------------

    st.subheader("Resumen de consulta")

    total_observaciones = len(df_ok)
    total_indicadores_ok = df_ok["codigo"].nunique()
    fecha_min = df_ok["fecha"].min()
    fecha_max = df_ok["fecha"].max()
    grupos_consultados = df_ok["grupo"].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Indicadores con datos",
        total_indicadores_ok,
    )

    col2.metric(
        "Grupos",
        grupos_consultados,
    )

    col3.metric(
        "Observaciones",
        total_observaciones,
    )

    col4.metric(
        "Fecha mínima",
        fecha_min.strftime("%Y-%m-%d"),
    )

    col5.metric(
        "Fecha máxima",
        fecha_max.strftime("%Y-%m-%d"),
    )

    st.markdown("---")

    # --------------------------------------------------------
    # Gráficos
    # --------------------------------------------------------

    mostrar_graficos_series_temporales(df_ok)

    st.markdown("---")

    # --------------------------------------------------------
    # Últimos valores
    # --------------------------------------------------------

    st.subheader("Últimos valores disponibles por indicador")

    df_ultimos_mostrar = df_ultimos.copy()

    if not df_ultimos_mostrar.empty:
        df_ultimos_mostrar["valor"] = pd.to_numeric(
            df_ultimos_mostrar["valor"],
            errors="coerce",
        ).round(6)

    st.dataframe(
        df_ultimos_mostrar,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # --------------------------------------------------------
    # Histórico completo
    # --------------------------------------------------------

    st.subheader("Histórico consultado")

    df_historico_mostrar = df_historico.copy()
    df_historico_mostrar["valor"] = pd.to_numeric(
        df_historico_mostrar["valor"],
        errors="coerce",
    ).round(6)

    st.dataframe(
        df_historico_mostrar,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # --------------------------------------------------------
    # Resumen estadístico
    # --------------------------------------------------------

    st.subheader("Resumen estadístico")

    df_resumen_mostrar = df_resumen.copy()

    columnas_redondear = [
        "valor_min",
        "valor_max",
        "valor_promedio",
        "ultimo_valor",
    ]

    for columna in columnas_redondear:
        if columna in df_resumen_mostrar.columns:
            df_resumen_mostrar[columna] = pd.to_numeric(
                df_resumen_mostrar[columna],
                errors="coerce",
            ).round(6)

    st.dataframe(
        df_resumen_mostrar,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # --------------------------------------------------------
    # Calidad de datos
    # --------------------------------------------------------

    st.subheader("Calidad de datos")

    st.caption(
        """
        Esta tabla permite revisar si alguna serie no devolvió datos,
        tuvo error de consulta o quedó sin observaciones válidas.
        """
    )

    st.dataframe(
        df_calidad,
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")

    # --------------------------------------------------------
    # Descargas
    # --------------------------------------------------------

    st.subheader("Descargar resultados")

    df_base_100 = preparar_base_100(df_ok)
    df_matriz_original = preparar_pivot_serie_temporal(df_ok)

    col_csv, col_excel = st.columns(2)

    csv_historico = df_historico.to_csv(index=False).encode("utf-8-sig")

    with col_csv:
        st.download_button(
            label="Descargar histórico CSV",
            data=csv_historico,
            file_name=(
                f"indicadores_financieros_bde_"
                f"{fecha_desde}_{fecha_hasta}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

    excel_data = dataframe_a_excel(
        df_historico=df_historico,
        df_ultimos=df_ultimos,
        df_resumen=df_resumen,
        df_calidad=df_calidad,
        df_catalogo=df_catalogo,
        df_base_100=df_base_100,
        df_matriz_original=df_matriz_original,
    )

    with col_excel:
        st.download_button(
            label="Descargar Excel completo",
            data=excel_data,
            file_name=(
                f"indicadores_financieros_banco_central_"
                f"{fecha_desde}_{fecha_hasta}.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    # --------------------------------------------------------
    # Notas finales
    # --------------------------------------------------------

    st.markdown("---")

    st.info(
        """
        **Notas de interpretación**

        - Los indicadores de dólar observado quedan marcados por defecto.
        - Puedes seleccionar indicadores adicionales usando los checkboxes.
        - El gráfico **base 100** permite comparar tendencias entre indicadores con unidades distintas.
        - Los gráficos de **valores originales por unidad** evitan mezclar escalas incompatibles.
        - Algunas series son diarias, otras mensuales y otras anuales, por lo que no todas tendrán observaciones todos los días.
        - Si una serie no aparece en el gráfico, revisa la sección **Calidad de datos**.
        """
    )


# ============================================================
# Ejecutar app
# ============================================================

if __name__ == "__main__":
    main()
