from __future__ import annotations

import pandas as pd

from dashboard_data import (
    DATA_PATH,
    aspect_priority,
    filter_dataset,
    high_agreement_low_rating,
    load_dataset,
    model_agreement,
    sentiment_time_series,
)


def main() -> None:
    raw_header = pd.read_csv(DATA_PATH, nrows=0, encoding="utf-8-sig")
    assert len(raw_header.columns) == 54, f"Expected 54 raw columns, found {len(raw_header.columns)}"

    df = load_dataset(DATA_PATH)
    assert len(df) == 24459, f"Expected 24,459 rows, found {len(df)}"
    assert df["review_rating_num"].between(1, 5).all(), "Ratings must stay on the 1-5 scale"

    service_df = filter_dataset(df, service_relevant_only=True)
    assert 12000 <= len(service_df) <= 14000, (
        "Default service-relevant scope should be near the profiled 12.5k rows, "
        f"found {len(service_df):,}"
    )

    reddit = df[df["source_norm"].eq("reddit")]
    assert not reddit.empty, "Reddit rows should exist"
    assert reddit["review_rating_num"].max() <= 5, "Reddit rating must not use upvotes"
    assert reddit["agreement_count"].max() > 5, "Reddit agreement/upvote signal should be separate"

    priority = aspect_priority(service_df)
    top_aspects = priority.head(4)["Aspect"].tolist()
    assert "Crowding & Comfort" in top_aspects, "Crowding should remain a top priority"
    assert "Fare & Payment System" in top_aspects, "Fare/payment should remain a top priority"

    agreement, _pairs = model_agreement(df)
    assert 0.88 <= agreement <= 0.90, f"Expected model agreement around 89.15%, found {agreement:.2%}"

    complaints = high_agreement_low_rating(service_df, min_agreement=20, max_rating=2)
    assert not complaints.empty, "High-agreement, low-rating complaint table should not be empty"

    recent = filter_dataset(
        df,
        service_relevant_only=True,
        date_range=(pd.Timestamp("2025-01-01"), pd.Timestamp("2026-04-30")),
    )
    assert not recent.empty, "Date range filter should return recent BTS-service rows"
    assert recent["review_date_ui"].notna().all(), "Date-filtered rows should have parsed dates"
    assert recent["review_date_ui"].min() >= pd.Timestamp("2025-01-01"), "Date filter lower bound failed"
    assert recent["review_date_ui"].max() < pd.Timestamp("2026-05-01"), "Date filter upper bound failed"

    trend = sentiment_time_series(recent, "M")
    assert not trend.empty, "Sentiment time-series chart should have monthly data"
    assert set(trend["Sentiment"].unique()) == {"Negative", "Neutral", "Positive"}, (
        "Trend chart should include all three sentiment series"
    )

    print("Dashboard verification passed")
    print(f"Raw dataset: {len(df):,} rows x {len(raw_header.columns)} columns")
    print(f"Default service-relevant scope: {len(service_df):,} rows")
    print(f"LR vs DistilBERT agreement: {agreement:.2%}")
    print(f"Top priority aspects: {', '.join(top_aspects)}")
    print(f"Recent date-filtered rows: {len(recent):,}")


if __name__ == "__main__":
    main()
