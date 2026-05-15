# GUIDE.md - Sentiment Analysis & Time-Based Business Insights Dashboard

## 1. Dashboard Objective

Build a BTS Skytrain business sentiment dashboard from:

```text
full_dataset_with_predictions.csv
```

The dashboard analyzes customer reviews that have already been sentiment-labeled as Positive, Neutral, or Negative. It must behave like an AI-powered business decision support system, not only a visualization page.

The dashboard must:

- Measure overall customer satisfaction using Net Sentiment Score.
- Monitor sentiment fluctuations over time.
- Identify which aspects, services, and operating areas create positive or negative experiences.
- Extract the reasons behind customer praise and complaints.
- Generate time-based actionable business recommendations.
- Support strategic decision-making through interactive visual analytics.

## 2. Current Repository

Use the existing static dashboard pipeline unless the user explicitly asks for another framework:

- `dashboard_data.py` - data loading, cleaning, filtering, aggregation, and aspect-based sentiment metrics.
- `build_static_site.py` - generates `docs/index.html`.
- `verify_dashboard.py` - verifies the data contract.
- `docs/index.html` - deployed GitHub Pages dashboard.

## 3. Dataset Contract

Actual data file:

```text
full_dataset_with_predictions.csv
```

Important rules:

1. `Final_Label` is the global review sentiment.
2. `sentiment_*` columns are aspect-level sentiment fields.
3. `sentiment_overall` is the ABSA aspect "Overall Experience", not global sentiment.
4. `review_rating_num` is the 1-5 rating signal.
5. `like_count` is agreement or engagement evidence, not a star rating.
6. Default analysis should use BTS-service-relevant reviews.

## 4. BTS Aspect Mapping

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

## 5. Recommended Dashboard Structure

The dashboard must be divided into exactly 4 main tabs to keep the interface clean, professional, and easy to navigate.

## TAB 1 - Executive Overview

### Purpose

Provide a high-level summary of customer sentiment performance and business health.

### Main KPIs

Display:

- Total Reviews.
- Total Positive Reviews.
- Total Neutral Reviews.
- Total Negative Reviews.
- Positive Rate.
- Negative Rate.
- Net Sentiment Score.
- Most Mentioned Aspect.
- Worst Performing Aspect.

### Net Sentiment Score

Formula:

```text
Net Sentiment Score = ((Positive Reviews - Negative Reviews) / Total Reviews) * 100
```

Interpretation:

| Net Sentiment Score | Interpretation |
| --- | --- |
| > 50 | Excellent customer satisfaction |
| 20 to 50 | Good |
| 0 to 20 | Neutral |
| < 0 | Negative customer experience |

### Visualizations

Required charts:

- Sentiment Distribution Pie Chart.
- Net Sentiment Score KPI Card.
- Monthly or Weekly Net Sentiment Score Trend Line.
- Review Volume Trend.
- Aspect Distribution.
- Aspect Sentiment Heatmap or stacked sentiment matrix.
- Aspect Ranking Table.

### Filters

Required filters:

- Date Range.
- BTS Line, source, product, branch, or service proxy.
- Aspect.
- Sentiment.

### Interpretation Requirements

Every chart must include business-language explanation:

- What the chart shows.
- Whether the system is healthy.
- Which aspect is strongest.
- Which aspect creates risk.
- What action the business should consider.

### Review Explorer

The overview must include a review explorer with:

- Search review text.
- Filter by aspect.
- Filter by sentiment.
- Filter by date when supported.
- Filter by BTS line or source as business proxies.
- Show date, source, BTS line, rating, agreement count, sentiment, primary aspect, and review snippet.

## TAB 2 - Time-Based Trend Analysis

### Purpose

Analyze how customer sentiment changes over time. This tab is the core analytical section of the dashboard.

### Required Time Controls

Support:

- Daily trend.
- Weekly trend.
- Monthly trend.
- Quarterly trend.

### 1. Net Sentiment Score Trend Over Time

Visual:

- Interactive Line Chart.

Metrics:

- Daily Net Sentiment Score.
- Weekly Net Sentiment Score.
- Monthly Net Sentiment Score.
- Quarterly Net Sentiment Score.

Insights to display:

- Peak positive periods.
- Sudden negative drops.
- Seasonal patterns where the data supports them.
- Recovery periods after service improvements.
- Recent movement against the previous comparable period.

### 2. Sentiment Volume Trend

Visual:

- Stacked Area Chart.
- Positive vs Negative over time.

Purpose:

- Identify periods with high complaint volume.
- Detect business incidents or operational problems.
- Track review frequency changes.

### 3. Aspect-Based Trend Analysis

Users must be able to select BTS-service-relevant aspects, including:

- Staff & Customer Service.
- Punctuality & Reliability.
- Crowding & Comfort.
- Cleanliness & Hygiene.
- Fare & Payment System.
- Safety & Security.
- Route Coverage & Connectivity.
- Signage & Navigation.
- Infrastructure & Facilities.
- Overall Experience.

Visual:

- Multi-line trend chart by aspect.

Example insights:

- Negative sentiment related to punctuality increased significantly during a selected month.
- Cleanliness sentiment improved after a later period.
- Crowding sentiment may reflect recurring peak-hour pressure.

### 4. Negative Spike Detection

The time-based tab must also detect sharp negative movement.

Required spike analysis:

- Negative sentiment spike detection.
- Aspect contribution analysis.
- Time-window comparison.
- Risk severity scoring.
- Operational incident detection.

Required metrics:

- Negative growth.
- Spike intensity.
- Frequency increase.
- Aspect contribution.
- Weekly, monthly, and quarterly comparison.

Required risk classification:

- Critical.
- High.
- Medium.
- Low.

Interpretation rules:

- Explain when the spike happened.
- Explain which aspects contributed.
- Avoid causal certainty. Use "suggests", "indicates", or "may reflect".

### 5. Time-Based Recommendation Engine

This section must dynamically generate recommendations based on selected time periods.

Logic example:

```text
IF:
- Net Sentiment Score decreases sharply
- Negative reviews for an aspect increase
- Complaint frequency spikes

THEN:
- Generate a recommendation focused on that operational area
```

## TAB 3 - Aspect & Root Cause Analysis

### Purpose

Identify why customers feel positive or negative.

### 1. Aspect Sentiment Distribution

Visualizations:

- Horizontal Bar Chart.
- Heatmap.
- Stacked sentiment matrix.

Metrics:

- Positive percentage.
- Neutral percentage.
- Negative percentage.
- Net Sentiment Score per aspect.

### 2. Positive vs Negative Word Clouds

Positive Word Cloud focus:

- Common praise keywords.
- Positive service themes.
- Strengths that should be maintained.

Negative Word Cloud focus:

- Complaint keywords.
- Recurring pain points.
- Operational risk language.

### 3. Topic Modeling Section

This section is optional advanced analysis.

Recommended methods:

- LDA.
- BERTopic.

Purpose:

- Automatically discover hidden complaint topics.
- Group recurring business issues.
- Support root cause discovery.

Example topics:

| Topic | Common Keywords |
| --- | --- |
| Delay or Reliability | late, waiting, schedule |
| Poor Service | rude, support, response |
| Crowding or Comfort | crowded, packed, uncomfortable |
| Facilities | broken, escalator, station |

### 4. Aspect Performance Ranking

Visual:

- Ranked Bar Chart.

Display:

- Best-performing aspects.
- Worst-performing aspects.
- Aspect Net Sentiment Score ranking.
- Aspect review volume.

### 5. Drill-Down Analysis

Users should be able to:

- Click an aspect.
- View related reviews.
- View keyword patterns.
- View sentiment trend history.
- Compare aspect behavior across selected periods.

## TAB 4 - Strategic Recommendation Center

### Purpose

Convert sentiment findings into business actions. This tab should feel like an executive decision-support system.

Recommendations must be dynamic and data-driven. They cannot be static. Each recommendation must update according to:

- Selected period.
- Aspect trends.
- Net Sentiment Score fluctuations.
- Negative spike detection.
- Operational sentiment changes.

### Recommendation Framework

Each recommendation must contain:

| Field | Description |
| --- | --- |
| Time Period | Selected analysis range |
| Aspect | Related business area |
| Problem | Detected issue |
| Evidence | Supporting data |
| Interpretation | Business meaning of the evidence |
| Business Conclusion | Decision-oriented conclusion |
| Strategic Action | Suggested improvement |
| Priority | High, Medium, or Low |
| Expected Impact | Expected business outcome |

### Example Recommendation 1

Problem:

Negative sentiment for punctuality increased during the selected period.

Evidence:

- Punctuality-related negative sentiment increased by 35%.
- Complaint frequency spiked compared with the previous comparable period.
- Related keywords include delay, waiting, and late.

Interpretation:

The selected period suggests reliability pressure or passenger frustration with service timing.

Business Conclusion:

Punctuality is likely the highest operational risk during this period.

Strategic Action:

Investigate timetable adherence, delay communication, and crowd management during the affected dates.

Priority:

High.

### Example Recommendation 2

Problem:

Positive sentiment for staff service increased after a later period.

Evidence:

- Staff sentiment improved compared with the previous period.
- Positive staff-related reviews increased.
- Complaint frequency decreased.

Interpretation:

The data may reflect improved frontline service quality or better passenger support.

Business Conclusion:

Service training and staff communication should be maintained and standardized.

Strategic Action:

Continue staff training and track whether the improvement remains stable over the next period.

Priority:

Medium.

### Example Recommendation 3

Problem:

Fare or payment complaints spike during selected periods.

Evidence:

- Negative fare and payment sentiment increased.
- Reviews mention cost, payment, card, or ticketing issues.
- The spike coincides with higher complaint volume.

Interpretation:

The data suggests pricing clarity or payment process friction.

Business Conclusion:

Payment experience may be reducing customer satisfaction even when core transport service is stable.

Strategic Action:

Review fare communication, payment instructions, and ticketing support.

Priority:

Medium.

## 6. Suggested Dashboard Layout

### Top Section

- KPI Cards.
- Net Sentiment Score.
- Total Reviews.
- Positive Rate.
- Negative Rate.

### Middle Section

- Time Trend Charts.
- Aspect Trend Analysis.
- Volume Analysis.
- Negative Spike Analysis.

### Bottom Section

- Recommendation Cards.
- Root Cause Insights.
- Word Clouds.
- Review Explorer.

## 7. UI Design Skill

The dashboard must look like a real business intelligence product, not a generic AI-generated GUI. The visual design should feel polished, credible, and useful for repeated analysis.

### Design Direction

- Build a professional analytics interface for business users.
- Prioritize dense but readable information over decorative empty space.
- Use a calm, modern dashboard style with clear hierarchy.
- Make the BTS and transport-service context visible through labels, aspect names, and operational language.
- Avoid generic "AI dashboard" styling such as random glowing gradients, oversized hero banners, floating blobs, fake futuristic panels, or decorative glass cards.

### Layout Rules

- Keep the 4-tab navigation clean and obvious.
- Put filters in a consistent control bar near the top of each tab.
- Use KPI cards only for important numbers, not every small metric.
- Group related charts into full-width sections with clear headings.
- Use tables for evidence and review drill-downs because business users need scanable detail.
- Avoid card-inside-card layouts.
- Keep chart explanations close to the chart they explain.

### Visual Style

- Use a restrained palette with neutral backgrounds, strong text contrast, and limited accent colors.
- Use sentiment colors consistently:
  - Positive: green.
  - Neutral: gray or blue-gray.
  - Negative: red or orange-red.
  - Warning or risk: amber.
- Do not make the whole dashboard one color theme.
- Avoid overusing purple, blue-purple gradients, beige-only palettes, and dark slate-only themes.
- Use subtle borders and shadows only when they improve separation.
- Keep border radius modest.

### Typography

- Use readable font sizes suitable for dashboard scanning.
- Use compact headings inside cards and chart panels.
- Reserve large text for page-level section titles and major KPI values.
- Avoid text overflow in buttons, labels, legends, and table cells.
- Use short labels for filters, tabs, and metrics.

### Chart Design

- Every chart must be easy to read without guessing.
- Use clear axis labels, legends, and units.
- Prefer line charts for trends, bars for rankings, heatmaps for intensity, and tables for evidence.
- Avoid unnecessary 3D charts, heavy animation, and decorative chart effects.
- Highlight the selected period, spike, worst aspect, or best aspect directly in the chart where possible.
- Keep chart colors consistent across tabs.

### Interaction Design

- Filters should feel immediate and predictable.
- Clickable aspects should open related reviews or supporting evidence.
- Recommendation cards should show why the action was suggested, not only the action.
- Use visual priority indicators for High, Medium, and Low recommendations.
- Empty states must explain what filter combination caused no result and how to recover.

### Quality Bar

Before considering the UI acceptable, check:

- It does not look like a template generated in one prompt.
- It does not rely on decorative AI visuals to appear impressive.
- It looks useful for a manager reviewing service performance.
- It supports scanning, comparison, and drill-down without visual clutter.
- It feels specific to BTS Skytrain sentiment and operational analysis.

## 8. Recommended Technologies

Use the current project stack first.

Current stack:

- Python.
- Pandas.
- Plotly or static HTML chart output.
- Static GitHub Pages output through `docs/index.html`.

Optional visualization libraries:

- Plotly.
- Seaborn.
- Matplotlib.

Optional BI tools:

- Microsoft Power BI.
- Tableau.

## 9. Recommended Visual Components

| Visualization | Purpose |
| --- | --- |
| KPI Cards | Quick overview |
| Pie Chart | Sentiment distribution |
| Line Chart | Net Sentiment Score trend |
| Area Chart | Sentiment volume |
| Heatmap | Aspect intensity |
| Word Cloud | Keyword extraction |
| Bar Chart | Aspect ranking |
| Review Explorer | Drill-down evidence |
| Recommendation Cards | Strategic insights |

## 10. Important Dashboard Requirements

The dashboard must support:

- Interactive filters for date range, aspect, BTS line or source, product or service proxy, and sentiment type.
- Time-based analytics for daily, weekly, monthly, and quarterly periods.
- Dynamic recommendations based on selected period, aspect trends, and Net Sentiment Score fluctuations.
- Drill-down analysis from aspect summaries into related reviews.
- Business-language interpretation for every major chart.
- Evidence-backed conclusions, not unsupported causal claims.

## 11. Chart Explanation Documentation

The project must include documentation for visualizations. For each major chart, document:

1. Chart name.
2. Purpose.
3. Data source.
4. Business meaning.
5. How to interpret.
6. Example insight.
7. Recommended action.

Example:

Chart name:

Sentiment Trend Timeline.

Purpose:

Track sentiment changes over time.

Business meaning:

Identify periods of declining customer satisfaction.

How to interpret:

- Rising negative trend indicates a possible operational issue.
- Stable positive trend indicates healthy performance.
- Sudden spikes suggest a service incident or unusual passenger experience.

Example insight:

Negative sentiment increased during the selected week, mainly related to punctuality.

Recommended action:

Investigate operational changes or incidents during the affected period.

## 12. Verification

Before finishing dashboard changes:

```powershell
python build_static_site.py
python verify_dashboard.py
```

Also check generated `docs/index.html` for JavaScript syntax when Node is available.

## 13. Acceptance Criteria

The dashboard is acceptable when:

- UI has exactly 4 main tabs.
- Tab 1 is Executive Overview.
- Tab 2 is Time-Based Trend Analysis.
- Tab 3 is Aspect & Root Cause Analysis.
- Tab 4 is Strategic Recommendation Center.
- Net Sentiment Score is calculated as `((Positive Reviews - Negative Reviews) / Total Reviews) * 100`.
- Time-based analysis supports daily, weekly, monthly, and quarterly views.
- Dynamic recommendations update from selected period, aspect trends, and Net Sentiment Score fluctuations.
- Overview includes KPI cards, data insight, and review exploration.
- Root cause analysis identifies why customers are satisfied or dissatisfied.
- Strategic recommendations include evidence, interpretation, conclusion, action, priority, and expected impact.
- UI looks professional, specific to BTS service analytics, and avoids generic AI-generated dashboard styling.
