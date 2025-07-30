# app/services/note_service.py
from app.utils.db import get_db_connection
from app.core.logger import get_logger

logger = get_logger(__name__)

# THE FIX: Changed the parameter name from 'content' to 'note_content'
def log_note(note_content: str, **kwargs) -> dict:
    """Logs a note to the database."""
    if not note_content:
        return {"status": "failed", "message": "There was nothing to note down."}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (content) VALUES (?)", (note_content,))
        conn.commit()
        conn.close()
        logger.info(f"Note saved: {note_content}")
        return {"status": "success", "message": "Noted."}
    except Exception as e:
        logger.exception("Failed to save note.")
        return {"status": "error", "message": "I couldn't save that note."}

def read_notes(limit=5, **kwargs) -> dict:
    """Reads recent notes from the database."""
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
        return {"status": "error", "message": "I couldn't fetch your notes."}