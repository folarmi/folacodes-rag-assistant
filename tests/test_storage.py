import json
from pathlib import Path

from app.storage import (
    append_json_record,
    read_json_list,
    write_json_list,
)


def test_read_json_list_returns_records(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "records.json"

    file_path.write_text(
        json.dumps([{"id": "one"}]),
        encoding="utf-8",
    )

    records = read_json_list(file_path)

    assert records == [{"id": "one"}]


def test_read_json_list_returns_empty_for_invalid_json(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "invalid.json"
    file_path.write_text("invalid JSON", encoding="utf-8")

    records = read_json_list(file_path)

    assert records == []


def test_write_json_list_writes_records(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "records.json"

    write_json_list(
        file_path,
        [{"id": "one"}, {"id": "two"}],
    )

    records = json.loads(
        file_path.read_text(encoding="utf-8")
    )

    assert records == [
        {"id": "one"},
        {"id": "two"},
    ]


def test_append_json_record_adds_record(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "records.json"
    file_path.write_text("[]", encoding="utf-8")

    append_json_record(
        file_path,
        {"id": "one"},
    )

    records = json.loads(
        file_path.read_text(encoding="utf-8")
    )

    assert records == [{"id": "one"}]


def test_append_json_record_respects_maximum_records(
    tmp_path: Path,
) -> None:
    file_path = tmp_path / "records.json"

    file_path.write_text(
        json.dumps(
            [
                {"id": "one"},
                {"id": "two"},
            ]
        ),
        encoding="utf-8",
    )

    append_json_record(
        file_path,
        {"id": "three"},
        maximum_records=2,
    )

    records = json.loads(
        file_path.read_text(encoding="utf-8")
    )

    assert records == [
        {"id": "two"},
        {"id": "three"},
    ]