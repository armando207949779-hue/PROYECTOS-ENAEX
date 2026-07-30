
# ============================================================
# 01_CARGAR_ARCHIVO_FLUJO
# APP_ESTRATEGIAS_LIBERACION
#
# NUEVO FORMATO ÚNICO:
#   5 archivos independientes: Liberador 1, 2, 3, 4 y 5.
#   Cada archivo puede ser CSV, Parquet o Excel.
#
# La aplicación:
#   1. valida cada nivel;
#   2. conserva todas las reglas originales, incluidos * y V;
#   3. reconstruye una tabla interna:
#      CECO | Planta | Desde | Hasta | TipoDoc |
#      Lib1 | Lib2 | Lib3 | Lib4 | Lib5
#   4. deja los 5 DataFrame originales en session_state.
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

LEVELS = (1, 2, 3, 4, 5)

BASE_RULE_COLUMNS = [
    "CompanyCode",
    "BillingAddress",
    "AccountCategory",
    "CostCenter",
    "cus_POClasedeDocumento",
    "PurchaseGroup",
    "TotalCost Bajo",
    "TotalCost Alto",
]

COMMON_COLUMNS = [
    *BASE_RULE_COLUMNS,
    "User",
    "Required",
    "Tooltip",
]

GROUP_COLUMNS = [
    *BASE_RULE_COLUMNS,
    "Group",
    "User",
    "Required",
    "Tooltip",
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

DOC_TYPES = {"AZNB", "AZSR"}
LS_LABEL = "Liberador Servicios"
LS_GROUP_VALUES = {
    "liberacion servicios",
    "liberación servicios",
    "liberador servicios",
}

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_CASE_KEY = "flujo_liberacion_last_case"
SESSION_FILE_BYTES_KEY = "flujo_liberacion_file_bytes"
SESSION_SIGNATURE_KEY = "flujo_liberacion_upload_signature_v03"
SESSION_VALIDATION_KEY = "flujo_liberacion_validation_v03"
SESSION_SOURCE_FILES_KEY = "flujo_liberacion_source_files_v03"


# ============================================================
# ESTILOS Y LOGO
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
            }

            .fl-logo-wrap img {
                width: 220px;
                max-width: min(60vw, 220px);
                max-height: 88px;
                object-fit: contain;
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
                font-size: .82rem;
                overflow-wrap: anywhere;
            }

            .level-card {
                border: 1px solid #E2E8F0;
                border-radius: 12px;
                padding: 12px;
                background: #FFFFFF;
                min-height: 105px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def buscar_logo() -> Path | None:
    return next(
        (path for path in LOGO_CANDIDATES if path.exists() and path.is_file()),
        None,
    )


def mostrar_logo() -> None:
    path = buscar_logo()
    if path is None:
        return

    try:
        raw = path.read_bytes()
        if path.suffix.lower() == ".svg":
            mime = "image/svg+xml"
        elif path.suffix.lower() == ".png":
            mime = "image/png"
        else:
            mime = "image/jpeg"

        encoded = base64.b64encode(raw).decode("utf-8")
        st.markdown(
            f'<div class="fl-logo-wrap"><img src="data:{mime};base64,{encoded}" '
            'alt="Logo ENAEX"></div>',
            unsafe_allow_html=True,
        )
    except (OSError, UnicodeError):
        pass


# ============================================================
# LIMPIEZA
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
    return "" if text.lower() in {
        "", "nan", "none", "null", "<na>", "n/a", "—", "-"
    } else text


def normalized_key(value: Any) -> str:
    return clean_text(value).casefold()


def normalize_column_name(value: Any) -> str:
    text = clean_text(value)
    text = re.sub(r"\s+", " ", text)
    return text


def parse_bound(value: Any, *, low: bool) -> float:
    text = clean_text(value)

    if text in {"", "*"}:
        return 1.0 if low else 1e18

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
        raise ValueError(f"Límite no válido: {value!r}") from error


def normalize_required(value: Any) -> str:
    text = normalized_key(value)
    if text in {"true", "verdadero", "1", "sí", "si", "x"}:
        return "TRUE"
    if text in {"false", "falso", "0", "no"}:
        return "FALSE"
    return clean_text(value) or "TRUE"


def liberator_from_row(row: pd.Series) -> str:
    group = clean_text(row.get("Group", ""))
    user = clean_text(row.get("User", ""))

    if normalized_key(group) in LS_GROUP_VALUES:
        return LS_LABEL

    return user


# ============================================================
# LECTURA DE CSV / PARQUET / EXCEL
# ============================================================

def read_csv_flexible(raw: bytes) -> pd.DataFrame:
    attempts = [
        {"sep": None, "engine": "python", "encoding": "utf-8-sig"},
        {"sep": ";", "encoding": "utf-8-sig"},
        {"sep": ",", "encoding": "utf-8-sig"},
        {"sep": "\t", "encoding": "utf-8-sig"},
        {"sep": None, "engine": "python", "encoding": "latin-1"},
    ]

    last_error: Exception | None = None

    for options in attempts:
        try:
            frame = pd.read_csv(BytesIO(raw), dtype=object, **options)
            if len(frame.columns) >= 2:
                return frame
        except Exception as error:
            last_error = error

    raise ValueError("No fue posible interpretar el CSV.") from last_error


def read_uploaded_table(uploaded_file: Any) -> tuple[pd.DataFrame, bytes]:
    raw = uploaded_file.getvalue()
    if not raw:
        raise ValueError("El archivo está vacío.")

    suffix = Path(uploaded_file.name).suffix.lower()

    try:
        if suffix == ".csv":
            frame = read_csv_flexible(raw)
        elif suffix in {".parquet", ".pq"}:
            frame = pd.read_parquet(BytesIO(raw))
        elif suffix in {".xlsx", ".xls", ".xlsm"}:
            frame = pd.read_excel(BytesIO(raw), dtype=object)
        else:
            raise ValueError(
                "Formato no admitido. Usa CSV, Parquet, XLSX, XLS o XLSM."
            )
    except ValueError:
        raise
    except Exception as error:
        raise ValueError(
            f"No fue posible leer {uploaded_file.name}."
        ) from error

    frame.columns = [normalize_column_name(column) for column in frame.columns]
    frame = frame.dropna(axis=0, how="all").dropna(axis=1, how="all")

    return frame, raw


# ============================================================
# VALIDACIÓN POR NIVEL
# ============================================================

def expected_columns_for_level(level: int) -> list[str]:
    # Group es opcional en cualquier nivel.
    return COMMON_COLUMNS


def normalize_level_dataframe(
    dataframe: pd.DataFrame,
    level: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = dataframe.copy()
    frame.columns = [normalize_column_name(column) for column in frame.columns]

    required = expected_columns_for_level(level)
    missing = [column for column in required if column not in frame.columns]

    if missing:
        raise ValueError(
            f"Liberador {level}: faltan columnas obligatorias: "
            + ", ".join(missing)
        )

    if "Group" not in frame.columns:
        frame.insert(
            frame.columns.get_loc("User"),
            "Group",
            "",
        )

    frame = frame.loc[:, GROUP_COLUMNS].copy()

    for column in GROUP_COLUMNS:
        frame[column] = frame[column].map(clean_text)

    frame["Required"] = frame["Required"].map(normalize_required)

    invalid_ranges: list[dict[str, Any]] = []
    empty_approver_rows: list[int] = []

    lows: list[float] = []
    highs: list[float] = []

    for index, row in frame.iterrows():
        excel_row = int(index) + 2

        try:
            low = parse_bound(row["TotalCost Bajo"], low=True)
            high = parse_bound(row["TotalCost Alto"], low=False)
        except ValueError as error:
            invalid_ranges.append({
                "Nivel": level,
                "Fila": excel_row,
                "Detalle": str(error),
            })
            low, high = 1.0, 1e18

        if low > high:
            invalid_ranges.append({
                "Nivel": level,
                "Fila": excel_row,
                "Detalle": "TotalCost Bajo es mayor que TotalCost Alto.",
            })

        lows.append(low)
        highs.append(high)

        if not liberator_from_row(row):
            empty_approver_rows.append(excel_row)

    if invalid_ranges:
        preview = "; ".join(
            f"fila {item['Fila']}: {item['Detalle']}"
            for item in invalid_ranges[:8]
        )
        raise ValueError(f"Liberador {level}: rangos inválidos. {preview}")

    frame["_DesdeNum"] = lows
    frame["_HastaNum"] = highs
    frame["_Nivel"] = level
    frame["_Liberador"] = frame.apply(liberator_from_row, axis=1)

    explicit_mask = (
        frame["CostCenter"].ne("")
        & frame["CostCenter"].ne("*")
        & frame["cus_POClasedeDocumento"].isin(DOC_TYPES)
    )

    duplicate_columns = [
        *BASE_RULE_COLUMNS,
        "Group",
        "User",
    ]
    duplicate_rows = int(
        frame.duplicated(subset=duplicate_columns, keep=False).sum()
    )

    report = {
        "level": level,
        "rows": len(frame),
        "explicit_rows": int(explicit_mask.sum()),
        "special_rows": int((~explicit_mask).sum()),
        "empty_approver_rows": empty_approver_rows,
        "duplicate_rows": duplicate_rows,
        "service_group_rows": int(
            frame["Group"].map(normalized_key).isin(LS_GROUP_VALUES).sum()
        ),
    }

    return frame.reset_index(drop=True), report


# ============================================================
# RECONSTRUCCIÓN DEL FLUJO INTERNO
# ============================================================

def company_from_ceco(ceco: str) -> str:
    match = re.match(r"^(EC\d{2})", clean_text(ceco).upper())
    return match.group(1) if match else ""


def canonical_rule_key(row: pd.Series) -> tuple[str, str, float, float]:
    return (
        clean_text(row["CostCenter"]),
        clean_text(row["cus_POClasedeDocumento"]).upper(),
        float(row["_DesdeNum"]),
        float(row["_HastaNum"]),
    )


def display_bound(value: float, *, high: bool) -> int | float:
    if high and value >= 1e17:
        return 999_999_999_999

    if float(value).is_integer():
        return int(value)

    return float(value)


def reconstruct_flow(
    level_frames: dict[int, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rule_keys: set[tuple[str, str, float, float]] = set()

    explicit_by_level: dict[int, pd.DataFrame] = {}

    for level, frame in level_frames.items():
        explicit = frame[
            frame["CostCenter"].ne("")
            & frame["CostCenter"].ne("*")
            & frame["cus_POClasedeDocumento"].isin(DOC_TYPES)
        ].copy()

        explicit_by_level[level] = explicit

        for _, row in explicit.iterrows():
            rule_keys.add(canonical_rule_key(row))

    records: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []

    for ceco, doc, low, high in sorted(rule_keys):
        record: dict[str, Any] = {
            "CECO": ceco,
            "Planta": "",
            "Desde": display_bound(low, high=False),
            "Hasta": display_bound(high, high=True),
            "TipoDoc": doc,
            "Lib1": "",
            "Lib2": "",
            "Lib3": "",
            "Lib4": "",
            "Lib5": "",
        }

        expected_company = company_from_ceco(ceco)

        for level in LEVELS:
            level_rows = explicit_by_level[level]
            matches = level_rows[
                level_rows["CostCenter"].eq(ceco)
                & level_rows["cus_POClasedeDocumento"].eq(doc)
                & level_rows["_DesdeNum"].eq(low)
                & level_rows["_HastaNum"].eq(high)
            ].copy()

            if expected_company:
                preferred = matches[
                    matches["CompanyCode"].isin({expected_company, "*", ""})
                ]
                if not preferred.empty:
                    matches = preferred

            values = [
                value
                for value in matches["_Liberador"].map(clean_text).tolist()
                if value
            ]

            unique_values = list(dict.fromkeys(values))

            if len(unique_values) == 1:
                record[f"Lib{level}"] = unique_values[0]
            elif len(unique_values) > 1:
                conflicts.append({
                    "CECO": ceco,
                    "TipoDoc": doc,
                    "Desde": display_bound(low, high=False),
                    "Hasta": display_bound(high, high=True),
                    "Nivel": level,
                    "Liberadores": " | ".join(unique_values),
                })
                record[f"Lib{level}"] = unique_values[0]

        records.append(record)

    flow = pd.DataFrame(records, columns=FLOW_COLUMNS)

    if not flow.empty:
        flow = (
            flow.sort_values(
                ["CECO", "TipoDoc", "Desde", "Hasta"],
                kind="stable",
            )
            .reset_index(drop=True)
        )

    duplicate_rule_rows = int(
        flow.duplicated(subset=FLOW_KEY_COLUMNS, keep=False).sum()
    )

    empty_flow_rows = (
        flow[LIB_COLS]
        .apply(lambda row: not any(clean_text(value) for value in row), axis=1)
        .sum()
        if not flow.empty
        else 0
    )

    report = {
        "conflicts": pd.DataFrame(conflicts),
        "duplicate_rule_rows": duplicate_rule_rows,
        "empty_flow_rows": int(empty_flow_rows),
        "rule_count": len(flow),
        "ceco_count": int(flow["CECO"].nunique()) if not flow.empty else 0,
    }

    return flow, report


# ============================================================
# FIRMA, ESTADO Y CARGA
# ============================================================

def files_signature(files: dict[int, Any]) -> str:
    parts: list[str] = []

    for level in LEVELS:
        uploaded = files[level]
        raw = uploaded.getvalue()
        digest = hashlib.sha1(raw).hexdigest()
        parts.append(
            f"{level}|{uploaded.name}|{len(raw)}|{digest}"
        )

    return "||".join(parts)


def clear_active_files() -> None:
    for key in [
        SESSION_DATA_KEY,
        SESSION_FILE_KEY,
        SESSION_CASE_KEY,
        SESSION_FILE_BYTES_KEY,
        SESSION_SIGNATURE_KEY,
        SESSION_VALIDATION_KEY,
        SESSION_SOURCE_FILES_KEY,
    ]:
        st.session_state.pop(key, None)


def load_five_files(
    uploaded_files: dict[int, Any],
) -> tuple[dict[str, Any], dict[str, bytes], dict[str, Any]]:
    level_frames: dict[int, pd.DataFrame] = {}
    level_reports: dict[int, dict[str, Any]] = {}
    source_bytes: dict[str, bytes] = {}

    for level in LEVELS:
        frame_raw, raw = read_uploaded_table(uploaded_files[level])
        frame, report = normalize_level_dataframe(frame_raw, level)

        level_frames[level] = frame
        level_reports[level] = report
        source_bytes[f"liberador_{level}"] = raw

    flow, flow_report = reconstruct_flow(level_frames)

    if flow.empty:
        raise ValueError(
            "Los cinco archivos no contienen reglas con CostCenter explícito "
            "y TipoDoc AZNB/AZSR para construir el flujo."
        )

    data: dict[str, Any] = {
        "flujo": flow,
        "liberadores": level_frames,
        "liberador_1": level_frames[1],
        "liberador_2": level_frames[2],
        "liberador_3": level_frames[3],
        "liberador_4": level_frames[4],
        "liberador_5": level_frames[5],
        # Se mantienen claves conocidas por otras pantallas.
        "dic_users": pd.DataFrame(columns=["Correo", "Cargo"]),
        "dic_ceco": pd.DataFrame(columns=["CECO", "Planta", "Centro"]),
        "dic_rangos": pd.DataFrame(columns=["Orden", "Desde", "Hasta"]),
    }

    validation = {
        "levels": level_reports,
        "flow": flow_report,
    }

    return data, source_bytes, validation


# ============================================================
# INTERFAZ
# ============================================================

def render_header() -> None:
    mostrar_logo()

    st.markdown(
        '<div class="fl-title">01 Cargar Archivos</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="fl-subtitle">
            Carga los cinco niveles oficiales de liberación.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_format_help() -> None:
    columns = " | ".join(GROUP_COLUMNS)

    st.markdown(
        compact_html(
            f"""
            <div class="format-card">
                <div class="format-title">Formato único desde ahora</div>
                <div class="format-columns">{columns}</div>
            </div>
            """
        ),
        unsafe_allow_html=True,
    )

    st.caption(
        "Cada nivel puede cargarse como CSV, Parquet o Excel. "
        "La columna Group puede venir vacía, pero debe existir cuando el archivo "
        "la utiliza para representar Liberacion Servicios."
    )


def render_uploaders() -> dict[int, Any]:
    uploaded: dict[int, Any] = {}

    columns = st.columns(5)

    for level, column in zip(LEVELS, columns):
        with column:
            st.markdown(
                f"""
                <div class="level-card">
                    <b>Liberador {level}</b><br>
                    <small>CSV · Parquet · Excel</small>
                </div>
                """,
                unsafe_allow_html=True,
            )
            uploaded[level] = st.file_uploader(
                f"Archivo Liberador {level}",
                type=["csv", "parquet", "pq", "xlsx", "xls", "xlsm"],
                accept_multiple_files=False,
                key=f"liberador_uploader_v03_{level}",
                label_visibility="collapsed",
            )

    return uploaded


def render_validation_report(report: dict[str, Any]) -> None:
    level_reports = report.get("levels", {})
    flow_report = report.get("flow", {})

    with st.expander("Informe de validación", expanded=False):
        rows = []

        for level in LEVELS:
            item = level_reports.get(level, {})
            rows.append({
                "Nivel": level,
                "Filas": item.get("rows", 0),
                "Reglas CECO": item.get("explicit_rows", 0),
                "Reglas especiales": item.get("special_rows", 0),
                "Grupo Servicios": item.get("service_group_rows", 0),
                "Duplicadas": item.get("duplicate_rows", 0),
                "Sin liberador": len(item.get("empty_approver_rows", [])),
            })

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

        conflicts = flow_report.get("conflicts", pd.DataFrame())

        if isinstance(conflicts, pd.DataFrame) and not conflicts.empty:
            st.error(
                f"Se detectaron {len(conflicts)} conflictos: una misma regla "
                "tiene más de un liberador en el mismo nivel."
            )
            st.dataframe(
                conflicts,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success("No se detectaron conflictos de liberadores.")

        if flow_report.get("duplicate_rule_rows", 0):
            st.error(
                "La tabla interna contiene reglas CECO/TipoDoc/rango duplicadas."
            )

        if flow_report.get("empty_flow_rows", 0):
            st.warning(
                f"Hay {flow_report['empty_flow_rows']} reglas internas "
                "sin ningún liberador."
            )


def render_active_state() -> None:
    data = st.session_state.get(SESSION_DATA_KEY)

    if not isinstance(data, dict):
        st.info("Carga los cinco archivos para activar la aplicación.")
        return

    flow = data.get("flujo", pd.DataFrame())
    liberators = data.get("liberadores", {})

    if not isinstance(flow, pd.DataFrame) or flow.empty:
        st.warning("No existe un flujo interno válido.")
        return

    st.success(
        (
            f"Cinco archivos activos · **{len(flow):,} reglas internas** · "
            f"**{flow['CECO'].nunique():,} CECO**"
        ).replace(",", ".")
    )

    metrics = st.columns(5)
    for level, column in zip(LEVELS, metrics):
        frame = liberators.get(level, pd.DataFrame())
        column.metric(
            f"Liberador {level}",
            f"{len(frame):,}".replace(",", "."),
        )

    report = st.session_state.get(SESSION_VALIDATION_KEY, {})
    if isinstance(report, dict):
        render_validation_report(report)

    with st.expander("Vista previa del flujo reconstruido", expanded=False):
        st.dataframe(
            flow.head(200),
            use_container_width=True,
            hide_index=True,
        )

    tabs = st.tabs([f"Liberador {level}" for level in LEVELS])

    for level, tab in zip(LEVELS, tabs):
        with tab:
            frame = liberators.get(level, pd.DataFrame())
            st.dataframe(
                frame.drop(
                    columns=[
                        "_DesdeNum",
                        "_HastaNum",
                        "_Nivel",
                        "_Liberador",
                    ],
                    errors="ignore",
                ).head(200),
                use_container_width=True,
                hide_index=True,
            )

    if st.button(
        "🗑️ Quitar los cinco archivos",
        use_container_width=True,
    ):
        clear_active_files()
        st.rerun()


def main() -> None:
    aplicar_estilos()
    render_header()

    st.markdown(
        '<div class="fl-section-title">1. Seleccionar los cinco archivos</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="fl-help">
            Los cinco niveles son obligatorios y forman una única versión.
            No se acepta el formato maestro antiguo.
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_format_help()
    uploaded_files = render_uploaders()

    all_present = all(uploaded_files[level] is not None for level in LEVELS)

    if any(uploaded_files.values()) and not all_present:
        missing = [
            str(level)
            for level in LEVELS
            if uploaded_files[level] is None
        ]
        st.warning(
            "Faltan archivos: Liberador " + ", ".join(missing) + "."
        )

    if all_present:
        signature = files_signature(uploaded_files)

        needs_load = (
            st.session_state.get(SESSION_SIGNATURE_KEY) != signature
            or SESSION_DATA_KEY not in st.session_state
        )

        if needs_load:
            try:
                with st.spinner(
                    "Leyendo, validando y consolidando los cinco archivos..."
                ):
                    data, source_bytes, validation = load_five_files(
                        uploaded_files
                    )

                names = {
                    level: uploaded_files[level].name
                    for level in LEVELS
                }

                st.session_state[SESSION_DATA_KEY] = data
                st.session_state[SESSION_FILE_KEY] = names
                st.session_state[SESSION_SOURCE_FILES_KEY] = source_bytes
                st.session_state[SESSION_FILE_BYTES_KEY] = source_bytes
                st.session_state[SESSION_SIGNATURE_KEY] = signature
                st.session_state[SESSION_VALIDATION_KEY] = validation
                st.session_state.pop(SESSION_CASE_KEY, None)

                st.toast(
                    "Cinco archivos cargados correctamente.",
                    icon="✅",
                )
                st.rerun()

            except ValueError as error:
                clear_active_files()
                st.error(str(error))

    st.markdown("---")
    st.markdown(
        '<div class="fl-section-title">2. Versión activa</div>',
        unsafe_allow_html=True,
    )

    render_active_state()


if __name__ == "__main__":
    main()
