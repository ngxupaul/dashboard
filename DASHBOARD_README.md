# BTS Skytrain ABSA Business Dashboard

This Streamlit dashboard turns `full_dataset_with_predictions.csv` into a final-exam business UI for:

- service pain-point prioritization,
- aspect-based sentiment analysis,
- time-range filtering with monthly, quarterly, and yearly sentiment trend charts,
- rating vs. agreement separation,
- operational action evidence,
- searchable passenger review examples.

For section-by-section analysis notes, see
[`docs/analysis_explanation.md`](docs/analysis_explanation.md).

For table-by-table and chart-by-chart reading guidance, see
[`docs/dashboard_observation_guide.md`](docs/dashboard_observation_guide.md).

## Run

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If your default `python` is not available on Windows, use the Python executable installed for your environment.

## Deployment

### Streamlit Community Cloud

Use these settings for the full interactive dashboard:

- Repository: `ngxupaul/dashboard`
- Branch: `main`
- Main file path: `app.py`
- Python dependencies: `requirements.txt`
- App config: `.streamlit/config.toml`

After the Streamlit app is connected to this repository, pushing to `main` updates the deployed app automatically.

### GitHub Pages Static Snapshot

The repository includes a GitHub Pages workflow that builds a static business snapshot from the same CSV:

```powershell
python build_static_site.py
```

After pushing to `main`, GitHub Actions deploys it to:

<https://ngxupaul.github.io/dashboard/>

If that URL returns 404, enable Pages once in GitHub: **Settings -> Pages -> Deploy from a branch -> `gh-pages` -> `/ (root)`**.

### GitHub Codespaces

For the full Streamlit app on GitHub, use GitHub Codespaces and run:

```bash
python -m streamlit run app.py
```

## Data Rule

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
