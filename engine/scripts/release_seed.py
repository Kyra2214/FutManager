#!/usr/bin/env python3
"""Sanitize and validate the GameState database used in release artifacts.

The release seed must describe a new installation, never a manager session from
an author's local workspace.  This utility intentionally fails closed when one
of the career-state tables contains rows after sanitization.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import tempfile
import sqlite3
import shutil
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

CAREER_TABLES = (
    "manager_selection_assignments",
    "manager_careers",
    "managers",
)


@contextmanager
def _open_database(source: Path) -> Iterator[tuple[sqlite3.Connection, Path]]:
    """Yield a writable temporary SQLite database for a .db or .db.gz source."""
    temporary = tempfile.NamedTemporaryFile(prefix="futmanager-release-seed-", suffix=".db")
    temporary_path = Path(temporary.name)
    temporary.close()
    try:
        if source.name.endswith(".gz"):
            with gzip.open(source, "rb") as compressed, temporary_path.open("wb") as database:
                shutil.copyfileobj(compressed, database)
        else:
            shutil.copyfile(source, temporary_path)
        connection = sqlite3.connect(temporary_path)
        try:
            yield connection, temporary_path
        finally:
            connection.close()
    finally:
        temporary_path.unlink(missing_ok=True)


def _table_counts(connection: sqlite3.Connection) -> dict[str, int]:
    existing = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    return {
        table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
        for table in CAREER_TABLES
        if table in existing
    }


def _assert_empty(counts: dict[str, int], source: Path) -> None:
    non_empty = {table: count for table, count in counts.items() if count}
    if non_empty:
        details = ", ".join(f"{table}={count}" for table, count in non_empty.items())
        raise SystemExit(f"Release seed contains manager state ({details}): {source}")


def validate(source: Path) -> dict[str, int]:
    with _open_database(source) as database:
        connection, _ = database
        counts = _table_counts(connection)
        _assert_empty(counts, source)
        return counts


def sanitize(source: Path, destination: Path) -> dict[str, int]:
    if source.resolve() == destination.resolve():
        raise SystemExit("Sanitization requires a distinct output path")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with _open_database(source) as database:
        connection, temporary_path = database
        existing = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        for table in CAREER_TABLES:
            if table in existing:
                connection.execute(f'DELETE FROM "{table}"')
        connection.commit()
        connection.execute("VACUUM")
        counts = _table_counts(connection)
        _assert_empty(counts, source)
        connection.close()
        with temporary_path.open("rb") as database_file:
            if destination.name.endswith(".gz"):
                with destination.open("wb") as compressed_file:
                    with gzip.GzipFile(filename="", mode="wb", fileobj=compressed_file, mtime=0) as compressed:
                        shutil.copyfileobj(database_file, compressed)
            else:
                with destination.open("wb") as output:
                    shutil.copyfileobj(database_file, output)
    return counts


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="fail if manager state is present")
    validate_parser.add_argument("source", type=Path)

    sanitize_parser = subparsers.add_parser("sanitize", help="write a clean release seed")
    sanitize_parser.add_argument("source", type=Path)
    sanitize_parser.add_argument("destination", type=Path)

    args = parser.parse_args()
    if args.command == "validate":
        counts = validate(args.source)
        print(f"Release seed is clean: {args.source} ({counts})")
    else:
        counts = sanitize(args.source, args.destination)
        print(f"Sanitized release seed: {args.destination} ({counts}, sha256={checksum(args.destination)})")


if __name__ == "__main__":
    main()
