"""
Standalone DB connectivity + permission check.
SAFE FOR PROD:
- Does NOT modify data
- Does NOT run INSERT/UPDATE/DELETE
- Only reads PostgreSQL metadata/catalog tables

Usage:
    python scripts/check_db_connection.py
"""

import sys

import psycopg2

from app.config import settings


def check_connection() -> None:
    print(
        f"Connecting to PostgreSQL at "
        f"{settings.db_host}:{settings.db_port} / {settings.db_name} ..."
    )

    try:
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            connect_timeout=5,
        )

        # extra safety
        conn.set_session(readonly=True, autocommit=True)

        cur = conn.cursor()

        # Connection test
        cur.execute("SELECT version();")
        row = cur.fetchone()
        version = row[0] if row else "unknown"

        print("Connection successful!")
        print(f"Server: {version}")

        # Current user
        cur.execute("SELECT current_user;")
        current_user = cur.fetchone()[0] # type: ignore

        print(f"\nCurrent User: {current_user}")

        # Role attributes
        cur.execute(
            """
            SELECT
                rolname,
                rolsuper,
                rolcreaterole,
                rolcreatedb
            FROM pg_roles
            WHERE rolname = current_user;
            """
        )

        role = cur.fetchone()

        if role:
            print("\nRole Attributes:")
            print(f"  Superuser     : {role[1]}")
            print(f"  Create Role   : {role[2]}")
            print(f"  Create DB     : {role[3]}")

        # Table privileges
        cur.execute(
            """
            SELECT DISTINCT privilege_type
            FROM information_schema.role_table_grants
            WHERE grantee = current_user
            ORDER BY privilege_type;
            """
        )

        privileges = [r[0] for r in cur.fetchall()]

        print("\nTable Privileges:")

        if privileges:
            for p in privileges:
                print(f"  - {p}")
        else:
            print("  No explicit table privileges found.")

        # Simple interpretation
        write_privs = {"INSERT", "UPDATE", "DELETE", "TRUNCATE"}

        has_write = any(p in write_privs for p in privileges)

        print("\nAccess Summary:")

        if has_write:
            print("  User HAS write permissions.")
        else:
            print("  User appears READ-ONLY.")

        cur.close()
        conn.close()

    except psycopg2.OperationalError as exc:
        print(f"Connection failed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    check_connection()