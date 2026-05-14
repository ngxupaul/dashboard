# BTS Skytrain ABSA Business Dashboard

Static HTML/JavaScript business dashboard for the final exam topic:

**Enhancing BTS Skytrain Services through Aspect-Based Sentiment Analysis of Passenger Reviews**

The final dashboard is generated from `full_dataset_with_predictions.csv` and does **not** require Streamlit. It shows:

- overall sentiment from `Final_Label`,
- sentiment distribution for every ABSA service aspect,
- monthly sentiment trend for each selected aspect,
- aspect priority ranking,
- high-agreement complaint evidence,
- a dedicated Business Suggestions tab with numeric evidence and written conclusions for each recommendation.

Detailed explanations for each analysis section are in
[`docs/analysis_explanation.md`](docs/analysis_explanation.md).

A table-by-table and chart-by-chart observation guide is in
[`docs/dashboard_observation_guide.md`](docs/dashboard_observation_guide.md).

## Core Data Rule

`Final_Label` is the final overall sentiment of the whole review.

Aspect-based sentiment uses the `sentiment_*` columns:

- `sentiment_fare_payment` for fare, payment, and price-related feedback,
- `sentiment_crowding` for crowding and comfort,
- `sentiment_infrastructure` for facilities,
- `sentiment_route_connectivity` for route and connectivity,
- `sentiment_overall` for the ABSA aspect **Overall Experience**.

`sentiment_overall` is an aspect-level field. It is not the same thing as the global overall sentiment.

`review_rating_num` is the 1-5 sentiment-derived rating. `like_count` is preserved separately as `agreement_count`, so high-upvote complaints stay negative complaints with stronger evidence weight.

## Build Locally

```powershell
python -m pip install -r requirements.txt
python build_static_site.py
```

Open:

```text
docs/index.html
```

## Deploy

The dashboard is deployed as a static GitHub Pages site.

The workflow in `.github/workflows/deploy-pages.yml` verifies the data contract, builds `docs/index.html`, and deploys the generated static dashboard.

Expected URL after the workflow finishes:

<https://ngxupaul.github.io/dashboard/>

One-time GitHub setting if the URL returns 404:
open repository **Settings -> Pages**, choose **Deploy from a branch**, select `gh-pages` and `/ (root)`, then save.

## Verify

```powershell
python verify_dashboard.py
```

The verification checks the CSV shape, default BTS-service relevance filter, Reddit rating/upvote separation, model agreement, date filtering, and sentiment time-series output.
