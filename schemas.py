from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


FitnessGoal = Literal["Weight loss", "Muscle gain", "General wellness", "Flexibility", "Endurance"]
WorkoutIntensity = Literal["Low", "Medium", "High"]


class UserInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(min_length=2, max_length=80)
    user_id: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    age: int = Field(ge=13, le=110)
    weight: float = Field(gt=25, le=350)
    goal: FitnessGoal
    intensity: WorkoutIntensity

    @field_validator("username")
    @classmethod
    def username_has_letters(cls, value: str) -> str:
        if not any(character.isalpha() for character in value):
            raise ValueError("Name must contain at least one letter.")
        return value


class FeedbackInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    user_id: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    plan_id: int = Field(gt=0)
    feedback: str = Field(min_length=5, max_length=2000)


class PlanResponse(BaseModel):
    user_id: str
    plan_id: int
    workout_plan: str
    nutrition_tip: str


class FeedbackResponse(BaseModel):
    user_id: str
    plan_id: int
    original_workout_plan: str
    updated_workout_plan: str