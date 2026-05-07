import io
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
from pandas.api.types import is_datetime64_any_dtype


# =========================
# Ruta del logo ENAEX
# =========================

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
LOGO_PATH = ROOT_DIR / "assets" / "logo.svg"


# =========================
# Configuración Streamlit
# =========================

st.set_page_config(
    page_title="Limpieza Transacción N°3 NME80FN",
    page_icon="📊",
    layout="wide"
)


# =========================
# Encabezado con logo ENAEX centrado
# =========================

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
    st.error(f"Logo no encontrado en ruta correcta: {LOGO_PATH}")


# =========================================================
# Funciones base
# =========================================================

def obtener_separador(separador_csv: str):
    if separador_csv == "Automático":
        return None
    if separador_csv == "Punto y coma (;)":
        return ";"
    if separador_csv == "Coma (,)":
        return ","
    if separador_csv == "Tabulación":
        return "\t"
    return None


def validar_columnas_requeridas(df: pd.DataFrame):
    columnas_requeridas = [
        "Documento compras",
        "Posición",
        "Fecha de documento",
        "Fecha contabiliz.",
        "Clase de operación"
    ]

    faltantes = [
        col for col in columnas_requeridas
        if col not in df.columns
    ]

    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")


def leer_archivo(uploaded_file, separador_csv: str) -> pd.DataFrame:
    nombre = uploaded_file.name.lower()

    if nombre.endswith(".parquet"):
        return pd.read_parquet(uploaded_file)

    if nombre.endswith(".xlsx"):
        return pd.read_excel(uploaded_file)

    if nombre.endswith(".csv"):
        sep = obtener_separador(separador_csv)

        try:
            return pd.read_csv(
                uploaded_file,
                sep=sep,
                engine="python",
                encoding="utf-8-sig",
                on_bad_lines="skip"
            )
        except Exception:
            uploaded_file.seek(0)
            return pd.read_csv(
                uploaded_file,
                sep=sep,
                engine="python",
                encoding="latin1",
                on_bad_lines="skip"
            )

    raise ValueError("Formato no soportado. Usa .parquet, .xlsx o .csv")


def limpiar_nme80fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(axis=1, how="all")

    columnas_unnamed = [
        col for col in df.columns
        if str(col).startswith("Unnamed")
    ]

    for col in columnas_unnamed:
        if df[col].isna().all():
            df = df.drop(columns=[col])

    validar_columnas_requeridas(df)

    columnas_fecha = [
        "Fecha de entrada",
        "Fecha de documento",
        "Fecha contabiliz."
    ]

    for col in columnas_fecha:
        if col in df.columns:
            df[col] = pd.to_datetime(
                df[col],
                errors="coerce"
            )

    df["Clase de operación"] = pd.to_numeric(
        df["Clase de operación"],
        errors="coerce"
    )

    columnas_numericas = [
        "Documento compras",
        "Posición",
        "Cantidad",
        "Impte.mon.local",
        "Importe"
    ]

    for col in columnas_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    if "Material" in df.columns:
        df["Material"] = (
            df["Material"]
            .astype("string")
            .str.strip()
            .str.replace(r"\.0$", "", regex=True)
        )

    cols_texto = df.select_dtypes(include=["object", "string"]).columns

    for col in cols_texto:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
        )
        df[col] = df[col].replace("", pd.NA)

    return df


def aplicar_logica_fechas_nme80fn(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    validar_columnas_requeridas(df)

    hoy = pd.Timestamp.today().normalize()
    keys = ["Documento compras", "Posición"]

    final_df = (
        df
        .sort_index()
        .drop_duplicates(
            subset=keys,
            keep="first"
        )
        .copy()
    )

    df_clase_2 = df[
        df["Clase de operación"].eq(2)
    ].copy()

    if not df_clase_2.empty:
        df_doc = df_clase_2.dropna(
            subset=["Fecha de documento"]
        ).copy()

        if not df_doc.empty:
            df_doc["_dist_fecha_documento"] = (
                df_doc["Fecha de documento"] - hoy
            ).abs()

            idx_doc = (
                df_doc
                .groupby(keys)["_dist_fecha_documento"]
                .idxmin()
            )

            fechas_documento = (
                df_doc
                .loc[idx_doc, keys + ["Fecha de documento"]]
                .rename(columns={
                    "Fecha de documento": "fecha_facturacion_proveedor"
                })
            )
        else:
            fechas_documento = pd.DataFrame(
                columns=keys + ["fecha_facturacion_proveedor"]
            )

        df_cont = df_clase_2.dropna(
            subset=["Fecha contabiliz."]
        ).copy()

        if not df_cont.empty:
            df_cont["_dist_fecha_contabiliz"] = (
                df_cont["Fecha contabiliz."] - hoy
            ).abs()

            idx_cont = (
                df_cont
                .groupby(keys)["_dist_fecha_contabiliz"]
                .idxmin()
            )

            fechas_contabiliz = (
                df_cont
                .loc[idx_cont, keys + ["Fecha contabiliz."]]
                .rename(columns={
                    "Fecha contabiliz.": "fecha_entrada_mercancia_recepcion"
                })
            )
        else:
            fechas_contabiliz = pd.DataFrame(
                columns=keys + ["fecha_entrada_mercancia_recepcion"]
            )
    else:
        fechas_documento = pd.DataFrame(
            columns=keys + ["fecha_facturacion_proveedor"]
        )
        fechas_contabiliz = pd.DataFrame(
            columns=keys + ["fecha_entrada_mercancia_recepcion"]
        )

    final_df = final_df.merge(
        fechas_documento,
        on=keys,
        how="left"
    )

    final_df = final_df.merge(
        fechas_contabiliz,
        on=keys,
        how="left"
    )

    return final_df


# =========================================================
# Diagnóstico liviano
# =========================================================

def diagnostico_general_liviano(df: pd.DataFrame) -> dict:
    total_filas = len(df)
    total_columnas = len(df.columns)
    total_celdas = total_filas * total_columnas

    total_nulos = int(df.isna().sum().sum())

    porcentaje_nulos = (
        round(total_nulos / total_celdas * 100, 2)
        if total_celdas > 0
        else 0
    )

    return {
        "total_filas": total_filas,
        "total_columnas": total_columnas,
        "total_nulos": total_nulos,
        "porcentaje_nulos": porcentaje_nulos
    }


def tabla_diagnostico_columnas_liviana(df: pd.DataFrame) -> pd.DataFrame:
    total_filas = len(df)

    diag = pd.DataFrame({
        "Columna": df.columns,
        "Tipo de dato": [str(dtype) for dtype in df.dtypes],
        "No nulos": df.notna().sum().values,
        "Nulos": df.isna().sum().values,
    })

    if total_filas > 0:
        diag["% Nulos"] = (
            diag["Nulos"] / total_filas * 100
        ).round(2)
    else:
        diag["% Nulos"] = 0

    return diag.sort_values(
        "% Nulos",
        ascending=False
    ).reset_index(drop=True)


def columnas_fecha(df: pd.DataFrame) -> list:
    return [
        col for col in df.columns
        if is_datetime64_any_dtype(df[col])
    ]


# =========================================================
# Exportación segura
# =========================================================

def convertir_a_csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(
        index=False,
        encoding="utf-8-sig"
    ).encode("utf-8-sig")


def convertir_a_parquet(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    df.to_parquet(
        output,
        index=False,
        engine="pyarrow"
    )

    return output.getvalue()


def convertir_a_excel_seguro(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="NME80FN_Final"
        )

    return output.getvalue()


# =========================================================
# Interfaz Streamlit
# =========================================================

st.markdown(
    """
    <h1 style='text-align: center;'>
        Limpieza Transacción N°3 NME80FN
    </h1>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <p style='text-align: center; font-size: 18px;'>
        Sube un archivo Parquet, Excel o CSV de <b>NME80FN</b>.
        La app agrupa por <b>Documento compras</b> y <b>Posición</b>,
        conserva una fila base y crea las columnas
        <b>fecha_facturacion_proveedor</b> y
        <b>fecha_entrada_mercancia_recepcion</b>.
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()


with st.sidebar:
    pagina = st.radio(
        "Menú",
        options=[
            "Limpieza",
            "Diagnóstico"
        ],
        index=0
    )

    st.divider()

    separador_csv = st.selectbox(
        "Separador CSV",
        options=[
            "Automático",
            "Punto y coma (;)",
            "Coma (,)",
            "Tabulación"
        ],
        index=0
    )

    st.caption(
        "Esta opción solo aplica para archivos CSV."
    )


uploaded_file = st.file_uploader(
    "Selecciona archivo NME80FN",
    type=["parquet", "xlsx", "csv"]
)


if uploaded_file is not None:
    try:
        with st.spinner("Leyendo archivo..."):
            df_original = leer_archivo(
                uploaded_file,
                separador_csv
            )

        with st.spinner("Limpiando archivo..."):
            df_limpio = limpiar_nme80fn(df_original)

        with st.spinner("Aplicando lógica de fechas..."):
            df_final = aplicar_logica_fechas_nme80fn(df_limpio)

        if pagina == "Limpieza":
            st.success("Archivo procesado correctamente.")

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Filas originales",
                f"{len(df_original):,}"
            )

            col2.metric(
                "Filas limpias",
                f"{len(df_limpio):,}"
            )

            col3.metric(
                "Filas finales",
                f"{len(df_final):,}"
            )

            col4.metric(
                "Filas agrupadas",
                f"{len(df_limpio) - len(df_final):,}"
            )

            st.subheader("Vista previa original")
            st.dataframe(
                df_original.head(30),
                use_container_width=True
            )

            st.subheader("Vista previa final con columnas nuevas")

            columnas_preferidas = [
                "Documento compras",
                "Posición",
                "Centro",
                "Fecha de entrada",
                "Material",
                "Texto breve",
                "Cantidad",
                "Unidad medida pedido",
                "Impte.mon.local",
                "Moneda",
                "Importe",
                "Clase de operación",
                "Fecha de documento",
                "Fecha contabiliz.",
                "fecha_facturacion_proveedor",
                "fecha_entrada_mercancia_recepcion"
            ]

            columnas_preferidas = [
                col for col in columnas_preferidas
                if col in df_final.columns
            ]

            st.dataframe(
                df_final[columnas_preferidas].head(100),
                use_container_width=True
            )

            st.divider()

            st.subheader("Descargar resultado final")

            formato_descarga = st.radio(
                "Formato de descarga",
                options=[
                    "Parquet",
                    "CSV",
                    "Excel"
                ],
                horizontal=True
            )

            if formato_descarga == "Parquet":
                parquet_bytes = convertir_a_parquet(df_final)

                st.download_button(
                    label="Descargar como Parquet",
                    data=parquet_bytes,
                    file_name="resultado_limpieza_transaccion_3_nme80fn.parquet",
                    mime="application/octet-stream"
                )

            elif formato_descarga == "CSV":
                csv_bytes = convertir_a_csv(df_final)

                st.download_button(
                    label="Descargar como CSV",
                    data=csv_bytes,
                    file_name="resultado_limpieza_transaccion_3_nme80fn.csv",
                    mime="text/csv"
                )

            elif formato_descarga == "Excel":
                limite_excel = 250_000

                if len(df_final) > limite_excel:
                    st.warning(
                        f"El resultado tiene {len(df_final):,} filas. "
                        f"Para evitar que Streamlit se caiga, Excel está limitado a "
                        f"{limite_excel:,} filas. Usa Parquet o CSV."
                    )
                else:
                    excel_bytes = convertir_a_excel_seguro(df_final)

                    st.download_button(
                        label="Descargar como Excel",
                        data=excel_bytes,
                        file_name="resultado_limpieza_transaccion_3_nme80fn.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        elif pagina == "Diagnóstico":
            st.subheader("Diagnóstico general")

            diag_general = diagnostico_general_liviano(df_final)
            diag_columnas = tabla_diagnostico_columnas_liviana(df_final)

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Filas",
                f"{diag_general['total_filas']:,}"
            )

            col2.metric(
                "Columnas",
                f"{diag_general['total_columnas']:,}"
            )

            col3.metric(
                "Celdas nulas",
                f"{diag_general['total_nulos']:,}"
            )

            col4.metric(
                "% nulos total",
                f"{diag_general['porcentaje_nulos']}%"
            )

            st.subheader("Detalle de columnas")
            st.dataframe(
                diag_columnas,
                use_container_width=True
            )

            st.subheader("Porcentaje de nulos por columna")
            data_nulos = (
                diag_columnas
                .set_index("Columna")["% Nulos"]
                .sort_values(ascending=False)
            )

            st.bar_chart(data_nulos)

            st.subheader("Columnas de fecha detectadas")
            fechas = columnas_fecha(df_final)

            if fechas:
                st.write(fechas)
            else:
                st.info("No se encontraron columnas de fecha.")

    except Exception as e:
        st.error("Ocurrió un error al procesar el archivo.")
        st.exception(e)

else:
    st.warning("Carga un archivo para comenzar.")
