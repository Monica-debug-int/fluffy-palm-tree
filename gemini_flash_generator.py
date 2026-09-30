from app.config import settings
from app.gemini_client import generate_text


def generate_nutrition_tip_with_flash(goal: str, intensity: str) -> str:
    prompt = (
        "Give one concise, practical nutrition or recovery recommendation for a fitness "
        f"goal of {goal} and {intensity.lower()} workout intensity. Keep it to 2-3 sentences, "
        "avoid medical claims, and remind the reader that individual needs vary."
    )
    return generate_text(prompt, settings.tip_model)