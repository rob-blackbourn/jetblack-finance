"""Currencies"""

import json
from pathlib import Path
from typing import List, Any, Dict

from mariadb.connections import Connection


def _reshape_row(row: Dict[str, str]) -> Dict[str, Any]:
    return {
        'name': row['name'],
    }


def _load_data() -> List[Dict[str, Any]]:
    root = Path('jetblack_finance/db/data')
    file_name = root / "instrument_types.json"
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
CREATE TABLE instrument_type
(
    instrument_type_id  INT             NOT NULL    AUTO_INCREMENT,
    name                VARCHAR(256)    NOT NULL,

    PRIMARY KEY (instrument_type_id)
) WITH SYSTEM VERSIONING;
""")
        conn.commit()


def _insert_data(conn: Connection, data: List[Dict[str, Any]]) -> None:
    sql = """
INSERT INTO instrument_type(name)
VALUES (?);
"""
    args = [
        (
            item['name'],
        )
        for item in data
    ]

    with conn.cursor() as cur:
        cur.executemany(sql, args)
        conn.commit()


def create_instrument_types(conn: Connection) -> None:
    print("Creating the instrument types")
    _create_table(conn)
    data = _load_data()
    _insert_data(conn, data)
