import json
from openai import OpenAI
from app.core.logger import get_logger
from app.core.config import get_settings
from app.utils.prompt_templates import INTENT_PROMPT_TEMPLATE

logger = get_logger(__name__)
settings = get_settings()

client = OpenAI(api_key=settings.OPENAI_API_KEY)

VALID_INTENTS = {
    "turn_on_light", "turn_off_light",
    "turn_on_plug", "turn_off_plug",
    "set_thermostat",
    "set_reminder",
    "turn_on_speaker", "turn_off_speaker",
    "get_schedule", "create_event"
}

def detect_intent(user_input: str):
    try:
        prompt = INTENT_PROMPT_TEMPLATE.format(user_input=user_input, valid_intents=', '.join(VALID_INTENTS))

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful smart office assistant."},
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content.strip()
        logger.debug(f"[GPT Raw Output] {result}")
        parsed = json.loads(result)

        intent = parsed.get("intent")
        parameters = parsed.get("parameters", {})

        if intent not in VALID_INTENTS:
            return "unsupported", {}

        return intent, parameters

    except Exception as e:
        logger.exception("Intent recognition error.")
        return None, None
