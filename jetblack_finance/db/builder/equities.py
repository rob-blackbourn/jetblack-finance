"""Currencies"""

import json
from pathlib import Path
from typing import List, Any, Dict

from mariadb.connections import Connection


def _reshape_row(row: Dict[str, str]) -> Dict[str, Any]:
    return {
        'name': row['name'],
        'ccy': row['ccy'],
    }


def _load_data() -> List[Dict[str, Any]]:
    root = Path('jetblack_finance/db/data')
    file_name = root / "equities.json"
    if not file_name.exists():
        return []

    with open(file_name, "rt", encoding="utf-8") as file_ptr:
        raw_data = json.load(file_ptr)
        data = []
        for row in raw_data:
            data.append(_reshape_row(row))
        return data


def _create_table(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
CREATE TABLE equity
(
    instrument_id           INT     NOT NULL,
    currency_id             INT     NOT NULL,

    PRIMARY KEY (instrument_id),
    FOREIGN KEY (instrument_id) REFERENCES instrument(instrument_id),
    FOREIGN KEY (currency_id) REFERENCES currency(currency_id)
) WITH SYSTEM VERSIONING;
""")
        conn.commit()


def _insert_data(conn: Connection, data: List[Dict[str, Any]]) -> None:
    sql_instrument = """
INSERT INTO instrument(instrument_type_id, name)
SELECT it.instrument_type_id, ?
FROM instrument_type AS it
WHERE it.name = ?;
"""
    sql_equity = """
INSERT INTO equity(instrument_id, currency_id)
SELECT i.instrument_id, c.currency_id
FROM instrument AS i, currency AS c
WHERE i.name = ?
AND c.ccy = ?;
"""
    with conn.cursor() as cur:
        for item in data:
            cur.execute(sql_instrument, (item['name'], 'EQUITY'))
            cur.execute(sql_equity, (item['name'], item['ccy']))
            conn.commit()


def create_equities(conn: Connection) -> None:
    print("Creating equity instruments")
    _create_table(conn)
    data = _load_data()
    _insert_data(conn, data)
