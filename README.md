# MusicTrainer
AI generated practice tools

## Repository layout

```
MusicTrainer/
├── frontend/          React single-page app (webpack → frontend/build/main.js)
│   └── src/
│       └── components/
├── backend/           Django project
│   ├── manage.py
│   ├── DjangoProject/ settings, root urls, wsgi/asgi
│   └── App/
│       ├── views.py        HTTP layer: requests in, responses out
│       ├── services/       business logic (auth, etude generation)
│       ├── repositories/   data access (database tables, generated files)
│       ├── templates/      Django templates (login, signup, SPA shell)
│       └── static/
└── ml/                Machine-learning code, independent of the web app
    ├── melodyt5/      MelodyT5 model: training + inference
    ├── data_tagging/  difficulty tagging for training data
    └── notebooks/
```

Dependencies only point one way inside the backend:
`views → services → repositories → database / files`.
The backend reaches the model only through `EtudeService`, using the paths
configured in `backend/DjangoProject/settings.py` (`MELODYT5_DIR`,
`MELODYT5_PYTHON`).

## Running locally

Build the frontend (Django serves the bundle as a static file):

```bash
cd frontend && npm install && npm run build
```

Use `npm run dev` instead to rebuild on every change.

Start the backend:

```bash
cd backend && pip install -r requirements.txt && python manage.py migrate && python manage.py runserver
```

Then open http://localhost:8000/home.

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
