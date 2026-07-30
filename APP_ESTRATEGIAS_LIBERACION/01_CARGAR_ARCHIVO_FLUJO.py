
# ============================================================
# 01_CARGAR_ARCHIVO_FLUJO
# APP_ESTRATEGIAS_LIBERACION
#
# NUEVO FORMATO ÚNICO:
#   7 archivos obligatorios y 1 opcional:
#   - Liberador 1, 2, 3, 4 y 5.
#   - Diccionario CECO-Plantas.
#   - Diccionario Usuarios-Cargos.
#   - Cambios (opcional).
#   Cada archivo puede ser CSV, Parquet o Excel.
#
# La aplicación:
#   1. valida cada nivel;
#   2. conserva todas las reglas originales, incluidos * y V;
#   3. reconstruye una tabla interna:
#      CECO | Planta | Desde | Hasta | TipoDoc |
#      Lib1 | Lib2 | Lib3 | Lib4 | Lib5
#   4. incorpora Planta y cargos desde los dos diccionarios;
#   5. deja los archivos normalizados en session_state;
#   6. incorpora el historial de cambios cuando se adjunta.
# ============================================================

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib.util
import re
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse
from textwrap import dedent
from typing import Any, Callable

import pandas as pd
import requests
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


CECO_DICTIONARY_COLUMNS = ["CECO", "Planta", "Centro"]
USER_DICTIONARY_COLUMNS = ["Correo", "Cargo"]

CHANGE_COLUMNS = [
    "FechaHora",
    "Usuario",
    "CECO",
    "Desde",
    "Hasta",
    "TipoDoc",
    "Campo",
    "ValorAntes",
    "ValorDespues",
    "Nota",
]

FILE_ROLE_LIBERATORS = {level: f"liberador_{level}" for level in LEVELS}
FILE_ROLE_CECO = "dic_ceco"
FILE_ROLE_USERS = "dic_users"
FILE_ROLE_CHANGES = "cambios"
REQUIRED_FILE_ROLES = [
    *[FILE_ROLE_LIBERATORS[level] for level in LEVELS],
    FILE_ROLE_CECO,
    FILE_ROLE_USERS,
]
OPTIONAL_FILE_ROLES = [FILE_ROLE_CHANGES]
ALL_FILE_ROLES = [*REQUIRED_FILE_ROLES, *OPTIONAL_FILE_ROLES]

SESSION_DATA_KEY = "flujo_liberacion_data"
SESSION_FILE_KEY = "flujo_liberacion_file_name"
SESSION_CASE_KEY = "flujo_liberacion_last_case"
SESSION_FILE_BYTES_KEY = "flujo_liberacion_file_bytes"
SESSION_SIGNATURE_KEY = "flujo_liberacion_upload_signature_v05"
SESSION_VALIDATION_KEY = "flujo_liberacion_validation_v05"
SESSION_SOURCE_FILES_KEY = "flujo_liberacion_source_files_v06"
SESSION_CHANGES_KEY = "flujo_liberacion_changes_v01"
SESSION_REMOTE_FILES_KEY = "flujo_liberacion_remote_files_v01"
SESSION_REMOTE_SOURCE_KEY = "flujo_liberacion_remote_source_v01"


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
# CONEXIÓN REMOTA MEDIANTE REQUESTS + SECRETS
# ============================================================

class RemoteUploadedFile:
    """Adaptador mínimo compatible con read_uploaded_table."""
    def __init__(self, name: str, raw: bytes):
        self.name = Path(name).name
        self._raw = bytes(raw)

    def getvalue(self) -> bytes:
        return self._raw


def secret_value(
    key: str,
    default: Any = None,
    *,
    required: bool = False,
) -> Any:
    try:
        section = st.secrets["sharepoint_flujo"]
        value = section.get(key, default)
    except Exception as error:
        if required:
            raise ValueError(
                "No existe la sección [sharepoint_flujo] en Secrets."
            ) from error
        return default

    if required and not clean_text(value):
        raise ValueError(
            f"Falta configurar sharepoint_flujo.{key} en Secrets."
        )

    return value


def obtener_url_remota_segura() -> str:
    url = clean_text(secret_value("url", required=True))
    parsed = urlparse(url)

    if parsed.scheme.lower() != "https" or not parsed.netloc:
        raise ValueError(
            "La URL remota debe ser una dirección HTTPS válida."
        )

    allowed_host = clean_text(
        secret_value("allowed_host", "")
    ).casefold()
    if allowed_host and parsed.hostname:
        hostname = parsed.hostname.casefold()
        if hostname != allowed_host and not hostname.endswith(
            "." + allowed_host
        ):
            raise ValueError(
                "El host de la URL no coincide con allowed_host."
            )

    return url


def calcular_sha256(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def validar_clave_conexion(clave_ingresada: str) -> bool:
    expected_hash = clean_text(
        secret_value("access_key_sha256", required=True)
    ).casefold()

    if not clave_ingresada or not expected_hash:
        return False

    return hmac.compare_digest(
        calcular_sha256(clave_ingresada).casefold(),
        expected_hash,
    )


def preparar_url_descarga(url: str) -> str:
    if "download=1" in url.casefold():
        return url

    separator = "&" if "?" in url else "?"
    return f"{url}{separator}download=1"


def request_headers_from_secrets() -> dict[str, str]:
    headers = {
        "User-Agent": "ENAEX-Estrategias-Liberacion/1.0",
        "Accept": (
            "application/zip, application/octet-stream, "
            "application/x-zip-compressed"
        ),
    }

    bearer_token = clean_text(
        secret_value("bearer_token", "")
    )
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    return headers


def request_auth_from_secrets() -> tuple[str, str] | None:
    username = clean_text(secret_value("username", ""))
    password = clean_text(secret_value("password", ""))

    if username and password:
        return username, password

    return None


def validate_remote_response(
    response: requests.Response,
    expected_host: str,
) -> None:
    response.raise_for_status()

    final = urlparse(response.url)
    if final.scheme.lower() != "https":
        raise ValueError(
            "La descarga fue redirigida a una URL no segura."
        )

    allow_redirect_host = bool(
        secret_value("allow_redirect_host", False)
    )
    if (
        not allow_redirect_host
        and final.hostname
        and final.hostname.casefold() != expected_host.casefold()
    ):
        raise ValueError(
            "La descarga fue redirigida a otro host no autorizado."
        )

    content_type = response.headers.get(
        "Content-Type",
        "",
    ).casefold()
    beginning = response.content[:500].casefold()

    if (
        "text/html" in content_type
        or b"<html" in beginning
        or b"<!doctype html" in beginning
    ):
        raise ValueError(
            "El servidor devolvió una página HTML, no el ZIP esperado."
        )

    max_mb = int(secret_value("max_download_mb", 250))
    if len(response.content) > max_mb * 1024 * 1024:
        raise ValueError(
            f"La descarga supera el máximo configurado de {max_mb} MB."
        )


@st.cache_data(show_spinner=False, ttl=300)
def descargar_zip_remoto_cache(
    url: str,
    headers_items: tuple[tuple[str, str], ...],
    auth: tuple[str, str] | None,
    timeout_seconds: int,
    verify_ssl: bool,
) -> bytes:
    response = requests.get(
        preparar_url_descarga(url),
        headers=dict(headers_items),
        auth=auth,
        allow_redirects=True,
        timeout=timeout_seconds,
        verify=verify_ssl,
    )

    expected_host = urlparse(url).hostname or ""
    validate_remote_response(response, expected_host)

    raw = response.content
    if not zipfile.is_zipfile(BytesIO(raw)):
        raise ValueError(
            "La URL configurada no devolvió un archivo ZIP válido."
        )

    return raw


def archivos_desde_zip_remoto(
    raw_zip: bytes,
) -> dict[str, RemoteUploadedFile]:
    supported = {
        ".csv",
        ".parquet",
        ".pq",
        ".xlsx",
        ".xls",
        ".xlsm",
    }
    uploaded: dict[str, RemoteUploadedFile] = {}
    unresolved: list[str] = []
    duplicated: list[str] = []

    with zipfile.ZipFile(BytesIO(raw_zip), mode="r") as archive:
        members = [
            item
            for item in archive.infolist()
            if not item.is_dir()
            and Path(item.filename).suffix.casefold() in supported
            and not Path(item.filename).name.startswith("~$")
            and "__MACOSX" not in Path(item.filename).parts
        ]

        if len(members) > 8:
            raise ValueError(
                "El ZIP contiene más de ocho archivos compatibles."
            )

        for member in members:
            safe_name = Path(member.filename).name
            role = detect_file_role(safe_name)

            if role is None:
                unresolved.append(safe_name)
                continue

            if role in uploaded:
                duplicated.append(role)
                continue

            max_member_mb = int(
                secret_value("max_file_mb", 100)
            )
            if member.file_size > max_member_mb * 1024 * 1024:
                raise ValueError(
                    f"{safe_name} supera el máximo de "
                    f"{max_member_mb} MB."
                )

            uploaded[role] = RemoteUploadedFile(
                safe_name,
                archive.read(member),
            )

    if unresolved:
        raise ValueError(
            "No se pudo identificar dentro del ZIP: "
            + ", ".join(unresolved)
        )

    if duplicated:
        raise ValueError(
            "El ZIP contiene roles duplicados: "
            + ", ".join(
                role_label(role)
                for role in sorted(set(duplicated))
            )
        )

    missing = [
        role
        for role in REQUIRED_FILE_ROLES
        if role not in uploaded
    ]
    if missing:
        raise ValueError(
            "Faltan archivos obligatorios en el ZIP remoto: "
            + ", ".join(role_label(role) for role in missing)
        )

    return uploaded


def conectar_y_obtener_archivos(
    clave_ingresada: str,
) -> dict[str, RemoteUploadedFile]:
    if not validar_clave_conexion(clave_ingresada):
        raise ValueError("Clave de conexión incorrecta.")

    url = obtener_url_remota_segura()
    headers = request_headers_from_secrets()
    auth = request_auth_from_secrets()
    timeout_seconds = int(secret_value("timeout_seconds", 90))
    verify_ssl = bool(secret_value("verify_ssl", True))

    raw_zip = descargar_zip_remoto_cache(
        url=url,
        headers_items=tuple(sorted(headers.items())),
        auth=auth,
        timeout_seconds=timeout_seconds,
        verify_ssl=verify_ssl,
    )
    return archivos_desde_zip_remoto(raw_zip)


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
# DICCIONARIOS
# ============================================================

def normalize_ceco_dictionary(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = dataframe.copy()
    frame.columns = [normalize_column_name(column) for column in frame.columns]

    missing = [
        column
        for column in ["CECO", "Planta"]
        if column not in frame.columns
    ]
    if missing:
        raise ValueError(
            "Diccionario CECO-Plantas: faltan columnas obligatorias: "
            + ", ".join(missing)
        )

    if "Centro" not in frame.columns:
        frame["Centro"] = ""

    frame = frame.loc[:, CECO_DICTIONARY_COLUMNS].copy()

    for column in CECO_DICTIONARY_COLUMNS:
        frame[column] = frame[column].map(clean_text)

    frame = frame[frame["CECO"].ne("")].copy()

    duplicate_rows = int(
        frame.duplicated(subset=["CECO"], keep=False).sum()
    )

    conflicting_cecos: list[dict[str, Any]] = []
    for ceco, group in frame.groupby("CECO", sort=False):
        plants = [
            value
            for value in group["Planta"].drop_duplicates().tolist()
            if value
        ]
        if len(plants) > 1:
            conflicting_cecos.append({
                "CECO": ceco,
                "Plantas": " | ".join(plants),
            })

    result = (
        frame.drop_duplicates(subset=["CECO"], keep="last")
        .sort_values("CECO", kind="stable")
        .reset_index(drop=True)
    )

    report = {
        "rows": len(result),
        "duplicate_rows": duplicate_rows,
        "conflicts": pd.DataFrame(conflicting_cecos),
        "empty_plants": int(result["Planta"].eq("").sum()),
    }
    return result, report


def normalize_user_dictionary(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    frame = dataframe.copy()
    frame.columns = [normalize_column_name(column) for column in frame.columns]

    aliases = {
        "Email": "Correo",
        "Mail": "Correo",
        "Usuario": "Correo",
        "Rol": "Cargo",
        "Role": "Cargo",
    }
    frame = frame.rename(
        columns={
            column: aliases.get(column, column)
            for column in frame.columns
        }
    )

    missing = [
        column
        for column in USER_DICTIONARY_COLUMNS
        if column not in frame.columns
    ]
    if missing:
        raise ValueError(
            "Diccionario Usuarios-Cargos: faltan columnas obligatorias: "
            + ", ".join(missing)
        )

    frame = frame.loc[:, USER_DICTIONARY_COLUMNS].copy()
    frame["Correo"] = frame["Correo"].map(clean_text)
    frame["Cargo"] = frame["Cargo"].map(clean_text)
    frame = frame[frame["Correo"].ne("")].copy()

    duplicate_rows = int(
        frame.duplicated(subset=["Correo"], keep=False).sum()
    )

    result = (
        frame.drop_duplicates(subset=["Correo"], keep="last")
        .sort_values("Correo", key=lambda values: values.str.casefold())
        .reset_index(drop=True)
    )

    report = {
        "rows": len(result),
        "duplicate_rows": duplicate_rows,
        "empty_roles": int(result["Cargo"].eq("").sum()),
    }
    return result, report


def apply_ceco_dictionary(
    flow: pd.DataFrame,
    ceco_dictionary: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    result = flow.copy()
    plant_by_ceco = dict(
        zip(
            ceco_dictionary["CECO"],
            ceco_dictionary["Planta"],
        )
    )
    known_cecos = set(ceco_dictionary["CECO"].astype(str))

    result["Planta"] = result["CECO"].map(plant_by_ceco).fillna("")

    missing_cecos = sorted(
        set(result["CECO"].astype(str)) - known_cecos
    )
    cecos_without_plant = sorted(
        result.loc[
            result["CECO"].isin(known_cecos)
            & result["Planta"].eq(""),
            "CECO",
        ]
        .drop_duplicates()
        .astype(str)
        .tolist()
    )
    return result, missing_cecos, cecos_without_plant


def normalize_changes_file(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Normaliza el archivo opcional de historial de cambios."""
    frame = dataframe.copy()
    frame.columns = [
        normalize_column_name(column)
        for column in frame.columns
    ]

    aliases = {
        "Fecha Hora": "FechaHora",
        "Fecha_Hora": "FechaHora",
        "Responsable": "Usuario",
        "Tipo Documento": "TipoDoc",
        "TipoDocumento": "TipoDoc",
        "Valor Antes": "ValorAntes",
        "Valor Después": "ValorDespues",
        "Valor Despues": "ValorDespues",
        "Observación": "Nota",
        "Observacion": "Nota",
        "Motivo": "Nota",
    }
    frame = frame.rename(
        columns={
            column: aliases.get(column, column)
            for column in frame.columns
        }
    )

    # El archivo puede venir de versiones anteriores con menos columnas.
    for column in CHANGE_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""

    result = frame.loc[:, CHANGE_COLUMNS].copy()

    for column in CHANGE_COLUMNS:
        result[column] = result[column].map(clean_text)

    result = result[
        result.apply(
            lambda row: any(clean_text(value) for value in row),
            axis=1,
        )
    ].reset_index(drop=True)

    report = {
        "rows": len(result),
        "empty_user": int(result["Usuario"].eq("").sum()),
        "empty_ceco": int(result["CECO"].eq("").sum()),
        "empty_note": int(result["Nota"].eq("").sum()),
    }
    return result, report


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

def files_signature(files: dict[str, Any]) -> str:
    parts: list[str] = []

    for role in ALL_FILE_ROLES:
        uploaded = files.get(role)
        if uploaded is None:
            parts.append(f"{role}|NO_CARGADO")
            continue

        raw = uploaded.getvalue()
        digest = hashlib.sha1(raw).hexdigest()
        parts.append(
            f"{role}|{uploaded.name}|{len(raw)}|{digest}"
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
        SESSION_CHANGES_KEY,
        SESSION_REMOTE_FILES_KEY,
        SESSION_REMOTE_SOURCE_KEY,
    ]:
        st.session_state.pop(key, None)


def load_seven_files(
    uploaded_files: dict[str, Any],
    progress_callback: Callable[[int, str], None] | None = None,
) -> tuple[dict[str, Any], dict[str, bytes], dict[str, Any]]:
    """
    Lee y consolida siete archivos obligatorios y un archivo
    de cambios opcional.
    """
    def report(percent: int, message: str) -> None:
        if progress_callback is not None:
            progress_callback(
                max(0, min(100, int(percent))),
                message,
            )

    level_frames: dict[int, pd.DataFrame] = {}
    level_reports: dict[int, dict[str, Any]] = {}
    source_bytes: dict[str, bytes] = {}

    ordered_roles = [
        *[FILE_ROLE_LIBERATORS[level] for level in LEVELS],
        FILE_ROLE_CECO,
        FILE_ROLE_USERS,
    ]
    if FILE_ROLE_CHANGES in uploaded_files:
        ordered_roles.append(FILE_ROLE_CHANGES)

    total_files = len(ordered_roles)
    completed_files = 0

    def file_progress(
        file_number: int,
        stage_fraction: float,
    ) -> int:
        base = (file_number - 1) / total_files
        value = base + stage_fraction / total_files
        # Reserva el 15% final para reconstrucción y activación.
        return int(2 + value * 78)

    report(
        1,
        f"Preparando carga de {total_files} archivos...",
    )

    # 1–5: liberadores.
    for level in LEVELS:
        role = FILE_ROLE_LIBERATORS[level]
        file_number = ordered_roles.index(role) + 1

        report(
            file_progress(file_number, 0.10),
            (
                f"Archivo {file_number} de {total_files} · "
                f"Leyendo Liberador {level}..."
            ),
        )
        frame_raw, raw = read_uploaded_table(uploaded_files[role])

        report(
            file_progress(file_number, 0.55),
            (
                f"Archivo {file_number} de {total_files} · "
                f"Validando Liberador {level}..."
            ),
        )
        frame, validation_report = normalize_level_dataframe(
            frame_raw,
            level,
        )

        level_frames[level] = frame
        level_reports[level] = validation_report
        source_bytes[role] = raw
        completed_files += 1

        report(
            file_progress(file_number, 1.0),
            (
                f"Archivo {file_number} de {total_files} completado · "
                f"Liberador {level} · {len(frame):,} filas"
            ).replace(",", "."),
        )

    # Diccionario CECO.
    role = FILE_ROLE_CECO
    file_number = ordered_roles.index(role) + 1
    report(
        file_progress(file_number, 0.10),
        (
            f"Archivo {file_number} de {total_files} · "
            "Leyendo Diccionario CECO-Plantas..."
        ),
    )
    ceco_raw, ceco_bytes = read_uploaded_table(
        uploaded_files[role]
    )
    report(
        file_progress(file_number, 0.55),
        (
            f"Archivo {file_number} de {total_files} · "
            "Validando Diccionario CECO-Plantas..."
        ),
    )
    ceco_dictionary, ceco_report = normalize_ceco_dictionary(
        ceco_raw
    )
    source_bytes[role] = ceco_bytes
    completed_files += 1
    report(
        file_progress(file_number, 1.0),
        (
            f"Archivo {file_number} de {total_files} completado · "
            f"CECO-Plantas · {len(ceco_dictionary):,} registros"
        ).replace(",", "."),
    )

    # Diccionario usuarios.
    role = FILE_ROLE_USERS
    file_number = ordered_roles.index(role) + 1
    report(
        file_progress(file_number, 0.10),
        (
            f"Archivo {file_number} de {total_files} · "
            "Leyendo Diccionario Usuarios-Cargos..."
        ),
    )
    users_raw, users_bytes = read_uploaded_table(
        uploaded_files[role]
    )
    report(
        file_progress(file_number, 0.55),
        (
            f"Archivo {file_number} de {total_files} · "
            "Validando Diccionario Usuarios-Cargos..."
        ),
    )
    users_dictionary, users_report = normalize_user_dictionary(
        users_raw
    )
    source_bytes[role] = users_bytes
    completed_files += 1
    report(
        file_progress(file_number, 1.0),
        (
            f"Archivo {file_number} de {total_files} completado · "
            f"Usuarios-Cargos · {len(users_dictionary):,} registros"
        ).replace(",", "."),
    )

    # Archivo opcional de cambios.
    changes_dataframe = pd.DataFrame(columns=CHANGE_COLUMNS)
    changes_report = {
        "rows": 0,
        "empty_user": 0,
        "empty_ceco": 0,
        "empty_note": 0,
        "loaded": False,
    }

    if FILE_ROLE_CHANGES in uploaded_files:
        role = FILE_ROLE_CHANGES
        file_number = ordered_roles.index(role) + 1
        report(
            file_progress(file_number, 0.10),
            (
                f"Archivo {file_number} de {total_files} · "
                "Leyendo historial de cambios..."
            ),
        )
        changes_raw, changes_bytes = read_uploaded_table(
            uploaded_files[role]
        )
        report(
            file_progress(file_number, 0.55),
            (
                f"Archivo {file_number} de {total_files} · "
                "Validando historial de cambios..."
            ),
        )
        changes_dataframe, changes_report = normalize_changes_file(
            changes_raw
        )
        changes_report["loaded"] = True
        source_bytes[role] = changes_bytes
        completed_files += 1
        report(
            file_progress(file_number, 1.0),
            (
                f"Archivo {file_number} de {total_files} completado · "
                f"Cambios · {len(changes_dataframe):,} registros"
            ).replace(",", "."),
        )

    report(
        82,
        (
            f"{completed_files} de {total_files} archivos procesados · "
            "Reconstruyendo el flujo..."
        ),
    )
    flow, flow_report = reconstruct_flow(level_frames)

    if flow.empty:
        raise ValueError(
            "Los cinco archivos de liberadores no contienen reglas con "
            "CostCenter explícito y TipoDoc AZNB/AZSR."
        )

    report(
        91,
        (
            f"Flujo reconstruido · {len(flow):,} reglas · "
            "Aplicando diccionarios..."
        ).replace(",", "."),
    )
    flow, missing_cecos, cecos_without_plant = apply_ceco_dictionary(
        flow,
        ceco_dictionary,
    )
    flow_report["cecos_without_dictionary"] = missing_cecos
    flow_report["cecos_without_plant"] = cecos_without_plant

    report(97, "Preparando la versión activa...")
    data: dict[str, Any] = {
        "flujo": flow,
        "liberadores": level_frames,
        "liberador_1": level_frames[1],
        "liberador_2": level_frames[2],
        "liberador_3": level_frames[3],
        "liberador_4": level_frames[4],
        "liberador_5": level_frames[5],
        "dic_users": users_dictionary,
        "dic_ceco": ceco_dictionary,
        "cambios": changes_dataframe,
        "dic_rangos": pd.DataFrame(
            columns=["Orden", "Desde", "Hasta"]
        ),
    }

    validation = {
        "levels": level_reports,
        "flow": flow_report,
        "dic_ceco": ceco_report,
        "dic_users": users_report,
        "cambios": changes_report,
        "file_count": total_files,
    }

    report(
        100,
        (
            f"Carga completada · {total_files} de {total_files} "
            "archivos procesados."
        ),
    )
    return data, source_bytes, validation



# ============================================================
# EXPORTACIÓN DE LOS SIETE ARCHIVOS
# ============================================================

def dataframe_for_export(
    data: dict[str, Any],
    role: str,
) -> pd.DataFrame:
    """Obtiene una copia limpia del archivo lógico solicitado."""
    if role == FILE_ROLE_CECO:
        frame = data.get("dic_ceco", pd.DataFrame())
        columns = CECO_DICTIONARY_COLUMNS
    elif role == FILE_ROLE_USERS:
        frame = data.get("dic_users", pd.DataFrame())
        columns = USER_DICTIONARY_COLUMNS
    elif role == FILE_ROLE_CHANGES:
        frame = data.get("cambios", pd.DataFrame())
        columns = CHANGE_COLUMNS
    else:
        level = next(
            (
                current_level
                for current_level in LEVELS
                if FILE_ROLE_LIBERATORS[current_level] == role
            ),
            None,
        )
        if level is None:
            raise ValueError(f"Rol de archivo no reconocido: {role}")

        frame = data.get("liberadores", {}).get(
            level,
            pd.DataFrame(),
        )
        columns = GROUP_COLUMNS

    if not isinstance(frame, pd.DataFrame):
        raise ValueError(
            f"No hay datos disponibles para {role_label(role)}."
        )

    result = frame.drop(
        columns=[
            "_DesdeNum",
            "_HastaNum",
            "_Nivel",
            "_Liberador",
        ],
        errors="ignore",
    ).copy()

    for column in columns:
        if column not in result.columns:
            result[column] = ""

    return result.loc[:, columns].copy()


def source_extension(
    role: str,
    file_names: dict[str, str],
) -> str:
    """Determina la extensión del archivo originalmente cargado."""
    name = clean_text(file_names.get(role, ""))
    suffix = Path(name).suffix.lower()

    if suffix in {".parquet", ".pq"}:
        return ".parquet"
    if suffix == ".csv":
        return ".csv"
    if suffix in {".xlsx", ".xls", ".xlsm"}:
        return ".xlsx"

    return ".csv"


def dataframe_to_csv_bytes(dataframe: pd.DataFrame) -> bytes:
    return dataframe.to_csv(
        index=False,
        sep=";",
        lineterminator="\n",
    ).encode("utf-8-sig")


def available_parquet_engine() -> str | None:
    """Retorna el motor Parquet disponible en el entorno."""
    if importlib.util.find_spec("pyarrow") is not None:
        return "pyarrow"

    if importlib.util.find_spec("fastparquet") is not None:
        return "fastparquet"

    return None


def dataframe_to_parquet_bytes(dataframe: pd.DataFrame) -> bytes:
    engine = available_parquet_engine()

    if engine is None:
        raise ValueError(
            "La exportación Parquet requiere instalar `pyarrow` "
            "o `fastparquet`. Agrega `pyarrow` a requirements.txt."
        )

    output = BytesIO()

    try:
        dataframe.to_parquet(
            output,
            index=False,
            engine=engine,
        )
    except Exception as error:
        raise ValueError(
            f"No fue posible generar el archivo Parquet con {engine}."
        ) from error

    return output.getvalue()


def dataframe_to_excel_bytes(
    dataframe: pd.DataFrame,
) -> bytes:
    output = BytesIO()

    try:
        with pd.ExcelWriter(
            output,
            engine="openpyxl",
        ) as writer:
            dataframe.to_excel(
                writer,
                index=False,
                sheet_name="Sheet1",
            )
    except Exception as error:
        raise ValueError(
            "No fue posible generar el archivo Excel."
        ) from error

    return output.getvalue()


def export_file_name(
    role: str,
    extension: str,
) -> str:
    if role == FILE_ROLE_CECO:
        stem = "Diccionario_CECO_Plantas"
    elif role == FILE_ROLE_USERS:
        stem = "Diccionario_Usuarios_Cargos"
    elif role == FILE_ROLE_CHANGES:
        stem = "Cambios"
    else:
        level = next(
            level
            for level in LEVELS
            if FILE_ROLE_LIBERATORS[level] == role
        )
        stem = f"Liberador_{level}_Compra_Directa_ENAEX"

    return f"{stem}{extension}"


def build_export_zip(
    data: dict[str, Any],
    file_names: dict[str, str],
    export_mode: str,
) -> bytes:
    """
    Genera un ZIP con los siete archivos.

    export_mode:
      - source: conserva CSV/Parquet/Excel según el archivo de entrada.
      - csv: convierte todos a CSV.
      - parquet: convierte todos a Parquet.
    """
    if export_mode not in {"source", "csv", "parquet"}:
        raise ValueError("Modo de exportación no válido.")

    output = BytesIO()

    with zipfile.ZipFile(
        output,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        export_roles = list(REQUIRED_FILE_ROLES)
        changes = data.get("cambios", pd.DataFrame())
        if isinstance(changes, pd.DataFrame) and not changes.empty:
            export_roles.append(FILE_ROLE_CHANGES)

        for role in export_roles:
            dataframe = dataframe_for_export(data, role)

            if export_mode == "csv":
                extension = ".csv"
            elif export_mode == "parquet":
                extension = ".parquet"
            else:
                extension = source_extension(role, file_names)

            if extension == ".csv":
                content = dataframe_to_csv_bytes(dataframe)
            elif extension == ".parquet":
                content = dataframe_to_parquet_bytes(dataframe)
            elif extension == ".xlsx":
                content = dataframe_to_excel_bytes(dataframe)
            else:
                raise ValueError(
                    f"Extensión de exportación no válida: {extension}"
                )

            archive.writestr(
                export_file_name(role, extension),
                content,
            )

    return output.getvalue()


def render_export_section(data: dict[str, Any]) -> None:
    st.markdown("---")
    st.markdown(
        '<div class="fl-section-title">Descargar versión completa</div>',
        unsafe_allow_html=True,
    )
    st.caption(
        "Descarga los siete archivos conservando su formato de origen "
        "o conviértelos todos a CSV o Parquet."
    )

    file_names = st.session_state.get(SESSION_FILE_KEY, {})
    if not isinstance(file_names, dict):
        file_names = {}

    input_extensions = {
        source_extension(role, file_names)
        for role in REQUIRED_FILE_ROLES
    }

    if input_extensions == {".parquet"}:
        default_index = 2
    elif input_extensions == {".csv"}:
        default_index = 1
    else:
        default_index = 0

    parquet_engine = available_parquet_engine()
    options = ["source", "csv"]

    if parquet_engine is not None:
        options.append("parquet")
    elif ".parquet" in input_extensions:
        st.error(
            "Se cargaron archivos Parquet, pero el entorno no tiene un motor "
            "Parquet instalado. Agrega `pyarrow` a requirements.txt."
        )
        return
    else:
        st.info(
            "La opción Parquet se habilitará automáticamente al instalar "
            "`pyarrow` o `fastparquet`."
        )

    default_mode = (
        "parquet"
        if default_index == 2 and "parquet" in options
        else "csv"
        if default_index == 1
        else "source"
    )

    selected_mode = st.radio(
        "Formato de descarga",
        options=options,
        index=options.index(default_mode),
        format_func=lambda value: {
            "source": "Conservar formato original de cada archivo",
            "csv": "Convertir los 7 archivos a CSV",
            "parquet": (
                "Convertir los 7 archivos a Parquet "
                f"({parquet_engine})"
            ),
        }[value],
        horizontal=False,
        key="export_format_mode_v02",
    )

    try:
        zip_bytes = build_export_zip(
            data=data,
            file_names=file_names,
            export_mode=selected_mode,
        )
    except ValueError as error:
        st.error(str(error))
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    mode_label = {
        "source": "FORMATO_ORIGINAL",
        "csv": "CSV",
        "parquet": "PARQUET",
    }[selected_mode]

    st.download_button(
        "⬇️ Descargar ZIP con los 7 archivos",
        data=zip_bytes,
        file_name=(
            f"VERSION_LIBERADORES_{mode_label}_{timestamp}.zip"
        ),
        mime="application/zip",
        type="primary",
        use_container_width=True,
        key=f"download_seven_files_{selected_mode}_v01",
    )

# ============================================================
# INTERFAZ
# ============================================================

def render_header() -> None:
    mostrar_logo()

    st.markdown(
        '<div class="fl-title">01 Cargar Versión</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="fl-subtitle">
            Carga la versión manualmente o mediante Requests y Secrets.
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


def detect_file_role(name: str) -> str | None:
    """Identifica los cinco niveles, dos diccionarios y cambios opcionales."""
    text = Path(name).stem.casefold()
    simplified = re.sub(r"[^a-z0-9]+", " ", text).strip()

    ceco_terms = (
        ("diccionario" in simplified or "dic" in simplified)
        and ("ceco" in simplified or "centro costo" in simplified)
        and ("planta" in simplified or "centro" in simplified)
    )
    if ceco_terms:
        return FILE_ROLE_CECO

    user_terms = (
        ("diccionario" in simplified or "dic" in simplified)
        and (
            "usuario" in simplified
            or "usuarios" in simplified
            or "correo" in simplified
        )
        and (
            "cargo" in simplified
            or "cargos" in simplified
            or "rol" in simplified
        )
    )
    if user_terms:
        return FILE_ROLE_USERS

    changes_terms = (
        "cambio" in simplified
        or "cambios" in simplified
        or "historial" in simplified
        or "auditoria" in simplified
        or "auditoría" in simplified
    )
    if changes_terms:
        return FILE_ROLE_CHANGES

    patterns = [
        r"liberador[_\-\s]*(\d)",
        r"nivel[_\-\s]*(\d)",
        r"lib[_\-\s]*(\d)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            level = int(match.group(1))
            if level in LEVELS:
                return FILE_ROLE_LIBERATORS[level]

    return None


def role_label(role: str) -> str:
    if role == FILE_ROLE_CECO:
        return "Diccionario CECO-Plantas"
    if role == FILE_ROLE_USERS:
        return "Diccionario Usuarios-Cargos"
    if role == FILE_ROLE_CHANGES:
        return "Historial de Cambios (opcional)"

    for level in LEVELS:
        if role == FILE_ROLE_LIBERATORS[level]:
            return f"Liberador {level}"

    return role


def render_remote_connection() -> dict[str, Any]:
    st.caption(
        "La URL y las credenciales técnicas se leen desde "
        "`st.secrets[\"sharepoint_flujo\"]`."
    )

    with st.form("form_remote_flujo_v01"):
        access_key = st.text_input(
            "Clave de conexión",
            type="password",
            placeholder="Ingresa la clave autorizada",
        )
        connect = st.form_submit_button(
            "Conectar y cargar versión",
            use_container_width=True,
            type="primary",
        )

    if connect:
        try:
            with st.spinner(
                "Conectando y descargando el ZIP..."
            ):
                remote_files = conectar_y_obtener_archivos(
                    access_key
                )

            st.session_state[SESSION_REMOTE_FILES_KEY] = (
                remote_files
            )
            st.session_state[SESSION_REMOTE_SOURCE_KEY] = (
                "requests_secrets"
            )
            st.success(
                f"Conexión realizada. Se detectaron "
                f"{len(remote_files)} archivos."
            )
        except requests.RequestException:
            st.session_state.pop(
                SESSION_REMOTE_FILES_KEY,
                None,
            )
            st.error(
                "No fue posible descargar la versión remota. "
                "Revisa la URL, permisos y conectividad."
            )
        except ValueError as error:
            st.session_state.pop(
                SESSION_REMOTE_FILES_KEY,
                None,
            )
            st.error(str(error))

    value = st.session_state.get(
        SESSION_REMOTE_FILES_KEY,
        {},
    )
    return value if isinstance(value, dict) else {}


def render_uploader() -> dict[str, Any]:
    """Carga siete archivos obligatorios y un historial opcional."""
    selected_files = st.file_uploader(
        "Seleccionar 7 archivos obligatorios y 1 opcional",
        type=["csv", "parquet", "pq", "xlsx", "xls", "xlsm"],
        accept_multiple_files=True,
        key="liberadores_diccionarios_uploader_v06",
        label_visibility="collapsed",
        help=(
            "Selecciona Liberador 1–5, Diccionario CECO-Plantas, "
            "Diccionario Usuarios-Cargos y, opcionalmente, Cambios."
        ),
    )

    if not selected_files:
        return {}

    if len(selected_files) > 8:
        st.error(
            "Selecciona como máximo ocho archivos: siete obligatorios "
            "y el historial de cambios opcional."
        )
        return {}

    uploaded: dict[str, Any] = {}
    unresolved: list[str] = []
    duplicated_roles: list[str] = []

    for uploaded_file in selected_files:
        role = detect_file_role(uploaded_file.name)

        if role is None:
            unresolved.append(uploaded_file.name)
            continue

        if role in uploaded:
            duplicated_roles.append(role)
            continue

        uploaded[role] = uploaded_file

    if unresolved:
        st.error(
            "No pude identificar: "
            + ", ".join(unresolved)
            + ". Revisa los nombres de los archivos."
        )

    if duplicated_roles:
        labels = ", ".join(
            role_label(role)
            for role in sorted(set(duplicated_roles))
        )
        st.error(f"Hay archivos duplicados para: {labels}.")

    if unresolved or duplicated_roles:
        return {}

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

        dictionary_rows = [
            {
                "Archivo": "Diccionario CECO-Plantas",
                "Filas": report.get("dic_ceco", {}).get("rows", 0),
                "Duplicadas": report.get("dic_ceco", {}).get(
                    "duplicate_rows", 0
                ),
                "Valores vacíos": report.get("dic_ceco", {}).get(
                    "empty_plants", 0
                ),
            },
            {
                "Archivo": "Diccionario Usuarios-Cargos",
                "Filas": report.get("dic_users", {}).get("rows", 0),
                "Duplicadas": report.get("dic_users", {}).get(
                    "duplicate_rows", 0
                ),
                "Valores vacíos": report.get("dic_users", {}).get(
                    "empty_roles", 0
                ),
            },
        ]

        changes_report = report.get("cambios", {})
        if changes_report.get("loaded"):
            dictionary_rows.append({
                "Archivo": "Historial de Cambios",
                "Filas": changes_report.get("rows", 0),
                "Duplicadas": 0,
                "Valores vacíos": (
                    changes_report.get("empty_user", 0)
                    + changes_report.get("empty_ceco", 0)
                    + changes_report.get("empty_note", 0)
                ),
            })

        st.markdown("#### Diccionarios e historial")
        st.dataframe(
            pd.DataFrame(dictionary_rows),
            use_container_width=True,
            hide_index=True,
        )

        ceco_conflicts = report.get("dic_ceco", {}).get(
            "conflicts", pd.DataFrame()
        )
        if isinstance(ceco_conflicts, pd.DataFrame) and not ceco_conflicts.empty:
            st.error(
                "Hay CECO asociados a más de una planta en el diccionario."
            )
            st.dataframe(
                ceco_conflicts,
                use_container_width=True,
                hide_index=True,
            )

        missing_cecos = flow_report.get("cecos_without_dictionary", [])
        if missing_cecos:
            st.error(
                f"Hay {len(missing_cecos)} CECO del flujo que no existen "
                "en el diccionario CECO-Plantas."
            )

        cecos_without_plant = flow_report.get("cecos_without_plant", [])
        if cecos_without_plant:
            st.warning(
                f"Hay {len(cecos_without_plant)} CECO presentes en el "
                "diccionario, pero con Planta vacía."
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
        st.info("Carga los siete archivos para activar la aplicación.")
        return

    flow = data.get("flujo", pd.DataFrame())
    liberators = data.get("liberadores", {})

    if not isinstance(flow, pd.DataFrame) or flow.empty:
        st.warning("No existe un flujo interno válido.")
        return

    changes = data.get("cambios", pd.DataFrame())
    changes_count = (
        len(changes)
        if isinstance(changes, pd.DataFrame)
        else 0
    )
    active_count = 8 if changes_count else 7

    st.success(
        (
            f"{active_count} archivos activos · "
            f"**{len(flow):,} reglas internas** · "
            f"**{flow['CECO'].nunique():,} CECO**"
            + (
                f" · **{changes_count:,} cambios históricos**"
                if changes_count
                else ""
            )
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

    tab_labels = (
        [f"Liberador {level}" for level in LEVELS]
        + ["CECO-Plantas", "Usuarios-Cargos"]
    )
    if changes_count:
        tab_labels.append("Cambios")

    tabs = st.tabs(tab_labels)

    for level, tab in zip(LEVELS, tabs[:5]):
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

    with tabs[5]:
        st.dataframe(
            data.get("dic_ceco", pd.DataFrame()).head(300),
            use_container_width=True,
            hide_index=True,
        )

    with tabs[6]:
        st.dataframe(
            data.get("dic_users", pd.DataFrame()).head(300),
            use_container_width=True,
            hide_index=True,
        )

    if changes_count:
        with tabs[7]:
            st.dataframe(
                changes.head(500),
                use_container_width=True,
                hide_index=True,
            )

    render_export_section(data)

    if st.button(
        "🗑️ Quitar la versión cargada",
        use_container_width=True,
    ):
        clear_active_files()
        st.rerun()


def main() -> None:
    aplicar_estilos()
    render_header()

    st.markdown(
        '<div class="fl-section-title">Cargar versión completa</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="fl-help">
            Carga manualmente Liberador 1–5, CECO–Plantas y
            Usuarios–Cargos, con Cambios opcional, o conecta un ZIP
            remoto configurado mediante Requests y Secrets.
        </div>
        """,
        unsafe_allow_html=True,
    )

    load_method = st.radio(
        "Método de carga",
        options=["Carga manual", "Conexión Requests + Secrets"],
        horizontal=True,
        key="flujo_load_method_v01",
    )

    if load_method == "Carga manual":
        st.session_state.pop(SESSION_REMOTE_FILES_KEY, None)
        uploaded_files = render_uploader()
    else:
        uploaded_files = render_remote_connection()

    # Antes de cargar los archivos obligatorios no se muestra contenido adicional.
    if not uploaded_files:
        if load_method == "Carga manual":
            st.info(
                "Los nombres deben identificar Liberador 1–5, "
                "CECO-Plantas, Usuarios-Cargos y opcionalmente Cambios."
            )
        else:
            st.info(
                "Configura Secrets, ingresa la clave autorizada "
                "y conecta el ZIP remoto."
            )
        return

    missing = [
        role
        for role in REQUIRED_FILE_ROLES
        if role not in uploaded_files
    ]

    if missing:
        st.warning(
            "Faltan archivos: "
            + ", ".join(role_label(role) for role in missing)
            + "."
        )
        return

    signature = files_signature(uploaded_files)

    needs_load = (
        st.session_state.get(SESSION_SIGNATURE_KEY) != signature
        or SESSION_DATA_KEY not in st.session_state
    )

    if needs_load:
        progress_bar = st.progress(
            0,
            text="0% · Preparando la carga...",
        )
        status_placeholder = st.empty()

        def update_progress(percent: int, message: str) -> None:
            progress_bar.progress(
                percent,
                text=f"{percent}% · {message}",
            )
            status_placeholder.caption(message)

        try:
            data, source_bytes, validation = load_seven_files(
                uploaded_files,
                progress_callback=update_progress,
            )

            names = {
                role: uploaded_file.name
                for role, uploaded_file in uploaded_files.items()
            }

            st.session_state[SESSION_DATA_KEY] = data
            st.session_state[SESSION_FILE_KEY] = names
            st.session_state[SESSION_SOURCE_FILES_KEY] = source_bytes
            st.session_state[SESSION_FILE_BYTES_KEY] = source_bytes
            st.session_state[SESSION_SIGNATURE_KEY] = signature
            st.session_state[SESSION_VALIDATION_KEY] = validation
            st.session_state[SESSION_CHANGES_KEY] = data.get(
                "cambios",
                pd.DataFrame(columns=CHANGE_COLUMNS),
            )
            st.session_state.pop(SESSION_CASE_KEY, None)

            loaded_count = len(uploaded_files)
            progress_bar.progress(
                100,
                text=(
                    f"100% · {loaded_count} de {loaded_count} "
                    "archivos cargados correctamente."
                ),
            )
            status_placeholder.success(
                "Versión validada y activada correctamente."
            )
            st.toast(
                f"{loaded_count} archivos cargados correctamente.",
                icon="✅",
            )
            st.rerun()

        except (ValueError, requests.RequestException) as error:
            progress_bar.progress(
                0,
                text="Carga interrumpida.",
            )
            status_placeholder.empty()
            clear_active_files()
            st.error(str(error))
            return

    # Solo después de una carga válida aparecen los demás elementos.
    render_active_state()


if __name__ == "__main__":
    main()
