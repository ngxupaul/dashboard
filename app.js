const CSV_URL = "DATA_QUALITY_CHECKLIST_filled.csv";
const COLORS = {
  Positive: "#168a4a",
  Neutral: "#7a8288",
  Negative: "#c83b33",
  sukhumvit: "#2f9e44",
  silom: "#087f8c",
  grid: "#dfe7e9",
  text: "#182025",
  muted: "#66737c",
};

const state = {
  rows: [],
  filtered: [],
  sortKey: "date",
  sortDir: -1,
  activeTab: "overview",
  filterTimer: null,
};

const $ = (id) => document.getElementById(id);
const fmt = new Intl.NumberFormat("en-US");
const pct = (v, d = 1) => `${Number.isFinite(v) ? v.toFixed(d) : "0.0"}%`;
const nss = (pos, neg, total) => (total ? ((pos - neg) / total) * 100 : 0);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;

  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    const next = text[i + 1];
    if (quoted) {
      if (c === '"' && next === '"') {
        field += '"';
        i += 1;
      } else if (c === '"') {
        quoted = false;
      } else {
        field += c;
      }
    } else if (c === '"') {
      quoted = true;
    } else if (c === ",") {
      row.push(field);
      field = "";
    } else if (c === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (c !== "\r") {
      field += c;
    }
  }
  if (field || row.length) {
    row.push(field);
    rows.push(row);
  }

  const headers = rows.shift().map((h) => h.trim());
  return rows
    .filter((r) => r.length > 1)
    .map((r) => Object.fromEntries(headers.map((h, i) => [h, r[i] ?? ""])));
}

function normalizeLine(value) {
  const raw = String(value || "").trim();
  const lower = raw.toLowerCase();
  if (!raw) return "Unknown";
  if (lower.includes("both") || lower.includes("integrated")) return "Both Sukhumvit + Silom";
  if (lower.includes("sukhumvit")) return "Sukhumvit";
  if (lower.includes("silom")) return "Silom";
  return raw;
}

function isTopicRelevant(text) {
  return /\b(bts|skytrain|sukhumvit|silom|station|stations|train|trains|platform|platforms|fare|ticket|tickets|rabbit card|interchange|escalator|elevator|lift|airport rail link|arl|mrt|transit|transport|commute|siam|asok|on nut|mo chit|chon nonsi|sala daeng|bearing|national stadium|bang wa|saphan taksin|ari|phrom phong|udom suk|phaya thai|ekkamai|thong lor|ha yaek lat phrao|saphan khwai|krung thon buri)\b/i.test(text || "");
}

function isLikelyOffTopic(text) {
  const value = String(text || "");
  const nonServiceMarkers = /\b(restaurant|restaurants|coffee shop|cinema|movie|hotel|condo|apartment|housing|gym|fried chicken|vegetarian|halaal|nightlife|club|bar|beer|food|teacher|dungeons|dragons|clinic|dentist|visa|fruit|boxes|laundry|meal|buffet|neighborhood|neighbourhood|where to stay|accommodation|accommodations)\b/i;
  const serviceMarkers = /\b(crowded|crowding|packed|fare|ticket|rabbit|delay|late|waiting|frequency|broken|dirty|clean|unsafe|security|staff helped|platform|signage|wayfinding|payment machine|escalator|elevator|lift)\b/i;
  return nonServiceMarkers.test(value) && !serviceMarkers.test(value);
}

function cleanRows(rows) {
  return rows.map((r, i) => {
    const dateText = String(r.created_at_date || "").slice(0, 10);
    const time = Date.parse(dateText);
    const confidence = Math.max(0, Math.min(1, Number(r.sentiment_confidence) || 0));
    const rating = Number(r.review_rating) || null;
    const sentiment = r.sentiment_pred || r.sentiment || "Unknown";
    const text = r.review_text || "";
    const likelyOffTopic = isLikelyOffTopic(text);
    return {
      id: i,
      text,
      rating,
      source: r.source || "Unknown",
      dateText,
      date: Number.isFinite(time) ? new Date(time) : null,
      rawLine: String(r.bts_line || "").trim(),
      line: normalizeLine(r.bts_line),
      hometown: r.reviewer_hometown || "",
      aspect: r.aspect_pred || r.aspect || "Unknown",
      sentiment,
      confidence,
      topicRelevant: isTopicRelevant(text),
      likelyOffTopic,
      ratingConflict: Boolean(rating && confidence >= 0.8 && ((rating <= 2 && sentiment === "Positive") || (rating >= 4 && sentiment === "Negative"))),
    };
  });
}

function sentimentCounts(rows) {
  const counts = { Positive: 0, Neutral: 0, Negative: 0 };
  rows.forEach((r) => {
    if (counts[r.sentiment] !== undefined) counts[r.sentiment] += 1;
  });
  return counts;
}

function groupBy(rows, fn) {
  const map = new Map();
  rows.forEach((row) => {
    const key = fn(row);
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(row);
  });
  return map;
}

function timeKey(date, grain) {
  if (!date) return "No date";
  const y = date.getFullYear();
  const m = date.getMonth() + 1;
  if (grain === "day") return date.toISOString().slice(0, 10);
  if (grain === "week") {
    const first = new Date(y, 0, 1);
    const week = Math.ceil((((date - first) / 86400000) + first.getDay() + 1) / 7);
    return `${y}-W${String(week).padStart(2, "0")}`;
  }
  if (grain === "quarter") return `${y}-Q${Math.floor((m - 1) / 3) + 1}`;
  return `${y}-${String(m).padStart(2, "0")}`;
}

function summarize(rows) {
  const counts = sentimentCounts(rows);
  const total = rows.length;
  const aspects = [...groupBy(rows, (r) => r.aspect)].map(([aspect, list]) => {
    const c = sentimentCounts(list);
    return { aspect, total: list.length, ...c, nss: nss(c.Positive, c.Negative, list.length), negRate: list.length ? c.Negative / list.length : 0 };
  }).sort((a, b) => b.total - a.total);
  return {
    total,
    counts,
    nss: nss(counts.Positive, counts.Negative, total),
    positiveRate: total ? (counts.Positive / total) * 100 : 0,
    negativeRate: total ? (counts.Negative / total) * 100 : 0,
    confidence: total ? rows.reduce((s, r) => s + r.confidence, 0) / total : 0,
    aspects,
  };
}

function fillSelect(id, values, allLabel) {
  const el = $(id);
  el.innerHTML = `<option value="">${allLabel}</option>${values.map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join("")}`;
}

function setupFilters() {
  const dated = state.rows.filter((r) => r.date).map((r) => r.dateText).sort();
  $("dateFrom").value = dated[0] || "";
  $("dateTo").value = dated[dated.length - 1] || "";
  fillSelect("lineFilter", ["Sukhumvit", "Silom", "Both Sukhumvit + Silom", "Unknown"], "All BTS reviews");
  fillSelect("aspectFilter", [...new Set(state.rows.map((r) => r.aspect))].sort(), "All aspects");
  fillSelect("sentimentFilter", ["Positive", "Neutral", "Negative"], "All sentiment");
  fillSelect("sourceFilter", [...new Set(state.rows.map((r) => r.source))].sort(), "All sources");
  $("dataScopeFilter").innerHTML = ["Likely BTS service reviews", "Needs manual review", "All rows from CSV"]
    .map((v) => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`)
    .join("");
  $("dataScopeFilter").value = "Likely BTS service reviews";

  ["dateFrom", "dateTo", "lineFilter", "aspectFilter", "sentimentFilter", "sourceFilter", "dataScopeFilter", "grainFilter"].forEach((id) => {
    $(id).addEventListener("change", applyFilters);
  });
  $("confidenceFilter").addEventListener("input", scheduleApplyFilters);
  $("searchInput").addEventListener("input", scheduleApplyFilters);
  $("resetFilters").addEventListener("click", () => {
    $("dateFrom").value = dated[0] || "";
    $("dateTo").value = dated[dated.length - 1] || "";
    $("lineFilter").value = "";
    $("aspectFilter").value = "";
    $("sentimentFilter").value = "";
    $("sourceFilter").value = "";
    $("dataScopeFilter").value = "Likely BTS service reviews";
    $("confidenceFilter").value = "0";
    $("grainFilter").value = "month";
    $("searchInput").value = "";
    applyFilters();
  });
  document.querySelectorAll(".tab").forEach((btn) => btn.addEventListener("click", () => {
    state.activeTab = btn.dataset.tab;
    document.querySelectorAll(".tab").forEach((b) => b.classList.toggle("active", b === btn));
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === state.activeTab));
    render();
  }));
  document.querySelectorAll(".sort-button").forEach((btn) => btn.addEventListener("click", () => {
    const key = btn.dataset.sort;
    if (state.sortKey === key) state.sortDir *= -1;
    else {
      state.sortKey = key;
      state.sortDir = key === "date" || key === "confidence" ? -1 : 1;
    }
    renderReviewTable();
  }));
}

function scheduleApplyFilters() {
  $("confidenceValue").textContent = `${Math.round((Number($("confidenceFilter").value) || 0) * 100)}%`;
  clearTimeout(state.filterTimer);
  state.filterTimer = setTimeout(applyFilters, 180);
}

function applyFilters() {
  const from = $("dateFrom").value ? new Date($("dateFrom").value) : null;
  const to = $("dateTo").value ? new Date($("dateTo").value) : null;
  const line = $("lineFilter").value;
  const aspect = $("aspectFilter").value;
  const sentiment = $("sentimentFilter").value;
  const source = $("sourceFilter").value;
  const dataScope = $("dataScopeFilter").value;
  const minConfidence = Number($("confidenceFilter").value) || 0;
  const search = $("searchInput").value.trim().toLowerCase();
  $("confidenceValue").textContent = `${Math.round(minConfidence * 100)}%`;

  state.filtered = state.rows.filter((r) => {
    if (from && (!r.date || r.date < from)) return false;
    if (to && (!r.date || r.date > to)) return false;
    if (line && r.line !== line) return false;
    if (aspect && r.aspect !== aspect) return false;
    if (sentiment && r.sentiment !== sentiment) return false;
    if (source && r.source !== source) return false;
    if (dataScope === "Likely BTS service reviews" && r.likelyOffTopic) return false;
    if (dataScope === "Needs manual review" && !(r.likelyOffTopic || r.confidence < 0.6 || r.ratingConflict || !r.topicRelevant)) return false;
    if (r.confidence < minConfidence) return false;
    if (search && !r.text.toLowerCase().includes(search)) return false;
    return true;
  });
  render();
}

function timeSeries(rows) {
  const grain = $("grainFilter").value;
  return [...groupBy(rows.filter((r) => r.date), (r) => timeKey(r.date, grain))]
    .map(([period, list]) => {
      const c = sentimentCounts(list);
      return { period, total: list.length, ...c, nss: nss(c.Positive, c.Negative, list.length), negRate: list.length ? c.Negative / list.length : 0 };
    })
    .sort((a, b) => a.period.localeCompare(b.period));
}

function setStatus(type, text) {
  const panel = document.querySelector(".status-panel");
  panel.classList.remove("ready", "error");
  if (type) panel.classList.add(type);
  $("dataStatus").textContent = text;
}

function render() {
  if (state.activeTab === "overview") {
    renderKpis();
    renderOverview();
  } else if (state.activeTab === "trends") {
    renderTrends();
  } else if (state.activeTab === "aspects") {
    renderAspects();
  } else if (state.activeTab === "recommendations") {
    renderRecommendations();
  }
}

function renderKpis() {
  const s = summarize(state.filtered);
  const kpis = [
    ["Total Reviews", fmt.format(s.total), `${fmt.format(s.counts.Positive)} positive, ${fmt.format(s.counts.Negative)} negative`],
    ["Net Sentiment Score", pct(s.nss), nssLabel(s.nss)],
    ["Positive Rate", pct(s.positiveRate), "Share of reviews classified positive"],
    ["Negative Rate", pct(s.negativeRate), "Complaint pressure in current slice"],
    ["Avg. Confidence", pct(s.confidence * 100), "Mean model confidence"],
  ];
  $("kpiGrid").innerHTML = kpis.map(([label, value, note]) => `
    <article class="kpi-card">
      <span class="kpi-label">${label}</span>
      <strong class="kpi-value">${value}</strong>
      <div class="kpi-note">${note}</div>
    </article>
  `).join("");
}

function nssLabel(score) {
  if (score > 50) return "Excellent passenger satisfaction";
  if (score > 20) return "Good service perception";
  if (score >= 0) return "Mixed or neutral service perception";
  return "Service risk: negative experience leads";
}

function renderOverview() {
  const rows = state.filtered;
  const s = summarize(rows);
  renderDonut("sentimentChart", s.counts);
  $("sentimentInsight").textContent = `Current selection contains ${fmt.format(s.total)} reviews. NSS is ${pct(s.nss)}, which indicates ${nssLabel(s.nss).toLowerCase()}.`;
  renderLineChart("nssTrendOverview", timeSeries(rows), [{ key: "nss", label: "NSS", color: COLORS.silom }], -100, 100);
  $("nssOverviewInsight").textContent = trendSentence(timeSeries(rows));
  renderStackedBars("reviewVolumeOverview", timeSeries(rows));
  $("reviewVolumeOverviewInsight").textContent = volumeSentence(timeSeries(rows));
  renderTopSignals(s.aspects);
  renderLineCoverage(rows);
}

window.setFilter = (id, value) => {
  $(id).value = value;
  applyFilters();
};

function renderTopSignals(aspects) {
  const ranked = aspects.filter((a) => a.total >= 5);
  const best = [...ranked].sort((a, b) => b.nss - a.nss)[0];
  const worst = [...ranked].sort((a, b) => a.nss - b.nss)[0];
  const common = ranked[0];
  $("topSignals").innerHTML = [
    signalCard("Strongest Aspect", best, "positive"),
    signalCard("Highest Risk Aspect", worst, "negative"),
    signalCard("Most Discussed Aspect", common, "neutral"),
  ].join("");
}

function signalCard(title, item, tone) {
  if (!item) return `<div class="signal-card">${title}<strong>No data</strong></div>`;
  return `<div class="signal-card">
    <span class="pill ${tone}">${title}</span>
    <strong>${escapeHtml(item.aspect)}</strong>
    <div class="meta-row"><span>${fmt.format(item.total)} reviews</span><span>NSS ${pct(item.nss)}</span></div>
  </div>`;
}

function renderLineCoverage(rows) {
  const items = [...groupBy(rows, (r) => r.line)]
    .map(([line, list]) => {
      const c = sentimentCounts(list);
      return { line, total: list.length, nss: nss(c.Positive, c.Negative, list.length), negativeRate: list.length ? c.Negative / list.length : 0 };
    })
    .sort((a, b) => b.total - a.total);
  $("lineCoverage").innerHTML = items.map((item) => {
    const tone = item.line === "Unknown" ? "negative" : item.line.includes("Both") ? "medium" : "positive";
    return `<div class="signal-card">
      <span class="pill ${tone}">${escapeHtml(item.line)}</span>
      <strong>${fmt.format(item.total)} reviews</strong>
      <div class="meta-row"><span>NSS ${pct(item.nss)}</span><span>${pct(item.negativeRate * 100)} negative</span></div>
    </div>`;
  }).join("") || empty("No line coverage in current filter.");
  const silom = items.find((x) => x.line === "Silom");
  $("lineCoverageInsight").textContent = silom && silom.total < 100
    ? `Silom has only ${fmt.format(silom.total)} reviews in this selection, so line-level conclusions should be treated as directional rather than definitive.`
    : "Unknown and integrated rows are shown separately so line-level comparisons do not hide data coverage issues.";
}

function renderTrends() {
  const series = timeSeries(state.filtered);
  renderLineChart("nssTrend", series, [
    { key: "nss", label: "NSS", color: COLORS.silom },
    { key: "Positive", label: "Positive", color: COLORS.Positive, scale: "count" },
    { key: "Negative", label: "Negative", color: COLORS.Negative, scale: "count" },
  ], -100, 100);
  $("trendInsight").textContent = trendSentence(series);
  renderStackedBars("volumeTrend", series);
  $("volumeInsight").textContent = volumeSentence(series);
  renderAspectTrend();
  renderSpikeCards(series);
}

function renderSpikeCards(series) {
  let worst = null;
  let best = null;
  for (let i = 1; i < series.length; i += 1) {
    const delta = series[i].nss - series[i - 1].nss;
    if (!worst || delta < worst.delta) worst = { ...series[i], delta };
    if (!best || delta > best.delta) best = { ...series[i], delta };
  }
  const peak = [...series].sort((a, b) => b.Negative - a.Negative)[0];
  $("worstDrop").textContent = worst ? `${pct(worst.delta)}` : "-";
  $("worstDropNote").textContent = worst ? `${worst.period} compared with previous period` : "Not enough periods";
  $("complaintPeak").textContent = peak ? peak.period : "-";
  $("complaintPeakNote").textContent = peak ? `${fmt.format(peak.Negative)} negative reviews` : "No negative reviews";
  $("bestRecovery").textContent = best ? `+${pct(best.delta)}` : "-";
  $("bestRecoveryNote").textContent = best ? `${best.period} compared with previous period` : "Not enough periods";
}

function renderAspectTrend() {
  const rows = state.filtered.filter((r) => r.date);
  const topAspects = summarize(rows).aspects.slice(0, 5).map((a) => a.aspect);
  const grain = $("grainFilter").value;
  const periods = [...new Set(rows.map((r) => timeKey(r.date, grain)))].sort();
  const topSet = new Set(topAspects);
  const buckets = new Map();
  rows.forEach((r) => {
    if (!topSet.has(r.aspect)) return;
    const period = timeKey(r.date, grain);
    const key = `${period}|||${r.aspect}`;
    if (!buckets.has(key)) buckets.set(key, { total: 0, Negative: 0 });
    const bucket = buckets.get(key);
    bucket.total += 1;
    if (r.sentiment === "Negative") bucket.Negative += 1;
  });
  const data = periods.map((period) => {
    const item = { period };
    topAspects.forEach((aspect) => {
      const bucket = buckets.get(`${period}|||${aspect}`);
      item[aspect] = bucket?.total ? (bucket.Negative / bucket.total) * 100 : 0;
    });
    return item;
  });
  renderLineChart("aspectTrend", data, topAspects.map((a, i) => ({ key: a, label: a, color: ["#087f8c", "#2f9e44", "#b7791f", "#c83b33", "#4f6272"][i] })), 0, 100);
  const riskiest = summarize(rows).aspects.filter((a) => a.total >= 10).sort((a, b) => b.negRate - a.negRate)[0];
  $("aspectTrendInsight").textContent = riskiest ? `${riskiest.aspect} has the highest negative share among frequent aspects at ${pct(riskiest.negRate * 100)}.` : "No aspect trend is available for this filter.";
}

function renderAspects() {
  const aspects = summarize(state.filtered).aspects.filter((a) => a.total > 0).slice(0, 10);
  renderAspectBars(aspects);
  const worst = [...aspects].sort((a, b) => b.negRate - a.negRate)[0];
  $("aspectInsight").textContent = worst ? `${worst.aspect} is the clearest root-cause candidate, with ${pct(worst.negRate * 100)} negative share across ${fmt.format(worst.total)} reviews.` : "No aspect data is available.";
  renderHeatmap();
  renderAspectEvidence();
  renderNegativeEvidence();
  renderReviewTable();
}

function renderRecommendations() {
  const rows = state.filtered;
  const s = summarize(rows);
  const diagnostics = computeTimeDiagnostics(rows);
  renderTimeDiagnostics(diagnostics);
  const recs = buildRecommendations(rows, s, diagnostics);
  $("recommendationCards").innerHTML = recs.map((r) => `
    <article class="recommendation-card ${r.priority.toLowerCase()}">
      <div class="meta-row"><span class="pill ${r.priority.toLowerCase()}">${r.priority} priority</span><span>${escapeHtml(r.period)}</span></div>
      <h3>${escapeHtml(r.title)}</h3>
      <dl>
        <div><dt>Problem</dt><dd>${escapeHtml(r.problem)}</dd></div>
        <div><dt>Evidence</dt><dd>${escapeHtml(r.evidence)}</dd></div>
        <div><dt>Strategic action</dt><dd>${escapeHtml(r.action)}</dd></div>
        <div><dt>Expected impact</dt><dd>${escapeHtml(r.impact)}</dd></div>
      </dl>
    </article>
  `).join("") || empty("No recommendation can be generated for this filter.");
  $("contextSummary").innerHTML = `
    <div class="context-item"><span class="kpi-label">Selected Reviews</span><strong>${fmt.format(s.total)}</strong></div>
    <div class="context-item"><span class="kpi-label">NSS</span><strong>${pct(s.nss)}</strong><small>${nssLabel(s.nss)}</small></div>
    <div class="context-item"><span class="kpi-label">Negative Reviews</span><strong>${fmt.format(s.counts.Negative)}</strong><small>${pct(s.negativeRate)} of selected reviews</small></div>
    <div class="context-item"><span class="kpi-label">Date Range</span><strong>${escapeHtml($("dateFrom").value || "Start")} to ${escapeHtml($("dateTo").value || "End")}</strong></div>
    <div class="context-item"><span class="kpi-label">Time Grain</span><strong>${escapeHtml($("grainFilter").selectedOptions[0]?.textContent || "Monthly")}</strong><small>Recommendations compare periods at this grain.</small></div>
  `;
}

function computeTimeDiagnostics(rows) {
  const series = timeSeries(rows);
  const minVolume = Math.max(10, Math.round(rows.length * 0.005));
  const comparable = series.filter((p) => p.total >= minVolume);
  let worstDrop = null;
  let bestRecovery = null;
  for (let i = 1; i < comparable.length; i += 1) {
    const delta = comparable[i].nss - comparable[i - 1].nss;
    const item = { current: comparable[i], previous: comparable[i - 1], delta };
    if (!worstDrop || delta < worstDrop.delta) worstDrop = item;
    if (!bestRecovery || delta > bestRecovery.delta) bestRecovery = item;
  }
  const latest = series[series.length - 1] || null;
  const previous = series[series.length - 2] || null;
  const latestDelta = latest && previous ? latest.nss - previous.nss : 0;
  const complaintPeak = [...comparable].sort((a, b) => b.Negative - a.Negative)[0] || [...series].sort((a, b) => b.Negative - a.Negative)[0] || null;
  const aspectSpike = computeAspectSpike(rows, minVolume);
  return { series, comparable, minVolume, latest, previous, latestDelta, worstDrop, bestRecovery, complaintPeak, aspectSpike };
}

function computeAspectSpike(rows, minVolume) {
  const grain = $("grainFilter").value;
  const dated = rows.filter((r) => r.date);
  const periods = [...new Set(dated.map((r) => timeKey(r.date, grain)))].sort();
  if (periods.length < 2) return null;
  const latest = periods[periods.length - 1];
  const previous = periods[periods.length - 2];
  const buckets = new Map();
  dated.forEach((r) => {
    const period = timeKey(r.date, grain);
    if (period !== latest && period !== previous) return;
    const key = `${period}|||${r.aspect}`;
    if (!buckets.has(key)) buckets.set(key, { total: 0, Negative: 0 });
    const bucket = buckets.get(key);
    bucket.total += 1;
    if (r.sentiment === "Negative") bucket.Negative += 1;
  });
  const aspects = [...new Set([...buckets.keys()].map((key) => key.split("|||")[1]))];
  const aspectMin = Math.max(5, Math.round(minVolume * 0.2));
  return aspects.map((aspect) => {
    const now = buckets.get(`${latest}|||${aspect}`) || { total: 0, Negative: 0 };
    const before = buckets.get(`${previous}|||${aspect}`) || { total: 0, Negative: 0 };
    const nowRate = now.total ? now.Negative / now.total : 0;
    const beforeRate = before.total ? before.Negative / before.total : 0;
    return {
      aspect,
      latest,
      previous,
      latestTotal: now.total,
      previousTotal: before.total,
      latestNegative: now.Negative,
      previousNegative: before.Negative,
      rateDelta: nowRate - beforeRate,
      countDelta: now.Negative - before.Negative,
      latestRate: nowRate,
    };
  }).filter((x) => x.latestTotal >= aspectMin || x.previousTotal >= aspectMin)
    .sort((a, b) => (b.rateDelta * 100 + b.countDelta) - (a.rateDelta * 100 + a.countDelta))[0] || null;
}

function renderTimeDiagnostics(d) {
  $("timeDiagnostics").innerHTML = [
    {
      label: "Latest Period Movement",
      value: d.latest && d.previous ? `${d.previous.period} -> ${d.latest.period}` : "Not enough periods",
      note: d.latest && d.previous ? `NSS changed ${d.latestDelta >= 0 ? "+" : ""}${pct(d.latestDelta)}; latest negative reviews: ${fmt.format(d.latest.Negative)}.${d.previous.total < d.minVolume ? ` Previous period has low volume (${fmt.format(d.previous.total)} reviews), so confirm with review evidence.` : ""}` : "Select a wider date range.",
    },
    {
      label: "Worst Time Drop",
      value: d.worstDrop ? `${pct(d.worstDrop.delta)}` : "-",
      note: d.worstDrop ? `${d.worstDrop.previous.period} -> ${d.worstDrop.current.period}; NSS fell from ${pct(d.worstDrop.previous.nss)} to ${pct(d.worstDrop.current.nss)}. Periods below ${fmt.format(d.minVolume)} reviews are excluded.` : `No comparable drop found after excluding periods below ${fmt.format(d.minVolume)} reviews.`,
    },
    {
      label: "Complaint Peak",
      value: d.complaintPeak ? d.complaintPeak.period : "-",
      note: d.complaintPeak ? `${fmt.format(d.complaintPeak.Negative)} negative reviews; ${pct(d.complaintPeak.negRate * 100)} negative share.` : "No complaint period found.",
    },
    {
      label: "Aspect Spike",
      value: d.aspectSpike ? d.aspectSpike.aspect : "-",
      note: d.aspectSpike ? `${d.aspectSpike.previous} -> ${d.aspectSpike.latest}: negative share changed ${d.aspectSpike.rateDelta >= 0 ? "+" : ""}${pct(d.aspectSpike.rateDelta * 100)}.` : "No aspect-level spike found.",
    },
  ].map((x) => `<div class="diagnostic-card"><span>${x.label}</span><strong>${escapeHtml(x.value)}</strong><small>${escapeHtml(x.note)}</small></div>`).join("");
}

function buildRecommendations(rows, s, diagnostics) {
  if (!rows.length) return [];
  const period = `${$("dateFrom").value || "start"} to ${$("dateTo").value || "end"}`;
  const frequent = s.aspects.filter((a) => a.total >= Math.max(5, s.total * 0.01));
  const worst = [...frequent].sort((a, b) => b.negRate - a.negRate)[0] || s.aspects[0];
  const line = [...groupBy(rows, (r) => r.line)].map(([name, list]) => {
    const c = sentimentCounts(list);
    return { name, total: list.length, nss: nss(c.Positive, c.Negative, list.length) };
  }).filter((x) => x.name !== "Unknown").sort((a, b) => a.nss - b.nss)[0];
  const recs = [];
  if (diagnostics.latest && diagnostics.previous && diagnostics.latestDelta < -10) {
    const lowBaseline = diagnostics.previous.total < diagnostics.minVolume;
    const priority = !lowBaseline && (diagnostics.latestDelta < -25 || diagnostics.latest.nss < 0) ? "High" : "Medium";
    recs.push({
      priority,
      period,
      title: `Investigate latest NSS decline in ${diagnostics.latest.period}`,
      problem: `The latest ${$("grainFilter").selectedOptions[0]?.textContent.toLowerCase()} period deteriorated compared with the previous period.`,
      evidence: `NSS moved from ${pct(diagnostics.previous.nss)} in ${diagnostics.previous.period} to ${pct(diagnostics.latest.nss)} in ${diagnostics.latest.period}, a ${pct(diagnostics.latestDelta)} change. Negative reviews in the latest period: ${fmt.format(diagnostics.latest.Negative)}.${lowBaseline ? ` Previous period has only ${fmt.format(diagnostics.previous.total)} reviews, so treat the movement as a warning signal and validate with review text.` : ""}`,
      action: "Check operational logs, crowding conditions, delay notices, ticketing issues, and station-level communication during the latest period, then validate with the representative reviews table.",
      impact: "Turns the dashboard into an early-warning monitor and focuses action on the period where sentiment changed.",
    });
  }
  if (diagnostics.aspectSpike && (diagnostics.aspectSpike.rateDelta > 0.08 || diagnostics.aspectSpike.countDelta > 10)) {
    const x = diagnostics.aspectSpike;
    recs.push({
      priority: x.rateDelta > 0.2 || x.countDelta > 30 ? "High" : "Medium",
      period,
      title: `Time-based spike in ${x.aspect}`,
      problem: `${x.aspect} worsened from ${x.previous} to ${x.latest}.`,
      evidence: `Negative share changed ${x.rateDelta >= 0 ? "+" : ""}${pct(x.rateDelta * 100)} and negative review count changed ${x.countDelta >= 0 ? "+" : ""}${fmt.format(x.countDelta)}.`,
      action: actionForAspect(x.aspect),
      impact: "Targets the aspect that changed most recently, rather than only the aspect with the largest historical volume.",
    });
  }
  if (diagnostics.complaintPeak && diagnostics.complaintPeak.Negative > Math.max(20, s.counts.Negative * 0.08)) {
    recs.push({
      priority: diagnostics.complaintPeak.nss < 0 ? "High" : "Medium",
      period,
      title: `Complaint peak review: ${diagnostics.complaintPeak.period}`,
      problem: "One time period concentrates a large share of negative passenger feedback.",
      evidence: `${diagnostics.complaintPeak.period} has ${fmt.format(diagnostics.complaintPeak.Negative)} negative reviews and NSS ${pct(diagnostics.complaintPeak.nss)}.`,
      action: "Use this period as the first drill-down window; filter reviews to identify whether complaints mention crowding, fares, staff, reliability, or navigation.",
      impact: "Helps examiners see a clear time-based decision path from chart movement to operational action.",
    });
  }
  if (s.nss < 0 || s.negativeRate > 30) {
    recs.push({
      priority: "High",
      period,
      title: "Current selected range remains service-risk",
      problem: `Negative sentiment is materially high across the selected range.`,
      evidence: `Overall NSS is ${pct(s.nss)} with ${fmt.format(s.counts.Negative)} negative reviews out of ${fmt.format(s.total)} total reviews.`,
      action: "Use the time diagnostics above to isolate the period that caused the weak range-level result, then assign the dominant aspect to the responsible operations team.",
      impact: "Connects broad dissatisfaction to a concrete period and aspect for management follow-up.",
    });
  }
  if (worst) {
    const priority = worst.negRate > 0.35 ? "High" : worst.negRate > 0.2 ? "Medium" : "Low";
    recs.push({
      priority,
      period,
      title: `${worst.aspect} requires targeted follow-up`,
      problem: `${worst.aspect} has the highest complaint concentration among visible aspects.`,
      evidence: `${fmt.format(worst.Negative)} negative reviews from ${fmt.format(worst.total)} aspect mentions; negative share is ${pct(worst.negRate * 100)}. Use this after checking the time-based spike cards above.`,
      action: `${actionForAspect(worst.aspect)} Prioritize periods where this aspect worsens against the previous period.`,
      impact: "Focuses management effort on the most visible passenger pain point instead of treating all complaints equally.",
    });
  }
  if (line && line.name !== "Unknown") {
    recs.push({
      priority: line.nss < 0 ? "High" : "Medium",
      period,
      title: `Line-specific review for ${line.name}`,
      problem: `${line.name} has the weakest line-level NSS in the current selection.`,
      evidence: `${line.name} records NSS ${pct(line.nss)} across ${fmt.format(line.total)} reviews in the selected date range.`,
      action: "Compare this line period-by-period with the stronger line by station access, train frequency, interchange clarity, and peak-hour congestion.",
      impact: "Supports line-level service planning for Sukhumvit and Silom instead of a single system-wide action.",
    });
  }
  if (s.confidence < 0.75) {
    recs.push({
      priority: "Medium",
      period,
      title: "Validate lower-confidence insight slice",
      problem: "Average model confidence is lower than the desired analysis threshold.",
      evidence: `Average confidence is ${pct(s.confidence * 100)} in the selected reviews.`,
      action: "Manually audit representative reviews before using this slice for management decisions.",
      impact: "Improves reliability of aspect and sentiment conclusions used in reporting.",
    });
  }
  return recs.slice(0, 5);
}

function actionForAspect(aspect) {
  const a = aspect.toLowerCase();
  if (a.includes("crowd") || a.includes("comfort")) return "Review peak-hour train frequency, platform flow, and passenger announcements for crowded stations.";
  if (a.includes("fare") || a.includes("payment")) return "Improve ticketing instructions, fare transparency, and payment failure support at stations.";
  if (a.includes("navigation") || a.includes("route")) return "Audit wayfinding signs, interchange instructions, and English-language route information.";
  if (a.includes("punctual") || a.includes("reliability")) return "Investigate timetable adherence, delay communication, and service recovery procedures.";
  if (a.includes("clean")) return "Increase cleaning checks at high-traffic stations and monitor hygiene complaints by period.";
  if (a.includes("staff")) return "Review frontline assistance quality and standardize passenger support training.";
  if (a.includes("safe")) return "Check station safety messaging, crowd control, and incident-response communication.";
  return "Inspect related review evidence and assign the issue to the responsible operations team.";
}

function renderDonut(id, counts) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  if (!total) return void ($(id).innerHTML = empty("No sentiment data."));
  let acc = 0;
  const cx = 170, cy = 140, r = 92, sw = 34;
  const paths = ["Positive", "Neutral", "Negative"].map((key) => {
    const value = counts[key];
    const start = (acc / total) * Math.PI * 2 - Math.PI / 2;
    acc += value;
    const end = (acc / total) * Math.PI * 2 - Math.PI / 2;
    return `<path d="${arc(cx, cy, r, start, end)}" fill="none" stroke="${COLORS[key]}" stroke-width="${sw}" data-tip="${key}: ${fmt.format(value)} reviews (${pct(value / total * 100)})"></path>`;
  }).join("");
  $(id).innerHTML = `<svg viewBox="0 0 520 300" role="img">
    ${paths}
    <text x="${cx}" y="${cy - 5}" text-anchor="middle" class="chart-title-small">${fmt.format(total)}</text>
    <text x="${cx}" y="${cy + 16}" text-anchor="middle" class="axis-label">reviews</text>
    ${["Positive", "Neutral", "Negative"].map((k, i) => `<circle cx="330" cy="${92 + i * 34}" r="6" fill="${COLORS[k]}"></circle><text x="346" y="${96 + i * 34}" class="axis-label">${k}: ${fmt.format(counts[k])}</text>`).join("")}
  </svg>`;
  attachTips($(id));
}

function arc(cx, cy, r, start, end) {
  const sx = cx + r * Math.cos(start), sy = cy + r * Math.sin(start);
  const ex = cx + r * Math.cos(end), ey = cy + r * Math.sin(end);
  const large = end - start > Math.PI ? 1 : 0;
  return `M ${sx} ${sy} A ${r} ${r} 0 ${large} 1 ${ex} ${ey}`;
}

function renderLineChart(id, data, lines, minYArg, maxYArg) {
  if (!data.length) return void ($(id).innerHTML = empty("No time data for this filter."));
  const width = 920, height = 360, p = { l: 56, r: 20, t: 28, b: 58 };
  const countMax = Math.max(1, ...data.flatMap((d) => lines.filter((l) => l.scale === "count").map((l) => d[l.key] || 0)));
  const yMin = minYArg ?? Math.min(0, ...data.flatMap((d) => lines.map((l) => d[l.key] || 0)));
  const yMax = maxYArg ?? Math.max(1, ...data.flatMap((d) => lines.map((l) => d[l.key] || 0)));
  const x = (i) => p.l + (data.length === 1 ? 0.5 : i / (data.length - 1)) * (width - p.l - p.r);
  const y = (v, line) => {
    const scaled = line.scale === "count" ? (v / countMax) * (yMax - yMin) + yMin : v;
    return height - p.b - ((scaled - yMin) / (yMax - yMin || 1)) * (height - p.t - p.b);
  };
  const grid = [0, 0.25, 0.5, 0.75, 1].map((g) => {
    const yy = p.t + g * (height - p.t - p.b);
    return `<line x1="${p.l}" x2="${width - p.r}" y1="${yy}" y2="${yy}" stroke="${COLORS.grid}"></line>`;
  }).join("");
  const paths = lines.map((line) => {
    const d = data.map((row, i) => `${i ? "L" : "M"} ${x(i)} ${y(row[line.key] || 0, line)}`).join(" ");
    const dots = data.map((row, i) => `<circle cx="${x(i)}" cy="${y(row[line.key] || 0, line)}" r="3" fill="${line.color}" data-tip="${escapeHtml(line.label)} | ${row.period}: ${line.scale === "count" ? fmt.format(row[line.key] || 0) : pct(row[line.key] || 0)}"></circle>`).join("");
    return `<path d="${d}" fill="none" stroke="${line.color}" stroke-width="2.5"></path>${dots}`;
  }).join("");
  const tickEvery = Math.max(1, Math.ceil(data.length / 8));
  const xLabels = data.map((d, i) => i % tickEvery === 0 ? `<text x="${x(i)}" y="${height - 25}" text-anchor="middle" class="axis-label">${escapeHtml(d.period)}</text>` : "").join("");
  const legend = lines.map((l, i) => `<circle cx="${p.l + i * 155}" cy="16" r="5" fill="${l.color}"></circle><text x="${p.l + 10 + i * 155}" y="20" class="axis-label">${escapeHtml(l.label)}</text>`).join("");
  $(id).innerHTML = `<svg viewBox="0 0 ${width} ${height}">${legend}${grid}<line x1="${p.l}" x2="${p.l}" y1="${p.t}" y2="${height - p.b}" stroke="${COLORS.grid}"></line><line x1="${p.l}" x2="${width - p.r}" y1="${height - p.b}" y2="${height - p.b}" stroke="${COLORS.grid}"></line>${paths}${xLabels}<text x="8" y="34" class="axis-label">${pct(yMax, 0)}</text><text x="8" y="${height - p.b}" class="axis-label">${pct(yMin, 0)}</text></svg>`;
  attachTips($(id));
}

function renderStackedBars(id, data) {
  if (!data.length) return void ($(id).innerHTML = empty("No volume data for this filter."));
  const width = 760, height = 360, p = { l: 46, r: 18, t: 28, b: 58 };
  const max = Math.max(1, ...data.map((d) => d.total));
  const barW = Math.max(5, (width - p.l - p.r) / data.length - 2);
  const x = (i) => p.l + i * ((width - p.l - p.r) / data.length);
  const y = (v) => height - p.b - (v / max) * (height - p.t - p.b);
  const bars = data.map((d, i) => {
    let base = height - p.b;
    return ["Negative", "Neutral", "Positive"].map((k) => {
      const h = base - y(d[k]);
      base -= h;
      return `<rect x="${x(i)}" y="${base}" width="${barW}" height="${Math.max(0, h)}" fill="${COLORS[k]}" data-tip="${d.period} ${k}: ${fmt.format(d[k])}"></rect>`;
    }).join("");
  }).join("");
  const tickEvery = Math.max(1, Math.ceil(data.length / 7));
  const labels = data.map((d, i) => i % tickEvery === 0 ? `<text x="${x(i)}" y="${height - 25}" text-anchor="middle" class="axis-label">${escapeHtml(d.period)}</text>` : "").join("");
  $(id).innerHTML = `<svg viewBox="0 0 ${width} ${height}"><line x1="${p.l}" x2="${p.l}" y1="${p.t}" y2="${height - p.b}" stroke="${COLORS.grid}"></line><line x1="${p.l}" x2="${width - p.r}" y1="${height - p.b}" y2="${height - p.b}" stroke="${COLORS.grid}"></line>${bars}${labels}</svg>`;
  attachTips($(id));
}

function renderAspectBars(aspects) {
  if (!aspects.length) return void ($("aspectBars").innerHTML = empty("No aspect data for this filter."));
  const width = 820, rowH = 34, p = { l: 230, r: 28, t: 18, b: 20 };
  const height = p.t + p.b + aspects.length * rowH;
  const max = Math.max(1, ...aspects.map((a) => a.total));
  const rows = aspects.map((a, i) => {
    const y = p.t + i * rowH;
    const full = (a.total / max) * (width - p.l - p.r);
    const posW = full * (a.Positive / a.total || 0);
    const neuW = full * (a.Neutral / a.total || 0);
    const negW = full * (a.Negative / a.total || 0);
    return `<text x="8" y="${y + 20}" class="axis-label">${escapeHtml(a.aspect)}</text>
      <rect x="${p.l}" y="${y + 6}" width="${posW}" height="18" fill="${COLORS.Positive}" data-tip="${escapeHtml(a.aspect)} Positive: ${fmt.format(a.Positive)}"></rect>
      <rect x="${p.l + posW}" y="${y + 6}" width="${neuW}" height="18" fill="${COLORS.Neutral}" data-tip="${escapeHtml(a.aspect)} Neutral: ${fmt.format(a.Neutral)}"></rect>
      <rect x="${p.l + posW + neuW}" y="${y + 6}" width="${negW}" height="18" fill="${COLORS.Negative}" data-tip="${escapeHtml(a.aspect)} Negative: ${fmt.format(a.Negative)}"></rect>
      <text x="${p.l + full + 8}" y="${y + 20}" class="axis-label">NSS ${pct(a.nss, 0)}</text>`;
  }).join("");
  $("aspectBars").innerHTML = `<svg viewBox="0 0 ${width} ${height}">${rows}</svg>`;
  attachTips($("aspectBars"));
}

function renderHeatmap() {
  const rows = state.filtered.filter((r) => r.date);
  const grain = $("grainFilter").value;
  const aspects = summarize(rows).aspects.slice(0, 7).map((a) => a.aspect);
  const periods = [...new Set(rows.map((r) => timeKey(r.date, grain)))].sort().slice(-8);
  if (!aspects.length || !periods.length) return void ($("heatmap").innerHTML = empty("No heatmap data."));
  $("heatmap").style.setProperty("--cols", periods.length);
  const header = `<div class="heatmap-row"><div></div>${periods.map((p) => `<div class="heatmap-label">${escapeHtml(p)}</div>`).join("")}</div>`;
  const body = aspects.map((aspect) => `<div class="heatmap-row"><div class="heatmap-label">${escapeHtml(aspect)}</div>${periods.map((period) => {
    const list = rows.filter((r) => r.aspect === aspect && timeKey(r.date, grain) === period);
    const c = sentimentCounts(list);
    const rate = list.length ? c.Negative / list.length : 0;
    const color = `rgba(200, 59, 51, ${0.16 + rate * 0.84})`;
    return `<div class="heatmap-cell" style="background:${color}" title="${escapeHtml(aspect)} ${period}">${pct(rate * 100, 0)}</div>`;
  }).join("")}</div>`).join("");
  $("heatmap").innerHTML = header + body;
  $("heatmapInsight").textContent = "Darker cells show periods where an aspect has a higher negative review share.";
}

function renderAspectEvidence() {
  const items = summarize(state.filtered).aspects
    .filter((a) => a.total >= 5)
    .sort((a, b) => b.negRate - a.negRate)
    .slice(0, 8);
  $("aspectEvidence").innerHTML = items.map((a) => `
    <div class="evidence-item">
      <button type="button" onclick="setFilter('aspectFilter','${escapeHtml(a.aspect)}')">${escapeHtml(a.aspect)}</button>
      <div class="meta-row"><span>${fmt.format(a.total)} reviews</span><span>NSS ${pct(a.nss)}</span></div>
      <small>${fmt.format(a.Negative)} negative, ${fmt.format(a.Neutral)} neutral, ${fmt.format(a.Positive)} positive. Negative share: ${pct(a.negRate * 100)}.</small>
    </div>
  `).join("") || empty("No aspect evidence available.");
}

function renderNegativeEvidence() {
  const riskyAspects = summarize(state.filtered).aspects
    .filter((a) => a.total >= 5)
    .sort((a, b) => b.negRate - a.negRate)
    .slice(0, 3)
    .map((a) => a.aspect);
  const reviews = state.filtered
    .filter((r) => r.sentiment === "Negative" && riskyAspects.includes(r.aspect))
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 8);
  $("negativeEvidence").innerHTML = reviews.map((r) => `
    <div class="evidence-item">
      <div class="meta-row"><span>${escapeHtml(r.dateText || "No date")} | ${escapeHtml(r.line)}</span><span>${pct(r.confidence * 100, 0)} confidence</span></div>
      <strong>${escapeHtml(r.aspect)}</strong>
      <p>${escapeHtml(r.text.slice(0, 260))}${r.text.length > 260 ? "..." : ""}</p>
      <small>Source: ${escapeHtml(r.source)}${r.rating ? ` | Rating: ${escapeHtml(r.rating)}` : ""}</small>
    </div>
  `).join("") || empty("No high-confidence negative review evidence for this filter.");
}

function renderWords(id, sentiment) {
  const stop = new Set("the and for with that this from have are was were you your bts skytrain bangkok station stations train trains line lines very just can will not but they them our out about there their more when what where into also only some much many would could should".split(" "));
  const counts = new Map();
  state.filtered.filter((r) => r.sentiment === sentiment).forEach((r) => {
    (r.text.toLowerCase().match(/[a-z][a-z]{2,}/g) || []).forEach((w) => {
      if (!stop.has(w)) counts.set(w, (counts.get(w) || 0) + 1);
    });
  });
  const words = [...counts].sort((a, b) => b[1] - a[1]).slice(0, 32);
  $(id).innerHTML = words.map(([w, c]) => `<span class="word" style="font-size:${Math.min(1.35, 0.78 + c / Math.max(20, words[0]?.[1] || 1))}rem">${escapeHtml(w)} <small>${c}</small></span>`).join("") || empty(`No ${sentiment.toLowerCase()} keywords.`);
}

function renderReviewTable() {
  const rows = [...state.filtered].sort((a, b) => {
    const dir = state.sortDir;
    if (state.sortKey === "date") return dir * ((a.date?.getTime() || 0) - (b.date?.getTime() || 0));
    if (state.sortKey === "confidence") return dir * (a.confidence - b.confidence);
    return dir * String(a[state.sortKey] || "").localeCompare(String(b[state.sortKey] || ""));
  }).slice(0, 150);
  $("tableMeta").textContent = `Showing ${fmt.format(rows.length)} of ${fmt.format(state.filtered.length)} filtered reviews`;
  $("reviewTable").innerHTML = rows.map((r) => `<tr>
    <td>${escapeHtml(r.dateText || "-")}</td>
    <td>${escapeHtml(r.line)}</td>
    <td><button class="sort-button" onclick="setFilter('aspectFilter','${escapeHtml(r.aspect)}')" type="button">${escapeHtml(r.aspect)}</button></td>
    <td><span class="pill ${r.sentiment.toLowerCase()}">${escapeHtml(r.sentiment)}</span></td>
    <td>${pct(r.confidence * 100, 0)}</td>
    <td><div class="review-text">${escapeHtml(r.text.slice(0, 420))}${r.text.length > 420 ? "..." : ""}</div></td>
  </tr>`).join("") || `<tr><td colspan="6">${empty("No reviews match the current filters.")}</td></tr>`;
}

function trendSentence(series) {
  if (series.length < 2) return "Not enough dated periods to describe movement.";
  const first = series[0], last = series[series.length - 1];
  const delta = last.nss - first.nss;
  const direction = delta >= 0 ? "improved" : "declined";
  return `NSS ${direction} by ${pct(Math.abs(delta))} from ${first.period} to ${last.period}. Latest period NSS is ${pct(last.nss)} with ${fmt.format(last.total)} reviews.`;
}

function volumeSentence(series) {
  if (!series.length) return "No volume movement is available.";
  const peak = [...series].sort((a, b) => b.total - a.total)[0];
  const neg = [...series].sort((a, b) => b.Negative - a.Negative)[0];
  return `${peak.period} has the highest total review volume (${fmt.format(peak.total)}). Complaint volume peaks in ${neg.period} with ${fmt.format(neg.Negative)} negative reviews.`;
}

function empty(text) {
  return `<div class="empty-state">${escapeHtml(text)}</div>`;
}

let tooltip;
function attachTips(root) {
  root.querySelectorAll("[data-tip]").forEach((el) => {
    el.addEventListener("mousemove", (event) => {
      if (!tooltip) {
        tooltip = document.createElement("div");
        tooltip.className = "tooltip";
        document.body.appendChild(tooltip);
      }
      tooltip.innerHTML = escapeHtml(el.dataset.tip);
      tooltip.style.left = `${event.clientX + 12}px`;
      tooltip.style.top = `${event.clientY + 12}px`;
    });
    el.addEventListener("mouseleave", () => {
      tooltip?.remove();
      tooltip = null;
    });
  });
}

async function loadCsv() {
  try {
    const res = await fetch(CSV_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const text = await res.text();
    state.rows = cleanRows(parseCsv(text));
    setStatus("ready", `${fmt.format(state.rows.length)} reviews loaded`);
    setupFilters();
    applyFilters();
  } catch (err) {
    setStatus("error", "Manual CSV needed");
    $("fallbackLoader").classList.remove("hidden");
    $("manualCsv").addEventListener("change", async (event) => {
      const file = event.target.files[0];
      if (!file) return;
      state.rows = cleanRows(parseCsv(await file.text()));
      setStatus("ready", `${fmt.format(state.rows.length)} reviews loaded`);
      $("fallbackLoader").classList.add("hidden");
      setupFilters();
      applyFilters();
    }, { once: true });
  }
}

loadCsv();
