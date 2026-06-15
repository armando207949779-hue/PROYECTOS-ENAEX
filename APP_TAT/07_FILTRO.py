# ============================================================
# 07_FILTRO
# Filtro y búsqueda de solicitudes de compra
# Usa df_tat cargado desde 06_CARGAR_ARCHIVO
# ============================================================

import base64
from pathlib import Path
from io import BytesIO

import pandas as pd
import streamlit as st


# ============================================================
# Configuración de página
# ============================================================

st.set_page_config(
    page_title="07_FILTRO",
    page_icon="🔎",
    layout="wide",
)


# ============================================================
# Rutas
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# ============================================================
# Estilos
# IMPORTANTE:
# No se modifica .block-container para no afectar el logo.
# ============================================================

st.markdown(
    """
    <style>
        div[data-testid="stMetric"] {
            background-color: #f8f9fa;
            padding: 14px;
            border-radius: 12px;
            border: 1px solid #e9ecef;
        }

        div[data-testid="stFileUploader"] {
            padding: 10px;
            border-radius: 12px;
        }

        .app-header {
            text-align: center;
            margin-bottom: 1rem;
        }

        .app-title {
            font-size: 30px;
            font-weight: 700;
            margin-bottom: 0;
        }

        .app-subtitle {
            color: #6c757d;
            font-size: 16px;
            margin-top: 4px;
        }

        .step-box {
            background-color: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 16px;
        }

        .small-muted {
            color: #6c757d;
            font-size: 14px;
        }

        .field-label {
            font-weight: 700;
            color: #495057;
            font-size: 13px;
            margin-bottom: 2px;
        }

        .field-value {
            color: #212529;
            font-size: 15px;
            margin-bottom: 10px;
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
    else:
        st.warning(f"Logo no encontrado: {LOGO_PATH}")


# ============================================================
# Utilidades
# ============================================================

def obtener_separador(separador_csv: str):
    separadores = {
        "Automático": None,
        "Punto y coma (;)": ";",
        "Coma (,)": ",",
        "Tabulación": "\t",
    }

    return separadores.get(separador_csv, None)


@st.cache_data(show_spinner=False)
def leer_archivo_cache(
    archivo_bytes: bytes,
    nombre_archivo: str,
    separador_csv: str,
) -> pd.DataFrame:

    extension = Path(nombre_archivo).suffix.lower()
    buffer = BytesIO(archivo_bytes)

    if extension == ".parquet":
        return pd.read_parquet(buffer)

    if extension in [".xlsx", ".xls"]:
        return pd.read_excel(buffer)

    if extension == ".csv":
        sep = obtener_separador(separador_csv)

        try:
            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip",
            )

        except Exception:
            buffer.seek(0)

            return pd.read_csv(
                buffer,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip",
            )

    raise ValueError("Formato no soportado. Usa CSV, XLSX, XLS o PARQUET.")


def limpiar_nombres_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def normalizar_columnas_me80fn(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compatibilidad con archivos antiguos que aún tienen NME80FN.
    """
    df = df.copy()

    renombrar = {
        col: col.replace("NME80FN", "ME80FN")
        for col in df.columns
        if "NME80FN" in col
    }

    df = df.rename(columns=renombrar)

    if "Estado del match" in df.columns:
        df["Estado del match"] = (
            df["Estado del match"]
            .astype("string")
            .str.replace("NME80FN", "ME80FN", regex=False)
        )

    return df


def buscar_columna(df: pd.DataFrame, candidatos: list[str]) -> str | None:
    for col in candidatos:
        if col in df.columns:
            return col

    return None


def formatear_valor(valor) -> str:
    if pd.isna(valor):
        return ""

    if isinstance(valor, pd.Timestamp):
        return valor.strftime("%Y-%m-%d")

    return str(valor)


def normalizar_texto_serie(serie: pd.Series) -> pd.Series:
    return (
        serie
        .astype("string")
        .str.strip()
        .str.lower()
    )


def obtener_opciones(df: pd.DataFrame, columna: str, max_opciones: int = 300) -> list:
    if columna is None or columna not in df.columns:
        return []

    valores = (
        df[columna]
        .dropna()
        .astype("string")
        .str.strip()
    )

    valores = valores[valores.ne("")].unique().tolist()
    valores = sorted(valores)

    if len(valores) > max_opciones:
        return []

    return valores


def convertir_fecha_segura(serie: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(serie):
        return pd.to_datetime(serie, errors="coerce")

    return pd.to_datetime(
        serie,
        errors="coerce",
        dayfirst=True,
    )


def aplicar_filtro_texto(
    df: pd.DataFrame,
    columna: str | None,
    texto: str,
    modo: str = "Contiene",
) -> pd.DataFrame:

    if columna is None or columna not in df.columns:
        return df

    texto = str(texto).strip()

    if not texto:
        return df

    serie = normalizar_texto_serie(df[columna])
    texto_norm = texto.lower().strip()

    if modo == "Exacta":
        return df[serie.eq(texto_norm)].copy()

    return df[serie.str.contains(texto_norm, na=False, regex=False)].copy()


def aplicar_filtro_multiselect(
    df: pd.DataFrame,
    columna: str | None,
    valores: list,
) -> pd.DataFrame:

    if columna is None or columna not in df.columns:
        return df

    if not valores:
        return df

    return df[df[columna].astype("string").isin(valores)].copy()


def aplicar_filtro_fecha(
    df: pd.DataFrame,
    columna: str | None,
    rango_fecha,
) -> pd.DataFrame:

    if columna is None or columna not in df.columns:
        return df

    if not rango_fecha or len(rango_fecha) != 2:
        return df

    fecha_inicio, fecha_fin = rango_fecha

    if fecha_inicio is None or fecha_fin is None:
        return df

    df = df.copy()
    fecha_serie = convertir_fecha_segura(df[columna])

    fecha_inicio = pd.to_datetime(fecha_inicio)
    fecha_fin = pd.to_datetime(fecha_fin)

    mask = fecha_serie.between(
        fecha_inicio,
        fecha_fin,
        inclusive="both",
    )

    return df[mask.fillna(False)].copy()


def construir_resumen_columnas(df: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "N°": range(1, len(df.columns) + 1),
            "Columna": list(df.columns),
            "Tipo de dato": [str(df[col].dtype) for col in df.columns],
            "Valores no nulos": [int(df[col].notna().sum()) for col in df.columns],
            "Valores nulos": [int(df[col].isna().sum()) for col in df.columns],
        }
    )


def detectar_columnas_clave(df: pd.DataFrame) -> dict:
    return {
        "solped": buscar_columna(
            df,
            [
                "Solicitud de pedido - ME5A",
                "Solicitud de pedido",
                "Solicitud de compra ERP - ARIBA",
                "ariba_solicitud_compra_erp",
            ],
        ),
        "pedido": buscar_columna(
            df,
            [
                "Pedido - ME5A",
                "Pedido",
                "ID pedido - ARIBA",
                "ariba_id_pedido",
            ],
        ),
        "posicion": buscar_columna(
            df,
            [
                "Posición solicitud de pedido - ME5A",
                "Pos.solicitud pedido",
                "Posición de pedido - ME5A",
                "Posición de pedido",
            ],
        ),
        "material": buscar_columna(
            df,
            [
                "Material - ME5A",
                "Material",
                "Material - ME80FN",
            ],
        ),
        "centro": buscar_columna(
            df,
            [
                "Centro - ME5A",
                "Centro",
                "Centro - ME80FN",
            ],
        ),
        "estado_match": buscar_columna(
            df,
            [
                "Estado del match",
                "estado_match",
            ],
        ),
        "tipo_oc": buscar_columna(
            df,
            [
                "tipo_oc",
            ],
        ),
        "origen": buscar_columna(
            df,
            [
                "origen",
            ],
        ),
        "sistema": buscar_columna(
            df,
            [
                "sistema",
            ],
        ),
        "performance_tat": buscar_columna(
            df,
            [
                "performance_tat_total",
            ],
        ),
        "rango_incumplimiento": buscar_columna(
            df,
            [
                "rango_incumplimiento_tat",
            ],
        ),
        "fecha_solicitud": buscar_columna(
            df,
            [
                "fecha_solicitud_final",
                "Fecha de solicitud - ME5A",
                "Fecha de solicitud",
            ],
        ),
    }


def construir_columnas_preferidas(df: pd.DataFrame) -> list[str]:
    columnas = [
        "Solicitud de pedido - ME5A",
        "Solicitud de pedido",
        "Pedido - ME5A",
        "Pedido",
        "Posición solicitud de pedido - ME5A",
        "Pos.solicitud pedido",
        "Material - ME5A",
        "Material",
        "Texto breve - ME5A",
        "Texto breve",
        "Centro - ME5A",
        "Centro",
        "Estado del match",
        "tipo_oc",
        "origen",
        "sistema",
        "nombre_tipo_compra",
        "fecha_solicitud_final",
        "fecha_liberacion_final",
        "fecha_pedido_final",
        "fecha_facturacion_final",
        "fecha_recepcion_final",
        "dias_tat_total",
        "umbral_tat_total",
        "performance_tat_total",
        "dias_incumplimiento_tat",
        "rango_incumplimiento_tat",
    ]

    columnas = [
        col for col in columnas
        if col in df.columns
    ]

    if columnas:
        return columnas

    return list(df.columns)


def mostrar_campo(label: str, valor):
    st.markdown(
        f"""
        <div class="field-label">{label}</div>
        <div class="field-value">{formatear_valor(valor)}</div>
        """,
        unsafe_allow_html=True,
    )


def mostrar_ficha_solped(registro: pd.Series, columnas_clave: dict):
    st.markdown("#### Información de la solicitud")

    col1, col2, col3 = st.columns(3)

    with col1:
        mostrar_campo(
            "Solicitud de pedido",
            registro.get(columnas_clave["solped"], "")
            if columnas_clave["solped"]
            else "",
        )

        mostrar_campo(
            "Pedido",
            registro.get(columnas_clave["pedido"], "")
            if columnas_clave["pedido"]
            else "",
        )

        mostrar_campo(
            "Posición",
            registro.get(columnas_clave["posicion"], "")
            if columnas_clave["posicion"]
            else "",
        )

    with col2:
        mostrar_campo(
            "Material",
            registro.get(columnas_clave["material"], "")
            if columnas_clave["material"]
            else "",
        )

        mostrar_campo(
            "Centro",
            registro.get(columnas_clave["centro"], "")
            if columnas_clave["centro"]
            else "",
        )

        mostrar_campo(
            "Estado del match",
            registro.get(columnas_clave["estado_match"], "")
            if columnas_clave["estado_match"]
            else "",
        )

    with col3:
        mostrar_campo(
            "Tipo OC",
            registro.get(columnas_clave["tipo_oc"], "")
            if columnas_clave["tipo_oc"]
            else "",
        )

        mostrar_campo(
            "Origen",
            registro.get(columnas_clave["origen"], "")
            if columnas_clave["origen"]
            else "",
        )

        mostrar_campo(
            "Sistema",
            registro.get(columnas_clave["sistema"], "")
            if columnas_clave["sistema"]
            else "",
        )

    st.markdown("#### Fechas y TAT")

    columnas_fechas = [
        "fecha_solicitud_final",
        "fecha_liberacion_final",
        "fecha_pedido_final",
        "fecha_facturacion_final",
        "fecha_recepcion_final",
    ]

    data_fechas = []

    for col in columnas_fechas:
        if col in registro.index:
            data_fechas.append(
                {
                    "Campo": col,
                    "Valor": formatear_valor(registro.get(col)),
                }
            )

    if data_fechas:
        st.dataframe(
            pd.DataFrame(data_fechas),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No se encontraron columnas de fechas finales para esta solicitud.")

    st.markdown("#### Performance")

    columnas_performance = [
        "dias_liberacion_solped",
        "dias_comprador",
        "dias_liberacion_pedido",
        "dias_proveedor",
        "dias_logistica",
        "dias_tat_total",
        "umbral_tat_total",
        "performance_tat_total",
        "dias_incumplimiento_tat",
        "rango_incumplimiento_tat",
    ]

    data_perf = []

    for col in columnas_performance:
        if col in registro.index:
            data_perf.append(
                {
                    "Campo": col,
                    "Valor": formatear_valor(registro.get(col)),
                }
            )

    if data_perf:
        st.dataframe(
            pd.DataFrame(data_perf),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No se encontraron columnas de performance para esta solicitud.")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow",
    )

    return output.getvalue()


def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig",
    ).encode("utf-8-sig")


@st.cache_data(show_spinner=False)
def convertir_a_parquet_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_parquet(df)


@st.cache_data(show_spinner=False)
def convertir_a_csv_cache(df: pd.DataFrame) -> bytes:
    return convertir_a_csv(df)


# ============================================================
# Encabezado
# ============================================================

mostrar_logo()

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">07_FILTRO</div>
        <div class="app-subtitle">
            Filtra, busca y visualiza solicitudes de compra individuales
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Obtener dataframe activo
# ============================================================

df_tat = st.session_state.get("df_tat")
nombre_archivo_tat = st.session_state.get("nombre_archivo_tat")

if df_tat is None:
    st.info(
        "No hay un archivo activo en sesión. Primero carga un archivo en 06_CARGAR_ARCHIVO."
    )

    with st.expander("Carga temporal para esta búsqueda", expanded=False):
        separador_csv_temporal = st.selectbox(
            "Separador CSV",
            options=[
                "Automático",
                "Punto y coma (;)",
                "Coma (,)",
                "Tabulación",
            ],
            index=0,
            key="filtro_separador_csv_temporal",
        )

        archivo_temporal = st.file_uploader(
            "Cargar archivo temporal",
            type=["parquet", "xlsx", "xls", "csv"],
            key="filtro_archivo_temporal",
        )

        if archivo_temporal is not None:
            try:
                df_tat = leer_archivo_cache(
                    archivo_bytes=archivo_temporal.getvalue(),
                    nombre_archivo=archivo_temporal.name,
                    separador_csv=separador_csv_temporal,
                )

                df_tat = limpiar_nombres_columnas(df_tat)
                df_tat = normalizar_columnas_me80fn(df_tat)

                st.session_state["df_tat"] = df_tat
                st.session_state["nombre_archivo_tat"] = archivo_temporal.name

                nombre_archivo_tat = archivo_temporal.name

                st.success(f"Archivo temporal cargado: {archivo_temporal.name}")

            except Exception as e:
                st.error("No fue posible leer el archivo temporal.")
                st.exception(e)
                st.stop()

    if df_tat is None:
        st.stop()

df_tat = limpiar_nombres_columnas(df_tat)
df_tat = normalizar_columnas_me80fn(df_tat)

columnas_clave = detectar_columnas_clave(df_tat)

if columnas_clave["solped"] is None:
    st.error(
        "No se encontró una columna de solicitud de pedido. "
        "Se esperaba una columna como 'Solicitud de pedido - ME5A' o 'Solicitud de pedido'."
    )
    st.stop()


# ============================================================
# Filtros en encabezado
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">Filtros y búsqueda</h4>
        <p class="small-muted">
            Usa los filtros para reducir la información o busca una SOLPED específica para visualizar su detalle.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])

with col_f1:
    busqueda_solped = st.text_input(
        "Buscar SOLPED",
        placeholder="Ejemplo: 6000123456",
        key="filtro_busqueda_solped",
    )

with col_f2:
    modo_busqueda = st.selectbox(
        "Modo búsqueda",
        options=[
            "Contiene",
            "Exacta",
        ],
        index=0,
        key="filtro_modo_busqueda",
    )

with col_f3:
    if columnas_clave["estado_match"]:
        opciones_estado = obtener_opciones(
            df_tat,
            columnas_clave["estado_match"],
        )

        filtro_estado = st.multiselect(
            "Estado match",
            options=opciones_estado,
            key="filtro_estado_match",
        )
    else:
        filtro_estado = []

with col_f4:
    if columnas_clave["performance_tat"]:
        opciones_performance = obtener_opciones(
            df_tat,
            columnas_clave["performance_tat"],
        )

        filtro_performance = st.multiselect(
            "Performance TAT",
            options=opciones_performance,
            key="filtro_performance_tat",
        )
    else:
        filtro_performance = []


col_f5, col_f6, col_f7, col_f8 = st.columns(4)

with col_f5:
    if columnas_clave["tipo_oc"]:
        opciones_tipo_oc = obtener_opciones(
            df_tat,
            columnas_clave["tipo_oc"],
        )

        filtro_tipo_oc = st.multiselect(
            "Tipo OC",
            options=opciones_tipo_oc,
            key="filtro_tipo_oc",
        )
    else:
        filtro_tipo_oc = []

with col_f6:
    if columnas_clave["origen"]:
        opciones_origen = obtener_opciones(
            df_tat,
            columnas_clave["origen"],
        )

        filtro_origen = st.multiselect(
            "Origen",
            options=opciones_origen,
            key="filtro_origen",
        )
    else:
        filtro_origen = []

with col_f7:
    if columnas_clave["sistema"]:
        opciones_sistema = obtener_opciones(
            df_tat,
            columnas_clave["sistema"],
        )

        filtro_sistema = st.multiselect(
            "Sistema",
            options=opciones_sistema,
            key="filtro_sistema",
        )
    else:
        filtro_sistema = []

with col_f8:
    if columnas_clave["centro"]:
        filtro_centro = st.text_input(
            "Centro",
            placeholder="Ejemplo: CEN1",
            key="filtro_centro",
        )
    else:
        filtro_centro = ""


if columnas_clave["fecha_solicitud"]:
    fecha_serie = convertir_fecha_segura(df_tat[columnas_clave["fecha_solicitud"]])
    fecha_min = fecha_serie.min()
    fecha_max = fecha_serie.max()

    if pd.notna(fecha_min) and pd.notna(fecha_max):
        rango_fecha = st.date_input(
            "Rango fecha solicitud",
            value=(fecha_min.date(), fecha_max.date()),
            key="filtro_rango_fecha",
        )
    else:
        rango_fecha = None
else:
    rango_fecha = None


limpiar_filtros = st.button(
    "Limpiar filtros",
    use_container_width=True,
)

if limpiar_filtros:
    claves_filtros = [
        "filtro_busqueda_solped",
        "filtro_modo_busqueda",
        "filtro_estado_match",
        "filtro_performance_tat",
        "filtro_tipo_oc",
        "filtro_origen",
        "filtro_sistema",
        "filtro_centro",
        "filtro_rango_fecha",
    ]

    for clave in claves_filtros:
        if clave in st.session_state:
            del st.session_state[clave]

    st.rerun()


# ============================================================
# Aplicar filtros
# ============================================================

df_filtrado = df_tat.copy()

df_filtrado = aplicar_filtro_texto(
    df=df_filtrado,
    columna=columnas_clave["solped"],
    texto=busqueda_solped,
    modo=modo_busqueda,
)

df_filtrado = aplicar_filtro_multiselect(
    df=df_filtrado,
    columna=columnas_clave["estado_match"],
    valores=filtro_estado,
)

df_filtrado = aplicar_filtro_multiselect(
    df=df_filtrado,
    columna=columnas_clave["performance_tat"],
    valores=filtro_performance,
)

df_filtrado = aplicar_filtro_multiselect(
    df=df_filtrado,
    columna=columnas_clave["tipo_oc"],
    valores=filtro_tipo_oc,
)

df_filtrado = aplicar_filtro_multiselect(
    df=df_filtrado,
    columna=columnas_clave["origen"],
    valores=filtro_origen,
)

df_filtrado = aplicar_filtro_multiselect(
    df=df_filtrado,
    columna=columnas_clave["sistema"],
    valores=filtro_sistema,
)

df_filtrado = aplicar_filtro_texto(
    df=df_filtrado,
    columna=columnas_clave["centro"],
    texto=filtro_centro,
    modo="Contiene",
)

df_filtrado = aplicar_filtro_fecha(
    df=df_filtrado,
    columna=columnas_clave["fecha_solicitud"],
    rango_fecha=rango_fecha,
)


# ============================================================
# Indicadores
# ============================================================

total_original = len(df_tat)
total_filtrado = len(df_filtrado)

total_solped_original = (
    int(df_tat[columnas_clave["solped"]].nunique(dropna=True))
    if columnas_clave["solped"] in df_tat.columns
    else 0
)

total_solped_filtrado = (
    int(df_filtrado[columnas_clave["solped"]].nunique(dropna=True))
    if columnas_clave["solped"] in df_filtrado.columns
    else 0
)

col_m1, col_m2, col_m3, col_m4 = st.columns(4)

col_m1.metric("Filas totales", f"{total_original:,}")
col_m2.metric("Filas filtradas", f"{total_filtrado:,}")
col_m3.metric("SOLPED únicas", f"{total_solped_original:,}")
col_m4.metric("SOLPED filtradas", f"{total_solped_filtrado:,}")


# ============================================================
# Resultado búsqueda individual
# ============================================================

if busqueda_solped.strip():
    st.markdown(
        """
        <div class="step-box">
            <h4 style="margin-top:0;">Resultado de búsqueda individual</h4>
            <p class="small-muted">
                Detalle de la SOLPED buscada según los filtros aplicados.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df_filtrado.empty:
        st.warning("No se encontraron registros para la SOLPED buscada con los filtros actuales.")
    else:
        st.success(f"Se encontraron {len(df_filtrado):,} registro(s) para la búsqueda.")

        if len(df_filtrado) == 1:
            registro = df_filtrado.iloc[0]
            mostrar_ficha_solped(registro, columnas_clave)
        else:
            df_selector = df_filtrado.copy()
            df_selector["_indice_original"] = df_selector.index

            columnas_selector = [
                columnas_clave["solped"],
                columnas_clave["pedido"],
                columnas_clave["posicion"],
                columnas_clave["material"],
                columnas_clave["centro"],
                columnas_clave["estado_match"],
                columnas_clave["performance_tat"],
            ]

            columnas_selector = [
                col for col in columnas_selector
                if col is not None and col in df_selector.columns
            ]

            st.dataframe(
                df_selector[columnas_selector].head(200),
                use_container_width=True,
                hide_index=True,
            )

            indices = df_selector["_indice_original"].tolist()

            indice_elegido = st.selectbox(
                "Selecciona un registro para visualizar detalle",
                options=indices,
                format_func=lambda x: f"Fila original {x}",
                key="selector_registro_solped",
            )

            registro = df_tat.loc[indice_elegido]
            mostrar_ficha_solped(registro, columnas_clave)


# ============================================================
# Tabla filtrada
# ============================================================

st.markdown(
    """
    <div class="step-box">
        <h4 style="margin-top:0;">Resultado filtrado</h4>
        <p class="small-muted">
            Vista consolidada de los registros filtrados.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

columnas_preferidas = construir_columnas_preferidas(df_filtrado)

limite_vista = st.number_input(
    "Filas a mostrar",
    min_value=20,
    max_value=1000,
    value=200,
    step=20,
)

if df_filtrado.empty:
    st.warning("No hay registros para mostrar con los filtros actuales.")
else:
    st.dataframe(
        df_filtrado[columnas_preferidas].head(int(limite_vista)),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Detalle opcional
# ============================================================

with st.expander("Columnas disponibles", expanded=False):
    st.dataframe(
        construir_resumen_columnas(df_tat),
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# Descarga opcional
# ============================================================

with st.expander("Descargar resultado filtrado", expanded=False):
    st.caption("Parquet es el formato recomendado. CSV se prepara solo cuando lo solicitas.")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        if not df_filtrado.empty:
            parquet_bytes = convertir_a_parquet_cache(df_filtrado)

            st.download_button(
                label="Descargar Parquet filtrado",
                data=parquet_bytes,
                file_name="resultado_filtrado_solped.parquet",
                mime="application/octet-stream",
                type="primary",
                use_container_width=True,
            )
        else:
            st.button(
                "Descargar Parquet filtrado",
                disabled=True,
                use_container_width=True,
            )

    with col_d2:
        preparar_csv = st.button(
            "Preparar CSV filtrado",
            use_container_width=True,
        )

        if preparar_csv:
            if df_filtrado.empty:
                st.warning("No hay registros filtrados para exportar.")
            else:
                with st.spinner("Preparando CSV..."):
                    csv_bytes = convertir_a_csv_cache(df_filtrado)

                st.download_button(
                    label="Descargar CSV filtrado",
                    data=csv_bytes,
                    file_name="resultado_filtrado_solped.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
