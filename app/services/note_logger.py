# app/services/note_logger.py
from app.utils.db import get_db_connection
from app.core.logger import get_logger

logger = get_logger(__name__)

def log_note(content: str, **kwargs) -> dict:
    """V3: Logs a note to the database and returns a result dictionary."""
    if not content:
        return {"status": "failed", "message": "There was nothing to note down."}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        conn.commit()
        conn.close()
        logger.info(f"Note saved: {content}")
        return {"status": "success", "message": "Noted."}
    except Exception as e:
        logger.exception("Failed to save note.")
        return {"status": "error", "message": "I couldn't save that note due to a database error."}

def read_recent_notes(limit=5, **kwargs) -> dict:
    """V3: Reads notes and returns them in the message."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM notes ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return {"status": "success", "message": "You don't have any recent notes."}
        
        notes_text = "Here are your latest notes: " + ". ".join([row['content'] for row in rows])
        return {"status": "success", "message": notes_text}
    except Exception as e:
        logger.exception("Failed to retrieve notes.")
        return {"status": "error", "message": "I couldn't fetch your notes from the database."}