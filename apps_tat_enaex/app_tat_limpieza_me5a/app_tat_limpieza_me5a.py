# =========================================================
# Métricas superiores + descarga rápida por defecto
# =========================================================

col1, col2, col3, col4 = st.columns(4)

col1.metric("Filas originales", f"{len(df_original):,}")
col2.metric("Columnas originales", f"{df_original.shape[1]:,}")
col3.metric("Filas limpias", f"{len(df_limpio):,}")
col4.metric("Columnas limpias", f"{df_limpio.shape[1]:,}")

st.divider()

# =========================================================
# Descarga rápida siempre visible
# =========================================================

st.markdown("### Descarga rápida")

with st.spinner("Preparando archivos de salida..."):

    parquet_bytes = convertir_a_parquet(df_limpio)

    csv_bytes = convertir_a_csv(df_limpio)

    excel_bytes = convertir_a_excel(
        df_limpio=df_limpio,
        diagnostico_columnas=diagnostico_columnas,
        resumen_fechas=resumen_fechas,
        resumen_num=resumen_num
    )

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.download_button(
        label="Descargar Parquet",
        data=parquet_bytes,
        file_name="me5a_limpio.parquet",
        mime="application/octet-stream",
        use_container_width=True
    )

with col_d2:
    st.download_button(
        label="Descargar Excel",
        data=excel_bytes,
        file_name="me5a_limpio.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_d3:
    st.download_button(
        label="Descargar CSV",
        data=csv_bytes,
        file_name="me5a_limpio.csv",
        mime="text/csv",
        use_container_width=True
    )

st.caption(
    "Parquet se deja como formato principal recomendado para conservar tipos de datos y trabajar con Python."
)

st.divider()
