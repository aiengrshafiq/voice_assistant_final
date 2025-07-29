# app/services/intent_recognizer.py
import openai
import datetime
import json
from app.core.logger import get_logger
from app.core.config import get_settings
from app.utils.prompt_templates import get_nlu_prompt_template

logger = get_logger(__name__)
settings = get_settings()
client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

async def detect_intent_with_context(command: str, history: list) -> dict:
    prompt_template = get_nlu_prompt_template()
    now = datetime.datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")
    formatted_history = json.dumps(history, indent=2)
    prompt = prompt_template.format(current_time=now, history=formatted_history, command=command)

    try:
        logger.info("Sending request to LLM for NLU processing...")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only responds in a single, well-formed JSON object."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        response_content = response.choices[0].message.content
        return json.loads(response_content)
    except Exception as e:
        logger.error(f"An error occurred while calling the OpenAI API: {e}")
        return {"intent": "nlu_error", "message": str(e), "user_command": command}

async def is_confirmed(command: str) -> bool:
    """Uses the LLM to intelligently determine if a user's response is an affirmation."""
    if not command:
        return False
        
    prompt = f"""
    The user was asked a yes/no confirmation question. Their response was: "{command}"
    Analyze the sentiment and content of the response.
    Respond with a single JSON object with one key, "confirmed", which is a boolean value.
    Examples:
    - "Yes, please do" -> {{"confirmed": true}}
    - "Correct" -> {{"confirmed": true}}
    - "No, cancel that" -> {{"confirmed": false}}
    - "Stop" -> {{"confirmed": false}}
    - "What is the weather?" -> {{"confirmed": false}}
    """
    try:
        logger.info(f"Sending request to LLM for confirmation processing: '{command}'")
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only responds in JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Confirmation result: {result}")
        return result.get("confirmed", False)
    except Exception as e:
        logger.error(f"An error occurred during confirmation check: {e}")
        return False