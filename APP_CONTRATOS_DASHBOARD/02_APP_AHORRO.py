from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import base64
import html

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import streamlit as st


# ============================================================
# Configuración general
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"

PROCESOS_ESPERADOS = [
    "Licitación",
    "Cotización",
    "Asignación Directa",
    "Negociación - Cost Avoidance",
]


@dataclass(frozen=True)
class KPIResultado:
    ahorro_planificado: float
    ahorro_real: float
    cumplimiento: float
    numero_registros: int
    linea_base_valida: float
    eficiencia: float
    cobertura_linea_base: float


# ============================================================
# Estilo visual
# ============================================================
def configurar_pagina() -> None:
    st.set_page_config(
        page_title="Ahorro | Dashboard",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def aplicar_estilo() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background: linear-gradient(180deg, #F8FAFC 0%, #FFFFFF 28%);
            }

            .block-container {
                max-width: 1560px;
                padding-top: 1.4rem;
                padding-bottom: 3rem;
            }

            .hero {
                background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #2563EB 100%);
                border-radius: 24px;
                padding: 30px 34px;
                color: white;
                margin-bottom: 22px;
                box-shadow: 0 16px 40px rgba(15, 23, 42, 0.18);
            }

            .hero h1 {
                margin: 0;
                font-size: 2.15rem;
                letter-spacing: -0.035em;
            }

            .hero p {
                margin: 10px 0 0 0;
                color: #DBEAFE;
                font-size: 1rem;
                max-width: 920px;
            }

            .section-title {
                font-size: 1.25rem;
                font-weight: 800;
                color: #0F172A;
                margin: 1.2rem 0 0.7rem 0;
                letter-spacing: -0.02em;
            }

            .kpi-card {
                background: rgba(255,255,255,0.96);
                border: 1px solid #E2E8F0;
                border-radius: 18px;
                padding: 18px 18px 16px 18px;
                min-height: 132px;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            }

            .kpi-title {
                color: #64748B;
                font-size: 0.82rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.045em;
            }

            .kpi-value {
                color: #0F172A;
                font-size: 1.68rem;
                line-height: 1.15;
                font-weight: 850;
                margin-top: 10px;
            }

            .kpi-subtitle {
                color: #64748B;
                font-size: 0.78rem;
                line-height: 1.35;
                margin-top: 10px;
            }

            .info-card {
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                padding: 16px 18px;
                min-height: 134px;
            }

            .info-title {
                color: #0F172A;
                font-weight: 800;
                margin-bottom: 7px;
            }

            .info-text {
                color: #475569;
                font-size: 0.88rem;
                line-height: 1.45;
            }

            .formula {
                background: white;
                border: 1px solid #E2E8F0;
                border-radius: 10px;
                padding: 8px 10px;
                margin-top: 10px;
                color: #1E293B;
                font-size: 0.82rem;
                font-weight: 700;
            }

            div[data-testid="stSidebar"] {
                background: #F8FAFC;
                border-right: 1px solid #E2E8F0;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                overflow: hidden;
            }

            .quality-ok {
                background: #ECFDF5;
                border: 1px solid #A7F3D0;
                color: #065F46;
                border-radius: 12px;
                padding: 11px 13px;
                font-size: 0.88rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mostrar_encabezado() -> None:
    logo_html = ""
    if LOGO_PATH.exists():
        logo_svg = LOGO_PATH.read_text(encoding="utf-8")
        logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")
        logo_html = (
            f'<img src="data:image/svg+xml;base64,{logo_base64}" '
            'style="width:190px;max-height:70px;object-fit:contain;margin-bottom:14px;">'
        )

    st.markdown(
        f"""
        <div class="hero">
            {logo_html}
            <h1>Dashboard de Ahorro</h1>
            <p>
                Seguimiento integral del ahorro planificado y real, cumplimiento por gestor,
                eficiencia sobre línea base, evolución mensual y distribución por proceso.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def titulo_seccion(texto: str) -> None:
    st.markdown(f'<div class="section-title">{html.escape(texto)}</div>', unsafe_allow_html=True)


def kpi_card(titulo: str, valor: str, subtitulo: str = "") -> None:
    subtitulo_html = f'<div class="kpi-subtitle">{html.escape(subtitulo)}</div>' if subtitulo else ""
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{html.escape(titulo)}</div>
            <div class="kpi-value">{html.escape(valor)}</div>
            {subtitulo_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def info_card(titulo: str, texto: str, formula: str) -> None:
    st.markdown(
        f"""
        <div class="info-card">
            <div class="info-title">{html.escape(titulo)}</div>
            <div class="info-text">{html.escape(texto)}</div>
            <div class="formula">{html.escape(formula)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# Utilidades de datos
# ============================================================
def limpiar_texto(serie: pd.Series) -> pd.Series:
    return (
        serie.astype("string")
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    )


def convertir_numero_latino(valor) -> float | pd.NA:
    """Convierte números con formatos 1.234,56 o 1234.56 sin perder magnitud."""
    if pd.isna(valor):
        return pd.NA

    texto = str(valor).strip().replace(" ", "")
    if not texto or texto.lower() in {"nan", "none", "null"}:
        return pd.NA

    if "." in texto and "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "," in texto:
        texto = texto.replace(",", ".")

    return pd.to_numeric(texto, errors="coerce")


def formato_kusd(valor: float) -> str:
    if pd.isna(valor):
        return "—"
    return f"{valor:,.1f} kUSD"


def formato_porcentaje(valor: float) -> str:
    if pd.isna(valor):
        return "—"
    return f"{valor:.1%}".replace(".", ",")


def validar_columnas(df: pd.DataFrame, columnas: list[str], nombre: str) -> bool:
    faltantes = [columna for columna in columnas if columna not in df.columns]
    if faltantes:
        st.error(f"La tabla **{nombre}** no contiene las columnas requeridas: {faltantes}")
        return False
    return True


def obtener_dataframe(nombre: str) -> pd.DataFrame | None:
    dataframes = st.session_state.get("dataframes_cargados", {})
    if nombre not in dataframes:
        st.error(f"No se encontró `{nombre}` en los datos cargados.")
        return None
    return dataframes[nombre].copy()


@st.cache_data(show_spinner=False)
def preparar_datos(
    df_plan_original: pd.DataFrame,
    df_catalogo_original: pd.DataFrame,
    df_contratos_original: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_plan = df_plan_original.copy()
    df_catalogo = df_catalogo_original.copy()
    df_real = df_contratos_original.copy()

    df_plan["Gestor"] = limpiar_texto(df_plan["Gestor"])
    df_plan["Ahorro_Planificado_kUSD_num"] = df_plan["Ahorro_Planificado_kUSD"].apply(convertir_numero_latino)

    df_catalogo["Categoria"] = limpiar_texto(df_catalogo["Categoria"])
    df_catalogo["Gestor"] = limpiar_texto(df_catalogo["Gestor"])

    df_real["Fecha_Registro"] = pd.to_datetime(
        df_real["Fecha_Registro"], dayfirst=True, errors="coerce"
    )
    df_real["Categoria"] = limpiar_texto(df_real["Categoria"])
    df_real["Contratista"] = limpiar_texto(df_real["Contratista"])
    df_real["Tipo_Proceso"] = limpiar_texto(df_real["Tipo_Proceso"])
    df_real["Ahorro_Real_kUSD_num"] = df_real["Ahorro_Real_kUSD"].apply(convertir_numero_latino)
    df_real["LineaBase_kUSD_num"] = df_real["LineaBase_kUSD"].apply(convertir_numero_latino)

    if "Gestor" not in df_real.columns or df_real["Gestor"].isna().all():
        relaciones = (
            df_catalogo.dropna(subset=["Categoria", "Gestor"])
            .groupby("Categoria")["Gestor"]
            .agg(lambda valores: valores.iloc[0] if valores.nunique() == 1 else pd.NA)
            .reset_index()
        )
        df_real = df_real.drop(columns=["Gestor"], errors="ignore")
        df_real = df_real.merge(relaciones, on="Categoria", how="left")
    else:
        df_real["Gestor"] = limpiar_texto(df_real["Gestor"])

    df_real["Gestor"] = df_real["Gestor"].fillna("Sin gestor")

    # Columna exclusiva para visualización: fecha sin hora.
    df_real["Fecha_Registro_Sin_Hora"] = df_real["Fecha_Registro"].dt.date

    return df_plan, df_catalogo, df_real


def aplicar_filtros(
    df_real: pd.DataFrame,
    gestores: list[str],
    procesos: list[str],
    rango_fechas,
) -> pd.DataFrame:
    resultado = df_real.copy()
    resultado = resultado[resultado["Gestor"].isin(gestores)]
    resultado = resultado[resultado["Tipo_Proceso"].isin(procesos)]

    if isinstance(rango_fechas, tuple) and len(rango_fechas) == 2:
        fecha_inicio, fecha_fin = rango_fechas
        resultado = resultado[
            resultado["Fecha_Registro"].dt.date.between(fecha_inicio, fecha_fin)
        ]

    return resultado


def filtrar_plan_por_gestor(df_plan: pd.DataFrame, gestores: list[str]) -> pd.DataFrame:
    return df_plan[df_plan["Gestor"].isin(gestores)].copy()


def calcular_kpis(df_plan_filtrado: pd.DataFrame, df_real_filtrado: pd.DataFrame) -> KPIResultado:
    ahorro_planificado = df_plan_filtrado["Ahorro_Planificado_kUSD_num"].sum(min_count=1)
    ahorro_real = df_real_filtrado["Ahorro_Real_kUSD_num"].sum(min_count=1)

    ahorro_planificado = 0.0 if pd.isna(ahorro_planificado) else float(ahorro_planificado)
    ahorro_real = 0.0 if pd.isna(ahorro_real) else float(ahorro_real)
    cumplimiento = ahorro_real / ahorro_planificado if ahorro_planificado else 0.0

    filtro_base = (
        df_real_filtrado["LineaBase_kUSD_num"].notna()
        & (df_real_filtrado["LineaBase_kUSD_num"] > 0)
    )
    linea_base = df_real_filtrado.loc[filtro_base, "LineaBase_kUSD_num"].sum(min_count=1)
    ahorro_con_base = df_real_filtrado.loc[filtro_base, "Ahorro_Real_kUSD_num"].sum(min_count=1)
    linea_base = 0.0 if pd.isna(linea_base) else float(linea_base)
    ahorro_con_base = 0.0 if pd.isna(ahorro_con_base) else float(ahorro_con_base)

    eficiencia = ahorro_con_base / linea_base if linea_base else 0.0
    cobertura = filtro_base.mean() if len(df_real_filtrado) else 0.0

    return KPIResultado(
        ahorro_planificado=ahorro_planificado,
        ahorro_real=ahorro_real,
        cumplimiento=cumplimiento,
        numero_registros=len(df_real_filtrado),
        linea_base_valida=linea_base,
        eficiencia=eficiencia,
        cobertura_linea_base=float(cobertura),
    )


def preparar_tabla_visual(df: pd.DataFrame) -> pd.DataFrame:
    salida = df.copy()
    if "Fecha_Registro" in salida.columns:
        salida["Fecha_Registro"] = pd.to_datetime(salida["Fecha_Registro"], errors="coerce").dt.date
    salida = salida.drop(columns=["Fecha_Registro_Sin_Hora"], errors="ignore")
    return salida


def controles_calidad(df_real: pd.DataFrame, df_catalogo: pd.DataFrame) -> pd.DataFrame:
    categorias_ambiguas = (
        df_catalogo.dropna(subset=["Categoria", "Gestor"])
        .groupby("Categoria")["Gestor"]
        .nunique()
        .gt(1)
        .sum()
    )

    return pd.DataFrame(
        {
            "Validación": [
                "Fechas inválidas",
                "Ahorro real no numérico",
                "Línea base no numérica",
                "Registros sin gestor",
                "Ahorros negativos",
                "Categorías con múltiples gestores",
            ],
            "Cantidad": [
                int(df_real["Fecha_Registro"].isna().sum()),
                int(df_real["Ahorro_Real_kUSD_num"].isna().sum()),
                int(df_real["LineaBase_kUSD_num"].isna().sum()),
                int(df_real["Gestor"].eq("Sin gestor").sum()),
                int(df_real["Ahorro_Real_kUSD_num"].lt(0).sum()),
                int(categorias_ambiguas),
            ],
        }
    )


# ============================================================
# Gráficos
# ============================================================
def estilo_ejes(ax) -> None:
    ax.grid(axis="y", alpha=0.16)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CBD5E1")
    ax.spines["bottom"].set_color("#CBD5E1")
    ax.tick_params(colors="#475569")


def grafico_cumplimiento(df_plan: pd.DataFrame, df_real: pd.DataFrame, gestores: list[str]):
    plan = (
        df_plan.groupby("Gestor", as_index=False)["Ahorro_Planificado_kUSD_num"]
        .sum()
        .rename(columns={"Ahorro_Planificado_kUSD_num": "Plan"})
    )
    real = (
        df_real.groupby("Gestor", as_index=False)["Ahorro_Real_kUSD_num"]
        .sum()
        .rename(columns={"Ahorro_Real_kUSD_num": "Real"})
    )
    dimension = pd.DataFrame({"Gestor": sorted(set(gestores) | set(real["Gestor"].dropna()))})
    tabla = dimension.merge(plan, on="Gestor", how="left").merge(real, on="Gestor", how="left").fillna(0)
    tabla["Cumplimiento_%"] = tabla.apply(lambda r: r["Real"] / r["Plan"] * 100 if r["Plan"] > 0 else 0, axis=1)
    tabla = tabla.sort_values("Cumplimiento_%")

    if tabla.empty:
        return None, tabla

    fig, ax = plt.subplots(figsize=(12.5, max(4.8, len(tabla) * 0.55)))
    valores = tabla["Cumplimiento_%"]
    colores = ["#16A34A" if valor >= 100 else "#DC2626" for valor in valores]
    barras = ax.barh(tabla["Gestor"], valores, color=colores, alpha=0.9)
    ax.axvline(100, linestyle="--", linewidth=1.2, color="#0F172A", label="Meta 100%")
    ax.set_xlabel("Cumplimiento [%]")
    ax.set_title("Cumplimiento por gestor", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(xmax=100, decimals=0))
    estilo_ejes(ax)

    limite = max(125, valores.max() * 1.22 if not valores.empty else 125)
    ax.set_xlim(0, limite)
    for barra, (_, fila) in zip(barras, tabla.iterrows()):
        ax.text(
            min(barra.get_width() + limite * 0.015, limite * 0.96),
            barra.get_y() + barra.get_height() / 2,
            f"{fila['Cumplimiento_%']:.1f}% | {fila['Real']:,.1f} / {fila['Plan']:,.1f} kUSD",
            va="center",
            fontsize=8.5,
            fontweight="bold",
        )
    fig.tight_layout()
    return fig, tabla


def grafico_evolucion(df_real: pd.DataFrame):
    datos = df_real.dropna(subset=["Fecha_Registro"]).copy()
    if datos.empty:
        return None, pd.DataFrame()

    datos["Mes"] = datos["Fecha_Registro"].dt.to_period("M").dt.to_timestamp()
    mensual = datos.groupby("Mes", as_index=False)["Ahorro_Real_kUSD_num"].sum()

    rango = pd.date_range(mensual["Mes"].min(), mensual["Mes"].max(), freq="MS")
    mensual = (
        mensual.set_index("Mes")
        .reindex(rango, fill_value=0)
        .rename_axis("Mes")
        .reset_index()
    )
    mensual["Acumulado"] = mensual["Ahorro_Real_kUSD_num"].cumsum()
    mensual["Periodo"] = mensual["Mes"].dt.strftime("%Y-%m")

    fig, ax1 = plt.subplots(figsize=(12.5, 5.4))
    ax1.bar(mensual["Mes"], mensual["Ahorro_Real_kUSD_num"], width=20, alpha=0.35, color="#60A5FA")
    ax1.set_ylabel("Ahorro mensual [kUSD]")
    ax1.set_xlabel("Mes")
    ax1.set_xticks(mensual["Mes"])
    ax1.set_xticklabels(mensual["Periodo"], rotation=45, ha="right")
    estilo_ejes(ax1)

    ax2 = ax1.twinx()
    ax2.plot(mensual["Mes"], mensual["Acumulado"], marker="o", linewidth=2.6, color="#1D4ED8")
    ax2.set_ylabel("Ahorro acumulado [kUSD]")
    ax2.spines["top"].set_visible(False)
    ax2.spines["left"].set_visible(False)
    ax2.spines["right"].set_color("#CBD5E1")
    ax1.set_title("Ahorro real mensual y acumulado", fontsize=14, fontweight="bold", pad=14)
    fig.tight_layout()
    return fig, mensual


def grafico_top_registros(df_real: pd.DataFrame, top_n: int):
    datos = df_real.copy()
    datos["Categoria"] = datos["Categoria"].fillna("Sin categoría")
    datos["Contratista"] = datos["Contratista"].fillna("Sin contratista")
    datos["Etiqueta"] = datos["Contratista"] + " | " + datos["Categoria"]

    top = (
        datos.dropna(subset=["Ahorro_Real_kUSD_num"])
        .sort_values("Ahorro_Real_kUSD_num", ascending=False)
        .head(top_n)
        .sort_values("Ahorro_Real_kUSD_num")
    )
    if top.empty:
        return None, top

    fig, ax = plt.subplots(figsize=(12.5, max(4.8, top_n * 0.48)))
    barras = ax.barh(top["Etiqueta"], top["Ahorro_Real_kUSD_num"], color="#2563EB")
    ax.set_xlabel("Ahorro real [kUSD]")
    ax.set_title("Top registros por ahorro real", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    estilo_ejes(ax)

    maximo = top["Ahorro_Real_kUSD_num"].max()
    ax.set_xlim(0, maximo * 1.24 if maximo > 0 else 1)
    for barra in barras:
        ax.text(
            barra.get_width() + maximo * 0.02,
            barra.get_y() + barra.get_height() / 2,
            f"{barra.get_width():,.1f} kUSD",
            va="center",
            fontsize=8.5,
            fontweight="bold",
        )
    fig.tight_layout()
    return fig, top


def grafico_procesos(df_real: pd.DataFrame):
    resumen = (
        df_real.groupby("Tipo_Proceso", as_index=False)["Ahorro_Real_kUSD_num"]
        .sum()
        .rename(columns={"Ahorro_Real_kUSD_num": "Ahorro_Real_Total_kUSD"})
    )
    dimension = pd.DataFrame(
        {"Tipo_Proceso": sorted(set(PROCESOS_ESPERADOS) | set(resumen["Tipo_Proceso"].dropna()))}
    )
    resumen = dimension.merge(resumen, on="Tipo_Proceso", how="left").fillna(0)
    resumen = resumen.sort_values("Ahorro_Real_Total_kUSD")

    if resumen.empty:
        return None, resumen

    fig, ax = plt.subplots(figsize=(12.5, 5.3))
    barras = ax.barh(resumen["Tipo_Proceso"], resumen["Ahorro_Real_Total_kUSD"], color="#0EA5E9")
    ax.set_xlabel("Ahorro real total [kUSD]")
    ax.set_title("Ahorro real por tipo de proceso", fontsize=14, fontweight="bold", pad=14)
    ax.xaxis.set_major_formatter(mticker.StrMethodFormatter("{x:,.0f}"))
    estilo_ejes(ax)

    maximo = resumen["Ahorro_Real_Total_kUSD"].max()
    ax.set_xlim(0, maximo * 1.24 if maximo > 0 else 1)
    if maximo > 0:
        for barra in barras:
            ax.text(
                barra.get_width() + maximo * 0.02,
                barra.get_y() + barra.get_height() / 2,
                f"{barra.get_width():,.1f} kUSD",
                va="center",
                fontsize=8.5,
                fontweight="bold",
            )
    fig.tight_layout()
    return fig, resumen


# ============================================================
# Aplicación
# ============================================================
def main() -> None:
    configurar_pagina()
    aplicar_estilo()
    mostrar_encabezado()

    if not st.session_state.get("dataframes_cargados"):
        st.warning("Primero debes cargar las bases desde la pestaña **01_CARGA_ARCHIVOS**.")
        st.stop()

    df_plan_original = obtener_dataframe("df_plan_ahorro_gestores")
    df_catalogo_original = obtener_dataframe("df_catalogo_categorias")
    df_contratos_original = obtener_dataframe("df_registro_contratos")

    if any(df is None for df in [df_plan_original, df_catalogo_original, df_contratos_original]):
        st.stop()

    validaciones = [
        validar_columnas(df_plan_original, ["Gestor", "Ahorro_Planificado_kUSD"], "Plan de ahorro"),
        validar_columnas(df_catalogo_original, ["Categoria", "Gestor"], "Catálogo de categorías"),
        validar_columnas(
            df_contratos_original,
            [
                "Fecha_Registro",
                "Categoria",
                "Contratista",
                "Tipo_Proceso",
                "LineaBase_kUSD",
                "Ahorro_Real_kUSD",
            ],
            "Registro de contratos",
        ),
    ]
    if not all(validaciones):
        st.stop()

    df_plan, df_catalogo, df_real = preparar_datos(
        df_plan_original, df_catalogo_original, df_contratos_original
    )

    gestores_disponibles = sorted(df_real["Gestor"].dropna().unique().tolist())
    procesos_disponibles = sorted(df_real["Tipo_Proceso"].dropna().unique().tolist())
    fechas_validas = df_real["Fecha_Registro"].dropna()

    with st.sidebar:
        st.header("Filtros")
        gestores_filtro = st.multiselect(
            "Gestor",
            options=gestores_disponibles,
            default=gestores_disponibles,
        )
        procesos_filtro = st.multiselect(
            "Tipo de proceso",
            options=procesos_disponibles,
            default=procesos_disponibles,
        )

        if fechas_validas.empty:
            rango_fechas = None
            st.info("No hay fechas válidas disponibles.")
        else:
            fecha_min = fechas_validas.min().date()
            fecha_max = fechas_validas.max().date()
            rango_fechas = st.date_input(
                "Rango de fechas",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                format="DD/MM/YYYY",
            )

        st.divider()
        top_n = st.slider("Cantidad de registros del top", 5, 20, 10)

    if not gestores_filtro or not procesos_filtro:
        st.warning("Selecciona al menos un gestor y un tipo de proceso para visualizar resultados.")
        st.stop()

    df_real_filtrado = aplicar_filtros(
        df_real, gestores_filtro, procesos_filtro, rango_fechas
    )
    df_plan_filtrado = filtrar_plan_por_gestor(df_plan, gestores_filtro)
    kpis = calcular_kpis(df_plan_filtrado, df_real_filtrado)

    titulo_seccion("Indicadores principales")
    columnas = st.columns(3)
    with columnas[0]:
        kpi_card("Ahorro planificado", formato_kusd(kpis.ahorro_planificado), "Plan correspondiente a los gestores seleccionados")
    with columnas[1]:
        kpi_card("Ahorro real", formato_kusd(kpis.ahorro_real), "Resultado del período y filtros activos")
    with columnas[2]:
        kpi_card("Cumplimiento", formato_porcentaje(kpis.cumplimiento), "Ahorro real dividido por ahorro planificado")

    columnas = st.columns(3)
    with columnas[0]:
        kpi_card("N.º de registros", f"{kpis.numero_registros:,}", "Cantidad de filas después de aplicar filtros")
    with columnas[1]:
        kpi_card("Eficiencia", formato_porcentaje(kpis.eficiencia), "Ahorro real sobre línea base válida")
    with columnas[2]:
        kpi_card("Cobertura línea base", formato_porcentaje(kpis.cobertura_linea_base), formato_kusd(kpis.linea_base_valida))

    with st.expander("Definición de indicadores"):
        col1, col2 = st.columns(2)
        with col1:
            info_card(
                "Cumplimiento",
                "Indica qué proporción del ahorro planificado fue alcanzada con el ahorro real registrado.",
                "(Ahorro real / Ahorro planificado) × 100",
            )
        with col2:
            info_card(
                "Eficiencia",
                "Relaciona el ahorro real con la línea base de los registros que tienen una línea base válida.",
                "(Ahorro real con base válida / Línea base válida) × 100",
            )

    titulo_seccion("Cumplimiento por gestor")
    fig, tabla_cumplimiento = grafico_cumplimiento(df_plan_filtrado, df_real_filtrado, gestores_filtro)
    if fig is None:
        st.info("No hay datos para visualizar.")
    else:
        st.pyplot(fig, clear_figure=True)

    titulo_seccion("Evolución mensual")
    fig, tabla_mensual = grafico_evolucion(df_real_filtrado)
    if fig is None:
        st.info("No hay fechas válidas para construir la evolución mensual.")
    else:
        st.pyplot(fig, clear_figure=True)

    titulo_seccion("Top de ahorro real")
    fig, tabla_top = grafico_top_registros(df_real_filtrado, top_n)
    if fig is None:
        st.info("No hay datos para construir el top.")
    else:
        st.pyplot(fig, clear_figure=True)

    titulo_seccion("Distribución por tipo de proceso")
    fig, tabla_procesos = grafico_procesos(df_real_filtrado)
    if fig is None:
        st.info("No hay datos para visualizar por proceso.")
    else:
        st.pyplot(fig, clear_figure=True)

    titulo_seccion("Calidad y detalle de datos")
    calidad = controles_calidad(df_real, df_catalogo)
    if calidad["Cantidad"].sum() == 0:
        st.markdown('<div class="quality-ok">No se detectaron alertas en las validaciones principales.</div>', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Calidad", "Registros filtrados", "Cumplimiento", "Evolución", "Procesos"]
    )
    with tab1:
        st.dataframe(calidad, use_container_width=True, hide_index=True)
    with tab2:
        # Las fechas se muestran como objetos date: nunca incluyen horas.
        st.dataframe(preparar_tabla_visual(df_real_filtrado), use_container_width=True, hide_index=True)
    with tab3:
        st.dataframe(tabla_cumplimiento, use_container_width=True, hide_index=True)
    with tab4:
        tabla_mensual_visual = tabla_mensual.copy()
        if not tabla_mensual_visual.empty:
            tabla_mensual_visual["Mes"] = tabla_mensual_visual["Mes"].dt.date
        st.dataframe(tabla_mensual_visual, use_container_width=True, hide_index=True)
    with tab5:
        st.dataframe(tabla_procesos, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
