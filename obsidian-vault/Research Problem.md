---
tags: [research, problem-statement]
---

# Research Problem

Hypertension is one of the most common chronic conditions globally, yet routine BP monitoring
still depends on **cuff-based sphygmomanometers** that are intermittent, bulky, and
unsuitable for continuous or at-home use. Cuffless estimation from photoplethysmography (PPG)
is the active alternative direction.

## Specific Question

Most published cuffless-BP work uses **research-grade datasets** (e.g. MIMIC) collected with
**clinical or laboratory-grade** sensors. Comparatively little literature documents what
happens when the same pipeline is applied to a **commodity, low-cost PPG sensor** of the kind
actually embedded in consumer wearables.

> Can a low-cost optical sensor (MAX30102) combined with basic demographic features and
> classical / ensemble ML produce **clinically meaningful** estimates of systolic and
> diastolic blood pressure from a single fingertip capture?

## Why It Matters

- **Accessibility:** the entire device is built from <$30 of off-the-shelf parts.
- **Hardware reality:** commodity sensors are what end users will actually wear. Studying their failure modes is itself a contribution.
- **Negative-result rigour:** if the answer is "no", documenting *why* (with full feature engineering, three feature-selection strategies, and nine regression candidates) provides credible evidence for future researchers to choose better sensors.

## What Counts As "Clinically Meaningful"

The paper cites **MAE ≤ 5 mmHg, R² > 0.5** as the clinical-practice bar.
This project's plateau is **MAE ≈ 9 mmHg, R² ≈ 0.24** — see [[Results]].

## Linked Notes

- [[Methodology]] — how the problem is approached
- [[Results]] — quantitative outcome and the four diagnosable failure factors
- [[Data Pipeline]] — full system layout
- [[PROJECT OVERVIEW]]
