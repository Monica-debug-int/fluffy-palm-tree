from app.config import settings
from app.gemini_client import GeminiQuotaError, generate_text


def generate_workout_gemini(
    username: str, age: int, weight: float, goal: str, intensity: str
) -> str:
    prompt = f"""Create a safe, personalized 7-day workout plan for this person:
Name: {username}
Age: {age}
Weight: {weight} kg
Fitness goal: {goal}
Workout intensity: {intensity}

Include exactly Day 1 through Day 7. For every day, provide a warm-up, a main workout
with named exercises and sets/repetitions or duration, and a cooldown/recovery section.
Schedule appropriate rest and recovery based on the intensity and goal. Finish with a
clear safety note. Keep the plan practical, readable, and avoid claiming medical advice.
"""
    try:
        return generate_text(prompt, settings.workout_model)
    except GeminiQuotaError:
        if settings.tip_model == settings.workout_model:
            raise
        return generate_text(prompt, settings.tip_model)