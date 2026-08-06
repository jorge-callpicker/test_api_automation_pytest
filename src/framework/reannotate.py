from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path

_TC_RE = re.compile(r"tc[-_]?(\d+)", re.IGNORECASE)

_OUTCOME_MAP = {
    "passed": "PASSED",
    "failed": "FAILED",
    "skipped": "SKIPPED",
}


def _tc_id_from_nodeid(nodeid: str) -> str | None:
    match = _TC_RE.search(nodeid)
    if not match:
        return None
    return f"TC-{match.group(1)}"


def _load_results(results_path: Path) -> dict[str, tuple[str, str]]:
    with results_path.open(encoding="utf-8") as f:
        report = json.load(f)

    created = report.get("created")
    if created is not None:
        timestamp = datetime.fromtimestamp(created, tz=UTC).isoformat()
    else:
        timestamp = datetime.now(tz=UTC).isoformat()

    results: dict[str, tuple[str, str]] = {}
    for test in report.get("tests", []):
        tc_id = _tc_id_from_nodeid(test.get("nodeid", ""))
        if tc_id is None:
            continue
        raw_outcome = test.get("outcome", "")
        outcome = _OUTCOME_MAP.get(raw_outcome, raw_outcome.upper())
        results[tc_id] = (outcome, timestamp)
    return results


def _tc_column(fieldnames: list[str]) -> str:
    for candidate in ("TC", "id"):
        if candidate in fieldnames:
            return candidate
    raise ValueError("El CSV no tiene columna 'TC' ni 'id' para matchear los resultados")


def reannotate(matrix_path: Path, results_path: Path) -> None:
    results = _load_results(results_path)

    with matrix_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    tc_column = _tc_column(fieldnames)
    for column in ("ultimo_resultado", "ultima_ejecucion"):
        if column not in fieldnames:
            fieldnames.append(column)

    for row in rows:
        tc_id = row.get(tc_column, "")
        if tc_id in results:
            outcome, timestamp = results[tc_id]
            row["ultimo_resultado"] = outcome
            row["ultima_ejecucion"] = timestamp

    with matrix_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reanota la matriz CSV con resultados de pytest-json-report."
    )
    parser.add_argument("--matrix", required=True, type=Path)
    parser.add_argument("--results", required=True, type=Path)
    args = parser.parse_args()
    reannotate(args.matrix, args.results)


if __name__ == "__main__":
    main()
