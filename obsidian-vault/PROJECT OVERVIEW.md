---
tags: [index, project]
---

# PROJECT OVERVIEW — Cuffless Blood-Pressure Estimation System

> *Limitations of Low-Cost PPG Sensors for Cuffless Blood Pressure Estimation Using IoT and Machine Learning*
>
> Ridwan Sharif and Arif Mahmud — Daffodil International University, Bangladesh

A research-and-engineering capstone delivering an end-to-end IoT + ML pipeline for cuffless
blood-pressure estimation, plus a credibly negative finding: commodity PPG sensors (MAX30102)
cannot meet clinical accuracy thresholds, and the bottleneck is hardware, not methodology.

## Research

- [[Research Problem]]
- [[Methodology]]
- [[Results]]

## Pipeline

- [[Data Pipeline]] — full end-to-end sequence

## Components

- [[Firmware (ESP32)]]
- [[Backend API]]
- [[MongoDB]]
- [[Frontend Dashboard]]
- [[Flask ML API]]

## Datasets — kept

- [[BP_Measuring finalData]]
- [[cleaned_data]]
- [[all_features_dataset]]

## Datasets — archived

- [[Kaggle PPG-BP]]
- [[Online PPG-BP]]
- [[Resampled variants]]
- [[Feature ablation experiments]]

## Models — kept

- [[random_forest_tuned_model]] (default deployed)
- [[best_catboost_model]] (statistically tied alternate)

## Models — archived

- [[Single-target RF baselines]]
- [[Multi-output combined experiments]]
- [[Tightened-threshold experiments]]
- [[Kaggle-track experiments]]
