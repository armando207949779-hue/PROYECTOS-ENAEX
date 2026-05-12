# Gráficos Streamlit con Altair: ordenados correctamente de mayor a menor

import altair as alt


def chart_nulos_por_columna(diag_cols: pd.DataFrame, top_n: int | None = None):
    """
    Grafica el porcentaje de nulos por columna.
    El gráfico queda forzado de mayor a menor usando Altair.
    """

    data = (
        diag_cols[["Columna", "% Nulos"]]
        .copy()
        .sort_values("% Nulos", ascending=False)
    )

    if top_n is not None:
        data = data.head(top_n)

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "Columna:N",
                sort=alt.SortField(
                    field="% Nulos",
                    order="descending"
                ),
                title="Columna",
                axis=alt.Axis(labelAngle=-90)
            ),
            y=alt.Y(
                "% Nulos:Q",
                title="% Nulos"
            ),
            tooltip=[
                alt.Tooltip("Columna:N", title="Columna"),
                alt.Tooltip("% Nulos:Q", title="% Nulos")
            ]
        )
        .properties(
            height=420
        )
    )

    st.altair_chart(chart, use_container_width=True)


def chart_tipos_dato(df: pd.DataFrame):
    """
    Grafica cantidad de columnas por tipo de dato.
    El gráfico queda forzado de mayor a menor.
    """

    data = (
        pd.Series(df.dtypes.astype(str), name="Tipo de dato")
        .value_counts()
        .reset_index()
    )

    data.columns = ["Tipo de dato", "Cantidad"]

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "Tipo de dato:N",
                sort=alt.SortField(
                    field="Cantidad",
                    order="descending"
                ),
                title="Tipo de dato"
            ),
            y=alt.Y(
                "Cantidad:Q",
                title="Cantidad de columnas"
            ),
            tooltip=[
                alt.Tooltip("Tipo de dato:N", title="Tipo de dato"),
                alt.Tooltip("Cantidad:Q", title="Cantidad")
            ]
        )
        .properties(
            height=350
        )
    )

    st.altair_chart(chart, use_container_width=True)


def chart_valores_unicos(diag_cols: pd.DataFrame, top_n: int = 10):
    """
    Grafica las columnas con más valores únicos.
    El gráfico queda forzado de mayor a menor.
    """

    data = (
        diag_cols[["Columna", "Valores únicos"]]
        .copy()
        .sort_values("Valores únicos", ascending=False)
        .head(top_n)
    )

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "Columna:N",
                sort=alt.SortField(
                    field="Valores únicos",
                    order="descending"
                ),
                title="Columna",
                axis=alt.Axis(labelAngle=-90)
            ),
            y=alt.Y(
                "Valores únicos:Q",
                title="Valores únicos"
            ),
            tooltip=[
                alt.Tooltip("Columna:N", title="Columna"),
                alt.Tooltip("Valores únicos:Q", title="Valores únicos")
            ]
        )
        .properties(
            height=420
        )
    )

    st.altair_chart(chart, use_container_width=True)
