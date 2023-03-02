import sys
import unittest
from pathlib import Path

from src.genesis.db.table_manager import DBTypes, TableManager
from tests.helpers.clients import TestWithDBConn

src_path = Path(__file__).parent.parent.parent.parent.absolute()
sys.path.append(str(src_path))


class TestTableManager(TestWithDBConn):
    test_table = "table_manager_testing"
    table_manager: TableManager

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        table = cls.test_table
        columns = (
            ("text_column", DBTypes.text),
            ("numeric_column", DBTypes.numeric),
        )
        indexes = ("numeric_column",)
        cls.table_manager = TableManager(cls.db_conn, table, columns, indexes)

    @classmethod
    def setUp(cls) -> None:
        with cls.db_conn.cursor() as db:
            db.execute(
                f"""
                DROP TABLE IF EXISTS {cls.test_table};
            """
            )

    def test__ensure_table(self) -> None:
        exists = self.table_manager.table_exists(self.test_table)
        self.assertFalse(exists)

        self.table_manager.ensure_table()
        exists = self.table_manager.table_exists(self.test_table)
        self.assertTrue(exists)

    # TODO: test cascade
    # NB: _drop_table test depends on _ensure_table's correctness
    def test__drop_table(self) -> None:
        self.table_manager.ensure_table()
        exists = self.table_manager.table_exists(self.test_table)
        self.assertTrue(exists)

        self.table_manager.drop_table()
        exists = self.table_manager.table_exists(self.test_table)
        self.assertFalse(exists)


if __name__ == "__main__":
    unittest.main()
