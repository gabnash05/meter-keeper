import os
import sqlite3
from flask import current_app, g

################## Define the database connection and initialization functions #################

def get_db():
    """Get a database connection from the application context."""
    
    if "db" not in g:
        db_path = current_app.config["DATABASE_PATH"]
        g.db = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES,
            check_same_thread=False,
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Close the database connection if it exists."""

    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database from schema.sql in migrations directory"""

    db = get_db()
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        db.executescript(f.read())
    db.commit()

################## Query and Execute Functions #################

def query_one(sql, params=()):
    cur = get_db().execute(sql, params)
    row = cur.fetchone()
    cur.close()
    return row

def query_all(sql, params=()):
    cur = get_db().execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    return rows

def execute(sql, params=()):
    db = get_db()
    cur = db.execute(sql, params)
    db.commit()
    last_id = cur.lastrowid
    cur.close()
    return last_id