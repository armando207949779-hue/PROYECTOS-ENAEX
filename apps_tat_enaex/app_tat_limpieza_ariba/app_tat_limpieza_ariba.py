import pandas as pd
import streamlit as st
from io import BytesIO

st.set_page_config(
    page_title="Filtro Tipo de Compra - CEN1",
    layout="wide"
)

st.title("Filtro de compras CEN1")
st.write(
    "Sube el archivo Excel, la app leerá la hoja **Data** desde **B14**, "
    "filtrará los registros válidos y agregará la columna **FLAG**."
)

archivo = st.file_uploader(
    "Sube el archivo Excel",
    type=["xlsx", "xls"]
)

if archivo is not None:
    try:
        with st.spinner("Leyendo archivo..."):
            df = pd.read_excel(
                archivo,
                sheet_name="Data",
                header=13
            )

            # Empezar desde columna B
            df = df.iloc[:, 1:].copy()

        st.subheader("Vista inicial del archivo")
        st.write("Dimensiones iniciales:", df.shape)
        st.dataframe(df.head(50), use_container_width=True)

        columnas_requeridas = [
            "Tipo de Compra",
            "ID de unidad de negocio"
        ]

        faltantes = [col for col in columnas_requeridas if col not in df.columns]

        if faltantes:
            st.error(f"Faltan columnas requeridas: {faltantes}")
            st.write("Columnas encontradas:")
            st.write(list(df.columns))
        else:
            with st.spinner("Aplicando filtros..."):

                # Excluir nulos en Tipo de Compra
                df_filtrado = df[df["Tipo de Compra"].notna()].copy()

                # Dejar solo CEN1
                df_filtrado = df_filtrado[
                    df_filtrado["ID de unidad de negocio"].astype(str).str.strip() == "CEN1"
                ].copy()

                # Mapeo Tipo de Compra
                mapa_tipo_compra = {
                    1: "CATALOGADA",
                    2: "NO CATALOGADA",
                    3: "COMPRA DIRECTA"
                }

                df_filtrado["Tipo de Compra"] = df_filtrado["Tipo de Compra"].astype(int)
                df_filtrado["FLAG"] = df_filtrado["Tipo de Compra"].map(mapa_tipo_compra)

            st.success("Proceso completado")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Filas originales", f"{len(df):,}")

            with col2:
                st.metric("Filas filtradas", f"{len(df_filtrado):,}")

            with col3:
                st.metric(
                    "Nulos excluidos en Tipo de Compra",
                    f"{df['Tipo de Compra'].isna().sum():,}"
                )

            st.subheader("Conteo por FLAG")
            conteo_flag = (
                df_filtrado["FLAG"]
                .value_counts(dropna=False)
                .reset_index()
            )
            conteo_flag.columns = ["FLAG", "Cantidad"]
            st.dataframe(conteo_flag, use_container_width=True)

            st.subheader("Valores únicos revisados")

            col_a, col_b = st.columns(2)

            with col_a:
                st.write("**Tipo de Compra**")
                st.write(df_filtrado["Tipo de Compra"].dropna().unique())

            with col_b:
                st.write("**ID de unidad de negocio**")
                st.write(df_filtrado["ID de unidad de negocio"].dropna().unique())

            st.subheader("Datos filtrados")
            st.dataframe(df_filtrado.head(1000), use_container_width=True)

            # Descargar resultado en Excel
            output = BytesIO()

            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_filtrado.to_excel(writer, index=False, sheet_name="Filtrado_CEN1")
                conteo_flag.to_excel(writer, index=False, sheet_name="Conteo_FLAG")

            output.seek(0)

            st.download_button(
                label="Descargar resultado en Excel",
                data=output,
                file_name="resultado_filtrado_CEN1.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    except Exception as e:
        st.error("Ocurrió un error procesando el archivo.")
        st.exception(e)

else:
    st.info("Sube un archivo Excel para comenzar.")