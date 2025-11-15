## README

### `README.md`

````md
# Minimal React + TypeScript + FastAPI Demo

This is a simple demo app with:

- A **React + TypeScript** frontend (Vite)
- A **FastAPI** backend in Python

The flow:

1. Home page asks for a username (no password).
2. After "login", it navigates to a projects page.
3. The projects page fetches a list of projects for that username from the backend.

---

## Prerequisites

- **Node.js** (v18+ recommended)
- **Python** (3.10+ recommended)
- `pip` for Python package installation

---

## Backend Setup (FastAPI)

From the project root:

```bash
cd backend
python -m venv .venv
# Activate the virtual environment:

# On macOS / Linux:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
```
````

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server:

```bash
uvicorn main:app --reload --port 8000
```

The backend will be available at: `http://localhost:8000`

Test endpoint:

```bash
curl http://localhost:8000/projects/alice
```

---

## Frontend Setup (React + TypeScript + Vite)

From the project root:

```bash
cd frontend
npm install
```

Run the development server:

```bash
npm run dev
```

Vite will show a local URL, typically:

- `http://localhost:5173`

Open that in your browser.

---

## Usage

1. Start the backend (FastAPI) at `http://localhost:8000`.
2. Start the frontend (Vite dev server).
3. Open the frontend URL in a browser.
4. On the home page, enter a username (e.g. `alice` or `bob`) and press **Login**.
5. You’ll be taken to the projects page, which fetches data from:

   - `GET http://localhost:8000/projects/<username>`

For unknown usernames, the backend returns a simple default project list.

---

## Notes

- This demo **does not** implement real authentication or authorization.
- All project data is in memory in `backend/main.py`.
- To customize, edit `PROJECTS_BY_USER` on the backend and adjust UI as needed.
