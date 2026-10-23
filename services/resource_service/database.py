
import json
import sqlite3
from pathlib import Path
from contextlib import closing


DB_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "research_workspace.db"
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


def init_db():
    with closing(get_connection()) as conn:
        with conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_username TEXT NOT NULL,
                    name TEXT NOT NULL,
                    rows_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS exports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id INTEGER NOT NULL,
                    filename TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dataset_id)
                        REFERENCES datasets(id)
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    actor_username TEXT NOT NULL,
                    action TEXT NOT NULL,
                    dataset_id INTEGER,
                    outcome TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_datasets_owner
                    ON datasets(owner_username);
            """)

    print(f"Database initialized: {DB_PATH}")


def create_dataset(
    owner_username: str,
    name: str,
    rows: list[dict]
) -> int:

    if not owner_username or not owner_username.strip():
        raise ValueError("Invalid owner")

    if not isinstance(name, str) or not (1 <= len(name.strip()) <= 100):
        raise ValueError("Dataset name must be 1-100 characters")

    if not isinstance(rows, list) or not (1 <= len(rows) <= 1000):
        raise ValueError("Dataset must contain 1-1000 rows")

    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Each row must be an object")

    rows_json = json.dumps(rows, allow_nan=False)

    with closing(get_connection()) as conn:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO datasets
                    (owner_username, name, rows_json)
                VALUES (?, ?, ?)
                """,
                (owner_username, name.strip(), rows_json)
            )

            return cursor.lastrowid


def get_dataset(
    dataset_id: int,
    requester_username: str
) -> dict | None:

    with closing(get_connection()) as conn:
         result = conn.execute(
        """
        SELECT id, owner_username, name,
               rows_json, created_at
        FROM datasets
        WHERE id = ?
        """,
        (dataset_id,)
    ).fetchone()

    if result is None:
        return None

    return {
        "id": result["id"],
        "owner_username": result["owner_username"],
        "name": result["name"],
        "rows": json.loads(result["rows_json"]),
        "created_at": result["created_at"]
    }


if __name__ == "__main__":
    init_db()
