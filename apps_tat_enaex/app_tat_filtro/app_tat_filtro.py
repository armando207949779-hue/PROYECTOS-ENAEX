import io
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st


# =========================================================
# Configuración general
# =========================================================
st.set_page_config(
    page_title="Buscador SolPed / OC",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Buscador de SolPed y Órdenes de Compra")
st.caption(
    "Carga un archivo Parquet, CSV o Excel ya procesado y filtra por SolPed, OC, material, centro, solicitante, performance y días calculados."
)


# =========================================================
# Columnas principales esperadas
# =========================================================
COL_SOLPED = "Solicitud de pedido - ME5A"
COL_OC_ME5A = "Pedido - ME5A"
COL_OC_NME = "Documento de compras - NME80FN"
COL_POS_SOLPED = "Posición solicitud de pedido - ME5A"
COL_POS_OC = "Posición de pedido - ME5A"
COL_MATERIAL = "Material - ME5A"
COL_TEXTO = "Texto breve - ME5A"
COL_CENTRO = "Centro - ME5A"
COL_SOLICITANTE = "Solicitante"
COL_AUTOR = "Autor"
COL_GRUPO_COMPRAS = "Grupo de compras"
COL_TIPO_OC = "tipo_oc"
COL_ORIGEN = "origen"
COL_SISTEMA = "sistema"
COL_ESTADO_MATCH = "Estado del match"
COL_PERF_TAT = "performance_tat_total"
COL_RANGO_INC = "rango_incumplimiento_tat"
COL_INC_TAT = "incumplimiento_tat"
COL_DIAS_TAT = "dias_tat_total"
COL_DIAS_INC = "dias_incumplimiento_tat"
COL_MONTO = "monto"

FECHAS_CANDIDATAS = [
    "Fecha de solicitud - ME5A",
    "Fecha modificación",
    "Fecha de liberación - ME5A",
    "Fecha de pedido - ME5A",
    "Fecha de entrega - ME5A",
    "Fecha de liberación",
    "Fecha solicitud de compra - ARIBA",
    "Fecha de aprobación - ARIBA",
    "Fecha de entrada - NME80FN",
    "Fecha de documento - NME80FN",
    "Fecha contabilización - NME80FN",
    "Fecha facturación proveedor - NME80FN",
    "Fecha recepción mercancía - NME80FN",
    "fecha_solicitud_final",
    "fecha_liberacion_final",
    "fecha_pedido_final",
    "fecha_facturacion_final",
    "fecha_recepcion_final",
]

COLUMNAS_RESUMEN = [
    COL_SOLPED,
    COL_OC_ME5A,
    COL_OC_NME,
    COL_POS_SOLPED,
    COL_POS_OC,
    COL_MATERIAL,
    COL_TEXTO,
    COL_CENTRO,
    COL_SOLICITANTE,
    COL_GRUPO_COMPRAS,
    COL_TIPO_OC,
    COL_ORIGEN,
    COL_SISTEMA,
    COL_ESTADO_MATCH,
    COL_PERF_TAT,
    COL_RANGO_INC,
    COL_DIAS_TAT,
    COL_DIAS_INC,
    COL_MONTO,
    "fecha_solicitud_final",
    "fecha_pedido_final",
    "fecha_recepcion_final",
]

COLUMNAS_DIAS = [
    "dias_liberacion_solped",
    "dias_comprador",
    "dias_liberacion_pedido",
    "dias_proveedor",
    "dias_logistica",
    "dias_tat_total",
    "dias_incumplimiento_tat",
]

COLUMNAS_PERFORMANCE = [
    "performance_liberacion_solped",
    "performance_comprador",
    "performance_liberacion_pedido",
    "performance_proveedor",
    "performance_logistica",
    "performance_tat_total",
]


# =========================================================
# Funciones de lectura y limpieza
# =========================================================
def obtener_separador(opcion: str):
    if opcion == "Automático":
        return None
    if opcion == "Punto y coma (;)":
        return ";"
    if opcion == "Coma (,)":
        return ","
    if opcion == "Tabulación":
        return "\t"
    return None


@st.cache_data(show_spinner=False)
def leer_archivo(bytes_archivo: bytes, nombre_archivo: str, separador_csv: str) -> pd.DataFrame:
    buffer = io.BytesIO(bytes_archivo)
    nombre = nombre_archivo.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(buffer)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)
        try:
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="utf-8-sig", on_bad_lines="skip")
        except Exception:
            buffer.seek(0)
            return pd.read_csv(buffer, sep=sep, engine="python", encoding="latin1", on_bad_lines="skip")

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(buffer)

    raise ValueError("Formato no soportado. Usa Parquet, CSV o Excel.")


def limpiar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    return df


def convertir_fechas_visuales(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte columnas de fecha para visualización.

    Soporta fechas datetime, texto, timestamp en milisegundos y timestamp en segundos.
    """
    df = df.copy()

    for col in FECHAS_CANDIDATAS:
        if col not in df.columns:
            continue

        serie = df[col]

        if pd.api.types.is_datetime64_any_dtype(serie):
            df[col] = pd.to_datetime(serie, errors="coerce")
            continue

        serie_num = pd.to_numeric(serie, errors="coerce")
        resultado = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
        mask_num = serie_num.notna()

        if mask_num.any():
            mask_ms = mask_num & serie_num.abs().ge(10**11)
            mask_s = mask_num & serie_num.abs().lt(10**11)

            if mask_ms.any():
                resultado.loc[mask_ms] = pd.to_datetime(serie_num.loc[mask_ms], unit="ms", errors="coerce")
            if mask_s.any():
                resultado.loc[mask_s] = pd.to_datetime(serie_num.loc[mask_s], unit="s", errors="coerce")

        mask_texto = ~mask_num
        if mask_texto.any():
            resultado.loc[mask_texto] = pd.to_datetime(serie.loc[mask_texto], errors="coerce", dayfirst=True)

        # Solo reemplaza si logró convertir algo. Si no, mantiene el valor original.
        if resultado.notna().any():
            df[col] = resultado

    return df


def columna_existe(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns


def opciones_columna(df: pd.DataFrame, col: str, max_opciones: int = 500):
    if col not in df.columns:
        return []
    valores = df[col].dropna().astype(str).sort_values().unique().tolist()
    return valores[:max_opciones]


def contiene_texto(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    if columna not in df.columns or not texto:
        return pd.Series(True, index=df.index)
    return df[columna].astype(str).str.contains(str(texto), case=False, na=False, regex=False)


def filtrar_por_ids(df: pd.DataFrame, columna: str, texto: str) -> pd.Series:
    """Permite buscar uno o varios IDs separados por coma, espacio o salto de línea."""
    if columna not in df.columns or not texto.strip():
        return pd.Series(True, index=df.index)

    tokens = (
        texto.replace("\n", ",")
        .replace(";", ",")
        .replace(" ", ",")
        .split(",")
    )
    tokens = [t.strip() for t in tokens if t.strip()]

    if not tokens:
        return pd.Series(True, index=df.index)

    serie = df[columna].astype(str).str.replace(".0", "", regex=False)
    mask = pd.Series(False, index=df.index)

    for token in tokens:
        token_limpio = token.replace(".0", "")
        mask = mask | serie.str.contains(token_limpio, case=False, na=False, regex=False)

    return mask


def aplicar_rango_numerico(df: pd.DataFrame, columna: str, minimo, maximo) -> pd.Series:
    if columna not in df.columns:
        return pd.Series(True, index=df.index)

    serie = pd.to_numeric(df[columna], errors="coerce")
    mask = pd.Series(True, index=df.index)

    if minimo is not None:
        mask = mask & serie.ge(minimo)
    if maximo is not None:
        mask = mask & serie.le(maximo)

    return mask


def dataframe_a_excel(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Resultado")
    return output.getvalue()


def dataframe_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    df.to_parquet(output, index=False, engine="pyarrow")
    return output.getvalue()


# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.header("Carga")

    separador_csv = st.selectbox(
        "Separador CSV",
        ["Automático", "Punto y coma (;)", "Coma (,)", "Tabulación"],
        index=0,
    )

    uploaded_file = st.file_uploader(
        "Sube el archivo ya procesado",
        type=["parquet", "csv", "xlsx", "xls"],
    )

    st.divider()
    st.header("Vista")

    limite_vista = st.number_input(
        "Filas a mostrar",
        min_value=50,
        max_value=5000,
        value=500,
        step=50,
    )

    mostrar_todas_columnas = st.checkbox("Mostrar todas las columnas", value=False)


if uploaded_file is None:
    st.info("Sube un archivo Parquet, CSV o Excel para comenzar.")
    st.stop()

try:
    df = leer_archivo(uploaded_file.getvalue(), uploaded_file.name, separador_csv)
    df = limpiar_columnas(df)
    df = convertir_fechas_visuales(df)
except Exception as e:
    st.error("No se pudo leer el archivo.")
    st.exception(e)
    st.stop()


# =========================================================
# Filtros principales
# =========================================================
st.subheader("Filtros principales")

with st.expander("Buscar por SolPed, OC, posición y texto", expanded=True):
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        txt_solped = st.text_input("SolPed", placeholder="Ej: 1001973319")
        txt_pos_solped = st.text_input("Posición SolPed", placeholder="Ej: 10")

    with c2:
        txt_oc = st.text_input("Orden de compra / Pedido", placeholder="Ej: 4502321875")
        txt_pos_oc = st.text_input("Posición OC", placeholder="Ej: 10")

    with c3:
        txt_material = st.text_input("Material", placeholder="Ej: 20012021")
        txt_descripcion = st.text_input("Descripción / texto breve", placeholder="Ej: bloqueador")

    with c4:
        txt_solicitante = st.text_input("Solicitante", placeholder="Ej: c.silva")
        txt_autor = st.text_input("Autor", placeholder="Ej: CL17330735")

with st.expander("Filtros de clasificación y performance", expanded=True):
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        tipo_oc_sel = st.multiselect("Tipo OC", opciones_columna(df, COL_TIPO_OC))
        origen_sel = st.multiselect("Origen", opciones_columna(df, COL_ORIGEN))

    with c2:
        sistema_sel = st.multiselect("Sistema", opciones_columna(df, COL_SISTEMA))
        centro_sel = st.multiselect("Centro", opciones_columna(df, COL_CENTRO))

    with c3:
        grupo_sel = st.multiselect("Grupo de compras", opciones_columna(df, COL_GRUPO_COMPRAS))
        estado_match_sel = st.multiselect("Estado del match", opciones_columna(df, COL_ESTADO_MATCH))

    with c4:
        perf_tat_sel = st.multiselect("Performance TAT", opciones_columna(df, COL_PERF_TAT))
        rango_inc_sel = st.multiselect("Rango incumplimiento TAT", opciones_columna(df, COL_RANGO_INC))

with st.expander("Filtros por días y monto", expanded=False):
    c1, c2, c3 = st.columns(3)

    with c1:
        dias_tat_min = st.number_input("Días TAT mínimo", value=0, step=1)
        usar_dias_tat_min = st.checkbox("Aplicar mínimo TAT", value=False)

    with c2:
        dias_tat_max = st.number_input("Días TAT máximo", value=9999, step=1)
        usar_dias_tat_max = st.checkbox("Aplicar máximo TAT", value=False)

    with c3:
        solo_incumplimiento = st.checkbox("Solo incumplimiento TAT", value=False)
        solo_fechas_inconsistentes = st.checkbox("Solo fechas inconsistentes", value=False)

    c4, c5 = st.columns(2)
    with c4:
        monto_min = st.number_input("Monto mínimo", value=0.0, step=1000.0)
        usar_monto_min = st.checkbox("Aplicar monto mínimo", value=False)

    with c5:
        monto_max = st.number_input("Monto máximo", value=0.0, step=1000.0)
        usar_monto_max = st.checkbox("Aplicar monto máximo", value=False)

with st.expander("Filtro por fechas", expanded=False):
    fecha_col_disponibles = [c for c in FECHAS_CANDIDATAS if c in df.columns and pd.api.types.is_datetime64_any_dtype(df[c])]

    if fecha_col_disponibles:
        col_fecha_filtro = st.selectbox("Columna de fecha", fecha_col_disponibles, index=0)
        fecha_min_real = df[col_fecha_filtro].min()
        fecha_max_real = df[col_fecha_filtro].max()

        if pd.notna(fecha_min_real) and pd.notna(fecha_max_real):
            c1, c2 = st.columns(2)
            with c1:
                fecha_desde = st.date_input("Desde", value=fecha_min_real.date())
            with c2:
                fecha_hasta = st.date_input("Hasta", value=fecha_max_real.date())
            usar_filtro_fecha = st.checkbox("Aplicar filtro de fecha", value=False)
        else:
            usar_filtro_fecha = False
            st.warning("La columna seleccionada no tiene fechas válidas.")
    else:
        usar_filtro_fecha = False
        st.info("No se encontraron columnas de fecha convertibles para filtrar.")


# =========================================================
# Aplicar filtros
# =========================================================
mask = pd.Series(True, index=df.index)

mask &= filtrar_por_ids(df, COL_SOLPED, txt_solped)
mask &= filtrar_por_ids(df, COL_OC_ME5A, txt_oc) | filtrar_por_ids(df, COL_OC_NME, txt_oc)
mask &= filtrar_por_ids(df, COL_POS_SOLPED, txt_pos_solped)
mask &= filtrar_por_ids(df, COL_POS_OC, txt_pos_oc)
mask &= filtrar_por_ids(df, COL_MATERIAL, txt_material)
mask &= contiene_texto(df, COL_TEXTO, txt_descripcion)
mask &= contiene_texto(df, COL_SOLICITANTE, txt_solicitante)
mask &= contiene_texto(df, COL_AUTOR, txt_autor)

if tipo_oc_sel and COL_TIPO_OC in df.columns:
    mask &= df[COL_TIPO_OC].astype(str).isin(tipo_oc_sel)
if origen_sel and COL_ORIGEN in df.columns:
    mask &= df[COL_ORIGEN].astype(str).isin(origen_sel)
if sistema_sel and COL_SISTEMA in df.columns:
    mask &= df[COL_SISTEMA].astype(str).isin(sistema_sel)
if centro_sel and COL_CENTRO in df.columns:
    mask &= df[COL_CENTRO].astype(str).isin(centro_sel)
if grupo_sel and COL_GRUPO_COMPRAS in df.columns:
    mask &= df[COL_GRUPO_COMPRAS].astype(str).isin(grupo_sel)
if estado_match_sel and COL_ESTADO_MATCH in df.columns:
    mask &= df[COL_ESTADO_MATCH].astype(str).isin(estado_match_sel)
if perf_tat_sel and COL_PERF_TAT in df.columns:
    mask &= df[COL_PERF_TAT].astype(str).isin(perf_tat_sel)
if rango_inc_sel and COL_RANGO_INC in df.columns:
    mask &= df[COL_RANGO_INC].astype(str).isin(rango_inc_sel)

mask &= aplicar_rango_numerico(
    df,
    COL_DIAS_TAT,
    dias_tat_min if usar_dias_tat_min else None,
    dias_tat_max if usar_dias_tat_max else None,
)

mask &= aplicar_rango_numerico(
    df,
    COL_MONTO,
    monto_min if usar_monto_min else None,
    monto_max if usar_monto_max else None,
)

if solo_incumplimiento and COL_INC_TAT in df.columns:
    mask &= df[COL_INC_TAT].eq(True)

if solo_fechas_inconsistentes and "tiene_fechas_inconsistentes" in df.columns:
    mask &= df["tiene_fechas_inconsistentes"].eq(True)

if usar_filtro_fecha and fecha_col_disponibles:
    inicio = pd.Timestamp(fecha_desde)
    fin = pd.Timestamp(fecha_hasta) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    mask &= df[col_fecha_filtro].between(inicio, fin, inclusive="both")

df_filtrado = df.loc[mask].copy()


# =========================================================
# Métricas
# =========================================================
st.subheader("Métricas del resultado filtrado")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Filas totales", f"{len(df):,}")
c2.metric("Filas filtradas", f"{len(df_filtrado):,}")

if COL_PERF_TAT in df_filtrado.columns:
    c3.metric("TAT cumple", f"{int(df_filtrado[COL_PERF_TAT].eq('Cumple').sum()):,}")
    c4.metric("TAT no cumple", f"{int(df_filtrado[COL_PERF_TAT].eq('No cumple').sum()):,}")
else:
    c3.metric("TAT cumple", "N/A")
    c4.metric("TAT no cumple", "N/A")

if COL_MONTO in df_filtrado.columns:
    monto_total = pd.to_numeric(df_filtrado[COL_MONTO], errors="coerce").sum()
    c5.metric("Monto filtrado", f"{monto_total:,.0f}")
else:
    c5.metric("Monto filtrado", "N/A")

c6, c7, c8, c9 = st.columns(4)
if COL_DIAS_TAT in df_filtrado.columns:
    dias_tat = pd.to_numeric(df_filtrado[COL_DIAS_TAT], errors="coerce")
    c6.metric("TAT promedio", f"{dias_tat.mean():.1f}" if dias_tat.notna().any() else "N/A")
    c7.metric("TAT máximo", f"{dias_tat.max():.0f}" if dias_tat.notna().any() else "N/A")
else:
    c6.metric("TAT promedio", "N/A")
    c7.metric("TAT máximo", "N/A")

if COL_DIAS_INC in df_filtrado.columns:
    dias_inc = pd.to_numeric(df_filtrado[COL_DIAS_INC], errors="coerce")
    c8.metric("Incumplimiento promedio", f"{dias_inc.mean():.1f}" if dias_inc.notna().any() else "N/A")
    c9.metric("Incumplimiento máximo", f"{dias_inc.max():.0f}" if dias_inc.notna().any() else "N/A")
else:
    c8.metric("Incumplimiento promedio", "N/A")
    c9.metric("Incumplimiento máximo", "N/A")


# =========================================================
# Tablas resumen
# =========================================================
with st.expander("Distribuciones", expanded=False):
    c1, c2 = st.columns(2)

    with c1:
        if COL_PERF_TAT in df_filtrado.columns:
            st.markdown("**Performance TAT**")
            st.dataframe(
                df_filtrado[COL_PERF_TAT].value_counts(dropna=False).reset_index(name="Cantidad").rename(columns={COL_PERF_TAT: "Performance TAT"}),
                use_container_width=True,
                hide_index=True,
            )

        if COL_TIPO_OC in df_filtrado.columns:
            st.markdown("**Tipo OC**")
            st.dataframe(
                df_filtrado[COL_TIPO_OC].value_counts(dropna=False).reset_index(name="Cantidad").rename(columns={COL_TIPO_OC: "Tipo OC"}),
                use_container_width=True,
                hide_index=True,
            )

    with c2:
        if COL_RANGO_INC in df_filtrado.columns:
            st.markdown("**Rango incumplimiento TAT**")
            st.dataframe(
                df_filtrado[COL_RANGO_INC].value_counts(dropna=False).reset_index(name="Cantidad").rename(columns={COL_RANGO_INC: "Rango"}),
                use_container_width=True,
                hide_index=True,
            )

        if COL_ESTADO_MATCH in df_filtrado.columns:
            st.markdown("**Estado del match**")
            st.dataframe(
                df_filtrado[COL_ESTADO_MATCH].value_counts(dropna=False).reset_index(name="Cantidad").rename(columns={COL_ESTADO_MATCH: "Estado"}),
                use_container_width=True,
                hide_index=True,
            )


# =========================================================
# Resultado
# =========================================================
st.subheader("Resultado filtrado")

columnas_disponibles_resumen = [c for c in COLUMNAS_RESUMEN if c in df_filtrado.columns]

if mostrar_todas_columnas or not columnas_disponibles_resumen:
    columnas_a_mostrar = df_filtrado.columns.tolist()
else:
    columnas_extra = [c for c in COLUMNAS_DIAS + COLUMNAS_PERFORMANCE if c in df_filtrado.columns and c not in columnas_disponibles_resumen]
    columnas_a_mostrar = columnas_disponibles_resumen + columnas_extra

with st.expander("Seleccionar columnas visibles", expanded=False):
    columnas_a_mostrar = st.multiselect(
        "Columnas",
        options=df_filtrado.columns.tolist(),
        default=columnas_a_mostrar,
    )

if columnas_a_mostrar:
    st.dataframe(
        df_filtrado[columnas_a_mostrar].head(int(limite_vista)),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.warning("Selecciona al menos una columna para visualizar.")


# =========================================================
# Detalle por registro
# =========================================================
with st.expander("Detalle de un registro", expanded=False):
    if df_filtrado.empty:
        st.info("No hay registros filtrados para mostrar detalle.")
    else:
        opciones_detalle = []
        for idx, row in df_filtrado.head(5000).iterrows():
            solped = row.get(COL_SOLPED, "")
            oc = row.get(COL_OC_ME5A, row.get(COL_OC_NME, ""))
            pos = row.get(COL_POS_SOLPED, "")
            texto = row.get(COL_TEXTO, "")
            opciones_detalle.append((idx, f"SolPed {solped} | OC {oc} | Pos {pos} | {texto}"))

        labels = [x[1] for x in opciones_detalle]
        seleccionado = st.selectbox("Registro", labels)
        idx_sel = opciones_detalle[labels.index(seleccionado)][0]

        registro = df_filtrado.loc[[idx_sel]].T.reset_index()
        registro.columns = ["Campo", "Valor"]
        st.dataframe(registro, use_container_width=True, hide_index=True)


# =========================================================
# Descargas
# =========================================================
st.subheader("Descarga del resultado filtrado")

csv_bytes = df_filtrado.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")

c1, c2, c3 = st.columns(3)
with c1:
    st.download_button(
        "Descargar CSV filtrado",
        data=csv_bytes,
        file_name="resultado_filtrado_solped_oc.csv",
        mime="text/csv",
        use_container_width=True,
    )

with c2:
    try:
        parquet_bytes = dataframe_a_parquet(df_filtrado)
        st.download_button(
            "Descargar Parquet filtrado",
            data=parquet_bytes,
            file_name="resultado_filtrado_solped_oc.parquet",
            mime="application/octet-stream",
            use_container_width=True,
        )
    except Exception:
        st.button("Parquet no disponible", disabled=True, use_container_width=True)

with c3:
    if len(df_filtrado) <= 250_000:
        excel_bytes = dataframe_a_excel(df_filtrado)
        st.download_button(
            "Descargar Excel filtrado",
            data=excel_bytes,
            file_name="resultado_filtrado_solped_oc.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    else:
        st.button("Excel no disponible", disabled=True, use_container_width=True)
        st.caption("Excel se desactiva sobre 250.000 filas.")


# =========================================================
# Información técnica
# =========================================================
with st.expander("Columnas disponibles en el archivo", expanded=False):
    st.write(df.columns.tolist())
