"""
utils/history_manager.py
Gestión del historial de comprensiones con SQLite.
"""

from __future__ import annotations
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .logger import get_logger
from models.history_entry import HistoryEntry

logger = get_logger("history")

_DB_PATH = Path(__file__).parent.parent / "history.db"

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS history (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        TEXT NOT NULL,
    filename         TEXT NOT NULL,
    file_type        TEXT NOT NULL,
    original_size    INTEGER NOT NULL,
    final_size       INTEGER NOT NULL,
    reduction_percent REAL NOT NULL,
    elapsed_seconds  REAL NOT NULL,
    output_path      TEXT NOT NULL,
    method_used      TEXT NOT NULL,
    success          INTEGER NOT NULL
);
"""


class HistoryManager:
    """
    Gestiona el historial persistente de comprensiones.

    Usa SQLite estándar sin dependencias externas.
    La base de datos se crea automáticamente en history.db.
    """

    def __init__(self, db_path: Path = _DB_PATH) -> None:
        self._db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Crea la tabla si no existe."""
        try:
            with self._get_connection() as conn:
                conn.execute(_CREATE_TABLE_SQL)
                conn.commit()
            logger.debug("Base de datos de historial inicializada en %s", self._db_path)
        except sqlite3.Error as exc:
            logger.error("Error al inicializar la base de datos: %s", exc)

    def add_entry(self, entry: HistoryEntry) -> None:
        """Inserta una nueva entrada en el historial."""
        sql = """
            INSERT INTO history
                (timestamp, filename, file_type, original_size, final_size,
                 reduction_percent, elapsed_seconds, output_path, method_used, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self._get_connection() as conn:
                conn.execute(sql, (
                    entry.timestamp.isoformat(),
                    entry.filename,
                    entry.file_type,
                    entry.original_size,
                    entry.final_size,
                    entry.reduction_percent,
                    entry.elapsed_seconds,
                    entry.output_path,
                    entry.method_used,
                    1 if entry.success else 0,
                ))
                conn.commit()
            logger.debug("Historial: entrada agregada para %s", entry.filename)
        except sqlite3.Error as exc:
            logger.error("Error al guardar en historial: %s", exc)

    def get_all(self, limit: int = 500) -> list[HistoryEntry]:
        """Retorna las últimas N entradas ordenadas por fecha desc."""
        sql = "SELECT * FROM history ORDER BY id DESC LIMIT ?"
        try:
            with self._get_connection() as conn:
                rows = conn.execute(sql, (limit,)).fetchall()
            return [_row_to_entry(row) for row in rows]
        except sqlite3.Error as exc:
            logger.error("Error al leer historial: %s", exc)
            return []

    def get_stats(self) -> dict:
        """Retorna estadísticas globales del historial."""
        sql = """
            SELECT
                COUNT(*) as total,
                SUM(original_size) as total_original,
                SUM(final_size) as total_final,
                AVG(reduction_percent) as avg_reduction,
                SUM(original_size - final_size) as total_saved
            FROM history
            WHERE success = 1
        """
        try:
            with self._get_connection() as conn:
                row = conn.execute(sql).fetchone()
            return {
                "total": row["total"] or 0,
                "total_original": row["total_original"] or 0,
                "total_final": row["total_final"] or 0,
                "avg_reduction": round(row["avg_reduction"] or 0, 1),
                "total_saved": row["total_saved"] or 0,
            }
        except sqlite3.Error as exc:
            logger.error("Error al calcular estadísticas: %s", exc)
            return {}

    def clear(self) -> None:
        """Elimina todo el historial."""
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM history")
                conn.commit()
            logger.info("Historial eliminado.")
        except sqlite3.Error as exc:
            logger.error("Error al limpiar historial: %s", exc)


def _row_to_entry(row: sqlite3.Row) -> HistoryEntry:
    """Convierte una fila SQLite a HistoryEntry."""
    return HistoryEntry(
        id=row["id"],
        timestamp=datetime.fromisoformat(row["timestamp"]),
        filename=row["filename"],
        file_type=row["file_type"],
        original_size=row["original_size"],
        final_size=row["final_size"],
        reduction_percent=row["reduction_percent"],
        elapsed_seconds=row["elapsed_seconds"],
        output_path=row["output_path"],
        method_used=row["method_used"],
        success=bool(row["success"]),
    )
