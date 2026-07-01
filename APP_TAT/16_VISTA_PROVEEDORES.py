# ============================================================
# 16_VISTA_PROVEEDORES
# Vista ejecutiva de Performance Proveedor
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
#
# Enfoque:
# - Vista ejecutiva inspirada en 13_VISTA_EJECUTIVA_PERFORMANCE_PLANTAS
# - Base de análisis: registros evaluables Cumple + No cumple
# - Donut global porcentual Cumple / No cumple
# - Proveedores por cantidad de registros evaluables
# - Tendencia mensual de performance proveedor
# - Tablas ejecutivas y descarga de información
# ============================================================

import io
import base64
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# ============================================================
# Configuración general
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"

COLOR_CUMPLE = "#5F6264"
COLOR_NO_CUMPLE = "#E83E51"
COLOR_META = "#00593A"
COLOR_TEXTO = "#1F2937"
COLOR_MUTED = "#6B7280"
COLOR_GRID = "#D1D5DB"

META_CUMPLIMIENTO = 65

COL_PROVEEDOR = "Proveedor ERP - ARIBA"
COL_PERFORMANCE_PROVEEDOR = "performance_proveedor"
COL_DIAS_PROVEEDOR = "dias_proveedor"
COL_FECHA_PROVEEDOR = "Fecha facturación proveedor - ME80FN"

COL_FECHA_RECEPCION_FINAL = "fecha_recepcion_final"
COL_FECHA_FACTURACION_FINAL = "fecha_facturacion_final"
COL_PEDIDO = "Pedido - ME5A"
COL_DOCUMENTO_COMPRAS = "Documento de compras - ME80FN"

TOP_N_DEFAULT = 20

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
    12: "diciembre",
}


# ============================================================
# Estilos
# ============================================================

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 4.25rem;
            padding-bottom: 1.2rem;
            max-width: 1380px;
        }

        .exec-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 18px;
            padding: 12px 16px 8px 16px;
            border-radius: 18px;
            background: linear-gradient(90deg, #F8FAFC 0%, #FFFFFF 100%);
            border: 1px solid #E5E7EB;
            margin-bottom: 12px;
        }

        .exec-title {
            color: #111827;
            font-size: 22px;
            font-weight: 850;
            letter-spacing: .2px;
            margin: 0;
        }

        .exec-subtitle {
            color: #6B7280;
            font-size: 12px;
            margin-top: 2px;
        }

        .exec-filter-note {
            color: #374151;
            font-size: 12px;
            background: #F9FAFB;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 8px 12px;
        }

        .exec-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 16px;
            padding: 14px 16px;
            box-shadow: 0 8px 20px rgba(17, 24, 39, 0.04);
            height: 100%;
        }

        .exec-kpi-title {
            color: #6B7280;
            font-size: 12px;
            font-weight: 750;
            margin-bottom: 4px;
        }

        .exec-kpi-value {
            color: #111827;
            font-size: 28px;
            font-weight: 900;
            line-height: 1.0;
        }

        .exec-kpi-subtitle {
            color: #6B7280;
            font-size: 12px;
            margin-top: 6px;
            line-height: 1.3;
        }

        .exec-section-title {
            color: #111827;
            font-size: 17px;
            font-weight: 850;
            margin: 12px 0 2px 0;
        }

        .exec-small {
            color: #6B7280;
            font-size: 12px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Logo
# ============================================================

def mostrar_logo():
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
                margin-top: 5px;
                margin-bottom: 10px;
            ">
                <img
                    src="data:image/svg+xml;base64,{logo_base64}"
                    style="width: 220px; display: block;"
                >
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# Utilidades
# ============================================================

def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def convertir_fecha_columna(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    serie_num = pd.to_numeric(serie, errors="coerce")
    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")

    mask_num = serie_num.notna()

    if mask_num.any():
        mask_ms = mask_num & serie_num.abs().ge(10**11)
        mask_s = mask_num & serie_num.abs().lt(10**11)

        if mask_ms.any():
            resultado.loc[mask_ms] = pd.to_datetime(
                serie_num.loc[mask_ms],
                unit="ms",
                errors="coerce",
            )

        if mask_s.any():
            resultado.loc[mask_s] = pd.to_datetime(
                serie_num.loc[mask_s],
                unit="s",
                errors="coerce",
            )

    mask_no_num = ~mask_num

    if mask_no_num.any():
        resultado.loc[mask_no_num] = pd.to_datetime(
            serie.loc[mask_no_num],
            errors="coerce",
            dayfirst=True,
        )

    return resultado


def formatear_entero(valor) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return "—"

    return f"{int(round(numero)):,}"


def formatear_porcentaje(valor) -> str:
    if pd.isna(valor):
        return "—"

    numero = pd.to_numeric(valor, errors="coerce")

    if pd.isna(numero):
        return "—"

    return f"{numero:.1f}%"


def normalizar_estado_performance(valor) -> str:
    texto = str(valor).strip().lower()

    texto = (
        texto.replace("á", "a")
        .replace("é", "e")
        .replace("í", "i")
        .replace("ó", "o")
        .replace("ú", "u")
    )

    if texto == "cumple":
        return "Cumple"

    if texto in ["no cumple", "nocumple"]:
        return "No cumple"

    if texto == "en proceso":
        return "En proceso"

    if texto in ["no aplica", "no aplica al analisis", "no aplica al análisis"]:
        return "No aplica"

    if texto in ["nan", "none", "<na>", "null", "", "sin datos"]:
        return "Sin datos"

    return "Sin datos"


def obtener_columna_fecha(df: pd.DataFrame) -> str | None:
    candidatos = [
        COL_FECHA_PROVEEDOR,
        COL_FECHA_FACTURACION_FINAL,
        COL_FECHA_RECEPCION_FINAL,
        "Fecha recepción mercancía - ME80FN",
        "Fecha facturación proveedor - NME80FN",
    ]

    for col in candidatos:
        if col in df.columns:
            return col

    return None


def mostrar_kpi_ejecutivo(titulo: str, valor: str, subtitulo: str):
    st.markdown(
        f"""
        <div class="exec-card">
            <div class="exec-kpi-title">{titulo}</div>
            <div class="exec-kpi-value">{valor}</div>
            <div class="exec-kpi-subtitle">{subtitulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def titulo_vista_proveedores(nombre_archivo: str):
    st.markdown(
        f"""
        <div class="exec-header">
            <div>
                <div class="exec-title">16_VISTA_PROVEEDORES · Performance proveedor</div>
                <div class="exec-subtitle">
                    Vista ejecutiva de proveedores: tabla principal, cumplimiento, volumen y evolución mensual.
                </div>
            </div>
            <div class="exec-filter-note">
                Archivo activo: <b>{nombre_archivo}</b><br>
                Base principal: <b>Cumple + No cumple</b>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def etiqueta_mes_corta(fecha) -> str:
    if pd.isna(fecha):
        return "—"

    fecha = pd.Timestamp(fecha)
    return MESES_NOMBRE.get(int(fecha.month), str(fecha.month))


def preparar_tabla_ejecutiva_display(tabla_proveedores: pd.DataFrame) -> pd.DataFrame:
    if tabla_proveedores.empty:
        return pd.DataFrame()

    salida = tabla_proveedores.copy()

    columnas_orden = [
        "proveedor_grafico",
        "Cumple",
        "No cumple",
        "Evaluables",
        "% Cumple",
        "% No cumple",
        "Promedio días proveedor",
    ]

    columnas_orden = [c for c in columnas_orden if c in salida.columns]

    salida = salida[columnas_orden].copy()
    salida = salida.sort_values(
        ["Evaluables", "% No cumple"],
        ascending=[False, False],
    ).reset_index(drop=True)

    return salida


# ============================================================
# Preparación base proveedores
# ============================================================

@st.cache_data(show_spinner=False)
def preparar_base_proveedores(df_original: pd.DataFrame) -> pd.DataFrame:
    df = limpiar_nombres_columnas(df_original)

    columnas_requeridas = [
        COL_PROVEEDOR,
        COL_PERFORMANCE_PROVEEDOR,
    ]

    faltantes = [c for c in columnas_requeridas if c not in df.columns]

    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas para la vista de proveedores: {faltantes}"
        )

    df[COL_PROVEEDOR] = (
        df[COL_PROVEEDOR]
        .astype("string")
        .str.strip()
    )

    df["proveedor_grafico"] = df[COL_PROVEEDOR].fillna("Sin proveedor ARIBA")
    df["proveedor_grafico"] = df["proveedor_grafico"].replace("", "Sin proveedor ARIBA")

    df["performance_proveedor_norm"] = (
        df[COL_PERFORMANCE_PROVEEDOR]
        .apply(normalizar_estado_performance)
    )

    if COL_DIAS_PROVEEDOR in df.columns:
        df[COL_DIAS_PROVEEDOR] = pd.to_numeric(
            df[COL_DIAS_PROVEEDOR],
            errors="coerce",
        )

    col_fecha = obtener_columna_fecha(df)

    if col_fecha is not None:
        df["fecha_proveedor_grafico"] = convertir_fecha_columna(df[col_fecha])
        df["periodo_fecha"] = (
            df["fecha_proveedor_grafico"]
            .dt.to_period("M")
            .dt.to_timestamp()
        )
        df["anio"] = df["fecha_proveedor_grafico"].dt.year
        df["mes_num"] = df["fecha_proveedor_grafico"].dt.month
        df["mes_nombre"] = df["mes_num"].map(MESES_NOMBRE)
        df["periodo_label"] = np.where(
            df["anio"].notna() & df["mes_nombre"].notna(),
            df["mes_nombre"].astype(str)
            + " "
            + df["anio"].astype("Int64").astype(str),
            pd.NA,
        )
    else:
        df["fecha_proveedor_grafico"] = pd.NaT
        df["periodo_fecha"] = pd.NaT
        df["anio"] = pd.NA
        df["mes_num"] = pd.NA
        df["mes_nombre"] = pd.NA
        df["periodo_label"] = pd.NA

    return df


# ============================================================
# Filtros
# ============================================================

def aplicar_filtros_proveedores(
    df_base: pd.DataFrame,
    fecha_inicio,
    fecha_fin,
    proveedores_sel: list,
    perf_sel: list,
    incluir_sin_proveedor: bool,
) -> pd.DataFrame:

    df = df_base.copy()

    if not incluir_sin_proveedor:
        df = df[df["proveedor_grafico"].ne("Sin proveedor ARIBA")].copy()

    if fecha_inicio is not None and fecha_fin is not None:
        fecha_inicio_ts = pd.Timestamp(fecha_inicio)
        fecha_fin_ts = pd.Timestamp(fecha_fin) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

        df = df[
            df["fecha_proveedor_grafico"].notna()
            & df["fecha_proveedor_grafico"].between(fecha_inicio_ts, fecha_fin_ts)
        ].copy()

    if proveedores_sel:
        df = df[df["proveedor_grafico"].isin(proveedores_sel)].copy()

    if perf_sel:
        df = df[df["performance_proveedor_norm"].isin(perf_sel)].copy()

    df = df[df["performance_proveedor_norm"].isin(["Cumple", "No cumple"])].copy()

    return df


# ============================================================
# Resúmenes
# ============================================================

def calcular_kpis_proveedores(df_base: pd.DataFrame, df_dashboard: pd.DataFrame) -> dict:
    total_base = int(len(df_base))
    total_filtrado = int(len(df_dashboard))

    cumple = int(df_dashboard["performance_proveedor_norm"].eq("Cumple").sum())
    no_cumple = int(df_dashboard["performance_proveedor_norm"].eq("No cumple").sum())
    evaluables = cumple + no_cumple

    proveedores_identificados = int(
        df_dashboard["proveedor_grafico"]
        .ne("Sin proveedor ARIBA")
        .sum()
    )

    proveedores_unicos = int(
        df_dashboard.loc[
            df_dashboard["proveedor_grafico"].ne("Sin proveedor ARIBA"),
            "proveedor_grafico",
        ]
        .nunique()
    )

    pct_cumple = cumple / evaluables * 100 if evaluables else 0
    pct_no_cumple = no_cumple / evaluables * 100 if evaluables else 0
    pct_proveedor_identificado = proveedores_identificados / total_filtrado * 100 if total_filtrado else 0

    dias_promedio = (
        pd.to_numeric(df_dashboard[COL_DIAS_PROVEEDOR], errors="coerce").mean()
        if COL_DIAS_PROVEEDOR in df_dashboard.columns
        else np.nan
    )

    return {
        "total_base": total_base,
        "total_filtrado": total_filtrado,
        "evaluables": evaluables,
        "cumple": cumple,
        "no_cumple": no_cumple,
        "pct_cumple": pct_cumple,
        "pct_no_cumple": pct_no_cumple,
        "proveedores_identificados": proveedores_identificados,
        "proveedores_unicos": proveedores_unicos,
        "pct_proveedor_identificado": pct_proveedor_identificado,
        "dias_promedio": dias_promedio,
    }


def crear_resumen_proveedores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    resumen = (
        df
        .groupby(["proveedor_grafico", "performance_proveedor_norm"])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index="proveedor_grafico",
        columns="performance_proveedor_norm",
        values="cantidad",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for col in ["Cumple", "No cumple"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["Evaluables"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Evaluables"] > 0,
        tabla["Cumple"] / tabla["Evaluables"] * 100,
        0,
    )

    tabla["% No cumple"] = np.where(
        tabla["Evaluables"] > 0,
        tabla["No cumple"] / tabla["Evaluables"] * 100,
        0,
    )

    if COL_DIAS_PROVEEDOR in df.columns:
        dias = (
            df
            .groupby("proveedor_grafico")[COL_DIAS_PROVEEDOR]
            .mean()
            .reset_index()
            .rename(columns={COL_DIAS_PROVEEDOR: "Promedio días proveedor"})
        )
        tabla = tabla.merge(dias, on="proveedor_grafico", how="left")
    else:
        tabla["Promedio días proveedor"] = np.nan

    return tabla.sort_values("Evaluables", ascending=False).reset_index(drop=True)


def crear_resumen_mensual_proveedores(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "periodo_fecha" not in df.columns:
        return pd.DataFrame()

    base = df[
        df["periodo_fecha"].notna()
        & df["performance_proveedor_norm"].isin(["Cumple", "No cumple"])
    ].copy()

    if base.empty:
        return pd.DataFrame()

    resumen = (
        base
        .groupby(["periodo_fecha", "periodo_label", "performance_proveedor_norm"])
        .size()
        .reset_index(name="cantidad")
    )

    tabla = resumen.pivot_table(
        index=["periodo_fecha", "periodo_label"],
        columns="performance_proveedor_norm",
        values="cantidad",
        aggfunc="sum",
        fill_value=0,
    ).reset_index()

    for col in ["Cumple", "No cumple"]:
        if col not in tabla.columns:
            tabla[col] = 0

    tabla["Evaluables"] = tabla["Cumple"] + tabla["No cumple"]

    tabla["% Cumple"] = np.where(
        tabla["Evaluables"] > 0,
        tabla["Cumple"] / tabla["Evaluables"] * 100,
        0,
    )

    tabla["% No cumple"] = np.where(
        tabla["Evaluables"] > 0,
        tabla["No cumple"] / tabla["Evaluables"] * 100,
        0,
    )

    return tabla.sort_values("periodo_fecha").reset_index(drop=True)


# ============================================================
# Gráficos Matplotlib
# ============================================================

def grafico_donut_global(cumple: int, no_cumple: int):
    evaluables = cumple + no_cumple

    if evaluables <= 0:
        st.info("Sin registros evaluables.")
        return

    pct_cumple = cumple / evaluables * 100
    pct_no_cumple = no_cumple / evaluables * 100

    fig, ax = plt.subplots(figsize=(4.2, 3.2), dpi=180)

    ax.pie(
        [cumple, no_cumple],
        startangle=90,
        counterclock=False,
        colors=[COLOR_CUMPLE, COLOR_NO_CUMPLE],
        wedgeprops={
            "width": 0.42,
            "edgecolor": "white",
            "linewidth": 1.4,
        },
    )

    ax.text(
        0,
        0.08,
        f"{pct_cumple:.0f}%",
        ha="center",
        va="center",
        fontsize=24,
        fontweight="bold",
        color=COLOR_TEXTO,
    )

    ax.text(
        0,
        -0.16,
        "Cumple",
        ha="center",
        va="center",
        fontsize=9,
        color=COLOR_MUTED,
    )

    ax.text(
        1.05,
        -0.65,
        f"Cumple\n{cumple:,}\n{pct_cumple:.1f}%",
        ha="left",
        va="center",
        fontsize=8,
        color=COLOR_TEXTO,
    )

    ax.text(
        -1.05,
        0.82,
        f"No cumple\n{no_cumple:,}\n{pct_no_cumple:.1f}%",
        ha="right",
        va="center",
        fontsize=8,
        color=COLOR_TEXTO,
    )

    ax.axis("equal")
    fig.patch.set_alpha(0)
    fig.tight_layout(pad=0.2)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def grafico_barras_apiladas_top_proveedores(data: pd.DataFrame, top_n: int):
    if data.empty:
        st.info("No hay datos para graficar.")
        return

    plot_data = (
        data
        .sort_values("Evaluables", ascending=False)
        .head(top_n)
        .sort_values("Evaluables", ascending=True)
    )

    fig_height = max(4.5, len(plot_data) * 0.38)
    fig, ax = plt.subplots(figsize=(11.5, fig_height), dpi=160)

    y = np.arange(len(plot_data))

    cumple = pd.to_numeric(plot_data["Cumple"], errors="coerce").fillna(0)
    no_cumple = pd.to_numeric(plot_data["No cumple"], errors="coerce").fillna(0)

    ax.barh(
        y,
        cumple,
        color=COLOR_CUMPLE,
        label="Cumple",
    )

    ax.barh(
        y,
        no_cumple,
        left=cumple,
        color=COLOR_NO_CUMPLE,
        label="No cumple",
    )

    ax.set_yticks(y)
    ax.set_yticklabels(plot_data["proveedor_grafico"].astype(str), fontsize=8)
    ax.set_title(
        f"Top {top_n} proveedores por cantidad de registros",
        loc="left",
        fontsize=13,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )
    ax.set_xlabel("Cantidad de registros evaluables", color=COLOR_MUTED)
    ax.legend(frameon=False, loc="lower right")

    ax.grid(False)
    ax.tick_params(axis="x", colors=COLOR_MUTED)
    ax.tick_params(axis="y", colors=COLOR_TEXTO)

    for spine in ax.spines.values():
        spine.set_visible(False)

    fig.tight_layout()

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def grafico_performance_proveedor_matplotlib(
    tabla_mensual: pd.DataFrame,
    titulo: str,
):
    if tabla_mensual.empty:
        st.info("No hay datos mensuales evaluables para graficar.")
        return

    data = tabla_mensual.copy()
    data["periodo_fecha"] = pd.to_datetime(data["periodo_fecha"], errors="coerce")
    data = data[data["periodo_fecha"].notna()].copy()
    data = data[data["Evaluables"].gt(0)].copy()
    data = data.sort_values("periodo_fecha").reset_index(drop=True)

    if data.empty:
        st.info("No hay meses con registros evaluables para graficar.")
        return

    x = np.arange(len(data))

    cumple_pct = pd.to_numeric(data["% Cumple"], errors="coerce").fillna(0).to_numpy()
    no_cumple_pct = pd.to_numeric(data["% No cumple"], errors="coerce").fillna(0).to_numpy()

    cumple_n = pd.to_numeric(data["Cumple"], errors="coerce").fillna(0).astype(int).to_numpy()
    no_cumple_n = pd.to_numeric(data["No cumple"], errors="coerce").fillna(0).astype(int).to_numpy()
    evaluables = pd.to_numeric(data["Evaluables"], errors="coerce").fillna(0).astype(int).to_numpy()

    labels = [etiqueta_mes_corta(v) for v in data["periodo_fecha"]]

    fig_width = max(9.5, len(data) * 0.85)
    fig, ax = plt.subplots(figsize=(fig_width, 4.4), dpi=180)

    bar_width = 0.78

    ax.bar(
        x,
        cumple_pct,
        width=bar_width,
        color=COLOR_CUMPLE,
        label="Cumple",
        edgecolor="white",
        linewidth=1.0,
    )

    ax.bar(
        x,
        no_cumple_pct,
        bottom=cumple_pct,
        width=bar_width,
        color=COLOR_NO_CUMPLE,
        label="No cumple",
        edgecolor="white",
        linewidth=1.0,
    )

    ax.axhline(
        META_CUMPLIMIENTO,
        color=COLOR_META,
        linestyle=(0, (2, 2)),
        linewidth=1.8,
        alpha=0.95,
        label=f"Meta {META_CUMPLIMIENTO}%",
    )

    for i, (c_pct, nc_pct, c_n, nc_n, total) in enumerate(
        zip(cumple_pct, no_cumple_pct, cumple_n, no_cumple_n, evaluables)
    ):
        if total <= 0:
            continue

        if c_pct >= 8:
            ax.text(
                i,
                c_pct / 2,
                f"{c_pct:.1f}%",
                ha="center",
                va="center",
                fontsize=7.4,
                color="white",
                fontweight="bold",
            )

        if nc_pct >= 8:
            ax.text(
                i,
                c_pct + nc_pct / 2,
                f"{nc_pct:.1f}%",
                ha="center",
                va="center",
                fontsize=7.4,
                color="white",
                fontweight="bold",
            )
        elif nc_pct > 0:
            ax.text(
                i,
                min(98, c_pct + nc_pct + 1.8),
                f"{nc_pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=6.8,
                color=COLOR_NO_CUMPLE,
                fontweight="bold",
            )

    ax.set_ylim(0, 105)
    ax.set_yticks([0, 50, 100])
    ax.set_yticklabels(["0%", "50%", "100%"], fontsize=8, color=COLOR_MUTED)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=0, fontsize=8, color=COLOR_MUTED)

    ax.set_title(
        titulo,
        loc="left",
        fontsize=14.5,
        fontweight="bold",
        color=COLOR_TEXTO,
        pad=10,
    )

    ax.grid(axis="y", linestyle=":", linewidth=0.7, color=COLOR_GRID)
    ax.grid(axis="x", visible=False)
    ax.tick_params(axis="both", length=0)

    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.legend(
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=3,
        frameon=False,
        fontsize=8.6,
    )

    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    fig.tight_layout()
    fig.subplots_adjust(bottom=0.22)

    st.pyplot(fig, clear_figure=True, use_container_width=True)
    plt.close(fig)


def mostrar_evolucion_por_anio_proveedor(tabla_mensual: pd.DataFrame):
    st.markdown(
        "<div class='exec-section-title'>Tendencia mensual proveedor</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='exec-small'>
            Barras 100% apiladas: gris oscuro = Cumple, rojo = No cumple.
            Los años anteriores quedan colapsados y el último año disponible queda visible por defecto.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tabla_mensual.empty:
        st.info("No hay datos mensuales disponibles.")
        return

    data = tabla_mensual.copy()
    data["periodo_fecha"] = pd.to_datetime(data["periodo_fecha"], errors="coerce")
    data = data[data["periodo_fecha"].notna()].copy()
    data = data[data["Evaluables"].gt(0)].copy()

    if data.empty:
        st.info("No hay meses con registros evaluables para graficar.")
        return

    data["anio_grafico"] = data["periodo_fecha"].dt.year
    anios = sorted(data["anio_grafico"].dropna().astype(int).unique().tolist())

    if not anios:
        st.info("No hay años disponibles para graficar.")
        return

    ultimo_anio = max(anios)

    for anio in anios:
        data_anio = (
            data[data["anio_grafico"].eq(anio)]
            .drop(columns=["anio_grafico"])
            .sort_values("periodo_fecha")
            .reset_index(drop=True)
        )

        evaluables_anio = int(pd.to_numeric(data_anio["Evaluables"], errors="coerce").fillna(0).sum())
        cumple_anio = int(pd.to_numeric(data_anio["Cumple"], errors="coerce").fillna(0).sum())
        no_cumple_anio = int(pd.to_numeric(data_anio["No cumple"], errors="coerce").fillna(0).sum())

        pct_cumple_anio = cumple_anio / evaluables_anio * 100 if evaluables_anio else 0
        pct_no_cumple_anio = no_cumple_anio / evaluables_anio * 100 if evaluables_anio else 0

        expanded = anio == ultimo_anio
        titulo_expander = (
            f"Año {anio} · "
            f"Evaluables: {formatear_entero(evaluables_anio)} · "
            f"Cumple: {formatear_porcentaje(pct_cumple_anio)} · "
            f"No cumple: {formatear_porcentaje(pct_no_cumple_anio)}"
        )

        with st.expander(titulo_expander, expanded=expanded):
            col_a1, col_a2, col_a3 = st.columns(3)

            with col_a1:
                mostrar_kpi_ejecutivo(
                    "Evaluables año",
                    formatear_entero(evaluables_anio),
                    f"{len(data_anio)} mes(es) con registros evaluables.",
                )

            with col_a2:
                mostrar_kpi_ejecutivo(
                    "Cumplimiento año",
                    formatear_porcentaje(pct_cumple_anio),
                    f"{formatear_entero(cumple_anio)} registros cumplen.",
                )

            with col_a3:
                mostrar_kpi_ejecutivo(
                    "No cumplimiento año",
                    formatear_porcentaje(pct_no_cumple_anio),
                    f"{formatear_entero(no_cumple_anio)} registros no cumplen.",
                )

            grafico_performance_proveedor_matplotlib(
                data_anio,
                titulo=f"Performance proveedor {anio}",
            )

            with st.expander(f"Tabla mensual proveedor {anio}", expanded=False):
                columnas = [
                    "periodo_label",
                    "Cumple",
                    "No cumple",
                    "Evaluables",
                    "% Cumple",
                    "% No cumple",
                ]

                columnas = [c for c in columnas if c in data_anio.columns]

                st.dataframe(
                    data_anio[columnas],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "% Cumple": st.column_config.ProgressColumn(
                            "% Cumple",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100,
                        ),
                        "% No cumple": st.column_config.ProgressColumn(
                            "% No cumple",
                            format="%.1f%%",
                            min_value=0,
                            max_value=100,
                        ),
                    },
                )


# ============================================================
# Exportación
# ============================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


def convertir_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Registros",
        )

    return output.getvalue()


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


@st.cache_data(show_spinner=False)
def convertir_a_excel_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_excel(df)


# ============================================================
# App
# ============================================================

mostrar_logo()

if "df_tat" not in st.session_state or st.session_state.get("df_tat") is None:
    st.info("Primero debes cargar un archivo activo en 06_CARGAR_ARCHIVO.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

titulo_vista_proveedores(nombre_archivo)

try:
    with st.spinner("Preparando base de proveedores..."):
        df_final = preparar_base_proveedores(df_original)

except Exception as e:
    st.error("No se pudo preparar la vista de proveedores.")
    st.exception(e)
    st.stop()


# ============================================================
# Preparación filtros
# ============================================================

df_pre_filtro = df_final.copy()

fechas_validas = df_pre_filtro["fecha_proveedor_grafico"].dropna()

fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

proveedores_disponibles = (
    df_pre_filtro["proveedor_grafico"]
    .dropna()
    .astype(str)
    .sort_values()
    .unique()
    .tolist()
)

perf_options = ["Cumple", "No cumple"]

st.markdown(
    "<div class='exec-section-title'>Filtros ejecutivos</div>",
    unsafe_allow_html=True,
)

st.caption(
    "La vista se calcula solo sobre registros evaluables: Cumple + No cumple. "
    "Puedes incluir o excluir registros sin proveedor ARIBA."
)

with st.form("form_filtros_vista_proveedores"):
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1.2, 1, 1.2, 0.8, 0.8])

    with col_f1:
        if fecha_min is not None and fecha_max is not None:
            rango_fechas = st.date_input(
                "Fecha proveedor",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
                key="vista_proveedores_rango_fechas",
            )
        else:
            rango_fechas = None
            st.warning("No hay fechas válidas para filtrar.")

    with col_f2:
        perf_sel = st.multiselect(
            "Performance proveedor",
            options=perf_options,
            default=perf_options,
            key="vista_proveedores_performance",
        )

    with col_f3:
        proveedores_sel = st.multiselect(
            "Proveedor",
            options=proveedores_disponibles,
            default=[],
            key="vista_proveedores_proveedor",
            help="Opcional. Si no seleccionas proveedor, se consideran todos.",
        )

    with col_f4:
        incluir_sin_proveedor = st.checkbox(
            "Incluir sin proveedor",
            value=False,
            key="vista_proveedores_incluir_sin_proveedor",
        )

    with col_f5:
        top_n = st.number_input(
            "Top N",
            min_value=5,
            max_value=50,
            value=TOP_N_DEFAULT,
            step=5,
            key="vista_proveedores_top_n",
        )

    st.form_submit_button(
        "Actualizar vista proveedores",
        use_container_width=True,
        type="primary",
    )


if (
    rango_fechas is not None
    and isinstance(rango_fechas, (tuple, list))
    and len(rango_fechas) == 2
):
    fecha_inicio = rango_fechas[0]
    fecha_fin = rango_fechas[1]
else:
    fecha_inicio = None
    fecha_fin = None


# ============================================================
# Aplicar filtros
# ============================================================

df_dashboard = aplicar_filtros_proveedores(
    df_base=df_final,
    fecha_inicio=fecha_inicio,
    fecha_fin=fecha_fin,
    proveedores_sel=proveedores_sel,
    perf_sel=perf_sel,
    incluir_sin_proveedor=incluir_sin_proveedor,
)

if df_dashboard.empty:
    st.warning("No hay registros evaluables con los filtros seleccionados.")
    st.stop()

tabla_proveedores = crear_resumen_proveedores(df_dashboard)
tabla_mensual = crear_resumen_mensual_proveedores(df_dashboard)
kpis = calcular_kpis_proveedores(df_final, df_dashboard)

st.markdown(
    f"""
    <div class='exec-small'>
        Fechas: {fecha_inicio if fecha_inicio else "Todas"} a {fecha_fin if fecha_fin else "Todas"} ·
        Performance: {", ".join(perf_sel) if perf_sel else "Todas"} ·
        Proveedor: {", ".join(proveedores_sel) if proveedores_sel else "Todos"} ·
        Sin proveedor ARIBA: {"Incluido" if incluir_sin_proveedor else "Excluido"}
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# KPIs
# ============================================================

col_k1, col_k2, col_k3, col_k4 = st.columns(4)

with col_k1:
    mostrar_kpi_ejecutivo(
        "Registros evaluables",
        formatear_entero(kpis["evaluables"]),
        f"{formatear_entero(kpis['cumple'])} cumplen · {formatear_entero(kpis['no_cumple'])} no cumplen.",
    )

with col_k2:
    mostrar_kpi_ejecutivo(
        "Cumplimiento proveedor",
        formatear_porcentaje(kpis["pct_cumple"]),
        f"Meta referencial: {META_CUMPLIMIENTO}%.",
    )

with col_k3:
    mostrar_kpi_ejecutivo(
        "No cumplimiento proveedor",
        formatear_porcentaje(kpis["pct_no_cumple"]),
        "Complemento sobre registros evaluables.",
    )

with col_k4:
    mostrar_kpi_ejecutivo(
        "Proveedores únicos",
        formatear_entero(kpis["proveedores_unicos"]),
        f"Proveedor identificado en {formatear_porcentaje(kpis['pct_proveedor_identificado'])} de la vista.",
    )


# ============================================================
# Visual 1: Tabla ejecutiva de proveedores
# ============================================================

st.markdown(
    "<div class='exec-section-title'>Tabla ejecutiva de proveedores</div>",
    unsafe_allow_html=True,
)

st.caption(
    "Tabla principal de la vista. Ordenada por cantidad de registros evaluables y porcentaje de no cumplimiento."
)

tabla_ejecutiva_display = preparar_tabla_ejecutiva_display(tabla_proveedores)

col_tabla_1, col_tabla_2 = st.columns([4, 1])

with col_tabla_2:
    excel_resumen_principal = convertir_a_excel_cache(tabla_ejecutiva_display)

    st.download_button(
        label="Descargar resumen proveedores",
        data=excel_resumen_principal,
        file_name="16_VISTA_PROVEEDORES_V2_resumen_proveedores.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary",
    )

with col_tabla_1:
    st.dataframe(
        tabla_ejecutiva_display,
        use_container_width=True,
        hide_index=True,
        height=560,
        column_config={
            "proveedor_grafico": st.column_config.TextColumn(
                "Proveedor",
                width="large",
            ),
            "Cumple": st.column_config.NumberColumn(
                "Cumple",
                format="%d",
            ),
            "No cumple": st.column_config.NumberColumn(
                "No cumple",
                format="%d",
            ),
            "Evaluables": st.column_config.NumberColumn(
                "Evaluables",
                format="%d",
            ),
            "% Cumple": st.column_config.ProgressColumn(
                "% Cumple",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "% No cumple": st.column_config.ProgressColumn(
                "% No cumple",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Promedio días proveedor": st.column_config.NumberColumn(
                "Promedio días proveedor",
                format="%.1f",
            ),
        },
    )


# ============================================================
# Visual 2: Resumen global proveedor
# ============================================================

st.markdown(
    "<div class='exec-section-title'>Resumen global proveedor</div>",
    unsafe_allow_html=True,
)

col_g1, col_g2 = st.columns([1, 2])

with col_g1:
    grafico_donut_global(
        cumple=kpis["cumple"],
        no_cumple=kpis["no_cumple"],
    )

with col_g2:
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Estado": "Cumple",
                    "Registros": kpis["cumple"],
                    "%": kpis["pct_cumple"],
                },
                {
                    "Estado": "No cumple",
                    "Registros": kpis["no_cumple"],
                    "%": kpis["pct_no_cumple"],
                },
            ]
        ),
        use_container_width=True,
        hide_index=True,
        column_config={
            "%": st.column_config.ProgressColumn(
                "%",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            )
        },
    )


# ============================================================
# Visual 3: Volumen de registros por proveedor
# ============================================================

st.markdown(
    "<div class='exec-section-title'>Proveedores por cantidad de registros</div>",
    unsafe_allow_html=True,
)

grafico_barras_apiladas_top_proveedores(
    data=tabla_proveedores,
    top_n=int(top_n),
)


# ============================================================
# Visual 4: Tendencia mensual por año
# ============================================================

mostrar_evolucion_por_anio_proveedor(tabla_mensual)


# ============================================================
# Tablas secundarias
# ============================================================


with st.expander("Tabla mensual proveedor", expanded=False):
    if tabla_mensual.empty:
        st.info("No hay tabla mensual disponible.")
    else:
        columnas = [
            "periodo_label",
            "Cumple",
            "No cumple",
            "Evaluables",
            "% Cumple",
            "% No cumple",
        ]

        columnas = [c for c in columnas if c in tabla_mensual.columns]

        st.dataframe(
            tabla_mensual[columnas],
            use_container_width=True,
            hide_index=True,
            column_config={
                "% Cumple": st.column_config.ProgressColumn(
                    "% Cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
                "% No cumple": st.column_config.ProgressColumn(
                    "% No cumple",
                    format="%.1f%%",
                    min_value=0,
                    max_value=100,
                ),
            },
        )


with st.expander("Vista previa de registros evaluables filtrados", expanded=False):
    limite_vista = st.number_input(
        "Filas a mostrar",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
        key="vista_proveedores_limite_vista",
    )

    columnas_preferidas = [
        "Solicitud de pedido - ME5A",
        COL_PEDIDO,
        COL_DOCUMENTO_COMPRAS,
        COL_PROVEEDOR,
        "proveedor_grafico",
        COL_FECHA_PROVEEDOR,
        "fecha_proveedor_grafico",
        COL_DIAS_PROVEEDOR,
        COL_PERFORMANCE_PROVEEDOR,
        "performance_proveedor_norm",
        "origen",
        "sistema",
        "tipo_oc",
        "monto",
    ]

    columnas_preferidas = [
        col for col in columnas_preferidas
        if col in df_dashboard.columns
    ]

    if columnas_preferidas:
        st.dataframe(
            df_dashboard[columnas_preferidas].head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(
            df_dashboard.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )


# ============================================================
# Descargas
# ============================================================

with st.expander("Descargar base proveedores filtrada", expanded=False):
    firma_export = (
        f"{len(df_dashboard)}_"
        f"{fecha_inicio}_"
        f"{fecha_fin}_"
        f"{','.join(proveedores_sel)}_"
        f"{','.join(perf_sel)}_"
        f"{incluir_sin_proveedor}"
    )

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        preparar_excel = st.button(
            "Preparar Excel registros",
            use_container_width=True,
            key="vista_proveedores_preparar_excel",
        )

        if preparar_excel:
            with st.spinner("Preparando Excel..."):
                st.session_state["vista_proveedores_excel_bytes"] = convertir_a_excel_cache(df_dashboard)
                st.session_state["vista_proveedores_excel_firma"] = firma_export

        if (
            st.session_state.get("vista_proveedores_excel_bytes") is not None
            and st.session_state.get("vista_proveedores_excel_firma") == firma_export
        ):
            st.download_button(
                label="Descargar Excel registros",
                data=st.session_state["vista_proveedores_excel_bytes"],
                file_name="16_VISTA_PROVEEDORES_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV registros",
            use_container_width=True,
            key="vista_proveedores_preparar_csv",
        )

        if preparar_csv:
            with st.spinner("Preparando CSV..."):
                st.session_state["vista_proveedores_csv_bytes"] = convertir_a_csv_cache(df_dashboard)
                st.session_state["vista_proveedores_csv_firma"] = firma_export

        if (
            st.session_state.get("vista_proveedores_csv_bytes") is not None
            and st.session_state.get("vista_proveedores_csv_firma") == firma_export
        ):
            st.download_button(
                label="Descargar CSV registros",
                data=st.session_state["vista_proveedores_csv_bytes"],
                file_name="16_VISTA_PROVEEDORES_filtrado.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with col_d3:
        excel_resumen = convertir_a_excel_cache(tabla_ejecutiva_display)

        st.download_button(
            label="Descargar resumen proveedores",
            data=excel_resumen,
            file_name="16_VISTA_PROVEEDORES_V2_resumen.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
