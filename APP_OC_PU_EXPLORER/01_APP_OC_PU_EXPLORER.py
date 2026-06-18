# ============================================================
# 01_APP_OC_PU_EXPLORER
# Consulta histórica de precios OC por proveedor y material
#
# Fuente base:
# - Descarga ME2N SAP
#
# Filtros esperados:
# - Grupo de compras: EAD, EAA, EAT, EAX, EAY, EAQ, EAO, EAL, EAK
# - Fecha documento: desde 2024 hasta hoy
# - Tipo de posición != F, si existe la columna
# - Licitación contiene PU
#
# Input usuario:
# - Código proveedor SAP
# - Código material SAP
#
# Output:
# - Código proveedor
# - Nombre proveedor
# - Fecha documento
# - Material
# - Documento compras / OC
# - Precio neto
# ============================================================

import base64
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

st.set_page_config(
    page_title="OC PU Explorer",
    page_icon="🔎",
    layout="wide",
)


# ============================================================
# RUTAS DEL PROYECTO
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_PATH = PROJECT_DIR / "assets" / "logo.svg"


# ============================================================
# CONSTANTES DEL PRODUCTO
# ============================================================

GRUPOS_COMPRA_VALIDOS = [
    "EAD",
    "EAA",
    "EAT",
    "EAX",
    "EAY",
    "EAQ",
    "EAO",
    "EAL",
    "EAK",
]

COLUMNAS_OUTPUT = [
    "Codigo proveedor",
    "Nombre proveedor limpio",
    "Fecha documento",
    "Material",
    "Documento compras",
    "Precio neto",
    "Licitación",
    "Grupo de compras",
    "Texto breve",
]


# ============================================================
# LOGO
# ============================================================

def mostrar_logo() -> None:
    """
    Muestra el logo institucional desde:
    PROJECT_DIR / assets / logo.svg
    """
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
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# UTILIDADES DE LIMPIEZA Y CARGA
# ============================================================

def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia nombres de columnas y elimina columnas basura tipo Unnamed.
    """
    df = df.copy()

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace("\ufeff", "", regex=False)
    )

    columnas_validas = [
        col for col in df.columns
        if not col.lower().startswith("unnamed")
    ]

    return df[columnas_validas]


def cargar_csv_me2n(archivo) -> pd.DataFrame:
    """
    Carga robusta del archivo CSV exportado desde ME2N.

    Usa engine='python' para tolerar problemas de comas,
    comillas o filas irregulares.
    """
    try:
        df = pd.read_csv(
            archivo,
            encoding="utf-8-sig",
            sep=",",
            dtype=str,
            engine="python",
            on_bad_lines="skip",
        )
    except UnicodeDecodeError:
        archivo.seek(0)
        df = pd.read_csv(
            archivo,
            encoding="latin-1",
            sep=",",
            dtype=str,
            engine="python",
            on_bad_lines="skip",
        )

    df = normalizar_columnas(df)

    return df


def limpiar_texto_serie(serie: pd.Series) -> pd.Series:
    """
    Limpia espacios, NaN y formatos básicos de texto.
    """
    return (
        serie
        .fillna("")
        .astype(str)
        .str.strip()
    )


def extraer_codigo_proveedor(valor: str) -> str:
    """
    Desde una celda como:
    '449065     Proveedor Ariba Fase Cut'

    Extrae:
    '449065'
    """
    valor = str(valor).strip()

    if not valor:
        return ""

    partes = valor.split()

    if not partes:
        return ""

    return partes[0].strip()


def extraer_nombre_proveedor(valor: str) -> str:
    """
    Desde una celda como:
    '449065     Proveedor Ariba Fase Cut'

    Extrae:
    'Proveedor Ariba Fase Cut'
    """
    valor = str(valor).strip()

    if not valor:
        return ""

    partes = valor.split()

    if len(partes) <= 1:
        return valor

    return " ".join(partes[1:]).strip()


def preparar_base(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara y filtra la base ME2N para consulta PU.
    """
    df = df.copy()
    df = normalizar_columnas(df)

    # ========================================================
    # VALIDACIÓN DE COLUMNAS MÍNIMAS
    # ========================================================

    columnas_requeridas = [
        "Licitación",
        "Grupo de compras",
        "Fecha documento",
        "Documento compras",
        "Material",
        "Precio neto",
        "Nombre de proveedor",
    ]

    columnas_faltantes = [
        col for col in columnas_requeridas
        if col not in df.columns
    ]

    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas requeridas en el archivo: "
            + ", ".join(columnas_faltantes)
        )

    # ========================================================
    # LIMPIEZA GENERAL
    # ========================================================

    for col in df.columns:
        df[col] = limpiar_texto_serie(df[col])

    # Fecha documento
    df["Fecha documento"] = pd.to_datetime(
        df["Fecha documento"],
        errors="coerce",
        dayfirst=False,
    )

    # Código proveedor y nombre proveedor limpio
    df["Codigo proveedor"] = df["Nombre de proveedor"].apply(extraer_codigo_proveedor)
    df["Nombre proveedor limpio"] = df["Nombre de proveedor"].apply(extraer_nombre_proveedor)

    # Normalización de campos clave
    df["Licitación_norm"] = (
        df["Licitación"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["Grupo de compras_norm"] = (
        df["Grupo de compras"]
        .fillna("")
        .astype(str)
        .str.upper()
        .str.strip()
    )

    df["Material_norm"] = (
        df["Material"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    df["Codigo proveedor_norm"] = (
        df["Codigo proveedor"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # Precio numérico auxiliar
    df["Precio neto num"] = (
        df["Precio neto"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    df["Precio neto num"] = pd.to_numeric(
        df["Precio neto num"],
        errors="coerce",
    )

    # ========================================================
    # FILTROS DE NEGOCIO
    # ========================================================

    # Grupo de compras válido
    df = df[df["Grupo de compras_norm"].isin(GRUPOS_COMPRA_VALIDOS)]

    # Fecha desde 2024 hasta hoy
    fecha_inicio = pd.Timestamp("2024-01-01")
    fecha_hoy = pd.Timestamp(date.today())

    df = df[
        (df["Fecha documento"] >= fecha_inicio)
        & (df["Fecha documento"] <= fecha_hoy)
    ]

    # Tipo de posición distinto de F, solo si existe la columna
    posibles_columnas_tipo_posicion = [
        "Tipo de posición",
        "Tipo posición",
        "Tipo posicion",
        "Tp.posición",
        "Tp.posicion",
    ]

    columna_tipo_posicion = None

    for col in posibles_columnas_tipo_posicion:
        if col in df.columns:
            columna_tipo_posicion = col
            break

    if columna_tipo_posicion:
        df = df[
            df[columna_tipo_posicion]
            .fillna("")
            .astype(str)
            .str.upper()
            .str.strip()
            != "F"
        ]

    # Licitación PU y derivados
    #
    # Incluye ejemplos como:
    # - PU
    # - AD PU
    # - AD-PU
    # - AD-PU-TAR
    # - AD-PU-URG
    # - PU USD462
    # - ad-pu
    df = df[df["Licitación_norm"].str.contains("PU", na=False)]

    return df


def filtrar_por_proveedor_material(
    df: pd.DataFrame,
    codigo_proveedor: str,
    codigo_material: str,
) -> pd.DataFrame:
    """
    Filtra la base preparada por código proveedor SAP y material.
    """
    codigo_proveedor = str(codigo_proveedor).strip()
    codigo_material = str(codigo_material).strip()

    resultado = df[
        (df["Codigo proveedor_norm"] == codigo_proveedor)
        & (df["Material_norm"] == codigo_material)
    ].copy()

    resultado = resultado.sort_values(
        by="Fecha documento",
        ascending=False,
        na_position="last",
    )

    columnas_disponibles = [
        col for col in COLUMNAS_OUTPUT
        if col in resultado.columns
    ]

    return resultado[columnas_disponibles]


def descargar_excel(df: pd.DataFrame) -> bytes:
    """
    Convierte un dataframe a Excel en memoria.
    """
    from io import BytesIO

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")

    return output.getvalue()


# ============================================================
# COMPONENTES VISUALES
# ============================================================

def mostrar_encabezado() -> None:
    mostrar_logo()

    st.markdown(
        """
        <h1 style='text-align: center;'>OC PU Explorer</h1>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p style='text-align: center; font-size: 18px; color: #555;'>
            Consulta histórica de precios OC por proveedor SAP y material,
            usando base ME2N filtrada por licitación PU.
        </p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")


def mostrar_instrucciones() -> None:
    with st.expander("ℹ️ Reglas de negocio aplicadas", expanded=False):
        st.markdown(
            """
            Esta app aplica los siguientes criterios:

            - Fuente: archivo CSV descargado desde SAP ME2N.
            - Grupos de compra considerados:
              `EAD`, `EAA`, `EAT`, `EAX`, `EAY`, `EAQ`, `EAO`, `EAL`, `EAK`.
            - Fecha documento desde `2024-01-01` hasta hoy.
            - Si existe columna de tipo de posición, se excluye `F`.
            - Se consideran registros donde la columna `Licitación` contiene `PU`.
            - La búsqueda final se realiza por:
              - Código proveedor SAP
              - Código material SAP
            """
        )


def mostrar_kpis(df_original: pd.DataFrame, df_filtrado: pd.DataFrame) -> None:
    """
    Muestra KPIs generales de la carga.
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Registros archivo",
            f"{len(df_original):,}".replace(",", "."),
        )

    with col2:
        st.metric(
            "Registros PU filtrados",
            f"{len(df_filtrado):,}".replace(",", "."),
        )

    with col3:
        proveedores = (
            df_filtrado["Codigo proveedor"].nunique()
            if "Codigo proveedor" in df_filtrado.columns
            else 0
        )

        st.metric(
            "Proveedores PU",
            f"{proveedores:,}".replace(",", "."),
        )

    with col4:
        materiales = (
            df_filtrado["Material"].nunique()
            if "Material" in df_filtrado.columns
            else 0
        )

        st.metric(
            "Materiales PU",
            f"{materiales:,}".replace(",", "."),
        )


def mostrar_valores_unicos_licitacion(df: pd.DataFrame) -> None:
    """
    Muestra los valores únicos de licitación encontrados.
    """
    if "Licitación" not in df.columns:
        return

    valores = (
        df["Licitación"]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", pd.NA)
        .dropna()
        .drop_duplicates()
        .sort_values()
    )

    with st.expander("Ver valores únicos de Licitación", expanded=False):
        st.write(
            f"Total valores únicos no vacíos: **{len(valores):,}**".replace(",", ".")
        )

        st.dataframe(
            pd.DataFrame({"Licitación": valores}),
            use_container_width=True,
            hide_index=True,
        )


def mostrar_ayuda_sin_resultados(df_pu: pd.DataFrame) -> None:
    """
    Muestra ayuda cuando no hay resultados para la combinación buscada.
    """
    with st.expander("Ayuda para revisar posibles valores", expanded=False):
        proveedores_disponibles = (
            df_pu["Codigo proveedor"]
            .dropna()
            .drop_duplicates()
            .sort_values()
            .head(100)
        )

        materiales_disponibles = (
            df_pu["Material"]
            .dropna()
            .drop_duplicates()
            .sort_values()
            .head(100)
        )

        col_a, col_b = st.columns(2)

        with col_a:
            st.caption("Primeros proveedores disponibles")
            st.dataframe(
                pd.DataFrame({"Codigo proveedor": proveedores_disponibles}),
                use_container_width=True,
                hide_index=True,
            )

        with col_b:
            st.caption("Primeros materiales disponibles")
            st.dataframe(
                pd.DataFrame({"Material": materiales_disponibles}),
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# PÁGINA PRINCIPAL
# ============================================================

def pagina_app() -> None:
    mostrar_encabezado()
    mostrar_instrucciones()

    # ========================================================
    # 1. CARGA DE ARCHIVO
    # ========================================================

    st.subheader("1. Cargar archivo ME2N")

    archivo = st.file_uploader(
        "Carga el archivo CSV descargado desde ME2N",
        type=["csv"],
    )

    if archivo is None:
        st.info("Carga un archivo CSV para comenzar.")
        st.stop()

    try:
        df_original = cargar_csv_me2n(archivo)
    except Exception as e:
        st.error("No fue posible cargar el archivo.")
        st.exception(e)
        st.stop()

    st.success("Archivo cargado correctamente.")

    with st.expander("Vista previa del archivo cargado", expanded=False):
        st.write(
            f"Dimensión original: **{df_original.shape[0]:,} filas × {df_original.shape[1]:,} columnas**"
            .replace(",", ".")
        )

        st.dataframe(
            df_original.head(20),
            use_container_width=True,
        )

        st.caption("Columnas detectadas")
        st.write(df_original.columns.tolist())

    mostrar_valores_unicos_licitacion(df_original)

    # ========================================================
    # 2. PREPARAR BASE PU
    # ========================================================

    try:
        df_pu = preparar_base(df_original)
    except Exception as e:
        st.error("No fue posible preparar la base ME2N.")
        st.exception(e)
        st.stop()

    st.markdown("---")
    st.subheader("2. Base PU preparada")

    mostrar_kpis(df_original, df_pu)

    with st.expander("Vista previa de base PU filtrada", expanded=False):
        st.dataframe(
            df_pu.head(50),
            use_container_width=True,
        )

    # ========================================================
    # 3. INPUT USUARIO
    # ========================================================

    st.markdown("---")
    st.subheader("3. Buscar proveedor-material")

    col1, col2 = st.columns(2)

    with col1:
        codigo_proveedor = st.text_input(
            "Código proveedor SAP",
            placeholder="Ejemplo: 449065",
        )

    with col2:
        codigo_material = st.text_input(
            "Código material SAP",
            placeholder="Ejemplo: 100016",
        )

    buscar = st.button("Buscar combinación", type="primary")

    if not buscar:
        st.info(
            "Ingresa un código de proveedor SAP y un código de material para consultar."
        )
        st.stop()

    if not codigo_proveedor or not codigo_material:
        st.warning("Debes ingresar ambos campos: proveedor SAP y material SAP.")
        st.stop()

    # ========================================================
    # 4. RESULTADO
    # ========================================================

    resultado = filtrar_por_proveedor_material(
        df=df_pu,
        codigo_proveedor=codigo_proveedor,
        codigo_material=codigo_material,
    )

    st.markdown("---")
    st.subheader("4. Resultado")

    if resultado.empty:
        st.warning(
            "No se encontraron órdenes de compra PU para la combinación proveedor-material ingresada."
        )

        mostrar_ayuda_sin_resultados(df_pu)

        st.stop()

    st.success(
        f"Se encontraron **{len(resultado):,} líneas** para la combinación ingresada."
        .replace(",", ".")
    )

    st.dataframe(
        resultado,
        use_container_width=True,
        hide_index=True,
    )

    excel_bytes = descargar_excel(resultado)

    st.download_button(
        label="Descargar resultado Excel",
        data=excel_bytes,
        file_name=f"resultado_oc_pu_{codigo_proveedor}_{codigo_material}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ============================================================
# EJECUTAR APP
# ============================================================

pagina_app()
