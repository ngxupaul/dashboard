# BTS Skytrain ABSA Business Dashboard

This project now uses a static HTML/JavaScript dashboard generated from `full_dataset_with_predictions.csv`. The final dashboard does not need Streamlit.

It includes:

- overall sentiment distribution from `Final_Label`,
- aspect-based sentiment distribution for every `sentiment_*` service aspect,
- monthly sentiment trend by selected aspect,
- priority ranking based on negative volume and agreement weight,
- high-agreement low-rating evidence reviews,
- a dedicated Business Suggestions tab with written recommendations, supporting numbers, evidence snippets, and conclusions.

For section-by-section analysis notes, see
[`docs/analysis_explanation.md`](docs/analysis_explanation.md).

For table-by-table and chart-by-chart reading guidance, see
[`docs/dashboard_observation_guide.md`](docs/dashboard_observation_guide.md).

## Build

```powershell
python -m pip install -r requirements.txt
python build_static_site.py
```

The generated dashboard is:

```text
docs/index.html
```

## Deployment

The GitHub Pages workflow builds and publishes the static dashboard:

```powershell
python build_static_site.py
```

After pushing to `main`, GitHub Actions deploys it to:

<https://ngxupaul.github.io/dashboard/>

If that URL returns 404, enable Pages once in GitHub: **Settings -> Pages -> Deploy from a branch -> `gh-pages` -> `/ (root)`**.

## Data Rule

`Final_Label` is the global review sentiment.

`sentiment_overall` is not global overall sentiment. It is the ABSA field for the `Overall Experience` aspect.

`review_rating_num` is the 1-5 sentiment-derived rating. `like_count` is kept as `agreement_count`, so Reddit upvotes are analyzed as how many people agreed with or engaged with a review, not as star ratings.

## Verification

```powershell
python verify_dashboard.py
```

The verification checks:

- `full_dataset_with_predictions.csv` loads as 24,459 rows and 54 raw columns.
- the default business scope filters broad/off-topic posts to about 12.5k BTS-service-relevant rows.
- date-range filters update KPIs, sentiment charts, aspect analysis, and review tables.
- Reddit `review_rating_num` remains on the 1-5 scale while `agreement_count` keeps larger upvote values.
- Logistic Regression vs. DistilBERT label agreement is about 89.15%.
