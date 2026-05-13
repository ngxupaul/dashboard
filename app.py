from __future__ import annotations

from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from dashboard_data import (
    ACTION_ASPECTS,
    ASPECT_ACTIONS,
    ASPECT_COLUMNS,
    DATA_PATH,
    SENTIMENT_ORDER,
    aspect_sentiment_time_series,
    aspect_evidence_reviews,
    aspect_priority,
    aspect_sentiment_matrix,
    filter_dataset,
    high_agreement_low_rating,
    kpi_summary,
    load_dataset,
    model_agreement,
    review_table,
    sentiment_distribution,
    sentiment_time_series,
    source_distribution,
)


SENTIMENT_COLORS = {
    "Negative": "#C43C35",
    "Neutral": "#8A8F98",
    "Positive": "#1F8A70",
}


st.set_page_config(
    page_title="BTS Skytrain ABSA Business Dashboard",
    page_icon=None,
    layout="wide",
)


@st.cache_data(show_spinner="Loading BTS review dataset...")
def get_data() -> pd.DataFrame:
    return load_dataset(DATA_PATH)


def main() -> None:
    inject_css()
    df = get_data()
    filtered = sidebar_filters(df)

    st.markdown(
        """
        <div class="app-header">
            <div>
                <h1>BTS Skytrain Business Intelligence</h1>
                <p>Aspect-based sentiment analysis of passenger reviews for service improvement decisions.</p>
            </div>
            <div class="header-pill">ABSA final exam dashboard</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if filtered.empty:
        st.warning("No reviews match the current filters.")
        return

    page = st.sidebar.radio(
        "Dashboard view",
        [
            "Executive Overview",
            "Aspect Priority Dashboard",
            "Rating vs Agreement",
            "Operational Actions",
            "Review Explorer",
        ],
    )

    if page == "Executive Overview":
        executive_overview(df, filtered)
    elif page == "Aspect Priority Dashboard":
        aspect_priority_dashboard(filtered)
    elif page == "Rating vs Agreement":
        rating_vs_agreement(filtered)
    elif page == "Operational Actions":
        operational_actions(filtered)
    else:
        review_explorer(filtered)


def sidebar_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title("Filters")
    service_relevant_only = st.sidebar.checkbox("BTS-service relevant only", value=True)

    scoped = df[df["service_relevant"]] if service_relevant_only else df
    sources = sorted(scoped["source_display"].dropna().unique().tolist())
    lines = sorted(scoped["bts_line_display"].dropna().unique().tolist())

    selected_sources = st.sidebar.multiselect("Source", sources, default=sources)
    selected_lines = st.sidebar.multiselect("BTS line", lines, default=lines)
    selected_sentiments = st.sidebar.multiselect(
        "Overall sentiment",
        SENTIMENT_ORDER,
        default=SENTIMENT_ORDER,
    )
    selected_aspects = st.sidebar.multiselect(
        "Service aspect",
        list(ASPECT_COLUMNS.keys()),
        default=[],
        placeholder="All aspects",
    )

    rating_range = st.sidebar.slider("Rating range", 1.0, 5.0, (1.0, 5.0), step=1.0)
    max_agreement = int(max(1, scoped["agreement_count"].max()))
    min_agreement = st.sidebar.slider(
        "Minimum agreement count",
        0,
        max_agreement,
        0,
        step=1,
    )

    dated = scoped["review_date_ui"].dropna()
    selected_date_range = None
    if not dated.empty:
        min_date = dated.min().date()
        max_date = dated.max().date()
        raw_date_range = st.sidebar.date_input(
            "Review date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if isinstance(raw_date_range, tuple) and len(raw_date_range) == 2:
            selected_date_range = (
                pd.Timestamp(raw_date_range[0]),
                pd.Timestamp(raw_date_range[1]),
            )
        elif isinstance(raw_date_range, date):
            selected_date_range = (pd.Timestamp(raw_date_range), pd.Timestamp(raw_date_range))
        st.sidebar.caption(
            "Date range filters charts, KPIs, and review tables. "
            "Rows without parsed dates are excluded from time-filtered views."
        )

    st.sidebar.selectbox(
        "Time aggregation",
        ["Monthly", "Quarterly", "Yearly"],
        index=0,
        key="time_grain",
    )

    return filter_dataset(
        df,
        service_relevant_only=service_relevant_only,
        sources=selected_sources,
        lines=selected_lines,
        sentiments=selected_sentiments,
        aspects=selected_aspects,
        ratings=rating_range,
        date_range=selected_date_range,
        min_agreement=min_agreement,
    )


def executive_overview(df: pd.DataFrame, filtered: pd.DataFrame) -> None:
    st.info(
        "`review_rating_num` is the sentiment-derived 1-5 star signal. "
        "`like_count` is stored separately as passenger agreement or engagement, "
        "so high-upvote complaints are not treated as positive reviews."
    )

    summary = kpi_summary(filtered, total_rows=len(df))
    columns = st.columns(5)
    with columns[0]:
        metric_card("Total reviews", f"{summary['total_reviews']:,.0f}", "Raw CSV rows")
    with columns[1]:
        metric_card("Filtered reviews", f"{summary['filtered_reviews']:,.0f}", "Current business scope")
    with columns[2]:
        metric_card("Average rating", f"{summary['average_rating']:.2f}", "Sentiment-derived stars")
    with columns[3]:
        metric_card("Negative share", f"{summary['negative_share']:.1%}", "Final_Label = Negative")
    with columns[4]:
        metric_card("Agreement count", f"{summary['total_agreement']:,.0f}", "Upvotes / helpful votes")

    st.subheader("Sentiment over time")
    trend_metric = st.radio(
        "Trend metric",
        ["Review count", "Sentiment share"],
        horizontal=True,
        key="overview_trend_metric",
    )
    trend = sentiment_time_series(filtered, time_frequency())
    st.altair_chart(sentiment_trend_chart(trend, trend_metric), width="stretch")

    left, right = st.columns([1.05, 1])
    with left:
        st.subheader("Overall sentiment")
        st.altair_chart(sentiment_bar(sentiment_distribution(filtered)), width="stretch")

    with right:
        st.subheader("Top service pain points")
        priority = aspect_priority(filtered).head(8)
        st.altair_chart(priority_bar(priority), width="stretch")

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Review source mix")
        st.altair_chart(source_bar(source_distribution(filtered)), width="stretch")
    with right:
        st.subheader("Model checkpoint")
        agreement, pairs = model_agreement(filtered)
        metric_card("LR vs DistilBERT agreement", f"{agreement:.2%}", "Agreement on current filtered rows")
        st.dataframe(pairs.head(8), width="stretch", hide_index=True)


def aspect_priority_dashboard(filtered: pd.DataFrame) -> None:
    priority = aspect_priority(filtered)
    heatmap = aspect_sentiment_matrix(filtered)

    left, right = st.columns([1.15, 1])
    with left:
        st.subheader("ABSA sentiment heatmap")
        st.altair_chart(aspect_heatmap(heatmap), width="stretch")
    with right:
        st.subheader("Priority ranking")
        display = priority.copy()
        display["Negative share"] = display["Negative share"].map(lambda value: f"{value:.1%}")
        display["Negative agreement"] = display["Negative agreement"].map(lambda value: f"{value:,.0f}")
        display["Priority score"] = display["Priority score"].map(lambda value: f"{value:,.1f}")
        st.dataframe(display, width="stretch", hide_index=True)

    selected_aspect = st.selectbox("Aspect drilldown", priority["Aspect"].tolist())
    row = priority[priority["Aspect"].eq(selected_aspect)].iloc[0]
    cols = st.columns(4)
    with cols[0]:
        metric_card("Mentions", f"{row['Mentions']:,.0f}", selected_aspect)
    with cols[1]:
        metric_card("Negative", f"{row['Negative']:,.0f}", "Aspect-level negative")
    with cols[2]:
        metric_card("Negative agreement", f"{row['Negative agreement']:,.0f}", "Engagement on complaints")
    with cols[3]:
        metric_card("Priority score", f"{row['Priority score']:,.1f}", "Negative + 0.1 x agreement")

    st.subheader("Highest-agreement evidence")
    st.dataframe(
        aspect_evidence_reviews(filtered, selected_aspect, limit=8),
        width="stretch",
        hide_index=True,
        column_config={"Review link": st.column_config.LinkColumn("Review link")},
    )

    st.subheader(f"{selected_aspect} sentiment over time")
    aspect_trend_metric = st.radio(
        "Aspect trend metric",
        ["Review count", "Sentiment share"],
        horizontal=True,
        key="aspect_trend_metric",
    )
    st.altair_chart(
        sentiment_trend_chart(
            aspect_sentiment_time_series(filtered, selected_aspect, time_frequency()),
            aspect_trend_metric,
        ),
        width="stretch",
    )


def rating_vs_agreement(filtered: pd.DataFrame) -> None:
    st.info(
        "A high agreement count means many people engaged with or agreed with the review. "
        "It is intentionally separate from the 1-5 sentiment rating."
    )

    scatter_df = scatter_sample(filtered)
    st.subheader("Rating and agreement are separate signals")
    st.altair_chart(rating_agreement_scatter(scatter_df), width="stretch")

    st.subheader("Sentiment trend in the selected period")
    st.altair_chart(
        sentiment_trend_chart(sentiment_time_series(filtered, time_frequency()), "Review count"),
        width="stretch",
    )

    threshold = st.slider(
        "High-agreement complaint threshold",
        min_value=0,
        max_value=int(max(1, filtered["agreement_count"].max())),
        value=20,
        step=1,
    )
    st.subheader("High-agreement, low-rating complaints")
    st.dataframe(
        high_agreement_low_rating(filtered, min_agreement=threshold, max_rating=2, limit=30),
        width="stretch",
        hide_index=True,
        column_config={"Review link": st.column_config.LinkColumn("Review link")},
    )


def operational_actions(filtered: pd.DataFrame) -> None:
    priority = aspect_priority(filtered).set_index("Aspect")
    tabs = st.tabs(ACTION_ASPECTS)

    for tab, aspect in zip(tabs, ACTION_ASPECTS):
        with tab:
            actions = ASPECT_ACTIONS[aspect]
            row = priority.loc[aspect]
            st.subheader(actions["goal"])
            cols = st.columns(4)
            with cols[0]:
                metric_card("Negative reviews", f"{row['Negative']:,.0f}", aspect)
            with cols[1]:
                metric_card("Positive reviews", f"{row['Positive']:,.0f}", aspect)
            with cols[2]:
                metric_card("Agreement weight", f"{row['Negative agreement']:,.0f}", "Negative examples")
            with cols[3]:
                metric_card("Priority score", f"{row['Priority score']:,.1f}", "Action ranking")

            left, right = st.columns([0.85, 1.15])
            with left:
                st.markdown("**Recommended business actions**")
                for action in actions["actions"]:
                    st.markdown(f"- {action}")
                st.markdown("**Success metrics to track**")
                for metric in actions["metrics"]:
                    st.markdown(f"- {metric}")
            with right:
                st.markdown("**Evidence reviews**")
                st.dataframe(
                    aspect_evidence_reviews(filtered, aspect, limit=6),
                    width="stretch",
                    hide_index=True,
                    column_config={"Review link": st.column_config.LinkColumn("Review link")},
                )


def review_explorer(filtered: pd.DataFrame) -> None:
    st.subheader("Review explorer")
    search_text = st.text_input("Search review text", placeholder="Example: Rabbit Card, crowded, elevator")
    limit = st.slider("Rows to show", 25, 500, 100, step=25)

    explorer_df = filter_dataset(
        filtered,
        service_relevant_only=False,
        search_text=search_text,
    ).sort_values(["agreement_count", "review_rating_num"], ascending=[False, True])

    st.caption(f"{len(explorer_df):,} reviews match the current explorer query.")
    table = review_table(explorer_df, limit=limit)
    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        column_config={"Review link": st.column_config.LinkColumn("Review link")},
    )

    if explorer_df.empty:
        return

    options = explorer_df.head(250).index.tolist()
    selected_index = st.selectbox(
        "Evidence card",
        options,
        format_func=lambda idx: evidence_option_label(explorer_df.loc[idx]),
    )
    evidence_card(explorer_df.loc[selected_index])


def metric_card(label: str, value: str, detail: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def sentiment_bar(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Sentiment:N", sort=SENTIMENT_ORDER),
            y=alt.Y("Reviews:Q"),
            color=sentiment_color(),
            tooltip=["Sentiment", "Reviews", alt.Tooltip("Share:Q", format=".1%")],
        )
        .properties(height=300)
    )


def priority_bar(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("Priority score:Q", title="Priority score"),
            y=alt.Y("Aspect:N", sort="-x", title=None),
            color=alt.value("#0F4C5C"),
            tooltip=[
                "Aspect",
                "Negative",
                alt.Tooltip("Negative agreement:Q", format=",.0f"),
                alt.Tooltip("Priority score:Q", format=",.1f"),
            ],
        )
        .properties(height=300)
    )


def source_bar(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
        .encode(
            x=alt.X("Reviews:Q"),
            y=alt.Y("Source:N", sort="-x", title=None),
            color=alt.value("#2A9D8F"),
            tooltip=["Source", "Reviews"],
        )
        .properties(height=320)
    )


def aspect_heatmap(data: pd.DataFrame) -> alt.Chart:
    base = (
        alt.Chart(data)
        .encode(
            x=alt.X("Sentiment:N", sort=SENTIMENT_ORDER),
            y=alt.Y("Aspect:N", sort="-color", title=None),
            color=alt.Color("Reviews:Q", scale=alt.Scale(scheme="tealblues")),
            tooltip=["Aspect", "Sentiment", "Reviews"],
        )
        .properties(height=420)
    )
    return base.mark_rect() + base.mark_text(color="#101820").encode(text="Reviews:Q")


def rating_agreement_scatter(data: pd.DataFrame) -> alt.Chart:
    return (
        alt.Chart(data)
        .mark_circle(size=62, opacity=0.55)
        .encode(
            x=alt.X("review_rating_num:Q", title="Sentiment-derived rating", scale=alt.Scale(domain=[0.7, 5.3])),
            y=alt.Y("agreement_count:Q", title="Agreement count", scale=alt.Scale(type="sqrt")),
            color=sentiment_color("Final_Label"),
            tooltip=[
                alt.Tooltip("review_title_display:N", title="Title"),
                alt.Tooltip("source_display:N", title="Source"),
                alt.Tooltip("review_rating_num:Q", title="Rating"),
                alt.Tooltip("agreement_count:Q", title="Agreement", format=",.0f"),
                alt.Tooltip("primary_aspect:N", title="Aspect"),
                alt.Tooltip("Final_Label:N", title="Sentiment"),
            ],
        )
        .properties(height=430)
    )


def sentiment_trend_chart(data: pd.DataFrame, metric: str) -> alt.Chart:
    if data.empty:
        return (
            alt.Chart(pd.DataFrame({"Message": ["No dated reviews in the selected filter."]}))
            .mark_text(size=16, color="#5D6673")
            .encode(text="Message:N")
            .properties(height=320)
        )

    value_field = "Share" if metric == "Sentiment share" else "Reviews"
    y_axis = alt.Y(
        f"{value_field}:Q",
        title="Sentiment share" if value_field == "Share" else "Reviews",
        axis=alt.Axis(format=".0%" if value_field == "Share" else ","),
    )
    base = (
        alt.Chart(data)
        .encode(
            x=alt.X("Period:T", title="Period"),
            y=y_axis,
            color=sentiment_color(),
            tooltip=[
                alt.Tooltip("Period:T", title="Period", format="%Y-%m"),
                "Sentiment",
                alt.Tooltip("Reviews:Q", format=","),
                alt.Tooltip("Share:Q", format=".1%"),
            ],
        )
        .properties(height=330)
    )
    return base.mark_line(point=False, strokeWidth=3) + base.mark_circle(size=54)


def time_frequency() -> str:
    return {
        "Monthly": "M",
        "Quarterly": "Q",
        "Yearly": "Y",
    }.get(st.session_state.get("time_grain", "Monthly"), "M")


def sentiment_color(field: str = "Sentiment") -> alt.Color:
    return alt.Color(
        f"{field}:N",
        scale=alt.Scale(
            domain=list(SENTIMENT_COLORS.keys()),
            range=list(SENTIMENT_COLORS.values()),
        ),
        legend=alt.Legend(title="Sentiment"),
    )


def scatter_sample(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) <= 6000:
        return df
    high_agreement = df[df["agreement_count"].gt(0)]
    remaining = df[df["agreement_count"].le(0)]
    sample_size = max(0, 6000 - len(high_agreement))
    sampled_remaining = remaining.sample(min(sample_size, len(remaining)), random_state=7)
    return pd.concat([high_agreement, sampled_remaining], ignore_index=True)


def evidence_option_label(row: pd.Series) -> str:
    return (
        f"{row['source_display']} | {row['Final_Label']} | "
        f"{row['review_rating_num']:.0f} stars | {row['text_snippet'][:70]}"
    )


def evidence_card(row: pd.Series) -> None:
    link = row.get("review_link", "")
    link_html = f'<a href="{link}" target="_blank">Open original review</a>' if link else ""
    st.markdown(
        f"""
        <div class="evidence-card">
            <div class="evidence-title">{row['review_title_display']}</div>
            <div class="evidence-meta">
                {row['source_display']} | {row['Final_Label']} | Rating {row['review_rating_num']:.0f}
                | Agreement {row['agreement_count']:,.0f} | {row['primary_aspect']}
            </div>
            <p>{row['text_snippet']}</p>
            {link_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def inject_css() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.35rem;
            padding-bottom: 2.5rem;
        }
        .app-header {
            align-items: center;
            border-bottom: 1px solid #D8DEE4;
            display: flex;
            justify-content: space-between;
            margin-bottom: 1.2rem;
            padding-bottom: 0.85rem;
        }
        .app-header h1 {
            color: #101820;
            font-size: 2rem;
            font-weight: 750;
            letter-spacing: 0;
            margin: 0;
        }
        .app-header p {
            color: #5D6673;
            font-size: 0.98rem;
            margin: 0.25rem 0 0;
        }
        .header-pill {
            background: #E8F3F1;
            border: 1px solid #BBDCD6;
            border-radius: 999px;
            color: #0F4C5C;
            font-size: 0.82rem;
            font-weight: 650;
            padding: 0.45rem 0.75rem;
            white-space: nowrap;
        }
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #D8DEE4;
            border-radius: 8px;
            box-shadow: 0 1px 2px rgba(16, 24, 32, 0.06);
            min-height: 112px;
            padding: 0.85rem 0.9rem;
        }
        .metric-label {
            color: #5D6673;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .metric-value {
            color: #101820;
            font-size: 1.8rem;
            font-weight: 760;
            line-height: 1.2;
            margin-top: 0.2rem;
        }
        .metric-detail {
            color: #697586;
            font-size: 0.82rem;
            line-height: 1.3;
            margin-top: 0.25rem;
        }
        .evidence-card {
            background: #FFFFFF;
            border: 1px solid #D8DEE4;
            border-radius: 8px;
            margin-top: 0.75rem;
            padding: 1rem;
        }
        .evidence-title {
            color: #101820;
            font-size: 1.05rem;
            font-weight: 750;
            margin-bottom: 0.3rem;
        }
        .evidence-meta {
            color: #5D6673;
            font-size: 0.86rem;
            font-weight: 650;
            margin-bottom: 0.5rem;
        }
        div[data-testid="stMetric"] {
            background: #FFFFFF;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
