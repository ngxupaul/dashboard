# UI Generation Guide

## Project Topic

Build a professional analytics dashboard for:

**Enhancing BTS Skytrain Services through Aspect-Based Sentiment Analysis of Passenger Reviews**

Scope:
- BTS Skytrain lines: **Sukhumvit** and **Silom**
- Review dataset: `all_reviews_predicted.csv`
- Goal: help transport operators understand passenger sentiment, identify service pain points, compare line performance, and prioritize service improvements using aspect-based sentiment analysis.

## Data Context

Use the CSV columns as the main source of truth:

| Column | Meaning |
| --- | --- |
| `review_text` | Passenger review content |
| `review_rating` | Original review rating |
| `source` | Review platform/source |
| `created_at_date` | Review timestamp |
| `bts_line` | BTS line, mainly Sukhumvit or Silom |
| `reviewer_hometown` | Reviewer location when available |
| `aspect` | Original aspect label |
| `sentiment` | Original sentiment label |
| `aspect_pred` | Predicted service aspect |
| `sentiment_pred` | Predicted sentiment: Positive, Neutral, Negative |
| `sentiment_confidence` | Model confidence score |

Primary analysis fields should be:
- `created_at_date`
- `bts_line`
- `aspect_pred`
- `sentiment_pred`
- `sentiment_confidence`
- `review_text`
- `source`
- `review_rating`

## Product Goal

Create a dashboard that feels like a real transit operations intelligence tool, not a generic AI-generated dashboard.

The UI should support:
- Executive-level monitoring of public satisfaction
- Time-based detection of service issues
- Aspect-level diagnosis of passenger complaints
- Comparison between Sukhumvit and Silom lines
- Evidence-backed recommendations for operational improvement
- Drill-down into real passenger reviews

## Recommended Tech Skills

Use the project stack if it already exists. If starting from scratch, prefer:

- **Frontend**: React + Vite
- **Styling**: Tailwind CSS or clean CSS modules
- **Charts**: Recharts, ECharts, Plotly, or Chart.js
- **Data parsing**: Papa Parse for CSV
- **Icons**: Lucide React
- **Date handling**: date-fns

UI behavior should be fully client-side unless a backend already exists.

## Visual Direction

Design the dashboard like a serious public transit analytics product.

Use a restrained, polished style:
- White or very light gray page background
- Dark charcoal text
- BTS-inspired accents without overusing them
- Sukhumvit line accent: green
- Silom line accent: deep blue or teal
- Negative sentiment: red
- Neutral sentiment: amber or gray
- Positive sentiment: green

Avoid:
- Purple-blue AI gradients
- Overly rounded cards
- Floating glassmorphism panels
- Decorative blobs, orbs, or generic AI backgrounds
- Large marketing hero sections
- Emoji-heavy UI
- Fake-looking generic illustrations
- Cards nested inside cards

Preferred look:
- Dense but readable
- Operational and professional
- Similar to a transit control-room dashboard, BI dashboard, or city mobility analytics platform
- Clean typography, compact spacing, and clear data hierarchy

## Information Architecture

Use a tabbed dashboard with four main views.

### 1. Executive Overview

Purpose:
Give a quick summary of passenger satisfaction and system health.

Required components:
- KPI cards:
  - Total Reviews
  - Net Sentiment Score
  - Positive Rate
  - Negative Rate
  - Average Model Confidence
- Sentiment Distribution chart
- Review Volume Over Time chart
- NSS Trend chart
- Line comparison summary for Sukhumvit vs Silom
- Top positive aspect and top negative aspect

Net Sentiment Score formula:

```text
NSS = ((Positive Reviews - Negative Reviews) / Total Reviews) * 100
```

NSS interpretation:

| NSS | Meaning |
| --- | --- |
| > 50 | Excellent passenger satisfaction |
| 20 to 50 | Good |
| 0 to 20 | Mixed or neutral |
| < 0 | Service risk |

### 2. Time-Based Trend Analysis

Purpose:
Reveal when passenger sentiment changes and connect those changes to service issues.

Required components:
- Time granularity selector:
  - Daily
  - Weekly
  - Monthly
  - Quarterly
- NSS line chart over time
- Stacked sentiment volume chart over time
- Line filter: All, Sukhumvit, Silom
- Aspect trend selector
- Multi-line trend chart by aspect
- Spike/drop detection cards:
  - Worst NSS drop
  - Highest complaint period
  - Best recovery period

Use this tab as the core analytical workspace.

### 3. Aspect & Root Cause Analysis

Purpose:
Explain why passengers feel positive or negative.

Required components:
- Aspect sentiment distribution bar chart
- Aspect NSS ranking
- Heatmap:
  - Rows: aspects
  - Columns: sentiment or month
  - Cell value: review count, negative rate, or NSS
- Positive keyword panel
- Negative keyword panel
- Review drill-down table

The review table should include:
- Date
- BTS line
- Aspect
- Sentiment
- Confidence
- Rating
- Source
- Review text preview

Aspect examples should be BTS-specific:
- Crowding & Comfort
- Fare & Payment System
- Route Coverage & Connectivity
- Information & Navigation
- Station Facilities
- Staff & Service
- Safety & Security
- Train Frequency & Waiting Time
- Cleanliness
- Accessibility

### 4. Strategic Recommendation Center

Purpose:
Convert sentiment findings into management actions.

Recommendation cards should contain:
- Time Period
- BTS Line
- Aspect
- Problem
- Evidence
- Strategic Action
- Priority
- Expected Impact

Example recommendation:

```text
Issue Identified:
Negative sentiment for Crowding & Comfort increased during the selected period, especially on the Sukhumvit line.

Evidence:
Negative review share rose while total review volume also increased.

Strategic Action:
Review train frequency during peak periods and improve station crowd-flow communication.

Priority:
High

Expected Impact:
Reduced crowding complaints and improved passenger comfort perception.
```

## Global Filters

Place filters in a persistent top filter bar or left sidebar.

Required filters:
- Date range
- BTS line: All, Sukhumvit, Silom
- Aspect
- Sentiment
- Source
- Confidence threshold
- Time granularity

Filters should update all charts and recommendation cards.

## Dashboard Layout Rules

Use a practical dashboard layout:
- Top: compact title, subtitle, and global filters
- Then: KPI row
- Then: charts in a responsive grid
- Then: evidence panels, recommendations, and review drill-down

Desktop:
- Use a 12-column grid
- KPI cards should be compact
- Put important charts above the fold
- Avoid excessive vertical whitespace

Mobile:
- Stack sections cleanly
- Keep filters usable
- Make charts horizontally readable
- Avoid text overflow in cards and buttons

## Interaction Requirements

The UI should support:
- Clicking an aspect to filter related charts and reviews
- Clicking a sentiment segment to filter review records
- Hover tooltips on charts
- Sorting review table rows
- Searching review text
- Reset filters button
- Empty states when filters return no data
- Loading state while parsing CSV
- Error state if CSV cannot load

## Recommendation Logic

Recommendations can be rule-based.

Use patterns such as:
- If NSS drops sharply, flag the affected period.
- If negative review share increases for one aspect, create a high-priority recommendation.
- If a line has worse NSS than the other line, recommend line-specific investigation.
- If confidence is low, mark insights as needing manual validation.
- If positive sentiment rises after a bad period, highlight recovery and sustainment actions.

Priority guidance:
- High: negative share is high, NSS is below 0, or complaint volume spikes.
- Medium: negative trend is rising but NSS remains positive.
- Low: stable issue with low volume.

## Data Quality Rules

Handle data carefully:
- Parse dates from `created_at_date`
- Ignore rows with missing dates in time charts
- Treat missing `bts_line` as `Unknown`
- Prefer `aspect_pred` over `aspect`
- Prefer `sentiment_pred` over `sentiment`
- Clamp confidence values between 0 and 1 if needed
- Do not invent data that is not in the CSV
- Label generated recommendations as data-driven suggestions, not facts

## Tone And Copywriting

Use concise, operational language.

Good labels:
- Passenger Sentiment
- Service Aspect
- Line Performance
- Complaint Pressure
- Recovery Signal
- Review Evidence
- Operational Recommendation

Avoid generic AI wording:
- "Unlock insights"
- "AI-powered magic"
- "Transform your business"
- "Revolutionary analytics"
- "Seamless experience"

## Visual Components Checklist

Include:
- KPI cards
- Segmented tabs
- Date range controls
- Select dropdowns
- Line chart
- Stacked area or bar chart
- Horizontal bar chart
- Heatmap
- Review table
- Recommendation cards
- Confidence indicator
- Reset filters action

Use icons only where helpful:
- Train or route icon for BTS line
- Calendar icon for date range
- Filter icon for filter controls
- Trending up/down icons for NSS movement
- Alert icon for high-priority issues

## Final Quality Bar

Before considering the UI complete:
- It must clearly communicate the BTS Skytrain topic on the first screen.
- Sukhumvit and Silom must be visible as primary analysis dimensions.
- The dashboard must use real CSV fields.
- The design must look like a professional analytics tool, not a template.
- Charts must have clear labels, legends, and tooltips.
- Filters must affect visible insights.
- Recommendation cards must cite evidence from selected data.
- The review drill-down must connect charts back to real passenger comments.
- The layout must be responsive and avoid overlapping text.
