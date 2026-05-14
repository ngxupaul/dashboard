# GUIDE.md - Codex Build Guide for BTS Skytrain ABSA Business Dashboard

## Mission

Build and improve a business analytics dashboard from:

- `full_dataset_with_predictions.csv`

The dashboard must use aspect-based sentiment analysis (ABSA) results to explain BTS Skytrain passenger feedback in business language. It must not stop at charts. It must turn the model output into measurable insight, time-based analysis, evidence, and practical business recommendations.

Final goal:

> An AI-powered business decision support dashboard that helps BTS Skytrain stakeholders understand what passengers like, what passengers complain about, which service aspects are worsening or improving, and which operational actions should be prioritized.

## Current Project Context

This repository already contains a static dashboard pipeline:

- `dashboard_data.py` - data loading, cleaning, filtering, sentiment aggregation, aspect metrics.
- `build_static_site.py` - generates the static dashboard into `docs/index.html`.
- `verify_dashboard.py` - validates the data contract and dashboard assumptions.
- `docs/analysis_explanation.md` - explanation of analysis logic.
- `docs/dashboard_observation_guide.md` - guide for reading each chart/table.
- `docs/index.html` - generated static dashboard.

Prefer extending this existing pipeline instead of replacing it with a new framework unless explicitly requested.

## Required Working Skills

When working on this dashboard, Codex should apply these analysis and implementation skills:

- Data profiling: inspect column names, missing values, date coverage, sentiment labels, aspect columns, and source distribution before changing logic.
- Pandas data engineering: use structured dataframe operations for cleaning, grouping, filtering, time aggregation, ranking, and evidence extraction.
- Time-series analysis: support daily, weekly, monthly, and quarterly views when feasible; detect spikes, changes, and recent movement.
- Business intelligence storytelling: every major chart/table needs a short interpretation that explains business meaning, not only the numeric result.
- ABSA interpretation: distinguish global review sentiment from aspect-level sentiment.
- Dashboard UX: keep the interface dense, readable, and decision-focused; prioritize filters, KPI cards, trend charts, ranking tables, evidence snippets, and recommendation blocks.
- Verification: run existing checks and add focused checks when changing data contracts or aggregation logic.

Do not invent model outputs or business conclusions that cannot be traced to the CSV.

## Dataset Contract

Primary file:

```text
full_dataset_with_predictions.csv
```

Known raw shape:

- 24,459 rows.
- 54 raw columns.

Important columns:

```text
entity_name
entity_id
bts_line
category
review_id
review_title
review_text
review_rating
published_date
created_at_date
trip_type
stay_date
review_language
is_translated
original_language
like_count
images_count
reviewer_id
reviewer_name
reviewer_username
reviewer_contribution_count
reviewer_hometown
reviewer_profile_link
has_owner_response
owner_response_text
owner_response_date
review_link
entity_link
source
relevant
overall_sentiment
primary_aspect
aspects_detected
aspect_count
sentiment_staff
sentiment_punctuality
sentiment_crowding
sentiment_cleanliness
sentiment_fare_payment
sentiment_safety
sentiment_route_connectivity
sentiment_signage
sentiment_infrastructure
sentiment_overall
review_length
word_count
review_rating_num
review_date
review_month
full_text
clean_text
LogisticRegression_Label
DistilBERT_Label
Final_Label
```

## Critical Data Rules

Use these rules consistently:

1. `Final_Label` is the global sentiment of the full review.
2. `sentiment_*` columns are aspect-level sentiment fields.
3. `sentiment_overall` is an ABSA aspect named "Overall Experience". It is not the same as `Final_Label`.
4. `review_rating_num` is the 1-5 rating signal.
5. `like_count` must be treated as agreement/engagement evidence, not as a star rating.
6. In processed data, preserve `like_count` separately as `agreement_count`.
7. Default analysis should focus on BTS-service-relevant reviews, using the existing relevance logic in `dashboard_data.py`.
8. Do not use broad/off-topic rows as the default business scope.
9. Do not use generic restaurant/e-commerce aspects from the old guide. Use the actual BTS service aspects below.

## BTS Aspect Mapping

Use these dashboard labels and CSV columns:

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

## Dashboard Structure

The dashboard should provide these sections or tabs.

### 1. Executive Overview

Purpose:

Give a high-level business snapshot.

Required elements:

- Total reviews in raw dataset.
- Total service-relevant reviews used for default analysis.
- Positive, neutral, and negative rates from `Final_Label`.
- Top positive aspect.
- Highest-risk aspect.
- Customer satisfaction index or equivalent score.
- Model agreement summary between `LogisticRegression_Label` and `DistilBERT_Label`.

Recommended charts:

- Global sentiment distribution.
- Review volume over time.
- Monthly sentiment trend.
- Top positive aspects.
- Top negative/risk aspects.

Required interpretation:

- Explain what the numbers mean for BTS operations.
- Identify whether sentiment is improving, stable, or worsening.
- Identify which aspect is the main business risk.

### 2. Aspect-Based Sentiment Analysis

Purpose:

Explain passenger sentiment for every BTS service aspect.

Required elements:

- Aspect sentiment distribution.
- Negative share by aspect.
- Positive share by aspect.
- Mention count by aspect.
- Agreement-weighted negative complaints.
- Priority/risk ranking table.

Recommended visuals:

- Stacked bar chart: Negative / Neutral / Positive by aspect.
- Heatmap or compact matrix: aspect vs sentiment intensity.
- Ranking table: Aspect, mentions, positive %, negative %, agreement weight, priority score, risk level.

Interpretation examples:

- "Crowding & Comfort is a high-priority operational issue because it combines high complaint volume with strong passenger agreement."
- "Fare & Payment complaints indicate friction in pricing perception, Rabbit Card top-up, ticketing, or payment experience."

### 3. Time-Based Analysis

Purpose:

Track how sentiment and aspect complaints change over time.

Required time controls:

- Daily when data density supports it.
- Weekly.
- Monthly.
- Quarterly.

Required charts:

- Overall sentiment trend using `Final_Label`.
- Review count trend.
- Aspect-specific sentiment trend for selected `sentiment_*` columns.
- Negative sentiment trend for priority aspects.

Required insight logic:

- Detect negative sentiment spikes.
- Compare recent period vs previous period.
- Explain which aspect contributed most to worsening sentiment.
- Explain which aspect improved.

Example interpretation:

- "Negative sentiment rose in the recent period, mainly driven by crowding and fare/payment complaints."
- "Positive sentiment improved for cleanliness, suggesting recent facility or maintenance perception may be stronger."

### 4. Root Cause and Business Intelligence

Purpose:

Translate sentiment patterns into operational causes.

Required elements:

- Root cause matrix:
  - Problem.
  - Related aspect.
  - Frequency.
  - Negative share.
  - Agreement evidence.
  - Severity.
- Correlation or relationship analysis when the available data supports it:
  - Rating vs global sentiment.
  - Review source vs sentiment.
  - BTS line vs sentiment.
  - Aspect count vs negative sentiment.
  - Agreement count vs complaint priority.

Suggested root cause themes:

- Peak-hour crowding.
- Ticketing or Rabbit Card friction.
- Fare/value dissatisfaction.
- Infrastructure/facility problems.
- Route transfer or connectivity confusion.
- Staff/service inconsistency.
- Safety/security concerns.

Do not claim causal certainty. Use language such as "suggests", "is associated with", or "may indicate" unless a controlled causal analysis exists.

### 5. Recommendation and Resolution Center

Purpose:

Provide actionable recommendations, not only problem lists.

Every recommendation block must include:

- Problem.
- Evidence.
- Business impact.
- Recommendation.
- Priority.
- Success metric.

Evidence should use measured values:

- Negative reviews.
- Negative share.
- Mention volume.
- Agreement-weighted complaint count.
- Recent trend movement.
- Representative review snippets.

Priority rules:

- Critical: high negative share, high volume, and high agreement weight.
- High: high volume or strong recent worsening.
- Medium: moderate volume with clear operational signal.
- Low: low volume or unclear evidence.

Recommended priority aspects:

- Crowding & Comfort.
- Fare & Payment System.
- Infrastructure & Facilities.
- Route Coverage & Connectivity.

### 6. Business Suggestion Tab

This section must exist as a dedicated executive-facing section.

Purpose:

Provide strategic recommendations for business decision makers. This is not a technical model-analysis section.

Required structure:

Section A - Key Business Risks:

- List top operational risks with numeric evidence.
- Include the aspect, negative share, complaint volume, and agreement evidence.

Section B - Strategic Opportunities:

- Identify aspects with high positive sentiment.
- Explain how BTS can leverage these strengths in service communication or operations.

Section C - Executive Recommendations:

Each recommendation must include:

1. Evidence.
2. Interpretation.
3. Business conclusion.
4. Suggested action.
5. Success metric.

Example:

Evidence:

- Crowding & Comfort has high negative volume and strong agreement-weighted complaints.

Interpretation:

- Passenger dissatisfaction is concentrated around crowded or uncomfortable travel conditions.

Business conclusion:

- Perceived service quality may weaken during high-demand periods even when core transport access remains useful.

Suggested action:

- Add peak-hour passenger-flow management, platform guidance, and station-level crowding communication.

Success metric:

- Reduce negative crowding share and agreement-weighted crowding complaints in the next measured period.

### 7. Review Explorer

Purpose:

Allow users to inspect raw evidence behind the dashboard.

Required filters:

- Sentiment.
- Aspect.
- Date range.
- BTS line.
- Source.
- Rating range.
- Minimum agreement count.
- Text search.

Required columns:

- Date.
- Source.
- BTS line.
- Rating.
- Agreement count.
- Global sentiment.
- Primary aspect.
- Review title.
- Review snippet.
- Review link when available.

Recommended features:

- Highlight high-agreement complaints.
- Show representative positive and negative examples.
- Avoid exposing unnecessary reviewer personal details unless needed.

## Business Interpretation Requirements

Every major chart or table should include a short explanation in business language.

Good explanation:

- States the finding.
- Gives the numeric evidence.
- Explains business meaning.
- Suggests the next action or why it matters.

Weak explanation:

- Only repeats the chart title.
- Only says "this chart shows sentiment distribution".
- Makes unsupported claims without numbers.

## Suggested Analytics Features

Add these if they can be implemented cleanly:

- Time granularity selector: day, week, month, quarter.
- Recent vs previous period comparison.
- Negative spike detection.
- Aspect risk score.
- Agreement-weighted complaint ranking.
- Source breakdown.
- BTS line breakdown.
- Representative review extraction.
- Keyword extraction for top negative and positive terms.
- Model agreement and disagreement section.
- Data quality summary.

## Static Dashboard Requirements

If maintaining the current static HTML approach:

1. Use `build_static_site.py` to generate `docs/index.html`.
2. Keep calculations in `dashboard_data.py` where possible.
3. Keep generated HTML deterministic.
4. Avoid hardcoding metrics that can be computed from CSV.
5. Keep dashboard usable from GitHub Pages without a Python server.
6. Use CDN visualization libraries only when acceptable for static deployment.

## Streamlit Requirements

If maintaining or extending Streamlit:

1. Use `app.py`.
2. Cache expensive CSV loading and aggregation.
3. Keep filters synchronized across tabs.
4. Keep text explanations next to charts.
5. Do not require manual data preprocessing outside the app.

## Verification Checklist

Before finishing dashboard work:

Run:

```powershell
python verify_dashboard.py
```

If `docs/index.html` is generated:

```powershell
python build_static_site.py
```

Check:

- CSV loads with expected columns.
- `Final_Label` drives global sentiment.
- `sentiment_*` columns drive aspect sentiment.
- `sentiment_overall` is handled as an aspect, not global sentiment.
- `review_rating_num` remains a 1-5 rating.
- `like_count` remains agreement evidence.
- Date filters update KPIs, charts, and tables.
- Default scope filters to BTS-service-relevant reviews.
- Recommendation evidence matches computed numbers.
- No chart is left without interpretation.

## Acceptance Criteria

The final dashboard is acceptable when it answers these questions clearly:

- What is the overall passenger sentiment?
- Which BTS service aspect creates the biggest business risk?
- Which aspects are strongest?
- How is sentiment changing over time?
- Which negative spikes or recent changes require attention?
- What evidence supports each recommendation?
- What specific operational actions should BTS prioritize?
- Which raw reviews support the conclusions?

## Development Notes for Codex

- Start by reading `dashboard_data.py`, `build_static_site.py`, `verify_dashboard.py`, and the CSV header.
- Preserve user changes in the worktree.
- Prefer small, focused edits.
- Add or update tests/checks when changing data semantics.
- Keep documentation aligned with the implemented dashboard.
- Use clear business wording in generated explanations.
- Avoid generic ABSA wording that does not mention BTS, passenger service, stations, routes, fare/payment, crowding, or facilities.
