import openai
import datetime
import json
from app.core.logger import get_logger
from app.core.config import get_settings
from app.utils.prompt_templates import get_nlu_prompt_template

logger = get_logger(__name__)
settings = get_settings()
# Ensure your OPENAI_API_KEY is set in your .env file
openai.api_key = settings.OPENAI_API_KEY

def detect_intent_with_context(command: str, history: str) -> dict:
    """
    Detects intent from a command using context from conversation history.

    Args:
        command: The user's latest voice command as text.
        history: A formatted string of recent conversation turns.

    Returns:
        A dictionary containing the structured NLU result (intent, confidence, etc.).
        Returns a default 'unsupported' dictionary on failure.
    """
    
    # --- All dynamic data is now prepared here ---
    prompt_template = get_nlu_prompt_template()

    # Prepare dynamic values for the template
    now = datetime.datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")
    tomorrow_date = (datetime.date.today() + datetime.timedelta(days=1))
    example_start_time = tomorrow_date.strftime("%Y-%m-%d") + "T16:00:00"
    example_end_time = (datetime.datetime.strptime(example_start_time, "%Y-%m-%dT%H:%M:%S") + datetime.timedelta(minutes=90)).strftime("%Y-%m-%dT%H:%M:%S")

    # Format the template with all dynamic parts in one go
    prompt = prompt_template.format(
        current_time=now,
        example_start_time=example_start_time,
        example_end_time=example_end_time,
        history=history,
        command=command
    )

    try:
        logger.info("Sending request to LLM for NLU processing...")
        response = openai.chat.completions.create(
            model="gpt-4-turbo",  # Or "gpt-3.5-turbo" for faster, less expensive results
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only responds in JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Low temperature for more predictable, structured output
            response_format={"type": "json_object"} # Use JSON mode
        )
        
        response_content = response.choices[0].message.content
        logger.info(f"LLM Response received: {response_content}")
        
        nlu_result = json.loads(response_content)
        # Ensure the original command is part of the result for context stacking
        if 'user_command' not in nlu_result:
            nlu_result['user_command'] = command
            
        return nlu_result

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from LLM.")
        return {"intent": "nlu_error", "confidence": 0.0, "details": "Invalid JSON response", "user_command": command}
    except Exception as e:
        logger.exception(f"An error occurred while calling the OpenAI API: {e}")
        return {"intent": "nlu_error", "confidence": 0.0, "details": str(e), "user_command": command}