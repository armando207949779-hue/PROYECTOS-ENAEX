from pathlib import Path
import sys


def reemplazar_una_vez(texto: str, anterior: str, nuevo: str, descripcion: str) -> str:
    if anterior not in texto:
        raise RuntimeError(f"No se encontró el bloque para: {descripcion}")
    return texto.replace(anterior, nuevo, 1)


def actualizar_archivo(ruta_entrada: Path, ruta_salida: Path) -> None:
    texto = ruta_entrada.read_text(encoding="utf-8")

    marcador = 'def estilizar_dataframe(\n    df: pd.DataFrame,\n    columnas_monto: list[str] | None = None,\n    columnas_porcentaje: list[str] | None = None,\n    columnas_entero: list[str] | None = None,\n):'

    reemplazo = 'def formatear_fechas_dataframe(\n    df: pd.DataFrame,\n    columnas_fecha: list[str] | None = None,\n) -> pd.DataFrame:\n    df_formateado = df.copy()\n\n    for col in columnas_fecha or []:\n        if col not in df_formateado.columns:\n            continue\n\n        fechas = pd.to_datetime(\n            df_formateado[col],\n            errors="coerce",\n        )\n\n        df_formateado[col] = fechas.dt.strftime("%d-%m-%Y")\n        df_formateado.loc[fechas.isna(), col] = ""\n\n    return df_formateado\n\n\ndef estilizar_dataframe(\n    df: pd.DataFrame,\n    columnas_monto: list[str] | None = None,\n    columnas_porcentaje: list[str] | None = None,\n    columnas_entero: list[str] | None = None,\n):'

    texto = reemplazar_una_vez(
        texto,
        marcador,
        reemplazo,
        "incorporar el formateo visual de fechas",
    )

    texto = reemplazar_una_vez(
        texto,
        '        str(fecha_inicio),\n        "Fecha inicial seleccionada",',
        '        fecha_inicio.strftime("%d-%m-%Y"),\n        "Fecha inicial seleccionada",',
        "formatear la fecha inicial del KPI",
    )

    texto = reemplazar_una_vez(
        texto,
        '        str(fecha_fin),\n        "Fecha final seleccionada",',
        '        fecha_fin.strftime("%d-%m-%Y"),\n        "Fecha final seleccionada",',
        "formatear la fecha final del KPI",
    )

    reemplazos_expanders = {
        '    with st.expander(\n        "Ver tabla de gasto anual"\n    ):':
            '    with st.expander(\n        "Ver tabla de gasto anual",\n        expanded=True,\n    ):',
        '    with st.expander(\n        "Ver tabla completa de gasto mensual"\n    ):':
            '    with st.expander(\n        "Ver tabla completa de gasto mensual",\n        expanded=True,\n    ):',
        '    with st.expander(\n        "Ver tabla por tipo de OC"\n    ):':
            '    with st.expander(\n        "Ver tabla por tipo de OC",\n        expanded=True,\n    ):',
        'with st.expander(\n    "Monedas únicas en órdenes"\n):':
            'with st.expander(\n    "Monedas únicas en órdenes",\n    expanded=True,\n):',
        'with st.expander(\n    "Órdenes ME2N convertidas a USD"\n):':
            'with st.expander(\n    "Órdenes ME2N convertidas a USD",\n    expanded=True,\n):',
        'with st.expander(\n    "Resumen de validación"\n):':
            'with st.expander(\n    "Resumen de validación",\n    expanded=True,\n):',
    }

    for anterior, nuevo in reemplazos_expanders.items():
        texto = reemplazar_una_vez(
            texto,
            anterior,
            nuevo,
            "desplegar una tabla de apoyo",
        )

    marcador_detalle = '        st.dataframe(\n            estilizar_dataframe(\n                df_detalle_mes_tabla,\n                columnas_monto=['
    reemplazo_detalle = '        df_detalle_mes_visual = formatear_fechas_dataframe(\n            df_detalle_mes_tabla,\n            columnas_fecha=["Fecha_documento"],\n        )\n\n        st.dataframe(\n            estilizar_dataframe(\n                df_detalle_mes_visual,\n                columnas_monto=['

    texto = reemplazar_una_vez(
        texto,
        marcador_detalle,
        reemplazo_detalle,
        "formatear fechas del detalle mensual",
    )

    marcador_preview = '    st.dataframe(\n        estilizar_dataframe(\n            df_preview,\n            columnas_monto=['
    reemplazo_preview = '    df_preview_visual = formatear_fechas_dataframe(\n        df_preview,\n        columnas_fecha=["Fecha_documento"],\n    )\n\n    st.dataframe(\n        estilizar_dataframe(\n            df_preview_visual,\n            columnas_monto=['

    texto = reemplazar_una_vez(
        texto,
        marcador_preview,
        reemplazo_preview,
        "formatear fechas de la vista previa",
    )

    cambios_titulos = {
        '"Gasto total por año"': '"1. Gasto total por año"',
        '"Gasto mensual"': '"2. Evolución mensual del gasto"',
        '"Participación por tipo de orden de compra"':
            '"3. Distribución por tipo de orden de compra"',
        '"Tablas de apoyo"': '"4. Tablas de apoyo y validaciones"',
    }

    for anterior, nuevo in cambios_titulos.items():
        texto = reemplazar_una_vez(
            texto,
            anterior,
            nuevo,
            f"actualizar el título {anterior}",
        )

    texto = texto.replace("figsize=(9, 5)", "figsize=(12, 5.8)", 1)
    texto = texto.replace("figsize=(11, 5.5)", "figsize=(13, 6)", 1)

    ruta_salida.write_text(texto, encoding="utf-8")
    compile(texto, str(ruta_salida), "exec")


def main() -> None:
    entrada = (
        Path(sys.argv[1]).expanduser().resolve()
        if len(sys.argv) > 1
        else Path("03_APP_GASTOS.py").resolve()
    )

    salida = (
        Path(sys.argv[2]).expanduser().resolve()
        if len(sys.argv) > 2
        else entrada.with_name("03_APP_GASTOS_actualizado.py")
    )

    if not entrada.exists():
        raise FileNotFoundError(f"No se encontró el archivo de entrada: {entrada}")

    actualizar_archivo(entrada, salida)
    print(f"Archivo actualizado y validado: {salida}")


if __name__ == "__main__":
    main()
