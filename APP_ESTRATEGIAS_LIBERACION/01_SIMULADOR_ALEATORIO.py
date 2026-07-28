# ============================================================
# 01_APP_SIMULADOR_ALEATORIO
# APP_FLUJO_LIBERACION_SERVICIOS
#
# Funciones incluidas:
# - Mostrar logo del proyecto.
# - Cargar un archivo Excel desde Streamlit.
# - Leer y validar las hojas Flujo y Dic_Usuarios.
# - Simular un caso aleatorio de liberación.
# - Buscar un flujo por CECO, tipo de documento y monto.
#
# No incluye todavía:
# - Modificación de liberadores.
# - Cambio de versión.
# - Escritura o actualización del Excel original.
# ============================================================

from __future__ import annotations

import base64
import random
import re
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

LOGO_CANDIDATES = [
    PROJECT_DIR / "assets" / "logo.svg",
    BASE_DIR / "assets" / "logo.svg",
    PROJECT_DIR / "assets" / "logo.png",
    BASE_DIR / "assets" / "logo.png",
]

LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]

FLOW_REQUIRED_COLUMNS = [
    "CECO",
    "Planta",
    "Desde",
    "Hasta",
    "TipoDoc",
    "Lib1",
    "Lib2",
    "Lib3",
    "Lib4",
    "Lib5",
    "N_EO",
    "N_CD",
    "Match",
]

USER_REQUIRED_COLUMNS = ["Correo", "Cargo"]

DOC_LABEL = {
    "AZNB": "Material (AZNB)",
    "AZSR": "Servicio (AZSR)",
}

DOC_COLOR = {
    "AZNB": "#C62828",
    "AZSR": "#1565C0",
}

LS_LABEL = "Liberador Servicios"

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_CASE_KEY = "flujo_liberacion_last_case"


# ============================================================
# ESTILOS
# ============================================================

def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .block-container {
                padding-top: 1.2rem;
                padding-bottom: 2.5rem;
            }

            .fl-title {
                text-align: center;
                color: #17365D;
                font-size: 2rem;
                font-weight: 800;
                margin-top: 0.2rem;
                margin-bottom: 0.2rem;
            }

            .fl-subtitle {
                text-align: center;
                color: #64748B;
                font-size: 1rem;
                margin-bottom: 1.2rem;
            }

            .fl-section-title {
                color: #17365D;
                font-size: 1.1rem;
                font-weight: 800;
                margin-top: 0.4rem;
                margin-bottom: 0.6rem;
            }

            .fl-help {
                color: #64748B;
                font-size: 0.85rem;
                margin-top: -0.35rem;
                margin-bottom: 0.8rem;
            }

            .fl-card {
                font-family: Arial, sans-serif;
                padding: 16px;
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
            }

            .fl-metric {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 11px 13px;
                background: #FFFFFF;
                min-height: 78px;
            }

            .fl-metric-label {
                color: #64748B;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.03em;
            }

            .fl-metric-value {
                color: #17365D;
                font-size: 17px;
                font-weight: 800;
                margin-top: 5px;
                word-break: break-word;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LOGO
# ============================================================

def buscar_logo() -> Path | None:
    for path in LOGO_CANDIDATES:
        if path.exists() and path.is_file():
            return path
    return None


def mostrar_logo() -> None:
    logo_path = buscar_logo()

    if logo_path is None:
        return

    if logo_path.suffix.lower() == ".svg":
        try:
            logo_svg = logo_path.read_text(encoding="utf-8")
            logo_base64 = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")
            st.markdown(
                f"""
                <div style="
                    width: 100%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    margin-top: 4px;
                    margin-bottom: 10px;
                ">
                    <img
                        src="data:image/svg+xml;base64,{logo_base64}"
                        style="width: 220px; max-width: 60%; display: block;"
                        alt="Logo"
                    >
                </div>
                """,
                unsafe_allow_html=True,
            )
        except (OSError, UnicodeError):
            st.warning(f"No fue posible leer el logo: {logo_path.name}")
    else:
        st.image(str(logo_path), width=220)


# ============================================================
# UTILIDADES DE DATOS
# ============================================================

def clean_user(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none", "—", "-"} else text


def strip_user_email(value: Any) -> str:
    text = clean_user(value)

    if not text:
        return ""

    if text == LS_LABEL:
        return LS_LABEL

    match = re.match(r"^(.*?)(?:\s*\(([^)]+)\))?$", text)
    return match.group(1).strip() if match else text


def parse_bound(value: Any, low: bool = True) -> float:
    text = clean_user(value)

    if text in {"", "*"}:
        return 0.0 if low else 1e18

    normalized = text.replace(" ", "")

    # Formatos admitidos, entre otros:
    # 1.000.000 / 1,000,000 / 1000000 / 1000000,50
    if "." in normalized and "," in normalized:
        if normalized.rfind(",") > normalized.rfind("."):
            normalized = normalized.replace(".", "").replace(",", ".")
        else:
            normalized = normalized.replace(",", "")
    elif normalized.count(".") > 1:
        normalized = normalized.replace(".", "")
    elif normalized.count(",") > 1:
        normalized = normalized.replace(",", "")
    elif "," in normalized:
        left, right = normalized.rsplit(",", 1)
        normalized = left + right if len(right) == 3 else left + "." + right
    elif "." in normalized:
        left, right = normalized.rsplit(".", 1)
        if len(right) == 3 and left.replace("-", "").isdigit():
            normalized = left + right

    try:
        return float(normalized)
    except ValueError as exc:
        raise ValueError(f"Valor de rango no válido: {value!r}") from exc


def parse_amount(value: str) -> int | None:
    text = (value or "").strip()

    if not text:
        return None

    amount = parse_bound(text, low=True)

    if amount < 0:
        raise ValueError("El monto no puede ser negativo.")

    return int(round(amount))


def fmt_bound(value: Any) -> str:
    text = clean_user(value)

    if text == "*":
        return "*"

    try:
        number = parse_bound(value, low=False)
        if number >= 1e15:
            return "*"
        return f"{int(number):,}".replace(",", ".")
    except (TypeError, ValueError):
        return text


def fmt_money(value: int | float) -> str:
    return f"$ {int(value):,}".replace(",", ".")


def normalize_int(value: Any) -> int:
    if value is None:
        return 0

    try:
        if pd.isna(value):
            return 0
    except (TypeError, ValueError):
        pass

    try:
        return int(float(str(value).replace(",", ".")))
    except (TypeError, ValueError):
        return 0


def normalize_yes(value: Any) -> bool:
    return clean_user(value).upper() in {"SI", "SÍ", "YES", "TRUE", "1"}


def normalize_flow_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    flow = df.copy()
    flow.columns = [str(column).strip() for column in flow.columns]

    missing = [column for column in FLOW_REQUIRED_COLUMNS if column not in flow.columns]
    if missing:
        raise ValueError(
            "La hoja 'Flujo' no contiene todas las columnas obligatorias. "
            f"Faltan: {', '.join(missing)}."
        )

    flow["CECO"] = flow["CECO"].map(clean_user)
    flow["Planta"] = flow["Planta"].map(clean_user)
    flow["TipoDoc"] = flow["TipoDoc"].map(clean_user).str.upper()
    flow["Match"] = flow["Match"].map(clean_user).str.upper()

    for column in LIB_COLS:
        flow[column] = flow[column].map(clean_user)

    flow = flow[
        flow["CECO"].ne("")
        & flow["TipoDoc"].isin(DOC_LABEL)
    ].copy()

    if flow.empty:
        raise ValueError(
            "La hoja 'Flujo' no contiene registros válidos con CECO y TipoDoc AZNB/AZSR."
        )

    # Validación temprana de rangos.
    for index, row in flow.iterrows():
        try:
            low = parse_bound(row["Desde"], low=True)
            high = parse_bound(row["Hasta"], low=False)
        except ValueError as exc:
            excel_row = index + 2
            raise ValueError(f"Error de rango en la fila Excel {excel_row}: {exc}") from exc

        if low > high:
            excel_row = index + 2
            raise ValueError(
                f"Rango inválido en la fila Excel {excel_row}: Desde es mayor que Hasta."
            )

    return flow.reset_index(drop=True)


def normalize_users_dataframe(df: pd.DataFrame | None) -> pd.DataFrame:
    if df is None:
        return pd.DataFrame(columns=USER_REQUIRED_COLUMNS)

    users = df.copy()
    users.columns = [str(column).strip() for column in users.columns]

    for column in USER_REQUIRED_COLUMNS:
        if column not in users.columns:
            users[column] = ""

    users["Correo"] = users["Correo"].map(strip_user_email)
    users["Cargo"] = users["Cargo"].map(clean_user)
    users = users[users["Correo"].ne("")].drop_duplicates("Correo", keep="last")

    return users.reset_index(drop=True)


def load_workbook(uploaded_file: Any) -> dict[str, pd.DataFrame]:
    raw_bytes = uploaded_file.getvalue()

    if not raw_bytes:
        raise ValueError("El archivo cargado está vacío.")

    buffer = BytesIO(raw_bytes)

    try:
        excel_file = pd.ExcelFile(buffer)
    except Exception as exc:
        raise ValueError(
            "No fue posible abrir el archivo. Verifica que sea un Excel válido (.xlsx o .xls)."
        ) from exc

    if "Flujo" not in excel_file.sheet_names:
        raise ValueError("El archivo debe contener una hoja llamada 'Flujo'.")

    try:
        flow_raw = pd.read_excel(excel_file, sheet_name="Flujo")
        users_raw = (
            pd.read_excel(excel_file, sheet_name="Dic_Usuarios")
            if "Dic_Usuarios" in excel_file.sheet_names
            else None
        )
    except Exception as exc:
        raise ValueError("No fue posible leer las hojas del archivo Excel.") from exc

    return {
        "flujo": normalize_flow_dataframe(flow_raw),
        "dic_users": normalize_users_dataframe(users_raw),
    }


# ============================================================
# LÓGICA DE SIMULACIÓN
# ============================================================

def cargo_map(data: dict[str, pd.DataFrame]) -> dict[str, str]:
    mapping: dict[str, str] = {}

    for _, row in data["dic_users"].iterrows():
        email = strip_user_email(row.get("Correo", ""))
        cargo = clean_user(row.get("Cargo", ""))

        if email:
            mapping[email.lower()] = cargo

    return mapping


def display_with_cargo(user: Any, data: dict[str, pd.DataFrame]) -> str:
    email = strip_user_email(user)

    if not email:
        return ""

    if email == LS_LABEL:
        return LS_LABEL

    cargo = cargo_map(data).get(email.lower(), "")

    if not cargo or cargo == LS_LABEL:
        return email

    return f"{email} ({cargo})"


def pick_row(
    flow: pd.DataFrame,
    ceco: str,
    doc_type: str,
    amount: int | float,
) -> pd.Series | None:
    subset = flow[
        flow["CECO"].eq(ceco)
        & flow["TipoDoc"].eq(doc_type)
    ]

    for _, row in subset.iterrows():
        low = parse_bound(row["Desde"], low=True)
        high = parse_bound(row["Hasta"], low=False)

        if low <= amount <= high:
            return row

    return None


def libs_from_row(row: pd.Series) -> list[str]:
    return [
        strip_user_email(row[column])
        for column in LIB_COLS
        if strip_user_email(row[column])
    ]


def random_amount_for_row(row: pd.Series) -> int:
    low = max(0, int(parse_bound(row["Desde"], low=True)))
    high_value = parse_bound(row["Hasta"], low=False)

    # Los tramos abiertos (*) se acotan para generar un caso práctico.
    if high_value >= 1e17:
        high = low + 20_000_000
    else:
        high = int(high_value)

    if high < low:
        raise ValueError("El rango seleccionado tiene límites inconsistentes.")

    return random.randint(low, high)


def build_case(
    data: dict[str, pd.DataFrame],
    ceco: str,
    doc_type: str | None = None,
    amount: int | None = None,
) -> dict[str, Any]:
    flow = data["flujo"]
    ceco = clean_user(ceco)

    available_docs = sorted(
        flow.loc[flow["CECO"].eq(ceco), "TipoDoc"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    available_docs = [doc for doc in available_docs if doc in DOC_LABEL]

    if not available_docs:
        raise ValueError(f"No existen datos válidos para el CECO {ceco}.")

    if doc_type is None:
        doc_type = random.choice(available_docs)

    if doc_type not in available_docs:
        raise ValueError(
            f"El CECO {ceco} no tiene registros para {DOC_LABEL.get(doc_type, doc_type)}."
        )

    rows = flow[
        flow["CECO"].eq(ceco)
        & flow["TipoDoc"].eq(doc_type)
    ]

    if amount is None:
        selected_row = rows.sample(n=1).iloc[0]
        amount = random_amount_for_row(selected_row)
    else:
        selected_row = pick_row(flow, ceco, doc_type, amount)

    if selected_row is None:
        raise ValueError(
            "No se encontró un tramo para la combinación de CECO, tipo y monto indicada."
        )

    return {
        "ceco": ceco,
        "planta": clean_user(selected_row.get("Planta", "")),
        "doc": doc_type,
        "monto": int(amount),
        "desde": selected_row["Desde"],
        "hasta": selected_row["Hasta"],
        "match": normalize_yes(selected_row.get("Match", "")),
        "n_eo": normalize_int(selected_row.get("N_EO", 0)),
        "n_cd": normalize_int(selected_row.get("N_CD", 0)),
        "libs": libs_from_row(selected_row),
    }


def available_pairs(
    data: dict[str, pd.DataFrame],
    only_match: bool,
    doc_filter: str,
) -> list[tuple[str, str]]:
    flow = data["flujo"]

    if only_match:
        flow = flow[flow["Match"].map(normalize_yes)]

    if doc_filter in DOC_LABEL:
        flow = flow[flow["TipoDoc"].eq(doc_filter)]

    pairs = (
        flow[["CECO", "TipoDoc"]]
        .drop_duplicates()
        .itertuples(index=False, name=None)
    )

    return [
        (str(ceco), str(doc_type))
        for ceco, doc_type in pairs
        if doc_type in DOC_LABEL
    ]


# ============================================================
# HTML DE RESULTADOS
# ============================================================

def html_flow(
    case: dict[str, Any],
    data: dict[str, pd.DataFrame],
) -> str:
    users = [user for user in case["libs"] if clean_user(user)]

    if not users:
        return (
            "<p style='font-family:Arial,sans-serif;color:#64748B;'>"
            "El tramo no tiene liberadores registrados.</p>"
        )

    range_text = f"{fmt_bound(case['desde'])} – {fmt_bound(case['hasta'])}"
    parts: list[str] = []

    for index, user in enumerate(users, start=1):
        is_eo = index <= case["n_eo"]

        if is_eo:
            background = "#EAF7EE"
            border = "#7BC596"
            text_color = "#166534"
            group_label = "EO"
        else:
            background = "#F8FAFC"
            border = "#CBD5E1"
            text_color = "#1E3A8A"
            group_label = "CD"

        parts.append(
            f"""
            <div style="
                min-width: 170px;
                max-width: 225px;
                background: {background};
                border: 2px solid {border};
                border-radius: 12px;
                padding: 11px;
                font-family: Arial, sans-serif;
            ">
                <div style="font-size:11px;color:#64748B;font-weight:700;">
                    Liberador {index} · {group_label}
                </div>
                <div style="
                    font-weight:700;
                    color:{text_color};
                    margin:6px 0;
                    overflow-wrap:anywhere;
                    font-size:12px;
                ">
                    {escape(display_with_cargo(user, data))}
                </div>
                <div style="font-size:10px;color:#64748B;">
                    {escape(range_text)}
                </div>
            </div>
            """
        )

        if index < len(users):
            parts.append(
                "<div style='font-size:21px;color:#94A3B8;font-weight:700;'>→</div>"
            )

    return (
        "<div style='font-family:Arial,sans-serif;margin-top:14px;'>"
        "<div style='font-weight:800;color:#17365D;margin-bottom:8px;'>Flujo final</div>"
        "<div style='display:flex;flex-wrap:wrap;align-items:center;gap:7px;'>"
        f"{''.join(parts)}"
        "</div></div>"
    )


def html_case(
    case: dict[str, Any],
    data: dict[str, pd.DataFrame],
    title: str,
) -> str:
    doc_color = DOC_COLOR.get(case["doc"], "#17365D")

    if case["match"]:
        badge = (
            "<span style='background:#166534;color:#FFFFFF;padding:3px 9px;"
            "border-radius:999px;font-size:11px;font-weight:700;'>MATCH</span>"
        )
    else:
        badge = (
            "<span style='background:#C2410C;color:#FFFFFF;padding:3px 9px;"
            "border-radius:999px;font-size:11px;font-weight:700;'>Solo CD</span>"
        )

    metrics = [
        ("CECO", case["ceco"]),
        ("Planta", case["planta"] or "—"),
        ("Tipo", DOC_LABEL.get(case["doc"], case["doc"])),
        ("Monto", fmt_money(case["monto"])),
        ("Tramo", f"{fmt_bound(case['desde'])} – {fmt_bound(case['hasta'])}"),
        ("Liberadores", str(len(case["libs"]))),
    ]

    metric_html = "".join(
        f"""
        <div class="fl-metric">
            <div class="fl-metric-label">{escape(label)}</div>
            <div class="fl-metric-value" style="{'color:' + doc_color + ';' if label == 'Tipo' else ''}">
                {escape(value)}
            </div>
        </div>
        """
        for label, value in metrics
    )

    return f"""
        <div class="fl-card">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
                <div style="color:#17365D;font-size:17px;font-weight:800;">
                    {escape(title)}
                </div>
                {badge}
            </div>

            <div style="
                display:grid;
                grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
                gap:9px;
                margin-top:13px;
            ">
                {metric_html}
            </div>

            {html_flow(case, data)}
        </div>
    """


# ============================================================
# COMPONENTES DE INTERFAZ
# ============================================================

def render_header() -> None:
    mostrar_logo()
    st.markdown(
        '<div class="fl-title">01 Simulador Aleatorio</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="fl-subtitle">
            Simulación de flujos de liberación para materiales y servicios.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upload_section() -> None:
    st.markdown(
        '<div class="fl-section-title">1. Cargar base de datos</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="fl-help">
            Carga el Excel de flujo de liberación. La hoja <b>Flujo</b> es obligatoria;
            la hoja <b>Dic_Usuarios</b> se utiliza para mostrar el cargo de cada correo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Archivo Excel",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        key="flujo_liberacion_uploader",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        current_name = st.session_state.get(SESSION_FILE_KEY)
        needs_load = (
            current_name != uploaded_file.name
            or SESSION_DATA_KEY not in st.session_state
        )

        if needs_load:
            try:
                with st.spinner("Leyendo y validando archivo..."):
                    data = load_workbook(uploaded_file)

                st.session_state[SESSION_DATA_KEY] = data
                st.session_state[SESSION_FILE_KEY] = uploaded_file.name
                st.session_state.pop(SESSION_CASE_KEY, None)
            except ValueError as exc:
                st.session_state.pop(SESSION_DATA_KEY, None)
                st.session_state.pop(SESSION_FILE_KEY, None)
                st.session_state.pop(SESSION_CASE_KEY, None)
                st.error(str(exc))

    data = st.session_state.get(SESSION_DATA_KEY)

    if data is not None:
        flow = data["flujo"]
        file_name = st.session_state.get(SESSION_FILE_KEY, "Archivo cargado")
        match_count = int(flow["Match"].map(normalize_yes).sum())

        st.success(
            f"Archivo activo: **{file_name}** · "
            f"**{len(flow):,} filas** · "
            f"**{flow['CECO'].nunique():,} CECO** · "
            f"**{match_count:,} filas MATCH**".replace(",", ".")
        )

        with st.expander("Vista previa de la hoja Flujo", expanded=False):
            preview_columns = [
                column
                for column in [
                    "CECO",
                    "Planta",
                    "Desde",
                    "Hasta",
                    "TipoDoc",
                    "Lib1",
                    "Lib2",
                    "Lib3",
                    "Lib4",
                    "Lib5",
                    "N_EO",
                    "N_CD",
                    "Match",
                ]
                if column in flow.columns
            ]
            st.dataframe(
                flow[preview_columns].head(100),
                use_container_width=True,
                hide_index=True,
            )


def ceco_options(data: dict[str, pd.DataFrame]) -> list[str]:
    flow = data["flujo"]
    options: list[str] = []

    for ceco in sorted(flow["CECO"].unique().tolist()):
        plants = (
            flow.loc[flow["CECO"].eq(ceco), "Planta"]
            .map(clean_user)
            .loc[lambda series: series.ne("")]
            .unique()
            .tolist()
        )
        plant = plants[0] if plants else ""
        options.append(f"{ceco} | {plant}" if plant else ceco)

    return options


def parse_ceco_label(value: str) -> str:
    text = clean_user(value)
    return text.split("|", 1)[0].strip() if "|" in text else text


def render_simulator(data: dict[str, pd.DataFrame]) -> None:
    st.markdown("---")
    st.markdown(
        '<div class="fl-section-title">2. Simular flujo</div>',
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1], gap="large")

    with left:
        only_match = st.checkbox(
            "Solo considerar CECO con MATCH",
            value=True,
            key="sim_only_match",
        )

        doc_filter = st.selectbox(
            "Tipo de documento",
            options=["RAND", "AZNB", "AZSR"],
            format_func=lambda value: {
                "RAND": "Aleatorio (Material o Servicio)",
                "AZNB": "Material (AZNB)",
                "AZSR": "Servicio (AZSR)",
            }[value],
            key="sim_doc_filter",
        )

        random_button = st.button(
            "🎲 Generar caso aleatorio",
            type="primary",
            use_container_width=True,
            key="sim_random_button",
        )

    with right:
        selected_ceco_label = st.selectbox(
            "CECO",
            options=[""] + ceco_options(data),
            format_func=lambda value: "— Selecciona un CECO —" if not value else value,
            key="sim_ceco",
        )

        manual_doc = st.selectbox(
            "Tipo para búsqueda",
            options=["RAND", "AZNB", "AZSR"],
            format_func=lambda value: {
                "RAND": "Automático según CECO",
                "AZNB": "Material (AZNB)",
                "AZSR": "Servicio (AZSR)",
            }[value],
            key="sim_manual_doc",
        )

        amount_text = st.text_input(
            "Monto",
            placeholder="Vacío = monto automático",
            key="sim_amount",
        )

        search_button = st.button(
            "🔎 Buscar CECO y monto",
            use_container_width=True,
            key="sim_search_button",
        )

    if random_button:
        try:
            pairs = available_pairs(data, only_match, doc_filter)

            if not pairs:
                raise ValueError(
                    "No existen combinaciones CECO/tipo para los filtros seleccionados."
                )

            ceco, doc_type = random.choice(pairs)
            case = build_case(data, ceco, doc_type=doc_type, amount=None)
            st.session_state[SESSION_CASE_KEY] = {
                "case": case,
                "title": f"Caso aleatorio · {DOC_LABEL[doc_type]}",
            }
        except ValueError as exc:
            st.error(str(exc))

    if search_button:
        try:
            ceco = parse_ceco_label(selected_ceco_label)

            if not ceco:
                raise ValueError("Selecciona un CECO para realizar la búsqueda.")

            amount = parse_amount(amount_text)
            flow = data["flujo"]

            docs = sorted(
                flow.loc[flow["CECO"].eq(ceco), "TipoDoc"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            docs = [doc for doc in docs if doc in DOC_LABEL]

            if not docs:
                raise ValueError("El CECO seleccionado no tiene registros AZNB/AZSR.")

            doc_type = random.choice(docs) if manual_doc == "RAND" else manual_doc
            case = build_case(data, ceco, doc_type=doc_type, amount=amount)
            st.session_state[SESSION_CASE_KEY] = {
                "case": case,
                "title": "Resultado de búsqueda",
            }
        except ValueError as exc:
            st.error(str(exc))

    result = st.session_state.get(SESSION_CASE_KEY)

    if result:
        st.markdown("---")
        st.markdown(
            '<div class="fl-section-title">3. Resultado</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            html_case(result["case"], data, result["title"]),
            unsafe_allow_html=True,
        )
    else:
        st.info(
            "Genera un caso aleatorio o realiza una búsqueda para visualizar el flujo."
        )


# ============================================================
# APP PRINCIPAL
# ============================================================

def main() -> None:
    aplicar_estilos()
    render_header()
    render_upload_section()

    data = st.session_state.get(SESSION_DATA_KEY)

    if data is None:
        st.info("Carga un archivo Excel para habilitar el simulador.")
        st.stop()

    render_simulator(data)


if __name__ == "__main__":
    main()
