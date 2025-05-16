from app.utils.db import get_db_connection
from app.core.logger import get_logger
from app.services.text_to_speech import speak

logger = get_logger(__name__)

def log_note(content: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO notes (content) VALUES (?)", (content,))
        conn.commit()
        conn.close()
        logger.info(f"Note saved: {content}")
        speak("Noted.")
    except Exception as e:
        logger.exception("Failed to save note.")
        speak("I couldn't save that note.")

def read_recent_notes(limit=5):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content, timestamp FROM notes ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            speak("You don’t have any notes yet.")
            return

        speak("Here are your latest notes.")
        for row in rows:
            speak(f"{row['timestamp']}: {row['content']}")

    except Exception as e:
        logger.exception("Failed to retrieve notes.")
        speak("I couldn’t fetch your notes.")
