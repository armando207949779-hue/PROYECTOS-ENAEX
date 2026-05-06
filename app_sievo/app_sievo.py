import base64
import io
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st


# =========================
# Rutas del proyecto
# =========================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# =========================
# Funciones auxiliares
# =========================

def mostrar_logo_centrado():
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
                >
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


def limpiar_valor(v, separador_decimal="."):
    if pd.isna(v):
        return np.nan

    v = str(v).strip()
    v = v.replace("$", "")
    v = v.replace(" ", "")

    if separador_decimal == ",":
        # Formato con coma decimal:
        # 1.234,56 -> 1234.56
        # 1218,50 -> 1218.50
        v = v.replace(".", "")
        v = v.replace(",", ".")
    else:
        # Formato con punto decimal:
        # 1,234.56 -> 1234.56
        # 1218.50 -> 1218.50
        v = v.replace(",", "")

    return pd.to_numeric(v, errors="coerce")


def fmt_k(v):
    signo = "+" if v > 0 else ""

    if abs(v) >= 1000:
        return f"{signo}{v / 1000:.1f}k$"

    return f"{signo}{v:,.0f}$"


def fmt_inside(v):
    if abs(v) >= 1000:
        return f"{v / 1000:.1f}k$"

    return f"{v:,.0f}$"


def parsear_tabla_desde_texto(texto, separador_decimal="."):
    texto = texto.strip()

    if not texto:
        raise ValueError("El cuadro de texto está vacío.")

    df = pd.read_csv(
        io.StringIO(texto),
        sep="\t"
    )

    df.columns = df.columns.str.strip()

    if "Concepto" not in df.columns or "Valor_USD" not in df.columns:
        raise ValueError(
            "El texto debe contener las columnas 'Concepto' y 'Valor_USD'."
        )

    df = df[["Concepto", "Valor_USD"]].copy()

    df["Concepto"] = (
        df["Concepto"]
        .astype(str)
        .str.strip()
    )

    df["Valor_USD"] = df["Valor_USD"].apply(
        lambda x: limpiar_valor(
            x,
            separador_decimal=separador_decimal
        )
    )

    if df["Valor_USD"].isna().any():
        filas_malas = df[df["Valor_USD"].isna()]
        raise ValueError(
            f"Hay valores no numéricos en Valor_USD:\n{filas_malas}"
        )

    return df


def graficar_savings_bridge(df):
    conceptos = df["Concepto"].tolist()
    valores = df["Valor_USD"].tolist()

    barras_totales = {
        "Spend Previous Year",
        "Final Explained",
        "Spend Current Year (Real)"
    }

    color_total = "#2F5A97"
    color_pos = "#D62828"
    color_neg = "#6DBE45"

    x = np.arange(len(df))
    bottoms = []
    heights = []
    colors = []

    running = 0

    for concepto, valor in zip(conceptos, valores):
        if concepto in barras_totales:
            bottoms.append(0)
            heights.append(valor)
            colors.append(color_total)

            if concepto == "Spend Previous Year":
                running = valor
            elif concepto == "Final Explained":
                running = valor
            elif concepto == "Spend Current Year (Real)":
                running = valor

        else:
            if valor >= 0:
                bottoms.append(running)
                heights.append(valor)
                colors.append(color_pos)
            else:
                bottoms.append(running + valor)
                heights.append(abs(valor))
                colors.append(color_neg)

            running += valor

    fig, ax = plt.subplots(figsize=(12, 6))
    bar_width = 0.58

    ax.bar(
        x,
        heights,
        bottom=bottoms,
        width=bar_width,
        color=colors,
        edgecolor="none"
    )

    running = 0

    for i, (concepto, valor) in enumerate(zip(conceptos, valores)):
        if i == 0:
            if concepto == "Spend Previous Year":
                running = valor
            continue

        prev_x = x[i - 1]
        curr_x = x[i]

        if concepto in barras_totales:
            nivel = valor
            running = valor
        else:
            nivel = running
            running += valor

        ax.plot(
            [prev_x + bar_width / 2, curr_x - bar_width / 2],
            [nivel, nivel],
            linestyle="--",
            linewidth=0.8,
            color="#9AA9C2"
        )

    running = 0
    max_abs = max(abs(v) for v in valores) if valores else 1

    for i, (concepto, valor) in enumerate(zip(conceptos, valores)):
        if concepto in barras_totales:
            ax.text(
                x[i],
                valor * 0.55,
                fmt_inside(valor),
                ha="center",
                va="center",
                color="white",
                fontsize=11,
                fontweight="bold"
            )

            if concepto == "Spend Previous Year":
                running = valor
            elif concepto == "Final Explained":
                running = valor
            elif concepto == "Spend Current Year (Real)":
                running = valor

        else:
            if valor >= 0:
                y_text = running + valor + max_abs * 0.02
            else:
                y_text = running + valor - max_abs * 0.05

            ax.text(
                x[i],
                y_text,
                fmt_k(valor),
                ha="center",
                va="center",
                color=colors[i],
                fontsize=11,
                fontweight="bold"
            )

            running += valor

    labels_map = {
        "Spend Previous Year": "Spend\nPrevious\nYear",
        "Volume": "Volume",
        "IPC": "IPC",
        "Diesel": "Diesel",
        "IR": "IR",
        "Currency": "Currency",
        "Final Explained": "Final\nExplained",
        "Gap / Mix": "Gap / Mix",
        "Spend Current Year (Real)": "Spend\nCurrent\nYear\n(Real)"
    }

    labels = [
        labels_map.get(c, c.replace(" ", "\n"))
        for c in conceptos
    ]

    ax.set_xticks(x)
    ax.set_xticklabels(
        labels,
        fontsize=11,
        color="#1F4A8A"
    )

    ax.set_title(
        "SavingsBridge™",
        fontsize=22,
        fontweight="bold",
        color="#1F4A8A",
        pad=20
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)

    ax.tick_params(axis="y", left=False, labelleft=False)
    ax.tick_params(axis="x", length=0)

    ax.set_facecolor("#F2F2F2")
    fig.patch.set_facecolor("#F2F2F2")

    plt.tight_layout()

    return fig


def crear_excel_salida(df):
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            sheet_name="Savings Bridge",
            index=False
        )

    return buffer.getvalue()


# =========================
# Texto ejemplo
# =========================

TEXTO_EJEMPLO = """Concepto\tValor_USD
Spend Previous Year\t182056
Volume\t-19452
IPC\t1218
Diesel\t4093
IR\t3699
Currency\t-18
Final Explained\t171596
Gap / Mix\t-21426
Spend Current Year (Real)\t150170"""


# =========================
# App Streamlit
# =========================

st.set_page_config(
    page_title="Savings Bridge",
    page_icon="🏢",
    layout="wide"
)

mostrar_logo_centrado()

st.markdown(
    "<h1 style='text-align: center;'>Savings Bridge</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Pega una tabla con las columnas Concepto y Valor_USD para generar el gráfico.
    </p>
    """,
    unsafe_allow_html=True
)

st.markdown("---")


# =========================
# Entrada de datos
# =========================

with st.expander("Ver formato esperado"):
    st.code(
        TEXTO_EJEMPLO,
        language="text"
    )

separador_decimal = st.radio(
    "¿Qué separador decimal usan los valores pegados?",
    options=[
        "Punto decimal: 1218.50",
        "Coma decimal: 1218,50"
    ],
    index=0,
    horizontal=True
)

if separador_decimal.startswith("Coma"):
    separador_decimal_valor = ","
else:
    separador_decimal_valor = "."

texto_usuario = st.text_area(
    label="Pega aquí la tabla copiada desde Excel",
    value=TEXTO_EJEMPLO,
    height=240
)


# =========================
# Botón generar
# =========================

if st.button("Generar Savings Bridge"):
    try:
        df_bridge = parsear_tabla_desde_texto(
            texto_usuario,
            separador_decimal=separador_decimal_valor
        )

        st.session_state["df_bridge"] = df_bridge
        st.session_state["separador_decimal"] = separador_decimal_valor

        st.success("Tabla leída correctamente.")

    except Exception as e:
        st.error(f"Error: {e}")


# =========================
# Resultados
# =========================

if "df_bridge" in st.session_state:
    df_bridge = st.session_state["df_bridge"]

    st.subheader("Tabla procesada")

    st.dataframe(
        df_bridge,
        use_container_width=True
    )

    st.subheader("Gráfico Savings Bridge")

    fig = graficar_savings_bridge(df_bridge)

    st.pyplot(fig)

    excel_salida = crear_excel_salida(df_bridge)

    st.download_button(
        label="Descargar Excel",
        data=excel_salida,
        file_name="savings_bridge.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
