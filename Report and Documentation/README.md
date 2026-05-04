# Report and Documentation

Academic deliverables and supporting documents for the Final Year Design Project (ID
213-15-4381).

## Reports & Papers

| File | What it is |
|---|---|
| **`10330_Camera_Ready.pdf`** | **Conference paper, camera-ready** — *"Limitations of Low-Cost PPG Sensors for Cuffless Blood Pressure Estimation Using IoT and Machine Learning"* by Ridwan Sharif and Arif Mahmud (Daffodil International University). The authoritative write-up: problem statement, gap analysis, methodology, full feature taxonomy, three-stage feature selection, nine-model evaluation, and the negative-result discussion. |
| `213-15-4381_Defence_report.pdf` | Final defense report (PDF). |
| `213-15-4381_Defence_report.docx` | Editable Word source for the same report. |
| `213-15-4381_Defence_report-2.pdf` | Alternative version of the defense report. |
| `213-15-4381_FYDP_Final_report.docx` | Final Year Design Project full report. |
| `Literature review summary.pdf` | Condensed survey of cuffless BP / PPG literature. |
| `Best model evaluation.pdf` | Per-model comparison (MAE / RMSE / R² / MAPE) with discussion of why Random Forest was selected. |
| `Final defense preparation.pdf` | Defense prep notes. |
| `1) Preprocess once, then window.pdf` | Methodology note on preprocessing strategy. |
| `humanized_conferce_draft.docx` / `non-humanized_draft_confernce.docx` | Conference / journal paper drafts. |
| `Darft.docx` | Earlier draft. |

## Slide Decks

| File | What it is |
|---|---|
| `213-15-4381 Pre-Defense Slide, Summer 25.pptx` | Pre-defense presentation. |
| `Pre-Defense Slide Template, Summer 25.pptx` | University template. |

## Supporting Material

| File | What it is |
|---|---|
| `BP_Measuring.rawDataCollection.json` | Sample raw-data export from MongoDB used in early figures. **Gitignored** — kept locally only because it contains real-subject measurements. |
| `Website Structure.txt` | Folder/page layout notes. |
| `PerfectyWorkingServerCode.txt` | Reference snapshot of a working backend version. |
| `color_pages.txt` | UI palette notes. |
| `*.png`, `*.jpg` | Figures and photos used in the report and slides. |

## Headline Result

The defense and journal documents converge on:

> Random Forest, trained on IR-derived features + demographic features, was selected as the
> deployed model with **MAE 9.08, RMSE 12.87, R² 0.2416, MAPE 8.83 %** on a 5-fold
> cross-validation over 318 captured sessions.

For methodology, full evaluation, and discussion of limitations (sample size, demographic
skew, sensor quality), see the defense report.
