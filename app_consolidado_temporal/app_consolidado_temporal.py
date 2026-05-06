# =========================
# MOP
# =========================

URL_PAGINA_MOP = (
    "https://planeamiento.mop.gob.cl/"
    "indices-y-precios-para-calculo-del-reajuste-polinomico/"
)

MESES_MOP = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12
}

ITEMS_OBJETIVO_MOP = {
    1: "MOP indice precios consumidor",
    2: "MOP indice remuneraciones",
    3: "MOP petroleo diesel",
    22: "MOP dolar observado",
    27: "MOP petroleo diesel refineria concon"
}


def extraer_mes_anio_desde_archivo_mop(archivo):
    nombre = normalizar_texto(archivo)

    nombre_limpio = re.sub(r"[_\-.]+", " ", nombre)
    nombre_limpio = re.sub(r"\s+", " ", nombre_limpio).strip()

    partes = nombre_limpio.split()

    mes_detectado = None
    numero_mes = None

    for mes, numero in MESES_MOP.items():
        if mes in partes:
            mes_detectado = mes
            numero_mes = numero
            break

    if numero_mes is None:
        match_mes_num = re.search(
            r"(?:^|[^0-9])(0?[1-9]|1[0-2])(?:[^0-9]|$)",
            nombre_limpio
        )

        if match_mes_num:
            numero_mes = int(match_mes_num.group(1))
            mes_detectado = MESES_NOMBRE.get(numero_mes, "")

    anio_match = re.search(r"(20\d{2})", nombre_limpio)
    anio_detectado = int(anio_match.group(1)) if anio_match else None

    return mes_detectado, numero_mes, anio_detectado


def convertir_item_mop_a_entero(valor):
    if pd.isna(valor):
        return None

    texto = str(valor).strip()

    if texto.endswith(".0"):
        texto = texto[:-2]

    if texto.isdigit():
        return int(texto)

    return None


def obtener_valor_item_mop(df, item_objetivo):
    """
    Busca el ITEM en la columna 0 del Excel MOP
    y devuelve el valor de la columna 3.
    """

    for _, fila in df.iterrows():
        item = fila[0] if len(fila) > 0 else pd.NA
        valor = fila[3] if len(fila) > 3 else pd.NA

        item_numero = convertir_item_mop_a_entero(item)

        if item_numero == item_objetivo:
            return valor

    return pd.NA


@st.cache_data
def obtener_archivos_excel_mop():
    response = requests.get(
        URL_PAGINA_MOP,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    html = response.text

    hrefs = re.findall(
        r'href=["\'](.*?)["\']',
        html,
        flags=re.IGNORECASE
    )

    enlaces = []

    for href in hrefs:
        url_completa = urljoin(URL_PAGINA_MOP, href)
        url_decodificada = unquote(url_completa)

        enlaces.append({
            "url": url_completa,
            "url_decodificada": url_decodificada
        })

    df_enlaces = pd.DataFrame(enlaces).drop_duplicates()

    df_excel = df_enlaces[
        df_enlaces["url_decodificada"]
        .str.lower()
        .str.contains(r"\.xls|\.xlsx", regex=True, na=False)
    ].copy()

    if df_excel.empty:
        return df_excel

    df_excel["archivo"] = df_excel["url_decodificada"].str.split("/").str[-1]

    df_excel[["mes_texto", "Mes", "Año"]] = df_excel["archivo"].apply(
        lambda x: pd.Series(extraer_mes_anio_desde_archivo_mop(x))
    )

    df_excel = df_excel.dropna(subset=["Año", "Mes"]).copy()

    df_excel["Año"] = df_excel["Año"].astype(int)
    df_excel["Mes"] = df_excel["Mes"].astype(int)

    df_excel = df_excel.sort_values(
        ["Año", "Mes"],
        ascending=[True, True]
    ).reset_index(drop=True)

    return df_excel


@st.cache_data
def leer_archivo_excel_mop(url_archivo, archivo):
    response = requests.get(
        url_archivo,
        headers=HEADERS,
        timeout=30
    )
    response.raise_for_status()

    contenido = response.content

    excel = pd.ExcelFile(BytesIO(contenido))

    hoja = "planilla" if "planilla" in excel.sheet_names else excel.sheet_names[0]

    df = pd.read_excel(
        BytesIO(contenido),
        sheet_name=hoja,
        header=None
    )

    mes_texto, mes_numero, anio = extraer_mes_anio_desde_archivo_mop(archivo)

    registro = {
        "Año": anio,
        "Mes": mes_numero,
        "Fecha": pd.Timestamp(year=anio, month=mes_numero, day=1)
    }

    for item_objetivo, nombre_columna in ITEMS_OBJETIVO_MOP.items():
        registro[nombre_columna] = obtener_valor_item_mop(
            df=df,
            item_objetivo=item_objetivo
        )

    return registro


def generar_df_mop(anios):
    try:
        df_archivos = obtener_archivos_excel_mop()

        if df_archivos.empty:
            return pd.DataFrame()

        df_archivos = df_archivos[
            df_archivos["Año"].isin(anios)
        ].copy()

        if df_archivos.empty:
            return pd.DataFrame()

        registros = []

        barra = st.progress(0)
        estado = st.empty()

        total = len(df_archivos)

        for posicion, (_, row) in enumerate(df_archivos.iterrows(), start=1):
            estado.write(f"Procesando MOP {posicion} de {total}")

            try:
                registro = leer_archivo_excel_mop(
                    row["url_decodificada"],
                    row["archivo"]
                )

                registros.append(registro)

            except Exception as e:
                st.warning(f"MOP {row['archivo']}: {e}")

            barra.progress(posicion / total)

        barra.empty()
        estado.empty()

        df = pd.DataFrame(registros)

        if df.empty:
            return df

        for columna in df.columns:
            if columna not in ["Fecha", "Año", "Mes"]:
                df[columna] = convertir_numerico(df[columna])

        df = df.sort_values(
            ["Año", "Mes"],
            ascending=[True, True]
        ).reset_index(drop=True)

        return df

    except Exception as e:
        st.warning(f"MOP: {e}")
        return pd.DataFrame()
