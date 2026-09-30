# FitBuddy

FitBuddy creates personalized seven-day workout plans with Google's Gemini API. It stores profiles and original/revised plans in SQLite, generates a nutrition or recovery tip, and provides a session-protected admin dashboard.

## Prerequisites

- Python 3.10 or newer
- A Gemini API key from Google AI Studio for live plan generation
- VS Code (optional, but a launch configuration is included)

## Run in VS Code

1. Open the `FitBuddy.AI` folder in VS Code.
2. Create and activate a virtual environment, then install dependencies:

   **Windows PowerShell**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

   **Windows CMD**
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env`. Set `GEMINI_API_KEY` to your key, change `ADMIN_PASSWORD`, and replace `SESSION_SECRET` with a long random value. Keep `.env` private; it is ignored by Git.
4. Start the server and open the app:

   ```bash
   uvicorn app.main:app --reload
   ```

   App: <http://127.0.0.1:8000>  
   Swagger: <http://127.0.0.1:8000/docs>

You can also select **FitBuddy: FastAPI** in VS Code's Run and Debug view. The admin login is at `/admin-login`; use the `ADMIN_PASSWORD` value from `.env`.

## Tests

The tests mock Gemini calls and use an in-memory SQLite database. They do not require a real API key.

```bash
pytest -q
```

## API

- `GET /health` reports service status.
- `POST /api/generate-workout` accepts `username`, `user_id`, `age`, `weight`, `goal`, and `intensity` as JSON.
- `POST /api/submit-feedback` accepts `user_id`, `plan_id`, and `feedback` as JSON.
- `GET /api/users` returns saved profiles and plans only to an authenticated admin session.
- The interactive API reference is available at `/docs`.

Goals: Weight loss, Muscle gain, General wellness, Flexibility, Endurance. Intensities: Low, Medium, High. Feedback updates a plan's revised version without overwriting the original.

## Troubleshooting

- **Gemini is not configured:** Copy `.env.example` to `.env` and add a valid `GEMINI_API_KEY`.
- **Invalid model or Gemini request:** Check `GEMINI_WORKOUT_MODEL` and `GEMINI_TIP_MODEL` against models enabled for your API key, and check network access and quota.
- **PowerShell blocks activation:** Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in the current PowerShell session, then activate the environment again.
- **Import or package errors:** Confirm the virtual environment is active and reinstall with `pip install -r requirements.txt`.
- **Admin login fails:** Use the exact `ADMIN_PASSWORD` from `.env`; restart Uvicorn after changing environment settings.
- **Database file errors:** Stop Uvicorn and check that the project folder is writable. SQLite creates `fitbuddy.db` on first startup.

## How to Run in VS Code – 4 Simple Steps

1. Open this folder in VS Code.
2. Create and activate `venv`, then run `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and set Gemini key, admin password, and session secret.
4. Run `uvicorn app.main:app --reload`, then visit <http://127.0.0.1:8000>.