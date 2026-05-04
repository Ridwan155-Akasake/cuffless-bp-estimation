# BP-Monitoring-website — Web Dashboard

The user-facing layer. A small static HTML/JS site (served by Express) that fetches the
latest captured PPG data from the backend, lets the user enter demographics + ground-truth
BP, calls the Flask ML API for a predicted blood pressure, and displays a table of every
captured session.

## Files

| File | Purpose |
|---|---|
| [`index.js`](index.js) | Optional Express host that exposes the same Mongo-backed endpoints (mirrors `BP-Monitoring-website-server`) for local development. |
| [`public/index.html`](public/index.html) | Landing page. |
| [`public/collect.html`](public/collect.html) | "Collect Data" page — pulls latest IR/RED, plots them, captures ground-truth demographics + BP, posts to `/api/mergeData/latest`. |
| [`public/measure.html`](public/measure.html) | "Measure BP" page — reads localStorage + form fields, calls the Flask API, displays predicted systolic / diastolic. |
| [`public/data.html`](public/data.html) | Tabular view of every record in the `finalData` collection. |
| [`public/about.html`](public/about.html) | About page. |
| [`public/main.js`](public/main.js) | All client-side logic. |
| [`public/style.css`](public/style.css) | Styling, including a `.dark-theme` toggle. |
| [`package.json`](package.json) | Dependencies: `express`, `mongodb`, `cors`, `dotenv`. |
| [`vercel.json`](vercel.json) | Vercel deployment config. |

## Page → Function Map (`public/main.js`)

| Page | Entry function | What it does |
|---|---|---|
| `collect.html` | `fetchSensorData()` | `GET /api/ppgData/latest`, render IR + RED line charts via Chart.js, store IR/RED/HR/SpO₂ in `localStorage`. |
| `collect.html` | `commitCollectedData()` | Read demographics + ground-truth BP from form, compute height-cm + BMI, `POST /api/mergeData/latest`. |
| `measure.html` | `measureBP()` | Read stored IR/RED + form fields, `POST` to the Flask API at `https://akasake-bp-monitor-api.hf.space/predict`, render `[systolic, diastolic]`. |
| `data.html` | `DOMContentLoaded` handler | `GET /api/finalData`, render every record into a table. |
| any | `toggleTheme()` | Toggle `.dark-theme` on `<body>` and persist to `localStorage`. |

## API Endpoints This Page Calls

| URL | Where |
|---|---|
| `https://io-t-ppg-bp-monitor-backend.vercel.app/api/ppgData/latest` | `fetchSensorData` |
| `https://io-t-ppg-bp-monitor-backend.vercel.app/api/mergeData/latest` | `commitCollectedData` |
| `https://akasake-bp-monitor-api.hf.space/predict` | `measureBP` |
| `https://io-t-ppg-bp-monitor-backend.vercel.app/api/finalData` | `data.html` table loader |

These URLs are hard-coded in `main.js`. To repoint the dashboard at a local backend or local
Flask instance, edit them there.

## Run Locally

```bash
npm install
cp .env.example .env       # then edit .env with real Mongo creds
node index.js
# Open http://localhost:5000
```

Required env vars: `USER`, `PASS`, `MONGO_CLUSTER` (see `.env.example`).

## Deployment

Hosted on Vercel — the static `public/` folder is served alongside the Express endpoints.
