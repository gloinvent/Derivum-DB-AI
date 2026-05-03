"""
Unit tests for execute_query().
All psycopg2 calls are mocked — no live DB needed.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.sql_validator import validate_read_only
from app.services.query_executor import execute_query


def _make_cursor(rows: list[dict]):
    """Return a mock cursor whose fetchall() returns RealDict-like rows."""
    cur = MagicMock()
    cur.__enter__ = lambda s: s
    cur.__exit__ = MagicMock(return_value=False)
    cur.fetchall.return_value = [dict(r) for r in rows]
    return cur


def _make_conn(cursor):
    conn = MagicMock()
    conn.__enter__ = lambda s: s
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor
    return conn


class TestValidateReadOnly:
    def test_valid_select_passes(self):
        validate_read_only('SELECT * FROM public."PDB_isin_records" LIMIT 10;')

    def test_select_with_joins_passes(self):
        validate_read_only(
            'SELECT ir.* FROM public."PDB_isin_records" ir '
            'JOIN public."PDB_tag" t ON ir.id = t.isin_id WHERE t.tag = \'PSU\';'
        )

    def test_insert_blocked(self):
        with pytest.raises(ValueError):
            validate_read_only('INSERT INTO public."PDB_isin_records" (isin) VALUES (\'X\');')

    def test_update_blocked(self):
        with pytest.raises(ValueError):
            validate_read_only('UPDATE public."PDB_isin_records" SET isin = \'X\' WHERE id = 1;')

    def test_delete_blocked(self):
        with pytest.raises(ValueError):
            validate_read_only('DELETE FROM public."PDB_isin_records" WHERE id = 1;')

    def test_truncate_blocked(self):
        with pytest.raises(ValueError):
            validate_read_only('TRUNCATE TABLE public."PDB_isin_records";')

    def test_drop_blocked(self):
        with pytest.raises(ValueError):
            validate_read_only('DROP TABLE public."PDB_isin_records";')

    def test_with_cte_passes(self):
        validate_read_only('WITH ranked AS (SELECT *, ROW_NUMBER() OVER (ORDER BY id) AS rn FROM t) SELECT * FROM ranked LIMIT 10;')

    def test_cte_containing_write_op_blocked(self):
        with pytest.raises(ValueError):
            validate_read_only('WITH x AS (DELETE FROM t RETURNING *) SELECT * FROM x;')

    def test_execute_query_blocked_on_write(self):
        """execute_query must not open a DB connection for a write query."""
        with patch("app.services.query_executor._get_connection") as mock_conn:
            with pytest.raises(ValueError):
                execute_query('DELETE FROM public."PDB_isin_records";')
        mock_conn.assert_not_called()


class TestExecuteQuery:
    def test_returns_rows_and_elapsed(self):
        rows = [{"isin": "INE001A07KL8", "name_of_the_instrument": "BOND A"}]
        cur = _make_cursor(rows)
        conn = _make_conn(cur)
        with patch("app.services.query_executor._get_connection", return_value=conn):
            result, elapsed = execute_query('SELECT * FROM public."PDB_isin_records" LIMIT 1;')
        assert isinstance(result, list)
        assert result == rows
        assert isinstance(elapsed, float) and elapsed >= 0

    def test_empty_result_returns_empty_list(self):
        cur = _make_cursor([])
        conn = _make_conn(cur)
        with patch("app.services.query_executor._get_connection", return_value=conn):
            result, elapsed = execute_query("SELECT 1 WHERE false;")
        assert result == []
        assert elapsed >= 0

    def test_connection_closed_after_query(self):
        cur = _make_cursor([{"count": 5}])
        conn = _make_conn(cur)
        with patch("app.services.query_executor._get_connection", return_value=conn):
            execute_query("SELECT COUNT(*) FROM x;")
        conn.close.assert_called_once()

    def test_connection_closed_on_exception(self):
        cur = MagicMock()
        cur.__enter__ = lambda s: s
        cur.__exit__ = MagicMock(return_value=False)
        cur.execute.side_effect = Exception("column does not exist")
        conn = _make_conn(cur)
        with patch("app.services.query_executor._get_connection", return_value=conn):
            with pytest.raises(Exception, match="column does not exist"):
                execute_query('SELECT nonexistent_col FROM public."PDB_isin_records";')
        conn.close.assert_called_once()

    def test_sql_is_executed_as_given(self):
        sql = 'SELECT * FROM public."PDB_isin_records" LIMIT 5;'
        cur = _make_cursor([])
        conn = _make_conn(cur)
        with patch("app.services.query_executor._get_connection", return_value=conn):
            execute_query(sql)
        cur.execute.assert_called_once_with(sql)

    def test_multiple_rows_returned(self):
        rows = [{"isin": f"ISIN{i}"} for i in range(10)]
        cur = _make_cursor(rows)
        conn = _make_conn(cur)
        with patch("app.services.query_executor._get_connection", return_value=conn):
            result, _ = execute_query("SELECT * FROM x LIMIT 10;")
        assert len(result) == 10
        assert result[0]["isin"] == "ISIN0"
        assert result[9]["isin"] == "ISIN9"
