# =========================================================
# APP
# Estructura actualizada:
# logo -> leer df global -> procesamiento -> dashboard
# =========================================================

aplicar_css()

# ---------------------------------------------------------
# 1) Logo y encabezado
# ---------------------------------------------------------
mostrar_logo(220)

st.markdown(
    """
    <div style="text-align:center; margin-bottom: 22px;">
        <div style="font-size:42px; font-weight:850; color:#1F2937; line-height:1.12;">
            Performance TAT - Match Integrado
        </div>
        <div style="font-size:14px; color:#6B7280; margin-top:10px;">
            ME5A · ARIBA · NME80FN · Fechas finales
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 2) Configuración lateral
# ---------------------------------------------------------
with st.sidebar:
    st.header("Configuración")

    limite_vista = st.number_input(
        "Filas en vista previa",
        min_value=50,
        max_value=5000,
        value=300,
        step=50,
    )

    ordenar_performance_final = st.checkbox(
        "Mover columnas de performance al final",
        value=True,
    )

    mostrar_resumen_logica = st.checkbox(
        "Mostrar lógica de cálculo al iniciar",
        value=False,
    )

# ---------------------------------------------------------
# 3) Leer dataframe global cargado previamente
# ---------------------------------------------------------
st.subheader("Archivo")

if "df_tat" not in st.session_state:
    st.warning("Primero debes cargar el archivo base en Análisis TAT > Cargar archivo.")
    st.stop()

df_original = st.session_state["df_tat"].copy()
nombre_archivo = st.session_state.get("nombre_archivo_tat", "Archivo cargado")

st.success(f"Archivo activo: {nombre_archivo}")

# ---------------------------------------------------------
# 4) Procesar dataframe global
# ---------------------------------------------------------
try:
    columnas_originales = list(df_original.columns)

    with st.spinner("Aplicando lógica de performance..."):
        df_final = aplicar_logica_performance(df_original)

        columnas_nuevas = [
            col for col in df_final.columns
            if col not in columnas_originales
        ]

        if ordenar_performance_final:
            df_final = reordenar_columnas_performance_al_final(df_final)

        resumen_perf = resumen_performance(df_final)
        resumen_cols = resumen_columnas_nuevas(df_final)
        tabla_formulas = tabla_inputs_formulas()
        parquet_bytes = convertir_a_parquet_cache(df_final)

    st.success("Performance TAT calculada correctamente.")

    # -----------------------------------------------------
    # 5) Filtros del dashboard
    # -----------------------------------------------------
    st.subheader("Filtros del dashboard")

    df_dashboard = df_final.copy()

    col_centro = None
    for candidato in ["Centro", "Centro - ME5A", "Centro - NME80FN"]:
        if candidato in df_dashboard.columns:
            col_centro = candidato
            break

    fechas_validas = df_dashboard[COL_FECHA_RECEPCION_FINAL].dropna()
    fecha_min = fechas_validas.min().date() if not fechas_validas.empty else None
    fecha_max = fechas_validas.max().date() if not fechas_validas.empty else None

    f1, f2, f3, f4 = st.columns(4)

    with f1:
        if fecha_min is not None and fecha_max is not None:
            rango_fechas = st.date_input(
                "Fecha recepción",
                value=(fecha_min, fecha_max),
                min_value=fecha_min,
                max_value=fecha_max,
            )
        else:
            rango_fechas = None
            st.warning("No hay fechas válidas de recepción.")

    with f2:
        if "sistema" in df_dashboard.columns:
            sistemas = sorted(
                df_dashboard["sistema"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            sistemas_sel = st.multiselect(
                "Sistema",
                sistemas,
                default=sistemas,
            )
        else:
            sistemas_sel = []
            st.info("Sin columna sistema")

    with f3:
        if col_centro is not None:
            centros = sorted(
                df_dashboard[col_centro]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

            default_centros = ["E002"] if "E002" in centros else centros

            centros_sel = st.multiselect(
                "Centro",
                centros,
                default=default_centros,
            )
        else:
            centros_sel = []
            st.info("Sin columna centro")

    with f4:
        perf_options = [
            "Cumple",
            "No cumple",
            "En proceso",
            "No aplica al análisis",
            "Sin datos",
        ]

        if "performance_tat_total" in df_dashboard.columns:
            perf_existentes = [
                x for x in perf_options
                if x in df_dashboard["performance_tat_total"].astype(str).unique()
            ]
        else:
            perf_existentes = []

        perf_sel = st.multiselect(
            "Performance TAT",
            perf_existentes,
            default=[
                x for x in ["Cumple", "No cumple"]
                if x in perf_existentes
            ],
        )

    # -----------------------------------------------------
    # Aplicar filtros
    # -----------------------------------------------------
    if rango_fechas is not None:
        if isinstance(rango_fechas, (tuple, list)) and len(rango_fechas) == 2:
            fecha_inicio = pd.Timestamp(rango_fechas[0])
            fecha_fin = (
                pd.Timestamp(rango_fechas[1])
                + pd.Timedelta(days=1)
                - pd.Timedelta(microseconds=1)
            )

            df_dashboard = df_dashboard[
                df_dashboard[COL_FECHA_RECEPCION_FINAL].notna()
                & df_dashboard[COL_FECHA_RECEPCION_FINAL].between(
                    fecha_inicio,
                    fecha_fin,
                )
            ].copy()

    if "sistema" in df_dashboard.columns and sistemas_sel:
        df_dashboard = df_dashboard[
            df_dashboard["sistema"].astype(str).isin(sistemas_sel)
        ].copy()

    if col_centro is not None and centros_sel:
        df_dashboard = df_dashboard[
            df_dashboard[col_centro]
            .astype(str)
            .str.strip()
            .isin([str(x).strip() for x in centros_sel])
        ].copy()

    if "performance_tat_total" in df_dashboard.columns and perf_sel:
        df_dashboard = df_dashboard[
            df_dashboard["performance_tat_total"]
            .astype(str)
            .isin(perf_sel)
        ].copy()

    # -----------------------------------------------------
    # 6) Tabs principales
    # -----------------------------------------------------
    tab_dashboard, tab_auditoria, tab_datos, tab_descarga = st.tabs(
        [
            "Dashboard",
            "Auditoría",
            "Datos",
            "Descarga",
        ]
    )

    with tab_dashboard:
        st.subheader("Indicadores generales")

        total_filas = len(df_dashboard)

        cumple_tat = (
            int(df_dashboard["performance_tat_total"].eq("Cumple").sum())
            if "performance_tat_total" in df_dashboard.columns
            else 0
        )

        no_cumple_tat = (
            int(df_dashboard["performance_tat_total"].eq("No cumple").sum())
            if "performance_tat_total" in df_dashboard.columns
            else 0
        )

        evaluables_tat = cumple_tat + no_cumple_tat
        pct_cumple_tat = cumple_tat / evaluables_tat * 100 if evaluables_tat else 0

        incumplimientos_tat = (
            int(df_dashboard["incumplimiento_tat"].eq(True).sum())
            if "incumplimiento_tat" in df_dashboard.columns
            else 0
        )

        k1, k2, k3, k4, k5 = st.columns(5)

        with k1:
            card_metric("Filas filtradas", f"{total_filas:,}")

        with k2:
            card_metric("TAT evaluable", f"{evaluables_tat:,}")

        with k3:
            card_metric("Cumple TAT", f"{cumple_tat:,}", f"{pct_cumple_tat:.1f}%")

        with k4:
            card_metric("No cumple TAT", f"{no_cumple_tat:,}")

        with k5:
            card_metric("Incumplimiento TAT", f"{incumplimientos_tat:,}")

        st.divider()

        st.subheader("Performance TAT mensual")
        tabla_mensual = crear_resumen_mensual(df_dashboard)
        grafico_mensual_100(tabla_mensual)

        st.divider()

        st.subheader("Cumplimiento por etapa")

        st.caption(
            "Las donas replican la lógica solicitada: se consideran solo estados "
            "Cumple / No Cumple de cada etapa, y el promedio usa únicamente días positivos, Dx > 0."
        )

        resumen_etapas = []
        cols_etapas = st.columns(4)

        for i, etapa in enumerate(ETAPAS_DASHBOARD):
            datos = datos_etapa(df_dashboard, etapa)

            resumen_etapas.append(
                {
                    "Métrica": etapa["titulo"],
                    "Cumple": datos["cumple"],
                    "No Cumple": datos["no_cumple"],
                    "Evaluables": datos["total"],
                    "% Cumple": datos["pct_cumple"],
                    "% No Cumple": datos["pct_no_cumple"],
                    "Promedio Dx > 0": datos["promedio"],
                    "N promedio": datos["n_promedio"],
                }
            )

            with cols_etapas[i]:
                st.markdown(f"**{etapa['titulo_largo']}**")

                st.markdown(
                    f"""
                    <div style='font-size:12px;color:#555;min-height:36px'>
                        {etapa['regla']}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.altair_chart(
                    grafico_donut(datos["cumple"], datos["no_cumple"]),
                    use_container_width=True,
                )

                st.markdown(
                    f"""
                    <div style="text-align:center; margin-top:-6px;">
                        <div style="font-size:32px; font-weight:800; color:#1f2937;">
                            {datos['promedio']:.0f}
                        </div>
                        <div style="font-size:12px; color:#6b7280;">
                            {etapa['texto_promedio']}
                        </div>
                        <div style="font-size:11px; color:#6b7280; margin-top:4px;">
                            Evaluables: {datos['total']:,} · Promedio Dx &gt; 0: {datos['n_promedio']:,}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        resumen_etapas_df = pd.DataFrame(resumen_etapas)

        c_rank, c_rangos = st.columns([1.1, 1])

        with c_rank:
            st.subheader("Ranking de cumplimiento por etapa")
            grafico_barras_etapas(resumen_etapas_df)

        with c_rangos:
            st.subheader("Rango de incumplimiento TAT")
            grafico_rangos(df_dashboard)

        with st.expander("Ver tabla resumen por etapa", expanded=False):
            st.dataframe(
                resumen_etapas_df,
                use_container_width=True,
                hide_index=True,
            )

    with tab_auditoria:
        st.subheader("Lógica y trazabilidad")

        if mostrar_resumen_logica:
            st.info(
                f"Se cargaron {len(df_original):,} registros. "
                f"El resultado final conserva {len(df_final):,} registros y agrega {len(columnas_nuevas):,} columnas calculadas."
            )

        with st.expander("Inputs y fórmulas aplicadas", expanded=True):
            st.dataframe(
                tabla_formulas,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Columnas nuevas agregadas", expanded=False):
            st.dataframe(
                resumen_cols,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Resumen de performance", expanded=True):
            st.dataframe(
                resumen_perf,
                use_container_width=True,
                hide_index=True,
            )

        with st.expander("Top filas con mayor incumplimiento TAT", expanded=False):
            if "dias_incumplimiento_tat" in df_dashboard.columns:
                columnas_top = [
                    "Solicitud de pedido - ME5A",
                    COL_PEDIDO,
                    COL_DOCUMENTO_COMPRAS,
                    "tipo_oc",
                    "origen",
                    "sistema",
                    "dias_tat_total",
                    "umbral_tat_total",
                    "dias_incumplimiento_tat",
                    "rango_incumplimiento_tat",
                    "performance_tat_total",
                    COL_FECHA_SOLICITUD_FINAL,
                    COL_FECHA_RECEPCION_FINAL,
                ]

                columnas_top = [
                    col for col in columnas_top
                    if col in df_dashboard.columns
                ]

                st.dataframe(
                    df_dashboard
                    .sort_values("dias_incumplimiento_tat", ascending=False)[columnas_top]
                    .head(int(limite_vista)),
                    use_container_width=True,
                    hide_index=True,
                )

        with st.expander("Auditoría de días altos por etapa", expanded=False):
            columnas_dias = [
                "dias_liberacion_solped",
                "dias_comprador",
                "dias_proveedor",
                "dias_logistica",
                "dias_tat_total",
            ]

            columnas_dias = [
                col for col in columnas_dias
                if col in df_dashboard.columns
            ]

            if columnas_dias:
                etapa_auditoria = st.selectbox(
                    "Selecciona etapa",
                    columnas_dias,
                )

                modo = st.radio(
                    "Ordenar por",
                    ["Días más altos", "Días más bajos / negativos"],
                    horizontal=True,
                )

                asc = modo == "Días más bajos / negativos"

                serie = pd.to_numeric(
                    df_dashboard[etapa_auditoria],
                    errors="coerce",
                )

                col_umbral = etapa_auditoria.replace("dias_", "umbral_")

                sobre_umbral = 0

                if col_umbral in df_dashboard.columns:
                    sobre_umbral = int(
                        serie.gt(
                            pd.to_numeric(
                                df_dashboard[col_umbral],
                                errors="coerce",
                            )
                        ).sum()
                    )

                a1, a2, a3 = st.columns(3)

                a1.metric("Valores válidos", f"{int(serie.notna().sum()):,}")
                a2.metric("Días negativos", f"{int(serie.lt(0).sum()):,}")
                a3.metric("Sobre umbral", f"{sobre_umbral:,}")

                columnas_auditoria = [
                    "Solicitud de pedido - ME5A",
                    COL_PEDIDO,
                    COL_DOCUMENTO_COMPRAS,
                    "tipo_oc",
                    "origen",
                    "sistema",
                    COL_FECHA_SOLICITUD_FINAL,
                    COL_FECHA_LIBERACION_FINAL,
                    COL_FECHA_PEDIDO_FINAL,
                    COL_FECHA_FACTURACION_FINAL,
                    COL_FECHA_RECEPCION_FINAL,
                    "dias_liberacion_solped",
                    "dias_comprador",
                    "dias_proveedor",
                    "dias_logistica",
                    "dias_tat_total",
                    "performance_tat_total",
                ]

                columnas_auditoria = [
                    col for col in columnas_auditoria
                    if col in df_dashboard.columns
                ]

                st.dataframe(
                    df_dashboard
                    .assign(_orden=serie)
                    .sort_values("_orden", ascending=asc)
                    .drop(columns=["_orden"])[columnas_auditoria]
                    .head(int(limite_vista)),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.info("No hay columnas de días disponibles para auditar.")

    with tab_datos:
        st.subheader("Vista previa original")

        st.caption(
            f"Mostrando hasta {int(limite_vista):,} registros de {len(df_original):,} originales."
        )

        st.dataframe(
            df_original.head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )

        st.subheader("Vista previa final filtrada")

        columnas_preferidas = [
            "Solicitud de pedido - ME5A",
            COL_PEDIDO,
            COL_DOCUMENTO_COMPRAS,
            "tipo_oc",
            "origen",
            "sistema",
            "nombre_tipo_compra",
            "monto",
            COL_FECHA_SOLICITUD_FINAL,
            COL_FECHA_LIBERACION_FINAL,
            COL_FECHA_PEDIDO_FINAL,
            COL_FECHA_FACTURACION_FINAL,
            COL_FECHA_RECEPCION_FINAL,
            "dias_liberacion_solped",
            "dias_comprador",
            "dias_liberacion_pedido",
            "dias_proveedor",
            "dias_logistica",
            "dias_tat_total",
            "umbral_liberacion_solped",
            "umbral_comprador",
            "umbral_proveedor",
            "umbral_logistica",
            "umbral_tat_total",
            "performance_liberacion_solped",
            "performance_comprador",
            "performance_proveedor",
            "performance_logistica",
            "performance_tat_total",
            "tiene_fechas_inconsistentes",
            "dias_incumplimiento_tat",
            "incumplimiento_tat",
            "rango_incumplimiento_tat",
        ]

        columnas_preferidas = [
            col for col in columnas_preferidas
            if col in df_dashboard.columns
        ]

        st.dataframe(
            df_dashboard[columnas_preferidas].head(int(limite_vista)),
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("Ver columnas disponibles", expanded=False):
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("**Columnas originales**")
                st.write(columnas_originales)

            with c2:
                st.markdown("**Columnas finales**")
                st.write(df_final.columns.tolist())

    with tab_descarga:
        st.subheader("Descarga")

        st.download_button(
            label="Descargar resultado completo en Parquet",
            data=parquet_bytes,
            file_name="match_integrado_me5a_ariba_nme80fn_performance.parquet",
            mime="application/octet-stream",
            use_container_width=True,
        )

        col_csv, col_excel = st.columns(2)

        with col_csv:
            csv_bytes = convertir_a_csv_cache(df_final)

            st.download_button(
                label="Descargar resultado completo en CSV",
                data=csv_bytes,
                file_name="match_integrado_me5a_ariba_nme80fn_performance.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with col_excel:
            limite_excel = 250_000

            if len(df_final) > limite_excel:
                st.warning(
                    f"Excel no disponible porque la salida supera {limite_excel:,} filas. Usa Parquet o CSV."
                )
            else:
                excel_bytes = convertir_a_excel_cache(
                    df_final,
                    resumen_perf,
                    resumen_cols,
                    tabla_formulas,
                )

                st.download_button(
                    label="Descargar resultado completo en Excel",
                    data=excel_bytes,
                    file_name="match_integrado_me5a_ariba_nme80fn_performance.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
