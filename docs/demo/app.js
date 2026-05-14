// Demo dashboard logic (#59).
//
// Fetches data files cross-origin from the `data` branch via
// raw.githubusercontent.com. The branch is updated by the
// demo-snapshot.yml (weekly) and fear-greed.yaml (daily) workflows,
// which commit verified API commits to a branch outside the
// default-branch ruleset's scope.

const DATA_BASE_URL =
  "https://raw.githubusercontent.com/qte77/analyze-stock-kpi/data";
const UNIVERSE = "qte77-watchlist";

const RATING_CLASSES = {
  "extreme fear": "rating-extreme-fear",
  "fear": "rating-fear",
  "neutral": "rating-neutral",
  "greed": "rating-greed",
  "extreme greed": "rating-extreme-greed",
};

const state = {
  snapshot: [],
  sortKey: "composite_scores.screener_score",
  sortDir: -1,
};

// English glossary for detail-panel tooltips (title= attributes on labels).
const KPI_GLOSSARY = {
  forward_pe: "Forward P/E = price / next-12mo EPS estimate. Lower = cheaper.",
  trailing_pe: "Trailing P/E = price / past-12mo EPS. Lower = cheaper.",
  trail_fwd_pe:
    "Trailing P/E divided by Forward P/E. >1 = EPS growth expected; <1 = EPS contraction expected.",
  trailing_peg_ratio:
    "Trailing PEG = P/E adjusted for historical earnings growth. Lower better; <1 is the classic Peter Lynch threshold.",
  beta: "5y market sensitivity. <1 = less volatile than market.",
  rd_to_revenue:
    "R&D expense / total revenue (latest annual income statement). EQUITY-only.",
  operating_margins:
    "Operating income / revenue. Pre-tax, pre-interest — comparable across countries.",
  gross_margins: "(Revenue - COGS) / revenue. Pricing power / cost discipline.",
  profit_margins:
    "Net margin = net income / revenue. Bottom-line efficiency after tax + interest.",
  return_on_equity:
    "ROE = net income / equity. Profitability per equity dollar; sensitive to leverage.",
  return_on_assets:
    "ROA = net income / total assets. Leverage-neutral profitability per asset dollar.",
  roi:
    "Simplified ROIC = NetIncome / (BookEquity + TotalDebt - TotalCash). Screener-style; not company-filed ROIC.",
  current_ratio:
    "Current assets / current liabilities. Short-term liquidity (>1 = assets cover liabilities).",
  quick_ratio:
    "(Current assets - inventory) / current liabilities. Stricter liquidity than Current.",
  debt_to_equity: "Total debt / equity. Leverage (higher = more leveraged).",
  sortino_ratio:
    "Annualized Sortino over 1y (rf=0). Higher = better upside vs downside skew.",
  screener_score:
    "Composite of the 9 visible main-table KPIs (0-100). Higher = better.",
  quality:
    "Mean of normalized ROE, ROA, operating margin, and inverted D/E. Higher = stronger fundamentals.",
  dividend:
    "Dividend yield + payout-ratio sweet spot (peaks near ~50% payout). Higher = healthier dividend profile.",
  growth:
    "Mean of normalized revenue + earnings growth. Higher = stronger top-line and bottom-line growth.",
  big_call:
    "Weighted Quality (40%) + Dividend (30%) + Growth (30%); reweights proportionally when a component is missing.",
  aaqs:
    "Quality combined with low-volatility (low beta is better). Higher = quality with stable beta.",
  hgi:
    "Growth-tilted score with a fixed bonus when operating margin clears ~10%.",
};

async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`fetch ${url} failed: ${res.status}`);
  return res.json();
}

const loadManifest = () =>
  fetchJson(`${DATA_BASE_URL}/results/demo/${UNIVERSE}/index.json`);

const loadSnapshot = (date) =>
  fetchJson(`${DATA_BASE_URL}/results/demo/${UNIVERSE}/${date}.json`);

async function loadFearGreedYears() {
  const thisYear = new Date().getUTCFullYear();
  const results = await Promise.allSettled([
    fetchJson(`${DATA_BASE_URL}/results/cnn_fg/${thisYear - 1}.json`),
    fetchJson(`${DATA_BASE_URL}/results/cnn_fg/${thisYear}.json`),
  ]);
  const merged = [];
  for (const r of results) {
    if (r.status === "fulfilled" && Array.isArray(r.value)) {
      merged.push(...r.value);
    }
  }
  return merged.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
}

function nested(obj, key) {
  return key.split(".").reduce((o, k) => (o == null ? null : o[k]), obj);
}

const fmtNum = (v, d = 1) =>
  v == null || Number.isNaN(Number(v)) ? "—" : Number(v).toFixed(d);

const fmtPct = (v) => (v == null ? "—" : (Number(v) * 100).toFixed(2));

function compareValues(a, b, dir) {
  if (a == null && b == null) return 0;
  if (a == null) return 1;
  if (b == null) return -1;
  if (typeof a === "string") return dir * a.localeCompare(b);
  return dir * (a - b);
}

function td(text, cls) {
  const el = document.createElement("td");
  el.textContent = text;
  if (cls) el.className = cls;
  return el;
}

function renderTable() {
  const tbody = document.querySelector("#universe-table tbody");
  tbody.replaceChildren();
  const sorted = [...state.snapshot].sort((a, b) =>
    compareValues(nested(a, state.sortKey), nested(b, state.sortKey), state.sortDir),
  );
  // Per-row Weight % = score / sum(scores), shown as a row-level title=.
  const totalScore = state.snapshot.reduce((acc, row) => {
    const s = nested(row, "composite_scores.screener_score");
    return acc + (s == null ? 0 : Number(s));
  }, 0);
  for (const row of sorted) {
    const tr = document.createElement("tr");
    const score = nested(row, "composite_scores.screener_score");
    if (score != null && totalScore > 0) {
      const weightPct = ((100 * Number(score)) / totalScore).toFixed(1);
      tr.title = `Weight ${weightPct} % (Score ${Number(score).toFixed(0)} / sum)`;
    }
    tr.append(
      td(row.symbol ?? "—"),
      td(row.long_name ?? "—"),
      td(row.sector ?? "—"),
      td(fmtNum(row.forward_pe, 2), "num"),
      td(fmtNum(row.trailing_peg_ratio, 2), "num"),
      td(fmtNum(row.beta, 2), "num"),
      td(fmtPct(row.rd_to_revenue), "num"),
      td(fmtPct(row.operating_margins), "num"),
      td(fmtPct(row.return_on_equity), "num"),
      td(fmtPct(row.return_on_assets), "num"),
      td(fmtNum(row.current_ratio, 2), "num"),
      td(fmtNum(row.sortino_ratio, 2), "num"),
      td(fmtNum(score, 0), "num"),
    );
    tr.addEventListener("click", () => showDetail(row));
    tbody.appendChild(tr);
  }
}

function dl(pairs) {
  const frag = document.createDocumentFragment();
  for (const [label, value, sectionHeader, tooltip] of pairs) {
    const dt = document.createElement("dt");
    dt.textContent = label;
    if (sectionHeader) {
      dt.className = "section";
      frag.append(dt);
      continue;
    }
    if (tooltip) {
      dt.title = tooltip;
      dt.tabIndex = 0;
    }
    const dd = document.createElement("dd");
    dd.textContent = value;
    frag.append(dt, dd);
  }
  return frag;
}

function showDetail(row) {
  const cs = row.composite_scores ?? {};
  const mcap = row.market_cap
    ? `$${(row.market_cap / 1e9).toFixed(2)} B`
    : "—";

  const aside = document.getElementById("row-detail");
  aside.replaceChildren();

  const closeBtn = document.createElement("button");
  closeBtn.id = "close-detail";
  closeBtn.setAttribute("aria-label", "Close");
  closeBtn.textContent = "×";
  closeBtn.addEventListener("click", () => {
    aside.hidden = true;
  });
  aside.append(closeBtn);

  const h3 = document.createElement("h3");
  h3.textContent = `${row.symbol ?? "—"} · ${row.long_name ?? ""}`;
  aside.append(h3);

  const trail = row.trailing_pe;
  const fwd = row.forward_pe;
  const trailFwd =
    trail != null && fwd != null && fwd !== 0
      ? (trail / fwd).toFixed(2)
      : "—";
  const list = document.createElement("dl");
  list.append(
    dl([
      ["Sector", row.sector ?? "—"],
      ["Industry", row.industry ?? "—"],
      ["Exchange", `${row.exchange ?? "—"} (${row.currency ?? "—"})`],
      ["Market cap", mcap],
      [
        "Trail / Fwd P/E",
        `${fmtNum(row.trailing_pe, 2)} / ${fmtNum(row.forward_pe, 2)}`,
        false,
        KPI_GLOSSARY.trailing_pe,
      ],
      ["Trail/Fwd P/E ratio", trailFwd, false, KPI_GLOSSARY.trail_fwd_pe],
      ["P/B / P/S TTM", `${fmtNum(row.price_to_book, 2)} / ${fmtNum(row.price_to_sales_ttm, 2)}`],
      [
        "Gross margin %",
        fmtPct(row.gross_margins),
        false,
        KPI_GLOSSARY.gross_margins,
      ],
      [
        "Net margin %",
        fmtPct(row.profit_margins),
        false,
        KPI_GLOSSARY.profit_margins,
      ],
      [
        "ROE / ROA",
        `${fmtPct(row.return_on_equity)} % / ${fmtPct(row.return_on_assets)} %`,
        false,
        KPI_GLOSSARY.return_on_equity,
      ],
      ["ROI", fmtPct(row.roi), false, KPI_GLOSSARY.roi],
      [
        "R&D / Revenue %",
        fmtPct(row.rd_to_revenue),
        false,
        KPI_GLOSSARY.rd_to_revenue,
      ],
      [
        "Op margin %",
        fmtPct(row.operating_margins),
        false,
        KPI_GLOSSARY.operating_margins,
      ],
      ["D/E", fmtNum(row.debt_to_equity, 2), false, KPI_GLOSSARY.debt_to_equity],
      [
        "Current ratio",
        fmtNum(row.current_ratio, 2),
        false,
        KPI_GLOSSARY.current_ratio,
      ],
      ["Quick ratio", fmtNum(row.quick_ratio, 2), false, KPI_GLOSSARY.quick_ratio],
      ["Revenue growth", `${fmtPct(row.revenue_growth)} %`],
      ["Earnings growth", `${fmtPct(row.earnings_growth)} %`],
      ["Div yield / Payout", `${fmtPct(row.dividend_yield)} % / ${fmtPct(row.payout_ratio)} %`],
      ["52w high / low", `$${fmtNum(row.fifty_two_week_high, 2)} / $${fmtNum(row.fifty_two_week_low, 2)}`],
      ["Beta", fmtNum(row.beta, 2), false, KPI_GLOSSARY.beta],
      [
        "PEG (trailing)",
        fmtNum(row.trailing_peg_ratio, 2),
        false,
        KPI_GLOSSARY.trailing_peg_ratio,
      ],
      [
        "Sortino (1y, rf=0)",
        fmtNum(row.sortino_ratio, 2),
        false,
        KPI_GLOSSARY.sortino_ratio,
      ],
      ["Composite scores", "", true],
      ["Quality", fmtNum(cs.quality, 0), false, KPI_GLOSSARY.quality],
      ["Dividend", fmtNum(cs.dividend, 0), false, KPI_GLOSSARY.dividend],
      ["Growth", fmtNum(cs.growth, 0), false, KPI_GLOSSARY.growth],
      ["Big Call", fmtNum(cs.big_call, 0), false, KPI_GLOSSARY.big_call],
      ["AAQS", fmtNum(cs.aaqs, 0), false, KPI_GLOSSARY.aaqs],
      ["HGI", fmtNum(cs.hgi, 0), false, KPI_GLOSSARY.hgi],
      [
        "Screener",
        fmtNum(cs.screener_score, 0),
        false,
        KPI_GLOSSARY.screener_score,
      ],
    ]),
  );
  aside.append(list);
  aside.hidden = false;
}

function findClosestScore(entries, latestMs, daysAgo) {
  const target = latestMs - daysAgo * 86400000;
  let best = null;
  let bestDiff = Infinity;
  for (const e of entries) {
    const diff = Math.abs(new Date(e.timestamp).getTime() - target);
    if (diff < bestDiff) {
      bestDiff = diff;
      best = e;
    }
  }
  return best?.score;
}

function renderFearGreedHeader(entries) {
  if (!entries.length) return;
  const last = entries[entries.length - 1];
  document.getElementById("fg-score").textContent = fmtNum(last.score, 0);
  const rating = (last.rating ?? "").toLowerCase();
  const chip = document.getElementById("fg-rating");
  chip.textContent = last.rating ?? "—";
  chip.className = `chip ${RATING_CLASSES[rating] ?? ""}`;

  const latestMs = new Date(last.timestamp).getTime();
  const deltas = [
    ["yesterday", 1],
    ["last week", 7],
    ["last month", 30],
    ["last year", 365],
  ]
    .map(([label, d]) => `${label} ${fmtNum(findClosestScore(entries, latestMs, d), 0)}`)
    .join(" · ");
  document.getElementById("fg-deltas").textContent = `(${deltas})`;
}

function renderFearGreedChart(entries) {
  if (!entries.length || typeof Chart === "undefined") return;
  const ctx = document.getElementById("fg-chart");
  // eslint-disable-next-line no-new
  new Chart(ctx, {
    type: "line",
    data: {
      labels: entries.map((e) => e.timestamp.slice(0, 10)),
      datasets: [
        {
          data: entries.map((e) => e.score),
          borderColor: "#1d1d1f",
          backgroundColor: "rgba(29, 29, 31, 0.08)",
          fill: true,
          pointRadius: 0,
          borderWidth: 1.5,
          tension: 0.15,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: { duration: 250 },
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100, ticks: { stepSize: 25 } },
        x: { ticks: { maxTicksLimit: 14 } },
      },
    },
  });
}

function bindTableSort() {
  document.querySelectorAll("#universe-table thead th").forEach((th) => {
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      if (state.sortKey === key) {
        state.sortDir *= -1;
      } else {
        state.sortKey = key;
        state.sortDir = 1;
      }
      document.querySelectorAll("#universe-table thead th").forEach((t) => {
        t.classList.remove("sort-asc", "sort-desc");
      });
      th.classList.add(state.sortDir > 0 ? "sort-asc" : "sort-desc");
      renderTable();
    });
  });
}

async function init() {
  bindTableSort();
  const initialSortTh = document.querySelector(
    `#universe-table thead th[data-key="${state.sortKey}"]`,
  );
  if (initialSortTh) {
    initialSortTh.classList.add(state.sortDir > 0 ? "sort-asc" : "sort-desc");
  }

  let manifest;
  try {
    manifest = await loadManifest();
  } catch {
    document.getElementById("universe-name").textContent =
      "qte77-watchlist (no data yet — first cron run pending)";
    return;
  }

  const selector = document.getElementById("date-selector");
  for (const date of [...manifest.dates].reverse()) {
    const opt = document.createElement("option");
    opt.value = date;
    opt.textContent = date;
    selector.appendChild(opt);
  }
  selector.value = manifest.latest;
  selector.addEventListener("change", async () => {
    state.snapshot = await loadSnapshot(selector.value);
    renderTable();
  });

  state.snapshot = await loadSnapshot(manifest.latest);
  document.getElementById("universe-size").textContent =
    `${state.snapshot.length} tickers`;
  renderTable();
  document.getElementById("updated").textContent =
    `updated ${manifest.updated_at}`;

  const fgEntries = await loadFearGreedYears();
  renderFearGreedHeader(fgEntries);
  renderFearGreedChart(fgEntries);
}

document.addEventListener("DOMContentLoaded", init);
