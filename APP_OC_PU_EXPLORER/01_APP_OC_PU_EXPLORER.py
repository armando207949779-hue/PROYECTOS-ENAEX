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
# Flujo usuario:
# 1. Cargar archivo ME2N
# 2. Buscar por código proveedor SAP
# 3. Seleccionar material disponible para ese proveedor
# 4. Filtrar combinación proveedor-material
#
# Output:
# - Fecha documento
# - Código proveedor
# - Nombre proveedor
# - Material
# - OC
# - Precio neto
# ============================================================

import sys
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

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from assets.configurar_espanol import configurar_espanol

configurar_espanol()


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

COLUMNAS_VISTA_PREVIA = [
    "Fecha documento",
    "Codigo proveedor",
    "Nombre proveedor limpio",
    "Material",
    "Texto breve",
    "Documento compras",
    "Precio neto",
    "Licitación",
    "Grupo de compras",
    "Cantidad de pedido",
    "Unidad medida pedido",
    "Valor neto de orden",
    "Moneda",
    "Solicitante",
    "Centro",
    "Organización compras",
]

COLUMNAS_OUTPUT = [
    "Fecha documento",
    "Codigo proveedor",
    "Nombre proveedor limpio",
    "Material",
    "Texto breve",
    "Documento compras",
    "Precio neto",
    "Licitación",
    "Grupo de compras",
    "Cantidad de pedido",
    "Unidad medida pedido",
    "Valor neto de orden",
    "Moneda",
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


def convertir_numero_sap(valor) -> float:
    """
    Convierte números SAP exportados como texto a número.

    Soporta ejemplos:
    - 25000
    - 25.000
    - 25.000,50
    - 25000,50
    """
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto == "":
        return None

    texto = texto.replace(" ", "")

    if "," in texto:
        texto = texto.replace(".", "")
        texto = texto.replace(",", ".")
    else:
        texto = texto.replace(".", "")

    return pd.to_numeric(texto, errors="coerce")


def formato_miles_cl(valor) -> str:
    """
    Formatea número con separador de miles estilo Chile.

    Ejemplos:
    25000 -> 25.000
    25000.5 -> 25.000,50
    """
    if pd.isna(valor):
        return ""

    try:
        numero = float(valor)
    except Exception:
        return str(valor)

    if numero.is_integer():
        return f"{int(numero):,}".replace(",", ".")

    texto = f"{numero:,.2f}"
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")

    return texto


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


def ordenar_columnas(df: pd.DataFrame, columnas_preferidas: list[str]) -> pd.DataFrame:
    """
    Ordena columnas poniendo primero las columnas preferidas.
    El resto queda al final en el orden original.
    """
    df = df.copy()

    primeras = [
        col for col in columnas_preferidas
        if col in df.columns
    ]

    restantes = [
        col for col in df.columns
        if col not in primeras
    ]

    return df[primeras + restantes]


def preparar_df_visual(df: pd.DataFrame, columnas_preferidas: list[str]) -> pd.DataFrame:
    """
    Prepara un dataframe para mostrar en Streamlit:
    - Ordena columnas
    - Formatea fecha
    - Formatea precio neto
    - Formatea valor neto de orden
    """
    df_visual = df.copy()

    if "Fecha documento" in df_visual.columns:
        df_visual["Fecha documento"] = pd.to_datetime(
            df_visual["Fecha documento"],
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")

    if "Precio neto num" in df_visual.columns:
        df_visual["Precio neto"] = df_visual["Precio neto num"].apply(formato_miles_cl)

    if "Valor neto de orden num" in df_visual.columns:
        df_visual["Valor neto de orden"] = df_visual["Valor neto de orden num"].apply(formato_miles_cl)

    df_visual = ordenar_columnas(df_visual, columnas_preferidas)

    columnas_ocultas = [
        "Licitación_norm",
        "Grupo de compras_norm",
        "Material_norm",
        "Codigo proveedor_norm",
        "Precio neto num",
        "Valor neto de orden num",
    ]

    columnas_visibles = [
        col for col in df_visual.columns
        if col not in columnas_ocultas
    ]

    return df_visual[columnas_visibles]


# ============================================================
# PREPARACIÓN BASE
# ============================================================

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
    df["Precio neto num"] = df["Precio neto"].apply(convertir_numero_sap)

    # Valor neto de orden numérico auxiliar, si existe
    if "Valor neto de orden" in df.columns:
        df["Valor neto de orden num"] = df["Valor neto de orden"].apply(convertir_numero_sap)

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
    # Incluye ejemplos:
    # - PU
    # - AD PU
    # - AD-PU
    # - AD-PU-TAR
    # - AD-PU-URG
    # - PU USD462
    # - ad-pu
    df = df[df["Licitación_norm"].str.contains("PU", na=False)]

    df = df.sort_values(
        by=["Fecha documento", "Codigo proveedor", "Material"],
        ascending=[False, True, True],
        na_position="last",
    )

    return df


def filtrar_por_proveedor(
    df: pd.DataFrame,
    codigo_proveedor: str,
) -> pd.DataFrame:
    """
    Filtra la base preparada por código proveedor SAP.
    """
    codigo_proveedor = str(codigo_proveedor).strip()

    resultado = df[
        df["Codigo proveedor_norm"] == codigo_proveedor
    ].copy()

    resultado = resultado.sort_values(
        by=["Material", "Fecha documento"],
        ascending=[True, False],
        na_position="last",
    )

    return resultado


def resumen_materiales_por_proveedor(df_proveedor: pd.DataFrame) -> pd.DataFrame:
    """
    Genera resumen de materiales disponibles para un proveedor.
    """
    agrupaciones = {
        "Documento compras": "nunique",
        "Fecha documento": ["min", "max"],
        "Precio neto num": ["min", "max", "count"],
    }

    if "Texto breve" in df_proveedor.columns:
        resumen = (
            df_proveedor
            .groupby(["Material", "Texto breve"], dropna=False)
            .agg(agrupaciones)
            .reset_index()
        )

        resumen.columns = [
            "Material",
            "Texto breve",
            "Cantidad OCs",
            "Primera fecha",
            "Última fecha",
            "Precio mínimo num",
            "Precio máximo num",
            "Cantidad líneas",
        ]
    else:
        resumen = (
            df_proveedor
            .groupby(["Material"], dropna=False)
            .agg(agrupaciones)
            .reset_index()
        )

        resumen.columns = [
            "Material",
            "Cantidad OCs",
            "Primera fecha",
            "Última fecha",
            "Precio mínimo num",
            "Precio máximo num",
            "Cantidad líneas",
        ]

    resumen["Primera fecha"] = pd.to_datetime(
        resumen["Primera fecha"],
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")

    resumen["Última fecha"] = pd.to_datetime(
        resumen["Última fecha"],
        errors="coerce",
    ).dt.strftime("%Y-%m-%d")

    resumen["Precio mínimo"] = resumen["Precio mínimo num"].apply(formato_miles_cl)
    resumen["Precio máximo"] = resumen["Precio máximo num"].apply(formato_miles_cl)

    columnas = [
        "Material",
        "Texto breve",
        "Cantidad líneas",
        "Cantidad OCs",
        "Primera fecha",
        "Última fecha",
        "Precio mínimo",
        "Precio máximo",
    ]

    columnas = [
        col for col in columnas
        if col in resumen.columns
    ]

    resumen = resumen[columnas]

    resumen = resumen.sort_values(
        by=["Material"],
        ascending=True,
    )

    return resumen


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

    return resultado[columnas_disponibles + [
        col for col in resultado.columns
        if col not in columnas_disponibles
    ]]


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
            - Flujo de consulta:
              1. Buscar por código proveedor SAP.
              2. Revisar materiales disponibles.
              3. Seleccionar material.
              4. Filtrar combinación proveedor-material.
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
    Muestra ayuda cuando no hay resultados para el proveedor.
    """
    with st.expander("Ayuda para revisar posibles proveedores", expanded=False):
        proveedores_disponibles = (
            df_pu[["Codigo proveedor", "Nombre proveedor limpio"]]
            .drop_duplicates()
            .sort_values("Codigo proveedor")
            .head(150)
        )

        st.caption("Primeros proveedores disponibles")
        st.dataframe(
            proveedores_disponibles,
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

    with st.expander("Vista previa de base PU filtrada", expanded=True):
        df_preview = preparar_df_visual(
            df_pu.head(100),
            COLUMNAS_VISTA_PREVIA,
        )

        st.dataframe(
            df_preview,
            use_container_width=True,
            hide_index=True,
        )

    # ========================================================
    # 3. BUSCAR PROVEEDOR
    # ========================================================

    st.markdown("---")
    st.subheader("3. Buscar proveedor")

    codigo_proveedor = st.text_input(
        "Código proveedor SAP",
        placeholder="Ejemplo: 449065",
    )

    buscar_proveedor = st.button(
        "Buscar proveedor",
        type="primary",
    )

    if buscar_proveedor:
        if not codigo_proveedor:
            st.warning("Debes ingresar un código de proveedor SAP.")
            st.stop()

        df_proveedor = filtrar_por_proveedor(
            df=df_pu,
            codigo_proveedor=codigo_proveedor,
        )

        st.session_state["codigo_proveedor_buscado"] = codigo_proveedor
        st.session_state["df_proveedor_pu"] = df_proveedor

    if "df_proveedor_pu" not in st.session_state:
        st.info("Ingresa un proveedor y presiona **Buscar proveedor**.")
        st.stop()

    df_proveedor = st.session_state["df_proveedor_pu"]
    codigo_proveedor_buscado = st.session_state["codigo_proveedor_buscado"]

    if df_proveedor.empty:
        st.warning(
            f"No se encontraron registros PU para el proveedor **{codigo_proveedor_buscado}**."
        )

        mostrar_ayuda_sin_resultados(df_pu)
        st.stop()

    nombre_proveedor = (
        df_proveedor["Nombre proveedor limpio"]
        .dropna()
        .astype(str)
        .replace("", pd.NA)
        .dropna()
        .unique()
    )

    nombre_proveedor_texto = nombre_proveedor[0] if len(nombre_proveedor) > 0 else ""

    st.success(
        f"Proveedor encontrado: **{codigo_proveedor_buscado}**"
        + (f" · **{nombre_proveedor_texto}**" if nombre_proveedor_texto else "")
    )

    materiales_unicos = df_proveedor["Material"].nunique()
    lineas_proveedor = len(df_proveedor)
    ocs_proveedor = df_proveedor["Documento compras"].nunique()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Materiales encontrados",
            f"{materiales_unicos:,}".replace(",", "."),
        )

    with col2:
        st.metric(
            "Líneas proveedor",
            f"{lineas_proveedor:,}".replace(",", "."),
        )

    with col3:
        st.metric(
            "OCs proveedor",
            f"{ocs_proveedor:,}".replace(",", "."),
        )

    st.markdown("---")
    st.subheader("4. Seleccionar material")

    resumen_materiales = resumen_materiales_por_proveedor(df_proveedor)

    st.caption("Materiales disponibles para el proveedor seleccionado")

    st.dataframe(
        resumen_materiales,
        use_container_width=True,
        hide_index=True,
    )

    lista_materiales = (
        df_proveedor["Material"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .sort_values()
        .tolist()
    )

    if not lista_materiales:
        st.warning("El proveedor existe, pero no tiene materiales válidos asociados.")
        st.stop()

    material_seleccionado = st.selectbox(
        "Selecciona un material",
        options=lista_materiales,
        index=0,
    )

    filtrar_material = st.button(
        "Filtrar material",
        type="primary",
    )

    if not filtrar_material:
        st.info("Selecciona un material y presiona **Filtrar material**.")
        st.stop()

    # ========================================================
    # 5. RESULTADO FINAL
    # ========================================================

    resultado = filtrar_por_proveedor_material(
        df=df_pu,
        codigo_proveedor=codigo_proveedor_buscado,
        codigo_material=material_seleccionado,
    )

    st.markdown("---")
    st.subheader("5. Resultado proveedor-material")

    if resultado.empty:
        st.warning(
            "No se encontraron órdenes de compra PU para la combinación proveedor-material seleccionada."
        )
        st.stop()

    st.success(
        f"Se encontraron **{len(resultado):,} líneas** para el proveedor "
        f"**{codigo_proveedor_buscado}** y material **{material_seleccionado}**."
        .replace(",", ".")
    )

    resultado_visual = preparar_df_visual(
        resultado,
        COLUMNAS_OUTPUT,
    )

    st.dataframe(
        resultado_visual,
        use_container_width=True,
        hide_index=True,
    )

    excel_bytes = descargar_excel(resultado_visual)

    st.download_button(
        label="Descargar resultado Excel",
        data=excel_bytes,
        file_name=f"resultado_oc_pu_{codigo_proveedor_buscado}_{material_seleccionado}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ============================================================
# EJECUTAR APP
# ============================================================

pagina_app()
