"""
SQLite database for persistent chat history.
"""
import sqlite3
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import uuid

from ..config import config

logger = logging.getLogger(__name__)


class ChatDB:
    """
    Manages chat history persistence using SQLite.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize Chat DB.

        Args:
            db_path: Path to database file
        """
        self.db_path = db_path or config.CHAT_DB_PATH
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialize database schema."""
        try:
            with self._get_conn() as conn:
                # Sessions table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Messages table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        session_id TEXT,
                        role TEXT,
                        content TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(session_id) REFERENCES sessions(id) ON DELETE CASCADE
                    )
                """)
                
                # Indexes
                conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_updated ON sessions(updated_at DESC)")
                
        except Exception as e:
            logger.error(f"Failed to initialize chat database: {e}")
            raise

    def create_session(self, title: str = "New Chat") -> str:
        """Create a new chat session."""
        session_id = str(uuid.uuid4())
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, updated_at) VALUES (?, ?, ?)",
                (session_id, title, datetime.now())
            )
        return session_id

    def get_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent chat sessions."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific session."""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_session_title(self, session_id: str, title: str):
        """Update session title."""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, datetime.now(), session_id)
            )

    def delete_session(self, session_id: str):
        """Delete a session and its messages."""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to a session."""
        message_id = str(uuid.uuid4())
        meta_json = json.dumps(metadata) if metadata else "{}"
        
        with self._get_conn() as conn:
            # Add message
            conn.execute(
                """
                INSERT INTO messages (id, session_id, role, content, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (message_id, session_id, role, content, meta_json, datetime.now())
            )
            
            # Touch session updated_at
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (datetime.now(), session_id)
            )
            
        return message_id

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,)
            )
            messages = []
            for row in cursor:
                msg = dict(row)
                if msg["metadata"]:
                    try:
                        msg["metadata"] = json.loads(msg["metadata"])
                    except Exception:
                        msg["metadata"] = {}
                messages.append(msg)
            return messages
