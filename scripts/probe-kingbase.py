#!/usr/bin/env python3
"""Kingbase / PostgreSQL 连通性探针。用法：python scripts/probe-kingbase.py <DATABASE_URL>"""

import sys

from sqlalchemy import create_engine, text


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python scripts/probe-kingbase.py <DATABASE_URL>")
        sys.exit(1)
    url = sys.argv[1]
    engine = create_engine(url)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        conn.execute(text("SELECT '{}'::jsonb"))
    print("OK:", version)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("FAIL:", exc)
        sys.exit(1)
