# ============================================================
# 04_APP_DICCIONARIOS
# APP_ESTRATEGIAS_LIBERACION
#
# Vista compacta de la versión activa:
# - Flujo reconstruido.
# - Liberador 1, 2, 3, 4 y 5.
# - Diccionario CECO-Plantas.
# - Diccionario Usuarios-Cargos.
# - Historial de Cambios, cuando existe.
# ============================================================

from __future__ import annotations

import base64
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent
CHILE_TZ = ZoneInfo("America/Santiago")

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_VALIDATION_KEY = "flujo_liberacion_validation_v05"

LOGO_CANDIDATES = [
    PROJECT_DIR / "assets" / "logo.svg",
    BASE_DIR / "assets" / "logo.svg",
    PROJECT_DIR / "assets" / "logo.png",
    BASE_DIR / "assets" / "logo.png",
    PROJECT_DIR / "assets" / "logo.jpg",
    BASE_DIR / "assets" / "logo.jpg",
    PROJECT_DIR / "assets" / "logo.jpeg",
    BASE_DIR / "assets" / "logo.jpeg",
]

TABLE_CONFIG = {
    "flujo": {
        "label": "Flujo",
        "session_key": "flujo",
        "file_role": None,
    },
    "liberador_1": {
        "label": "Liberador 1",
        "session_key": "liberador_1",
        "file_role": "liberador_1",
    },
    "liberador_2": {
        "label": "Liberador 2",
        "session_key": "liberador_2",
        "file_role": "liberador_2",
    },
    "liberador_3": {
        "label": "Liberador 3",
        "session_key": "liberador_3",
        "file_role": "liberador_3",
    },
    "liberador_4": {
        "label": "Liberador 4",
        "session_key": "liberador_4",
        "file_role": "liberador_4",
    },
    "liberador_5": {
        "label": "Liberador 5",
        "session_key": "liberador_5",
        "file_role": "liberador_5",
    },
    "dic_ceco": {
        "label": "CECO–Plantas",
        "session_key": "dic_ceco",
        "file_role": "dic_ceco",
    },
    "dic_users": {
        "label": "Usuarios–Cargos",
        "session_key": "dic_users",
        "file_role": "dic_users",
    },
    "cambios": {
        "label": "Cambios",
        "session_key": "cambios",
        "file_role": "cambios",
    },
}

TECHNICAL_COLUMNS = {
    "_DesdeNum",
    "_HastaNum",
    "_Nivel",
    "_Liberador",
}


# ============================================================
# ESTILO
# ============================================================

def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .stMainBlockContainer,
            .block-container {
                padding-top: 5.4rem !important;
                padding-bottom: 2rem !important;
                max-width: 1500px !important;
            }

            .app-logo {
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 0 0 .35rem;
            }

            .app-logo img {
                width: 180px;
                max-height: 72px;
                object-fit: contain;
            }

            .app-title {
                text-align: center;
                color: #17365D;
                font-size: 1.75rem;
                font-weight: 800;
                margin: 0;
            }

            .app-subtitle {
                text-align: center;
                color: #667085;
                font-size: .92rem;
                margin: .2rem 0 1rem;
            }

            div[data-testid="stMetric"] {
                border: 1px solid #E4E7EC;
                border-radius: 10px;
                background: #FFFFFF;
                padding: .6rem .8rem;
            }

            div[data-testid="stDataFrame"] {
                border: 1px solid #E4E7EC;
                border-radius: 10px;
                overflow: hidden;
            }

            div[data-baseweb="tab-list"] {
                gap: .2rem;
            }

            button[data-baseweb="tab"] {
                padding-left: .75rem;
                padding-right: .75rem;
            }

            .source-line {
                color: #667085;
                font-size: .82rem;
                margin: -.25rem 0 .55rem;
                overflow-wrap: anywhere;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# UTILIDADES
# ============================================================

def clean_text(value: Any) -> str:
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()
    return "" if text.casefold() in {
        "",
        "nan",
        "none",
        "null",
        "<na>",
    } else text


def buscar_logo() -> Path | None:
    return next(
        (
            path
            for path in LOGO_CANDIDATES
            if path.exists() and path.is_file()
        ),
        None,
    )


def mostrar_logo() -> None:
    path = buscar_logo()
    if path is None:
        return

    try:
        raw = path.read_bytes()
        suffix = path.suffix.casefold()
        mime = {
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
        }.get(suffix, "application/octet-stream")

        encoded = base64.b64encode(raw).decode("utf-8")
        st.markdown(
            (
                '<div class="app-logo">'
                f'<img src="data:{mime};base64,{encoded}" alt="Logo ENAEX">'
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    except OSError:
        pass


def render_header() -> None:
    mostrar_logo()
    st.markdown(
        '<div class="app-title">04 Vista de Datos</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        (
            '<div class="app-subtitle">'
            "Consulta la versión activa y sus archivos normalizados."
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def obtener_version_desde_nombre(
    nombre_archivo: str,
) -> datetime | None:
    stem = Path(clean_text(nombre_archivo)).stem

    patterns = [
        (
            r"(?<!\d)(\d{2})(\d{2})(\d{4})[_-]"
            r"(\d{2})(\d{2})(\d{2})(?!\d)",
            "DMY",
        ),
        (
            r"(?<!\d)(\d{4})(\d{2})(\d{2})[_-]"
            r"(\d{2})(\d{2})(\d{2})(?!\d)",
            "YMD",
        ),
    ]

    for pattern, order in patterns:
        matches = list(re.finditer(pattern, stem))
        if not matches:
            continue

        values = [int(value) for value in matches[-1].groups()]

        try:
            if order == "DMY":
                day, month, year, hour, minute, second = values
            else:
                year, month, day, hour, minute, second = values

            return datetime(
                year,
                month,
                day,
                hour,
                minute,
                second,
            )
        except ValueError:
            continue

    return None


def obtener_version_activa(
    file_names: dict[str, str],
) -> str:
    dates = [
        version
        for name in file_names.values()
        if (version := obtener_version_desde_nombre(name)) is not None
    ]

    if not dates:
        return "No detectada"

    return max(dates).strftime("%d-%m-%Y %H:%M:%S")


def get_dataframe(
    data: dict[str, Any],
    table_key: str,
) -> pd.DataFrame:
    if table_key.startswith("liberador_"):
        level = int(table_key.rsplit("_", 1)[-1])
        liberators = data.get("liberadores", {})

        if isinstance(liberators, dict):
            frame = liberators.get(level)
            if isinstance(frame, pd.DataFrame):
                return frame.copy()

    session_key = TABLE_CONFIG[table_key]["session_key"]
    frame = data.get(session_key)

    if isinstance(frame, pd.DataFrame):
        return frame.copy()

    return pd.DataFrame()


def clean_display_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe.copy()

    return dataframe.drop(
        columns=[
            column
            for column in dataframe.columns
            if column in TECHNICAL_COLUMNS
        ],
        errors="ignore",
    ).copy()


def apply_search(
    dataframe: pd.DataFrame,
    search_text: str,
) -> pd.DataFrame:
    search = clean_text(search_text).casefold()
    if not search or dataframe.empty:
        return dataframe.copy()

    text_frame = dataframe.fillna("").astype(str)
    mask = text_frame.apply(
        lambda row: row.str.casefold().str.contains(
            re.escape(search),
            regex=True,
            na=False,
        ).any(),
        axis=1,
    )
    return dataframe.loc[mask].copy()


def dataframe_to_csv_bytes(
    dataframe: pd.DataFrame,
) -> bytes:
    return dataframe.to_csv(
        index=False,
        sep=";",
        lineterminator="\n",
    ).encode("utf-8-sig")


def dataframe_to_excel_bytes(
    dataframe: pd.DataFrame,
    sheet_name: str,
) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:
        dataframe.to_excel(
            writer,
            index=False,
            sheet_name=sheet_name[:31],
        )
    return output.getvalue()


def safe_file_part(value: str) -> str:
    return re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        clean_text(value),
    ).strip("_") or "DATOS"


# ============================================================
# COMPONENTES
# ============================================================

def render_summary(
    data: dict[str, Any],
    file_names: dict[str, str],
) -> None:
    flow = get_dataframe(data, "flujo")
    changes = get_dataframe(data, "cambios")

    metrics = st.columns(4)
    metrics[0].metric(
        "Versión",
        obtener_version_activa(file_names),
    )
    metrics[1].metric(
        "Reglas",
        f"{len(flow):,}".replace(",", "."),
    )
    metrics[2].metric(
        "CECO",
        (
            f"{flow['CECO'].nunique():,}".replace(",", ".")
            if "CECO" in flow.columns
            else "0"
        ),
    )
    metrics[3].metric(
        "Cambios",
        f"{len(changes):,}".replace(",", "."),
    )


def render_table_view(
    table_key: str,
    dataframe: pd.DataFrame,
    source_name: str,
) -> None:
    config = TABLE_CONFIG[table_key]
    label = config["label"]
    display = clean_display_dataframe(dataframe)

    if source_name:
        st.markdown(
            (
                '<div class="source-line">'
                f"Fuente: {source_name}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

    if display.empty:
        st.info(f"No hay registros disponibles en {label}.")
        return

    control_1, control_2 = st.columns([3, 1])

    with control_1:
        search = st.text_input(
            "Buscar",
            placeholder="Buscar en todas las columnas",
            key=f"view_search_{table_key}_v01",
            label_visibility="collapsed",
        )

    searched = apply_search(display, search)

    max_rows = max(25, min(5000, len(searched)))
    default_rows = min(250, max_rows)

    with control_2:
        rows_to_show = st.selectbox(
            "Filas",
            options=[
                value
                for value in [50, 100, 250, 500, 1000, 2500, 5000]
                if value <= max_rows
            ] or [max_rows],
            index=(
                [
                    value
                    for value in [50, 100, 250, 500, 1000, 2500, 5000]
                    if value <= max_rows
                ] or [max_rows]
            ).index(default_rows)
            if default_rows in (
                [
                    value
                    for value in [50, 100, 250, 500, 1000, 2500, 5000]
                    if value <= max_rows
                ] or [max_rows]
            )
            else 0,
            key=f"view_rows_{table_key}_v01",
            label_visibility="collapsed",
        )

    visible = searched.head(rows_to_show)

    info_1, info_2, info_3 = st.columns(3)
    info_1.caption(
        f"Registros: {len(display):,}".replace(",", ".")
    )
    info_2.caption(
        f"Coincidencias: {len(searched):,}".replace(",", ".")
    )
    info_3.caption(
        f"Columnas: {len(display.columns):,}".replace(",", ".")
    )

    st.dataframe(
        visible,
        use_container_width=True,
        hide_index=True,
        height=min(
            700,
            max(300, 34 * (len(visible) + 1)),
        ),
    )

    timestamp = datetime.now(CHILE_TZ).strftime(
        "%d%m%Y_%H%M%S"
    )
    base_name = safe_file_part(label)

    download_1, download_2 = st.columns(2)

    with download_1:
        st.download_button(
            "Descargar CSV",
            data=dataframe_to_csv_bytes(searched),
            file_name=f"{base_name}_{timestamp}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"view_csv_{table_key}_v01",
        )

    with download_2:
        st.download_button(
            "Descargar Excel",
            data=dataframe_to_excel_bytes(
                searched,
                label,
            ),
            file_name=f"{base_name}_{timestamp}.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            key=f"view_excel_{table_key}_v01",
        )


def render_validation(
    data: dict[str, Any],
) -> None:
    flow = get_dataframe(data, "flujo")
    cecos = get_dataframe(data, "dic_ceco")
    users = get_dataframe(data, "dic_users")

    if flow.empty:
        st.info("No hay flujo reconstruido para validar.")
        return

    known_cecos = (
        set(cecos["CECO"].map(clean_text))
        if "CECO" in cecos.columns
        else set()
    )
    flow_cecos = (
        set(flow["CECO"].map(clean_text))
        if "CECO" in flow.columns
        else set()
    )
    missing_cecos = sorted(flow_cecos - known_cecos)

    known_users = (
        {
            clean_text(value).casefold()
            for value in users["Correo"].tolist()
            if clean_text(value)
        }
        if "Correo" in users.columns
        else set()
    )

    lib_columns = [
        column
        for column in ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]
        if column in flow.columns
    ]
    flow_users = {
        clean_text(value).casefold()
        for column in lib_columns
        for value in flow[column].tolist()
        if clean_text(value)
        and clean_text(value) != "Liberador Servicios"
    }
    missing_users = sorted(flow_users - known_users)

    metrics = st.columns(4)
    metrics[0].metric("CECO en flujo", len(flow_cecos))
    metrics[1].metric("CECO faltantes", len(missing_cecos))
    metrics[2].metric("Usuarios en flujo", len(flow_users))
    metrics[3].metric("Usuarios faltantes", len(missing_users))

    if missing_cecos:
        with st.expander(
            f"CECO sin diccionario · {len(missing_cecos)}",
            expanded=False,
        ):
            st.dataframe(
                pd.DataFrame({"CECO": missing_cecos}),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.success("Todos los CECO existen en el diccionario.")

    if missing_users:
        with st.expander(
            f"Usuarios sin diccionario · {len(missing_users)}",
            expanded=False,
        ):
            st.dataframe(
                pd.DataFrame({"Correo": missing_users}),
                use_container_width=True,
                hide_index=True,
            )
    else:
        st.success(
            "Todos los liberadores existen en el diccionario de usuarios."
        )


def render_no_file() -> None:
    st.info(
        "No hay una versión activa. Carga los archivos desde "
        "**01 Cargar Versión**."
    )

    try:
        if st.button(
            "Ir a 01 Cargar Versión",
            type="primary",
            use_container_width=True,
        ):
            st.switch_page("01_CARGAR_ARCHIVO_FLUJO.py")
    except Exception:
        pass


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    aplicar_estilos()
    render_header()

    data = st.session_state.get(SESSION_DATA_KEY)
    file_names = st.session_state.get(SESSION_FILE_KEY, {})

    if not isinstance(data, dict):
        render_no_file()
        return

    if not isinstance(file_names, dict):
        file_names = {}

    render_summary(data, file_names)
    st.divider()

    available_keys = [
        key
        for key in TABLE_CONFIG
        if not get_dataframe(data, key).empty
    ]

    tab_labels = [
        TABLE_CONFIG[key]["label"]
        for key in available_keys
    ]
    tab_labels.append("Validación")

    tabs = st.tabs(tab_labels)

    for tab, table_key in zip(
        tabs[:len(available_keys)],
        available_keys,
    ):
        with tab:
            config = TABLE_CONFIG[table_key]
            role = config["file_role"]
            source_name = (
                clean_text(file_names.get(role, ""))
                if role
                else "Flujo reconstruido"
            )
            render_table_view(
                table_key,
                get_dataframe(data, table_key),
                source_name,
            )

    with tabs[-1]:
        render_validation(data)


if __name__ == "__main__":
    main()
