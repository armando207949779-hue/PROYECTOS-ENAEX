import pandas as pd
import numpy as np
import streamlit as st
from difflib import SequenceMatcher
from io import BytesIO

# =========================================================
# CONFIGURACIÓN APP
# =========================================================
st.set_page_config(
    page_title="Match ME5A vs Ariba",
    layout="wide"
)

st.title("Match ME5A vs Ariba")
st.write("Carga los archivos, aplica el algoritmo de coincidencia y descarga los resultados.")

# =========================================================
# FUNCIONES AUXILIARES
# =========================================================
def limpiar_id(valor):
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    try:
        if "e+" in texto.lower() or "e-" in texto.lower():
            texto = str(int(float(texto)))
    except Exception:
        pass

    if texto.endswith(".0"):
        texto = texto[:-2]

    return texto


def limpiar_texto(valor):
    if pd.isna(valor):
        return ""

    texto = str(valor).upper().strip()
    texto = " ".join(texto.split())
    return texto


def similitud_texto(a, b):
    a = limpiar_texto(a)
    b = limpiar_texto(b)

    if a == "" or b == "":
        return 0

    return SequenceMatcher(None, a, b).ratio()


def texto_contenido(a, b):
    a = limpiar_texto(a)
    b = limpiar_texto(b)

    if a == "" or b == "":
        return False

    return a in b or b in a


def leer_archivo(archivo):
    nombre = archivo.name.lower()

    if nombre.endswith(".xlsx") or nombre.endswith(".xls"):
        return pd.read_excel(archivo)

    if nombre.endswith(".csv"):
        try:
            return pd.read_csv(archivo)
        except UnicodeDecodeError:
            archivo.seek(0)
            return pd.read_csv(archivo, encoding="latin1")

    raise ValueError("Formato no soportado. Usa .xlsx, .xls o .csv")


def dataframe_a_excel_bytes(df):
    salida = BytesIO()
    with pd.ExcelWriter(salida, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="resultado")
    salida.seek(0)
    return salida


def aplicar_algoritmo(me5a, ariba_final, umbral_similitud=0.70):
    # =========================
    # COPIAS BASE
    # =========================
    me5a_base = me5a.copy()
    ariba_base = ariba_final.copy()

    # ID interno para mantener una fila por cada registro original de ME5A
    me5a_base["me5a_id_fila_original"] = me5a_base.index

    # =========================
    # LIMPIEZA ME5A
    # =========================
    me5a_base["Solicitud de pedido limpia"] = me5a_base["Solicitud de pedido"].apply(limpiar_id)
    me5a_base["Pedido limpio"] = me5a_base["Pedido"].apply(limpiar_id)
    me5a_base["Texto breve limpio"] = me5a_base["Texto breve"].apply(limpiar_texto)

    me5a_base["Linea Ariba esperada"] = pd.to_numeric(
        me5a_base["Pos.solicitud pedido"],
        errors="coerce"
    ) / 10

    # =========================
    # LIMPIEZA ARIBA
    # =========================
    ariba_base["ID ERP limpio"] = ariba_base["ID de solicitud de compra del ERP"].apply(limpiar_id)
    ariba_base["ID pedido limpio"] = ariba_base["ID de pedido"].apply(limpiar_id)
    ariba_base["Descripcion limpia"] = ariba_base["Descripción"].apply(limpiar_texto)

    ariba_base["Linea Ariba"] = pd.to_numeric(
        ariba_base["Número de línea de la solicitud de compra"],
        errors="coerce"
    )

    # =========================
    # PREFIJOS
    # =========================
    me5a_pref = me5a_base.add_prefix("me5a_")
    ariba_pref = ariba_base.add_prefix("ariba_")

    # =========================
    # MERGE PRINCIPAL
    # =========================
    df_unido = me5a_pref.merge(
        ariba_pref,
        how="left",
        left_on="me5a_Solicitud de pedido limpia",
        right_on="ariba_ID ERP limpio"
    )

    # =========================
    # VALIDACIONES
    # =========================
    df_unido["match_solicitud"] = (
        df_unido["me5a_Solicitud de pedido limpia"] == df_unido["ariba_ID ERP limpio"]
    )

    df_unido["match_linea"] = (
        df_unido["me5a_Linea Ariba esperada"] == df_unido["ariba_Linea Ariba"]
    )

    df_unido["match_pedido"] = (
        df_unido["me5a_Pedido limpio"] == df_unido["ariba_ID pedido limpio"]
    )

    df_unido["match_descripcion_exacta"] = (
        df_unido["me5a_Texto breve limpio"] == df_unido["ariba_Descripcion limpia"]
    )

    df_unido["match_descripcion_parcial"] = df_unido.apply(
        lambda row: texto_contenido(
            row["me5a_Texto breve limpio"],
            row["ariba_Descripcion limpia"]
        ),
        axis=1
    )

    df_unido["similitud_descripcion"] = df_unido.apply(
        lambda row: similitud_texto(
            row["me5a_Texto breve limpio"],
            row["ariba_Descripcion limpia"]
        ),
        axis=1
    )

    df_unido["match_descripcion_similar"] = (
        df_unido["similitud_descripcion"] >= umbral_similitud
    )

    # =========================
    # SCORE
    # =========================
    df_unido["score_match"] = (
        df_unido["match_solicitud"].fillna(False).astype(int) * 4 +
        df_unido["match_linea"].fillna(False).astype(int) * 4 +
        df_unido["match_pedido"].fillna(False).astype(int) * 3 +
        df_unido["match_descripcion_exacta"].fillna(False).astype(int) * 3 +
        df_unido["match_descripcion_parcial"].fillna(False).astype(int) * 2 +
        df_unido["match_descripcion_similar"].fillna(False).astype(int) * 1
    )

    # =========================
    # TIPO DE MATCH
    # =========================
    df_unido["tipo_match"] = np.select(
        [
            df_unido["match_solicitud"] &
            df_unido["match_linea"] &
            df_unido["match_pedido"] &
            (
                df_unido["match_descripcion_exacta"] |
                df_unido["match_descripcion_parcial"] |
                df_unido["match_descripcion_similar"]
            ),

            df_unido["match_solicitud"] &
            df_unido["match_linea"] &
            df_unido["match_pedido"],

            df_unido["match_solicitud"] &
            df_unido["match_linea"],

            df_unido["match_solicitud"],
        ],
        [
            "MATCH FUERTE: solicitud + línea + pedido + descripción",
            "MATCH BUENO: solicitud + línea + pedido",
            "MATCH MEDIO: solicitud + línea",
            "MATCH DÉBIL: solo solicitud",
        ],
        default="SIN MATCH ARIBA"
    )

    # =========================
    # ORDENAMIENTO
    # =========================
    df_unido = df_unido.sort_values(
        by=[
            "me5a_me5a_id_fila_original",
            "score_match",
            "match_linea",
            "match_pedido",
            "match_descripcion_exacta",
            "match_descripcion_parcial",
            "similitud_descripcion"
        ],
        ascending=[True, False, False, False, False, False, False]
    ).reset_index(drop=True)

    df_todas_las_coincidencias = df_unido.copy()

    df_mejor_match = (
        df_unido
        .drop_duplicates(subset=["me5a_me5a_id_fila_original"], keep="first")
        .reset_index(drop=True)
    )

    return df_todas_las_coincidencias, df_mejor_match


# =========================================================
# CARGA DE ARCHIVOS
# =========================================================
st.sidebar.header("Carga de archivos")

archivo_me5a = st.sidebar.file_uploader(
    "Carga archivo ME5A",
    type=["xlsx", "xls", "csv"]
)

archivo_ariba = st.sidebar.file_uploader(
    "Carga archivo ARIBA_FINAL",
    type=["xlsx", "xls", "csv"]
)

umbral = st.sidebar.slider(
    "Umbral similitud descripción",
    min_value=0.50,
    max_value=1.00,
    value=0.70,
    step=0.01
)

procesar = st.sidebar.button("Procesar match")

# =========================================================
# VALIDACIÓN Y PROCESAMIENTO
# =========================================================
if archivo_me5a is None or archivo_ariba is None:
    st.info("Carga ambos archivos para comenzar.")

else:
    try:
        me5a = leer_archivo(archivo_me5a)
        ariba_final = leer_archivo(archivo_ariba)

        st.subheader("Vista previa de archivos cargados")

        col1, col2 = st.columns(2)

        with col1:
            st.write("ME5A")
            st.write(f"Filas: {len(me5a)} | Columnas: {len(me5a.columns)}")
            st.dataframe(me5a.head(10), use_container_width=True)

        with col2:
            st.write("ARIBA_FINAL")
            st.write(f"Filas: {len(ariba_final)} | Columnas: {len(ariba_final.columns)}")
            st.dataframe(ariba_final.head(10), use_container_width=True)

        columnas_requeridas_me5a = [
            "Solicitud de pedido",
            "Pedido",
            "Texto breve",
            "Pos.solicitud pedido"
        ]

        columnas_requeridas_ariba = [
            "ID de solicitud de compra del ERP",
            "ID de pedido",
            "Descripción",
            "Número de línea de la solicitud de compra"
        ]

        faltantes_me5a = [c for c in columnas_requeridas_me5a if c not in me5a.columns]
        faltantes_ariba = [c for c in columnas_requeridas_ariba if c not in ariba_final.columns]

        if faltantes_me5a:
            st.error(f"Faltan columnas en ME5A: {faltantes_me5a}")

        if faltantes_ariba:
            st.error(f"Faltan columnas en ARIBA_FINAL: {faltantes_ariba}")

        if procesar and not faltantes_me5a and not faltantes_ariba:
            with st.spinner("Procesando coincidencias..."):
                df_todas, df_mejor = aplicar_algoritmo(
                    me5a,
                    ariba_final,
                    umbral_similitud=umbral
                )

            st.success("Proceso terminado.")

            # =========================================================
            # MÉTRICAS
            # =========================================================
            st.subheader("Resumen")

            total_me5a = len(me5a)
            total_ariba = len(ariba_final)
            total_todas = len(df_todas)
            total_mejor = len(df_mejor)
            con_match = (df_mejor["tipo_match"] != "SIN MATCH ARIBA").sum()
            sin_match = (df_mejor["tipo_match"] == "SIN MATCH ARIBA").sum()

            m1, m2, m3, m4, m5 = st.columns(5)

            m1.metric("Filas ME5A", total_me5a)
            m2.metric("Filas ARIBA", total_ariba)
            m3.metric("Todas coincidencias", total_todas)
            m4.metric("Con match", con_match)
            m5.metric("Sin match", sin_match)

            # =========================================================
            # RESUMEN TIPO MATCH
            # =========================================================
            st.subheader("Resumen por tipo de match")

            resumen = (
                df_mejor["tipo_match"]
                .value_counts(dropna=False)
                .reset_index()
            )
            resumen.columns = ["tipo_match", "cantidad"]

            st.dataframe(resumen, use_container_width=True)

            # =========================================================
            # RESULTADOS
            # =========================================================
            st.subheader("Mejor match por registro ME5A")
            st.dataframe(df_mejor, use_container_width=True)

            with st.expander("Ver todas las coincidencias posibles"):
                st.dataframe(df_todas, use_container_width=True)

            # =========================================================
            # DESCARGAS
            # =========================================================
            st.subheader("Descargar resultados")

            excel_mejor = dataframe_a_excel_bytes(df_mejor)
            excel_todas = dataframe_a_excel_bytes(df_todas)

            col_desc1, col_desc2 = st.columns(2)

            with col_desc1:
                st.download_button(
                    label="Descargar mejor match",
                    data=excel_mejor,
                    file_name="me5a_ariba_mejor_match.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            with col_desc2:
                st.download_button(
                    label="Descargar todas las coincidencias",
                    data=excel_todas,
                    file_name="me5a_ariba_todas_las_coincidencias.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error("Ocurrió un error al procesar los archivos.")
        st.exception(e)