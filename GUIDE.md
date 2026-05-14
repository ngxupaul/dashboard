# GUIDE.md - AI Business Sentiment Dashboard Specification

## Mission

Build a BTS Skytrain business sentiment dashboard from:

```text
full_dataset_with_predictions.csv
```

The dashboard must behave like an AI-powered business decision support system. It should not only visualize sentiment. It must detect operational problems, explain time-based movement, identify Negative Sentiment Spikes (NSS), and generate dynamic business suggestions backed by data.

## Current Repository

Use the existing static dashboard pipeline unless the user explicitly asks for another framework:

- `dashboard_data.py` - data loading, cleaning, filtering, aggregation, ABSA metrics.
- `build_static_site.py` - generates `docs/index.html`.
- `verify_dashboard.py` - verifies the data contract.
- `docs/index.html` - deployed GitHub Pages dashboard.

## Dataset Contract

Actual data file:

```text
full_dataset_with_predictions.csv
```

Important rules:

1. `Final_Label` is the global review sentiment.
2. `sentiment_*` columns are aspect-level sentiment fields.
3. `sentiment_overall` is the ABSA aspect "Overall Experience", not global sentiment.
4. `review_rating_num` is the 1-5 rating signal.
5. `like_count` is agreement/engagement evidence, not a star rating.
6. Default analysis should use BTS-service-relevant reviews.

## BTS Aspect Mapping

| Business Aspect | CSV Column |
| --- | --- |
| Staff & Customer Service | `sentiment_staff` |
| Punctuality & Reliability | `sentiment_punctuality` |
| Crowding & Comfort | `sentiment_crowding` |
| Cleanliness & Hygiene | `sentiment_cleanliness` |
| Fare & Payment System | `sentiment_fare_payment` |
| Safety & Security | `sentiment_safety` |
| Route Coverage & Connectivity | `sentiment_route_connectivity` |
| Signage & Navigation | `sentiment_signage` |
| Infrastructure & Facilities | `sentiment_infrastructure` |
| Overall Experience | `sentiment_overall` |

## Required Skills

Codex should apply:

- Data profiling.
- Pandas aggregation.
- Aspect-based sentiment analysis.
- Negative Sentiment Spike detection.
- Daily, weekly, monthly, and quarterly time-series analysis.
- Root cause and risk scoring.
- Dynamic recommendation generation from time-based evidence.
- Business-language explanation for every major chart.

## Dashboard Structure

The UI must contain only 4 main tabs.

## Tab 1 - Overview & Data Insight

Purpose:

Provide a complete overview of passenger sentiment, business health, aspect performance, and raw evidence.

Required KPI cards:

- Total Reviews.
- Positive Sentiment %.
- Negative Sentiment %.
- Most Mentioned Aspect.
- Worst Performing Aspect.
- Customer Satisfaction Index.

Required charts and tables:

- Sentiment Distribution.
- Aspect Distribution.
- Review Volume Timeline.
- Top Positive Aspects.
- Top Negative Aspects.
- Aspect Sentiment Heatmap or stacked sentiment matrix.
- Aspect ranking table.
- Review Explorer.

Required interpretation:

- Every chart must include text explaining business meaning.
- Explain whether the system is healthy, which aspect is risky, and which aspect is strongest.

Review Explorer requirements:

- Search review text.
- Filter by aspect.
- Filter by sentiment.
- Filter by date when supported.
- Filter by BTS line/source as business proxies.
- Show date, source, BTS line, rating, agreement count, sentiment, primary aspect, and review snippet.

## Tab 2 - NSS (Negative Sentiment Spike)

Purpose:

Detect sudden increases in negative sentiment and identify business causes.

Required NSS features:

- Spike detection.
- Aspect contribution analysis.
- Time-window comparison.
- Risk severity scoring.
- Operational incident detection.

Required NSS metrics:

- Negative growth.
- Spike intensity.
- Frequency increase.
- Aspect contribution.
- Weekly/monthly comparison.

Required charts and tables:

- Negative Sentiment Timeline.
- Spike Detection Timeline.
- Aspect Spike/Change table.
- Negative Trend Comparison.
- Root Cause Matrix.
- Source and BTS-line breakdown.
- Complaint keyword table.

Required risk classification:

- Critical.
- High.
- Medium.
- Low.

Required interpretation:

- Explain when the spike happened.
- Explain which aspects contributed.
- Avoid causal certainty; use "suggests", "indicates", or "may reflect".

## Tab 3 - Time-Based Analysis

Purpose:

Track passenger sentiment evolution over time.

Required controls:

- Daily trend.
- Weekly trend.
- Monthly trend.
- Quarterly trend.

Required analysis:

- Positive trend evolution.
- Negative trend evolution.
- Review frequency trend.
- Aspect trend movement.
- Seasonal patterns where the data supports them.
- Recurring operational issues.
- Unstable periods.
- Recovery trends.
- Performance improvements.

Required charts:

- Sentiment Trend Timeline.
- Aspect Trend Comparison.
- Review Frequency Timeline.
- Time-based sentiment movement.

Required interpretation:

- Explain recent movement against the previous comparable period.
- Identify the selected aspect's current direction: worsening, improving, or stable.

## Tab 4 - Business Suggestion & Resolution Center

Purpose:

Generate actionable business recommendations using time-based evidence.

Important rule:

Suggestions must be dynamic and data-driven. They cannot be static. Each suggestion must use NSS data, aspect trends, time-based movement, and operational sentiment changes.

Each suggestion must contain:

1. Problem.
2. Evidence.
3. Interpretation.
4. Business Conclusion.
5. Suggested Action.
6. Priority.

Required resolution features:

- Root cause analysis.
- Priority classification.
- Suggested operational fixes.
- Business opportunity detection.
- Strategic recommendation generation.

Required business intelligence answers:

- Why customers are unhappy.
- Which aspect creates the biggest risk.
- When problems occur.
- Why negative spikes happen.
- Which operations are unstable.
- What business action should be prioritized.

## Chart Explanation Documentation

The project must include documentation for visualizations. For each major chart, document:

1. Chart name.
2. Purpose.
3. Data source.
4. Business meaning.
5. How to interpret.
6. Example insight.
7. Recommended action.

## Verification

Before finishing:

```powershell
python build_static_site.py
python verify_dashboard.py
```

Also check generated `docs/index.html` for JavaScript syntax when Node is available.

## Acceptance Criteria

The dashboard is acceptable when:

- UI has exactly 4 main tabs.
- Suggestions are based on time-based evidence, not static text.
- NSS appears as a dedicated tab.
- Time-based analysis supports daily, weekly, monthly, and quarterly views.
- Overview includes data insight and review exploration.
- Business Suggestion tab includes evidence, interpretation, conclusion, action, and priority.
