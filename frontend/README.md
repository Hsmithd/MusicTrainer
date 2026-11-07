# MusicTrainer frontend

React app bundled with webpack. Django serves the bundle (`build/main.js`)
from the page in `backend/trainer/templates/trainer/index.html`.

```
src/
├── index.js      entry point: mounts <App /> with the router
├── App.js        route table (/home, /profile)
├── pages/        one component per route (Home, Profile)
├── components/   reusable pieces used by pages (ScoreViewer)
└── api/          functions that call the Django backend
```

## Commands

Install dependencies once:

```bash
npm install
```

Build once (do this before starting Django):

```bash
npm run build
```

Rebuild automatically while you edit:

```bash
npm run dev
```
