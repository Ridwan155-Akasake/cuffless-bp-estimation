---
tags: [component, database]
---

# MongoDB

Cluster: MongoDB Atlas (host configured via `MONGO_CLUSTER` env var).
Database: `BP_Measuring`.

## Collections

### `rawDataCollection`
Raw PPG payloads from the device. Auto-incremented `serialNumber`.

```json
{ "serialNumber": 42, "ir": [...], "red": [...], "spo2": 97, "heartRate": 72 }
```

### `finalData`
Same payload merged with demographics + ground-truth BP. The labelled training set.

```json
{
  "serialNumber": 42, "ir": [...], "red": [...], "spo2": 97, "heartRate": 72,
  "userAge": 24, "userGender": "male", "userHeight": 175.26, "userWeight": 70,
  "userBmi": 22.81, "systolic_BP": 118, "diastolic_BP": 78
}
```

## Written By

- [[Backend API]] — `POST /api/ppgData`, `POST /api/mergeData/latest`.

## Read By

- [[Backend API]] — `GET /api/ppgData/latest`, `GET /api/finalData`, etc.
- Offline export → [[BP_Measuring finalData]].

## Linked

- [[Data Pipeline]]
- [[PROJECT OVERVIEW]]
