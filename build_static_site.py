from __future__ import annotations

import json
from pathlib import Path

from dashboard_data import (
    DATA_PATH,
    aspect_priority,
    filter_dataset,
    high_agreement_low_rating,
    kpi_summary,
    load_dataset,
    sentiment_distribution,
    sentiment_time_series,
    source_distribution,
)


DOCS_DIR = Path(__file__).with_name("docs")
OUT_PATH = DOCS_DIR / "index.html"


def main() -> None:
    df = load_dataset(DATA_PATH)
    service_df = filter_dataset(df, service_relevant_only=True)

    summary = kpi_summary(service_df, total_rows=len(df))
    sentiment = sentiment_distribution(service_df)
    priority = aspect_priority(service_df).head(10)
    sources = source_distribution(service_df, limit=8)
    trend = sentiment_time_series(service_df, "M")
    if not trend.empty:
        cutoff = trend["Period"].max() - __import__("pandas").DateOffset(months=35)
        trend = trend[trend["Period"].ge(cutoff)]

    complaints = high_agreement_low_rating(
        service_df,
        min_agreement=20,
        max_rating=2,
        limit=12,
    )

    payload = {
        "sentiment": sentiment.to_dict("records"),
        "priority": priority[
            ["Aspect", "Negative", "Positive", "Negative agreement", "Priority score"]
        ].to_dict("records"),
        "sources": sources.to_dict("records"),
        "trend": _json_records(trend),
    }

    DOCS_DIR.mkdir(exist_ok=True)
    OUT_PATH.write_text(render_html(summary, payload, complaints), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


def render_html(summary: dict[str, float], payload: dict, complaints) -> str:
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
      --ink: #101820;
      --muted: #5d6673;
      --line: #d8dee4;
      --teal: #0f4c5c;
      --green: #1f8a70;
      --red: #c43c35;
      --gray: #8a8f98;
      --bg: #f6f8fb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, Segoe UI, Arial, sans-serif;
      margin: 0;
    }}
    header {{
      background: #ffffff;
      border-bottom: 1px solid var(--line);
      padding: 28px max(24px, calc((100vw - 1180px) / 2));
    }}
    header h1 {{
      font-size: clamp(28px, 4vw, 44px);
      letter-spacing: 0;
      margin: 0;
    }}
    header p {{
      color: var(--muted);
      font-size: 17px;
      line-height: 1.5;
      margin: 10px 0 0;
      max-width: 920px;
    }}
    main {{
      display: grid;
      gap: 22px;
      margin: 0 auto;
      max-width: 1180px;
      padding: 24px;
    }}
    .notice, .panel, .metric {{
      background: #ffffff;
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 1px 2px rgba(16, 24, 32, 0.05);
    }}
    .notice {{
      border-left: 5px solid var(--teal);
      color: var(--muted);
      line-height: 1.55;
      padding: 16px 18px;
    }}
    .metrics {{
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(5, minmax(0, 1fr));
    }}
    .metric {{ padding: 16px; }}
    .metric small {{
      color: var(--muted);
      display: block;
      font-size: 12px;
      font-weight: 750;
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }}
    .metric strong {{
      display: block;
      font-size: clamp(24px, 3vw, 34px);
      margin-top: 6px;
    }}
    .grid {{
      display: grid;
      gap: 22px;
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }}
    .panel {{ min-height: 360px; padding: 18px; }}
    .wide {{ grid-column: 1 / -1; }}
    h2 {{ font-size: 20px; margin: 0 0 16px; }}
    canvas {{ max-height: 310px; }}
    table {{
      border-collapse: collapse;
      font-size: 14px;
      width: 100%;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 11px 9px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-size: 12px; text-transform: uppercase; }}
    .snippet {{ color: var(--muted); line-height: 1.45; }}
    .footer {{
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
      text-align: center;
    }}
    @media (max-width: 920px) {{
      .metrics, .grid {{ grid-template-columns: 1fr; }}
      main {{ padding: 16px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>BTS Skytrain Business Intelligence</h1>
    <p>Static GitHub Pages snapshot of the ABSA dashboard. The full interactive Streamlit app is in the same repository and can run in Codespaces or locally.</p>
  </header>
  <main>
    <section class="notice">
      <b>Rating and agreement are decoupled.</b>
      <code>review_rating_num</code> is the 1-5 sentiment-derived rating.
      <code>like_count</code> is shown as agreement count, so a high-upvote complaint stays a complaint.
    </section>
    <section class="metrics">
      {metric("Total reviews", summary["total_reviews"], "Raw CSV rows")}
      {metric("Service reviews", summary["filtered_reviews"], "Default BTS scope")}
      {metric("Average rating", f"{summary['average_rating']:.2f}", "Sentiment stars")}
      {metric("Negative share", f"{summary['negative_share']:.1%}", "Final_Label negative")}
      {metric("Agreement", summary["total_agreement"], "Upvotes/helpful votes")}
    </section>
    <section class="grid">
      <article class="panel"><h2>Overall sentiment</h2><canvas id="sentimentChart"></canvas></article>
      <article class="panel"><h2>Top service priorities</h2><canvas id="priorityChart"></canvas></article>
      <article class="panel wide"><h2>Sentiment over time</h2><canvas id="trendChart"></canvas></article>
      <article class="panel"><h2>Source mix</h2><canvas id="sourceChart"></canvas></article>
      <article class="panel"><h2>Business interpretation</h2>
        <p class="snippet">Priority score = negative review count + 0.1 x negative agreement count. This highlights service aspects that are both frequent and strongly agreed with by passengers.</p>
        <p class="snippet">The top default issues are crowding, fare/payment, infrastructure, and route/connectivity.</p>
      </article>
      <article class="panel wide"><h2>High-agreement low-rating complaints</h2>{complaint_table(complaints)}</article>
    </section>
    <p class="footer">Generated from <code>full_dataset_with_predictions.csv</code>. For full filters and review explorer, run <code>python -m streamlit run app.py</code>.</p>
  </main>
  <script>
    const dashboardData = {json.dumps(payload, ensure_ascii=False)};
    const colors = {{ Negative: "#C43C35", Neutral: "#8A8F98", Positive: "#1F8A70" }};
    const commonOptions = {{ responsive: true, maintainAspectRatio: false, plugins: {{ legend: {{ position: "bottom" }} }} }};

    new Chart(document.getElementById("sentimentChart"), {{
      type: "doughnut",
      data: {{
        labels: dashboardData.sentiment.map(d => d.Sentiment),
        datasets: [{{ data: dashboardData.sentiment.map(d => d.Reviews), backgroundColor: dashboardData.sentiment.map(d => colors[d.Sentiment]) }}]
      }},
      options: commonOptions
    }});

    new Chart(document.getElementById("priorityChart"), {{
      type: "bar",
      data: {{
        labels: dashboardData.priority.map(d => d.Aspect),
        datasets: [{{ label: "Priority score", data: dashboardData.priority.map(d => d["Priority score"]), backgroundColor: "#0F4C5C" }}]
      }},
      options: {{ ...commonOptions, indexAxis: "y" }}
    }});

    const periods = [...new Set(dashboardData.trend.map(d => d.Period))];
    new Chart(document.getElementById("trendChart"), {{
      type: "line",
      data: {{
        labels: periods,
        datasets: ["Negative", "Neutral", "Positive"].map(s => ({{
          label: s,
          data: periods.map(p => (dashboardData.trend.find(d => d.Period === p && d.Sentiment === s) || {{ Reviews: 0 }}).Reviews),
          borderColor: colors[s],
          backgroundColor: colors[s],
          tension: 0.25
        }}))
      }},
      options: commonOptions
    }});

    new Chart(document.getElementById("sourceChart"), {{
      type: "bar",
      data: {{
        labels: dashboardData.sources.map(d => d.Source),
        datasets: [{{ label: "Reviews", data: dashboardData.sources.map(d => d.Reviews), backgroundColor: "#2A9D8F" }}]
      }},
      options: {{ ...commonOptions, indexAxis: "y" }}
    }});
  </script>
</body>
</html>
"""


def metric(label: str, value, detail: str) -> str:
    if isinstance(value, (int, float)):
        value = f"{value:,.0f}"
    return f'<div class="metric"><small>{label}</small><strong>{value}</strong><span>{detail}</span></div>'


def complaint_table(complaints) -> str:
    rows = []
    for _, row in complaints.iterrows():
        rows.append(
            "<tr>"
            f"<td>{escape(str(row['Source']))}</td>"
            f"<td>{int(row['Rating'])}</td>"
            f"<td>{int(row['Agreement count'])}</td>"
            f"<td>{escape(str(row['Primary aspect']))}</td>"
            f"<td class=\"snippet\">{escape(str(row['Review snippet']))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Source</th><th>Rating</th><th>Agreement</th>"
        "<th>Aspect</th><th>Review evidence</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _json_records(df):
    out = df.copy()
    if "Period" in out.columns:
        out["Period"] = out["Period"].dt.strftime("%Y-%m")
    return out.to_dict("records")


def escape(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


if __name__ == "__main__":
    main()
