# BP-Monitoring-website-server — Node/Express + MongoDB Backend

The cloud-side data layer. Receives raw PPG payloads from the ESP32 device, persists them in
MongoDB Atlas, and serves merged "final" records (raw signals + demographics + ground-truth
BP) for both the dashboard and the training pipeline.

## Files

| File | Purpose |
|---|---|
| [`index.js`](index.js) | Express app — Mongo connection, all REST endpoints. |
| [`package.json`](package.json) | Dependencies: `express`, `mongodb`, `cors`, `dotenv`. |
| [`vercel.json`](vercel.json) | Vercel deployment config. |

## Environment Variables

The Mongo URI is constructed from environment variables at runtime (`index.js:13`):

```
USER=<mongodb_username>
PASS=<mongodb_password>
MONGO_CLUSTER=<your-cluster>.mongodb.net
PORT=5000   # optional, defaults to 5000
```

Copy `.env.example` to `.env` and fill in the real values. `.env` is gitignored.

## Database

- **Cluster:** MongoDB Atlas (host configured via `MONGO_CLUSTER` env var)
- **Database:** `BP_Measuring`
- **Collections:**
  - `rawDataCollection` — raw PPG payloads from the ESP32. Auto-incremented `serialNumber`.
  - `finalData` — same payload merged with demographics and ground-truth BP, used as the labelled training set.

### `rawDataCollection` schema
```json
{
  "serialNumber": 42,
  "ir":   [int, int, ...],
  "red":  [int, int, ...],
  "spo2": 97,
  "heartRate": 72
}
```

### `finalData` schema
```json
{
  "serialNumber": 42,
  "ir":   [int, int, ...],
  "red":  [int, int, ...],
  "spo2": 97,
  "heartRate": 72,
  "userAge": 24,
  "userGender": "male",
  "userHeight": 175.26,
  "userWeight": 70,
  "userBmi": 22.81,
  "systolic_BP": 118,
  "diastolic_BP": 78
}
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/ppgData` | Insert a new raw PPG record (called by the ESP32). Auto-assigns `serialNumber`. |
| `GET`  | `/api/ppgData/latest` | Return the most recent raw record (`heartRate`, `spo2`, `ir`, `red`). |
| `GET`  | `/api/ppgData` | Return every raw record. |
| `PUT`  | `/api/ppgData/latest` | Patch the latest raw record with demographics + BP (legacy in-place merge). |
| `POST` | `/api/mergeData/latest` | Take the latest raw record + demographics from the body, write a merged document into `finalData`. **This is the path the dashboard uses.** |
| `GET`  | `/api/finalData` | Return every merged record (used by the dashboard's data view). |
| `GET`  | `/api/finalData/latest` | Return the most recent merged record. |
| `DELETE` | `/api/ppgData/:id` | Delete a raw record by Mongo ObjectId. |
| `GET`  | `/` | Health check — returns `{ message, status: "OK" }`. |

## Run Locally

```bash
npm install
cp .env.example .env       # then edit .env with real Mongo creds
node index.js
# Server listens on http://localhost:5000
```

## Deployment

Hosted on Vercel at **`https://io-t-ppg-bp-monitor-backend.vercel.app`**. The ESP32 firmware,
the dashboard, and the Flask API all reference this base URL.
