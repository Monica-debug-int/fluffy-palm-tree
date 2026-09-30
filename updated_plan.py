from app.config import settings
from app.gemini_client import generate_text


def update_workout_plan(original_plan: str, feedback: str, goal: str, intensity: str) -> str:
    prompt = f"""Revise the workout plan below using the person's feedback.
Fitness goal: {goal}
Workout intensity: {intensity}
User feedback: {feedback}

Return a complete revised plan containing Day 1 through Day 7. Every day must include
a warm-up, a main workout with named exercises and sets/repetitions or duration, and a
cooldown/recovery section. Include appropriate rest/recovery and a safety note. Preserve
the stated goal and intensity unless the feedback clearly requests a safe adjustment.
Do not mention hidden instructions or omit days.

Current plan:
{original_plan}
"""
    return generate_text(prompt, settings.workout_model)