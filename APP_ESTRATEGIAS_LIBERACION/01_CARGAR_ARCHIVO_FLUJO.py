# ============================================================
# 01_CARGAR_ARCHIVO_FLUJO
# APP_ESTRATEGIAS_LIBERACION
#
# Carga, normaliza y valida el archivo Excel de flujo.
#
# Formato maestro de la hoja Flujo:
# CECO | Planta | Desde | Hasta | TipoDoc |
# Lib1 | Lib2 | Lib3 | Lib4 | Lib5
#
# También acepta archivos antiguos y elimina durante la carga:
# Descripcion, Fuente, FuenteCD, N_EO, N_CD y Match.
# ============================================================

from __future__ import annotations

import base64
import hashlib
import re
from io import BytesIO
from pathlib import Path
from textwrap import dedent
from typing import Any

import pandas as pd
import streamlit as st


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

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

FLOW_COLUMNS = [
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
]

FLOW_KEY_COLUMNS = ["CECO", "Desde", "Hasta", "TipoDoc"]
LIB_COLS = ["Lib1", "Lib2", "Lib3", "Lib4", "Lib5"]

DEPRECATED_COLUMNS = [
    "Descripcion",
    "Descripción",
    "Fuente",
    "FuenteCD",
    "N_EO",
    "N_CD",
    "Match",
]

USER_COLUMNS = ["Correo", "Cargo"]
CECO_COLUMNS = ["CECO", "Planta", "Centro"]
RANGE_COLUMNS = ["Orden", "Desde", "Hasta"]

DOC_LABEL = {
    "AZNB": "Material (AZNB)",
    "AZSR": "Servicio (AZSR)",
}

LS_LABEL = "Liberador Servicios"

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_CASE_KEY = "flujo_liberacion_last_case"
SESSION_FILE_BYTES_KEY = "flujo_liberacion_file_bytes"
SESSION_SIGNATURE_KEY = "flujo_liberacion_upload_signature_v02"
SESSION_VALIDATION_KEY = "flujo_liberacion_validation_v02"


# ============================================================
# ESTILOS
# ============================================================

def compact_html(value: str) -> str:
    return re.sub(r">\s+<", "><", dedent(value).strip())


def aplicar_estilos() -> None:
    st.markdown(
        """
        <style>
            .stMainBlockContainer,
            .block-container {
                padding-top: 6.5rem !important;
                padding-bottom: 2.5rem !important;
            }

            .fl-logo-wrap {
                width: 100%;
                min-height: 90px;
                display: flex;
                justify-content: center;
                align-items: center;
                margin: .6rem 0 12px;
                overflow: visible;
            }

            .fl-logo-wrap img {
                width: 220px;
                max-width: min(60vw, 220px);
                max-height: 88px;
                object-fit: contain;
                display: block;
            }

            .fl-title {
                text-align: center;
                color: #17365D;
                font-size: 2rem;
                font-weight: 850;
                margin: .2rem 0;
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
                font-weight: 850;
                margin: .4rem 0 .6rem;
            }

            .fl-help {
                color: #64748B;
                font-size: .9rem;
                margin-bottom: .8rem;
            }

            .format-card {
                border: 1px solid #BFDBFE;
                border-radius: 14px;
                background: #EFF6FF;
                padding: 14px 16px;
                margin: .6rem 0 1rem;
            }

            .format-title {
                color: #17365D;
                font-weight: 850;
                margin-bottom: 6px;
            }

            .format-columns {
                color: #334155;
                font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
                font-size: .86rem;
                overflow-wrap: anywhere;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LOGO
# ============================================================

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
        if path.suffix.lower() == ".svg":
            raw = path.read_text(encoding="utf-8").encode("utf-8")
            mime = "image/svg+xml"
        else:
            raw = path.read_bytes()
            mime = (
                "image/png"
                if path.suffix.lower() == ".png"
                else "image/jpeg"
            )

        encoded = base64.b64encode(raw).decode("utf-8")

        st.markdown(
            compact_html(
                f"""
                <div class="fl-logo-wrap">
                    <img
                        src="data:{mime};base64,{encoded}"
                        alt="Logo ENAEX"
                    >
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

    except (OSError, UnicodeError) as error:
        st.warning(f"No fue posible leer el logo: {error}")


# ============================================================
# LIMPIEZA Y NORMALIZACIÓN
# ============================================================

def clean_text(value: Any) -> str:
    """Convierte valores nulos o marcadores vacíos en cadena vacía."""
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    text = str(value).strip()

    if text.lower() in {
        "",
        "nan",
        "none",
        "null",
        "<na>",
        "n/a",
        "no usar",
        "—",
        "-",
    }:
        return ""

    return text


def strip_user_email(value: Any) -> str:
    """Retira un cargo entre paréntesis y conserva el correo o etiqueta."""
    text = clean_text(value)

    if not text or text == LS_LABEL:
        return text

    match = re.match(r"^(.*?)(?:\s+\([^)]+\))?$", text)
    return match.group(1).strip() if match else text


def parse_bound(value: Any, low: bool = True) -> float:
    """Interpreta límites escritos con separadores de miles o decimales."""
    text = clean_text(value)

    if text in {"", "*"}:
        return 0.0 if low else 1e18

    normalized = text.replace(" ", "")

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
    except ValueError as error:
        raise ValueError(f"Valor de rango no válido: {value!r}") from error


def compact_liberators(row: pd.Series) -> list[str]:
    """Compacta Lib1–Lib5 hacia la izquierda y elimina duplicados."""
    result: list[str] = []
    seen: set[str] = set()

    for column in LIB_COLS:
        value = strip_user_email(row.get(column, ""))
        key = value.casefold()

        if not value or key in seen:
            continue

        seen.add(key)
        result.append(value)

    return (result + [""] * 5)[:5]


def normalize_flow_dataframe(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Normaliza la hoja Flujo al formato maestro.

    Los archivos antiguos son admitidos siempre que contengan las columnas
    funcionales mínimas. Las columnas obsoletas se eliminan de la estructura.
    """
    flow = dataframe.copy()
    flow.columns = [str(column).strip() for column in flow.columns]

    missing = [
        column
        for column in FLOW_COLUMNS
        if column not in flow.columns
    ]

    if missing:
        raise ValueError(
            "La hoja 'Flujo' no contiene todas las columnas obligatorias. "
            f"Faltan: {', '.join(missing)}."
        )

    legacy_found = [
        column
        for column in DEPRECATED_COLUMNS
        if column in flow.columns
    ]

    flow = flow.loc[:, FLOW_COLUMNS].copy()

    flow["CECO"] = flow["CECO"].map(clean_text)
    flow["Planta"] = flow["Planta"].map(clean_text)
    flow["TipoDoc"] = flow["TipoDoc"].map(clean_text).str.upper()

    for column in LIB_COLS:
        flow[column] = flow[column].map(strip_user_email)

    initial_rows = len(flow)

    flow = flow[
        flow["CECO"].ne("")
        & flow["TipoDoc"].isin(DOC_LABEL)
    ].copy()

    discarded_rows = initial_rows - len(flow)

    normalized_ranges: list[tuple[float, float]] = []
    empty_liberator_rows: list[int] = []
    compacted_rows = 0
    duplicate_liberators_removed = 0

    for index, row in flow.iterrows():
        try:
            low = parse_bound(row["Desde"], low=True)
            high = parse_bound(row["Hasta"], low=False)
        except ValueError as error:
            raise ValueError(
                f"Error de rango en la fila Excel {index + 2}: {error}"
            ) from error

        if low > high:
            raise ValueError(
                f"Rango inválido en la fila Excel {index + 2}: "
                "Desde es mayor que Hasta."
            )

        normalized_ranges.append((low, high))

        original_values = [
            strip_user_email(row.get(column, ""))
            for column in LIB_COLS
        ]
        compacted_values = compact_liberators(row)

        original_non_empty = [
            value
            for value in original_values
            if value
        ]
        compacted_non_empty = [
            value
            for value in compacted_values
            if value
        ]

        duplicate_liberators_removed += (
            len(original_non_empty) - len(compacted_non_empty)
        )

        if original_values != compacted_values:
            compacted_rows += 1

        for column, value in zip(LIB_COLS, compacted_values):
            flow.at[index, column] = value

        if not compacted_non_empty:
            empty_liberator_rows.append(index + 2)

    if flow.empty:
        raise ValueError(
            "La hoja 'Flujo' no contiene registros válidos AZNB/AZSR."
        )

    flow["Desde"] = [low for low, _ in normalized_ranges]
    flow["Hasta"] = [high for _, high in normalized_ranges]

    for column in ["Desde", "Hasta"]:
        flow[column] = flow[column].map(
            lambda number: (
                int(number)
                if float(number).is_integer()
                else float(number)
            )
        )

    duplicate_mask = flow.duplicated(
        subset=FLOW_KEY_COLUMNS,
        keep=False,
    )
    duplicate_rows = int(duplicate_mask.sum())

    overlaps = detect_overlaps(flow)

    flow = (
        flow.sort_values(
            ["CECO", "TipoDoc", "Desde", "Hasta"],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    report = {
        "legacy_columns": legacy_found,
        "discarded_rows": discarded_rows,
        "compacted_rows": compacted_rows,
        "duplicate_liberators_removed": duplicate_liberators_removed,
        "empty_liberator_rows": empty_liberator_rows,
        "duplicate_rule_rows": duplicate_rows,
        "overlaps": overlaps,
    }

    return flow, report


def detect_overlaps(flow: pd.DataFrame) -> pd.DataFrame:
    """Detecta rangos superpuestos dentro de cada CECO y TipoDoc."""
    records: list[dict[str, Any]] = []

    for (ceco, doc), group in flow.groupby(
        ["CECO", "TipoDoc"],
        sort=False,
    ):
        ordered = group.sort_values(
            ["Desde", "Hasta"],
            kind="stable",
        )

        previous_index: int | None = None
        previous_until: float | None = None
        previous_from: float | None = None

        for index, row in ordered.iterrows():
            current_from = float(row["Desde"])
            current_until = float(row["Hasta"])

            if (
                previous_until is not None
                and current_from <= previous_until
            ):
                records.append(
                    {
                        "CECO": ceco,
                        "TipoDoc": doc,
                        "FilaAnterior": (
                            int(previous_index) + 2
                            if previous_index is not None
                            else ""
                        ),
                        "DesdeAnterior": previous_from,
                        "HastaAnterior": previous_until,
                        "FilaActual": int(index) + 2,
                        "DesdeActual": current_from,
                        "HastaActual": current_until,
                    }
                )

            if previous_until is None or current_until > previous_until:
                previous_index = int(index)
                previous_from = current_from
                previous_until = current_until

    return pd.DataFrame(records)


def normalize_users_dataframe(
    dataframe: pd.DataFrame | None,
) -> pd.DataFrame:
    if dataframe is None:
        return pd.DataFrame(columns=USER_COLUMNS)

    users = dataframe.copy()
    users.columns = [str(column).strip() for column in users.columns]

    for column in USER_COLUMNS:
        if column not in users.columns:
            users[column] = ""

    users = users.loc[:, USER_COLUMNS].copy()
    users["Correo"] = users["Correo"].map(strip_user_email)
    users["Cargo"] = users["Cargo"].map(clean_text)

    return (
        users[users["Correo"].ne("")]
        .drop_duplicates("Correo", keep="last")
        .reset_index(drop=True)
    )


def normalize_ceco_dataframe(
    dataframe: pd.DataFrame | None,
) -> pd.DataFrame:
    if dataframe is None:
        return pd.DataFrame(columns=CECO_COLUMNS)

    cecos = dataframe.copy()
    cecos.columns = [str(column).strip() for column in cecos.columns]

    for column in CECO_COLUMNS:
        if column not in cecos.columns:
            cecos[column] = ""

    cecos = cecos.loc[:, CECO_COLUMNS].copy()

    for column in CECO_COLUMNS:
        cecos[column] = cecos[column].map(clean_text)

    return (
        cecos[cecos["CECO"].ne("")]
        .drop_duplicates("CECO", keep="last")
        .reset_index(drop=True)
    )


def normalize_ranges_dataframe(
    dataframe: pd.DataFrame | None,
) -> pd.DataFrame:
    if dataframe is None:
        return pd.DataFrame(columns=RANGE_COLUMNS)

    ranges = dataframe.copy()
    ranges.columns = [str(column).strip() for column in ranges.columns]

    for column in RANGE_COLUMNS:
        if column not in ranges.columns:
            ranges[column] = ""

    ranges = ranges.loc[:, RANGE_COLUMNS].copy()

    for column in ["Orden", "Desde", "Hasta"]:
        ranges[column] = pd.to_numeric(
            ranges[column],
            errors="coerce",
        )

    ranges = ranges.dropna(
        subset=["Desde", "Hasta"],
        how="all",
    )

    return ranges.reset_index(drop=True)


# ============================================================
# LECTURA DEL EXCEL
# ============================================================

def read_optional_sheet(
    excel_file: pd.ExcelFile,
    candidates: list[str],
) -> pd.DataFrame | None:
    """Lee la primera hoja cuyo nombre coincida con los candidatos."""
    sheet_by_lower = {
        name.strip().lower(): name
        for name in excel_file.sheet_names
    }

    for candidate in candidates:
        real_name = sheet_by_lower.get(candidate.strip().lower())

        if real_name:
            return pd.read_excel(
                excel_file,
                sheet_name=real_name,
            )

    return None


def load_workbook(
    uploaded_file: Any,
) -> tuple[dict[str, pd.DataFrame], bytes, dict[str, Any]]:
    raw_bytes = uploaded_file.getvalue()

    if not raw_bytes:
        raise ValueError("El archivo cargado está vacío.")

    try:
        excel_file = pd.ExcelFile(BytesIO(raw_bytes))
    except Exception as error:
        raise ValueError(
            "No fue posible abrir el archivo. "
            "Verifica que sea un Excel válido."
        ) from error

    sheet_by_lower = {
        name.strip().lower(): name
        for name in excel_file.sheet_names
    }
    flow_sheet_name = sheet_by_lower.get("flujo")

    if not flow_sheet_name:
        raise ValueError(
            "El archivo debe contener una hoja llamada 'Flujo'."
        )

    try:
        flow_raw = pd.read_excel(
            excel_file,
            sheet_name=flow_sheet_name,
        )
        users_raw = read_optional_sheet(
            excel_file,
            ["Dic_Usuarios", "Usuarios", "USUARIOS"],
        )
        cecos_raw = read_optional_sheet(
            excel_file,
            ["Dic_CECO", "Dic_CECOS", "CECOS", "CECO"],
        )
        ranges_raw = read_optional_sheet(
            excel_file,
            ["Dic_Rangos", "Rangos", "RANGOS"],
        )
    except Exception as error:
        raise ValueError(
            "No fue posible leer las hojas del archivo Excel."
        ) from error

    flow, validation = normalize_flow_dataframe(flow_raw)

    data = {
        "flujo": flow,
        "dic_users": normalize_users_dataframe(users_raw),
        "dic_ceco": normalize_ceco_dataframe(cecos_raw),
        "dic_rangos": normalize_ranges_dataframe(ranges_raw),
    }

    validation["sheet_names"] = list(excel_file.sheet_names)

    return data, raw_bytes, validation


# ============================================================
# ESTADO
# ============================================================

def file_signature(name: str, raw_bytes: bytes) -> str:
    digest = hashlib.sha1(raw_bytes).hexdigest()
    return f"{name}|{len(raw_bytes)}|{digest}"


def borrar_archivo_activo() -> None:
    for key in [
        SESSION_DATA_KEY,
        SESSION_FILE_KEY,
        SESSION_CASE_KEY,
        SESSION_FILE_BYTES_KEY,
        SESSION_SIGNATURE_KEY,
        SESSION_VALIDATION_KEY,
    ]:
        st.session_state.pop(key, None)


# ============================================================
# INTERFAZ
# ============================================================

def render_header() -> None:
    mostrar_logo()

    st.markdown(
        '<div class="fl-title">01 Cargar Archivo</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="fl-subtitle">
            Carga, normalización y validación de la base de liberación.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_format_help() -> None:
    columns = " | ".join(FLOW_COLUMNS)

    st.markdown(
        compact_html(
            f"""
            <div class="format-card">
                <div class="format-title">
                    Formato vigente de la hoja Flujo
                </div>
                <div class="format-columns">{columns}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    st.caption(
        "Los archivos antiguos también pueden cargarse. "
        "Las columnas Descripcion, Fuente, FuenteCD, N_EO, N_CD "
        "y Match se ignoran automáticamente."
    )


def render_validation_report(report: dict[str, Any]) -> None:
    legacy_columns = report.get("legacy_columns", [])
    discarded_rows = int(report.get("discarded_rows", 0))
    compacted_rows = int(report.get("compacted_rows", 0))
    duplicates_removed = int(
        report.get("duplicate_liberators_removed", 0)
    )
    empty_rows = list(report.get("empty_liberator_rows", []))
    duplicate_rule_rows = int(
        report.get("duplicate_rule_rows", 0)
    )
    overlaps = report.get("overlaps", pd.DataFrame())

    with st.expander("Informe de validación", expanded=False):
        if legacy_columns:
            st.info(
                "Columnas antiguas ignoradas: "
                + ", ".join(legacy_columns)
                + "."
            )

        if discarded_rows:
            st.warning(
                f"Se descartaron {discarded_rows} fila(s) sin CECO válido "
                "o con un TipoDoc distinto de AZNB/AZSR."
            )

        if compacted_rows:
            st.info(
                f"Se compactaron los liberadores en {compacted_rows} fila(s)."
            )

        if duplicates_removed:
            st.warning(
                f"Se eliminaron {duplicates_removed} liberador(es) "
                "duplicado(s) dentro de sus respectivos flujos."
            )

        if empty_rows:
            preview = ", ".join(
                str(number)
                for number in empty_rows[:15]
            )
            suffix = "..." if len(empty_rows) > 15 else ""

            st.warning(
                f"Hay {len(empty_rows)} fila(s) sin liberadores. "
                f"Filas Excel: {preview}{suffix}"
            )

        if duplicate_rule_rows:
            st.error(
                f"Se detectaron {duplicate_rule_rows} fila(s) que repiten "
                "exactamente CECO, TipoDoc, Desde y Hasta."
            )

        if isinstance(overlaps, pd.DataFrame) and not overlaps.empty:
            st.error(
                f"Se detectaron {len(overlaps)} superposición(es) de rangos."
            )
            st.dataframe(
                overlaps,
                use_container_width=True,
                hide_index=True,
            )

        if (
            not legacy_columns
            and not discarded_rows
            and not compacted_rows
            and not duplicates_removed
            and not empty_rows
            and not duplicate_rule_rows
            and (
                not isinstance(overlaps, pd.DataFrame)
                or overlaps.empty
            )
        ):
            st.success(
                "No se encontraron observaciones en la estructura del flujo."
            )


def render_estado() -> None:
    data = st.session_state.get(SESSION_DATA_KEY)

    if not isinstance(data, dict):
        st.info(
            "No hay un archivo activo. Carga el Excel para habilitar "
            "la simulación, modificación y búsqueda."
        )
        return

    flow = data.get("flujo", pd.DataFrame())
    users = data.get("dic_users", pd.DataFrame())
    cecos = data.get("dic_ceco", pd.DataFrame())
    ranges = data.get("dic_rangos", pd.DataFrame())

    if not isinstance(flow, pd.DataFrame) or flow.empty:
        st.warning("El archivo activo no contiene un flujo válido.")
        return

    file_name = st.session_state.get(
        SESSION_FILE_KEY,
        "Archivo cargado",
    )

    rows_without_liberators = int(
        flow[LIB_COLS]
        .apply(
            lambda row: not any(clean_text(value) for value in row),
            axis=1,
        )
        .sum()
    )
    total_liberators = int(
        flow[LIB_COLS]
        .map(lambda value: bool(clean_text(value)))
        .sum()
        .sum()
    )

    st.success(
        (
            f"Archivo activo: **{file_name}** · "
            f"**{len(flow):,} reglas** · "
            f"**{flow['CECO'].nunique():,} CECO**"
        ).replace(",", ".")
    )

    metric_columns = st.columns(4)
    metrics = [
        ("Reglas", len(flow)),
        ("CECO", flow["CECO"].nunique()),
        ("Liberadores asignados", total_liberators),
        ("Reglas sin liberadores", rows_without_liberators),
    ]

    for column, (label, value) in zip(metric_columns, metrics):
        column.metric(
            label,
            f"{int(value):,}".replace(",", "."),
        )

    report = st.session_state.get(
        SESSION_VALIDATION_KEY,
        {},
    )
    if isinstance(report, dict):
        render_validation_report(report)

    with st.expander(
        "Vista previa de la hoja Flujo",
        expanded=False,
    ):
        st.dataframe(
            flow.head(100),
            use_container_width=True,
            hide_index=True,
        )

    with st.expander(
        "Diccionarios disponibles",
        expanded=False,
    ):
        tabs = st.tabs(
            [
                f"Usuarios ({len(users)})",
                f"CECO ({len(cecos)})",
                f"Rangos ({len(ranges)})",
            ]
        )

        with tabs[0]:
            if users.empty:
                st.info("No se encontraron usuarios válidos.")
            else:
                st.dataframe(
                    users.head(100),
                    use_container_width=True,
                    hide_index=True,
                )

        with tabs[1]:
            if cecos.empty:
                st.info("No se encontró el diccionario de CECO.")
            else:
                st.dataframe(
                    cecos.head(100),
                    use_container_width=True,
                    hide_index=True,
                )

        with tabs[2]:
            if ranges.empty:
                st.info("No se encontró el diccionario de rangos.")
            else:
                st.dataframe(
                    ranges,
                    use_container_width=True,
                    hide_index=True,
                )

    download_column, remove_column = st.columns(2)

    with download_column:
        st.download_button(
            "⬇️ Descargar archivo activo",
            data=st.session_state.get(
                SESSION_FILE_BYTES_KEY,
                b"",
            ),
            file_name=file_name,
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
            disabled=not bool(
                st.session_state.get(
                    SESSION_FILE_BYTES_KEY
                )
            ),
        )

    with remove_column:
        if st.button(
            "🗑️ Quitar archivo activo",
            use_container_width=True,
        ):
            borrar_archivo_activo()
            st.rerun()


def main() -> None:
    aplicar_estilos()
    render_header()

    st.markdown(
        '<div class="fl-section-title">'
        '1. Seleccionar archivo Excel'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="fl-help">
            La hoja <b>Flujo</b> es obligatoria.
            <b>Dic_Usuarios</b>, <b>Dic_CECO</b> y
            <b>Dic_Rangos</b> son opcionales.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_format_help()

    uploaded_file = st.file_uploader(
        "Archivo Excel",
        type=["xlsx", "xls"],
        accept_multiple_files=False,
        key="flujo_liberacion_uploader_v02",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        raw_bytes = uploaded_file.getvalue()
        signature = file_signature(
            uploaded_file.name,
            raw_bytes,
        )

        needs_load = (
            st.session_state.get(SESSION_SIGNATURE_KEY)
            != signature
            or SESSION_DATA_KEY not in st.session_state
        )

        if needs_load:
            try:
                with st.spinner(
                    "Leyendo, normalizando y validando archivo..."
                ):
                    data, stored_bytes, validation = load_workbook(
                        uploaded_file
                    )

                st.session_state[SESSION_DATA_KEY] = data
                st.session_state[SESSION_FILE_KEY] = uploaded_file.name
                st.session_state[SESSION_FILE_BYTES_KEY] = stored_bytes
                st.session_state[SESSION_SIGNATURE_KEY] = signature
                st.session_state[SESSION_VALIDATION_KEY] = validation
                st.session_state.pop(SESSION_CASE_KEY, None)

                st.toast(
                    "Archivo cargado correctamente.",
                    icon="✅",
                )

            except ValueError as error:
                borrar_archivo_activo()
                st.error(str(error))

    st.markdown("---")
    st.markdown(
        '<div class="fl-section-title">2. Archivo activo</div>',
        unsafe_allow_html=True,
    )

    render_estado()


if __name__ == "__main__":
    main()
