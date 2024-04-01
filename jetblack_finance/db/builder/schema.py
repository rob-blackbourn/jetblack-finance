"""Schema"""

from mariadb.connections import Connection


def create_schema(conn: Connection, schema_name) -> None:
    with conn.cursor() as cur:
        cur.execute(f"""
CREATE SCHEMA IF NOT EXISTS {schema_name}
CHARACTER SET = utf8mb4
COLLATE = utf8mb4_unicode_ci;
""")
        conn.commit()


def drop_schema(conn: Connection, schema_name) -> None:
    with conn.cursor() as cur:
        cur.execute(f"""
DROP SCHEMA IF EXISTS {schema_name}
""")
        conn.commit()
