import itertools
from contextlib import contextmanager
from enum import Enum
from typing import Any, Generator, List, Tuple

from psycopg import Connection


class DBTypes(Enum):
    text = "text"
    numeric = "numeric"
    interface = "public.app_enum_0f6c2478ba"


class TableManager:
    def __init__(
        self,
        db_conn: Connection,
        table: str,
        columns: Tuple[Tuple[str, DBTypes], ...],
        indexes: Tuple[str, ...],
        schema: str = "app",
    ):
        self.db_conn = db_conn
        self.table = table
        self.columns = columns
        self.indexes = indexes
        self.schema = schema

    def get_column_names(self) -> Generator[str, Any, None]:
        return (name for name, _ in self.columns)

    def select_query(self, column_names: List[str]) -> str:
        res = self.db_conn.execute(
            f"""
            SELECT {",".join(column_names)} FROM {self.table}
        """
        ).fetchall()
        return list(itertools.chain(*res))

    def ensure_table(self):
        with self.db_conn.cursor() as db:
            db.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.schema}.{self.table} (
                    {", ".join([f"{name} {type_.value}" for name, type_ in self.columns])}
                );
                -- TODO: psycopg break out of transaction
                -- CREATE INDEX CONCURRENTLY ON {self.schema}.{self.table} ({",".join(self.indexes)})
            """
            )
            self.db_conn.commit()
            # TODO error checking / handling (?)

    def drop_table(self, cascade: bool = False):
        cascade_clause = ""
        if cascade:
            cascade_clause = "CASCADE"

        with self.db_conn.cursor() as db:
            db.execute(
                f"""
                DROP TABLE IF EXISTS {self.schema}.{self.table} {cascade_clause};
            """
            )
            self.db_conn.commit()
            # TODO error checking / handling (?)

    def table_exists(self, table: str) -> bool:
        with self.db_conn.cursor() as db:
            res_db_execute = db.execute(
                f"""
                    SELECT EXISTS (
                        SELECT FROM pg_tables WHERE
                            schemaname = 'app' AND
                            tablename  = '{table}'
                    )
                """
            ).fetchone()

            assert res_db_execute is not None

            return res_db_execute[0]

    @contextmanager
    def db_copy(self):
        with self.db_conn.cursor() as db:
            with db.copy(
                f'COPY {self.table} ({",".join(self.get_column_names())}) FROM STDIN'
            ) as copy:
                yield copy
        self.db_conn.commit()
