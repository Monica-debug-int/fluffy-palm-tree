import hmac
import secrets
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.database import get_db
from app.gemini_client import GeminiError
from app.gemini_flash_generator import generate_nutrition_tip_with_flash
from app.gemini_generator import generate_workout_gemini
from app.models import Plan, User
from app.schemas import FeedbackInput, UserInput
from app.updated_plan import update_workout_plan

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


def _error(request: Request, message: str, status_code: int = 400) -> HTMLResponse:
	return templates.TemplateResponse(
		request=request,
		name="error.html",
		context={"message": message},
		status_code=status_code,
	)


def _validation_message(error: ValidationError) -> str:
	return "; ".join(item["msg"] for item in error.errors())


def _require_admin(request: Request) -> None:
	if not request.session.get("is_admin"):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin login required.")


def _generate_plan(user_data: UserInput) -> tuple[str, str]:
	workout = generate_workout_gemini(
		user_data.username, user_data.age, user_data.weight, user_data.goal, user_data.intensity
	)
	tip = generate_nutrition_tip_with_flash(user_data.goal, user_data.intensity)
	return workout, tip


def _save_user_and_plan(database: Session, user_data: UserInput, workout: str, tip: str) -> Plan:
	user = database.get(User, user_data.user_id)
	if user is None:
		user = User(user_id=user_data.user_id, username=user_data.username, age=user_data.age,
					weight=user_data.weight, goal=user_data.goal, intensity=user_data.intensity)
		database.add(user)
	else:
		user.username = user_data.username
		user.age = user_data.age
		user.weight = user_data.weight
		user.goal = user_data.goal
		user.intensity = user_data.intensity
	plan = Plan(user_id=user_data.user_id, original_workout_plan=workout, nutrition_tip=tip)
	database.add(plan)
	database.commit()
	database.refresh(plan)
	return plan


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
	return templates.TemplateResponse(request=request, name="index.html", context={})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout_form(
	request: Request,
	username: str = Form(...),
	user_id: str = Form(...),
	age: str = Form(...),
	weight: str = Form(...),
	goal: str = Form(...),
	intensity: str = Form(...),
	database: Session = Depends(get_db),
):
	try:
		user_data = UserInput.model_validate({
			"username": username, "user_id": user_id, "age": age,
			"weight": weight, "goal": goal, "intensity": intensity,
		})
		workout, tip = _generate_plan(user_data)
		plan = _save_user_and_plan(database, user_data, workout, tip)
	except ValidationError as exc:
		return _error(request, _validation_message(exc), 422)
	except GeminiError as exc:
		return _error(request, str(exc), 503)
	except SQLAlchemyError:
		database.rollback()
		return _error(request, "We could not save your plan. Please try again.", 500)
	return RedirectResponse(url=f"/result/{user_data.user_id}?plan_id={plan.id}", status_code=303)


@router.get("/result/{user_id}", response_class=HTMLResponse)
def result_page(request: Request, user_id: str, plan_id: int, database: Session = Depends(get_db)):
	plan = database.scalar(select(Plan).where(Plan.id == plan_id, Plan.user_id == user_id))
	user = database.get(User, user_id)
	if user is None:
		return _error(request, "We could not find that user.", 404)
	if plan is None:
		return _error(request, "We could not find that workout plan.", 404)
	return templates.TemplateResponse(
		request=request, name="result.html", context={"user": user, "plan": plan}
	)


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback_form(
	request: Request,
	user_id: str = Form(...),
	plan_id: str = Form(...),
	feedback: str = Form(...),
	database: Session = Depends(get_db),
):
	try:
		feedback_data = FeedbackInput.model_validate(
			{"user_id": user_id, "plan_id": plan_id, "feedback": feedback}
		)
	except ValidationError as exc:
		return _error(request, _validation_message(exc), 422)
	user = database.get(User, feedback_data.user_id)
	plan = database.scalar(
		select(Plan).where(Plan.id == feedback_data.plan_id, Plan.user_id == feedback_data.user_id)
	)
	if user is None:
		return _error(request, "We could not find that user.", 404)
	if plan is None:
		return _error(request, "We could not find that workout plan.", 404)
	try:
		revised = update_workout_plan(
			plan.original_workout_plan, feedback_data.feedback, user.goal, user.intensity
		)
		plan.feedback = feedback_data.feedback
		plan.updated_workout_plan = revised
		database.commit()
	except GeminiError as exc:
		database.rollback()
		return _error(request, str(exc), 503)
	except SQLAlchemyError:
		database.rollback()
		return _error(request, "We could not save your updated plan. Please try again.", 500)
	return RedirectResponse(
		url=f"/result/{user.user_id}?plan_id={plan.id}", status_code=303
	)


@router.get("/admin-login", response_class=HTMLResponse)
def admin_login_page(request: Request):
	return templates.TemplateResponse(
		request=request, name="admin_login.html", context={"error": None}
	)


@router.post("/admin-login", response_class=HTMLResponse)
def admin_login(request: Request, password: str = Form(...)):
	if hmac.compare_digest(password, settings.admin_password):
		request.session["is_admin"] = True
		request.session["csrf_token"] = secrets.token_urlsafe(32)
		return RedirectResponse(url="/view-all-users", status_code=303)
	return templates.TemplateResponse(
		request=request,
		name="admin_login.html",
		context={"error": "The password was not accepted."},
		status_code=401,
	)


@router.get("/admin-logout")
def admin_logout(request: Request):
	request.session.clear()
	return RedirectResponse(url="/admin-login", status_code=303)


@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, database: Session = Depends(get_db)):
	if not request.session.get("is_admin"):
		return RedirectResponse(url="/admin-login", status_code=303)
	users = database.scalars(
		select(User).options(selectinload(User.plans)).order_by(User.created_at.desc())
	).all()
	if not request.session.get("csrf_token"):
		request.session["csrf_token"] = secrets.token_urlsafe(32)
	return templates.TemplateResponse(
		request=request,
		name="all_users.html",
		context={"users": users, "csrf_token": request.session["csrf_token"]},
	)


@router.post("/admin/delete-user/{user_id}")
def delete_user(
	request: Request,
	user_id: str,
	csrf_token: str = Form(...),
	database: Session = Depends(get_db),
):
	if not request.session.get("is_admin"):
		return RedirectResponse(url="/admin-login", status_code=303)
	expected = request.session.get("csrf_token", "")
	if not expected or not hmac.compare_digest(csrf_token, expected):
		raise HTTPException(status_code=403, detail="Invalid request token.")
	user = database.get(User, user_id)
	if user is None:
		raise HTTPException(status_code=404, detail="User not found.")
	try:
		database.delete(user)
		database.commit()
	except SQLAlchemyError as exc:
		database.rollback()
		raise HTTPException(status_code=500, detail="Could not delete user.") from exc
	return RedirectResponse(url="/view-all-users", status_code=303)


@router.post("/api/generate-workout")
def generate_workout_api(user_data: UserInput, database: Session = Depends(get_db)):
	try:
		workout, tip = _generate_plan(user_data)
		plan = _save_user_and_plan(database, user_data, workout, tip)
	except GeminiError as exc:
		raise HTTPException(status_code=503, detail=str(exc)) from exc
	except SQLAlchemyError as exc:
		database.rollback()
		raise HTTPException(status_code=500, detail="We could not save your plan.") from exc
	return {"user_id": user_data.user_id, "plan_id": plan.id, "workout_plan": workout, "nutrition_tip": tip}


@router.post("/api/submit-feedback")
def submit_feedback_api(feedback_data: FeedbackInput, database: Session = Depends(get_db)):
	user = database.get(User, feedback_data.user_id)
	plan = database.scalar(
		select(Plan).where(Plan.id == feedback_data.plan_id, Plan.user_id == feedback_data.user_id)
	)
	if user is None:
		raise HTTPException(status_code=404, detail="User not found.")
	if plan is None:
		raise HTTPException(status_code=404, detail="Workout plan not found.")
	try:
		revised = update_workout_plan(
			plan.original_workout_plan, feedback_data.feedback, user.goal, user.intensity
		)
		plan.feedback = feedback_data.feedback
		plan.updated_workout_plan = revised
		database.commit()
	except GeminiError as exc:
		database.rollback()
		raise HTTPException(status_code=503, detail=str(exc)) from exc
	except SQLAlchemyError as exc:
		database.rollback()
		raise HTTPException(status_code=500, detail="We could not save your updated plan.") from exc
	return {
		"user_id": user.user_id,
		"plan_id": plan.id,
		"original_workout_plan": plan.original_workout_plan,
		"updated_workout_plan": revised,
	}


@router.get("/api/users")
def api_users(request: Request, database: Session = Depends(get_db)):
	_require_admin(request)
	users = database.scalars(
		select(User).options(selectinload(User.plans)).order_by(User.created_at.desc())
	).all()
	return [
		{
			"user_id": user.user_id,
			"username": user.username,
			"age": user.age,
			"weight": user.weight,
			"goal": user.goal,
			"intensity": user.intensity,
			"plans": [
				{
					"id": plan.id,
					"original_workout_plan": plan.original_workout_plan,
					"updated_workout_plan": plan.updated_workout_plan,
					"feedback": plan.feedback,
					"nutrition_tip": plan.nutrition_tip,
				}
				for plan in user.plans
			],
		}
		for user in users
	]


@router.get("/health")
def health():
	return {"status": "ok"}
