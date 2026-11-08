# MusicTrainer frontend

React app bundled with webpack. `npm run build` writes `build/index.html`
(generated from `index.html` in this folder) and a hashed bundle
`build/main.<hash>.js`. Django serves both.

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

Develop with instant reloads at http://localhost:3000 (keep Django running on
port 8000; API and login requests are forwarded to it):

```bash
npm start
```

Build for Django to serve at http://localhost:8000:

```bash
npm run build
```
