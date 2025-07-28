import asyncio
import openai
import datetime
import json
from app.core.logger import get_logger
from app.core.config import get_settings
from app.utils.prompt_templates import get_nlu_prompt_template

logger = get_logger(__name__)
settings = get_settings()
openai.api_key = settings.OPENAI_API_KEY

# V3: The function is now asynchronous to work with the new state machine
async def detect_intent_with_context(command: str, history: list) -> dict:
    """
    V3: Asynchronously detects intent using the conversational NLU prompt.

    Args:
        command: The user's latest voice command as text.
        history: A list of recent conversation turn dictionaries.

    Returns:
        A dictionary containing the structured NLU result.
    """
    
    prompt_template = get_nlu_prompt_template()

    # V3: Simplified formatting for the new prompt
    now = datetime.datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")
    formatted_history = json.dumps(history, indent=2)

    prompt = prompt_template.format(
        current_time=now,
        history=formatted_history,
        command=command
    )

    try:
        logger.info("Sending request to LLM for NLU processing...")
        response = await openai.chat.completions.create(
            # gpt-4o is faster and cheaper than turbo, ideal for this use case
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": "You are a helpful assistant that only responds in a single, well-formed JSON object."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"} # Force JSON mode
        )
        
        response_content = response.choices[0].message.content
        logger.info(f"LLM Response received: {response_content}")
        
        nlu_result = json.loads(response_content)
        nlu_result['user_command'] = command # Ensure command is always in the result
        
        return nlu_result

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON response from LLM.")
        return {"intent": "nlu_error", "message": "Invalid JSON response", "user_command": command}
    except Exception as e:
        logger.exception(f"An error occurred while calling the OpenAI API: {e}")
        return {"intent": "nlu_error", "message": str(e), "user_command": command}