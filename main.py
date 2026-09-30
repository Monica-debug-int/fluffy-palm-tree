from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import Base, engine
from app import models
from app.routes import router

BASE_DIR = Path(__file__).resolve().parent.parent
Base.metadata.create_all(bind=engine)

app = FastAPI(title="FitBuddy", description="Personalized AI fitness plans", version="1.0.0")
app.add_middleware(
	SessionMiddleware,
	secret_key=settings.session_secret,
	session_cookie="fitbuddy_session",
	same_site="lax",
	https_only=False,
)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(router)
