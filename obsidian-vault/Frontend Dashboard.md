---
tags: [component, frontend, web]
---

# Frontend Dashboard

Path: `BP-Monitoring-website/`

## Role

The user-facing surface. Pulls the latest captured PPG, lets the user enter demographics +
ground-truth BP, calls [[Flask ML API]] for a prediction, displays history.

## Pages

- `index.html` — landing.
- `collect.html` — fetch latest IR/RED, plot via Chart.js, capture demographics + ground-truth BP, post to [[Backend API]].
- `measure.html` — call [[Flask ML API]], render predicted systolic / diastolic.
- `data.html` — table view of every record in `finalData`.
- `about.html` — about page.

## Stack

- Plain HTML / CSS / vanilla JS. Chart.js for waveform plots. Express server for hosting. Deployed on Vercel.

## Talks To

- [[Backend API]] — fetch latest, post merged record, list final records.
- [[Flask ML API]] — `POST /predict`.

## Linked

- [[Data Pipeline]]
- [[PROJECT OVERVIEW]]
