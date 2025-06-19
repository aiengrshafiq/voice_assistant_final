from app.core.logger import get_logger
from app.services.slack_service import slack_service
from app.services.home_assistant_service import ha_service

logger = get_logger(__name__)

# This ACTION_MAP is the heart of the dispatcher.
# It maps an 'intent' string from the NLU to a specific service function.
ACTION_MAP = {
    "summon_person": lambda result: slack_service.summon_person(result.get('target')),
    "set_mood": lambda result: ha_service.trigger_scene_by_name(result.get('target')),
    # Add more intents and their corresponding actions here in the future
    # e.g., "set_reminder": lambda result: calendar_service.set_reminder(...)
}

def dispatch_action(nlu_result: dict) -> str:
    """
    Looks at the NLU result and calls the appropriate service function.

    Args:
        nlu_result: The structured dictionary from the NLU engine.

    Returns:
        A user-friendly string indicating the result of the action.
    """
    intent = nlu_result.get('intent')
    logger.info(f"Dispatching action for intent: '{intent}'")
    logger.debug(f"Full NLU result for dispatch: {nlu_result}")

    if not intent:
        return "I'm not sure what you want me to do. The intent is missing."

    # Look up the intent in our action map
    action_function = ACTION_MAP.get(intent)

    if action_function:
        try:
            # Call the associated function, passing the full NLU result
            return action_function(nlu_result)
        except Exception as e:
            logger.exception(f"An error occurred while executing the action for intent '{intent}': {e}")
            return "I ran into an unexpected error while trying to perform that action."
    else:
        logger.warning(f"No action defined for the intent: '{intent}'")
        return f"I understand you want to '{intent.replace('_', ' ')}', but I don't know how to do that yet."