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
)


# ============================================================
# Constantes Banco Central
# ============================================================

URL_BDE = "https://si3.bcentral.cl/SieteRestWS/SieteRestWS.ashx"


# ============================================================
# Diccionario de indicadores financieros
# ============================================================

SERIES_INDICADORES = {
    # ========================================================
    # DÓLAR OBSERVADO / TIPO DE CAMBIO
    # ========================================================

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

    # ========================================================
    # UF / UTM
    # ========================================================

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

    # ========================================================
    # IPC
    # ========================================================

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

    # ========================================================
    # ICL - ÍNDICE DE COSTOS LABORALES
    # ========================================================

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

    # ========================================================
    # IR - ÍNDICE DE REMUNERACIONES
    # ========================================================

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


def calcular_rango_default() -> tuple[date, date]:
    """Rango por defecto: últimos 24 meses hasta hoy."""
    hasta = date.today()
    desde = hasta - timedelta(days=730)
    return desde, hasta


def validar_rango_fechas(fecha_desde: date, fecha_hasta: date) -> None:
    """Valida que el rango de fechas sea correcto."""

    if fecha_desde > fecha_hasta:
        st.error("La fecha desde no puede ser mayor que la fecha hasta.")
        st.stop()

    if fecha_hasta > date.today():
        st.error("La fecha hasta no puede ser posterior a hoy.")
        st.stop()


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
        .groupby(["codigo", "nombre", "grupo", "frecuencia", "unidad", "seriesId"], as_index=False)
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


# ============================================================
# Exportación Excel
# ============================================================

def dataframe_a_excel(
    df_historico: pd.DataFrame,
    df_ultimos: pd.DataFrame,
    df_resumen: pd.DataFrame,
    df_catalogo: pd.DataFrame,
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

        df_catalogo.to_excel(
            writer,
            index=False,
            sheet_name="Catalogo_Indicadores",
        )

    return output.getvalue()


# ============================================================
# Formateadores
# ============================================================

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
            Consulta temporal de dólar observado, UF, UTM, IPC, ICL e IR
            desde la BDE del Banco Central de Chile.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")

    user, password = obtener_credenciales()

    df_catalogo = obtener_catalogo_indicadores()

    # --------------------------------------------------------
    # Panel de consulta
    # --------------------------------------------------------

    fecha_desde_default, fecha_hasta_default = calcular_rango_default()

    col_grupo, col_indicador = st.columns([1, 2])

    with col_grupo:
        grupos_disponibles = ["Todos"] + sorted(df_catalogo["grupo"].unique().tolist())

        grupo_seleccionado = st.selectbox(
            "Grupo de indicadores",
            options=grupos_disponibles,
            index=0,
        )

    if grupo_seleccionado == "Todos":
        df_catalogo_filtrado = df_catalogo.copy()
    else:
        df_catalogo_filtrado = df_catalogo[
            df_catalogo["grupo"] == grupo_seleccionado
        ].copy()

    opciones_indicadores = {
        f"{row.codigo} - {row.nombre}": row.codigo
        for row in df_catalogo_filtrado.itertuples(index=False)
    }

    with col_indicador:
        opcion_indicador = st.selectbox(
            "Seleccionar indicador",
            options=["Todos los indicadores del grupo"] + list(opciones_indicadores.keys()),
            index=0,
        )

    if opcion_indicador == "Todos los indicadores del grupo":
        codigos_seleccionados = df_catalogo_filtrado["codigo"].tolist()
    else:
        codigos_seleccionados = [opciones_indicadores[opcion_indicador]]

    col_desde, col_hasta, col_total = st.columns([1, 1, 1])

    with col_desde:
        fecha_desde = st.date_input(
            "Fecha desde",
            value=fecha_desde_default,
            max_value=date.today(),
        )

    with col_hasta:
        fecha_hasta = st.date_input(
            "Fecha hasta",
            value=fecha_hasta_default,
            max_value=date.today(),
        )

    with col_total:
        st.metric(
            "Indicadores seleccionados",
            len(codigos_seleccionados),
        )

    validar_rango_fechas(fecha_desde, fecha_hasta)

    st.markdown("---")

    # --------------------------------------------------------
    # Catálogo visible
    # --------------------------------------------------------

    with st.expander("Ver catálogo de indicadores disponibles", expanded=False):
        st.dataframe(
            df_catalogo_filtrado,
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
            Selecciona un grupo, un indicador y un rango de fechas.
            Luego presiona **Consultar Banco Central**.
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

        progress_text.info("Construyendo resúmenes...")
        progress_bar.progress(90)

        df_ultimos = crear_resumen_ultimos_valores(df_historico)
        df_resumen = crear_resumen_estadistico(df_historico)

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

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Indicadores con datos",
        total_indicadores_ok,
    )

    col2.metric(
        "Observaciones",
        total_observaciones,
    )

    col3.metric(
        "Fecha mínima",
        fecha_min.strftime("%Y-%m-%d"),
    )

    col4.metric(
        "Fecha máxima",
        fecha_max.strftime("%Y-%m-%d"),
    )

    st.markdown("---")

    # --------------------------------------------------------
    # Últimos valores
    # --------------------------------------------------------

    st.subheader("Últimos valores disponibles por indicador")

    df_ultimos_mostrar = df_ultimos.copy()
    df_ultimos_mostrar["valor"] = df_ultimos_mostrar["valor"].round(6)

    st.dataframe(
        df_ultimos_mostrar,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Gráfico temporal
    # --------------------------------------------------------

    st.markdown("---")
    st.subheader("Serie temporal")

    if df_ok["codigo"].nunique() == 1:
        codigo_unico = df_ok["codigo"].iloc[0]
        nombre_unico = df_ok["nombre"].iloc[0]
        unidad_unica = df_ok["unidad"].iloc[0]

        df_grafico = df_ok[["fecha", "valor"]].copy()
        df_grafico = df_grafico.sort_values("fecha")
        df_grafico = df_grafico.set_index("fecha")

        st.caption(f"{codigo_unico} - {nombre_unico} | Unidad: {unidad_unica}")

        st.line_chart(
            df_grafico,
            use_container_width=True,
        )

    else:
        st.info(
            """
            Para visualizar un gráfico temporal, selecciona un solo indicador.
            Si consultas varios indicadores, se muestra la tabla histórica consolidada.
            """
        )

    # --------------------------------------------------------
    # Histórico completo
    # --------------------------------------------------------

    st.markdown("---")
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

    # --------------------------------------------------------
    # Resumen estadístico
    # --------------------------------------------------------

    st.markdown("---")
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
            df_resumen_mostrar[columna] = df_resumen_mostrar[columna].round(6)

    st.dataframe(
        df_resumen_mostrar,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------------
    # Descargas
    # --------------------------------------------------------

    st.markdown("---")
    st.subheader("Descargar resultados")

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
        df_catalogo=df_catalogo,
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

        - `USD_DIARIO` corresponde al dólar observado diario en CLP por USD.
        - `USD_MENSUAL` corresponde al dólar observado mensual histórico.
        - `USD_ANUAL` corresponde al dólar observado anual.
        - `UF` y `UTM` están expresadas en CLP por unidad.
        - `IPC`, `ICL` e `IR` son índices o variaciones según la serie seleccionada.
        - Algunas series son diarias, otras mensuales y otras anuales, por lo que no todas tendrán observaciones todos los días.
        """
    )


# ============================================================
# Ejecutar app
# ============================================================

if __name__ == "__main__":
    main()
