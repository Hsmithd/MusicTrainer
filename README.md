# MusicTrainer
AI generated practice tools

## Repository layout

```
MusicTrainer/
├── frontend/              React app (what the user sees)
│   └── src/
│       ├── pages/         one component per route: Home, Profile
│       ├── components/    reusable UI: ScoreViewer
│       └── api/           functions that call the backend
├── backend/               Django server
│   ├── manage.py
│   ├── musictrainer/      project settings, root urls, wsgi/asgi
│   └── trainer/           the app itself
│       ├── views.py           HTTP layer: requests in, responses out
│       ├── services/          business logic (auth, etude generation)
│       ├── repositories/      data access (database tables, generated files)
│       ├── templates/trainer/ login, signup, and the page that loads React
│       ├── static/trainer/    CSS for the login/signup pages
│       └── tests/             one test file per layer
└── ml/                    machine-learning code, independent of the web app
    ├── melodyt5/          MelodyT5 model: training and inference
    ├── data_tagging/      difficulty tagging for training data
    └── notebooks/
```

How a request flows:

```
frontend/src/api  →  trainer/views.py  →  trainer/services  →  trainer/repositories  →  database / files
                                                     └──────→  ml/melodyt5 (runs the model)
```

Each layer only calls the one to its right. The backend finds the model
through the paths in `backend/musictrainer/settings.py` (`MELODYT5_DIR`,
`MELODYT5_PYTHON`).

## Running locally

First-time setup:

```bash
cd backend && pip install -r requirements.txt && python manage.py migrate
```

```bash
cd frontend && npm install
```

### While developing

Run both servers, each in its own terminal:

```bash
cd backend && python manage.py runserver
```

```bash
cd frontend && npm start
```

Open **http://localhost:3000**. Frontend changes show up instantly. The dev
server forwards `/api`, `/login`, `/signup`, `/admin` and `/static` to
Django on port 8000, so logging in works the same as in production.

### Like production (Django only)

```bash
cd frontend && npm run build
```

```bash
cd backend && python manage.py runserver
```

Open **http://localhost:8000**. Django serves `frontend/build/index.html` for
every page React handles, and the bundle (`main.<hash>.js`) as a static file.

### Adding a page

Add a `<Route>` in `frontend/src/App.js`. Django needs no change: any URL
that isn't `/api/`, `/admin/`, `/static/`, `/login` or `/signup` is sent to
React.

Etude generation runs `ml/melodyt5/inference.py`; set up its environment as
described in `ml/melodyt5/README.md`. If the model uses a different Python
(e.g. a conda env), point the backend at it:

```bash
export MELODYT5_PYTHON=/path/to/conda/envs/melodyt5/bin/python
```

Run the backend tests:

```bash
cd backend && python manage.py test
```
