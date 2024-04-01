"""Books"""

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
    with open(root / "books.json", "rt", encoding="utf-8") as file_ptr:
        raw_data = json.load(file_ptr)
        data = []
        for row in raw_data:
            data.append(_reshape_row(row))
        return data


def _create_table(conn: Connection) -> None:
    with conn.cursor() as cur:
        cur.execute("""
CREATE TABLE book
(
    book_id     INT             NOT NULL    AUTO_INCREMENT,
    name        VARCHAR(256)    NOT NULL,

    PRIMARY KEY (book_id),
    UNIQUE (name)
) WITH SYSTEM VERSIONING;
""")
        conn.commit()


def _insert_data(conn: Connection, data: List[Dict[str, Any]]) -> None:
    sql = """
INSERT INTO book(name)
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


def create_books(conn: Connection) -> None:
    print("Creating the books")
    _create_table(conn)
    data = _load_data()
    _insert_data(conn, data)
