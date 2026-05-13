# BTS Skytrain ABSA Business Dashboard

Streamlit business dashboard for the final exam topic:

**Enhancing BTS Skytrain Services through Aspect-Based Sentiment Analysis of Passenger Reviews**

The dashboard uses `full_dataset_with_predictions.csv` as its single input and shows:

- executive KPIs for service-relevant reviews,
- sentiment trends by selected date range,
- ABSA service-aspect priority ranking,
- rating vs. agreement separation,
- operational recommendations backed by review evidence,
- searchable passenger review explorer.

## Core Data Rule

`review_rating_num` is the 1-5 sentiment-derived rating.

`like_count` is preserved separately as `agreement_count`, so Reddit upvotes or platform engagement measure how many people agree with or engage with a complaint. A high-upvote negative review is not treated as a 5-star review.

## Run Locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Verify

```powershell
python verify_dashboard.py
```

The verification checks the CSV shape, default BTS-service relevance filter, Reddit rating/upvote separation, model agreement, date filtering, and sentiment time-series output.
