from __future__ import annotations

import json
from html import escape
from pathlib import Path

import pandas as pd

from dashboard_data import (
    ACTION_ASPECTS,
    ASPECT_ACTIONS,
    ASPECT_COLUMNS,
    DATA_PATH,
    aspect_evidence_reviews,
    aspect_nss_summary,
    aspect_priority,
    aspect_recent_changes,
    aspect_sentiment_time_series,
    categorical_sentiment_breakdown,
    filter_dataset,
    high_agreement_low_rating,
    keyword_frequency,
    lda_topic_keywords,
    kpi_summary,
    load_dataset,
    model_agreement,
    negative_spikes,
    recent_period_comparison,
    review_table,
    root_cause_matrix,
    sentiment_distribution,
    sentiment_time_series,
    time_coverage_summary,
)


DOCS_DIR = Path(__file__).with_name("docs")
OUT_PATH = DOCS_DIR / "index.html"

TIME_FREQUENCIES = {
    "daily": "D",
    "weekly": "W",
    "monthly": "M",
    "quarterly": "Q",
}

ASPECT_LABELS = {
    "Fare & Payment System": "Fare & Payment (Price)",
}


def main() -> None:
    df = load_dataset(DATA_PATH)
    service_df = filter_dataset(df, service_relevant_only=True)

    priority = add_aspect_labels(aspect_priority(service_df))
    root_causes = root_cause_matrix(service_df)
    root_causes["Aspect label"] = root_causes["Related aspect"].map(aspect_label)

    agreement, model_pairs = model_agreement(service_df)
    summary = kpi_summary(service_df, total_rows=len(df))
    summary.update(executive_summary(priority, agreement))

    payload = {
        "summary": summary,
        "sentiment": sentiment_distribution(service_df).to_dict("records"),
        "timeSeries": {
            key: _json_records(recent_periods(sentiment_time_series(service_df, freq), key))
            for key, freq in TIME_FREQUENCIES.items()
        },
        "aspectTrends": {
            key: {
                aspect: _json_records(
                    recent_periods(aspect_sentiment_time_series(service_df, aspect, freq), key)
                )
                for aspect in ASPECT_COLUMNS
            }
            for key, freq in TIME_FREQUENCIES.items()
        },
        "periodComparison": recent_period_comparison(service_df, "M"),
        "negativeSpikes": _json_records(negative_spikes(service_df, "M", limit=6)),
        "aspectChanges": add_aspect_labels(aspect_recent_changes(service_df, "M")).to_dict("records"),
        "nssByAspect": add_aspect_labels(aspect_nss_summary(service_df)).to_dict("records"),
        "timeCoverage": time_coverage_summary(service_df),
        "aspectDistribution": aspect_distribution_records(priority),
        "priority": priority_table_records(priority),
        "rootCauses": root_causes.to_dict("records"),
        "sourceBreakdown": categorical_sentiment_breakdown(
            service_df,
            "source_display",
            "Source",
            limit=10,
        ).to_dict("records"),
        "lineBreakdown": categorical_sentiment_breakdown(
            service_df,
            "bts_line_display",
            "BTS line",
            limit=10,
        ).to_dict("records"),
        "negativeKeywords": keyword_frequency(service_df, sentiment="Negative", limit=16).to_dict("records"),
        "positiveKeywords": keyword_frequency(service_df, sentiment="Positive", limit=16).to_dict("records"),
        "negativeTopics": lda_topic_keywords(service_df, sentiment="Negative").to_dict("records"),
        "positiveTopics": lda_topic_keywords(service_df, sentiment="Positive").to_dict("records"),
        "recommendations": business_recommendations(service_df, priority),
        "modelPairs": model_pairs.head(10).to_dict("records"),
        "reviews": _json_records(
            review_table(
                service_df.sort_values(["agreement_count", "review_rating_num"], ascending=[False, True]),
                limit=800,
            )
        ),
        "evidenceComplaints": _json_records(
            high_agreement_low_rating(service_df, min_agreement=20, max_rating=2, limit=18)
        ),
    }

    DOCS_DIR.mkdir(exist_ok=True)
    OUT_PATH.write_text(render_html(payload), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


def add_aspect_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["Aspect label"] = out["Aspect"].map(aspect_label)
    return out


def aspect_label(aspect: str) -> str:
    return ASPECT_LABELS.get(aspect, aspect)


def recent_periods(df: pd.DataFrame, grain: str) -> pd.DataFrame:
    if df.empty:
        return df
    months = {
        "daily": 6,
        "weekly": 18,
        "monthly": 36,
        "quarterly": 72,
    }[grain]
    cutoff = df["Period"].max() - pd.DateOffset(months=months)
    return df[df["Period"].ge(cutoff)].copy()


def executive_summary(priority: pd.DataFrame, agreement: float) -> dict[str, object]:
    worst = priority.iloc[0]
    positive = priority.assign(
        PositiveShare=lambda data: data["Positive"]
        / data[["Negative", "Neutral", "Positive"]].sum(axis=1).replace(0, 1)
    ).sort_values(["PositiveShare", "Positive"], ascending=False)
    best = positive.iloc[0]
    return {
        "model_agreement": agreement,
        "highest_risk_aspect": worst["Aspect label"],
        "highest_risk_negative_share": float(worst["Negative share"]),
        "highest_risk_negative": int(worst["Negative"]),
        "best_aspect": best["Aspect label"],
        "best_aspect_positive_share": float(best["PositiveShare"]),
        "best_aspect_positive": int(best["Positive"]),
    }


def aspect_distribution_records(priority: pd.DataFrame) -> list[dict]:
    out = priority.copy()
    totals = out[["Negative", "Neutral", "Positive"]].sum(axis=1).replace(0, 1)
    out["Negative share"] = out["Negative"] / totals
    out["Neutral share"] = out["Neutral"] / totals
    out["Positive share"] = out["Positive"] / totals
    return out[
        [
            "Aspect",
            "Aspect label",
            "Mentions",
            "Negative",
            "Neutral",
            "Positive",
            "Negative share",
            "Neutral share",
            "Positive share",
            "Negative agreement",
            "Priority score",
        ]
    ].to_dict("records")


def priority_table_records(priority: pd.DataFrame) -> list[dict]:
    return priority[
        [
            "Aspect",
            "Aspect label",
            "Mentions",
            "Negative",
            "Neutral",
            "Positive",
            "Negative agreement",
            "Priority score",
            "Negative share",
        ]
    ].to_dict("records")


def business_recommendations(service_df: pd.DataFrame, priority: pd.DataFrame) -> list[dict]:
    rows = priority.set_index("Aspect")
    recommendations = []
    for aspect in ACTION_ASPECTS:
        row = rows.loc[aspect]
        actions = ASPECT_ACTIONS[aspect]
        time_signal = aspect_time_signal(service_df, aspect)
        evidence = aspect_evidence_reviews(service_df, aspect, limit=2)
        snippets = evidence["Review snippet"].tolist() if not evidence.empty else []
        recommendations.append(
            {
                "aspect": aspect,
                "aspectLabel": aspect_label(aspect),
                "problem": actions["goal"],
                "priority": recommendation_priority(row, time_signal),
                "businessImpact": business_impact(aspect),
                "actions": actions["actions"],
                "successMetrics": actions["metrics"],
                "evidenceReviews": snippets,
                "timeSignal": time_signal,
                "timeBasedTrigger": time_based_trigger(aspect, time_signal),
                "numbers": {
                    "mentions": int(row["Mentions"]),
                    "negative": int(row["Negative"]),
                    "neutral": int(row["Neutral"]),
                    "positive": int(row["Positive"]),
                    "negativeShare": float(row["Negative share"]),
                    "negativeAgreement": int(row["Negative agreement"]),
                    "priorityScore": float(row["Priority score"]),
                },
                "interpretation": recommendation_interpretation(aspect, row, time_signal),
                "conclusion": recommendation_conclusion(aspect, row, time_signal),
            }
        )
    return sorted(
        recommendations,
        key=lambda rec: (
            rec["timeSignal"]["negativeShareChange"],
            rec["timeSignal"]["negativeCountChange"],
            rec["numbers"]["priorityScore"],
        ),
        reverse=True,
    )


def aspect_time_signal(service_df: pd.DataFrame, aspect: str) -> dict[str, object]:
    trend = aspect_sentiment_time_series(service_df, aspect, "M")
    if trend.empty:
        return empty_time_signal()

    pivot = (
        trend.pivot_table(index="Period", columns="Sentiment", values="Reviews", aggfunc="sum")
        .reindex(columns=["Negative", "Neutral", "Positive"], fill_value=0)
        .sort_index()
    )
    active = pivot[pivot.sum(axis=1).gt(0)]
    if len(active) < 2:
        return empty_time_signal()

    previous = active.iloc[-2]
    current = active.iloc[-1]
    previous_total = int(previous.sum())
    current_total = int(current.sum())
    previous_negative_share = float(previous["Negative"] / previous_total) if previous_total else 0
    current_negative_share = float(current["Negative"] / current_total) if current_total else 0

    negative_series = active["Negative"].astype(float)
    baseline = float(negative_series.iloc[-4:-1].mean()) if len(negative_series) >= 4 else float(negative_series.iloc[:-1].mean())
    spike_score = max(0.0, float(current["Negative"]) - baseline)

    share_change = current_negative_share - previous_negative_share
    count_change = int(current["Negative"] - previous["Negative"])
    if share_change >= 0.05 or count_change >= 5:
        direction = "worsening"
    elif share_change <= -0.05 or count_change <= -5:
        direction = "improving"
    else:
        direction = "stable"

    return {
        "previousPeriod": active.index[-2].strftime("%Y-%m"),
        "currentPeriod": active.index[-1].strftime("%Y-%m"),
        "previousMentions": previous_total,
        "currentMentions": current_total,
        "previousNegative": int(previous["Negative"]),
        "currentNegative": int(current["Negative"]),
        "previousNegativeShare": previous_negative_share,
        "currentNegativeShare": current_negative_share,
        "negativeShareChange": float(share_change),
        "negativeCountChange": count_change,
        "spikeScore": spike_score,
        "direction": direction,
    }


def empty_time_signal() -> dict[str, object]:
    return {
        "previousPeriod": "",
        "currentPeriod": "",
        "previousMentions": 0,
        "currentMentions": 0,
        "previousNegative": 0,
        "currentNegative": 0,
        "previousNegativeShare": 0,
        "currentNegativeShare": 0,
        "negativeShareChange": 0,
        "negativeCountChange": 0,
        "spikeScore": 0,
        "direction": "unknown",
    }


def time_based_trigger(aspect: str, signal: dict[str, object]) -> str:
    label = aspect_label(aspect)
    if signal["direction"] == "worsening":
        return (
            f"{label} is worsening in {signal['currentPeriod']}: negative share moved from "
            f"{signal['previousNegativeShare']:.1%} to {signal['currentNegativeShare']:.1%}, "
            f"with {signal['negativeCountChange']:+,} negative reviews versus the previous month."
        )
    if signal["direction"] == "improving":
        return (
            f"{label} improved in {signal['currentPeriod']}: negative share moved from "
            f"{signal['previousNegativeShare']:.1%} to {signal['currentNegativeShare']:.1%}. "
            "Keep monitoring because the aspect remains a priority in the full-period evidence."
        )
    if signal["direction"] == "stable":
        return (
            f"{label} is stable month over month, with negative share near "
            f"{signal['currentNegativeShare']:.1%} in {signal['currentPeriod']}. "
            "The recommendation is driven by persistent risk rather than a sudden spike."
        )
    return f"{label} has insufficient month-over-month data, so the recommendation uses full-period evidence."


def recommendation_priority(row: pd.Series, time_signal: dict[str, object]) -> str:
    share = float(row["Negative share"])
    negative = int(row["Negative"])
    agreement = int(row["Negative agreement"])
    worsening = (
        time_signal["direction"] == "worsening"
        and (time_signal["negativeShareChange"] >= 0.08 or time_signal["negativeCountChange"] >= 10)
    )
    if (share >= 0.45 and negative >= 250 and agreement >= 1000) or worsening:
        return "Critical"
    if share >= 0.35 or negative >= 250 or agreement >= 1000:
        return "High"
    return "Medium"


def business_impact(aspect: str) -> str:
    return {
        "Crowding & Comfort": "Crowded and uncomfortable trips weaken perceived reliability during high-demand periods.",
        "Fare & Payment System": "Payment friction increases station stress and can make the service feel less accessible to tourists and occasional riders.",
        "Infrastructure & Facilities": "Facility issues reduce comfort, accessibility, and confidence in station operations.",
        "Route Coverage & Connectivity": "Transfer confusion and connectivity gaps can reduce network usefulness even when trains are available.",
    }.get(aspect, "The issue can reduce passenger satisfaction and repeat usage.")


def recommendation_interpretation(
    aspect: str,
    row: pd.Series,
    time_signal: dict[str, object],
) -> str:
    trend_sentence = time_based_trigger(aspect, time_signal)
    return (
        f"{aspect_label(aspect)} should be treated as an operational signal because "
        f"{int(row['Negative']):,} of {int(row['Mentions']):,} mentioned reviews are negative "
        f"({float(row['Negative share']):.1%}). Time-based evidence: {trend_sentence}"
    )


def recommendation_conclusion(
    aspect: str,
    row: pd.Series,
    time_signal: dict[str, object],
) -> str:
    if time_signal["direction"] == "worsening":
        urgency = "recent monthly deterioration"
    elif time_signal["direction"] == "improving":
        urgency = "remaining full-period risk despite recent improvement"
    elif time_signal["direction"] == "stable":
        urgency = "persistent month-over-month risk"
    else:
        urgency = "available full-period risk evidence"
    return (
        f"Prioritize {aspect_label(aspect).lower()} improvements because the issue has both "
        f"complaint volume and {int(row['Negative agreement']):,} agreement points behind negative reviews, "
        f"with the action trigger based on {urgency}."
    )


def render_html(payload: dict) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BTS Skytrain ABSA Business Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
  <style>
    :root {{
      color-scheme: light;
      --ink: #17202a;
      --muted: #667085;
      --line: #d7dde7;
      --panel: #ffffff;
      --bg: #eef2f6;
      --navy: #111827;
      --blue: #2563eb;
      --green: #138a63;
      --red: #c24132;
      --gray: #8a94a6;
      --amber: #b7791f;
      --purple: #7c3aed;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, Segoe UI, Arial, sans-serif;
      margin: 0;
    }}
    .shell {{
      display: grid;
      grid-template-columns: 300px minmax(0, 1fr);
      min-height: 100vh;
    }}
    aside {{
      background: var(--navy);
      color: #fff;
      padding: 24px 20px;
    }}
    .brand h1 {{
      color: #fff;
      font-size: 26px;
      letter-spacing: 0;
      line-height: 1.12;
      margin: 0;
    }}
    .brand p, .sidebar-note {{
      color: #cbd5e1;
      font-size: 13px;
      line-height: 1.55;
    }}
    .nav {{
      display: grid;
      gap: 8px;
      margin-top: 24px;
    }}
    .tab-button {{
      background: transparent;
      border: 1px solid rgba(255,255,255,.16);
      border-radius: 8px;
      color: #dbe4f0;
      cursor: pointer;
      font: inherit;
      padding: 10px 11px;
      text-align: left;
    }}
    .tab-button.active {{
      background: #fff;
      border-color: #fff;
      color: var(--navy);
      font-weight: 750;
    }}
    .sidebar-note {{
      border-top: 1px solid rgba(255,255,255,.14);
      margin-top: 24px;
      padding-top: 16px;
    }}
    main {{
      min-width: 0;
      padding: 24px;
    }}
    .page-head {{
      align-items: end;
      display: flex;
      gap: 16px;
      justify-content: space-between;
      margin-bottom: 18px;
    }}
    .page-head h2 {{
      font-size: 30px;
      letter-spacing: 0;
      margin: 0;
    }}
    .page-head p {{
      color: var(--muted);
      line-height: 1.5;
      margin: 6px 0 0;
      max-width: 840px;
    }}
    .pill {{
      background: #dbeafe;
      border: 1px solid #bfdbfe;
      border-radius: 999px;
      color: #1d4ed8;
      font-size: 13px;
      font-weight: 750;
      padding: 8px 12px;
      white-space: nowrap;
    }}
    .metrics {{
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(6, minmax(0, 1fr));
      margin-bottom: 18px;
    }}
    .metric, .panel, .recommendation, .insight {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgba(17,24,39,.04);
    }}
    .metric {{
      min-height: 104px;
      padding: 14px;
    }}
    .metric small {{
      color: var(--muted);
      display: block;
      font-size: 12px;
      font-weight: 750;
      letter-spacing: .04em;
      text-transform: uppercase;
    }}
    .metric strong {{
      display: block;
      font-size: clamp(22px, 2.4vw, 32px);
      margin-top: 6px;
    }}
    .metric span {{
      color: var(--muted);
      display: block;
      font-size: 13px;
      line-height: 1.35;
      margin-top: 4px;
    }}
    .grid {{
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .grid-3 {{
      display: grid;
      gap: 16px;
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }}
    .panel {{
      min-height: 360px;
      overflow: hidden;
      padding: 18px;
    }}
    .wide {{ grid-column: 1 / -1; }}
    .panel h3, .recommendation h3, .insight h3 {{
      font-size: 18px;
      margin: 0 0 10px;
    }}
    .panel p, .explain, .recommendation p, .insight p {{
      color: var(--muted);
      font-size: 14px;
      line-height: 1.55;
      margin: 0 0 12px;
    }}
    .canvas-box {{
      height: 310px;
      position: relative;
    }}
    .canvas-box.tall {{ height: 430px; }}
    .control-row {{
      align-items: center;
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 14px;
    }}
    select, input {{
      background: #fff;
      border: 1px solid var(--line);
      border-radius: 8px;
      color: var(--ink);
      font: inherit;
      min-height: 40px;
      padding: 8px 10px;
    }}
    select {{ min-width: 230px; }}
    input {{ min-width: 210px; }}
    table {{
      border-collapse: collapse;
      font-size: 14px;
      width: 100%;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 9px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    .snippet {{
      color: var(--muted);
      line-height: 1.45;
      max-width: 620px;
    }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
    .recommendations {{
      display: grid;
      gap: 14px;
    }}
    .recommendation {{
      border-left: 5px solid var(--blue);
      padding: 16px;
    }}
    .recommendation .meta {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
      margin-bottom: 8px;
    }}
    .recommendation .priority {{
      color: var(--ink);
      font-weight: 750;
    }}
    .insight {{
      padding: 16px;
    }}
    .risk {{
      display: inline-block;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 750;
      padding: 4px 8px;
    }}
    .risk.Critical {{ background: #fee2e2; color: #991b1b; }}
    .risk.High {{ background: #ffedd5; color: #9a3412; }}
    .risk.Medium {{ background: #fef3c7; color: #92400e; }}
    .risk.Low {{ background: #dcfce7; color: #166534; }}
    .review-count {{
      color: var(--muted);
      font-size: 13px;
      margin: 0 0 12px;
    }}
    .footer {{
      color: var(--muted);
      font-size: 13px;
      margin-top: 20px;
      text-align: center;
    }}
    @media (max-width: 1120px) {{
      .shell {{ grid-template-columns: 1fr; }}
      aside {{ position: static; }}
      .nav {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .metrics, .grid, .grid-3 {{ grid-template-columns: 1fr; }}
      .page-head {{ align-items: start; flex-direction: column; }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <h1>BTS Skytrain ABSA Business Dashboard</h1>
        <p>Generated from <code>reference/all_reviews_predicted.csv</code>. Built for time-based analysis, interpretation, and operational decisions.</p>
      </div>
      <nav class="nav" aria-label="Dashboard tabs">
        <button class="tab-button active" data-tab="overview">Executive Overview</button>
        <button class="tab-button" data-tab="time">Time-Based Trend Analysis</button>
        <button class="tab-button" data-tab="root">Aspect & Root Cause Analysis</button>
        <button class="tab-button" data-tab="recommendations">Strategic Recommendation Center</button>
      </nav>
      <div class="sidebar-note">
        Sentiment uses <code>sentiment_pred</code> and aspects use <code>aspect_pred</code>.
        The dashboard includes NSS, aspect risk, keyword evidence, and LDA topic insights.
      </div>
    </aside>
    <main>
      <section class="tab-panel active" id="overview">
        <div class="page-head">
          <div>
            <h2>Executive Overview</h2>
            <p>High-level customer sentiment performance, Net Sentiment Score, sentiment distribution, trend movement, and priority service areas.</p>
          </div>
          <div class="pill">Scope: service-relevant reviews</div>
        </div>
        <section class="metrics">
          {metric("Total reviews", payload["summary"]["filtered_reviews"], "Default BTS scope")}
          {metric("NSS", f"{payload['summary']['net_sentiment_score']:.1f}", "Net Sentiment Score")}
          {metric("Positive rate", f"{payload['summary']['positive_share']:.1%}", "Predicted positive")}
          {metric("Negative rate", f"{payload['summary']['negative_share']:.1%}", "Predicted negative")}
          {metric("Positive reviews", payload["summary"]["positive_reviews"], "Positive count")}
          {metric("Negative reviews", payload["summary"]["negative_reviews"], "Negative count")}
        </section>
        <section class="grid">
          <article class="panel">
            <h3>Overall sentiment distribution</h3>
            <p id="overallExplain"></p>
            <div class="canvas-box"><canvas id="sentimentChart"></canvas></div>
          </article>
          <article class="panel">
            <h3>Top service priorities</h3>
            <p id="priorityExplain"></p>
            <div class="canvas-box"><canvas id="priorityChart"></canvas></div>
          </article>
          <article class="panel wide">
            <h3>Monthly sentiment movement</h3>
            <p id="periodExplain"></p>
            <div class="canvas-box"><canvas id="overallTrendChart"></canvas></div>
          </article>
          <article class="panel wide">
            <h3>Net Sentiment Score by aspect</h3>
            <p>Notebook business-insight view: aspect NSS ranks which operating areas are creating satisfaction or dissatisfaction.</p>
            <div class="canvas-box tall"><canvas id="nssAspectChart"></canvas></div>
          </article>
          <article class="panel wide">
            <h3>Aspect distribution and sentiment heatmap</h3>
            <p>Stacked counts show whether each service area is mainly praised, neutral, or complained about.</p>
            <div class="canvas-box tall"><canvas id="aspectStackChart"></canvas></div>
          </article>
          <article class="panel">
            <h3>Aspect drilldown</h3>
            <div class="control-row">
              <label for="aspectSelect">Aspect</label>
              <select id="aspectSelect"></select>
            </div>
            <p id="aspectDrilldownExplain"></p>
            <div class="canvas-box"><canvas id="selectedAspectChart"></canvas></div>
          </article>
          <article class="panel">
            <h3>Priority ranking</h3>
            <div id="aspectTable"></div>
          </article>
          <article class="panel wide">
            <h3>Review Explorer</h3>
            <p>Search and filter raw review evidence behind the business insights.</p>
            <div class="control-row">
              <select id="reviewSentimentFilter"><option value="">All sentiments</option></select>
              <select id="reviewAspectFilter"><option value="">All aspects</option></select>
              <select id="reviewLineFilter"><option value="">All BTS lines</option></select>
              <select id="reviewSourceFilter"><option value="">All sources</option></select>
              <input id="reviewStartDate" type="date" title="Start date">
              <input id="reviewEndDate" type="date" title="End date">
              <input id="reviewSearch" type="search" placeholder="Search review text">
              <input id="reviewAgreement" type="number" min="0" value="0" title="Minimum agreement">
            </div>
            <p class="review-count" id="reviewCount"></p>
            <div id="reviewTable"></div>
          </article>
        </section>
      </section>

      <section class="tab-panel" id="time">
        <div class="page-head">
          <div>
            <h2>Time-Based Trend Analysis</h2>
            <p>Track overall sentiment, review frequency, and selected aspect movement by day, week, month, or quarter.</p>
          </div>
          <div class="pill">Daily / Weekly / Monthly / Quarterly</div>
        </div>
        <section class="grid">
          <article class="panel wide">
            <h3>Overall sentiment trend</h3>
            <div class="control-row">
              <label for="timeGrainSelect">Time grain</label>
              <select id="timeGrainSelect">
                <option value="monthly">Monthly</option>
                <option value="weekly">Weekly</option>
                <option value="quarterly">Quarterly</option>
                <option value="daily">Daily</option>
              </select>
            </div>
            <p id="timeExplain"></p>
            <div class="canvas-box tall"><canvas id="timeTrendChart"></canvas></div>
          </article>
          <article class="panel wide">
            <h3>Time coverage note</h3>
            <p id="timeCoverageExplain"></p>
          </article>
          <article class="panel">
            <h3>Selected aspect trend</h3>
            <div class="control-row">
              <label for="trendAspectSelect">Aspect</label>
              <select id="trendAspectSelect"></select>
            </div>
            <p id="aspectTrendExplain"></p>
            <div class="canvas-box"><canvas id="aspectTrendChart"></canvas></div>
          </article>
        </section>
      </section>

      <section class="tab-panel" id="root">
        <div class="page-head">
          <div>
            <h2>Aspect & Root Cause Analysis</h2>
            <p>Detect sudden increases in negative sentiment, identify contributing aspects, classify operational risk, and expose keyword patterns.</p>
          </div>
          <div class="pill">Spike detection and causes</div>
        </div>
        <section class="grid">
          <article class="panel">
            <h3>Negative spikes</h3>
            <p>Periods where negative review volume rises above the recent rolling baseline.</p>
            <div id="spikeTable"></div>
          </article>
          <article class="panel">
            <h3>Aspect spike contribution</h3>
            <p>Recent aspect movement explains which service areas are driving NSS risk.</p>
            <div id="aspectChangeTable"></div>
          </article>
          <article class="panel wide">
            <h3>Risk severity and root cause matrix</h3>
            <div id="rootCauseTable"></div>
          </article>
          <article class="panel">
            <h3>Source breakdown</h3>
            <p>Review sources can carry different passenger segments and complaint behavior.</p>
            <div class="canvas-box"><canvas id="sourceChart"></canvas></div>
          </article>
          <article class="panel">
            <h3>BTS line breakdown</h3>
            <p>Line-level sentiment helps identify whether risk is broad or concentrated.</p>
            <div class="canvas-box"><canvas id="lineChart"></canvas></div>
          </article>
          <article class="panel">
            <h3>Negative keywords</h3>
            <div id="negativeKeywordTable"></div>
          </article>
          <article class="panel">
            <h3>Positive keywords</h3>
            <div id="positiveKeywordTable"></div>
          </article>
          <article class="panel">
            <h3>LDA topics - negative reviews</h3>
            <p>Notebook business-insight view: topic keywords summarize recurring complaint themes.</p>
            <div id="negativeTopicTable"></div>
          </article>
          <article class="panel">
            <h3>LDA topics - positive reviews</h3>
            <p>Notebook business-insight view: topic keywords summarize repeated praise themes.</p>
            <div id="positiveTopicTable"></div>
          </article>
        </section>
      </section>

      <section class="tab-panel" id="recommendations">
        <div class="page-head">
          <div>
            <h2>Strategic Recommendation Center</h2>
            <p>Every recommendation is triggered by monthly time-based evidence, then supported with full-period complaint volume, agreement weight, business impact, action, and success metric.</p>
          </div>
          <div class="pill">{len(payload["recommendations"])} priority blocks</div>
        </div>
        <section class="recommendations" id="recommendationCards"></section>
        <div class="page-head">
          <div>
            <h2>Executive Decision Support</h2>
            <p>Strategic risks, opportunities, and executive actions based on recent monthly trend evidence plus measured sentiment evidence.</p>
          </div>
          <div class="pill">Dynamic suggestions</div>
        </div>
        <section class="grid-3">
          <article class="insight">
            <h3>Key business risks</h3>
            <div id="riskList"></div>
          </article>
          <article class="insight">
            <h3>Strategic opportunities</h3>
            <div id="opportunityList"></div>
          </article>
          <article class="insight">
            <h3>Executive recommendations</h3>
            <div id="executiveRecommendations"></div>
          </article>
        </section>
      </section>

      <p class="footer">Generated by <code>build_static_site.py</code> from <code>reference/all_reviews_predicted.csv</code>.</p>
    </main>
  </div>
  <script>
    const dashboardData = {json.dumps(payload, ensure_ascii=False)};
    const colors = {{ Negative: "#C24132", Neutral: "#8A94A6", Positive: "#138A63" }};
    const charts = {{}};

    const commonOptions = {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ position: "bottom" }} }}
    }};

    function number(value) {{
      return Number(value || 0).toLocaleString();
    }}

    function percent(value) {{
      return `${{(Number(value || 0) * 100).toFixed(1)}}%`;
    }}

    function html(value) {{
      return String(value ?? "").replace(/[&<>"']/g, char => ({{
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
      }}[char]));
    }}

    function periods(records) {{
      return [...new Set(records.map(d => d.Period))];
    }}

    function trendDatasets(records) {{
      const labels = periods(records);
      return ["Negative", "Neutral", "Positive"].map(sentiment => ({{
        label: sentiment,
        data: labels.map(period => (records.find(d => d.Period === period && d.Sentiment === sentiment) || {{ Reviews: 0 }}).Reviews),
        borderColor: colors[sentiment],
        backgroundColor: colors[sentiment],
        tension: 0.25,
        pointRadius: 2
      }}));
    }}

    function makeTrendChart(canvasId, records) {{
      const labels = periods(records);
      return new Chart(document.getElementById(canvasId), {{
        type: "line",
        data: {{ labels, datasets: trendDatasets(records) }},
        options: {{ ...commonOptions, scales: {{ y: {{ beginAtZero: true }} }} }}
      }});
    }}

    function updateTrendChart(chart, records) {{
      chart.data.labels = periods(records);
      chart.data.datasets = trendDatasets(records);
      chart.update();
    }}

    function renderSimpleTable(containerId, columns, rows, formatters = {{}}) {{
      const body = rows.map(row => `<tr>${{columns.map(col => {{
        const formatter = formatters[col];
        const value = formatter ? formatter(row[col], row) : row[col];
        return `<td>${{value}}</td>`;
      }}).join("")}}</tr>`).join("");
      document.getElementById(containerId).innerHTML =
        `<table><thead><tr>${{columns.map(col => `<th>${{html(col)}}</th>`).join("")}}</tr></thead><tbody>${{body}}</tbody></table>`;
    }}

    function setupTabs() {{
      document.querySelectorAll(".tab-button").forEach(button => {{
        button.addEventListener("click", () => {{
          document.querySelectorAll(".tab-button").forEach(item => item.classList.remove("active"));
          document.querySelectorAll(".tab-panel").forEach(item => item.classList.remove("active"));
          button.classList.add("active");
          document.getElementById(button.dataset.tab).classList.add("active");
          Object.values(charts).forEach(chart => chart.resize());
        }});
      }});
    }}

    function setupAspectSelectors() {{
      const options = dashboardData.aspectDistribution
        .map(row => `<option value="${{html(row.Aspect)}}">${{html(row["Aspect label"])}}</option>`)
        .join("");
      document.getElementById("aspectSelect").innerHTML = options;
      document.getElementById("trendAspectSelect").innerHTML = options;
      document.getElementById("aspectSelect").addEventListener("change", updateSelectedAspect);
      document.getElementById("trendAspectSelect").addEventListener("change", updateAspectTrend);
      document.getElementById("timeGrainSelect").addEventListener("change", updateTimeViews);
    }}

    function selectedAspect() {{
      const value = document.getElementById("aspectSelect").value;
      return dashboardData.aspectDistribution.find(row => row.Aspect === value) || dashboardData.aspectDistribution[0];
    }}

    function selectedTrendAspect() {{
      const value = document.getElementById("trendAspectSelect").value;
      return dashboardData.aspectDistribution.find(row => row.Aspect === value) || dashboardData.aspectDistribution[0];
    }}

    function updateSelectedAspect() {{
      const row = selectedAspect();
      charts.selectedAspect.data.labels = ["Negative", "Neutral", "Positive"];
      charts.selectedAspect.data.datasets[0].data = [row.Negative, row.Neutral, row.Positive];
      charts.selectedAspect.update();
      document.getElementById("aspectDrilldownExplain").textContent =
        `${{row["Aspect label"]}} has ${{number(row.Mentions)}} mentions. ${{number(row.Negative)}} are negative (${{percent(row["Negative share"])}}), while ${{number(row.Positive)}} are positive.`;
    }}

    function updateTimeViews() {{
      const grain = document.getElementById("timeGrainSelect").value;
      updateTrendChart(charts.timeTrend, dashboardData.timeSeries[grain] || []);
      updateAspectTrend();
      const comparison = dashboardData.periodComparison || {{}};
      const direction = Number(comparison.negative_share_change || 0) >= 0 ? "increased" : "decreased";
      document.getElementById("timeExplain").textContent =
        `The latest monthly negative share ${{direction}} by ${{percent(Math.abs(comparison.negative_share_change || 0))}} versus the previous month. Use the selector to inspect daily, weekly, monthly, or quarterly movement.`;
    }}

    function updateAspectTrend() {{
      const grain = document.getElementById("timeGrainSelect").value;
      const row = selectedTrendAspect();
      const records = (dashboardData.aspectTrends[grain] || {{}})[row.Aspect] || [];
      updateTrendChart(charts.aspectTrend, records);
      document.getElementById("aspectTrendExplain").textContent =
        `${{row["Aspect label"]}} trend is shown at the selected time grain. The full-period split is ${{number(row.Negative)}} negative, ${{number(row.Neutral)}} neutral, and ${{number(row.Positive)}} positive.`;
    }}

    function setupExplorerFilters() {{
      fillSelect("reviewSentimentFilter", [...new Set(dashboardData.reviews.map(r => r.Sentiment))].sort());
      fillSelect("reviewAspectFilter", [...new Set(dashboardData.reviews.map(r => r["Primary aspect"]).filter(Boolean))].sort());
      fillSelect("reviewLineFilter", [...new Set(dashboardData.reviews.map(r => r["BTS line"]).filter(Boolean))].sort());
      fillSelect("reviewSourceFilter", [...new Set(dashboardData.reviews.map(r => r.Source).filter(Boolean))].sort());
      document.getElementById("reviewStartDate").value = dashboardData.summary.date_start || "";
      document.getElementById("reviewEndDate").value = dashboardData.summary.date_end || "";
      ["reviewSentimentFilter", "reviewAspectFilter", "reviewLineFilter", "reviewSourceFilter", "reviewStartDate", "reviewEndDate", "reviewSearch", "reviewAgreement"]
        .forEach(id => document.getElementById(id).addEventListener("input", renderReviews));
    }}

    function fillSelect(id, values) {{
      const select = document.getElementById(id);
      const first = select.querySelector("option").outerHTML;
      select.innerHTML = first + values.map(value => `<option value="${{html(value)}}">${{html(value)}}</option>`).join("");
    }}

    function renderReviews() {{
      const sentiment = document.getElementById("reviewSentimentFilter").value;
      const aspect = document.getElementById("reviewAspectFilter").value;
      const line = document.getElementById("reviewLineFilter").value;
      const source = document.getElementById("reviewSourceFilter").value;
      const startDate = document.getElementById("reviewStartDate").value;
      const endDate = document.getElementById("reviewEndDate").value;
      const search = document.getElementById("reviewSearch").value.trim().toLowerCase();
      const minAgreement = Number(document.getElementById("reviewAgreement").value || 0);
      const rows = dashboardData.reviews.filter(row =>
        (!sentiment || row.Sentiment === sentiment) &&
        (!aspect || row["Primary aspect"] === aspect) &&
        (!line || row["BTS line"] === line) &&
        (!source || row.Source === source) &&
        (!startDate || !row.Date || row.Date >= startDate) &&
        (!endDate || !row.Date || row.Date <= endDate) &&
        Number(row["Agreement count"] || 0) >= minAgreement &&
        (!search || `${{row.Title}} ${{row["Review snippet"]}}`.toLowerCase().includes(search))
      );
      document.getElementById("reviewCount").textContent = `${{number(rows.length)}} reviews match the current explorer filters. Showing top 120 by agreement and low rating.`;
      renderSimpleTable(
        "reviewTable",
        ["Date", "Source", "BTS line", "Rating", "Agreement count", "Sentiment", "Primary aspect", "Review snippet"],
        rows.slice(0, 120),
        {{
          "Date": value => html(value || ""),
          "Source": value => html(value),
          "BTS line": value => html(value),
          "Rating": value => number(value),
          "Agreement count": value => number(value),
          "Sentiment": value => html(value),
          "Primary aspect": value => html(value),
          "Review snippet": value => `<span class="snippet">${{html(value)}}</span>`
        }}
      );
    }}

    function renderRecommendations() {{
      document.getElementById("recommendationCards").innerHTML = dashboardData.recommendations.map(rec => {{
        const nums = rec.numbers;
        const time = rec.timeSignal;
        const evidence = rec.evidenceReviews.map(item => `<li>${{html(item)}}</li>`).join("");
        const actions = rec.actions.map(item => `<li>${{html(item)}}</li>`).join("");
        const metrics = rec.successMetrics.map(item => `<li>${{html(item)}}</li>`).join("");
        return `<article class="recommendation">
          <h3>${{html(rec.aspectLabel)}} <span class="risk ${{html(rec.priority)}}">${{html(rec.priority)}}</span></h3>
          <div class="meta">Time-based trigger: ${{html(rec.timeBasedTrigger)}}</div>
          <div class="meta">${{html(time.previousPeriod)}} -> ${{html(time.currentPeriod)}}: negative share ${{percent(time.previousNegativeShare)}} -> ${{percent(time.currentNegativeShare)}}, negative count change ${{number(time.negativeCountChange)}}.</div>
          <div class="meta">Full-period support: ${{number(nums.negative)}} negative / ${{number(nums.mentions)}} mentions (${{percent(nums.negativeShare)}}); agreement evidence ${{number(nums.negativeAgreement)}}; priority score ${{number(nums.priorityScore)}}.</div>
          <p><b>Problem:</b> ${{html(rec.problem)}}</p>
          <p><b>Interpretation:</b> ${{html(rec.interpretation)}}</p>
          <p><b>Business impact:</b> ${{html(rec.businessImpact)}}</p>
          <p><b>Business conclusion:</b> ${{html(rec.conclusion)}}</p>
          <p><b>Suggested actions:</b></p><ul>${{actions}}</ul>
          <p><b>Success metrics:</b></p><ul>${{metrics}}</ul>
          <p><b>Evidence reviews:</b></p><ul>${{evidence}}</ul>
        </article>`;
      }}).join("");
    }}

    function renderStrategy() {{
      const risks = dashboardData.recommendations.slice(0, 4).map(rec =>
        `<p><b>${{html(rec.aspectLabel)}}</b>: ${{html(rec.timeBasedTrigger)}} Full-period support: ${{number(rec.numbers.negative)}} negative reviews and ${{number(rec.numbers.negativeAgreement)}} agreement points.</p>`
      ).join("");
      const opportunities = [...dashboardData.aspectDistribution]
        .sort((a, b) => b["Positive share"] - a["Positive share"])
        .slice(0, 4)
        .map(row => `<p><b>${{html(row["Aspect label"])}}</b>: ${{number(row.Positive)}} positive reviews (${{percent(row["Positive share"])}} positive share). Use this strength in passenger communication and service planning.</p>`)
        .join("");
      const recs = dashboardData.recommendations.map(rec =>
        `<p><b>${{html(rec.aspectLabel)}}:</b> Time evidence: ${{html(rec.timeBasedTrigger)}} Interpretation: ${{html(rec.interpretation)}} Suggested action: ${{html(rec.actions[0])}}</p>`
      ).join("");
      document.getElementById("riskList").innerHTML = risks;
      document.getElementById("opportunityList").innerHTML = opportunities;
      document.getElementById("executiveRecommendations").innerHTML = recs;
    }}

    function renderTables() {{
      renderSimpleTable(
        "aspectTable",
        ["Aspect label", "Mentions", "Negative", "Neutral", "Positive", "Negative share", "Negative agreement"],
        dashboardData.priority,
        {{
          "Aspect label": value => html(value),
          "Mentions": value => number(value),
          "Negative": value => number(value),
          "Neutral": value => number(value),
          "Positive": value => number(value),
          "Negative share": value => percent(value),
          "Negative agreement": value => number(value)
        }}
      );
      renderSimpleTable(
        "spikeTable",
        ["Period", "Negative reviews", "Negative share", "Spike score"],
        dashboardData.negativeSpikes,
        {{
          "Period": value => html(value),
          "Negative reviews": value => number(value),
          "Negative share": value => percent(value),
          "Spike score": value => number(value)
        }}
      );
      renderSimpleTable(
        "aspectChangeTable",
        ["Aspect label", "Negative share change", "Negative count change", "Current mentions"],
        dashboardData.aspectChanges.slice(0, 5),
        {{
          "Aspect label": value => html(value),
          "Negative share change": value => percent(value),
          "Negative count change": value => number(value),
          "Current mentions": value => number(value)
        }}
      );
      renderSimpleTable(
        "rootCauseTable",
        ["Problem", "Aspect label", "Frequency", "Negative share", "Agreement evidence", "Severity", "Interpretation"],
        dashboardData.rootCauses,
        {{
          "Problem": value => html(value),
          "Aspect label": value => html(value),
          "Frequency": value => number(value),
          "Negative share": value => percent(value),
          "Agreement evidence": value => number(value),
          "Severity": value => `<span class="risk ${{html(value)}}">${{html(value)}}</span>`,
          "Interpretation": value => `<span class="snippet">${{html(value)}}</span>`
        }}
      );
      renderSimpleTable("negativeKeywordTable", ["Keyword", "Count"], dashboardData.negativeKeywords, {{
        "Keyword": value => html(value),
        "Count": value => number(value)
      }});
      renderSimpleTable("positiveKeywordTable", ["Keyword", "Count"], dashboardData.positiveKeywords, {{
        "Keyword": value => html(value),
        "Count": value => number(value)
      }});
      renderSimpleTable("negativeTopicTable", ["Topic", "Keywords", "Weight"], dashboardData.negativeTopics, {{
        "Topic": value => html(value),
        "Keywords": value => `<span class="snippet">${{html(value)}}</span>`,
        "Weight": value => number(value)
      }});
      renderSimpleTable("positiveTopicTable", ["Topic", "Keywords", "Weight"], dashboardData.positiveTopics, {{
        "Topic": value => html(value),
        "Keywords": value => `<span class="snippet">${{html(value)}}</span>`,
        "Weight": value => number(value)
      }});
    }}

    setupTabs();
    setupAspectSelectors();
    setupExplorerFilters();
    renderTables();
    renderRecommendations();
    renderStrategy();

    document.getElementById("overallExplain").textContent =
      `Global sentiment is ${{percent(dashboardData.summary.positive_share)}} positive and ${{percent(dashboardData.summary.negative_share)}} negative across ${{number(dashboardData.summary.filtered_reviews)}} BTS-service reviews.`;
    document.getElementById("priorityExplain").textContent =
      `${{dashboardData.summary.highest_risk_aspect}} is the highest-risk aspect with ${{number(dashboardData.summary.highest_risk_negative)}} negative reviews and ${{percent(dashboardData.summary.highest_risk_negative_share)}} negative share.`;
    document.getElementById("periodExplain").textContent =
      `The data covers ${{dashboardData.summary.date_start}} to ${{dashboardData.summary.date_end}}. The latest period comparison is used to explain whether negative sentiment is rising or falling.`;
    document.getElementById("timeCoverageExplain").textContent = dashboardData.timeCoverage.message;

    charts.sentiment = new Chart(document.getElementById("sentimentChart"), {{
      type: "doughnut",
      data: {{
        labels: dashboardData.sentiment.map(d => d.Sentiment),
        datasets: [{{
          data: dashboardData.sentiment.map(d => d.Reviews),
          backgroundColor: dashboardData.sentiment.map(d => colors[d.Sentiment])
        }}]
      }},
      options: commonOptions
    }});

    charts.priority = new Chart(document.getElementById("priorityChart"), {{
      type: "bar",
      data: {{
        labels: dashboardData.priority.slice(0, 8).map(d => d["Aspect label"]),
        datasets: [{{
          label: "Priority score",
          data: dashboardData.priority.slice(0, 8).map(d => d["Priority score"]),
          backgroundColor: "#2563EB"
        }}]
      }},
      options: {{ ...commonOptions, indexAxis: "y", scales: {{ x: {{ beginAtZero: true }} }} }}
    }});

    charts.nssAspect = new Chart(document.getElementById("nssAspectChart"), {{
      type: "bar",
      data: {{
        labels: dashboardData.nssByAspect.map(d => d["Aspect label"]),
        datasets: [{{
          label: "NSS (%)",
          data: dashboardData.nssByAspect.map(d => d.NSS),
          backgroundColor: dashboardData.nssByAspect.map(d => Number(d.NSS) < 0 ? "#C24132" : Number(d.NSS) < 30 ? "#B7791F" : "#138A63")
        }}]
      }},
      options: {{
        ...commonOptions,
        indexAxis: "y",
        scales: {{ x: {{ min: -100, max: 100 }} }}
      }}
    }});

    charts.overallTrend = makeTrendChart("overallTrendChart", dashboardData.timeSeries.monthly);

    charts.aspectStack = new Chart(document.getElementById("aspectStackChart"), {{
      type: "bar",
      data: {{
        labels: dashboardData.aspectDistribution.map(d => d["Aspect label"]),
        datasets: ["Negative", "Neutral", "Positive"].map(sentiment => ({{
          label: sentiment,
          data: dashboardData.aspectDistribution.map(d => d[sentiment]),
          backgroundColor: colors[sentiment]
        }}))
      }},
      options: {{
        ...commonOptions,
        indexAxis: "y",
        scales: {{ x: {{ stacked: true, beginAtZero: true }}, y: {{ stacked: true }} }}
      }}
    }});

    charts.selectedAspect = new Chart(document.getElementById("selectedAspectChart"), {{
      type: "doughnut",
      data: {{
        labels: ["Negative", "Neutral", "Positive"],
        datasets: [{{ data: [0, 0, 0], backgroundColor: [colors.Negative, colors.Neutral, colors.Positive] }}]
      }},
      options: commonOptions
    }});

    charts.timeTrend = makeTrendChart("timeTrendChart", dashboardData.timeSeries.monthly);
    charts.aspectTrend = makeTrendChart("aspectTrendChart", dashboardData.aspectTrends.monthly[dashboardData.aspectDistribution[0].Aspect] || []);

    charts.source = new Chart(document.getElementById("sourceChart"), {{
      type: "bar",
      data: {{
        labels: dashboardData.sourceBreakdown.map(d => d.Source),
        datasets: ["Negative", "Neutral", "Positive"].map(sentiment => ({{
          label: sentiment,
          data: dashboardData.sourceBreakdown.map(d => d[sentiment]),
          backgroundColor: colors[sentiment]
        }}))
      }},
      options: {{ ...commonOptions, scales: {{ x: {{ stacked: true }}, y: {{ stacked: true, beginAtZero: true }} }} }}
    }});

    charts.line = new Chart(document.getElementById("lineChart"), {{
      type: "bar",
      data: {{
        labels: dashboardData.lineBreakdown.map(d => d["BTS line"]),
        datasets: ["Negative", "Neutral", "Positive"].map(sentiment => ({{
          label: sentiment,
          data: dashboardData.lineBreakdown.map(d => d[sentiment]),
          backgroundColor: colors[sentiment]
        }}))
      }},
      options: {{ ...commonOptions, indexAxis: "y", scales: {{ x: {{ stacked: true, beginAtZero: true }}, y: {{ stacked: true }} }} }}
    }});

    updateSelectedAspect();
    updateTimeViews();
    renderReviews();
  </script>
</body>
</html>
"""


def metric(label: str, value, detail: str) -> str:
    if isinstance(value, (int, float)):
        value = f"{value:,.0f}"
    return (
        f'<div class="metric"><small>{escape(label)}</small>'
        f"<strong>{escape(str(value))}</strong><span>{escape(detail)}</span></div>"
    )


def _json_records(df: pd.DataFrame) -> list[dict]:
    out = df.copy()
    for column in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[column]):
            out[column] = out[column].dt.strftime("%Y-%m-%d")
    return out.to_dict("records")


if __name__ == "__main__":
    main()
