from __future__ import annotations

import pandas as pd

from dashboard_data import (
    ASPECT_COLUMNS,
    DATA_PATH,
    aspect_nss_summary,
    aspect_priority,
    filter_dataset,
    high_agreement_low_rating,
    lda_topic_keywords,
    load_dataset,
    model_agreement,
    sentiment_time_series,
    time_coverage_summary,
)


def main() -> None:
    raw_header = pd.read_csv(DATA_PATH, nrows=0, encoding="utf-8-sig")
    expected_columns = {
        "review_text",
        "review_rating",
        "source",
        "created_at_date",
        "bts_line",
        "aspect_pred",
        "sentiment_pred",
    }
    missing = expected_columns - set(raw_header.columns)
    assert not missing, f"Prediction CSV is missing columns: {sorted(missing)}"

    df = load_dataset(DATA_PATH)
    assert len(df) == 20782, f"Expected 20,782 rows, found {len(df):,}"
    assert df["review_rating_num"].between(1, 5).all(), "Ratings must stay on the 1-5 scale"
    assert df["Final_Label"].isin({"Negative", "Neutral", "Positive"}).all(), (
        "Predicted sentiment must normalize to three sentiment classes"
    )
    assert set(ASPECT_COLUMNS).issuperset(set(df["primary_aspect"].unique())), (
        "Predicted aspects must normalize to the dashboard aspect taxonomy"
    )

    service_df = filter_dataset(df, service_relevant_only=True)
    assert len(service_df) == len(df), (
        "The final prediction file should already be scoped to BTS-service reviews"
    )

    priority = aspect_priority(service_df)
    top_aspects = priority.head(4)["Aspect"].tolist()
    assert "Fare & Payment System" in top_aspects, "Fare/payment should remain a top priority"
    assert "Crowding & Comfort" in top_aspects, "Crowding should remain a top priority"

    agreement, _pairs = model_agreement(df)
    assert 0.0 <= agreement <= 1.0, "Model agreement must be a valid ratio"

    complaints = high_agreement_low_rating(service_df, min_agreement=0, max_rating=2)
    assert not complaints.empty, "Low-rating complaint table should not be empty"

    trend = sentiment_time_series(service_df, "D")
    assert not trend.empty, "Sentiment time-series chart should have daily data"
    assert set(trend["Sentiment"].unique()) == {"Negative", "Neutral", "Positive"}, (
        "Trend chart should include all three sentiment series"
    )

    nss = aspect_nss_summary(service_df)
    assert not nss.empty and {"Aspect", "NSS"}.issubset(nss.columns), (
        "NSS by aspect must be available for notebook business-insight charts"
    )

    topics = lda_topic_keywords(service_df, sentiment="Negative", n_topics=3, n_top_words=5)
    assert not topics.empty, "Negative LDA/topic keyword table should not be empty"

    coverage = time_coverage_summary(service_df)
    assert coverage["date_count"] >= 1, "Time coverage summary should detect at least one date"

    print("Dashboard verification passed")
    print(f"Prediction dataset: {len(df):,} rows x {len(raw_header.columns)} columns")
    print(f"Default BTS scope: {len(service_df):,} rows")
    print(f"Original-vs-predicted sentiment agreement: {agreement:.2%}")
    print(f"Top priority aspects: {', '.join(top_aspects)}")
    print(f"Time coverage: {coverage['message']}")


if __name__ == "__main__":
    main()
