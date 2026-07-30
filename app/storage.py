import json
from pathlib import Path
from threading import Lock
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

CHAT_HISTORY_FILE = DATA_DIR / "chat_history.json"
FEEDBACK_FILE = DATA_DIR / "feedback.json"

_file_lock = Lock()


def ensure_storage_files() -> None:
    """Create the data directory and JSON files when missing."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for file_path in (CHAT_HISTORY_FILE, FEEDBACK_FILE):
        if not file_path.exists():
            file_path.write_text("[]", encoding="utf-8")


def read_json_list(file_path: Path) -> list[dict[str, Any]]:
    """Read a JSON array from disk."""

    ensure_storage_files()

    with _file_lock:
        try:
            content = file_path.read_text(encoding="utf-8")
            parsed = json.loads(content)

            if isinstance(parsed, list):
                return parsed

            return []
        except (json.JSONDecodeError, OSError):
            return []


def write_json_list(
    file_path: Path,
    records: list[dict[str, Any]],
) -> None:
    """Write a JSON array to disk."""

    ensure_storage_files()

    with _file_lock:
        file_path.write_text(
            json.dumps(records, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def append_json_record(
    file_path: Path,
    record: dict[str, Any],
    maximum_records: int | None = None,
) -> None:
    """Append one record to a JSON array."""

    records = read_json_list(file_path)
    records.append(record)

    if maximum_records is not None:
        records = records[-maximum_records:]

    write_json_list(file_path, records)