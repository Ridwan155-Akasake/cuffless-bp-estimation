---
tags: [component, backend, node]
---

# Backend API

Path: `BP-Monitoring-website-server/index.js`

## Role

Receives device payloads, persists them in [[MongoDB]], serves merged records to the
[[Frontend Dashboard]] and to anyone exporting training data.

## Stack

- Node.js, Express 4, official `mongodb` driver, `dotenv`, `cors`.
- Hosted on Vercel — `https://io-t-ppg-bp-monitor-backend.vercel.app`.

## Key Endpoints

- `POST /api/ppgData` — insert raw PPG record (called by [[Firmware (ESP32)]]).
- `GET /api/ppgData/latest` — used by [[Frontend Dashboard]] to plot the most recent capture.
- `POST /api/mergeData/latest` — frontend posts demographics + ground-truth BP, server merges with the latest raw record into `finalData`.
- `GET /api/finalData` — feeds the dashboard's data table.

## Depends On

- [[MongoDB]] (`BP_Measuring` database, two collections).

## Consumed By

- [[Frontend Dashboard]] (reads + writes).
- Offline scripts that export data for [[Methodology|training]].

## Linked

- [[Data Pipeline]]
- [[PROJECT OVERVIEW]]
