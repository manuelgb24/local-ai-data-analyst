"""Minimal DuckDB adapter for local dataset loading during the MVP."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import duckdb


def quote_identifier(identifier: str) -> str:
    escaped = identifier.replace('"', '""')
    return f'"{escaped}"'


class DuckDBContext:
    """Thin wrapper over a DuckDB connection used by a single run."""

    def __init__(self, connection: duckdb.DuckDBPyConnection) -> None:
        self._connection = connection

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        return self._connection

    def execute(self, sql: str, parameters: Sequence[object] | None = None) -> duckdb.DuckDBPyConnection:
        if parameters is None:
            return self._connection.execute(sql)
        return self._connection.execute(sql, parameters)

    def fetchone(self, sql: str, parameters: Sequence[object] | None = None) -> tuple[object, ...]:
        result = self.execute(sql, parameters).fetchone()
        if result is None:
            raise ValueError("Expected one row but query returned none")
        return result

    def fetchall(self, sql: str, parameters: Sequence[object] | None = None) -> list[tuple[object, ...]]:
        return self.execute(sql, parameters).fetchall()

    def create_table_from_select(
        self,
        table_name: str,
        select_sql: str,
        parameters: Sequence[object] | None = None,
    ) -> None:
        self.execute(f"CREATE TABLE {quote_identifier(table_name)} AS {select_sql}", parameters)

    def create_table(self, table_name: str, columns: Sequence[tuple[str, str]]) -> None:
        definition = ", ".join(
            f"{quote_identifier(column_name)} {column_type}" for column_name, column_type in columns
        )
        self.execute(f"CREATE TABLE {quote_identifier(table_name)} ({definition})")

    def insert_many(self, table_name: str, rows: Iterable[Sequence[object]], column_count: int) -> None:
        placeholders = ", ".join(["?"] * column_count)
        self.connection.executemany(
            f"INSERT INTO {quote_identifier(table_name)} VALUES ({placeholders})",
            list(rows),
        )

    def alter_column_type(self, table_name: str, column_name: str, column_type: str) -> None:
        self.execute(
            " ".join(
                [
                    f"ALTER TABLE {quote_identifier(table_name)}",
                    f"ALTER COLUMN {quote_identifier(column_name)}",
                    f"SET DATA TYPE {column_type}",
                ]
            )
        )

    def describe_table(self, table_name: str) -> list[tuple[object, ...]]:
        return self.fetchall(f"DESCRIBE {quote_identifier(table_name)}")

    def close(self) -> None:
        self._connection.close()


def create_duckdb_context() -> DuckDBContext:
    return DuckDBContext(connection=duckdb.connect(database=":memory:"))
