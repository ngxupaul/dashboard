from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

import pandas as pd


DATA_PATH = Path(__file__).parent / "reference" / "all_reviews_predicted.csv"

SENTIMENT_ORDER = ["Negative", "Neutral", "Positive"]

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "and",
    "are",
    "around",
    "because",
    "been",
    "before",
    "being",
    "bts",
    "but",
    "can",
    "from",
    "get",
    "had",
    "has",
    "have",
    "into",
    "its",
    "just",
    "like",
    "more",
    "not",
    "one",
    "only",
    "our",
    "out",
    "over",
    "review",
    "skytrain",
    "some",
    "station",
    "stations",
    "than",
    "that",
    "the",
    "their",
    "there",
    "they",
    "this",
    "through",
    "train",
    "trains",
    "use",
    "was",
    "were",
    "when",
    "with",
    "you",
    "your",
}

ASPECT_COLUMNS = {
    "Staff & Customer Service": "sentiment_staff",
    "Punctuality & Reliability": "sentiment_punctuality",
    "Crowding & Comfort": "sentiment_crowding",
    "Cleanliness & Hygiene": "sentiment_cleanliness",
    "Fare & Payment System": "sentiment_fare_payment",
    "Safety & Security": "sentiment_safety",
    "Route Coverage & Connectivity": "sentiment_route_connectivity",
    "Signage & Navigation": "sentiment_signage",
    "Infrastructure & Facilities": "sentiment_infrastructure",
    "Overall Experience": "sentiment_overall",
}

RAW_ASPECT_MAP = {
    "Staff & Service Quality": "Staff & Customer Service",
    "Facilities & Accessibility": "Infrastructure & Facilities",
    "Information & Navigation": "Signage & Navigation",
    "Overall Experience & Convenience": "Overall Experience",
}

ACTION_ASPECTS = [
    "Crowding & Comfort",
    "Fare & Payment System",
    "Infrastructure & Facilities",
    "Route Coverage & Connectivity",
]

ASPECT_ACTIONS = {
    "Crowding & Comfort": {
        "goal": "Reduce peak-hour crowding and improve passenger flow.",
        "actions": [
            "Increase peak-period headway monitoring on the busiest BTS-linked stations.",
            "Use platform staff and queue lanes at high-pressure transfer points.",
            "Publish crowding guidance for alternate boarding times and nearby stations.",
        ],
        "metrics": [
            "Negative crowding reviews",
            "Agreement-weighted crowding complaints",
            "Peak-hour complaint share",
        ],
    },
    "Fare & Payment System": {
        "goal": "Reduce ticketing friction and top-up frustration.",
        "actions": [
            "Improve Rabbit Card top-up instructions and passport-policy messaging.",
            "Prioritize ticket machine UX fixes where queues or cash-only issues appear.",
            "Track digital payment complaints separately from fare-price complaints.",
        ],
        "metrics": [
            "Negative fare/payment reviews",
            "Ticket machine complaint share",
            "Rabbit Card complaint examples",
        ],
    },
    "Infrastructure & Facilities": {
        "goal": "Target facility issues that hurt trip comfort and accessibility.",
        "actions": [
            "Rank station facility issues by agreement-weighted complaints.",
            "Separate AC, escalator, elevator, and platform complaints for maintenance routing.",
            "Use high-agreement examples as evidence for operational follow-up.",
        ],
        "metrics": [
            "Negative infrastructure reviews",
            "Agreement-weighted facility complaints",
            "Accessibility-related review examples",
        ],
    },
    "Route Coverage & Connectivity": {
        "goal": "Improve transfer clarity and perceived network coverage.",
        "actions": [
            "Identify stations and transfers repeatedly mentioned with negative sentiment.",
            "Improve wayfinding around transfers to MRT, Airport Rail Link, buses, and malls.",
            "Use review text to separate true coverage gaps from navigation confusion.",
        ],
        "metrics": [
            "Negative route/connectivity reviews",
            "Transfer-related complaint share",
            "Station-specific complaint examples",
        ],
    },
}

TRUSTED_REVIEW_SOURCES = {"tripadvisor", "klook"}

BTS_SIGNAL_PATTERN = re.compile(
    "|".join(
        [
            r"\bbts\b",
            r"skytrain",
            r"rabbit\s+card",
            r"sukhumvit\s+line",
            r"silom\s+line",
            r"mo\s+chit\s+bts",
            r"saphan\s+khwai\s+bts",
            r"ari\s+bts",
            r"sanam\s+pao\s+bts",
            r"victory\s+monument\s+bts",
            r"phaya\s+thai\s+bts",
            r"ratchathewi\s+bts",
            r"siam\s+bts",
            r"chit\s+lom\s+bts",
            r"phloen\s+chit\s+bts",
            r"nana\s+bts",
            r"asok(?:e)?\s+bts",
            r"phrom\s+phong\s+bts",
            r"thong\s*lo(?:r)?\s+bts",
            r"ekkamai\s+bts",
            r"phra\s+khanong\s+bts",
            r"on\s+nut\s+bts",
            r"bang\s+chak\s+bts",
            r"punnawithi\s+bts",
            r"udom\s+suk\s+bts",
            r"bang\s+na\s+bts",
            r"bearing\s+bts",
            r"samrong\s+bts",
            r"national\s+stadium\s+bts",
            r"ratchadamri\s+bts",
            r"sala\s+daeng\s+bts",
            r"chong\s+nonsi\s+bts",
            r"saint\s+louis\s+bts",
            r"surasak\s+bts",
            r"saphan\s+taksin\s+bts",
            r"krung\s+thon\s+buri\s+bts",
            r"wongwian\s+yai\s+bts",
        ]
    ),
    flags=re.IGNORECASE,
)

REQUIRED_COLUMNS = [
    "review_text",
    "review_rating",
    "source",
    "created_at_date",
    "bts_line",
    "aspect_pred",
    "sentiment_pred",
]


def load_dataset(csv_path: Path | str = DATA_PATH) -> pd.DataFrame:
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path, low_memory=False, encoding="utf-8-sig")
    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    return prepare_dataset(normalize_prediction_dataset(df))


def normalize_prediction_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Map the final prediction CSV into the dashboard's analysis contract."""
    df = df.copy()
    predicted_aspect = df["aspect_pred"].where(df["aspect_pred"].notna(), df.get("aspect", ""))
    predicted_sentiment = df["sentiment_pred"].where(
        df["sentiment_pred"].notna(),
        df.get("sentiment", ""),
    )

    df["primary_aspect"] = (
        predicted_aspect.fillna("")
        .astype(str)
        .str.strip()
        .replace(RAW_ASPECT_MAP)
    )
    df["Final_Label"] = predicted_sentiment.fillna("").astype(str).str.strip()
    df.loc[~df["Final_Label"].isin(SENTIMENT_ORDER), "Final_Label"] = "Neutral"

    df["review_title"] = ""
    df["review_rating_num"] = pd.to_numeric(df["review_rating"], errors="coerce").fillna(3)
    df["published_date"] = df["created_at_date"]
    df["review_date"] = df["created_at_date"]
    df["like_count"] = 0
    df["relevant"] = True
    df["review_link"] = ""
    df["LogisticRegression_Label"] = df.get("sentiment", df["Final_Label"])
    df["DistilBERT_Label"] = df["Final_Label"]

    for aspect, column in ASPECT_COLUMNS.items():
        df[column] = "Neutral"
        mask = df["primary_aspect"].eq(aspect)
        df.loc[mask, column] = df.loc[mask, "Final_Label"]

    return df


def prepare_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for column in [
        "review_title",
        "review_text",
        "full_text",
        "clean_text",
        "review_link",
        "source",
        "bts_line",
        "Final_Label",
        "overall_sentiment",
        "primary_aspect",
        "LogisticRegression_Label",
        "DistilBERT_Label",
        *ASPECT_COLUMNS.values(),
    ]:
        if column in df.columns:
            df[column] = df[column].fillna("").astype(str)

    df["review_rating_num"] = pd.to_numeric(
        df["review_rating_num"].where(df["review_rating_num"].notna(), df["review_rating"]),
        errors="coerce",
    ).fillna(3)
    df["agreement_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0)
    df["source_display"] = df["source"].str.strip().replace("", "Unknown")
    df["source_norm"] = df["source_display"].str.lower()
    df["bts_line_display"] = df["bts_line"].str.strip().replace("", "Unspecified")

    review_date = pd.to_datetime(df["review_date"], errors="coerce")
    published_date = pd.to_datetime(df["published_date"], errors="coerce")
    df["review_date_ui"] = review_date.fillna(published_date)
    df["review_month_ui"] = df["review_date_ui"].dt.to_period("M").astype(str)
    df.loc[df["review_month_ui"].eq("NaT"), "review_month_ui"] = "Unknown"

    text_source = _join_text_columns(df, ["review_title", "review_text"])
    fallback_text = _join_text_columns(df, ["full_text", "clean_text"])
    df["full_review_text"] = text_source.where(text_source.str.len() > 0, fallback_text)
    df["text_snippet"] = df["full_review_text"].map(_snippet)
    df["review_title_display"] = df["review_title"].map(_snippet_title)

    relevance_text = _join_text_columns(
        df,
        ["review_title", "review_text", "full_text", "clean_text"],
    )
    base_relevant = df["relevant"].astype(str).str.lower().eq("true")
    trusted_source = df["source_norm"].isin(TRUSTED_REVIEW_SOURCES)
    direct_bts_signal = relevance_text.str.contains(BTS_SIGNAL_PATTERN, regex=True, na=False)
    df["service_relevant"] = base_relevant | trusted_source | direct_bts_signal

    df["is_negative"] = df["Final_Label"].eq("Negative")
    df["negative_agreement_weight"] = df["agreement_count"].where(df["is_negative"], 0)
    return df


def filter_dataset(
    df: pd.DataFrame,
    *,
    service_relevant_only: bool = True,
    sources: list[str] | None = None,
    lines: list[str] | None = None,
    sentiments: list[str] | None = None,
    aspects: list[str] | None = None,
    ratings: tuple[float, float] | None = None,
    date_range: tuple[pd.Timestamp, pd.Timestamp] | None = None,
    min_agreement: float = 0,
    search_text: str = "",
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    if service_relevant_only:
        mask &= df["service_relevant"]
    if sources:
        mask &= df["source_display"].isin(sources)
    if lines:
        mask &= df["bts_line_display"].isin(lines)
    if sentiments:
        mask &= df["Final_Label"].isin(sentiments)
    if aspects:
        aspect_mask = df["primary_aspect"].isin(aspects)
        for aspect in aspects:
            column = ASPECT_COLUMNS.get(aspect)
            if column:
                aspect_mask |= df[column].isin(["Positive", "Negative"])
        mask &= aspect_mask
    if ratings:
        low, high = ratings
        mask &= df["review_rating_num"].between(low, high)
    if date_range and all(date_range):
        start, end = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        end = end + pd.Timedelta(days=1) - pd.Timedelta(nanoseconds=1)
        mask &= df["review_date_ui"].notna() & df["review_date_ui"].between(start, end)
    if min_agreement:
        mask &= df["agreement_count"] >= min_agreement
    if search_text.strip():
        pattern = re.escape(search_text.strip())
        mask &= df["full_review_text"].str.contains(pattern, case=False, regex=True, na=False)

    return df.loc[mask].copy()


def kpi_summary(df: pd.DataFrame, total_rows: int) -> dict[str, float]:
    review_count = len(df)
    negative_count = int(df["Final_Label"].eq("Negative").sum())
    neutral_count = int(df["Final_Label"].eq("Neutral").sum())
    positive_count = int(df["Final_Label"].eq("Positive").sum())
    dated = df["review_date_ui"].dropna()
    satisfaction_index = (
        (positive_count + 0.5 * neutral_count) / review_count * 100 if review_count else 0
    )
    return {
        "total_reviews": total_rows,
        "filtered_reviews": review_count,
        "positive_reviews": positive_count,
        "neutral_reviews": neutral_count,
        "negative_reviews": negative_count,
        "net_sentiment_score": ((positive_count - negative_count) / review_count * 100)
        if review_count
        else 0,
        "average_rating": float(df["review_rating_num"].mean()) if review_count else 0,
        "negative_share": negative_count / review_count if review_count else 0,
        "neutral_share": neutral_count / review_count if review_count else 0,
        "positive_share": positive_count / review_count if review_count else 0,
        "satisfaction_index": satisfaction_index,
        "total_agreement": float(df["agreement_count"].sum()),
        "negative_agreement": float(df["negative_agreement_weight"].sum()),
        "date_start": dated.min().strftime("%Y-%m-%d") if not dated.empty else "",
        "date_end": dated.max().strftime("%Y-%m-%d") if not dated.empty else "",
    }


def sentiment_distribution(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["Final_Label"].value_counts().reindex(SENTIMENT_ORDER, fill_value=0)
    out = counts.rename_axis("Sentiment").reset_index(name="Reviews")
    total = out["Reviews"].sum()
    out["Share"] = (out["Reviews"] / total).fillna(0)
    return out


def sentiment_time_series(df: pd.DataFrame, frequency: str = "M") -> pd.DataFrame:
    dated = df[df["review_date_ui"].notna()].copy()
    if dated.empty:
        return pd.DataFrame(columns=["Period", "Sentiment", "Reviews", "Share"])

    dated["Period"] = dated["review_date_ui"].dt.to_period(frequency).dt.to_timestamp()
    grouped = (
        dated.groupby(["Period", "Final_Label"])
        .size()
        .rename("Reviews")
        .reset_index()
        .rename(columns={"Final_Label": "Sentiment"})
    )
    periods = sorted(grouped["Period"].unique())
    index = pd.MultiIndex.from_product(
        [periods, SENTIMENT_ORDER],
        names=["Period", "Sentiment"],
    )
    out = (
        grouped.set_index(["Period", "Sentiment"])
        .reindex(index, fill_value=0)
        .reset_index()
    )
    totals = out.groupby("Period")["Reviews"].transform("sum")
    out["Share"] = (out["Reviews"] / totals).fillna(0)
    return out


def net_sentiment_time_series(df: pd.DataFrame, frequency: str = "M") -> pd.DataFrame:
    trend = sentiment_time_series(df, frequency)
    if trend.empty:
        return pd.DataFrame(columns=["Period", "Positive", "Neutral", "Negative", "Reviews", "NSS"])

    pivot = (
        trend.pivot_table(index="Period", columns="Sentiment", values="Reviews", aggfunc="sum")
        .reindex(columns=SENTIMENT_ORDER, fill_value=0)
        .sort_index()
    )
    pivot["Reviews"] = pivot[SENTIMENT_ORDER].sum(axis=1)
    pivot["NSS"] = (
        (pivot["Positive"] - pivot["Negative"]) / pivot["Reviews"].replace(0, pd.NA) * 100
    ).fillna(0)
    return pivot.reset_index()


def aspect_net_sentiment_time_series(df: pd.DataFrame, frequency: str = "M") -> pd.DataFrame:
    rows = []
    for aspect in ASPECT_COLUMNS:
        trend = aspect_sentiment_time_series(df, aspect, frequency)
        if trend.empty:
            continue
        pivot = (
            trend.pivot_table(index="Period", columns="Sentiment", values="Reviews", aggfunc="sum")
            .reindex(columns=SENTIMENT_ORDER, fill_value=0)
            .sort_index()
        )
        pivot["Reviews"] = pivot[SENTIMENT_ORDER].sum(axis=1)
        pivot["NSS"] = (
            (pivot["Positive"] - pivot["Negative"]) / pivot["Reviews"].replace(0, pd.NA) * 100
        ).fillna(0)
        for period, row in pivot.iterrows():
            if int(row["Reviews"]) > 0:
                rows.append(
                    {
                        "Period": period,
                        "Aspect": aspect,
                        "Reviews": int(row["Reviews"]),
                        "NSS": float(row["NSS"]),
                        "Positive": int(row["Positive"]),
                        "Negative": int(row["Negative"]),
                    }
                )
    return pd.DataFrame(rows)


def aspect_nss_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for aspect, column in ASPECT_COLUMNS.items():
        mask = df["primary_aspect"].eq(aspect) | df[column].isin(["Positive", "Negative"])
        subset = df.loc[mask]
        if subset.empty:
            rows.append(
                {
                    "Aspect": aspect,
                    "Reviews": 0,
                    "Positive": 0,
                    "Negative": 0,
                    "NSS": 0.0,
                }
            )
            continue
        counts = subset[column].value_counts().reindex(SENTIMENT_ORDER, fill_value=0)
        reviews = int(counts.sum())
        nss = (counts["Positive"] - counts["Negative"]) / reviews * 100 if reviews else 0
        rows.append(
            {
                "Aspect": aspect,
                "Reviews": reviews,
                "Positive": int(counts["Positive"]),
                "Negative": int(counts["Negative"]),
                "NSS": float(nss),
            }
        )
    return pd.DataFrame(rows).sort_values("NSS")


def time_coverage_summary(df: pd.DataFrame) -> dict[str, object]:
    dated = df["review_date_ui"].dropna()
    if dated.empty:
        return {
            "date_count": 0,
            "start": "",
            "end": "",
            "message": "No usable date field is available, so time-based analysis is disabled.",
        }
    distinct_days = int(dated.dt.date.nunique())
    start = dated.min().strftime("%Y-%m-%d %H:%M")
    end = dated.max().strftime("%Y-%m-%d %H:%M")
    if distinct_days <= 1:
        message = (
            "The prediction file contains a single review date snapshot. Daily, weekly, "
            "monthly, and quarterly controls are available, but trend claims should be "
            "treated as snapshot monitoring rather than long-term seasonality."
        )
    else:
        message = (
            f"The data spans {distinct_days:,} distinct review dates, allowing period-over-period "
            "sentiment movement and recovery analysis."
        )
    return {"date_count": distinct_days, "start": start, "end": end, "message": message}


def aspect_sentiment_time_series(
    df: pd.DataFrame,
    aspect: str,
    frequency: str = "M",
) -> pd.DataFrame:
    column = ASPECT_COLUMNS[aspect]
    mentioned = df[
        df["review_date_ui"].notna()
        & (df[column].isin(["Positive", "Negative"]) | df["primary_aspect"].eq(aspect))
    ].copy()
    if mentioned.empty:
        return pd.DataFrame(columns=["Period", "Sentiment", "Reviews", "Share"])

    mentioned["Period"] = mentioned["review_date_ui"].dt.to_period(frequency).dt.to_timestamp()
    grouped = (
        mentioned.groupby(["Period", column])
        .size()
        .rename("Reviews")
        .reset_index()
        .rename(columns={column: "Sentiment"})
    )
    periods = sorted(grouped["Period"].unique())
    index = pd.MultiIndex.from_product(
        [periods, SENTIMENT_ORDER],
        names=["Period", "Sentiment"],
    )
    out = (
        grouped.set_index(["Period", "Sentiment"])
        .reindex(index, fill_value=0)
        .reset_index()
    )
    totals = out.groupby("Period")["Reviews"].transform("sum")
    out["Share"] = (out["Reviews"] / totals).fillna(0)
    return out


def source_distribution(df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
    out = (
        df["source_display"]
        .value_counts()
        .head(limit)
        .rename_axis("Source")
        .reset_index(name="Reviews")
    )
    return out


def categorical_sentiment_breakdown(
    df: pd.DataFrame,
    column: str,
    label: str,
    *,
    limit: int = 12,
) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame(columns=[label, "Reviews", "Negative", "Neutral", "Positive", "Negative share"])

    grouped = (
        df.groupby([column, "Final_Label"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=SENTIMENT_ORDER, fill_value=0)
    )
    grouped["Reviews"] = grouped[SENTIMENT_ORDER].sum(axis=1)
    grouped["Negative share"] = (grouped["Negative"] / grouped["Reviews"]).fillna(0)
    out = grouped.reset_index().rename(columns={column: label})
    return out.sort_values(["Reviews", "Negative"], ascending=False).head(limit)


def aspect_priority(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for aspect, column in ASPECT_COLUMNS.items():
        negative_mask = df[column].eq("Negative")
        positive_mask = df[column].eq("Positive")
        neutral_mask = df[column].eq("Neutral")
        mentioned_mask = negative_mask | positive_mask | df["primary_aspect"].eq(aspect)
        negative_count = int(negative_mask.sum())
        positive_count = int(positive_mask.sum())
        neutral_count = int((neutral_mask & mentioned_mask).sum())
        mention_count = int(mentioned_mask.sum())
        negative_agreement = float(df.loc[negative_mask, "agreement_count"].sum())
        priority_score = negative_count + 0.1 * negative_agreement
        rows.append(
            {
                "Aspect": aspect,
                "Mentions": mention_count,
                "Negative": negative_count,
                "Neutral": neutral_count,
                "Positive": positive_count,
                "Negative agreement": negative_agreement,
                "Priority score": priority_score,
                "Negative share": negative_count / mention_count if mention_count else 0,
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["Priority score", "Negative"],
        ascending=False,
    )


def root_cause_matrix(df: pd.DataFrame) -> pd.DataFrame:
    priority = aspect_priority(df)
    rows = []
    for _, row in priority.iterrows():
        aspect = row["Aspect"]
        severity = risk_level(row["Negative share"], row["Negative"], row["Negative agreement"])
        rows.append(
            {
                "Problem": root_cause_problem(aspect),
                "Related aspect": aspect,
                "Frequency": int(row["Negative"]),
                "Mentions": int(row["Mentions"]),
                "Negative share": float(row["Negative share"]),
                "Agreement evidence": int(row["Negative agreement"]),
                "Severity": severity,
                "Interpretation": root_cause_interpretation(aspect, row, severity),
            }
        )
    return pd.DataFrame(rows)


def risk_level(negative_share: float, negative_count: float, agreement: float) -> str:
    if negative_share >= 0.45 and negative_count >= 250 and agreement >= 1000:
        return "Critical"
    if negative_share >= 0.35 and (negative_count >= 150 or agreement >= 500):
        return "High"
    if negative_share >= 0.2 and negative_count >= 75:
        return "Medium"
    return "Low"


def root_cause_problem(aspect: str) -> str:
    return {
        "Crowding & Comfort": "Peak-hour crowding and travel comfort pressure",
        "Fare & Payment System": "Fare, ticketing, Rabbit Card, or payment friction",
        "Infrastructure & Facilities": "Station facility, access, AC, escalator, or platform issue",
        "Route Coverage & Connectivity": "Transfer clarity or network connectivity gap",
        "Staff & Customer Service": "Staff support or service consistency issue",
        "Punctuality & Reliability": "Waiting time, delay, or reliability concern",
        "Cleanliness & Hygiene": "Cleanliness and station hygiene concern",
        "Safety & Security": "Safety, security, or crowd-control concern",
        "Signage & Navigation": "Wayfinding, signage, or navigation confusion",
        "Overall Experience": "General BTS experience dissatisfaction",
    }.get(aspect, f"{aspect} operational issue")


def root_cause_interpretation(aspect: str, row: pd.Series, severity: str) -> str:
    return (
        f"{aspect} is rated {severity.lower()} because {int(row['Negative']):,} of "
        f"{int(row['Mentions']):,} mentioned reviews are negative "
        f"({float(row['Negative share']):.1%}) and those complaints collect "
        f"{int(row['Negative agreement']):,} agreement points."
    )


def recent_period_comparison(df: pd.DataFrame, frequency: str = "M") -> dict[str, object]:
    trend = sentiment_time_series(df, frequency)
    if trend.empty:
        return {}

    pivot = (
        trend.pivot_table(index="Period", columns="Sentiment", values="Reviews", aggfunc="sum")
        .reindex(columns=SENTIMENT_ORDER, fill_value=0)
        .sort_index()
    )
    if len(pivot) < 2:
        return {}

    previous = pivot.iloc[-2]
    current = pivot.iloc[-1]
    previous_total = previous.sum()
    current_total = current.sum()
    previous_negative_share = previous["Negative"] / previous_total if previous_total else 0
    current_negative_share = current["Negative"] / current_total if current_total else 0
    return {
        "previous_period": pivot.index[-2].strftime("%Y-%m-%d"),
        "current_period": pivot.index[-1].strftime("%Y-%m-%d"),
        "previous_reviews": int(previous_total),
        "current_reviews": int(current_total),
        "previous_negative_share": float(previous_negative_share),
        "current_negative_share": float(current_negative_share),
        "negative_share_change": float(current_negative_share - previous_negative_share),
        "negative_count_change": int(current["Negative"] - previous["Negative"]),
        "positive_count_change": int(current["Positive"] - previous["Positive"]),
    }


def negative_spikes(df: pd.DataFrame, frequency: str = "M", *, limit: int = 5) -> pd.DataFrame:
    trend = sentiment_time_series(df, frequency)
    if trend.empty:
        return pd.DataFrame(columns=["Period", "Negative reviews", "Negative share", "Spike score"])

    negative = trend[trend["Sentiment"].eq("Negative")].copy()
    if negative.empty:
        return pd.DataFrame(columns=["Period", "Negative reviews", "Negative share", "Spike score"])

    negative["Rolling mean"] = negative["Reviews"].rolling(3, min_periods=1).mean().shift(1)
    negative["Spike score"] = (negative["Reviews"] - negative["Rolling mean"]).fillna(0)
    out = negative[negative["Spike score"].gt(0)].copy()
    out = out.sort_values(["Spike score", "Reviews"], ascending=False).head(limit)
    return out.rename(
        columns={
            "Reviews": "Negative reviews",
            "Share": "Negative share",
        }
    )[["Period", "Negative reviews", "Negative share", "Spike score"]]


def aspect_recent_changes(df: pd.DataFrame, frequency: str = "M") -> pd.DataFrame:
    rows = []
    for aspect in ASPECT_COLUMNS:
        trend = aspect_sentiment_time_series(df, aspect, frequency)
        if trend.empty:
            continue
        pivot = (
            trend.pivot_table(index="Period", columns="Sentiment", values="Reviews", aggfunc="sum")
            .reindex(columns=SENTIMENT_ORDER, fill_value=0)
            .sort_index()
        )
        if len(pivot) < 2:
            continue
        previous = pivot.iloc[-2]
        current = pivot.iloc[-1]
        previous_total = previous.sum()
        current_total = current.sum()
        previous_negative_share = previous["Negative"] / previous_total if previous_total else 0
        current_negative_share = current["Negative"] / current_total if current_total else 0
        rows.append(
            {
                "Aspect": aspect,
                "Previous negative share": float(previous_negative_share),
                "Current negative share": float(current_negative_share),
                "Negative share change": float(current_negative_share - previous_negative_share),
                "Negative count change": int(current["Negative"] - previous["Negative"]),
                "Current mentions": int(current_total),
            }
        )
    columns = [
        "Aspect",
        "Previous negative share",
        "Current negative share",
        "Negative share change",
        "Negative count change",
        "Current mentions",
    ]
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns).sort_values("Negative share change", ascending=False)


def keyword_frequency(
    df: pd.DataFrame,
    *,
    sentiment: str,
    limit: int = 20,
    min_length: int = 4,
) -> pd.DataFrame:
    subset = df[df["Final_Label"].eq(sentiment)]
    words: Counter[str] = Counter()
    for text in subset["full_review_text"].fillna("").astype(str):
        for word in re.findall(r"[A-Za-z][A-Za-z']+", text.lower()):
            word = word.strip("'")
            if len(word) >= min_length and word not in STOPWORDS:
                words[word] += 1
    return pd.DataFrame(
        [{"Keyword": word, "Count": count} for word, count in words.most_common(limit)]
    )


def lda_topic_keywords(
    df: pd.DataFrame,
    *,
    sentiment: str,
    n_topics: int = 6,
    n_top_words: int = 8,
) -> pd.DataFrame:
    texts = (
        df.loc[df["Final_Label"].eq(sentiment), "full_review_text"]
        .fillna("")
        .astype(str)
        .tolist()
    )
    texts = [text for text in texts if len(text.split()) >= 5]
    if len(texts) < n_topics * 2:
        return pd.DataFrame(columns=["Topic", "Keywords", "Weight"])

    try:
        from sklearn.decomposition import LatentDirichletAllocation
        from sklearn.feature_extraction.text import CountVectorizer
    except ImportError:
        keywords = keyword_frequency(df, sentiment=sentiment, limit=n_topics * n_top_words)
        rows = []
        for topic_idx in range(n_topics):
            chunk = keywords.iloc[topic_idx * n_top_words : (topic_idx + 1) * n_top_words]
            if chunk.empty:
                continue
            rows.append(
                {
                    "Topic": f"Topic {topic_idx + 1}",
                    "Keywords": ", ".join(chunk["Keyword"].tolist()),
                    "Weight": int(chunk["Count"].sum()),
                }
            )
        return pd.DataFrame(rows)

    vectorizer = CountVectorizer(
        max_features=4000,
        stop_words=list(STOPWORDS),
        token_pattern=r"\b[a-z]{3,}\b",
        min_df=5,
    )
    matrix = vectorizer.fit_transform(texts)
    if matrix.shape[1] == 0:
        return pd.DataFrame(columns=["Topic", "Keywords", "Weight"])

    lda = LatentDirichletAllocation(
        n_components=n_topics,
        random_state=42,
        max_iter=12,
        learning_method="batch",
    ).fit(matrix)
    feature_names = vectorizer.get_feature_names_out()
    rows = []
    for idx, component in enumerate(lda.components_):
        top_idx = component.argsort()[: -n_top_words - 1 : -1]
        rows.append(
            {
                "Topic": f"Topic {idx + 1}",
                "Keywords": ", ".join(feature_names[i] for i in top_idx),
                "Weight": float(component[top_idx].sum()),
            }
        )
    return pd.DataFrame(rows)


def aspect_sentiment_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for aspect, column in ASPECT_COLUMNS.items():
        mentioned_mask = df[column].isin(["Positive", "Negative"]) | df["primary_aspect"].eq(aspect)
        counts = df.loc[mentioned_mask, column].value_counts().reindex(SENTIMENT_ORDER, fill_value=0)
        for sentiment, count in counts.items():
            rows.append({"Aspect": aspect, "Sentiment": sentiment, "Reviews": int(count)})
    return pd.DataFrame(rows)


def high_agreement_low_rating(
    df: pd.DataFrame,
    *,
    min_agreement: float = 20,
    max_rating: float = 2,
    limit: int = 25,
) -> pd.DataFrame:
    mask = (
        df["Final_Label"].eq("Negative")
        & df["review_rating_num"].le(max_rating)
        & df["agreement_count"].ge(min_agreement)
    )
    return review_table(
        df.loc[mask].sort_values(["agreement_count", "review_rating_num"], ascending=[False, True]),
        limit=limit,
    )


def model_agreement(df: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    valid = df[
        df["LogisticRegression_Label"].isin(SENTIMENT_ORDER)
        & df["DistilBERT_Label"].isin(SENTIMENT_ORDER)
    ]
    if valid.empty:
        return 0, pd.DataFrame()

    agreement = valid["LogisticRegression_Label"].eq(valid["DistilBERT_Label"]).mean()
    pairs = (
        valid.groupby(["LogisticRegression_Label", "DistilBERT_Label"])
        .size()
        .reset_index(name="Reviews")
        .sort_values("Reviews", ascending=False)
    )
    return float(agreement), pairs


def aspect_evidence_reviews(
    df: pd.DataFrame,
    aspect: str,
    *,
    limit: int = 5,
    negative_only: bool = True,
) -> pd.DataFrame:
    column = ASPECT_COLUMNS[aspect]
    if negative_only:
        mask = df[column].eq("Negative") | (
            df["primary_aspect"].eq(aspect) & df["Final_Label"].eq("Negative")
        )
    else:
        mask = df[column].isin(["Positive", "Negative"]) | df["primary_aspect"].eq(aspect)
    ranked = df.loc[mask].sort_values(
        ["agreement_count", "review_rating_num"],
        ascending=[False, True],
    )
    return review_table(ranked, limit=limit)


def review_table(df: pd.DataFrame, *, limit: int = 200) -> pd.DataFrame:
    columns = [
        "review_date_ui",
        "review_title_display",
        "text_snippet",
        "source_display",
        "bts_line_display",
        "review_rating_num",
        "agreement_count",
        "primary_aspect",
        "Final_Label",
        "review_link",
    ]
    out = df.head(limit)[columns].rename(
        columns={
            "review_date_ui": "Date",
            "review_title_display": "Title",
            "text_snippet": "Review snippet",
            "source_display": "Source",
            "bts_line_display": "BTS line",
            "review_rating_num": "Rating",
            "agreement_count": "Agreement count",
            "primary_aspect": "Primary aspect",
            "Final_Label": "Sentiment",
            "review_link": "Review link",
        }
    )
    return out.reset_index(drop=True)


def _join_text_columns(df: pd.DataFrame, columns: list[str]) -> pd.Series:
    available = [column for column in columns if column in df.columns]
    if not available:
        return pd.Series("", index=df.index)
    text = df[available[0]].fillna("").astype(str)
    for column in available[1:]:
        text = text.str.cat(df[column].fillna("").astype(str), sep=" ")
    return text.map(_normalize_spaces)


def _normalize_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", str(value)).strip()


def _snippet(value: str, length: int = 260) -> str:
    text = _normalize_spaces(value)
    if len(text) <= length:
        return text
    return text[: length - 3].rstrip() + "..."


def _snippet_title(value: str, length: int = 90) -> str:
    text = _normalize_spaces(value)
    if not text:
        return "Untitled review"
    if len(text) <= length:
        return text
    return text[: length - 3].rstrip() + "..."
