"""Currencies"""

import json
from pathlib import Path
from typing import List, Any, Dict

from mariadb.connections import Connection


def _reshape_row(row: Dict[str, str]) -> Dict[str, Any]:
    return {
        'name': row['name'],
        'ccy': row['ccy'],
        'minor_unit': row['minor_unit'],
        'numeric_code': row['numeric_code']
    }


def _load_data() -> List[Dict[str, Any]]:
    root = Path('jetblack_finance/db/data')
    with open(root / "currencies.json", "rt", encoding="utf-8") as file_ptr:
        raw_data = json.load(file_ptr)
        data = []
        for row in raw_data:
            data.append(_reshape_row(row))
        return data


def _create_table(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
CREATE TABLE currency
(
	currency_id  INT          NOT NULL AUTO_INCREMENT,
    name         VARCHAR(200) NOT NULL,
    ccy          CHAR(3)      NOT NULL,
    minor_unit   INT          NULL,
    numeric_code INT          NOT NULL,

    PRIMARY KEY (currency_id),
    UNIQUE (name),
    UNIQUE (ccy)
) WITH SYSTEM VERSIONING;
""")
        conn.commit()


def _insert_data(conn: Connection, data: List[Dict[str, Any]]) -> None:
    sql = """
INSERT INTO currency(name, ccy, minor_unit, numeric_code)
VALUES (?, ?, ?, ?);
"""
    args = [
        (
            item['name'],
            item['ccy'],
            item['minor_unit'],
            item['numeric_code']
        )
        for item in data
    ]

    with conn.cursor() as cur:
        cur.executemany(sql, args)
        conn.commit()


def create_currencies(conn: Connection) -> None:
    print("Creating the currencies")
    _create_table(conn)
    data = _load_data()
    _insert_data(conn, data)
